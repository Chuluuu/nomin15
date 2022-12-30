# -*- coding: utf-8 -*-
##############################################################################
#    Copyright (C) 2014-2020 Asterisk-technologies LLC Developer). All Rights Reserved
#
#    Address : Chingeltei District, Peace Tower, 205, Asterisk-technologies LLC Developer Ganzorig
#    Email : support@asterisk-tech.mn
#    Phone : 976 + 99241623
#
##############################################################################
{
    'name': 'Nomin tender website',
    'version': '1.0',
    'website': 'https://www.odoo.com',
    "author" : 'Otgonbayar.O',
    'category': 'Nomin',
    "summary": "Website",
    'data': [
        #'security/ir_ui_view.xml',
        'views/website.xml',
        'views/templates.xml',
        'views/assets.xml',
        'views/pages.xml',
        'views/tender_account.xml',
        'views/layout.xml',
        'views/content_list.xml',
        'views/web_context_tunnel.xml',
        'views/web_tender_menu.xml', 
        'portal_user_file_view.xml',
        'views/contract_inherit_view.xml',
        'security/ir.model.access.csv',
    ],
    'depends': [
        'website', 'website_portal', 'website_form', 'nomin_tender'
    ],
    'description': """
    """,
    'test': [
        'static/test/context_tunnel.js',
    ],
    'installable': True,
    'auto_install': False,
    'js': ['static/src/js/survey.js','static/src/js/survey_result.js','static/src/js/upload.js'],
    'application': True,
    'icon': '/nomin_web/static/img/bid.png',
    # 'qweb': ['views/templates.xml','portal_user_file_view.xml','views/pages.xml','views/layout.xml',],
}