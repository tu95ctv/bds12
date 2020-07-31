# -*- coding: utf-8 -*-
from odoo import models, fields, api
# from odoo.addons.bds.models.fetch import fetch, fetch_all_url
import re
from odoo import models,fields
from odoo.addons.bds.models.bds_tools  import  FetchError
import math


#lam gon lai ngay 29/07
def div_part(total_page, number_of_part, nth_part):
    # nth_part = 1,2,3
    once = math.ceil(total_page/number_of_part)
    first = once * (nth_part -1 ) + 1
    second = once *  nth_part
    if second > total_page:
        second = total_page
    number_page = second - first + 1
    return (first, second, number_page)

class BDSFetchLine(models.Model):
    _name = 'bds.fetch.item'
    
    name = fields.Char(related='url_id.description', store=True)
    url_id = fields.Many2one('bds.url')
    description = fields.Char(related='url_id.description')
    web_last_page_number = fields.Integer(related='url_id.web_last_page_number')
    fetch_id = fields.Many2one('bds.fetch')
    min_page = fields.Integer()
    set_number_of_page_once_fetch = fields.Integer(default=5)
    current_page = fields.Integer()
    update_link_number = fields.Integer(readonly=1)
    create_link_number = fields.Integer(readonly=1)
    existing_link_number = fields.Integer(readonly=1)
    link_number = fields.Integer(readonly=1)
    interval = fields.Integer(readonly=1)
    set_leech_max_page = fields.Integer()
    is_finished = fields.Boolean()
    model_id = fields.Many2one('ir.model')
    limit = fields.Integer(default=20)
    asc_or_desc = fields.Selection([('asc','asc'),('desc','desc')], default='asc')

#lam gon lai ngay 23/02
class Fetch(models.Model):

    _name = 'bds.fetch'
    _inherit = 'abstract.main.fetch'
    _auto = True

    name = fields.Char(compute='_compute_name', store=True)
    url_id = fields.Many2one('bds.url')
    url_ids = fields.Many2many('bds.url')
    last_fetched_item_id = fields.Many2one('bds.fetch.item')#>0
    max_page = fields.Integer()
    # is_current_page_2 = fields.Boolean()
    des = fields.Char()
    is_next_if_only_finish = fields.Boolean()
    fetch_item_ids = fields.One2many('bds.fetch.item','fetch_id')
    number_of_part = fields.Integer()
    nth_part = fields.Integer()
    batch_number_of_once_fetch = fields.Integer()
    is_cronjob = fields.Boolean()
    is_bo_sung_topic = fields.Boolean()
    def set_batch_number_of_once_fetch(self):
        if self.batch_number_of_once_fetch:
            for item in self.fetch_item_ids:
                item.set_number_of_page_once_fetch = self.batch_number_of_once_fetch

    def batch_div_part(self):
        print ('***batch_div_part***')
        if self.nth_part and self.number_of_part:
            print ('***batch_div_part2***')
            for item in self.fetch_item_ids:
                if item.web_last_page_number:
                    first, second, number_page = div_part(item.web_last_page_number, self.number_of_part, self.nth_part)
                    print ('***first, second**', first, second)
                    item.min_page = first
                    item.set_leech_max_page = second

    def cronjob_1(self):
        print ('cronjob_1')
        fetch_obj = self.search([('is_cronjob','=',True)], limit=1)
        if fetch_obj:
            fetch_obj.fetch()
        else:
            self.env['bds.error'].create({'name':'không có cronjob 1', 'des':'không có cronjob 1'})

    def write_fetch_item(self, obj, vals):
        if 'url_ids' in vals:
            url_in_fetch_item_ids = obj.fetch_item_ids.mapped('url_id')
            for url in obj.url_ids:
                if url not in url_in_fetch_item_ids:
                    self.env['bds.fetch.item'].create({'url_id':url.id, 'fetch_id':obj.id})

            # for fetch_item in obj.fetch_item_ids:
            #     if fetch_item.url_id not in obj.url_ids:
            #         fetch_item.unlink()


    @api.model
    def create(self,vals):
        obj = super().create(vals)
        self.write_fetch_item(obj, vals)
        return obj

    @api.multi
    def write(self, vals):
        rs = super().write(vals)
        self.write_fetch_item(self, vals)
        return rs
      
    def name_get(self):
        result = []
        for r in self:
            result.append((r.id, "id:%s-%s"%(r.id, r.name)))
        return result


    def unlink_url_ids(self):
        self.write({'url_ids':[(5,0,0)]}) 

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
                if name:
                    name = name[:100]
                r.name = name

    @api.multi
    def set_0(self):
        self.url_ids.write({'current_page':0, 'create_link_number':0})
    
    

    
        
    

    

            


        


        
