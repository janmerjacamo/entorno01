from odoo import fields, models
from .crm_lead import LOCALIZA_OWNER_SELECTION


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    localiza_opportunity_id = fields.Many2one('crm.lead', string='Oportunidad', index=True, ondelete='set null')
    localiza_partner_id = fields.Many2one('res.partner', string='Contacto/Cuenta', index=True)
    localiza_owner = fields.Selection(LOCALIZA_OWNER_SELECTION, string='Responsable del evento/tarea')
    localiza_task_type = fields.Selection([
        ('tarea', 'Tarea interna'),
        ('reunion', 'Reunión'),
        ('llamada', 'Llamada'),
        ('seguimiento', 'Seguimiento'),
    ], string='Tipo de evento/tarea', default='reunion')
    localiza_task_state = fields.Selection([
        ('no_iniciado', 'No iniciado'),
        ('en_proceso', 'En proceso'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ], string='Estado del evento/tarea', default='no_iniciado')
    localiza_priority = fields.Selection([
        ('bajo', 'Bajo'),
        ('normal', 'Normal'),
        ('alto', 'Alto'),
        ('urgente', 'Urgente'),
    ], string='Prioridad', default='alto')
    localiza_evidence = fields.Binary(string='Evidencia')
    localiza_evidence_filename = fields.Char(string='Nombre de evidencia')
