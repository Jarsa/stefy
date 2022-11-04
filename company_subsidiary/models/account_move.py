# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    ######################
    # Private attributes #
    ######################
    _inherit = "account.move"

    ###################
    # Default methods #
    ###################

    ######################
    # Fields declaration #
    ######################
    company_subsidiary_id = fields.Many2one(comodel_name="res.company.subsidiary",
                                            related="journal_id.company_subsidiary_id")

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
