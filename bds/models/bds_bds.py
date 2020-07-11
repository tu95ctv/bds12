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

def detech_mat_tien(html, p = None):
    mat_tien_full_address_possibles = True
    before_index = 0
    deal_s = []
    full_adress_list = []
    while mat_tien_full_address_possibles:
        html = html [before_index:]
        # p = '(?i:nhà|mt|mặt tiền|số)\s+(\d{1,4}[a-zA-Z]{0,2})[\s,]+(?i:đường)*\s*(?P<ten_duong>(?:[A-Z0-9Đ][\w|/]*\s*){1,4})(?:\.|\s|\,|$|<)'
        mat_tien_full_address_possibles = re.search(p, html, re.I)  #((\S+(?:\s|\.|$|,)+){1,4})
        if mat_tien_full_address_possibles:
            before_index = mat_tien_full_address_possibles.span()[1] + 1
            number = mat_tien_full_address_possibles.group(1)
            ten_duong = mat_tien_full_address_possibles.group('ten_duong')
            is_check_word = re.search('[a-zđ]',ten_duong, re.I)
            if not is_check_word:
                continue
            full_address = number + ' ' +  ten_duong
            full_address_unidecode = unidecode (full_address)
            if number not in deal_s:
                deal_s.append(number)
                sxs = re.search('x(?: |$)',ten_duong, re.I) # có x trong tên đường
                if sxs:
                    continue
                # ddm = re.search('\d+m',ten_duong, re.I)
                # if ddm:
                #     continue
                ddm = re.search('(?:^|x|\*|\s)\s*\d+m',full_address, re.I)# check mét
                if ddm:
                    continue

                check_co_word = re.search('\D', full_address)
                if not check_co_word:
                    continue
                ten_duong_lower = ten_duong.strip().lower() 
                if ten_duong_lower in ['căn']:
                    continue
                pt = 'MT|Lầu|tỷ|căn|phòng|tấm|PN|WC|mặt|trệt|tầng|sẹc|sẹt|xẹc|xẹt|lửng|lững|trục đường|\dt\s*\dl'
                pt = unidecode(pt)
                is_mt = re.search(pt, full_address_unidecode, re.I)
                if is_mt:
                    continue
                bao_nhieu_met = re.search('\d+m', number)
                if bao_nhieu_met:
                    continue

                index = mat_tien_full_address_possibles.span()[0]
                pre_index = index - 12
                if pre_index < 0:
                    pre_index = 0
                check_hem_string = html[pre_index:index]
                if check_hem_string:
                    is_hem = re.search('hẻm|hxt|đường|bđs|cty|nhà đất|vp|văn phòng|phường|quận', check_hem_string, re.I)
                    if is_hem:
                        continue
                full_adress_list.append((number, full_address))
    return full_adress_list

def detect_hem_address(address):
    posible_address_search = True
    keys_street_has_numbers = ['3/2','30/4','19/5','3/2.','3/2,','23/9']
    # keys_24_7 = ['24/24','24/7','24/24h', '24/24H','24/24/7']
    pat_247 = '24h*/7|24h*/24|1/500'
    trust_address_result_keys = []
    only_number_trust_address_result_keys = []
    co_date_247_result_keys=[]
    index_before = 0
    while posible_address_search:
        address = address[index_before:]
        posible_address_search = re.search('(?P<adress_number>\d+\w{0,2}/\d+\w{0,2}(?:/\d+\w{0,2})*)[\s,]+(?:đường[\s,]+)*(?P<ten_duong>(?:[\w|/]+\s*){1,4})(?:\.|\s|,|$)', address)
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
                if adress_number in ['1/2','50/100','100/100']:
                    continue
                rs = re.search(pat_247, adress_number, re.I)
                if rs:
                    co_date_247_result_keys.append(rs.group(0))
                    continue
                if adress_number in keys_street_has_numbers:
                    # street_result_keys.append(adress_number)
                    continue
                is_day = re.search('\d+/\d\d\d\d', adress_number)
                if is_day:
                    continue
                pnwc = re.search('(?:pn|wc|x)', adress_number, re.I)
                if pnwc:
                    continue
                is_ty_m2 =  re.search('tỷ|tr|m2', full_adress, re.I)
                if is_ty_m2:
                    continue
                
                index = posible_address_search.span()[0]
                before_index = index -20
                if before_index < 0:
                    before_index = 0
                before_string = address[before_index: index]
                is_van_phong = re.search('văn phòng|vp|bđs|nhà đất', before_string, re.I)
                if is_van_phong:
                    continue
                trust_address_result_keys.append((adress_number, full_adress))
                only_number_trust_address_result_keys.append(adress_number)
    return trust_address_result_keys, co_date_247_result_keys

def tim_dien_tich_trong_bai(html):
    p ='(?:diện tích|dt|dtcn)[\W]*([1-9]+[\.,]\d+)\s*m2'
    rs = re.search(p, html, re.I)
    dt = 0
    if rs:
        dt = rs.group(1)
        dt = dt.replace(',','.')
        dt = float(dt)
    return dt

def tim_dien_tich_sd_trong_bai(html):
    p ='(?:(?:diện tích|dt)\s*(?:sử dụng|sd|sàn))[\W]*([0-9]+[\.,]*\d*)\s*m2'
    rs = re.search(p, html, re.I)
    dt = 0
    if rs:
        dt = rs.group(1)
        dt = dt.replace(',','.')
        dt = float(dt)
    return dt

def tim_dai_rong(html):
    auto_ngang, auto_doc = 0,0
    pt= '(\d{1,3}[\.,m]{0,1}\d{0,2}) {0,1}m{0,1}(( {0,1}[x*] {0,1}))(\d{1,3}[\.,m]{0,1}\d{0,2})'
    rs = re.search(pt, html,flags = re.I)
    
    if rs:
        auto_ngang, auto_doc = float(rs.group(1).replace(',','.').replace('m','.').replace('M','.')),float(rs.group(4).replace(',','.').replace('m','.').replace('M','.'))
    elif not rs:
        pt= '(dài|rộng|ngang)[: ]{1,2}(\d{1,3}[\.,m]{0,1}\d{0,2}) {0,1}m{0,1}(([\W]{1,3}(dài|rộng|ngang)[: ]{1,2}))(\d{1,3}[\.,m]{0,1}\d{0,2})'
        rs = re.search(pt, html,flags = re.I)
        if rs:
            auto_ngang, auto_doc = float(rs.group(2).replace(',','.').replace('m','.').replace('M','.')),float(rs.group(6).replace(',','.').replace('m','.').replace('M','.'))
    return auto_ngang, auto_doc

def auto_ngang_doc_compute(html,rarea):
    auto_ngang, auto_doc = tim_dai_rong(html)
    dien_tich_trong_topic = tim_dien_tich_trong_bai(html)
    choose_area = 0
    auto_dien_tich = 0
    ti_le_dien_tich_web_vs_auto_dien_tich = 0
    if auto_ngang and auto_doc:
        auto_dien_tich = auto_ngang*auto_doc
        ti_le_dien_tich_web_vs_auto_dien_tich = rarea/auto_dien_tich
        if rarea ==0:
            choose_area = auto_dien_tich 
        elif ti_le_dien_tich_web_vs_auto_dien_tich > 1.4:
            choose_area = auto_dien_tich
        else:
            choose_area = rarea
    else:
        choose_area = rarea or dien_tich_trong_topic
    return auto_ngang, auto_doc, auto_dien_tich, choose_area, ti_le_dien_tich_web_vs_auto_dien_tich,  dien_tich_trong_topic

def detech_hxh(html):
    p = '(?:h|hẻm|hẽm|d|đ|đường)\s{0,1}(?:xh|xe hơi)'
    rs = re.search(p, html, re.I)
    hxh_str, full_hxh = False,False
    if rs:
        span0 = rs.span(0)[0]
        pre_index = span0-30
        pre = html[pre_index:span0]
        gan_sat_cach_pt = 'gần|sát|cách'
        gan_sat_cach_search = re.search(gan_sat_cach_pt,pre, re.I)
        if gan_sat_cach_search:
            return hxh_str, full_hxh
        before_index = span0 + 10
        full_hxh = html[pre_index:before_index]
        hxh_str = rs.group(0)
    return hxh_str, full_hxh

def detech_is_mat_tien(html):
    # is_loop = True
    while 1:
        p = '(?:(?<!2 )mặt tiền|nhà mt|mặt phố)(?! hẻm)'
        rs = re.search(p, html, re.I)
        hxh_str, full_hxh,is_mat_tien = False,False,False
        if rs:
            span0 = rs.span(0)[0]
            pre_index = span0-10
            if pre_index<0:
                pre_index = 0
            pre = html[pre_index:span0]
            gan_sat_cach_pt = 'gần|sát|cách|hai|từ|ra'
            gan_sat_cach_search = re.search(gan_sat_cach_pt,pre, re.I)
            if gan_sat_cach_search:
                before_index = rs.span()[1] + 1
                html = html[before_index:]
                continue
            hxh_str = rs.group(0)
            full_before_index = rs.span(0)[1] + 10
            full_hxh = html[pre_index:full_before_index]
            is_mat_tien = True
            return hxh_str, full_hxh, is_mat_tien
        else:
            return hxh_str, full_hxh, is_mat_tien



def detech_hxt(html):
    p = '(?:h|hẻm|hẽm|d|đ|đường)\s{0,1}(?:xt|xe (?:tải|tãi))'
    rs = re.search(p, html, re.I)
    hxh_str, full_hxh = False,False
    if rs:
        span0 = rs.span(0)[0]
        pre_index = span0-30
        pre = html[pre_index:span0]
        gan_sat_cach_pt = 'gần|sát|cách'
        gan_sat_cach_search = re.search(gan_sat_cach_pt,pre, re.I)
        if gan_sat_cach_search:
            return hxh_str, full_hxh
        before_index = span0 + 10
        full_hxh = html[pre_index:before_index]
        hxh_str = rs.group(0)
    return hxh_str, full_hxh
    
def detech_hxm(html):
    p = '(?:h|hẻm|hẽm)\s{0,1}(?:xm|xe (?:máy))'
    rs = re.search(p, html, re.I)
    hxh_str, full_hxh = False,False
    if rs:
        span0 = rs.span(0)[0]
        pre_index = span0-30
        pre = html[pre_index:span0]
        gan_sat_cach_pt = 'gần|sát|cách'
        gan_sat_cach_search = re.search(gan_sat_cach_pt,pre, re.I)
        if gan_sat_cach_search:
            return hxh_str, full_hxh
        before_index = span0 + 10
        full_hxh = html[pre_index:before_index]
        hxh_str = rs.group(0)
    return hxh_str, full_hxh
    
def detech_hbg(html):
    p = '(?:h|hẻm|hẽm)\s{0,1}(?:bg|ba (?:gát|gác))'
    rs = re.search(p, html, re.I)
    hxh_str, full_hxh = False,False
    if rs:
        span0 = rs.span(0)[0]
        pre_index = span0-30
        pre = html[pre_index:span0]
        gan_sat_cach_pt = 'gần|sát|cách'
        gan_sat_cach_search = re.search(gan_sat_cach_pt,pre, re.I)
        if gan_sat_cach_search:
            return hxh_str, full_hxh
        before_index = span0 + 10
        full_hxh = html[pre_index:before_index]
        hxh_str = rs.group(0)
    return hxh_str, full_hxh

def detech_hem_all(html):
    loai_hem_selection = False
    loai_hem, full_loai_hem = detech_hxh(html)
    if loai_hem:
        loai_hem_selection = 'hxh'
    else:
        loai_hem,  full_loai_hem = detech_hxt(html)
        if loai_hem:
            loai_hem_selection = 'hxt'
        else:
            loai_hem,  full_loai_hem = detech_hxm(html)
            if loai_hem:
                loai_hem_selection = 'hxm'
            else:
                loai_hem,  full_loai_hem = detech_hbg(html)
                if loai_hem:
                    loai_hem_selection = 'hbg'
    return loai_hem, full_loai_hem, loai_hem_selection


def skip_if_cate_not_bds(depend_func):
    def wrapper(*args,**kargs):
        self = args[0]
        for r in self:
            if r.cate ==u'bds':
                depend_func(r)
    return wrapper

def skip_depends(depend_func):
    def wrapper(*args,**kargs):
        self = args[0]
        for r in self:
            return 
            # if r.cate ==u'bds':
            #     depend_func(r)
    return wrapper



class UserReadMark(models.Model):
    _name = 'user.read.mark'

    user_id = fields.Many2one('res.users')
    bds_id = fields.Char('bds.bds')

class UserQuanTamMark(models.Model):
    _name = 'user.quantam.mark'

    user_id = fields.Many2one('res.users')
    bds_id = fields.Char('bds.bds')

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
    title = fields.Char()
    images_ids = fields.One2many('bds.images', 'bds_id' )
    siteleech_id = fields.Many2one('bds.siteleech')
    thumb = fields.Char()
    poster_id = fields.Many2one('bds.poster', ondelete='restrict')
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
    diff_public_datetime = fields.Integer()
    public_date = fields.Date()
    diff_public_date = fields.Integer()
    publicdate_ids =fields.One2many('bds.publicdate','bds_id')
    len_publicdate_ids = fields.Integer(compute='len_publicdate_ids_', store=True)
    gialines_ids = fields.One2many('bds.gialines','bds_id')
    diff_gia = fields.Float()
    ngay_update_gia = fields.Datetime()
    #set field (field mà mình điền vào)
    is_read = fields.Boolean()
    quan_tam = fields.Datetime(string=u'Quan Tâm')
    ko_quan_tam = fields.Datetime(string=u'Không Quan Tâm')

    #compute field
    html_show = fields.Text(compute='html_show_',string=u'Nội dung')
    html_replace = fields.Html(compute='html_replace_')
    html_khong_dau = fields.Html(compute='html_khong_dau_',store=True)
    link_show =  fields.Char(compute='link_show_')

   
    
    # subtitle_html_for_agency = fields.Html(compute='subtitle_html_for_agency_',store=True, string="Để làm cò")
    auto_ngang = fields.Float(compute = 'auto_ngang_doc_',store=True)
    auto_doc = fields.Float(compute = 'auto_ngang_doc_',store=True)
    auto_dien_tich = fields.Float(digits=(6,2), compute = 'auto_ngang_doc_',store=True)
    ti_le_dien_tich_web_vs_auto_dien_tich = fields.Float(digits=(6,2), compute = 'auto_ngang_doc_',store=True)
  

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
    don_gia = fields.Float(digit=(6,2),compute='don_gia_',store=True,string=u'Đơn giá')
    ti_le_don_gia = fields.Float(digits=(6,2),compute='ti_le_don_gia_',store=True)
    muc_don_gia = fields.Selection([('0-30','0-30'),('30-60','30-60'),('60-90','60-90'),
                                    ('90-120','90-120'),('120-150','120-150'),('150-180','150-180'),
                                    ('180-210','180-210'),('>210','>210')],compute='muc_don_gia_',store=True)
    muc_ti_le_don_gia = fields.Selection([('0-0.4','0-0.4'),('0.4-0.8','0.4-0.8'),('0.8-1.2','0.8-1.2'),
                                    ('1.2-1.6','1.2-1.6'),('1.6-2.0','1.6-2.0'),('2.0-2.4','2.0-2.4'),
                                    ('2.4-2.8','2.4-2.8'),('>2.8','>2.8')],compute='muc_ti_le_don_gia_',store=True)

    post_ids_of_user  = fields.One2many('bds.bds','poster_id',related='poster_id.post_ids')



    detail_du_doan_cc_or_mg = fields.Selection(related='poster_id.detail_du_doan_cc_or_mg', store = True)
    du_doan_cc_or_mg = fields.Selection(related='poster_id.du_doan_cc_or_mg', store = True)
    count_chotot_post_of_poster = fields.Integer(related= 'poster_id.count_chotot_post_of_poster',store=True,string=u'chotot post quantity')
    count_bds_post_of_poster = fields.Integer(related= 'poster_id.count_bds_post_of_poster',store=True,string=u'bds post quantity')
    count_post_all_site = fields.Integer(related= 'poster_id.count_post_all_site',store=True)
    dd_tin_cua_co_rate = fields.Float(related='poster_id.dd_tin_cua_co_rate', store  = True)
    dd_tin_cua_dau_tu_rate = fields.Float(related='poster_id.dd_tin_cua_dau_tu_rate', store  = True)
    len_site = fields.Integer(related='poster_id.len_site', store  = True)

    count_post_of_onesite_max = fields.Integer(related='poster_id.count_post_of_onesite_max', store  = True)
    siteleech_max_id = fields.Many2one(related='poster_id.siteleech_max_id', store  = True)
    # site_ids = fields.Many2many(related='poster_id.site_ids', store  = True)
    #!related
    # for filter field
    quan_id_selection = fields.Selection('get_quan_')
    greater_day = fields.Integer()
    siteleech_id_selection = fields.Selection('siteleech_id_selection_')
    is_user_read_mark = fields.Boolean(compute='_is_user_read_mark')
    is_user_quantam_mark = fields.Boolean(compute='_is_user_quantam_mark')
    trigger = fields.Boolean()
    diff_public_days_from_now = fields.Integer(compute='_compute_diff_public_days_from_now', store=True)

    trich_dia_chi = fields.Char(compute='trich_dia_chi_', store = True,string='Trích địa chỉ')
    mat_tien_address = fields.Char(compute ='_mat_tien_address', store=True)
    mat_tien_or_trich_dia_chi = fields.Char(compute='_compute_mat_tien_or_trich_dia_chi', store=True)
    # is_mat_tien_or_trich_dia_chi = fields.Boolean(compute='_compute_mat_tien_or_trich_dia_chi', store=True)
    is_mat_tien_or_trich_dia_chi = fields.Selection([('1','Có trích địa chỉ hoặc mặt tiền'),('0','Không Có trích địa chỉ hoặc mặt tiền' )],compute='_compute_mat_tien_or_trich_dia_chi', store=True)
    # dd_tin_cua_co = fields.Boolean(compute='_compute_kw_mg', store = True, string='is có kw môi giới')
    dd_tin_cua_co = fields.Selection([('kw_co_cap_1', 'Keyword cò cấp 1'),('no_kw_co_cap_1', 'Không coKeyword cò cấp 1')],compute='_compute_kw_mg', store = True, string='is có kw môi giới')
    kw_mg = fields.Char(compute='_compute_kw_mg', store = True, string='kw môi giới')
    kw_mg_cap_2= fields.Char(compute='_compute_kw_mg', store = True, string='kw môi giới cấp 2')
    is_kw_mg_cap_2= fields.Char(compute='_compute_kw_mg', store = True, string='kw môi giới cấp 2')
    kw_co_date = fields.Char(compute='_compute_kw_mg',store=True)
    kw_co_break = fields.Integer(compute='_compute_kw_mg',store=True)
    kw_co_special_break = fields.Integer(compute='_compute_kw_mg',store=True)
    kw_co_mtg = fields.Char(compute='_compute_kw_mg',store=True)
    number_char = fields.Integer(compute='_compute_kw_mg',store=True)
    hoa_la_canh = fields.Char(compute='_compute_kw_mg',store=True)
    t1l1 = fields.Char(compute='_compute_kw_mg', store=True)


    dd_tin_cua_dau_tu = fields.Boolean(compute='_compute_dd_tin_cua_dau_tu', store = True,string='kw đầu tư')
    kw_hoa_hong = fields.Char(compute ='_compute_dd_tin_cua_dau_tu', store=True)
    kw_so_tien_hoa_hong = fields.Char(compute ='_compute_dd_tin_cua_dau_tu', store=True)
    
    # so_lau = fields.Float()
    # so_lau_char = fields.Char()
    # hem_rong = fields.Float()
    # hem_rong_char = fields.Char()
    # choose_area = fields.Float(digits=(6,2))#,store=True
    
    choose_area = fields.Float(digits=(6,2), compute = 'auto_ngang_doc_', store=True)#,store=True
    so_lau = fields.Float(digits=(6,1),compute ='_compute_so_lau',store=True)
    so_lau_char = fields.Char(compute ='_compute_so_lau',store=True)
    hem_rong = fields.Float(digits=(6,2), compute='_compute_hem_rong', store=True)
    hem_rong_char = fields.Char(compute='_compute_hem_rong', store=True)

    so_phong_ngu = fields.Integer(compute='_compute_so_phong_ngu', store=True)
    dtsd = fields.Float(digits=(6,2), compute='auto_ngang_doc_', store=True)

 
    
    loai_hem_selection = fields.Selection([('hxh','hxh'), ('hxt','hxt'), ('hxm','hxm'), ('hbg','hbg')], compute='_compute_loai_hem', store=True)
    

    so_lan_diff_public_update = fields.Integer()
    so_lan_gia_update = fields.Integer()
    mat_tien = fields.Char(compute='_detect_mat_tien', store=True)
    full_mat_tien = fields.Char(compute='_detect_mat_tien', store=True)
    is_mat_tien = fields.Boolean(compute='_detect_mat_tien', store = True)
    vip = fields.Char()
    @api.depends('trigger')
    def _detect_mat_tien(self):
        for r in self:
            r.mat_tien, r.full_mat_tien, r.is_mat_tien = detech_is_mat_tien(r.title + ' ' + r.html)

    def search(self, args, **kwargs):
        try:
            rs = args.index(1)
        except:
            rs = None
        if rs !=None:
            # l =[('user_read_mark_ids','=',False)]
            rs = args.index(1)
            del args[rs]
            user_read_mark = self.env['user.read.mark'].search([('user_id','=',self.env.uid)])
            user_read_mark_bds_ids = user_read_mark.mapped('bds_id')
            # user_read_mark_bds_ids = tuple(map(lambda i:i.id, user_read_mark_bds_ids))
            # user_read_mark_bds_ids = user_read_mark.ids
            if user_read_mark_bds_ids:
                args += [['id', 'not in', user_read_mark_bds_ids]]
        return super(bds, self).search(args, **kwargs)
        

    
    @api.depends('html')
    def _compute_loai_hem(self):
        for r in self:
            html = r.title + ' '  + r.html
            loai_hem, full_loai_hem, loai_hem_selection = detech_hem_all(html)
            r.loai_hem, r.full_loai_hem, r.loai_hem_selection = loai_hem, full_loai_hem, loai_hem_selection
            

    @api.depends('html','title','address')
    def _mat_tien_address(self):
        for r in self:
            full_adress_list_sum =  []
            number_list_sum = []
            html = r.html
            title = r.title
            address = r.address
            # address = (r.address or '').replace(',',' ')
            # p = '(?<!cách )(?i:nhà|mt|mặt tiền|số)\s+(\d{1,4}[a-zA-Z]{0,2})[\s,]+(?i:đường)*\s*(?P<ten_duong>(?:[A-Z0-9Đ][\w|/]*\s*){1,4})(?:\.|\s|\,|$|<)'
            p = '(?<!cách )(?i:nhà|mt|mặt tiền|số)\s+(\d{1,4}[a-zA-Z]{0,2})[\s,]+(?i:đường)*\s*(?P<ten_duong>(?-i:[A-Z0-9Đ][\w|/]*\s*){1,4})(?:\.|\s|\,|$|<)'
            addresses = {
            # 'title':{'value':title},
            'html':{'value':title + html,
                'p':'(?<!cách )(?i:nhà|mt|mặt tiền|số)\s+(\d{1,4}[a-zA-Z]{0,2})[\s,]+(?i:đường)*\s*(?P<ten_duong>(?-i:[A-Z0-9Đ][\w|/]*\s*){1,4})(?:\.|\s|\,|$|<)'
                }, 
            }
            for key,val in addresses.items():
                html = val['value']
                p = val.get('p',p)
                if html:
                    full_adress_list = detech_mat_tien(html, p)
                    if full_adress_list:
                        for number, full_address in full_adress_list:
                            if number not in number_list_sum:
                                full_adress_list_sum.append(full_address)
                                number_list_sum.append(number)
            if full_adress_list_sum:
                r.mat_tien_address = ','.join(full_adress_list_sum)


    @api.depends('trich_dia_chi','mat_tien_address')
    def _compute_mat_tien_or_trich_dia_chi(self):
        for r in self:
            r.mat_tien_or_trich_dia_chi = r.mat_tien_address or r.trich_dia_chi
            r.is_mat_tien_or_trich_dia_chi ='1' if  bool(r.mat_tien_or_trich_dia_chi) else '0'


    def _so_phong_ngu_detect(self, html):
        so_phong_ngu = 0
        pt = '(\d{1,2})\s*(?:pn|phòng ngủ)(?:\W|$)'
        rs = re.search(pt, html, re.I)
        if rs:
            so_phong_ngu = rs.group(1)
            try:
                so_phong_ngu = int(so_phong_ngu)
            except: 
                so_phong_ngu = 0
        return so_phong_ngu



    @api.depends('html')
    def _compute_so_phong_ngu(self):

        for r in self:
            html = (r.title or '' ) + ' ' + (r.html or '')
            so_phong_ngu = self._so_phong_ngu_detect(html)
            r.so_phong_ngu = so_phong_ngu


    def _compute_t1l1_detect(self, html):
        t1l1_list = []
        pt = '(1t[,\s]*(\d{1,2})l)(?:\W|$)'
        rs = re.search(pt, html, re.I)
        if rs:
            t1l1_list.append(rs.group(1))
        pt = '((\d{1,2})\s*pn)(?:\W|$)'
        rs = re.search(pt, html, re.I)
        if rs:
            t1l1_list.append(rs.group(1))
        pt = '(?:\W|^)(st)(?:\W|$)'
        rs = re.search(pt, html, re.I)
        if rs:
            t1l1_list.append(rs.group(1))
            
        # t1l1 = ','.join(t1l1_list)
        return t1l1_list
        

    # @api.depends('html')
    # def _compute_t1l1(self):
    #     for r in self:
    #         html = r.html
    #         t1l1_list = self._compute_t1l1_detect(html)
    #         r.t1l1 = ','.join(t1l1_list)
            



    @api.depends('html')
    def _compute_hem_rong(self):
        for r in self:
            pt = '(?<!cách )(?:hẻm|hẽm|đường)\s+(?:trước nhà)*\s*(?:xh|xe hơi|xe máy|kia|ba gác|ba gát)*\s*(?:nhỏ)*\s*(?:rộng)*\s*(\d+\.*\d*)\s*(?:m|mét)(?:\W|$)'
            rs = re.search(pt, r.html, re.I)
            if rs:
                r.hem_rong_char, r.hem_rong = rs.group(0), rs.group(1)
    
    
    def detect_lau(self, html):
        pt = '(\d{1,2})\s*(?:lầu|l)(?:\W|$)'
        rs = re.search(pt, html, re.I)
        so_lau = 0
        so_lau_char = False
        
        # if not rs:
        #     pt = '1t[,\s]*(\d)l(?:\W|$)'
        #     rs = re.search(pt, html, re.I)
        #     print (rs)
        if rs:
            so_lau = rs.group(1)
            so_lau_char = rs.group(0)
            try:
                so_lau = int(so_lau)
            except:
                so_lau = 0
            pt = '(\d{1,2})\s*(?:tầng)(?:\W|$)'
            so_lau_char = rs.group(0)
            try:
                so_tang = int(so_lau)
                so_lau = so_tang - 1
            except:
                so_lau = 0
            
        else:
            pt = '(cấp 4|c4|c4)\W'
            rs = re.search(pt, html, re.I)
            if rs:
                so_lau = 0.1
                so_lau_char = rs.group(1)
        pt = 'lửng|lững'
        rs = re.search(pt, html, re.I)
        if rs:
            so_lau +=0.5
        return so_lau, so_lau_char



    @api.depends('html')
    def _compute_so_lau(self):
        for r in self:
            so_lau, so_lau_char =  self.detect_lau(r.html)
            r.so_lau = so_lau
            r.so_lau_char = so_lau_char

    
    @api.model
    def create(self, vals):
        r = super(bds,self).create(vals)
        r.count_post_of_poster_()
        r.poster_id.quanofposter_ids_()
        r.quan_id.muc_gia_quan_()
        r.quan_id.len_post_ids_()
        # r.quan_id.muc_gia_quan_()






    @api.depends('public_date')
    def _compute_diff_public_days_from_now(self):
        for r in self:
            if r.public_date:
                r.diff_public_days_from_now = (fields.Date.today() - r.public_date).days


    
    def make_trigger(self):
        for r in self:
            r.trigger = True

    # def test(self):
    #     query = "select html from bds_bds where html like 'mặt tiền' limit 2"
    #     rs =  self.env.cr.execute(query)

    #     raise UserError(rs)

    def test(self):
        # rs = self.env['bds.bds'].read_group([],['loai_nha'],['loai_nha'])
        # rs = map(lambda i: i['loai_nha'].replace('\n','') if i['loai_nha'] else i['loai_nha'], rs)
        # rs = filter(lambda i: i != False, rs)
        # rs = map(lambda i: (i,i), rs)
        # rs = list(rs)
        # self.env['ir.config_parameter'].set_param("bds.loai_nha", rs)
        readgroup_rs = self.env['bds.bds'].read_group([('don_gia','>=', 20), ('don_gia','<=', 300),('poster_id','=',18)],['quan_id','siteleech_id','avg_gia:avg(gia)','count(quan_id)'],['quan_id','siteleech_id'], lazy=False)
        # rs = readgroup_rs[0]['don_gia']
        # r.muc_gia_quan = rs
        raise UserError(str(readgroup_rs))

    def test2(self):
        rs = self.env['ir.config_parameter'].get_param("bds.loai_nha")
        rs = eval(rs)
        raise UserError('%s-%s'%(type(rs),str(rs)))
    
    def count_post_of_poster_(self):
        for r in self:
            bds_id = r
            r = bds_id.poster_id    
            poster_dict = {}
            count_chotot_post_of_poster = self.search_count([('poster_id','=',r.id),('siteleech_id.name','=', 'chotot')])
            poster_dict['count_chotot_post_of_poster'] = count_chotot_post_of_poster
            count_bds_post_of_poster = self.search_count([('poster_id','=',r.id),('link','like','batdongsan')])
            poster_dict['count_bds_post_of_poster'] = count_bds_post_of_poster
            
            count_post_all_site = self.search_count([('poster_id','=',r.id)])
            poster_dict['count_post_all_site'] = count_post_all_site
           
           
            # domain_in_month = [('poster_id','=',r.id),('public_datetime','>', fields.Datetime.to_string(datetime.datetime.now() + datetime.timedelta(days=-30)))]
            month = ('public_datetime','>', fields.Datetime.to_string(datetime.datetime.now() + datetime.timedelta(days=-30)))
            domain_in_month = [('poster_id','=',r.id), month]
            count_post_every_site_max_readgroup_rsul = self.env['bds.bds'].read_group(domain_in_month,['siteleech_id'],['siteleech_id'])
            list_siteleech_id_count_post = list(map(lambda i: i['siteleech_id_count'], count_post_every_site_max_readgroup_rsul))
            site_ids = list(map(lambda i: i['siteleech_id'][0], count_post_every_site_max_readgroup_rsul))
            try:
                count_post_of_onesite_max = max(list_siteleech_id_count_post)
                count_post_of_onesite_max_index = list_siteleech_id_count_post.index(count_post_of_onesite_max)
                siteleech_max_id = count_post_every_site_max_readgroup_rsul[count_post_of_onesite_max_index]['siteleech_id'][0]
            except ValueError as e:
                count_post_of_onesite_max = count_post_all_site
                siteleech_max_id = bds_id.siteleech_id.id


            poster_dict['count_post_of_onesite_max'] = count_post_of_onesite_max
            poster_dict['siteleech_max_id'] = siteleech_max_id
            count_post_all_site_in_month = self.search_count(domain_in_month)

            poster_dict['site_ids'] = [(6,0,site_ids)]

            poster_dict['count_post_all_site_in_month'] = count_post_all_site_in_month
            
            address_topic_number = self.search_count([('poster_id','=',r.id),('trich_dia_chi','!=', False)])
            poster_dict['address_topic_number'] = address_topic_number
            address_rate = 0

            if count_post_all_site:
                address_rate = address_topic_number/count_post_all_site
                poster_dict['address_rate'] = address_rate
                dd_tin_cua_co_count = self.search_count([('poster_id','=',r.id),('dd_tin_cua_co','=', True)])
                poster_dict['dd_tin_cua_co_rate'] = dd_tin_cua_co_count/count_post_all_site

                dd_tin_cua_dau_tu_count = self.search_count([('poster_id','=',r.id),('dd_tin_cua_dau_tu','=', True)])
                poster_dict['dd_tin_cua_dau_tu_rate'] = dd_tin_cua_dau_tu_count/count_post_all_site

            count_chotot_moi_gioi = self.search_count([('poster_id','=',r.id),('siteleech_id.name','=', 'chotot'), ('chotot_moi_gioi_hay_chinh_chu','=', 'moi_gioi')])
            if count_chotot_moi_gioi:
                chotot_mg_or_cc = 'moi_gioi'
            else:
                if count_chotot_post_of_poster:
                    chotot_mg_or_cc = 'chinh_chu'
                else:
                    chotot_mg_or_cc = 'khong_biet'
            poster_dict['chotot_mg_or_cc'] = chotot_mg_or_cc
            dd_tin_cua_co = self.search_count([('poster_id','=',r.id),('dd_tin_cua_co','=', 'kw_co_cap_1')])
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
                    if count_post_of_onesite_max > 3:
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
                    if count_post_of_onesite_max  > 3:
                        if address_rate >= 0.3:
                            du_doan_cc_or_mg= 'dd_cc'
                            detail_du_doan_cc_or_mg = 'dd_cc_b_khong_biet_n_cpas_gt_3_n_address_rate_gte_0_3'
                        else:
                            du_doan_cc_or_mg= 'dd_mg'
                            detail_du_doan_cc_or_mg = 'dd_mg_b_khong_biet_n_cpas_gt_3_n_address_rate_lt_0_3'
                            
                    else: #count_post_of_onesite_max  <= 3
                        if address_rate: 
                            du_doan_cc_or_mg= 'dd_cc'
                            detail_du_doan_cc_or_mg = 'dd_cc_b_khong_biet_n_cpas_lte_3_n_address_rate_gt_0'
                        else:
                            du_doan_cc_or_mg= 'dd_kb'
                            detail_du_doan_cc_or_mg = 'dd_kb_b_khong_biet_n_cpas_lte_3_n_address_rate_eq_0'

            if du_doan_cc_or_mg !='dd_mg':
                if  dd_tin_cua_dau_tu:
                    du_doan_cc_or_mg= 'dd_dt'
                    
                  
            poster_dict['du_doan_cc_or_mg'] = du_doan_cc_or_mg
            poster_dict['detail_du_doan_cc_or_mg'] = detail_du_doan_cc_or_mg
            r.write(poster_dict)
            # bds_id.du_doan_cc_or_mg = du_doan_cc_or_mg
            # bds_id.detail_du_doan_cc_or_mg = detail_du_doan_cc_or_mg     

        


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


    @api.depends('html')
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
            
    
    def compute_kw_mg(self, html):
        found_kw_mgs = []
        pat_247 = '24h*/7|(?<!an ninh )24h*/24|1/500'
        rs = re.search(pat_247, html, re.I)
        kw_co_date = False #1
        if rs:
            found_kw_mgs.append(rs.group(0))
            kw_co_date = rs.group(0)
        
        #(?:hẻm|h) {0,1}xh|(?<!phòng )khách(?! sạn)
        # nha_dat_kws = 'nhà đất|uy tín|real|bds|bđs|cần tuyển|tuyển sale|tuyển dụng|bất động sản|bđs|ký gửi|kí gửi|'+\
        # '(?<!nova)land(?!mark|abc)|tư vấn|thông tin chính xác|shr|(?:cc|công chứng )(?:ngay )*(?:sang tên|trong ngày)|' +\
        # '(?:lh|liên hệ).{0,20}xem nhà|xem nhà miễn phí|(?:hổ|hỗ) trợ miễn phí|khách hàng|gọi ngay|giá tốt|' +\
        # 'hổ trợ[\w\s]{0,20}ngân hàng|hợp.{1,20}đầu tư|tin thật|cn đủ|hình thật|csht|tttm|(?-i:MTKD)|(?-i:BTCT)|(?-i:CHDV)|(?-i:DTSD)|'+\
        # '(?:quý|quí) khách|cho khách|chưa qua đầu tư|(?:khu vực an ninh|dân trí cao)\W{1,3}(?:khu vực an ninh|dân trí cao)|mong gặp khách thiện chí|'+\
        # 'tiện kinh doanh[ ,]{1,2}buôn bán[ ,]{1,2}mở công ty[ ,]{1,2}văn phòng|không lỗi phong thủy|xuất cảnh|nợ ngân hàng'

        nha_dat_kws_cap_1 = 'nhà đất(?! thánh)|uy tín|real|bds|bđs|cần tuyển|tuyển sale|tuyển dụng|bất động sản|bđs|ký gửi|kí gửi|'+\
        '(?<!nova)land(?!mark|abc)|tư vấn|(?:thông tin|sản phẩm) (?:chính xác|thật)|' +\
        'xem nhà miễn phí|(?:hổ|hỗ) trợ miễn phí|khách hàng|' +\
        'hỗ trợ[\w\s]{0,20}pháp lý|hợp.{1,20}đầu tư|csht|tttm|'+\
        'chưa qua đầu tư|cấp 1[,\- ]*2[,\- ]*3|'+\
        'tiện kinh doanh[ ,]{1,2}buôn bán[ ,]{1,2}mở công ty[ ,]{1,2}văn phòng|nợ ngân hàng|hợp tác|thanh lý' 

        # nha_dat_kws_cap_2 = 'shr|(?:cc|công chứng )(?:ngay )*(?:sang tên|trong ngày)|gọi ngay|giá tốt|tin thật|cn đủ|hình thật|(?:lh|liên hệ).{0,20}xem nhà'
        # nha_dat_kws_cap_3 = '(?-i:MTKD)|(?-i:BTCT)|(?-i:CHDV)|(?-i:DTSD)|(?:.{0,10}cho khách?:.{0,10})|(?:khu vực an ninh|dân trí cao)\W{1,3}(?:khu vực an ninh|dân trí cao)|' +\
        #hỗ trợ[\w\s]{0,20}ngân hàng|vay (?:vốn )*ngân hàng
        # 'không lỗi phong thủy'


        nha_dat_list_rs = re.findall(nha_dat_kws_cap_1, html, re.I)
        if nha_dat_list_rs:
            found_kw_mgs.extend(nha_dat_list_rs)

        mtg_kws = 'mmg|mqc|mtg|(?-i:MTKD)|(?-i:BTCT)|(?-i:CHDV)|(?-i:DTSD)|(?:.{0,10}cho khách?:.{0,10})|(?:khu vực an ninh|dân trí cao)\W{1,3}(?:khu vực an ninh|dân trí cao)'
        nha_dat_list_rs = re.findall(mtg_kws, html, re.I)
        kw_mg_cap_2 = False #2
        is_kw_mg_cap_2 = False#3
        if nha_dat_list_rs:
            # found_kw_mgs.extend(nha_dat_list_rs)
            kw_mg_cap_2 = ','.join(nha_dat_list_rs)
            is_kw_mg_cap_2 = True

        # break_kw = '(\n-|\n\+)'
        break_kw = '(\n✓|\n\*)'
        break_rs = re.findall(break_kw, html, re.I)
        kw_co_special_break = False # 4
        if break_rs:
            len_break_rs = len(break_rs)
            kw_co_special_break = len_break_rs
            # if len_break_rs > 2:
            #     found_kw_mgs.append('len_special_break_rs > 2')


        
        break_kw = '(\n)'
        break_rs = re.findall(break_kw, html, re.I)
        kw_co_break = False # 5
        if break_rs:
            len_break_rs = len(break_rs)
            kw_co_break = len_break_rs
            # if len_break_rs > 8:
            #     found_kw_mgs.append('len_break_rs > 8')
        
        number_char = len(html)
        

        hoa_la_canh_pt = '🏠|💥|✅|👉🏻|⭐️|💵|💰|☎️|⚡|📲|💎|🌹|☎|🌈|🍎|🍏|🏦|📣|🆘|☎️|🤝|👍|👉|' +\
            '🏡|🗽|🎠|🏖|😍|🔥'
        nha_dat_list_rs = re.findall(hoa_la_canh_pt, html, re.I)
        hoa_la_canh = False # 6
        if nha_dat_list_rs:
            hoa_la_canh = len(nha_dat_list_rs)
            # found_kw_mgs.append(nha_dat_list_rs[0])
        
        t1l1_list = self._compute_t1l1_detect(html)
        t1l1 = False #7
        if t1l1_list:
            t1l1 = ','.join(t1l1_list)
            # if len (t1l1_list)> 1:
            #     found_kw_mgs.append('len (t1l1_list)> 1')
        kw_mg = False #8
        dd_tin_cua_co = 'no_kw_co_cap_1' # 9
        if found_kw_mgs:
            kw_mg = ','.join(found_kw_mgs)
            dd_tin_cua_co = 'kw_co_cap_1'

        return kw_co_date, kw_mg_cap_2, is_kw_mg_cap_2, kw_co_special_break, kw_co_break,\
                hoa_la_canh, t1l1, kw_mg, dd_tin_cua_co


    @api.depends('html', 'title')
    @skip_if_cate_not_bds 
    def _compute_kw_mg(self):  
        for r in self:
            html = r.title + ' ' + r.html
            r.kw_co_date, r.kw_mg_cap_2, r.is_kw_mg_cap_2, r.kw_co_special_break, r.kw_co_break,\
                r.hoa_la_canh, r.t1l1, r.kw_mg, r.dd_tin_cua_co = self.compute_kw_mg(html)
            
            
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
            html = r.html
            auto_ngang, auto_doc, auto_dien_tich, choose_area, ti_le_dien_tich_web_vs_auto_dien_tich,  dien_tich_trong_topic = \
                auto_ngang_doc_compute(html, r.area)
            r.choose_area = choose_area
            r.dtsd = tim_dien_tich_sd_trong_bai(r.html)
            r.auto_ngang,r.auto_doc, r.auto_dien_tich, r.ti_le_dien_tich_web_vs_auto_dien_tich =\
                 auto_ngang, auto_doc, auto_dien_tich, ti_le_dien_tich_web_vs_auto_dien_tich

    def str_before_index(self, index, input_str):
        pre_index = index - 30
        if pre_index < 0:
            pre_index = 0
        pre_str = input_str[pre_index:index]
        return pre_str


    def _compute_hoa_hong(self, html):
        p = '((?<=\W)(?:hoa hồng|hh(?!t)|huê hồng|🌹)\s*(?:cho)*\s*(?:mg|môi giới|mô giới|TG|Trung gian)*\s*(?:\D|\s){0,31}((\d|\.)+\s*(%|triệu|tr))*)(?:\s+|$|<|\.|)'
        rs = re.search(p, html, re.I)
        if not rs:
            p = '((?:phí(?! hh| hoa hồng| huê hồng|\w)|chấp nhận)\s*(?:cho)*\s*(?:mg|môi giới|mô giới|TG|Trung gian)*\s*((\d|\.)+\s*(%|triệu|tr))*)(?:\s+|$|<|\.|)'
            rs = re.search(p, html, re.I)
        kw_hoa_hong, kw_so_tien_hoa_hong, dd_tin_cua_dau_tu = False, False, False
        if rs:
            for i in [1]:
                index = rs.span()[0]
                pre_str = self.str_before_index(index, html)
                khong_cho_mg = re.search('không|ko', pre_str, re.I)
                if khong_cho_mg:
                    continue
                kw_hoa_hong_tach = rs.group(1)
                kw_hoa_hong_tach = kw_hoa_hong_tach.strip().lower()
                if kw_hoa_hong_tach in  ['phí', 'chấp nhận']:
                    continue
                kw_hoa_hong = kw_hoa_hong_tach
                kw_so_tien_hoa_hong = rs.group(2)
                dd_tin_cua_dau_tu = True
        else:
            rs = re.search('((1)%)', html, re.I)
            if rs:
                kw_hoa_hong = rs.group(1)
                kw_so_tien_hoa_hong = rs.group(2)
                dd_tin_cua_dau_tu = True
        return kw_hoa_hong, kw_so_tien_hoa_hong, dd_tin_cua_dau_tu




    @api.depends('html')
    @skip_if_cate_not_bds               
    def _compute_dd_tin_cua_dau_tu(self):
        
        for r in self:
            r.kw_hoa_hong, r.kw_so_tien_hoa_hong, r.dd_tin_cua_dau_tu =  self._compute_hoa_hong(r.html)

                
           

                    
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
                
    @api.depends('gia','choose_area')
    def don_gia_(self):
        for r in self:
            if r.gia > 0.5 and r.choose_area:
                r.don_gia = r.gia*1000/r.choose_area
                
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

    @api.depends('choose_area')
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
        khong_hien_thi_nhieu_html = self.env['ir.config_parameter'].sudo().get_param('bds.khong_hien_thi_nhieu_html')
        for r in self:
            r.html_show = 'id:%s <b>%s</b>'%(r.id, r.title if r.title else '') + \
            ('\n' + '<b>%s</b>'%r.quan_id.name if r.quan_id.name  else '') +\
            ('\n<br>' + r.html if r.html else '') +\
            ('\n<br>Phone: ' + (r.poster_id.name or '')) +\
            ('\n<br>detail_du_doan_cc_or_mg: %s'%r.poster_id.detail_du_doan_cc_or_mg) +\
            (
            (
            ('\n<br>' +r.link_show if  r.link_show else '')+ \
            ('\n<br> Giá: <b>%s tỷ</b>'%(r.gia if r.gia else '')) +\
            ('\n<br> kích thước: %s'%('<b>%sm x %sm</b>'%(r.auto_ngang, r.auto_doc) if (r.auto_ngang or r.auto_doc) else ''))+\
            ('\n<br> Area: %s'%('<b>%s m2</b>'%r.area if r.area else ''))+\
            ('\n<br> auto_dien_tich: %s'%('<b>%s m2</b>'%r.auto_dien_tich if r.auto_dien_tich else ''))+\
            ('\n<br> Chọn lại diện tích: %s'%('<b>%s m2</b>'%r.choose_area if r.choose_area else ''))+\
            ('\n<br>địa chỉ: %s'%(r.trich_dia_chi or r.mat_tien_address)) +\
            ('\n<br>Site: %s'%r.siteleech_id.name) +\
            ('\n<br>Đơn giá: %.2f'%r.don_gia) + \
            ('\n<br>Tỉ lệ đơn giá: %.2f'%r.ti_le_don_gia)  + \
            ('\n<br>Tổng số bài của người này: <b>%s</b>'%r.count_post_all_site) +\
            ('\n<br>Chợ tốt CC or MG: %s' %dict(self.env['bds.bds']._fields['chotot_moi_gioi_hay_chinh_chu'].selection).get(r.chotot_moi_gioi_hay_chinh_chu))+\
            ('\n<br>du_doan_cc_or_mg: <b>%s </b>'%dict(self.env['bds.poster']._fields['du_doan_cc_or_mg'].selection).get(r.poster_id.du_doan_cc_or_mg))+\
            ('\n<br> address_rate: %s'%r.poster_id.address_rate) +\
            ('\n<br>tỉ lệ keyword cò : %s'%r.poster_id.dd_tin_cua_co_rate) +\
            ('\n<br>tỉ lệ keyword đầu tư: %s'%r.poster_id.dd_tin_cua_dau_tu_rate) +\
            ('\n<br>public_date %s'%r.public_date)
            ) if not khong_hien_thi_nhieu_html else '')
            


    @api.depends('link')
    def cho_tot_link_fake_(self):
        for r in self:
            if r.link and 'chotot' in r.link:
                rs = re.search('/(\d*)$',r.link)
                id_link = rs.group(1)
                r.cho_tot_link_fake = 'https://nha.chotot.com/nhadat/mua-ban-nha-dat/'  + id_link+ '.htm'
                

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
        # minutes =25
        gia = float(self.env['ir.config_parameter'].sudo().get_param('bds.gia',default=0))
        if gia ==0:
            gia =100
            
        #mat_tien_address
        # gia = 100
        minutes_5_last = fields.Datetime.now() -   datetime.timedelta(minutes=minutes, seconds=1)
        cr = self.search([('create_date','>', minutes_5_last),
            # ('du_doan_cc_or_mg','in', ['dd_cc', 'dd_dt']),
            ('quan_id.name', 'in',['Quận 1','Quận 3', 'Quận 5', 'Quận 10', 'Quận Tân Bình', 'Quận Tân Phú', 'Quận Phú Nhuận', 'Quận Bình Thạnh']),
            '|', '&', ('trich_dia_chi','!=',False), ('gia','<', gia), '&', ('mat_tien_address','!=',False), ('gia','<', 13)
            ])
        # raise UserError(str(cr))
        if cr:
            for r in cr:
                # one_mail_html = one_mail_template%(r.title, r.html_show)
                one_mail_html = r.html_show
                images = r.images_ids
                image_tags = map(lambda i: '<img src="%s" style="width:300px" alt="Girl in a jacket">'%i, list(images.mapped('url')) + [r.thumb])
                image_html = '<br>'.join(image_tags)
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


    
        

               

