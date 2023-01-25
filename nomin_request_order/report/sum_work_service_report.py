
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


class SumWorkServiceReport(models.TransientModel):
    _name = 'sum.work.service.report'



    date_from = fields.Date(string='Date from')
    date_to = fields.Date(string='Date to')    
    type = fields.Selection([('sector','Sector'),('employee','Employee')],string="Type", default = "sector")
    sector_ids = fields.Many2many(comodel_name = 'hr.department', string=u'Захиалагч Салбар')
    perform_department_ids = fields.Many2many('hr.department','hr_department_request_order_service_sum_report_perform_rel','department_id','report_id', string=u'Гүйцэтгэгч хэлтэс')
    employee_ids = fields.Many2many(comodel_name = 'hr.employee',string=u'Ажилтан')
    request_config_id     = fields.Many2one('request.order.config',string="Төлөв")




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
        report_type = {
            'sector':u'Салбар',
            'unit':u'Нэгж',
            'employee':u'нэгж',
        }
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
        file_name = u'Нэгтгэл тайлан '
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
                    where=where+" and employee.id in %s"%(str(tuple(self.employee_ids.ids)))
                else:               
                    where=where+" and employee.id = %s"%(str(self.employee_ids.ids[0]))

        query=" select line.date_evaluate as date_evaluate , line.date as date,line.state as state ,line.rate as rate ,line.maintenance as maintenance,line.qty as qty, work.name as service , line.id as line,line.amount as total_sum,\
                    a.name as id , a.request_name as request_name , dep.name as req_department_name , emp.name_related as employee , perform.name as perform_department_name , \
                    employee.name_related as perform_employee,a.date_order as start_time,a.description as description\
                            from request_order a \
                     left join hr_employee emp on a.employee_id = emp.id\
                     left join hr_department dep on  a.department_id = dep.id \
                     left join hr_department sector on  a.sector_id = sector.id \
                     left join hr_department perform on  a.perform_department_id = perform.id \
                    inner join request_order_line line on a.id = line.order_id \
                     left join hr_employee employee on line.perform_employee_id = employee.id\
                     left join work_service work on line.service_id = work.id \
                 "
        query = query +where
        self.env.cr.execute(query)
        dictfetchall = self.env.cr.dictfetchall() 

        sheet.set_row(9, 20)
        sheet.merge_range(row, 0,row+2, 0, u'Д/д', header_color)
        sheet.set_column(0,0,5)
        sheet.merge_range(row, 1,row+2, 1, u'Гүйцэтгэгч хэлтэс ', header_color)
        sheet.set_column(1,1,15)
        sheet.merge_range(row, 2,row+2, 2, u' Ажил гүйцэтгэгч ', header_color)
        sheet.set_column(2,2,15)
        sheet.merge_range(row, 3,row+2, 3, u'Захиалагч хэлтэс ', header_color)
        sheet.set_column(3,3,15)       
        sheet.merge_range(row, 4,row+2, 4, u'Гүйцэтгэсэн ажлын тоо ', header_color)
        sheet.set_column(4,4,15)
        sheet.merge_range(row, 5,row+2, 5, u'Ажил үйлчилгээ ', header_color)
        sheet.set_column(5,5,15)
        sheet.merge_range(row, 6,row+2, 6, u'Төлөв  ', header_color)
        sheet.set_column(6,6,15)
        sheet.merge_range(row, 7,row+2, 7, u'Нийт дүн ', header_color)
        sheet.set_column(7,7,15)
        row = row+2
   
        if dictfetchall:
            sectors={}
            employees = {}
            if self.type =='sector':
                for dic in dictfetchall:

                    group = dic['perform_department_name']
                    if group not in sectors:
                        sectors[group]={
                            'sector':u'',                                                
                            'employees':{},

                        }
                    sectors[group]['sector'] = group
                    
                    group1 = dic['perform_employee']

                    if group1 not in sectors[group]['employees']:
                        sectors[group]['employees'][group1]={
                            'name':u'',                            
                            'req_sectors':{},
                        }
                    sectors[group]['employees'][group1]['name'] = group1

                    group2 = dic['req_department_name']
                    if group2 not in sectors[group]['employees'][group1]['req_sectors']:
                        sectors[group]['employees'][group1]['req_sectors'][group2] = {
                            'name':u'',
                            'orders':{},
                        }
                    sectors[group]['employees'][group1]['req_sectors'][group2]['name'] = group2

                    group3 = dic['service']
                    if group3 not in sectors[group]['employees'][group1]['req_sectors'][group2]['orders']:
                        sectors[group]['employees'][group1]['req_sectors'][group2]['orders'][group3] = {
                            'name':u'',
                            'count':0,
                            'total_sum':0,
                            'states':{},
                            
                        }
                    sectors[group]['employees'][group1]['req_sectors'][group2]['orders'][group3]['name'] = group3

                    group4 = dic['state']

                    if group4 not in sectors[group]['employees'][group1]['req_sectors'][group2]['orders'][group3]['states']:
                        sectors[group]['employees'][group1]['req_sectors'][group2]['orders'][group3]['states'][group4] = {
                            'name':u'',
                            'count':0,
                            'total_sum':0,
                            'states':{},
                            
                        }

                    
                    sectors[group]['employees'][group1]['req_sectors'][group2]['orders'][group3]['states'][group4]['name'] = group4 
                    sectors[group]['employees'][group1]['req_sectors'][group2]['orders'][group3]['states'][group4]['count'] += 1
                    sectors[group]['employees'][group1]['req_sectors'][group2]['orders'][group3]['states'][group4]['total_sum'] += dic['total_sum'] 



                 

                row+=1  
                sum_total_value=0
                line_count=0

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
                    for employee in sorted(sector['employees'].values(), key=itemgetter('name')):
                        for dep in sorted(employee['req_sectors'].values(), key=itemgetter('name')):
                            for service in sorted(dep['orders'].values(), key=itemgetter('name')):
                                for state in sorted(service['states'].values(), key=itemgetter('name')):
                                    sheet.write(row, 0 , count)
                                    count += 1
                                    sheet.write(row, 1 , sector['sector'], cell_float_format_right)
                                    sheet.write(row, 2 , employee['name'], cell_float_format_right)
                                    sheet.write(row, 3 , dep['name'], cell_float_format_right)
                                    sheet.write(row, 4 , state['count'], cell_float_format_right)
                                    sheet.write(row, 5 , service['name'], cell_float_format_right)
                                    sheet.write(row, 6 , state['name'], cell_float_format_right)
                                    sheet.write(row, 7 , state['total_sum'], cell_float_format_right)

                            

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

