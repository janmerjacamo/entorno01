from odoo import fields, models

class LocalizaDashboard(models.Model):
    _name = 'localiza.dashboard'
    _description = 'Tablero analitico Localiza'

    name = fields.Char(default='Tablero Operativo')
    puestos_activos = fields.Integer(compute='_compute_kpis')
    articulos_total = fields.Integer(compute='_compute_kpis')
    gps_total = fields.Integer(compute='_compute_kpis')
    gps_instalados = fields.Integer(compute='_compute_kpis')
    asignaciones_mes = fields.Integer(compute='_compute_kpis')
    stock_bodega = fields.Integer(compute='_compute_kpis')
    pendientes = fields.Integer(compute='_compute_kpis')

    def _compute_kpis(self):
        today = fields.Date.context_today(self)
        month_start = today.replace(day=1)
        Puesto = self.env['localiza.puesto']
        Art = self.env['localiza.articulo']
        GPS = self.env['localiza.gps']
        Asig = self.env['localiza.asignacion']
        for rec in self:
            rec.puestos_activos = Puesto.search_count([('active','=',True)])
            rec.articulos_total = Art.search_count([])
            rec.gps_total = GPS.search_count([])
            rec.gps_instalados = GPS.search_count([('estado','=','instalado')])
            rec.asignaciones_mes = Asig.search_count([('fecha','>=',month_start)])
            rec.stock_bodega = Art.search_count([('estado','=','bodega')])
            rec.pendientes = Asig.search_count([('estado','=','borrador')])
