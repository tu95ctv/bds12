# -*- coding: utf-8 -*-
from odoo import models, fields, api,sql_db
import re
from unidecode import unidecode

def is_number(str):
    rs = re.match('\d+$',str,re.I)
    if rs:
        return True
    else:
        return False
    
    
def viet_tat(string):
    string = string.strip()
    ns = re.sub('\s{2,}', ' ', string)
    ns = re.sub('[^\w ]','', ns,flags = re.UNICODE)
    slit_name = ns.split(' ')
    slit_name = filter(lambda w : True if w else False, slit_name)
    one_char_slit_name = map(lambda w: w[0] if not is_number(w) else w,slit_name)
    rs = ''.join(one_char_slit_name).upper()
    return rs

def name_khong_dau_compute(self_):
    for r  in self_:
        if r.name:
            name = r.name
            if name:
                try:
                    name_khong_dau = unidecode(name)
                except:
                    raise ValueError(name)
                r.name_khong_dau = name_khong_dau
                r.name_viet_tat = viet_tat(name_khong_dau)
                
class KhongDauModel(models.Model):
    _name = 'khongdaumodel'
    _auto = False
    name = fields.Char()
    name_khong_dau = fields.Char(compute='name_khong_dau_', store=True)
    name_viet_tat =  fields.Char(compute='name_khong_dau_', store=True)
    @api.depends('name')
    def name_khong_dau_(self):
        name_khong_dau_compute(self)
        
        
class QuanHuyen(models.Model):
    _name = 'bds.quan'
    _inherit = ['khongdaumodel']
    _auto = True
    name = fields.Char()
    name_unidecode = fields.Char()
    name_without_quan = fields.Char()
    post_ids = fields.One2many('bds.bds','quan_id')
    muc_gia_quan = fields.Float(digit=(6,2),compute='muc_gia_quan_',store=True,string=u'Mức Đơn Giá(triệu/m2)')
    len_post_ids = fields.Integer(compute='len_post_ids_')
    level = fields.Selection([('trung_tam','Trung Tâm'), ('kha_trung_tam','Khá Trung Tâm'), ('vung_ven','Vùng ven')])

    @api.depends('post_ids')
    def len_post_ids_(self):
        for r in self:
            r.len_post_ids = self.env['bds.bds'].search_count([('quan_id','=',r.id)])
#             r.len_post_ids = len(r.post_ids)
        
    @api.depends('name')
    def name_khong_dau_(self):
        name_khong_dau_compute(self)
        
    @api.depends('post_ids')
    def muc_gia_quan_(self):
        for r in self:
            # sql_cmd = "select AVG(don_gia),count(id) from bds_bds where  quan_id = %s and  don_gia >= 20 and don_gia <300"%r.id
            # self.env.cr.execute(sql_cmd)
            # rsul = self.env.cr.fetchall()
            # r.muc_gia_quan = rsul[0][0]
            readgroup_rs = self.env['bds.bds'].read_group([('don_gia','>=', 20), ('don_gia','<=', 300),('quan_id','=',r.id)],['don_gia:avg(don_gia)'],[])
            rs = readgroup_rs[0]['don_gia']
            r.muc_gia_quan = rs
    
    def set_cron_quan_trung_tam(self):
        trung_tams = ['quận 1', 'quận 3', 'quận 5', 'quận 10', 'quận tân bình', 'quận phú nhuận', 'quận tân bình', 'quận tân phú']
       
        for quan_name in trung_tams:
            match_quan = self.search([('name','=ilike',quan_name)])
            if match_quan:
                match_quan.level = 'trung_tam'
            
class Phuong(models.Model):
    _name = 'bds.phuong'
    name = fields.Char(compute='name_',store=True)
    name_phuong = fields.Char()
    quan_id = fields.Many2one('bds.quan')
    name_unidecode = fields.Char()
    @api.depends('name_phuong','quan_id')
    def name_(self):
        self.name = ( self.name_phuong if self.name_phuong else '' )+ ('-' + self.quan_id.name) if self.quan_id.name else ''
    @api.multi
    def name_get(self):
        res = []
        for r in self:
            new_name = u'phường ' + r.name
            res.append((r.id,new_name))
        return res  