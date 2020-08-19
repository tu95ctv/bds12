# -*- coding: utf-8 -*-
import re
import base64
from unidecode import unidecode

#BDS compute field
#_compute_so_phong_ngu, _compute_mat_tien_or_trich_dia_chi

def _compute_so_phong_ngu( html):
        so_phong_ngu = 0
        pt = '(\d{1,2})\s*(?:pn|phòng ngủ)(?:\W|$)'
        rs = re.search(pt, html, re.I)
        if rs:
            so_phong_ngu = rs.group(1)
            try:
                so_phong_ngu = int(so_phong_ngu)
            except: 
                so_phong_ngu = 0
        return so_phong_ngu

def detect_mat_tien_address(html, p = None):
    #parent function call: detect_mat_tien_address_sum
    mat_tien_full_address_possibles = True
    before_index = 0
    deal_s = []
    full_adress_list = []
    while mat_tien_full_address_possibles:
        html = html [before_index:]
        # p = '(?i:nhà|mt|mặt tiền|số)\s+(\d{1,4}[a-zA-Z]{0,2})[\s,]+(?i:đường)*\s*(?P<ten_duong>(?:[A-Z0-9Đ][\w|/]*\s*){1,4})(?:\.|\s|\,|$|<)'
        mat_tien_full_address_possibles = re.search(p, html, re.I)  #((\S+(?:\s|\.|$|,)+){1,4})
        if mat_tien_full_address_possibles:
            before_index = mat_tien_full_address_possibles.span()[1] + 1
            number = mat_tien_full_address_possibles.group(1)
            ten_duong = mat_tien_full_address_possibles.group('ten_duong')
            is_check_word = re.search('[a-zđ]',ten_duong, re.I)
            if not is_check_word:
                continue
            full_address = number + ' ' +  ten_duong
            full_address_unidecode = unidecode(full_address)
            if number not in deal_s:
                deal_s.append(number)
                sxs = re.search('x(?: |$)|^[x\d\s]+$',ten_duong, re.I) # có x trong tên đường
                if sxs:
                    continue
                ddm = re.search('(?:^|x|\*|\s)\s*\d+m',full_address, re.I)# check mét
                if ddm:
                    continue

                check_co_word = re.search('\D', full_address)
                if not check_co_word:
                    continue
                ten_duong_lower = ten_duong.strip().lower() 
                if ten_duong_lower in ['căn']:
                    continue
                pt = 'MT|Lầu|tỷ|căn|phòng|tấm|PN|WC|mặt|trệt|tầng|sẹc|sẹt|xẹc|xẹt|lửng|lững|trục đường|\dt\s*\dl'
                pt = unidecode(pt)
                is_mt = re.search(pt, full_address_unidecode, re.I)
                if is_mt:
                    continue
                bao_nhieu_met = re.search('\d+m|50/50', number)
                if bao_nhieu_met:
                    continue
                co_format_sdt = re.search('[\d\W]{6,}|3 Tháng 2|đi |thẳng ', full_address)
                if co_format_sdt:
                    continue
                if len(ten_duong) == 1:
                    continue
                index = mat_tien_full_address_possibles.span()[0]
                pre_index = index - 12
                if pre_index < 0:
                    pre_index = 0
                check_hem_string = html[pre_index:index]
                if check_hem_string:
                    is_hem = re.search('hẻm|hxt|đường|bđs|cty|nhà đất|vp|văn phòng|phường|quận', check_hem_string, re.I)
                    if is_hem:
                        continue
                full_adress_list.append((number, full_address))
    return full_adress_list

def detect_mat_tien_address_sum(html):
    #parent function call: _compute_mat_tien_or_trich_dia_chi
    full_adress_list_sum =  []
    number_list_sum = []
    addresses = {
    'html':{'value':html,
        'p':'(?<!cách )(?i:nhà|mt|mặt tiền|số)\s+(\d{1,4}[a-zA-Z]{0,2})[\s,]+(?i:đường)*\s*(?P<ten_duong>(?-i:[A-Z0-9Đ][\w|/]*\s*){1,4})(?:\.|\s|\,|$|<)'
        }, 
    }
    for key,val in addresses.items():
        html = val['value']
        p = val['p']
        if html:
            mat_tien_adress_list = detect_mat_tien_address(html, p)
            if mat_tien_adress_list:
                for number, full_address in mat_tien_adress_list:
                    if number not in number_list_sum:
                        full_adress_list_sum.append(full_address)
                        number_list_sum.append(number)
    mat_tien_address = False                  
    if full_adress_list_sum:
        mat_tien_address = ','.join(full_adress_list_sum)
    return mat_tien_address

def trim_street_name(street_name_may_be):
    #pr: detect_hem_address
    rs = re.sub(',|\.','', street_name_may_be, flags=re.I)
    rs = rs.strip()
    return rs

def detect_hem_address(address):
    #@pr: detect_hem_address_list
    keys_street_has_numbers = ['3/2','30/4','19/5','3/2.','3/2,','23/9']
    pat_247 = '24h*/7|24h*/24|1/500'
    trust_address_result_keys = []
    only_number_trust_address_result_keys = []
    co_date_247_result_keys=[]
    index_before = 0
    while 1:
        address = address[index_before:]
        posible_address_search = re.search('(?P<adress_number>\d+\w{0,2}/\d+\w{0,2}(?:/\d+\w{0,2})*)[\s,]+(?:đường[\s,]+)*(?P<ten_duong>(?:[\w|/]+\s*){1,4})(?:\.|\s|,|$)', address)
        if posible_address_search:
            index_before = posible_address_search.span()[1]
            adress_number = posible_address_search.group('adress_number')
            street_name = posible_address_search.group('ten_duong')
            street_name = trim_street_name(street_name)
            full_adress = adress_number +' ' + street_name
            if adress_number not in only_number_trust_address_result_keys:
                black_list = '23/23 Nguyễn Hữu Tiến|5 Độc Lập'
                black_list_rs = re.search(black_list, address, re.I)
                if black_list_rs:
                    only_number_trust_address_result_keys.append(adress_number)
                    continue
                if adress_number in ['1/2','50/100','100/100']:
                    continue
                rs = re.search(pat_247, adress_number, re.I)
                if rs:
                    co_date_247_result_keys.append(rs.group(0))
                    continue
                if adress_number in keys_street_has_numbers:
                    # street_result_keys.append(adress_number)
                    continue
                is_day = re.search('\d+/\d\d\d\d', adress_number)
                if is_day:
                    continue
                pnwc = re.search('(?:pn|wc|x)', adress_number, re.I)
                if pnwc:
                    continue
                is_ty_m2 =  re.search('tỷ|tr|m2', full_adress, re.I)
                if is_ty_m2:
                    continue
                
                index = posible_address_search.span()[0]
                before_index = index -20
                if before_index < 0:
                    before_index = 0
                before_string = address[before_index: index]
                is_van_phong = re.search('văn phòng|vp|bđs|nhà đất|[\d\W]{4,}', before_string, re.I)
                if is_van_phong:
                    continue
                trust_address_result_keys.append((adress_number, full_adress))
                only_number_trust_address_result_keys.append(adress_number)
        else:
            break
    return trust_address_result_keys, co_date_247_result_keys

def detect_hem_address_list(address_list):
    #pr: _compute_mat_tien_or_trich_dia_chi
    sum_full_hem_address = [] 
    only_number_address_sum_full_hem_address = [] 
    co_date_247_result_keys_sum = []
    for ad in address_list:
        trust_address_result_keys, co_date_247_result_keys = detect_hem_address(ad)
        co_date_247_result_keys_sum.extend(co_date_247_result_keys)
        for i in trust_address_result_keys:
            number_address = i[0]
            if number_address not in only_number_address_sum_full_hem_address:
                sum_full_hem_address.append(i)
                only_number_address_sum_full_hem_address.append(number_address)
    return sum_full_hem_address, co_date_247_result_keys_sum

def _compute_mat_tien_or_trich_dia_chi(self, html, html_trich_dia_chi, r):#compute
        mat_tien_address = detect_mat_tien_address_sum(html)
        trich_dia_chi = False
        address_list = [html_trich_dia_chi]
        sum_full_hem_address, co_date_247_result_keys_sum = detect_hem_address_list(address_list)
        if sum_full_hem_address:
            trich_dia_chi = ','.join(map(lambda i:i[1], sum_full_hem_address))
        mat_tien_or_trich_dia_chi = mat_tien_address or trich_dia_chi
        is_mat_tien_or_trich_dia_chi ='1' if  bool(mat_tien_or_trich_dia_chi) else '0'
        
        if trich_dia_chi:
            same_address_bds_ids  = self.env['bds.bds'].search([('trich_dia_chi','=ilike',trich_dia_chi),('id','!=',r.id)])
            same_address_bds_ids = [(6,0,same_address_bds_ids.mapped('id'))]
        else:
            same_address_bds_ids = False
        return mat_tien_address, trich_dia_chi, mat_tien_or_trich_dia_chi, is_mat_tien_or_trich_dia_chi, same_address_bds_ids

def _compute_mat_tien_or_trich_dia_chi1(self, html, html_trich_dia_chi):#compute
    mat_tien_address = detect_mat_tien_address_sum(html)
    trich_dia_chi = False
    address_list = [html_trich_dia_chi]
    sum_full_hem_address, co_date_247_result_keys_sum = detect_hem_address_list(address_list)
    if sum_full_hem_address:
        trich_dia_chi = ','.join(map(lambda i:i[1], sum_full_hem_address))
    mat_tien_or_trich_dia_chi = mat_tien_address or trich_dia_chi
    is_mat_tien_or_trich_dia_chi ='1' if  bool(mat_tien_or_trich_dia_chi) else '0'
    return mat_tien_address, trich_dia_chi, mat_tien_or_trich_dia_chi, is_mat_tien_or_trich_dia_chi


def compute_t1l1_detect(html):
    #@pr: _compute_kw_mg
    t1l1_list = []
    pt = '(1t[,\s]*(\d{1,2})l)(?:\W|$)'
    rs = re.search(pt, html, re.I)
    if rs:
        t1l1_list.append(rs.group(1))
    pt = '((\d{1,2})\s*pn)(?:\W|$)'
    rs = re.search(pt, html, re.I)
    if rs:
        t1l1_list.append(rs.group(1))
    pt = '(?:\W|^)(st)(?:\W|$)'
    rs = re.search(pt, html, re.I)
    if rs:
        t1l1_list.append(rs.group(1))
        
    return t1l1_list


def _compute_kw_mg( html):
        found_kw_mgs = []
        pat_247 = '24h*/7|(?<!an ninh )24h*/24|1/500'
        rs = re.search(pat_247, html, re.I)
        kw_co_date = False #1
        if rs:
            found_kw_mgs.append(rs.group(0))
            kw_co_date = rs.group(0)
        nha_dat_kws_cap_1 = 'nhà đất(?! thánh)|uy tín|real|bds|bđs|cần tuyển|tuyển sale|tuyển dụng|bất động sản|bđs|ký gửi|kí gửi|'+\
        '(?<!nova)land(?!mark|abc)|tư vấn|(?:thông tin|sản phẩm) (?:chính xác|thật)|' +\
        'xem nhà miễn phí|(?:hổ|hỗ) trợ miễn phí|khách hàng|' +\
        'hỗ trợ[\w\s]{0,20}pháp lý|hợp.{1,20}đầu tư|csht|tttm|'+\
        'chưa qua đầu tư|cấp 1[,\- ]*2[,\- ]*3|'+\
        'tiện kinh doanh[ ,]{1,2}buôn bán[ ,]{1,2}mở công ty[ ,]{1,2}văn phòng|nợ ngân hàng|hợp tác|thanh lý' 

     
        nha_dat_list_rs = re.findall(nha_dat_kws_cap_1, html, re.I)
        if nha_dat_list_rs:
            found_kw_mgs.extend(nha_dat_list_rs)

        mtg_kws = 'mmg|mqc|mtg|(?-i:MTKD)|(?-i:BTCT)|(?-i:CHDV)|(?-i:DTSD)|(?:.{0,10}cho khách?:.{0,10})|(?:khu vực an ninh|dân trí cao)\W{1,3}(?:khu vực an ninh|dân trí cao)'
        nha_dat_list_rs = re.findall(mtg_kws, html, re.I)
        kw_mg_cap_2 = False #2
        is_kw_mg_cap_2 = False#3
        if nha_dat_list_rs:
            kw_mg_cap_2 = ','.join(nha_dat_list_rs)
            is_kw_mg_cap_2 = True

        break_kw = '(\n✓|\n\*)'
        break_rs = re.findall(break_kw, html, re.I)
        kw_co_special_break = False # 4
        if break_rs:
            len_break_rs = len(break_rs)
            kw_co_special_break = len_break_rs
       
        break_kw = '(\n)'
        break_rs = re.findall(break_kw, html, re.I)
        kw_co_break = False # 5
        if break_rs:
            len_break_rs = len(break_rs)
            kw_co_break = len_break_rs
        number_char = len(html)
        hoa_la_canh_pt = '🏠|💥|✅|👉🏻|⭐️|💵|💰|☎️|⚡|📲|💎|🌹|☎|🌈|🍎|🍏|🏦|📣|🆘|☎️|🤝|👍|👉|' +\
            '🏡|🗽|🎠|🏖|😍|🔥'
        nha_dat_list_rs = re.findall(hoa_la_canh_pt, html, re.I)
        hoa_la_canh = False # 6
        if nha_dat_list_rs:
            hoa_la_canh = len(nha_dat_list_rs)
        t1l1_list = compute_t1l1_detect(html)
        t1l1 = False #7
        if t1l1_list:
            t1l1 = ','.join(t1l1_list)
        kw_mg = False #8
        dd_tin_cua_co = 'no_kw_co_cap_1' # 9
        if found_kw_mgs:
            kw_mg = ','.join(found_kw_mgs)
            dd_tin_cua_co = 'kw_co_cap_1'

        return kw_co_date, kw_mg_cap_2, is_kw_mg_cap_2, kw_co_special_break, kw_co_break,\
                hoa_la_canh, t1l1, kw_mg, dd_tin_cua_co

def str_before_index(index, input_str):
    #@pr: _compute_dd_tin_cua_dau_tu
    pre_index = index - 30
    if pre_index < 0:
        pre_index = 0
    pre_str = input_str[pre_index:index]
    return pre_str

def _compute_dd_tin_cua_dau_tu(html):
        p = '((?<=\W)(?:hoa hồng|hh(?!t)|huê hồng|🌹)\s*(?:cho)*\s*(?:mg|môi giới|mô giới|TG|Trung gian)*\s*(?:\D|\s){0,31}((\d|\.)+\s*(%|triệu|tr))*)(?:\s+|$|<|\.|)'
        rs = re.search(p, html, re.I)
        if not rs:
            p = '((?:phí(?! hh| hoa hồng| huê hồng|\w)|chấp nhận)\s*(?:cho)*\s*(?:mg|môi giới|mô giới|TG|Trung gian)*\s*((\d|\.)+\s*(%|triệu|tr))*)(?:\s+|$|<|\.|)'
            rs = re.search(p, html, re.I)
        kw_hoa_hong, kw_so_tien_hoa_hong, dd_tin_cua_dau_tu = False, False, False
        if rs:
            for i in [1]:
                index = rs.span()[0]
                pre_str = str_before_index(index, html)
                khong_cho_mg = re.search('không|ko', pre_str, re.I)
                if khong_cho_mg:
                    continue
                kw_hoa_hong_tach = rs.group(1)
                kw_hoa_hong_tach = kw_hoa_hong_tach.strip().lower()
                if kw_hoa_hong_tach in  ['phí', 'chấp nhận']:
                    continue
                kw_hoa_hong = kw_hoa_hong_tach
                kw_so_tien_hoa_hong = rs.group(2)
                dd_tin_cua_dau_tu = True
        else:
            rs = re.search('((1)%)', html, re.I)
            if rs:
                kw_hoa_hong = rs.group(1)
                kw_so_tien_hoa_hong = rs.group(2)
                dd_tin_cua_dau_tu = True
        return kw_hoa_hong, kw_so_tien_hoa_hong, dd_tin_cua_dau_tu


def detect_is_mat_tien(html):
    #@pr: _compute_loai_hem_combine
    while 1:
        p = '(?:(?<!2 )mặt tiền|nhà mt|mặt phố)(?! hẻm)'
        rs = re.search(p, html, re.I)
        hxh_str, full_hxh,is_mat_tien = False,False,False
        if rs:
            span0 = rs.span(0)[0]
            pre_index = span0-10
            if pre_index<0:
                pre_index = 0
            pre = html[pre_index:span0]
            gan_sat_cach_pt = 'gần|sát|cách|hai|từ|ra|sau lưng|hai'
            gan_sat_cach_search = re.search(gan_sat_cach_pt,pre, re.I)
            if gan_sat_cach_search:
                before_index = rs.span()[1] + 1
                html = html[before_index:]
                continue
            hxh_str = rs.group(0)
            full_before_index = rs.span(0)[1] + 10
            full_hxh = html[pre_index:full_before_index]
            is_mat_tien = True
            return hxh_str, full_hxh, is_mat_tien
        else:
            return hxh_str, full_hxh, is_mat_tien        




def cach_search(pre):
    #pr: detect_hem_rong()
    gan_sat_cach_pt = 'cách'
    gpxd_search = re.search(gan_sat_cach_pt,pre, re.I)
    return gpxd_search

def previous_of_match(html, rs_group, previous_char_number = 30):
    #pr: detect_hem_rong()
    span0 = rs_group.span(0)[0]
    pre_index = span0-previous_char_number
    pre = html[pre_index:span0]
    return pre
    
def detect_hem_rong(html):
    #@pr: _compute_loai_hem_combine
    while 1:
        pt = '(?<!cách )(?:hẻm|hẽm|đường)\s+(?:trước nhà)*\s*(?:xh|xe hơi|ô tô|xe máy|kia|ba gác|ba gát)*\s*(?:trước nhà)*\s*(?:nhỏ)*\s*(?:rộng)*\s*(?:khoảng|tầm)*\s*(\d+(?:\.|m|mét|,)*\d*)\s*(?:m|mét)*(?:\W|$)'
        rs = re.search(pt, html, re.I)
        if rs:
            pre = previous_of_match(html, rs)
            cach_search_rs = cach_search(pre)
            if cach_search_rs:
                before_index = rs.span(0)[1] + 1
                html = html[before_index:]
                continue
            else:
                hem_rong_char, hem_rong = rs.group(0), rs.group(1)
                hem_rong = re.sub('mét|mét|m|,','.',hem_rong, flags=re.I)
                hem_rong = re.sub('\.+','.',hem_rong)
                hem_rong = float(hem_rong)
                return hem_rong_char, hem_rong
        else:
            return False, False

def detect_hxh(html):
    #@pr:detect_loai_hem
    p = '(?:h|hẻm|hẽm|d|đ|đường)\s{0,1}(?:xh|xe hơi|oto|ô tô)'
    rs = re.search(p, html, re.I)
    hxh_str, full_hxh = False,False
    if rs:
        span0 = rs.span(0)[0]
        pre_index = span0-30
        if pre_index<0:
            pre_index = 0
        pre = html[pre_index:span0]
        gan_sat_cach_pt = 'gần|sát|cách'
        gan_sat_cach_search = re.search(gan_sat_cach_pt,pre, re.I)
        if gan_sat_cach_search:
            return hxh_str, full_hxh
        before_index = span0 + 10
        full_hxh = html[pre_index:before_index]
        hxh_str = rs.group(0)
    return hxh_str, full_hxh

def detect_hxt(html):
    #@pr:detect_loai_hem
    p = '(?:h|hẻm|hẽm|d|đ|đường)\s{0,1}(?:xt|xe (?:tải|tãi))'
    rs = re.search(p, html, re.I)
    hxh_str, full_hxh = False,False
    if rs:
        span0 = rs.span(0)[0]
        pre_index = span0-30
        pre = html[pre_index:span0]
        gan_sat_cach_pt = 'gần|sát|cách'
        gan_sat_cach_search = re.search(gan_sat_cach_pt,pre, re.I)
        if gan_sat_cach_search:
            return hxh_str, full_hxh
        before_index = span0 + 10
        full_hxh = html[pre_index:before_index]
        hxh_str = rs.group(0)
    return hxh_str, full_hxh
    
def detect_hxm(html):
    #@pr:detect_loai_hem
    p = '(?:h|hẻm|hẽm)\s{0,1}(?:xm|xe (?:máy))'
    rs = re.search(p, html, re.I)
    hxh_str, full_hxh = False,False
    if rs:
        span0 = rs.span(0)[0]
        pre_index = span0-30
        pre = html[pre_index:span0]
        gan_sat_cach_pt = 'gần|sát|cách'
        gan_sat_cach_search = re.search(gan_sat_cach_pt,pre, re.I)
        if gan_sat_cach_search:
            return hxh_str, full_hxh
        before_index = span0 + 10
        full_hxh = html[pre_index:before_index]
        hxh_str = rs.group(0)
    return hxh_str, full_hxh
    
def detect_hbg(html):
    #@pr:detect_loai_hem
    p = '(?:h|hẻm|hẽm)\s{0,1}(?:bg|ba (?:gát|gác))'
    rs = re.search(p, html, re.I)
    hxh_str, full_hxh = False,False
    if rs:
        span0 = rs.span(0)[0]
        pre_index = span0-30
        pre = html[pre_index:span0]
        gan_sat_cach_pt = 'gần|sát|cách'
        gan_sat_cach_search = re.search(gan_sat_cach_pt,pre, re.I)
        if gan_sat_cach_search:
            return hxh_str, full_hxh
        before_index = span0 + 10
        full_hxh = html[pre_index:before_index]
        hxh_str = rs.group(0)
    return hxh_str, full_hxh


def detect_loai_hem(html):
    loai_hem_selection = False
    loai_hem, full_loai_hem = detect_hxh(html)
    if loai_hem:
        loai_hem_selection = 'hxh'
    else:
        loai_hem,  full_loai_hem = detect_hxt(html)
        if loai_hem:
            loai_hem_selection = 'hxt'
        else:
            loai_hem,  full_loai_hem = detect_hxm(html)
            if loai_hem:
                loai_hem_selection = 'hxm'
            else:
                loai_hem,  full_loai_hem = detect_hbg(html)
                if loai_hem:
                    loai_hem_selection = 'hbg'
    return full_loai_hem, loai_hem_selection

def _compute_loai_hem_combine(html):
        mat_tien, full_mat_tien, is_mat_tien = detect_is_mat_tien(html)
        hem_rong_char, hem_rong = detect_hem_rong(html)
        full_loai_hem, loai_hem_selection = detect_loai_hem(html)
        loai_hem_combine = loai_hem_selection
        if not loai_hem_selection:
            if is_mat_tien:
                loai_hem_combine = 'mt'
            elif hem_rong:
                if hem_rong > 10:
                    loai_hem_combine = 'mt'
                elif hem_rong >= 6:
                    loai_hem_combine = 'hxt'
                elif hem_rong >= 4:
                    loai_hem_combine = 'hxh'
                elif hem_rong >= 2.5:
                    loai_hem_combine = 'hbg'
                elif hem_rong:
                    loai_hem_combine = 'hxm'
        return mat_tien, full_mat_tien, is_mat_tien,hem_rong_char, hem_rong, full_loai_hem, loai_hem_selection, loai_hem_combine
