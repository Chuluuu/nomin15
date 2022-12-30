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
from operator import itemgetter
from openerp.exceptions import UserError
# from openerp.exceptions import UserError, ValidationError
# import logging
# _logger = logging.getLogger(__name__)
# from operator import itemgetter
# from openerp.osv import osv

class PrintOrderRequest(models.AbstractModel):
    """
          Захиалгын баримт
    """
    _name = 'report.nomin_project.order_request_report'


    @api.multi
    def render_html(self, data):
        report = self.env['report']._get_report_from_name('nomin_project.order_request_report')

        order_obj = self.env['order.page']
        orders = order_obj.browse(self.id)
        lines = {}
        order_name = u"Захиалгат ажлын зардал " 

       

        for order in orders:
            if order.state not in ['cost_done','estimated','approved','handover','done']:
                raise UserError((u'Зардал батлагдсан төлвөөс хойш Зардлын мэдээллийг хэвлэх боломжтой болно.'))
            if not order.cost_info:
                raise UserError((u'Зардлын мэдээллийг үүсгээгүй үед хэвлэх боломжгүй'))
            line = {}            
            for cost in order.cost_info:
                if cost.id not in line:
                    line[cost.id] = {'id': cost.id or '',
                                'name': cost.position_name.name or '',
                                'rate':cost.rate or '',
                                'time':cost.time_info or '',
                                'total':cost.total or '',
                                 
                                    }

                lines[order.id] = sorted(line.values(), key=itemgetter('id'))
        


        docargs = {
                   'lines': lines,
                   'orders': orders,
                   'order_name': order_name,
        }
        return self.env['report'].render('nomin_project.order_request_report', docargs)

class PrintOrderRequestAct(models.AbstractModel):
    """
          Хүлээлцэх Акт
    """
    _name = 'report.nomin_project.order_request_act_report'


    @api.multi
    def render_html(self, data):
        report = self.env['report']._get_report_from_name('nomin_project.order_request_act_report')

        order_obj = self.env['order.page']
        orders = order_obj.browse(self.id)
        lines = {}
        order_name = u"Акт хүлээлцэх " 

        for order in orders:
            if order.state not in ['estimated','approved','done']:
                raise UserError(_(u'Хянуулах төлвөөс хойш Хүлээлцэх актыг хэвлэх боломжтой болно.'))
            if not order.task_info:
                raise UserError(_(u'Хийгдсэн ажил таб хоосон байна.'))
            line = {}            
            for task in order.task_info:
                if task.id not in line:
                    line[task.id] = {'id': task.id or '',
                                'task_name': task.implemented_task or '',
                                'description':task.explanation or '',
                                'comment':task.comment or '',
                                                            
                                 
                                    }
                

                lines[order.id] = sorted(line.values(), key=itemgetter('id'))

        docargs = {
                   'lines': lines,
                   'orders': orders,
                   'order_name': order_name,
        }
        return self.env['report'].render('nomin_project.order_request_act_report', docargs)

