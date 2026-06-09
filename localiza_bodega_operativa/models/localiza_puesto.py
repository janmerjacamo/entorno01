from odoo import api, fields, models

class LocalizaPuesto(models.Model):
    _name = 'localiza.puesto'
    _description = 'Puesto operativo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Puesto', required=True, tracking=True)
    code = fields.Char(string='Codigo')
    tipo = fields.Selection([('capital','Capital'),('departamental','Departamental'),('bodega','Bodega'),('cliente','Cliente'),('otro','Otro')], default='capital', string='Tipo')
    partner_id = fields.Many2one('res.partner', string='Cliente / Empresa')
    responsible_id = fields.Many2one('res.partner', string='Responsable')
    address = fields.Char(string='Direccion')
    department = fields.Char(string='Departamento / Zona')
    agent_count = fields.Integer(string='Cantidad de agentes')
    active = fields.Boolean(default=True)
    notes = fields.Text(string='Notas')
    assignment_count = fields.Integer(compute='_compute_counts', string='Asignaciones')
    gps_count = fields.Integer(compute='_compute_counts', string='GPS')

    def _compute_counts(self):
        Assignment = self.env['localiza.asignacion']
        GPS = self.env['localiza.gps']
        for rec in self:
            rec.assignment_count = Assignment.search_count([('puesto_id','=',rec.id)])
            rec.gps_count = GPS.search_count([('puesto_id','=',rec.id)])
