# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from lxml import etree
from odoo.exceptions import UserError
import xlwt
from xlwt import *
from datetime import date, datetime, timedelta
import time
from dateutil import rrule

class DeadlineProjectTask(models.TransientModel):
    _name = 'deadline.project.task'
    _description = 'Deadline Project Task'
    
    project_ids = fields.Many2one('project.project',string=u'Төсөл', required=True)
    user_id = fields.Many2many(comodel_name='res.users', string='User')
    reason_id = fields.Many2many(comodel_name='task.deadline.reason', string='Reason')
    project_stage = fields.Many2many(comodel_name='project.stage', string='Stage')
    
    @api.onchange('project_ids')
    def onchange_project_id(self):
        project = self.env['project.project'].search([('id','=',self.project_ids.id)])
        return {'domain':{'project_stage':[('id','in',project.project_stage.ids)]}}
    
    
    def get_export_data(self,report_code,context=None):
        if context is None:
            context = {}
        
        datas={}
        datas['model'] = 'project.task'
        datas['form'] = self.read(['project_ids','user_id','reason_id','project_stage'])[0] 
        data = datas['form']
        
        employee                        = self.env['hr.employee']
        employee_id                     = employee.sudo().search([('user_id','=',self._uid)])
        
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
        
        sheet.write(2, 5, u'Хугацаа хэтэрсэн ажлын шалтгааны тайлан ', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(3, 1, u'Төсөл : ', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(4, 1, u'Хариуцагч : ', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(5, 1, u'Шалтгаан : ', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(6, 1, u'Төслийн шат : ', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        
        search_value1 = [('deadline_task','!=', False)]
        search_value = []
        project_task_count = 0.0
        stage_search_value = []
        
        if data['project_ids']:
            sheet.write(3, 2, data['project_ids'][1],ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
            project = self.env['project.project'].search([('id', '=',data['project_ids'][0])])
            search_value.append(('task_id.project_id','=',project.id))
            search_value1.append(('project_id','=',project.id))
            
            result_count = self.env['project.task'].sudo().search(search_value1)
            project_task_count = len(result_count)
            
        
        if data['user_id']:
            user = self.env['res.users'].search([('id', 'in',data['user_id'])])
            col = 2
            for i in user:
                sheet.write(4, col, u'%s'%i.name, ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
                col += 1
            search_value.append(('task_id.user_id','in',user.ids))
            search_value1.append(('user_id','in',user.ids))
        else :
            sheet.write(4, 2, u'Бүгд', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        
        if data['project_stage']:
            stage_id = self.env['project.stage'].search([('id', 'in',data['project_stage'])])
            col = 2
            for i in stage_id:
                sheet.write(6, col, u'%s'%i.name, ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
                col += 1
            stage_search_value.append(('id','in',stage_id.ids))
            search_value1.append(('project_stage','in',stage_id.ids))
        else :
            sheet.write(6, 2, u'Бүгд', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        
        if data['reason_id']:
            reason_id = self.env['task.deadline.reason'].search([('id', 'in',data['reason_id'])])
            col = 2
            for i in reason_id:
                sheet.write(5, col, u'%s'%i.name, ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
                col += 1
            search_value.append(('reason_id','in',reason_id.ids))
        else :
            sheet.write(5, 2, u'Бүгд', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        
        result1 = self.env['project.task'].sudo().search(search_value1, order='id')
        
        stage_list = []
        for rs in result1:
            if rs.project_stage.id not in stage_list:
                stage_list.append(rs.project_stage.id)
        if not data['project_stage']:
            stage_search_value.append(('id','in',stage_list))
        stages = self.env['project.stage'].sudo().search(stage_search_value, order='id')
        
        id = 0
        result_dict = {}
        total_tasks = []
        for stage in stages:
            search_value.append(('task_id.project_stage','=',stage.id))
            result = self.env['task.deadline.reason.line'].sudo().search(search_value, order='id')
            search_value.remove(('task_id.project_stage','=',stage.id))
            reason_dict = {}
            for reason in result:
                if reason.task_id.id not in total_tasks:
                    total_tasks.append(reason.task_id.id)
                if reason.reason_id.id not in reason_dict:
                    reason_dict[reason.reason_id.id] = { 'name': reason.reason_id.name,'day': reason.count, 'task': [reason.task_id.id], 'task_count': 1, 'precent': 0}
                else:
                    reason_dict[reason.reason_id.id]['day'] += reason.count
                    if reason.task_id.id not in reason_dict[reason.reason_id.id]['task']:
                        reason_dict[reason.reason_id.id]['task_count'] += 1
                        reason_dict[reason.reason_id.id]['task'].append(reason.task_id.id)
            result_dict[id] = {'stage': [stage.id],'reason_dict':reason_dict}
            id +=1

        row = 8
        sheet.write(row, 0,u'№', style2)
        sheet.col(0).width = 1000
        sheet.row(row).height = 500
        sheet.write(row, 1,u'Шалтгаан', style2)
        sheet.col(1).width = 8000
        sheet.write(row, 2,u'Хоцорсон хоног', style2)
        sheet.col(2).width = 3000
        sheet.write(row, 3,u'Даалгаварын тоо', style2)
        sheet.col(3).width = 3600
        sheet.write(row, 4,u'Эзлэх хувь %', style2)
        sheet.col(4).width = 3000
        total_day = 0
        
        row += 1
        percent_row = row
        if result_dict:
            for stage in stages:
                count = 1
                sheet.write_merge(row,row, 0, 1,u'Төслийн үе шат', style2)
                sheet.write_merge(row,row, 2, 4,stage.name, style1)
                row += 1
                for res in result_dict:
                    if stage.id in result_dict[res]['stage']:
                        for rs in result_dict[res]['reason_dict']:
                            sheet.write(row,0,str(count), style2_1)
                            sheet.write(row,1,result_dict[res]['reason_dict'][rs]['name'], style2_1)
                            sheet.write(row,2,result_dict[res]['reason_dict'][rs]['day'], style2_1)
                            total_day += result_dict[res]['reason_dict'][rs]['day']
                            sheet.write(row,3,result_dict[res]['reason_dict'][rs]['task_count'], style2_1)
#                             percent = result_dict[res]['reason_dict'][rs]['task_count']*100
#                             sheet.write(row,4,percent/project_task_count, style2_1)
                            row += 1
                            count += 1
        percent_total = 0.0
        if result_dict:
            for stage in stages:
                percent_row += 1
                for res in result_dict:
                    if stage.id in result_dict[res]['stage']:
                        for rs in result_dict[res]['reason_dict']:
                            percent = result_dict[res]['reason_dict'][rs]['day']*100.0
                            sheet.write(percent_row,4,percent/total_day, style2_1)
                            percent_total += percent/total_day 
                            percent_row += 1
                            count += 1
        
        sheet.write_merge(row, row, 0, 1,u'Нийт', style2)
        sheet.write(row,2,total_day, style2_1)
        sheet.write(row,3,len(total_tasks), style2_1)
        sheet.write(row,4,percent_total, style2_1)
        
        row += 2
        sheet.write(row, 0,u'№', style2)
        sheet.row(row).height = 500
        sheet.write(row, 1,u'Даалгаварууд', style2)
        sheet.write(row, 2,u'Төлөвлөсөн', style2)
        sheet.write(row, 3,u'Гүйцэтгэсэн', style2)
        sheet.write(row, 4,u'Хоцорсон /хоног/', style2)
        sheet.write(row, 5,u'Хариуцагч', style2)
        sheet.col(5).width = 4000
        sheet.write(row, 6,u'Шалтгаан', style2)
        sheet.col(6).width = 6000
        sheet.write(row, 7,u'Өдөр', style2)
        sheet.col(7).width = 2000
        sheet.write(row, 8,u'Тайлбар', style2)
        sheet.col(8).width = 6000
        
        row += 1
        if result1:
            for stage in stages:
                count = 1
                sheet.write_merge(row,row, 0, 1,u'Төслийн үе шат', style2)
                sheet.write_merge(row,row, 2, 8,stage.name, style1)
                row += 1
                for data in result1:
                    if stage.id == data.project_stage.id:
                        rows = row
                        sheet.write_merge(row,row+len(data.deadline_task)-1, 0, 0,str(count), style2_1)
                        sheet.write_merge(row,row+len(data.deadline_task)-1, 1, 1,data.name, style2_1)
                        if data.task_date_start:
                            sheet.write_merge(row,row+len(data.deadline_task)-1, 2, 2,data.task_date_start, style2_1)
                        else:
                            sheet.write_merge(row,row+len(data.deadline_task)-1, 2, 2,'', style2_1)
                        if data.date_deadline:
                            sheet.write_merge(row,row+len(data.deadline_task)-1, 3, 3,data.date_deadline, style2_1)
                        else:
                            sheet.write_merge(row,row+len(data.deadline_task)-1, 3, 3,'', style2_1)
                        if data.count_date_deadline:
                            sheet.write_merge(row,row+len(data.deadline_task)-1, 4, 4,data.count_date_deadline, style2_1)
                        else:
                            sheet.write_merge(row,row+len(data.deadline_task)-1, 4, 4,'', style2_1)
                        if data.user_id.name:
                            sheet.write_merge(row,row+len(data.deadline_task)-1, 5, 5,data.user_id.name, style2_1)
                        else:
                            sheet.write_merge(row,row+len(data.deadline_task)-1, 5, 5,'', style2_1)
                        for line in data.deadline_task:
                            sheet.write(rows,6,line.reason_id.name, style2_1)
                            sheet.write(rows,7,line.count, style2_1)
                            if line.description:
                                sheet.write(rows,8,line.description, style2_1)
                            else:
                                sheet.write(rows,8,'', style2_1)
                            rows += 1
                        row += len(data.deadline_task)
                        count += 1
        sheet.write_merge(row, row, 0, 3,u'Нийт', style2)
        sheet.write(row,4,total_day, style2_1)
        
        row +=3
        sheet.write_merge(row,row, 1, 4,u'Тайлан хэвлэсэн: ................... /%s/'%(employee_id.name), ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        
        return {'data':book}