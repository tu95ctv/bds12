# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons.bds.models.bds_tools import g_or_c_ss
import re
from unidecode import unidecode

from odoo.addons.bds.models.fetch_site.fetch_chotot_obj  import create_cho_tot_page_link
from odoo.addons.bds.models.bds_tools  import  request_html
import json
import math
import datetime
class URL(models.Model):
    _name = 'bds.url'
    _sql_constraints = [
        ('name_unique',
         'UNIQUE(url)',
         "The url must be unique"),
    ]
    _rec_name = 'description'
    _order = 'priority asc'

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
    current_page_2 = fields.Integer()
    update_link_number = fields.Integer(readonly=1)
    create_link_number = fields.Integer(readonly=1)
    existing_link_number = fields.Integer(readonly=1)
    link_number = fields.Integer(readonly=1)
    interval = fields.Integer(readonly=1)
    # cate = fields.Selection([('bds','BDS'),('phone','Phone'),('laptop','Laptop')], default='bds')
    cate = fields.Char( default='bds')
    set_number_of_page_once_fetch = fields.Integer(default=5)
    set_leech_max_page = fields.Integer()
    sell_or_rent =  fields.Selection([('sell','sell'), ('rent', 'rent')], default='sell')
    priority = fields.Integer()
    minute_change =  fields.Integer(compute='_minute_change')

    def _minute_change(self):
        for r in self:
            print ('**r.write_date',r.write_date,type(r.write_date), datetime.datetime.now())
            r.minute_change = (r.write_date - datetime.datetime.now()).seconds/60

    def get_last_page_number(self):
        if self.siteleech_id.name =='chotot':
            page_1st_url = create_cho_tot_page_link(self.url, 1)
            html = request_html(page_1st_url)
            html = json.loads(html)
            total = int(html["total"])
            print ('***total***', total)
            web_last_page_number = int(math.ceil(total/20.0))
            self.web_last_page_number = web_last_page_number

    def get_last_page_all_url(self):
        all_urls = self.search([])
        for r in all_urls:
            r.get_last_page_number()

    def fetch_this(self):
        self.env['abstract.fetch'].fetch_a_url_id (self)

    @api.multi
    def set_0(self):
        self.write({'current_page':0, 'create_link_number':0})

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
                r.siteleech_id = g_or_c_ss(self.env['bds.siteleech'], {'name':name})
