# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons.bds.models.bds_tools  import  request_html
import json
import math
from odoo.addons.bds.models.fetch_site.fetch_muaban_obj  import MuabanObject
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


class MuabanFetch(models.AbstractModel):
    _inherit = 'abstract.main.fetch'

    def save_to_disk(self, ct, name_file ):
        path = os.path.dirname(os.path.abspath(__file__))
        f = open(os.path.join(path,'%s.html'%name_file), 'w')
        f.write(ct)
        f.close()

    def get_last_page_number(self, url_id):
        if self.site_name =='muaban':
            return 300
        return super(MuabanFetch, self).get_last_page_number(url_id)
        
    def parse_html_topic (self, topic_html_or_json, url_id):
        if self.site_name =='muaban':
            topic_dict = MuabanObject(self.env).get_topic(topic_html_or_json)
            return topic_dict
        return super(MuabanFetch, self).parse_html_topic(topic_html_or_json, url_id)

    # def copy_page_data_to_rq_topic(self, topic_data_from_page):
    #     filtered_page_topic_dict = super(MuabanFetch, self).copy_page_data_to_rq_topic(topic_data_from_page)
    #     if self.site_name =='muaban':
    #         filtered_page_topic_dict['area'] = topic_data_from_page.get('area',False)
    #         filtered_page_topic_dict['thumb'] = topic_data_from_page.get('thumb',False)
    #     return filtered_page_topic_dict

    def create_page_link(self, format_page_url, page_int):
        page_url = super(MuabanFetch, self).create_page_link(format_page_url, page_int)
        repl = '?cp=%s'%page_int
        if self.site_name == 'muaban':
            if 'cp=' in format_page_url:
                page_url =  re.sub('\?cp=(\d*)', repl, format_page_url)
            else:
                page_url = format_page_url +  '?' + repl

            
        return page_url

    def ph_parse_pre_topic(self, html_page):
        topic_data_from_pages_of_a_page = super(MuabanFetch, self).ph_parse_pre_topic(html_page)
        if self.site_name == 'muaban':
            a_page_html_soup = BeautifulSoup(html_page, 'html.parser')
            title_and_icons = a_page_html_soup.select('div.list-item-container')
            for title_and_icon in title_and_icons:
                # self.save_to_disk(str(title_and_icon),'muaban_item')
                topic_data_from_page = {}
                image_soups = title_and_icon.select("a.list-item__link")
                image_soups = image_soups[0]
                href = image_soups['href']
                img = image_soups.select('img')[0]
                src_img = img.get('data-src',False)
                topic_data_from_page['list_id'] = href
                topic_data_from_page['thumb'] = src_img
                area = 0
                try:
                    area = title_and_icon.select('span.list-item__area b')[0].get_text()
                    area = area.split(' ')[0].strip().replace(',','.')
                    try:
                        area = float(area)
                    except:
                        area = 0
                except IndexError:
                    pass
                topic_data_from_page['area']=area
                
                gia_soup = title_and_icon.select('span.list-item__price')
                if gia_soup:
                    gia = gia_soup[0].get_text()
                    # try:
                    #     gia = convert_muaban_string_gia_to_float(gia)
                    # except:
                    #     gia = 0
                else:
                    gia = False
                
                topic_data_from_page['price_string'] = gia

                # topic_data_from_page['gia'] = gia  
                ngay_soup = title_and_icon.select('span.list-item__date')
                ngay = ngay_soup[0].get_text().strip().replace('\n','')
                public_datetime = datetime.datetime.strptime(ngay,"%d/%m/%Y")
                topic_data_from_page['public_datetime'] = public_datetime  
                topic_data_from_pages_of_a_page.append(topic_data_from_page)
        return topic_data_from_pages_of_a_page

