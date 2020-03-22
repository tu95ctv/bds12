# -*- coding: utf-8 -*-
from odoo import api, models, _
# -*- coding: utf-8 -*-
from odoo.addons.bds.models.bds_tools  import  request_html, g_or_c_ss,  get_or_create_user_and_posternamelines, g_or_c_quan
from bs4 import BeautifulSoup
import re
from unidecode import unidecode
import datetime
##Nh fetch_bds
import json
import pytz
##############Cho tot###############

def create_cho_tot_page_link(url_input, page_int):
    repl = 'o=%s'%(20*(page_int-1))
    url_input = re.sub('o=\d+',repl,url_input)
    url = url_input +  '&page=' +str(page_int)
    return url

MAP_CHOTOT_DATE_TYPE_WITH_TIMEDELTA = {u'ngày':'days',u'tuần':'weeks',u'hôm qua':'days',u'giờ':'hours',u'phút':'minutes',u'giây':'seconds',u'năm':'days',u'tháng':'days'}

def convert_chotot_date_to_datetime(string):
    rs = re.search (r'(\d*?)\s?(ngày|tuần|hôm qua|giờ|phút|giây|năm|tháng)',string,re.I)
    rs1 =rs.group(1)
    rs2 =rs.group(2)
    if rs1=='':
        rs1 =1
    rs1 = int (rs1)
    if rs2==u'tháng':
        rs1 = rs1*365/12
    elif rs2==u'năm':
        rs1 = rs1*365
    elif rs2=='tuần':
        rs1 = rs1*7
    rs2 = MAP_CHOTOT_DATE_TYPE_WITH_TIMEDELTA[rs2]
    dt = datetime.datetime.now() - datetime.timedelta(**{rs2:rs1})
    return dt


def local_a_native_time(datetime_input):
    local = pytz.timezone("Etc/GMT-7")
    local_dt = local.localize(datetime_input, is_dst=None)
    utc_dt = local_dt.astimezone (pytz.utc)
    return utc_dt#utc_dt

def get_mobile_name_cho_tot(html):
    mobile = html['phone']
    name = html['account_name']
    return mobile,name

def convert_chotot_price(html):
    try:
        price = float(html['price'])/1000000000
        price_trieu = float(html['price'])/1000000
    except KeyError:
        price = 0
        price_trieu = 0
    return price, price_trieu
    
class ChototFetch(models.AbstractModel):
    _name = 'abstract.topic.fetch'

    def get_topic_chotot(self, topic_html_or_json, siteleech_id_id):
        obj = Chotot_get_topic(self)
        return obj.get_topic_chotot(topic_html_or_json, siteleech_id_id)
        
class Chotot_get_topic():
    
    def __init__(self, self_fetch_obj):
        self.env = self_fetch_obj.env

    def create_or_get_one_in_m2m_value(self, val):
        val = val.strip()
        if val:
            return g_or_c_ss(self.env['bds.images'],{'url':val})
    def write_images(self, html):
        update_dict = {}
        images_urls = html.get('images',[])
        if images_urls:
            object_m2m_list = list(map(self.create_or_get_one_in_m2m_value, images_urls))
            m2m_ids = list(map(lambda x:x.id, object_m2m_list))
            if m2m_ids:
                val = [(6, False, m2m_ids)]
                update_dict['images_ids'] = val
        return update_dict

    def write_quan_phuong(self, ad_params):
        update_dict = {}
        try:
            quan_name = ad_params['area']['value']
            quan_id = g_or_c_quan(self.env, quan_name)
            update_dict['quan_id'] = quan_id
        except KeyError:
            quan_id = None

        try:
            ward =  ad_params['ward']['value']
        except KeyError:
            ward = None

        if quan_id and ward:
            phuong_id = g_or_c_ss(self.env['bds.phuong'], {'name_phuong':ward, 'quan_id':quan_id}, {})
            update_dict['phuong_id'] = phuong_id.id
        return update_dict

    def write_gia(self, ad):
        update_dict = {}
        price, price_trieu = convert_chotot_price(ad)
        update_dict['gia'] = price
        update_dict['gia_trieu'] = price_trieu
        return update_dict

    def get_topic_chotot(self, topic_html_or_json, siteleech_id_id):
        update_dict = {}

        topic_html_or_json = json.loads(topic_html_or_json) 
        ad = topic_html_or_json['ad']
        ad_params = topic_html_or_json['ad_params']
        

        date = ad['date']
        update_dict['date_text'] = date
        update_dict.update(self.write_images(ad))
        update_dict.update(self.write_quan_phuong(ad_params))
        update_dict.update(self.write_gia(ad))
        
        try:
            address = ad['address']
            update_dict['address'] = address
        except KeyError:
            pass

        mobile, name = get_mobile_name_cho_tot(ad)
        user = get_or_create_user_and_posternamelines(self.env, mobile, name ,siteleech_id_id)
        update_dict['phone_poster'] = mobile
        update_dict['poster_id'] = user.id

        try:
            update_dict['html'] = ad['body']
        except KeyError:
            pass
        
        update_dict['area']= ad.get('size',0)
        update_dict['title']= ad['subject']
        return update_dict




        
        
   





