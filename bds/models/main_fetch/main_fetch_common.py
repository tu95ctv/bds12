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


class CommonMainFetch(models.AbstractModel):
    _name = 'abstract.main.fetch'

   
    def deal_a_topic(self, link, url_id, topic_data_from_page={}):
        # print (u'~~~~~~~~dealtopic_index %s/%s- page_int %s - page_index %s/so_page %s'
        #             %(number_notice_dict['topic_index'],number_notice_dict['length_link_per_curent_page'],
        #             number_notice_dict['page_int'], number_notice_dict['page_index'],number_notice_dict['so_page']))
        update_dict = {}
        public_datetime = topic_data_from_page['public_datetime'] # naitive datetime
        now = datetime.datetime.now()
        
        gmt7_public_datetime = convert_native_utc_datetime_to_gmt_7(public_datetime)
        public_date  = gmt7_public_datetime.date()
        search_bds_obj= self.env['bds.bds'].search([('link','=',link)])

        is_existing_link_number = 0
        is_update_link_number = 0
        is_create_link_number = 0

        if search_bds_obj:
            
            # number_notice_dict["existing_link_number"] = number_notice_dict["existing_link_number"] + 1
            diff_day_public_from_now =  (now - public_datetime).days
            if diff_day_public_from_now==0:
                
                public_datetime_cu  = fields.Datetime.from_string(search_bds_obj.public_datetime)
                diff_public_datetime_in_hours = int((public_datetime - public_datetime_cu + timedelta(hours=1)).seconds/3600)
                if diff_public_datetime_in_hours > 2 :
                    public_date_cu  = fields.Date.from_string(search_bds_obj.public_date)
                    diff_public_date = (public_date - public_date_cu).days
                    so_lan_diff_public_update = search_bds_obj.so_lan_diff_public_update + 1
                    update_dict.update({
                        'public_datetime': public_datetime, 
                        'public_datetime_cu':public_datetime_cu,
                        'diff_public_datetime':diff_public_datetime_in_hours,
                        'public_date':public_date, 
                        'public_date_cu':public_date_cu,
                        'diff_public_date':diff_public_date, 
                        'so_lan_diff_public_update':so_lan_diff_public_update,
                        'publicdate_ids':[(0,False,{
                                    'public_datetime': public_datetime, 
                                    'public_datetime_cu':public_datetime_cu,
                                    'diff_public_datetime':diff_public_datetime_in_hours,
                                    'public_date':public_date, 
                                    'public_date_cu':public_date_cu,
                                    'diff_public_date':diff_public_date, 
                                    }
                                    )]
                        })
            gia=topic_data_from_page['gia']
            gia_cu = search_bds_obj.gia
            diff_gia = gia - gia_cu
            if diff_gia != 0.0:
                so_lan_gia_update = r.so_lan_gia_update + 1
                update_dict.update({
                    'so_lan_gia_update':so_lan_gia_update,
                    'ngay_update_gia':datetime.datetime.now(),
                    'diff_gia':diff_gia,
                    'gialines_ids':[(0,False,{'gia':gia, 'gia_cu':gia_cu, 'diff_gia':diff_gia})]
                    })


            if update_dict:
                # print (u'-----------Update gia topic_index %s/%s- page_int %s - page_index %s/so_page %s'
                #     %(number_notice_dict['topic_index'],number_notice_dict['length_link_per_curent_page'],
                #     number_notice_dict['page_int'], number_notice_dict['page_index'],number_notice_dict['so_page']))
                search_bds_obj.write(update_dict)
                # number_notice_dict['update_link_number'] = number_notice_dict['update_link_number'] + 1
                is_update_link_number = 1
            is_existing_link_number = 1
        else:
            write_dict = {}
            write_dict.update({'public_date':public_date, 'public_datetime':public_datetime, 'url_id': url_id.id })
            # print (u'+++++++++Create topic_index %s/%s- page_int %s - page_index %s/so_page %s'%(number_notice_dict['topic_index'],number_notice_dict['length_link_per_curent_page'],
            #                                                                 number_notice_dict['page_int'], number_notice_dict['page_index'],number_notice_dict['so_page']))
            # lấy dữ liệu 1 topic về từ link
            rq_topic_dict = self.request_topic(link, url_id)# quan trong nhất
            copy_topic_dict = self.copy_page_data_to_rq_topic(topic_data_from_page)
            write_dict.update(rq_topic_dict)
            write_dict.update(copy_topic_dict)
            write_dict['siteleech_id'] = self.siteleech_id_id
            write_dict['link'] = link
            write_dict['cate'] = url_id.cate
            write_dict['sell_or_rent'] = url_id.sell_or_rent
            self.env['bds.bds'].create(write_dict) 
            # number_notice_dict['create_link_number'] = number_notice_dict['create_link_number'] + 1    
            is_create_link_number = 1
        # link_number = number_notice_dict.get("link_number", 0) + 1
        # number_notice_dict["link_number"] = link_number
        return is_existing_link_number, is_update_link_number, is_create_link_number
        

  


    def page_handle(self, page_int, url_id):
        format_page_url = url_id.url  
        existing_link_number, update_link_number, create_link_number, link_number = 0, 0, 0, 0
        remain_retry_bds = 1
        bds_exception_count = 0
        while remain_retry_bds:
            remain_retry_bds -=1
            try:
                topic_data_from_pages_of_a_page = self.fetch_topics_info_in_page_handle(page_int, format_page_url)
            except FetchError as e:
                self.env['bds.error'].create({'name':str(e),'des':str(e)})
                return existing_link_number, update_link_number, create_link_number, link_number
            except Exception as e:
                if url_id.siteleech_id.name == 'batdongsan':
                    self.env['bds.error'].create({'name':'lỗi fetch_topics_info_in_page_handle', 'des':traceback.format_exc()})
                    bds_exception_count +=1
                    if bds_exception_count ==3:
                        remain_retry_bds = 0
                        return existing_link_number, update_link_number, create_link_number, link_number
                    else:
                        remain_retry_bds = 1
                else:
                    raise
        
            

        # number_notice_dict['curent_page'] = page_int 
        # number_notice_dict['length_link_per_curent_page'] = len(topic_data_from_pages_of_a_page)
        # topic_index = 0
        
        link_number = len(topic_data_from_pages_of_a_page)
        for topic_data_from_page in topic_data_from_pages_of_a_page:
            # topic_index +=1
            # number_notice_dict['topic_index'] = topic_index
            list_id = topic_data_from_page['list_id']
            link = self.make_topic_link_from_list_id(list_id)
            try:
                is_existing_link_number, is_update_link_number, is_create_link_number = \
                    self.deal_a_topic(link, url_id, topic_data_from_page=topic_data_from_page)
                existing_link_number += is_existing_link_number
                update_link_number += is_update_link_number
                create_link_number += is_create_link_number
            except FetchError as e:
                self.env['bds.error'].create({'name':str(e),'des':str(e)})
            except Exception as e:
                if url_id.siteleech_id.name == 'batdongsan':
                    self.env['bds.error'].create({'name':str(e),'des':str(e)})
                else:
                    raise
        return existing_link_number, update_link_number, create_link_number, link_number

    

    def gen_page_number_list(self, url_id ): 
        is_current_page_2 = getattr(self, 'is_current_page_2', False)
        if is_current_page_2:
            current_page_field_name = 'current_page_2'
        else:
            current_page_field_name = 'current_page'
        self.current_page_field_name = current_page_field_name
        
        current_page = getattr(url_id, current_page_field_name)
        set_leech_max_page = getattr(self,'max_page',0) or url_id.set_leech_max_page
        
        fetch_error = False
        try:
            web_last_page_number =  self.get_last_page_number(url_id)
        except FetchError as e:
            web_last_page_number = url_id.web_last_page_number or 200
            fetch_error = True

        if set_leech_max_page and  set_leech_max_page < web_last_page_number:
            max_page =  set_leech_max_page
        else:
            max_page = web_last_page_number
        # if url_id.siteleech_id.name !='muaban':
        #     url_id.web_last_page_number = web_last_page_number
        # else:
            # if url_id.web_last_page_number == False:
        if fetch_error == False:
            url_id.web_last_page_number = web_last_page_number
        begin = current_page + 1
        # min_page = url_id.min_page or 1
        min_page = 1
        if begin > max_page:
            begin  = min_page
        end = begin   + url_id.set_number_of_page_once_fetch - 1
        if end > max_page:
            end = max_page
        end_page_number_in_once_fetch = end
        page_lists = range(begin, end+1)
        number_of_pages = end - begin + 1
        return end_page_number_in_once_fetch, page_lists, begin, number_of_pages


    # MỚI THÊM NGÀY 11/04
    def fetch_a_url_id (self, url_id):
        self.site_name = url_id.siteleech_id.name
        self.siteleech_id_id = url_id.siteleech_id.id
        end_page_number_in_once_fetch, page_lists, begin, so_page =  self.gen_page_number_list(url_id) 
        
        begin_time = datetime.datetime.now()
        # number_notice_dict = {
        #     'page_int':0,
        #     'curent_link':u'0/0',
        #     'link_number' : 0,
        #     'update_link_number' : 0,
        #     'create_link_number' : 0,
        #     'existing_link_number' : 0,
        #     'begin_page':begin,
        #     'so_page':so_page,
        #     'page_lists':page_lists,
        #     'length_link_per_curent_page':0,
        #     'topic_index':0,
        #     }
        # page_index = 0
        existing_link_number, update_link_number, create_link_number, link_number = 0, 0, 0, 0
        for page_int in page_lists:
            # page_index +=1
            # number_notice_dict['page_index'] = page_index

            # try:
            existing_link_number_one_page, update_link_number_one_page, create_link_number_one_page, link_number_one_page = \
                self.page_handle( page_int, url_id)

            existing_link_number += existing_link_number_one_page
            update_link_number += update_link_number_one_page
            create_link_number += create_link_number_one_page
            link_number += link_number_one_page
            # except FetchError as e:
            #     self.env['bds.error'].create({'name':str(e),'des':str(e)})

    
        self.last_fetched_url_id = url_id.id
        interval = (datetime.datetime.now() - begin_time).total_seconds()
        url_id.interval = interval
        url_id.write({self.current_page_field_name: end_page_number_in_once_fetch,
                    'create_link_number': create_link_number,
                    'update_link_number': update_link_number,
                    'link_number': link_number,
                    'existing_link_number': existing_link_number,
                    })
        return None


    





