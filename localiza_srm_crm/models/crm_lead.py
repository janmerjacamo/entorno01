from odoo import api, fields, models, _
from odoo.exceptions import UserError

LOCALIZA_OWNER_SELECTION = [
    ('maribel_garcia', 'Maribel García'),
    ('ana_beatriz_guinea', 'Ana Beatriz Guinea'),
    ('carolina_ortiz', 'Carolina Ortiz'),
]


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    localiza_owner = fields.Selection(LOCALIZA_OWNER_SELECTION, string='Propietario Localiza', tracking=True)
    localiza_client_classification = fields.Selection([
        ('nuevo', 'Nuevo'),
        ('existente', 'Cliente existente'),
        ('renovacion', 'Renovación'),
        ('prospecto', 'Prospecto'),
    ], string='Clasificación de cliente', tracking=True)
    localiza_source = fields.Selection([
        ('referido', 'Referido'),
        ('campana', 'Campaña'),
        ('llamada', 'Llamada'),
        ('correo', 'Correo'),
        ('web', 'Web'),
        ('otro', 'Otro'),
    ], string='Fuente', tracking=True)
    localiza_campaign_source = fields.Char(string='Fuente de campaña')
    localiza_prospect_source = fields.Char(string='Fuente de prospecto')
    localiza_product = fields.Selection([
        ('accesorios_gps', 'ACCESORIOS GPS'),
        ('ampliacion_cctv', 'AMPLIACIÓN CCTV'),
        ('cuentas_por_cobrar_sem', 'CUENTAS POR COBRAR SEM'),
        ('deducibles_gps', 'DEDUCIBLES POR GPS'),
        ('gastos_administrativos', 'GASTOS ADMINISTRATIVOS'),
        ('gps_anual', 'GPS ANUAL'),
        ('gps_mensual', 'GPS MENSUAL'),
        ('gps_portatiles', 'GPS PORTÁTILES'),
        ('luces_emergencia', 'LUCES DE EMERGENCIA'),
        ('mantenimiento_revisiones', 'MANTENIMIENTO Y REVISIONES'),
        ('materiales_cctv', 'MATERIALES CCTV'),
        ('microfonos', 'MICRÓFONOS'),
        ('monitoreo_gps', 'MONITOREO GPS'),
        ('otro', 'OTRO'),
    ], string='Tipo de producto')
    localiza_sale_modality = fields.Selection([
        ('renta', 'Renta'),
        ('venta', 'Venta'),
    ], string='Modalidad', tracking=True)
    localiza_payment_type = fields.Selection([
        ('contado', 'Contado'),
        ('credito', 'Crédito'),
    ], string='Forma de pago', tracking=True)
    localiza_due_datetime = fields.Datetime(string='Fecha y hora de vencimiento')
    localiza_summary = fields.Text(string='Resumen')
    localiza_sequence = fields.Char(string='No. oportunidad Localiza', copy=False, index=True, readonly=True)
    localiza_weighted_revenue = fields.Monetary(
        string='Importe ponderado',
        compute='_compute_localiza_weighted_revenue',
        store=True,
        currency_field='company_currency'
    )
    localiza_stage_history_ids = fields.One2many('localiza.crm.stage.history', 'lead_id', string='Historial de fases')
    localiza_stage_history_count = fields.Integer(string='Historial de fases', compute='_compute_localiza_counts')
    localiza_calendar_event_ids = fields.One2many('calendar.event', 'localiza_opportunity_id', string='Eventos/Reuniones')
    localiza_calendar_event_count = fields.Integer(string='Eventos/Reuniones', compute='_compute_localiza_counts')

    @api.depends('expected_revenue', 'probability')
    def _compute_localiza_weighted_revenue(self):
        for lead in self:
            lead.localiza_weighted_revenue = (lead.expected_revenue or 0.0) * ((lead.probability or 0.0) / 100.0)

    def _compute_localiza_counts(self):
        History = self.env['localiza.crm.stage.history'].sudo()
        Event = self.env['calendar.event'].sudo()
        for lead in self:
            lead.localiza_stage_history_count = History.search_count([('lead_id', '=', lead.id)]) if lead.id else 0
            lead.localiza_calendar_event_count = Event.search_count([('localiza_opportunity_id', '=', lead.id)]) if lead.id else 0

    def _localiza_stage_probability(self, stage):
        name = (stage.name or '').strip().lower() if stage else ''
        mapping = [
            (('cerrado perdido', 'perdido'), 0),
            (('nuevo',), 20),
            (('identificar responsable', 'identificar responsables'), 40),
            (('necesita análisis', 'necesita analisis'), 60),
            (('cotización', 'cotizacion', 'propuesta', 'precio'), 80),
            (('negociación', 'negociacion', 'revision', 'revisión'), 90),
            (('cerrado ganado', 'ganado', 'renovaciones', 'renovación'), 100),
        ]
        for keys, value in mapping:
            if any(key in name for key in keys):
                return value
        return stage.probability if stage and hasattr(stage, 'probability') else (self.probability or 0.0)

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env['ir.sequence'].sudo()
        for vals in vals_list:
            if not vals.get('localiza_sequence'):
                vals['localiza_sequence'] = sequence.next_by_code('localiza.crm.lead') or _('Nuevo')
            if vals.get('stage_id') and 'probability' not in vals:
                vals['probability'] = self._localiza_stage_probability(self.env['crm.stage'].browse(vals['stage_id']))
        leads = super().create(vals_list)
        for lead in leads:
            lead._localiza_create_stage_history(False, lead.stage_id)
        return leads

    def write(self, vals):
        old_stages = {lead.id: lead.stage_id for lead in self}
        res = super().write(vals)
        if 'stage_id' in vals and not self.env.context.get('skip_localiza_stage_sync'):
            for lead in self:
                old_stage = old_stages.get(lead.id)
                new_stage = lead.stage_id
                if old_stage != new_stage:
                    probability = lead._localiza_stage_probability(new_stage)
                    if lead.probability != probability:
                        lead.with_context(skip_localiza_stage_sync=True).write({'probability': probability})
                    lead._localiza_create_stage_history(old_stage, new_stage)
        return res

    def _localiza_create_stage_history(self, old_stage, new_stage):
        self.ensure_one()
        if not new_stage:
            return
        last = self.env['localiza.crm.stage.history'].sudo().search([('lead_id', '=', self.id)], limit=1)
        days = 0
        if last and last.change_date:
            days = max((fields.Datetime.now() - last.change_date).days, 0)
        self.env['localiza.crm.stage.history'].sudo().create({
            'lead_id': self.id,
            'previous_stage_id': old_stage.id if old_stage else False,
            'new_stage_id': new_stage.id,
            'user_id': self.env.user.id,
            'expected_revenue': self.expected_revenue,
            'weighted_revenue': self.localiza_weighted_revenue,
            'probability': self.probability,
            'days_in_previous_stage': days,
        })

    def _localiza_find_stage(self, names):
        Stage = self.env['crm.stage'].sudo()
        for name in names:
            stage = Stage.search([('name', '=ilike', name)], limit=1)
            if stage:
                return stage
        for name in names:
            stage = Stage.search([('name', 'ilike', name)], limit=1)
            if stage:
                return stage
        return False

    def action_localiza_mark_won(self):
        stage = self._localiza_find_stage(['Cerrado ganado', 'Ganado'])
        if not stage:
            raise UserError(_('No existe una etapa llamada Cerrado ganado o Ganado.'))
        self.write({'stage_id': stage.id, 'probability': 100})
        return True

    def action_localiza_mark_lost(self):
        stage = self._localiza_find_stage(['Cerrado perdido', 'Perdido'])
        if not stage:
            raise UserError(_('No existe una etapa llamada Cerrado perdido o Perdido.'))
        self.write({'stage_id': stage.id, 'probability': 0})
        return True

    def action_localiza_view_stage_history(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Historial de fases'),
            'res_model': 'localiza.crm.stage.history',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {'default_lead_id': self.id},
        }

    def action_localiza_view_calendar_events(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Eventos/Reuniones'),
            'res_model': 'calendar.event',
            'view_mode': 'calendar,list,form',
            'domain': [('localiza_opportunity_id', '=', self.id)],
            'context': {'default_localiza_opportunity_id': self.id, 'default_localiza_partner_id': self.partner_id.id},
        }

    def action_localiza_create_activity(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Crear actividad / recordatorio'),
            'res_model': 'mail.activity',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model_id': self.env['ir.model']._get_id('crm.lead'),
                'default_res_id': self.id,
                'default_summary': self.name,
                'default_user_id': self.user_id.id or self.env.user.id,
                'default_localiza_owner': self.localiza_owner,
            },
        }

    def action_localiza_create_event_task(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nuevo evento / tarea'),
            'res_model': 'calendar.event',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': _('Seguimiento: %s') % self.name,
                'default_localiza_opportunity_id': self.id,
                'default_localiza_partner_id': self.partner_id.id,
                'default_partner_ids': [(6, 0, [self.partner_id.id])] if self.partner_id else [],
                'default_localiza_owner': self.localiza_owner,
                'default_localiza_task_type': 'seguimiento',
            },
        }
