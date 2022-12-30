# -*- coding: utf-8 -*-
##############################################################################
#
# Managewall LLCC, Enterprise Management Solution
# Copyright (C) 2013-2022 Managewall LLC (<http://www.managewall.mn/, http://managewall.mn/&gt;). All Rights Reserved #
# Email : info@managewall.mn
# Phone : 976 + 99081691
#
##############################################################################

{
    "name" : "Base Module",
    "version" : "1.0",
    "author" : "Managewall LLC",
    "category" : "Mongolian Modules",
    "website": "http://www.managewall.mn",
    "summary": "Odoo Base Module",
    "depends" : ['base','hr'],
    "init": [],
    "data" : [
              'views/configure/integration.xml',
              'security/security.xml',
              'security/ir.model.access.csv',
              'views/res/hr_team.xml',
            #   'data/data_account_type.xml',
              #'wizard/abstract_report_model_view.xml',
            #   'data/report_data.xml',
            #   'views/res/res_company_view.xml',
            #   'views/res/res_currency_view.xml',
              'views/res/res_user_view.xml',
            #   'views/res/res_user_permission_log.xml',
#             'views/res/res_partner_view.xml',
            #   'views/res/res_bank_view.xml',
            #   'views/res/res_groups_view.xml',

            #   'views/request_template_view.xml',
            #   'views/work_service_view.xml',
            #   'views/hr_employee_location_view.xml',
            #   'views/hr_view.xml',
            #   'views/import_master_data_view.xml',
            #   'views/configure/evaluation_indicators_view.xml',
            #   'views/configure/nomin_state_changer_view.xml',              
            #   'views/configure/res_users_config_view.xml',              
            #   'views/configure/integration.xml',
            #   'views/configure/cct_integration.xml',
            #   'views/fingerprint_lottery_view.xml',
              'views/sod_matrix.xml',
              
            #   'report/report_res_users_view.xml',
            #   'views/menu.xml',
              
    ],
    "demo_xml": [
    ],
    "active": False,
    "installable": True,
    'application': True,
    'auto_install': False,
}
