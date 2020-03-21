# -*- coding: utf-8 -*-
from time import sleep
from urllib import request
from odoo import fields
from odoo.osv import expression
import datetime
from unidecode import unidecode


class MyError(Exception):
    type = None
    pass

def request_html(url, try_again=True, is_decode_utf8 = True):
    headers = { 'User-Agent' : 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36' }
    count_fail = 0
    def in_try():
        req =request.Request(url, None, headers)
        rp= request.urlopen(req)
        mybytes = rp.read()
        if is_decode_utf8:
            html = mybytes.decode("utf8")
            return html
        else:
            return mybytes
    while 1:
        if not try_again:
            return in_try()
        try:
            html = in_try()
            return html
        except Exception as e:
            count_fail +=1
            sleep(5)
            if count_fail ==5:
                raise ValueError(u'Lỗi get html')



def g_or_c_ss(self,class_name,search_dict,
                                create_write_dict ={},
                                is_must_update=False,noti_dict=None,
                                not_active_include_search = False,
                                model_effect_noti_dict=False,
                                create_or_write_info = False,
                                is_up_date = True):
    if not_active_include_search:
        domain_not_active = ['|',('active','=',True),('active','=',False)]
    else:
        domain_not_active = []
    domain = []
    if noti_dict =={}:
        noti_dict['create'] = 0
        noti_dict['update'] = 0
        noti_dict['skipupdate'] = 0
    for i in search_dict:
        tuple_in = (i,'=',search_dict[i])
        domain.append(tuple_in)
    domain = expression.AND([domain_not_active, domain])
#     domain.extend(domain_not_active)
    searched_object  = self.env[class_name].search(domain)
    if not searched_object:
        search_dict.update(create_write_dict)
        created_object = self.env[class_name].create(search_dict)
        if noti_dict !=None and ( model_effect_noti_dict==False or model_effect_noti_dict==class_name):
            noti_dict['create'] = noti_dict['create'] + 1
        create_or_write = 'create'
        return_obj =  created_object
    else:
        create_or_write = 'skip write'
        return_obj = searched_object
        if is_up_date: 
            if not is_must_update:
                is_write = False
                for attr in create_write_dict:
                    domain_val = create_write_dict[attr]
                    exit_val = getattr(searched_object,attr)
                    try:
                        exit_val = getattr(exit_val,'id',exit_val)
                        if exit_val ==None: #recorderset.id ==None when recorder sset = ()
                            exit_val=False
                    except:#singelton
                        pass
                    if isinstance(domain_val, datetime.date):
                        exit_val = fields.Date.from_string(exit_val)
                    if exit_val !=domain_val:
                        is_write = True
                        break
                
            else:
                is_write = True
            
            if is_write:
                create_or_write = 'write'
                searched_object.sudo().write(create_write_dict)
                if noti_dict !=None and ( model_effect_noti_dict==False or model_effect_noti_dict==class_name):
                    noti_dict['update'] = noti_dict['update'] + 1
    
            else:#'update'
                create_or_write = 'skip write'
                if noti_dict !=None and ( model_effect_noti_dict==False or model_effect_noti_dict==class_name):
                    noti_dict['skipupdate'] = noti_dict['skipupdate'] + 1
            
    if create_or_write_info:
        return return_obj,create_or_write
    return return_obj       

def get_or_create_user_and_posternamelines(self, mobile, name, site_name):
    search_dict = {}
    search_dict['phone'] = mobile 
    search_dict['login'] = str(mobile)+'@gmail.com'
#     search_dict['name'] = mobile
    user =  self.env['bds.poster'].search([('phone','=',mobile)])
    site_id = g_or_c_ss(self,'bds.siteleech', {'name':site_name}, {}, False)
    if user:
        posternamelines_id = g_or_c_ss(self,'bds.posternamelines',
                                               {'username_in_site':name, 'site_id':site_id.id, 'poster_id':user.id}, {}, False)
    else:
        search_dict.update({'ghi_chu':'created by %s'%site_name})
        user =  self.env['bds.poster'].create(search_dict)
        self.env['bds.posternamelines'].create( {'username_in_site':name,'site_id':site_id.id,'poster_id':user.id})
    return user 

def g_or_c_chotot_quan(self,quan_name, is_up_date=False):
    name_without_quan_huyen = quan_name.replace(u'Quận ','').replace(u'Huyện','')
    quan_unidecode = unidecode(quan_name).lower().replace(' ','-')
    quan = g_or_c_ss(self,'bds.quan', {'name_without_quan':name_without_quan_huyen}, {'name':quan_name,'name_unidecode':quan_unidecode}, False,is_up_date=is_up_date)
    return quan.id
