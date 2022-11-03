# -*- coding: utf-8 -*-

import base64

from odoo import http, tools
from odoo.http import request, content_disposition


class Controller(http.Controller):

    @http.route(["/factura_electronica_pa/signed_xml/<model('factura.electronica.result'):model>"], type="http", auth="user")
    def factura_electronica_pa_signed_xml(self, model):
        response = request.make_response(base64.b64decode(model.signed_xml),
                                         headers=[
            ("Content-Type", "application/vnd.ms-excel"),
            ("Content-Disposition",
             content_disposition("Factura Electronica - %s.xml" % model.move_id.name))
        ])
        return response
