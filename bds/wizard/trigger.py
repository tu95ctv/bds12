# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Trigger(models.TransientModel):
    _name = 'bds.trigger'
    _description = 'Trigger'

    offset = fields.Integer()
    limit = fields.Integer()
    count = fields.Integer()
    trigger_value = fields.Boolean(default=True)


    def search_method(self):
        args = [[]]
        kwargs = {}
        if self. limit:
            kwargs = {'limit':self. limit}
        if self.offset:
            kwargs = {'offset':self. offset}
        return args, kwargs

    @api.multi
    def count_from_search(self):
        args, kwargs = self.search_method()
        # self.count = self.env['bds.bds'].search_count(*args, **kwargs)
        bds = self.env['bds.bds'].search(*args, **kwargs)
        bds.write({'trigger': self.trigger_value})
        return  {
                'type': 'ir.actions.act_window',
                'res_model': 'bds.trigger',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.id,
                # 'context':{'active_model':self.model, 'function_key': self.function_key},
                'views': [(False, 'form')],
                'target': 'new',
            }
        # self.env['bds.bds'].search(*args, kwargs)