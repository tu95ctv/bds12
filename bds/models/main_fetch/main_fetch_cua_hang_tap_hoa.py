# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons.bds.models.bds_tools  import  request_html
import json
import math
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

class TapHoaMainFetch(models.AbstractModel):
    _inherit = 'abstract.main.fetch'


    def get_main_obj(self):
        rs = super().get_main_obj()
        if self.site_name =='cuahangtaphoa' or self.model_name=='tap.hoa':
            return self.env['tap.hoa']
        return rs


    def get_last_page_number(self, url_id):
        if self.site_name =='cuahangtaphoa':
            if url_id.web_last_page_number:
                return url_id.web_last_page_number
            return 300
        return super().get_last_page_number(url_id)

    def get_dia_chi(self, topic_soups, dia_chi_str= 'Địa chỉ:'):
        try:
            ngay_cap_soup = topic_soups.select("li:contains('%s')"%dia_chi_str)[0]
            ngay_cap = ngay_cap_soup.get_text().split(':')[1].strip()
        except IndexError:
            ngay_cap = None
        return ngay_cap

    def parse_html_topic (self, topic_html_or_json, url_id):
        
        if self.site_name =='cuahangtaphoa' or self.model_name=='tap.hoa':
            topic_dict = {}
            a_page_html_soup = BeautifulSoup(topic_html_or_json, 'html.parser')
            topic_soups = a_page_html_soup.select('div.item-page')[0]
            try:
                nghanh_nghe_soup = topic_soups.select("li:contains('Ngành nghề chính: ')")[0]
                nghanh_nghe = nghanh_nghe_soup.get_text().split(':')[1]
                nghanh_nghe = nghanh_nghe.replace('./.','').strip()
            except IndexError:
                nghanh_nghe = False
            
            topic_dict['nganh_nghe_kinh_doanh'] = nghanh_nghe

            return topic_dict
        return super().parse_html_topic(topic_html_or_json, url_id)


    # def create_page_link(self, format_page_url, page_int):
    #     page_url = super().create_page_link(format_page_url, page_int)
        
    #     if self.site_name == 'cuahangtaphoa':
    #         repl = 'page-%s-danh-sach'%page_int
    #         page_url =  re.sub('danh-sach', repl, format_page_url)
    #         # page_url = re.sub('/$','.aspx',page_url)
    #     return page_url

    #page-6-cua-hang-tap-hoa.html
    def create_page_link(self, format_page_url, page_int):
        page_url = super().create_page_link(format_page_url, page_int)
        if self.site_name == 'cuahangtaphoa':
            repl = 'page-%s'%page_int
            page_url =  re.sub('page-\d+', repl, format_page_url)
            # page_url = re.sub('/$','.aspx',page_url)
        return page_url




    def request_parse_html_topic(self, link, url_id):
        topic_dict = super().request_parse_html_topic(link, url_id)
        if self.site_name =='cuahangtaphoa' or self.model_name =='tap.hoa':
            topic_dict['is_full_topic'] = True
        return topic_dict


    def get_st_is_pre_topic_dict_from_page_dict_and_url_id(self, fetch_item_id):
        if self.site_name =='cuahangtaphoa' or self.model_name =='tap.hoa':
            return False
        return super().get_st_is_pre_topic_dict_from_page_dict_and_url_id(fetch_item_id)


    def get_st_is_compare_price_or_public_date(self, fetch_item_id):

        if self.site_name =='cuahangtaphoa' or self.model_name =='tap.hoa':
            return False
        return super().get_st_is_compare_price_or_public_date(fetch_item_id)

    
    # def get_st_is_bds_type(self, fetch_item_id):

    #     if self.site_name =='cuahangtaphoa' or self.model_name =='tap.hoa':
    #         return False
    #     return super().get_st_is_bds_type(fetch_item_id)

    def ph_parse_pre_topic(self,html_page):
        topic_data_from_pages_of_a_page = super().ph_parse_pre_topic(html_page)
        if self.site_name == 'cuahangtaphoa':
            a_page_html_soup = BeautifulSoup(html_page, 'html.parser')
            title_and_icons = a_page_html_soup.select('div.news-v3')
            if not title_and_icons:
                raise UserError('Không có topic nào từ page của muaban')
            for title_and_icon in title_and_icons:
                topic_data_from_page = {}
                try:
                    
                    chu_so_huu_soup = title_and_icon.select('a')[0]
                    chu_so_huu = chu_so_huu_soup.get_text()
                    topic_data_from_page['name_of_poster'] = chu_so_huu

                    mst_tag = title_and_icon.select('a')[1]
                    href = mst_tag['href']
                    title = mst_tag['title']
                    mst = mst_tag.get_text()

                    phone = re.search(' (\d{7,})$', title)
                    if phone:
                        phone = phone.group(1)
                        topic_data_from_page['poster_id'] = phone
                    else:
                        phone = False
                    
                except IndexError:
                    href = 'n/a'
                    title = False

                dia_chi_soup = title_and_icon.select("p:contains('Địa chỉ:')")[0]
                dia_chi = dia_chi_soup.get_text()
                dia_chis = dia_chi.split(',')  
                tinh = dia_chis[-1]
                quan = dia_chis[-2]
                try:
                    phuong = dia_chis[-3]
                except:
                    phuong = False

                try:
                    duong = dia_chis[-4]
                    duong = duong.replace('Địa chỉ: ')
                except:
                    duong = False

                ngay_thanh_lap_soup = title_and_icon.select("p:contains('Ngày thành lập: ')")[0]
                ngay_thanh_lap = ngay_thanh_lap_soup.get_text()
                ngay_thanh_lap_search = re.search('Ngày thành lập: ([\d/]+) \(', ngay_thanh_lap)
                if ngay_thanh_lap_search:
                    ngay_thanh_lap = ngay_thanh_lap_search.group(1)
                    format_str = '%d/%m/%Y' # The format
                    public_date = datetime.datetime.strptime(ngay_thanh_lap, format_str).date()
                    
                else:
                    ngay_thanh_lap = False
                    public_date = False
                topic_data_from_page['public_date'] = public_date
                topic_data_from_page['ngay_thanh_lap'] = ngay_thanh_lap
                topic_data_from_page['tinh']=tinh
                topic_data_from_page['quan']=quan
                topic_data_from_page['phuong']=phuong
                topic_data_from_page['duong']=duong
                topic_data_from_page['link'] = href
                topic_data_from_page['list_id'] = href
                topic_data_from_page['mst'] = mst
                topic_data_from_page['address'] = dia_chi
                topic_data_from_page['title'] = title
                topic_data_from_page['html'] = ''
                topic_data_from_pages_of_a_page.append(topic_data_from_page)
        return topic_data_from_pages_of_a_page

