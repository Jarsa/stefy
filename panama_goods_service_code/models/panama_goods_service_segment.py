# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PanamaGoodsServiceSegment(models.Model):
    ######################
    # Private attributes #
    ######################
    _name = "panama.goods.service.segment"
    _description = "Panama Goods and Services Segment"

    ###################
    # Default methods #
    ###################

    ######################
    # Fields declaration #
    ######################
    name = fields.Char(required=True)
    code = fields.Char(index=True,
                       required=True)
    child_ids = fields.One2many(comodel_name="panama.goods.service.family",
                                inverse_name="parent_id",
                                string="Families")

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
