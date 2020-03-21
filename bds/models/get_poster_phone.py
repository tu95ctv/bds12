from odoo import models, fields, api,sql_db
from odoo.addons.bds.models.import_contact import import_contact
import logging
from odoo.addons.bds.models.bds_tools import g_or_c_ss
import re
import datetime
from odoo.osv import expression




class GetPhonePoster(models.Model):
    _name = 'bds.getphoneposter'
    name = fields.Char(compute='name_',store=True)
    
    nha_mang = fields.Selection([('vina','vina'),('mobi','mobi'),('viettel','viettel'),('khac','khac')],default='mobi')
    post_count_min = fields.Integer(default=10)
    loc_gian_tiep_quan_bds_topic = fields.Selection([
        (u'poster_obj',u'Qua poster Object'),
        (u'bds_obj',u'Qua BDS Object'),
        (u'bds_sql',u'Qua BDS SQL'),
        ],default = u'poster_obj',required=True)
    
    
    poster_ids = fields.Many2many('bds.poster', compute='poster_ids_')
    len_poster = fields.Integer(compute='poster_ids_', store=True)
    phone_list = fields.Text(compute='poster_ids_', store=True)
    

    @api.depends('nha_mang')
    def name_(self):
        for r in self:
            r.name = u'id %s- nhà mạng %s' %(r.id or 'New',r.nha_mang)

    @api.depends('loc_gian_tiep_quan_bds_topic','post_count_min','nha_mang')
    def poster_ids_(self):
        for r in self:
            poster_ids = False
            if r.loc_gian_tiep_quan_bds_topic ==u'poster_obj':
                domain_tong = []
                if r.nha_mang:
                    nha_mang_domain = ('nha_mang','=',r.nha_mang)
                    domain_tong.append(nha_mang_domain)
               
                if r.post_count_min:
                    domain_tong = expression.AND([[('quanofposter_ids.quantity','>=',r.post_count_min)], domain_tong])
                poster_ids = self.env['bds.poster'].search(domain_tong)

      

            elif r.loc_gian_tiep_quan_bds_topic ==u'bds_obj':
                domain = []
                if  r.post_count_min:
                    domain = expression.AND([[('count_post_all_site','>=',r.post_count_min)],domain])
                bds_ids = self.env['bds.bds'].search(domain)
                post_ids = bds_ids.mapped('poster_id')
                if r.nha_mang:
                    post_ids = post_ids.filtered(lambda i: i.nha_mang == r.nha_mang)

            

            elif r.loc_gian_tiep_quan_bds_topic == u'bds_sql':
                slq_cmd = '''select distinct p.id from bds_bds as b inner join bds_poster as p on b.poster_id = p.id'''
                where_list = []
                
                if r.post_count_min:
                    where_list.append("b.count_post_all_site >= %s"%r.post_count_min)
                if r.nha_mang:
                    where_list.append("p.nha_mang ='%s'"%r.nha_mang)
                where_clause = u' and '.join(where_list)
                if where_list:
                    slq_cmd = slq_cmd + ' where ' + where_clause
                self.env.cr.execute(slq_cmd)
                rsul = self.env.cr.fetchall()
                poster_ids = list(map(lambda i:i[0],rsul))

            if poster_ids:
                domain = [('id','!=', r.id)] if isinstance(r.id, int) else []
                print ('***domain***', domain,'***poster_ids**', poster_ids)
                send_poster_ids = self.search(domain)
                filter_poster_ids = send_poster_ids.mapped('poster_ids')
                rs_poster_ids = self.env['bds.poster']
                # poster_ids = [p for p in poster_ids if p not in filter_poster_ids]
                for p in poster_ids:
                    if p not in filter_poster_ids:
                        rs_poster_ids +=p
                r.poster_ids = rs_poster_ids
                r.len_poster = len(rs_poster_ids)
                phone_lists = filter(lambda l: not isinstance(l,bool),r.poster_ids.mapped('phone'))
                r.phone_list = ','.join(phone_lists)

