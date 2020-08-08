# -*- coding: utf-8 -*-
{
    'name': "bds",

    'summary': """
    """,

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/quan_data.xml',
        'data/data_chotot_chung_cu.xml',
        'data/data_chotot_other.xml',
        'data/data_chotot_phuong.xml',
        'data/data_chotot.xml',
        'data/data_muaban.xml',
        'data/data_bdsvn.xml',
        'data/data_taphoa.xml',
        'data/cronjob_data.xml',
        'data/email.xml',
        'data/data_config_parameter.xml',

        'views/bds_images.xml',
        'views/cron.xml',
        'views/fetch.xml',
        'views/bds_search.xml',
        'views/bds_form.xml',
        'views/bds_list.xml',
        'views/tap_hoa_list.xml',
        'views/tap_hoa.xml',

        'views/poster.xml',
        'views/quan.xml',
        'views/error.xml',
        'views/url_views.xml',
        'views/laptop.xml',
        'views/get_phone_poster.xml',
        'views/ir_actions_server.xml',
        'views/res_config_settings_views.xml',
        'views/user_bds_mark_read.xml',
        'wizard/trigger_form.xml',
        'views/tieu_chi.xml',
        'views/menu.xml',

    ],
    
}