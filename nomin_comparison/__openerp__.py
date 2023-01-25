# -*- coding: utf-8 -*-
##############################################################################
#
# Asterisk Technologies LLC, Enterprise Management Solution
# Copyright (C) 2013-2015 Asterisk Technologies LLC (<http://www.erp.mn/, http://asterisk-tech.mn/&gt;). All Rights Reserved #
# Email : info@asterisk-tech.mn
# Phone : 976 + 88005462, 976 + 94100149
#
##############################################################################

{
    "name" : "Nomin Purchase Comparison",
    "version" : "1.0",
    "author" : "Asterisk Technologies LLC",
    "category" : "Mongolian Modules",
    "website": "http://www.asterisk-tech.mn",
    "summary": "Odoo Base Module",
    "depends" : ['nomin_purchase','nomin_contract'],
    "init": [],
    "data" : [
              'security/security.xml',
              'wizard/wizard_rate_purchase_partner.xml',
              'views/purchase_comparison_report_view.xml',
              'views/purchase_order_view.xml',
              'views/purchase_comparison_view.xml',
              'views/purchase_comparison_sequence.xml',
              'wizard/create_purchase_comparison.xml',
              'wizard/create_purchase_comparison_multiple.xml',
              'wizard/add_comparison_product_view.xml',
              'wizard/add_comparison_partner_view.xml',
              'report/report_purchase_comparison.xml',
              'report/report_purchase_comparison_participation.xml',
              'report/report_purchase_comparison_performance.xml',
              'static/xml/purchase_comparison.xml',
              'security/ir.model.access.csv',
              'views/purchase_order_inherit.xml',
              'views/purchase_comparison_indicator_menu_view.xml',

    ],
    "demo_xml": [
    ],
    "active": False,
    "installable": True,
    'application': True,
    'auto_install': False,
    'js': ['static/src/js/comparison.js'],
    'icon': '/nomin_base/static/description/asterisk-tech.png',
    'qweb': ['static/src/xml/comparison.xml',],
}
