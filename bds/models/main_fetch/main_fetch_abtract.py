# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.addons.bds.models.main_fetch.main_fetch_common1 import MainFetchCommon
class AbstractFetch(models.AbstractModel, MainFetchCommon):
    _name = 'abstract.main.fetch'