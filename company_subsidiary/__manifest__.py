# -*- coding: utf-8 -*-
{
    "name": "Company Subsidiary",
    "summary": """Company Subsidiary""",
    "description": """
        Company Subsidiary
    """,
    "author": "Eduweb Group",
    "website": "https://www.eduwebgroup.com",
    "category": "Extra Tools",
    "version": "1.0",
    "depends": [
        "account",
        "base",
        "base_geolocalize",
        "hr"
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_company_views.xml",
        "views/res_company_subsidiary_views.xml",
        "views/account_journal_views.xml",
        "views/hr_employee_views.xml"
    ],
    'price': 50,
    'currency': 'USD',
    'license': 'OPL-1',
}
