# -*- coding: utf-8 -*-
{
    'name': "bds",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',

        'data/data_chotot_chung_cu.xml',
        'data/data_chotot_other.xml',
        'data/data_chotot_phuong.xml',
        'data/data_chotot.xml',
        'data/data_muaban.xml',
        'data/cronjob_data.xml',

        'views/bds_images.xml',
        'views/cron.xml',
        'views/fetch.xml',
        'views/bds_search.xml',
        'views/bds_form.xml',
        'views/bds_list.xml',
        'views/poster.xml',
        'views/quan.xml',
        'views/error.xml',
        'views/url.xml',
        'views/laptop.xml',
        'views/get_phone_poster.xml',
        'views/ir_actions_server.xml',
        'views/res_config_settings_views.xml',

        'views/menu.xml',

    ],
    
}