# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Error(models.Model):
    _name = 'bds.error'
    name = fields.Char()
    des = fields.Char()
    
    
    