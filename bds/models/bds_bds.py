# -*- coding: utf-8 -*-
import re
import base64
from odoo import models, fields, api
from odoo.exceptions import UserError
from unidecode import unidecode
import datetime
from odoo.addons.bds.models.bds_tools  import  request_html
from odoo.exceptions import UserError
from odoo.addons.bds.models.bds_tools import g_or_c_ss
from odoo.addons.bds.models.main_fetch_common1  import  _compute_so_phong_ngu, _compute_mat_tien_or_trich_dia_chi,\
    _compute_dd_tin_cua_dau_tu, _compute_loai_hem_combine, _compute_kw_mg
from odoo.addons.bds.models.compute_choosed_area  import _compute_choosed_area_muc_gia
import psycopg2
import operator

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
    bds_id = fields.Char('bds.bds')


class UserQuanTamMark(models.Model):
    _name = 'user.quantam.mark'

    user_id = fields.Many2one('res.users')
    bds_id = fields.Char('bds.bds')


class bds(models.Model):
    _name = 'bds.bds'
    _order = "id desc"
    _rec_name = 'title'
    
    trigger = fields.Boolean()
    so_lan_diff_public_update = fields.Integer()
    so_lan_gia_update = fields.Integer()
    vip = fields.Char()
    user_read_mark_ids = fields.One2many('user.read.mark','bds_id')
    user_quantam_mark_ids = fields.One2many('user.quantam.mark','bds_id')
    sell_or_rent =  fields.Selection([('sell','sell'), ('rent', 'rent'),
        ('need_to_buy','need_to_buy')], default='sell')
    loai_nha = fields.Char('Loại nhà')
    loai_nha_selection = fields.Selection('get_loai_nha_selection_', string='Loại nhà')
    link = fields.Char()
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
    price = fields.Float()
    price_unit = fields.Char()
    area = fields.Float(digits=(32,1),string='Diện tích')
    address=fields.Char()
    quan_id = fields.Many2one('res.country.district',ondelete='restrict',string='Quận')
    state_id = fields.Many2one('res.country.state',related='quan_id.state_id', store=True)
    phuong_id = fields.Many2one('bds.phuong','Phường')
    date_text = fields.Char()
    public_datetime = fields.Datetime()
    diff_public_datetime = fields.Integer()
    public_date = fields.Date()
    diff_public_date = fields.Integer()
    publicdate_ids =fields.One2many('bds.publicdate','bds_id')
    gialines_ids = fields.One2many('bds.gialines','bds_id')
    diff_gia = fields.Float()
    ngay_update_gia = fields.Datetime()
    #set field (field mà mình điền vào)
    is_read = fields.Boolean()
    quan_tam = fields.Datetime(string=u'Quan Tâm')
    ko_quan_tam = fields.Datetime(string=u'Không Quan Tâm')
    nganh_nghe_kinh_doanh = fields.Char()
    name_of_poster = fields.Char()
    # related no store
    muc_gia_quan = fields.Float(related='quan_id.muc_gia_quan')
    post_ids_of_user  = fields.One2many('bds.bds','poster_id', related='poster_id.post_ids')
    #related store
    detail_du_doan_cc_or_mg = fields.Selection(related='poster_id.detail_du_doan_cc_or_mg', store = True)
    du_doan_cc_or_mg = fields.Selection(related='poster_id.du_doan_cc_or_mg', store = True)
    count_bds_post_of_poster = fields.Integer(related= 'poster_id.count_bds_post_of_poster',store=True,string=u'bds post quantity')
    count_post_all_site = fields.Integer(related= 'poster_id.count_post_all_site',store=True)
    dd_tin_cua_co_rate = fields.Float(related='poster_id.dd_tin_cua_co_rate', store  = True)
    dd_tin_cua_dau_tu_rate = fields.Float(related='poster_id.dd_tin_cua_dau_tu_rate', store  = True)
    len_site = fields.Integer(related='poster_id.len_site', store  = True)
    count_post_of_onesite_max = fields.Integer(related='poster_id.count_post_of_onesite_max', store  = True)
    siteleech_max_id = fields.Many2one(related='poster_id.siteleech_max_id', store  = True)
    #!related store

    # for filter field
    quan_id_selection = fields.Selection('get_quan_')
    siteleech_id_selection = fields.Selection('siteleech_id_selection_')
    greater_day = fields.Integer()# for search field
    # !for filter field



    # compute no store
    html_show = fields.Text(compute='html_show_',string=u'Nội dung')
    html_replace = fields.Html(compute='html_replace_')
    link_show =  fields.Char(compute='link_show_')
    cho_tot_link_fake = fields.Char(compute='cho_tot_link_fake_')
    thumb_view = fields.Binary(compute='thumb_view_')  
    is_user_read_mark = fields.Boolean(compute='_is_user_read_mark')
    is_user_quantam_mark = fields.Boolean(compute='_is_user_quantam_mark')
    diff_public_days_from_now = fields.Integer(compute='_compute_diff_public_days_from_now')
    #! compute no store

    #compute field#store field
    html_khong_dau = fields.Html(compute='html_khong_dau_',store=True)
    so_phong_ngu = fields.Integer(compute='_compute_so_phong_ngu', store=True)
    #dia chi
    # same_address_bds_ids = fields.Many2many('bds.bds','same_bds_and_bds_rel','same_bds_id','bds_id',
    #     )
    # trich_dia_chi = fields.Char(compute='_compute_mat_tien_or_trich_dia_chi', store = True, string='Trích địa chỉ')
    # mat_tien_address = fields.Char(compute ='_compute_mat_tien_or_trich_dia_chi', store=True)
    # mat_tien_or_trich_dia_chi = fields.Char(compute='_compute_mat_tien_or_trich_dia_chi', store=True)
    # is_mat_tien_or_trich_dia_chi = fields.Selection([('1','Có trích địa chỉ hoặc mặt tiền'),
    #     ('0','Không Có trích địa chỉ hoặc mặt tiền' )],compute='_compute_mat_tien_or_trich_dia_chi', store=True)
    
    same_address_bds_ids = fields.Many2many('bds.bds','same_bds_and_bds_rel','same_bds_id','bds_id',
        )
    trich_dia_chi = fields.Char( string='Trích địa chỉ')
    mat_tien_address = fields.Char()
    mat_tien_or_trich_dia_chi = fields.Char()
    is_mat_tien_or_trich_dia_chi = fields.Selection([('1','Có trích địa chỉ hoặc mặt tiền'),
        ('0','Không Có trích địa chỉ hoặc mặt tiền' )])


    #_compute_kw_mg
    dd_tin_cua_co = fields.Selection([('kw_co_cap_1', 'Keyword cò cấp 1'),
        ('no_kw_co_cap_1', 'Không coKeyword cò cấp 1')],compute='_compute_kw_mg', store = True, string='is có kw môi giới')
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
    #!_compute_kw_mg
    #_compute_dd_tin_cua_dau_tu
    dd_tin_cua_dau_tu = fields.Boolean(compute='_compute_dd_tin_cua_dau_tu', store = True,string='kw đầu tư')
    kw_hoa_hong = fields.Char(compute ='_compute_dd_tin_cua_dau_tu', store=True)
    kw_so_tien_hoa_hong = fields.Char(compute ='_compute_dd_tin_cua_dau_tu', store=True)
    #!_compute_dd_tin_cua_dau_tu
   
    hem_rong = fields.Float(digits=(6,2), compute='_compute_loai_hem_combine', store=True)
    hem_rong_char = fields.Char(compute='_compute_loai_hem_combine', store=True)
    loai_hem_selection = fields.Selection([('hxh','hxh'), ('hxt','hxt'), ('hxm','hxm'), ('hbg','hbg')], 
        compute='_compute_loai_hem_combine', store=True)
    loai_hem_combine = fields.Selection([('mt','mặt tiền'), ('hxh','hxh'), ('hxt','hxt'), ('hbg','hbg'), ('hxm','hxm') ],
         compute='_compute_loai_hem_combine', store=True)
    mat_tien = fields.Char(compute='_compute_loai_hem_combine', store=True)
    full_mat_tien = fields.Char(compute='_compute_loai_hem_combine', store=True)
    is_mat_tien = fields.Boolean(compute='_compute_loai_hem_combine', store = True)
    #auto_ngang_doc_
    muc_gia = fields.Selection([('0','0'), ('<1','<1'),('1-2','1-2'),('2-3','2-3'),
                                ('3-4','3-4'),('4-5','4-5'),('5-6','5-6'),
                                ('6-7','6-7'),('7-8','7-8'),('8-9','8-9'),
                                ('9-10','9-10'),('10-11','10-11'),('11-12','11-12'),('>12','>12')],
                               compute='_compute_choosed_area_muc_gia', store = True, string=u'Mức Giá')
    muc_dt = fields.Selection(
        [('0','0'), ('<10','<10'),('10-20','10-20'),('20-30','20-30'),('30-40','30-40'),
        ('40-50','40-50'),('50-60','50-60'),('60-70','60-70'),('>70','>70')],
        compute='_compute_choosed_area_muc_gia', store = True, string=u'Mức diện tích')
    muc_don_gia = fields.Selection([('0','0'),('0-30','0-30'),('30-60','30-60'),('60-90','60-90'),
                                    ('90-120','90-120'),('120-150','120-150'),('150-180','150-180'),
                                    ('180-210','180-210'),('>210','>210')], compute='_compute_choosed_area_muc_gia', store=True )
    ti_le_don_gia = fields.Float(digits=(6,2), compute='_compute_choosed_area_muc_gia', store=True )
    muc_ti_le_don_gia = fields.Selection([('0','0'), ('0-0.4','0-0.4'),('0.4-0.8','0.4-0.8'),('0.8-1.2','0.8-1.2'),
                                    ('1.2-1.6','1.2-1.6'),('1.6-2.0','1.6-2.0'),('2.0-2.4','2.0-2.4'),
                                    ('2.4-2.8','2.4-2.8'),('>2.8','>2.8')], compute='_compute_choosed_area_muc_gia', store=True)
    auto_ngang = fields.Float(compute = '_compute_choosed_area_muc_gia',store=True)
    auto_doc = fields.Float(compute = '_compute_choosed_area_muc_gia',store=True)
    auto_dien_tich = fields.Float(digits=(6,2), compute = '_compute_choosed_area_muc_gia',store=True)
    ti_le_dien_tich_web_vs_auto_dien_tich = fields.Float(digits=(6,2), compute = '_compute_choosed_area_muc_gia',store=True)
    don_gia = fields.Float(digit=(6,2),compute='_compute_choosed_area_muc_gia',store=True,string=u'Đơn giá')
    choose_area = fields.Float(digits=(6,2), compute = '_compute_choosed_area_muc_gia', store=True)#,store=True
    so_lau = fields.Float(digits=(6,1),compute ='_compute_choosed_area_muc_gia',store=True)
    so_lau_he_so = fields.Float(digits=(6,1),compute ='_compute_choosed_area_muc_gia',store=True)
    so_lau_char = fields.Char(compute ='_compute_choosed_area_muc_gia',store=True)
    dtsd = fields.Float(digits=(6,2), compute='_compute_choosed_area_muc_gia', store=True)
    dtsd_tu_so_lau = fields.Float(digits=(6,2), compute='_compute_choosed_area_muc_gia', store=True)
    ti_le_dtsd = fields.Float(digits=(6,2), compute='_compute_choosed_area_muc_gia', store=True)
    dtsd_combine = fields.Float(digits=(6,2), compute='_compute_choosed_area_muc_gia', store=True)
    gia_xac_nha = fields.Float(digits=(6,2), compute='_compute_choosed_area_muc_gia', store=True)
    gia_dat_con_lai = fields.Float(digits=(6,2), compute='_compute_choosed_area_muc_gia', store=True)
    don_gia_dat_con_lai = fields.Float(digits=(6,2), compute='_compute_choosed_area_muc_gia', store=True)
    ti_le_don_gia_dat_con_lai = fields.Float(digits=(6,2), compute='_compute_choosed_area_muc_gia', store=True)
    don_gia_quan = fields.Float(digits=(6,2), compute='_compute_choosed_area_muc_gia', store=True)
    
    # function not depends
    def search(self, args, **kwargs):
        try:
            rs = args.index(1)
        except:
            rs = None
        if rs !=None:
            rs = args.index(1)
            del args[rs]
            user_read_mark = self.env['user.read.mark'].search([('user_id','=',self.env.uid)])
            user_read_mark_bds_ids = user_read_mark.mapped('bds_id')
            if user_read_mark_bds_ids:
                args += [['id', 'not in', user_read_mark_bds_ids]]
        return super(bds, self).search(args, **kwargs)


    @api.model
    def create(self, vals):
        
        r = super(bds,self).create(vals)
        try:
            # pass
            r.count_post_of_poster_()
            # r.poster_id.quanofposter_ids_()
            # r.quan_id.muc_gia_quan_()
            # r.quan_id.len_post_ids_()
        except psycopg2.extensions.TransactionRollbackError:
            pass
        return r

    def make_trigger(self):
        for r in self:
            r.trigger = True

    # method out function
   

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


    def get_quan_(self):
        quans = self.env['res.country.district'].search([])
        rs = list(map(lambda i:(i.name,i.name),quans))
        return rs

    # no store
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

    @api.depends('public_date')
    def _compute_diff_public_days_from_now(self):
        for r in self:
            if r.public_date:
                r.diff_public_days_from_now = (fields.Date.today() - r.public_date).days

   
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
            
    def link_show_(self):
        for r in self:
            if r.siteleech_id.name == 'chotot':
                r.link_show = r.cho_tot_link_fake
            else:
                r.link_show = r.link
                
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

    # ! depend no store


    @api.depends('html')
    @skip_if_cate_not_bds
    def _compute_loai_hem_combine(self):
        for r in self:
            html = r.title + ' '  + r.html
            
            r.mat_tien, r.full_mat_tien, r.is_mat_tien, r.hem_rong_char, r.hem_rong, full_loai_hem,\
            r.loai_hem_selection, r.loai_hem_combine = \
                _compute_loai_hem_combine(html)


    @api.depends('html','title')
    @skip_if_cate_not_bds
    def _compute_mat_tien_or_trich_dia_chi(self):
        for r in self:
            html = r.title + ' ' + r.html
            html_trich_dia_chi = r.title or '' +  r.html or '' + r.address or ''
            r.mat_tien_address, r.trich_dia_chi, r.mat_tien_or_trich_dia_chi, r.is_mat_tien_or_trich_dia_chi,\
            r.same_address_bds_ids = \
            _compute_mat_tien_or_trich_dia_chi(self, html, html_trich_dia_chi, r)

            
    @api.depends('html')
    @skip_if_cate_not_bds
    def _compute_so_phong_ngu(self):
        for r in self:
            html = (r.title or '' ) + ' ' + (r.html or '')
            so_phong_ngu = _compute_so_phong_ngu(html)
            r.so_phong_ngu = so_phong_ngu


    @api.depends('html', 'title')
    @skip_if_cate_not_bds 
    def _compute_kw_mg(self):  
        for r in self:
            html = r.title + ' ' + r.html
            r.kw_co_date, r.kw_mg_cap_2, r.is_kw_mg_cap_2, r.kw_co_special_break, r.kw_co_break,\
                r.hoa_la_canh, r.t1l1, r.kw_mg, r.dd_tin_cua_co = _compute_kw_mg(html)
            
    



    @api.depends('html','cate','area','trigger','gia','loai_hem_combine')
    @skip_if_cate_not_bds            
    def _compute_choosed_area_muc_gia(self):
        for r in self:
            html = r.title + r.html
            gia = r.gia
            quan_id = r.quan_id
            loai_hem_combine = r.loai_hem_combine
            area = r.area


            don_gia_quan, ti_le_don_gia_dat_con_lai, ti_le_don_gia, \
            auto_ngang, auto_doc, auto_dien_tich, ti_le_dien_tich_web_vs_auto_dien_tich, \
            dtsd, choose_area, so_lau, so_lau_char, so_lau_he_so,\
            dtsd_tu_so_lau, ti_le_dtsd, dtsd_combine, gia_xac_nha,\
            gia_dat_con_lai, don_gia_dat_con_lai, don_gia, muc_don_gia,\
            muc_ti_le_don_gia, muc_dt, muc_gia = _compute_choosed_area_muc_gia(html, gia, area, quan_id, loai_hem_combine)


            r.don_gia_quan = don_gia_quan
            r.ti_le_don_gia_dat_con_lai = ti_le_don_gia_dat_con_lai
            r.ti_le_don_gia  = ti_le_don_gia
            r.auto_ngang,r.auto_doc, r.auto_dien_tich, r.ti_le_dien_tich_web_vs_auto_dien_tich =\
                 auto_ngang, auto_doc, auto_dien_tich, ti_le_dien_tich_web_vs_auto_dien_tich
            r.dtsd = dtsd
            r.choose_area = choose_area
            r.so_lau = so_lau
            r.so_lau_char = so_lau_char
            r.so_lau_he_so = so_lau_he_so

            r.dtsd_tu_so_lau = dtsd_tu_so_lau
            r.ti_le_dtsd = ti_le_dtsd
            r.dtsd_combine = dtsd_combine 
            r.gia_xac_nha = gia_xac_nha

            r.gia_dat_con_lai = gia_dat_con_lai
            r.don_gia_dat_con_lai = don_gia_dat_con_lai
            r.don_gia = don_gia
            r.muc_don_gia = muc_don_gia
            r.muc_ti_le_don_gia = muc_ti_le_don_gia
            r.muc_dt = muc_dt
            r.muc_gia = muc_gia

    @api.depends('html')
    @skip_if_cate_not_bds               
    def _compute_dd_tin_cua_dau_tu(self):
        for r in self:
            r.kw_hoa_hong, r.kw_so_tien_hoa_hong, r.dd_tin_cua_dau_tu =  _compute_dd_tin_cua_dau_tu(r.html)
                    
    
    @api.depends('html')
    def html_khong_dau_(self):
        for r in self:
            r.html_khong_dau = unidecode(r.html) if r.html else r.html
  

    # out function 
    def send_mail_chinh_chu(self):
        body_html = ''
        minutes = int(self.env['ir.config_parameter'].sudo().get_param('bds.interval_mail_chinh_chu_minutes',default=0))
        if minutes ==0:
            minutes=5
        gia = float(self.env['ir.config_parameter'].sudo().get_param('bds.gia',default=0))
        if gia ==0:
            gia =13
        minutes_5_last = fields.Datetime.now() -   datetime.timedelta(minutes=minutes, seconds=1)
        cr = self.search([('create_date','>', minutes_5_last),
            ('quan_id.name', 'in',['Quận 1','Quận 3', 'Quận 5', 'Quận 10', 'Quận Tân Bình', 'Quận Tân Phú', 'Quận Phú Nhuận', 'Quận Bình Thạnh']),
            '|', '&', ('trich_dia_chi','!=',False), ('gia','<', gia), '&', ('mat_tien_address','!=',False), ('gia','<', 13)
            ])
        if cr:
            for r in cr:
                one_mail_html = r.html_show
                images = r.images_ids
                image_tags = map(lambda i: '<img src="%s" style="width:300px" alt="Girl in a jacket">'%i, list(images.mapped('url')) + [r.thumb])
                image_html = '<br>'.join(image_tags)
                one_mail_html += '<br>' + image_html

                body_html += '<br><br><br>' + one_mail_html
            email_to = self.env['ir.config_parameter'].sudo().get_param('bds.email_to')
            if email_to:
                email_to = email_to.split(',')
            else:
                email_to = []
            email_to.append('nguyenductu@gmail.com')
            email_to = ','.join(email_to)
            mail_id = self.env['mail.mail'].create({
                'subject':'%s topic chính chủ trong 5 phút qua'%(len(cr)),
                'email_to':email_to,
                'body_html': body_html,
                })
            mail_id.send()

    def cronjob_trich_dia_chi_tieu_chi(self):
        query = 'select count(mat_tien_address) as count,mat_tien_address,poster_id,siteleech_id from bds_bds where mat_tien_address is not null group by mat_tien_address,poster_id,siteleech_id having count(mat_tien_address) > 2 ORDER BY count desc limit 3'
        query = 'select count(trich_dia_chi) as count,trich_dia_chi,poster_id,siteleech_id from bds_bds where trich_dia_chi is not null group by trich_dia_chi,poster_id,siteleech_id having count(trich_dia_chi) > 0 ORDER BY count desc limit 3'
        self.env.cr.execute(query)
        rss = self.env.cr.fetchall()
        for rs in rss:
            search_dict = {'tieu_chi_char_1':rs[1], 'tieu_chi_int_2':rs[3], 'tieu_chi_int_2':rs[2]} # tieu_chi_int_2: siteleech_id
            update_dict = {'tieu_chi_int_1':rs[0]}#tieu_chi_int_1: count
            quan = g_or_c_ss(self.env['bds.tieuchi'],search_dict, update_dict )
        

    def test(self):
        readgroup_rs = self.env['bds.bds'].read_group([('don_gia','>=', 20), ('don_gia','<=', 300),('poster_id','=',18)],['quan_id','siteleech_id','avg_gia:avg(gia)','count(quan_id)'],['quan_id','siteleech_id'], lazy=False)
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
           
            site_id = bds_id.siteleech_id.id
            site_post_count = r.site_post_count
            one_site_post_count = site_post_count.get(str(site_id),0)
            site_post_count[str(site_id)] = one_site_post_count + 1
            poster_dict['site_post_count'] = site_post_count
            count_post_of_onesite_max = max(site_post_count.items(), key=operator.itemgetter(1))[1]
            count_post_all_site = r.count_post_all_site + 1
            poster_dict['count_post_all_site'] = count_post_all_site
            
            if bds_id.mat_tien_or_trich_dia_chi:
                address_topic_number = r.address_topic_number + 1
                r.address_topic_number = address_topic_number
            else:
                address_topic_number = 0  


            address_rate = address_topic_number/count_post_all_site
            poster_dict['address_rate'] = address_rate
            # else:
            #     address_topic_number = r.address_topic_number


            poster_dict['count_post_of_onesite_max'] = count_post_of_onesite_max

            # address_topic_number = self.search_count([('poster_id','=',r.id),('trich_dia_chi','!=', False)])
            # poster_dict['address_topic_number'] = address_topic_number

            if bds_id.mat_tien_or_trich_dia_chi:
                self.env['bds.address'].write_address_to_table(bds_id.mat_tien_or_trich_dia_chi, bds_id.siteleech_id.id, bds_id.id, r.id)

            # if count_post_all_site:
            guess_count  = r.guess_count
            guess_count['address_rate'] = address_rate
            dd_tin_cua_co_count  = guess_count.get('dd_tin_cua_co_count', 0)
            # dd_tin_cua_co_count  = r.dd_tin_cua_co_count
            if bds_id.dd_tin_cua_co:
                dd_tin_cua_co_count +=1
                guess_count['dd_tin_cua_co_count'] = dd_tin_cua_co_count
                poster_dict['dd_tin_cua_co_rate'] = dd_tin_cua_co_count/count_post_all_site
                r.dd_tin_cua_co_count = dd_tin_cua_co_count
            
            dd_tin_cua_dau_tu_count  = guess_count.get('dd_tin_cua_dau_tu_count', 0)
            if bds_id.dd_tin_cua_dau_tu:
                dd_tin_cua_dau_tu_count +=1
                guess_count['dd_tin_cua_dau_tu_count'] = dd_tin_cua_dau_tu_count
                poster_dict['dd_tin_cua_dau_tu_rate'] = dd_tin_cua_dau_tu_count/count_post_all_site
                r.dd_tin_cua_dau_tu_count = dd_tin_cua_dau_tu_count
            
            
            r.guess_count = guess_count 
            chotot_moi_gioi_count  = guess_count.get('chotot_moi_gioi_count', 0)
            chotot_chinh_chu_count  = guess_count.get('chotot_chinh_chu_count', 0)
            if bds_id.siteleech_id.name =='chotot':
                if bds_id.chotot_moi_gioi_hay_chinh_chu =='moi_gioi':
                    chotot_moi_gioi_count += 1
                    guess_count['chotot_moi_gioi_count'] = chotot_moi_gioi_count
                else:
                    chotot_chinh_chu_count += 1
                    guess_count['chotot_chinh_chu_count'] = chotot_chinh_chu_count
            count_chotot_moi_gioi = self.search_count([('poster_id','=',r.id),('siteleech_id.name','=', 'chotot'), ('chotot_moi_gioi_hay_chinh_chu','=', 'moi_gioi')])
            
            if chotot_moi_gioi_count:
                chotot_mg_or_cc = 'moi_gioi'
            else:
                if chotot_chinh_chu_count:
                    chotot_mg_or_cc = 'chinh_chu'
                else:
                    chotot_mg_or_cc = 'khong_biet'
            poster_dict['chotot_mg_or_cc'] = chotot_mg_or_cc
            guess_count['chotot_mg_or_cc'] = chotot_mg_or_cc
            # dd_tin_cua_co = self.search_count([('poster_id','=',r.id),('dd_tin_cua_co','=', 'kw_co_cap_1')])
            # dd_tin_cua_dau_tu = self.search_count([('poster_id','=',r.id),('dd_tin_cua_dau_tu','!=', False)])
            
            if chotot_mg_or_cc =='moi_gioi' :
                if address_rate > 0.5:
                    du_doan_cc_or_mg= 'dd_cc'
                    detail_du_doan_cc_or_mg = 'dd_cc_b_moi_gioi_n_address_rate_gt_0_5'
                else:
                    du_doan_cc_or_mg= 'dd_mg'
                    detail_du_doan_cc_or_mg = 'dd_mg_b_moi_gioi_n_address_rate_lte_0_5'
            elif dd_tin_cua_co_count:
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
                if  dd_tin_cua_dau_tu_count:
                    du_doan_cc_or_mg= 'dd_dt'
            poster_dict['du_doan_cc_or_mg'] = du_doan_cc_or_mg
            poster_dict['detail_du_doan_cc_or_mg'] = detail_du_doan_cc_or_mg
            r.guess_count = guess_count
            r.write(poster_dict)




    #
    
        

               

