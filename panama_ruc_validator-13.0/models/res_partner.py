# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.addons.panama_ruc_validator.ruc_calculator import ruc


class ResPartner(models.Model):
    _inherit = "res.partner"

    recipient_type = fields.Selection(
        selection=[('1', "Contribuyente"), ('2', "Consumidor final")
            , ('3', "Gobierno"), ('4', "extranjero")], string="iTipoRec")

    @api.constrains("vat", "country_id")
    def _check_vat_dv(self):
        for record in self.filtered(lambda x: x.vat and x.country_id.code == "PA" and x.recipient_type in ['1','3']):
            ruc_dv = self._get_ruc_dv(record.vat)
            if ruc.calculateDV(ruc_dv["ruc"]) != ruc_dv["dv"]:
                raise UserError("RUC/DV is invalid")

    @api.model
    def _get_ruc_dv(self, vat):
        dictionary = {
            "ruc": "",
            "dv": ""
        }

        if vat:
            ruc = vat.upper().replace(" ", "")
            lst = ruc.split("DV")

            if len(lst) != 2:
                raise UserError("Invalid format for RUC/DV")

            dictionary["ruc"] = lst[0]
            dictionary["dv"] = lst[1]

        return dictionary
