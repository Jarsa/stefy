# -*- coding: utf-8 -*-
{
    "name": "Factura Electrónica Panamá (Panama E-Invoice)",
    "summary": """Factura Electrónica Panamá (Panama E-Invoice)""",
    "description": """
        Factura Electrónica Panamá (Panama E-Invoice)
    """,
    "author": "Eduweb Group",
    "website": "https://www.eduwebgroup.com",
    "category": "Invoicing & Payments",
    "version": "1.1",
    "depends": [
        "account",
        "web",
        "panama_divisions",
        "panama_company_subsidiary",
        "panama_goods_service_code",
        "panama_uom",
        "panama_ruc_validator",
    ],
    'images': [
        'static/description/images/description.gif',
        'static/description/images/ElecInvoice.png',
        'static/description/images/EnvioCAFE.png'
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence.xml",
        "data/paperformat_data.xml",
        "views/account_move_views.xml",
        "views/account_journal_views.xml",
        "views/account_invoice_send_views.xml",
        "views/factura_electronica_result_views.xml",
        "views/ir_actions_report.xml",
        "views/layout_views.xml",
        "reports/tax_breakdown_template.xml",
        "reports/report_invoice_signed.xml",
        "reports/report_invoice_signed_common.xml",
        "reports/report_ticket_signed.xml",
        "reports/custom_report_electronic_invoice_signed.xml",
        "views/invoice_signed_email_template.xml",
    ],
    'price': 200,
    'currency': 'USD',
    'license': 'OPL-1',
}
