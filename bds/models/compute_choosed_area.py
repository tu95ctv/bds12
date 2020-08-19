# -*- coding: utf-8 -*-
import re
import base64
from unidecode import unidecode
from odoo.addons.bds.models.main_fetch_common1  import previous_of_match


def tim_dien_tich_trong_bai(html):
    p ='(?:diện tích|dt|dtcn)[\W]*([1-9]+[\.,]\d+)\s*m2'
    rs = re.search(p, html, re.I)
    dt = 0
    if rs:
        dt = rs.group(1)
        dt = dt.replace(',','.')
        dt = float(dt)
    return dt

def tim_dien_tich_sd_trong_bai(html):
    dt = 0
    while 1:
        p ='(?:(?:diện tích|dt)\s*(?:sử dụng|sd|sàn|xd))[\W]*([0-9]+[\.,]*\d*)\s*m2'
        rs = re.search(p, html, re.I)
        if rs:
            span0 = rs.span(0)[0]
            span1 =  rs.span(0)[1]
            pre_index = span0-50
            if pre_index<0:
                pre_index = 0
            pre = html[pre_index:span0]
            gan_sat_cach_pt = 'gpxd|giấy phép xây dựng'
            gpxd_search = re.search(gan_sat_cach_pt,pre, re.I)
            if gpxd_search:
                before_index = span1 + 1
                html = html[before_index:]
                continue
            else:
                dt = rs.group(1)
                dt = dt.replace(',','.')
                dt = float(dt)
                return dt
        else:
            return dt

def tim_dai_rong(html):
    auto_ngang, auto_doc = 0,0
    pt= '(\d{1,3}[\.,m]{0,1}\d{0,2}) {0,1}m{0,1}(( {0,1}[x*] {0,1}))(\d{1,3}[\.,m]{0,1}\d{0,2})'
    rs = re.search(pt, html,flags = re.I)
    
    if rs:
        auto_ngang, auto_doc = float(rs.group(1).replace(',','.').replace('m','.').replace('M','.')),float(rs.group(4).replace(',','.').replace('m','.').replace('M','.'))
    elif not rs:
        pt= '(dài|rộng|ngang)[: ]{1,2}(\d{1,3}[\.,m]{0,1}\d{0,2}) {0,1}m{0,1}(([\W]{1,3}(dài|rộng|ngang)[: ]{1,2}))(\d{1,3}[\.,m]{0,1}\d{0,2})'
        rs = re.search(pt, html,flags = re.I)
        if rs:
            auto_ngang, auto_doc = float(rs.group(2).replace(',','.').replace('m','.').replace('M','.')),float(rs.group(6).replace(',','.').replace('m','.').replace('M','.'))
    return auto_ngang, auto_doc

def auto_ngang_doc_compute(html,rarea):
    auto_ngang, auto_doc = tim_dai_rong(html)
    dien_tich_trong_topic = tim_dien_tich_trong_bai(html)
    choose_area = 0
    auto_dien_tich = 0
    ti_le_dien_tich_web_vs_auto_dien_tich = 0
    if auto_ngang and auto_doc:
        auto_dien_tich = auto_ngang*auto_doc
        ti_le_dien_tich_web_vs_auto_dien_tich = rarea/auto_dien_tich
        if rarea ==0:
            choose_area = auto_dien_tich 
        elif ti_le_dien_tich_web_vs_auto_dien_tich > 1.4 and ti_le_dien_tich_web_vs_auto_dien_tich < 5:
            choose_area = auto_dien_tich
        else:
            choose_area = rarea
    else:
        choose_area = rarea or dien_tich_trong_topic
    return auto_ngang, auto_doc, auto_dien_tich, choose_area, ti_le_dien_tich_web_vs_auto_dien_tich,  dien_tich_trong_topic

def gpxd_search(pre):
    gan_sat_cach_pt = 'gpxd|giấy phép xây dựng'
    gpxd_search = re.search(gan_sat_cach_pt,pre, re.I)
    return gpxd_search

def detect_only_lau(html, pt = '(\d{1,2})\s*(?:lầu|l)(?:\W|$)'):
    while 1:
        rs = re.search(pt, html, re.I)
        so_lau = 0
        so_lau_char = False
        if rs:
            pre = previous_of_match(html, rs)
            gpxd_search_rs = gpxd_search(pre)
            if gpxd_search_rs:
                before_index = rs.span(0)[1] + 1
                html = html[before_index:]
                continue
            else:
                so_lau = rs.group(1)
                so_lau_char = rs.group(0)
                try:
                    so_lau = int(so_lau)
                except:
                    so_lau = 0
                return so_lau, so_lau_char
        else:
            return so_lau, so_lau_char

def detect_lung_only(html, pt = 'lửng|lững'):
    while 1:
        is_lung = False
        rs = re.search(pt, html, re.I)
        so_lau = 0
        so_lau_char = False
        if rs:
            pre = previous_of_match(html, rs)
            gpxd_search_rs = gpxd_search(pre)
            if gpxd_search_rs:
                before_index = rs.span(0)[1] + 1
                html = html[before_index:]
                continue
            else:
                is_lung = True
                return is_lung
        else:
            return is_lung

def detect_lau_tranh_gpxd(html):
    so_lau, so_lau_char = detect_only_lau(html)
    if not so_lau:
        so_lau, so_lau_char = detect_only_lau(html, pt = '(\d{1,2})\s*(?:tầng)(?:\W|$)')
        if so_lau:
            so_lau = so_lau -1
    so_lau_he_so = so_lau
    is_lung = detect_lung_only(html)
    if is_lung:
        so_lau +=0.5
        so_lau_he_so +=0.7

    is_st = detect_lung_only(html, pt = 'sân thượng')
    if is_st:
        so_lau +=1
        so_lau_he_so +=0.5
    return so_lau, so_lau_char, so_lau_he_so

def detect_lau(html):
    pt = '(\d{1,2})\s*(?:lầu|l)(?:\W|$)'
    rs = re.search(pt, html, re.I)
    so_lau = 0
    so_lau_char = False
    
    if rs:
        so_lau = rs.group(1)
        so_lau_char = rs.group(0)
        try:
            so_lau = int(so_lau)
        except:
            so_lau = 0
    else:
        pt = '(\d{1,2})\s*(?:tầng)(?:\W|$)'
        rs = re.search(pt, html, re.I)
        if rs:
            so_lau = rs.group(1)
            so_lau_char = rs.group(0)
            try:
                so_lau = int(so_lau)
            except:
                so_lau = 0
        else:
            pt = '(cấp 4|c4|c4)\W'
            rs = re.search(pt, html, re.I)
            if rs:
                so_lau = 0.1
                so_lau_char = rs.group(1)


                
    so_lau_he_so = so_lau
    pt = 'lửng|lững'
    rs = re.search(pt, html, re.I)
    if rs:
        so_lau +=0.5
        so_lau_he_so +=0.7

    pt = 'sân thượng'
    rs = re.search(pt, html, re.I)
    if rs:
        so_lau +=1
        so_lau_he_so +=0.5

    return so_lau, so_lau_char, so_lau_he_so

def _compute_muc_gia(gia):
        muc_gia_list = [('0','0'),('<1','<1'),('1-2','1-2'),('2-3','2-3'),
            ('3-4','3-4'),('4-5','4-5'),('5-6','5-6'),('6-7','6-7'),('7-8','7-8'),('8-9','8-9'),('9-10','9-10'),('10-11','10-11'),('11-12','11-12'),('>12','>12')]
        selection = None
        for muc_gia_can_tren in range(0,len(muc_gia_list)):
            if gia <= muc_gia_can_tren:
                selection = muc_gia_list[muc_gia_can_tren][0]
                break
        if not selection:
            selection = muc_gia_list[-1][0]
        return selection

def muc_don_gia_(don_gia):
    muc_dt_list =[('0','0'),('0-30','0-30'),('30-60','30-60'),('60-90','60-90'),
                                ('90-120','90-120'),('120-150','120-150'),('150-180','150-180'),('180-210','180-210'),('>210','>210')]
    selection = None
    for muc_gia_can_tren in range(0,8):
        if don_gia <= muc_gia_can_tren*30:
            selection = muc_dt_list[muc_gia_can_tren][0]
            break
    if not selection:
        selection = muc_dt_list[-1][0]
    return selection

def muc_ti_le_don_gia_(ti_le_don_gia):
    muc_dt_list =[('0','0'), ('0-0.4','0-0.4'),('0.4-0.8','0.4-0.8'),('0.8-1.2','0.8-1.2'),
                                ('1.2-1.6','1.2-1.6'), ('1.6-2.0','1.6-2.0'), ('2.0-2.4','2.0-2.4'), ('2.4-2.8','2.4-2.8'), ('>2.8','>2.8')]
    selection = None
    for muc_gia_can_tren in range(0,8):
        if ti_le_don_gia <= muc_gia_can_tren*0.4:
            selection = muc_dt_list[muc_gia_can_tren][0]
            break
    if not selection:
        selection = muc_dt_list[-1][0]
    return selection
    
def _muc_dt(choose_area):
        muc_dt_list = [('0','0'), ('<10','<10'),('10-20','10-20'),('20-30','20-30'),('30-40','30-40'),('40-50','40-50'),('50-60','50-60'),('60-70','60-70'),('>70','>70')]
        selection = None
        for muc_gia_can_tren in range(0,8):
            if choose_area <= muc_gia_can_tren*10:
                selection = muc_dt_list[muc_gia_can_tren][0]
                break
        if not selection:
            selection = muc_dt_list[-1][0]
        return selection

def _compute_choosed_area_muc_gia(html, gia, area, quan_id, loai_hem_combine):
        auto_ngang, auto_doc, auto_dien_tich, choose_area, ti_le_dien_tich_web_vs_auto_dien_tich,  dien_tich_trong_topic = \
                auto_ngang_doc_compute(html, area)
        dtsd = tim_dien_tich_sd_trong_bai(html)
        so_lau, so_lau_char, so_lau_he_so =  detect_lau_tranh_gpxd(html)
        ti_le_dtsd = False
        dtsd_tu_so_lau = 0
        dtsd_he_so_lau = 0

        allow_loop = 2
        while allow_loop:
            allow_loop -=1
            if so_lau:
                dtsd_tu_so_lau = (so_lau + 1) * choose_area * 0.9
                dtsd_he_so_lau = (so_lau_he_so + 1) * choose_area * 0.9 
                if so_lau_he_so < 2:
                    dtsd_he_so_lau = dtsd_he_so_lau * 0.5
                if dtsd and choose_area:
                    ti_le_dtsd = dtsd_tu_so_lau / dtsd
            dtsd_combine = dtsd or dtsd_tu_so_lau
            dtsd_combine_he_so_lau = dtsd_he_so_lau or dtsd
            if not dtsd_combine_he_so_lau:
                dtsd_combine_he_so_lau =  choose_area * 0.5
            gia_xac_nha = dtsd_combine_he_so_lau * 0.006
            gia_dat_con_lai = 0
            don_gia_dat_con_lai = 0
            if gia > 0.2 and gia_xac_nha:
                gia_dat_con_lai = gia - gia_xac_nha
                if choose_area:
                    don_gia_dat_con_lai = 1000 * gia_dat_con_lai / choose_area
            don_gia = 0
            if gia > 0.5 and choose_area:
                don_gia = gia*1000/choose_area

            # muc gia quan vao day
            don_gia_quan = 0
            ti_le_don_gia_dat_con_lai = 0

            if loai_hem_combine and don_gia_dat_con_lai:
                if loai_hem_combine =='mt':
                    loai_hem_combine = 'mat_tien'
                else:
                    loai_hem_combine = loai_hem_combine
                attr = 'don_gia_%s'%loai_hem_combine
                don_gia_quan = getattr(quan_id, attr)
                if not don_gia_quan:
                    don_gia_quan = getattr(quan_id, attr + '_tc')

            
            if not don_gia_quan:
                don_gia_quan = quan_id.muc_gia_quan or quan_id.don_gia_hbg_tc

            if don_gia_quan:
                ti_le_don_gia_dat_con_lai = don_gia_dat_con_lai/don_gia_quan

            if ti_le_don_gia_dat_con_lai != 0 and ti_le_don_gia_dat_con_lai < 0.3:
                if choose_area and so_lau:
                    choose_area = choose_area/(so_lau + 1) # cho lập lại khi choose_area được gán lại
                    continue
                else:
                    break
            else:
                break

        ti_le_don_gia = ti_le_don_gia_dat_con_lai
        muc_ti_le_don_gia = muc_ti_le_don_gia_(ti_le_don_gia)   
        muc_don_gia = muc_don_gia_(don_gia)  
        muc_dt = _muc_dt(choose_area)
        muc_gia = _compute_muc_gia(gia)

        return don_gia_quan, ti_le_don_gia_dat_con_lai, ti_le_don_gia, \
            auto_ngang, auto_doc, auto_dien_tich, ti_le_dien_tich_web_vs_auto_dien_tich, \
            dtsd, choose_area, so_lau, so_lau_char, so_lau_he_so,\
            dtsd_tu_so_lau, ti_le_dtsd, dtsd_combine, gia_xac_nha,\
            gia_dat_con_lai, don_gia_dat_con_lai, don_gia, muc_don_gia,\
            muc_ti_le_don_gia, muc_dt, muc_gia