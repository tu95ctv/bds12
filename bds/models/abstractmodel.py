# -*- coding: utf-8 -*-
from odoo import api, models, _
from odoo.addons.bds.models.fetch_site.fetch_chotot  import  create_cho_tot_page_link
from odoo.addons.bds.models.bds_tools  import  request_html
import json
import math
from odoo.addons.bds.models.fetch_site.fetch_bds_com_vn  import get_bds_dict_in_topic, get_last_page_from_bdsvn_website, convert_gia_from_string_to_float
from odoo.addons.bds.models.fetch_site.fetch_chotot  import  create_cho_tot_page_link, convert_chotot_price, convert_chotot_date_to_datetime
# from odoo.addons.bds.models.fetch_site.fetch_muaban  import get_muaban_vals_one_topic
from odoo.addons.bds.models.fetch_site.fetch_muaban_obj  import MuabanObject

from bs4 import BeautifulSoup
import re
import datetime
from copy import deepcopy
from odoo.exceptions import UserError

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



class ChototFetch(models.AbstractModel):
    _name = 'abstract.fetch'
    _inherit = 'abstract.topic.fetch'

    def get_last_page_number(self, url_id):
        if self.site_name =='chotot':
            page_1st_url = create_cho_tot_page_link(url_id.url, 1)
            html = request_html(page_1st_url)
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
    def make_topic_link_from_list_id(self, list_id):
        if  self.site_name =='chotot':
            link  = 'https://gateway.chotot.com/v1/public/ad-listing/' + str(list_id)
        elif self.site_name =='batdongsan':
            link  = 'https://batdongsan.com.vn' +  list_id
        else:
            link = list_id
        return link


    def create_page_link(self, format_page_url, page_int):
        if self.site_name == 'chotot':
            url =  create_cho_tot_page_link(format_page_url, page_int)
            return url


    def fetch_topics_info_for_page_handle(self, page_int, format_page_url):
        topic_data_from_pages_of_a_page = []
        self.page_url = self.create_page_link(format_page_url, page_int)
        self.html_page = request_html(self.page_url)
        if self.site_name == 'chotot':
            json_a_page = json.loads(self.html_page)
            topic_data_from_pages_of_a_page_origin = json_a_page['ads']
            for topic_data_from_page_cho_tot in topic_data_from_pages_of_a_page_origin:
                topic_data_from_page = deepcopy (topic_data_from_page_cho_tot)
                gia, trieu_gia = convert_chotot_price(topic_data_from_page)#topic_data_from_page['price']
                topic_data_from_page ['gia'] = gia
                date = topic_data_from_page['date']
                naitive_dt = convert_chotot_date_to_datetime(date)
                topic_data_from_page ['public_datetime'] = naitive_dt
                topic_data_from_pages_of_a_page.append(topic_data_from_page)
        return topic_data_from_pages_of_a_page

    def request_topic (self, link, url_id):
        if self.site_name =='chotot':
            topic_html_or_json = request_html(link)           
            topic_dict = self.get_topic_chotot(topic_html_or_json,self.siteleech_id_id)
            return topic_dict

    def copy_page_data_to_rq_topic(self, topic_data_from_page):
        copy_topic_dict = {}
        if self.site_name =='chotot':
            copy_topic_dict['thumb'] = topic_data_from_page.get('image',False)
            copy_topic_dict['chotot_moi_gioi_hay_chinh_chu'] = 'moi_gioi' if topic_data_from_page.get('company_ad',False) else 'chinh_chu'
        return copy_topic_dict

class MuabanFetch(models.AbstractModel):
    _inherit = 'abstract.fetch'

    def get_last_page_number(self, url_id):
        if self.site_name =='muaban':
            return 100
        return super(MuabanFetch, self).get_last_page_number(url_id)
        
    def request_topic (self, link, url_id):
        topic_dict = super(MuabanFetch, self).request_topic(link, url_id)
        if self.site_name =='muaban':
            topic_html_or_json = request_html(link)
            topic_dict = MuabanObject(self).get_muaban_vals_one_topic(topic_html_or_json, self.siteleech_id_id)
        return topic_dict
    def copy_page_data_to_rq_topic(self, topic_data_from_page):
        copy_topic_dict = super(MuabanFetch, self).copy_page_data_to_rq_topic(topic_data_from_page)
        if self.site_name =='muaban':
            copy_topic_dict['area'] = topic_data_from_page.get('area',False)
            copy_topic_dict['thumb'] = topic_data_from_page.get('thumb','ahahah')
        return copy_topic_dict

    def create_page_link(self, format_page_url, page_int):
        page_url = super(MuabanFetch, self).create_page_link(format_page_url, page_int)
        if self.site_name == 'muaban':
            page_url =  re.sub('\?cp=(\d*)', '?cp=%s'%page_int, format_page_url)
            
        return page_url

    def fetch_topics_info_for_page_handle(self, page_int, format_page_url):
        topic_data_from_pages_of_a_page = super(MuabanFetch, self).fetch_topics_info_for_page_handle(page_int, format_page_url)
        if self.site_name == 'muaban':
            a_page_html_soup = BeautifulSoup(self.html_page, 'html.parser')
            title_and_icons = a_page_html_soup.select('div.list-item-container')
            if not title_and_icons:
                raise UserError('Không có topic nào từ page của muaban')
            for title_and_icon in title_and_icons:
                topic_data_from_page = {}
                image_soups = title_and_icon.select("a.list-item__link")
                image_soups = image_soups[0]
                href = image_soups['href']
                img = image_soups.select('img')[0]
                src_img = img.get('data-original',False)
                topic_data_from_page['list_id'] = href
                topic_data_from_page['thumb'] = src_img
                area = 0
                try:
                    area = title_and_icon.select('span.list-item__area b')[0].get_text()
                    area = area.split(' ')[0].strip().replace(',','.')
                    area = float(area)
                except IndexError:
                    pass
                topic_data_from_page['area']=area
                
                gia_soup = title_and_icon.select('span.list-item__price')
                if gia_soup:
                    gia = gia_soup[0].get_text()
                    gia = convert_muaban_string_gia_to_float(gia)
                else:
                    gia = 0
                topic_data_from_page['gia'] = gia  
                ngay_soup = title_and_icon.select('span.list-item__date')
                ngay = ngay_soup[0].get_text().strip().replace('\n','')
                public_datetime = datetime.datetime.strptime(ngay,"%d/%m/%Y")
                topic_data_from_page['public_datetime'] = public_datetime  
                topic_data_from_pages_of_a_page.append(topic_data_from_page)
        return topic_data_from_pages_of_a_page




class BDSFetch(models.AbstractModel):
    _inherit = 'abstract.fetch'

    def get_last_page_number(self, url_id):
        if self.site_name =='batdongsan':
            return get_last_page_from_bdsvn_website(url_id.url)
        return super(BDSFetch, self).get_last_page_number(url_id)
    
    def request_topic (self, link, url_id):
        topic_dict = super(BDSFetch, self).request_topic(link, url_id)
        if self.site_name =='batdongsan':
            topic_html_or_json = request_html(link)
            topic_dict = get_muaban_vals_one_topic(self,  topic_html_or_json, self.siteleech_id_id)
        return topic_dict

    def copy_page_data_to_rq_topic(self, topic_data_from_page):
        
        copy_topic_dict = super(BDSFetch, self).copy_page_data_to_rq_topic(topic_data_from_page)
        
        if self.site_name =='batdongsan' :   
            copy_topic_dict['thumb'] = topic_data_from_page.get('thumb',False)
        
        return copy_topic_dict

    def create_page_link(self, format_page_url, page_int):
        page_url = super(BDSFetch, self).create_page_link(format_page_url, page_int)
        if self.site_name == 'batdongsan':
            page_url = format_page_url + '/' + 'p' +str(page_int)
        return page_url

    def fetch_topics_info_for_page_handle(self, page_int, format_page_url):
        topic_data_from_pages_of_a_page = super(BDSFetch, self).fetch_topics_info_for_page_handle(page_int, format_page_url)
        if self.site_name == 'batdongsan':
            soup = BeautifulSoup(self.html_page, 'html.parser')
            title_and_icons = soup.select('div.search-productItem')
            for title_and_icon in title_and_icons:
                topic_data_from_page = {}
                title_soups = title_and_icon.select("div.p-title  a")
                topic_data_from_page['list_id'] = title_soups[0]['href']
                icon_soup = title_and_icon.select('img.product-avatar-img')
                topic_data_from_page['thumb'] = icon_soup[0]['src']
                gia_soup = title_and_icon.select('strong.product-price')
                gia = gia_soup[0].get_text()
                int_gia = convert_gia_from_string_to_float(gia)
                topic_data_from_page['gia'] = int_gia
                date_dang = title_and_icon.select('div.p-main div.p-bottom-crop div.floatright')
                date_dang = date_dang[0].get_text().replace('\n','')
                date_dang = date_dang[-10:]
                public_datetime = datetime.datetime.strptime(date_dang,"%d/%m/%Y")
                topic_data_from_page['public_datetime'] = public_datetime
                topic_data_from_page['thumb'] = icon_soup[0]['src']
                topic_data_from_pages_of_a_page.append(topic_data_from_page)
        return topic_data_from_pages_of_a_page





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
