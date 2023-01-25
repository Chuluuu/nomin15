{
    'name': 'Nomin request order',
    'version': '1.0',
    'category': '',
    'depends' : ['nomin_project'],
    'description': """ Request order""",
    'data': [
      
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/request_order_view.xml',
        'views/req_order_seq.xml',
        'views/request_order_config_view.xml',
        'wizard/to_evaluate_employee_view.xml',
        'wizard/return_work_service_view.xml',
        'wizard/request_cost_sharing_view.xml',
        'wizard/reject_work_service_view.xml',
        'wizard/to_control_work_service_view.xml',
        'wizard/to_change_price_view.xml',
        'report/request_order_report_view.xml',
        'report/sum_work_service_report_view.xml',
        'report/performance_work_report_view.xml',
        'report/doctor_report_view.xml',
       
       
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
