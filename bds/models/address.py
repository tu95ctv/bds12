# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from .poster import Jsonb
import operator
class Address(models.Model):
    _name = 'bds.address'

    name = fields.Char()
    count = fields.Integer()
    one_site_count_max = fields.Integer()
    bds_ids_dict = Jsonb(default="{}")
    user_ids_dict = Jsonb(default="{}")
    count_dict = Jsonb(default="{}")
    bds_ids_list = fields.Char()
    user_ids_list = fields.Char()


    def write_address_to_table(self, mat_tien_or_trich_dia_chi, siteleech_id, bds_id, poster_id):
        mat_tien_or_trich_dia_chis =mat_tien_or_trich_dia_chi.split(',')
        for mat_tien_or_trich_dia_chi in mat_tien_or_trich_dia_chis:
            name = mat_tien_or_trich_dia_chi.upper()
            r = self.search([('name','=', name)])
            if r:
                r.count = r.count + 1
                count_dict = r.count_dict
                val = count_dict.get(str(siteleech_id), 0)
                val +=1
                count_dict[str(siteleech_id)] = val
                r.count_dict = count_dict
                r.one_site_count_max = max(count_dict.items(), key=operator.itemgetter(1))[1]
            else:
                self.create({'name':name, 'count':1, 'one_site_count_max':1,
                            'count_dict':{str(siteleech_id):1},
                            'bds_ids_dict': {str(siteleech_id):[bds_id]},
                            'user_ids_dict': {str(siteleech_id):[poster_id]},
                            })