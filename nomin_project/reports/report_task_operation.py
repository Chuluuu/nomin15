# -*- coding: utf-8 -*-
from odoo import api, models

class ReportTaskOperation(models.AbstractModel):
    _name = 'report.nomin_project.report_task_opeartion_action'
    
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('nomin_project.report_task_opeartion_action')
        
        taks_ids = self.env['project.task'].browse(self._ids)
        employees = []
        emp =False
        

        for task in taks_ids:
            if task.user_id.id:
                emp =self.env['hr.employee'].sudo().search([('user_id','=',task.user_id.id)])
            for user in task.verify_user_ids:
                employees.append(user.employee_id)
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': taks_ids,
            'employees':employees,
            'emp':emp,
        }
        return report_obj.render('nomin_project.report_task_opeartion_action', docargs)