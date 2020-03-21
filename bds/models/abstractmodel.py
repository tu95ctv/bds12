# -*- coding: utf-8 -*-
from odoo import api, models, _
from odoo.addons.bds.models.fetch_site.fetch_chotot  import  create_cho_tot_page_link
from odoo.addons.bds.models.bds_tools  import  request_html
import json
import math


class AFetch(models.AbstractModel):
    _name = 'abstract.fetch'

    def get_last_page_number(self, url_id):
        page_1_url = create_cho_tot_page_link(url_id.url, 1)
        html = request_html(page_1_url)
        html = json.loads(html)
        total = int(html["total"])
        web_last_page_number = int(math.ceil(total/20.0))
        return web_last_page_number

        
    def gen_page_number_list(self, url_id ): 
        current_page = url_id.current_page
        web_last_page_number =  self.get_last_page_number(url_id)
        if url_id.set_leech_max_page and  url_id.set_leech_max_page < web_last_page_number:
            max_page =  url_id.set_leech_max_page
        else:
            max_page = web_last_page_number
        url_id.web_last_page_number = web_last_page_number
        begin = current_page + 1
        if begin > max_page:
            begin  = 1
        end = begin   + url_id.set_number_of_page_once_fetch - 1
        if end > max_page:
            end = max_page
        end_page_number_in_once_fetch = end
        page_lists = range(begin, end+1)
        number_of_pages = end - begin + 1
        return end_page_number_in_once_fetch, page_lists, begin, number_of_pages


class MuabanFetch(models.AbstractModel):
    _inherit = 'abstract.fetch'

    def get_last_page_number(self, url_id):
        if self.site_name =='muaban':
            return 100
        return super(MuabanFetch, self).get_last_page_number(url_id)


class BDSFetch(models.AbstractModel):
    _inherit = 'abstract.fetch'

    def get_last_page_number(self, url_id):
        if self.site_name =='batdongsan':
            return get_last_page_from_bdsvn_website(url_id.url)
        return super(BDSFetch, self).get_last_page_number(url_id)
       

# class Fetch(models.AbstracModeltModel):
#     _name = 'abstract.fetch'

#     def get_last_page_number_ct(self, url_id):
#         page_1_url = create_cho_tot_page_link(url_id.url, 1)
#         html = request_html(page_1_url)
#         html = json.loads(html)
#         total = int(html["total"])
#         web_last_page_number = int(math.ceil(total/20.0))
#         return web_last_page_number

    # def get_last_page_number_bds(self, url_id):
    #     return  get_last_page_from_bdsvn_website(url_id.url)
    # def get_last_page_number_mb(self, url_id):
    #     return 100
