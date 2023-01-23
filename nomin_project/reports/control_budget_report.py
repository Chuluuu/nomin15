# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.translate import _

# class PrintTarifTask(osv.AbstractModel):
#     _name = 'report.nomin_project.control_budget_report'

#     def render_html(self, cr, uid, ids, data=None, context=None):
#         report_obj = self.pool['report']
#         budget_obj = self.pool['control.budget']
#         email = {}
#         phone = {}
#         report = report_obj._get_report_from_name(cr, 1, 'nomin_project.control_budget_report')
#         budgets = budget_obj.browse(cr, 1, ids, context=context)
#         user_id = self.pool.get('hr.employee').search(cr, 1, [('user_id','=',budgets.user_id.id)])
#         emp = self.pool.get('hr.employee').browse(cr,1,user_id,context=context)
#         docargs = {
#                    'budgets': budgets,
#                    'emp':emp
#         }
#         return report_obj.render(cr, 1, ids, 'nomin_project.control_budget_report', docargs, context=context)
        
# class PrintTarifTask(osv.AbstractModel):
#     _name = 'report.nomin_project.control_budget_report'

#     def render_html(self, cr, uid, ids, data=None, context=None):
#         report_obj = self.pool['report']
#         budget_obj = self.pool['control.budget']
#         email = {}
#         phone = {}
#         report = report_obj._get_report_from_name(cr, 1, 'nomin_project.control_budget_report')
#         budgets = budget_obj.browse(cr, 1, ids, context=context)
#         user_id = self.pool.get('hr.employee').search(cr, 1, [('user_id','=',budgets.user_id.id)])
#         emp = self.pool.get('hr.employee').browse(cr,1,user_id,context=context)
#         docargs = {
#                    'budgets': budgets,
#                    'emp':emp
#         }
#         return report_obj.render(cr, 1, ids, 'nomin_project.control_budget_report', docargs, context=context)

class PrintTarifTask(models.AbstractModel):
    """
          Захиалгын баримт
    """
    _name = 'report.nomin_project.control_budget_report'

    
    def render_html(self, data):
        budget_obj = self.env['control.budget']
        report = self.env['report']._get_report_from_name('nomin_project.control_budget_report')
        budgets = budget_obj.browse(self.id)
        user_id = self.env['hr.employee'].search([('user_id','=',budgets.user_id.id)])
        emp = self.env['hr.employee'].browse(user_id.id)
        docargs = {
                   'budgets': budgets,
                   'emp':emp
        }
        return self.env['report'].render('nomin_project.control_budget_report', docargs)