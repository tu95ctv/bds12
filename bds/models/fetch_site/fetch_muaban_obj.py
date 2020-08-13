# -*- coding: utf-8 -*-
from odoo.addons.bds.models.bds_tools  import  request_html, g_or_c_ss, get_or_create_user_and_posternamelines
from bs4 import BeautifulSoup
import re
import datetime
from odoo.addons.bds.models.fetch_site.fetch_bdscomvn  import get_or_create_quan_include_state
############mua ban ############

def get_mobile_name_for_muaban(soup):
    try:
        mobile_and_name_soup = soup.select('div.ct-contact ')[0]
        mobile_soup = mobile_and_name_soup.select('div.price-name + div > b')[0]
        mobile = mobile_soup.get_text()
        name = mobile
    except IndexError:
        mobile =  None
        name= None
    return mobile,name


class MuabanObject():

    def __init__(self, env):
        self.env = env

    def create_or_get_one_in_m2m_value(self, url):
        url = url.strip()
        if url:
            return g_or_c_ss(self.env['bds.images'],{'url':url})

    def write_images(self, soup):
        update_dict = {}
        image_soup = soup.select('div.image__slides img')
        images = [i['src'] for i in image_soup]
        # vì đang load... dùng javascript nên ko lấy được ảnh
        # raise ValueError('akakaka')

        # for i in image_soup:
        #     data_src = i['src']
        #     if data_src:
        #         images.append(data_src)
        # print ('***images**', images)
        if images:
            object_m2m_list = list(map(self.create_or_get_one_in_m2m_value, images))
            m2m_ids = list(map(lambda x:x.id, object_m2m_list))
            if m2m_ids:
                val = [(6, False, m2m_ids)]
                update_dict['images_ids'] = val
        return update_dict

    def write_gia(self, soup):
        gia_soup = soup.select('div.price-container__value')
        try:
            gia =  gia_soup[0].get_text()
            gia = re.sub(u'\.|đ|\s', '',gia)
            gia = float(gia)
            gia = gia/1000000000.0
        except IndexError:
            gia = 0
        return {'gia':gia}

    def write_gia_tho(self, soup):
        gia_soup = soup.select('div.price-container__value')
        try:
            gia =  gia_soup[0].get_text()
            # gia = re.sub(u'\.|đ|\s', '',gia)
            # gia = float(gia)
            # gia = gia/1000000000.0
        except IndexError:
            gia = False
        return {'price_string':gia}



    
    def write_quan_phuong(self, soup):
        quan_soup = soup.select('span.location-clock__location')
        quan_txt =  quan_soup[0].get_text()
        quan_tinhs = quan_txt.split('-')
        tinh_name = quan_tinhs[1].strip()
        tinh_name = re.sub('tphcm','Hồ Chí Minh',tinh_name,flags=re.I)
        quan_name =  quan_tinhs[0].strip()
        quan = get_or_create_quan_include_state(self, tinh_name, quan_name)
        return {'quan_id': quan.id}

    def write_quan_phuong_tho(self, soup):
        quan_soup = soup.select('span.location-clock__location')
        quan_txt =  quan_soup[0].get_text()
        quan_tinhs = quan_txt.split('-')
        tinh_name = quan_tinhs[1].strip()
        tinh_name = re.sub('tphcm','Hồ Chí Minh', tinh_name,flags=re.I)
        quan_name =  quan_tinhs[0].strip()
        # quan = get_or_create_quan_include_state(self, tinh_name, quan_name)
        return {'region_name':tinh_name, 'area_name':quan_name}


    def write_poster(self, soup, siteleech_id_id):
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


        user = get_or_create_user_and_posternamelines(self.env, mobile, name, siteleech_id_id)
        return {'poster_id':user.id}

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


        # mobile = ad['phone']
        # name = ad['account_name']

        # user = get_or_create_user_and_posternamelines(self.env, mobile, name, siteleech_id_id)
        return {'phone':mobile, 'account_name':name}



    def get_loai_nha(self, soup):
        loai_nha_soup = soup.select('div.breadcrumb li:last-child')
        loai_nha = loai_nha_soup[0].get_text()
        return {'loai_nha':loai_nha}

    def get_topic(self, html, siteleech_id_id):
        update_dict  = {}
        
        update_dict['data'] = html
        soup = BeautifulSoup(html, 'html.parser')

        content_soup = soup.select('div.body-container')
        
        update_dict['html']  = content_soup[0].get_text()
        # update_dict.update(self.write_images(soup))

        update_dict.update(self.write_gia_tho(soup))
        update_dict.update(self.write_quan_phuong_tho(soup))
        update_dict.update(self.get_loai_nha(soup))
        update_dict.update(self.write_poster_tho(soup))

        title = soup.select('h1.title')[0].get_text()
        title = title.strip()
        update_dict['title'] = title
    
        
        
        return update_dict

############## end mua ban  ###########