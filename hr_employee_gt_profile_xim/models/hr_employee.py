from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # ------------------------------------------------------------------
    # Datos personales Guatemala - campos que no cubre Odoo estándar
    # ------------------------------------------------------------------
    gt_home_phone = fields.Char(string="Teléfono de Casa")
    gt_age = fields.Integer(string="Edad", compute="_compute_gt_age", store=True)
    gt_dpi = fields.Char(string="DPI")
    gt_dpi_extended_place = fields.Char(string="Extendido en")
    gt_nit = fields.Char(string="NIT")
    gt_igss_number = fields.Char(string="Afiliación al IGSS")
    gt_residence_municipality = fields.Char(string="Municipio de Residencia")
    gt_residence_department = fields.Char(string="Departamento de Residencia")
    gt_housing_type = fields.Selection([
        ("own", "Propio"),
        ("rented", "Alquilado"),
        ("family", "Familiar"),
    ], string="Donde Vive Es")
    gt_residence_time = fields.Char(string="Tiempo de Vivir Allí")
    gt_has_other_income = fields.Boolean(string="Posee Otros Ingresos")
    gt_other_income_notes = fields.Char(string="Detalle de Otros Ingresos")
    gt_has_vehicle = fields.Boolean(string="Posee Vehículo")
    gt_vehicle_type = fields.Char(string="Tipo de Vehículo")
    gt_vehicle_brand = fields.Char(string="Marca de Vehículo")
    gt_has_debts = fields.Boolean(string="Posee Deudas")
    gt_debt_amount = fields.Float(string="Monto de Deuda")
    gt_full_address = fields.Char(string="Dirección / Domicilio")
    gt_address_notes = fields.Text(string="Direcciones / Referencias")

    # ------------------------------------------------------------------
    # Datos familiares
    # ------------------------------------------------------------------
    gt_father_name = fields.Char(string="Nombre del Padre")
    gt_father_phone = fields.Char(string="Teléfono del Padre")
    gt_mother_name = fields.Char(string="Nombre de la Madre")
    gt_mother_phone = fields.Char(string="Teléfono de la Madre")
    gt_spouse_phone = fields.Char(string="Teléfono del Cónyuge")
    gt_spouse_address = fields.Char(string="Dirección del Cónyuge")
    gt_siblings_count = fields.Integer(string="Número de Hermanos")

    # ------------------------------------------------------------------
    # Salud
    # ------------------------------------------------------------------
    gt_smokes = fields.Boolean(string="Fuma")
    gt_drinks = fields.Boolean(string="Bebe")
    gt_sports = fields.Boolean(string="Realiza Actividades Deportivas")
    gt_weight = fields.Float(string="Peso")
    gt_height = fields.Float(string="Altura")
    gt_disabilities = fields.Text(string="Impedimentos")
    gt_disease = fields.Text(string="Padece Alguna Enfermedad")
    gt_medication = fields.Text(string="Toma Algún Medicamento")
    gt_blood_type = fields.Selection([
        ("A+", "A+"), ("A-", "A-"),
        ("B+", "B+"), ("B-", "B-"),
        ("AB+", "AB+"), ("AB-", "AB-"),
        ("O+", "O+"), ("O-", "O-"),
    ], string="Tipo de Sangre")

    # ------------------------------------------------------------------
    # Trabajo / asignación operativa
    # ------------------------------------------------------------------
    gt_service_position_name = fields.Char(string="Nombre del Puesto de Servicio")
    gt_entry_date = fields.Date(string="Fecha de Ingreso")
    gt_reentry_date = fields.Date(string="Fecha de Reingreso")
    gt_service_address = fields.Char(string="Dirección del Puesto")
    gt_assigned_department = fields.Char(string="Departamento Asignado")
    gt_position_change_date = fields.Date(string="Fecha de Cambio de Puesto")
    gt_new_position_name = fields.Char(string="Nombre del Puesto Nuevo")
    gt_current_salary = fields.Monetary(string="Salario", currency_field="gt_currency_id")
    gt_currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        related="company_id.currency_id",
        readonly=True,
        store=True,
    )
    gt_contract_condition = fields.Selection([
        ("contract", "Contrato"),
        ("fixed", "Fijo"),
        ("temporary", "Temporal"),
    ], string="Condiciones")
    gt_benefits = fields.Selection([
        ("none", "Sin Prestaciones"),
        ("full", "Completas"),
        ("half", "50%"),
    ], string="Prestaciones")

    # ------------------------------------------------------------------
    # Líneas repetibles
    # ------------------------------------------------------------------
    gt_experience_ids = fields.One2many(
        "hr.employee.gt.experience", "employee_id", string="Experiencia Laboral"
    )
    gt_reference_ids = fields.One2many(
        "hr.employee.gt.reference", "employee_id", string="Referencias Personales"
    )
    gt_education_ids = fields.One2many(
        "hr.employee.gt.education", "employee_id", string="Estudios"
    )
    gt_technical_study_ids = fields.One2many(
        "hr.employee.gt.technical.study", "employee_id", string="Estudios Técnicos"
    )
    gt_document_ids = fields.One2many(
        "hr.employee.gt.document", "employee_id", string="Documentos Guatemala"
    )

    @api.depends("birthday")
    def _compute_gt_age(self):
        today = fields.Date.context_today(self)
        for employee in self:
            employee.gt_age = relativedelta(today, employee.birthday).years if employee.birthday else 0
