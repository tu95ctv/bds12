# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons.bds.models.bds_tools  import  request_html
import json
import math
from odoo.addons.bds.models.bds_tools  import   save_to_disk, file_from_tuong_doi, g_or_c_ss
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
from odoo.addons.bds.models.bds_tools  import  FetchError, SaveAndRaiseException
import traceback
from time import sleep
import logging
from odoo.addons.bds.models.fetch_site.fetch_bdscomvn  import get_or_create_quan_include_state
from dateutil.relativedelta import relativedelta
_logger = logging.getLogger(__name__)

def convert_native_utc_datetime_to_gmt_7(utc_datetime_inputs):
        local = pytz.timezone('Etc/GMT-7')
        utc_tz =pytz.utc
        gio_bat_dau_utc_native = utc_datetime_inputs#fields.Datetime.from_string(self.gio_bat_dau)
        gio_bat_dau_utc = utc_tz.localize(gio_bat_dau_utc_native, is_dst=None)
        gio_bat_dau_vn = gio_bat_dau_utc.astimezone (local)
        return gio_bat_dau_vn

ty_trieu_nghin_look = {'tỷ':1000000000, 'triệu':1000000, 'nghìn':1000, 'đ':1}     
def convert_gia_from_string_to_float(gia):# 3.5 triệu/tháng
    gia_ty, trieu_gia, price, thang_m2_hay_m2 = False, False, False, False
    gia = gia.strip()
    if not gia:
        return gia_ty, trieu_gia, price, thang_m2_hay_m2

    if re.search('thỏa thuận', gia, re.I):
        return gia_ty, trieu_gia, price, thang_m2_hay_m2

    try:
        rs = re.search('([\d\,\.]*) (\w+)(?:$|/)(.*$)', gia)
        gia_char = rs.group(1).strip()
        if not gia_char:
            return gia_ty, trieu_gia, price, thang_m2_hay_m2
        gia_char = gia_char.replace(',','.')
        ty_trieu_nghin = rs.group(2)
        thang_m2_hay_m2 = rs.group(3)
        if ty_trieu_nghin == 'đ':
            gia_char = gia_char.replace('.','')
        gia_float = float(gia_char)
        he_so = ty_trieu_nghin_look[ty_trieu_nghin]
        price = gia_float* he_so
        gia_ty = price/1000000000
        trieu_gia = price/1000000

    except:
        print ('exception gia', gia)
        raise
        
    return gia_ty, trieu_gia, price, thang_m2_hay_m2

MAP_CHOTOT_DATE_TYPE_WITH_TIMEDELTA = {
        u'ngày':'days',
        u'tuần':'weeks',
        u'hôm qua':'days',
        u'giờ':'hours',
        u'phút':'minutes',
        u'giây':'seconds',
        u'năm':'years',
        u'tháng':'months'
        }
        
def convert_chotot_date_to_datetime(string):
    rs = re.search (r'(\d*?)\s?(ngày|tuần|hôm qua|giờ|phút|giây|năm|tháng)',string,re.I)
    rs1 =rs.group(1)
    rs2 =rs.group(2)
    if rs1=='':
        rs1 =1
    rs1 = int (rs1)
    rs2 = MAP_CHOTOT_DATE_TYPE_WITH_TIMEDELTA[rs2]
    dt = datetime.datetime.now() - relativedelta(**{rs2:rs1})
    return dt

class CommonMainFetch(models.AbstractModel):
    _name = 'abstract.main.fetch'
    allow_update = True
   
    def get_main_obj(self):
        return self.env['bds.bds']
    
    def get_public_date(self, topic_data_from_page):
        public_datetime = topic_data_from_page['public_datetime'] # naitive datetime
        gmt7_public_datetime = convert_native_utc_datetime_to_gmt_7(public_datetime)
        public_date  = gmt7_public_datetime.date()
        return public_datetime, public_date


    def th_topic_update_compare_price(self, search_bds_obj, topic_data_from_page):

        public_datetime, public_date = self.get_public_date(topic_data_from_page)
        update_dict = {}
        now = datetime.datetime.now()
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
        return update_dict


    def th_bds_create_dict_from_page_dict_and_url_id(self, topic_data_from_page, url_id, link, is_topic_link_or_topic_path):
        create_dict = {}
        if not is_topic_link_or_topic_path:
            public_datetime, public_date = self.get_public_date(topic_data_from_page)
            create_dict.update({'public_date':public_date, 'public_datetime':public_datetime, 'url_id': url_id.id })
        create_dict['siteleech_id'] = self.siteleech_id_id
        create_dict['cate'] = url_id.cate
        create_dict['sell_or_rent'] = url_id.sell_or_rent
        create_dict['link'] = link
        
        return create_dict

    def request_write(self, fetch_item_id, link, url_id ):
        return {}

    def parse_html_topic (self, topic_html_or_json, url_id):
        return {}
    
    def request_parse_html_topic_tho(self, link, url_id):
        if not getattr(self,'topic_path',None):
            headers = self.page_header_request()
            header_kwargs = {'headers': headers} if headers else {}
            topic_html_or_json = request_html(link, **header_kwargs)
        else:
            topic_html_or_json = file_from_tuong_doi(self.topic_path)
        try:
            topic_dict = self.parse_html_topic(topic_html_or_json, url_id)
        except SaveAndRaiseException as e:
            save_to_disk(topic_html_or_json, 'file_topic_bug_theo_y_muon_%s'%str(e))
            raise
        except:
            save_to_disk(topic_html_or_json, 'file_topic_bug')
            raise
        return topic_dict

    def get_or_create_quan_include_state(self, tinh_str, quan_str):
        tinh_str = re.sub('tp|Thành phố|tỉnh','', tinh_str, flags=re.I)
        tinh_str = tinh_str.strip()
        country_obj = self.env['res.country'].search([('name','ilike','viet')])[0]
        state = g_or_c_ss(self.env['res.country.state'], {'name':tinh_str, 'country_id':country_obj.id},
                            {'code':tinh_str}, False)
        if quan_str:
            quan = g_or_c_ss(self.env['res.country.district'], {'name':quan_str, 'state_id':state.id},
                                {}, False)
        else:
            quan = False
        return state, quan
   
    def write_quan_phuong(self, topic_dict):
        update_dict = {}
        tinh = topic_dict['region_name']
        if 'area_name' in topic_dict:
            quan_name = topic_dict['area_name']
        else:
            quan_name = False
        state, quan = self.get_or_create_quan_include_state(tinh, quan_name)
        if quan:
            quan_id = quan.id
        else:
            quan_id = False
        if quan_id:
            update_dict['quan_id'] = quan_id
        try:
            ward =  topic_dict['ward_name']
            phuong_id = g_or_c_ss(self.env['bds.phuong'], {'name_phuong':ward, 'quan_id':quan_id}, {})
            update_dict['phuong_id'] = phuong_id.id
        except:
            pass
        return update_dict

    def write_images(self, topic_dict):
        def create_or_get_one_in_m2m_value( url):
            url = url.strip()
            if url:
                return g_or_c_ss(self.env['bds.images'],{'url':url})
        update_dict = {}
        images_urls = topic_dict.get('images',[])
        if images_urls:
            object_m2m_list = list(map(create_or_get_one_in_m2m_value, images_urls))
            m2m_ids = list(map(lambda x:x.id, object_m2m_list))
            if m2m_ids:
                val = [(6, False, m2m_ids)]
                update_dict['images_ids'] = val
        return update_dict   

    def write_poster(self, topic_dict, siteleech_id_id):
        search_dict = {}
        phone = topic_dict['phone']
        search_dict['phone'] = phone 
        account_name = topic_dict['account_name']
        search_dict['login'] = str(phone)+'@gmail.com'
        poster =  self.env['bds.poster'].search([('phone','=', phone)])
        if poster:
            posternamelines_search_dict = {'username_in_site':account_name, 'site_id':siteleech_id_id, 'poster_id':poster.id}
            g_or_c_ss(self.env['bds.posternamelines'], posternamelines_search_dict)
                                                
        else:
            search_dict.update({'created_by_site_id': siteleech_id_id})
            poster =  self.env['bds.poster'].create(search_dict)
            self.env['bds.posternamelines'].create( {'username_in_site':account_name, 'site_id':siteleech_id_id, 'poster_id':poster.id})
        return {'poster_id':poster.id}


    def write_gia(self, topic_dict):
        gia_dict = {}
        price_string = topic_dict.get('price_string',False)
        if price_string:
            gia_ty, trieu_gia, price, price_unit = convert_gia_from_string_to_float(price_string)
        else:
            gia_ty, trieu_gia, price, price_unit= False,False,False,False
        
        gia_dict['price_unit'] = price_unit # tháng/m2
        price = topic_dict.get('price', price)
        
        if price:
            gia_ty, gia_trieu = price/1000000000, price/1000000
        else:
            gia_ty, gia_trieu = False, False
        gia_dict['gia'] = gia_ty
        gia_dict['gia_trieu'] = gia_trieu
        gia_dict['price'] = price
        return gia_dict

    def write_public_datetime(self, topic_dict):
        update = {}
        if 'date' in topic_dict and 'public_datetime' not in topic_dict:
            date = topic_dict['date']
            update ['public_datetime'] = convert_chotot_date_to_datetime(date)
        return update

    def odoo_model_topic_dict(self, topic_dict):
        topic_dict.update(self.write_quan_phuong(topic_dict))
        topic_dict.update(self.write_images(topic_dict))
        topic_dict.update(self.write_poster(topic_dict, self.siteleech_id_id))
        topic_dict.update(self.write_gia(topic_dict))
        topic_dict.update(self.write_public_datetime(topic_dict))


    def request_parse_html_topic(self, link, url_id):
        topic_dict = self.request_parse_html_topic_tho(link, url_id)
        if self.st_is_compare_price_or_public_date:
            self.odoo_model_topic_dict(topic_dict)
        return topic_dict


    def del_list_id_topic_data_from_page(self, topic_data_from_page):
        if 'list_id' in topic_data_from_page:
            del topic_data_from_page['list_id']


    def topic_handle(self, link, url_id, topic_data_from_page, fetch_item_id,  search_bds_obj=None):
        if self.st_is_compare_price_or_public_date:
            topic_data_from_page.update(self.write_public_datetime(topic_data_from_page))
            topic_data_from_page.update(self.write_gia(topic_data_from_page))
        print ('topic: %s'%self.topic_count)
        self.link = link
        self.page_dict = topic_data_from_page
        main_obj = self.get_main_obj()
        search_bds_obj= main_obj.search([('link','=',link)])
        is_fail_link_number = 0
        is_existing_link_number = 0
        is_update_link_number = 0
        is_create_link_number = 0
        try:
            if search_bds_obj:
                is_must_update_combine = fetch_item_id.topic_link or fetch_item_id.topic_path or fetch_item_id.is_must_update_topic
                if not is_must_update_combine:# update ở mode bình thường
                    update_dict = {}

                    if self.st_is_compare_price_or_public_date:
                        compare_update_dict = self.th_topic_update_compare_price(search_bds_obj, topic_data_from_page)
                        update_dict.update(compare_update_dict)

                    if fetch_item_id.model_id:
                        request_write_dict = self.request_parse_html_topic(link, url_id)
                        request_write_dict['is_full_topic'] =  True
                        update_dict.update(request_write_dict)

                    if fetch_item_id.page_path:
                        update_dict = self.request_parse_html_topic(link, url_id)
                    
                else:#topic_link, topic_path
                    self.del_list_id_topic_data_from_page(topic_data_from_page)
                    update_dict = self.request_parse_html_topic(link, url_id)

                if update_dict:
                        search_bds_obj.write(update_dict)
                        is_update_link_number = 1

                is_existing_link_number = 1
            else:
                create_dict = {}
                is_topic_link_or_topic_path = bool(fetch_item_id.topic_link or fetch_item_id.topic_path)
                
                if self.st_is_pre_topic_dict_from_page_dict_and_url_id:
                    pre_create_dict = self.th_bds_create_dict_from_page_dict_and_url_id(topic_data_from_page, url_id, link, is_topic_link_or_topic_path)
                    create_dict.update(pre_create_dict)
               
                if not fetch_item_id.not_request_topic:
                    rq_topic_dict = self.request_parse_html_topic(link, url_id)
                    create_dict.update(rq_topic_dict)
                else:
                    if self.st_is_compare_price_or_public_date:
                        self.odoo_model_topic_dict(topic_data_from_page)

                if not is_topic_link_or_topic_path:
                    self.del_list_id_topic_data_from_page(topic_data_from_page)
                    create_dict.update(topic_data_from_page)
                
                main_obj.create(create_dict) 
                self.env.cr.commit()
                
                is_create_link_number = 1
                self.env['bds.error'].create({
                'name':'success link',
                'des':'success link',
                'link':link,
                'type':'success',
                'link_type':'topic',
                'fetch_item_id':fetch_item_id.id,
                'error_or_success':'success',
                    }
                )

        except FetchError as e:
            is_fail_link_number = 1
            self.env['bds.error'].create({
                'name':str(e),
                'des':str(e),
                'link':link,
                'type':'fetch_error',
                'link_type':'topic',
                'fetch_item_id':fetch_item_id.id,
                }
            )

           
        except:
            raise
            is_fail_link_number = 1
            self.env['bds.error'].create({
                'name':'internal_error',
                'des':str(traceback.format_exc()),
                'link':link,
                'type':'internal_error',
                'link_type':'topic',
                'fetch_item_id':fetch_item_id.id,
                }
                )
        return is_existing_link_number, is_update_link_number, is_create_link_number, is_fail_link_number

        


    def make_topic_link_from_list_id(self, list_id):
        link = list_id
        return link  

    def page_header_request(self):
        return None

    def page_handle(self, page_int, url_id, fetch_item_id):
        format_page_url = url_id.url  
        existing_link_number, update_link_number, create_link_number, fail_link_number = 0, 0, 0, 0
        try:
            if not fetch_item_id.page_path:
                page_url = self.create_page_link(format_page_url, page_int)
                headers = self.page_header_request()
                header_kwargs = {'headers': headers} if headers else {}
                html_page = request_html(page_url,**header_kwargs)
            else:
                html_page = file_from_tuong_doi(fetch_item_id.page_path)
            try:
                topic_data_from_pages_of_a_page = self.ph_parse_pre_topic(html_page)

            except SaveAndRaiseException as e:
                save_to_disk(html_page, 'file_topic_bug_theo_y_muon_%s'%str(e))
                raise
                # raise 
            except:
                file_name = 'file_page_bug' if not fetch_item_id.page_path else 'file_page_bug_page_path'
                save_to_disk(html_page, file_name)
                raise
        except FetchError as e:
            self.env['bds.error'].create({
                'name':str(e),
                'des':str(e),
                'link':page_url,
                'type':'fetch_error',
                'link_type':'page',
                'fetch_item_id':fetch_item_id.id,
                }
            )
            return existing_link_number, update_link_number, create_link_number, fail_link_number, link_number
        except Exception as e:
            raise
        if not topic_data_from_pages_of_a_page:
            file_name = 'file_page_bug' if not fetch_item_id.page_path else 'file_page_bug_page_path'
            save_to_disk(html_page, file_name)
            raise ValueError('topic_data_from_pages_of_a_page is empty')
         
        for topic_count, topic_data_from_page in enumerate(topic_data_from_pages_of_a_page):
            self.topic_count = topic_count
            list_id = topic_data_from_page['list_id']

            link = self.make_topic_link_from_list_id(list_id)
            # if self.topic_count == 5:
            #     self.env.cr.rollback()
                # return is_existing_link_number, is_update_link_number, is_create_link_number, is_fail_link_number


            is_existing_link_number, is_update_link_number, is_create_link_number, is_fail_link_number = \
                self.topic_handle(link, url_id, topic_data_from_page, 
                        fetch_item_id)
            existing_link_number += is_existing_link_number
            update_link_number += is_update_link_number
            create_link_number += is_create_link_number
            fail_link_number +=is_fail_link_number
        link_number = len(topic_data_from_pages_of_a_page)
        return existing_link_number, update_link_number, create_link_number, fail_link_number, link_number

    def gen_page_number_list(self, fetch_item_id ): 
        url_id = fetch_item_id
        # current_page_field_name = 'current_page'
        set_number_of_page_once_fetch_name = 'set_number_of_page_once_fetch'
        set_leech_max_page_name = 'set_leech_max_page'
        # self.current_page_field_name = current_page_field_name
        current_page = fetch_item_id.current_page
        set_number_of_page_once_fetch = getattr(url_id, set_number_of_page_once_fetch_name)
        url_set_leech_max_page = getattr(url_id, set_leech_max_page_name)
        set_leech_max_page = self.max_page or url_set_leech_max_page
        fetch_error = False
        try:
            web_last_page_number =  self.get_last_page_number(fetch_item_id.url_id)
        except FetchError as e:
            web_last_page_number = fetch_item_id.url_id.web_last_page_number or 200
            fetch_error = True

        if set_leech_max_page and  set_leech_max_page < web_last_page_number:
            max_page =  set_leech_max_page
        else:
            max_page = web_last_page_number
        if fetch_error == False:
            fetch_item_id.url_id.web_last_page_number = web_last_page_number
        begin = current_page + 1
        min_page = url_id.min_page or 1
        if begin < min_page:
            begin = min_page
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
        model = fetch_item_id.model_id.name
        objs = self.env[model].search([('is_full_topic','=',False)], limit=fetch_item_id.limit)
        existing_link_number, update_link_number, create_link_number, link_number, fail_link_number = 0,0,0,0,0
        for r in objs:
            url_id = False
            try:
                is_fail_link_number, is_existing_link_number, is_update_link_number, is_create_link_number= \
                    self.topic_handle(r.link, url_id,{}, fetch_item_id, search_bds_obj=r)
                existing_link_number += is_existing_link_number
                update_link_number += is_update_link_number
                create_link_number += is_create_link_number
                fail_link_number += is_fail_link_number
                link_number += 1
            except FetchError as e:
                self.env['bds.error'].create({'name':str(e),'des':str(e)})
        return existing_link_number, update_link_number, create_link_number, link_number, fail_link_number


    def get_st_is_compare_price_or_public_date(self, fetch_item_id):
        return True
        
    def get_st_is_pre_topic_dict_from_page_dict_and_url_id(self, fetch_item_id):
        return True


    def fetch_a_url_id (self, fetch_item_id):
        begin_time = datetime.datetime.now()
        is_finished = False
        url_id = fetch_item_id.url_id
        self.siteleech_id_id = url_id.siteleech_id.id
        self.site_name = url_id.siteleech_id.name + (' ' +   url_id.fetch_mode if url_id.fetch_mode else '')
        self.model_name = fetch_item_id.model_id.name
        end_page_number_in_once_fetch = False
        existing_link_number, update_link_number, create_link_number, link_number, fail_link_number = 0, 0, 0, 0, 0
        self.st_is_compare_price_or_public_date = self.get_st_is_compare_price_or_public_date(fetch_item_id)
        self.st_is_pre_topic_dict_from_page_dict_and_url_id = self.get_st_is_pre_topic_dict_from_page_dict_and_url_id(fetch_item_id)
        
        
        if fetch_item_id.topic_link or fetch_item_id.topic_path:
            self.topic_path = fetch_item_id.topic_path
            existing_link_number_one_page, update_link_number_one_page, create_link_number_one_page,\
                    fail_link_number_one_page = \
                self.topic_handle(fetch_item_id.topic_link, url_id, {}, fetch_item_id, None)
            link_number_one_page = 1
            existing_link_number += existing_link_number_one_page
            update_link_number += update_link_number_one_page
            create_link_number += create_link_number_one_page
            fail_link_number += fail_link_number_one_page
            link_number += link_number_one_page
        elif  fetch_item_id.model_id:
            existing_link_number, update_link_number, create_link_number, link_number, fail_link_number = \
                self.fetch_bo_sung_da_co_link(fetch_item_id)
            link_number = update_link_number
            end_page_number_in_once_fetch = False
            is_finished = False
        else:
            
            if not fetch_item_id.page_path:
                end_page_number_in_once_fetch, page_lists, begin, so_page =  self.gen_page_number_list(fetch_item_id) 
            else: 
                page_lists = range(1)
            
            for page_int in page_lists:
                page_handle_rs = self.page_handle( page_int, url_id, fetch_item_id)
                existing_link_number_one_page, update_link_number_one_page, create_link_number_one_page,\
                    fail_link_number_one_page, link_number_one_page = page_handle_rs
                    
                existing_link_number += existing_link_number_one_page
                update_link_number += update_link_number_one_page
                create_link_number += create_link_number_one_page
                fail_link_number += fail_link_number_one_page
                link_number += link_number_one_page
                
                if not fetch_item_id.page_path:
                    if end_page_number_in_once_fetch == self.max_page_assign_again:
                        is_finished = True
                else:
                    is_finished = True

        self.last_fetched_item_id = fetch_item_id
        interval = (datetime.datetime.now() - begin_time).total_seconds()
        fetch_item_id.interval = interval
        fetch_item_id.write({'current_page': end_page_number_in_once_fetch,
                    'create_link_number': create_link_number,
                    'update_link_number': update_link_number,
                    'link_number': link_number,
                    'fail_link_number':fail_link_number, 
                    'existing_link_number': existing_link_number,
                    'is_finished':is_finished,
                    })
        can_xoa = self.env['bds.fetch.item.history'].search([('fetch_item_id','=', fetch_item_id.id)], offset=4)
        can_xoa.unlink()

        self.env['bds.fetch.item.history'].create({
            'current_page': end_page_number_in_once_fetch,
            'create_link_number': create_link_number,
            'update_link_number': update_link_number,
            'link_number': link_number,
            'existing_link_number': existing_link_number,
            'fetch_item_id':fetch_item_id.id,
            'interval':interval,
        })
        fetch_item_id.fetched_number +=1

        return None

    def look_next_fetched_url_id(self):
        fetch_item_ids = self.fetch_item_ids.filtered(lambda i: not i.disible)

        if self.is_next_if_only_finish:
            object_url_ids = fetch_item_ids.filtered(lambda r: not r.is_finished)
        else:
            object_url_ids = fetch_item_ids
       
        current_fetched_url_id = self.last_fetched_item_id
        if not current_fetched_url_id.model_id:
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
            # while 1:
                # sleep_count = 5
                # while sleep_count:
                #     print ('sleep....%s'%sleep_count)
                #     sleep(1)
                #     sleep_count-=1
            url_id = self.look_next_fetched_url_id()
            try:
                self.fetch_a_url_id(url_id)
            except FetchError as e:
                self.env['bds.error'].create({'name':str(e),'des':'type of error:%s'%type(e)})


    def fetch_all_url(self):
        url_ids = self.fetch_item_ids
        for url_id in url_ids:
            self.fetch_a_url_id (url_id)



    





