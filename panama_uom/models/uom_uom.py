# -*- coding: utf-8 -*-

from odoo import models, fields, api


class UoM(models.Model):
    ######################
    # Private attributes #
    ######################
    _inherit = "uom.uom"

    ###################
    # Default methods #
    ###################

    ######################
    # Fields declaration #
    ######################
    panama_uom_id = fields.Many2one(comodel_name="panama.uom",
                                    string="Panamanian UoM")
    panama_uom_code = fields.Char(string="Panamanian UoM Code",
                                  related="panama_uom_id.code")

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
