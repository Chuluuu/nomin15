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
import dateutil 
import datetime 
import time 

class OrderPlanReport(models.TransientModel):
    '''Захиалгын ерөнхий тайлан
    '''
    _name = 'order.plan.report'
    _inherit = 'abstract.report.model'
    _description = 'Helpdesk Coupon Report'

    
    
    
    start_date = fields.Date(string=u'Эхлэх огноо', required=True)
    end_date = fields.Date(string=u'Дуусах огноо', required=True)
    department_id = fields.Many2one('hr.department', string = 'Захиалагч салбар', ondelete="restrict", track_visibility='always')
    project_manager_id = fields.Many2one('hr.employee', string='Төслийн менежер' , domain=[('parent_department','=',254)],track_visibility='always')
    project_state_name = fields.Many2one('project.state.name' , string='Ажлын явц')

    @api.multi
    def get_export_data(self,report_code,context=None):
        '''Тайлан экселруу импорт хийх
        '''
        if context is None:
            context = {}
        
        datas={}
        datas['model'] = 'order.page'
        datas['form'] = self.read(['department_id','start_date','end_date','project_manager_id','project_state_name'])[0] 
        data = datas['form']
        employee = self.env['hr.employee']
        employee_id = employee.sudo().search([('user_id','=',self._uid)])
        
        ezxf = xlwt.easyxf
        style1 = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
        style2 = ezxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin; pattern: pattern solid, fore_color light_turquoise')
        style3 = ezxf('font: bold on; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin; pattern: pattern solid, fore_color light_turquoise')
        style2_1 = ezxf('font: bold off; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
        style2_12 = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
        body_style2 = ezxf('font: bold off; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
        body_style_right = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
            
        search_value = [('start_date','>=',data['start_date']),('start_date','<=',data['end_date'])]

        if self.department_id and self.project_manager_id and self.project_state_name:
            search_value = [('start_date','>=',data['start_date']),('start_date','<=',data['end_date']),('project_manager_id','=',data['project_manager_id'][0]),('department_id','=',data['department_id'][0]),('project_state_name','=',data['project_state_name'][0])]
        elif self.department_id:
             search_value = [('start_date','>=',data['start_date']),('start_date','<=',data['end_date']),('department_id','=',data['department_id'][0])]
        elif self.project_manager_id:
            search_value = [('start_date','>=',data['start_date']),('start_date','<=',data['end_date']),('project_manager_id','=',data['project_manager_id'][0])]
        elif self.project_state_name:
            search_value = [('start_date','>=',data['start_date']),('start_date','<=',data['end_date']),('project_state_name','=',data['project_state_name'][0])]

        


        book = xlwt.Workbook(encoding='utf8')
        sheet = book.add_sheet('Work Report')
        sheet.portrait=True
        ezxf = xlwt.easyxf
        
        sheet.write(2, 6, u'Захиалгын ерөнхий тайлан', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(6, 1, u'Тайлант хугацаа : %s - %s'%(data['start_date'],data['end_date']), ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(7, 1, u'Хэвлэсэн огноо : %s'%(str(datetime.datetime.strptime(fields.Datetime.now(), '%Y-%m-%d %H:%M:%S')).split(' ')[0]), ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        
                   
                             
        orders = self.env['order.page'].search(search_value)    
        search_value1 = [('plan_id','in',orders.ids)] 
        plans = self.env['server.info'].search(search_value1)

        row = 9 
        sheet.col(0).width = 800
        sheet.write_merge(row,row+1,0,0 , u'№', style2)
        sheet.col(1).width = 4000
        sheet.write_merge(row,row+1,1,1 , u'Захиалгын нэр', style2)
        sheet.col(2).width = 4000
        sheet.write_merge(row,row+1,2,2 , u'Үндэслэл', style2)
        sheet.col(2).width = 4000        
        sheet.write_merge(row,row+1,3,3 , u'Захиалагч салбар ', style2)
        sheet.col(3).width = 5500
        sheet.write_merge(row,row+1,4,4 , u'Захиалга үүсгэгч ', style2)
        sheet.col(4).width = 5500
        sheet.write_merge(row,row+1,5,5 , u'Захиалга батлагдсан огноо ', style2)
        sheet.col(5).width = 5500
        sheet.write_merge(row,row+1,6,6 , u'Хуваарилагдсан огноо', style2)
        sheet.col(6).width = 5500        
        sheet.write_merge(row,row+1,7,7 , u'Төслийн менежер ', style2)
        sheet.col(7).width = 5500
        sheet.write_merge(row,row+1,8,8,u'Огноо', style2)
        sheet.col(8).width = 4000
        sheet.write_merge(row,row+1,9,9,u'Төлөвлөгөө', style2)
        sheet.write_merge(row,row+1,10,10,u'Ажлын явц', style2)

        sheet.write_merge(row,row,11,14, u'Гүйцэтгэл ', style2)

        sheet.write(row+1, 11, u'1-р долоо хоног', style2)
        sheet.col(10).width = 4000
        sheet.write(row +1, 12, u'2-р долоо хоног', style2)
        sheet.col(11).width = 4000

        sheet.write(row+1, 13, u'3-р долоо хоног', style2)
        sheet.col(12).width = 4000
        sheet.write(row +1, 14, u'4-р долоо хоног', style2)
        sheet.col(13).width = 4000

        row +=2
        line_number = 1
        

        total_child_count = 0
        for order in orders:                   

            sheet.write(row, 0,line_number, style2_1)
            sheet.write(row, 1,order.order_name, style2_1)              
            sheet.write(row, 2,order.purpose , style2_1)    
            sheet.write(row, 3,order.department_id.name or '', style2_1)
            sheet.write(row, 4,order.employee_id.name , style2_1)    
            sheet.write(row, 5,order.confirmed_date or '', style2_1)
            sheet.write(row, 6,order.assigned_date , style2_1)    
            sheet.write(row, 7,order.project_manager_id.name or '', style2_1)
            sheet.write(row, 10,order.project_state_name.name or '', style2_1)

            plans = order.plan_info

            pre_row = row

            for plan in plans:
                if pre_row != row:
                    sheet.write(row, 0,'', style2_1)
                    sheet.write(row, 1,'', style2_1)              
                    sheet.write(row, 2,'' , style2_1)    
                    sheet.write(row, 3,'', style2_1)
                    sheet.write(row, 4,'', style2_1)    
                    sheet.write(row, 5,'', style2_1)
                    sheet.write(row, 6,'', style2_1)    
                    sheet.write(row, 7,'', style2_1)
                sheet.write(row, 8,plan.month_id.name , style2_1)    
                sheet.write(row, 9,plan.plan_name or '', style2_1)
                sheet.write(row, 11,plan.first_week , style2_1)    
                sheet.write(row, 12,plan.second_week or '', style2_1)
                sheet.write(row, 13,plan.third_week , style2_1)    
                sheet.write(row, 14,plan.fourth_week or '', style2_1)            
                row += 1

    

            
            line_number +=1
            if len(plans) <= 0:
                row +=1  
           
        row += 3

        
        sheet.write_merge(row, row, 0, 12, u'Боловсруулсан: Менежер ................................../%s/'%(employee_id.name), ezxf('font: bold on;align:wrap off,vert centre,horiz center;'))
        return {'data':book}