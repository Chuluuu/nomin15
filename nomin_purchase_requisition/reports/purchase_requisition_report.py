# -*- coding: utf-8 -*-

from odoo.osv import osv
from odoo.tools.translate import _
from odoo.addons.nomin_base.report_helper import verbose_numeric, comma_me, convert_curr
from odoo import api, models
from odoo.exceptions import UserError, AccessError
from operator import itemgetter

class PrintPurchaseRequsition1(osv.AbstractModel):
    _name = 'report.purchase_requisition.report_purchaserequisitions1'

    def render_html(self, cr, uid, ids, data=None, context=None):
        if context is None:
            context = {}
        report_obj = self.pool['report']
        requisition_obj = self.pool['purchase.requisition']
        employee_obj = self.pool['hr.employee']
        verbose_total_dict = {}
        report = report_obj._get_report_from_name(cr, uid, 'purchase_requisition.report_purchaserequisitions1')
        if data and not ids:
            ids = data['ids']
        pickings = requisition_obj.browse(cr, uid, ids, context=context)
        lines = {}
        total = {}
        emp_list = []
        employees = []
        employees2 = []
        employees3 = []
        document_name = u"ШААРДАХ ХУУДАС"
        background = '' 
        for pick in pickings:
            document_name = u"ШААРДАХ ХУУДАС №%s"%(pick.name) 
            line = {}
            total.update({pick.id:{'total': 0.0,}})
            for pr_line in pick.line_ids:
                if pr_line.id not in line:
                    product_state = 'Бараа олголт зөвшөөрөгдөөгүй байгаа'
                    if pr_line.state in ('rejected','canceled'):
                        product_state = 'Бараа олголт цуцлагдсан'
                    elif pr_line.state in ('tender_created'):
                        product_state = 'Тендер үүссэн'
                    elif pr_line.state in ('purchased'):
                        product_state = 'Худалдан авалт үүссэн'
                    elif pr_line.state in ('sent_to_supply','ready','assigned','sent_to_supply_manager'):
                        product_state = 'Хангамжийн мэргэжилтэнд хуваарьлагдсан'
                    elif pr_line.state in ('done','sent_nybo'):
                        product_state = 'Захиалагч барааг хүлээн авсан'


                    line[pr_line.id] = {'name': pr_line.product_id.product_code or '',
                                        'desc':pr_line.product_id.name or '',
                                        'test':comma_me(pr_line.product_desc),
                                      'uom': pr_line.product_uom_id.name,
                                      'qty': comma_me(pr_line.product_qty),
                                      'allow_qty':comma_me(pr_line.allowed_qty),
                                      'price': comma_me(pr_line.product_price),
                                      'amount': comma_me(pr_line.allowed_amount),
                                      'state': product_state
                                      }
                total[pick.id]['total'] += pr_line.amount
                lines[pick.id] = sorted(line.values(), key=itemgetter('name'))
            list = verbose_numeric(abs(total[pick.id]['total']))
            curr = pick.company_id.currency_id.integer
            div_curr = pick.company_id.currency_id.divisible
            verbose_total_dict[pick.id] = convert_curr(list, curr, div_curr)
            
            c = 1
            draft_date = False
            if pick.state in ['confirmed','fulfill','fulfil_request','purchased','assigned','tender_created','done']:
                for confirm in pick.history_lines:
                    if confirm.type=='draft':
                        if not draft_date:
                            draft_date =confirm.create_date
                        elif draft_date <=confirm.create_date:
                            draft_date =confirm.create_date
            is_append = True
            count = 0
            if pick.state in ['confirmed','fulfill','fulfil_request','purchased','assigned','tender_created','done']:
                for confirm in pick.history_lines:
                    if confirm.type not in ['draft','sent','sent_to_supply','assigned','fulfill','fulfil_request','done']:
                        if confirm.create_date >=draft_date:
                            employee_id = employee_obj.search(cr, 1, [('user_id','=',confirm.user_id.id)])
                            
                            emp_obj = employee_obj.browse(cr, 1 ,employee_id)
                            if emp_obj not in employees3:
                                employees3.append(emp_obj)
                                
                                if count==2:
                                   employees.append(employees2)
                                   employees2= []
                                   count =0
                                employees2.append(emp_obj)
                                count+=1                 

            if pick.state in ['assigned','fulfill','fulfil_request','assigned','purchased','tender_created','done']: 
                # employees3.reverse() 
                for confirm in pick.history_lines:
                    
                    if confirm.create_date >=draft_date:
                        if confirm.type  in ['assigned','fulfill','fulfil_request']:

                            employee_id = employee_obj.search(cr, 1, [('user_id','=',confirm.user_id.id)])
                            emp_obj = employee_obj.browse(cr, 1 ,employee_id)
                            
                            if emp_obj not in employees3:
                                employees3.append(emp_obj)
                                if count==2:
                                   employees.append(employees2)
                                   employees2= []
                                   count =0
                                employees2.append(emp_obj)
                                count+=1   
            if count >=1:
                employees.append(employees2)
            

            if pick.state in ['done']:
                background = """body{
                        background: url(http://4.bp.blogspot.com/-81Mm7YWThWU/X9DNAeiE0KI/AAAAAAAAAao/zo2TMFY0D4YQSy0zGlRjeqnRGlnpf_adwCK4BGAYYCw/s1600/baraag_olgoson.gif) right top no-repeat;
                        background-size: 250px 150px;
                    }"""

            elif pick.state not in ['assigned','sent_to_supply_manager','sent_to_supply']:
                background = """body{
                        background: url(http://4.bp.blogspot.com/-fczHFsACg_0/X9DNPFp1LTI/AAAAAAAAAa4/xXxcOIC4inMwQZKlrnnah90AWU52nnrzgCK4BGAYYCw/s1600/zvwxvvrvgdvvgvi.gif) right top no-repeat;
                        background-size: 250px 150px;
                    }"""
            eindex=0

        if not lines:
            raise UserError((u'Анхааруулга!'), (u'Шаардахын мөр хоосон байна!'))
        

        docargs = {
            'doc_ids': ids,
            'doc_model': report.model,
            'docs': pickings,
            'lines': lines,
            'verbose_total': verbose_total_dict,
            'document_name': document_name,
            'background': background,
            'emp_list':employees
        }
        return report_obj.render(cr, uid, ids, 'purchase_requisition.report_purchaserequisitions1', docargs, context=context)

class PrintPurchaseRequsition(osv.AbstractModel):
    _name = 'report.purchase_requisition.report_purchaserequisitions'


    def render_html(self, cr, uid, ids, data=None, context=None):
       
        report_obj = self.pool['report']
        requisition_obj = self.pool['purchase.requisition']
        employee_obj = self.pool['hr.employee']
        report = report_obj._get_report_from_name(cr, 1, 'purchase_requisition.report_purchaserequisitions')

        requisition_id = requisition_obj.browse(cr, 1, ids, context=context)

        employees = []

        for req in requisition_id:
            for confirm in req.history_lines:
                if confirm.type != 'sent':
                    employee_id = employee_obj.search(cr, 1, [('user_id','=',confirm.user_id.id)])
                    employees.append(employee_obj.browse(cr, 1 ,employee_id))
    

        
        docargs = {
            'doc_ids': ids,
            'doc_model': report.model,
            'docs': requisition_id,
            'employees': employees,
            }
        return report_obj.render(cr, 1, ids, 'purchase_requisition.report_purchaserequisitions', docargs, context=context)
        
