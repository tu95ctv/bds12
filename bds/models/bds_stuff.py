# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api
from odoo.addons.bds.models.bds_tools  import  request_html
import base64

class Gialines(models.Model):
    _name='bds.gialines'
    gia = fields.Float()
    bds_id = fields.Many2one('bds.bds', ondelete='cascade')
    gia_cu = fields.Float()
    diff_gia = fields.Float()
    

class Publicdate(models.Model):
    _name='bds.publicdate'
    bds_id = fields.Many2one('bds.bds', ondelete='cascade')
    public_date = fields.Date()
    public_date_cu = fields.Date()
    diff_public_date = fields.Integer()
    public_datetime = fields.Datetime()
    public_datetime_cu = fields.Datetime()
    diff_public_datetime = fields.Integer()

class SiteDuocLeech(models.Model):
    _name = 'bds.siteleech'
    name = fields.Char() 
    name_viet_tat = fields.Char()  

    
class Images(models.Model):
    _name = 'bds.images'
    url = fields.Char()
    bds_id = fields.Many2one('bds.bds')
    thumb_view = fields.Binary(compute='thumb_view_')  

    @api.depends('url')
    def thumb_view_(self):
        for r in self:
            if r.url:
                photo = base64.encodestring(request_html(r.url, False, is_decode_utf8 = False))
                r.thumb_view = photo 


