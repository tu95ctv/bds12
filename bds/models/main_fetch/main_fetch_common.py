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
import logging
_logger = logging.getLogger(__name__)
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
    allow_update = True
   
    def get_main_obj(self):
        return self.env['bds.bds']
        
    
    
    def topic_handle(self, link, url_id, topic_data_from_page={}):
        update_dict = {}
        if self.allow_update:
            public_datetime = topic_data_from_page['public_datetime'] # naitive datetime
            now = datetime.datetime.now()
            gmt7_public_datetime = convert_native_utc_datetime_to_gmt_7(public_datetime)
            public_date  = gmt7_public_datetime.date()
        main_obj = self.get_main_obj()
        
        search_bds_obj= main_obj.search([('link','=',link)])
        is_existing_link_number = 0
        is_update_link_number = 0
        is_create_link_number = 0
        if search_bds_obj:
            if self.allow_update:
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
                    so_lan_gia_update = search_bds_obj.so_lan_gia_update + 1
                    update_dict.update({
                        'so_lan_gia_update':so_lan_gia_update,
                        'ngay_update_gia':datetime.datetime.now(),
                        'diff_gia':diff_gia,
                        'gialines_ids':[(0,False,{'gia':gia, 'gia_cu':gia_cu, 'diff_gia':diff_gia})]
                        })
                if update_dict:
                    search_bds_obj.write(update_dict)
                    is_update_link_number = 1
            is_existing_link_number = 1
        else:
            write_dict = {}
            if self.allow_update:
                write_dict.update({'public_date':public_date, 'public_datetime':public_datetime, 'url_id': url_id.id })

            rq_topic_dict = self.request_topic(link, url_id)# quan trong nhất
            filtered_page_topic_dict = self.copy_page_data_to_rq_topic(topic_data_from_page)
            write_dict.update(rq_topic_dict)
            write_dict.update(filtered_page_topic_dict)
            write_dict['siteleech_id'] = self.siteleech_id_id
            write_dict['link'] = link
            write_dict['cate'] = url_id.cate
            write_dict['sell_or_rent'] = url_id.sell_or_rent
            main_obj.create(write_dict) 
            is_create_link_number = 1
        return is_existing_link_number, is_update_link_number, is_create_link_number

    def write_dict_for_topic_handle(self):
        pass

    def write_dict_for_topic_handle(self):
        pass



    def make_topic_link_from_list_id(self, list_id):
        link = list_id
        return link  

    def page_header_request(self):
        return None

    def page_handle(self, page_int, url_id):
        format_page_url = url_id.url  
        existing_link_number, update_link_number, create_link_number, link_number = 0, 0, 0, 0
        remain_retry_bds = 1
        bds_exception_count = 0
        while remain_retry_bds:
            remain_retry_bds -=1
            try:
                page_url = self.create_page_link(format_page_url, page_int)
                headers = self.page_header_request()
                header_kwargs = {'headers': headers} if headers else {}
                html_page = request_html(page_url,**header_kwargs)
                topic_data_from_pages_of_a_page = self.fetch_topics_info_per_page(html_page)
            except FetchError as e:
                self.env['bds.error'].create({'name':str(e),'des':str(e)})
                return existing_link_number, update_link_number, create_link_number, link_number
            except Exception as e:
                if url_id.siteleech_id.name == 'batdongsan':
                    self.env['bds.error'].create({'name':'lỗi fetch_topics_info_per_page', 'des':traceback.format_exc()})
                    bds_exception_count +=1
                    if bds_exception_count ==3:
                        remain_retry_bds = 0
                        return existing_link_number, update_link_number, create_link_number, link_number
                    else:
                        remain_retry_bds = 1
                else:
                    raise
        
        link_number = len(topic_data_from_pages_of_a_page)
        for topic_data_from_page in topic_data_from_pages_of_a_page:
            list_id = topic_data_from_page['list_id']
            link = self.make_topic_link_from_list_id(list_id)
            try:
                is_existing_link_number, is_update_link_number, is_create_link_number = \
                    self.topic_handle(link, url_id, topic_data_from_page=topic_data_from_page)
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

    def gen_page_number_list(self, fetch_item_id ): 
        url_id = fetch_item_id
        # is_current_page_2 = getattr(self, 'is_current_page_2', False)
        # if is_current_page_2:
        #     current_page_field_name = 'current_page_2'
        #     set_number_of_page_once_fetch_name = 'set_number_of_page_once_fetch2'
        #     set_leech_max_page_name = 'set_leech_max_page2'
        # else:

        current_page_field_name = 'current_page'
        set_number_of_page_once_fetch_name = 'set_number_of_page_once_fetch'
        set_leech_max_page_name = 'set_leech_max_page'

        self.current_page_field_name = current_page_field_name
        current_page = getattr(url_id, current_page_field_name)
        set_number_of_page_once_fetch = getattr(url_id, set_number_of_page_once_fetch_name)
        url_set_leech_max_page = getattr(url_id, set_leech_max_page_name)
        set_leech_max_page = self.max_page or url_set_leech_max_page
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
        if fetch_error == False:
            url_id.web_last_page_number = web_last_page_number
        begin = current_page + 1
        min_page = url_id.min_page or 1
        if begin > max_page:
            begin  = min_page
        end = begin   + set_number_of_page_once_fetch - 1
        if end > max_page:
            end = max_page
        self.max_page_assign_again = max_page
        end_page_number_in_once_fetch = end
        page_lists = range(begin, end+1)
        number_of_pages = end - begin + 1
        return end_page_number_in_once_fetch, page_lists, begin, number_of_pages


    def fetch_bo_sung_da_co_link(self, fetch_item_id):
        print ('****hahahah*** fetch_bo_sung_da_co_link')
        model = fetch_item_id.model_id.name
        objs = self.env[model].search([('is_full_topic','=',False)],limit=fetch_item_id.limit)
        len_objs = len(objs)
        print ('***len_objs***', len_objs)
        for r in objs:
            url_id = False
            rq_topic_dict = self.request_topic(r.link, url_id)# quan trong nhất
            r.write(rq_topic_dict)
            is_existing_link_number, is_update_link_number, is_create_link_number = \
                len_objs, len_objs, 0
        return is_existing_link_number, is_update_link_number, is_create_link_number


    # MỚI THÊM NGÀY 11/04
    def fetch_a_url_id (self, fetch_item_id):
        
        url_id = fetch_item_id.url_id
        self.site_name = url_id.siteleech_id.name
        if self.is_bo_sung_topic:
            existing_link_number, update_link_number, create_link_number = \
                self.fetch_bo_sung_da_co_link(fetch_item_id)
            link_number = create_link_number
            end_page_number_in_once_fetch = False
            is_finished = False
        else:
            self.siteleech_id_id = url_id.siteleech_id.id
            end_page_number_in_once_fetch, page_lists, begin, so_page =  self.gen_page_number_list(fetch_item_id) 
            
            begin_time = datetime.datetime.now()
            existing_link_number, update_link_number, create_link_number, link_number = 0, 0, 0, 0
            for page_int in page_lists:
                existing_link_number_one_page, update_link_number_one_page, create_link_number_one_page, link_number_one_page = \
                    self.page_handle( page_int, url_id)

                existing_link_number += existing_link_number_one_page
                update_link_number += update_link_number_one_page
                create_link_number += create_link_number_one_page
                link_number += link_number_one_page
            self.last_fetched_item_id = fetch_item_id
            interval = (datetime.datetime.now() - begin_time).total_seconds()
            fetch_item_id.interval = interval
            is_finished = False
            if end_page_number_in_once_fetch == self.max_page_assign_again:
                is_finished = True

        fetch_item_id.write({'current_page': end_page_number_in_once_fetch,
                    'create_link_number': create_link_number,
                    'update_link_number': update_link_number,
                    'link_number': link_number,
                    'existing_link_number': existing_link_number,
                    'is_finished':is_finished,
                    })
        return None

    def look_next_fetched_url_id(self):
        fetch_item_ids = self.fetch_item_ids

        if self.is_next_if_only_finish:
            object_url_ids = fetch_item_ids.filtered(lambda r: not r.is_finished)
        else:
            object_url_ids = fetch_item_ids
        if not self.is_bo_sung_topic:
            current_fetched_url_id = self.last_fetched_item_id
            if current_fetched_url_id not in fetch_item_ids:
                current_fetched_url_id = False
            if current_fetched_url_id and self.is_next_if_only_finish:
                if not current_fetched_url_id.is_finished:
                    return current_fetched_url_id
            if not object_url_ids and self.is_next_if_only_finish:
                object_url_ids.write({'is_finished':False})


        # tuần tự
        filtered_object_url_ids_id = object_url_ids.ids
        
        if not self.last_fetched_item_id.id:
            new_index = 0
        else:
            try:
                index_of_last_fetched_url_id = filtered_object_url_ids_id.index(self.last_fetched_item_id.id)
                new_index =  index_of_last_fetched_url_id + 1
            except ValueError:
                new_index = 0
            if new_index == len(filtered_object_url_ids_id):
                new_index = 0
        try:
            url_id = object_url_ids[new_index]
        except:
            raise UserError('Không loop được url')
        return url_id

    # làm gọn lại ngày 23/02
    def fetch (self):
        url_id = self.look_next_fetched_url_id()
        try:
            self.fetch_a_url_id(url_id)
        except FetchError as e:
            self.env['bds.error'].create({'name':str(e),'des':'type of error:%s'%type(e)})


    def fetch_all_url(self):
        url_ids = self.fetch_item_ids
        for url_id in url_ids:
            self.fetch_a_url_id (url_id)



    





