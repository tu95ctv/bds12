# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_detail_guest = fields.Boolean(string='group detail guest', implied_group='bds.detail_guest')
    interval_mail_chinh_chu_minutes = fields.Integer()
    gia = fields.Float(digits=(6,2))
    email_to = fields.Char()
    khong_hien_thi_nhieu_html = fields.Boolean()
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['interval_mail_chinh_chu_minutes'] = int(self.env['ir.config_parameter'].sudo().get_param('bds.interval_mail_chinh_chu_minutes',default=0))
        res['gia'] = float(self.env['ir.config_parameter'].sudo().get_param('bds.gia',default=0))
        res['email_to'] = self.env['ir.config_parameter'].sudo().get_param('bds.email_to')
        res['khong_hien_thi_nhieu_html'] = self.env['ir.config_parameter'].sudo().get_param('bds.khong_hien_thi_nhieu_html')
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('bds.interval_mail_chinh_chu_minutes', self.interval_mail_chinh_chu_minutes)
        self.env['ir.config_parameter'].sudo().set_param('bds.gia', self.gia)
        self.env['ir.config_parameter'].sudo().set_param('bds.email_to', self.email_to)
        self.env['ir.config_parameter'].sudo().set_param('bds.khong_hien_thi_nhieu_html', self.khong_hien_thi_nhieu_html)
        super(ResConfigSettings, self).set_values()



  