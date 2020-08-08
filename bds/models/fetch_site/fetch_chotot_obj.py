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
from dateutil.relativedelta import relativedelta

from odoo.addons.bds.models.fetch_site.fetch_bds_com_vn  import convert_gia_from_string_to_float
from odoo.addons.bds.models.fetch_site.fetch_bds_com_vn  import get_or_create_quan_include_state
##############Cho tot###############

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

# MAP_CHOTOT_DATE_TYPE_WITH_TIMEDELTA = {
#         u'ngày':'days',
#         u'tuần':'weeks',
#         u'hôm qua':'days',
#         u'giờ':'hours',
#         u'phút':'minutes',
#         u'giây':'seconds',
#         u'năm':'days',
#         u'tháng':'days'
#         }

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


def convert_to_utc_tz_a_vn_native_time(datetime_input):
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
        gia_ty = float(html['price'])/1000000000
        trieu_gia = float(html['price'])/1000000
    except KeyError:
        gia_ty = 0
        trieu_gia = 0
    return gia_ty, trieu_gia
    
def write_ty_trieu_gia(ad):
        update_dict = {}
        gia_ty, price_trieu = convert_chotot_price(ad)
        update_dict['gia'] = gia_ty
        update_dict['gia_trieu'] = price_trieu
        return update_dict

def deal_gia_chotot(ad):
    gia_dict = {}
    price_string = ad['price_string']
    print ('***price_string***', price_string)
    gia_ty, trieu_gia, price, price_unit = convert_gia_from_string_to_float(price_string)
    gia_dict['price'] = ad['price']
    gia_dict['price_unit'] = price_unit # tháng/m2
    gia_dict.update(write_ty_trieu_gia(ad))
    return gia_dict

def create_quan_for_chotot(self, ad):
    tinh = ad['region_name']
    quan_name = ad['area_name']
    quan = get_or_create_quan_include_state(self,tinh, quan_name)
    return quan

        # try:
        #     ward =  ad['ward_name']
        # except KeyError:
        #     ward = None

        # if quan_id and ward:
        #     phuong_id = g_or_c_ss(self.env['bds.phuong'], {'name_phuong':ward, 'quan_id':quan_id}, {})
        #     update_dict['phuong_id'] = phuong_id.id
        # return update_dict 

def write_quan_phuong(self, ad):
        update_dict = {}
        quan = create_quan_for_chotot(self, ad)
        quan_id = quan.id
        update_dict['quan_id'] = quan_id
        ward =  ad['ward_name']
        # if quan_id and ward:
        phuong_id = g_or_c_ss(self.env['bds.phuong'], {'name_phuong':ward, 'quan_id':quan_id}, {})
        update_dict['phuong_id'] = phuong_id.id
        return update_dict
class ChototFetch(models.AbstractModel):
    _name = 'abstract.topic.fetch'

    def get_topic_chotot(self, topic_html_or_json, siteleech_id_id):
        obj = ChototGetTopic(self)
        return obj.get_topic_chotot(topic_html_or_json, siteleech_id_id)
        
class ChototGetTopic():
    
    def __init__(self, env):
        self.env = env

    def create_or_get_one_in_m2m_value(self, url):
        url = url.strip()
        if url:
            return g_or_c_ss(self.env['bds.images'],{'url':url})

    def write_images(self, ad):
        update_dict = {}
        images_urls = ad.get('images',[])
        if images_urls:
            object_m2m_list = list(map(self.create_or_get_one_in_m2m_value, images_urls))
            m2m_ids = list(map(lambda x:x.id, object_m2m_list))
            if m2m_ids:
                val = [(6, False, m2m_ids)]
                update_dict['images_ids'] = val
        return update_dict

    


    

    def write_poster(self, ad, siteleech_id_id):
        mobile, name = get_mobile_name_cho_tot(ad)
        user = get_or_create_user_and_posternamelines(self.env, mobile, name, siteleech_id_id)
        return {'poster_id': user.id }

    def write_address(self,ad_params):
        address = ad_params.get('address',{}).get('value',False)
        if address:
            return {'address':address}
        else:
            return {}


    def get_topic(self, topic_html_or_json, page_dict, siteleech_id_id, ad = None):
        update_dict = {}
        if not ad:
            topic_html_or_json = json.loads(topic_html_or_json) 
            ad = topic_html_or_json['ad']
            ad_params = topic_html_or_json['ad_params']
        else:
            ad_params = ad
        
        # date = ad['date']
        # update_dict['date_text'] = date

        
        # gia_dict = deal_gia_chotot(ad)
        # update_dict.update(gia_dict)
        if 'quan_id' not in page_dict:
            update_dict.update(write_quan_phuong(self, ad))


        update_dict.update(self.write_images(ad))
        update_dict.update(self.write_poster(ad, siteleech_id_id))
        update_dict.update(self.write_address(ad_params))
       
        try:
            if not 'html' in page_dict:
                update_dict['html'] = ad['body']
        except KeyError:
            pass
        # if 'area' not in page_dict:
        update_dict['area']= ad.get('size',0)
        if 'title' not in page_dict:
            update_dict['title']= ad['subject']
        return update_dict




        
        
   





