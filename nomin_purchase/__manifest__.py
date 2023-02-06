# -*- coding: utf-8 -*-

{
    "name" : "nomin - Purchase",
    "version" : "1.0",
    "author" : "Asterisk Technologies LLC",
    'sequence': 50,
    "description": """
    * Depending nomin_base, purchase_requisition, hr
""",
    "website" : False,
    "category" : "Purchase",
    "depends" : ['purchase','purchase_requisition'],
    "init": [],
    "data" : [
        'security/security.xml',
        'views/purchase_view.xml',
        'views/portal_purchase.xml',
        'views/purchase_cron.xml',
        'email_templates/purchase_mail.xml',
        'wizard/stock_picking_seperate.xml',
        'views/stock_picking_type_view.xml',
        'wizard/purchase_order_cancel_view.xml',
        'views/stock_report.xml',
        'reports/report_picking_all.xml',
        'reports/purchase_order_report.xml',
        'reports/purchase_order_supplier_report.xml',
        'reports/report_rfq_view.xml',
        'reports/purchase_requisition_receive_report_wizard.xml',
        'reports/report_purchaseorder.xml',
        # 'reports/purchase_printquatation.xml',
        'security/ir.model.access.csv',
        'views/purchase_priority_view.xml',
    ],
    "demo_xml": [
    ],
    "active": False,
    # 'icon': '/nomin_purchase_requisition/static/src/img/asterisk.png',
    "installable": True,
    'auto_install': False,
    'application': True,
   
}
