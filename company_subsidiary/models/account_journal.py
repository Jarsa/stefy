# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountJournal(models.Model):
    ######################
    # Private attributes #
    ######################
    _inherit = "account.journal"

    ###################
    # Default methods #
    ###################

    ######################
    # Fields declaration #
    ######################
    company_subsidiary_id = fields.Many2one(comodel_name="res.company.subsidiary",
                                            domain="[('company_id', '=', company_id)]",
                                            string="Subsidiary")

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
