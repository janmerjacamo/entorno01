from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LocalizaGtSettlement(models.Model):
    _name = 'localiza.gt.settlement'
    _description = 'Liquidación Localiza Guatemala'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'exit_date desc, id desc'

    name = fields.Char(string='Referencia', default='Nueva liquidación', copy=False)
    company_id = fields.Many2one('res.company', string='Compañía', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True, tracking=True)
    contract_id = fields.Many2one('hr.contract', string='Contrato')
    dpi = fields.Char(string='DPI')
    job_name = fields.Char(string='Puesto')
    reason = fields.Selection([('dismissal', 'Despido'), ('resignation', 'Renuncia'), ('agreement', 'Mutuo acuerdo'), ('contract_end', 'Fin de contrato')], string='Motivo', default='dismissal')
    calculation_date = fields.Date(string='Fecha cálculo', default=fields.Date.context_today)
    entry_date = fields.Date(string='Fecha ingreso', required=True)
    exit_date = fields.Date(string='Fecha salida', required=True)
    total_days_worked = fields.Integer(string='Total días laborados', compute='_compute_dates', store=True)
    pending_days = fields.Float(string='Días pendientes de pago')
    pending_overtime = fields.Monetary(string='Horas extras pendientes', currency_field='currency_id')
    salary_history_ids = fields.One2many('localiza.gt.settlement.salary.history', 'settlement_id', string='Últimos salarios')
    average_salary = fields.Monetary(string='Promedio últimos 6 meses', compute='_compute_settlement', store=True, currency_field='currency_id')
    indemnity_salary = fields.Monetary(string='Salario para indemnización', compute='_compute_settlement', store=True, currency_field='currency_id', help='Promedio * 14 / 12 según formato Localiza.')
    pending_salary_amount = fields.Monetary(string='Salario pendiente', compute='_compute_settlement', store=True, currency_field='currency_id')
    indemnity_amount = fields.Monetary(string='Indemnización', compute='_compute_settlement', store=True, currency_field='currency_id')
    bono14_amount = fields.Monetary(string='Bono 14 proporcional', compute='_compute_settlement', store=True, currency_field='currency_id')
    aguinaldo_amount = fields.Monetary(string='Aguinaldo proporcional', compute='_compute_settlement', store=True, currency_field='currency_id')
    vacation_amount = fields.Monetary(string='Vacaciones proporcionales', compute='_compute_settlement', store=True, currency_field='currency_id')
    igss_deduction = fields.Monetary(string='(-) IGSS', compute='_compute_settlement', store=True, currency_field='currency_id')
    total_benefits = fields.Monetary(string='Total prestaciones', compute='_compute_settlement', store=True, currency_field='currency_id')
    net_amount = fields.Monetary(string='Líquido a recibir', compute='_compute_settlement', store=True, currency_field='currency_id')
    state = fields.Selection([('draft', 'Borrador'), ('computed', 'Calculada'), ('approved', 'Aprobada'), ('cancel', 'Cancelada')], default='draft', tracking=True)
    notes = fields.Text(string='Notas')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nueva liquidación') == 'Nueva liquidación':
                vals['name'] = self.env['ir.sequence'].next_by_code('localiza.gt.settlement') or 'Nueva liquidación'
        return super().create(vals_list)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for rec in self:
            emp = rec.employee_id
            if emp:
                rec.dpi = emp.localiza_dpi or emp.identification_id
                rec.job_name = emp.job_id.name or ''
                contract = self.env['hr.contract'].search([('employee_id', '=', emp.id), ('state', '=', 'open')], limit=1)
                rec.contract_id = contract.id
                if contract:
                    rec.entry_date = contract.date_start

    @api.depends('entry_date', 'exit_date')
    def _compute_dates(self):
        for rec in self:
            if rec.entry_date and rec.exit_date:
                rec.total_days_worked = (rec.exit_date - rec.entry_date).days + 1
            else:
                rec.total_days_worked = 0

    @api.depends('salary_history_ids.amount', 'pending_days', 'pending_overtime', 'entry_date', 'exit_date')
    def _compute_settlement(self):
        Param = self.env['localiza.gt.payroll.parameter']
        for rec in self:
            params = Param.get_company_parameter(rec.company_id or self.env.company)
            salaries = rec.salary_history_ids.mapped('amount')
            rec.average_salary = sum(salaries) / len(salaries) if salaries else 0.0
            rec.indemnity_salary = rec.average_salary * 14.0 / 12.0 if rec.average_salary else 0.0
            daily_salary = rec.average_salary / 30.0 if rec.average_salary else 0.0
            rec.pending_salary_amount = daily_salary * (rec.pending_days or 0.0)
            days_total = rec.total_days_worked or 0
            rec.indemnity_amount = (days_total * rec.indemnity_salary / 365.0) if rec.reason == 'dismissal' else 0.0
            rec.bono14_amount = days_total * rec.average_salary / 365.0 if rec.average_salary else 0.0
            rec.aguinaldo_amount = days_total * rec.average_salary / 365.0 if rec.average_salary else 0.0
            rec.vacation_amount = days_total * ((rec.average_salary / 2.0) / 365.0) if rec.average_salary else 0.0
            rec.igss_deduction = -abs((rec.pending_salary_amount + rec.pending_overtime) * (params.igss_employee_rate / 100.0))
            rec.total_benefits = rec.pending_salary_amount + rec.pending_overtime + rec.indemnity_amount + rec.bono14_amount + rec.aguinaldo_amount + rec.vacation_amount
            rec.net_amount = rec.total_benefits + rec.igss_deduction

    def action_load_last_six_months(self):
        for rec in self:
            if not rec.employee_id:
                raise UserError(_('Seleccione un empleado.'))
            rec.salary_history_ids.unlink()
            exit_date = rec.exit_date or fields.Date.context_today(self)
            lines = []
            # Busca recibos calculados/pagados de Odoo; si no encuentra, usa contrato actual.
            payslips = self.env['hr.payslip'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('date_to', '<=', exit_date),
                ('state', 'in', ['done', 'paid', 'verify']),
            ], order='date_to desc', limit=6)
            for slip in payslips:
                amount = 0.0
                for line in slip.line_ids:
                    if line.code in ('BASIC', 'BASICGT', 'SUELDO_BASE', 'GROSS'):
                        amount += line.total
                if not amount:
                    amount = slip.contract_id.wage or 0.0
                lines.append((0, 0, {'date': slip.date_to, 'amount': amount, 'source': 'payslip'}))
            if not lines:
                contract = rec.contract_id or self.env['hr.contract'].search([('employee_id', '=', rec.employee_id.id)], limit=1)
                wage = contract.wage if contract else 0.0
                for i in range(6):
                    month_date = exit_date - relativedelta(months=i)
                    lines.append((0, 0, {'date': month_date, 'amount': wage, 'source': 'contract'}))
            rec.salary_history_ids = lines
            rec.state = 'computed'

    def action_compute(self):
        self._compute_settlement()
        self.write({'state': 'computed'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def action_cancel(self):
        self.write({'state': 'cancel'})


class LocalizaGtSettlementSalaryHistory(models.Model):
    _name = 'localiza.gt.settlement.salary.history'
    _description = 'Historial salarial para liquidación'
    _order = 'date desc'

    settlement_id = fields.Many2one('localiza.gt.settlement', required=True, ondelete='cascade')
    date = fields.Date(string='Mes / fecha', required=True)
    amount = fields.Monetary(string='Salario', required=True, currency_field='currency_id')
    currency_id = fields.Many2one(related='settlement_id.currency_id', readonly=True)
    source = fields.Selection([('manual', 'Manual'), ('payslip', 'Recibo Odoo'), ('contract', 'Contrato')], default='manual', string='Origen')
