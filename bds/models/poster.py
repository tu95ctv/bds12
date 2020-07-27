# -*- coding: utf-8 -*-

from odoo import models, fields, api,sql_db
import datetime
import re
from odoo.addons.bds.models.bds_tools import g_or_c_ss
from odoo.exceptions import UserError

class Poster(models.Model):
    _name = 'bds.poster'
    _order = 'count_post_all_site desc'
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
    # site_ids = fields.Many2many('bds.siteleech','site_poster_rel','siteleech_id', 'poster_id')
    site_ids = fields.Many2many('bds.siteleech')
    len_site = fields.Integer(compute='_compute_len_site', store=True)

    @api.depends('site_ids')
    def _compute_len_site(self):
        for r in self:
            r.len_site = len(r.site_ids)




   



    # site_count_of_poster = fields.Integer(, store=True)
    # address_topic_number = fields.Integer(compute ='count_post_of_poster_', store=True)
    # chotot_mg_or_cc = fields.Selection([('moi_gioi','moi_gioi'), 
    #         ('chinh_chu','chinh_chu'), ('khong_biet', 'Không có bài ở chợ tốt')],
    #         compute ='count_post_of_poster_', store=True)
    # dd_tin_cua_co_rate = fields.Float(digits=(6,2), compute ='count_post_of_poster_', store=True)
    # dd_tin_cua_dau_tu_rate = fields.Float(digits=(6,2), compute ='count_post_of_poster_', store=True)
    # address_rate = fields.Float(digits=(6,2),compute ='count_post_of_poster_', store=True)
    # du_doan_cc_or_mg = fields.Selection([('dd_mg','MG'),
    #                                      ('dd_dt','ĐT'),
    #                                      ('dd_cc','CC'),
    #                                      ('dd_kb', 'KB')],
    #                                     compute = 'count_post_of_poster_', string="Dự đoán CC hay MG", store=True)
    # count_chotot_post_of_poster = fields.Integer(compute='count_post_of_poster_',string=u'chotot count', store=True)
    # count_bds_post_of_poster = fields.Integer(compute='count_post_of_poster_', store=True)
    # count_post_all_site = fields.Integer(compute='count_post_of_poster_', store=True)
    # count_post_all_site_in_month = fields.Integer(compute='count_post_of_poster_', store=True) 
    # detail_du_doan_cc_or_mg = fields.Selection(
    #                                               [('dd_cc_b_moi_gioi_n_address_rate_gt_0_5','dd_cc_b_moi_gioi_n_address_rate_gt_0_5'),
    #                                                ('dd_mg_b_moi_gioi_n_address_rate_lte_0_5','dd_mg_b_moi_gioi_n_address_rate_lte_0_5'), 
    #                                                ('dd_cc_b_kw_co_n_address_rate_gt_0_5', 'dd_cc_b_kw_co_n_address_rate_gt_0_5'),
    #                                                ('dd_mg_b_kw_co_n_address_rate_lte_0_5','dd_mg_b_kw_co_n_address_rate_lte_0_5'),
                                                   
    #                                                ('dd_cc_b_chinh_chu_n_cpas_gt_3_n_address_rate_gt_0', 'dd_cc_b_chinh_chu_n_cpas_gt_3_n_address_rate_gt_0'),
    #                                                ('dd_mg_b_chinh_chu_n_cpas_gt_3_n_address_rate_eq_0', 'dd_mg_b_chinh_chu_n_cpas_gt_3_n_address_rate_eq_0'),
    #                                                ('dd_cc_b_chinh_chu_n_cpas_lte_3_n_address_rate_gt_0_sure', 'dd_cc_b_chinh_chu_n_cpas_lte_3_n_address_rate_gt_0_sure'),
    #                                                ('dd_cc_b_chinh_chu_n_cpas_lte_3_n_address_rate_eq_0_nosure', 'dd_cc_b_chinh_chu_n_cpas_lte_3_n_address_rate_eq_0_nosure'),

                                                   
                                                   
    #                                                ('dd_cc_b_khong_biet_n_cpas_gt_3_n_address_rate_gte_0_3','dd_cc_b_khong_biet_n_cpas_gt_3_n_address_rate_gte_0_3'),
    #                                                ('dd_mg_b_khong_biet_n_cpas_gt_3_n_address_rate_lt_0_3','dd_mg_b_khong_biet_n_cpas_gt_3_n_address_rate_lt_0_3'),
    #                                                ('dd_cc_b_khong_biet_n_cpas_lte_3_n_address_rate_gt_0','dd_cc_b_khong_biet_n_cpas_lte_3_n_address_rate_gt_0'),
    #                                                ('dd_kb','dd_kb'),
    #                                                ('dd_kb_b_khong_biet_n_cpas_lte_3_n_address_rate_eq_0','dd_kb_b_khong_biet_n_cpas_lte_3_n_address_rate_eq_0')
    #                                                ], store=True
    #                                                )



    # site_count_of_poster = fields.Integer()
    # address_topic_number = fields.Integer(compute ='count_post_of_poster_')
    # chotot_mg_or_cc = fields.Selection([('moi_gioi','moi_gioi'), 
    #         ('chinh_chu','chinh_chu'), ('khong_biet', 'Không có bài ở chợ tốt')],
    #         compute ='count_post_of_poster_')
    # dd_tin_cua_co_rate = fields.Float(digits=(6,2), compute ='count_post_of_poster_')
    # dd_tin_cua_dau_tu_rate = fields.Float(digits=(6,2), compute ='count_post_of_poster_')
    # address_rate = fields.Float(digits=(6,2),compute ='count_post_of_poster_')
    # du_doan_cc_or_mg = fields.Selection([('dd_mg','MG'),
    #                                      ('dd_dt','ĐT'),
    #                                      ('dd_cc','CC'),
    #                                      ('dd_kb', 'KB')],
    #                                     compute = 'count_post_of_poster_', string="Dự đoán CC hay MG")
    # count_chotot_post_of_poster = fields.Integer(compute='count_post_of_poster_',string=u'chotot count')
    # count_bds_post_of_poster = fields.Integer(compute='count_post_of_poster_')
    # count_post_all_site = fields.Integer(compute='count_post_of_poster_',store=True)
    # count_post_all_site_in_month = fields.Integer(compute='count_post_of_poster_') 
    # detail_du_doan_cc_or_mg = fields.Selection(
    #                                               [('dd_cc_b_moi_gioi_n_address_rate_gt_0_5','dd_cc_b_moi_gioi_n_address_rate_gt_0_5'),
    #                                                ('dd_mg_b_moi_gioi_n_address_rate_lte_0_5','dd_mg_b_moi_gioi_n_address_rate_lte_0_5'), 
    #                                                ('dd_cc_b_kw_co_n_address_rate_gt_0_5', 'dd_cc_b_kw_co_n_address_rate_gt_0_5'),
    #                                                ('dd_mg_b_kw_co_n_address_rate_lte_0_5','dd_mg_b_kw_co_n_address_rate_lte_0_5'),
                                                   
    #                                                ('dd_cc_b_chinh_chu_n_cpas_gt_3_n_address_rate_gt_0', 'dd_cc_b_chinh_chu_n_cpas_gt_3_n_address_rate_gt_0'),
    #                                                ('dd_mg_b_chinh_chu_n_cpas_gt_3_n_address_rate_eq_0', 'dd_mg_b_chinh_chu_n_cpas_gt_3_n_address_rate_eq_0'),
    #                                                ('dd_cc_b_chinh_chu_n_cpas_lte_3_n_address_rate_gt_0_sure', 'dd_cc_b_chinh_chu_n_cpas_lte_3_n_address_rate_gt_0_sure'),
    #                                                ('dd_cc_b_chinh_chu_n_cpas_lte_3_n_address_rate_eq_0_nosure', 'dd_cc_b_chinh_chu_n_cpas_lte_3_n_address_rate_eq_0_nosure'),

                                                   
                                                   
    #                                                ('dd_cc_b_khong_biet_n_cpas_gt_3_n_address_rate_gte_0_3','dd_cc_b_khong_biet_n_cpas_gt_3_n_address_rate_gte_0_3'),
    #                                                ('dd_mg_b_khong_biet_n_cpas_gt_3_n_address_rate_lt_0_3','dd_mg_b_khong_biet_n_cpas_gt_3_n_address_rate_lt_0_3'),
    #                                                ('dd_cc_b_khong_biet_n_cpas_lte_3_n_address_rate_gt_0','dd_cc_b_khong_biet_n_cpas_lte_3_n_address_rate_gt_0'),
    #                                                ('dd_kb','dd_kb'),
    #                                                ('dd_kb_b_khong_biet_n_cpas_lte_3_n_address_rate_eq_0','dd_kb_b_khong_biet_n_cpas_lte_3_n_address_rate_eq_0')
    #                                                ]
    #                                                )



    site_count_of_poster = fields.Integer()
    address_topic_number = fields.Integer()
    chotot_mg_or_cc = fields.Selection([('moi_gioi','moi_gioi'), 
            ('chinh_chu','chinh_chu'), ('khong_biet', 'Không có bài ở chợ tốt')],
            )
    dd_tin_cua_co_rate = fields.Float(digits=(6,2))
    dd_tin_cua_dau_tu_rate = fields.Float(digits=(6,2) )
    address_rate = fields.Float(digits=(6,2))
    du_doan_cc_or_mg = fields.Selection([('dd_mg','MG'),
                                         ('dd_dt','ĐT'),
                                         ('dd_cc','CC'),
                                         ('dd_kb', 'KB')],
                                         string="Dự đoán CC hay MG")
    count_chotot_post_of_poster = fields.Integer(string=u'chotot count')
    count_bds_post_of_poster = fields.Integer()
    count_post_all_site = fields.Integer(store=True)
    count_post_all_site_in_month = fields.Integer() 
    count_post_of_onesite_max = fields.Integer(store=True)
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

    # @api.depends('post_ids','post_ids.trich_dia_chi', 'post_ids.dd_tin_cua_dau_tu', 'post_ids.dd_tin_cua_co')
    @api.depends('post_ids')
    def count_post_of_poster_(self):
        bds_obj = self.env['bds.bds']
        for r in self:
            count_post_all_site = bds_obj.search_count([('poster_id','=',r.id)])
            r.count_post_all_site = count_post_all_site
            # return count_post_all_site
            count_chotot_post_of_poster = bds_obj.search_count([('poster_id','=',r.id),('siteleech_id.name','=', 'chotot')])
            r.count_chotot_post_of_poster = count_chotot_post_of_poster
            count_bds_post_of_poster = bds_obj.search_count([('poster_id','=',r.id),('link','like','batdongsan')])
            r.count_bds_post_of_poster = count_bds_post_of_poster
            count_post_all_site_in_month = bds_obj.search_count([('poster_id','=',r.id),('public_datetime','>',fields.Datetime.to_string(datetime.datetime.now() + datetime.timedelta(days=-30)))])
            r.count_post_all_site_in_month = count_post_all_site_in_month
            address_topic_number = bds_obj.search_count([('poster_id','=',r.id),('trich_dia_chi','!=', False)])
            r.address_topic_number= address_topic_number
            address_rate = 0
            if count_post_all_site:
                address_rate = address_topic_number/count_post_all_site
                r.address_rate = address_rate
                dd_tin_cua_co_count = bds_obj.search_count([('poster_id','=',r.id),('dd_tin_cua_co','=', True)])
                r.dd_tin_cua_co_rate = dd_tin_cua_co_count/count_post_all_site

                dd_tin_cua_dau_tu_count = bds_obj.search_count([('poster_id','=',r.id),('dd_tin_cua_dau_tu','=', True)])
                r.dd_tin_cua_dau_tu_rate = dd_tin_cua_dau_tu_count/count_post_all_site

            count_chotot_moi_gioi = bds_obj.search_count([('poster_id','=',r.id),('siteleech_id.name','=', 'chotot'), ('chotot_moi_gioi_hay_chinh_chu','=', 'moi_gioi')])
            if count_chotot_moi_gioi:
                chotot_mg_or_cc = 'moi_gioi'
            else:
                if count_chotot_post_of_poster:
                    chotot_mg_or_cc = 'chinh_chu'
                else:
                    chotot_mg_or_cc = 'khong_biet'
            r.chotot_mg_or_cc = chotot_mg_or_cc
            dd_tin_cua_co = bds_obj.search_count([('poster_id','=',r.id),('dd_tin_cua_co','=', 'kw_co_cap_1')])
            dd_tin_cua_dau_tu = bds_obj.search_count([('poster_id','=',r.id),('dd_tin_cua_dau_tu','!=', False)])
            
            if chotot_mg_or_cc =='moi_gioi' :
                if address_rate > 0.5:
                    du_doan_cc_or_mg= 'dd_cc'
                    detail_du_doan_cc_or_mg = 'dd_cc_b_moi_gioi_n_address_rate_gt_0_5'
                else:
                    du_doan_cc_or_mg= 'dd_mg'
                    detail_du_doan_cc_or_mg = 'dd_mg_b_moi_gioi_n_address_rate_lte_0_5'
            elif dd_tin_cua_co:
                if address_rate > 0.5:
                    du_doan_cc_or_mg= 'dd_cc'
                    detail_du_doan_cc_or_mg = 'dd_cc_b_kw_co_n_address_rate_gt_0_5'
                else:
                    du_doan_cc_or_mg= 'dd_mg'
                    detail_du_doan_cc_or_mg = 'dd_mg_b_kw_co_n_address_rate_lte_0_5'
            else:
                if chotot_mg_or_cc =='chinh_chu':
                    
                    if count_post_all_site > 3:
                        if address_rate > 0:
                            du_doan_cc_or_mg= 'dd_cc'
                            detail_du_doan_cc_or_mg = 'dd_cc_b_chinh_chu_n_cpas_gt_3_n_address_rate_gt_0'
                        else:
                            du_doan_cc_or_mg= 'dd_mg'
                            detail_du_doan_cc_or_mg = 'dd_mg_b_chinh_chu_n_cpas_gt_3_n_address_rate_eq_0'
                    else:
                        du_doan_cc_or_mg= 'dd_cc'
                        if address_rate > 0:
                            detail_du_doan_cc_or_mg = 'dd_cc_b_chinh_chu_n_cpas_lte_3_n_address_rate_gt_0_sure'
                        else:
                            detail_du_doan_cc_or_mg = 'dd_cc_b_chinh_chu_n_cpas_lte_3_n_address_rate_eq_0_nosure' 
                else:#khong_biet, muaban
                    if count_post_all_site  > 3:
                        if address_rate >= 0.3:
                            du_doan_cc_or_mg= 'dd_cc'
                            detail_du_doan_cc_or_mg = 'dd_cc_b_khong_biet_n_cpas_gt_3_n_address_rate_gte_0_3'
                        else:
                            du_doan_cc_or_mg= 'dd_mg'
                            detail_du_doan_cc_or_mg = 'dd_mg_b_khong_biet_n_cpas_gt_3_n_address_rate_lt_0_3'
                            
                    else: #count_post_all_site  <= 3
                        if address_rate: 
                            du_doan_cc_or_mg= 'dd_cc'
                            detail_du_doan_cc_or_mg = 'dd_cc_b_khong_biet_n_cpas_lte_3_n_address_rate_gt_0'
                        else:
                            du_doan_cc_or_mg= 'dd_kb'
                            detail_du_doan_cc_or_mg = 'dd_kb_b_khong_biet_n_cpas_lte_3_n_address_rate_eq_0'

            if du_doan_cc_or_mg !='dd_mg':
                if  dd_tin_cua_dau_tu:
                    du_doan_cc_or_mg= 'dd_dt'
                    
                    
            r.du_doan_cc_or_mg = du_doan_cc_or_mg
            r.detail_du_doan_cc_or_mg = detail_du_doan_cc_or_mg     

    
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
                    
    @api.depends('post_ids','post_ids.gia')
    def quanofposter_ids_tanbinh(self):
        self.quanofposter_ids_common(u'Tân Bình')

    def quanofposter_ids_common(self,quan_name):
        for r in self:
            if r.id:
                product_category_query =\
                 '''select count(quan_id),quan_id,min(gia),avg(gia),max(gia) from bds_bds where poster_id = %s group by quan_id'''%r.id
                self.env.cr.execute(product_category_query)
                product_category = self.env.cr.fetchall()
                for  tuple_count_quan in product_category:
                    quan_id = int(tuple_count_quan[1])
                    quan = self.env['res.country.district'].browse(quan_id)
                    if quan.name in [quan_name]:#u'Quận 1',u'Quận 3',u'Quận 5',u'Quận 10',u'Tân Bình'
                        for key1 in ['count','avg']:
                            if key1 =='count':
                                value = tuple_count_quan[0]
                            elif key1 =='avg':
                                value = tuple_count_quan[3]
                            name = quan.name_unidecode.replace('-','_')
                            name = key1+'_'+name
                            setattr(r, name, value)
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
            
            
    
            
   