# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class AccountInvoiceSend(models.TransientModel):
    _inherit = 'account.invoice.send'

    is_electronic_invoice = fields.Boolean('E-invoice', default=False)
    is_all_electronic_invoice = fields.Boolean('E-invoice is Success', default=False)
    country_code = fields.Char(string="Country Code", readonly=True)

    def _print_document(self):
        action = super()._print_document()
        if self.country_code == 'PA' and all([move.factura_result_id.is_success, move.factura_result_id.apcon_id, move.cufe] for move in self.invoice_ids):
            action_signed = self.invoice_ids.action_electronic_invoice_print()
            action_signed.update({'close_on_report_download': True})
            return action_signed
        else:
            return action

    @api.onchange("is_electronic_invoice")
    def _check_payslip_deduction(self):
        default_template = self.env.ref(self._get_mail_template(), raise_if_not_found=False)
        if self.is_electronic_invoice:
            for move in self.invoice_ids:
                if not all([move.factura_result_id.is_success, move.factura_result_id.apcon_id, move.cufe]):
                    self.is_electronic_invoice = False
                    self.template_id = default_template.id
                    raise ValidationError("Electronic invoice is not yet successful on this move: %s" % move.name)
                else:
                    self.template_id = self.env.ref("factura_electronica_pa.email_template_electronic_invoice",
                                                        raise_if_not_found=False).id
        else:
            self.template_id = default_template.id

    def _get_mail_template(self):
        """
        :return: the correct mail template based on the current move type
        """
        return 'account.email_template_edi_invoice'
