from odoo import fields, models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_localiza_operativo = fields.Boolean(string='Producto operativo Localiza')
    x_localiza_tipo = fields.Selection([
        ('uniforme', 'Uniforme'),
        ('bota', 'Bota'),
        ('insumo', 'Insumo'),
        ('gps', 'GPS'),
        ('equipo', 'Equipo'),
        ('otro', 'Otro'),
    ], string='Tipo operativo')
    x_localiza_talla = fields.Char(string='Talla')
    x_localiza_codigo_excel = fields.Char(string='Codigo Excel')
    x_localiza_ubicacion_texto = fields.Char(string='Ubicacion texto')
