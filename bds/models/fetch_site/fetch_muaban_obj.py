# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import re
import datetime
############mua ban ############


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
        loai_nha_soup = soup.select('div.breadcrumb li:last-child')
        loai_nha = loai_nha_soup[0].get_text()
        return {'loai_nha':loai_nha}

    def get_topic(self, html):
        update_dict  = {}
        update_dict['data'] = html
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

############## end mua ban  ###########