# -*- coding: utf-8 -*-
import xlrd
import base64
def import_contact(self):
    recordlist = base64.decodestring(self.file)
    excel = xlrd.open_workbook(file_contents = recordlist)
    sheet = excel.sheet_by_index(0)
    full_name_index = 2
    phone_index = 4
    
    land_contact_saved_number = 0
    for row in range(2,sheet.nrows):
        full_name = sheet.cell_value(row,full_name_index)
        phone = sheet.cell_value(row,phone_index)
        phone = phone.replace('(Mobile)','').replace('(Home)','').replace('(Other)','').replace(' ','').replace('+84','0')
        ###print phone,full_name
        rs_mycontact  = self.env['bds.mycontact'].search([('phone','=',phone)])
        if rs_mycontact:
            if rs_mycontact.name != full_name:
                rs_mycontact.write({'name':full_name})
        else:
            rs_mycontact = self.env['bds.mycontact'].create({'name':full_name,'phone':phone})
        rs_user = self.env['bds.poster'].search([('phone','=',phone)])
        if rs_user:
            land_contact_saved_number +=1
            rs_user.write({'ten_luu_trong_danh_ba':full_name,'mycontact_id':rs_mycontact.id})
    self.land_contact_saved_number = land_contact_saved_number