# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-Today OpenERP SA (<http://www.openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.addons.l10n_mn_report_base.report_helper import verbose_numeric, comma_me, convert_curr
# from openerp.exceptions import UserError, ValidationError
# import logging
# _logger = logging.getLogger(__name__)
# from operator import itemgetter
# from openerp.osv import osv

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

    @api.multi
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