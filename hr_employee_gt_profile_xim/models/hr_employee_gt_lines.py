from datetime import timedelta

from odoo import api, fields, models


class HrEmployeeGtExperience(models.Model):
    _name = "hr.employee.gt.experience"
    _description = "Experiencia Laboral Guatemala"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    employee_id = fields.Many2one("hr.employee", string="Empleado", required=True, ondelete="cascade")
    company_name = fields.Char(string="Nombre de Empresa", required=True)
    position = fields.Char(string="Puesto que Ocupaba")
    time_worked = fields.Char(string="Tiempo Laborado")
    salary = fields.Float(string="Salario")
    leaving_reason = fields.Char(string="Motivo de Retiro")
    immediate_boss = fields.Char(string="Jefe Inmediato")
    company_phone = fields.Char(string="Teléfono de la Empresa")
    can_request_reference = fields.Selection([
        ("yes", "Sí"),
        ("no", "No"),
    ], string="¿Se Puede Pedir Referencias?")


class HrEmployeeGtReference(models.Model):
    _name = "hr.employee.gt.reference"
    _description = "Referencia Personal Guatemala"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    employee_id = fields.Many2one("hr.employee", string="Empleado", required=True, ondelete="cascade")
    name = fields.Char(string="Nombre", required=True)
    phone = fields.Char(string="Teléfono")
    relationship = fields.Char(string="Parentesco")


class HrEmployeeGtEducation(models.Model):
    _name = "hr.employee.gt.education"
    _description = "Estudio Guatemala"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    employee_id = fields.Many2one("hr.employee", string="Empleado", required=True, ondelete="cascade")
    degree = fields.Char(string="Título Obtenido", required=True)
    year = fields.Char(string="Año")
    institution = fields.Char(string="Institución")
    currently_studying = fields.Boolean(string="Estudia Actualmente")
    schedule = fields.Char(string="Indicar Horario")


class HrEmployeeGtTechnicalStudy(models.Model):
    _name = "hr.employee.gt.technical.study"
    _description = "Estudio Técnico Guatemala"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    employee_id = fields.Many2one("hr.employee", string="Empleado", required=True, ondelete="cascade")
    technical_study = fields.Char(string="Estudio Técnico")
    degree = fields.Char(string="Título Obtenido", required=True)
    year = fields.Char(string="Año")
    institution = fields.Char(string="Institución")


class HrEmployeeGtDocument(models.Model):
    _name = "hr.employee.gt.document"
    _description = "Documento de Empleado Guatemala"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "expiration_date asc, id"

    employee_id = fields.Many2one("hr.employee", string="Empleado", required=True, ondelete="cascade", tracking=True)
    document_type = fields.Selection([
        ("vaccination_card", "Carné de Vacunas"),
        ("lung_card", "Tarjeta de Pulmones"),
        ("fingerprints", "Huellas"),
        ("document_acknowledgment", "Reconocimiento de Documentos"),
        ("authorized_contract", "Contrato de Trabajo Autorizado"),
        ("dpi", "DPI"),
        ("driver_license", "Licencia de Conducir"),
        ("igss", "Afiliación al IGSS"),
        ("police_record", "Antecedentes Policíacos"),
        ("criminal_record", "Antecedentes Penales"),
        ("health_card", "Tarjeta de Salud"),
        ("lung_certificate", "Tarjeta de Pulmones"),
        ("medical_certificate", "Certificado Médico"),
        ("ornato", "Boleto de Ornato"),
        ("digessp", "Credencial DIGESSP"),
        ("nasp", "NASP"),
        ("birth_certificate", "Certificado de Nacimiento"),
        ("other", "Otro"),
    ], string="Tipo de Documento", required=True, tracking=True)
    name = fields.Char(string="Nombre / Descripción")
    issue_date = fields.Date(string="Fecha de Emisión")
    expiration_date = fields.Date(string="Fecha de Vencimiento", tracking=True)
    days_to_expire = fields.Integer(string="Días para Vencer", compute="_compute_expiration", store=True)
    expiration_state = fields.Selection([
        ("no_date", "Sin Vencimiento"),
        ("valid", "Vigente"),
        ("warning", "Por Vencer"),
        ("expired", "Vencido"),
    ], string="Estado", compute="_compute_expiration", store=True)
    attachment = fields.Binary(string="Archivo", attachment=True)
    attachment_filename = fields.Char(string="Nombre del Archivo")
    notes = fields.Text(string="Observaciones")

    @api.depends("expiration_date")
    def _compute_expiration(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if not rec.expiration_date:
                rec.days_to_expire = 0
                rec.expiration_state = "no_date"
                continue
            delta = (rec.expiration_date - today).days
            rec.days_to_expire = delta
            if delta < 0:
                rec.expiration_state = "expired"
            elif delta <= 30:
                rec.expiration_state = "warning"
            else:
                rec.expiration_state = "valid"

    def action_create_expiration_activity(self):
        activity_type = self.env.ref("mail.mail_activity_data_todo", raise_if_not_found=False)
        for document in self:
            if not document.employee_id or not activity_type:
                continue
            user = document.employee_id.parent_id.user_id or document.employee_id.coach_id.user_id or self.env.user
            summary = "Documento de empleado por vencer"
            note = "El documento %s del empleado %s vence el %s." % (
                dict(document._fields["document_type"].selection).get(document.document_type),
                document.employee_id.name,
                document.expiration_date or "sin fecha",
            )
            document.activity_schedule(
                activity_type_id=activity_type.id,
                summary=summary,
                note=note,
                user_id=user.id,
                date_deadline=document.expiration_date or fields.Date.context_today(document),
            )

    @api.model
    def _cron_check_expiring_documents(self):
        today = fields.Date.context_today(self)
        limit_date = today + timedelta(days=30)
        docs = self.search([
            ("expiration_date", "!=", False),
            ("expiration_date", ">=", today),
            ("expiration_date", "<=", limit_date),
            ("expiration_state", "=", "warning"),
        ])
        docs.action_create_expiration_activity()
