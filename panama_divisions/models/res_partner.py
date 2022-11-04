# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PanamaCorregimiento(models.Model):
    _name = 'panama_divisions.corregimiento'
    _description = 'Panama corregimiento'

    district_id = fields.Many2one('panama_divisions.district')
    name = fields.Char()
    code = fields.Char()


class PanamaDistricts(models.Model):
    _name = 'panama_divisions.district'
    _description = 'Panama district'

    province_id = fields.Many2one('res.country.state')
    name = fields.Char()


class ResPartner(models.Model):
    _inherit = "res.partner"

    panama_district_id = fields.Many2one('panama_divisions.district')
    panama_corregimiento_id = fields.Many2one('panama_divisions.corregimiento')
    is_panama_country = fields.Boolean(
        store=True, compute='compute_is_panama_country')

    @api.onchange('panama_corregimiento_id')
    def onchange_panama_corregimiento_id(self):
        for partner in self:
            partner.zip = partner.panama_corregimiento_id.name

    @api.onchange('panama_district_id')
    def onchange_panama_district_id(self):
        for partner in self:
            partner.city = partner.panama_district_id.name

    @api.depends('country_id', 'country_id.code')
    def compute_is_panama_country(self):
        for partner in self:
            partner.is_panama_country = partner.country_id.code == 'PA'

    def _validate_corregimiento(self):
        self.ensure_one()
