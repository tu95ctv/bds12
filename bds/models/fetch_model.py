# -*- coding: utf-8 -*-
from odoo import models, fields, api
# from odoo.addons.bds.models.fetch import fetch, fetch_all_url
import psycopg2
import threading
import re
from odoo.exceptions import UserError
import datetime

#import thư viện lấy từ file fetch.py qua
from odoo.exceptions import UserError
from odoo import models,fields
from odoo.addons.bds.models.bds_tools  import  request_html,g_or_c_ss, get_or_create_user_and_posternamelines, MyError
from odoo.addons.bds.models.fetch_site.fetch_bds_com_vn  import get_bds_dict_in_topic, get_last_page_from_bdsvn_website, convert_gia_from_string_to_float
from odoo.addons.bds.models.fetch_site.fetch_chotot  import  get_topic_chotot, create_cho_tot_page_link, local_a_native_time, convert_chotot_price, convert_chotot_date_to_datetime, gmt_7_a_native_time
from odoo.addons.bds.models.fetch_site.fetch_muaban  import get_muaban_vals_one_topic
from bs4 import BeautifulSoup
import datetime
import re
from unidecode import unidecode
import json
import math
from copy import deepcopy
import pytz

#!import thư viện lấy từ file fetch.py qua

def convert_native_utc_datetime_to_gmt_7(utc_datetime_inputs):
        local = pytz.timezone('Etc/GMT-7')
        utc_tz =pytz.utc
        gio_bat_dau_utc_native = utc_datetime_inputs#fields.Datetime.from_string(self.gio_bat_dau)
        gio_bat_dau_utc = utc_tz.localize(gio_bat_dau_utc_native, is_dst=None)
        gio_bat_dau_vn = gio_bat_dau_utc.astimezone (local)
        return gio_bat_dau_vn

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

#lam gon lai ngay 23/02
class Fetch(models.Model):
    _name = 'bds.fetch'
    name = fields.Char(compute='_compute_name', store=True)
    url_id = fields.Many2one('bds.url')
    url_ids = fields.Many2many('bds.url')
    last_fetched_url_id = fields.Many2one('bds.url')#>0
    is_for_first = fields.Selection([('1','1'),('2','2')])

    @api.depends('url_ids')
    def _compute_name(self):
        for r in self:
            if r.url_ids:
                r.name = ','.join(r.url_ids.mapped('description'))

    @api.multi
    def set_0(self):
        self.url_ids.write({'current_page':0})
   
   # làm gọn lại ngày 23/02
    def fetch (self):
        url_ids = self.url_ids.ids
        if not self.last_fetched_url_id.id:
            new_index = 0
        else:
            try:
                index_of_last_fetched_url_id = url_ids.index(self.last_fetched_url_id.id)
                new_index =  index_of_last_fetched_url_id + 1
            except ValueError:
                new_index = 0
            if new_index == len(url_ids):
                new_index = 0
        url_id = self.url_ids[new_index]
        try:
            self.fetch_a_url_id (url_id)
        except MyError as e:
            self.env['bds.error'].create({'name':str(e),'des':e.url})


    def fetch_all_url(self):
        url_ids = self.url_ids
        for url_id in url_ids:
            self.fetch_a_url_id (url_id)
        
    def fetch_a_url_id (self, url_id):
        end_page_number_in_once_fetch, page_lists, begin, so_page =  self.gen_page_number_list(url_id) 
        begin_time = datetime.datetime.now()
        number_notice_dict = {
            'page_int':0,
            'curent_link':u'0/0',
            'link_number' : 0,
            'update_link_number' : 0,
            'create_link_number' : 0,
            'existing_link_number' : 0,
            'begin_page':begin,
            'so_page':so_page,
            'page_lists':page_lists,
            'length_link_per_curent_page':0,
            'topic_index':0,
            }
        page_index = 0
        for page_int in page_lists:
            page_index +=1
            number_notice_dict['page_int'] = page_int
            number_notice_dict['page_index'] = page_index
            self.page_handle( page_int, url_id, number_notice_dict)
    
        self.last_fetched_url_id = url_id.id
        if self.is_for_first=='2':
            current_page_field_name = 'current_page_for_first'
        else:
            current_page_field_name = 'current_page'
        interval = (datetime.datetime.now() - begin_time).total_seconds()
        url_id.interval = interval
        url_id.write({current_page_field_name: end_page_number_in_once_fetch,
                    'create_link_number': number_notice_dict['create_link_number'],
                    'update_link_number': number_notice_dict["update_link_number"],
                    'link_number': number_notice_dict["link_number"],
                    'existing_link_number': number_notice_dict["existing_link_number"],
                    })
        return None

    def gen_page_number_list(self, url_id ): 
        '''return end_page_number_in_once_fetch, page_lists, begin, number_of_pages
        '''
        url_id_site_leech_name  = url_id.siteleech_id.name

        if self.is_for_first=='2':
            current_page_or_current_page_for_first = 'current_page_for_first'
        else:
            current_page_or_current_page_for_first = 'current_page'
        current_page = getattr(url_id, current_page_or_current_page_for_first)
        
        if url_id_site_leech_name ==  'batdongsan':
            web_last_page_number =  get_last_page_from_bdsvn_website(url_id.url)
        elif url_id_site_leech_name=='chotot':
            page_1_url = create_cho_tot_page_link(url_id.url, 1)
            html = request_html(page_1_url)
            html = json.loads(html)
            total = int(html["total"])
            web_last_page_number = int(math.ceil(total/20.0))
        elif url_id_site_leech_name=='muaban':
            web_last_page_number = 100
        if   url_id.set_leech_max_page and  url_id.set_leech_max_page < web_last_page_number:
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

    def page_handle(self, page_int, url_id, number_notice_dict):
        number_notice_dict['page_int'] = page_int
        topic_data_from_pages_of_a_page = []
        #topic_data_from_pages_of_a_page = [{'ad_id': 99350273, 'list_id': 69165465, 'list_time': 1583592684170, 'date': 'hôm qua', 'account_id': 13211589, 'account_oid': '547621fc551409
        #
        format_page_url = url_id.url
        siteleech_id = url_id.siteleech_id
        allow_write_public_datetime = True # depend site, if muaban , it = False if page_int >2
        
        if siteleech_id.name=='batdongsan':
            url = format_page_url + '/' + 'p' +str(page_int)
            html = request_html(url)
            soup = BeautifulSoup(html, 'html.parser')
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

        elif siteleech_id.name =='chotot':
            url = create_cho_tot_page_link(format_page_url, page_int)
            json_a_page = request_html(url)
            json_a_page = json.loads(json_a_page)
            topic_data_from_pages_of_a_page_origin = json_a_page['ads']
            for topic_data_from_page_cho_tot in topic_data_from_pages_of_a_page_origin:
                topic_data_from_page = deepcopy (topic_data_from_page_cho_tot)
                gia, trieu_gia = convert_chotot_price(topic_data_from_page)#topic_data_from_page['price']
                topic_data_from_page ['gia'] = gia
                date = topic_data_from_page['date']
                naitive_dt = convert_chotot_date_to_datetime(date)
                topic_data_from_page ['public_datetime'] = naitive_dt
                topic_data_from_pages_of_a_page.append(topic_data_from_page)

        elif siteleech_id.name =='muaban':
            if page_int > 2:
                allow_write_public_datetime = False
            page_url =  re.sub('\?cp=(\d*)', '?cp=%s'%page_int, format_page_url)
            a_page_html = request_html(page_url)
            a_page_html_soup = BeautifulSoup(a_page_html, 'html.parser')
            # title_and_icons = a_page_html_soup.select('div.mbn-box-list-content')
            title_and_icons = a_page_html_soup.select('div.list-item-container')
            if not title_and_icons:
                raise UserError('Không có topic nào từ page của muaban')
            for title_and_icon in title_and_icons:
                topic_data_from_page = {}
                print ('***title_and_icon***', title_and_icon)
              
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
        print ('***topic_data_from_pages_of_a_page', len(topic_data_from_pages_of_a_page))
        number_notice_dict['curent_page'] = page_int 
        number_notice_dict['length_link_per_previous_page']  = number_notice_dict.get('length_link_per_curent_page', None)
        number_notice_dict['length_link_per_curent_page'] = len(topic_data_from_pages_of_a_page)
        topic_index = 0
        for topic_data_from_page in topic_data_from_pages_of_a_page:
            topic_index +=1
            number_notice_dict['topic_index'] = topic_index
            if  siteleech_id.name =='chotot':
                link  = 'https://gateway.chotot.com/v1/public/ad-listing/' + str(topic_data_from_page['list_id'])
            elif 'batdongsan' in siteleech_id.name:
                link  = 'https://batdongsan.com.vn' +  topic_data_from_page['list_id']
            else:
                link = topic_data_from_page['list_id']
                print ('link', link)
            self.deal_a_topic(link, number_notice_dict, url_id, topic_data_from_page=topic_data_from_page, allow_write_public_datetime=allow_write_public_datetime)

    
            
            
    def deal_a_topic(self, link, number_notice_dict, url_id, topic_data_from_page={}, allow_write_public_datetime=None):
        print ('link trong deal_a_topic', link)
        update_dict = {}
        public_datetime = topic_data_from_page['public_datetime'] # naitive datetime
        gmt7_public_datetime = convert_native_utc_datetime_to_gmt_7(public_datetime)
        public_date  = gmt7_public_datetime.date()
        search_link_obj= self.env['bds.bds'].search([('link','=',link)])
        if search_link_obj:
            number_notice_dict["existing_link_number"] = number_notice_dict["existing_link_number"] + 1
            public_date_cu  = fields.Date.from_string(search_link_obj.public_date)
            if allow_write_public_datetime and  public_date != public_date_cu and public_date_cu and public_date:
                diff_public_date = (public_date - public_date_cu).days
                update_dict.update({'public_date':public_date})
                update_dict.update({'ngay_update_gia':datetime.datetime.now(),'diff_public_date':diff_public_date, 'public_date':public_date, 'publicdate_ids':[(0,False,{'diff_public_date':diff_public_date,'public_date':public_date,'public_date_cu':public_date_cu})]})
            
            self.request_topic(link, update_dict, url_id, topic_data_from_page)
            if update_dict:
                print (u'___________Update giá topic_index %s/%s- page_int %s - page_index %s/so_page %s'%(number_notice_dict['topic_index'],number_notice_dict['length_link_per_curent_page'],
                                                                            number_notice_dict['page_int'], number_notice_dict['page_index'],number_notice_dict['so_page']))
                search_link_obj.write(update_dict)
                number_notice_dict['update_link_number'] = number_notice_dict['update_link_number'] + 1
        else:
            write_dict = {}
            write_dict.update({'public_date':public_date, 'public_datetime':public_datetime, 'url_id': url_id.id })
            print (u'+++++++++Create topic_index %s/%s- page_int %s - page_index %s/so_page %s'%(number_notice_dict['topic_index'],number_notice_dict['length_link_per_curent_page'],
                                                                            number_notice_dict['page_int'], number_notice_dict['page_index'],number_notice_dict['so_page']))
            # lấy dữ liệu 1 topic về từ link
            self.request_topic(link, write_dict, url_id, topic_data_from_page)
            write_dict['link'] = link
            write_dict.update({'url_ids':[(4, url_id.id)]})
            write_dict['cate'] = url_id.cate
            # tạo 1 object bds
            self.env['bds.bds'].create(write_dict) 
            number_notice_dict['create_link_number'] = number_notice_dict['create_link_number'] + 1    
        link_number = number_notice_dict.get("link_number", 0) + 1
        number_notice_dict["link_number"] = link_number

    def request_topic (self, link, write_dict, url_id, topic_data_from_page):
        topic_html_or_json = request_html(link)
        # print ('***topic_data_from_page***', topic_data_from_page)
        # print ('***topic_html_or_json***', topic_html_or_json)
        # print (a)
        siteleech_id = url_id.siteleech_id
        if siteleech_id.name =='chotot':
            topic_html_or_json = json.loads(topic_html_or_json)

        if siteleech_id.name =='batdongsan':    
            get_bds_dict_in_topic(self, write_dict, topic_html_or_json, siteleech_id)
            write_dict['thumb'] = topic_data_from_page.get('thumb',False)

        elif siteleech_id.name =='chotot':
            get_topic_chotot(self, write_dict, topic_html_or_json, siteleech_id)
            write_dict['thumb'] = topic_data_from_page.get('image',False)
            moi_gioi_hay_chinh_chu = topic_data_from_page.get('company_ad',False)
            if moi_gioi_hay_chinh_chu:
                moi_gioi_hay_chinh_chu = 'moi_gioi'
            else:
                moi_gioi_hay_chinh_chu = 'chinh_chu'
            write_dict['moi_gioi_hay_chinh_chu'] = moi_gioi_hay_chinh_chu

        elif siteleech_id.name =='muaban':
            get_muaban_vals_one_topic(self, write_dict, topic_html_or_json, siteleech_id)
            write_dict['area'] = topic_data_from_page.get('area',False)
            write_dict['thumb'] = topic_data_from_page.get('thumb','ahahah')
