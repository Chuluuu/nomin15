
# -*- coding: utf-8 -*-

from odoo.tools.translate import _
from odoo import api, fields, models, _,modules
from datetime import datetime,timedelta
from operator import itemgetter
import xlsxwriter
from io import BytesIO
import base64
import logging
_logger = logging.getLogger(__name__)
class PerformanceWorkReport(models.TransientModel):
    _name = 'performance.work.report'

    date_from = fields.Date(string='Date from')
    date_to = fields.Date(string='Date to')    
    type = fields.Selection([('sector','Sector'),('employee','Perform employee')],string="Type", default = "sector")
    sector_ids = fields.Many2many(comodel_name = 'hr.department', string=u'Захиалагч хэлтэс')
    perform_department_ids = fields.Many2many('hr.department','hr_department_request_order_report_performance_work_rel','department_id','report_id', string=u'Гүйцэтгэгч хэлтэс')
    employee_ids = fields.Many2many(comodel_name = 'hr.employee',string=u'Ажилтан')
    request_config_id     = fields.Many2one('request.order.config',string="Төлөв")
    report_type = fields.Selection([('full_report','Дэлгэрэнгүй'),('summary_report','Хураангуй')],string="Report type" , default="")
    job_ids = fields.Many2many('hr.job',string="Jobs")

    @api.onchange('type')
    def onchange_type(self):
        is_true= self.env.user.has_group('nomin_project.group_project_admin')
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


    
    def action_export(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        report_type = {
            'sector':u'Салбар',
            'employee':u'Ажилтан',
        }
        header = workbook.add_format({'border':1,'fg_color':'#b0e2ff','align':'justify','valign':'vjustify','text_wrap':100,'pattern':0})
        employee = self.env['hr.employee']
        employee_id = employee.sudo().search([('user_id','=',self._uid)])

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
        file_name = u'Гүйцэтгэсэн ажлын тайлан '
        sheet.set_row(2, 30)
        # sheet.write(1, 0, u'БАТЛАВ:'+  self.date_from)
        sheet.merge_range(2, 0, 2, col ,file_name,title)
        sheet.write(2, 0, u'БАТЛАВ: "Номин Реалтор ХХК"-ийн гүйцэтгэх захирал .............................................../Н.Шинэбаяр/')
        # sheet.write_merge(row,row, 3, 0,u'Тайлан хэвлэсэн: ................... /%s/'%(employee_id.name))
        sheet.write(3, 0,  self.date_from[:3] + ' оны ' + self.date_from[5:7] + ' сарын ажлын гүйцэтгэл')
        # sheet.write(4, 0, u'Дуусах хугацаа :'+ self.date_to )
        sheet.set_row(5, 20)
        sheet.set_column(0,0,5)
        sheet.set_column(1, 6,15)
        

        where = "where line.date_evaluate between '%s' and '%s' "%(self.date_from,self.date_to)
        if self.report_type == 'full_report':
            if self.type =='sector':            
                if self.sector_ids:
                    if len(self.sector_ids.ids)>1:
                        where=where+" and dep.id in %s"%(str(tuple(self.sector_ids.ids)))
                    else:               
                        where=where+" and dep.id = %s"%(str(self.sector_ids.ids[0]))
                
                if self.perform_department_ids:
                    if len(self.perform_department_ids.ids)>1:
                        where=where+" and perform.id in %s"%(str(tuple(self.perform_department_ids.ids)))
                    else:               
                        where=where+" and perform.id = %s"%(str(self.perform_department_ids.ids[0]))
            else:
                if self.employee_ids:                
                    if len(self.employee_ids.ids)>1:
                        where=where+" and employee.id in %s"%(str(tuple(self.employee_ids.ids)))
                    else:               
                        where=where+" and employee.id = %s"%(str(self.employee_ids.ids[0]))
        elif self.report_type == 'summary_report':
            if self.type =='sector':            
                if self.sector_ids:
                    if len(self.sector_ids.ids)>1:
                        where=where+" and dep.id in %s"%(str(tuple(self.sector_ids.ids)))
                    else:               
                        where=where+" and dep.id = %s"%(str(self.sector_ids.ids[0]))
                
                if self.perform_department_ids:
                    if len(self.perform_department_ids.ids)>1:
                        where=where+" and perform.id in %s"%(str(tuple(self.perform_department_ids.ids)))
                    else:               
                        where=where+" and perform.id = %s"%(str(self.perform_department_ids.ids[0]))
            if self.job_ids:                
                if len(self.job_ids.ids)>1:
                    where=where+" and job.id in %s"%(str(tuple(self.job_ids.ids)))
                else:               
                    where=where+" and job.id = %s"%(str(self.job_ids.ids[0]))
       
            if self.employee_ids:                
                if len(self.employee_ids.ids)>1:
                    where=where+" and employee.id in %s"%(str(tuple(self.employee_ids.ids)))
                else:               
                    where=where+" and employee.id = %s"%(str(self.employee_ids.ids[0]))

        query=" SELECT employee.last_name as last_name ,line.total_score as total_score ,job.name as job, time.name as time , line.finished_date as finished_date, line.date_evaluate as date_evaluate , line.date as date,line.state as state ,line.rate as rate ,line.maintenance as maintenance,line.qty as qty, work.name as service , line.id as line,line.amount as total_sum,\
                    a.name as id , a.request_name as request_name , dep.name as req_department_name , emp.name_related as employee , perform.name as perform_department_name , cost.name as cost_department_name , \
                    employee.name_related as perform_employee,a.date_order as start_time,a.date_due as date_to ,a.description as description , a.is_urgent as urgent\
                FROM request_order a \
                    LEFT join hr_employee emp on a.employee_id = emp.id\
                    LEFT join hr_department dep on  a.department_id = dep.id \
                    LEFT join hr_department sector on  a.sector_id = sector.id \
                    LEFT join hr_department perform on  a.perform_department_id = perform.id \
                    LEFT join hr_department cost on  a.cost_sector_id = cost.id \
                    LEFT join request_order_line line on a.id = line.order_id \
                    LEFT join hr_employee employee on line.perform_employee_id = employee.id\
                    LEFT join work_service work on line.service_id = work.id \
                    LEFT join work_service_time time on work.time_id = time.id \
                    LEFT join hr_job job on employee.job_id = job.id \
                 "
        query = query +where
        self.env.cr.execute(query)
        if self.report_type == 'full_report':
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
            sheet.merge_range(row, 12,row+2, 12, u'Яаралтай эсэх', header_color)
            sheet.set_column(12,12,15)
            sheet.merge_range(row, 13,row, 17, u'Огноо', header_color)
            sheet.merge_range(row+1, 13,row+2, 13, u'Захиалга өгсөн', header_color)
            sheet.merge_range(row+1, 14,row+2, 14, u'Дизайнерт хуваарилсан', header_color)
            sheet.merge_range(row+1, 15,row+2, 15, u'Дуусгах шаардлагай', header_color)
            sheet.merge_range(row+1, 16,row+2, 16, u'Дизайнер дуусгасан ', header_color)
            sheet.merge_range(row+1, 17,row+2, 17, u'Захиалга хаасан ', header_color)
            sheet.merge_range(row, 18,row+2, 18, u'Тайлбар', header_color)
            sheet.set_column(18,18,15)
            sheet.merge_range(row, 19,row+2, 19, u'Төлөв', header_color)
            sheet.set_column(19,19,15)
            sheet.merge_range(row, 20,row+2, 20, u'Зардал гаргах салбар', header_color)
            sheet.set_column(20,20,15)
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
                                'employee':u'',
                                'request_name':u'',
                                'request_number':u'',
                                'perform_department_name':u'',
                                'cost_department_name':u'',
                                'perform_employee':u'',
                                'qty':u'',
                                'maintenance_qty':u'',
                                'rate':u'',
                                'urgent':u'',
                                'total_sum':0,
                                'date_order':u'',
                                'date_evaluate ':u'',                            
                                'state ':u'',
                                'lines':{},
                            }


                        sectors[group]['orders'][group1]['request_name']= dic['request_name']
                        sectors[group]['orders'][group1]['name']= dic['service']
                        sectors[group]['orders'][group1]['employee']= dic['employee']
                        sectors[group]['orders'][group1]['request_number']= dic['id']
                        sectors[group]['orders'][group1]['perform_department_name']= dic['perform_department_name']
                        sectors[group]['orders'][group1]['perform_employee']= dic['perform_employee']
                        sectors[group]['orders'][group1]['qty']= dic['qty']
                        sectors[group]['orders'][group1]['maintenance_qty']= dic['maintenance']
                        sectors[group]['orders'][group1]['rate']= dic['rate']
                        sectors[group]['orders'][group1]['total_sum']+= dic['total_sum'] if dic['total_sum']  else 0
                        sectors[group]['orders'][group1]['date_order']= dic['start_time']
                        sectors[group]['orders'][group1]['date_due']= dic['date_to']
                        sectors[group]['orders'][group1]['urgent']= dic['urgent']
                        sectors[group]['orders'][group1]['date_evaluate']= dic['date_evaluate']
                        sectors[group]['orders'][group1]['description']= dic['description']
                        sectors[group]['orders'][group1]['state']= dic['state']
                        sectors[group]['orders'][group1]['cost_department_name']= dic['cost_department_name']
                        group2 = dic['line']
                        if group2 not in sectors[group]['orders'][group1]['lines']:
                            sectors[group]['orders'][group1]['lines'][group2] = {
                                'perform_department_name':u'',
                                'cost_department_name':u'',
                                'perform_employee':u'',
                                'employee':'',
                                'qty':u'',
                                'maintenance_qty':u'',
                                'urgent':u'',
                                'rate':u'',
                                'total_sum':0,
                                'date_order':u'',
                                'date_to':u'',
                                'date':u'',
                                'finished_date':u'',
                                'date_evaluate ':u'',                            
                                'state ':u'',
                                'line':u'',
                                'name':u'',
                            }
                        sectors[group]['orders'][group1]['lines'][group2]['line']= dic['line']
                        sectors[group]['orders'][group1]['lines'][group2]['name']= dic['service']
                        sectors[group]['orders'][group1]['lines'][group2]['employee']= dic['employee']
                        sectors[group]['orders'][group1]['lines'][group2]['perform_department_name']= dic['perform_department_name']
                        sectors[group]['orders'][group1]['lines'][group2]['perform_employee']= dic['perform_employee']
                        sectors[group]['orders'][group1]['lines'][group2]['qty']= dic['qty']
                        sectors[group]['orders'][group1]['lines'][group2]['maintenance_qty']= dic['maintenance']
                        sectors[group]['orders'][group1]['lines'][group2]['finished_date']= dic['finished_date']
                        sectors[group]['orders'][group1]['lines'][group2]['date']= dic['date']
                        sectors[group]['orders'][group1]['lines'][group2]['rate']= dic['rate']
                        sectors[group]['orders'][group1]['lines'][group2]['total_sum'] += dic['total_sum'] if dic['total_sum']  else 0
                        sectors[group]['orders'][group1]['lines'][group2]['date_order']= dic['start_time']
                        sectors[group]['orders'][group1]['lines'][group2]['date_to']= dic['date_to']
                        sectors[group]['orders'][group1]['lines'][group2]['urgent']= dic['urgent']
                        sectors[group]['orders'][group1]['lines'][group2]['date_evaluate']= dic['date_evaluate']
                        sectors[group]['orders'][group1]['lines'][group2]['description']= dic['description']
                        sectors[group]['orders'][group1]['lines'][group2]['state']= dic['state']
                        sectors[group]['orders'][group1]['lines'][group2]['cost_department_name']= dic['cost_department_name']


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

                    urgents = {
                        'False',u'Үгүй',
                        'True',u'Тийм',
                    }

                    for sector in sorted(sectors.values(), key=itemgetter('sector')):
                        count = 1
                        for service in sorted(sector['orders'].values(), key=itemgetter('request_number')):
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
                                sheet.write(row, 12 , service['urgent'], cell_float_format_right)
                                sheet.write(row, 13 , service['date_order'], cell_float_format_right)
                                sheet.write(row, 14 , line['date'], cell_float_format_right)
                                sheet.write(row, 15 , service['date_due'], cell_float_format_right)
                                sheet.write(row, 16 , line['finished_date'], cell_float_format_right)
                                sheet.write(row, 17 , line['date_evaluate'], cell_float_format_right)
                                sheet.write(row, 18 , service['description'], cell_float_format_right)
                                # if service['urgent'] in urgents:
                                #     sheet.write(row, 12 ,urgents[service['urgent']], cell_float_format_right)
                                # else:
                                #     sheet.write(row, 12 ,'Тодорхойгүй', cell_float_format_right)
                                
                                if line['state'] in states:
                                    sheet.write(row, 19 , states[line['state']], cell_float_format_right)
                                else:
                                    sheet.write(row, 19 , 'Тодорхойгүй', cell_float_format_right)
                                sheet.write(row, 20 , service['cost_department_name'], cell_float_format_right)
                                
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
                                'cost_department_name':u'',
                                'perform_employee':u'',
                                'qty':u'',
                                'maintenance_qty':u'',
                                'rate':u'',
                                'urgent':u'',
                                'total_sum':0,
                                'date_order':u'',
                                'date_evaluate ':u'',                            
                                'state ':u'',
                                'lines':{},
                            }


                        employees[group]['orders'][group1]['request_name']= dic['request_name']
                        employees[group]['orders'][group1]['name']= dic['service']
                        employees[group]['orders'][group1]['employee']= dic['employee']
                        employees[group]['orders'][group1]['request_number']= dic['id']
                        employees[group]['orders'][group1]['perform_department_name']= dic['perform_department_name']
                        employees[group]['orders'][group1]['perform_employee']= dic['perform_employee']
                        employees[group]['orders'][group1]['qty']= dic['qty']
                        employees[group]['orders'][group1]['maintenance_qty']= dic['maintenance']
                        employees[group]['orders'][group1]['rate']= dic['rate']
                        employees[group]['orders'][group1]['total_sum']+= dic['total_sum'] if dic['total_sum']  else 0
                        employees[group]['orders'][group1]['date_order']= dic['start_time']
                        employees[group]['orders'][group1]['date_due']= dic['date_to']
                        employees[group]['orders'][group1]['urgent']= dic['urgent']
                        employees[group]['orders'][group1]['date_evaluate']= dic['date_evaluate']
                        employees[group]['orders'][group1]['description']= dic['description']
                        employees[group]['orders'][group1]['state']= dic['state']
                        employees[group]['orders'][group1]['cost_department_name']= dic['cost_department_name']
                        
                        group2 = dic['line']
                        if group2 not in employees[group]['orders'][group1]['lines']:
                            employees[group]['orders'][group1]['lines'][group2] = {
                                'perform_department_name':u'',
                                'cost_department_name':u'',
                                'perform_employee':u'',
                                'qty':u'',
                                'maintenance_qty':u'',
                                'urgent':u'',
                                'rate':u'',
                                'total_sum':0,
                                'date_order':u'',
                                'date_to':u'',
                                'date':u'',
                                'finished_date':u'',
                                'date_evaluate ':u'',                            
                                'state ':u'',
                                'line':u'',
                                'name':u'',
                                'employee':u'',
                            }
                        employees[group]['orders'][group1]['lines'][group2]['line']= dic['line']
                        employees[group]['orders'][group1]['lines'][group2]['name']= dic['service']
                        employees[group]['orders'][group1]['lines'][group2]['perform_department_name']= dic['perform_department_name']
                        employees[group]['orders'][group1]['lines'][group2]['perform_employee']= dic['perform_employee']
                        employees[group]['orders'][group1]['lines'][group2]['qty']= dic['qty']
                        employees[group]['orders'][group1]['lines'][group2]['maintenance_qty']= dic['maintenance']
                        employees[group]['orders'][group1]['lines'][group2]['finished_date']= dic['finished_date']
                        employees[group]['orders'][group1]['lines'][group2]['date']= dic['date']
                        employees[group]['orders'][group1]['lines'][group2]['rate']= dic['rate']
                        employees[group]['orders'][group1]['lines'][group2]['total_sum'] += dic['total_sum'] if dic['total_sum']  else 0
                        employees[group]['orders'][group1]['lines'][group2]['date_order']= dic['start_time']
                        employees[group]['orders'][group1]['lines'][group2]['date_to']= dic['date_to']
                        employees[group]['orders'][group1]['lines'][group2]['urgent']= dic['urgent']
                        employees[group]['orders'][group1]['lines'][group2]['date_evaluate']= dic['date_evaluate']
                        employees[group]['orders'][group1]['lines'][group2]['description']= dic['description']
                        employees[group]['orders'][group1]['lines'][group2]['state']= dic['state']
                        employees[group]['orders'][group1]['lines'][group2]['cost_department_name']= dic['cost_department_name']


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
                    for sector in sorted(employees.values(), key=itemgetter('sector')):
                        count = 1
                        for service in sorted(sector['orders'].values(), key=itemgetter('request_number')):
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
                                sheet.write(row, 12 , service['urgent'], cell_float_format_right)
                                sheet.write(row, 13 , service['date_order'], cell_float_format_right)
                                sheet.write(row, 14 , line['date'], cell_float_format_right)
                                sheet.write(row, 15 , service['date_due'], cell_float_format_right)
                                sheet.write(row, 16 , line['finished_date'], cell_float_format_right)
                                sheet.write(row, 17 , line['date_evaluate'], cell_float_format_right)
                                sheet.write(row, 18 , service['description'], cell_float_format_right)
                                if line['state'] in states:
                                    sheet.write(row, 19 , states[line['state']], cell_float_format_right)
                                else:
                                    sheet.write(row, 19 , 'Тодорхойгүй', cell_float_format_right)
                                sheet.write(row, 20 , service['cost_department_name'], cell_float_format_right)
                                
                                row+=1
        else:
            dictfetchall = self.env.cr.dictfetchall() 

            
            sheet.write(row, 0, u'Д/д', header_color)
            sheet.set_column(0,0,5)
            sheet.write(row, 1, u'Захиалгын дугаар', header_color)
            sheet.set_column(1,1,15)
            sheet.write(row, 2, u'Ажлын нэр', header_color)
            sheet.set_column(2,2,15)
            sheet.write(row, 3, u'Хэмжих', header_color)
            sheet.set_column(3,3,15)
            

            sheet.write(row, 4, u'Менежер', header_color)
            sheet.set_column(4,4,15)
            sheet.write(row, 5, u'Тоо ширхэг', header_color)
            sheet.set_column(5,5,15)
            sheet.write(row, 6, u'Нийт тоо', header_color)
            sheet.set_column(6,6,15)
            sheet.write(row, 7, u'Тайлбар', header_color)
            sheet.set_column(7,7,15)
           
            # row = row+2
            
            if dictfetchall:
                sectors={}
                employees={}
                jobs = {}

                for dic in dictfetchall:
                    group = dic['perform_employee']
                    if group not in employees:
                        employees[group]={                            
                            'perform_employee':u'',
                            'last_name':u'',
                            'job':u'',
                            'orders':{},

                        }
                    
                    
                    
                    employees[group]['perform_employee'] = dic['perform_employee']
                    employees[group]['last_name'] = dic['last_name']
                    employees[group]['job'] = dic['job']

                    
                    group1 = dic['id']
                    if group1 not in employees[group]['orders']:
                        employees[group]['orders'][group1]={                                
                            'request_number':u'',                                
                            'employee':u'',
                            'last_name':u'',                                                               
                            'lines':{},
                        }


                    
                    
                    employees[group]['orders'][group1]['employee']= dic['employee']                        
                    employees[group]['orders'][group1]['request_number']= dic['id']                       
                    
                    
                    
                    group2 = dic['line']
                    if group2 not in employees[group]['orders'][group1]['lines']:
                        employees[group]['orders'][group1]['lines'][group2] = {
                            'description':u'',
                            'qty':u'',
                            'total_score':u'',                           
                            'line':u'',
                            'name':u'',
                            'measure':u'',
                            'perform_employee':u'',
                            'last_name':u'',
                        }
                    employees[group]['orders'][group1]['lines'][group2]['line']= dic['line']
                    employees[group]['orders'][group1]['lines'][group2]['name']= dic['service']                        
                    employees[group]['orders'][group1]['lines'][group2]['qty']= dic['qty']
                    employees[group]['orders'][group1]['lines'][group2]['perform_employee']= dic['perform_employee']
                    employees[group]['orders'][group1]['lines'][group2]['last_name']= dic['last_name']                        
                    employees[group]['orders'][group1]['lines'][group2]['description']= dic['description']
                    employees[group]['orders'][group1]['lines'][group2]['total_score']= dic['total_score']
                    employees[group]['orders'][group1]['lines'][group2]['measure']= dic['time']


                row+=1  

                sumtotal_value = 0
                for sector in sorted(employees.values(), key=itemgetter('perform_employee')):  
                                
                    row +=1
                    sheet.merge_range(row, 0,row, 7, sector['job'] + ':  '+ sector['last_name'][0] +'.' + sector['perform_employee'])
                    
                    count = 1
                    row +=1
                    total_value = 0
                    for service in sorted(sector['orders'].values(), key=itemgetter('request_number')):    
                                                
                        for line in sorted(service['lines'].values(), key=itemgetter('line')):
                            total_value += line['total_score']
                            sumtotal_value += line['total_score']
                            row+=1
                            sheet.write(row , 0 , count )
                            
                            count+=1
                            sheet.write(row, 1 , service['request_number'], cell_float_format_right)
                            sheet.write(row, 2 , line['name'], cell_float_format_right)
                            sheet.write(row, 3 , line['measure'], cell_float_format_right)
                            sheet.write(row, 4 , service['employee'], cell_float_format_right)
                            sheet.write(row, 5 , line['qty'], cell_float_format_right)
                            sheet.write(row, 6 , line['total_score'], cell_float_format_right)
                            sheet.write(row, 7 , line['description'], cell_float_format_right)

                    row+=1
                    sheet.merge_range(row, 0,row, 6, total_value)                                      
                    row+=1
                row+=1
                sheet.merge_range(row, 0,row, 6, sumtotal_value)                                      
                row+=1

                    
        sheet.merge_range(row, 0, row, 6, u'Хянасан:  ............')
        row+=1
        sheet.merge_range(row, 0, row, 6, u'Боловсруулсан:/%s/'%(employee_id.job_id.name)  + ' .................... ' + '/%s'%(employee_id.last_name[0]) + '.' + '%s/'%(employee_id.name))
        workbook.close()
        out = base64.encodestring(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data':out,'name':file_name + '.xlsx'})

        

        return {
		'name': 'Export Report',
		'view_mode':'form',
		'res_model':'report.excel.output',
		'res_id':excel_id.id,
		'view_id':False,
		'type': 'ir.actions.act_window',
		'target':'new',
		'nodestroy': True,
		}

