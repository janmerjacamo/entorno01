from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    localiza_dpi = fields.Char(string='DPI')
    localiza_igss_number = fields.Char(string='Número IGSS')
    localiza_nit = fields.Char(string='NIT')
    localiza_bank_account = fields.Char(string='Cuenta bancaria planilla')
    localiza_payroll_area = fields.Selection([
        ('administracion', 'Administración'),
        ('operaciones', 'Operaciones'),
        ('monitoreo', 'Monitoreo'),
        ('tecnicos', 'Técnicos'),
        ('seguridad', 'Agentes de Seguridad'),
    ], string='Área planilla Localiza')
