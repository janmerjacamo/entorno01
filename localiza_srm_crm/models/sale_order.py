from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    localiza_sale_modality = fields.Selection([('renta', 'Renta'), ('venta', 'Venta')], string='Modalidad')
    localiza_payment_type = fields.Selection([('contado', 'Contado'), ('credito', 'Crédito')], string='Forma de pago')
