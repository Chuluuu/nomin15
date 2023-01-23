# -*- coding: utf-8 -*-
import dateutil
import time
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError
from odoo import models, fields, api, _
from io import StringIO
from io import BytesIO
import base64
import xlsxwriter

class project_status_report(models.TransientModel):
    _name = 'project.status.report'
    _description = 'Project Status Report'

    project_id = fields.Many2one('project.project', required=True,string=u'Төсөл')
    
    
    def export_chart(self,report_code,context=None):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()
        worksheet2 = workbook.add_worksheet()
        
        employee                        = self.env['hr.employee']
        employee_id                     = employee.sudo().search([('user_id','=',self._uid)])
        
        today = datetime.today()
        weekday = today.weekday()
        start_delta = timedelta(days=weekday)
        start_of_week = today - start_delta
        week_dates = []
        week2_dates = []
        for day in range(7):
            week_dates.append(start_of_week + timedelta(days=day))

        for day in range(7):
            week2_dates.append((week_dates[-1] + timedelta(days=1))+ timedelta(days=day))
        
        format = workbook.add_format({'bold': True, 'font_color': 'black', 'border': True})
        format.set_pattern(0)  # This is optional when using a solid fill.
        format.set_bg_color('#00e5ff')
        datas={}
        datas['model'] = 'project.project'
        datas['form'] = self.read(['project_id'])[0] 
        data = datas['form']
        state = ''
        issue_search_value = []
        task_search_value = []
        budget_search_value = []
        project_task_search_value = []
        project_task_search_value2 = []
        worksheet.merge_range('F2:H2', u'ТӨСЛИЙН ЯВЦЫН ТАЙЛАН')
#          
        row = 4
        worksheet.merge_range('A%s:C%s'%(row,row),u'Төслийн нэр', format)
        worksheet.merge_range('D%s:F%s'%(row,row),u'Төслийн менежер', format)
        worksheet.merge_range('G%s:I%s'%(row,row),u'Хэлтэс', format)
        worksheet.merge_range('J%s:L%s'%(row,row),u'Огноо', format)
        worksheet.merge_range('M%s:O%s'%(row,row),u'Төслийн төлөв', format)
        row += 1
        if data['project_id']:
            project = self.env['project.project'].search([('id', '=',data['project_id'][0])])
            issue_search_value.append(('project_id', '=',project.id))
            task_search_value.append(('project_id', '=',project.id))
            all_tasks =  self.env['project.task'].sudo().search(task_search_value, order='id')
            project_task_search_value.append(('project_id', '=',project.id))
            project_task_search_value2.append(('project_id', '=',project.id))
#             project_task_search_value.append(('task_state','not in',('t_done','t_cancel')))
#             project_task_search_value2.append(('task_state','not in',('t_done','t_cancel')))
            budget_search_value.append(('project_id', '=',project.id))
            budgets  = self.env['control.budget'].sudo().search(budget_search_value)
            issue_category = []
            for line in project.type_ids:
                issue_category.append(line.name)
            issue_for_data = []
            for line in project.type_ids:
                issue_for_data.append(line.id)
            issue_data = []
            budget_data = []
            budget_append_data = []
            task_for_data = ['t_confirm','t_back','t_cancel']
            task_data = []
            project_status = 0
            project_stages_category = []
            project_stages = []
            project_category = [u'Хугацаандаа (Нээлттэй)',u'Хугацаа хэтэрсэн (Нээлттэй)',u'Дууссан']
            project_data = []
            project_data2 = []
            for i in issue_for_data:
                issue_search_value.append(('stage_id','=',i ))
                issue = self.env['project.issue'].sudo().search(issue_search_value, order='id')
                issue_data.append(len(issue))
                issue_search_value.remove(('stage_id','=',i ))
            total = 0.0
            if project:
                for line in project.main_line_ids:
                    if line.confirm == True:
                        budget_append_data.append(line.material_line_limit)
                        budget_append_data.append(line.material_line_limit - line.material_line_real)
                        budget_append_data.append(line.material_line_real)
                        budget_data.append(budget_append_data)
                        budget_append_data = []
                        
                        budget_append_data.append(line.labor_line_limit)
                        budget_append_data.append(line.labor_line_limit - line.labor_line_real)
                        budget_append_data.append(line.labor_line_real)
                        budget_data.append(budget_append_data)
                        budget_append_data = []
                        
                        budget_append_data.append(line.equipment_line_limit)
                        budget_append_data.append(line.equipment_line_limit - line.equipment_line_real)
                        budget_append_data.append(line.equipment_line_real)
                        budget_data.append(budget_append_data)
                        budget_append_data = []
                        
                        budget_append_data.append(line.postage_line_limit)
                        budget_append_data.append(line.postage_line_limit - line.postage_line_real)
                        budget_append_data.append(line.postage_line_real)
                        budget_data.append(budget_append_data)
                        budget_append_data = []
                        
                        budget_append_data.append(line.other_line_limit)
                        budget_append_data.append(line.other_line_limit - line.other_line_real)
                        budget_append_data.append(line.other_line_real)
                        budget_data.append(budget_append_data)
                        budget_append_data = []
                        
                        budget_append_data.append(line.carriage_limit)
                        budget_append_data.append(line.carriage_limit - line.carriage_real)
                        budget_append_data.append(line.carriage_real)
                        budget_data.append(budget_append_data)
                        budget_append_data = []
                        
            sequense_stages = self.env['project.stage'].search([('id', 'in', project.project_stage.ids)], order='sequense')
            for stage in sequense_stages:
                project_stages.append(stage.id)
            for stages in project_stages:
                stages_obj = self.env['project.stage'].sudo().search([('id', '=', stages)])
                project_stages_category.append(stages_obj.name)
                end_stage_tasks = self.env['project.task'].sudo().search([ '&' , '&' , ('project_id', '=', project.id) , ('project_stage', '=', stages_obj.id) , ('task_state', '=', 't_done') ], order='id')
                stage_tasks = self.env['project.task'].sudo().search([ '&' ,('project_id', '=', project.id) , ('project_stage', '=', stages_obj.id)], order='id')
                if len(end_stage_tasks) != 0:
                    data = len(end_stage_tasks)*(100/len(stage_tasks))
                    project_data.append(str(data)+' %')
                else:
                    project_data.append('0 %')
            worksheet.write('A39',u'Үе шат',format)
            worksheet.write('A40',u'Хувь',format)
            column = 1
            for categ in project_stages_category:
                worksheet.write(38,column,categ,format)
                column += 1
            column = 1
            for data in project_data:
                worksheet.write(39,column,data)
                column += 1
            worksheet.merge_range('A%s:C%s'%(row,row), u'%s'%project.name)
            worksheet.merge_range('D%s:F%s'%(row,row), u'%s'%project.user_id.name)
            worksheet.merge_range('G%s:I%s'%(row,row), u'%s'%project.department_id.name)
            worksheet.merge_range('J%s:L%s'%(row,row), u'%s'%fields.Date.context_today(self))
            if project.state == 'draft':
                state = u'Ноорог'
            if project.state == 'request':
                state = u'Хүсэлт'
            if project.state == 'comfirm':
                state = u'Батлагдсан'
            if project.state == 'project_started':
                state = u'Эхэлсэн'
            if project.state == 'finished':
                state = u'Дууссан'
            if project.state == 'ready':
                state = u'Үнэлэх'
            if project.state == 'evaluate':
                state = u'Үнэлэгдсэн'
            if project.state == 'cancelled':
                state = u'Цуцлагдсан'
            worksheet.merge_range('M%s:O%s'%(row,row), u'%s'%state)
#             Project CHART
            project_task_search_value.append(('date_deadline','>=',fields.Date.context_today(self)))
            on_tasks = self.env['project.task'].sudo().search(project_task_search_value, order='id')
            project_data2.append(len(on_tasks))
            project_task_search_value2.append(('date_deadline','<',fields.Date.context_today(self)))
            project_task_search_value2.append(('task_state','!=','t_done'))
            deadline_tasks = self.env['project.task'].sudo().search(project_task_search_value2, order='id')
            done_tasks = self.env['project.task'].sudo().search([('project_id','=',project.id),('task_state','=','t_done')], order='id')
            project_data2.append(len(deadline_tasks))
            project_data2.append(len(done_tasks))
            worksheet2.write_column('S10', project_category)
            worksheet2.write_column('T10', project_data2)
            project_task_chart = workbook.add_chart({'type': 'pie'})
            project_task_chart.add_series({
                                    'categories': '=Sheet2!$S$10:$S$12',
                                    'values': '=Sheet2!$T$10:$T$12',
                                    'data_labels': {'value': 1},
                                    'points': [
                                                {'fill': {
                                                          'color': 'yellow'
                                                          }},
                                                {'fill': {
                                                          'color': 'red',
                                                          }},
                                                {'fill': {
                                                          'color': 'green',
                                                          }},
                                            ],
                                    })
            project_task_chart.set_chartarea({'fill': {'color': 'white', 'transparency': 75}})
            
            status_tasks = self.env['project.task'].sudo().search([('project_id','=',project.id)])
            tasks_total_day = 0
            complete_percent_day = 0
            for task in status_tasks:
                if task.date_deadline and task.task_date_start:
                    if task.task_state != 't_cancel':
                        day_count = datetime.strptime(task.date_deadline, '%Y-%m-%d') - datetime.strptime(task.task_date_start, '%Y-%m-%d')
                        tasks_total_day += day_count.days + 1
                        if task.task_state == 't_done':
                            complete_percent_day += day_count.days + 1
                        else:
                            complete_percent_day += ((day_count.days+1) * task.flow)/100
            if complete_percent_day > 0:
                project_status  = (complete_percent_day * 100) / tasks_total_day
            else:
                project_status = 0
            
            project_task_chart.set_title({ 'name': u'Төслийн явц %s %s'%(project_status,'%')})
            worksheet.insert_chart('A8', project_task_chart)
#             Task CHART
            task_search_value.append(('task_type', 'in',('work_graph','work_task')))
            for i in task_for_data:
                task_search_value.append(('task_state','=',i))
                task = self.env['project.task'].sudo().search(task_search_value, order='id')
                task_data.append(len(task))
                task_search_value.remove(('task_state','=',i))
            worksheet2.write_column('W10', task_data)
            task_chart = workbook.add_chart({'type': 'bar'})
            task_chart.add_series({
                                    'name':u'Батлагдаагүй',
                                    'values': '=Sheet2!$W$10'
                                    })
            task_chart.add_series({
                                    'name':u'Хойшлуулсан',
                                    'values': '=Sheet2!$W$11'
                                    })
            task_chart.add_series({
                                    'name':u'Цуцалсан',
                                    'values': '=Sheet2!$W$12'
                                    })
            task_chart.set_title({ 'name': u'Хүлээгдэж буй'})
            task_chart.set_chartarea({'fill': {'color': 'white', 'transparency': 100}})
            worksheet.insert_chart('I8', task_chart)
#             ISSUE CHART
            worksheet2.write_column('U10', issue_category)
            worksheet2.write_column('V10', issue_data)
            issue_chart = workbook.add_chart({'type': 'column'})
            issue_chart.set_title({ 'name': u'Асуудлын явц'})
            issue_chart.set_x_axis({'name': u'Шат'})
            issue_chart.set_y_axis({'name': u'Тоо'})
            issue_chart.add_series({
                                    'name':u'Асуудал',
                                    'categories': '=Sheet2!$U$10:$U$%s'%(str(10 + len(issue_category))),
                                    'values': '=Sheet2!$V$10:$V$%s'%(str(10 + len(issue_category))),
                                    'width': 100
                                    })
            issue_chart.set_chartarea({'fill': {'color': 'white', 'transparency': 100}})
            worksheet.insert_chart('I23', issue_chart)
#              BUDGET CHART
            if budgets:
                worksheet2.write('X10',u'Материал')
                worksheet2.write('Y10',u'Ажиллах хүч')
                worksheet2.write('Z10',u'Машин механизм')
                worksheet2.write('AA10',u'Шууд')
                worksheet2.write('AB10',u'Бусад')
                worksheet2.write('AC10',u'Тээвэр')
                
                b_row = 10
                b_col = 23
                for data in budget_data:
                    worksheet2.write_column(b_row,b_col, data)
                    b_col += 1
                budget_chart = workbook.add_chart({'type': 'column', 'subtype': 'stacked'})
                budget_chart.set_title({ 'name': u'Төсөв'})
                budget_chart.set_x_axis({'name': u'Зардлын төрлүүд'})
                budget_chart.add_series({
                                        'name' : u'Төсөвлөсөн дүн',
                                        'data_labels': {'value': 1},
                                        'categories': '=Sheet2!$X$10:$AC$10',
                                        'values': '=Sheet2!$X$11:$AC$11'
                                        })
                budget_chart.add_series({
                                        'name' : u'Гүйцэтгэл',
                                        'data_labels': {'value': 1},
                                        'categories': '=Sheet2!$X$10:$AC$10',
                                        'values': '=Sheet2!$X$12:$AC$12'
                                        })
                budget_chart.add_series({
                                        'name' : u'Үлдэгдэл',
                                        'data_labels': {'value': 1},
                                        'categories': '=Sheet2!$X$10:$AC$10',
                                        'values': '=Sheet2!$X$13:$AC$13'
                                        })
                budget_chart.set_chartarea({'fill': {'color': 'white', 'transparency': 75}})
                worksheet.insert_chart('A23', budget_chart)
#         WEEK TASKS
#         current_week_search_value.append(('project_id','=',project.id))
#         current_week_search_value = ['|',('date_deadline','>=',str(week_dates[0])),('date_deadline','<=',str(week_dates[-1])),('task_date_start','>=',str(week_dates[0])),('task_date_start','<=',str(week_dates[-1]))]
        search_query = "SELECT id FROM project_task WHERE id in (SELECT id from project_task where task_date_start BETWEEN '%s' AND '%s' and project_id ='%s') or id IN (SELECT id from project_task where date_deadline BETWEEN '%s' AND '%s' AND project_id ='%s')"%(str(week_dates[0]),str(week_dates[-1]),project.id,str(week_dates[0]),str(week_dates[-1]),project.id)
        self.env.cr.execute(search_query)
        query_ids = self.env.cr.fetchall()
        
        search_query2 = "SELECT id FROM project_task WHERE id in (SELECT id from project_task where task_date_start BETWEEN '%s' AND '%s' and project_id ='%s') or id IN (SELECT id from project_task where date_deadline BETWEEN '%s' AND '%s' AND project_id ='%s')"%(str(week2_dates[0]),str(week2_dates[-1]),project.id,str(week2_dates[0]),str(week2_dates[-1]),project.id)
        self.env.cr.execute(search_query2)
        query_ids2 = self.env.cr.fetchall()
        
        current_week_tasks =  self.env['project.task'].sudo().search([('id', 'in',query_ids)],order='task_date_start')
        next_week_tasks =  self.env['project.task'].sudo().search([('id', 'in',query_ids2)], order='task_date_start')
        row = 42
        worksheet.merge_range('A%s:O%s'%(row,row),u'Тайлант хугацаанд хийгдсэн ажлууд: %s - %s'%(str(week_dates[0]),str(week_dates[-1])), format)
        row += 1
        worksheet.merge_range('A%s:C%s'%(row,row),u'Таск',format)
        worksheet.merge_range('D%s:F%s'%(row,row),u'Эхлэх хугацаа',format)
        worksheet.merge_range('G%s:I%s'%(row,row),u'Дуусах хугацаа',format)
        worksheet.merge_range('J%s:L%s'%(row,row),u'Хариуцагч',format)
        worksheet.merge_range('M%s:O%s'%(row,row),u'Явцын хувь %',format)
        row += 1
        for current_task in current_week_tasks:
            worksheet.merge_range('A%s:C%s'%(row,row),current_task.name)
            if current_task.task_date_start:
                worksheet.merge_range('D%s:F%s'%(row,row),current_task.task_date_start)
            else:
                worksheet.merge_range('D%s:F%s'%(row,row),'')
            if current_task.date_deadline:
                worksheet.merge_range('G%s:I%s'%(row,row),current_task.date_deadline)
            else:
                worksheet.merge_range('G%s:I%s'%(row,row),'')
            if current_task.user_id:
                worksheet.merge_range('J%s:L%s'%(row,row),current_task.user_id.name)
            else:
                worksheet.merge_range('J%s:L%s'%(row,row),'')
                
            worksheet.merge_range('M%s:O%s'%(row,row),current_task.flow)
            row += 1
        
        row += 1
        worksheet.merge_range('A%s:O%s'%(row,row),u'Дараагийн тайлант хугацаанд хийгдэх ажлууд: %s - %s'%(str(week2_dates[0]),str(week2_dates[-1])), format)
        row += 1
        worksheet.merge_range('A%s:C%s'%(row,row),u'Таск',format)
        worksheet.merge_range('D%s:F%s'%(row,row),u'Эхлэх хугацаа',format)
        worksheet.merge_range('G%s:I%s'%(row,row),u'Дуусах хугацаа',format)
        worksheet.merge_range('J%s:L%s'%(row,row),u'Хариуцагч',format)
        worksheet.merge_range('M%s:O%s'%(row,row),u'Явцын хувь %',format)
        row += 1
        for current_task in next_week_tasks:
            if current_task.date_deadline >= str(week2_dates[0]) and current_task.date_deadline <= str(week2_dates[-1]):
                worksheet.merge_range('A%s:C%s'%(row,row),current_task.name)
                worksheet.merge_range('D%s:F%s'%(row,row),current_task.task_date_start or '')
                worksheet.merge_range('G%s:I%s'%(row,row),current_task.date_deadline or '')
                worksheet.merge_range('J%s:L%s'%(row,row),current_task.user_id.name or '')
                worksheet.merge_range('M%s:O%s'%(row,row),100)
            else:
                task_day_count = 0
                merge_count    = 0
                worksheet.merge_range('A%s:C%s'%(row,row),current_task.name)
                if current_task.task_date_start:
                    worksheet.merge_range('D%s:F%s'%(row,row),current_task.task_date_start)
                else:
                    worksheet.merge_range('D%s:F%s'%(row,row),'')
                if current_task.date_deadline:
                    worksheet.merge_range('G%s:I%s'%(row,row),current_task.date_deadline)
                else:
                    worksheet.merge_range('G%s:I%s'%(row,row),'')
                if current_task.user_id:
                    worksheet.merge_range('J%s:L%s'%(row,row),current_task.user_id.name)
                else:
                    worksheet.merge_range('J%s:L%s'%(row,row),'')
                if current_task.date_deadline and current_task.task_date_start:
                    date = datetime.strptime(current_task.date_deadline, '%Y-%m-%d') - datetime.strptime(current_task.task_date_start, '%Y-%m-%d')
                    task_day_count  = date.days +1
                    if current_task.date_deadline < str(week2_dates[-1]):
                        end_date = current_task.date_deadline
                    else:
                        end_date = week2_dates[-1]
                    if current_task.task_date_start < str(week2_dates[0]):
                        start_date = week2_dates[0]
                    else:
                        start_date = current_task.task_date_start
                    merge_count = (datetime.strptime(str(end_date), '%Y-%m-%d') - datetime.strptime(str(start_date), '%Y-%m-%d')).days
                    merge_count += 1
                    if merge_count > 0:
                        worksheet.merge_range('M%s:O%s'%(row,row),(merge_count*100)/task_day_count)
                    else:
                        worksheet.merge_range('M%s:O%s'%(row,row),100)
                else:
                    worksheet.merge_range('M%s:O%s'%(row,row),'')
            row += 1
        
        row +=3
        worksheet.merge_range('A%s:D%s'%(row,row),u'Тайлан хэвлэсэн: ................... /%s/'%(employee_id.name),)
        
        workbook.close()
        
        out = base64.encodestring(output.getvalue())
        file_name = u'Төслийн явцын тайлан'
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
        