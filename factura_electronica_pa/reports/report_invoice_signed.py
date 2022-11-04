# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from functools import lru_cache


class ReportInvoiceWithSigned(models.AbstractModel):
    _name = 'report.factura_electronica_pa.report_invoice_with_signed'
    _description = 'Account report with signed'
    _inherit = 'report.account.report_invoice_with_payments'

    @api.model
    def _get_report_values(self, docids, data=None):
        rslt = super()._get_report_values(docids, data)
        rslt['report_type'] = data.get('report_type') if data else ''
        for invoice in rslt['docs']:
            if invoice.company_id.country_id.code != "PA":
                raise ValidationError(_("This operation is restricted!"))
            if not all([invoice.factura_result_id.is_success, invoice.factura_result_id.apcon_id]):
                raise ValidationError("Electronic invoice is not yet successful for %s" % invoice.name)
        return rslt


class ReportInvoiceWithSignedTicket(models.AbstractModel):
    _name = 'report.factura_electronica_pa.report_ticket_with_signed'
    _description = 'Account report with signed'
    _inherit = 'report.account.report_invoice_with_payments'

    @api.model
    def _get_report_values(self, docids, data=None):
        rslt = super()._get_report_values(docids, data)
        rslt['report_type'] = data.get('report_type') if data else ''
        for invoice in rslt['docs']:
            if invoice.company_id.country_id.code != "PA":
                raise ValidationError(_("This operation is restricted!"))
            if not all([invoice.factura_result_id.is_success, invoice.factura_result_id.apcon_id]):
                raise ValidationError("Electronic invoice is not yet successful for %s" % invoice.name)
        return rslt


class ReportInvoiceWithSignedCustom(models.AbstractModel):
    _name = 'report.factura_electronica_pa.report_invoice_with_signed_2'
    _description = 'Account report with signed (oryu)'
    _inherit = 'report.account.report_invoice_with_payments'

    @api.model
    def _get_report_values(self, docids, data=None):
        rslt = super()._get_report_values(docids, data)
        rslt['report_type'] = data.get('report_type') if data else ''
        for invoice in rslt['docs']:
            if invoice.company_id.country_id.code != "PA":
                raise ValidationError(_("This operation is restricted!"))
            if not all([invoice.factura_result_id.is_success, invoice.factura_result_id.apcon_id]):
                raise ValidationError("Electronic invoice is not yet successful for %s" % invoice.name)
        return rslt