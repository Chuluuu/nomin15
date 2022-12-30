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

# from itertools import accumulate
from openerp.osv import osv
from openerp.tools.translate import _
from openerp.addons.l10n_mn_report_base.report_helper import verbose_numeric, comma_me, convert_curr
from operator import itemgetter
from openerp.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class ReportFixed_assets(osv.AbstractModel):
    '''Ажил хүлээлгэн өгөх хуудас
    '''
    _name = 'report.nomin_purchase_requisition.report_fixed_assets'

    def render_html(self, cr, uid, ids, data=None, context=None):
        report_obj = self.pool['report']
        fixed_asset_obj = self.pool['fixed.asset.counting']
        phone = {}
        report = report_obj._get_report_from_name(cr, 1, 'nomin_purchase_requisition.report_fixed_assets')
        fixed_asset_id = fixed_asset_obj.browse(cr, 1, ids, context=context)
        owners = {}
        if fixed_asset_id:
            for line in fixed_asset_id.change_line_ids_for_counting:
                accumulated_depreciation = 0
                current_value = 0
                # amount = 0
                for item in line.detail_ids:
                    accumulated_depreciation += item.accumulated_depreciation
                    current_value += item.current_value
                group = line.employee_id
                if group not in owners:
                    owners[group]={
                        'employee_id':'',
                        'employee_name':'',
                        'employee_last_name':'',
                        'amount':0,
                        'income':0,
                        'expense':0,
                        'qty':0,
                        'current_qty':0,
                        'accumulated_depreciation':0,
                        'current_value':0,
                        'income_total':0,
                        'expense_total':0
                    }
                    owners[group]['employee_id']=line.employee_id.id
                    owners[group]['employee_name']=line.employee_id.name_related
                    owners[group]['employee_last_name']=line.employee_id.last_name
                    owners[group]['amount']=line.amount
                    owners[group]['income']=line.income
                    owners[group]['expense']=line.expense
                    owners[group]['qty']=line.qty
                    owners[group]['current_qty']=line.current_qty
                    owners[group]['accumulated_depreciation']=accumulated_depreciation
                    owners[group]['current_value']=current_value
                    owners[group]['income_total']=line.income * line.amount
                    owners[group]['expense_total']=line.expense * line.amount

                else:
                    owners[group].update({
                        'qty':owners[group]['qty'] +line.qty,
                        'current_qty':owners[group]['current_qty'] +line.current_qty,
                        'accumulated_depreciation':owners[group]['accumulated_depreciation'] +accumulated_depreciation,
                        'current_qty':owners[group]['current_qty'] +line.current_qty,
                        'amount':owners[group]['amount'] +line.amount,
                        'income':owners[group]['income'] +line.income,
                        'expense':owners[group]['expense'] +line.expense,
                        'income_total':owners[group]['income_total'] + line.income * line.amount,
                        'expense_total':owners[group]['expense_total'] + line.expense * line.amount
                        
                        })
                # group1 = line.id
                # if group not in owners[group]['assets']:
                #     owners[group]['assets'][group1] = {
                #         'id':'Тодорхойгүй',
                #         'amount':0,
                #         'income':0,
                #         'expense':0,
                #         'qty':0,
                #         'current_qty':0,
                #         'accumulated_depreciation':0,
                #         'current_value':0,
                #     }
                # owners[group]['assets'][group1]['id']=group1
                # owners[group]['assets'][group1]['amount']=line.amount
                # owners[group]['assets'][group1]['income']=line.income
                # owners[group]['assets'][group1]['expense']=line.expense
                # owners[group]['assets'][group1]['qty']=line.qty
                # owners[group]['assets'][group1]['current_qty']=line.current_qty
                # owners[group]['assets'][group1]['accumulated_depreciation']=accumulated_depreciation
                # owners[group]['assets'][group1]['current_value']=current_value
        docargs = {
                   'fixed_asset_id': fixed_asset_id,
                   'owners': owners, 
        }
        return report_obj.render(cr, 1, ids, 'nomin_purchase_requisition.report_fixed_assets', docargs, context=context)
        