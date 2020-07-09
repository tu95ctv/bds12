# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons.bds.models.bds_tools  import  request_html
import json
import math
from odoo.addons.bds.models.fetch_site.fetch_bds_com_vn  import get_bds_dict_in_topic, get_last_page_from_bdsvn_website, convert_gia_from_string_to_float
from odoo.addons.bds.models.fetch_site.fetch_muaban_obj  import MuabanObject
from odoo.addons.bds.models.fetch_site.fetch_chotot_obj  import ChototGetTopic, create_cho_tot_page_link, convert_chotot_price, convert_chotot_date_to_datetime
from odoo.addons.bds.models.fetch_site.fetch_bds_com_vn  import get_bds_dict_in_topic

from bs4 import BeautifulSoup
import re
import datetime
from datetime import timedelta
from copy import deepcopy
from odoo.exceptions import UserError
import os
import pytz
from odoo.addons.bds.models.bds_tools  import  request_html
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
        
    def request_topic (self, link, url_id):
        topic_dict = super(MuabanFetch, self).request_topic(link, url_id)
        if self.site_name =='muaban':
            topic_html_or_json = request_html(link)
            # path = os.path.dirname(os.path.abspath(__file__))
            # f = open(os.path.join(path,'muaban.html'), 'w')
            # f.write(topic_html_or_json)
            # f.close()
            topic_dict = MuabanObject(self.env).get_topic(topic_html_or_json, self.siteleech_id_id)
        return topic_dict

    def copy_page_data_to_rq_topic(self, topic_data_from_page):
        copy_topic_dict = super(MuabanFetch, self).copy_page_data_to_rq_topic(topic_data_from_page)
        if self.site_name =='muaban':
            copy_topic_dict['area'] = topic_data_from_page.get('area',False)
            copy_topic_dict['thumb'] = topic_data_from_page.get('thumb',False)
        return copy_topic_dict

    def create_page_link(self, format_page_url, page_int):
        page_url = super(MuabanFetch, self).create_page_link(format_page_url, page_int)
        repl = '?cp=%s'%page_int
        if self.site_name == 'muaban':
            if 'cp=' in format_page_url:
                page_url =  re.sub('\?cp=(\d*)', repl, format_page_url)
            else:
                page_url = format_page_url +  '?' + repl

            
        return page_url

    def fetch_topics_info_in_page_handle(self, page_int, format_page_url):
        topic_data_from_pages_of_a_page = super(MuabanFetch, self).fetch_topics_info_in_page_handle(page_int, format_page_url)
        if self.site_name == 'muaban':
            page_url = self.create_page_link(format_page_url, page_int)
            html_page = request_html(page_url)
            a_page_html_soup = BeautifulSoup(html_page, 'html.parser')
            title_and_icons = a_page_html_soup.select('div.list-item-container')
            if not title_and_icons:
                raise UserError('Không có topic nào từ page của muaban')
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
                    try:
                        gia = convert_muaban_string_gia_to_float(gia)
                    except:
                        gia = 0
                else:
                    gia = 0
                topic_data_from_page['gia'] = gia  
                ngay_soup = title_and_icon.select('span.list-item__date')
                ngay = ngay_soup[0].get_text().strip().replace('\n','')
                public_datetime = datetime.datetime.strptime(ngay,"%d/%m/%Y")
                topic_data_from_page['public_datetime'] = public_datetime  
                topic_data_from_pages_of_a_page.append(topic_data_from_page)
        return topic_data_from_pages_of_a_page

