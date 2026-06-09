from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from .crm_lead import LOCALIZA_OWNER_SELECTION


def _clean(value):
    return ' '.join((value or '').strip().upper().split())


def _clean_phone(value):
    return ''.join(ch for ch in (value or '') if ch.isdigit())


class ResPartner(models.Model):
    _inherit = 'res.partner'

    localiza_owner = fields.Selection(LOCALIZA_OWNER_SELECTION, string='Comercial responsable')
    localiza_duplicate_count = fields.Integer(string='Duplicados', compute='_compute_localiza_duplicate_count')

    def _localiza_duplicate_domain_from_values(self, vals=None):
        vals = vals or {}
        partner_id = self.id if len(self) == 1 and isinstance(self.id, int) else False
        parts = []
        name = _clean(vals.get('name', self.name if len(self) == 1 else False))
        email = (vals.get('email', self.email if len(self) == 1 else False) or '').strip()
        vat = (vals.get('vat', self.vat if len(self) == 1 else False) or '').strip()
        phone = _clean_phone(vals.get('phone', self.phone if len(self) == 1 else False))
        mobile = _clean_phone(vals.get('mobile', self.mobile if len(self) == 1 else False))
        phone_value = phone or mobile
        if vat:
            parts.append([('vat', '=ilike', vat)])
        if email:
            parts.append([('email', '=ilike', email)])
        if phone_value:
            parts.append(['|', ('phone', 'ilike', phone_value), ('mobile', 'ilike', phone_value)])
        if name:
            parts.append([('name', '=ilike', name)])
        if not parts:
            return [('id', '=', 0)]
        domain = expression.OR(parts)
        if partner_id:
            domain = [('id', '!=', partner_id)] + domain
        return domain

    def _compute_localiza_duplicate_count(self):
        for partner in self:
            partner.localiza_duplicate_count = self.sudo().search_count(partner._localiza_duplicate_domain_from_values()) if partner.id else 0

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get('localiza_allow_duplicate_partner'):
            Partner = self.sudo()
            for vals in vals_list:
                pseudo = self.new(vals)
                domain = pseudo._localiza_duplicate_domain_from_values(vals)
                duplicate = Partner.search(domain, limit=1)
                if duplicate:
                    raise ValidationError(_('Ya existe un contacto/cliente similar: %s. Revise la ficha existente antes de crear otro registro.') % duplicate.display_name)
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('localiza_allow_duplicate_partner') and any(k in vals for k in ['name', 'vat', 'email', 'phone', 'mobile']):
            for partner in self:
                duplicate = self.sudo().search(partner._localiza_duplicate_domain_from_values(), limit=1)
                if duplicate:
                    raise ValidationError(_('Ya existe un contacto/cliente similar: %s. Revise la ficha existente antes de guardar duplicados.') % duplicate.display_name)
        return res

    def action_localiza_view_duplicates(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Posibles duplicados'),
            'res_model': 'res.partner',
            'view_mode': 'list,form',
            'domain': self._localiza_duplicate_domain_from_values(),
        }

    def action_localiza_create_opportunity(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nueva oportunidad'),
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'context': {'default_partner_id': self.id, 'default_type': 'opportunity', 'default_localiza_owner': self.localiza_owner},
        }

    def action_localiza_create_activity(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nueva actividad / recordatorio'),
            'res_model': 'mail.activity',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model_id': self.env['ir.model']._get_id('res.partner'),
                'default_res_id': self.id,
                'default_summary': _('Seguimiento cliente: %s') % self.display_name,
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
            'context': {'default_localiza_partner_id': self.id, 'default_partner_ids': [(6, 0, [self.id])], 'default_name': _('Seguimiento con %s') % self.display_name, 'default_localiza_task_type': 'seguimiento'},
        }
