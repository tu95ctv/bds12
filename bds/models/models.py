# -*- coding: utf-8 -*-
from odoo import models, fields, api,sql_db
from odoo.addons.bds.models.import_contact import import_contact
import logging
from odoo.addons.bds.models.bds_tools import g_or_c_ss
import re
import datetime
from odoo.osv import expression



class SiteDuocLeech(models.Model):
    _name = 'bds.siteleech'
    name = fields.Char() 
    name_viet_tat = fields.Char()  
    
class Images(models.Model):
    _name = 'bds.images'
    url = fields.Char()
    bds_id = fields.Many2one('bds.bds')

class PosterNameLines(models.Model):
    _name = 'bds.posternamelines'
    username_in_site = fields.Char()
    site_id = fields.Many2one('bds.siteleech')
    poster_id = fields.Many2one('bds.poster')

    
class QuanOfPoster(models.Model):
    _name = 'bds.quanofposter'
    name = fields.Char(compute='name_',store=True)
    
    quan_id = fields.Many2one('bds.quan')
    siteleech_id = fields.Many2one('bds.siteleech')
    quantity = fields.Integer()
    min_price = fields.Float(digits=(32,1))
    avg_price = fields.Float(digits=(32,1))
    max_price = fields.Float(digits=(32,1))
    poster_id = fields.Many2one('bds.poster')
    @api.depends('quan_id','quantity') 
    def name_(self):
        for r in self:
            if r.siteleech_id or  r.quan_id:
                r.name = (( r.siteleech_id.name + ' ' ) if r.siteleech_id.name else '') +  r.quan_id.name + ':' + str(r.quantity)
            else:
                r.name ='all'

   



class Importcontact(models.Model):
    _name = 'bds.importcontact'
    file = fields.Binary()
    land_contact_saved_number = fields.Integer()
    trigger_fields = fields.Selection([('bds.bds','bds.bds')])
    
    @api.multi
    def trigger(self):
        self.env[self.trigger_fields].search([]).write({'is_triger':True})
    @api.multi
    def import_contact(self):
        import_contact(self)
        
  
    @api.multi
    def count_post_of_poster(self):
        for r in self.env['bds.poster'].search([]):
            post_of_poster_cho_tot = self.env['bds.bds'].search([('poster_id','=',r.id),('link','like','chotot')])
            count_bds_post_of_poster = self.env['bds.bds'].search([('poster_id','=',r.id),('link','like','batdongsan')])
            r.count_chotot_post_of_poster = len(post_of_poster_cho_tot)
            r.count_bds_post_of_poster = len(count_bds_post_of_poster)
            count_bds_post_of_poster = self.env['bds.bds'].search([('poster_id','=',r.id)])
            r.count_post_all_site = len(count_bds_post_of_poster)
            
    @api.multi
    def insert_count_by_sql(self):
        product_category_query = '''UPDATE bds_poster 
SET count_post_all_site = i.count
FROM (
    SELECT count(id),poster_id
    FROM bds_bds group by poster_id)  i
WHERE 
    i.poster_id = bds_poster.ID

'''    
        
        #self.env.cr.execute(product_category_query)
        
        bds_site = self.env['bds.siteleech'].search([('name','like','batdongsan')]).id
        chotot_site = self.env['bds.siteleech'].search([('name','like','chotot')]).id
        for x in [bds_site,chotot_site]:
            if x ==bds_site:
                name = 'bds'
            else:
                name ='chotot'
            product_category_query = '''UPDATE bds_poster 
    SET count_post_of_poster_%s = i.count
    FROM (
        SELECT count(id),poster_id,siteleech_id
        FROM bds_bds group by poster_id,siteleech_id)  i
    WHERE 
        i.poster_id = bds_poster.ID and i.siteleech_id=%s'''%(name,x)
        
            self.env.cr.execute(product_category_query) 
        #product_category = self.env.cr.fetchall()
        ##print product_category
    @api.multi
    def add_nha_mang(self):
        for r in self.env['bds.poster'].search([]):
            #print 'handling...',r.name
            patterns = {'vina':'(^091|^094|^0123|^0124|^0125|^0127|^0129|^088)',
                        'mobi':'(^090|^093|^089|^0120|^0121|^0122|^0126|^0128)',
                       'viettel': '(^098|^097|^096|^0169|^0168|^0167|^0166|^0165|^0164|^0163|^0162|^086)'}
            if r.phone:
                for nha_mang,pattern in patterns.items():
                    rs = re.search(pattern, r.phone)
                    if rs:
                        r.nha_mang = nha_mang
                        break
                if not rs:
                    r.nha_mang = 'khac'
    
    @api.multi
    def add_site_leech_tobds(self):
        chotot_site = self.env['bds.siteleech'].search([('name','ilike','chotot')])
        ctbds = self.env['bds.bds'].search([('link','ilike','chotot')])
        ctbds.write({'siteleech_id':chotot_site.id})
        
        chotot_site = self.env['bds.siteleech'].search([('name','ilike','batdongsan')])
        ctbds = self.env['bds.bds'].search([('link','ilike','batdongsan')])
        ctbds.write({'siteleech_id':chotot_site.id})
        
    
  
    @api.multi
    def add_min_max_avg_for_user(self):
        for c,r in enumerate(self.env['bds.poster'].search([])):
            #print 'hadling...one usee' ,c
            product_category_query = '''select min(gia),avg(gia),max(gia) from bds_bds  where poster_id = %s and gia > 0'''%r.id
            self.env.cr.execute(product_category_query)
            product_category = self.env.cr.fetchall()
            r.min_price = product_category[0][0]
            r.avg_price = product_category[0][1]
            r.max_price = product_category[0][2]
            #print' min,avg,max', product_category
            
    @api.multi
    def add_quan_lines_ids_to_poster(self):
        for c,r in enumerate(self.env['bds.poster'].search([])):
            #print 'hadling...one usee' ,c
            product_category_query =\
             '''select count(quan_id),quan_id,min(gia),avg(gia),max(gia) from bds_bds where poster_id = %s group by quan_id'''%r.id
            self.env.cr.execute(product_category_query)
            product_category = self.env.cr.fetchall()
            #print product_category
            for  tuple_count_quan in product_category:
                quan_id = int(tuple_count_quan[1])
                #quantity = int(tuple_count_quan[0].replace('L',''))
                quan = self.env['bds.quan'].browse(quan_id)
                if quan.name in [u'Quận 1',u'Quận 3',u'Quận 5',u'Quận 10',u'Tân Bình']:
                    for key1 in ['count','avg']:
                        if key1 =='count':
                            value = tuple_count_quan[0]
                        elif key1 =='avg':
                            value = tuple_count_quan[3]
                        name = quan.name_unidecode.replace('-','_')
                        name = key1+'_'+name
                        setattr(r, name, value)
                        #print 'set attr',name,value
                g_or_c_ss(self,'bds.quanofposter', {'quan_id':quan_id,
                                                             'poster_id':r.id}, {'quantity':tuple_count_quan[0],
                                                                                'min_price':tuple_count_quan[2],
                                                                                'avg_price':tuple_count_quan[3],
                                                                                'max_price':tuple_count_quan[4],
                                                                                 }, True)
                
                
    @api.multi
    def add_quan_lines_ids_to_poster_theo_siteleech_id(self):
        for c,r in enumerate(self.env['bds.poster'].search([])):
            
            product_category_query_siteleech =\
             '''select count(quan_id),quan_id,min(gia),avg(gia),max(gia),siteleech_id from bds_bds where poster_id = %s group by quan_id,siteleech_id'''%r.id
            product_category_query_no_siteleech = \
            '''select count(quan_id),quan_id,min(gia),avg(gia),max(gia) from bds_bds where poster_id = %s group by quan_id'''%r.id
            a = {'product_category_query_siteleech':product_category_query_siteleech,
                 'product_category_query_no_siteleech':product_category_query_no_siteleech
                 }
            for k,product_category_query in a.items():
                self.env.cr.execute(product_category_query)
                product_category = self.env.cr.fetchall()
                #print product_category
                for  tuple_count_quan in product_category:
                    quan_id = int(tuple_count_quan[1])
                    if k =='product_category_query_no_siteleech':
                        siteleech_id =False
                    else:
                        siteleech_id = int(tuple_count_quan[5])
                    g_or_c_ss(self,'bds.quanofposter', {'quan_id':quan_id,
                                                                 'poster_id':r.id,'siteleech_id':siteleech_id}, {'quantity':tuple_count_quan[0],
                                                                                    'min_price':tuple_count_quan[2],
                                                                                    'avg_price':tuple_count_quan[3],
                                                                                    'max_price':tuple_count_quan[4],
                                                                                     }, True)
                
            
    @api.multi
    def add_site_leech_to_url(self):
        for r in self.env['bds.url'].search([]):
            r.url = r.url
 
class Luong(models.Model):
    _name = 'bds.luong'
    threadname = fields.Char()
    url_id = fields.Many2one('bds.url')
    current_page = fields.Integer()

    
class Cron(models.Model):
 
    _inherit = "ir.cron"
    _logger = logging.getLogger(_inherit)
    @api.model
    def worker(self,thread_index,url_id,thread_number):
        new_cr = sql_db.db_connect(self.env.cr.dbname).cursor()
        uid, context = self.env.uid, self.env.context
        with api.Environment.manage():
            self.env = api.Environment(new_cr, uid, context)
            luong = g_or_c_ss(self,'bds.luong', {'threadname':str(1),'url_id':url_id})
            if luong[0].current_page==0:
                current_page = thread_index
            else:
                current_page = luong[0].current_page + thread_number
            luong[0].write({'current_page':current_page})
            new_cr.commit()
            self.env.cr.close()
def name_compute(r,adict=None,join_char = u' - '):
    names = []
    for fname,attr_dict in adict:
        val = getattr(r,fname)
        fnc = attr_dict.get('fnc',None)
        if fnc:
            val = fnc(val)
        if  not val:# Cho có trường hợp New ID
            if attr_dict.get('skip_if_False',True):
                continue
            if  fname=='id' :
                val ='New'
            else:
                val ='_'
        if attr_dict.get('pr',None):
            item =  attr_dict['pr'] + u': ' + unicode(val)
        else:
            item = unicode (val)
        names.append(item)
    if names:
        name = join_char.join(names)
    else:
        name = False
    return name
class IphoneType(models.Model):
    _name = 'iphonetype'
    name = fields.Char(compute='name_',store=True)
    name_cate = fields.Char()
    dung_luong = fields.Integer()
    nhap_khau_hay_chinh_thuc = fields.Selection([(u'nhập khẩu',u'Nhập Khẩu'),(u'chính thức',u'chính Thức')])
    @api.depends('name_cate','dung_luong','nhap_khau_hay_chinh_thuc')
    def name_(self):
        for r in self:
            r.name = \
            name_compute(r,[('name_cate',{}),
                            ('dung_luong',{}),
                            ('nhap_khau_hay_chinh_thuc',{})
                            ]
            )
class DienThoai(models.Model):
    _name = 'dienthoai'
    iphonetype_id = fields.Many2one('iphonetype')
    title = fields.Char()
    link = fields.Char()
    gia = fields.Float(digit=(6,2))
    so_luong = fields.Integer()
    duoc_ban_boi = fields.Char()
    is_bien_dong_item = fields.Boolean()
    original_itself_id = fields.Many2one('dienthoai')
    bien_dong_ids = fields.One2many('dienthoai','original_itself_id')
    topic_id  =  fields.Char()
    gia_hien_thoi = fields.Float(digit=(6,2))
    noi_dung_bien_dong = fields.Char()
    so_luong_hien_thoi = fields.Char()


        
        
class Mycontact(models.Model):
    _name = 'bds.mycontact'
    name = fields.Char()
    phone = fields.Char()