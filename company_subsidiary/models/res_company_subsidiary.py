# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResCompanySubsidiary(models.Model):
    ######################
    # Private attributes #
    ######################
    _name = "res.company.subsidiary"
    _description = "Company Subsidiary"
    _rec_name = "code"

    ###################
    # Default methods #
    ###################

    ######################
    # Fields declaration #
    ######################
    company_id = fields.Many2one(comodel_name="res.company",
                                 required=True)
    code = fields.Char(string="Code",
                       index=True,
                       required=True)
    journal_ids = fields.One2many(comodel_name="account.journal",
                                  inverse_name="company_subsidiary_id",
                                  domain="[('company_id', '=', company_id)]")
    employee_ids = fields.One2many(comodel_name="hr.employee",
                                   inverse_name="company_subsidiary_id",
                                   domain="[('company_id', '=', company_id)]")
    len_employees = fields.Integer(string="# of Employees",
                                   compute="_len_employees")

    # Address and Contact
    country_id = fields.Many2one(comodel_name="res.country",
                                 default=lambda self: self.env.company.id)
    state_id = fields.Many2one(comodel_name="res.country.state",
                               domain="[('country_id', '=?', country_id)]")
    city = fields.Char(string="City")
    zip = fields.Char(string="Zip Code")
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street2")
    email_address = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    mobile = fields.Char(string="Mobile")
    complete_address = fields.Char(string="Complete Address",
                                   compute="_compute_complete_address",
                                   store=True)

    # Geolocation
    date_localization = fields.Date(string="Geolocation Date")
    latitude = fields.Float(string="Geo Latitude",
                            digits=(4, 4))
    longitude = fields.Float(string="Geo Longitude",
                             digits=(4, 4))

    ##############################
    # Compute and search methods #
    ##############################
    @api.depends("employee_ids")
    def _len_employees(self):
        for subsidiary in self:
            subsidiary.len_employees = len(subsidiary.employee_ids)

    @api.depends("country_id", "state_id", "city", "zip", "street", "street2")
    def _compute_complete_address(self):
        for subsidiary in self:
            FORMAT = subsidiary.country_id.address_format or "%(street)s\n%(street2)s\n%(city)s %(state_code)s %(zip)s\n%(country_name)s"
            args = {
                "state_code": self.state_id.code or "",
                "state_name": self.state_id.name or "",
                "country_code": self.country_id.code or "",
                "country_name": self.country_id.name or "",
                "street": self.street or "",
                "street2": self.street2 or "",
                "city": self.city or "",
                "zip": self.zip or ""
            }
            subsidiary.complete_address = FORMAT % args

    ############################
    # Constrains and onchanges #
    ############################
    @api.onchange("code", "company_id")
    def _onchange_code(self):
        if self.search_count([("company_id", "=", self.company_id.id),
                              ("code", "=", self.code)]):
            raise ValidationError(
                "Subsidiary Code should be unique in a company!")

    #########################
    # CRUD method overrides #
    #########################

    ##################
    # Action methods #
    ##################
    def geo_localize(self):
        for partner in self.with_context(lang="en_US"):
            result = self._geo_localize(partner.street,
                                        partner.zip,
                                        partner.city,
                                        partner.state_id.name,
                                        partner.country_id.name)

            if result:
                partner.write({
                    "latitude": result[0],
                    "longitude": result[1],
                    "date_localization": fields.Date.context_today(partner)
                })
        return True

    ####################
    # Business methods #
    ####################
    @api.model
    def _geo_localize(self, street="", zip="", city="", state="", country=""):
        geo_obj = self.env["base.geocoder"]
        search = geo_obj.geo_query_address(
            street=street, zip=zip, city=city, state=state, country=country)
        result = geo_obj.geo_find(search, force_country=country)
        if result is None:
            search = geo_obj.geo_query_address(
                city=city, state=state, country=country)
            result = geo_obj.geo_find(search, force_country=country)
        return result
