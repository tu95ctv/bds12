# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Error(models.Model):
    _name = 'bds.error'
    _order = 'id desc'
    name = fields.Char()
    des = fields.Char()
    fetch_item_id = fields.Many2one('bds.fetch.item')
    type = fields.Selection([('fetch_error', 'fetch_error'), ('internal_error', 'internal_error')
        , ('success', 'success')])
    link = fields.Char()
    link_type = fields.Selection([('topic', 'topic'), ('page', 'page'), ('web_last_page', 'web_last_page')])
    error_or_success = fields.Selection([('error', 'error'), ('success', 'success')], default='error')
    
    