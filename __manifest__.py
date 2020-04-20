{
    'name': 'Return Order',
    'version': '1',
    'summary': 'Return Order Management',
    'description': 'manage customer return orders',
    'category': 'Operations',
    'author': 'Ahmed Maher',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['base', 'sale', 'contacts', 'account'],
    'data': [
        'security/return_secuirty.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/account_move_reversal.xml',
        'views/return_settings.xml',
        'views/return_reason.xml',
        'views/return_order.xml',
        'views/sale.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
