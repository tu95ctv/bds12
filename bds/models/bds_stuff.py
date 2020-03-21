# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api

class Setread(models.TransientModel):
    _name = "bds.setread"
    
    @api.multi
    def set_bdsread(self):
        print ('self._context',self._context,'self._context.get("active_ids")',self._context.get("active_ids"))
        self.env['bds.bds'].browse(self._context.get("active_ids")).write({'is_read':True})
        return {
                'type': 'ir.actions.act_window',
                'res_model': 'bds.setread',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.id,
                'views': [(False, 'form')],
                'target': 'new',
            }

    
class Images(models.Model):
    _name='bds.myimage'
    image = fields.Binary(attachment=True)
    name = fields.Char()
    bds_id = fields.Many2one('bds.bds')
    

class Gialines(models.Model):
    _name='bds.gialines'
    gia = fields.Float()
    bds_id = fields.Many2one('bds.bds')
    gia_cu = fields.Float()
    diff_gia = fields.Float()
    

class Publicdate(models.Model):
    _name='bds.publicdate'
    public_date_cu = fields.Date()
    bds_id = fields.Many2one('bds.bds')
    public_date = fields.Date()
    diff_public_date = fields.Integer()


class SiteDuocLeech(models.Model):
    _name = 'bds.siteleech'
    name = fields.Char() 
    name_viet_tat = fields.Char()  

    
class Images(models.Model):
    _name = 'bds.images'
    url = fields.Char()
    bds_id = fields.Many2one('bds.bds')


