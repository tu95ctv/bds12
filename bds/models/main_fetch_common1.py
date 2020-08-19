# -*- coding: utf-8 -*-
import re
import datetime
from datetime import timedelta
import os
import sys
print (sys.path)
import pytz
import traceback
from time import sleep
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)

import json
import math
import re
from urllib import request
from unidecode import unidecode
# from odoo.osv import expression
# from .compute_bds import _compute_mat_tien_or_trich_dia_chi1
import logging
_logger = logging.getLogger(__name__)

##########bds tools####################
class FetchError(Exception):
    pass

class SaveAndRaiseException(Exception):
    pass

class SaveAndPass(Exception):
    pass

def g_or_c_ss(self_env_class_name,search_dict,
                create_write_dict ={},
                update_no_need_check_change=False,
                is_up_date = True,
                not_active_include_search = False
            ):
    if not_active_include_search:
        domain_not_active = ['|',('active','=',True),('active','=',False)]
    else:
        domain_not_active = []
    domain = []
    for i in search_dict:
        tuple_in = (i,'=',search_dict[i])
        domain.append(tuple_in)
    # domain = expression.AND([domain_not_active, domain])
    domain_not_active.extend(domain)
    domain = domain_not_active
    searched_object  = self_env_class_name.search(domain)
    if not searched_object:
        search_dict.update(create_write_dict)
        created_object = self_env_class_name.create(search_dict)
        return_obj =  created_object
    else:
        return_obj = searched_object
        is_change = update_no_need_check_change
        if not is_change and is_up_date:
            for attr in create_write_dict:
                domain_val = create_write_dict[attr]
                exit_val = getattr(searched_object,attr)
                try:
                    exit_val = getattr(exit_val,'id',exit_val)
                    if exit_val ==None: #recorderset.id ==None when recorder sset = ()
                        exit_val=False
                except:#singelton
                    pass
                # if isinstance(domain_val, datetime.date):
                #     exit_val = fields.Date.from_string(exit_val)
                if exit_val !=domain_val:
                    is_change = True
                    break
        if is_change:
            searched_object.write(create_write_dict)
    return return_obj       

##############! bds tools ########################
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
##############!cho tot###########

def convert_native_utc_datetime_to_gmt_7(utc_datetime_inputs):
        local = pytz.timezone('Etc/GMT-7')
        utc_tz =pytz.utc
        gio_bat_dau_utc_native = utc_datetime_inputs
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

def write_gia(topic_dict):
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

def write_public_datetime(topic_dict):
    update = {}
    print ('**topic_dict**', topic_dict)
    if 'date' in topic_dict and 'public_datetime' not in topic_dict:
        date = topic_dict['date']
        public_datetime = convert_chotot_date_to_datetime(date)
        update ['public_datetime'] = public_datetime
    if 'publish_date_str' in topic_dict and 'public_datetime' not in topic_dict:
        publish_date_str = topic_dict['publish_date_str']
        public_datetime = datetime.datetime.strptime(publish_date_str,"%d/%m/%Y")
        update ['public_datetime'] = public_datetime
        

    public_datetime = topic_dict.get('public_datetime')  or public_datetime # naitive datetime
    gmt7_public_datetime = convert_native_utc_datetime_to_gmt_7(public_datetime)
    public_date  = gmt7_public_datetime.date()
    # return public_datetime, public_date
    print ('***public_date***', public_date)
    update['public_date'] = public_date
    update['public_datetime'] = public_datetime
    return update

class MainFetchCommon():
    # _name = 'abstract.main.fetch'
    allow_update = True
    attrs_dict = {}
    def __init__(self, attrs_dict = {}):
        self.attrs_dict = attrs_dict
    
    def file_from_tuong_doi(self, tuong_doi_path):
        dir_path = os.path.dirname(os.path.abspath(__file__))
        # if self.is_test:
        dir_path = os.path.dirname(dir_path)
        # dir_path = os.path.dirname(dir_path)
    #     dir_path = r"C:\D4\tgl_code\bds12\bds\models"
        f = open(os.path.join(dir_path,'html_log', '%s.html'%tuong_doi_path), 'r', encoding="utf8")
        return f.read()
    
    def save_to_disk(self, ct, name_file ):
        dir_path = os.path.dirname(os.path.abspath(__file__))
        dir_path = os.path.dirname(dir_path)
        # dir_path = os.path.dirname(dir_path)
        f = open(os.path.join(dir_path, 'html_log', '%s.html'%name_file), 'w', encoding="utf8")
        f.write(ct)
        f.close()

    def save_to_disk_mau( self, ct, page_or_topic, surfix='' ):
        if self.attrs_dict.get('is_save_mau'):
            dir_path = os.path.dirname(os.path.abspath(__file__))
            dir_path = os.path.dirname(dir_path)
            # dir_path = os.path.dirname(dir_path)
            f = open(os.path.join(dir_path, 'html_log', '%s_%s%s.html'%(page_or_topic, self.site_name, '_%s'%surfix if surfix else '')), 'w', encoding="utf8")
            f.write(ct)
            f.close()

    def get_main_obj(self):
        return self.env['bds.bds']
    
    def get_public_date_from_public_datetime(self, topic_data_from_page):
        public_datetime = topic_data_from_page['public_datetime'] # naitive datetime
        gmt7_public_datetime = convert_native_utc_datetime_to_gmt_7(public_datetime)
        public_date  = gmt7_public_datetime.date()
        return public_datetime, public_date


    def th_bds_type_update_compare_price(self, search_bds_obj, topic_data_from_page):

        public_datetime = topic_data_from_page['public_datetime']
        public_date = topic_data_from_page['public_date']
        update_dict = {}
        now = datetime.datetime.now()
        diff_day_public_from_now =  (now - public_datetime).days
        if diff_day_public_from_now==0:
            public_datetime_cu  = search_bds_obj.public_datetime
            print ('**topic_data_from_page**', topic_data_from_page)
            print ('***public_datetime**', public_datetime, '**public_datetime_cu**', public_datetime_cu)
            diff_public_datetime_in_hours = int((public_datetime - public_datetime_cu + timedelta(hours=1)).seconds/3600)
            if diff_public_datetime_in_hours > 2 :
                public_date_cu =  search_bds_obj.public_date
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
            gia=topic_data_from_page['price']
            gia_cu = search_bds_obj.price
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


    def th_more_create_dict(self, topic_data_from_page, url_id, link):
        create_dict = {}
       
        create_dict['siteleech_id'] = self.siteleech_id_id
        create_dict['cate'] = url_id.cate
        create_dict['sell_or_rent'] = url_id.sell_or_rent
        # create_dict['link'] = link
        create_dict['url_id'] = url_id.id
        
        return create_dict



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
            
            poster =  self.env['bds.poster'].create(search_dict)
            if siteleech_id_id:
                search_dict.update({'created_by_site_id': siteleech_id_id})
                self.env['bds.posternamelines'].create( {'username_in_site':account_name, 'site_id':siteleech_id_id, 'poster_id':poster.id})
        return {'poster_id':poster.id}

    def write_trich_dia_chi(self, topic_dict):
        html = topic_dict['html']
        mat_tien_address, trich_dia_chi, mat_tien_or_trich_dia_chi, is_mat_tien_or_trich_dia_chi = \
            _compute_mat_tien_or_trich_dia_chi1(self, html, html)
        topic_dict['mat_tien_address'] = mat_tien_address
        topic_dict['trich_dia_chi'] = trich_dia_chi
        topic_dict['mat_tien_or_trich_dia_chi'] = mat_tien_or_trich_dia_chi
        topic_dict['is_mat_tien_or_trich_dia_chi'] = is_mat_tien_or_trich_dia_chi
        
    def odoo_model_topic_dict(self, topic_dict):
        if not self.is_test:
            topic_dict.update(self.write_quan_phuong(topic_dict))
            topic_dict.update(self.write_images(topic_dict))
            topic_dict.update(self.write_poster(topic_dict, self.siteleech_id_id))
        
        topic_dict.update(write_gia(topic_dict))
        topic_dict.update(write_public_datetime(topic_dict))
        self.write_trich_dia_chi(topic_dict)

    def request_parse_html_topic(self, link):
        if getattr(self,'topic_path',None):
            topic_html = self.file_from_tuong_doi(self.topic_path)
        else:
            headers = self.page_header_request()
            header_kwargs = {'headers': headers} if headers else {}
            topic_html = request_html(link, **header_kwargs)
        
        if not getattr(self,'topic_count',None):
            self.save_to_disk_mau(topic_html, 'topic', surfix='')
        try:
            # is_save_and_raise_in_topic = self.attrs_dict.get('is_save_and_raise_in_topic')
            # if is_save_and_raise_in_topic:
            #     raise SaveAndRaiseException(self.site_name)
            topic_dict = self.parse_html_topic(topic_html)
        except SaveAndRaiseException as e:
            self.save_to_disk(topic_html, 'file_topic_bug_theo_y_muon_%s'%str(e))
            raise
        except SaveAndPass as e:
            self.save_to_disk(topic_html, 'file_topic_bug_save_and_pass_%s'%str(e))
            raise
        except:
            self.save_to_disk(topic_html, 'file_topic_bug')
            raise
        topic_dict['link'] = link
        return topic_dict


    def del_list_id_topic_data_from_page(self, topic_data_from_page):
        if 'list_id' in topic_data_from_page:
            del topic_data_from_page['list_id']


    def topic_handle(self, link, url_id, topic_data_from_page, search_bds_obj=None):
        
        create_dict = {}
        self.link = link
        self.page_dict = topic_data_from_page
        if not self.is_test:
            if not search_bds_obj:
                main_obj = self.get_main_obj()
                search_bds_obj= main_obj.search([('link','=',link)])
            else:
                link = search_bds_obj.link
        is_fail_link_number = 0
        is_existing_link_number = 0
        is_update_link_number = 0
        is_create_link_number = 0
        try:
            if  not self.is_test and search_bds_obj:
                if not self.is_must_update_combine:# update ở mode bình thường
                    update_dict = {}
                    if self.st_is_bds_site:
                        topic_data_from_page.update(write_public_datetime(topic_data_from_page))
                        topic_data_from_page.update(write_gia(topic_data_from_page))
                        compare_update_dict = self.th_bds_type_update_compare_price(search_bds_obj, topic_data_from_page)
                        update_dict.update(compare_update_dict)
                    a_topic_fetch_dict = topic_data_from_page
                else:
                    update_dict = self.request_parse_html_topic(link)
                    update_dict.update(topic_data_from_page)
                    if self.st_is_bds_site:
                        self.odoo_model_topic_dict(update_dict)

                    if self.model_id:
                        update_dict['is_full_topic'] =  True
                    a_topic_fetch_dict = update_dict
                if update_dict:
                    search_bds_obj.write(update_dict)
                    is_update_link_number = 1

                is_existing_link_number = 1
            else:
                create_dict = {}
            
                if self.st_is_request_topic:
                    create_dict = self.request_parse_html_topic(link)
                if self.is_pagehandle:
                    create_dict.update(topic_data_from_page)
                
                if self.st_is_bds_site :
                    print ('***vao day khong')
                    self.odoo_model_topic_dict(create_dict)
                    if not self.is_test:
                        more_create_dict = self.th_more_create_dict(create_dict, url_id, link)
                        create_dict.update(more_create_dict)
                a_topic_fetch_dict = create_dict
                if not self.is_test:
                    main_obj.create(create_dict) 
                    self.env.cr.commit()
                is_create_link_number = 1
                if not self.is_test:
                    self.env['bds.error'].create({
                    'name':'success link',
                    'des':'success link',
                    'link':link,
                    'type':'success',
                    'link_type':'topic',
                    'fetch_item_id':self.fetch_item_id.id,
                    'error_or_success':'success',
                        })
                    

        except FetchError as e:
            is_fail_link_number = 1
            if not self.is_test:
                self.env['bds.error'].create({
                    'name':str(e),
                    'des':str(e),
                    'link':link,
                    'type':'fetch_error',
                    'link_type':'topic',
                    'fetch_item_id':self.fetch_item_id.id,
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
                'fetch_item_id':self.fetch_item_id.id,
                }
                )
        return is_existing_link_number, is_update_link_number, is_create_link_number, is_fail_link_number, a_topic_fetch_dict

        


    def make_topic_link_from_list_id_common(self, list_id):
        link = list_id
        return link  

    def page_header_request(self):
        return None

    def page_handle(self, page_int,url, url_id, fetch_item_id):
        existing_link_number, update_link_number, create_link_number, fail_link_number, link_number = 0, 0, 0, 0, 0
        page_list = []
        try:
            if not self.page_path:
                format_page_url = url or  url_id.url 
                page_url = self.create_page_link(format_page_url, page_int)
                headers = self.page_header_request()
                header_kwargs = {'headers': headers} if headers else {}
                html_page = request_html(page_url,**header_kwargs)
            else:
                html_page = self.file_from_tuong_doi(self.page_path)
            self.save_to_disk_mau(html_page, 'page', surfix='')
            try:
                topic_data_from_pages_of_a_page = self.ph_parse_pre_topic(html_page)
            except SaveAndRaiseException as e:
                self.save_to_disk(html_page, 'file_topic_bug_theo_y_muon_%s'%str(e))
                raise
                # raise 
            except:
                file_name = 'file_page_bug' if not self.page_path else 'file_page_bug_page_path'
                self.save_to_disk(html_page, file_name)
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
            file_name = 'file_page_bug_no_topic' if not self.page_path else 'file_page_bug_page_path'
            self.save_to_disk(html_page, file_name)
            raise ValueError('topic_data_from_pages_of_a_page is empty')
         
        for topic_count, topic_data_from_page in enumerate(topic_data_from_pages_of_a_page):
            self.topic_count = topic_count
            link = topic_data_from_page['link']
            # link = self.make_topic_link_from_list_id(list_id)
            # if self.topic_count == 5:
            #     self.env.cr.rollback()
                # return is_existing_link_number, is_update_link_number, is_create_link_number, is_fail_link_number
            try:
                is_existing_link_number, is_update_link_number, is_create_link_number, is_fail_link_number,  a_topic_fetch_dict = \
                    self.topic_handle(link, url_id, topic_data_from_page
                            )
                existing_link_number += is_existing_link_number
                update_link_number += is_update_link_number
                create_link_number += is_create_link_number
                fail_link_number +=is_fail_link_number
                page_list.append(a_topic_fetch_dict)
                
            except SaveAndPass:
                pass

        link_number = len(topic_data_from_pages_of_a_page)
        return existing_link_number, update_link_number, create_link_number, fail_link_number, link_number, page_list

    def gen_page_number_list(self, fetch_item_id ): 
        if self.is_test:
            end_page_number_in_once_fetch, page_lists, begin, number_of_pages = 1,[1],1,1
            return end_page_number_in_once_fetch, page_lists, begin, number_of_pages
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
            print ('**8web_last_page_number**', web_last_page_number)
        except FetchError as e:
            web_last_page_number = fetch_item_id.url_id.web_last_page_number or 200
            fetch_error = True

        if set_leech_max_page and  set_leech_max_page < web_last_page_number:
            max_page =  set_leech_max_page
        else:
            max_page = web_last_page_number
        print ('***max_page***', max_page)
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
        page_lists = range(begin, end + 1)
        number_of_pages = end - begin + 1
        return end_page_number_in_once_fetch, page_lists, begin, number_of_pages


    def fetch_bo_sung_da_co_link(self, fetch_item_id):
        model = fetch_item_id.model_id.name
        objs = self.env[model].search([('is_full_topic','=',False)], limit=fetch_item_id.limit)
        existing_link_number, update_link_number, create_link_number, link_number, fail_link_number = 0,0,0,0,0
        for r in objs:
            url_id = False
            try:
                topic_data_from_page = {}
                    
                link = None
                is_fail_link_number, is_existing_link_number, is_update_link_number, is_create_link_number, create_dict= \
                    self.topic_handle(link, url_id, topic_data_from_page, search_bds_obj=r)
                existing_link_number += is_existing_link_number
                update_link_number += is_update_link_number
                create_link_number += is_create_link_number
                fail_link_number += is_fail_link_number
                link_number += 1
            except FetchError as e:
                self.env['bds.error'].create({'name':str(e),'des':str(e)})
        return existing_link_number, update_link_number, create_link_number, link_number, fail_link_number


    def get_st_is_bds_site(self):
        return True


    def setting_for_fetch_obj(self, url_id, fetch_item_id):
        self.siteleech_id_id = url_id.siteleech_id.id  if url_id else False
        self.site_name = (url_id.siteleech_id.name + (' ' + url_id.fetch_mode if url_id.fetch_mode else '')) if url_id else self.attrs_dict.get('site_name')
        self.model_name = fetch_item_id.model_id.name if fetch_item_id else False
        self.st_is_bds_site = self.get_st_is_bds_site()
        
        self.st_is_request_topic = not fetch_item_id.not_request_topic if fetch_item_id else self.attrs_dict.get('st_is_request_topic', True)
        self.model_id = fetch_item_id.model_id if fetch_item_id else False
        self.topic_link = fetch_item_id.topic_link if fetch_item_id else self.attrs_dict.get('topic_link')
        self.topic_path = fetch_item_id.topic_path if fetch_item_id else self.attrs_dict.get('topic_path')
        self.page_path = fetch_item_id.page_path if fetch_item_id else self.attrs_dict.get('page_path')
        self.is_must_update_topic = fetch_item_id.page_path if fetch_item_id else False
        self.is_pagehandle = not (self.topic_link or self.topic_path or \
                    self.model_id)
        self.is_test = self.attrs_dict.get('is_test')
        self.url = url_id.url if url_id else self.attrs_dict.get('url')
        

    def _fetch_a_url_id (self,url_id, fetch_item_id):
        fetch_list = []
        end_page_number_in_once_fetch = False
        existing_link_number, update_link_number, create_link_number, link_number, fail_link_number = 0, 0, 0, 0, 0
        if self.topic_link or self.topic_path:
            topic_data_from_page = {}
            existing_link_number_one_page, update_link_number_one_page, create_link_number_one_page,\
                    fail_link_number_one_page, fetch_dict = \
                self.topic_handle(self.topic_link, url_id, topic_data_from_page)
            link_number_one_page = 1
            existing_link_number += existing_link_number_one_page
            update_link_number += update_link_number_one_page
            create_link_number += create_link_number_one_page
            fail_link_number += fail_link_number_one_page
            link_number += link_number_one_page
            is_finished = False
            fetch_list.append(fetch_dict)
        elif self.model_id:
            existing_link_number, update_link_number, create_link_number, link_number, fail_link_number = \
                self.fetch_bo_sung_da_co_link(fetch_item_id)
            link_number = update_link_number
            is_finished = False
        else:
            if not self.page_path and fetch_item_id:
                end_page_number_in_once_fetch, page_lists, begin, so_page =  self.gen_page_number_list(fetch_item_id) 
            else: 
                if not self.page_path:
                    begin_page, end_page = self.attrs_dict.get('begin_page') or 1, self.attrs_dict.get('end_page') or 1
                else:
                    begin_page, end_page = 1,1
                page_lists = range(begin_page,end_page+1)
            
            for page_int in page_lists:
                rs = self.page_handle( page_int,self.url, url_id, fetch_item_id)
                existing_link_number_one_page, update_link_number_one_page, create_link_number_one_page,\
                    fail_link_number_one_page, link_number_one_page, page_list = rs
                    
                existing_link_number += existing_link_number_one_page
                update_link_number += update_link_number_one_page
                create_link_number += create_link_number_one_page
                fail_link_number += fail_link_number_one_page
                link_number += link_number_one_page
                if not self.page_path and not self.is_test:
                    if end_page_number_in_once_fetch == self.max_page_assign_again:
                        is_finished = True
                    else:
                        is_finished = False
                else:
                    is_finished = True
                fetch_list.extend(page_list)
        return existing_link_number, update_link_number, create_link_number, link_number, fail_link_number, is_finished, end_page_number_in_once_fetch, fetch_list


    def fetch_a_url_id (self, fetch_item_id):
        begin_time = datetime.datetime.now()
        if fetch_item_id:
            url_id = fetch_item_id.url_id
        else:
            url_id = False
        self.setting_for_fetch_obj( url_id, fetch_item_id)
        
        self.is_must_update_combine = self.topic_link or self.topic_path \
                     or self.is_must_update_topic or bool(self.model_id)
        self.fetch_item_id = fetch_item_id


        existing_link_number, update_link_number, create_link_number, link_number, fail_link_number, is_finished,\
            end_page_number_in_once_fetch, fetch_list = \
            self._fetch_a_url_id (url_id, fetch_item_id)
        interval = (datetime.datetime.now() - begin_time).total_seconds()
        if not self.is_test:
            self.write_fetch(fetch_item_id, interval, end_page_number_in_once_fetch, create_link_number,\
            update_link_number, link_number, fail_link_number, existing_link_number, is_finished)
            self.ph_fetch_item_history_deal(fetch_item_id, end_page_number_in_once_fetch, create_link_number,\
            update_link_number, link_number, existing_link_number, interval)
            self.last_fetched_item_id = fetch_item_id
        return fetch_list

    def write_fetch(self, fetch_item_id, interval, end_page_number_in_once_fetch, create_link_number,\
        update_link_number, link_number, fail_link_number, existing_link_number, is_finished):
        fetch_item_id.fetched_number +=1
        fetch_item_id.interval = interval
        fetch_item_id.write({'current_page': end_page_number_in_once_fetch,
                    'create_link_number': create_link_number,
                    'update_link_number': update_link_number,
                    'link_number': link_number,
                    'fail_link_number':fail_link_number, 
                    'existing_link_number': existing_link_number,
                    'is_finished':is_finished,
                    })

    def ph_fetch_item_history_deal(self, fetch_item_id, end_page_number_in_once_fetch, create_link_number,\
        update_link_number, link_number, existing_link_number, interval):
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
            raise ValueError('Không loop được url')
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

    ########## cho tot###############

    def ph_parse_pre_topic(self, html_page):
        topic_data_from_pages_of_a_page = []
        if self.site_name == 'chotot':
            json_a_page = json.loads(html_page)
#             raise SaveAndRaiseException('chototnew')
            topic_data_from_pages_of_a_page_origin = json_a_page['ads']
            for ad in topic_data_from_pages_of_a_page_origin:
                topic_data_from_page = {}
                topic_data_from_page['price_string'] = ad['price_string']
                topic_data_from_page['price'] = ad['price']
                topic_data_from_page['gia'] = ad['price']/1000000000
                topic_data_from_page['date'] = ad['date']
                topic_data_from_page['link'] = self.make_topic_link_from_list_id(ad['list_id'])
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

    def parse_html_topic (self, topic_html):
        if self.site_name =='chotot':
            topic_dict = self.get_topic_chotot(topic_html, self.page_dict)
            return topic_dict
        return super().parse_html_topic(topic_html)

    def make_topic_link_from_list_id(self, list_id):
        if  self.site_name =='chotot':
            link  = 'https://gateway.chotot.com/v1/public/ad-listing/' + str(list_id)
            return link
        return self.make_topic_link_from_list_id_common(list_id)

    def get_last_page_number(self, url_id):
        if self.site_name =='chotot':
            page_1st_url = create_cho_tot_page_link(url_id.url, 1)
            html = request_html(page_1st_url)
            html = json.loads(html)
            total = int(html["total"])
            web_last_page_number = int(math.ceil(total/20.0))
            return web_last_page_number
    
    def get_topic_chotot(self, topic_html, page_dict):
        update_dict = {}
        
        topic_html = json.loads(topic_html) 
        ad = topic_html['ad']
        ad_params = topic_html['ad_params']

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
        update_dict['date'] = ad['date']
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


#######################BDSCOMVN###################


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
from bs4 import BeautifulSoup

def get_last_page_from_bdsvn_website(url_id):
    html = request_html(url_id.url)
    soup = BeautifulSoup(html, 'html.parser')
    range_pages = soup.select('div.background-pager-right-controls > a')
    
    if range_pages:
        try:
            last_page_href =  range_pages[-1]['href']
            kq= re.search('\d+$',last_page_href)
            web_last_page_number =  int(kq.group(0))
            return web_last_page_number
        except Exception as e:
            pass
    if url_id.web_last_page_number:
        return url_id.web_last_page_number
    else:
        web_last_page_number = 1000
    return web_last_page_number


class MainFetchCommonBDS(MainFetchCommon):

    def get_last_page_number(self, url_id):
        if self.site_name =='batdongsan':
            return get_last_page_from_bdsvn_website(url_id)
        return super().get_last_page_number(url_id)
    
    def make_topic_link_from_list_id(self, list_id):
        link = super().make_topic_link_from_list_id(list_id)
        if self.site_name =='batdongsan':
            link  = 'https://batdongsan.com.vn' +  list_id
        
        return link

    def parse_html_topic (self, topic_html):
        if self.site_name =='batdongsan':
            # get_bds_dict_in_topic(self, topic_html, self.page_dict)
            topic_dict = get_bds_dict_in_topic(topic_html, self.page_dict)
            return topic_dict
        return super().parse_html_topic(topic_html)
        

    def create_page_link(self, format_page_url, page_int):
        page_url = super().create_page_link(format_page_url, page_int)
        if self.site_name == 'batdongsan':
            page_url = format_page_url  + '/p' +str(page_int)
        return page_url

    def page_header_request(self):
        # return None
        
        if self.site_name == 'batdongsan':
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
        topic_data_from_pages_of_a_page = super().ph_parse_pre_topic(html_page)
        if self.site_name == 'batdongsan':
            soup = BeautifulSoup(html_page, 'html.parser')
            title_and_icons = soup.select('div.search-productItem')
            if title_and_icons:
                page_css_type = 1
                for title_and_icon in title_and_icons:
                    vip = title_and_icon['class'][0]
                    topic_data_from_page = {}
                    topic_data_from_page['vip'] = vip
                    title_soups = title_and_icon.select("div.p-title  a")
                    href = title_soups[0]['href']
                    topic_data_from_page['link'] = self.make_topic_link_from_list_id(href)
                    icon_soup = title_and_icon.select('img.product-avatar-img')
                    thumb = icon_soup[0]['src']
                    if 'nophoto' in thumb:
                        thumb = 'https://batdongsan.com.vn/Images/nophoto.jpg'
                    topic_data_from_page['thumb'] = thumb
                    gia_soup = title_and_icon.select('strong.product-price')
                    gia = gia_soup[0].get_text()
                    gia = gia.strip()
                    quan_huyen_str = title_and_icon.select('span.p-district strong.product-city-dist')[0].get_text()

                    topic_data_from_page['price_string'] = gia
                    quan_huyen_strs = quan_huyen_str.split(',')
                    tinh_str = quan_huyen_strs[1]
                    quan_str = quan_huyen_strs[0]
                    topic_data_from_page['region_name'] = tinh_str
                    topic_data_from_page['area_name'] = quan_str



                    date_dang = title_and_icon.select('span.uptime')
                    date_dang = date_dang[0].get_text().replace('\n','')
                    date_dang = date_dang[-10:]
                    # public_datetime = datetime.datetime.strptime(date_dang,"%d/%m/%Y")
                    # topic_data_from_page['public_datetime'] = public_datetime
                    topic_data_from_page['publish_date_str'] = date_dang
                    topic_data_from_page['thumb'] = icon_soup[0]['src']
                    topic_data_from_pages_of_a_page.append(topic_data_from_page)
            else:
                title_and_icons = soup.select('div.product-item')
                if title_and_icons:
                    page_css_type = 2
                for title_and_icon in title_and_icons:
                    vip = title_and_icon['class'][0]
                    topic_data_from_page = {}
                    topic_data_from_page['vip'] = vip
                    title_soup = title_and_icon.select(".product-title  a")[0]
                    href = title_soup['href']
                    topic_data_from_page['link'] = self.make_topic_link_from_list_id(href)

                    icon_soup = title_and_icon.select('img.product-avatar-img')[0]
                    topic_data_from_page['thumb'] = icon_soup['src']
                    gia_soup = title_and_icon.select('span.price')
                    gia = gia_soup[0].get_text()
                    gia = gia.strip()
                    quan_huyen_str = title_and_icon.select('div.product-info > span.location')[0].get_text()
                    
                    topic_data_from_page['price_string'] = gia
                    quan_huyen_strs = quan_huyen_str.split(',')
                    tinh_str = quan_huyen_strs[1]
                    quan_str = quan_huyen_strs[0]
                    topic_data_from_page['region_name'] = tinh_str
                    topic_data_from_page['area_name'] = quan_str
                  

                    date_dang = title_and_icon.select('span.tooltip-time')
                    date_dang = date_dang[0].get_text().replace('\n','')
                    public_datetime = datetime.datetime.strptime(date_dang,"%d/%m/%Y")
                    topic_data_from_page['public_datetime'] = public_datetime
                    topic_data_from_pages_of_a_page.append(topic_data_from_page)

                if not title_and_icons:
                    title_and_icons = soup.select('div.vip5')[1:]
                    if title_and_icons:
                        page_css_type = 3
                    
                    for title_and_icon in title_and_icons:
                        vip = title_and_icon['class'][0]
                        topic_data_from_page = {}
                        topic_data_from_page['vip'] = vip
                        title_soups = title_and_icon.select("div.p-title  a")
                        href = title_soups[0]['href']
                        topic_data_from_page['link'] = self.make_topic_link_from_list_id(href)
                        icon_soup = title_and_icon.select('img.product-avatar-img')
                        topic_data_from_page['thumb'] = icon_soup[0]['src']
                        gia_soup = title_and_icon.select('span.product-price')
                        gia = gia_soup[0].get_text()
                        gia = gia.strip()

                        topic_data_from_page['price_string'] = gia
                        # quan_huyen_strs = quan_huyen_str.split(',')
                        # tinh_str = quan_huyen_strs[1]
                        # quan_str = quan_huyen_strs[0]
                        # topic_data_from_page['region_name'] = tinh_str
                        # topic_data_from_page['area_name'] = quan_str

                        date_dang = title_and_icon.select('div.p-content div.mar-right-10')
                        date_dang = date_dang[0].get_text().replace('\n','')
                        date_dang = re.sub('\s*','', date_dang)
                        date_dang = date_dang[-10:]
                        public_datetime = datetime.datetime.strptime(date_dang,"%d/%m/%Y")
                        topic_data_from_page['public_datetime'] = public_datetime
                        topic_data_from_page['thumb'] = icon_soup[0]['src']
                        topic_data_from_pages_of_a_page.append(topic_data_from_page)
            # print ('***page_css_type***', page_css_type)
#             raise SaveAndRaiseException('page_bdscomvn_type_%s'%page_css_type)
            # print (aaa)
            # if topic_data_from_pages_of_a_page:
            if self.is_test or page_css_type ==1:
                self.save_to_disk(html_page, 'bds_page_loai_%s'%page_css_type)
        return topic_data_from_pages_of_a_page
MainFetchCommon = MainFetchCommonBDS
####################### PARSE MUABAN##########################

def get_phuong_xa_from_topic(self,soup):
    sl = soup.select('div#divWard li.current')   
    if sl:
        phuong_name =  sl[0].get_text()
    else:
        phuong_name =  False
    return phuong_name


def get_images_for_bds_com_vn(soup):
    rs = soup.select('meta[property="og:image"]')
    images =  list(map(lambda i:i['content'], rs))
    return images


def get_public_datetime(soup):
    try:
        select = soup.select('div.prd-more-info > div:nth-of-type(3)')#[0].contents[0]
        publish_date_str = select[0].contents[2]
    except IndexError:
        pass
    publish_date_str = publish_date_str.replace('\r','').replace('\n','')
    publish_date_str = re.sub('\s*', '', publish_date_str)
    public_datetime = datetime.datetime.strptime(publish_date_str,"%d-%m-%Y")
    return public_datetime


def get_product_detail(soup, type_bdscom_topic = 1):
    if type_bdscom_topic==1:
        select = soup.select('div.pm-desc')[0]
    elif type_bdscom_topic==2:
        
        select = soup.select('div.des-product')[0]
        
    return select.get_text()
    

def get_mobile_name_for_batdongsan(soup):
    phone = get_mobile_user(soup)
    try:
        name = get_user_name(soup)
    except:
        name = 'no name bds'
    return phone, name
   

def get_dientich(soup):
    try:
        kqs = soup.find_all("span", class_="gia-title")
        gia = kqs[1].find_all("strong")
    except:
        try:
            gia = soup.select('div.short-detail-wrap > ul.short-detail-2 > li:nth-of-type(2) > span.sp2')
        except:
            raise 
    try:
        gia = gia[0].get_text()
    except:
        return False
    try:
        rs = re.search(r"(\d+)", gia)
        gia = rs.group(1)
    except:
        gia = 0
    float_gia = float(gia)
    return float_gia


def get_mobile_user(soup):
    # mobile = False
    try:
        select = soup.select('div#LeftMainContent__productDetail_contactMobile')[0]
        mobile =  select.contents[3].contents[0]
        mobile =  mobile.strip()
        # raise SaveAndPass('bds_mobile_loai_1')
        # return mobile
    except IndexError:
        try:
            select = soup.select('span.phoneEvent')[0]
            phone = select['raw']
            # raise SaveAndPass('bds_mobile_loai_2')
        except IndexError:
            select = soup.select('#divCustomerInfoAd div.right-content .right')[0]
            phone = select.get_text()
            # raise SaveAndPass('bds_mobile_loai_3')
        mobile = phone
    if not mobile:
        raise ValueError('not phone')
    return mobile
    

def get_user_name(soup):
    name = False
    try:
        select = soup.select('div#LeftMainContent__productDetail_contactName')[0]
        name =  select.contents[3].contents[0]
        name =  name.strip()

    except:
        select = soup.select('dive.name')[0]
        name = select['title']
   
    if not name:
        raise ValueError('name')
    return name

def get_bds_dict_in_topic( html, page_dict):
    update_dict = {}
#     update_dict['data'] = html
    soup = BeautifulSoup(html, 'html.parser')
    
    try:
        kqs = soup.find_all("span", class_="gia-title")
        gia = kqs[0].find_all("strong")
        gia = gia[0].get_text()
        type_bdscom_topic = 1
        self.save_to_disk(html_page, 'topic_bdscomvn_page_loai_%s'%type_bdscom_topic)
    except:
        gia_soup = soup.select("div.short-detail-wrap > ul.short-detail-2 > li:nth-of-type(1) > span.sp2")[0]
        gia = gia_soup.get_text()
        type_bdscom_topic = 2
    update_dict['price_string'] = gia

    if type_bdscom_topic == 2:
        gia_soup = soup.select("div.product-config ul.short-detail-2 li:nth-of-type(1) span:nth-of-type(2)")[0]
        gia = gia_soup.get_text()
        update_dict['publish_date_str'] = gia

        gia_soups = soup.select("div.breadcrumb > a")

        region_name = gia_soups[1].get_text()
        update_dict['region_name'] = region_name

        area_name = gia_soups[2].get_text()
        update_dict['area_name'] = area_name

    
    
    update_dict['html'] = get_product_detail(soup, type_bdscom_topic)
    images = get_images_for_bds_com_vn(soup)
    if images:
        update_dict['images'] = images
    update_dict['area'] = get_dientich(soup)
    try:
        title = soup.select('div.pm-title > h1')[0].contents[0] 
    except:
        try:
            title = soup.select('h1.tile-product')[0].get_text()
        except:
            raise 
    update_dict['title']=title
    update_dict['phone'], update_dict['account_name'] = get_mobile_name_for_batdongsan(soup)
    try:
        loai_nha = soup.select('span.diadiem-title a')[0].get_text()
        loai_nha_search = re.search('(^.*?) tại', loai_nha)
        loai_nha = loai_nha_search.group(1)
    except:
        try:
            loai_nha = soup.select('div.breadcrumb a')[-1].get_text()
            loai_nha_search = re.search('(^.*?) tại', loai_nha)
            loai_nha = loai_nha_search.group(1)
        except:
            loai_nha = soup.select('span.diadiem > strong')[0].get_text()
    loai_nha = re.sub('^bán |^cho thuê ','',loai_nha, flags=re.I)  
    loai_nha = loai_nha.capitalize()    
    update_dict['loai_nha'] = loai_nha  

    for key, value in update_dict.items():
        if key not in page_dict:
            page_dict[key]  = value
    return page_dict

################## mua ban ############################
class MuabanFetch(MainFetchCommon):
    # _inherit = 'abstract.main.fetch'

    def get_last_page_number(self, url_id):
        if self.site_name =='muaban':
            return 300
        return super(MuabanFetch, self).get_last_page_number(url_id)
        
    def parse_html_topic (self, topic_html):
        if self.site_name =='muaban':
            topic_dict = MuabanObject().get_topic(topic_html)
            return topic_dict
        return super(MuabanFetch, self).parse_html_topic(topic_html)

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
                topic_data_from_page = {}
                image_soups = title_and_icon.select("a.list-item__link")
                image_soups = image_soups[0]
                href = image_soups['href']
                img = image_soups.select('img')[0]
                src_img = img.get('data-src',False)
                topic_data_from_page['link'] = self.make_topic_link_from_list_id(href)
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
                else:
                    gia = False
                
                topic_data_from_page['price_string'] = gia
                ngay_soup = title_and_icon.select('span.list-item__date')
                ngay = ngay_soup[0].get_text().strip().replace('\n','')
                public_datetime = datetime.datetime.strptime(ngay,"%d/%m/%Y")
                topic_data_from_page['public_datetime'] = public_datetime  
                topic_data_from_pages_of_a_page.append(topic_data_from_page)
        return topic_data_from_pages_of_a_page

MainFetchCommon = MuabanFetch


class MuabanObject():
    def write_images(self, soup):
        update_dict = {}
        image_soup = soup.select('div.image__slides img')
        images = [i['src'] for i in image_soup]
        update_dict['images'] = images
        return update_dict

    def write_gia_tho(self, soup):
        gia_soup = soup.select('div.price-container__value')
        try:
            gia =  gia_soup[0].get_text()
        except IndexError:
            gia = False
        return {'price_string':gia}

    def write_quan_phuong_tho(self, soup):
        quan_soup = soup.select('span.location-clock__location')
        quan_txt =  quan_soup[0].get_text()
        quan_tinhs = quan_txt.split('-')
        tinh_name = quan_tinhs[1].strip()
        tinh_name = re.sub('tphcm','Hồ Chí Minh', tinh_name,flags=re.I)
        quan_name =  quan_tinhs[0].strip()
        return {'region_name':tinh_name, 'area_name':quan_name}

    def write_poster_tho(self, soup):
        try:
            name_soup = soup.select('div.user-info__fullname')[0]
            name =  name_soup.get_text()
        except:
            name = None
        try:
            span_mobile_soup = soup.select('div.mobile-container__value span')[0]
            mobile = span_mobile_soup['mobile']
        except:
            mobile = None
        mobile = mobile or 'No Mobile'
        name = name or mobile
        return {'phone':mobile, 'account_name':name}

    def get_loai_nha(self, soup):
        loai_nha_soup = soup.select('div.breadcrumb li')
        loai_nha = loai_nha_soup[-1].get_text()
        return {'loai_nha':loai_nha}

    def get_topic(self, html):
        update_dict  = {}
        soup = BeautifulSoup(html, 'html.parser')
        content_soup = soup.select('div.body-container')
        update_dict['html']  = content_soup[0].get_text()
        update_dict.update(self.write_gia_tho(soup))
        update_dict.update(self.write_quan_phuong_tho(soup))
        update_dict.update(self.get_loai_nha(soup))
        update_dict.update(self.write_poster_tho(soup))
        title = soup.select('h1.title')[0].get_text()
        title = title.strip()
        update_dict['title'] = title
        return update_dict
################## !mua ban ###########################
class TapHoaMainFetch(MainFetchCommon):
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

    def parse_html_topic (self, topic_html):
        
        if self.site_name =='cuahangtaphoa' or self.model_name=='tap.hoa':
            topic_dict = {}
            a_page_html_soup = BeautifulSoup(topic_html, 'html.parser')
            topic_soups = a_page_html_soup.select('div.item-page')[0]
            try:
                nghanh_nghe_soup = topic_soups.select("li:contains('Ngành nghề chính: ')")[0]
                nghanh_nghe = nghanh_nghe_soup.get_text().split(':')[1]
                nghanh_nghe = nghanh_nghe.replace('./.','').strip()
            except IndexError:
                nghanh_nghe = False

            topic_dict['nganh_nghe_kinh_doanh'] = nghanh_nghe

            return topic_dict
        return super().parse_html_topic(topic_html)

    def create_page_link(self, format_page_url, page_int):
        page_url = super().create_page_link(format_page_url, page_int)
        if self.site_name == 'cuahangtaphoa':
            repl = 'page-%s'%page_int
            page_url =  re.sub('page-\d+', repl, format_page_url)
        return page_url

    def request_parse_html_topic(self, link):
        topic_dict = super().request_parse_html_topic(link)
        if self.site_name =='cuahangtaphoa' or self.model_name =='tap.hoa':
            topic_dict['is_full_topic'] = True
        return topic_dict

    def get_st_is_bds_site(self):
        if self.site_name =='cuahangtaphoa' or self.model_name =='tap.hoa':
            return False
        return super().get_st_is_bds_site()
    
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
                topic_data_from_page['mst'] = mst
                topic_data_from_page['address'] = dia_chi
                topic_data_from_page['title'] = title
                topic_data_from_page['html'] = ''
                topic_data_from_pages_of_a_page.append(topic_data_from_page)
        return topic_data_from_pages_of_a_page
MainFetchCommon = TapHoaMainFetch
############# COMPUTE FUNCTION ###############


def _compute_so_phong_ngu( html):
        so_phong_ngu = 0
        pt = '(\d{1,2})\s*(?:pn|phòng ngủ)(?:\W|$)'
        rs = re.search(pt, html, re.I)
        if rs:
            so_phong_ngu = rs.group(1)
            try:
                so_phong_ngu = int(so_phong_ngu)
            except: 
                so_phong_ngu = 0
        return so_phong_ngu

def detect_mat_tien_address(html, p = None):
    #parent function call: detect_mat_tien_address_sum
    before_index = 0
    deal_s = []
    full_adress_list = []
    while 1:
        html = html [before_index:]
        # p = '(?i:nhà|mt|mặt tiền|số)\s+(\d{1,4}[a-zA-Z]{0,2})[\s,]+(?i:đường)*\s*(?P<ten_duong>(?:[A-Z0-9Đ][\w|/]*\s*){1,4})(?:\.|\s|\,|$|<)'
        mat_tien_full_address_possibles = re.search(p, html, re.I)  #((\S+(?:\s|\.|$|,)+){1,4})
        if not mat_tien_full_address_possibles:
            break
        if mat_tien_full_address_possibles:
            before_index = mat_tien_full_address_possibles.span()[1] + 1
            number = mat_tien_full_address_possibles.group(1)
            ten_duong = mat_tien_full_address_possibles.group('ten_duong')
            is_check_word = re.search('[a-zđ]',ten_duong, re.I)
            if not is_check_word:
                continue
            full_address = number + ' ' +  ten_duong
            full_address_unidecode = unidecode(full_address)
            if number not in deal_s:
                deal_s.append(number)
                sxs = re.search('x(?: |$)|^[x\d\s]+$',ten_duong, re.I) # có x trong tên đường
                if sxs:
                    continue
                ddm = re.search('(?:^|x|\*|\s)\s*\d+m',full_address, re.I)# check mét
                if ddm:
                    continue

                check_co_word = re.search('\D', full_address)
                if not check_co_word:
                    continue
                ten_duong_lower = ten_duong.strip().lower() 
                if ten_duong_lower in ['căn']:
                    continue
                pt = 'MT|Lầu|tỷ|căn|phòng|tấm|PN|WC|mặt|trệt|tầng|sẹc|sẹt|xẹc|xẹt|lửng|lững|trục đường|\dt\s*\dl'
                pt = unidecode(pt)
                is_mt = re.search(pt, full_address_unidecode, re.I)
                if is_mt:
                    continue
                bao_nhieu_met = re.search('\d+m|\dT', number, re.I)
                print ('**bao_nhieu_met**', bao_nhieu_met)
                if bao_nhieu_met:
                    continue
                co_format_sdt = re.search('[\d\W]{6,}|3 Tháng 2|đi |thẳng |\d+(?:tr|t) \dL', full_address)
                if co_format_sdt:
                    continue
                if len(ten_duong) == 1:
                    continue
                index = mat_tien_full_address_possibles.span()[0]
                pre_index = index - 12
                if pre_index < 0:
                    pre_index = 0
                check_hem_string = html[pre_index:index]
                if check_hem_string:
                    is_hem = re.search('hẻm|hxt|đường|bđs|cty|nhà đất|vp|văn phòng|phường|quận', check_hem_string, re.I)
                    if is_hem:
                        continue
                full_adress_list.append((number, full_address))
    return full_adress_list

def detect_mat_tien_address_sum(html):
    #parent function call: _compute_mat_tien_or_trich_dia_chi
    full_adress_list_sum =  []
    number_list_sum = []
    addresses = {
    'html':{'value':html,
        'p':'(?<!cách )(?i:nhà|mt|mặt tiền|số)\s+(\d{1,4}[a-zA-Z]{0,2})[\s,]+(?i:đường)*\s*(?P<ten_duong>(?-i:[A-Z0-9Đ][\w|/]*\s*){1,4})(?:\.|\s|\,|$|<)'
        }, 
    }
    for key,val in addresses.items():
        html = val['value']
        p = val['p']
        if html:
            mat_tien_adress_list = detect_mat_tien_address(html, p)
            if mat_tien_adress_list:
                for number, full_address in mat_tien_adress_list:
                    if number not in number_list_sum:
                        full_adress_list_sum.append(full_address)
                        number_list_sum.append(number)
    mat_tien_address = False                  
    if full_adress_list_sum:
        mat_tien_address = ','.join(full_adress_list_sum)
    return mat_tien_address

def trim_street_name(street_name_may_be):
    #pr: detect_hem_address
    rs = re.sub(',|\.','', street_name_may_be, flags=re.I)
    rs = rs.strip()
    return rs

def detect_hem_address(address):
    #@pr: detect_hem_address_list
    keys_street_has_numbers = ['3/2','30/4','19/5','3/2.','3/2,','23/9']
    pat_247 = '24h*/7|24h*/24|1/500'
    trust_address_result_keys = []
    only_number_trust_address_result_keys = []
    co_date_247_result_keys=[]
    index_before = 0
    while 1:
        address = address[index_before:]
        posible_address_search = re.search('(?P<adress_number>\d+\w{0,2}/\d+\w{0,2}(?:/\d+\w{0,2})*)[\s,]+(?:đường[\s,]+)*(?P<ten_duong>(?:[\w|/]+\s*){1,4})(?:\.|\s|,|$)', address)
        if posible_address_search:
            index_before = posible_address_search.span()[1]
            adress_number = posible_address_search.group('adress_number')
            street_name = posible_address_search.group('ten_duong')
            street_name = trim_street_name(street_name)
            full_adress = adress_number +' ' + street_name
            if adress_number not in only_number_trust_address_result_keys:
                black_list = '23/23 Nguyễn Hữu Tiến|5 Độc Lập'
                black_list_rs = re.search(black_list, address, re.I)
                if black_list_rs:
                    only_number_trust_address_result_keys.append(adress_number)
                    continue
                if adress_number in ['1/2','50/100','100/100']:
                    continue
                rs = re.search(pat_247, adress_number, re.I)
                if rs:
                    co_date_247_result_keys.append(rs.group(0))
                    continue
                if adress_number in keys_street_has_numbers:
                    # street_result_keys.append(adress_number)
                    continue
                is_day = re.search('\d+/\d\d\d\d', adress_number)
                if is_day:
                    continue
                pnwc = re.search('(?:pn|wc|x|50/50)', adress_number, re.I)
                if pnwc:
                    continue
                is_ty_m2 =  re.search('tỷ|tr|m2', full_adress, re.I)
                if is_ty_m2:
                    continue
                
                index = posible_address_search.span()[0]
                before_index = index -20
                if before_index < 0:
                    before_index = 0
                before_string = address[before_index: index]
                is_van_phong = re.search('văn phòng|vp|bđs|nhà đất|[\d\W]{4,}', before_string, re.I)
                if is_van_phong:
                    continue
                trust_address_result_keys.append((adress_number, full_adress))
                only_number_trust_address_result_keys.append(adress_number)
        else:
            break
    return trust_address_result_keys, co_date_247_result_keys

def detect_hem_address_list(address_list):
    #pr: _compute_mat_tien_or_trich_dia_chi
    sum_full_hem_address = [] 
    only_number_address_sum_full_hem_address = [] 
    co_date_247_result_keys_sum = []
    for ad in address_list:
        trust_address_result_keys, co_date_247_result_keys = detect_hem_address(ad)
        co_date_247_result_keys_sum.extend(co_date_247_result_keys)
        for i in trust_address_result_keys:
            number_address = i[0]
            if number_address not in only_number_address_sum_full_hem_address:
                sum_full_hem_address.append(i)
                only_number_address_sum_full_hem_address.append(number_address)
    return sum_full_hem_address, co_date_247_result_keys_sum

def _compute_mat_tien_or_trich_dia_chi(self, html, html_trich_dia_chi, r):#compute
        mat_tien_address = detect_mat_tien_address_sum(html)
        trich_dia_chi = False
        address_list = [html_trich_dia_chi]
        sum_full_hem_address, co_date_247_result_keys_sum = detect_hem_address_list(address_list)
        if sum_full_hem_address:
            trich_dia_chi = ','.join(map(lambda i:i[1], sum_full_hem_address))
        mat_tien_or_trich_dia_chi = mat_tien_address or trich_dia_chi
        is_mat_tien_or_trich_dia_chi ='1' if  bool(mat_tien_or_trich_dia_chi) else '0'
        
        if trich_dia_chi:
            same_address_bds_ids  = self.env['bds.bds'].search([('trich_dia_chi','=ilike',trich_dia_chi),('id','!=',r.id)])
            same_address_bds_ids = [(6,0,same_address_bds_ids.mapped('id'))]
        else:
            same_address_bds_ids = False
        return mat_tien_address, trich_dia_chi, mat_tien_or_trich_dia_chi, is_mat_tien_or_trich_dia_chi, same_address_bds_ids

def _compute_mat_tien_or_trich_dia_chi1(self, html, html_trich_dia_chi):#compute
    mat_tien_address = detect_mat_tien_address_sum(html)
    trich_dia_chi = False
    address_list = [html_trich_dia_chi]
    sum_full_hem_address, co_date_247_result_keys_sum = detect_hem_address_list(address_list)
    if sum_full_hem_address:
        trich_dia_chi = ','.join(map(lambda i:i[1], sum_full_hem_address))
    mat_tien_or_trich_dia_chi = mat_tien_address or trich_dia_chi
    is_mat_tien_or_trich_dia_chi ='1' if  bool(mat_tien_or_trich_dia_chi) else '0'
    return mat_tien_address, trich_dia_chi, mat_tien_or_trich_dia_chi, is_mat_tien_or_trich_dia_chi


def compute_t1l1_detect(html):
    #@pr: _compute_kw_mg
    t1l1_list = []
    pt = '(1t[,\s]*(\d{1,2})l)(?:\W|$)'
    rs = re.search(pt, html, re.I)
    if rs:
        t1l1_list.append(rs.group(1))
    pt = '((\d{1,2})\s*pn)(?:\W|$)'
    rs = re.search(pt, html, re.I)
    if rs:
        t1l1_list.append(rs.group(1))
    pt = '(?:\W|^)(st)(?:\W|$)'
    rs = re.search(pt, html, re.I)
    if rs:
        t1l1_list.append(rs.group(1))
        
    return t1l1_list


def _compute_kw_mg( html):
        found_kw_mgs = []
        pat_247 = '24h*/7|(?<!an ninh )24h*/24|1/500'
        rs = re.search(pat_247, html, re.I)
        kw_co_date = False #1
        if rs:
            found_kw_mgs.append(rs.group(0))
            kw_co_date = rs.group(0)
        nha_dat_kws_cap_1 = 'nhà đất(?! thánh)|uy tín|real|bds|bđs|cần tuyển|tuyển sale|tuyển dụng|bất động sản|bđs|ký gửi|kí gửi|'+\
        '(?<!nova)land(?!mark|abc)|tư vấn|(?:thông tin|sản phẩm) (?:chính xác|thật)|' +\
        'xem nhà miễn phí|(?:hổ|hỗ) trợ miễn phí|khách hàng|' +\
        'hỗ trợ[\w\s]{0,20}pháp lý|hợp.{1,20}đầu tư|csht|tttm|'+\
        'chưa qua đầu tư|cấp 1[,\- ]*2[,\- ]*3|'+\
        'tiện kinh doanh[ ,]{1,2}buôn bán[ ,]{1,2}mở công ty[ ,]{1,2}văn phòng|nợ ngân hàng|hợp tác|thanh lý' 

     
        nha_dat_list_rs = re.findall(nha_dat_kws_cap_1, html, re.I)
        if nha_dat_list_rs:
            found_kw_mgs.extend(nha_dat_list_rs)

        mtg_kws = 'mmg|mqc|mtg|(?-i:MTKD)|(?-i:BTCT)|(?-i:CHDV)|(?-i:DTSD)|(?:.{0,10}cho khách?:.{0,10})|(?:khu vực an ninh|dân trí cao)\W{1,3}(?:khu vực an ninh|dân trí cao)'
        nha_dat_list_rs = re.findall(mtg_kws, html, re.I)
        kw_mg_cap_2 = False #2
        is_kw_mg_cap_2 = False#3
        if nha_dat_list_rs:
            kw_mg_cap_2 = ','.join(nha_dat_list_rs)
            is_kw_mg_cap_2 = True

        break_kw = '(\n✓|\n\*)'
        break_rs = re.findall(break_kw, html, re.I)
        kw_co_special_break = False # 4
        if break_rs:
            len_break_rs = len(break_rs)
            kw_co_special_break = len_break_rs
       
        break_kw = '(\n)'
        break_rs = re.findall(break_kw, html, re.I)
        kw_co_break = False # 5
        if break_rs:
            len_break_rs = len(break_rs)
            kw_co_break = len_break_rs
        number_char = len(html)
        hoa_la_canh_pt = '🏠|💥|✅|👉🏻|⭐️|💵|💰|☎️|⚡|📲|💎|🌹|☎|🌈|🍎|🍏|🏦|📣|🆘|☎️|🤝|👍|👉|' +\
            '🏡|🗽|🎠|🏖|😍|🔥'
        nha_dat_list_rs = re.findall(hoa_la_canh_pt, html, re.I)
        hoa_la_canh = False # 6
        if nha_dat_list_rs:
            hoa_la_canh = len(nha_dat_list_rs)
        t1l1_list = compute_t1l1_detect(html)
        t1l1 = False #7
        if t1l1_list:
            t1l1 = ','.join(t1l1_list)
        kw_mg = False #8
        dd_tin_cua_co = 'no_kw_co_cap_1' # 9
        if found_kw_mgs:
            kw_mg = ','.join(found_kw_mgs)
            dd_tin_cua_co = 'kw_co_cap_1'

        return kw_co_date, kw_mg_cap_2, is_kw_mg_cap_2, kw_co_special_break, kw_co_break,\
                hoa_la_canh, t1l1, kw_mg, dd_tin_cua_co

def str_before_index(index, input_str):
    #@pr: _compute_dd_tin_cua_dau_tu
    pre_index = index - 30
    if pre_index < 0:
        pre_index = 0
    pre_str = input_str[pre_index:index]
    return pre_str

def _compute_dd_tin_cua_dau_tu(html):
        p = '((?<=\W)(?:hoa hồng|hh(?!t)|huê hồng|🌹)\s*(?:cho)*\s*(?:mg|môi giới|mô giới|TG|Trung gian)*\s*(?:\D|\s){0,31}((\d|\.)+\s*(%|triệu|tr))*)(?:\s+|$|<|\.|)'
        rs = re.search(p, html, re.I)
        if not rs:
            p = '((?:phí(?! hh| hoa hồng| huê hồng|\w)|chấp nhận)\s*(?:cho)*\s*(?:mg|môi giới|mô giới|TG|Trung gian)*\s*((\d|\.)+\s*(%|triệu|tr))*)(?:\s+|$|<|\.|)'
            rs = re.search(p, html, re.I)
        kw_hoa_hong, kw_so_tien_hoa_hong, dd_tin_cua_dau_tu = False, False, False
        if rs:
            for i in [1]:
                index = rs.span()[0]
                pre_str = str_before_index(index, html)
                khong_cho_mg = re.search('không|ko', pre_str, re.I)
                if khong_cho_mg:
                    continue
                kw_hoa_hong_tach = rs.group(1)
                kw_hoa_hong_tach = kw_hoa_hong_tach.strip().lower()
                if kw_hoa_hong_tach in  ['phí', 'chấp nhận']:
                    continue
                kw_hoa_hong = kw_hoa_hong_tach
                kw_so_tien_hoa_hong = rs.group(2)
                dd_tin_cua_dau_tu = True
        else:
            rs = re.search('((1)%)', html, re.I)
            if rs:
                kw_hoa_hong = rs.group(1)
                kw_so_tien_hoa_hong = rs.group(2)
                dd_tin_cua_dau_tu = True
        return kw_hoa_hong, kw_so_tien_hoa_hong, dd_tin_cua_dau_tu


def detect_is_mat_tien(html):
    #@pr: _compute_loai_hem_combine
    while 1:
        p = '(?:(?<!2 )mặt tiền|nhà mt|mặt phố)(?! hẻm)'
        rs = re.search(p, html, re.I)
        hxh_str, full_hxh,is_mat_tien = False,False,False
        if rs:
            span0 = rs.span(0)[0]
            pre_index = span0-10
            if pre_index<0:
                pre_index = 0
            pre = html[pre_index:span0]
            gan_sat_cach_pt = 'gần|sát|cách|hai|từ|ra|sau lưng|hai'
            gan_sat_cach_search = re.search(gan_sat_cach_pt,pre, re.I)
            if gan_sat_cach_search:
                before_index = rs.span()[1] + 1
                html = html[before_index:]
                continue
            hxh_str = rs.group(0)
            full_before_index = rs.span(0)[1] + 10
            full_hxh = html[pre_index:full_before_index]
            is_mat_tien = True
            return hxh_str, full_hxh, is_mat_tien
        else:
            return hxh_str, full_hxh, is_mat_tien        


def cach_search(pre):
    #pr: detect_hem_rong()
    gan_sat_cach_pt = 'cách'
    gpxd_search = re.search(gan_sat_cach_pt,pre, re.I)
    return gpxd_search

def previous_of_match(html, rs_group, previous_char_number = 30):
    #pr: detect_hem_rong()
    span0 = rs_group.span(0)[0]
    pre_index = span0-previous_char_number
    pre = html[pre_index:span0]
    return pre
    
def detect_hem_rong(html):
    #@pr: _compute_loai_hem_combine
    while 1:
        pt = '(?<!cách )(?:hẻm|hẽm|đường)\s+(?:trước nhà)*\s*(?:xh|xe hơi|ô tô|xe máy|kia|ba gác|ba gát)*\s*(?:trước nhà)*\s*(?:nhỏ)*\s*(?:rộng)*\s*(?:khoảng|tầm)*\s*(\d+(?:\.|m|mét|,)*\d*)\s*(?:m|mét)*(?:\W|$)'
        rs = re.search(pt, html, re.I)
        if rs:
            pre = previous_of_match(html, rs)
            cach_search_rs = cach_search(pre)
            if cach_search_rs:
                before_index = rs.span(0)[1] + 1
                html = html[before_index:]
                continue
            else:
                hem_rong_char, hem_rong = rs.group(0), rs.group(1)
                hem_rong = re.sub('mét|mét|m|,','.',hem_rong, flags=re.I)
                hem_rong = re.sub('\.+','.',hem_rong)
                hem_rong = float(hem_rong)
                return hem_rong_char, hem_rong
        else:
            return False, False

def detect_hxh(html):
    #@pr:detect_loai_hem
    p = '(?:h|hẻm|hẽm|d|đ|đường)\s{0,1}(?:xh|xe hơi|oto|ô tô)'
    rs = re.search(p, html, re.I)
    hxh_str, full_hxh = False,False
    if rs:
        span0 = rs.span(0)[0]
        pre_index = span0-30
        if pre_index<0:
            pre_index = 0
        pre = html[pre_index:span0]
        gan_sat_cach_pt = 'gần|sát|cách'
        gan_sat_cach_search = re.search(gan_sat_cach_pt,pre, re.I)
        if gan_sat_cach_search:
            return hxh_str, full_hxh
        before_index = span0 + 10
        full_hxh = html[pre_index:before_index]
        hxh_str = rs.group(0)
    return hxh_str, full_hxh

def detect_hxt(html):
    #@pr:detect_loai_hem
    p = '(?:h|hẻm|hẽm|d|đ|đường)\s{0,1}(?:xt|xe (?:tải|tãi))'
    rs = re.search(p, html, re.I)
    hxh_str, full_hxh = False,False
    if rs:
        span0 = rs.span(0)[0]
        pre_index = span0-30
        pre = html[pre_index:span0]
        gan_sat_cach_pt = 'gần|sát|cách'
        gan_sat_cach_search = re.search(gan_sat_cach_pt,pre, re.I)
        if gan_sat_cach_search:
            return hxh_str, full_hxh
        before_index = span0 + 10
        full_hxh = html[pre_index:before_index]
        hxh_str = rs.group(0)
    return hxh_str, full_hxh
    
def detect_hxm(html):
    #@pr:detect_loai_hem
    p = '(?:h|hẻm|hẽm)\s{0,1}(?:xm|xe (?:máy))'
    rs = re.search(p, html, re.I)
    hxh_str, full_hxh = False,False
    if rs:
        span0 = rs.span(0)[0]
        pre_index = span0-30
        pre = html[pre_index:span0]
        gan_sat_cach_pt = 'gần|sát|cách'
        gan_sat_cach_search = re.search(gan_sat_cach_pt,pre, re.I)
        if gan_sat_cach_search:
            return hxh_str, full_hxh
        before_index = span0 + 10
        full_hxh = html[pre_index:before_index]
        hxh_str = rs.group(0)
    return hxh_str, full_hxh
    
def detect_hbg(html):
    #@pr:detect_loai_hem
    p = '(?:h|hẻm|hẽm)\s{0,1}(?:bg|ba (?:gát|gác))'
    rs = re.search(p, html, re.I)
    hxh_str, full_hxh = False,False
    if rs:
        span0 = rs.span(0)[0]
        pre_index = span0-30
        pre = html[pre_index:span0]
        gan_sat_cach_pt = 'gần|sát|cách'
        gan_sat_cach_search = re.search(gan_sat_cach_pt,pre, re.I)
        if gan_sat_cach_search:
            return hxh_str, full_hxh
        before_index = span0 + 10
        full_hxh = html[pre_index:before_index]
        hxh_str = rs.group(0)
    return hxh_str, full_hxh


def detect_loai_hem(html):
    loai_hem_selection = False
    loai_hem, full_loai_hem = detect_hxh(html)
    if loai_hem:
        loai_hem_selection = 'hxh'
    else:
        loai_hem,  full_loai_hem = detect_hxt(html)
        if loai_hem:
            loai_hem_selection = 'hxt'
        else:
            loai_hem,  full_loai_hem = detect_hxm(html)
            if loai_hem:
                loai_hem_selection = 'hxm'
            else:
                loai_hem,  full_loai_hem = detect_hbg(html)
                if loai_hem:
                    loai_hem_selection = 'hbg'
    return full_loai_hem, loai_hem_selection

def _compute_loai_hem_combine(html):
        mat_tien, full_mat_tien, is_mat_tien = detect_is_mat_tien(html)
        hem_rong_char, hem_rong = detect_hem_rong(html)
        full_loai_hem, loai_hem_selection = detect_loai_hem(html)
        loai_hem_combine = loai_hem_selection
        if not loai_hem_selection:
            if is_mat_tien:
                loai_hem_combine = 'mt'
            elif hem_rong:
                if hem_rong > 10:
                    loai_hem_combine = 'mt'
                elif hem_rong >= 6:
                    loai_hem_combine = 'hxt'
                elif hem_rong >= 4:
                    loai_hem_combine = 'hxh'
                elif hem_rong >= 2.5:
                    loai_hem_combine = 'hbg'
                elif hem_rong:
                    loai_hem_combine = 'hxm'
        return mat_tien, full_mat_tien, is_mat_tien,hem_rong_char, hem_rong, full_loai_hem, loai_hem_selection, loai_hem_combine
######################### !compute function ###############




def valid_fetch_list(rs):
    for i in ['public_date', 'public_datetime',  'area_name', 'region_name', 'price', 'gia','mat_tien_or_trich_dia_chi']:
        print ('**%s**'%i)
        filter_rs = list(filter(lambda r: r[i], rs))
        print (len(filter_rs))
        if i =='mat_tien_or_trich_dia_chi':
            for r in filter_rs:
                print ('mat_tien_or_trich_dia_chi', r['link'])
                print ('mat_tien_or_trich_dia_chi', r['mat_tien_or_trich_dia_chi'])



    print ('**not gia**')
    filter_rs = list(filter(lambda r: not r['gia'], rs))
    print (len(filter_rs))

def test_fetch():
    attrs_dict = {}
    site_name = 'chotot'
    site_name = 'muaban'
    site_name = 'cuahangtaphoa'
    site_name = 'batdongsan'
    site_name = 'chotot'
    is_test = True
    is_save_mau = True
    topic_path = False
    topic_link = False
    page_path = False
    page_link = False

    attrs_dict.update({'is_test':is_test, 'site_name': site_name, 'is_save_mau':is_save_mau})
    if site_name == 'chotot':
        # topic_link = 'https://gateway.chotot.com/v1/public/ad-listing/73970343'
        # topic_link = 'https://gateway.chotot.com/v1/public/ad-listing/76138717'
        # topic_path = 'mau/topic_chotot_50_50'
        more_dict = { 'url':'https://gateway.chotot.com/v1/public/ad-listing?cg=1000&limit=20&st=s,k',
        'begin_page':1,  'end_page':5 }
    elif site_name =='batdongsan':
        more_dict = { 'url':'https://batdongsan.com.vn/nha-dat-ban',
        'begin_page':500,  'end_page':500,  'topic_path':'mau/file_topic_bug_theo_y_muon_batdongsan'}
        # more_dict = {'is_test':True, 'site_name': 'batdongsan', 'page_path':'mau/bds_page_loai_2',
        # 'st_is_request_topic':False, }
        more_dict = {'url':'https://batdongsan.com.vn/nha-dat-ban',
        'begin_page':500,  'end_page':500, }# 'is_save_and_raise_in_topic':True
    
        # more_dict = {'is_test':True, 'site_name': 'batdongsan', 'url':'https://batdongsan.com.vn/nha-dat-ban',
        # 'begin_page':500,  'end_page':500,  'topic_link':'https://batdongsan.com.vn/ban-can-ho-chung-cu-duong-ho-tung-mau-phuong-phu-dien-prj-goldmark-city/-bay-gio-hoac-khong-bao-gio-mua-160m2-cho-gia-dinh-da-the-he-tang-ngay-hon-600-000-000-pr26721510'
        # }
    elif site_name =='muaban':
        more_dict = { 'url':'https://muaban.net/ban-nha-ho-chi-minh-l59-c32?cp=14' }
    elif site_name =='cuahangtaphoa':
        more_dict = { 'url':'http://www.cuahangtaphoa.com/page-6-cua-hang-tap-hoa.html' }

    attrs_dict.update(more_dict)
    attrs_dict['topic_path']=topic_path
    attrs_dict['topic_link']=topic_link
    attrs_dict['page_path']=page_path
    attrs_dict['page_link']=page_link

    main_fetch = MainFetchCommon(attrs_dict = attrs_dict)
    fetch_list = main_fetch.fetch_a_url_id(False)
    print ('***fetch_list***', fetch_list)
    print ('len(fetch_list)',len(fetch_list))
    if site_name in ['chotot','batdongsan','cuahangtaphoa']:
        valid_fetch_list(fetch_list)

def test_trich_dia_chi():
    html = 'nhà 1tr 2L là không được'
    rs = _compute_mat_tien_or_trich_dia_chi1 (False, html, html)
    print (rs)

if __name__ == '__main__':
    loai_test = 'trich_dia_chi'
    loai_test = 'test_fetch'
    if loai_test == 'trich_dia_chi':
        test_trich_dia_chi()
    else:
        test_fetch()
    

    
    





