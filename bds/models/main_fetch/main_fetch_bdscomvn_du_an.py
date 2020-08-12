# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons.bds.models.bds_tools  import  request_html, SaveAndRaiseException
import json
import math
from odoo.addons.bds.models.fetch_site.fetch_bdscomvn  import get_last_page_from_bdsvn_website, convert_gia_from_string_to_float
from odoo.addons.bds.models.fetch_site.fetch_muaban_obj  import MuabanObject
from odoo.addons.bds.models.fetch_site.fetch_chotot_obj  import create_cho_tot_page_link, convert_chotot_price, convert_chotot_date_to_datetime
from odoo.addons.bds.models.fetch_site.fetch_bdscomvn  import get_bds_dict_in_topic, g_or_create_quan_include_state

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

header = {
                'Host': 'batdongsan.com.vn',
                #'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0',
                'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                # 'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://batdongsan.com.vn/ban-nha-dat-tp-hcm/p4',
                'Connection': 'keep-alive',
                'Cookie': 'SERVERNAME=L_22006251500; _gcl_au=1.1.271490124.1593699646; __cfduid=d962388d50425a164b6fa007bb18400a11593699656; _ga=GA1.3.2004129680.1593699653; usidtb=el2cCH0hYkeyFsUCXtus4pJnBJX0iIA5; __auc=fc627e9a1730fe6dc02b1aad644; ins-storage-version=75; c_u_id=104601; uitb=%7B%22name%22%3A%22Nguyen%20Duc%20Tu%22%2C%22email%22%3A%22nguyenductu%40gmail.com%22%2C%22mobile%22%3A%220916022787%22%2C%22time%22%3A1593701739318%7D; NPS_b514e4e7_last_seen=1593701743389; _fbp=fb.2.1593701744644.54625863; _ym_uid=15937017471040494592; _ym_d=1593701747; __zi=2000.SSZzejyD6jy_Zl2jp1eKttQU_gxC3nMGTChWuC8NLyncmFxoW0L1t2AVkF62JGtQ8fgnzeP5IDidclhqXafDtIkV_FG.1; fpsend=147621; __zlcmid=yzjFnky3OLinOV; SERVERID=H; ASP.NET_SessionId=pmzli2x4f0m2fw0jfdbp2aov; _gid=GA1.3.1740494310.1594452137; psortfilter=1%24all%24VOE%2FWO8MpO1adIX%2BwMGNUA%3D%3D; sidtb=Xs6HBrUnnCvh6iGaEMGmhBx2nCLrUMGh; __asc=b0a63b421733d08f828fd8fa4e2',
                # 'Upgrade-Insecure-Requests': 1
                }

class BDSFetch(models.AbstractModel):
    _inherit = 'abstract.main.fetch'

    def get_last_page_number(self, url_id):
        print ('****self.site_name***', self.site_name)
        if self.site_name == 'batdongsan dự án':
            return 20
            return get_last_page_from_bdsvn_website(url_id)
        return super(BDSFetch, self).get_last_page_number(url_id)
    
    def make_topic_link_from_list_id(self, list_id):
        link = super().make_topic_link_from_list_id(list_id)
        if self.site_name == 'batdongsan dự án':
            link = 'https://batdongsan.com.vn' +  list_id
        
        return link

    def parse_html_topic (self, topic_html_or_json, url_id):
        if self.site_name == 'batdongsan dự án':
            topic_dict = get_bds_dict_in_topic(self, self.page_dict, topic_html_or_json, self.siteleech_id_id)
            return topic_dict
        return super().parse_html_topic(topic_html_or_json, url_id)
        

    # def copy_page_data_to_rq_topic(self, topic_data_from_page):
    #     filtered_page_topic_dict = super(BDSFetch, self).copy_page_data_to_rq_topic(topic_data_from_page)
    #     print ('***topic_data_from_page***', topic_data_from_page)
    #     print (aaa)
    #     if self.site_name == 'batdongsan dự án' :  
    #         filtered_page_topic_dict['thumb'] = topic_data_from_page.get('thumb',False)
    #         filtered_page_topic_dict['vip'] = topic_data_from_page['vip']
    #         filtered_page_topic_dict['quan_id'] = topic_data_from_page['quan_id']
    #     return filtered_page_topic_dict

    def create_page_link(self, format_page_url, page_int):
        page_url = super(BDSFetch, self).create_page_link(format_page_url, page_int)
        if self.site_name == 'batdongsan dự án':
            page_url = format_page_url  + '/p' +str(page_int)
        return page_url

    def page_header_request(self):
        # return None
        
        if self.site_name == 'batdongsan dự án':
            header = {
                'Host': 'batdongsan.com.vn',
                #'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0',
                'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                # 'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://batdongsan.com.vn/ban-nha-dat-tp-hcm/p4',
                'Connection': 'keep-alive',
                'Cookie': '__cfduid=d6a5f615edb1d758de8f6076e15eaa6731596941037; expires=Tue, 08-Sep-20 02:43:57 GMT; path=/; domain=.useinsider.com; HttpOnly; SameSite=Lax',
                #set-cookie: __cfduid=d6a5f615edb1d758de8f6076e15eaa6731596941037; expires=Tue, 08-Sep-20 02:43:57 GMT; path=/; domain=.useinsider.com; HttpOnly; SameSite=Lax

                # 'Upgrade-Insecure-Requests': 1
                }
            return header
        return super().page_header_request()

    def ph_parse_pre_topic(self, html_page):
        topic_data_from_pages_of_a_page = super(BDSFetch, self).ph_parse_pre_topic(html_page)
        if self.site_name == 'batdongsan dự án':
            soup = BeautifulSoup(html_page, 'html.parser')
            projects = soup.select('div.list-view div.listProject')
            if projects:
                page_css_type = 1
                for pr in projects:
                    title_soup = pr.select('h3 a')[0]
                    href = title_soup['href']
                    print ('***href***', href)
            else:
                projects = soup.select('.project-body-left .prj-list > ul.list-view > #listProject > li')
                print ('***projects***', len(projects))
                if projects:
                    for pr in projects:
                        title_soup = pr.select('.detail .bigfont h3 a')[0]
                        href = title_soup['href']
                        print ('***href2***', href)

                

        return topic_data_from_pages_of_a_page

