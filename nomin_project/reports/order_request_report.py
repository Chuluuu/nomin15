# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.addons.l10n_mn_report_base.report_helper import verbose_numeric, comma_me, convert_curr
from operator import itemgetter
from odoo.exceptions import UserError

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

