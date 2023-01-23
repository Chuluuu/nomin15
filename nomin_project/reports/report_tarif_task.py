# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.translate import _
# from operator import itemgetter
from odoo.exceptions import UserError, ValidationError
# import logging
# _logger = logging.getLogger(__name__)

# class PrintTarifTask(osv.AbstractModel):
#     _name = 'report.nomin_project.report_tarif_task'

#     def render_html(self, cr, uid, ids, data=None, context=None):
#         report_obj = self.pool['report']
#         task_obj = self.pool['project.task']
#         email = {}
#         phone = {}
#         report = report_obj._get_report_from_name(cr, 1, 'nomin_project.report_tarif_task')
#         tasks = task_obj.browse(cr, 1, ids, context=context)
#         for task in tasks:
#             if task.task_type == 'normal':
#                 raise UserError(_(u'Даалгаварийн төрөл энгийн үед хэвлэх боломжгүй'))
#             if task.task_state != 't_done':
#                 raise UserError(_(u'Даалгавар дууссан үед хэвлэх боломжтой'))
#             emp = task.task_verifier
#             user_id = self.pool.get('hr.employee').search(cr, 1, [('user_id','=',task.user_id.id)])
#             user = self.pool.get('hr.employee').browse(cr,1,user_id,context=context)
            
#         docargs = {
#                    'tasks': tasks,
#                    'owner': user,
#                    'emp': emp
#         }
#         return report_obj.render(cr, 1, ids, 'nomin_project.report_tarif_task', docargs, context=context)

class PrintTarifTask(models.AbstractModel):
    _name = 'report.nomin_project.report_tarif_task'

    # def render_html(self, cr, uid, ids, data=None, context=None):
    #     report_obj = self.pool['report']
    #     task_obj = self.pool['project.task']
    #     email = {}
    #     phone = {}
    #     report = report_obj._get_report_from_name(cr, 1, 'nomin_project.report_tarif_task')
    #     tasks = task_obj.browse(cr, 1, ids, context=context)
    #     for task in tasks:
    #         if task.task_type == 'normal':
    #             raise UserError(_(u'Даалгаварийн төрөл энгийн үед хэвлэх боломжгүй'))
    #         if task.task_state != 't_done':
    #             raise UserError(_(u'Даалгавар дууссан үед хэвлэх боломжтой'))
    #         emp = task.task_verifier
    #         user_id = self.pool.get('hr.employee').search(cr, 1, [('user_id','=',task.user_id.id)])
    #         user = self.pool.get('hr.employee').browse(cr,1,user_id,context=context)
            
    #     docargs = {
    #                'tasks': tasks,
    #                'owner': user,
    #                'emp': emp
    #     }
    #     return report_obj.render(cr, 1, ids, 'nomin_project.report_tarif_task', docargs, context=context)

    
    def render_html(self, data):
        task_obj = self.env['project.task']
        report = self.env['report']._get_report_from_name('nomin_project.report_tarif_task')
        tasks = task_obj.browse(self.id)
        for task in tasks:
            if task.task_type == 'normal':
                raise UserError(_(u'Даалгаварийн төрөл энгийн үед хэвлэх боломжгүй'))
            if task.task_state != 't_done':
                raise UserError(_(u'Даалгавар дууссан үед хэвлэх боломжтой'))
            emp = task.task_verifier
            user_id = self.env['hr.employee'].search([('user_id','=',task.user_id.id)])
            user = self.env['hr.employee'].browse(user_id.id)
        docargs = {
                   'tasks': tasks,
                   'owner': user,
                   'emp': emp
        }
        return self.env['report'].render('nomin_project.control_budget_report', docargs)
        