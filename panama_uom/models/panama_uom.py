# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PanamaUoM(models.Model):
    ######################
    # Private attributes #
    ######################
    _name = "panama.uom"

    ###################
    # Default methods #
    ###################

    ######################
    # Fields declaration #
    ######################
    name = fields.Char(required=True)
    code = fields.Char(required=True,
                       index=True)

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
