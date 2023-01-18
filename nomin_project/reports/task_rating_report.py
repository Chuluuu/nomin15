# -*- coding: utf-8 -*-

import datetime
import time
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from lxml import etree
from odoo.exceptions import UserError
import xlwt
from xlwt import *
from datetime import date, datetime, timedelta
from dateutil import rrule
# import time
# from StringIO import StringIO

class deadline_project_task(models.TransientModel):
    _name = 'project.task.rating.report'
    _inherit = 'abstract.report.model'
    _description = 'Project Task Rating Report'
    
    @api.model
    def _get_start_date(self):
        return datetime.strptime(fields.Datetime.now(), '%Y-%m-%d %H:%M:%S')

    @api.model
    def _get_end_date(self):
        return datetime.strptime(fields.Datetime.now(), '%Y-%m-%d %H:%M:%S')
    
    def weeks_between(self, start_date, end_date):
        weeks = rrule.rrule(rrule.WEEKLY, dtstart=start_date, until=end_date)
        return weeks.count()
    
    start_date = fields.Date(string=u'Эхлэх огноо', required=True, default=_get_start_date)
    end_date = fields.Date(string=u'Дуусах огноо', required=True, default=_get_end_date)
    project_id = fields.Many2many(comodel_name='project.project', required=True,string=u'Төсөл')
    user_id = fields.Many2many(comodel_name='res.users', string=u'Хариуцагч')
    department_id = fields.Many2many(comodel_name='hr.department', string=u'Салбар')
    
    @api.multi
    def get_export_data(self,report_code,context=None):
        if context is None:
            context = {}
            
        datas={}
        datas['model'] = 'project.task'
        datas['form'] = self.read(['project_id','user_id','department_id','project_stage','start_date','end_date'])[0] 
        data = datas['form']
        
        ezxf = xlwt.easyxf
        style1 = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
        style2 = ezxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin; pattern: pattern solid, fore_color light_turquoise')
        style2_1 = ezxf('font: bold off; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
        body_style2 = ezxf('font: bold off; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
        body_style_right = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
            
        book = xlwt.Workbook(encoding='utf8')
        sheet = book.add_sheet('Work Report')
        sheet.portrait=True
        ezxf = xlwt.easyxf
        
        employee                        = self.env['hr.employee']
        employee_id                     = employee.sudo().search([('user_id','=',self._uid)])
        
        sheet.write(2, 5, u'ДААЛГАВРЫН ГҮЙЦЭТГЭЛИЙН ТАЙЛАН', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(3, 1, u'Төсөл : ', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(4, 1, u'Хариуцагч : ', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(5, 1, u'Салбар : ', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write_merge(7, 7, 1, 5, u'Тайлант хугацаа : %s - %s'%(data['start_date'],data['end_date']), ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        
        search_value = []
#         search_value = [('task_date_start','>=',data['start_date']),('task_date_start','<=',data['end_date'])]
            
        if data['user_id']:
            users = self.env['res.users'].search([('id', 'in',data['user_id'])])
            col = 2
            for i in users:
                sheet.write(4, col, u'%s'%i.name, ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
                col += 1
            search_value.append(('user_id','in',users.ids))
        else :
            sheet.write(4, 2, u'Бүгд', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
            
        if data['department_id']:
            departments = self.env['hr.department'].search([('id', 'in',data['department_id'])])
            col = 2
            for i in departments:
                sheet.write(5, col, u'%s'%i.name, ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
                col += 1
            search_value.append(('department_id','in',departments.ids))
        else :
            sheet.write(5, 2, u'Бүгд', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        
        row = 10
        sheet.write(row, 0,u'№', style2)
        sheet.row(row).height = 700
        sheet.write(row, 1,u'Төлөв', style2)
        sheet.col(1).width = 3000
        sheet.write(row, 2,u'Эхлэх хугацаа', style2)
        sheet.col(2).width = 4000
        sheet.write(row, 3,u'Дуусах хугацаа', style2)
        sheet.col(3).width = 4000
        sheet.write(row, 4,u'Төлөвлөсөн эхлэх хугацаа', style2)
        sheet.col(4).width = 4000
        sheet.write(row, 5,u'Төлөвлөсөн дуусах хугацаа', style2)
        sheet.col(5).width = 4000
        sheet.write(row, 6,u'Даалгавар', style2)
        sheet.col(6).width = 10000
        sheet.write(row, 7,u'Хариуцагч Салбар хэлтэс', style2)
        sheet.col(7).width = 6000
        sheet.write(row, 8,u'Хариуцагч', style2)
        sheet.col(8).width = 4000
        sheet.write(row, 9,u'Тайлбар', style2)
        sheet.col(9).width = 8000
        
        sheet.write(row, 10,u'Tөлөвлөсөн цаг', style2)
        sheet.col(10).width = 3500
        sheet.write(row, 11,u'Ажилласан цаг', style2)
        sheet.col(11).width = 3500
        
        sheet.write(row, 12,u'Гүйцэтгэл', style2)
        sheet.col(12).width = 3000
        sheet.write(row, 13,u'Үнэлгээ', style2)
        sheet.col(13).width = 2500
        sheet.write(row, 14,u'Холбоотой ажил', style2)
        sheet.col(14).width = 6000
        sheet.write(row, 15,u'Төлөв', style2)
        sheet.col(15).width = 6000
        sheet.write(row, 16,u'Дуусах огноо', style2)
        sheet.col(16).width = 6000
#         sheet.row(row).height = 1000
        
        if data['project_id']:
            projects = self.env['project.project'].search([('id', 'in',data['project_id'])])
            col = 2
            for project in projects:
                sheet.write(3, col, u'%s'%project.name, ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
                col += 1
                count = 1
                search_value.append(('project_id','=',project.id))
                result = self.env['project.task'].sudo().search(search_value, order='id')
                search_value.remove(('project_id','=',project.id))
                if result:
                    row += 1
                    sheet.write_merge(row,row, 0, 3,u'Төсөл', style2)
                    sheet.write_merge(row,row, 4, 10,project.name, style1)
                    row += 1
                    for task in result:
                        if (task.task_date_start >= data['start_date'] and task.task_date_start <= data['end_date']) or (task.date_deadline >= data['start_date'] and task.date_deadline <= data['end_date']):
                            space = ', '
                            names = []
                            flow_str = ''
                            percent_str = ''
                            desc_str = ''
                            add_row = 0
                            total_time = 0.0
                            child_tasks = self.env['project.task'].search([('parent_task', '=',task.id)])
                            child_row = row
                            if child_tasks:
                                add_row = len(child_tasks)-1
                            sheet.write_merge(row,row+add_row ,0 , 0,str(count), style2_1)
                            if task.task_state == 't_new':
                                state = u'Шинэ'
                            if task.task_state == 't_cheapen':
                                state = u'Үнэ тохирох'
                            if task.task_state == 't_cheapened':
                                state = u'Үнэ тохирсон'
                            if task.task_state == 't_user':
                                state = u'Хариуцагчтай'
                            if task.task_state == 't_start':
                                state = u'Хийгдэж буй'
                            if task.task_state == 't_control':
                                state = u'Хянах'
                            if task.task_state == 't_confirm':
                                state = u'Батлах'
                            if task.task_state == 't_evaluate':
                                state = u'Үнэлэх'
                            if task.task_state == 't_done':
                                state = u'Дууссан'
                            if task.task_state == 't_cancel':
                                state = u'Цуцалсан'
                            if task.task_state == 't_back':
                                state = u'Хойшлуулсан'
                            sheet.write_merge(row,row+add_row ,1 , 1,state, style2_1)
                            sheet.write_merge(row,row+add_row ,2 , 2,task.task_date_start or '', style2_1)
                            sheet.write_merge(row,row+add_row ,3 , 3,task.date_deadline, style2_1)
                            sheet.write_merge(row,row+add_row ,4 , 4,task.planned_start_date, style2_1)
                            sheet.write_merge(row,row+add_row ,5 , 5,task.planned_end_date or '', style2_1)
                            sheet.write_merge(row,row+add_row ,6 , 6,task.name, style2_1)
                            sheet.write_merge(row,row+add_row ,7 , 7,task.department_id.name, style2_1)
                            sheet.write_merge(row,row+add_row ,8 , 8,task.user_id.name, style2_1)
                            if task.description != False:
                                desc_str = str(task.description)
                            sheet.write_merge(row,row+add_row ,9 , 9,desc_str, style2_1)
                            
                            sheet.write_merge(row,row+add_row ,10 , 10,task.planned_hours, style2_1)
                            for line in task.timesheet_ids:
                                total_time += line.unit_amount
                            sheet.write_merge(row,row+add_row ,11 , 11,total_time, style2_1)
                            flow_str = str(task.flow) + '%'
                            sheet.write_merge(row,row+add_row ,12 , 12,flow_str, style2_1)
                            flow_str = ''
                            if task.task_type != 'normal':
                                percent_str = str(task.total_percent)
                            sheet.write_merge(row,row+add_row ,13 , 13,percent_str, style2_1)
                            percent_str = ''
                            
                            for child in child_tasks:
                                sheet.write(child_row, 14,child.name, style2_1)
                                if child.task_state == 't_new':
                                    c_state = u'Шинэ'
                                if child.task_state == 't_cheapen':
                                    c_state = u'Үнэ тохирох'
                                if child.task_state == 't_cheapened':
                                    c_state = u'Үнэ тохирсон'
                                if child.task_state == 't_user':
                                    c_state = u'Хариуцагчтай'
                                if child.task_state == 't_start':
                                    c_state = u'Хийгдэж буй'
                                if child.task_state == 't_control':
                                    c_state = u'Хянах'
                                if child.task_state == 't_confirm':
                                    c_state = u'Батлах'
                                if child.task_state == 't_evaluate':
                                    c_state = u'Үнэлэх'
                                if child.task_state == 't_done':
                                    c_state = u'Дууссан'
                                if child.task_state == 't_cancel':
                                    c_state = u'Цуцалсан'
                                if child.task_state == 't_back':
                                    c_state = u'Хойшлуулсан'
                                sheet.write(child_row, 15,c_state, style2_1)
                                sheet.write(child_row, 16,child.date_deadline, style2_1)
                                child_row += 1
                            count += 1
                            row += 1
                            row += add_row
        
        row +=10
        sheet.write_merge(row,row, 1, 4,u'Тайлан хэвлэсэн: ................... /%s/'%(employee_id.name), ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        
        return {'data':book}