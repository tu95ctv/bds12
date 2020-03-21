# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons.bds.models.bds_tools import g_or_c_ss
import re
from unidecode import unidecode
class URL(models.Model):
    _name = 'bds.url'
    _sql_constraints = [
        ('name_unique',
         'UNIQUE(url)',
         "The url must be unique"),
    ]
    name = fields.Char(compute='name_',store = True)
    name_khong_dau = fields.Char(compute='name_', store = True)
    url = fields.Char()
    description = fields.Char()    
    siteleech_id = fields.Many2one('bds.siteleech',compute='siteleech_id_',store=True)
    web_last_page_number = fields.Integer()
    quan_id = fields.Many2one('bds.quan',ondelete='restrict')
    quan_name = fields.Char()
    
    phuong_id = fields.Many2one('bds.phuong')
    current_page = fields.Integer()
    current_page_for_first = fields.Integer()
    post_ids = fields.Many2many('bds.bds','url_post_relate','url_id','post_id')
    
    phuong_ids =  fields.Many2many('bds.phuong',compute='phuong_ids_',store=True)
    quan_ids =  fields.Many2many('bds.quan',compute='quan_ids_',store=True)
    
    update_link_number = fields.Integer()
    create_link_number = fields.Integer()
    existing_link_number = fields.Integer()
    link_number = fields.Integer()
    interval = fields.Integer()
    cate = fields.Selection([('bds','BDS'),('phone','Phone'),('laptop','Laptop')], default='bds')
    set_number_of_page_once_fetch = fields.Integer(default=5)
    set_leech_max_page = fields.Integer()
    @api.depends('post_ids')
    def quan_ids_(self):
        for r in self:
            r.quan_ids = r.post_ids.mapped('quan_id')
    @api.depends('post_ids')
    def phuong_ids_(self):
        for r in self:
            r.phuong_ids = r.post_ids.mapped('phuong_id')
    @api.depends('url')
    def siteleech_id_(self):
        for r in self:
            if r.url:
                if 'chotot' in r.url:
                    name = 'chotot'
                elif 'batdongsan' in r.url:
                    name = 'batdongsan'
                elif 'muaban' in r.url:
                    name = 'muaban'
                else:
                    name = re.search('\.(.*?)\.', r.url).group(1)
                chottot_site = g_or_c_ss(self,'bds.siteleech', {'name':name})
                r.siteleech_id = chottot_site.id
            
    @api.depends('url','quan_id','phuong_id')
    def name_(self):
        for r in self:
            surfix =  r.phuong_id.name or  r.quan_id.name  
            url = r.url
            name = (url if url else '') + ((' ' +  surfix ) if surfix else '')
            r.name = name
            r.name_khong_dau = unidecode(name) +' ' + unidecode(r.description)
    @api.multi
    def name_get(self):
        res = []
        for r in self:
            surfix =  r.quan_id.name or r.phuong_id.name
            new_name = r.url + ((' ' +  surfix ) if surfix else '' )+' current_page: %s'%r. current_page
            res.append((r.id,new_name))
        return res