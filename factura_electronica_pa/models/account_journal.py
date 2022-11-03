# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    ######################
    # Private attributes #
    ######################
    _inherit = "account.journal"

    ###################
    # Default methods #
    ###################
    @api.model
    def _get_default_report_id(self):
        return self.env.ref('factura_electronica_pa.account_invoices_without_signed', False)

    ######################
    # Fields declaration #
    ######################
    used_in_electronic_invoicing = fields.Boolean(
        string="Electronic Invoicing")
    dPtoFacDF = fields.Char(string="Invoice Issuing Point",
                            size=3,
                            index=True)

    api_token = fields.Char(string="Factura Electronica API TOKEN")
    api_url = fields.Char(string="E-invoice API URL")
    template_id = fields.Many2one("ir.actions.report", string="E-Invoiced Signed Template",
                                  domain=[('report_type','=','qweb-pdf'), ("use_in_electronic_invoice", "=", True)], default=_get_default_report_id, required=True)
    ##############################
    # Compute and search methods #
    ##############################

    ############################
    # Constrains and onchanges #
    ############################
    @api.constrains("dPtoFacDF")
    def _check_dPtoFacDF(self):
        for journal in self:
            if journal.dPtoFacDF:
                if self.search([("dPtoFacDF", "=", journal.dPtoFacDF), ("id", "!=", journal.id)]):
                    raise ValidationError(
                        "The Invoice Issuing Point must be unique!")

    #########################
    # CRUD method overrides #
    #########################

    ##################
    # Action methods #
    ##################

    ####################
    # Business methods #
    ####################
