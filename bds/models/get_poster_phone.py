from odoo import models, fields, api,sql_db
import logging
from odoo.addons.bds.models.bds_tools import g_or_c_ss
import re
import datetime
from odoo.osv import expression

MOBILE_DAU_SO = {'vina':'(^091|^094|^083|^084|^085|^081|^082)',
                        'mobi':'(^090|^093|070|^079|^077|^076|^078)',
                       'viettel':'(^086|^096|^097|^098|^032|^033|^034|^035|^036|^037|^038|^039)'}


class GetPhonePoster(models.Model):
    _name = 'bds.getphoneposter'
    name = fields.Char(compute='name_',store=True)
    
    nha_mang = fields.Selection([('vina','vina'),('mobi','mobi'),('viettel','viettel'),('khac','khac')],default='mobi')
    post_count_min = fields.Integer(default=10)
    # loc_gian_tiep_quan_bds_topic = fields.Selection([
    #     (u'poster_obj',u'Qua poster Object'),
    #     (u'bds_obj',u'Qua BDS Object'),
    #     (u'bds_sql',u'Qua BDS SQL'),
    #     ],default = u'poster_obj',required=True)
    
    
    poster_ids = fields.Many2many('bds.poster', compute='poster_ids_')
    len_poster = fields.Integer(compute='poster_ids_', store=True)
    phone_list = fields.Text(compute='poster_ids_', store=True)
    quan_id = fields.Many2one('res.country.district')
    not_in_phone = fields.Text()

    @api.depends('nha_mang')
    def name_(self):
        for r in self:
            r.name = u'id %s- nhà mạng %s' %(r.id or 'New',r.nha_mang)
    
    @api.depends('post_count_min','quan_id', 'nha_mang','not_in_phone')
    def poster_ids_(self):
        for r in self:
         
            where_clause = 'where quan_id = %s'%r.quan_id.id if r.quan_id else ''
            qr = '''select count(poster_id), bds_poster.name, poster_id from bds_bds left join bds_poster on poster_id = bds_poster.id %(where_clause)s group by 
                poster_id, bds_poster.name having count(poster_id) > %(post_count_min)s order by count(poster_id) desc'''%{'post_count_min':r.post_count_min,
                'where_clause':where_clause
                }
            self.env.cr.execute(qr)
            rs = self.env.cr.fetchall()
            phone_list = [i[1] for i in rs]
            if r.nha_mang:
                dau_so_pattern = MOBILE_DAU_SO[r.nha_mang]
                phone_list = list(filter(lambda i: re.search(dau_so_pattern, i), phone_list))
            if r.not_in_phone:
                not_in_phone = r.not_in_phone.split(',')
                not_in_phone = [i.replace("'",'').replace(" ",'') for i in not_in_phone]
                # print ('***not_in_phone***', not_in_phone)
                phone_list = list(filter(lambda i: i not in not_in_phone , phone_list))
            phone_list_txt = ','.join(phone_list )


            r.len_poster = len(phone_list)
            # poster_ids = [i[2] for i in rs]
            r.phone_list = phone_list_txt
            # r.poster_ids = poster_ids

    # @api.depends('loc_gian_tiep_quan_bds_topic','post_count_min','nha_mang')
    # def poster_ids_(self):
    #     for r in self:
    #         poster_ids = False
    #         if r.loc_gian_tiep_quan_bds_topic ==u'poster_obj':
    #             domain_tong = []
    #             if r.nha_mang:
    #                 nha_mang_domain = ('nha_mang','=',r.nha_mang)
    #                 domain_tong.append(nha_mang_domain)
               
    #             if r.post_count_min:
    #                 domain_tong = expression.AND([[('quanofposter_ids.quantity','>=',r.post_count_min)], domain_tong])
    #             poster_ids = self.env['bds.poster'].search(domain_tong)

      

    #         elif r.loc_gian_tiep_quan_bds_topic ==u'bds_obj':
    #             domain = []
    #             if  r.post_count_min:
    #                 domain = expression.AND([[('count_post_all_site','>=',r.post_count_min)],domain])
    #             bds_ids = self.env['bds.bds'].search(domain)
    #             post_ids = bds_ids.mapped('poster_id')
    #             if r.nha_mang:
    #                 post_ids = post_ids.filtered(lambda i: i.nha_mang == r.nha_mang)

            

    #         elif r.loc_gian_tiep_quan_bds_topic == u'bds_sql':
    #             slq_cmd = '''select distinct p.id from bds_bds as b inner join bds_poster as p on b.poster_id = p.id'''
    #             where_list = []
                
    #             if r.post_count_min:
    #                 where_list.append("b.count_post_all_site >= %s"%r.post_count_min)
    #             if r.nha_mang:
    #                 where_list.append("p.nha_mang ='%s'"%r.nha_mang)
    #             where_clause = u' and '.join(where_list)
    #             if where_list:
    #                 slq_cmd = slq_cmd + ' where ' + where_clause
    #             self.env.cr.execute(slq_cmd)
    #             rsul = self.env.cr.fetchall()
    #             poster_ids = list(map(lambda i:i[0],rsul))

    #         if poster_ids:
    #             domain = [('id','!=', r.id)] if isinstance(r.id, int) else []
    #             send_poster_ids = self.search(domain)
    #             filter_poster_ids = send_poster_ids.mapped('poster_ids')
    #             rs_poster_ids = self.env['bds.poster']
    #             # poster_ids = [p for p in poster_ids if p not in filter_poster_ids]
    #             for p in poster_ids:
    #                 if p not in filter_poster_ids:
    #                     rs_poster_ids +=p
    #             r.poster_ids = rs_poster_ids
    #             r.len_poster = len(rs_poster_ids)
    #             phone_lists = filter(lambda l: not isinstance(l,bool),r.poster_ids.mapped('phone'))
    #             r.phone_list = ','.join(phone_lists)

