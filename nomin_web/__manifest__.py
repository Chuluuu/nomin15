# -*- coding: utf-8 -*-
{
    'name': 'Nomin tender website',
    'version': '2.0',
    'website': 'https://www.odoo.com',
    "author" : 'Chuluunbor.B',
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
        'website', 'portal', 'website_form', 'website_slides'
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
}