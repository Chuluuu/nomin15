# -*- coding: utf-8 -*-
##############################################################################
#
#    Asterisk Technologies LLC, Enterprise Management Solution    
#    Copyright (C) 2007-2013 Asterisk Technologies LLC Co.,ltd (<http://www.erp.mn>). All Rights Reserved
#
#    Email : unuruu25@gmail.com
#    Phone : 976 + 88005462
#
##############################################################################
from openerp.tools.translate import _
from openerp import api, fields, models, _
import time
import openerp.netsvc, decimal, base64, os, time, xlrd
from tempfile import NamedTemporaryFile
from openerp.exceptions import UserError
from datetime import datetime
import xlsxwriter
from io import BytesIO
import logging
_logger = logging.getLogger(__name__)
class ProjectBudgetExportImport(models.TransientModel):
    _name ="project.budget.export.import"
    _description = 'Project budget export.import'
    """Төслийн хөрөнгө оруулалт export import хийх"""
    data=fields.Binary('Excel File')
    type= fields.Selection([('export','Export'),('import','Import')],string="type")    

    @api.multi
    def action_export(self):
        active_id = self.env.context and self.env.context.get('active_id', False) or False
        project_obj = self.env['project.project']
        project = project_obj.browse(active_id)
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
        cell_float_format_text = workbook.add_format({
        'border': 0,
        'bold': 0,
        'align': 'right',
        'valign': 'vcenter',
        'text_wrap': 'on',
        'font_size':10,
        'font_name': 'Arial',
        # 'bg_color':'#40E0D0',
        # 'num_format': '#,##0.00'
        })
        sheet = workbook.add_worksheet()
        row = 0
        sheet.portrait=True
        sheet.write(row,  0,u'Төслийн зориулалт', header_color)
        sheet.set_column(0,0,20)
        sheet.write(row,  1,u'Салбар', header_color)    
        sheet.set_column(0,1,20)
        sheet.write(row,  2,u'Материалын зардал', header_color)        
        sheet.set_column(0,2,20)
        sheet.write(row,  3,u'Ажиллах хүчний зардал', header_color)
        sheet.set_column(0,3,20)
        sheet.write(row,  4,u'Тоног төхөөрөмжийн зардал', header_color)                 
        sheet.set_column(0,4,20)
        sheet.write(row,  5,u'Тээврийн зардал', header_color)            
        sheet.set_column(0,5,20)
        sheet.write(row,  6,u'Шууд зардал', header_color)
        sheet.set_column(0,6,20)
        sheet.write(row,  7,u'Бусад зардал', header_color)
        sheet.set_column(0,7,20)
        sheet.write(row,  8,u'Тайлбар', header_color)
        sheet.set_column(0,7,20)
        row+=1
        if project and project.budget_line_ids:
            for budget in project.budget_line_ids:
                for line in budget.line_ids:
                    sheet.write(row, 0 , project.specification_id.name, cell_float_format_right)
                    sheet.write(row, 1 , line.department_id.nomin_code, cell_float_format_text)
                    sheet.write(row, 2 , line.material_cost, cell_float_format_right)
                    sheet.write(row, 3 , line.labor_cost, cell_float_format_right)
                    sheet.write(row, 4 , line.equipment_cost, cell_float_format_right)
                    sheet.write(row, 5 , line.carriage_cost, cell_float_format_right)
                    sheet.write(row, 6 , line.postage_cost, cell_float_format_right)
                    sheet.write(row, 7 , line.other_cost, cell_float_format_right)
                    sheet.write(row, 8 , line.description, cell_float_format_text)
                    row+=1
                # sheet.write(row, 0 , '', sum_format_center)
                # sheet.write(row, 1 , '', sum_format_center)
                # sheet.write(row, 2 , budget.total_material_cost, sum_format_center)
                # sheet.write(row, 3 , budget.total_labor_cost, sum_format_center)
                # sheet.write(row, 4 , budget.equipment_cost, sum_format_center)
                # sheet.write(row, 5 , budget.carriage_cost, sum_format_center)
                # sheet.write(row, 6 , budget.postage_cost, sum_format_center)
                # sheet.write(row, 7 , budget.total_other_cost, sum_format_center)
                # sheet.write(row, 8 , '', sum_format_center)
                
        elif project.project_categ and project.project_categ.specification_ids:
            for line in project.project_categ.specification_ids:                
                sheet.write(row, 0 , line.name, cell_float_format_right)
                sheet.write(row, 1 , '', cell_float_format_text)
                sheet.write(row, 2 , 0, cell_float_format_right)
                sheet.write(row, 3 , 0, cell_float_format_right)
                sheet.write(row, 4 , 0, cell_float_format_right)
                sheet.write(row, 5 , 0, cell_float_format_right)
                sheet.write(row, 6 , 0, cell_float_format_right)
                sheet.write(row, 7 , 0, cell_float_format_right)
                sheet.write(row, 8 , '', cell_float_format_text)
                row+=1



        workbook.close()
        file_name="Төслийн хөрөнгө оруулалт"
        out = base64.encodestring(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data':out,'name':file_name + '.xlsx'})

        return {
		'name': 'Export Report',
		'view_type':'form',
		'view_mode':'form',
		'res_model':'report.excel.output',
		'res_id':excel_id.id,
		'view_id':False,
		#'context':self._context,
		'type': 'ir.actions.act_window',
		'target':'new',
		'nodestroy': True,
		}
        
        
    @api.multi
    def action_import(self):
        project_obj = self.env['project.project']
        active_id = self.env.context and self.env.context.get('active_id', False) or False
        project = project_obj.browse(active_id)
        fileobj = NamedTemporaryFile('w+')
        fileobj.write(base64.decodestring(self.data))
        # fileobj.write(base64.decodestring(obj.data))
        fileobj.seek(0)
        if not os.path.isfile(fileobj.name):
            raise UserError(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
        book = xlrd.open_workbook(fileobj.name)
        sheet = book.sheet_by_index(0)
        nrows = sheet.nrows
        rowi = 1
        budgets = {}
        if project.budget_line_ids:
            for budget in project.budget_line_ids:
                group = budget.specification_id.name
                if group not in budgets:
                    budgets[group] = {
                        'budget':'',
                        'name':'',
                        'material_value':0,
                        'labor_value':0,
                        'equipment_value':0,
                        'carriage_value':0,
                        'postage_value':0,
                        'other_value':0,
                        'lines':{}
                    }
                budgets[group]['budget']=budget
                budgets[group]['name']=group
                
                for line in budget.line_ids:
                    group1 = line.department_id.nomin_code
                    if group1 not in budgets[group]['lines']:
                        budgets[group]['lines'][group1]={
                            'line':'',
                            'name':'',
                            'material_value':0,
                            'labor_value':0,
                            'equipment_value':0,
                            'carriage_value':0,
                            'postage_value':0,
                            'other_value':0,
                        }
                    budgets[group]['lines'][group1]['line'] = line
                    budgets[group]['lines'][group1]['name'] = group1
                    budgets[group]['lines'][group1]['material_value'] = line.material_cost
                    budgets[group]['lines'][group1]['labor_value'] = line.labor_cost
                    budgets[group]['lines'][group1]['equipment_value'] = line.equipment_cost
                    budgets[group]['lines'][group1]['carriage_value'] = line.carriage_cost
                    budgets[group]['lines'][group1]['postage_value'] = line.postage_cost
                    budgets[group]['lines'][group1]['other_value'] = line.other_cost

        while rowi < nrows :
            row = sheet.row(rowi)
            specification  = row[0].value
            specification_id = self.env['project.specification'].search([('name','=',specification)])
            if not specification_id:
                 raise UserError(_(u' %s : Ийм нэртэй зориулалт бүртгэгдээгүй байна. Төслийн админтай холбогдоно уу. ' % specification))
            department  = row[1].value
            department_id = self.env['hr.department'].search([('nomin_code','=',department)])
            if not department_id:
                 raise UserError(_(u' %s номин кодтой Салбар олдсонгүй.' % department))
            

            if budgets and specification in budgets:
                if department in budgets[specification]['lines']:
                    line = budgets[specification]['lines'][department]['line']
                    line.update({'material_cost':row[2].value,'labor_cost':row[3].value,'equipment_cost':row[4].value,
                                'carriage_cost':row[5].value,'postage_cost':row[6].value,'other_cost':row[7].value,'description':row[8].value})
                else:
                    group1 = department
                    budgets[group]['lines'][group1]={
                            'line':'',
                            'name':'',                            
                        }
                    budgets[group]['lines'][group1]['name'] = group1
                    line_id = self.env['project.budget.line'].create({'project_budget_id':budgets[group]['budget'].id,'department_id':department_id.id,'material_cost':row[2].value,'labor_cost':row[3].value,'equipment_cost':row[4].value,
                                'carriage_cost':row[5].value,'postage_cost':row[6].value,'other_cost':row[7].value,'description':row[8].value})
                    budgets[group]['lines'][group1]['line'] = line_id
            else:
                group = specification                
                if group not in budgets:
                    budgets[group] = {
                        'budget':'',
                        'name':'',                        
                        'lines':{}
                    }
                budget = self.env['project.budget'].create({'specification_id':specification_id.id,'project_id':project.id})
                budgets[group]['name']=group
                budgets[group]['budget']=budget
                
                line_id = self.env['project.budget.line'].create({'project_budget_id':budgets[group]['budget'].id,'department_id':department_id.id,'material_cost':row[2].value,'labor_cost':row[3].value,'equipment_cost':row[4].value,
                                'carriage_cost':row[5].value,'postage_cost':row[6].value,'other_cost':row[7].value,'description':row[8].value})
                group1= line_id.department_id.nomin_code
                if group1 not in budgets[group]['lines']:
                        budgets[group]['lines'][group1]={
                            'line':'',
                            'name':'',}            
                budgets[group]['lines'][group1]['line'] = line_id
                budgets[group]['lines'][group1]['name'] = group1
            rowi+=1
class ImporTask(models.TransientModel):
    
    '''
        Төслийн даалгавар импортлох
    '''
    
    _name = 'import.task'
    _description = 'Import task'
        
    data=fields.Binary('Excel File', required=True)
    

    @api.multi
    def import_data(self):
        task_obj = self.env['project.task']
        form = self.browse()
        fileobj = NamedTemporaryFile('w+')
        fileobj.write(base64.decodestring(self.data))
        # fileobj.write(base64.decodestring(obj.data))
        fileobj.seek(0)
        if not os.path.isfile(fileobj.name):
            raise UserError(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
        book = xlrd.open_workbook(fileobj.name)
        sheet = book.sheet_by_index(0)
        nrows = sheet.nrows
        rowi = 1
        data = {}
        tasks_ids = []
        prod_problem = []
        qty_problem = []
        while rowi < nrows :
            verifier_users = []
            row = sheet.row(rowi)
            name        = row[0].value
            # names = self.env['project.task'].search([('name', '=', name)])


            department  = row[1].value
            departments = self.env['hr.department'].search([('name', '=', department)])
            deps = self.env['hr.department'].browse(departments)
            if not deps:
                 raise UserError(_(u' %s : Ийм нэртэй хэлтэс бүртгэгдээгүй байна ' % department))


            project     = row[2].value
            projects = self.env['project.project'].search([('name', '=', project)])
            projs =  self.env['project.project'].browse(projects)
            if not projects:
                 raise UserError(_(u' %s : Ийм нэртэй төсөл бүртгэгдээгүй байна ' % project))


            project_stage = row[3].value
            project_stages = self.env['project.stage'].search([('name', '=', project_stage)])
            proj_stages = self.env['project.stage'].browse(project_stages)
            if not project_stages:
                 raise UserError(_(u' %s : Ийм нэртэй төслийн даалгаварын үе шат бүртгэгдээгүй байна ' % project_stages))


            verifier    = row[4].value
            verifiers = self.env['hr.employee'].search([('passport_id', 'in', verifier.split(','))])
            if verifiers:
                for user in verifiers:
                    verifier_users.append(user.id)
            if not verifiers:
                 raise UserError(_(u' %s : Ийм регистерийн дугаартай ажилтан бүртгэгдээгүй байна' % verifier))


            user        = row[5].value
            users_employee = self.env['hr.employee'].search([('passport_id', '=', user)])
            if not users_employee:
                 raise UserError(_(u' %s : Ийм регистерийн дугаартай ажилтан бүртгэгдээгүй байна ' % user))
             
            start_date  = row[6].value
            end_date    = row[7].value
            if not end_date:
                raise UserError(_(u'Дуусгах огноо хоосон байна.'))

            names = self.env['project.task'].search([('name', '=', name),('project_id','=',projects.id),('user_id','=',users_employee.user_id.id)])
            if names:
                _logger.warning(_(u'%s Даалгавар үүссэн байна'%(name)))
            else:
                vals = {
                        'name':name,
                        'department_id': departments.id,
                        'project_id': projects.id,
                        'project_stage':project_stages.id,
                        'task_verifier_users':[(6,0,verifier_users)],
                        'user_id':users_employee.user_id.id,
                        'task_date_start':start_date,
                        'date_deadline':end_date,
                        'task_state':'t_new',
                        'task_type': 'normal',
                        'parent_task':False
                        }
                task_id = task_obj.create(vals)
                tasks_ids.append(task_id.id)
                _logger.warning(_(u'%s Даалгавар үүслээ'%(name)))
                
            rowi += 1
        return {
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'project.task',                      
            'domain':[('id','in',tasks_ids)],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }