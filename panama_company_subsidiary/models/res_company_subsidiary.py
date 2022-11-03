# -*- coding: utf-8 -*-

import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResCompanySubsidiary(models.Model):
    ######################
    # Private attributes #
    ######################
    _inherit = "res.company.subsidiary"

    ###################
    # Default methods #
    ###################

    ######################
    # Fields declaration #
    ######################
    panama_district_id = fields.Many2one(
        comodel_name="panama_divisions.district")
    panama_corregimiento_id = fields.Many2one(
        comodel_name="panama_divisions.corregimiento")
    is_panama_country = fields.Boolean(compute="compute_is_panama_country",
                                       store=True)

    @api.onchange("panama_corregimiento_id")
    def onchange_panama_corregimiento_id(self):
        for partner in self:
            partner.zip = partner.panama_corregimiento_id.name

    @api.onchange("panama_district_id")
    def onchange_panama_district_id(self):
        for partner in self:
            partner.city = partner.panama_district_id.name

    @api.constrains("phone", "is_panama_country")
    def _check_phone_pa(self):
        for partner in self:
            if partner.is_panama_country:
                if not partner.phone:
                    raise ValidationError("Phone number must be set if country is Panama.")
                match = re.match(r"\b\d{3,4}\b\-\b\d{4}\b", partner.phone)
                if not match:
                    raise ValidationError(
                        "The given phone number is not valid for Panama. Valid formats are: 999-9999 or 9999-9999.")

    @api.depends("country_id", "country_id.code")
    def compute_is_panama_country(self):
        for partner in self:
            partner.is_panama_country = partner.country_id.code == "PA"

    def _validate_corregimiento(self):
        self.ensure_one()

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
