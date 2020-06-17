# -*- coding: utf-8 -*-
from odoo import models, fields, api
# from odoo.addons.bds.models.fetch import fetch, fetch_all_url
import re
from odoo import models,fields
from odoo.addons.bds.models.bds_tools  import  FetchError



#lam gon lai ngay 23/02
class Fetch(models.Model):
    _name = 'bds.fetch'
    _inherit = 'abstract.main.fetch'
    _auto = True
    name = fields.Char(compute='_compute_name', store=True)
    url_id = fields.Many2one('bds.url')
    url_ids = fields.Many2many('bds.url')
    last_fetched_url_id = fields.Many2one('bds.url')#>0
    max_page = fields.Integer()
    is_current_page_2 = fields.Boolean()
    des = fields.Char()

    def name_get(self):
        result = []
        for r in self:
            result.append((r.id, "id:%s-%s"%(r.id, r.name)))
        return result
        
    @api.depends('url_ids','des')
    def _compute_name(self):
        for r in self:
            if r.url_ids:
                descriptions = ','.join(r.url_ids.mapped('name'))
                des = r.des
                if des:
                    name = '%s-%s'%(des, descriptions)
                else:
                    name = descriptions
                r.name = name

    @api.multi
    def set_0(self):
        self.url_ids.write({'current_page':0, 'create_link_number':0})
   
   # làm gọn lại ngày 23/02
    def fetch (self):
        url_ids = self.url_ids.ids
        if not self.last_fetched_url_id.id:
            new_index = 0
        else:
            try:
                index_of_last_fetched_url_id = url_ids.index(self.last_fetched_url_id.id)
                new_index =  index_of_last_fetched_url_id + 1
            except ValueError:
                new_index = 0
            if new_index == len(url_ids):
                new_index = 0
        url_id = self.url_ids[new_index]
        try:
            self.fetch_a_url_id (url_id)
        except Exception as e:
            self.env['bds.error'].create({'name':str(e),'des':'type of error:%s'%type(e)})

    def fetch_all_url(self):
        url_ids = self.url_ids
        for url_id in url_ids:
            self.fetch_a_url_id (url_id)
        
    

    

            


        


        
