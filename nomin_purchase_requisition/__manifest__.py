# -*- coding: utf-8 -*-
##############################################################################
#
#    Asterisk Technologies LLC, Enterprise Management Solution    
#    Copyright (C) 2013-2013 Asterisk Technologies LLC (<http://www.erp.mn>). All Rights Reserved
#
#    Email : unuruu25@gmail.com
#    Phone : 976 + 88005462
#
##############################################################################

{
    "name" : "nomin - Purchase Requisition",
    "version" : "1.0",
    "author" : "Asterisk Technologies LLC",
    'sequence': 51,
    "description": """
    * Depending nomin_base, purchase_requisition, hr
""",
    "website" : False,
    "category" : "Purchase Requisition",
    "depends" : ['purchase_requisition','nomin_comparison','nomin_purchase','nomin_project'],
    "init": [],
#     "data": [],
    "data" : [
        'security/requisition_security.xml',
        'security/document_security.xml',
        'email_templates/requisition_assignee_notification_cron.xml',
        'email_templates/requisition_follower_notification_template.xml',
        'email_templates/requisition_notification_cron.xml',
        'email_templates/follower_notification_cron.xml',
        'email_templates/requisition_line_notification.xml',
        'email_templates/requisition_email_template.xml',
        'wizard/purchase_requisition_cancel_note.xml',
        'wizard/create_purchase_order_view.xml',
        'wizard/create_purchase_comparison_view.xml',
        'wizard/purchase_order_merge_view.xml',
        'wizard/purchase_order_separation_view.xml',
        'wizard/purchase_requisition_assign.xml',
        'wizard/damage_asset_description_view.xml',
        # 'wizard/requisition_to_manager_view.xml',
        'wizard/create_purchase_order_wizard.xml',
        'wizard/distributed_purchase_requisition_view.xml',
        'wizard/purchase_requisition_set_done.xml',
        'wizard/action_tender_request.xml',
        'wizard/add_multiple_transfer_request.xml',
        'wizard/product_import_export.xml',
        'wizard/reason_asker.xml',
        'wizard/skip_purchase_comparison_view.xml',
        'wizard/prepare_fixed_assets.xml',
        'purchase_requisition_view.xml',
        'purchase_requisition_line_view.xml',
        'views/job_position_limit_config.xml',
        # 'purchase_order_view.xml',
        'purchase_requisition_line_state_history_view.xml',
        'views/purchase_plan_view.xml',
        'views/stock_requisition_view.xml',
        'views/purchase_category_config.xml',
        'views/product_view.xml',
        'views/asset_transfer_request.xml',
        'views/fixed_asset_counting.xml',
        'views/standart_product_list_view.xml',
        'reports/purchase_requisition_report.xml',
        'reports/purchase_requisition_performance.xml',
        'reports/stock_requisition_list_report.xml',
        'reports/work_implementation_report_view.xml',
        'reports/department_purchase_report.xml',
        'reports/report_fixed_assets_view.xml',
        'security/ir.model.access.csv',

        'reports/purchase_requisition_order_report.xml',
        'reports/product_list_report_view.xml',
        'reports/purchase_requisition_staff_report_view.xml',
        'reports/property_report_view.xml',
        'wizard/purchase_requisition_line_wizard_view.xml',
    ],
    "demo_xml": [
    ],
    "active": False,
    'icon': '/nomin_purchase_requisition/static/src/img/asterisk.png',
    "installable": True,
    'auto_install': False,
    'application': True,
   
}
