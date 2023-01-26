
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
class DoctorReport(models.TransientModel):
    _name = 'doctor.report'

    date_from = fields.Date(string='Date from')
    date_to = fields.Date(string='Date to')    
    type = fields.Selection([('sector','Sector'),('employee','request employee')],string="Type", default = "sector")
    sector_ids = fields.Many2many(comodel_name = 'hr.department', string=u'Захиалагч Салбар')
    perform_department_ids = fields.Many2many('hr.department','hr_department_doctor_report_perform_rel','dep_id','doc_report_id', string=u'Гүйцэтгэгч хэлтэс')    
    employee_ids = fields.Many2many(comodel_name = 'hr.employee',string=u'Ажилтан')
    request_config_id     = fields.Many2one('request.order.config',string="Төлөв")
    # state = fields.Selection([('open','Open'),('pending','Pending'),('control','Control'),('done','Done')], string="State" , default="done")




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
        file_name = u'Эмчийн тайлан'
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

        query="SELECT DATE_PART('year', CURRENT_DATE) - DATE_PART('year', emp.birthday) as age,emp.gender as gender, category.name as category, line.date_evaluate as date_evaluate , line.date as date,line.state as state ,line.rate as rate ,line.maintenance as maintenance,line.qty as qty, work.name as service , line.id as line,line.amount as total_sum,\
                    line.pain as pain,d.name as diagnosis,line.vital_signs as vital_signs,line.treatment_adv as treatment_adv,line.end_date as end_date,a.name as id , a.request_name as request_name , dep.name as req_department_name , emp.name_related as employee , perform.name as perform_department_name , \
                    employee.name_related as perform_employee,a.date_order as start_time,a.description as description\
                    FROM request_order a \
                LEFT JOIN hr_employee emp on a.employee_id = emp.id\
                LEFT JOIN hr_department dep on  a.department_id = dep.id \
                LEFT JOIN hr_department sector on  a.sector_id = sector.id \
                LEFT JOIN hr_department perform on  a.perform_department_id = perform.id \
                LEFT JOIN request_order_line line on a.id = line.order_id \
                LEFT JOIN diagnosis_list d on line.diagnosis = d.id \
                LEFT JOIN hr_employee employee on line.perform_employee_id = employee.id\
                LEFT JOIN work_service work on line.service_id = work.id \
                LEFT JOIN knowledge_store_category category on line.category_id = category.id \
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

        sheet.merge_range(row, 5,row+2, 5, u'Нас', header_color)
        sheet.set_column(5,5,15)
        sheet.merge_range(row, 6,row+2, 6, u'Хүйс', header_color)
        sheet.set_column(6,6,15)
        sheet.merge_range(row, 7,row+2, 7, u'Ангилал', header_color)
        sheet.set_column(7,7,15)

        sheet.merge_range(row, 8,row+2, 8, u'Ажлын нэр', header_color)
        sheet.set_column(8,8,15)
        sheet.merge_range(row, 9,row+2, 9, u'Зовиур', header_color)
        sheet.set_column(9,9,15)
        sheet.merge_range(row, 10,row+2, 10, u'Амин үзүүлэлт', header_color)
        sheet.set_column(10,10,15)
      
        sheet.merge_range(row, 11,row+2, 11, u'Онош', header_color)
        sheet.set_column(11,11,15)
        sheet.merge_range(row, 12,row+2, 12, u'Эмчилгээ зөвлөгөө', header_color)
        sheet.set_column(12,12,15)
        sheet.merge_range(row, 13,row+2, 13, u'Хаасан огноо', header_color)
        sheet.set_column(13,13,15)
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
                            'age':u'',
                            'gender':u'',
                            'category':u'',
                            'perform_employee':u'',
                            'qty':u'',
                            'maintenance_qty':u'',
                            'rate':u'',
                            'total_sum':0,
                            'date_order':u'',
                            'date_evaluate ':u'',                            
                            'state ':u'',
                            'lines':{},
                        }


                    sectors[group]['orders'][group1]['request_name']= dic['request_name']
                    sectors[group]['orders'][group1]['name']= dic['service']
                    sectors[group]['orders'][group1]['request_number']= dic['id']
                    sectors[group]['orders'][group1]['perform_department_name']= dic['perform_department_name']
                    sectors[group]['orders'][group1]['perform_employee']= dic['perform_employee']
                    sectors[group]['orders'][group1]['age']= dic['age']
                    sectors[group]['orders'][group1]['gender']= dic['gender']
                    sectors[group]['orders'][group1]['category']= dic['category']
                    sectors[group]['orders'][group1]['employee']= dic['employee']
                    sectors[group]['orders'][group1]['pain']= dic['pain']
                    sectors[group]['orders'][group1]['diagnosis']= dic['diagnosis']
                    sectors[group]['orders'][group1]['treatment_adv']= dic['treatment_adv']
                    sectors[group]['orders'][group1]['end_date']= dic['end_date']
                    sectors[group]['orders'][group1]['vital_signs']= dic['vital_signs']
                    sectors[group]['orders'][group1]['qty']= dic['qty']
                    sectors[group]['orders'][group1]['maintenance_qty']= dic['maintenance']
                    sectors[group]['orders'][group1]['rate']= dic['rate']
                    sectors[group]['orders'][group1]['total_sum']+= dic['total_sum'] if dic['total_sum']  else 0
                    sectors[group]['orders'][group1]['date_order']= dic['start_time']
                    sectors[group]['orders'][group1]['date_evaluate']= dic['date_evaluate']
                    sectors[group]['orders'][group1]['description']= dic['description']
                    sectors[group]['orders'][group1]['state']= dic['state']
                    group2 = dic['line']
                    if group2 not in sectors[group]['orders'][group1]['lines']:
                        sectors[group]['orders'][group1]['lines'][group2] = {
                            'perform_department_name':u'',
                            'perform_employee':u'',
                            'age':u'',
                            'gender':u'',
                            'category':u'',
                            'qty':u'',
                            'pain':u'',
                            'treatment_adv':u'',
                            'diagnosis':u'',
                            'end_date':u'',
                            'vital_signs':u'',
                            'maintenance_qty':u'',
                            'rate':u'',
                            'total_sum':0,
                            'date_order':u'',
                            'date_evaluate ':u'',                            
                            'state ':u'',
                            'line':u'',
                            'name':u'',
                        }
                    sectors[group]['orders'][group1]['lines'][group2]['line']= dic['line']
                    sectors[group]['orders'][group1]['lines'][group2]['name']= dic['service']
                    sectors[group]['orders'][group1]['lines'][group2]['perform_department_name']= dic['perform_department_name']
                    sectors[group]['orders'][group1]['lines'][group2]['perform_employee']= dic['perform_employee']
                    sectors[group]['orders'][group1]['lines'][group2]['pain']= dic['pain']
                    sectors[group]['orders'][group1]['lines'][group2]['treatment_adv']= dic['treatment_adv']
                    sectors[group]['orders'][group1]['lines'][group2]['diagnosis']= dic['diagnosis']
                    sectors[group]['orders'][group1]['lines'][group2]['end_date']= dic['end_date']
                    sectors[group]['orders'][group1]['lines'][group2]['vital_signs']= dic['vital_signs']
                    sectors[group]['orders'][group1]['lines'][group2]['qty']= dic['qty']
                    sectors[group]['orders'][group1]['lines'][group2]['age']= dic['age']
                    sectors[group]['orders'][group1]['lines'][group2]['gender']= dic['gender']
                    sectors[group]['orders'][group1]['lines'][group2]['category']= dic['category']
                    sectors[group]['orders'][group1]['lines'][group2]['maintenance_qty']= dic['maintenance']
                    sectors[group]['orders'][group1]['lines'][group2]['rate']= dic['rate']
                    sectors[group]['orders'][group1]['lines'][group2]['total_sum'] += dic['total_sum'] if dic['total_sum']  else 0
                    sectors[group]['orders'][group1]['lines'][group2]['date_order']= dic['start_time']
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
                genders = {
                    'female':'Эмэгтэй',
                    'male':'Эрэгтэй',
                }
                count = 1
                for sector in sorted(sectors.values(), key=itemgetter('sector')):

                    for service in sorted(sector['orders'].values(), key=itemgetter('name')):
                        for line in sorted(service['lines'].values(), key=itemgetter('line')):
                            sheet.write(row , 0 , count )
                            count+=1
                            sheet.write(row, 1 , service['request_number'], cell_float_format_right)
                            sheet.write(row, 2 , service['request_name'], cell_float_format_right)
                            sheet.write(row, 3 , sector['sector'], cell_float_format_right)
                            sheet.write(row, 4 , service['employee'], cell_float_format_right)
                            sheet.write(row, 5 , service['age'], cell_float_format_right)
                            if service['gender'] in genders:
                                sheet.write(row, 6 , genders[service['gender']], cell_float_format_right)
                            else:
                                sheet.write(row, 6 , 'Тодорхойгүй', cell_float_format_right)
                            
                            sheet.write(row, 7 , service['category'], cell_float_format_right)
                            sheet.write(row, 8 , line['name'], cell_float_format_right)
                            sheet.write(row, 9 , line['pain'], cell_float_format_right)
                            sheet.write(row, 10 , line['vital_signs'], cell_float_format_right)
                            sheet.write(row, 11 , line['diagnosis'], cell_float_format_right)
                            sheet.write(row, 12 , line['treatment_adv'], cell_float_format_right)
                            sheet.write(row, 13 , line['end_date'], cell_float_format_right)
                          
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
                            'age':u'',
                            'gender':u'',
                            'category':u'',
                            'perform_employee':u'',
                            'qty':u'',
                            'pain':u'',
                            'treatment_adv':u'',
                            'diagnosis':u'',
                            'end_date':u'',
                            'vital_signs':u'',
                            'maintenance_qty':u'',
                            'rate':u'',
                            'total_sum':0,
                            'date_order':u'',
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
                    employees[group]['orders'][group1]['pain']= dic['pain']
                    employees[group]['orders'][group1]['treatment_adv']= dic['treatment_adv']
                    employees[group]['orders'][group1]['diagnosis']= dic['diagnosis']
                    employees[group]['orders'][group1]['end_date']= dic['end_date']
                    employees[group]['orders'][group1]['vital_signs']= dic['vital_signs']
                    employees[group]['orders'][group1]['qty']= dic['qty']
                    employees[group]['orders'][group1]['age']= dic['age']
                    employees[group]['orders'][group1]['gender']= dic['gender']
                    employees[group]['orders'][group1]['category']= dic['category']
                    employees[group]['orders'][group1]['maintenance_qty']= dic['maintenance']
                    employees[group]['orders'][group1]['rate']= dic['rate']
                    employees[group]['orders'][group1]['total_sum']+= dic['total_sum'] if dic['total_sum']  else 0
                    employees[group]['orders'][group1]['date_order']= dic['start_time']
                    employees[group]['orders'][group1]['date_evaluate']= dic['date_evaluate']
                    employees[group]['orders'][group1]['description']= dic['description']
                    employees[group]['orders'][group1]['state']= dic['state']
                    group2 = dic['line']
                    if group2 not in employees[group]['orders'][group1]['lines']:
                        employees[group]['orders'][group1]['lines'][group2] = {
                            'perform_department_name':u'',
                            'perform_employee':u'',
                            'qty':u'',
                            'pain':u'',
                            'treatment_adv':u'',
                            'diagnosis':u'',
                            'end_date':u'',
                            'vital_signs':u'',
                            'age':u'',
                            'gender':u'',
                            'category':u'',
                            'maintenance_qty':u'',
                            'rate':u'',
                            'total_sum':0,
                            'date_order':u'',
                            'date_evaluate ':u'',                            
                            'state ':u'',
                            'line':u'',
                            'name':u'',
                        }
                    employees[group]['orders'][group1]['lines'][group2]['line']= dic['line']
                    employees[group]['orders'][group1]['lines'][group2]['name']= dic['service']
                    employees[group]['orders'][group1]['lines'][group2]['perform_department_name']= dic['perform_department_name']
                    employees[group]['orders'][group1]['lines'][group2]['perform_employee']= dic['perform_employee']
                    employees[group]['orders'][group1]['lines'][group2]['pain']= dic['pain']
                    employees[group]['orders'][group1]['lines'][group2]['treatment_adv']= dic['treatment_adv']
                    employees[group]['orders'][group1]['lines'][group2]['diagnosis']= dic['diagnosis']
                    employees[group]['orders'][group1]['lines'][group2]['vital_signs']= dic['vital_signs']
                    employees[group]['orders'][group1]['lines'][group2]['end_date']= dic['end_date']
                    employees[group]['orders'][group1]['lines'][group2]['qty']= dic['qty']
                    employees[group]['orders'][group1]['lines'][group2]['age']= dic['age']
                    employees[group]['orders'][group1]['lines'][group2]['gender']= dic['gender']
                    employees[group]['orders'][group1]['lines'][group2]['category']= dic['category']
                    employees[group]['orders'][group1]['lines'][group2]['maintenance_qty']= dic['maintenance']
                    employees[group]['orders'][group1]['lines'][group2]['rate']= dic['rate']
                    employees[group]['orders'][group1]['lines'][group2]['total_sum'] += dic['total_sum'] if dic['total_sum']  else 0
                    employees[group]['orders'][group1]['lines'][group2]['date_order']= dic['start_time']
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

                genders = {
                    'female':'Эмэгтэй',
                    'male':'Эрэгтэй',
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
                            if service['gender'] in genders:
                                sheet.write(row, 6 , genders[service['gender']], cell_float_format_right)
                            else:
                                sheet.write(row, 6 , 'Тодорхойгүй', cell_float_format_right)
                            sheet.write(row, 5 , service['age'], cell_float_format_right)
                            sheet.write(row, 7 , service['category'], cell_float_format_right)
                            sheet.write(row, 8 , line['name'], cell_float_format_right)
                            sheet.write(row, 9 , line['pain'], cell_float_format_right)
                            sheet.write(row, 10 , line['vital_signs'], cell_float_format_right)
                            sheet.write(row, 11 , line['diagnosis'], cell_float_format_right)
                            sheet.write(row, 12 , line['treatment_adv'], cell_float_format_right)
                            sheet.write(row, 13 , line['end_date'], cell_float_format_right)
                           
                            
                            row+=1
           


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

