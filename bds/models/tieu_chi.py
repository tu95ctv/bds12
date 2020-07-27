# -*- coding: utf-8 -*-
from odoo import models, fields, api

class bds(models.Model):
    _name = 'bds.tieuchi'
    _order = "id desc"
    
    tieu_chi_int_1 = fields.Integer()
    tieu_chi_int_2 = fields.Integer()
    tieu_chi_int_3 = fields.Integer()
    tieu_chi_int_4 = fields.Integer()

    tieu_chi_char_1 = fields.Char()
    tieu_chi_char_2 = fields.Char()
    tieu_chi_char_3 = fields.Char()
    tieu_chi_char_4 = fields.Char()

    tieu_chi_float_1 = fields.Float()
    tieu_chi_float_2 = fields.Float()
    tieu_chi_float_3 = fields.Float()
    tieu_chi_float_4 = fields.Float()

    type = fields.Char()
