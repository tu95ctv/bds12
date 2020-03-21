# -*- coding: utf-8 -*-

from odoo import models, fields, api
# from odoo.addons.bds.models.fetch import fetch

class loop_fetch_cron(models.Model):
    _name = 'loop.fetch.cron'
    fetch_ids = fields.Many2many('bds.fetch',required=True)
    fetch_current_id = fields.Many2one('bds.fetch')
    
    def fetch_cron(self):
        loop_fetch_cron_id =  self.search([], limit=1, order='id desc')
        if loop_fetch_cron_id:
            fetch_ids = loop_fetch_cron_id.fetch_ids
            if fetch_ids:
                if loop_fetch_cron_id.fetch_current_id:
                    try:
                        index_of_last_fetched_url_id = fetch_ids.ids.index( loop_fetch_cron_id.fetch_current_id.id)
                        new_index =  index_of_last_fetched_url_id+1
                    except ValueError:
                        new_index = 0
                else:
                    new_index =0
                if new_index > len(fetch_ids)-1:
                    new_index = 0    
                fetch_id = fetch_ids[new_index]
                try:
                    fetch_id.fetch_all_url()
                    loop_fetch_cron_id.fetch_current_id = fetch_id.id
                except Exception as e:
                    self.env['bds.error'].create({'name':str(e), 'des': 'id:%s - name:%s'(fetch_id.id, fetch_id.name)})
            else:
                raise ValueError('khong ton tai: fetch_ids')
        else:
            raise ValueError('khong ton tai loop_fetch_cron nao ca ')