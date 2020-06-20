# -*- coding: utf-8 -*-
import re
import base64
from odoo import models, fields, api,sql_db, tools
from odoo.exceptions import UserError
from unidecode import unidecode
import datetime
from odoo.addons.bds.models.bds_tools  import  request_html
from odoo.exceptions import UserError

def trim_street_name(street_name_may_be):
    rs = re.sub(',|\.','', street_name_may_be, flags=re.I)
    rs = rs.strip()
    return rs

def detech_mat_tien(html):
    mat_tien_full_address_possibles = True
    before_index = 0
    deal_s = []
    full_adress_list = []
    while mat_tien_full_address_possibles:
        html = html [before_index:]
        p = '(?i:nhà|mt|mặt tiền|số)\s+(\d{1,4}[a-zA-Z]{0,2})\s+(?:đường)*\s*(?P<ten_duong>(?:[A-Z0-9Đ][\w|/]+\s*){1,4})(?:\.|\s|\,|$)'
        mat_tien_full_address_possibles = re.search(p, html)  #((\S+(?:\s|\.|$|,)+){1,4})
        if mat_tien_full_address_possibles:
            before_index = mat_tien_full_address_possibles.span()[1] + 1
            number = mat_tien_full_address_possibles.group(1)
            ten_duong = mat_tien_full_address_possibles.group('ten_duong')
            full_address = number + ' ' +  ten_duong
            full_address_unidecode = unidecode (full_address)
            if number not in deal_s:
                deal_s.append(number)

                check_co_word = re.search('\D', full_address)
                if not check_co_word:
                    continue
                pt = 'MT|Lầu|tấm|PN|WC|mặt|trệt|tầng|sẹc'
                pt = unidecode(pt)
                is_mt = re.search(pt, full_address_unidecode, re.I)
                if is_mt:
                    continue
                bao_nhieu_met = re.search('\d+m', number)
                if bao_nhieu_met:
                    continue

                index = mat_tien_full_address_possibles.span()[0]
                pre_index = index - 30
                if pre_index < 0:
                    pre_index = 0
                check_hem_string = html[pre_index:index]
                if check_hem_string:
                    is_hem = re.search('hẻm|hxt|đường', check_hem_string, re.I)
                    if is_hem:
                        continue
                full_adress_list.append(full_address)
    return full_adress_list

def detect_hem_address(address):
    posible_address_search = True
    keys_street_has_numbers = ['3/2','30/4','19/5','3/2.','3/2,','23/9']
    keys_24_7 = ['24/24','24/7','24/24h', '24/24H','24/24/7']
    pat_247 = '24h*/7|24h*/24|1/500'
    trust_address_result_keys = []
    only_number_trust_address_result_keys = []
    co_date_247_result_keys=[]
    index_before = 0
    while posible_address_search:
        address = address[index_before:]
        posible_address_search = re.search('(?P<adress_number>\d+\w{0,2}/\d+\w{0,2}(?:/\d+\w{0,2})*)\s+(?P<ten_duong>(?:[\w|/]+\s*){1,4})(?:\.|\s|,|$)', address)
        if posible_address_search:
            index_before = posible_address_search.span()[1]
            adress_number = posible_address_search.group('adress_number')
            street_name = posible_address_search.group('ten_duong')
            street_name = trim_street_name(street_name)
            full_adress = adress_number +' ' + street_name
            if adress_number not in only_number_trust_address_result_keys:
                black_list = '23/23 Nguyễn Hữu Tiến|5 Độc Lập'
                black_list_rs = re.search(black_list, address, re.I)
                if black_list_rs:
                    only_number_trust_address_result_keys.append(adress_number)
                    continue
                rs = re.search(pat_247, adress_number, re.I)
                if rs:
                    co_date_247_result_keys.append(adress_number)
                    continue
                if adress_number in keys_street_has_numbers:
                    # street_result_keys.append(adress_number)
                    continue
                is_day = re.search('\d+/\d\d\d\d', adress_number)
                if is_day:
                    continue
                is_ty_m2 =  re.search('tỷ|tr|m2', adress_number, re.I)
                if is_ty_m2:
                    continue
                
                index = posible_address_search.span()[0]
                before_index = index -20
                if before_index < 0:
                    before_index = 0
                before_string = address[before_index: index]
                is_van_phong = re.search('văn phòng|vp', before_string, re.I)
                if is_van_phong:
                    continue
                trust_address_result_keys.append((adress_number, full_adress))
                only_number_trust_address_result_keys.append(adress_number)
    return trust_address_result_keys, co_date_247_result_keys



def skip_if_cate_not_bds(depend_func):
    def wrapper(*args,**kargs):
        self = args[0]
        for r in self:
            if r.cate ==u'bds':
                depend_func(r)
    return wrapper

class UserReadMark(models.Model):
    _name = 'user.read.mark'

    user_id = fields.Many2one('res.users')
    bds_id = fields.Many2one('bds.bds')

class UserQuanTamMark(models.Model):
    _name = 'user.quantam.mark'

    user_id = fields.Many2one('res.users')
    bds_id = fields.Many2one('bds.bds')


class bds(models.Model):
    _name = 'bds.bds'
    _order = "id desc"
    _rec_name = 'title'
    
    user_read_mark_ids = fields.One2many('user.read.mark','bds_id')
    user_quantam_mark_ids = fields.One2many('user.quantam.mark','bds_id')
    sell_or_rent =  fields.Selection([('sell','sell'), ('rent', 'rent')], default='sell')
    loai_nha = fields.Char('Loại nhà')

    loai_nha_selection = fields.Selection('get_loai_nha_selection_', string='Loại nhà')

    link = fields.Char()
    # cate = fields.Selection([('bds','BDS'),('phone','Phone'),('laptop','Laptop')])
    cate = fields.Char(default='bds')
    url_id = fields.Many2one('bds.url')
    publicdate_ids =fields.One2many('bds.publicdate','bds_id')
    len_publicdate_ids = fields.Integer(compute='len_publicdate_ids_', store=True)
    public_date = fields.Date()
    diff_public_date = fields.Integer()
    gialines_ids = fields.One2many('bds.gialines','bds_id')
    title = fields.Char()
    images_ids = fields.One2many('bds.images', 'bds_id' )
    siteleech_id = fields.Many2one('bds.siteleech')
    thumb = fields.Char()
    poster_id = fields.Many2one('bds.poster')
    html = fields.Html()
    chotot_moi_gioi_hay_chinh_chu = fields.Selection([('moi_gioi', 'Bán chuyên'), 
        ('chinh_chu', 'Cá nhân'),('khong_biet','Không Phải bài ở chợt tốt')], default='khong_biet',string='Bán chuyên')
    gia = fields.Float('Giá')
    gia_trieu = fields.Float()
    area = fields.Float(digits=(32,1),string='Diện tích')
    address=fields.Char()
    quan_id = fields.Many2one('bds.quan',ondelete='restrict',string='Quận')
    phuong_id = fields.Many2one('bds.phuong','Phường')
    date_text = fields.Char()
    public_datetime = fields.Datetime()
    ngay_update_gia = fields.Datetime()
    diff_public_datetime = fields.Integer()
    #set field (field mà mình điền vào)
    is_read = fields.Boolean()
    quan_tam = fields.Datetime(string=u'Quan Tâm')
    ko_quan_tam = fields.Datetime(string=u'Không Quan Tâm')

    #compute field
    html_show = fields.Text(compute='html_show_',string=u'Nội dung')
    html_replace = fields.Html(compute='html_replace_')
    html_khong_dau = fields.Html(compute='html_khong_dau_',store=True)
    link_show =  fields.Char(compute='link_show_')
    mtg = fields.Boolean(compute = 'mien_tiep_mg_', store = True,string='Miễn trung gian')
    mqc = fields.Boolean(compute = 'mqc_', store = True)
    trich_dia_chi = fields.Char(compute='trich_dia_chi_', store = True,string='Trích địa chỉ')
    dd_tin_cua_co = fields.Boolean(compute='trich_dia_chi_', store = True, string='is có kw môi giới')
    kw_mg= fields.Char(compute='trich_dia_chi_', store = True, string='kw môi giới')
    dd_tin_cua_dau_tu = fields.Boolean(compute='_compute_dd_tin_cua_dau_tu', store = True,string='kw đầu tư')
    # subtitle_html_for_agency = fields.Html(compute='subtitle_html_for_agency_',store=True, string="Để làm cò")
    auto_ngang = fields.Float(compute = 'auto_ngang_doc_',store=True)
    auto_doc = fields.Float(compute = 'auto_ngang_doc_',store=True)
    auto_dien_tich = fields.Float(compute = 'auto_ngang_doc_',store=True)
    ti_le_dien_tich_web_vs_auto_dien_tich = fields.Float(compute = 'auto_ngang_doc_',store=True)
    choose_area = fields.Float(digits=(6,2), compute = 'auto_ngang_doc_')#,store=True
    same_address_bds_ids = fields.Many2many('bds.bds','same_bds_and_bds_rel','same_bds_id','bds_id',compute='same_address_bds_ids_',store=True)
    mien_tiep_mg = fields.Char(compute='mien_tiep_mg_', store=True)
    cho_tot_link_fake = fields.Char(compute='cho_tot_link_fake_')
    thumb_view = fields.Binary(compute='thumb_view_')  
    muc_gia = fields.Selection([('<1','<1'),('1-2','1-2'),('2-3','2-3'),
                                ('3-4','3-4'),('4-5','4-5'),('5-6','5-6'),
                                ('6-7','6-7'),('7-8','7-8'),('8-9','8-9'),
                                ('9-10','9-10'),('10-11','10-11'),('11-12','11-12'),('>12','>12')],
                               compute='muc_gia_',store = True,string=u'Mức Giá')
    muc_dt = fields.Selection(
        [('<10','<10'),('10-20','10-20'),('20-30','20-30'),('30-40','30-40'),('40-50','40-50'),('50-60','50-60'),('60-70','60-70'),('>70','>70')],
        compute='muc_dt_',store = True,string=u'Mức diện tích')
    don_gia = fields.Float(digit=(6,0),compute='don_gia_',store=True,string=u'Đơn giá')
    ti_le_don_gia = fields.Float(digits=(6,2),compute='ti_le_don_gia_',store=True)
    muc_don_gia = fields.Selection([('0-30','0-30'),('30-60','30-60'),('60-90','60-90'),
                                    ('90-120','90-120'),('120-150','120-150'),('150-180','150-180'),
                                    ('180-210','180-210'),('>210','>210')],compute='muc_don_gia_',store=True)
    muc_ti_le_don_gia = fields.Selection([('0-0.4','0-0.4'),('0.4-0.8','0.4-0.8'),('0.8-1.2','0.8-1.2'),
                                    ('1.2-1.6','1.2-1.6'),('1.6-2.0','1.6-2.0'),('2.0-2.4','2.0-2.4'),
                                    ('2.4-2.8','2.4-2.8'),('>2.8','>2.8')],compute='muc_ti_le_don_gia_',store=True)

    post_ids_of_user  = fields.One2many('bds.bds','poster_id',related='poster_id.post_ids')



    # detail_du_doan_cc_or_mg = fields.Selection(related='poster_id.detail_du_doan_cc_or_mg', store = True)
    # du_doan_cc_or_mg = fields.Selection(related='poster_id.du_doan_cc_or_mg', store = True)
    # count_chotot_post_of_poster = fields.Integer(related= 'poster_id.count_chotot_post_of_poster',store=True,string=u'chotot post quantity')
    # count_bds_post_of_poster = fields.Integer(related= 'poster_id.count_bds_post_of_poster',store=True,string=u'bds post quantity')
    # count_post_all_site = fields.Integer(related= 'poster_id.count_post_all_site',store=True)
    # dd_tin_cua_co_rate = fields.Float(related='poster_id.dd_tin_cua_co_rate', store  = True)
    # dd_tin_cua_dau_tu_rate = fields.Float(related='poster_id.dd_tin_cua_dau_tu_rate', store  = True)


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
                                                   ], compute='count_post_of_poster_',  store=True)

    du_doan_cc_or_mg = fields.Selection([('dd_mg','MG'),
                                         ('dd_dt','ĐT'),
                                         ('dd_cc','CC'),
                                         ('dd_kb', 'KB')],
                                        string="Dự đoán CC hay MG",
                                        compute='count_post_of_poster_', store=True
                                        )
    
    count_chotot_post_of_poster = fields.Integer(string=u'chotot count')
    count_bds_post_of_poster = fields.Integer()
    count_post_all_site = fields.Integer()
    dd_tin_cua_co_rate = fields.Float()
    dd_tin_cua_dau_tu_rate = fields.Float()



    @api.depends('poster_id')
    def count_post_of_poster_(self):
        for r in self:
            print ('kakakak trong bds_bds, count_post_of_poster_ ')
            bds_id = r
            r = bds_id.poster_id    

            count_chotot_post_of_poster = self.search_count([('poster_id','=',r.id),('siteleech_id.name','=', 'chotot')])
            r.count_chotot_post_of_poster = count_chotot_post_of_poster
            count_bds_post_of_poster = self.search_count([('poster_id','=',r.id),('link','like','batdongsan')])
            r.count_bds_post_of_poster = count_bds_post_of_poster
            
            count_post_all_site = self.search_count([('poster_id','=',r.id)])
            r.count_post_all_site = count_post_all_site
            count_post_all_site_in_month = self.search_count([('poster_id','=',r.id),('public_datetime','>',fields.Datetime.to_string(datetime.datetime.now() + datetime.timedelta(days=-30)))])
            r.count_post_all_site_in_month = count_post_all_site_in_month
            address_topic_number = self.search_count([('poster_id','=',r.id),('trich_dia_chi','!=', False)])
            r.address_topic_number= address_topic_number
            address_rate = 0

            if count_post_all_site:
                address_rate = address_topic_number/count_post_all_site
                r.address_rate = address_rate
                dd_tin_cua_co_count = self.search_count([('poster_id','=',r.id),('dd_tin_cua_co','=', True)])
                r.dd_tin_cua_co_rate = dd_tin_cua_co_count/count_post_all_site

                dd_tin_cua_dau_tu_count = self.search_count([('poster_id','=',r.id),('dd_tin_cua_dau_tu','=', True)])
                r.dd_tin_cua_dau_tu_rate = dd_tin_cua_dau_tu_count/count_post_all_site




            # mtg_number = self.search_count([('poster_id','=',r.id),('mtg','=',True)])
            # r.mtg_number = mtg_number
            
            # mqc_number = self.search_count([('poster_id','=',r.id),('mqc','=',True)])
            # r.mqc_number = mqc_number
            count_chotot_moi_gioi = self.search_count([('poster_id','=',r.id),('siteleech_id.name','=', 'chotot'), ('chotot_moi_gioi_hay_chinh_chu','=', 'moi_gioi')])
            if count_chotot_moi_gioi:
                chotot_mg_or_cc = 'moi_gioi'
            else:
                if count_chotot_post_of_poster:
                    chotot_mg_or_cc = 'chinh_chu'
                else:
                    chotot_mg_or_cc = 'khong_biet'
            # if count_chotot_post_of_poster:
            #     rate_moi_gioi = count_chotot_moi_gioi/count_chotot_post_of_poster
            #     rate_chinh_chu =   1 - rate_moi_gioi
            #     r.rate_chinh_chu = rate_chinh_chu
            #     r.rate_moi_gioi = rate_moi_gioi
            r.chotot_mg_or_cc = chotot_mg_or_cc
                    
            dd_tin_cua_co = self.search_count([('poster_id','=',r.id),('dd_tin_cua_co','!=', False)])
            dd_tin_cua_dau_tu = self.search_count([('poster_id','=',r.id),('dd_tin_cua_dau_tu','!=', False)])
            

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





    #!related
    # for filter field
    quan_id_selection = fields.Selection('get_quan_')
    greater_day = fields.Integer()
    siteleech_id_selection = fields.Selection('siteleech_id_selection_')
    is_user_read_mark = fields.Boolean(compute='_is_user_read_mark')
    is_user_quantam_mark = fields.Boolean(compute='_is_user_quantam_mark')
    mat_tien_address = fields.Char(compute ='_mat_tien_address', store=True)
    trigger = fields.Boolean()
    diff_public_days_from_now = fields.Integer(compute='_compute_diff_public_days_from_now', store=True)
    kw_hoa_hong = fields.Char(compute ='_compute_dd_tin_cua_dau_tu', store=True)
    kw_so_tien_hoa_hong = fields.Char(compute ='_compute_dd_tin_cua_dau_tu', store=True)

 
    so_lau = fields.Integer(compute ='_compute_so_lau')
    # so_tang = fields.Integer(compute ='_compute_so_lau', store=True)
    # is_co_lung = fields.Boolean(compute ='_compute_so_lau', store=True)

    @api.depends('html')
    def _compute_so_lau(self):
        for r in self:
            pt = '(\d{1,2})\s*lầu'
            rs = re.search(pt, r.html, re.I)
            if rs:
                so_lau = rs.group(1)
                try:
                    so_lau = int(so_lau)
                except:
                    so_lau = 0
                r.so_lau = so_lau




    @api.depends('public_date')
    def _compute_diff_public_days_from_now(self):
        for r in self:
            if r.public_date:
                r.diff_public_days_from_now = (fields.Date.today() - r.public_date).days


    @api.depends('html','trigger')
    def _mat_tien_address(self):
        for r in self:
            html = r.html
            if html:
                full_adress_list = detech_mat_tien(html)
                if full_adress_list:
                    r.mat_tien_address = ','.join(full_adress_list)

    def make_trigger(self):
        self.trigger = True

    # def test(self):
    #     query = "select html from bds_bds where html like 'mặt tiền' limit 2"
    #     rs =  self.env.cr.execute(query)

    #     raise UserError(rs)

    def test(self):
        rs = self.env['bds.bds'].read_group([],['loai_nha'],['loai_nha'])
        rs = map(lambda i: i['loai_nha'].replace('\n','') if i['loai_nha'] else i['loai_nha'], rs)
        rs = filter(lambda i: i != False, rs)
        rs = map(lambda i: (i,i), rs)
        rs = list(rs)
        self.env['ir.config_parameter'].set_param("bds.loai_nha", rs)

    def test2(self):
        rs = self.env['ir.config_parameter'].get_param("bds.loai_nha")
        rs = eval(rs)
        raise UserError('%s-%s'%(type(rs),str(rs)))
    
        


    def _is_user_quantam_mark(self):
        for r in self:
            user = self.env.user
            bds_id = r
            is_user_quantam_mark = self.env['user.quantam.mark'].search([('user_id','=',user.id), ('bds_id','=',bds_id.id)])
            r.is_user_quantam_mark = bool(is_user_quantam_mark)

    def _is_user_read_mark(self):
        for r in self:
            user = self.env.user
            bds_id = r
            user_read_mark = self.env['user.read.mark'].search([('user_id','=',user.id), ('bds_id','=',bds_id.id)])
            r.is_user_read_mark = bool(user_read_mark)

    # !for search
    
    def user_read_mark(self):
        for r in self:
            user = self.env.user
            bds_id = r
            user_read_mark = self.env['user.read.mark'].search([('user_id','=',user.id), ('bds_id','=',bds_id.id)])
            if not user_read_mark:
                self.env['user.read.mark'].create({'user_id':user.id, 'bds_id':bds_id.id })
    
    def user_not_read_mark(self):
        for r in self:
            user = self.env.user
            bds_id = r
            user_read_mark = self.env['user.read.mark'].search([('user_id','=',user.id), ('bds_id','=',bds_id.id)])
            user_read_mark.unlink()

    
    def user_quantam_mark(self):
        for r in self:
            user = self.env.user
            bds_id = r
            user_read_mark = self.env['user.quantam.mark'].search([('user_id','=',user.id), ('bds_id','=',bds_id.id)])
            if not user_read_mark:
                self.env['user.quantam.mark'].create({'user_id':user.id, 'bds_id':bds_id.id })
    
    def user_not_quantam_mark(self):
        for r in self:
            user = self.env.user
            bds_id = r
            user_read_mark = self.env['user.quantam.mark'].search([('user_id','=',user.id), ('bds_id','=',bds_id.id)])
            user_read_mark.unlink()



    

    @api.multi
    def open_something(self):
        return {
                'name': 'abc',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'bds.bds',
                'view_id': self.env.ref('bds.bds_form').id,
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'target': 'new'
            }


    def set_quan_tam(self):
        for r in self:
            r.quan_tam = fields.Datetime.now()

    # for filter function

    def siteleech_id_selection_(self):
        rs = list(map(lambda i:(i.name,i.name),self.env['bds.siteleech'].search([])))
        return rs

    def get_loai_nha_selection_(self):
        rs = self.env['ir.config_parameter'].get_param("bds.loai_nha")
        if rs:
            rs = eval(rs)
        else:
            rs = []
        return rs
        # return [('Căn hộ/Chung cư','Căn hộ/Chung cư'),('Nhà ở','Nhà ở'), ('Văn phòng, Mặt bằng kinh doanh','Văn phòng, Mặt bằng kinh doanh')]


    def get_quan_(self):
        quans = self.env['bds.quan'].search([])
        rs = list(map(lambda i:(i.name,i.name),quans))
        return rs
           
    #depends function
    @api.depends('publicdate_ids')
    def len_publicdate_ids_(self):
        for r in self:
            r.len_publicdate_ids = len(r.publicdate_ids)
    
    @api.depends('html')
    @skip_if_cate_not_bds
    def html_replace_(self):
        for r in self:
            html =  r.html
            html_replace = re.sub('[\d. ]{10,11}','',html)# replace số điện thoại
            if r.trich_dia_chi:
                html_replace = html_replace.replace(r.trich_dia_chi,'')
            r.html_replace = html_replace
            
    @api.depends('html')
    @skip_if_cate_not_bds
    def mien_tiep_mg_(self):
        for r in self:
            rs = re.search('(miễn|không)[\w ]{0,15}(môi giới|mg|trung gian|tg|cò)|mtg|mmg',r.html,re.I)
            if rs:
                r.mien_tiep_mg = rs.group(0)
                r.mtg = True


    def detect_hem_address_list(self, address_list):
        sum_trust_address_result_keys = [] 
        only_number_address_sum_trust_address_result_keys = [] 
        co_date_247_result_keys_sum = []
        for ad in address_list:
            trust_address_result_keys, co_date_247_result_keys = detect_hem_address(ad)
            co_date_247_result_keys_sum.extend(co_date_247_result_keys)
            for i in trust_address_result_keys:
                number_address = i[0]
                if number_address not in only_number_address_sum_trust_address_result_keys:
                    sum_trust_address_result_keys.append(i)
                    only_number_address_sum_trust_address_result_keys.append(number_address)
        return sum_trust_address_result_keys, co_date_247_result_keys_sum


    @api.depends('html', 'trigger')
    @skip_if_cate_not_bds 
    def trich_dia_chi_(self):
        for r in self:
            title = r.title
            html =  r.html
            address = r.address
            address_list = []
            if title:
                address_list.append(title)
            if html: 
                address_list.append(html)
            if address:
                address_list.append(address)
            sum_trust_address_result_keys, co_date_247_result_keys_sum = self.detect_hem_address_list(address_list)
            if sum_trust_address_result_keys:
                trich_dia_chi = ','.join(map(lambda i:i[1], sum_trust_address_result_keys))
                r.trich_dia_chi = trich_dia_chi
            
            found_kw_mgs = co_date_247_result_keys_sum
            kw_mgs= ['nhà đất', 'uy tín', 'real','mmg','mqc','mtg', 'bds', 'cần tuyển','tuyển sale', 'tuyển dụng', 'bất động sản','bđs','ký gửi','(?<!nova)land','tư vấn','thông tin chính xác']
            for key in kw_mgs:
                rs = re.search(key, html, re.I)
                if rs:
                    found_kw_mgs.append(rs.group(0))

            if found_kw_mgs:
                dd_tin_cua_co = True
                r.kw_mg = ','.join(found_kw_mgs)
                r.dd_tin_cua_co = dd_tin_cua_co


    @api.depends('trich_dia_chi')
    def same_address_bds_ids_(self):
        for r in self:
            if r.trich_dia_chi:
                same_address_bds_ids  = self.env['bds.bds'].search([('trich_dia_chi','=ilike',r.trich_dia_chi),('id','!=',r.id)])
                r.same_address_bds_ids = [(6,0,same_address_bds_ids.mapped('id'))]


    @api.depends('html','cate','area')
    @skip_if_cate_not_bds            
    def auto_ngang_doc_(self):
        for r in self:
            pt= '(\d{1,3}[\.,m]{0,1}\d{0,2}) {0,1}m{0,1}(( {0,1}x {0,1}))(\d{1,3}[\.,m]{0,1}\d{0,2})'
            rs = re.search(pt, r.html,flags = re.I)
            if rs:
                auto_ngang, auto_doc = float(rs.group(1).replace(',','.').replace('m','.').replace('M','.')),float(rs.group(4).replace(',','.').replace('m','.').replace('M','.'))
            elif not rs:
                pt= '(dài|rộng|chiều dài|chiều rộng)[: ]{1,2}(\d{1,3}[\.,m]{0,1}\d{0,2}) {0,1}m{0,1}(([, ]{1,3}(dài|rộng|chiều dài|chiều rộng)[: ]{1,2}))(\d{1,3}[\.,m]{0,1}\d{0,2})'
                rs = re.search(pt, r.html,flags = re.I)
                if rs:
                    auto_ngang, auto_doc = float(rs.group(2).replace(',','.').replace('m','.').replace('M','.')),float(rs.group(6).replace(',','.').replace('m','.').replace('M','.'))
            if rs and  auto_ngang and auto_doc:
                auto_dien_tich = auto_ngang*auto_doc
                rarea = r.area
                ti_le_dien_tich_web_vs_auto_dien_tich = rarea/auto_dien_tich
                r.auto_ngang,r.auto_doc, r.auto_dien_tich, r.ti_le_dien_tich_web_vs_auto_dien_tich = auto_ngang, auto_doc, auto_dien_tich, ti_le_dien_tich_web_vs_auto_dien_tich
               
                if rarea ==0:
                    r.choose_area = auto_dien_tich
                elif ti_le_dien_tich_web_vs_auto_dien_tich > 1.8:
                    r.choose_area = auto_dien_tich
                else:
                    r.choose_area = rarea
            else:
                r.choose_area = r.area

    

                







    @api.depends('html')
    @skip_if_cate_not_bds
    def mqc_(self):
        kss= ['quảng cáo','mqc','miễn qc','miễn tiếp báo']
        for r in self:
            is_match = False
            for ks in kss:
                rs = re.search(ks,r.html, re.I)
                if rs:
                    is_match = True
                    break
            if is_match:
                r.mqc = True


    def str_before_index(self, index, input_str):
        pre_index = index - 30
        if pre_index < 0:
            pre_index = 0
        pre_str = input_str[pre_index:index]
        return pre_str


    @api.depends('html','trigger')
    @skip_if_cate_not_bds               
    def _compute_dd_tin_cua_dau_tu(self):
        p = '((?<=\W)(?:hoa hồng|hh(?!t)|phí(?! hh| hoa hồng| huê hồng)|huê hồng|chấp nhận)\s*(?:cho)*\s*(?:mg|môi giới|mô giới|TG|Trung gian)*\s*((\d|\.)+\s*(%|triệu|tr))*)(?:\s+|$|<|\.|)'
        for r in self:
            rs = re.search(p, r.html, re.I)
            if rs:
                index = rs.span()[0]
                pre_str = self.str_before_index(index, r.html)
                khong_cho_mg = re.search('không', pre_str, re.I)
                if khong_cho_mg:
                    continue
                kw_hoa_hong = rs.group(1)
                if kw_hoa_hong.strip().lower() in  ['phí', 'chấp nhận']:
                    continue
                r.kw_hoa_hong = kw_hoa_hong
                r.kw_so_tien_hoa_hong = rs.group(2)
                r.dd_tin_cua_dau_tu = True
                break
           

                    
    def link_show_(self):
        for r in self:
            if r.siteleech_id.name == 'chotot':
                r.link_show = r.cho_tot_link_fake
            else:
                r.link_show = r.link
    
    @api.depends('html')
    def html_khong_dau_(self):
        for r in self:
            r.html_khong_dau = unidecode(r.html) if r.html else r.html
    
  

    @api.depends('ti_le_don_gia')
    def muc_ti_le_don_gia_(self):
        muc_dt_list =[('0-0.4','0-0.4'),('0.4-0.8','0.4-0.8'),('0.8-1.2','0.8-1.2'),
                                    ('1.2-1.6','1.2-1.6'),('1.6-2.0','1.6-2.0'),('2.0-2.4','2.0-2.4'),('2.4-2.8','2.4-2.8'),('>2.8','>2.8')]
        for r in self:
            selection = None
            for muc_gia_can_tren in range(1,8):
                if r.ti_le_don_gia < muc_gia_can_tren*0.4:
                    selection = muc_dt_list[muc_gia_can_tren-1][0]
                    r.muc_ti_le_don_gia = selection
                    break
            if not selection:
                r.muc_ti_le_don_gia = '>2.8'

    @api.depends('don_gia','quan_id')
    def ti_le_don_gia_(self):
        for r in self:
            try:
                if r.don_gia and r.quan_id.muc_gia_quan:
                    r.ti_le_don_gia = r.don_gia/r.quan_id.muc_gia_quan
            except:
                pass
                
    @api.depends('gia','area')
    def don_gia_(self):
        for r in self:
            if r.gia and r.area:
                r.don_gia = r.gia*1000/r.area
                
    @api.depends('don_gia')
    def muc_don_gia_(self):
        muc_dt_list =[('0-30','0-30'),('30-60','30-60'),('60-90','60-90'),
                                    ('90-120','90-120'),('120-150','120-150'),('150-180','150-180'),('180-210','180-210'),('>210','>210')]
        for r in self:
            selection = None
            for muc_gia_can_tren in range(1,8):
                if r.don_gia < muc_gia_can_tren*30:
                    selection = muc_dt_list[muc_gia_can_tren-1][0]
                    r.muc_don_gia = selection
                    break
            if not selection:
                r.muc_don_gia = '>210'

    @api.depends('area')
    def muc_dt_(self):
        muc_dt_list = [('<10','<10'),('10-20','10-20'),('20-30','20-30'),('30-40','30-40'),('40-50','40-50'),('50-60','50-60'),('60-70','60-70'),('>70','>70')]
        for r in self:
            selection = None
            for muc_gia_can_tren in range(1,8):
                if r.area < muc_gia_can_tren*10:
                    selection = muc_dt_list[muc_gia_can_tren-1][0]
                    r.muc_dt = selection
                    break
            if not selection:
                r.muc_dt = '>70'

    @api.depends('gia')
    def muc_gia_(self):
        muc_gia_list = [('<1','<1'),('1-2','1-2'),('2-3','2-3'),('3-4','3-4'),('4-5','4-5'),('5-6','5-6'),('6-7','6-7'),('7-8','7-8'),('8-9','8-9'),('9-10','9-10'),('10-11','10-11'),('11-12','11-12'),('>12','>12')]
        for r in self:
            selection = None
            for muc_gia_can_tren in range(1,len(muc_gia_list)):
                if r.gia < muc_gia_can_tren:
                    selection = muc_gia_list[muc_gia_can_tren-1][0]
                    r.muc_gia = selection
                    break
            if not selection:
                r.muc_gia = muc_gia_list[-1][0]


    @api.depends('html')
    def html_show_(self):
        for r in self:
            r.html_show = 'id:%s <b>%s</b>'%(r.id, r.title if r.title else '') + \
            ('\n' + '<b>%s</b>'%r.quan_id.name if r.quan_id.name  else '') +\
            ('\n<br>' + r.html if r.html else '') +\
            ('\n<br>Phone: ' + (r.poster_id.name or '')) +\
            ('\n<br>' +r.link_show if  r.link_show else '')+ \
            ('\n<br> Giá: <b>%s tỷ</b>'%(r.gia if r.gia else '')) +\
            ('\n<br> kích thước: %s'%('<b>%sm x %sm</b>'%(r.auto_ngang, r.auto_doc) if (r.auto_ngang or r.auto_doc) else ''))+\
            ('\n<br> Area: %s'%('<b>%s m2</b>'%r.area if r.area else ''))+\
            ('\n<br> Chọn lại diện tích: %s'%('<b>%s m2</b>'%r.choose_area if r.choose_area else ''))+\
            ('\n<br>Site: %s'%r.siteleech_id.name) +\
            ('\n<br>Đơn giá: %.2f'%r.don_gia) + \
            ('\n<br>Tỉ lệ đơn giá: %.2f'%r.ti_le_don_gia)  + \
            ('\n<br>Tổng số bài của người này: <b>%s</b>'%r.count_post_all_site) +\
            ('\n<br>Chợ tốt CC or MG: %s' %dict(self.env['bds.bds']._fields['chotot_moi_gioi_hay_chinh_chu'].selection).get(r.chotot_moi_gioi_hay_chinh_chu))+\
            ('\n<br>du_doan_cc_or_mg: <b>%s </b>'%dict(self.env['bds.poster']._fields['du_doan_cc_or_mg'].selection).get(r.poster_id.du_doan_cc_or_mg))+\
            ('\n<br>detail_du_doan_cc_or_mg: %s'%r.poster_id.detail_du_doan_cc_or_mg) +\
            ('\n<br> address_rate: %s'%r.poster_id.address_rate) +\
            ('\n<br>tỉ lệ keyword cò : %s'%r.poster_id.dd_tin_cua_co_rate) +\
            ('\n<br>tỉ lệ keyword đầu tư: %s'%r.poster_id.dd_tin_cua_dau_tu_rate)

            


    @api.depends('link')
    def cho_tot_link_fake_(self):
        for r in self:
            if r.link and 'chotot' in r.link:
                rs = re.search('/(\d*)$',r.link)
                id_link = rs.group(1)
                r.cho_tot_link_fake = 'https://nha.chotot.com/quan-10/mua-ban-nha-dat/' + 'xxx-' + id_link+ '.htm'
                

    @api.depends('thumb')
    def thumb_view_(self):
        for r in self:
            if r.thumb:
                if 'nophoto' not in r.thumb:
                    photo = base64.encodestring(request_html(r.thumb, False, is_decode_utf8 = False))
                    r.thumb_view = photo 

    def send_mail_chinh_chu(self):
        body_html = ''
        minutes = int(self.env['ir.config_parameter'].sudo().get_param('bds.interval_mail_chinh_chu_minutes',default=0))
        if minutes ==0:
            minutes=5
        gia = float(self.env['ir.config_parameter'].sudo().get_param('bds.gia',default=0))
        if gia ==0:
            gia =100

        minutes_5_last = fields.Datetime.now() -   datetime.timedelta(minutes=minutes, seconds=1)
        cr = self.search([('create_date','>', minutes_5_last), ('trich_dia_chi','!=',False),
            ('du_doan_cc_or_mg','in', ['dd_cc', 'dd_dt']), ('gia','<', gia), 
            ('quan_id.name', 'in',['Quận 1','Quận 3', 'Quận 5', 'Quận 10', 'Quận Tân Bình', 'Quận Tân Phú', 'Quận Phú Nhuận', 'Quận Bình Thạnh'])
            ])
        if cr:
            for r in cr:
                # one_mail_html = one_mail_template%(r.title, r.html_show)
                one_mail_html = r.html_show
                images = r.images_ids
                image_tags = map(lambda i: '<img src="%s" style="width:300px" alt="Girl in a jacket">'%i, list(images.mapped('url')) + [r.thumb])
                image_html = '<br>'.join(image_tags)
                # print ('***image_html**', image_html)
                one_mail_html += '<br>' + image_html

                body_html += '<br><br><br>' + one_mail_html
            # raise UserError(str(cr))
            # recipient_ids = [(6,0,self.hcm_department_id.manager_ids.ids)] if self.hcm_department_id.manager_ids.ids else False
            email_to = self.env['ir.config_parameter'].sudo().get_param('bds.email_to')
            if email_to:
                email_to = email_to.split(',')
            else:
                email_to = []
            email_to.append('nguyenductu@gmail.com')
            email_to = ','.join(email_to)
            mail_id = self.env['mail.mail'].create({
                'subject':'%s topic chính chủ trong 5 phút qua'%(len(cr)),
                # 'recipient_ids':recipient_ids,
                # 'mail_message_id':mme_id.id,
                'email_to':email_to,
                'body_html': body_html,
                })
            mail_id.send()


    
        

               

