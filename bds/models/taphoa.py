# -*- coding: utf-8 -*-
from odoo import models, fields, api,sql_db, tools

class Taphoa(models.Model):
    _name = 'tap.hoa'
    _order = "id desc"
    # _rec_name = 'title'
    
    html = fields.Text()
    tinh = fields.Char()
    quan = fields.Char()
    phuong = fields.Char()
    duong = fields.Char()
    link = fields.Char()
    poster_id = fields.Char()
    address = fields.Char()
    title = fields.Char()
    name_of_poster = fields.Char()
    public_date = fields.Date()
    ngay_thanh_lap = fields.Char()
    nganh_nghe_kinh_doanh = fields.Char()
    ngay_thanh_lap = fields.Char()
    mst = fields.Char()
    is_full_topic = fields.Boolean()
