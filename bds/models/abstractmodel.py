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


class ChototMainFetch(models.AbstractModel):
    _name = 'abstract.main.fetch'

    def get_last_page_number(self, url_id):
        if self.site_name =='chotot':
            page_1st_url = create_cho_tot_page_link(url_id.url, 1)
            html = request_html(page_1st_url)
            html = json.loads(html)
            total = int(html["total"])
            web_last_page_number = int(math.ceil(total/20.0))
            return web_last_page_number


    def gen_page_number_list(self, url_id ): 
        is_current_page_2 = getattr(self, 'is_current_page_2', False)
        if is_current_page_2:
            current_page_field_name = 'current_page_2'
        else:
            current_page_field_name = 'current_page'
        self.current_page_field_name = current_page_field_name
        
        current_page = getattr(url_id, current_page_field_name)
        set_leech_max_page = getattr(self,'max_page',0) or url_id.set_leech_max_page
        
        web_last_page_number =  self.get_last_page_number(url_id)


        if set_leech_max_page and  set_leech_max_page < web_last_page_number:
            max_page =  set_leech_max_page
        else:
            max_page = web_last_page_number
        # if url_id.siteleech_id.name !='muaban':
        #     url_id.web_last_page_number = web_last_page_number
        # else:
            # if url_id.web_last_page_number == False:
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
        
        if self.site_name == 'chotot':
            page_url = self.create_page_link(format_page_url, page_int)
            html_page = request_html(page_url)
            json_a_page = json.loads(html_page)
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
            topic_dict = ChototGetTopic(self.env).get_topic(topic_html_or_json, self.siteleech_id_id)
            return topic_dict

    def copy_page_data_to_rq_topic(self, topic_data_from_page):
        copy_topic_dict = {}
        if self.site_name =='chotot':
            copy_topic_dict['thumb'] = topic_data_from_page.get('image',False)
            copy_topic_dict['chotot_moi_gioi_hay_chinh_chu'] = 'moi_gioi' if topic_data_from_page.get('company_ad',False) else 'chinh_chu'
            if topic_data_from_page.get('category_name'):
                copy_topic_dict['loai_nha'] =  topic_data_from_page.get('category_name')       
        return copy_topic_dict

    # MỚI THÊM NGÀY 11/04
    def fetch_a_url_id (self, url_id):
        self.site_name = url_id.siteleech_id.name
        self.siteleech_id_id = url_id.siteleech_id.id
        if self.site_name=='muaban':
            self.allow_write_public_datetime = False
        else:
            self.allow_write_public_datetime = True

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

            try:
                self.page_handle( page_int, url_id, number_notice_dict)
            except FetchError as e:
                self.env['bds.error'].create({'name':str(e),'des':str(e)})

    
        self.last_fetched_url_id = url_id.id
        interval = (datetime.datetime.now() - begin_time).total_seconds()
        url_id.interval = interval
        url_id.write({self.current_page_field_name: end_page_number_in_once_fetch,
                    'create_link_number': number_notice_dict['create_link_number'],
                    'update_link_number': number_notice_dict["update_link_number"],
                    'link_number': number_notice_dict["link_number"],
                    'existing_link_number': number_notice_dict["existing_link_number"],
                    })
        return None


    

    def page_handle(self, page_int, url_id, number_notice_dict):
        number_notice_dict['page_int'] = page_int
        format_page_url = url_id.url  
        topic_data_from_pages_of_a_page = self.fetch_topics_info_for_page_handle(page_int, format_page_url)
        number_notice_dict['curent_page'] = page_int 
        number_notice_dict['length_link_per_previous_page']  = number_notice_dict.get('length_link_per_curent_page', None)
        number_notice_dict['length_link_per_curent_page'] = len(topic_data_from_pages_of_a_page)
        topic_index = 0
        for topic_data_from_page in topic_data_from_pages_of_a_page:
            topic_index +=1
            number_notice_dict['topic_index'] = topic_index
            list_id = topic_data_from_page['list_id']
            link = self.make_topic_link_from_list_id(list_id)
            try:
                self.deal_a_topic(link, number_notice_dict, url_id, topic_data_from_page=topic_data_from_page)
            except FetchError as e:
                self.env['bds.error'].create({'name':str(e),'des':str(e)})
            except Exception as e:
                if url_id.siteleech_id.name == 'batdongsan':
                    self.env['bds.error'].create({'name':str(e),'des':str(e)})
                else:
                    raise


    def deal_a_topic(self, link, number_notice_dict, url_id, topic_data_from_page={}):
        # print (u'~~~~~~~~dealtopic_index %s/%s- page_int %s - page_index %s/so_page %s'
        #             %(number_notice_dict['topic_index'],number_notice_dict['length_link_per_curent_page'],
        #             number_notice_dict['page_int'], number_notice_dict['page_index'],number_notice_dict['so_page']))
        update_dict = {}
        public_datetime = topic_data_from_page['public_datetime'] # naitive datetime
        now = datetime.datetime.now()
        
        gmt7_public_datetime = convert_native_utc_datetime_to_gmt_7(public_datetime)
        public_date  = gmt7_public_datetime.date()
        search_bds_obj= self.env['bds.bds'].search([('link','=',link)])
        
        if search_bds_obj:
            number_notice_dict["existing_link_number"] = number_notice_dict["existing_link_number"] + 1
            diff_day_public_from_now =  (now - public_datetime).days
            if diff_day_public_from_now==0:
                
                public_datetime_cu  = fields.Datetime.from_string(search_bds_obj.public_datetime)
                diff_public_datetime_in_hours = int((public_datetime - public_datetime_cu + timedelta(hours=1)).seconds/3600)
                if diff_public_datetime_in_hours > 2 :
                    public_date_cu  = fields.Date.from_string(search_bds_obj.public_date)
                    diff_public_date = (public_date - public_date_cu).days
                    update_dict.update({
                        'public_datetime': public_datetime, 
                        'public_datetime_cu':public_datetime_cu,
                        'diff_public_datetime':diff_public_datetime_in_hours,
                        'public_date':public_date, 
                        'public_date_cu':public_date_cu,
                        'diff_public_date':diff_public_date, 
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
                update_dict.update({
                    'ngay_update_gia':datetime.datetime.now(),
                    'diff_gia':diff_gia,
                    'gialines_ids':[(0,False,{'gia':gia, 'gia_cu':gia_cu, 'diff_gia':diff_gia})]
                    })


            if update_dict:
                # print (u'-----------Update gia topic_index %s/%s- page_int %s - page_index %s/so_page %s'
                #     %(number_notice_dict['topic_index'],number_notice_dict['length_link_per_curent_page'],
                #     number_notice_dict['page_int'], number_notice_dict['page_index'],number_notice_dict['so_page']))
                search_bds_obj.write(update_dict)
                number_notice_dict['update_link_number'] = number_notice_dict['update_link_number'] + 1
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
            number_notice_dict['create_link_number'] = number_notice_dict['create_link_number'] + 1    
        
        link_number = number_notice_dict.get("link_number", 0) + 1
        number_notice_dict["link_number"] = link_number


class MuabanFetch(models.AbstractModel):
    _inherit = 'abstract.main.fetch'

    def save_to_disk(self, ct, name_file ):
        path = os.path.dirname(os.path.abspath(__file__))
        f = open(os.path.join(path,'%s.html'%name_file), 'w')
        f.write(ct)
        f.close()

    def get_last_page_number(self, url_id):
        if self.site_name =='muaban':
            return 300
        return super(MuabanFetch, self).get_last_page_number(url_id)
        
    def request_topic (self, link, url_id):
        topic_dict = super(MuabanFetch, self).request_topic(link, url_id)
        if self.site_name =='muaban':
            topic_html_or_json = request_html(link)
            # path = os.path.dirname(os.path.abspath(__file__))
            # f = open(os.path.join(path,'muaban.html'), 'w')
            # f.write(topic_html_or_json)
            # f.close()
            topic_dict = MuabanObject(self.env).get_topic(topic_html_or_json, self.siteleech_id_id)
        return topic_dict

    def copy_page_data_to_rq_topic(self, topic_data_from_page):
        copy_topic_dict = super(MuabanFetch, self).copy_page_data_to_rq_topic(topic_data_from_page)
        if self.site_name =='muaban':
            copy_topic_dict['area'] = topic_data_from_page.get('area',False)
            copy_topic_dict['thumb'] = topic_data_from_page.get('thumb',False)
        return copy_topic_dict

    def create_page_link(self, format_page_url, page_int):
        page_url = super(MuabanFetch, self).create_page_link(format_page_url, page_int)
        repl = '?cp=%s'%page_int
        if self.site_name == 'muaban':
            if 'cp=' in format_page_url:
                page_url =  re.sub('\?cp=(\d*)', repl, format_page_url)
            else:
                page_url = format_page_url +  '?' + repl

            
        return page_url

    def fetch_topics_info_for_page_handle(self, page_int, format_page_url):
        topic_data_from_pages_of_a_page = super(MuabanFetch, self).fetch_topics_info_for_page_handle(page_int, format_page_url)
        if self.site_name == 'muaban':
            page_url = self.create_page_link(format_page_url, page_int)
            html_page = request_html(page_url)
            a_page_html_soup = BeautifulSoup(html_page, 'html.parser')
            title_and_icons = a_page_html_soup.select('div.list-item-container')
            if not title_and_icons:
                raise UserError('Không có topic nào từ page của muaban')
            for title_and_icon in title_and_icons:
                # self.save_to_disk(str(title_and_icon),'muaban_item')
                topic_data_from_page = {}
                image_soups = title_and_icon.select("a.list-item__link")
                image_soups = image_soups[0]
                href = image_soups['href']
                img = image_soups.select('img')[0]
                src_img = img.get('data-src',False)
                topic_data_from_page['list_id'] = href
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
                    try:
                        gia = convert_muaban_string_gia_to_float(gia)
                    except:
                        gia = 0
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
    _inherit = 'abstract.main.fetch'

    def get_last_page_number(self, url_id):
        if self.site_name =='batdongsan':
            return get_last_page_from_bdsvn_website(url_id)
        return super(BDSFetch, self).get_last_page_number(url_id)
    
    
    def request_topic (self, link, url_id):
        topic_dict = super(BDSFetch, self).request_topic(link, url_id)
        if self.site_name =='batdongsan':
            topic_html_or_json = request_html(link)
            topic_dict = get_bds_dict_in_topic(self,{}, topic_html_or_json, self.siteleech_id_id)
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
            page_url = self.create_page_link(format_page_url, page_int)
            html_page = request_html(page_url)
            soup = BeautifulSoup(html_page, 'html.parser')
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
                # print ('***topic_data_from_page***', topic_data_from_page)
                date_dang = title_and_icon.select('span.uptime')
                date_dang = date_dang[0].get_text().replace('\n','')
                date_dang = date_dang[-10:]
                public_datetime = datetime.datetime.strptime(date_dang,"%d/%m/%Y")
                topic_data_from_page['public_datetime'] = public_datetime
                topic_data_from_page['thumb'] = icon_soup[0]['src']
                topic_data_from_pages_of_a_page.append(topic_data_from_page)
        return topic_data_from_pages_of_a_page





# class Fetch(models.AbstracModeltModel):
#     _name = 'abstract.main.fetch'

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
