# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PanamaGoodsServiceFamily(models.Model):
    ######################
    # Private attributes #
    ######################
    _name = "panama.goods.service.family"
    _description = "Panama Goods and Services Family"

    ###################
    # Default methods #
    ###################

    ######################
    # Fields declaration #
    ######################
    parent_id = fields.Many2one(comodel_name="panama.goods.service.segment",
                                string="Segment")
    name = fields.Char(required=True)
    code = fields.Char(index=True,
                       required=True)

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
