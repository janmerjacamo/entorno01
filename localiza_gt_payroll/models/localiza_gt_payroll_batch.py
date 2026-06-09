from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LocalizaGtPayrollBatch(models.Model):
    _name = 'localiza.gt.payroll.batch'
    _description = 'Planilla Localiza Guatemala'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_to desc, id desc'

    name = fields.Char(string='Nombre', required=True, default='Nueva planilla')
    company_id = fields.Many2one('res.company', string='Compañía', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)
    batch_type = fields.Selection([
        ('first_half', '1ra quincena'),
        ('second_half', '2da quincena'),
        ('benefits', 'Nómina prestaciones'),
        ('monthly', 'Mensual'),
    ], string='Tipo', default='monthly', required=True, tracking=True)
    date_from = fields.Date(string='Desde', required=True)
    date_to = fields.Date(string='Hasta', required=True)
    line_ids = fields.One2many('localiza.gt.payroll.batch.line', 'batch_id', string='Líneas')
    state = fields.Selection([('draft', 'Borrador'), ('computed', 'Calculada'), ('approved', 'Aprobada'), ('cancel', 'Cancelada')], default='draft', tracking=True)
    total_gross = fields.Monetary(string='Total bruto', compute='_compute_totals', store=True, currency_field='currency_id')
    total_deductions = fields.Monetary(string='Total descuentos', compute='_compute_totals', store=True, currency_field='currency_id')
    total_net = fields.Monetary(string='Líquido a recibir', compute='_compute_totals', store=True, currency_field='currency_id')
    total_provision = fields.Monetary(string='Provisión prestaciones', compute='_compute_totals', store=True, currency_field='currency_id')

    @api.depends('line_ids.gross_total', 'line_ids.total_deductions', 'line_ids.net_amount', 'line_ids.provision_total')
    def _compute_totals(self):
        for rec in self:
            rec.total_gross = sum(rec.line_ids.mapped('gross_total'))
            rec.total_deductions = sum(rec.line_ids.mapped('total_deductions'))
            rec.total_net = sum(rec.line_ids.mapped('net_amount'))
            rec.total_provision = sum(rec.line_ids.mapped('provision_total'))

    def action_compute(self):
        for rec in self:
            rec.line_ids._compute_amounts()
            rec.state = 'computed'

    def action_approve(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(_('No puede aprobar una planilla sin líneas.'))
            rec.state = 'approved'

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})


class LocalizaGtPayrollBatchLine(models.Model):
    _name = 'localiza.gt.payroll.batch.line'
    _description = 'Línea de planilla Localiza Guatemala'
    _order = 'department_name, employee_id'

    batch_id = fields.Many2one('localiza.gt.payroll.batch', string='Planilla', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='batch_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='batch_id.currency_id', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    contract_id = fields.Many2one('hr.contract', string='Contrato')
    department_name = fields.Char(string='Departamento / Área')
    job_name = fields.Char(string='Puesto')
    days_worked = fields.Float(string='Días laborados', default=30.0)
    base_salary = fields.Monetary(string='Sueldo base', currency_field='currency_id')
    incentive_bonus = fields.Monetary(string='Bonificación incentivo', currency_field='currency_id')
    decree_bonus = fields.Monetary(string='Bono DTO', currency_field='currency_id')
    overtime = fields.Monetary(string='Horas extras', currency_field='currency_id')
    first_half_amount = fields.Monetary(string='Primera quincena', currency_field='currency_id')
    gross_total = fields.Monetary(string='Total', compute='_compute_amounts', store=True, currency_field='currency_id')
    igss = fields.Monetary(string='IGSS', compute='_compute_amounts', store=True, currency_field='currency_id')
    isr = fields.Monetary(string='ISR', currency_field='currency_id')
    advances = fields.Monetary(string='Anticipos', currency_field='currency_id')
    other_deductions = fields.Monetary(string='Otros descuentos', currency_field='currency_id')
    total_deductions = fields.Monetary(string='Total descuentos', compute='_compute_amounts', store=True, currency_field='currency_id')
    net_amount = fields.Monetary(string='Líquido a recibir', compute='_compute_amounts', store=True, currency_field='currency_id')
    bono14_provision = fields.Monetary(string='Bono 14', compute='_compute_amounts', store=True, currency_field='currency_id')
    aguinaldo_provision = fields.Monetary(string='Aguinaldo', compute='_compute_amounts', store=True, currency_field='currency_id')
    indemnity_provision = fields.Monetary(string='Indemnización', compute='_compute_amounts', store=True, currency_field='currency_id')
    employer_igss = fields.Monetary(string='Patronal', compute='_compute_amounts', store=True, currency_field='currency_id')
    irtra = fields.Monetary(string='IRTRA', compute='_compute_amounts', store=True, currency_field='currency_id')
    intecap = fields.Monetary(string='INTECAP', compute='_compute_amounts', store=True, currency_field='currency_id')
    provision_total = fields.Monetary(string='Provisión', compute='_compute_amounts', store=True, currency_field='currency_id')

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for rec in self:
            emp = rec.employee_id
            if emp:
                rec.department_name = emp.department_id.name or emp.localiza_payroll_area or ''
                rec.job_name = emp.job_id.name or ''
                contract = self.env['hr.contract'].search([('employee_id', '=', emp.id), ('state', '=', 'open')], limit=1)
                rec.contract_id = contract.id
                if contract:
                    rec.base_salary = contract.wage or 0.0

    @api.depends('base_salary', 'incentive_bonus', 'decree_bonus', 'overtime', 'isr', 'advances', 'other_deductions', 'first_half_amount', 'batch_id.batch_type')
    def _compute_amounts(self):
        Param = self.env['localiza.gt.payroll.parameter']
        for rec in self:
            params = Param.get_company_parameter(rec.company_id or self.env.company)
            rec.gross_total = (rec.base_salary or 0.0) + (rec.incentive_bonus or 0.0) + (rec.decree_bonus or 0.0) + (rec.overtime or 0.0) + (rec.first_half_amount or 0.0)
            salary_for_social = rec.base_salary or 0.0
            rec.igss = salary_for_social * (params.igss_employee_rate / 100.0)
            rec.total_deductions = rec.igss + (rec.isr or 0.0) + (rec.advances or 0.0) + (rec.other_deductions or 0.0)
            rec.net_amount = rec.gross_total - rec.total_deductions
            rec.bono14_provision = salary_for_social * (params.bono14_rate / 100.0)
            rec.aguinaldo_provision = salary_for_social * (params.aguinaldo_rate / 100.0)
            rec.indemnity_provision = salary_for_social * (14.0 / 144.0)
            rec.employer_igss = salary_for_social * (params.igss_employer_rate / 100.0)
            rec.irtra = salary_for_social * (params.irtra_rate / 100.0)
            rec.intecap = salary_for_social * (params.intecap_rate / 100.0)
            rec.provision_total = rec.igss + rec.bono14_provision + rec.aguinaldo_provision + rec.indemnity_provision + rec.employer_igss + rec.irtra + rec.intecap
