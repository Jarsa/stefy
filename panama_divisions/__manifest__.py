# -*- coding: utf-8 -*-
{
    'name': "Provincias - Distritos - Corregimientos (Panama Division)",

    'summary': """Provincias - Distritos - Corregimientos (Panama Division)""",

    'description': """Provincias - Distritos - Corregimientos (Panama Division)""",

    'author': "Eduweb Group",
    'website': "https://www.eduwebgroup.com",

    'category': 'Technical',
    'version': '1.0.1',

    'depends': ['base'],
    'images': [
        'static/description/images/description.gif'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/inherited/res_partner_views.xml',
        
        'data/res.country.state.csv',
        'data/panama_divisions.district.csv',
        'data/panama_divisions.corregimiento.csv',
    ],

    'currency': 'USD',
    'license': 'OPL-1',
    'price': 50
}
