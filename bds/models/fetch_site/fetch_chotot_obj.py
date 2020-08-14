# -*- coding: utf-8 -*-
import json
def get_topic(self, topic_html_or_json, page_dict, ad = None):
    update_dict = {}
    if not ad:
        topic_html_or_json = json.loads(topic_html_or_json) 
        ad = topic_html_or_json['ad']
        ad_params = topic_html_or_json['ad_params']
    else:
        ad_params = ad

    update_dict['region_name'] = ad['region_name']
    update_dict['area_name'] = ad['area_name']
    try:
        update_dict['ward_name'] = ad['ward_name']
    except:
        pass
    update_dict['images']= ad.get('images',[])
    print ('***phone****', ad['phone'])
    update_dict['phone'] = ad['phone']
    update_dict['account_name'] = ad['account_name']
    update_dict['price_string'] = ad['price_string']
    update_dict['price'] = ad['price']

    address = ad_params.get('address',{}).get('value',False)
    if address:
        update_dict['address'] = address
    else:
        pass
    try:
        if not 'html' in page_dict:
            update_dict['html'] = ad['body']
    except KeyError:
        pass
    update_dict['area']= ad.get('size',0)
    if 'title' not in page_dict:
        update_dict['title']= ad['subject']
    return update_dict



   

   


    




        
        
   





