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
import time
import datetime
import openerp
#from openerp.osv import osv
from openerp import api, fields, models, _, modules
from openerp.tools.translate import _
from openerp.addons.l10n_mn_report_base.report_helper import verbose_numeric,comma_me, convert_curr
from operator import itemgetter
import logging
_logger = logging.getLogger(__name__)


    
class ReportPurchaseOrder(models.AbstractModel):
    _name = 'report.nomin_purchase.report_purchaseorder_document'

    @api.multi
    def render_html(self, data):

        # comparison_id = self.env['purchase.comparison'].browse(self.id)
        order_id = self.env['purchase.order'].browse(self.id)
        
        employees = []        
        emps = []
        for emp in order_id.history_lines:
            employee_id =self.env['hr.employee'].sudo().search([('user_id','=',emp.user_id.id)])
            
            if employee_id not in emps:
                emps.append(employee_id)
                employees.append({'space':"     ",'employee':employee_id,'date':emp.date[0:10].replace('-','.')})   
        
        docargs = {
            'docs': order_id,             
            'employees':employees
        }
        
        
        return self.env['report'].render('nomin_purchase.report_purchaseorder_document', docargs)