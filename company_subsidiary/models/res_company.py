# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCompany(models.Model):
    ######################
    # Private attributes #
    ######################
    _inherit = "res.company"

    ###################
    # Default methods #
    ###################

    ######################
    # Fields declaration #
    ######################
    subsidiary_ids = fields.One2many(comodel_name="res.company.subsidiary",
                                     inverse_name="company_id",
                                     string="Subsidiaries")

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
