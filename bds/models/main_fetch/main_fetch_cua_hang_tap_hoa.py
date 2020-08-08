# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons.bds.models.bds_tools  import  request_html
import json
import math
from odoo.addons.bds.models.fetch_site.fetch_bds_com_vn  import get_last_page_from_bdsvn_website
from odoo.addons.bds.models.fetch_site.fetch_muaban_obj  import MuabanObject
from odoo.addons.bds.models.fetch_site.fetch_chotot_obj  import ChototGetTopic, create_cho_tot_page_link, convert_chotot_price, convert_chotot_date_to_datetime


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
from odoo.addons.bds.models.bds_tools  import get_or_create_user_and_posternamelines, g_or_c_ss
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


    def get_main_obj(self):
        rs = super().get_main_obj()
        if self.site_name =='cuahangtaphoa' or getattr(self,'model_name',None)=='tap.hoa':
            return self.env['tap.hoa']
        return rs


    def get_last_page_number(self, url_id):
        if self.site_name =='cuahangtaphoa':
            if url_id.web_last_page_number:
                return url_id.web_last_page_number
            return 300
        return super(MuabanFetch, self).get_last_page_number(url_id)

    def get_dia_chi(self, topic_soups, dia_chi_str= 'Địa chỉ:'):
        try:
            ngay_cap_soup = topic_soups.select("li:contains('%s')"%dia_chi_str)[0]
            ngay_cap = ngay_cap_soup.get_text().split(':')[1].strip()
        except IndexError:
            ngay_cap = None
        return ngay_cap




    def parse_html_topic (self, topic_html_or_json, url_id):
        
        if self.site_name =='cuahangtaphoa' or getattr(self,'model_name',None)=='tap.hoa':
            topic_dict = {}
            # return topic_dict
            a_page_html_soup = BeautifulSoup(topic_html_or_json, 'html.parser')
            # quan_huyen = a_page_html_soup.select('ul.breadcrumb > li')
            # tinh = quan_huyen[1].get_text()
            # quan = quan_huyen[2].get_text()
            # country_obj = self.env['res.country'].search([('name','ilike','viet')])[0]
            # tinh_obj = g_or_c_ss(self.sudo().env['res.country.state'],
            #      {'name': tinh}, {'country_id':country_obj.id, 'code':tinh}, is_up_date=False)
            # quan_obj = g_or_c_ss(self.sudo().env['res.country.district'], {'name': quan, 
            #     'state_id':  tinh_obj.id})
            # topic_dict['quan_id'] = quan_obj.id
            topic_soups = a_page_html_soup.select('div.item-page')[0]
            # mobile = topic_soups.select('font[color="red"]')
            # mobile = mobile[0].get_text()
            # topic_dict['html'] = topic_soups.get_text()

            # ngay_cap_soup = topic_soups.select("li:contains('Ngày cấp')")[0]
            # ngay_cap = ngay_cap_soup.get_text().split(':')[1].strip()
            # format_str = '%d/%m/%Y' # The format
            # datetime_obj = datetime.datetime.strptime(ngay_cap, format_str)
            # topic_dict['public_date'] = datetime_obj
            
            
            # topic_dict['address'] = self.get_dia_chi(topic_soups, dia_chi_str= 'Địa chỉ:')
            # topic_dict['name_of_poster'] = self.get_dia_chi(topic_soups, dia_chi_str= 'Chủ sở hữu: ')
            try:
                nghanh_nghe_soup = topic_soups.select("li:contains('Ngành nghề chính: ')")[0]
                nghanh_nghe = nghanh_nghe_soup.get_text().split(':')[1]
                nghanh_nghe = nghanh_nghe.replace('./.','').strip()
            except IndexError:
                nghanh_nghe = False
            
            topic_dict['nganh_nghe_kinh_doanh'] = nghanh_nghe
            # topic_dict['link'] = link
            # user = get_or_create_user_and_posternamelines(self.env, mobile, mobile, self.siteleech_id_id)
            # topic_dict['poster_id'] = user.id
            # topic_dict['title'] = 'tạp hóa của: %s'%mobile
            return topic_dict
        return super().parse_html_topic(topic_html_or_json, url_id)


    def create_page_link(self, format_page_url, page_int):
        page_url = super(MuabanFetch, self).create_page_link(format_page_url, page_int)
        
        if self.site_name == 'cuahangtaphoa':
            repl = 'page-%s-danh-sach'%page_int
            page_url =  re.sub('danh-sach', repl, format_page_url)
            page_url = re.sub('/$','.aspx',page_url)
        return page_url


    def request_parse_html_topic(self, link, url_id):
        topic_dict = super().request_parse_html_topic(link, url_id)
        if self.site_name =='cuahangtaphoa' or self.model_name =='tap.hoa':
            topic_dict['is_full_topic'] = True
        return topic_dict


    # def th_bds_create_dict_from_page_dict_and_url_id(self, topic_data_from_page, url_id, link, is_topic_link_or_topic_path):
    #     if self.site_name =='cuahangtaphoa' or getattr(self,'model_name',None)=='tap.hoa':
    #         return {}
    #     return super().th_bds_create_dict_from_page_dict_and_url_id(topic_data_from_page, url_id, link, is_topic_link_or_topic_path)


    

    def get_st_is_pre_topic_dict_from_page_dict_and_url_id(self, fetch_item_id):
        if self.site_name =='cuahangtaphoa' or fetch_item_id.model_id.name =='tap.hoa':
            return False
        return super().get_st_is_pre_topic_dict_from_page_dict_and_url_id(fetch_item_id)


    # def get_setting_tp_is_request_update(self, fetch_item_id):
    #     if self.site_name =='cuahangtaphoa' or fetch_item_id.model_id.name =='tap.hoa':
    #         # if not fetch_item_id.not_request_topic or fetch_item_id.model_id:
    #         if fetch_item_id.model_id:
    #             return True
    #     return super().get_setting_tp_is_request_update(fetch_item_id)


    def get_st_is_compare_price_or_public_date(self, fetch_item_id):

        if self.site_name =='cuahangtaphoa' or fetch_item_id.model_id.name =='tap.hoa':
            return False
        return super().get_st_is_compare_price_or_public_date(fetch_item_id)


    # def request_write(self, fetch_item_id, link, url_id):
    #     if self.site_name =='cuahangtaphoa' or getattr(self,'model_name',None)=='tap.hoa':
    #         if not fetch_item_id.not_request_topic or fetch_item_id.model_id:
    #             rq_topic_dict = self.request_parse_html_topic(link, url_id)
    #             if rq_topic_dict:
    #                 rq_topic_dict['is_full_topic'] =  True
    #             return rq_topic_dict
    #     return super().request_write(fetch_item_id, link, url_id)

  

    # def copy_page_data_to_rq_topic(self, topic_data_from_page):
    #     filtered_page_topic_dict = super().copy_page_data_to_rq_topic(topic_data_from_page)
    #     if self.site_name =='cuahangtaphoa':
    #         filtered_page_topic_dict = topic_data_from_page
    #     return filtered_page_topic_dict

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
                        # print ('***phone***', phone)
                        # topic_data_from_page['phone'] = phone
                        # user = get_or_create_user_and_posternamelines(self.env, phone, phone, self.siteleech_id_id)
                        # topic_data_from_page['poster_id'] = user.id
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
                # print ('***ngay_thanh_lap**', ngay_thanh_lap)
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
                # country_obj = self.env['res.country'].search([('name','ilike','viet')])[0]
                # tinh_obj = g_or_c_ss(self.sudo().env['res.country.state'],
                #  {'name': tinh}, {'country_id':country_obj.id, 'code':tinh}, is_up_date=False)
                # quan_obj = g_or_c_ss(self.sudo().env['res.country.district'], {'name': quan, 
                #     'state_id':  tinh_obj.id})
                # topic_data_from_page['quan_id'] = quan_obj.id
                topic_data_from_page['tinh']=tinh
                topic_data_from_page['quan']=quan
                topic_data_from_page['phuong']=phuong
                topic_data_from_page['duong']=duong
                # topic_data_from_page['phuong']=phuong
                topic_data_from_page['link'] = href
                topic_data_from_page['list_id'] = href
                topic_data_from_page['mst'] = mst
                topic_data_from_page['address'] = dia_chi
                topic_data_from_page['title'] = title
                topic_data_from_page['html'] = ''
                topic_data_from_pages_of_a_page.append(topic_data_from_page)
        # print (topic_data_from_pages_of_a_page)
        # print (aaa)
        return topic_data_from_pages_of_a_page

