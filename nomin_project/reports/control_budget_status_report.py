# -*- coding: utf-8 -*-

from odooo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from lxml import etree
from odoo.exceptions import UserError
import xlwt
from xlwt import *
from StringIO import StringIO
from datetime import date, datetime, timedelta
import time
from dateutil import rrule

class control_budget_status_report(models.TransientModel):
    _name = 'control.budget.status.report'
    _inherit = 'abstract.report.model'
    _description = 'Control Budget Status Report'

    project_id = fields.Many2one('project.project', required=True,string=u'Төсөл')
    

    @api.multi
    def get_export_data(self,report_code,context=None):
        if context is None:
            context = {}
        datas={}
        datas['model'] = 'project.project'
        datas['form'] = self.read(['project_id'])[0] 
        data = datas['form']
        employee                        = self.env['hr.employee']
        employee_id                     = employee.sudo().search([('user_id','=',self._uid)])
        
        ezxf = xlwt.easyxf
        style1 = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
        style2 = ezxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin; pattern: pattern solid, fore_color  light_turquoise')
        style3 = ezxf('font: bold off; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;',num_format_str='#,##0.00')
        style4 = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;',num_format_str='#,##0.00')
        style5 = ezxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, right thin;',num_format_str='#,##0.00')
        style2_1 = ezxf('font: bold off; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
        body_style2 = ezxf('font: bold off; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
        body_style_right = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
             
        book = xlwt.Workbook(encoding='utf8')
        sheet = book.add_sheet('Work Report')
        sheet.portrait=True
        ezxf = xlwt.easyxf
         
        sheet.write(2, 5, u'ТӨСВИЙН ГҮЙЦЭТГЭЛИЙН ТАЙЛАН', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
         
        row = 4
        sheet.write_merge(row,row, 1, 21,u'Төсвийн задаргаанууд', style2)
        sheet.write(row, 0,u'Төслийн нэр', style2)
        row += 1
        sheet.col(0).width = 8000
        project_name_row = row
        sheet.write_merge(row, row, 1, 3, u'Материал', style2)
        sheet.write_merge(row, row, 4, 6,u'Ажиллах хүч', style2)
        sheet.write_merge(row, row, 7, 9,u'Машин механизм', style2)
        sheet.write_merge(row, row, 10, 12,u'Тээврийн', style2)
        sheet.write_merge(row, row, 13, 15,u'Шууд', style2)
        sheet.write_merge(row, row, 16, 18,u'Бусад', style2)
        sheet.write_merge(row, row, 19, 21,u'Нийт', style2)
        row += 1
        sheet.write(row, 0,u'Төслийн нийт төсөв', style2)
        project_budget_row = row
        row += 1
        budgets_row = row +1
        sheet.write(row, 0,u'Хяналтын төсөвүүд', style2)
        sheet.write(row, 1,u'Төсөв', style2)
        sheet.write(row, 2,u'Гүйцэтгэл', style2)
        sheet.write(row, 3,u'Үлдэгдэл', style2)
        
        sheet.write(row, 4,u'Төсөв', style2)
        sheet.write(row, 5,u'Гүйцэтгэл', style2)
        sheet.write(row, 6,u'Үлдэгдэл', style2)
        
        sheet.write(row, 7,u'Төсөв', style2)
        sheet.write(row, 8,u'Гүйцэтгэл', style2)
        sheet.write(row, 9,u'Үлдэгдэл', style2)
        
        sheet.write(row, 10,u'Төсөв', style2)
        sheet.write(row, 11,u'Гүйцэтгэл', style2)
        sheet.write(row, 12,u'Үлдэгдэл', style2)
        
        sheet.write(row, 13,u'Төсөв', style2)
        sheet.write(row, 14,u'Гүйцэтгэл', style2)
        sheet.write(row, 15,u'Үлдэгдэл', style2)
        
        sheet.write(row, 16,u'Төсөв', style2)
        sheet.write(row, 17,u'Гүйцэтгэл', style2)
        sheet.write(row, 18,u'Үлдэгдэл', style2)
        
        sheet.write(row, 19,u'Төсөв', style2)
        sheet.write(row, 20,u'Гүйцэтгэл', style2)
        sheet.write(row, 21,u'Үлдэгдэл', style2)
        row += 1
#         state = ''
        if data['project_id']:
            project = self.env['project.project'].search([('id', '=',data['project_id'][0])])
            sheet.write(project_name_row, 0, u'%s'%project.name, ezxf('font: bold on;align:wrap off,vert centre,horiz centre;'))
            for line in project.main_line_ids:
                if line.confirm == True:
                    sheet.write_merge(project_budget_row, project_budget_row, 1, 3, line.material_line_limit, ezxf('font: bold on;align:wrap off,vert centre,horiz centre;',num_format_str='#,##0.00'))
                    sheet.write_merge(project_budget_row, project_budget_row, 4, 6,line.labor_line_limit, ezxf('font: bold on;align:wrap off,vert centre,horiz centre;',num_format_str='#,##0.00'))
                    sheet.write_merge(project_budget_row, project_budget_row, 7, 9,line.equipment_line_limit, ezxf('font: bold on;align:wrap off,vert centre,horiz centre;',num_format_str='#,##0.00'))
                    sheet.write_merge(project_budget_row, project_budget_row, 10, 12,line.carriage_limit, ezxf('font: bold on;align:wrap off,vert centre,horiz centre;',num_format_str='#,##0.00'))
                    sheet.write_merge(project_budget_row, project_budget_row, 13, 15,line.postage_line_limit, ezxf('font: bold on;align:wrap off,vert centre,horiz centre;',num_format_str='#,##0.00'))
                    sheet.write_merge(project_budget_row, project_budget_row, 16, 18,line.other_line_limit, ezxf('font: bold on;align:wrap off,vert centre,horiz centre;',num_format_str='#,##0.00'))
                    sheet.write_merge(project_budget_row, project_budget_row, 19, 21,line.total_investment, ezxf('font: bold on;align:wrap off,vert centre,horiz centre;',num_format_str='#,##0.00'))
                    
        if data['project_id']:
            project = self.env['project.project'].search([('id', '=',data['project_id'][0])])
            price = 0.0
            limit = 0.0
            balance = 0.0
            for line in project.main_line_ids:
                if line.confirm == True:
                    for budget in line.control_budget_ids:
                        sheet.write(budgets_row, 0,budget.name, style4)
                        for util_line in budget.budgets_utilization:
                            if util_line.budget_type == 'material':
                                price += util_line.price
                                balance += util_line.balance
                                limit += util_line.utilization
                        sheet.write(budgets_row, 1,price, style3)
                        sheet.write(budgets_row, 2,limit, style3)
                        sheet.write(budgets_row, 3,balance, style3)
                        price = 0.0
                        limit = 0.0
                        balance = 0.0
                        for util_line in budget.budgets_utilization:
                            if util_line.budget_type == 'labor':
                                price += util_line.price
                                balance += util_line.balance
                                limit += util_line.utilization
                        sheet.write(budgets_row, 4,price, style3)
                        sheet.write(budgets_row, 5,limit, style3)
                        sheet.write(budgets_row, 6,balance, style3)
                        price = 0.0
                        limit = 0.0
                        balance = 0.0
                        for util_line in budget.budgets_utilization:
                            if util_line.budget_type == 'equipment':
                                price += util_line.price
                                balance += util_line.balance
                                limit += util_line.utilization
                        sheet.write(budgets_row, 7,price, style3)
                        sheet.write(budgets_row, 8,limit, style3)
                        sheet.write(budgets_row, 9,balance, style3)
                        price = 0.0
                        limit = 0.0
                        balance = 0.0
                        for util_line in budget.budgets_utilization:
                            if util_line.budget_type == 'carriage':
                                price += util_line.price
                                balance += util_line.balance
                                limit += util_line.utilization
                        sheet.write(budgets_row, 10,price, style3)
                        sheet.write(budgets_row, 11,limit, style3)
                        sheet.write(budgets_row, 12,balance, style3)
                        price = 0.0
                        limit = 0.0
                        balance = 0.0
                        for util_line in budget.budgets_utilization:
                            if util_line.budget_type == 'postage':
                                price += util_line.price
                                balance += util_line.balance
                                limit += util_line.utilization
                        sheet.write(budgets_row, 13,price, style3)
                        sheet.write(budgets_row, 14,limit, style3)
                        sheet.write(budgets_row, 15,balance, style3)
                        price = 0.0
                        limit = 0.0
                        balance = 0.0
                        for util_line in budget.budgets_utilization:
                            if util_line.budget_type == 'other':
                                price += util_line.price
                                balance += util_line.balance
                                limit += util_line.utilization
                        sheet.write(budgets_row, 16,price, style3)
                        sheet.write(budgets_row, 17,limit, style3)
                        sheet.write(budgets_row, 18,balance, style3)
                        sheet.write(budgets_row, 19,budget.budgets_utilization_total, style4)
                        sheet.write(budgets_row, 20,budget.budgets_utilization_util, style4)
                        sheet.write(budgets_row, 21,budget.budgets_utilization_balance, style4)
                        price = 0.0
                        limit = 0.0
                        balance = 0.0
                        row += 1
                        budgets_row = row
                        
        sheet.write(row, 0,u'Төслийн нийт төсвийн үлдэгдэл', style2)
        if data['project_id']:
            project = self.env['project.project'].search([('id', '=',data['project_id'][0])])
            for line in project.main_line_ids:
                if line.confirm == True:
                    sheet.write_merge(row, row, 1, 3, line.material_line_real, style5)
                    sheet.write_merge(row, row, 4, 6,line.labor_line_real, style5)
                    sheet.write_merge(row, row, 7, 9,line.equipment_line_real, style5)
                    sheet.write_merge(row, row, 10, 12,line.carriage_real, style5)
                    sheet.write_merge(row, row, 13, 15,line.postage_line_real, style5)
                    sheet.write_merge(row, row, 16, 18,line.other_line_real, style5)
                    sheet.write_merge(row, row, 19, 21,line.total_real, style5)
        row +=3
        sheet.write_merge(row,row, 1, 4,u'Тайлан хэвлэсэн: ................... /%s/'%(employee_id.name), ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
       
                         
        return {'data':book}