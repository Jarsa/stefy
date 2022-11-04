# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductProduct(models.Model):
    ######################
    # Private attributes #
    ######################
    _inherit = "product.template"

    ###################
    # Default methods #
    ###################

    ######################
    # Fields declaration #
    ######################
    panama_goods_service_family_id = fields.Many2one(comodel_name="panama.goods.service.family",
                                                     string="Panama Goods and Service Family")
    panama_goods_service_segment_id = fields.Many2one(comodel_name="panama.goods.service.segment",
                                                      string="Panama Goods and Service Segment",
                                                      related="panama_goods_service_family_id.parent_id")

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
