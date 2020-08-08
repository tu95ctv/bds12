# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons.bds.models.bds_tools  import  request_html
import json
import math
# from odoo.addons.bds.models.fetch_site.fetch_bds_com_vn  import get_or_create_quan_include_state
from odoo.addons.bds.models.fetch_site.fetch_muaban_obj  import MuabanObject
from odoo.addons.bds.models.fetch_site.fetch_chotot_obj  import ChototGetTopic, create_cho_tot_page_link, \
    convert_chotot_price, convert_chotot_date_to_datetime, deal_gia_chotot, create_quan_for_chotot, write_quan_phuong

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

def convert_muaban_string_gia_to_float(str):
    rs = re.search('(\d+) tỷ',str,re.I)
    if rs:
        ty = float(rs.group(1))*1000000000
    else:
        ty = 0
    rs = re.search('(\d+) triệu',str,re.I)
    if rs:
        trieu = float(rs.group(1))*1000000
    else:
        trieu = 0
    
    kq = (ty + trieu)/1000000000.0
    if not kq:
        gia = re.sub(u'\.|đ|\s', '',str)
        gia = float(gia)
        kq = gia/1000000000.0
    return kq

def convert_native_utc_datetime_to_gmt_7(utc_datetime_inputs):
        local = pytz.timezone('Etc/GMT-7')
        utc_tz =pytz.utc
        gio_bat_dau_utc_native = utc_datetime_inputs#fields.Datetime.from_string(self.gio_bat_dau)
        gio_bat_dau_utc = utc_tz.localize(gio_bat_dau_utc_native, is_dst=None)
        gio_bat_dau_vn = gio_bat_dau_utc.astimezone (local)
        return gio_bat_dau_vn



class ChototMainFetch(models.AbstractModel):
    _inherit = 'abstract.main.fetch'


    def create_page_link(self, format_page_url, page_int):
        if self.site_name == 'chotot':
            url =  create_cho_tot_page_link(format_page_url, page_int)
            return url


    def parse_html_topic (self, topic_html_or_json, url_id):
        if self.site_name =='chotot':
            topic_dict = ChototGetTopic(self.env).get_topic(topic_html_or_json, self.page_dict, self.siteleech_id_id)
            return topic_dict
        return super().parse_html_topic(topic_html_or_json, url_id)

    
    # def copy_page_data_to_rq_topic(self, topic_data_from_page):
    #     filtered_page_topic_dict = {}
    #     if self.site_name =='chotot':
    #         filtered_page_topic_dict['thumb'] = topic_data_from_page.get('image',False)
    #         filtered_page_topic_dict['chotot_moi_gioi_hay_chinh_chu'] = \
    #         'moi_gioi' if topic_data_from_page.get('company_ad',False) else 'chinh_chu'
    #         if topic_data_from_page.get('category_name'):
    #             filtered_page_topic_dict['loai_nha'] =  topic_data_from_page.get('category_name')       
    #     return filtered_page_topic_dict


    def make_topic_link_from_list_id(self, list_id):
        link = super().make_topic_link_from_list_id(list_id)
        if  self.site_name =='chotot':
            link  = 'https://gateway.chotot.com/v1/public/ad-listing/' + str(list_id)
        return link



   
    def ph_parse_pre_topic(self, html_page):
        topic_data_from_pages_of_a_page = []
        
        if self.site_name == 'chotot':
            json_a_page = json.loads(html_page)
            topic_data_from_pages_of_a_page_origin = json_a_page['ads']
            for ad in topic_data_from_pages_of_a_page_origin:
                # topic_data_from_page = deepcopy (topic_data_from_page_cho_tot)
                topic_data_from_page = {}
                # gia, trieu_gia = convert_chotot_price(ad)#topic_data_from_page['price']
                # topic_data_from_page ['gia'] = gia

                gia_dict = deal_gia_chotot(ad)
                topic_data_from_page.update(gia_dict)
                date = ad['date']
                # topic_data_from_page['date'] = date
                naitive_dt = convert_chotot_date_to_datetime(date)
                topic_data_from_page ['public_datetime'] = naitive_dt
                topic_data_from_page['list_id'] = ad['list_id']
                topic_data_from_page['html'] = ad['body']
                topic_data_from_page['title']= ad['subject']
                topic_data_from_page.update(write_quan_phuong(self, ad))
                # quan = create_quan_for_chotot(ad)
                # topic_data_from_page['quan_id'] = quan.id

                if 'image' in ad:
                    topic_data_from_page['thumb'] = ad['image']
                    # del topic_data_from_page['image']


                # topic_data_from_page['chotot_moi_gioi_hay_chinh_chu'] = \
                # 'moi_gioi' if topic_data_from_page.get('company_ad',False) else 'chinh_chu'

                if 'company_ad' in ad:
                    company_ad = ad['company_ad']
                    # del topic_data_from_page['company_ad']
                else:
                    company_ad = False 
                topic_data_from_page['chotot_moi_gioi_hay_chinh_chu'] = \
                'moi_gioi' if company_ad else 'chinh_chu' 

                if 'category_name' in ad:
                    category_name = ad['category_name']
                    # del topic_data_from_page['category_name']
                    topic_data_from_page['loai_nha'] =  category_name
                else:
                    topic_data_from_page['loai_nha'] =  False
                
                # del topic_data_from_page['category_name']

                # if topic_data_from_page.get('category_name'):
                #     filtered_page_topic_dict['loai_nha'] =  topic_data_from_page.get('category_name') 

                topic_data_from_pages_of_a_page.append(topic_data_from_page)
            # raise SaveAndRaiseException('cho_tot')
        return topic_data_from_pages_of_a_page

    def get_last_page_number(self, url_id):
        if self.site_name =='chotot':
            page_1st_url = create_cho_tot_page_link(url_id.url, 1)
            html = request_html(page_1st_url)
            html = json.loads(html)
            total = int(html["total"])
            web_last_page_number = int(math.ceil(total/20.0))
            return web_last_page_number



    


    





