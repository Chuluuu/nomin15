# -*- coding: utf-8 -*-

{
    'name': 'Nomin tender backend',
    'version': '1.0',
    'website': 'https://www.odoo.com',
    "author" : 'Asterisk-technologies',
    'category': 'Nomin',
    'sequence': 55,
    "summary": "Tender",
    'depends': [
        'base', 
        'mail',
        # TODO FIX LATER
        # 'nomin_purchase',
        # 'nomin_contract'
    ],
    'description': """
    """,
    'data': [
        'security/security.xml',
        'wizard/tender_invitation_view.xml',
        'wizard/tender_date_extend_view.xml',
        'views/tender_participants_view.xml',
        # TODO FIX LATER
        # 'wizard/tender_contract_view.xml',
        'wizard/tender_tender_note.xml',
        'wizard/purchase_tender_view.xml',
        'views/tender_view.xml',
        'wizard/tender_protocol_view.xml',
        'views/tender_valuation_view.xml',
        'views/res_partner_documents_view.xml',
        'views/res_partner_view.xml',
        'views/res_partner_request_view.xml',
        # 'res_config_view.xml',
        'views/tender_sequence.xml',
        
        'purchase_requisition.xml',
        'purchase_order_inherit.xml',
        'views/subscribe_users_view.xml',
        'views/tender_cron_view.xml',
        'report/tender_protocol.xml',
        'report/tender_request.xml',
        'report/tender_request_report.xml',
        # 'report/tender_list_report.xml',
        'report_menu_view.xml',
        'email_templates/tender_result_email_template.xml',
        'email_templates/tender_tender_email_template.xml',
        'email_templates/tender_followers_email_template.xml',
        'email_templates/tender_info_email_template.xml',
        'email_templates/tender_invitation_email_template.xml',
        'security/ir.model.access.csv',
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'icon': '/nomin_tender/static/img/tender.png',
    'qweb': [],
}