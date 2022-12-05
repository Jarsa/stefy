# -*- coding: utf-8 -*-

import base64
import json as jsonlib
import datetime
import logging
import re

from collections import defaultdict
from functools import reduce
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

from odoo.addons.factura_electronica_pa.constants import PA_COUNTRY_CATALOG

import requests
from werkzeug.urls import url_join

import xml.etree.ElementTree as ET
import io

_logger = logging.getLogger(__name__)


def date_to_iso8601(dt: datetime.date):
    dtime = datetime.datetime(
        year=dt.year, month=dt.month, day=dt.day, hour=5)
    return dtime.replace(tzinfo=datetime.timezone.utc, microsecond=0).isoformat()


def to_2_decimal_place(value: float):
    return "{:.2f}".format(value)


class AccountMove(models.Model):
    ######################
    # Private attributes #
    ######################
    _inherit = "account.move"

    ###################
    # Default methods #
    ###################

    ######################
    # Fields declaration #
    ######################
    used_in_electronic_invoicing = fields.Boolean(
        related="journal_id.used_in_electronic_invoicing")
    iDoc = fields.Selection(selection=[("1", "Internal operation Invoice"),
                                       ("2", "Import Invoice"),
                                       ("3", "Export Invoice"),
                                       ("4", "Credit Note Related with One or Several Invoices"),
                                       ("5", "Debit Note Related with One or Several Invoices"),
                                       ("6", "Generic Credit Note"),
                                       ("7", "Generic Debit Note"),
                                       ("8", "Free Zone Invoice"),
                                       ("9", "Reimbursement")],
                            string="Document Type",
                            compute="_compute_iDoc",
                            readonly=False)
    electronic_invoice_response = fields.Selection(selection=[("draft", "Draft"),
                                                              ("success", "Success"),
                                                              ("failed", "Attempted (error)"),
                                                              ("success_error", "Autorizado with Error")],
                                                   compute='_compute_electronic_invoice_response',
                                                   default='draft',
                                                   string="E-invoice Response" )
    electronic_invoice_message = fields.Char(string="E-invoice Message", compute='_compute_electronic_invoice_response',
                                             default="Not yet Send E-invoice")
    electronic_invoice_sign = fields.Selection(selection=[("draft", "X"),
                                                          ("success", "V"),
                                                          ("failed", "O"),
                                                          ("success_error", "0")],
                                                          related='electronic_invoice_response',
                                                          string="E-invoice Response", store=True)

    iNatOp = fields.Selection(selection=[("01", "Sale"),
                                         ("02", "Export"),
                                         ("10", "Transfer"),
                                         ("11", "Return"),
                                         ("12", "Consign"),
                                         ("13", "Remittance"),
                                         ("14", "Free Delivery"),
                                         ("20", "Purchase"),
                                         ("21", "Import")],
                              string="Nature of Transaction",
                              default="01")
    iTipoOp = fields.Selection(selection=[("1", "Sale"),
                                          ("2", "Purchase")],
                               string="Transaction Type",
                               default="1")
    iDest = fields.Selection(selection=[("1", "Panama"),
                                        ("2", "Abroad")],
                             string="Destination",
                             compute="_compute_iDest")
    iTipoTranVenta = fields.Selection(selection=[("1", "Business Operation"),
                                                 ("2", "Fixed Asset"),
                                                 ("3", "Real Estate"),
                                                 ("4", "Service")],
                                      string="Type of Sale Operation",
                                      compute="_compute_iTipoTranVenta",
                                      readonly=False)

    dNroDF = fields.Char(string="dNroDF",copy=False,)
    factura_result_id = fields.Many2one('factura.electronica.result', string="Factura Result", copy=False)
    factura_result_ids = fields.One2many('factura.electronica.result', 'move_id', string="Factura Result")
    qr_code = fields.Char(copy=False, string="QR Code Values", compute="_get_signed_xml_values", store=True)
    dFecProc = fields.Char(copy=False, string="Invoice Signed Date", compute='_get_signed_xml_values', store=True)
    cufe = fields.Char(copy=False, string="CUFE", store=True, compute='_get_signed_xml_values')
    total_product_qty = fields.Float(string="Total Qty", compute='_get_invoice_line_values', store=True)
    dFechaEm = fields.Char(string="dFechaEm", compute="_get_fechaem")
    monto_exento = fields.Float(compute='_get_invoice_line_values', string="Monto Exento")
    monto_gravado = fields.Float(compute='_get_invoice_line_values', string="Monto Gravado")
    total_discount = fields.Float(compute='_get_invoice_line_values', string="Total Discount")
    country_code = fields.Char(related="company_id.country_id.code", readonly=True)

    ##############################
    # Compute and search methods #
    ##############################
    @api.model
    def create(self, values):
        res = super(AccountMove, self).create(values)
        for rec in res:
            if rec.journal_id and rec.journal_id.used_in_electronic_invoicing:
                next_order = self.env['ir.sequence'].next_by_code('sequence.factura.electronica')
                rec.dNroDF = next_order
        return res

    @api.depends("invoice_date")
    def _get_fechaem(self):
        for invoice in self:
            if invoice.invoice_date:
                time = str(date_to_iso8601(invoice.invoice_date)).split('T')
                correct_time = time[1].split('+')
                invoice.dFechaEm = correct_time[0]

    @api.depends("invoice_line_ids", "name")
    def _get_invoice_line_values(self):
        total_qty = 0.00
        total_gravado = 0.00
        total_exento = 0.00
        total_discount = 0.00
        for order in self:
            for line in order.invoice_line_ids:
                total_qty += line.quantity
                if line.price_unit < 0:
                    total_discount += line.price_unit
                if line.tax_ids:
                    for tax in line.tax_ids:
                        if not tax.amount:
                            total_exento += line.quantity * line.price_unit
                        if tax.amount:
                            total_gravado += line.quantity * line.price_unit
                else:
                    total_exento += line.quantity * line.price_unit
            order.total_product_qty = total_qty
            order.monto_exento = total_exento
            order.monto_gravado = total_gravado
            order.total_discount = total_discount

    def action_invoice_sent(self):
        # OVERRIDE
        rslt = super(AccountMove, self).action_invoice_sent()
        rslt['context']['default_country_code'] = self.country_code
        if all([self.factura_result_id.is_success, self.factura_result_id.apcon_id, self.cufe]):
            rslt['context']['default_is_all_electronic_invoice'] = True
        return rslt

    def action_electronic_invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        if any(not move.is_invoice(include_receipts=True) for move in self):
            raise UserError(_("Only invoices could be printed."))

        self.filtered(lambda inv: not inv.invoice_sent).write({'invoice_sent': True})
        return self.env.ref(self.journal_id.template_id.xml_id).report_action(self)

    def action_electronic_invoice_upd_acc_date(self):
        for move in self:
            now = datetime.datetime.now()
            if move.electronic_invoice_response == 'success':
                move.date = now

    def action_electronic_invoice_sent(self):
        if self.country_code != "PA":
            raise ValidationError(_("This operation is restricted!"))
        template = self.env.ref("factura_electronica_pa.email_template_electronic_invoice", raise_if_not_found=False)
        invoice = self.env['account.move'].browse(self.id)
        if not all([invoice.factura_result_id.is_success, invoice.factura_result_id.apcon_id, invoice.cufe]):
            raise ValidationError("Electronic invoice is not yet successful for %s" % invoice.name)
        report_template_id = self.env.ref(
                invoice.journal_id.template_id.xml_id).render_qweb_pdf(self.id)
        data_record = base64.b64encode(report_template_id[0])
        ir_values = {
            'name': "E-Invoice Signed: %s" %invoice.name,
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/pdf',
        }
        data_id = self.env['ir.attachment'].create(ir_values)
        template.attachment_ids = [(6, 0, [data_id.id])]
        template.send_mail(self.id, force_send=True)
        template.attachment_ids = [(3, data_id.id)]
        return self.env.ref(invoice.journal_id.template_id.xml_id).report_action(self)

    @api.depends("factura_result_ids", "factura_result_ids.is_success", "factura_result_ids.error_message", "factura_result_ids.result")
    def _compute_electronic_invoice_response(self):
        for response in self:
            if response.factura_result_ids:
                factura_result_id = self._get_success_factura_result(response.factura_result_ids)
                if factura_result_id:
                    result = factura_result_id
                    response.write({'factura_result_id': factura_result_id.id})
                else:
                    result = self._get_current_factura_result(response.factura_result_ids)
                self._get_response_message(response, result)
            else:
                response.electronic_invoice_response = "draft"
                response.electronic_invoice_message = "Not yet send E-invoice"

    def _get_success_factura_result(self, result):
        for success_result in result:
            if success_result.is_success:
                return success_result
        return False

    def _get_current_factura_result(self, result):
        result_id = result.filtered('date').sorted('date', reverse=True)[:1]
        if result_id:
            return result_id
        else:
            return False

    def _get_response_message(self, response, result):
        if result.is_success and result.is_success_with_error_message == False:
            response.electronic_invoice_response = "success"
            response.electronic_invoice_message = "This invoice is Autorizado"
        elif result.is_success_with_error_message:
            response.electronic_invoice_response = "success_error"
            response.electronic_invoice_message = result.error_message
        elif all([result.is_success, result.is_success_with_error_message]) == False and \
                result.error_message:
            response.electronic_invoice_response = "failed"
            response.electronic_invoice_message = result.error_message
        else:
            response.electronic_invoice_response = "draft"
            response.electronic_invoice_message = "Not yet Send E-invoice"

    @api.depends("type", "iDest", "fiscal_position_id")
    def _compute_iDoc(self):
        for move in self:
            iDoc = move.iDest == "1" and "1" or "3"

            if move.type == "out_refund":
                iDoc = "6"
                # move.has_reconciled_entries and "4" or "6"
            if str(move.fiscal_position_id.name).lower() == "free zone":
                iDoc = "8"

            move.iDoc = iDoc

    @api.depends("partner_id", "partner_id.country_id")
    def _compute_iDest(self):
        for move in self:
            move.iDest = move.partner_id.is_panama_country \
                         and "1" \
                         or "2"

    @api.depends("type")
    def _compute_iTipoTranVenta(self):
        for move in self:
            move.iTipoTranVenta = move._is_invoice_sale() and "1" or False

    ############################
    # Constrains and onchanges #
    ############################

    #########################
    # CRUD method overrides #
    #########################

    ##################
    # Action methods #
    ##################
    def action_electronic_invoice(self):
        if self.country_code != "PA":
            raise ValidationError(_("This operation is restricted!"))
        if not self.journal_id.api_token:
            raise ValidationError("API TOKEN Must be set on the journal of the invoice")
        API_TOKEN = self.journal_id.api_token
        BASE_URL = self.journal_id.api_url or "https://qa.api.edocspanama.com/api/"

        not_success = self.filtered(lambda x: x.electronic_invoice_response == "success")
        if not_success:
            raise ValidationError("The following invoice is already signed e-invoice: %s"
                                  % not_success.mapped("name"))

        not_for_electonic_invoicing = self.filtered(
            lambda x: not x.used_in_electronic_invoicing)

        if not_for_electonic_invoicing:
            raise ValidationError("The journal of the following invoices are not allowed for electronic invoicing: %s"
                                  % not_for_electonic_invoicing.mapped("name"))
        not_posted = self.filtered(lambda x: x.state != "posted")
        if not_posted:
            raise ValidationError("The following invoices are yet posted: %s"
                                  % not_posted.mapped("name"))

        # not_paid = self.filtered(lambda x: x.amount_residual)
        # if not_paid:
        #     raise ValidationError("The following invoices are not yet paid: %s"
        #                           % not_paid.mapped("name"))

        fe_result_obj = self.env["factura.electronica.result"]
        results = fe_result_obj

        req_headers = {
            "Authorization": "Bearer %s" % API_TOKEN,
            "Accept": "application/json"
        }

        for move in self:
            existing = fe_result_obj.search(
                [("move_id", "=", move.id)], limit=1)

            log_values = {"move_id": move.id}

            if existing.apcon_id and existing.is_success:
                url = url_join(BASE_URL, f"invoiceFePa/{existing.apcon_id}")
                res = requests.get(url, headers=req_headers)
            else:
                values = {
                    "dGen": move._prepare_dGen_values(),
                    "gItem": move._prepare_gItem_values(),
                    "gTot": move._prepare_gTot_values()
                }

                log_values["payload"] = jsonlib.dumps(values, indent=2)

                url = url_join(BASE_URL, "invoiceFePa")
                res = requests.post(url, json=values, headers=req_headers)

            try:
                json = res.json()
            except:
                _logger.info(
                    " ERROR json from api response %s" %
                    (res)
                )
                raise ValidationError("Error decoding JSON fom API response.")
            log_values["result"] = jsonlib.dumps(json, indent=2)

            if json.get("code", 400) != 200 or not json.get("message"):
                log_values["error_message"] = json.get("status")
            else:
                message = json.get("message", {})
                if message.get("status", "Error") == "Error":
                    log_values["error_message"] = message.get("msgRes")
                log_values.update({
                    "apcon_id": message.get("id"),
                    "signed_xml": message.get("Signed_xml")
                })

            factura_id = fe_result_obj.create(log_values)
            results |= factura_id

        if results:
            return {
                "type": "ir.actions.act_window",
                "name": "Eletronic Invoice Results",
                "view_mode": "tree,form",
                "res_model": "factura.electronica.result",
                "target": "current",
                "domain": [("id", "in", results.ids)],
            }

    ####################
    # Business methods #
    ####################
    def action_electronic_invoice_upd_acc_date(self):
        for move in self:
            now = datetime.datetime.now()
            if move.electronic_invoice_response == 'success':
                move.date = now

    @api.depends('factura_result_id', 'electronic_invoice_sign')
    def _get_signed_xml_values(self):
        for invoice in self:
            qr_code = ""
            cufe = ""
            dFecProc = ""
            if all([invoice.factura_result_id.is_success, invoice.factura_result_id.apcon_id]):
                signed_xml = base64.b64decode(invoice.factura_result_id.signed_xml).decode("utf-8")
                xml_file = io.StringIO(signed_xml)
                tree = ET.parse(xml_file)
                root = tree.getroot()
                dCUFE = root.findall('.//dCUFE')
                qr = root.find('.//{http://dgi-fep.mef.gob.pa}dQRCode')
                dFecProc = root.findall('.//dFecProc')
                if dCUFE:
                    qr_code = qr.text
                    cufe = dCUFE[0].text
                    dFecProc = dFecProc[0].text
            
            invoice.qr_code = qr_code
            invoice.cufe = cufe
            invoice.dFecProc = dFecProc

    def _is_invoice_sale(self):
        self.ensure_one()
        return self.type in ["out_invoice"]

    def _get_invoice_line_tax_details(self, line):
        dTasaITBMS = "0"
        dValITBMS = 0.0
        dTasaISC = 0.0
        dValISC = 0.0
        if line.tax_ids:
            line.tax_ids.ensure_one()
            tax_group = line.tax_ids.tax_group_id

            if "ISC" in tax_group.name:
                dTasaISC = line.tax_ids.amount
                dValISC = line.tax_base_amount
            else:
                if "7%" in tax_group.name:
                    dTasaITBMS = "1"
                    dValITBMS = (line.price_subtotal * 7) / 100
                elif "10%" in tax_group.name:
                    dTasaITBMS = "2"
                    dValITBMS = (line.price_subtotal * 10) / 100
                elif "15%" in tax_group.name:
                    dTasaITBMS = "3"
                    dValITBMS = (line.price_subtotal * 15) / 100
        return {
            'dTasaITBMS': dTasaITBMS,
            'dValITBMS': dValITBMS,
            'dTasaISC': dTasaISC,
            'dValISC': dValISC
        }

    def _prepare_gItem_values(self):
        self.ensure_one()

        PAB = self.env["res.currency"].search([("name", "=", "PAB")], limit=1)

        def _convert_to_PAB(line, amount):
            if amount <= 0:
                return 0

            return self.currency_id._convert(amount, PAB, line.company_id, line.date, round=False)

        gItem = []
        for count, line in enumerate(self.invoice_line_ids.filtered(lambda x: x.product_id.id != False and x.price_subtotal >= 0), 1):
            product = line.product_id
            uom = line.product_uom_id
            panama_uom = uom.panama_uom_code

            if not product.panama_goods_service_family_id or not product.panama_goods_service_segment_id:
                raise ValidationError(
                    "The product %s has not been configured with a Panamanian Goods and Service code yet. "
                    "Please configure it before continuing." % product.name)

            tax_group = self._get_invoice_line_tax_details(line)
            dTasaITBMS = tax_group.get('dTasaITBMS', "0")
            dValITBMS = tax_group.get('dValITBMS', 0.00)
            dTasaISC = tax_group.get('dTasaISC', 0.00)
            dValISC = tax_group.get('dValISC', 0.00)
            dPrUnit = line.price_unit or 0.0
            dPrUnitDesc = line.price_unit * (line.discount / 100)
            dPrItem = line.quantity * (dPrUnit - dPrUnitDesc)
            dPrAcarItem = dPrSegItem = 0.0
            # SUM(dPrItem, dPrAcarItem, dPrSegItem, dValITBMS y dValISC)
            dValTotItem = sum(
                [dPrItem, dPrAcarItem, dPrSegItem, dValITBMS, dValISC])

            values = {
                "dSecItem": f"{count}".rjust(3, "0"),
                "dDescProd": line.name,
                "dCodProd": product.default_code and product.default_code.rjust(20, "0") or str(product.id).rjust(20,
                                                                                                                  "0"),
                "dCantCodInt": line.quantity,
                "dInfEmFE": line.internal_note or "",
                "dCodCPBSabr": product.panama_goods_service_segment_id.code,
                "dCodCPBScmp": product.panama_goods_service_family_id.code,
                "gPrecios": {
                    "dPrUnit": _convert_to_PAB(line, dPrUnit),
                    "dPrUnitDesc": _convert_to_PAB(line, dPrUnitDesc),
                    "dPrItem": _convert_to_PAB(line, dPrItem),
                    "dPrAcarItem": to_2_decimal_place(_convert_to_PAB(line, dPrAcarItem)),
                    "dPrSegItem": to_2_decimal_place(_convert_to_PAB(line, dPrSegItem)),
                    "dValTotItem": _convert_to_PAB(line, dValTotItem),
                },
                "gITBMSItem": {
                    "dTasaITBMS": str(dTasaITBMS),
                    "dValITBMS": _convert_to_PAB(line, dValITBMS)
                },
                "gISCItem": {
                    "dTasaISC": dTasaISC,
                    "dValISC": to_2_decimal_place(_convert_to_PAB(line, dValISC))
                }
            }

            # Manufacture
            # "dFechaFab": None,
            # "dFechaCad": None,

            if panama_uom:
                values["cUnidadCPBS"] = panama_uom

            if dTasaISC:
                values["gISCItem"] = {
                    "dTasaISC": dTasaISC,
                    "dValISC": to_2_decimal_place(_convert_to_PAB(line, dValISC))
                }

            gItem.append(values)

        return gItem

    def _prepare_gTot_values(self):
        self.ensure_one()
        reversal_entry_id = self.reversed_entry_id


        gItem = self._prepare_gItem_values()

        dTotITBMS = reduce(lambda value, i: value +
                                            float(i["gITBMSItem"]["dValITBMS"]), gItem, 0.0)
        dTotISC = reduce(lambda value, i: value +
                                          float(i.get("gISCItem", {}).get("dValISC", 0)), gItem, 0.0)
        dVTotItems = reduce(lambda value, i: value +
                                             float(i["gPrecios"]["dValTotItem"]), gItem, 0.0)
        dTotNeto = reduce(lambda value, i: value +
                                             float(i["gPrecios"]["dPrItem"]), gItem, 0.0)
        gDescBonif = []
        dDetalDesc = []
        dValDesc = 0
        for count, line in enumerate(self.invoice_line_ids.filtered(lambda x: x.product_id.id != False
                                                                              and x.price_subtotal <= -1), 1):
            tax_group = self._get_invoice_line_tax_details(line)
            discount_line_total = tax_group.get('dValITBMS', 0.00) + line.price_subtotal
            dDetalDesc.append(line.product_id.name if line.product_id else line.name)
            dValDesc += abs(discount_line_total)

        reg_expression_amp = "&(?!#\d{4};|amp;)"
        if dDetalDesc and dValDesc:
            gDescBonif.append({
            "dDetalDesc": re.sub(reg_expression_amp, "&amp;", (', '.join(dDetalDesc))),
            "dValDesc": to_2_decimal_place(dValDesc),
            })
        dTotDesc = reduce(lambda value, i: value + float(i["dValDesc"]), gDescBonif, 0.0)

        formaPagos = []
        gPagPlazo = []
        dTotRec = 0.0
        for count, line in enumerate(self.line_ids.filtered(lambda l: l.account_id.user_type_id.type == "receivable"),
                                     1):
            dTotRec += line.debit
            debit_credit = line.debit
            if self.iDoc in ["4", "6"] and self.type == "out_refund":
                debit_credit = line.credit
                dTotRec += line.credit
            formaPagos.append({
                "iFormaPago": self.invoice_date == line.date_maturity and "02" or "01",
                "dFormaPagoDesc": "",
                "dVlrCuota": to_2_decimal_place(debit_credit)
            })
            gPagPlazo.append({
                "dSecItem": f"{count}",
                "dFecItPlazo": date_to_iso8601(line.date_maturity),
                "dValItPlazo": to_2_decimal_place(debit_credit)
            })

        values = {
            "dTotNeto": to_2_decimal_place(dTotNeto),
            "dTotITBMS": to_2_decimal_place(dTotITBMS),
            "dTotGravado": to_2_decimal_place(dTotITBMS + dTotISC),
            "dTotDesc": to_2_decimal_place(abs(dTotDesc)),
            "dTotISC": to_2_decimal_place(dTotISC),
            "dTotAcar": "0.00",
            "dTotSeg": "0.00",
            "dVTot": to_2_decimal_place(self.amount_total),
            "dTotRec": to_2_decimal_place(dTotRec),
            "dVuelto": "0.00",
            "iPzPag": self.invoice_payment_term_id and str(self.invoice_payment_term_id._get_timing()) or "1",
            "dNroItems": str(len(gItem)),
            "dVTotItems": to_2_decimal_place(dVTotItems),
        }

        if gDescBonif:
            values["gDescBonif"] = gDescBonif
        if formaPagos:
            values["gFormaPago"] = formaPagos
        if gPagPlazo:
            values["gPagPlazo"] = gPagPlazo

        return values

    def _prepare_dGen_values(self):
        self.ensure_one()

        journal = self.journal_id
        subsidiary = self.company_subsidiary_id
        company = self.company_id
        issuer_partner = company.partner_id
        partner = self.partner_id
        reversal_entry_id = self.reversed_entry_id


        if not subsidiary:
            raise ValidationError(
                "No subsidiary detected in journal. Please set it first")

        if not partner.country_id:
            raise ValidationError(
                "No country set for customer. Please set it first")

        if not subsidiary.panama_corregimiento_id:
            raise ValidationError(
                "No corregimiento set in subsidiary. Please set it first")

        gRucEmi = issuer_partner.vat
        if not gRucEmi:
            raise ValidationError(
                "Company TAX ID is empty. Please set it first")
        dRuc, dDV = "", ""
        if "DV" in gRucEmi:
            dRuc, dDV = (i.strip() for i in gRucEmi.split("DV"))

        gRucRec = partner.vat
        if not gRucRec:
            raise ValidationError(
                "Customer TAX ID is empty. Please set it first")
        gdRuc, gdDV = "", ""
        dTipoRuc = ""
        iTipoRec = partner.recipient_type
        if not iTipoRec:
            raise ValidationError(
                "Customer recipient type is empty. Please set it first")


        if iTipoRec in ["1", "3"]:
            dTipoRuc = partner.company_type == "person" and "1" or "2"
            if "DV" in gRucRec:
                gdRuc, gdDV = (i.strip() for i in gRucRec.split("DV"))
                dDV.rjust(2, "0")
            if not all([partner.panama_corregimiento_id.code, partner.panama_corregimiento_id.name,
                        partner.panama_district_id.name, partner.state_id.name]):
                raise ValidationError(
                    "Customer address is empty. Please set it first,  it's mandatory if recipient type is on "
                    "Contribuyente and Gobierno")

        latitude = "%07.4f" % abs(subsidiary.latitude)
        longitude = "%07.4f" % abs(subsidiary.longitude)

        reg_expression_amp = "&(?!#\d{4};|amp;)"
        
        issuer_partner_address = issuer_partner._display_address(without_company=True).replace("\n", " ").strip()[:100]
        issuer_contact_address = re.sub(reg_expression_amp, "&amp;", issuer_partner_address)
        issuer_name = re.sub(reg_expression_amp, "&amp;", issuer_partner.name)
        
        partner_address = partner._display_address(without_company=True).replace("\n", " ").strip()[:100]
        partner_contact_address = re.sub(reg_expression_amp, "&amp;", partner_address)
              
        values = {
            "iDoc": self.iDoc,
            "dNroDF": self.dNroDF,
            "dPtoFacDF": journal.dPtoFacDF,
            "iNatOp": self.iNatOp,
            "dFechaEm": date_to_iso8601(self.invoice_date),
            "iTipoOp": self.iTipoOp,
            "iDest": self.iDest,
            "iTipoTranVenta": self._is_invoice_sale() and self.iTipoTranVenta or "",
            "dInfEmFE": self.name,
            "gEmis": {
                "dNombEm": issuer_name,
                "dSucEm": subsidiary.code,
                "dCoordEm": f"+{latitude},-{longitude}",
                "dDirecEm": issuer_contact_address,
                "dTfnEm": subsidiary.phone or "",
                "gRucEmi": {
                    "dTipoRuc": issuer_partner.company_type == "person" and "1" or "2",
                    "dRuc": dRuc,
                    "dDV": dDV,
                },
                "gUbiEm": {
                    "dCodUbi": subsidiary.panama_corregimiento_id.code,
                    "dCorreg": subsidiary.panama_corregimiento_id.name.upper(),
                    "dDistr": subsidiary.panama_district_id.name.upper(),
                    "dProv": subsidiary.state_id.name.upper()
                }
            },
            "gDatRec": {
                "iTipoRec": iTipoRec,
                "dNombRec": partner.name,
                "dDirecRec": partner_contact_address,
                "dTfnRec": partner.phone and partner.phone.replace("+507", "").strip() or "",
                "cPaisRec": partner.country_id.code.upper() in PA_COUNTRY_CATALOG and partner.country_id.code.upper() or "ZZ",
                "dPaisRecDesc": partner.country_id.name
            },
        }

        if iTipoRec in ["1", "3"]:
            values["gDatRec"]["gRucRec"] = {
                "dTipoRuc": dTipoRuc,
                "dRuc": gdRuc,
                "dDV": gdDV,
            }

        if iTipoRec == '2' and partner.vat:
            gdRuc = partner.vat
            values["gDatRec"]["dRuc"] = gdRuc

        if iTipoRec in ["1", "3"] or iTipoRec == "2" and all([partner.panama_corregimiento_id.code, partner.panama_corregimiento_id.name,
                    partner.panama_district_id.name, partner.state_id.name]):
            values["gDatRec"]["gUbiRec"] = {
                "dCodUbi": partner.panama_corregimiento_id.code,
                "dCorreg": partner.panama_corregimiento_id.name,
                "dDistr": partner.panama_district_id.name,
                "dProv": partner.state_id.name
            }

        if iTipoRec == "4":
            values["gDatRec"]["gIdExt"] = {
                "dIdExt": partner.vat
            }

        # "gDescBonif": {
        #
        # },
        # "gRetenc": None,  # withholding
        # "gPagPlazo": None  # installment

        if subsidiary.email_address:
            values["gEmis"]["dCorElectEmi"] = subsidiary.email_address

        if partner.email:
            values["gDatRec"]["dCorElectEmi"] = partner.email

        if self.type == "in_invoice":
            values["gPedComGl"] = {
                "dNroPed": self.name,
                "dNumAcept": "1",
                "dInfEmPedGI": "Ref: %s, Vendor: %s" % (self.name, self.partner_id.name)
            }

        if self.iDoc == "4" and self.type == "out_refund" and all([self.has_reconciled_entries, reversal_entry_id ]):
            invoice = self._get_refered_invoice()
            gDFRef_values = []
            for move in invoice:
                company_partner = move.company_id.partner_id
                company_vat = company_partner.vat
                if not company_vat:
                    raise ValidationError(
                        "Company TAX ID of referred invoice is empty. Please set it first")
                if not move.cufe:
                    raise ValidationError(
                        "Referred Invoice %s is not yet success Signed E-invoice. Please E-invoice it first" % move.name)
                company_dRuc, company_dDV = "", ""
                if "DV" in company_vat:
                    company_dRuc, company_dDV = (i.strip() for i in company_vat.split("DV"))

                company_name = move.company_id.name
                if company_name:
                    company_name = re.sub(reg_expression_amp, "&amp;", company_name)
                    
                gDFRef_values.append({
                    "gRucEmDFRef": {
                        "dTipoRuc": company_partner.company_type == "person" and "1" or "2",
                        "dRuc": company_dRuc,
                        "dDv": company_dDV,
                        "dNombEmRef":  company_name,
                        "dFechaDFRef": date_to_iso8601(move.invoice_date),
                    },

                    "gDFRefNum": {
                        "gDFRefFE": {
                            "dCUFERef": move.cufe
                            #
                        }
                    }
                })
            values["gDFRef"] = gDFRef_values

        return values

    def _get_refered_invoice(self):
        invoice = []
        for line in self.line_ids.filtered(lambda l: l.account_id.user_type_id.type == "receivable"):
            for move in line.matched_debit_ids:
                invoice.append(move.debit_move_id.move_id.id)
        return self.env['account.move'].browse(invoice)

    def get_total_line_amounts(self):
        self.ensure_one()
        total_discount = 0.0
        total_exento = 0.0
        total_gravado = 0.0
        for line in self.invoice_line_ids:
            original_price = line.quantity * line.price_unit
            discount_amount = 0
            if line.discount:
                discount_amount = original_price * (line.discount / 100)
            total_discount += discount_amount
            if line.price_unit >= 0:
                if line.tax_ids:
                    total_gravado += line.price_subtotal
                else:
                    total_exento += line.price_subtotal
        
        values = {
            "total_discount": total_discount + abs(self.total_discount),
            "total_gravado": total_gravado,
            "total_exento": total_exento,
        }
        return values
    
    def get_sale_note_html_to_text(self):
        self.ensure_one()
        orders = self.invoice_line_ids.sale_line_ids.mapped('order_id')
        notes = orders[0].note if len(orders) > 1 else orders.note if orders else ""
        tree = etree.fromstring('<p>%s</p>' % notes, etree.XMLParser(recover=True))
        return ' '.join(tree.itertext())
    
    def _prepare_tax_lines_data_for_totals_from_invoice(self, tax_line_id_filter=None, tax_ids_filter=None):
        """ Prepares data to be passed as tax_lines_data parameter of get_tax_breakdown_by_group() from an invoice.

            NOTE: tax_line_id_filter and tax_ids_filter are used to restrict the taxes with consider
                  in the totals.

            :param tax_line_id_filter: a function(aml, tax) returning true if tax should be considered on tax move line aml.
            :param tax_ids_filter: a function(aml, taxes) returning true if taxes should be considered on base move line aml.

            :return: A list of dict in the format described in _get_tax_totals's tax_lines_data's docstring.
        """
        self.ensure_one()

        tax_line_id_filter = tax_line_id_filter or (lambda aml, tax: True)
        tax_ids_filter = tax_ids_filter or (lambda aml, tax: True)

        tax_lines_data = []

        for line in self.line_ids:
            if line.tax_line_id and tax_line_id_filter(line, line.tax_line_id):
                tax_lines_data.append({
                    'line_key': 'tax_line_%s' % line.id,
                    'tax_amount': line.price_subtotal,
                    'tax': line.tax_line_id,
                })

            if line.tax_ids:
                for base_tax in line.tax_ids.flatten_taxes_hierarchy():
                    if tax_ids_filter(line, base_tax):
                        tax_lines_data.append({
                            'line_key': 'base_line_%s' % line.id,
                            'base_amount': line.price_subtotal,
                            'tax': base_tax,
                            'tax_affecting_base': line.tax_line_id,
                        })

        return tax_lines_data

    def get_tax_breakdown_by_group(self):
        self.ensure_one()
        total_tax_by_group = {}
        tax_lines_data = self._prepare_tax_lines_data_for_totals_from_invoice()
        if tax_lines_data:
            total_tax_by_group = self.get_tax_totals_by_group(tax_lines_data)
        return total_tax_by_group
    
    @api.model
    def get_tax_totals_by_group(self, tax_lines_data):
        account_tax = self.env['account.tax']

        grouped_taxes = defaultdict(lambda: defaultdict(lambda: {'base_amount': 0.0, 'tax_amount': 0.0, 'base_line_keys': set()}))
        for line_data in tax_lines_data:
            tax = line_data['tax']
            tax_group = line_data['tax'].tax_group_id

            # Update tax data
            tax_group_vals = grouped_taxes[tax_group][tax]
            
            if 'base_amount' in line_data:
                # Base line
                if tax_group == line_data.get('tax_affecting_base', account_tax).tax_group_id:
                    # In case the base has a tax_line_id belonging to the same group as the base tax,
                    # the base for the group will be computed by the base tax's original line (the one with tax_ids and no tax_line_id)
                    continue
               
                if line_data['line_key'] not in tax_group_vals['base_line_keys']:
                    # If the base line hasn't been taken into account yet, at its amount to the base total.
                    tax_group_vals['base_line_keys'].add(line_data['line_key'])
                    tax_group_vals['base_amount'] += line_data['base_amount']

            else:
                # Tax line
                tax_group_vals['tax_amount'] += line_data['tax_amount']
                
        total_tax_by_group = {}
        for tax_group, groups in grouped_taxes.items():
            total_tax_by_group[tax_group] = []
            for tax, amounts in sorted(groups.items(), key=lambda l: l[0].sequence):
                groups_vals = {
                    'tax_group_name': tax_group.name,
                    'tax_name': tax.name,
                    'tax_group': tax_group,
                    'tax': tax,
                    'tax_value': tax.amount,
                    'total_tax_amount': amounts['tax_amount'],
                    'total_tax_base_amount': amounts['base_amount'],
                }
                total_tax_by_group[tax_group].append(groups_vals)
        
        return total_tax_by_group
    