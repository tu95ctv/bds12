# -*- coding: utf-8 -*-
from odoo.addons.bds.models.bds_tools  import  request_html,g_or_c_ss, get_or_create_user_and_posternamelines
from bs4 import BeautifulSoup
import re
from unidecode import unidecode
import datetime
################### BDS ###################

def get_last_page_from_bdsvn_website(url_input):
    ##print '***url_input**',url_input
    html = request_html(url_input)
    soup = BeautifulSoup(html, 'html.parser')
    range_pages = soup.select('div.background-pager-right-controls > a')
    if range_pages:
        last_page_href =  range_pages[-1]['href']
        #end_page = int(last_page_href[-1])
        kq= re.search('\d+$',last_page_href)
        last_page_from_website =  int(kq.group(0))
    else:
        last_page_from_website = 1
    return last_page_from_website


def get_phuong_xa_from_topic(self,soup,quan_id):
    sl = soup.select('div#divWard li.current')   
    if sl:
        phuong_name =  sl[0].get_text()
        phuong = g_or_c_ss(self,'bds.phuong', {'name_phuong':phuong_name,'quan_id':quan_id}, {'quan_id':quan_id})
        return phuong.id
    else:
        return False

def get_images_for_bds_com_vn(soup):
    rs = soup.select('meta[property="og:image"]')
    images =  list(map(lambda i:i['content'],rs))
    return images

def get_bds_dict_in_topic(self,update_dict,html,siteleech_id,only_return_price=False):
    def create_or_get_one_in_m2m_value(val):
            val = val.strip()
            if val:
                return g_or_c_ss(self,'bds.images',{'url':val})
    update_dict['data'] = html
    soup = BeautifulSoup(html, 'html.parser')
    try:
        gia = get_price(soup)
    except:
        gia =0
    update_dict['gia'] = gia
    if  only_return_price:
        return gia
    
#     update_dict['public_datetime'] = get_public_datetime(soup)
    update_dict['html'] = get_product_detail(soup)
    update_dict['siteleech_id'] = siteleech_id.id
    images = get_images_for_bds_com_vn(soup)
    if images:
        object_m2m_list = list(map(create_or_get_one_in_m2m_value, images))
        m2m_ids = list(map(lambda x:x.id, object_m2m_list))
        ###print '**m2m_ids**',m2m_ids
        if m2m_ids:
            val = [(6, False, m2m_ids)]
            update_dict['images_ids'] = val
    try:
        update_dict['area'] = get_dientich(soup)
    except:
        pass
    quan_id= g_or_c_bds_quan(self,soup)
    update_dict['quan_id'] = quan_id
    update_dict['phuong_id'] = get_phuong_xa_from_topic(self,soup,quan_id)
    #get_all_phuong_xa_of_quan_from_topic(self,soup,quan_id)
    title = soup.select('div.pm-title > h1')[0].contents[0] 
    update_dict['title']=title
    ####print 'title',title
    mobile,name = get_mobile_name_for_batdongsan(soup)
    user = get_or_create_user_and_posternamelines(self,mobile,name,siteleech_id)
    update_dict['user_name_poster']=name
    update_dict['phone_poster']=mobile
    update_dict['poster_id'] = user.id    
    


def get_public_datetime(soup):
    select = soup.select('div.prd-more-info > div:nth-of-type(3)')#[0].contents[0]
    public_datetime_str = select[0].contents[2]
    public_datetime_str = public_datetime_str.replace('\r','').replace('\n','')
    public_datetime_str = re.sub('\s*', '', public_datetime_str)
    public_datetime = datetime.datetime.strptime(public_datetime_str,"%d-%m-%Y")
    return public_datetime



def get_product_detail(soup):
    select = soup.select('div.pm-desc')[0]
    
    return select.get_text()


# def get_quan_list_in_big_page(self,column_name='bds_bds.phuong_id'):
#     product_category_query = '''select  count(%s), %s from fetch_bds_relate inner join bds_bds on fetch_bds_relate.bds_id = bds_bds.id where fetch_id = %s group by %s'''%(column_name,column_name,self.id,column_name)
#     self.env.cr.execute(product_category_query)
#     product_category = self.env.cr.fetchall()
#     phuong_list = reduce(lambda y,x:([x[1]]+y) if x[1]!=None else y,product_category,[] )
#     return phuong_list

def g_or_c_bds_quan(self,soup):
    sl = soup.select('div#divDistrictOptions li.current')   
    if sl:
        quan_name =  sl[0].get_text()
        name_without_quan_huyen = quan_name.replace(u'Quận ','').replace(u'Huyện','')
        quan_unidecode = unidecode(quan_name).lower().replace(' ','-')
        quan = g_or_c_ss(self,'bds.quan', {'name_without_quan':name_without_quan_huyen},
                          {'name':quan_name,'name_unidecode':quan_unidecode}, False)
        return quan.id
    else:
        return False

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


def convert_gia_from_string_to_float(gia):
    if u'tỷ' in gia:
        int_gia = gia.replace(u'tỷ','').rstrip()
        int_gia = float(int_gia)
    else:
        int_gia = False
    return int_gia
def get_price(soup):
    kqs = soup.find_all("span", class_="gia-title")
    gia = kqs[0].find_all("strong")
    gia = gia[0].get_text()
    int_gia = convert_gia_from_string_to_float(gia)
    return int_gia
def get_dientich(soup):
    kqs = soup.find_all("span", class_="gia-title")
    gia = kqs[1].find_all("strong")
    gia = gia[0].get_text()
    rs = re.search(r"(\d+)", gia)
    gia = rs.group(1)
    int_gia = float(gia)
    return int_gia
def get_mobile_user(soup,id_select = 'div#LeftMainContent__productDetail_contactMobile'):
    select = soup.select(id_select)[0]
    mobile =  select.contents[3].contents[0]
    mobile =  mobile.strip()
    if not mobile:
        raise ValueError('sao khong co phone')
    return mobile
def get_name_user(soup):
    name = get_mobile_user(soup,id_select = 'div#LeftMainContent__productDetail_contactName')
    return name

