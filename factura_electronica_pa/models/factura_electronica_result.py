# -*- coding: utf-8 -*-

import base64

from odoo import models, fields, api
import json

class FacturaElectronicaResult(models.Model):
    ######################
    # Private attributes #
    ######################
    _name = "factura.electronica.result"

    ###################
    # Default methods #
    ###################

    ######################
    # Fields declaration #
    ######################
    move_id = fields.Many2one(comodel_name="account.move",
                              string="Account Move",
                              readonly=True)
    apcon_id = fields.Char(string="APCON ID",
                           readonly=True)
    name = fields.Char(related="move_id.name")
    payload = fields.Text(string="Request Payload",
                          readonly=True)
    result = fields.Text(string="Response Result",
                         readonly=True)
    signed_xml = fields.Text(string="Signed XML",
                             help="Encoded into Base64 format.",
                             readonly=True)
    date = fields.Datetime(readonly=True,
                           default=lambda _: fields.Datetime.now())
    error_message = fields.Char(readonly=True)
    is_success = fields.Boolean(compute="_compute_is_success",
                                store=True)
    is_success_with_error_message = fields.Boolean(compute="_compute_success_with_error",
                                store=True)

    ##############################
    # Compute and search methods #
    ##############################
    @api.depends("error_message", "result")
    def _compute_is_success(self):
        for result_id in self:
            if not result_id.result:
                return False
            response = json.loads(result_id.result)
            if "message" in response and response['message'] is not None and "status" in response['message']:
                if response['status'] == "Success" and response['message']['status'] == "Autorizado":
                    result_id.is_success = True
                else:
                    result_id.is_success = False
            else:
                result_id.is_success = False

    @api.depends("is_success", "error_message")
    def _compute_success_with_error(self):
        for response in self:
            if response.is_success and response.error_message:
                response.is_success_with_error_message = True
            else:
                response.is_success_with_error_message = False

    ############################
    # Constrains and onchanges #
    ############################

    #########################
    # CRUD method overrides #
    #########################

    ##################
    # Action methods #
    ##################
    def action_download_signed_xml(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_url",
            "url": "/factura_electronica_pa/signed_xml/%s" % self.id,
            "target": "new"
        }

    ####################
    # Business methods #
    ####################
