from odoo import api, fields, models


class LocalizaGtPayrollParameter(models.Model):
    _name = 'localiza.gt.payroll.parameter'
    _description = 'Parámetros de Nómina Guatemala'
    _rec_name = 'company_id'

    company_id = fields.Many2one('res.company', string='Compañía', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)
    igss_employee_rate = fields.Float(string='IGSS laboral', default=4.83, help='Porcentaje laboral IGSS.')
    igss_employer_rate = fields.Float(string='IGSS patronal', default=10.67)
    irtra_rate = fields.Float(string='IRTRA', default=1.0)
    intecap_rate = fields.Float(string='INTECAP', default=1.0)
    bono14_rate = fields.Float(string='Provisión Bono 14', default=8.333333)
    aguinaldo_rate = fields.Float(string='Provisión Aguinaldo', default=8.333333)
    vacation_days = fields.Float(string='Días vacaciones anuales', default=15.0)
    incentive_bonus_monthly = fields.Monetary(string='Bonificación incentivo mensual', default=250.0, currency_field='currency_id')
    settlement_months_average = fields.Integer(string='Meses para promedio liquidación', default=6)

    _sql_constraints = [('company_unique', 'unique(company_id)', 'Solo puede existir una configuración por compañía.')]

    @api.model
    def get_company_parameter(self, company=None):
        company = company or self.env.company
        rec = self.search([('company_id', '=', company.id)], limit=1)
        if not rec:
            rec = self.create({'company_id': company.id})
        return rec
