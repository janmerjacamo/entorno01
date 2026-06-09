from odoo import fields, models

class LocalizaGPS(models.Model):
    _name = 'localiza.gps'
    _description = 'Equipo GPS operativo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'imei'

    name = fields.Char(string='Nombre', compute='_compute_name', store=True)
    imei = fields.Char(string='IMEI', required=True, index=True, tracking=True)
    modelo = fields.Char(string='Modelo')
    marca = fields.Char(string='Marca')
    fecha_compra = fields.Date(string='Fecha compra')
    proveedor = fields.Char(string='Proveedor')
    factura = fields.Char(string='No. factura')
    serie = fields.Char(string='No. serie')
    precio = fields.Float(string='Precio unidad')
    iva = fields.Float(string='IVA')
    placa = fields.Char(string='Placa')
    cliente = fields.Char(string='Cliente')
    partner_id = fields.Many2one('res.partner', string='Cliente Odoo')
    puesto_id = fields.Many2one('localiza.puesto', string='Puesto / Ubicacion')
    product_id = fields.Many2one('product.product', string='Producto Odoo')
    estado = fields.Selection([
        ('bodega','En bodega'),('instalado','Instalado'),('retiro','Retirado'),('mantenimiento','Mantenimiento'),('danado','Dañado'),('baja','Baja')
    ], default='bodega', string='Estado', tracking=True)
    notes = fields.Text(string='Notas')

    _sql_constraints = [('imei_unique','unique(imei)','El IMEI ya existe.')]

    def _compute_name(self):
        for rec in self:
            rec.name = '%s / %s' % (rec.imei or 'GPS', rec.modelo or '')
