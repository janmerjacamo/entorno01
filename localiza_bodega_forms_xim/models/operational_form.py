# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class LocalizaOperationalForm(models.Model):
    _name = 'localiza.operational.form'
    _description = 'Formulario Operativo de Bodega'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'form_date desc, id desc'

    name = fields.Char(string='Folio Odoo', required=True, copy=False, readonly=True, default='Nuevo', tracking=True)
    external_folio = fields.Char(string='Folio externo', tracking=True, index=True)
    form_type = fields.Selection([
        ('warehouse_delivery', 'Entrega desde Bodega'),
        ('site_installation', 'Instalación en Puesto'),
        ('site_inventory', 'Inventario de Puesto'),
        ('tool_loan', 'Préstamo de Herramientas'),
        ('other', 'Otro Formulario'),
    ], string='Tipo de formulario', required=True, default='warehouse_delivery', tracking=True, index=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('validated', 'Validado'),
        ('closed', 'Cerrado'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='draft', tracking=True, index=True)

    form_date = fields.Datetime(string='Fecha / Hora', default=fields.Datetime.now, required=True, tracking=True)
    source_system = fields.Char(string='Sistema origen', default='Carga manual/Odoo')
    active_user = fields.Char(string='Usuario / Activo origen')
    location_text = fields.Char(string='Ubicación GPS / Mapa')

    # Personas y responsables
    supervisor_name = fields.Char(string='Persona que supervisa')
    delivery_responsible = fields.Char(string='Encargado de entrega')
    receiver_name = fields.Char(string='Persona que recibe / solicita')
    installer_name = fields.Char(string='Persona que instala')
    guard_name = fields.Char(string='Guardia de turno')
    dpi_receiver = fields.Char(string='DPI receptor')

    # Puestos / origen / destino
    source_place = fields.Char(string='Puesto / ubicación origen')
    destination_place = fields.Char(string='Puesto / ubicación destino')
    puesto_id = fields.Many2one('localiza.puesto', string='Puesto relacionado', ondelete='set null')
    partner_id = fields.Many2one('res.partner', string='Cliente / Contacto')

    # Control operacional
    reason = fields.Text(string='Motivo')
    summary = fields.Text(string='Resumen')
    observations = fields.Text(string='Observaciones')
    warranty_text = fields.Text(string='Responsabilidad / Nota legal', default=lambda self: self._default_warranty_text())

    # Campos comunes para equipo seriado / controlado
    equipment_serial = fields.Char(string='Serie principal')
    ammunition_qty = fields.Integer(string='Cantidad de munición / accesorios')
    expiration_date = fields.Date(string='Fecha de vencimiento / portación')

    # Evidencias y firmas como binarios simples para máxima compatibilidad
    photo_main = fields.Binary(string='Fotografía principal', attachment=True)
    photo_main_filename = fields.Char(string='Nombre foto principal')
    photo_document = fields.Binary(string='Foto documento / DPI', attachment=True)
    photo_document_filename = fields.Char(string='Nombre documento')
    photo_extra = fields.Binary(string='Fotografía adicional', attachment=True)
    photo_extra_filename = fields.Char(string='Nombre foto adicional')
    signature_1 = fields.Binary(string='Firma responsable / supervisor', attachment=True)
    signature_1_filename = fields.Char(string='Nombre firma 1')
    signature_2 = fields.Binary(string='Firma receptor / guardia', attachment=True)
    signature_2_filename = fields.Char(string='Nombre firma 2')
    original_pdf = fields.Binary(string='PDF original importado', attachment=True)
    original_pdf_filename = fields.Char(string='Nombre PDF original')

    line_ids = fields.One2many('localiza.operational.form.line', 'form_id', string='Detalle de artículos')
    line_count = fields.Integer(string='Cantidad de líneas', compute='_compute_line_count')

    @api.model
    def _default_warranty_text(self):
        return ('La persona que recibe los artículos descritos declara haberlos recibido en las condiciones indicadas y asume responsabilidad de custodia, uso y devolución según las políticas internas de la empresa.')

    @api.depends('line_ids')
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    @api.model_create_multi
    def create(self, vals_list):
        seq_map = {
            'warehouse_delivery': 'localiza.operational.form.delivery',
            'site_installation': 'localiza.operational.form.installation',
            'site_inventory': 'localiza.operational.form.inventory',
            'tool_loan': 'localiza.operational.form.tool',
            'other': 'localiza.operational.form.other',
        }
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                code = seq_map.get(vals.get('form_type'), 'localiza.operational.form.other')
                vals['name'] = self.env['ir.sequence'].next_by_code(code) or 'Nuevo'
        return super().create(vals_list)

    @api.constrains('external_folio')
    def _check_external_folio_unique(self):
        for rec in self:
            if rec.external_folio:
                dup = self.search_count([('external_folio', '=', rec.external_folio), ('id', '!=', rec.id)])
                if dup:
                    raise ValidationError(_('El folio externo ya existe: %s') % rec.external_folio)

    def action_validate(self):
        for rec in self:
            if not rec.line_ids and rec.form_type in ('site_inventory', 'tool_loan'):
                raise UserError(_('Agregue al menos una línea de detalle antes de validar.'))
            rec.state = 'validated'

    def action_close(self):
        self.write({'state': 'closed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def action_print_form(self):
        return self.env.ref('localiza_bodega_forms.action_report_localiza_operational_form').report_action(self)


class LocalizaOperationalFormLine(models.Model):
    _name = 'localiza.operational.form.line'
    _description = 'Línea de Formulario Operativo'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    form_id = fields.Many2one('localiza.operational.form', string='Formulario', required=True, ondelete='cascade', index=True)
    product_id = fields.Many2one('product.product', string='Producto')
    category_text = fields.Char(string='Categoría / Grupo')
    item_name = fields.Char(string='Artículo / Insumo', required=True)
    item_code = fields.Char(string='Código de artículo')
    serial_number = fields.Char(string='Serie / IMEI')
    quantity = fields.Float(string='Cantidad', default=1.0)
    movement_type = fields.Selection([
        ('out', 'Salida'),
        ('in', 'Entrada'),
        ('inventory', 'Inventario físico'),
        ('assigned', 'Asignado'),
        ('missing', 'Faltante'),
        ('damaged', 'Dañado'),
        ('change_required', 'Necesita cambio'),
    ], string='Tipo de movimiento', default='inventory')
    condition = fields.Selection([
        ('good', 'Bueno'),
        ('regular', 'Regular'),
        ('bad', 'Malo'),
        ('new', 'Nuevo'),
        ('used', 'Usado'),
        ('unknown', 'No indicado'),
    ], string='Condición', default='unknown')
    accessory = fields.Boolean(string='Accesorio')
    checked = fields.Boolean(string='Marcado / Incluido')
    notes = fields.Text(string='Observaciones')
    photo = fields.Binary(string='Fotografía', attachment=True)
    photo_filename = fields.Char(string='Nombre fotografía')
