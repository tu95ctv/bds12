# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons.bds.models.bds_tools  import  request_html
import json
import math
from odoo.addons.bds.models.fetch_site.fetch_chotot_obj  import create_cho_tot_page_link, \
    convert_chotot_price, convert_chotot_date_to_datetime, deal_gia_chotot, write_quan_phuong_raped, get_topic
from odoo.addons.bds.models.bds_tools  import   SaveAndRaiseException
from bs4 import BeautifulSoup
import re
import datetime
from datetime import timedelta
from copy import deepcopy
from odoo.exceptions import UserError
import os
import pytz
from unidecode import unidecode
import json
import math
from odoo.addons.bds.models.bds_tools  import  FetchError
import traceback


class ChototFetchIndepend(object):
    
    def ph_parse_pre_topic(self, html_page):
        topic_data_from_pages_of_a_page = []
        if self.site_name == 'chotot':
            json_a_page = json.loads(html_page)
            topic_data_from_pages_of_a_page_origin = json_a_page['ads']
            for ad in topic_data_from_pages_of_a_page_origin:
                topic_data_from_page = {}
                topic_data_from_page['price_string'] = ad['price_string']
                topic_data_from_page['price'] = ad['price']
                topic_data_from_page['gia'] = ad['price']/1000000000
                topic_data_from_page['date'] = ad['date']
                topic_data_from_page['list_id'] = ad['list_id']
                topic_data_from_page['html'] = ad['body']
                topic_data_from_page['title']= ad['subject']
                topic_data_from_page.update(write_quan_phuong_raped(ad))
                if 'image' in ad:
                    topic_data_from_page['thumb'] = ad['image']
                if 'company_ad' in ad:
                    company_ad = ad['company_ad']
                else:
                    company_ad = False 
                topic_data_from_page['chotot_moi_gioi_hay_chinh_chu'] = \
                'moi_gioi' if company_ad else 'chinh_chu' 
                if 'category_name' in ad:
                    category_name = ad['category_name']
                    topic_data_from_page['loai_nha'] =  category_name
                else:
                    topic_data_from_page['loai_nha'] =  False
                topic_data_from_pages_of_a_page.append(topic_data_from_page)
        return topic_data_from_pages_of_a_page


class ChototMainFetch(models.AbstractModel, ChototFetchIndepend):
    _inherit = 'abstract.main.fetch'

    def create_page_link(self, format_page_url, page_int):
        if self.site_name == 'chotot':
            url =  create_cho_tot_page_link(format_page_url, page_int)
            return url

    def parse_html_topic (self, topic_html_or_json, url_id):
        if self.site_name =='chotot':
            topic_dict = get_topic(self, topic_html_or_json, self.page_dict, self.siteleech_id_id)
            return topic_dict
        return super().parse_html_topic(topic_html_or_json, url_id)


    def make_topic_link_from_list_id(self, list_id):
        link = super().make_topic_link_from_list_id(list_id)
        if  self.site_name =='chotot':
            link  = 'https://gateway.chotot.com/v1/public/ad-listing/' + str(list_id)
        return link


    def get_last_page_number(self, url_id):
        if self.site_name =='chotot':
            page_1st_url = create_cho_tot_page_link(url_id.url, 1)
            html = request_html(page_1st_url)
            html = json.loads(html)
            total = int(html["total"])
            web_last_page_number = int(math.ceil(total/20.0))
            return web_last_page_number



    


    





