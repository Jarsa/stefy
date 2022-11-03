# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ReportInvoiceWithSignedCommon(models.AbstractModel):
    _name = 'report.factura_electronica_pa.report_invoice_with_signed_common'
    _description = 'Account report with signed (common)'
    _inherit = 'report.account.report_invoice'

    @api.model
    def _get_report_values(self, docids, data=None):
        result = super()._get_report_values(docids, data)
        result['report_type'] = data.get('report_type') if data else ''
        for invoice in result['docs']:
            if not all([invoice.factura_result_id.is_success, invoice.factura_result_id.apcon_id]):
                raise ValidationError("Electronic invoice is not yet successful for %s!" % invoice.name)
        return result