# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Cate(models.Model):
    _name = 'bds.cate'
    
    name = fields.Char()
    parent_id = fields.Many2one('bds.cate')
    source = fields.Char()
