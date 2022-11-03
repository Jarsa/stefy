# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountPaymentTerm(models.Model):
    ######################
    # Private attributes #
    ######################
    _inherit = "account.payment.term"

    ###################
    # Default methods #
    ###################

    ######################
    # Fields declaration #
    ######################

    ##############################
    # Compute and search methods #
    ##############################

    ############################
    # Constrains and onchanges #
    ############################

    #########################
    # CRUD method overrides #
    #########################

    ##################
    # Action methods #
    ##################

    ####################
    # Business methods #
    ####################
    def _get_timing(self):
        """Get payment term's timing. Used in Factura Electronica.
        1 - Immediate / 2 - Term / 3 - Mixed
        """
        self.ensure_one()

        first = self.line_ids[0]

        if first.days == 0:
            if first.value == "balance":
                return 1
            else:
                return 3
        return 2
