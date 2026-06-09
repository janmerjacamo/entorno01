from odoo import fields, models
from .crm_lead import LOCALIZA_OWNER_SELECTION


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    localiza_owner = fields.Selection(LOCALIZA_OWNER_SELECTION, string='Titular Localiza')
    localiza_priority = fields.Selection([
        ('0', 'Bajo'),
        ('1', 'Normal'),
        ('2', 'Alto'),
        ('3', 'Urgente'),
    ], string='Prioridad Localiza', default='2')
    localiza_state = fields.Selection([
        ('no_iniciado', 'No iniciado'),
        ('en_proceso', 'En proceso'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ], string='Estado de la tarea', default='no_iniciado')
