# -*- coding: utf-8 -*-
from odoo import models, fields, api
# from odoo.addons.bds.models.fetch import fetch, fetch_all_url
import psycopg2
import threading
import re
from odoo.exceptions import UserError
from odoo import models,fields
from odoo.addons.bds.models.bds_tools  import  request_html, g_or_c_ss, get_or_create_user_and_posternamelines, FetchError

from unidecode import unidecode
import json
import math
import pytz
import datetime

def convert_native_utc_datetime_to_gmt_7(utc_datetime_inputs):
        local = pytz.timezone('Etc/GMT-7')
        utc_tz =pytz.utc
        gio_bat_dau_utc_native = utc_datetime_inputs#fields.Datetime.from_string(self.gio_bat_dau)
        gio_bat_dau_utc = utc_tz.localize(gio_bat_dau_utc_native, is_dst=None)
        gio_bat_dau_vn = gio_bat_dau_utc.astimezone (local)
        return gio_bat_dau_vn



#lam gon lai ngay 23/02
class Fetch(models.Model):
    _name = 'bds.fetch'
    _inherit = 'abstract.fetch'
    _auto = True
    name = fields.Char(compute='_compute_name', store=True)
    url_id = fields.Many2one('bds.url')
    url_ids = fields.Many2many('bds.url')
    last_fetched_url_id = fields.Many2one('bds.url')#>0

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
        except FetchError as e:
            self.env['bds.error'].create({'name':str(e),'des':e.url})


    def fetch_all_url(self):
        url_ids = self.url_ids
        for url_id in url_ids:
            self.fetch_a_url_id (url_id)
        
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
            self.page_handle( page_int, url_id, number_notice_dict)
    
        self.last_fetched_url_id = url_id.id
        interval = (datetime.datetime.now() - begin_time).total_seconds()
        url_id.interval = interval
        url_id.write({'current_page': end_page_number_in_once_fetch,
                    'create_link_number': number_notice_dict['create_link_number'],
                    'update_link_number': number_notice_dict["update_link_number"],
                    'link_number': number_notice_dict["link_number"],
                    'existing_link_number': number_notice_dict["existing_link_number"],
                    })
        return None


    

    def page_handle(self, page_int, url_id, number_notice_dict):
        number_notice_dict['page_int'] = page_int
        format_page_url = url_id.url  
        print ('***format_page_url trong page_handle', format_page_url)  
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
            self.deal_a_topic(link, number_notice_dict, url_id, topic_data_from_page=topic_data_from_page)

    def deal_a_topic(self, link, number_notice_dict, url_id, topic_data_from_page={}):
        print ('link trong deal_a_topic', link)
        update_dict = {}
        public_datetime = topic_data_from_page['public_datetime'] # naitive datetime
        gmt7_public_datetime = convert_native_utc_datetime_to_gmt_7(public_datetime)
        public_date  = gmt7_public_datetime.date()
        search_bds_obj= self.env['bds.bds'].search([('link','=',link)])
        if search_bds_obj:
            number_notice_dict["existing_link_number"] = number_notice_dict["existing_link_number"] + 1
            public_date_cu  = fields.Date.from_string(search_bds_obj.public_date)
            if self.allow_write_public_datetime and  public_date != public_date_cu and public_date_cu and public_date:
                diff_public_date = (public_date - public_date_cu).days
                update_dict.update({'public_date':public_date})
                update_dict.update({'ngay_update_gia':datetime.datetime.now(),'diff_public_date':diff_public_date, 'public_date':public_date, 'publicdate_ids':[(0,False,{'diff_public_date':diff_public_date,'public_date':public_date,'public_date_cu':public_date_cu})]})
            
            # self.request_topic(link, update_dict, url_id, topic_data_from_page)
            if update_dict:
                print (u'-----------Update giá topic_index %s/%s- page_int %s - page_index %s/so_page %s'%(number_notice_dict['topic_index'],number_notice_dict['length_link_per_curent_page'],
                                                                            number_notice_dict['page_int'], number_notice_dict['page_index'],number_notice_dict['so_page']))
                search_bds_obj.write(update_dict)
                number_notice_dict['update_link_number'] = number_notice_dict['update_link_number'] + 1
        else:
            write_dict = {}
            write_dict.update({'public_date':public_date, 'public_datetime':public_datetime, 'url_id': url_id.id })
            print (u'+++++++++Create topic_index %s/%s- page_int %s - page_index %s/so_page %s'%(number_notice_dict['topic_index'],number_notice_dict['length_link_per_curent_page'],
                                                                            number_notice_dict['page_int'], number_notice_dict['page_index'],number_notice_dict['so_page']))
            # lấy dữ liệu 1 topic về từ link
            rq_topic_dict = self.request_topic(link, url_id)
            copy_topic_dict = self.copy_page_data_to_rq_topic(topic_data_from_page)
            write_dict.update(rq_topic_dict)
            write_dict.update(copy_topic_dict)
            write_dict['siteleech_id'] = self.siteleech_id_id
            write_dict['link'] = link
            write_dict['cate'] = url_id.cate
            self.env['bds.bds'].create(write_dict) 
            number_notice_dict['create_link_number'] = number_notice_dict['create_link_number'] + 1    
        
        link_number = number_notice_dict.get("link_number", 0) + 1
        number_notice_dict["link_number"] = link_number

    

            


        


        
