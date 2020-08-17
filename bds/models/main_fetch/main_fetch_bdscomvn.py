# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons.bds.models.bds_tools  import  request_html, SaveAndRaiseException
import json
import math
# from odoo.addons.bds.models.fetch_site.fetch_bdscomvn  import get_bds_dict_in_topic

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
from odoo.addons.bds.models.bds_tools  import  FetchError, SaveAndPass, save_to_disk
import traceback

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
from odoo.addons.bds.models.bds_tools import SaveAndRaiseException

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


class BDSFetch(models.AbstractModel):
    _inherit = 'abstract.main.fetch'

    def get_last_page_number(self, url_id):
        if self.site_name =='batdongsan':
            return get_last_page_from_bdsvn_website(url_id)
        return super(BDSFetch, self).get_last_page_number(url_id)
    
    def make_topic_link_from_list_id(self, list_id):
        link = super().make_topic_link_from_list_id(list_id)
        if self.site_name =='batdongsan':
            link  = 'https://batdongsan.com.vn' +  list_id
        
        return link

    def parse_html_topic (self, topic_html_or_json, url_id):
        if self.site_name =='batdongsan':
            # get_bds_dict_in_topic(self, topic_html_or_json, self.page_dict)
            topic_dict = get_bds_dict_in_topic(self, topic_html_or_json, self.page_dict)
            return topic_dict
        return super().parse_html_topic(topic_html_or_json, url_id)
        

    def create_page_link(self, format_page_url, page_int):
        page_url = super(BDSFetch, self).create_page_link(format_page_url, page_int)
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
        topic_data_from_pages_of_a_page = super(BDSFetch, self).ph_parse_pre_topic(html_page)
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
                    topic_data_from_page['list_id'] = href
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
                    topic_data_from_page['public_datetime_str'] = date_dang
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
                    topic_data_from_page['list_id'] = href

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
                        topic_data_from_page['list_id'] = href
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
            # raise SaveAndRaiseException('page_css_type_%s'%page_css_type)
            # print (aaa)
        if topic_data_from_pages_of_a_page:
            save_to_disk(html_page, 'bds_page_loai_%s'%page_css_type)
        return topic_data_from_pages_of_a_page

####################### PARSE##########################

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
        public_datetime_str = select[0].contents[2]
    except IndexError:
        pass
    public_datetime_str = public_datetime_str.replace('\r','').replace('\n','')
    public_datetime_str = re.sub('\s*', '', public_datetime_str)
    public_datetime = datetime.datetime.strptime(public_datetime_str,"%d-%m-%Y")
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

def get_bds_dict_in_topic(self, html, page_dict):
    update_dict = {}
    update_dict['data'] = html
    soup = BeautifulSoup(html, 'html.parser')
    
    try:
        kqs = soup.find_all("span", class_="gia-title")
        gia = kqs[0].find_all("strong")
        gia = gia[0].get_text()
        type_bdscom_topic = 1
    except:
        gia_soup = soup.select("div.short-detail-wrap > ul.short-detail-2 > li:nth-of-type(1) > span.sp2")[0]
        gia = gia_soup.get_text()
        type_bdscom_topic = 2
    update_dict['price_string'] = gia
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