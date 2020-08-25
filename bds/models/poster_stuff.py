# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api

class PosterNameLines(models.Model):
    _name = 'bds.posternamelines'
    username_in_site = fields.Char()
    site_id = fields.Many2one('bds.siteleech')
    poster_id = fields.Many2one('bds.poster')

    
