{
    "name": "Ficha de Empleado Guatemala",
    "version": "19.0.1.0.0",
    "summary": "Ficha fiscal, laboral y documental de empleados para Guatemala",
    "category": "Human Resources/Employees",
    "author": "XIM Power / Localiza",
    "depends": ["hr", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_employee_gt_views.xml",
        "data/hr_employee_gt_cron.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
