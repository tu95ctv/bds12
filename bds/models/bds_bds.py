# -*- coding: utf-8 -*-
import re
import base64
from odoo import models, fields, api,sql_db, tools
from odoo.exceptions import UserError
from unidecode import unidecode
import datetime
from odoo.addons.bds.models.bds_tools  import  request_html
from odoo.exceptions import UserError

def detect_street_name(street_name_may_be):
    pat = '((\S+)[\s\.$,]*){,4}'
    long_street_name_search_obj = re.search(pat,street_name_may_be, re.I)
    long_street_name = long_street_name_search_obj.group(0)
    street_name_obj = re.search(',|\.', long_street_name)
    if street_name_obj:
        street_name = long_street_name[:street_name_obj.span()[0]]
    else:
        street_name = long_street_name
    return street_name.strip()

def detech_mat_tien(html):
    ss = re.findall('(số \d+ )', html, re.I)
    deal_s = []
    full_adress_list = []
    for s in ss:
        if s not in deal_s:
            deal_s.append(s)
            s1 = re.search(s, html, re.I)
            index = s1.span()[1]
            number = s1.group(0)
            trim_street = html[index:index + 30]
            is_tang_cao = re.search('cao tầng|\(', trim_street, re.I)
            if is_tang_cao:
                continue
            pre_index = index - 30
            if pre_index < 0:
                pre_index = 0
            check_hem_string = html[pre_index:index]
            if check_hem_string:
                is_hem = re.search('hẻm', check_hem_string, re.I)
                if is_hem:
                    continue
            street_name = detect_street_name(trim_street)
            full_adress =  number + '' + street_name
            full_adress_list.append(full_adress)
    return full_adress_list

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
    loai_nha = fields.Char()
    loai_nha_selection = fields.Selection([('Căn hộ/Chung cư','Căn hộ/Chung cư'), ('Nhà ở','Nhà ở')], string='Loại nhà')
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
    dd_tin_cua_co = fields.Boolean(compute='trich_dia_chi_', store = True, string='kw môi giới')
    dd_tin_cua_dau_tu = fields.Boolean(compute='dd_tin_cua_dau_tu_', store = True,string='kw đầu tư')
    subtitle_html_for_agency = fields.Html(compute='subtitle_html_for_agency_',store=True, string="Để làm cò")
    auto_ngang = fields.Float(compute = 'auto_ngang_doc_',store=True)
    auto_doc = fields.Float(compute = 'auto_ngang_doc_',store=True)
    auto_dien_tich = fields.Float(compute = 'auto_ngang_doc_',store=True)
    ti_le_dien_tich_web_vs_auto_dien_tich = fields.Float(compute = 'auto_ngang_doc_',store=True)
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
    hoahongsearch = fields.Char(compute ='hoahongsearch_',store=True)

    # !compute field
    # related 
    post_ids_of_user  = fields.One2many('bds.bds','poster_id',related='poster_id.post_ids')
    username = fields.Char(related='poster_id.username')
    detail_du_doan_cc_or_mg = fields.Selection(related='poster_id.detail_du_doan_cc_or_mg', store = True)
    du_doan_cc_or_mg = fields.Selection(related='poster_id.du_doan_cc_or_mg', store = True)
    count_chotot_post_of_poster = fields.Integer(related= 'poster_id.count_chotot_post_of_poster',store=True,string=u'chotot post quantity')
    count_bds_post_of_poster = fields.Integer(related= 'poster_id.count_bds_post_of_poster',store=True,string=u'bds post quantity')
    count_post_all_site = fields.Integer(related= 'poster_id.count_post_all_site',store=True)
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

    def test(self):
        query = "select html from bds_bds where html like 'mặt tiền' limit 2"
        rs =  self.env.cr.execute(query)

        raise UserError(rs)


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
    
    def detect_hem_address_list(self, ad_list):

        def detect_hem_address(address):
            posible_address = re.findall('(\d+\w{0,2}/\d+\w{0,2}(?:/\d+\w{0,2})*)', address)
            keys_street_has_numbers = ['3/2','30/4','19/5','3/2.','3/2,','23/9']
            keys_24_7 = ['24/24','24/7','24/24h', '24/24H','24/24/7']
            pat = '24h*/7|24h*/24'
            result_keys = []
            trust_address_result_keys = []
            only_number_trust_address_result_keys = []
            black_list = '23/23 Nguyễn Hữu Tiến|5 Độc Lập'
            black_list_rs = re.search(black_list, address, re.I)
            if not black_list_rs:
                co_date_result_keys=[]
                street_result_keys=[]
                
                for adress_number in posible_address:
    #                 adress_number = adress_number[0]
                    rs = re.search(pat, adress_number, re.I)
                    if rs:
                        co_date_result_keys.append(adress_number)
                        continue
                    if adress_number in keys_street_has_numbers:
                        street_result_keys.append(adress_number)
                        continue
                    is_day = re.search('\d+/\d\d\d\d', adress_number)
                    if is_day:
                        continue
                    is_ty_m2 =  re.search('tỷ|tr|m2', adress_number)
                    if is_ty_m2:
                        continue
                    if adress_number not in only_number_trust_address_result_keys:
                        index = re.search(adress_number, address).span()[1]
                        trim_street = address[index+1:index+100]
                        street_name = detect_street_name(trim_street)
                        full_adress = adress_number + ' ' + street_name
                        trust_address_result_keys.append((adress_number, full_adress))
                        only_number_trust_address_result_keys.append(adress_number)
            return trust_address_result_keys, co_date_result_keys
        
        sum_trust_address_result_keys = [] 
        is_co_date_result_keys = False
        for ad in ad_list:
            trust_address_result_keys, co_date_result_keys = detect_hem_address(ad)
            is_co_date_result_keys = is_co_date_result_keys or bool(co_date_result_keys)
            for i in trust_address_result_keys:
                if i not in sum_trust_address_result_keys:
                    sum_trust_address_result_keys.append(i)
        return sum_trust_address_result_keys, is_co_date_result_keys

    @api.depends('html', 'trigger')
    @skip_if_cate_not_bds 
    def trich_dia_chi_(self):
        for r in self:
            title = r.title
            html =  r.html
            address = r.address
            ad_list = []
            if title:
                ad_list.append(title)
            if html: 
                ad_list.append(html)
            if address:
                ad_list.append(address)
            sum_trust_address_result_keys, dd_tin_cua_co = self.detect_hem_address_list(ad_list)
            if sum_trust_address_result_keys:
                trich_dia_chi = ','.join(map(lambda i:i[1], sum_trust_address_result_keys))
                r.trich_dia_chi = trich_dia_chi
            if dd_tin_cua_co == False:       
                kss= ['mmg','mqc','mtg', 'bds', 'cần tuyển','tuyển sale', 'tuyển dụng', 'bất động sản','bđs','ký gửi','land','tư vấn','thông tin chính xác']
                is_match = False
                for ks in kss:
                    rs = re.search(ks,html, re.I)
                    if rs:
                        is_match = True
                        break
                if is_match:
                    dd_tin_cua_co = True
            r.dd_tin_cua_co = dd_tin_cua_co



        
    @api.depends('trich_dia_chi')
    def same_address_bds_ids_(self):
        for r in self:
            if r.trich_dia_chi:
                same_address_bds_ids  = self.env['bds.bds'].search([('trich_dia_chi','=ilike',r.trich_dia_chi),('id','!=',r.id)])
                r.same_address_bds_ids = [(6,0,same_address_bds_ids.mapped('id'))]

    @api.depends('html','cate')
    @skip_if_cate_not_bds            
    def auto_ngang_doc_(self):
        for r in self:
            pt= '(\d{1,3}[\.,m]{0,1}\d{0,2}) {0,1}m{0,1}(( {0,1}x {0,1}))(\d{1,3}[\.,m]{0,1}\d{0,2})'
            rs = re.search(pt, r.html,flags = re.I)
            if rs:
                auto_ngang,auto_doc = float(rs.group(1).replace(',','.').replace('m','.').replace('M','.')),float(rs.group(4).replace(',','.').replace('m','.').replace('M','.'))
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
    
    @api.depends('html')
    @skip_if_cate_not_bds   
    def subtitle_html_for_agency_(self):
        for r in self:
            pt ='(liên hệ|lh|dt)([: ]{0,3})(.{1,20}[\d. -]{8,14})+'
            rs = re.sub(pt, '', r.html, flags = re.I)
            pt= '(hoa hồng|huê hồng|hh).*?(1%|\d{2,3}\s{0,1}(triệu|tr))'
            rs = re.sub(pt, '',rs, flags = re.I)
            r.subtitle_html_for_agency = rs
    
    
    @api.depends('subtitle_html_for_agency')
    @skip_if_cate_not_bds
    def hoahongsearch_(self):
        for r in self:
            pt= '(hoa hồng|huê hồng|hh).+?(\d[\.\d]{0,2}%|\d{2,3}\s{0,1}(triệu|tr))'
            rs = re.search(pt, r.subtitle_html_for_agency,flags = re.I)
            if rs:
                r.hoahongsearch = rs.group(0)

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

    @api.depends('html')
    @skip_if_cate_not_bds               
    def dd_tin_cua_dau_tu_(self):
        kss= ['hoa hồng','hh 1%', 'hh 0.5%','hh .{1,3}tr','1%','1 %','huê hồng','phí môi giới',]
        for r in self:
            is_match = False
            for ks in kss:
                rs = re.search(ks,r.html, re.I)
                if rs:
                    is_match = True
                    break
            if is_match:
                r.dd_tin_cua_dau_tu = True
                    
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
            r.html_show = '<b>%s</b>'%((r.title) if r.title else '') + \
            ('\n' + r.quan_id.name if r.quan_id.name  else '') +\
            ('\n' + r.html if r.html else '') +\
            ('\nPhone: ' + (r.poster_id.name or '')) +\
            ('\n' +r.link_show if  r.link_show else '')+ \
            ('\n Giá: %s tỷ'%r.gia if r.gia else '') +\
            ('\n Area: %s m2'%r.area if r.area else '')+\
            ('\nSite: %s'%r.siteleech_id.name) +\
            ('\nĐơn giá:%.2f'%r.don_gia) + \
            ('Tỉ lệ đơn giá: %.2f'%r.ti_le_don_gia)  + \
            ('\nCount post all site:%s'%r.count_post_all_site) +\
            ('\nChợ tốt CC or MG: %s'%r.chotot_moi_gioi_hay_chinh_chu)

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


    
        

               

