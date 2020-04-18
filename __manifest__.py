{
    'name': 'Return Order',
    'version': '1',
    'summary': 'Return Order Management',
    'description': 'manage customer return orders',
    'category': 'Operations',
    'author': 'Ahmed Maher',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/return_settings.xml',
        'views/return_order.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
