# -*- coding: utf-8 -*-
{
    'name': 'Localiza Bodega - Formularios Operativos',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Formularios operativos imprimibles para bodega, puestos, instalaciones e inventario físico.',
    'author': 'XIM Power / Localiza',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'product',
        'stock',
        'localiza_bodega_operativa',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/localiza_operational_form_views.xml',
        'views/localiza_form_menus.xml',
        'report/report_actions.xml',
        'report/report_operational_form.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
