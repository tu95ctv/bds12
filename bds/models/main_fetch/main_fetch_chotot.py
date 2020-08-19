# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons.bds.models.bds_tools  import  FetchError, SaveAndRaiseException, SaveAndPass
import json
import math
import re
from urllib import request
import logging
# from odoo.addons.bds.models.main_fetch.main_fetch_common import FetchError, SaveAndRaiseException, SaveAndPass

_logger = logging.getLogger(__name__)




headers = { 'User-Agent' : 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36' }
def request_html(url, try_again=1, is_decode_utf8 = True, headers=headers):
    _logger.warning('***request_html***' + url)
    count_fail = 0
    def in_try():
        req =request.Request(url, None, headers)
        rp= request.urlopen(req)
        mybytes = rp.read()
        if is_decode_utf8:
            html = mybytes.decode("utf8")
            return html
        else:
            return mybytes
    while 1:
        if not try_again:
            return in_try()
        try:
            html = in_try()
            return html
        except Exception as e:
            print ('loi html')
            count_fail +=1
            sleep(5)
            if count_fail ==5:
                raise FetchError(u'Lỗi get html, url: %s'%url)

def create_cho_tot_page_link(url_input, page_int):
    repl = 'o=%s'%(20*(page_int-1))
    url_input,count = re.subn('o=\d+', repl, url_input)
    if not count:
        url_input += '&'+ repl
    if '&page=' not in url_input: 
        url_input = url_input +  '&page=' +str(page_int)
    else:
        repl = 'page=' +str(page_int)
        url_input = re.sub('page=\d+', repl, url_input)
    return url_input

class MainFetchChotot():
    # _inherit = 'abstract.main.fetch'

    def ph_parse_pre_topic(self, html_page):
        topic_data_from_pages_of_a_page = []
        if self.site_name == 'chotot':
            json_a_page = json.loads(html_page)
            raise SaveAndRaiseException('chotot')
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
                topic_data_from_page['region_name'] = ad['region_name']
                topic_data_from_page['area_name'] = ad['area_name']
                try:
                    topic_data_from_page['ward_name'] = ad['ward_name']
                except:
                    pass
                
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


    def create_page_link(self, format_page_url, page_int):
        if self.site_name == 'chotot':
            url =  create_cho_tot_page_link(format_page_url, page_int)
            return url

    def parse_html_topic (self, topic_html_or_json):
        if self.site_name =='chotot':
            topic_dict = self.get_topic(topic_html_or_json, self.page_dict)
            return topic_dict
        return super().parse_html_topic(topic_html_or_json)

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
    
    def get_topic(self, topic_html_or_json, page_dict):
        update_dict = {}
        
        topic_html_or_json = json.loads(topic_html_or_json) 
        ad = topic_html_or_json['ad']
        ad_params = topic_html_or_json['ad_params']

        update_dict['region_name'] = ad['region_name']
        update_dict['area_name'] = ad['area_name']
        try:
            update_dict['ward_name'] = ad['ward_name']
        except:
            pass
        update_dict['images']= ad.get('images',[])
        update_dict['phone'] = ad['phone']
        update_dict['account_name'] = ad['account_name']
        update_dict['price_string'] = ad['price_string']
        update_dict['price'] = ad['price']

        address = ad_params.get('address',{}).get('value',False)
        if address:
            update_dict['address'] = address
        else:
            pass
        try:
            if not 'html' in page_dict:
                update_dict['html'] = ad['body']
        except KeyError:
            pass
        update_dict['area']= ad.get('size',0)
        if 'title' not in page_dict:
            update_dict['title']= ad['subject']
        return update_dict



    


    





