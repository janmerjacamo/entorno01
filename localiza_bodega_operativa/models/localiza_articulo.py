from odoo import api, fields, models

class LocalizaArticulo(models.Model):
    _name = 'localiza.articulo'
    _description = 'Articulo operativo de bodega'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'categoria, subcategoria, name'

    name = fields.Char(string='Articulo', required=True, tracking=True)
    codigo = fields.Char(string='Referencia interna', index=True)
    product_id = fields.Many2one('product.product', string='Producto Odoo')
    categoria = fields.Selection([
        ('uniforme','Uniforme'),('bota','Bota'),('insumo','Insumo'),('gps','GPS'),('equipo','Equipo'),('otro','Otro')
    ], string='Categoria', default='insumo', required=True, tracking=True)
    subcategoria = fields.Char(string='Subcategoria')
    talla = fields.Char(string='Talla')
    serie = fields.Char(string='Serie / Codigo')
    factura = fields.Char(string='No. factura')
    fecha_ingreso = fields.Date(string='Fecha ingreso')
    proveedor = fields.Char(string='Proveedor')
    costo = fields.Float(string='Costo')
    ubicacion_texto = fields.Char(string='Ubicacion original')
    puesto_id = fields.Many2one('localiza.puesto', string='Puesto / ubicacion')
    cantidad = fields.Float(string='Cantidad', default=1.0)
    estado = fields.Selection([
        ('bodega','En bodega'),('asignado','Asignado'),('devuelto','Devuelto'),('baja','Baja'),('perdido','Perdido'),('danado','Dañado')
    ], string='Estado', default='bodega', tracking=True)
    notes = fields.Text(string='Notas')

    _sql_constraints = [
        ('codigo_unique', 'unique(codigo)', 'La referencia interna ya existe.'),
    ]

    def action_create_product(self):
        ProductTemplate = self.env['product.template']
        Category = self.env['product.category']
        for rec in self:
            if rec.product_id:
                continue
            categ = Category.search([('name','=',rec.categoria.capitalize())], limit=1)
            if not categ:
                categ = Category.create({'name': rec.categoria.capitalize()})
            tmpl = ProductTemplate.create({
                'name': rec.name,
                'default_code': rec.codigo,
                'standard_price': rec.costo or 0.0,
                'categ_id': categ.id,
                'x_localiza_operativo': True,
                'x_localiza_tipo': rec.categoria,
                'x_localiza_talla': rec.talla,
                'x_localiza_codigo_excel': rec.codigo,
                'x_localiza_ubicacion_texto': rec.ubicacion_texto,
            })
            rec.product_id = tmpl.product_variant_id.id
