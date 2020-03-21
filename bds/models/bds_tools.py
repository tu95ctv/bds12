# -*- coding: utf-8 -*-
from time import sleep
from urllib import request
from odoo import fields
from odoo.osv import expression
import datetime
from unidecode import unidecode


class FetchError(Exception):
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

def g_or_c_ss(self,
                class_name,search_dict,
                create_write_dict ={},
                update_no_need_check_change=False,
                is_up_date = True,
                not_active_include_search = False
            ):
    if not_active_include_search:
        domain_not_active = ['|',('active','=',True),('active','=',False)]
    else:
        domain_not_active = []
    domain = []
    for i in search_dict:
        tuple_in = (i,'=',search_dict[i])
        domain.append(tuple_in)
    domain = expression.AND([domain_not_active, domain])
    searched_object  = self.env[class_name].search(domain)
    if not searched_object:
        search_dict.update(create_write_dict)
        created_object = self.env[class_name].create(search_dict)
        return_obj =  created_object
    else:
        return_obj = searched_object
        is_change = update_no_need_check_change
        if not is_change and is_up_date:
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
                    is_change = True
                    break
        if is_change:
            searched_object.write(create_write_dict)
    return return_obj       

def get_or_create_user_and_posternamelines(self, mobile, name, siteleech_id_id):
    search_dict = {}
    search_dict['phone'] = mobile 
    search_dict['login'] = str(mobile)+'@gmail.com'
    user =  self.env['bds.poster'].search([('phone','=', mobile)])
    if user:
        posternamelines_search_dict = {'username_in_site':name, 'site_id':siteleech_id_id, 'poster_id':user.id}
        g_or_c_ss(self,'bds.posternamelines',posternamelines_search_dict)
                                              
    else:
        search_dict.update({'created_by_site_id': siteleech_id_id})
        user =  self.env['bds.poster'].create(search_dict)
        self.env['bds.posternamelines'].create( {'username_in_site':name,'site_id':siteleech_id_id,'poster_id':user.id})
    return user 

def g_or_c_quan(self, quan_name):
    name_without_quan_huyen = quan_name.replace(u'Quận ','').replace(u'Huyện','')
    quan_unidecode = unidecode(quan_name).lower().replace(' ','-')
    quan_search_dict = {'name_without_quan':name_without_quan_huyen}
    quan_update_dict = {'name':quan_name,'name_unidecode':quan_unidecode}
    quan = g_or_c_ss(self,'bds.quan',quan_search_dict, quan_update_dict )
    return quan.id
