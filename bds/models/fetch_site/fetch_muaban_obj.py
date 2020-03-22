# -*- coding: utf-8 -*-
from odoo.addons.bds.models.bds_tools  import  request_html, g_or_c_ss, get_or_create_user_and_posternamelines,g_or_c_quan
from bs4 import BeautifulSoup
import re
import datetime
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

    def __init__(self, self_fetch_obj):
        self.env = self_fetch_obj.env

    def get_muaban_vals_one_topic(self, html, siteleech_id_id):
        update_dict  = {}
        def create_or_get_one_in_m2m_value(val):
                val = val.strip()
                if val:
                    return g_or_c_ss(self.env['bds.images'],{'url':val})
        
        update_dict['data'] = html
        soup = BeautifulSoup(html, 'html.parser')

        image_soup = soup.select('div.slider__frame')
        content_soup = soup.select('div.body-container')
        update_dict['html']  = content_soup[0].get_text()
        images = []
        for i in image_soup:
            data_src = i.get('data-src',False)
            if data_src:
                images.append(data_src)
            
        if images:
            object_m2m_list = list(map(create_or_get_one_in_m2m_value, images))
            m2m_ids = list(map(lambda x:x.id, object_m2m_list))
            if m2m_ids:
                val = [(6, False, m2m_ids)]
                update_dict['images_ids'] = val

        gia_soup = soup.select('div.price-container__value')
        try:
            gia =  gia_soup[0].get_text()
            gia = re.sub(u'\.|đ|\s', '',gia)
            gia = float(gia)
            gia = gia/1000000000.0
        except IndexError:
            gia = 0

        update_dict['gia'] = gia
        title = soup.select('h1.title')[0].get_text()
        title = title.strip()
        update_dict['title']=title
        update_dict['siteleech_id'] = siteleech_id_id
    
        quan_soup = soup.select('span.location-clock__location')
        quan_txt =  quan_soup[0].get_text()
        quan_name =  quan_txt.split('-')[0].strip()
        quan_id = g_or_c_quan(self.env, quan_name)
        update_dict['quan_id'] = quan_id
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

        if mobile != None:
            user = get_or_create_user_and_posternamelines(self.env, mobile,name, siteleech_id_id)
            update_dict['phone_poster']=mobile
            update_dict['poster_id'] = user.id
        return update_dict

############## end mua ban  ###########