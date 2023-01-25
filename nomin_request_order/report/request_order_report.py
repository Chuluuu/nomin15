
# -*- coding: utf-8 -*-

from openerp.tools.translate import _
from openerp import api, fields, models, _,modules
from datetime import datetime,timedelta
from operator import itemgetter
import xlsxwriter
from io import BytesIO
import base64
import pdfkit
# from openerp.addons.nomin_payroll.report.nomin_payroll_salary_report import encode_for_xml ,_xmlcharref_encode
from openerp.addons.l10n_mn_report_base.report_helper import verbose_numeric, comma_me, convert_curr
import logging
_logger = logging.getLogger(__name__)
class RequestOrderReport(models.TransientModel):
    _name = 'request.order.report'

    date_from = fields.Date(string='Date from')
    date_to = fields.Date(string='Date to')    
    type = fields.Selection([('sector','Sector'),('employee','request employee')],string="Type", default = "sector")
    sector_ids = fields.Many2many(comodel_name = 'hr.department', string=u'Захиалагч Салбар')
    perform_department_ids = fields.Many2many('hr.department','hr_department_request_order_report_perform_rel','department_id','report_id', string=u'Гүйцэтгэгч хэлтэс')    
    employee_ids = fields.Many2many(comodel_name = 'hr.employee',string=u'Ажилтан')
    request_config_id     = fields.Many2one('request.order.config',string="Төлөв")
    # state = fields.Selection([('open','Open'),('pending','Pending'),('control','Control'),('done','Done')], string="State" , default="done")




    @api.onchange('type')
    def onchange_type(self):
        is_true= self.env.user.has_group('project.group_project_admin')
        if not is_true:
            return {'domain':{
                            'perform_department_ids': [('id','in',self.env.user.project_allowed_departments.ids)],                         
                            }
                    }
    

    def encode_for_xml(self, unicode_data, encoding='ascii'):
        try:
            return unicode_data.encode(encoding, 'xmlcharrefreplace')
        except ValueError:
            return _xmlcharref_encode(unicode_data, encoding)

    def _xmlcharref_encode(self, unicode_data, encoding):
        chars = []
        for char in unicode_data:
            try:
                chars.append(char.encode(encoding, 'strict'))
            except UnicodeError:
                chars.append('&#%i;' % ord(char))
        return ''.join(chars)


    @api.multi
    def action_export(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        header = workbook.add_format({'border':1,'fg_color':'#b0e2ff','align':'justify','valign':'vjustify','text_wrap':100,'pattern':0})

        title = workbook.add_format({
		'border': 0,
		'bold': 1,
		'align': 'center',
		'valign': 'vcenter',
		# 'text_wrap': 'on',
		'font_size':18,
		'font_name': 'Arial',
		})


        header_color = workbook.add_format({
        'border': 1,
        'bold': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 'on',
        'font_size':10,
        'bg_color':'#E0E0E0',
        'font_name': 'Arial',
        })

        cell_float_format_left = workbook.add_format({
        'border': 0,
        'bold': 0,
        'align': 'left',
        'valign': 'vcenter',
        'text_wrap': 'on',
        'font_size':10,
        # 'bg_color':'#40E0D0',
        'font_name': 'Arial',
        'num_format': '#,##0.00'
        })
        cell_float_format_right = workbook.add_format({
        'border': 0,
        'bold': 0,
        'align': 'right',
        'valign': 'vcenter',
        'text_wrap': 'on',
        'font_size':10,
        'font_name': 'Arial',
        # 'bg_color':'#40E0D0',
        'num_format': '#,##0.00'
        })

        cell_format_center = workbook.add_format({
        'border': 1,
        'bold': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 'on',
        'font_size':10,
        #'bg_color':'#ADBFF7',
        'font_name': 'Arial',
        'num_format': '#,##0.00'
        })
        sum_format_center = workbook.add_format({
        'top': 1,
        'bold': 0,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 'on',
        'font_size':12,
        #'bg_color':'#ADBFF7',
        'font_name': 'Arial',
        'num_format': '#,##0.00'
        })

        footer_color = workbook.add_format({
        'border': 0,
        'bold': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 'on',
        'font_size':8,
        'bg_color':'#E0E0E0',
        'font_name': 'Arial',
        'num_format': '#,##0.00'
        })
        sheet = workbook.add_worksheet()

        sheet.portrait=True
        row = 5
        col = 6
        file_name = u'Захиалгын тайлан'
        sheet.set_row(2, 30)
        sheet.merge_range(2, 0, 2, col ,file_name,title)
        sheet.write(3, 0, u'Эхлэх хугацаа :'+  self.date_from)
        sheet.write(4, 0, u'Дуусах хугацаа :'+ self.date_to )
        sheet.set_row(5, 20)
        sheet.set_column(0,0,5)
        sheet.set_column(1, 6,15)


        where = "where a.date_order between '%s' and '%s' "%(self.date_from,self.date_to)
        if self.type =='sector':            
            if self.sector_ids:
                if len(self.sector_ids.ids)>1:
                    where=where+" and sector.id in %s"%(str(tuple(self.sector_ids.ids)))
                else:               
                    where=where+" and sector.id = %s"%(str(self.sector_ids.ids[0]))
            
            if self.perform_department_ids:
                if len(self.perform_department_ids.ids)>1:
                    where=where+" and perform.id in %s"%(str(tuple(self.perform_department_ids.ids)))
                else:               
                    where=where+" and perform.id = %s"%(str(self.perform_department_ids.ids[0]))
        else:
            if self.employee_ids:
                if len(self.employee_ids.ids)>1:
                    where=where+" and emp.id in %s"%(str(tuple(self.employee_ids.ids)))
                else:               
                    where=where+" and emp.id = %s"%(str(self.employee_ids.ids[0]))

        query=" select a.date_due as date_due, a.order_finished_date as order_finished_date,a.exceeded_day as exceeded_day,line.date_evaluate as date_evaluate , line.date as date,line.state as state ,line.rate as rate ,line.maintenance as maintenance,line.qty as qty, work.name as service , line.id as line,line.amount as total_sum,\
                    a.name as id , a.request_name as request_name , dep.name as req_department_name , emp.name_related as employee , perform.name as perform_department_name , \
                    employee.name_related as perform_employee,a.date_order as start_time,a.description as description\
                            from request_order a \
                     left join hr_employee emp on a.employee_id = emp.id\
                     left join hr_department dep on  a.department_id = dep.id \
                     left join hr_department sector on  a.sector_id = sector.id \
                     left join hr_department perform on  a.perform_department_id = perform.id \
                     left join request_order_line line on a.id = line.order_id \
                     left join hr_employee employee on line.perform_employee_id = employee.id\
                     left join work_service work on line.service_id = work.id \
                 "
        query = query +where
        self.env.cr.execute(query)
        dictfetchall = self.env.cr.dictfetchall() 


        sheet.set_row(9, 20)
        sheet.merge_range(row, 0,row+2, 0, u'Д/д', header_color)
        sheet.set_column(0,0,5)
        sheet.merge_range(row, 1,row+2, 1, u'Захиалгын дугаар', header_color)
        sheet.set_column(1,1,15)
        sheet.merge_range(row, 2,row+2, 2, u' Захиалгын нэр', header_color)
        sheet.set_column(2,2,15)
        sheet.merge_range(row, 3,row+2, 3, u'Захиалагч хэлтэс', header_color)
        sheet.set_column(3,3,15)
        

        sheet.merge_range(row, 4,row+2, 4, u'Захиалагч', header_color)
        sheet.set_column(4,4,15)
        sheet.merge_range(row, 5,row+2, 5, u'Ажлын нэр', header_color)
        sheet.set_column(5,5,15)
        sheet.merge_range(row, 6,row+2, 6, u'Гүйцэтгэгч хэлтэс', header_color)
        sheet.set_column(6,6,15)
        sheet.merge_range(row, 7,row+2, 7, u'Гүйцэтгэгч', header_color)
        sheet.set_column(7,7,15)
        sheet.merge_range(row, 8,row, 9, u'Тоо ширхэг', header_color)
        sheet.merge_range(row+1, 8,row+2, 8, u'үндсэн ', header_color)
        sheet.merge_range(row+1, 9,row+2, 9, u'засвар', header_color)
        sheet.set_column(11,7,12)
      
        sheet.merge_range(row, 10,row+2, 10, u'Үнэлгээ', header_color)
        sheet.set_column(10,10,15)
        sheet.merge_range(row, 11,row+2, 11, u'Нийт дүн', header_color)
        sheet.set_column(11,11,15)
        sheet.merge_range(row, 12,row, 13, u'Огноо', header_color)
        sheet.merge_range(row+1, 12,row+2, 12, u'Захиалга өгсөн ', header_color)
        sheet.merge_range(row+1, 13,row+2, 13, u'Үнэлсэн огноо', header_color)
        sheet.merge_range(row, 14,row+2, 14, u'Тайлбар', header_color)
        sheet.set_column(14,14,15)
        sheet.merge_range(row, 15,row+2, 15, u'Төлөв', header_color)
        sheet.set_column(15,15,15)
        sheet.merge_range(row, 16,row+2, 16, u'Дуусгасан огноо', header_color)
        sheet.set_column(16,16,16)
        sheet.merge_range(row, 17,row+2, 17, u'Дуусгах хоног', header_color)
        sheet.set_column(17,17,17)
        sheet.merge_range(row, 18,row+2, 18, u'Хэтэрсэн хоног', header_color)
        sheet.set_column(18,18,18)
        row = row+2
         
        if dictfetchall:
            sectors={}
            employees = {}
            if self.type =='sector':
                for dic in dictfetchall:
                    group = dic['req_department_name']
                    if group not in sectors:
                        sectors[group]={
                           'sector':u'',                    
                            'employee':u'',
                            'orders':{},

                        }
                    sectors[group]['sector'] = group
                    
                    
                    sectors[group]['employee'] = dic['employee']


                     # sectors {
                    #         'chuluu':{'name':'chuluu'}
                    # }
                    group1 = dic['id']
                    if group1 not in sectors[group]['orders']:
                        sectors[group]['orders'][group1]={
                            'name':u'',
                            'request_name':u'',
                            'request_number':u'',
                            'perform_department_name':u'',
                            'employee':u'',
                            'perform_employee':u'',
                            'qty':u'',
                            'maintenance_qty':u'',
                            'rate':u'',
                            'total_sum':0,
                            'date_order':u'',
                            'date_due':u'',
                            'order_finished_date':u'',
                            'exceeded_day':u'',
                            'date_evaluate ':u'',                            
                            'state ':u'',
                            'lines':{},
                        }


                    sectors[group]['orders'][group1]['request_name']= dic['request_name']
                    sectors[group]['orders'][group1]['name']= dic['service']
                    sectors[group]['orders'][group1]['request_number']= dic['id']
                    sectors[group]['orders'][group1]['perform_department_name']= dic['perform_department_name']
                    sectors[group]['orders'][group1]['perform_employee']= dic['perform_employee']
                    sectors[group]['orders'][group1]['employee']= dic['employee']
                    sectors[group]['orders'][group1]['qty']= dic['qty']
                    sectors[group]['orders'][group1]['maintenance_qty']= dic['maintenance']
                    sectors[group]['orders'][group1]['rate']= dic['rate']
                    sectors[group]['orders'][group1]['total_sum']+= dic['total_sum'] if dic['total_sum']  else 0
                    sectors[group]['orders'][group1]['date_order']= dic['start_time']
                    sectors[group]['orders'][group1]['date_due']= dic['date_due']
                    sectors[group]['orders'][group1]['order_finished_date']= dic['order_finished_date']
                    sectors[group]['orders'][group1]['exceeded_day']= dic['exceeded_day']
                    sectors[group]['orders'][group1]['date_evaluate']= dic['date_evaluate']
                    sectors[group]['orders'][group1]['description']= dic['description']
                    sectors[group]['orders'][group1]['state']= dic['state']
                    group2 = dic['line']
                    if group2 not in sectors[group]['orders'][group1]['lines']:
                        sectors[group]['orders'][group1]['lines'][group2] = {
                            'perform_department_name':u'',
                            'perform_employee':u'',
                            'qty':u'',
                            'maintenance_qty':u'',
                            'rate':u'',
                            'total_sum':0,
                            'date_order':u'',
                            'date_due':u'',
                            'order_finished_date':u'',
                            'exceeded_day':u'',
                            'date_evaluate ':u'',                            
                            'state ':u'',
                            'line':u'',
                            'name':u'',
                        }
                    sectors[group]['orders'][group1]['lines'][group2]['line']= dic['line']
                    sectors[group]['orders'][group1]['lines'][group2]['name']= dic['service']
                    sectors[group]['orders'][group1]['lines'][group2]['perform_department_name']= dic['perform_department_name']
                    sectors[group]['orders'][group1]['lines'][group2]['perform_employee']= dic['perform_employee']
                    sectors[group]['orders'][group1]['lines'][group2]['qty']= dic['qty']
                    sectors[group]['orders'][group1]['lines'][group2]['maintenance_qty']= dic['maintenance']
                    sectors[group]['orders'][group1]['lines'][group2]['rate']= dic['rate']
                    sectors[group]['orders'][group1]['lines'][group2]['total_sum'] += dic['total_sum'] if dic['total_sum']  else 0
                    sectors[group]['orders'][group1]['lines'][group2]['date_order']= dic['start_time']
                    sectors[group]['orders'][group1]['lines'][group2]['order_finished_date']= dic['order_finished_date']
                    sectors[group]['orders'][group1]['lines'][group2]['date_due']= dic['date_due']
                    sectors[group]['orders'][group1]['lines'][group2]['exceeded_day']= dic['exceeded_day']
                    sectors[group]['orders'][group1]['lines'][group2]['date_evaluate']= dic['date_evaluate']
                    sectors[group]['orders'][group1]['lines'][group2]['description']= dic['description']
                    sectors[group]['orders'][group1]['lines'][group2]['state']= dic['state']


                row+=1  

                states = {
                'draft':u'Ноорог',
                'open':u'Хариуцагчтай',
                'pending':u'Хийгдэж буй',
                'control':u'Хянах',
                'done':u'Хаагдсан',
                'rejected':u'Цуцалсан',
                'verify':u'Шалгуулах',

                }
                for sector in sorted(sectors.values(), key=itemgetter('sector')):
                    count = 1
                    for service in sorted(sector['orders'].values(), key=itemgetter('name')):
                        for line in sorted(service['lines'].values(), key=itemgetter('line')):
                            sheet.write(row , 0 , count )
                            count+=1
                            sheet.write(row, 1 , service['request_number'], cell_float_format_right)
                            sheet.write(row, 2 , service['request_name'], cell_float_format_right)
                            sheet.write(row, 3 , sector['sector'], cell_float_format_right)
                            sheet.write(row, 4 , service['employee'], cell_float_format_right)
                            sheet.write(row, 5 , line['name'], cell_float_format_right)
                            sheet.write(row, 6 , line['perform_department_name'], cell_float_format_right)
                            sheet.write(row, 7 , line['perform_employee'], cell_float_format_right)
                            sheet.write(row, 8 , line['qty'], cell_float_format_right)
                            sheet.write(row, 9 , line['maintenance_qty'], cell_float_format_right)
                            sheet.write(row, 10 , line['rate'], cell_float_format_right)
                            sheet.write(row, 11 , line['total_sum'], cell_float_format_right)
                            sheet.write(row, 12 , line['date_order'], cell_float_format_right)
                            sheet.write(row, 13 , line['date_evaluate'], cell_float_format_right)
                            sheet.write(row, 14 , line['description'], cell_float_format_right)
                            sheet.write(row, 16 , line['order_finished_date'], cell_float_format_right)
                            sheet.write(row, 17 , line['date_due'], cell_float_format_right)
                            sheet.write(row, 18 , line['exceeded_day'], cell_float_format_right)
                            if line['state'] in states:
                                sheet.write(row, 15 , states[line['state']], cell_float_format_right)
                            else:
                                sheet.write(row, 15 , 'Тодорхойгүй', cell_float_format_right)
                            
                            row+=1
            else:
                for dic in dictfetchall:
                    group = dic['req_department_name']
                    if group not in employees:
                        employees[group]={
                           'sector':u'',                    
                            'employee':u'',
                            'orders':{},

                        }
                    employees[group]['sector'] = group
                    
                    
                    employees[group]['employee'] = dic['employee']


                     # employees {
                    #         'chuluu':{'name':'chuluu'}
                    # }
                    group1 = dic['id']
                    if group1 not in employees[group]['orders']:
                        employees[group]['orders'][group1]={
                            'name':u'',
                            'request_name':u'',
                            'request_number':u'',
                            'perform_department_name':u'',
                            'employee':u'',
                            'perform_employee':u'',
                            'qty':u'',
                            'maintenance_qty':u'',
                            'rate':u'',
                            'total_sum':0,
                            'date_order':u'',
                            'date_due':u'',
                            'order_finished_date':u'',
                            'exceeded_day':u'',
                            'date_evaluate ':u'',                            
                            'state ':u'',
                            'lines':{},
                        }


                    employees[group]['orders'][group1]['request_name']= dic['request_name']
                    employees[group]['orders'][group1]['employee']= dic['employee']
                    employees[group]['orders'][group1]['name']= dic['service']
                    employees[group]['orders'][group1]['request_number']= dic['id']
                    employees[group]['orders'][group1]['perform_department_name']= dic['perform_department_name']
                    employees[group]['orders'][group1]['perform_employee']= dic['perform_employee']
                    employees[group]['orders'][group1]['qty']= dic['qty']
                    employees[group]['orders'][group1]['maintenance_qty']= dic['maintenance']
                    employees[group]['orders'][group1]['rate']= dic['rate']
                    employees[group]['orders'][group1]['total_sum']+= dic['total_sum'] if dic['total_sum']  else 0
                    employees[group]['orders'][group1]['date_order']= dic['start_time']
                    employees[group]['orders'][group1]['order_finished_date']= dic['order_finished_date']
                    employees[group]['orders'][group1]['date_due']= dic['date_due']
                    employees[group]['orders'][group1]['exceeded_day']= dic['exceeded_day']
                    employees[group]['orders'][group1]['date_evaluate']= dic['date_evaluate']
                    employees[group]['orders'][group1]['description']= dic['description']
                    employees[group]['orders'][group1]['state']= dic['state']
                    group2 = dic['line']
                    if group2 not in employees[group]['orders'][group1]['lines']:
                        employees[group]['orders'][group1]['lines'][group2] = {
                            'perform_department_name':u'',
                            'perform_employee':u'',
                            'qty':u'',
                            'maintenance_qty':u'',
                            'rate':u'',
                            'total_sum':0,
                            'date_order':u'',
                            'date_due':u'',
                            'order_finished_date':u'',
                            'exceeded_day':u'',
                            'date_evaluate ':u'',                            
                            'state ':u'',
                            'line':u'',
                            'name':u'',
                        }
                    employees[group]['orders'][group1]['lines'][group2]['line']= dic['line']
                    employees[group]['orders'][group1]['lines'][group2]['name']= dic['service']
                    employees[group]['orders'][group1]['lines'][group2]['perform_department_name']= dic['perform_department_name']
                    employees[group]['orders'][group1]['lines'][group2]['perform_employee']= dic['perform_employee']
                    employees[group]['orders'][group1]['lines'][group2]['qty']= dic['qty']
                    employees[group]['orders'][group1]['lines'][group2]['maintenance_qty']= dic['maintenance']
                    employees[group]['orders'][group1]['lines'][group2]['rate']= dic['rate']
                    employees[group]['orders'][group1]['lines'][group2]['total_sum'] += dic['total_sum'] if dic['total_sum']  else 0
                    employees[group]['orders'][group1]['lines'][group2]['date_order']= dic['start_time']
                    employees[group]['orders'][group1]['lines'][group2]['order_finished_date']= dic['order_finished_date']
                    employees[group]['orders'][group1]['lines'][group2]['date_due']= dic['date_due']
                    employees[group]['orders'][group1]['lines'][group2]['exceeded_day']= dic['exceeded_day']
                    employees[group]['orders'][group1]['lines'][group2]['date_evaluate']= dic['date_evaluate']
                    employees[group]['orders'][group1]['lines'][group2]['description']= dic['description']
                    employees[group]['orders'][group1]['lines'][group2]['state']= dic['state']


                row+=1  

                states = {
                'draft':u'Ноорог',
                'open':u'Хариуцагчтай',
                'pending':u'Хийгдэж буй',
                'control':u'Хянах',
                'done':u'Хаагдсан',
                'verify':u'Шалгуулах',
                'rejected':u'Цуцалсан',

                }
                for sector in sorted(employees.values(), key=itemgetter('sector')):
                    count = 1
                    for service in sorted(sector['orders'].values(), key=itemgetter('name')):
                        for line in sorted(service['lines'].values(), key=itemgetter('line')):
                            sheet.write(row , 0 , count )
                            count+=1
                            sheet.write(row, 1 , service['request_number'], cell_float_format_right)
                            sheet.write(row, 2 , service['request_name'], cell_float_format_right)
                            sheet.write(row, 3 , sector['sector'], cell_float_format_right)
                            sheet.write(row, 4 , service['employee'], cell_float_format_right)
                            sheet.write(row, 5 , line['name'], cell_float_format_right)
                            sheet.write(row, 6 , line['perform_department_name'], cell_float_format_right)
                            sheet.write(row, 7 , line['perform_employee'], cell_float_format_right)
                            sheet.write(row, 8 , line['qty'], cell_float_format_right)
                            sheet.write(row, 9 , line['maintenance_qty'], cell_float_format_right)
                            sheet.write(row, 10 , line['rate'], cell_float_format_right)
                            sheet.write(row, 11 , line['total_sum'], cell_float_format_right)
                            sheet.write(row, 12 , line['date_order'], cell_float_format_right)
                            sheet.write(row, 13 , line['date_evaluate'], cell_float_format_right)
                            sheet.write(row, 14 , line['description'], cell_float_format_right)
                            sheet.write(row, 16 , line['order_finished_date'], cell_float_format_right)
                            sheet.write(row, 17 , line['date_due'], cell_float_format_right)
                            sheet.write(row, 18 , line['exceeded_day'], cell_float_format_right)
                            if line['state'] in states:
                                sheet.write(row, 15 , states[line['state']], cell_float_format_right)
                            else:
                                sheet.write(row, 15 , 'Тодорхойгүй', cell_float_format_right)

                            
                            row+=1
           


        workbook.close()
        out = base64.encodestring(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data':out,'name':file_name + '.xlsx'})

        return {
		'name': 'Export Report',
		'view_type':'form',
		'view_mode':'form',
		'res_model':'report.excel.output',
		'res_id':excel_id.id,
		'view_id':False,
		'type': 'ir.actions.act_window',
		'target':'new',
		'nodestroy': True,
		}

