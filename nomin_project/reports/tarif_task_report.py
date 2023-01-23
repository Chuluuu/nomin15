# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from lxml import etree
from odoo.exceptions import UserError
import xlwt
from xlwt import *
from datetime import date, datetime, timedelta
import time
from operator import itemgetter
from dateutil import rrule

class project_tarif_task_report(models.TransientModel):
    _name = 'project.tarif.task.report'
    _description = 'Project Tarif Task Report'
    
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
    
    project_ids = fields.Many2many(comodel_name='project.project', required=True,string=u'Төсөл')
    user_ids = fields.Many2many(comodel_name='res.users', string=u'Хариуцагч')
    departments = fields.Many2many(comodel_name='hr.department', string=u'Хэлтэс')
    category_ids = fields.Many2many(comodel_name='knowledge.store.category', string=u'Тарифт ажлын ангилал')
    work_service = fields.Many2many(comodel_name='work.service',string=u'Тарифт ажил')
    
    
    def get_export_data(self,report_code,context=None):
        if context is None:
            context = {}
            
        datas={}
        datas['model'] = 'task.tarif.line'
        datas['form'] = self.read(['project_ids','user_ids','departments','category_ids','work_service','start_date','end_date'])[0] 
        data = datas['form']
        
        employee                        = self.env['hr.employee']
        employee_id                     = employee.sudo().search([('user_id','=',self._uid)])
        
        ezxf = xlwt.easyxf
        style1 = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
        style2 = ezxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin; pattern: pattern solid, fore_color light_turquoise')
        style3 = ezxf('font: bold on; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin; pattern: pattern solid, fore_color light_turquoise')
        style2_1 = ezxf('font: bold off; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
        style2_12 = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
        body_style2 = ezxf('font: bold off; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
        body_style_right = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
            
        book = xlwt.Workbook(encoding='utf8')
        sheet = book.add_sheet('Work Report')
        sheet.portrait=True
        ezxf = xlwt.easyxf
        
        sheet.write(2, 5, u'ТАРИФТ АЖЛЫН ДЭЛГЭРЭНГҮЙ ТАЙЛАН', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(3, 1, u'Төсөл : ', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(4, 1, u'Хариуцагч : ', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(5, 1, u'Хэлтэс : ', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(6, 1, u'Тарифт ажлын ангилал : ', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(7, 1, u'Тарифт ажил : ', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        
        task_search_value = [('task_id.task_type','!=','normal'),('task_id.task_state','=','t_done')]
        work_search_value = []
        
        if data['project_ids']:
            projects = self.env['project.project'].search([('id', 'in',data['project_ids'])])
            col = 2
            for i in projects:
                sheet.write(3, col, u'%s'%i.name, ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
                col += 1
            task_search_value.append(('task_id.project_id','in',projects.ids))
            
        if data['user_ids']:
            users = self.env['res.users'].search([('id', 'in',data['user_ids'])])
            col = 2
            for i in users:
                sheet.write(4, col, u'%s'%i.name, ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
                col += 1
            task_search_value.append(('task_id.user_id','in',users.ids))
        else :
            sheet.write(4, 2, u'Бүгд', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        if data['departments']:
            deparments = self.env['hr.department'].search([('id', 'in',data['departments'])])
            col = 2
            for i in deparments:
                sheet.write(5, col, u'%s'%i.name, ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
                col += 1
            task_search_value.append(('task_id.department_id','in',deparments.ids))
        else :
            sheet.write(5, 2, u'Бүгд', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
            
        if data['category_ids']:
            categorys = self.env['knowledge.store.category'].search([('id', 'in',data['category_ids'])])
            col = 2
            for i in categorys:
                sheet.write(6, col, u'%s'%i.name, ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
                col += 1
            task_search_value.append(('work_id.category_id','in',categorys.ids))
        else :
            sheet.write(6, 2, u'Бүгд', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        
        if data['work_service']:
            works = self.env['work.service'].search([('id', 'in',data['work_service'])], order="id")
            col = 2
            for i in works:
                sheet.write(7, col, u'%s'%i.name, ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
                col += 1
            task_search_value.append(('work_id.id','in',works.ids))
        else :
            sheet.write(7, 2, u'Бүгд', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        
        line = self.env['task.tarif.line'].sudo().search(task_search_value, order='work_id')
        
        row = 10
        sheet.write(row, 0,u'№', style2)
        sheet.write(row, 1,u'Төсөл', style2)
        sheet.col(1).width = 6000
        sheet.write(row, 2,u'Ангилал', style2)
        sheet.col(2).width = 6000
        sheet.write(row, 3,u'Даалгаврын нэр', style2)
        sheet.col(3).width = 6000
        sheet.write(row, 4,u'Ажил үйлчилгээ', style2)
        sheet.col(4).width = 10000
        sheet.write(row, 5,u'Хариуцагч хэлтэс', style2)
        sheet.col(5).width = 6000
        sheet.write(row, 6,u'Хариуцагч', style2)
        sheet.col(6).width = 6000
        sheet.write(row, 7,u'Захиалагч салбар', style2)
        sheet.col(7).width = 6000
        sheet.write(row, 8,u'Захиалагч ажилтан', style2)
        sheet.col(8).width = 7000
        sheet.write(row, 9,u'Ажил захиалсан огноо', style2)
        sheet.col(9).width = 6000
        sheet.write(row, 10,u'Дэлгэрэнгүй тайлбар', style2)
        sheet.col(10).width = 6000
        sheet.write(row, 11,u'Дууссан огноо', style2)
        sheet.col(11).width = 4000
        sheet.write(row, 12,u'Зарцуулсан хугацаа', style2)
        sheet.col(12).width = 4000
        sheet.write(row, 13,u'Төлбөр', style2)
        sheet.col(13).width = 3000
        sheet.write(row, 14,u'Үнэлгээ', style2)
        sheet.col(14).width = 3000
        sheet.row(row).height = 500
        count = 1
        row+=1
        merge_row = row
        total = 0.0
        total_day = 0.0
        task_dict = {}
        tasks = []
        works = []
        sub_total = 0
        dict_line = {}
        if line:
            for object in line:
                if (object.task_id.task_date_start >= data['start_date'] and object.task_id.task_date_start <= data['end_date']) or (object.task_id.date_deadline >= data['start_date'] and object.task_id.date_deadline <= data['end_date']):
                    group = object.task_id.project_id.name

                    if group not in dict_line:
                        dict_line[group]={
                        'project':u'Тодорхойгүй',
                        'tasks':{}
                        }
                    dict_line[group]['project'] = group
                    group1=object.task_id.name

                    if group1 not in dict_line[group]['tasks']:
                        dict_line[group]['tasks'][group1]={
                        'category':u'Тодорхойгүй',
                        'task':u'Тодорхойгүй',
                        'works':{},                        
                        }

                    dict_line[group]['tasks'][group1]['task']=object.task_id.name
                    group2 = object.work_id.name
                    if group2 not in dict_line[group]['tasks'][group1]['works']:
                        dict_line[group]['tasks'][group1]['works'][group2] ={
                        'department':u'Тодорхойгүй',
                        'user':u'Тодорхойгүй',
                        'partner':u'Тодорхойгүй',
                        'partner_user':u'Тодорхойгүй',
                        'date_start':u'Тодорхойгүй',
                        'description':u'Тодорхойгүй',
                        'date':u'Тодорхойгүй',
                        'used_day':u'Тодорхойгүй',
                        'payment':u'Тодорхойгүй',
                        'evaluate':u'Тодорхойгүй',
                        }
                    
                    dict_line[group]['tasks'][group1]['works'][group2]['category']=object.work_id.category_id.name
                    dict_line[group]['tasks'][group1]['works'][group2]['work']=object.work_id.name
                    dict_line[group]['tasks'][group1]['works'][group2]['department']=object.task_id.department_id.name
                    dict_line[group]['tasks'][group1]['works'][group2]['user']=object.task_id.user_id.name
                    dict_line[group]['tasks'][group1]['works'][group2]['partner']=object.task_id.customer_department.name
                    dict_line[group]['tasks'][group1]['works'][group2]['partner_user']=object.task_id.customer_id.name
                    dict_line[group]['tasks'][group1]['works'][group2]['date_start']=object.task_id.task_date_start
                    dict_line[group]['tasks'][group1]['works'][group2]['description']=object.description
                    dict_line[group]['tasks'][group1]['works'][group2]['date']=object.task_id.date_deadline
                    if object.task_id.task_date_start and object.task_id.done_date:
                        start_date = datetime.strptime(object.task_id.task_date_start,'%Y-%m-%d') 
                        done_date = datetime.strptime(object.task_id.done_date,'%Y-%m-%d') 
                        dict_line[group]['tasks'][group1]['works'][group2]['used_day']=str(start_date -done_date)
                    else:
                        dict_line[group]['tasks'][group1]['works'][group2]['used_day']= 0
                    dict_line[group]['tasks'][group1]['works'][group2]['payment']=object.agreed_price
                    dict_line[group]['tasks'][group1]['works'][group2]['evaluate']=object.task_id.total_percent

                
            for line in sorted(dict_line.values(),key=itemgetter('project')):
                    rowq=row
                    pro_total=0
                    for task in sorted(line['tasks'].values(),key=itemgetter('task')):
                        rows=row
                        sub_total=0
                        for work in sorted(task['works'].values(),key=itemgetter('work')):
                            sheet.write(row,0,str(count), style2_1)
                            sheet.write(row,2,work['category'], style2_1)
                            sheet.write(row,4,work['work'], style2_1)
                            sheet.write(row,5,work['department'], style2_1)
                            sheet.write(row,6,work['user'], style2_1)
                            sheet.write(row,7,work['partner'], style2_1)
                            sheet.write(row,8,work['partner_user'], style2_1)
                            sheet.write(row,9,work['date_start'], style2_1)                
                            sheet.write(row,10,work['description'], style2_1)                
                            sheet.write(row,11,work['date'], style2_1)
                            sheet.write(row,12,work['used_day'], style2_1)
                            sheet.write(row,13,work['payment'], style2_1)
                            total += work['payment']
                            pro_total += work['payment']
                            sub_total += work['payment']
                            sheet.write(row,14,work['evaluate'], style2_1)
                            sheet.row(row).height = 1000
                            count += 1                    
                            row += 1                                                    
                        if rows==row-1:
                            sheet.write(rows,3,task['task'], style2_1)
                        else:
                            sheet.write_merge(rows,row-1,3,3,task['task'],style2_1)
                        
                        sheet.write_merge(row,row,2, 12,u'Нийт', style3)
                        sheet.write(row,13,sub_total, style2_1)
                        sheet.write(row,14,'', style2_1)
                        row+=1
                    if rowq==row-1:
                        sheet.write(rowq,1,line['project'], style2_1)
                    else:
                        sheet.write_merge(rowq,row-1,1,1,line['project'],style2_1)
                    sheet.write_merge(row,row,0, 12,u'Нийт', style3)
                    sheet.write(row,14,0, style2_1)
                    sheet.write(row,13,pro_total, style2_1)
                    row+=1
                   
            
            sheet.write_merge(row,row,0, 12,u'Нийт', style3)
            sheet.write(row,14,0, style2_1)
            sheet.write(row,13,total, style2_1)
        # if line:
        #     for object in line:
        #         if (object.task_id.task_date_start >= data['start_date'] and object.task_id.task_date_start <= data['end_date']) or (object.task_id.date_deadline >= data['start_date'] and object.task_id.date_deadline <= data['end_date']):
        #             if object.task_id.id not in tasks:
        #                 total_time = 0.0
        #                 tasks.append(object.task_id.id)
        #                 for line in object.task_id.timesheet_ids:
        #                     total_time += line.unit_amount
        #                 task_dict[object.task_id.id] = {'count':len(object.task_id.tarif_line),'day':total_time}
        #     if task_dict:
        #         for dict in task_dict:
        #             total_day += task_dict[dict]['day']
        #             if object.work_id.name not in works:
        #                 if len(works)>0:
        #                     sheet.write_merge(row,row,0, 12,u'Нийт', style3)
        #                     sheet.write(row,13,sub_total, style2_1)
        #                     sub_total =0
        #                     row+=1
        #                     works.append(object.work_id.name)
        #                 else:
        #                     works.append(object.work_id.name)
        #             sheet.write_merge(merge_row,merge_row+task_dict[dict]['count']-1, 12, 12,task_dict[dict]['day'], style2_1)
        #             merge_row = merge_row+task_dict[dict]['count']
                
        
        
        row +=3
        sheet.write_merge(row,row, 1, 4,u'Тайлан хэвлэсэн: ................... /%s/'%(employee_id.name), ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        return {'data':book}