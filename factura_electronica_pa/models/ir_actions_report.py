#-*- coding:utf-8 -*-

from odoo import models, fields, api

class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    use_in_electronic_invoice = fields.Boolean(string="Use in E-invoice", readonly=True)