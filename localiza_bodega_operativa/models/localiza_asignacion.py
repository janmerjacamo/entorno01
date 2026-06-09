from odoo import api, fields, models

class LocalizaAsignacion(models.Model):
    _name = 'localiza.asignacion'
    _description = 'Asignacion operativa de bodega'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc, id desc'

    name = fields.Char(string='Referencia', default='Nuevo', copy=False, readonly=True)
    fecha = fields.Date(string='Fecha', default=fields.Date.context_today, required=True)
    tipo = fields.Selection([('entrega','Entrega'),('devolucion','Devolucion'),('traslado','Traslado'),('baja','Baja')], default='entrega', required=True, tracking=True)
    receptor = fields.Char(string='Receptor')
    dpi = fields.Char(string='DPI / Identificacion')
    employee_id = fields.Many2one('hr.employee', string='Empleado')
    partner_id = fields.Many2one('res.partner', string='Contacto')
    puesto_id = fields.Many2one('localiza.puesto', string='Puesto destino')
    articulo_id = fields.Many2one('localiza.articulo', string='Articulo')
    gps_id = fields.Many2one('localiza.gps', string='GPS')
    product_id = fields.Many2one('product.product', string='Producto')
    cantidad = fields.Float(string='Cantidad', default=1.0)
    talla = fields.Char(string='Talla')
    serie = fields.Char(string='Serie / IMEI')
    estado = fields.Selection([('borrador','Borrador'),('confirmado','Confirmado'),('cancelado','Cancelado')], default='borrador', tracking=True)
    observacion = fields.Text(string='Observacion')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('localiza.asignacion') or 'Nuevo'
        return super().create(vals_list)

    def action_confirmar(self):
        for rec in self:
            rec.estado = 'confirmado'
            if rec.articulo_id:
                rec.articulo_id.estado = 'asignado' if rec.tipo in ('entrega','traslado') else 'devuelto'
                if rec.puesto_id:
                    rec.articulo_id.puesto_id = rec.puesto_id.id
            if rec.gps_id:
                rec.gps_id.estado = 'instalado' if rec.tipo in ('entrega','traslado') else 'retiro'
                if rec.puesto_id:
                    rec.gps_id.puesto_id = rec.puesto_id.id
        return True

    def action_cancelar(self):
        self.write({'estado': 'cancelado'})
        return True
