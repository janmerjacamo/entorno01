from odoo import fields, models


class LocalizaCrmStageHistory(models.Model):
    _name = 'localiza.crm.stage.history'
    _description = 'Historial de fases de oportunidad Localiza'
    _order = 'change_date desc, id desc'

    lead_id = fields.Many2one('crm.lead', string='Oportunidad', required=True, ondelete='cascade', index=True)
    previous_stage_id = fields.Many2one('crm.stage', string='Etapa anterior')
    new_stage_id = fields.Many2one('crm.stage', string='Nueva etapa', required=True)
    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user, required=True)
    change_date = fields.Datetime(string='Fecha de cambio', default=fields.Datetime.now, required=True)
    expected_revenue = fields.Monetary(string='Ingreso esperado', currency_field='company_currency')
    weighted_revenue = fields.Monetary(string='Importe ponderado', currency_field='company_currency')
    probability = fields.Float(string='Probabilidad (%)')
    days_in_previous_stage = fields.Integer(string='Días en etapa anterior')
    company_currency = fields.Many2one(related='lead_id.company_currency', store=False, readonly=True)
