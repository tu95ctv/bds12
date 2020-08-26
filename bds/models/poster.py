# -*- coding: utf-8 -*-

from odoo import models, fields, api,sql_db
import datetime
import re
from odoo.addons.bds.models.bds_tools import g_or_c_ss
from odoo.exceptions import UserError
import json
class Jsonb(fields.Char):
    column_cast_from = ('jsonb',)
    _slots = {
        'size': None,                   # maximum size of values (deprecated)
    }

    @property
    def column_type(self):
        return ('jsonb','jsonb')

    def convert_to_read(self, value, record, use_name_get=True):
        if isinstance(value,dict):
            value = str(value)
            value = value.replace("'",'"')
        return value
        
    def convert_to_column(self, value, record, values=None):
        if isinstance(value, dict):
            value = json.dumps(value)
        elif isinstance(value,str):
            value = value.replace("'",'"')
        return value

    def convert_to_cache(self, value, record, validate=True):
        if value and isinstance(value, str):
            value = value.replace("'",'"')
            value = json.loads(value)
        return value



class Poster(models.Model):
    _name = 'bds.poster'
    _order = 'count_post_all_site desc'
    site_post_count = Jsonb(default={})
    guess_count = Jsonb(default={})
    phone = fields.Char()
    login = fields.Char()
    name = fields.Char(compute ='name_',store= True)
    @api.depends('phone')
    def name_(self):
        for r in self:
            r.name = r.phone
    post_ids = fields.One2many('bds.bds','poster_id')
    nha_mang = fields.Selection([('vina','vina'),('mobi','mobi'),('viettel','viettel'),('khac','khac')],compute='nha_mang_',store=True)
    
    poster_line_ids = fields.One2many('bds.posternamelines','poster_id')
    poster_line_ids_show = fields.Char(compute='poster_line_ids_show_')
    @api.depends('poster_line_ids')
    def poster_line_ids_show_(self):
        for r in self:
            username_in_site_ids_shows = map(lambda r : r.username_in_site + '(' + r.site_id.name +   ')',r.poster_line_ids)
            r.poster_line_ids_show = ','.join(username_in_site_ids_shows)

    len_site = fields.Integer()
  

    count_post_all_site = fields.Integer()
    count_post_of_onesite_max = fields.Integer()
    siteleech_max_id = fields.Many2one('bds.siteleech')
    address_topic_number = fields.Integer()
    address_rate = fields.Float(digits=(6,2))
    dd_tin_cua_co_count = fields.Integer()
    dd_tin_cua_co_rate = fields.Float(digits=(6,2))
    dd_tin_cua_dau_tu_count = fields.Integer()
    dd_tin_cua_dau_tu_rate = fields.Float(digits=(6,2) )
    chotot_count = fields.Integer()
    chotot_mo_gioi_count = fields.Integer()
    chotot_chinh_chu_count = fields.Integer()
    du_doan_cc_or_mg = fields.Selection([('dd_mg','MG'),
                                         ('dd_dt','ĐT'),
                                         ('dd_cc','CC'),
                                         ('dd_kb', 'KB')],
                                         string="Dự đoán CC hay MG")
    chotot_mg_or_cc = fields.Selection([('moi_gioi','moi_gioi'), 
            ('chinh_chu','chinh_chu'), ('khong_biet', 'Không có bài ở chợ tốt')],
            )


    detail_du_doan_cc_or_mg = fields.Selection(
                                                  [('dd_cc_b_moi_gioi_n_address_rate_gt_0_5','dd_cc_b_moi_gioi_n_address_rate_gt_0_5'),
                                                   ('dd_mg_b_moi_gioi_n_address_rate_lte_0_5','dd_mg_b_moi_gioi_n_address_rate_lte_0_5'), 
                                                   ('dd_cc_b_kw_co_n_address_rate_gt_0_5', 'dd_cc_b_kw_co_n_address_rate_gt_0_5'),
                                                   ('dd_mg_b_kw_co_n_address_rate_lte_0_5','dd_mg_b_kw_co_n_address_rate_lte_0_5'),
                                                   
                                                   ('dd_cc_b_chinh_chu_n_cpas_gt_3_n_address_rate_gt_0', 'dd_cc_b_chinh_chu_n_cpas_gt_3_n_address_rate_gt_0'),
                                                   ('dd_mg_b_chinh_chu_n_cpas_gt_3_n_address_rate_eq_0', 'dd_mg_b_chinh_chu_n_cpas_gt_3_n_address_rate_eq_0'),
                                                   ('dd_cc_b_chinh_chu_n_cpas_lte_3_n_address_rate_gt_0_sure', 'dd_cc_b_chinh_chu_n_cpas_lte_3_n_address_rate_gt_0_sure'),
                                                   ('dd_cc_b_chinh_chu_n_cpas_lte_3_n_address_rate_eq_0_nosure', 'dd_cc_b_chinh_chu_n_cpas_lte_3_n_address_rate_eq_0_nosure'),

                                                   
                                                   
                                                   ('dd_cc_b_khong_biet_n_cpas_gt_3_n_address_rate_gte_0_3','dd_cc_b_khong_biet_n_cpas_gt_3_n_address_rate_gte_0_3'),
                                                   ('dd_mg_b_khong_biet_n_cpas_gt_3_n_address_rate_lt_0_3','dd_mg_b_khong_biet_n_cpas_gt_3_n_address_rate_lt_0_3'),
                                                   ('dd_cc_b_khong_biet_n_cpas_lte_3_n_address_rate_gt_0','dd_cc_b_khong_biet_n_cpas_lte_3_n_address_rate_gt_0'),
                                                   ('dd_kb','dd_kb'),
                                                   ('dd_kb_b_khong_biet_n_cpas_lte_3_n_address_rate_eq_0','dd_kb_b_khong_biet_n_cpas_lte_3_n_address_rate_eq_0')
                                                   ]
                                                   )



    @api.multi
    def open_something(self):
        return {
                'name': 'abc',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'bds.poster',
                'view_id': self.env.ref('bds.poster_form').id,
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'target': 'new'
            }

   
    
    @api.depends('phone')
    def nha_mang_(self):
        for r in self:
            patterns = {'vina':'(^091|^094|^083|^084|^085|^081|^082)',
                        'mobi':'(^090|^093|070|^079|^077|^076|^078)',
                       'viettel':'(^086|^096|^097|^098|^032|^033|^034|^035|^036|^037|^038|^039)'}
           
            if r.phone:
                for nha_mang,pattern in patterns.items():
                    rs = re.search(pattern, r.phone)
                    if rs:
                        r.nha_mang = nha_mang
                        break
                if not rs:
                    r.nha_mang = 'khac'
    
    

    
    
    
            
    
            
   