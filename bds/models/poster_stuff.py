# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api



class PosterNameLines(models.Model):
    _name = 'bds.posternamelines'
    username_in_site = fields.Char()
    site_id = fields.Many2one('bds.siteleech')
    poster_id = fields.Many2one('bds.poster')

    
class QuanOfPoster(models.Model):
    _name = 'bds.quanofposter'
    name = fields.Char(compute='name_',store=True)
    
    quan_id = fields.Many2one('bds.quan')
    siteleech_id = fields.Many2one('bds.siteleech')
    quantity = fields.Integer()
    min_price = fields.Float(digits=(32,1))
    avg_price = fields.Float(digits=(32,1))
    max_price = fields.Float(digits=(32,1))
    poster_id = fields.Many2one('bds.poster')

    @api.depends('quan_id','quantity') 
    def name_(self):
        for r in self:
            if r.siteleech_id or  r.quan_id:
                r.name = (( r.siteleech_id.name + ' ' ) if r.siteleech_id.name else '') +  r.quan_id.name + ':' + str(r.quantity)
            else:
                r.name ='all'
