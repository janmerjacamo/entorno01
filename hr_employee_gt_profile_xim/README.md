# Ficha de Empleado Guatemala

Módulo para Odoo 19 que amplía la ficha del empleado con información fiscal, laboral, familiar, salud, estudios, referencias, experiencia laboral y documentos con fecha de vencimiento.

## Integración
- Hereda `hr.employee`.
- Usa campos estándar de Odoo cuando ya existen: empleado, departamento, puesto, fecha de nacimiento, estado civil, dirección, emergencia, hijos, jefe inmediato y fecha de ingreso.
- Crea campos propios con prefijo `gt_` solo para datos específicos de Guatemala/RRHH.
- Agrega modelos hijos para datos repetibles.

## Documentos con vencimiento
Incluye el modelo `hr.employee.gt.document` con fecha de emisión, vencimiento, estado, días para vencer y archivo adjunto.

Estados:
- Sin Vencimiento
- Vigente
- Por Vencer: 30 días o menos
- Vencido

Incluye una acción programada diaria que crea actividades para documentos por vencer.
