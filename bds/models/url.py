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
    # _rec_name = 'description'
    _order = 'priority asc'

    name = fields.Char(compute='_compute_name', store=True)
    
    @api.depends('description','siteleech_id')
    def _compute_name(self):
        for r in self:
            r.name = '%s-%s'%(r.siteleech_id.name, r.description)

    url = fields.Char()
    description = fields.Char()
    description_unidecode = fields.Char(compute='description_unidecode_', store = True)
    cate = fields.Char( default='bds')
    siteleech_id = fields.Many2one('bds.siteleech',compute='siteleech_id_',store=True)
    web_last_page_number = fields.Integer()
   
   
    # set_number_of_page_once_fetch = fields.Integer(default=5)
    # set_number_of_page_once_fetch2 = fields.Integer(default=2)
    # current_page = fields.Integer()
    # current_page_2 = fields.Integer()
    # update_link_number = fields.Integer(readonly=1)
    # create_link_number = fields.Integer(readonly=1)
    # existing_link_number = fields.Integer(readonly=1)
    # link_number = fields.Integer(readonly=1)
    # interval = fields.Integer(readonly=1)
    # set_leech_max_page = fields.Integer()
    # set_leech_max_page2 = fields.Integer()
    # min_page = fields.Integer()
    # is_finished = fields.Boolean()

    
    sell_or_rent =  fields.Selection([('sell','sell'), ('rent', 'rent')], default='sell')
    priority = fields.Integer()
    minute_change =  fields.Integer(compute='_minute_change')


    @api.depends('description')
    def description_unidecode_(self):
        for r in self:
            r.description_unidecode = unidecode(r.description)



    def _minute_change(self):
        for r in self:
            r.minute_change = (r.write_date - datetime.datetime.now()).seconds/60

    def get_last_page_number(self):
        if self.siteleech_id.name =='chotot':
            page_1st_url = create_cho_tot_page_link(self.url, 1)
            html = request_html(page_1st_url)
            html = json.loads(html)
            total = int(html["total"])
            web_last_page_number = int(math.ceil(total/20.0))
            self.web_last_page_number = web_last_page_number

    def get_last_page_all_url(self):
        all_urls = self.search([])
        for r in all_urls:
            r.get_last_page_number()

    def fetch_this(self):
        self.env['abstract.main.fetch'].fetch_a_url_id (self)

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

    def tao_url_cho_tap_hoa_tinh_thanh(self):
        data_url_tinh_thanh = [{'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-ho-chi-minh/', 'count': 204067}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-ha-noi/', 'count': 122685}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-an-giang/', 'count': 37938}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-bac-giang/', 'count': 25680}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-bac-kan/', 'count': 6936}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-bac-lieu/', 'count': 11522}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-bac-ninh/', 'count': 17828}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-ben-tre/', 'count': 29564}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-binh-dinh/', 'count': 29289}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-binh-duong/', 'count': 34666}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-binh-phuoc/', 'count': 13959}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-binh-thuan/', 'count': 33458}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-ca-mau/', 'count': 19432}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-can-tho/', 'count': 28130}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-cao-bang/', 'count': 5612}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-da-nang/', 'count': 32133}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-dak-lak/', 'count': 26304}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-dak-nong/', 'count': 10776}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-dien-bien/', 'count': 4335}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-dong-nai/', 'count': 65935}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-dong-thap/', 'count': 33070}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-gia-lai/', 'count': 20164}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-ha-giang/', 'count': 7801}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-ha-nam/', 'count': 13121}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-ha-tinh/', 'count': 47359}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-hai-duong/', 'count': 31348}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-hai-phong/', 'count': 36813}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-hau-giang/', 'count': 8696}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-hoa-binh/', 'count': 9020}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-hung-yen/', 'count': 18083}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-khanh-hoa/', 'count': 29395}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-kien-giang/', 'count': 26598}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-kon-tum/', 'count': 9169}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-lai-chau/', 'count': 2573}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-lam-dong/', 'count': 26133}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-lang-son/', 'count': 11259}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-lao-cai/', 'count': 11058}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-long-an/', 'count': 32602}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-nam-dinh/', 'count': 30864}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-nghe-an/', 'count': 42807}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-ninh-binh/', 'count': 24334}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-ninh-thuan/', 'count': 7349}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-phu-tho/', 'count': 21067}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-phu-yen/', 'count': 15729}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-quang-binh/', 'count': 18317}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-quang-nam/', 'count': 26808}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-quang-ngai/', 'count': 19826}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-quang-ninh/', 'count': 24812}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-quang-tri/', 'count': 19806}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-soc-trang/', 'count': 13527}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-son-la/', 'count': 14513}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-tay-ninh/', 'count': 19949}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-thai-binh/', 'count': 22766}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-thai-nguyen/', 'count': 28759}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-thanh-hoa/', 'count': 84557}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-tien-giang/', 'count': 30951}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-tinh-ba-ria-vung-tau/', 'count': 15549}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-tinh-thua-thien-hue/', 'count': 26495}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-tra-vinh/', 'count': 17933}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-tuyen-quang/', 'count': 10842}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-vinh-long/', 'count': 18400}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-vinh-phuc/', 'count': 10195}, {'href': 'http://www.cuahangtaphoa.com/danh-sach-cua-hang-tap-hoa-yen-bai/', 'count': 13150}]
        URL_obj = self
        for i in data_url_tinh_thanh:
            url = i['href']
            description = i['href'].split('/')[-2]
            web_last_page_number = math.ceil(i['count']/20.0)
            url_obj = g_or_c_ss(self, {'url':url},
                {'web_last_page_number':web_last_page_number,'description':description,'cate':'tap hoa' }, 
                is_up_date=True)
            print ('***url_obj', url_obj)

    
