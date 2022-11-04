# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    internal_note = fields.Text('Internal Note',
                                help="Note you can set through the customer statement about a receivable journal item")

    def get_stock_lot_ids(self):
        lot_ids = self.env["stock.production.lot"]
        if self.sale_line_ids:
            lot_ids = self.sale_line_ids.move_ids.move_line_ids.mapped("lot_id")
        return lot_ids