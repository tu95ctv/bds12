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
    _rec_name = 'description'


    url = fields.Char()
    description = fields.Char()
    description_unidecode = fields.Char(compute='description_unidecode_', store = True)
    @api.depends('description')
    def description_unidecode_(self):
        for r in self:
            r.description_unidecode = unidecode(r.description)
    siteleech_id = fields.Many2one('bds.siteleech',compute='siteleech_id_',store=True)
    web_last_page_number = fields.Integer()
    current_page = fields.Integer()
    current_page_for_first = fields.Integer()
    update_link_number = fields.Integer()
    create_link_number = fields.Integer()
    existing_link_number = fields.Integer()
    link_number = fields.Integer()
    interval = fields.Integer()
    cate = fields.Selection([('bds','BDS'),('phone','Phone'),('laptop','Laptop')], default='bds')
    set_number_of_page_once_fetch = fields.Integer(default=5)
    set_leech_max_page = fields.Integer()

    
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
                r.siteleech_id = g_or_c_ss(self,'bds.siteleech', {'name':name})
