# -*- coding: utf-8 -*-
from odoo.addons.bds.models.bds_tools  import  request_html,g_or_c_ss, get_or_create_user_and_posternamelines, save_to_disk, SaveAndRaiseException
from bs4 import BeautifulSoup
import re
from unidecode import unidecode
import datetime
################### BDS ###################


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


def get_phuong_xa_from_topic(self,soup,quan_id):
    sl = soup.select('div#divWard li.current')   
    if sl:
        phuong_name =  sl[0].get_text()
        phuong = g_or_c_ss(self.env['bds.phuong'], {'name_phuong':phuong_name,'quan_id':quan_id}, {'quan_id':quan_id})
        return phuong.id
    else:
        return False


def get_images_for_bds_com_vn(soup):
    rs = soup.select('meta[property="og:image"]')
    images =  list(map(lambda i:i['content'], rs))
    return images


def get_public_datetime(soup):
    select = soup.select('div.prd-more-info > div:nth-of-type(3)')#[0].contents[0]
    public_datetime_str = select[0].contents[2]
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
    

def g_or_c_bds_quan(self,soup):
    sl = soup.select('div#divDistrictOptions li.current')   
    if not sl:
        try:
            sl = soup.select('div.left-detail')[0]
        except:
            try:
                sl = soup.select('div.breadcrumb a:nth-of-type(3)')
            except:
                raise SaveAndRaiseException('quan')


    quan_name =  sl[0].get_text()
    name_without_quan_huyen = quan_name.replace(u'Quận ','').replace(u'Huyện','')
    quan_unidecode = unidecode(quan_name).lower().replace(' ','-')
    quan = g_or_c_ss(self.env['res.country.district'], {'name_without_quan':name_without_quan_huyen},
                        {'name':quan_name,'name_unidecode':quan_unidecode}, False)
    return quan.id

def get_or_create_quan_include_state(self, tinh_str, quan_str):
    tinh_str = re.sub('tp|Thành phố|tỉnh','', tinh_str, flags=re.I)
    tinh_str = tinh_str.strip()
    country_obj = self.env['res.country'].search([('name','ilike','viet')])[0]
    state = g_or_c_ss(self.env['res.country.state'], {'name':tinh_str, 'country_id':country_obj.id},
                        {'code':tinh_str}, False)
    quan = g_or_c_ss(self.env['res.country.district'], {'name':quan_str, 'state_id':state.id},
                        {}, False)
    return quan

def g_or_create_quan_include_state(self, quan_huyen_str):
    quan_huyen_strs = quan_huyen_str.split(',')
    quan_str = quan_huyen_strs[0]
    tinh_str = quan_huyen_strs[1]
    quan = get_or_create_quan_include_state(self, tinh_str, quan_str)
    return quan


    
    
    # state_id = fields.Many2one('res.country.state', string='Province')


def get_mobile_name_for_batdongsan(soup,site_name='batdongsan'):
    if site_name == 'batdongsan':
        mobile = get_mobile_user(soup)
        try:
            name = get_name_user(soup)
        except:
            name = 'no name bds'
    elif site_name=='muaban':
        try:
            mobile_and_name_soup = soup.select('div.ct-contact ')[0]
            mobile_soup = mobile_and_name_soup.select('div.price-name + div > b')[0]
            mobile = mobile_soup.get_text()
            name = mobile
        except IndexError:
            mobile =  None
            name= None
    return mobile,name


def get_dientich(soup):
    try:
        kqs = soup.find_all("span", class_="gia-title")
        gia = kqs[1].find_all("strong")
    except:
        try:
            print ('*************111111111111************')
            gia = soup.select('div.short-detail-wrap > ul.short-detail-2 > li:nth-of-type(2) > span.sp2')
            print ('*************22222222222222************')
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


def get_mobile_user(soup, id_select = 'div#LeftMainContent__productDetail_contactMobile'):
    try:
        select = soup.select(id_select)[0]
        mobile =  select.contents[3].contents[0]
        mobile =  mobile.strip()
        if not mobile:
            raise ValueError('sao khong co phone')
    except IndexError:
        try:
            select = soup.select('span.phoneEvent')[0]
            phone = select['raw']

        except:
            select = soup.select('#divCustomerInfoAd div.right-content .right')[0]
            phone = select.get_text()
        
        return phone

    return mobile


def get_name_user(soup):
    try:
        name = get_mobile_user(soup,id_select = 'div#LeftMainContent__productDetail_contactName')
    except:
        select = soup.select('dive.name')[0]
        name = select['title']
    return name


ty_trieu_nghin_look = {'tỷ':1000000000, 'triệu':1000000, 'nghìn':1000, 'đ':1}

def convert_gia_from_string_to_float(gia):# 3.5 triệu/tháng
    gia_ty, trieu_gia, price, thang_m2_hay_m2 = False, False, False, False
    gia = gia.strip()
    if not gia:
        return gia_ty, trieu_gia, price, thang_m2_hay_m2

    if re.search('thỏa thuận', gia, re.I):
        return gia_ty, trieu_gia, price, thang_m2_hay_m2

    try:
        rs = re.search('([\d\,\.]*) (\w+)(?:$|/)(.*$)', gia)
        gia_char = rs.group(1).strip()
        if not gia_char:
            return gia_ty, trieu_gia, price, thang_m2_hay_m2
        gia_char = gia_char.replace(',','.')
        ty_trieu_nghin = rs.group(2)
        thang_m2_hay_m2 = rs.group(3)
        if ty_trieu_nghin == 'đ':
            gia_char = gia_char.replace('.','')
        gia_float = float(gia_char)
        he_so = ty_trieu_nghin_look[ty_trieu_nghin]
        price = gia_float* he_so
        gia_ty = price/1000000000
        trieu_gia = price/1000000

    except:
        print ('exception gia', gia)
        raise
        
    return gia_ty, trieu_gia, price, thang_m2_hay_m2


def get_price(soup):
    gia_ty, price, thang_m2_hay_m2 = False, False, False
    
    try:
        kqs = soup.find_all("span", class_="gia-title")
        gia = kqs[0].find_all("strong")
        gia = gia[0].get_text()
        type_bdscom_topic = 1
    except:
        gia_soup = soup.select("div.short-detail-wrap > ul.short-detail-2 > li:nth-of-type(1) > span.sp2")[0]
        gia = gia_soup.get_text()
        type_bdscom_topic = 2
  

    gia_ty, trieu_gia, price, thang_m2_hay_m2 = convert_gia_from_string_to_float(gia)
    return gia_ty,trieu_gia, price, thang_m2_hay_m2, type_bdscom_topic


def get_bds_dict_in_topic(self, page_dict, html, siteleech_id_id):
    # def create_or_get_one_in_m2m_value(val):
    #         val = val.strip()
    #         if val:
    #             return g_or_c_ss(self.env['bds.images'],{'url':val})

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
   
    # gia, trieu_gia, price, price_unit, type_bdscom_topic = get_price(soup)
    # update_dict['price'] = price
    # update_dict['gia'] = gia
    # update_dict['trieu_gia'] = trieu_gia
    # update_dict['price_unit'] = price_unit



    update_dict['html'] = get_product_detail(soup, type_bdscom_topic)


    images = get_images_for_bds_com_vn(soup)
    if images:
        update_dict['images'] = images

        # object_m2m_list = list(map(create_or_get_one_in_m2m_value, images))
        # m2m_ids = list(map(lambda x:x.id, object_m2m_list))
        # if m2m_ids:
        #     val = [(6, False, m2m_ids)]
        #     update_dict['images_ids'] = val
    
    update_dict['area'] = get_dientich(soup)
 
    
    
    # if not page_dict.get('quan_id'):
    #     quan_id= g_or_c_bds_quan(self, soup)
    #     update_dict['quan_id'] = quan_id
    #     update_dict['phuong_id'] = get_phuong_xa_from_topic(self,soup,quan_id)
    
    
    
    
    try:
        title = soup.select('div.pm-title > h1')[0].contents[0] 
    except:
        try:
            title = soup.select('h1.tile-product')[0].get_text()
        except:
            raise 
    update_dict['title']=title
    update_dict['phone'], update_dict['account_name'] = get_mobile_name_for_batdongsan(soup)
    
    # user = get_or_create_user_and_posternamelines(self.env, mobile, name, siteleech_id_id)
    # update_dict['phone_poster']=mobile
    # update_dict['poster_id'] = user.id 

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