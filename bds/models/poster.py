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
    username = fields.Char(compute = 'username_')
    name = fields.Char(compute ='name_',store= True)
    @api.depends('phone')
    def name_(self):
        for r in self:
            r.name = r.phone
    post_ids = fields.One2many('bds.bds','poster_id')
    cong_ty = fields.Char()
    nhan_xet = fields.Char()
    nha_mang = fields.Selection([('vina','vina'),('mobi','mobi'),('viettel','viettel'),('khac','khac')],compute='nha_mang_',store=True)
    username_in_site_ids = fields.One2many('bds.posternamelines','poster_id')
    username_in_site_ids_show = fields.Char(compute='username_in_site_ids_show_')
    quan_id_for_search = fields.Many2one('res.country.district',related = 'quanofposter_ids.quan_id')
    quanofposter_ids_show = fields.Char(compute='quanofposter_ids_show_')
    site_ids = fields.Many2many('bds.siteleech')
    len_site = fields.Integer()

    du_doan_cc_or_mg = fields.Selection([('dd_mg','MG'),
                                         ('dd_dt','ĐT'),
                                         ('dd_cc','CC'),
                                         ('dd_kb', 'KB')],
                                         string="Dự đoán CC hay MG")
    chotot_mg_or_cc = fields.Selection([('moi_gioi','moi_gioi'), 
            ('chinh_chu','chinh_chu'), ('khong_biet', 'Không có bài ở chợ tốt')],
            )

            

    site_count_of_poster = fields.Integer()
    address_topic_number = fields.Integer()
    dd_tin_cua_co_rate = fields.Float(digits=(6,2))
    dd_tin_cua_dau_tu_rate = fields.Float(digits=(6,2) )
    address_rate = fields.Float(digits=(6,2))
                                        
    count_bds_post_of_poster = fields.Integer()
    count_post_all_site = fields.Integer()
    count_post_all_site_in_month = fields.Integer() 
    count_post_of_onesite_max = fields.Integer()
    siteleech_max_id = fields.Many2one('bds.siteleech')
    
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








    # quanofposter_ids = fields.One2many('bds.quanofposter', 'poster_id', compute='quanofposter_ids_', store = True)
    quanofposter_ids = fields.One2many('bds.quanofposter', 'poster_id')
    quan_chuyen_1 = fields.Many2one('bds.quanofposter', compute = 'quan_chuyen_1_')
    quan_chuyen_2 = fields.Many2one('bds.quanofposter', compute = 'quan_chuyen_1_')
    quan_chuyen_1_id = fields.Many2one('res.country.district', related ='quan_chuyen_1.quan_id' )
    number_post_of_quan = fields.Char(compute='number_post_of_quan_')
    created_by_site_id = fields.Many2one('bds.siteleech')
    block = fields.Boolean()


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
    def number_post_of_quan_(self):
        for r in self:
            qops = self.env['bds.quanofposter'].search([('poster_id','=',r.id), ('siteleech_id','!=',False)], order = 'quantity desc')
            alist = map(lambda i:u'%s_%s:%s'%(i.siteleech_id.name, i.quan_id.name_viet_tat, i.quantity), qops)
            rs = u', '.join(alist)
            r.number_post_of_quan = rs

    @api.multi
    def username_(self):
        for r in self:
            username_in_site_ids = r.username_in_site_ids
            if username_in_site_ids:
                username_in_site_id = username_in_site_ids[0]
                username = username_in_site_id.username_in_site
                sitename =username_in_site_id.site_id.name 
                if sitename == 'chotot':
                    shortsitename = 'ct'
                elif sitename == 'batdongsan':
                    shortsitename = 'bds'
                if sitename != 'muaban':
                    out = username.capitalize()#+ '-'+ shortsitename
                    r.username = out
                    
#     @api.depends('chotot_mg_or_cc', 'count_post_all_site', )

    @api.depends('quanofposter_ids')
    def quan_chuyen_1_(self):
        for r in self:
            qops = self.env['bds.quanofposter'].search([('poster_id','=',r.id), ('siteleech_id','=',False)], order = 'quantity desc', limit =2)
            if qops:
                r.quan_chuyen_1 = qops[0]
                if len(qops) == 2:
                    r.quan_chuyen_2 = qops[1]

    

    
    # @api.depends('post_ids','post_ids.gia')
    def quanofposter_ids_(self):#tạo sitequanofposter
        for r in self:
            if r.id:
                quanofposter_ids_lists= []
                product_category_query_siteleech =\
                 '''select count(quan_id),quan_id, min(gia), avg(gia), max(gia), siteleech_id from bds_bds where poster_id = %s  and gia > 0 group by quan_id,siteleech_id'''%r.id
                
                product_category_query_no_siteleech = \
                '''select count(quan_id),quan_id,min(gia),avg(gia),max(gia) from bds_bds where poster_id = %s  and gia > 0  group by quan_id'''%r.id
                
                all_site_all_quan = \
                '''select  count(quan_id),min(gia), avg(gia), max(gia) from bds_bds where poster_id = %s and gia > 0 '''%r.id
                
                a = {'product_category_query_siteleech':product_category_query_siteleech,
                     'product_category_query_no_siteleech':product_category_query_no_siteleech,
                     'all_site_all_quan':all_site_all_quan,
                     }
                for k,product_category_query in a.items():
                    self.env.cr.execute(product_category_query)
                    quan_va_gia_fetchall = self.env.cr.fetchall()
    
                    for  tuple_count_quan in quan_va_gia_fetchall:
                        offset = 0
                        if k =='all_site_all_quan':
                            siteleech_id =False
                            quan_id = False
                            offset = 1
                        elif k =='product_category_query_no_siteleech':
                            siteleech_id =False
                            quan_id = int(tuple_count_quan[1])
                        else:
                            quan_id = int(tuple_count_quan[1])
                            siteleech_id = int(tuple_count_quan[5])
                        quanofposter_search_dict =  {'quan_id':quan_id,
                            'poster_id':r.id,
                            'siteleech_id':siteleech_id 
                            }  
                        quanofposter_update_dict ={'quantity':tuple_count_quan[0],
                                'min_price':tuple_count_quan[2-offset],
                                'avg_price':tuple_count_quan[3-offset],
                                'max_price':tuple_count_quan[4-offset],
                                }
                        quanofposter = g_or_c_ss(self.env['bds.quanofposter'], quanofposter_search_dict, quanofposter_update_dict,update_no_need_check_change = True)
                        quanofposter_ids_lists.append(quanofposter[0].id)
                        
                        if siteleech_id ==False:
                            r.min_price = tuple_count_quan[2-offset]
                            r.avg_price = tuple_count_quan[3-offset]
                            r.max_price = tuple_count_quan[4-offset]
                r.quanofposter_ids = quanofposter_ids_lists                    
  
    @api.depends('username_in_site_ids')
    def username_in_site_ids_show_(self):
        for r in self:
            username_in_site_ids_shows = map(lambda r : r.username_in_site + '(' + r.site_id.name +   ')',r.username_in_site_ids)
            r.username_in_site_ids_show = ','.join(username_in_site_ids_shows)
                


    
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
                    
    # @api.depends('post_ids','post_ids.gia')
    # def quanofposter_ids_tanbinh(self):
    #     self.quanofposter_ids_common(u'Tân Bình')

    # def quanofposter_ids_common(self,quan_name):
    #     for r in self:
    #         if r.id:
    #             product_category_query =\
    #              '''select count(quan_id),quan_id,min(gia),avg(gia),max(gia) from bds_bds where poster_id = %s group by quan_id'''%r.id
    #             self.env.cr.execute(product_category_query)
    #             product_category = self.env.cr.fetchall()
    #             for  tuple_count_quan in product_category:
    #                 quan_id = int(tuple_count_quan[1])
    #                 quan = self.env['res.country.district'].browse(quan_id)
    #                 if quan.name in [quan_name]:#u'Quận 1',u'Quận 3',u'Quận 5',u'Quận 10',u'Tân Bình'
    #                     for key1 in ['count','avg']:
    #                         if key1 =='count':
    #                             value = tuple_count_quan[0]
    #                         elif key1 =='avg':
    #                             value = tuple_count_quan[3]
    #                         name = quan.name_unidecode.replace('-','_')
    #                         name = key1+'_'+name
    #                         setattr(r, name, value)
#                         #print 'set attr',name,value

    
    
                    
    
    @api.depends('quanofposter_ids')
    def quanofposter_ids_show_(self):
        for r in self:
            value =','.join(r.quanofposter_ids.mapped('name'))
            r.quanofposter_ids_show = value
  
    
    
    
    @api.depends('username_in_site_ids')
    def  site_count_of_poster_(self):
        for r in self:
            r.site_count_of_poster = len(r.username_in_site_ids)
            
            
    
            
   