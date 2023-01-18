# -*- coding: utf-8 -*-

from datetime import datetime, date
import time
import openerp.addons.decimal_precision as dp
from odoo import api, fields, models, _
from odoo.http import request
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from urllib3.connectionpool import _Default
from operator import itemgetter
import json

class ProjecTagsInherit(models.Model):
    _inherit = "project.tags"
    '''
           Пайз
    '''
    @api.model
    def create(self,vals):
        '''
           Пайзны давхардал шалгах
        '''

        tags = self.env['project.tags'].search([('name', '=', vals.get('name'))])
        if not tags:
            project_id = super(ProjecTagsInherit, self).create(vals)
            return project_id
        else:
            raise ValidationError(_(u'Ийм нэртэй пайз үүссэн байна !!!!'))

    @api.multi
    def unlink(self):
        '''
           Пайз устгах бүртгэлд ашигласан эсэх шалгах
        '''
        for proj in self:
            issue_ids = self.env['project.issue'].search([('tag_ids', '=', self.id)])
            tasks_ids = self.env['project.task'].search([('tag_ids', '=', self.id)])
            if not issue_ids and not tasks_ids:
                res = super(ProjecTagsInherit, self).unlink()
                return res
            else: 
                raise ValidationError(_(u'Энэхүү мэдээллийг бүртгэлд ашигласан тул устгах боломжгүй!!!!'))
    
class ProjecTaskType(models.Model):
    _inherit = 'project.task.type'
    '''
       Асуудын үе шат
    '''
    
    _description = 'Task Stage'
    
    name=fields.Char('Stage Name', required=True, translate=True, track_visibility='onchange')
    description=fields.Text('Description', translate=True, track_visibility='onchange')
    sequence=fields.Integer('Sequence', track_visibility='onchange')
    case_default=fields.Boolean('Default for New Projects',
                                     help="If you check this field, this stage will be proposed by default on each new project. It will not assign this stage to existing projects.")
            
    @api.model
    def create(self,vals):
        '''
           Асуудын үе шат үүсгэх, давхардал шалгах
        '''

        tags = self.env['project.task.type'].search([('name', '=', vals.get('name'))])
        if not tags:
            project_id = super(ProjecTaskType, self).create(vals)
            return project_id
        else:
            raise ValidationError(_(u'Ийм нэртэй асуудлын үе шат үүссэн байна !!!!'))
        
    @api.multi
    def unlink(self):
        '''
           Асуудын үе шат устгах, бүртгэлд ашигласан эсэх шалгах
        '''
        for proj in self:
            if not proj.project_ids:
                res = super(ProjecTaskType, self).unlink()
                return res
            else: 
                raise ValidationError(_(u'Энэхүү мэдээллийг бүртгэлд ашигласан тул устгах боломжгүй!!!!'))
    

    
    
class InvestmentBreakdown(models.Model):
    '''
        Хөрөнгө оруулалтын задаргаа
    '''
    _name = 'investment.breakdown'
    _description = 'Investment breakdown'
    _rec_name = 'amount_total'  
#     

    name=fields.Char('Investment name')
    amount_total=fields.Float('Amount')
    control_budget=fields.Many2one('control.budget', index=True, string = 'Control Budget')

class ProjectHistory(models.Model):
    _inherit = 'request.history'

    project_id = fields.Many2one('project.project', string='Project history', ondelete="cascade")


class ProjectIrAttachment(models.Model):
    '''
       Хавсралт
    '''
    _inherit = 'ir.attachment'


    @api.multi
    def _find_confirm_user(self):
        '''Батлах ажилтныг хэлтэс болон албан тушаалаар олох'''

        employee = self.env['hr.employee']
        employee_id = employee.sudo().search([('user_id','=',self._uid)])
        for attach in self:
            config_id = self.env['project.category'].search([('name','=',attach.project_document.project_categ.name)])
            config_line_id = self.env['project.category.line'].search([('parent_id','=',config_id.id),('project_type','=',attach.project_document.project_type),('project_state','=',attach.project_document.state)])
            if config_line_id:
                for line in config_line_id:
                    if line.is_confirm:
                                            
                        if employee_id.department_id == line.department_id and employee_id.job_id in line.job_ids:
                            attach.find_confirm_user = True
                        
            # confirm_attach_lines = self.env['project.category.line'].search([('parent_id','=',config_id.id),('project_type','=',attach.project_document.project_type),('confirm_state','=',attach.project_document.state)])
            # for line in confirm_attach_lines:
            #     print '\n\n\n test--' ,line.name 
            #     if line.is_confirm:
            #         raise ValidationError(_(u'%s - нэртэй хавсралтыг батлана уу.'%line.name)) 
                    
          
                        
            



  

    @api.multi
    def confirm_button(self):
        '''Батлах 
            Шаардах баримт бичгийг батлах
        '''


        employee = self.env['hr.employee']
        employee_id = employee.sudo().search([('user_id','=',self._uid)])
        self.write({'confirmed_employee': employee_id.id , 
                    'confirmed_date':time.strftime("%Y-%m-%d") , 
                    'is_invisible': True ,
                    }) 


    
    find_confirm_user = fields.Boolean(string='Confirm user' , default=False, compute=_find_confirm_user)
    confirmed_employee = fields.Many2one('hr.employee',string='Confirmed employee')
    confirmed_date = fields.Date(string='Confirmed date')
    is_invisible = fields.Boolean(string='Is invisible' , default=False)   
    attach_required = fields.Boolean('Хавсралт батлах', default=False)     
    confirm_attachment = fields.Boolean(string='Confirm attachment' , default=False)        

    project_document=fields.Many2one('project.project', string='Project Document')
    project_task_document=fields.Many2one('project.task','Task Document', index=True)
    project_work_task_document=fields.Many2one('project.task','Task Document', index=True)
    project_work_confirm_task_document=fields.Many2one('task.work.document','Task Document', index=True)
    control_budget_document=fields.Many2one('control.budget','Budget Document', index=True)
                
class MainSpecification(models.Model):
    '''
        Голлох үзүүлэлт
    '''
    _name = 'main.specification'
    _description = 'Main specifications'
    
    @api.multi
    def _is_editable_user(self):
        count = 0
        emp_obj = self.env['hr.employee']
        user = self.env['res.users'].browse(self.env.user.id)
        employees = emp_obj.sudo().search([('user_id','=',user.id)])
        for obj in self:
            if not employees:
                is_edit_user = False
            else:
                is_edit_user = False
                if obj.parent_project_id.state != 'draft':
                    is_edit_user = False
                if obj.parent_project_id.project_verifier.id == employees.ids[0] and  obj.confirm == True and obj.parent_project_id.state in ('comfirm','project_started') and obj.modify_click == True:
                    is_edit_user = True
            obj.is_editable_user = is_edit_user
    
    
    
    state=fields.Selection([('draft',u'Шинэ'),
                                                      ('cancel',u'Сонгогдоогүй'),
                                                      ('confirm',u'Баталсан'),
                                                      ('ready',u'Тодотгох'),
                                                      ('modify',u'Тодотгосон')],
                                                     u'Төлөв',readonly=True, default='draft')
    parent_project_id           = fields.Many2one('project.project', 'Project') # Төсөлтэй холбогдох талбар
    investment_id               = fields.Many2one('investment.breakdown', 'Investment') # Хөрөнгө оруулалт
    name                        = fields.Char('Main Line Name',required=True)
    area                        = fields.Integer('Area') # Талбайн хэмжээ
    sales_revenue               = fields.Float('Sales revenue') # Борлуулалтын орлого
    nvp                         = fields.Integer('NVP') # NVP
    irr                         = fields.Integer('IRR') # IRR
    roi                         = fields.Integer('ROI') # ROI
    recovery_of_investment_time = fields.Float('Recovery of investment time') # Хөрөнгө оруулалтын нөхөх хугацаа
    project_purpose             = fields.Char('Project Purpose') # Төслийн зориулалт
    other                       = fields.Char('Other') # бусад
    voters                      = fields.Many2many('hr.employee','project_main_hr_employee_ref_ref','project_main_id','emploe_id',string = u'Санал өгсөн ажилчид')# Бусад
    text                        = fields.Text(u'Тайлбар',required=True)
    is_editable_user            = fields.Boolean(compute=_is_editable_user , string = 'Is edit')
    
    
    # @api.model
    # def create(self,vals):
    #     '''
    #        Ноорог төлөвтөй үед үүсгэх боломжтой
    #     '''
    #     if vals and 'parent_project_id' in vals:
    #         if vals['parent_project_id'] != False:
    #             project = self.env['project.project'].browse(vals['parent_project_id'])
    #             if project.state != 'draft' and 'l_name' not in self._context:
    #                 raise UserError(_(u'Төсөл ноорог төлөвтөй үед голлох үзүүлэлт нэмэх боломжтой'))
    #     main = super(MainSpecification, self).create(vals)
    #     return main
    
    @api.multi
    def unlink(self):
        '''
           Ноорог төлөвтөй үед устгах боломжтой
        '''
        for obj in self:
            if obj.parent_project_id.state != 'draft':
                raise UserError(_(u'Төсөл ноорог төлөвтөй үед голлох үзүүлэлт устгах боломжтой'))
        return super(MainSpecification, self).unlink()

    

class ProjecCategory(models.Model):
    _name ='project.category'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    '''
       Төслийн ангилал бүртгэх
    '''
    

    name=fields.Char('Name',required=True, track_visibility='onchange')
    line_ids = fields.One2many('project.category.line','parent_id', string = 'Required attachment')   
     
    description=fields.Text(u'Тайлбар',  track_visibility='onchange')
    specification_ids = fields.Many2many('project.specification','project_category_specification_rel','categ_id','spec_id',string = 'Project specifications')#
    task_line_ids = fields.One2many('required.attachment.in.task','category_id', string = "Required attachment in task")
   
    @api.model         
    def create(self,vals):
        '''
           Төслийн ангилал үүсгэх, давхардал шалгах
        '''
        tags = self.env['project.category'].search([('name', '=', vals.get('name'))])
        if not tags:
            project_id = super(ProjecCategory, self).create(vals)
            return project_id
        else:
            raise ValidationError(_(u'Ийм нэртэй Төслийн ангилал үүссэн байна !!!!'))
    
    @api.multi
    def unlink(self):
        '''
           Төслийн ангилал устгах, бүртгэлд ашигласан эсэх шалгах
        '''
        issue_ids = self.env['project.project'].search([('project_categ', '=', self.id)])
        if len(issue_ids)==0:
            res = super(ProjecCategory, self).unlink()
            return res
        else: 
            raise ValidationError(_(u'Энэхүү мэдээллийг бүртгэлд ашигласан тул устгах боломжгүй!!!!'))
        
class ProjectCategroyLine(models.Model):
    _name = 'project.category.line'


    STATES = [('draft',u'Ноорог'),
                        ('verify_by_economist', u'ЭЗ Хянах'),
                        ('approve_by_director', u'СЗ Батлах'),
                        ('approve_by_business_director', u'БХЗ Батлах'),
                        ('approve_by_ceo', u'ХГЗ Батлах'),
                        ('approve_by_board_member', u'ТУЗ Батлах'),
                        ('comfirm',u'Батлагдсан'),
                        ('implement_project', u'Хэрэгжүүлэлт'),
                        ('ready', u'Үнэлэх'),
                        ]



    STATE_SELECTION = [('draft',u'Ноорог'),
                        ('request',u'Хүсэлт'),
                        ('comfirm',u'Батлагдсан'),
                        ('project_started',u'Эхэлсэн'),
                        ('finished',u'Дууссан'),
                        ('ready',u'Үнэлэх'),
                        ('evaluate',u'Үнэлэгдсэн'),
                        ]

    name = fields.Char(string='Name')
    parent_id = fields.Many2one('project.category',string = 'parent')
    project_id = fields.Many2one('project.project' , string='Project')
    project_state = fields.Selection(STATE_SELECTION,string = 'State', copy=False , default = 'draft', track_visibility='onchange')
    confirm_state = fields.Selection(STATES,string = 'Батлах төлөв ', required=True,  default = 'draft', track_visibility='onchange')
    project_type = fields.Selection([('investment_project',"Хөрөнгө оруулалттай төсөл"),('construction_project',"Барилгын засварын төсөл"),('operational_project',"Үйл ажиллагааны төсөл"),('general_project',"Ерөнхий")],string='Project type')
    is_confirm = fields.Boolean(string='Is confirm' , default=False)
    department_id =  fields.Many2one('hr.department', string='Батлах ажилтны хэлтэс')
    job_ids =  fields.Many2many('hr.job', string='Батлах ажилтны албан тушаал')

    

    @api.onchange('is_confirm')
    def onchange_is_confirm(self):
        
        for line in self:           
            if not line.is_confirm:
                line.update({'department_id':False,
                             'job_ids': False,
                            })
                




    

class RequiredAttachmentTask(models.Model):
    _name = 'required.attachment.in.task'

    task_id = fields.Many2one('project.task',string='Project task')
    name = fields.Text(string='Name')
    category_id = fields.Many2one('project.category',string = 'Project category')
    project_type = fields.Selection([('investment_project',"Хөрөнгө оруулалттай төсөл"),('construction_project',"Барилгын засварын төсөл"),('operational_project',"Үйл ажиллагааны төсөл"),('general_project',"Ерөнхий")],string='Project type')
    task_state = fields.Selection([
                                   ('t_new' ,u'Шинэ'),
                                   ('t_cheapen',u'Үнэ тохирох'),
                                   ('t_cheapened',u'Үнэ тохирсон'),
                                   ('t_user',u'Хариуцагчтай'),
                                   ('t_start',u'Хийгдэж буй'),
                                   ('t_control',u'Хянах'),
                                   ('t_confirm',u'Батлах'),
                                   ('t_evaluate',u'Үнэлэх'),
                                   ('t_done',u'Дууссан'),
                                   ('t_cancel',u'Цуцалсан'),
                                   ('t_back',u'Хойшлуулсан')],string='State')   
    task_type = fields.Selection([('normal',u'Энгийн'), # Энгийн ажил
                                                      ('tariff_task',u'Тарифт ажил'), # Тарифт ажил
                                                      ('work_graph',u'Ажлын зураг'),
                                                      ('work_task',u'Ажлын даалгавар'), # Худалдан авалтын ажил
                                                      ],
                                                     'Task type',  copy=False, default='normal', track_visibility='onchange')

class ProjectProject(models.Model):
    '''
        Төсөл
    '''
    _inherit = 'project.project'
    _description = 'Project'
    

    @api.multi
    def name_get(self):
        result = []
        for proj in self:
            name = proj.name[:50]
            result.append((proj.id, name))
        return result

    @api.multi
    def create_history(self,state,note):
        history_obj = self.env['request.history']
        history_obj.create({'user_id':self._uid,
                                # 'sequence':sequence,
                                'project_id':self.id,
                                # 'date':fields.Date.context_today(self),
                                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'comment':note
                            })

    @api.multi
    def _get_visibility_selection(self):
        
        """ Overriden in portal_project to offer more options """
        return [('portal', _('Захиалагчийн төрөл: Портал хэрэглэгч + RACI Хандалт')),
                ('employees', _('All Employees Project: all employees can access')),
                ('followers', _('Хувийн төсөл: RACI хандалт'))]



    def _control_budget_counts(self):        

        for order in self:
            order.control_budget_counts = len(self.env['control.budget'].sudo().search([('project_id','=',order.id)])) or 0            
        return True

    @api.one
    def _is_expenditure_handler(self):

        # self.logged_in_employee_id.id == employee_id.id or employee_id.user_id.has_group('nomin_hr.group_hr_timesheet_manager'):

        if self.env.user.has_group('project.group_project_manager') or self.env.user.has_group('project.group_project_admin') or self.env.user.has_group('project.group_project_leader'):
 
            self.is_expenditure_handler = True

    _visibility_selection = lambda self, *args, **kwargs: self._get_visibility_selection(*args, **kwargs)


    # @api.one
    # def _is_project_category(self):
    #     for project in self:
    #         print '\n\n\n project' , project
    #         if project.is_parent_project :
    #             project.project_category = True
    #             print '\n\n\n\n etseg',project.project_category
    #         elif not project.is_parent_project and not project.parent_project:   
    #             project.project_category = True
    #             print '\n\n\n\n undsen',project.project_category
    #         elif not project.is_parent_project and  project.parent_project:
    #             project.project_category = False
    #             print '\n\n\n\n ded',project.project_category
        
    
    # @api.onchange('is_parent_project')
    # def onchange_is_parent_project(self):
    #     for project in self:
    #         if project.is_parent_project :
    #             project.project_category = True
    #             print '\n\n\n\n onchange etseg',project.project_category
    #         elif not project.is_parent_project and not project.parent_project:   
    #             project.project_category = True
    #             print '\n\n\n\n on undsen',project.project_category
    #         else:
    #             project.project_category = False
    #             print '\n\n\n\n on ded',project.project_category

    @api.multi
    def _is_raci_user(self):
        for proj in self:            
            if proj.privacy_visibility in ['portal','followers']:
                if self.env.user.id in proj.r_user_ids.ids :
                    proj.is_raci_user = True
                elif self.env.user.id in proj.a_user_ids.ids:
                    proj.is_raci_user = True
                elif self.env.user.id in proj.c_user_ids.ids:
                    proj.is_raci_user = True
                else:
                    proj.is_raci_user = False
            else:
                proj.is_raci_user = True
            if proj.user_id.id != self._uid:
                proj.is_project_manager = False
            else:
                proj.is_project_manager = True
            if self.env.user.has_group('project.group_project_admin') or self.env.user.has_group('project.group_project_leader'):
                proj.is_project_manager = True
                proj.is_raci_user = True
    
    def state_handler(self,current_state,target):
        # for project in self:


        #     sod_id = project.env['sod.designer'].state_handler(project,current_state,project.department_id,project.created_user_id,target)
        #     print 'sod_id',sod_id,project

        
        # return  sod_id
                
        # if self:

        project = self
        sod_id = project.env['sod.designer'].state_handler(project,current_state,project.department_id,project.created_user_id,target)
            # print 'sod_id',sod_id,project

        
        return  sod_id


    # @api.one
    # def state_handler(self,current_state):

    #     flow_id = self.env['sod.designer'].search([('model_name','=','project.project')])
    #     if flow_id:
    #         object_id = self.env['sod.state'].search([('designer_id','=',flow_id.id),('code','=',current_state)])
    #         # print '\n\n\n\ haa----' , object_id 
    #         if object_id:

    #             if object_id.type[:2] == 'uv':
    #                 if object_id[0].python:      
    #                     exec(object_id[0].python)
    #                 result_values = flow_id[0].workflow_handler_by_user(self.workflow_name,self.department_id,self.created_user_id)

    #                 self.update(result_values)
    


    @api.multi
    def refresh_workflow(self):

        # self.state_handler(self.previous_state)
        # self.state_handler(self.state,'previous_state')
        self.state_handler(json.loads(self.json_data)['previous_state'],'previous_state')

    

    @api.multi
    def surplus_button(self):
        '''Дэд төслийн дүн тодотгох
        '''

        for project in self:
            if not project.user_id.id == self._uid:
                raise ValidationError(_(u'Төслийн менежер тодотгол үүсгэх боломжтой'))
          
     
        return {
                'name': 'Note',
                'context':{'surplus':'surplus'},
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'surplus.budgeted.amount',          
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'state' : 'draft' ,
                }


        # self.state_handler(self.state)
        # self.write({'previous_state':self.state,
        #     'state':json.loads(self.json_data)['next_state']})

        # self.create_history('surplus_budget','Modified')
    

    @api.depends('budget_line_ids')
    def _compute_total_limit(self):
        for project in self:
            balance  = 0
            if project.parent_budget_line_ids:
                for line in project.parent_budget_line_ids:                 
                    balance += line.approximate_amount
            elif project.budget_line_ids:
                for line in project.budget_line_ids:                 
                    balance += line.sum_of_budgeted_amount
            project.total_limit = balance
    

    @api.one
    def _project_flag(self):
        if self.create_date <= '2022-03-28 09:00:00':
            self.project_flag = False
        else:
            self.project_flag = True

    @api.multi
    def _compute_amount_new(self):
        for project in self:
            project.material_remaining_amount_new = project.material_budget_new - project.material_expenditure_new
            project.labour_remaining_amount_new = project.labour_budget_new - project.labour_expenditure_new
            project.equipment_remaining_amount_new = project.equipment_budget_new - project.equipment_expenditure_new
            project.transport_remaining_amount_new = project.transport_budget_new - project.transport_expenditure_new
            project.direct_remaining_amount_new = project.direct_budget_new - project.direct_expenditure_new
            project.other_remaining_amount_new = project.other_budget_new - project.other_expenditure_new
    
            

    

    project_flag = fields.Boolean(string='Project flag' , compute=_project_flag , default=True)
    # project_flag = fields.Boolean(string='Project flag' , default=False) 
    button_check = fields.Boolean(string='Button check' , default=False)             
    user_id=fields.Many2one('res.users', 'Project Manager', track_visibility='onchange')
    project_purpose=fields.Text("Project purpose", track_visibility='onchange') # Төслийн зорилго
    project_objectives=fields.Text("Project objectives", track_visibility='onchange') # Төслийн зорилт
    total_duration = fields.Float(string='Total duration', readonly=True,  copy=False)
    project_type = fields.Selection([('investment_project',"Хөрөнгө оруулалттай төсөл"),('construction_project',"Барилгын засварын төсөл"),('operational_project',"Үйл ажиллагааны төсөл"),('general_project',"Ерөнхий")],string='Project type')
    start_date=fields.Date('Start Date', select=True, track_visibility='onchange') # Төслийн эхлэх хугацаа
    end_date=fields.Date('End Date', select=True, track_visibility='onchange') # Төслийн дуусах хугацаа
    benefits=fields.Text("Benefits", track_visibility='onchange') # Төслийн үр ашиг
    project_categ=fields.Many2one('project.category', "Category", required = 'True', track_visibility='onchange', index=True) # Төслийн ангилал, readonly=True, states={'draft': [('readonly', False)]}
    parent_project=fields.Many2one('project.project',string = 'Parent project', track_visibility='onchange', index=True)
    project_checkers=fields.Many2many('hr.employee','project_project_project_hr_employee_ref','project_id_ids','employ_id',string = 'Project Checkers', track_visibility='onchange' ,domain="['|',('active','=',True),('active','=',False)]")#төсөл хянах хүмүүс
    required_cost=fields.Integer("Required Cost")# Төслийн хянасан зардал
    project_cost=fields.Integer("Project Cost")# Төслийн бодит зардал
    comment=fields.Text('Comment', track_visibility='onchange') # Тайлбар
    team_users=fields.Many2many('hr.employee','project_project_hr_employee_ref_team','project_team_id','emp_id',string = 'Project team', track_visibility='onchange')#төслийн баг
    project_verifier=fields.Many2one('hr.employee', index=True,string = 'Project verifier', track_visibility='onchange')#төсөл батлагч
    evaluator=fields.Many2many('hr.employee','project_project_project_hr_employee_ref_ref','project_id_id','empl_id',string = 'Project evaluators', track_visibility='onchange')#Төсөл үнэлэгчид
    created_user_id=fields.Many2one('res.users', index=True,string=u'Үүсгэсэн хэрэглэгч', default=lambda self: self.env.user.id)
    privacy_visibility=fields.Selection(_get_visibility_selection, string='Төслийн хандалтын эрх', required=True,
            help="Holds visibility of the tasks or issues that belong to the current project:\n"
                    "- Portal : employees see everything;\n"
                    "   if portal is activated, portal users see the tasks or issues followed by\n"
                    "   them or by someone of their company\n"
                    "- Employees Only: employees see all tasks or issues\n"
                    "- Followers Only: employees see only the followed tasks or issues; if portal\n"
                    "   is activated, portal users see the followed tasks or issues.", track_visibility='onchange',default=False)
         # Голлох үзүүлэлт класстай холбогдох талбар
    overrun_counts=fields.Integer(string = 'Overrun Counts')
    expenditure_ratio=fields.Integer(string = 'Expenditure Ratio',group_operator='avg')
    overrun_ratio=fields.Integer(string = 'Overrun Ratio')


    estimated_budget=fields.Float(string = 'Estimated Budget')
    project_budget=fields.Float(string = 'Total Budget')
    total_expenditure=fields.Float(string = 'Total Expenditure Amount')
    total_remaining_amount=fields.Float(string = 'Total Remaining Amount')
    task_counts=fields.Integer(string = 'Task Counts')
    issue_counts=fields.Integer(string = 'Issue Counts')

    material_budget_new =fields.Float(string = 'Material Budget')
    labour_budget_new =fields.Float(string = 'Labour Budget')
    equipment_budget_new =fields.Float(string = 'Equipment Budget')
    transport_budget_new =fields.Float(string = 'Transport Budget')                    
    direct_budget_new =fields.Float(string = 'Direct Budget')
    other_budget_new =fields.Float(string = 'Other Budget')


    material_budget=fields.Float(string = 'Material Budget')
    labour_budget=fields.Float(string = 'Labour Budget')
    equipment_budget=fields.Float(string = 'Equipment Budget')
    transport_budget=fields.Float(string = 'Transport Budget')                    
    direct_budget=fields.Float(string = 'Direct Budget')
    other_budget=fields.Float(string = 'Other Budget')

    material_expenditure_new=fields.Float(string = 'Material Expenditure Amount')
    labour_expenditure_new=fields.Float(string = 'Labour Expenditure Amount')
    equipment_expenditure_new=fields.Float(string = 'Equipment Expenditure Amount')
    transport_expenditure_new=fields.Float(string = 'Transport Expenditure Amount')                    
    direct_expenditure_new=fields.Float(string = 'Direct Expenditure Amount')
    other_expenditure_new=fields.Float(string = 'Other Expenditure Amount')

    material_expenditure=fields.Float(string = 'Material Expenditure Amount')
    labour_expenditure=fields.Float(string = 'Labour Expenditure Amount')
    equipment_expenditure=fields.Float(string = 'Equipment Expenditure Amount')
    transport_expenditure=fields.Float(string = 'Transport Expenditure Amount')                    
    direct_expenditure=fields.Float(string = 'Direct Expenditure Amount')
    other_expenditure=fields.Float(string = 'Other Expenditure Amount')


    material_remaining_amount_new =fields.Float(string = 'Material Remaining Amount', compute=_compute_amount_new)
    labour_remaining_amount_new =fields.Float(string = 'Labour Remaining Amount', compute=_compute_amount_new)
    equipment_remaining_amount_new =fields.Float(string = 'Equipment Remaining Amount', compute=_compute_amount_new)
    transport_remaining_amount_new =fields.Float(string = 'Transport Remaining Amount', compute=_compute_amount_new)                    
    direct_remaining_amount_new =fields.Float(string = 'Direct Remaining Amount', compute=_compute_amount_new)
    other_remaining_amount_new =fields.Float(string = 'Other Remaining Amount', compute=_compute_amount_new)

    material_remaining_amount=fields.Float(string = 'Material Remaining Amount')
    labour_remaining_amount=fields.Float(string = 'Labour Remaining Amount')
    equipment_remaining_amount=fields.Float(string = 'Equipment Remaining Amount')
    transport_remaining_amount=fields.Float(string = 'Transport Remaining Amount')                    
    direct_remaining_amount=fields.Float(string = 'Direct Remaining Amount')
    other_remaining_amount=fields.Float(string = 'Other Remaining Amount')

    control_budget_counts = fields.Integer(compute=_control_budget_counts, string='Control Budget Counts')
    is_expenditure_handler = fields.Boolean(string="Is Expenditure Handler", compute=_is_expenditure_handler, default=False)
    is_parent_project = fields.Boolean(string="Is Parent Project", default=False )
    # project_category = fields.Boolean(string="Is Parent Project", default=False , compute=_is_project_category)
    
    document=fields.One2many('ir.attachment','project_document', string = 'Document')
    check_date_start=fields.Date(string='Check Date')
    check_date_end=fields.Date(string='Check Date')
    # RACI 
    is_project_manager = fields.Boolean(string="Is project manager ", compute=_is_raci_user, default=True)
    is_raci_user = fields.Boolean(string="Is raci user", compute=_is_raci_user, default=True)
    r_user_ids = fields.Many2many('res.users','project_project_r_res_users_rel','project_id','r_user_id',string='R users')
    a_user_ids = fields.Many2many('res.users','project_project_a_res_users_rel','project_id','a_user_id',string='A users')
    c_user_ids = fields.Many2many('res.users','project_project_c_res_users_rel','project_id','a_user_id',string='C users')
    i_user_ids = fields.Many2many('res.users','project_project_i_res_users_rel','project_id','a_user_id',string='I users')
    budget_line_ids = fields.One2many('project.budget','project_id', string="Project budget")
    parent_budget_line_ids = fields.One2many('project.budget','parent_project_id', string="Parent project budget")
    surplus_line_ids = fields.One2many('surplus.budget','project_id', string="Surplus budget")
    parent_project_surplus = fields.One2many('surplus.budget','parent_project_id', string="Parent surplus budget")
    budgeted_line_ids = fields.One2many('budgeted.line','project_id', string="Budgeted line")
    parent_budgeted_line_ids = fields.One2many('budgeted.line','parent_project_id', string="Budgeted line")
    performance_line_ids = fields.One2many('performance.line','project_id', string="Performance line")
    project_category_line = fields.One2many('project.category.line','project_id', string="Project category line")
    subproject_line_ids = fields.One2many('subproject.line','project_id', string="SubProject line")

    #add new field
    sales_revenue = fields.Float(string="Sales revenue")
    average_annual_sales_revenue_growth = fields.Float(string="Average annual sales revenue growth")
    average_percentage_of_sales_of_operating_expenses = fields.Float(string="Average percentage of sales of operating expenses ")
    average_cost_of_resources = fields.Float(string="Average cost of resources")
    present_value = fields.Float(string="Present value")
    rate_of_return = fields.Float (string="Rate of return")
    gross_probit_percent = fields.Float(string="Gross probit percent")
    return_of_investment = fields.Float(string="Return of investment")
    compensate_of_investment = fields.Float(string="Compensate of investment (year)")
    area_m = fields.Integer(string="Area m.kB")
    total_investment = fields.Float(string = "Total investment")
    total_budget = fields.Float (string="Total budget")
    
    total_performance = fields.Float(string="Total performance")
    total_actual_balance = fields.Float(string="Total actual balance")
    total_limit = fields.Float(string="Нийт төлөвлөсөн хөрөнгө оруулалт" , compute = '_compute_total_limit' )
    workflow_name = fields.Char(string="Сонгогдсон урсгал")
    workflow_id = fields.Many2one('sod.workflow.name', string='Сонгогдсон урсгал')
    button_clickers = fields.Many2many('res.users', string='Button clickers')
    sod_msg = fields.Char(string='Товч дарах хэрэглэгч')
    has_follower = fields.Boolean('Дагагчаар нэмэх эсэх')
    skip_workflow = fields.Boolean('Урсгал алгасах эсэх')
    
    previous_state = fields.Char(string='Previous state',default = 'draft')

    history_ids = fields.One2many('request.history','project_id', string="Request History")

        
    duty_line_ids  = fields.One2many('employee.duty.line','project_id', string="Work Service")   
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             

    @api.onchange('parent_project')
    def onchange_parent_project_id(self):
        '''
            Эцэг төсөл солигдоход хөрөнгө оруулалтын төлөвлөлт табын мэдээллийг харуулах
        '''

        for project in self:    
            if project.parent_project:                   

                 project.update({'project_type': project.parent_project.project_type               
                        })
                            
 
    @api.onchange('privacy_visibility','project_verifier','evaluator','project_checkers','user_id')
    def onchange_privacy_visibility(self):
        for project in self:
            if project.privacy_visibility in ['portal','followers']:
                # R USERS
                if project.user_id and project.user_id.id not in project.r_user_ids.ids:
                    project.update({'r_user_ids':[(6,0,[project.user_id.id]+project.r_user_ids.ids)]})
                
                if project.project_verifier and project.project_verifier.user_id.id not in project.a_user_ids.ids:
                    project.update({'a_user_ids':[(6,0,[project.project_verifier.user_id.id]+project.a_user_ids.ids)]})
                
                if project.evaluator.ids:
                    user_ids=[]
                    for emp in  project.evaluator:
                        if emp.user_id and emp.user_id.id not in project.a_user_ids.ids:
                            user_ids.append(emp.user_id.id)
                    if user_ids:                        
                            project.update({'a_user_ids':[(6,0,user_ids+project.a_user_ids.ids)]})
                
                if project.project_checkers :                                        
                    user_ids=[]
                    for emp in  project.project_checkers:
                        if emp.user_id and emp.user_id.id not in project.c_user_ids.ids:
                            user_ids.append(emp.user_id.id)
                    if user_ids:                        
                            project.update({'c_user_ids':[(6,0,user_ids+project.c_user_ids.ids)]})

    @api.multi
    def add_raci_users(self, add_type, users):
        if type(users)==int:
            users = [users]
        for project in self:
            user_ids=[]
            if add_type=='R' and users:
                for user in users:
                    if  user not in project.r_user_ids.ids:
                        user_ids.append(user)
                project.update({'r_user_ids':[(6,0,user_ids+project.r_user_ids.ids)]})
            elif add_type=='A' and users:
                for user in users:
                    if  user not in project.a_user_ids.ids:
                        user_ids.append(user)
                project.update({'a_user_ids':[(6,0,user_ids+project.a_user_ids.ids)]})
            elif add_type=='C' and users:
                for user in users:
                    if  user not in project.c_user_ids.ids:
                        user_ids.append(user)
                project.update({'c_user_ids':[(6,0,user_ids+project.c_user_ids.ids)]})
            elif add_type=='I' and users:
                for user in users:
                    if  user not in project.i_user_ids.ids:
                        user_ids.append(user)
                project.update({'i_user_ids':[(6,0,user_ids+project.i_user_ids.ids)]})

    @api.model
    def create(self,vals):
        result =  super(ProjectProject, self).create(vals)
        
        budget_ids = []
        total = 0
        for project in result:   
            if project.is_parent_project:
                if not project.parent_budget_line_ids and project.project_flag:
                    raise UserError(_(u'Хөрөнгө оруулалтын төлөвлөлтийн мөр үүсээгүй байна'))
            elif project.parent_project.parent_budget_line_ids:
                for budget_line in project.parent_project.parent_budget_line_ids:   
                    if project.department_id == budget_line.department_id and budget_line.investment_pattern in project.project_categ.specification_ids: 
                        if budget_line.possible_amount_create_project !=0.0:
                            balance = 0 
                            if budget_line.possible_amount_create_project:
                                balance = budget_line.possible_amount_create_project    
                            
                            

                            budget_ids.append((0,0,{'investment_pattern':budget_line.investment_pattern.id,
                                                    'department_id':budget_line.department_id.id,
                                                    'approximate_amount':balance,
                                                    'state':budget_line.state,
                                                    'possible_amount_create_project':balance,
                                                    'default_type':True
                                                    })) 
                        else:
                            raise UserError(_(u'Сонгосон эцэг төслийн үлдэгдэл 00 болсон байна')) 
            # else:
            #     raise UserError(_(u'Та дэд төсөл үүсгэх бол эцэг төсөл сонгоно уу'))

                    

            project.update({'budget_line_ids':budget_ids})
                                          

            # if project.is_parent_project:
            #     for line in project.parent_budget_line_ids:
            #         total += line.approximate_amount
            #     project.total_limit = total
            # else:
            #     for line in project.budget_line_ids:
            #         total += line.approximate_amount
            #     project.total_limit = total

        return result

    @api.multi 
    def write(self, vals):    

        overrun_counts=0
        expenditure_ratio=0
        overrun_ratio=0


        project_budget_material_limit = 0.0
        project_budget_labor_limit = 0.0
        project_budget_equipment_limit = 0.0
        project_budget_carriage_limit = 0.0
        project_budget_postage_limit = 0.0
        project_budget_other_limit = 0.0

        material_cost = 0.0
        labor_cost = 0.0
        carriage_cost = 0.0
        equipment_cost = 0.0
        postage_cost = 0.0
        other_cost = 0.0

        project_budget_material = 0.0
        project_budget_labor = 0.0
        project_budget_equipment = 0.0
        project_budget_carriage = 0.0
        project_budget_postage = 0.0
        project_budget_other = 0.0

        project_budget_limit = 0.0
        total_expenditure = 0.0
        project_budget = 0.0


        task_counts = len(self.env['project.task'].sudo().search([('project_id','=',self.id)]))
        if task_counts>0:
            vals.update({
                'task_counts' : task_counts,
                })


        issue_counts = len(self.env['project.issue'].sudo().search([('project_id','=',self.id)]))
        if issue_counts>0:
            vals.update({
                'issue_counts' : issue_counts,
                })


        main_specification_id = self.env['main.specification'].sudo().search([('parent_project_id','=',self.id),('state','=','confirm')],limit =1)
        overrun_counts = len(self.env['main.specification'].sudo().search([('parent_project_id','=',self.id)]))
        control_budget = self.env['control.budget'].sudo().search([('project_id','=',self.id),('state','=','done')])
        control_budget_new = self.env['control.budget'].sudo().search([('project_id','=',self.id)])
        for project in self:
            if project.project_flag:
                
                if control_budget_new:
                    for i in control_budget_new:
                        

                        material_cost += i.material_cost 
                        labor_cost += i.labor_cost 
                        carriage_cost += i.carriage_cost 
                        equipment_cost += i.equipment_cost 
                        postage_cost += i.postage_cost
                        other_cost += i.other_cost 

                        total_expenditure += i.material_cost + i.labor_cost 
                        total_expenditure += i.carriage_cost + i.equipment_cost 
                        total_expenditure += i.postage_cost + i.other_cost 

                    project_budget_material_limit += i.project_budget_material_limit 
                    project_budget_labor_limit += i.project_budget_labor_limit
                    project_budget_equipment_limit += i.project_budget_equipment_limit 
                    project_budget_carriage_limit += i.project_budget_carriage_limit 
                    project_budget_postage_limit += i.project_budget_postage_limit
                    project_budget_other_limit += i.project_budget_other_limit 

                    project_budget_limit += i.project_budget_material_limit + i.project_budget_labor_limit 
                    project_budget_limit += i.project_budget_equipment_limit + i.project_budget_carriage_limit 
                    project_budget_limit += i.project_budget_postage_limit + i.project_budget_other_limit 

                    project_budget_material += i.project_budget_material
                    project_budget_labor += i.project_budget_labor
                    project_budget_equipment += i.project_budget_equipment 
                    project_budget_carriage += i.project_budget_carriage 
                    project_budget_postage += i.project_budget_postage
                    project_budget_other += i.project_budget_other 

                    project_budget += i.project_budget_material + i.project_budget_labor
                    project_budget += i.project_budget_equipment + i.project_budget_carriage 
                    project_budget += i.project_budget_postage + i.project_budget_other 

                    # expenditure_ratio = 0
                    # overrun_ratio = 0
                    # if main_specification_id.total_investment>0:
                    #     expenditure_ratio = int(total_expenditure*100/main_specification_id.total_investment)
                    #     overrun_ratio = int(project_budget_limit*100/main_specification_id.total_investment)

                    vals.update({



                        'material_expenditure_new':material_cost,
                        'labour_expenditure_new':labor_cost,
                        'equipment_expenditure_new':equipment_cost,
                        'transport_expenditure_new':carriage_cost,
                        'direct_expenditure_new':postage_cost,
                        'other_expenditure_new':other_cost,

                      

                        'project_budget' : project_budget_limit,
                        'total_expenditure' : total_expenditure,
                        'total_remaining_amount' : project_budget,


                        # 'overrun_counts':overrun_counts,
                        # 'expenditure_ratio':expenditure_ratio,
                        # 'overrun_ratio':overrun_ratio,
                        # 'estimated_budget' : main_specification_id.total_investment


                        })
            
            elif control_budget:
                for i in control_budget:
                    print '\n\n\n ccccccccccccbudget  i' , i

                    material_cost += i.material_cost 
                    labor_cost += i.labor_cost 
                    carriage_cost += i.carriage_cost 
                    equipment_cost += i.equipment_cost 
                    postage_cost += i.postage_cost
                    other_cost += i.other_cost 

                    total_expenditure += i.material_cost + i.labor_cost 
                    total_expenditure += i.carriage_cost + i.equipment_cost 
                    total_expenditure += i.postage_cost + i.other_cost 

                project_budget_material_limit += i.project_budget_material_limit 
                project_budget_labor_limit += i.project_budget_labor_limit
                project_budget_equipment_limit += i.project_budget_equipment_limit 
                project_budget_carriage_limit += i.project_budget_carriage_limit 
                project_budget_postage_limit += i.project_budget_postage_limit
                project_budget_other_limit += i.project_budget_other_limit 

                project_budget_limit += i.project_budget_material_limit + i.project_budget_labor_limit 
                project_budget_limit += i.project_budget_equipment_limit + i.project_budget_carriage_limit 
                project_budget_limit += i.project_budget_postage_limit + i.project_budget_other_limit 

                project_budget_material += i.project_budget_material
                project_budget_labor += i.project_budget_labor
                project_budget_equipment += i.project_budget_equipment 
                project_budget_carriage += i.project_budget_carriage 
                project_budget_postage += i.project_budget_postage
                project_budget_other += i.project_budget_other 

                project_budget += i.project_budget_material + i.project_budget_labor
                project_budget += i.project_budget_equipment + i.project_budget_carriage 
                project_budget += i.project_budget_postage + i.project_budget_other 

                expenditure_ratio = 0
                overrun_ratio = 0
                if main_specification_id.total_investment>0:
                    expenditure_ratio = int(total_expenditure*100/main_specification_id.total_investment)
                    overrun_ratio = int(project_budget_limit*100/main_specification_id.total_investment)

                vals.update({


                    'material_budget':project_budget_material_limit,
                    'labour_budget':project_budget_labor_limit,
                    'equipment_budget':project_budget_equipment_limit,
                    'transport_budget':project_budget_carriage_limit,
                    'direct_budget':project_budget_postage_limit,
                    'other_budget':project_budget_other_limit,

                    'material_expenditure':material_cost,
                    'labour_expenditure':labor_cost,
                    'equipment_expenditure':equipment_cost,
                    'transport_expenditure':carriage_cost,
                    'direct_expenditure':postage_cost,
                    'other_expenditure':other_cost,

                    'material_remaining_amount':project_budget_material,
                    'labour_remaining_amount':project_budget_labor,
                    'equipment_remaining_amount':project_budget_equipment,
                    'transport_remaining_amount':project_budget_carriage,
                    'direct_remaining_amount':project_budget_postage,
                    'other_remaining_amount':project_budget_other,

                    'project_budget' : project_budget_limit,
                    'total_expenditure' : total_expenditure,
                    'total_remaining_amount' : project_budget,


                    'overrun_counts':overrun_counts,
                    'expenditure_ratio':expenditure_ratio,
                    'overrun_ratio':overrun_ratio,
                    'estimated_budget' : main_specification_id.total_investment


                    })
        # if 'document' in vals:
            
        #         # if vals.get('document')[0][1]:
        #     raise UserError(_(u'Ноорог төлөв дээрх төслийн хавсралт устгах боломжтой.'))

        
        result = super(ProjectProject, self).write(vals)
        if vals.get('parent_project') or vals.get('department_id') :
            
            budget_ids = []
            for project in self:
                if project.parent_project:
                    if project.parent_project.parent_budget_line_ids and project.parent_project.is_parent_project:
                        for budget_line in  project.parent_project.parent_budget_line_ids:
                            if project.department_id == budget_line.department_id :  
                                if budget_line.possible_amount_create_project !=0.0:
                                
                                    budget_ids.append((0,0,{'investment_pattern':budget_line.investment_pattern.id,
                                                            'department_id':budget_line.department_id.id,
                                                            'approximate_amount':budget_line.possible_amount_create_project,
                                                            'state':budget_line.state,
                                                            'possible_amount_create_project':budget_line.possible_amount_create_project,
                                                            'default_type':True
                                                            })) 
                                else:
                                    raise UserError(_(u'Сонгосон эцэг төслийн үлдэгдэл 00 болсон байна'))            
                                
                            else:
                                project.budget_line_ids.unlink()
                    else:
                        raise UserError(_(u'Сонгосон эцэг төсөл дээр хөрөнгө оруулалтын төлөвлөлтийн мөр үүсээгүй байна'))  

                   
                    

            project.update({'budget_line_ids':budget_ids,
                            'project_type': project.parent_project.project_type               
                        })
        if  self.state in ('implement_project','ready'): 
            if vals.get('start_date') or vals.get('end_date'):
                if  not self.env.user.has_group('nomin_base.group_business_development_manager'):
                    raise UserError(_(u'БХХ Менежер огноог засах боломжтой'))
                

            
        
        return result  

    @api.multi
    def _get_type_common(self):
        ids = self.env['project.task.type'].search([('case_default','=',1)])
        return ids
     
    _defaults = {
        #'created_user_id':lambda obj,cr,uid,c={}:uid,
        'state' : 'draft',
        'type_ids': _get_type_common,
    }

    @api.multi
    def unlink(self):
        '''
           Төсөл  устгах
        '''
        for proj in self:
            if proj.created_user_id.id != self.env.user.id:
                raise UserError(_(u'Төслийг үүсгэсэн хэрэглэгч устгах хэрэгтэй'))
            if proj.state != 'draft':
                raise UserError(_(u'Ноорог төлөвтөй төсөл устах боломжтой'))
        res = super(ProjectProject, self).unlink()
        return res
    
    @api.model
    def _project_alarm_cron(self):
        user_emails = []
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        action_id = self.env['ir.model.data'].get_object_reference('project', 'action_view_task')[1]
        #  Хяналтын огнооны өмнөх өдөр майл явуулах
        query = """select id from project_task where id in (
                            select B.id  from project_project A inner join project_task B ON B.project_id = A.id 
                            where A.state in ('draft','request','comfirm','project_started') and B.task_state in ('t_new','t_cheapen','t_cheapened','t_user','t_start')  
                                and B.date_deadline between A.start_date and A.check_date_start and (A.check_date_start + INTERVAL '-1 day') = Date(now()) 
                                and  A.check_date_start is not null and B.date_deadline is not null and  A.start_date is not null)
                        or id in (
                            select B.id  from project_project A inner join project_task B ON B.project_id = A.id 
                            where A.state in ('draft','request','comfirm','project_started') and B.task_state in ('t_new','t_cheapen','t_cheapened','t_user','t_start')  
                                and B.date_deadline between A.start_date and A.check_date_end and (A.check_date_end + INTERVAL '-1 day') = Date(now()) 
                                and  A.check_date_end is not null and B.date_deadline is not null and  A.start_date is not null)
        """
        self.env.cr.execute(query)
        task_ids =  self.env.cr.fetchall()

        for task_id in task_ids: 
            db_name = request.session.db
            task = self.env['project.task'].browse(task_id)
            if task.user_id.login:
                check_date ='огноо1'
                if task.date_deadline > task.project_id.start_date and task.project_id.check_date_end > task.date_deadline:
                    check_date ='огноо2'
                body_html = u'''
                                <h4>Сайн байна уу? </h4>
                                <p><li>  Маргааш "%s" төслийн хяналтын %s болж буй тул та хариуцсан даалгавраа дуусгана уу. </li></p>
                                <p><li>Эсвэл тайлбар бичин даалгаврын дуусах хугацааг сунгах боломжтой.</li></p>
                                <br>
                                <p><li><b>Даалгавар: <a href=%s/web?db=%s#id=%s&view_type=form&model=project.task&action=%s>%s</a></b></li></p>
                                <p><li><b>Хэлтэс:</b> %s</li></p>
                                <br>
                                <p><li>Энэхүү мэйл нь ERP системээс автоматаар илгээгдэж байгаа болно.</li></p>
                            '''%(task.project_id.name,check_date,base_url,db_name,task.id,action_id,task.name,task.department_id.name)
                email_template = self.env['mail.mail'].create({
                    'name': _('Followup '),
                    'email_from': self.env.user.company_id.email or '',
                    'model_id': self.env['ir.model'].search([('model', '=', 'project.project')]).id,                    
                    'lang': self.env.user.lang,
                    'auto_delete': True,                    
                })
                subject = u'Хариуцсан даалгавраа дуусгах төлөвт оруулна уу.'
                email_template.write({'body_html':body_html,'subject':subject,'email_to':task.user_id.login})
                email_template.send()
        #  Хяналтын огнооны өдөр майл явуулах
        query = """select A.id as project_id, B.id as task_id,B.name as task_name, B.task_date_start as task_date_start , B.date_deadline as date_deadline ,B.done_date as done_date ,
                        A.start_date as project_start_date , A.check_date_end as project_check_date_end , A.check_date_start as project_check_date_start , C.name as department_name,
                        D.name as project_name , F.work_email as work_email
                        from project_project A 
                            inner join project_task B ON A.id = B.project_id
                            left join hr_department C ON A.department_id = C.id
                            left join account_analytic_account D ON D.id = A.analytic_account_id
							left join project_project_project_hr_employee_ref E ON E.project_id_ids = A.id 
							inner join hr_employee F ON F.id= E.employ_id
                            left join hr_employee ON F.id = A.project_verifier
                            where B.id in (
                                select B.id from project_project A inner join project_task B ON B.project_id = A.id 
                                    where A.state in ('draft','request','comfirm','project_started') and B.task_state  not in ('t_new','t_cheapen','t_cheapened','t_user','t_start')  
                                    and B.done_date between A.start_date and A.check_date_start and A.check_date_start = DATE(now())
                                    and  A.check_date_start is not null and B.done_date is not null and  A.start_date is not null)
                            or B.id in (
                                select B.id  from project_project A inner join project_task B ON B.project_id = A.id 
                                    where A.state in ('draft','request','comfirm','project_started') and B.task_state not in ('t_new','t_cheapen','t_cheapened','t_user','t_start')  
                                    and B.done_date between A.check_date_start and A.check_date_end and A.check_date_end = DATE(now()) 
                                    and  A.check_date_end is not null and A.check_date_start is not null and B.done_date is not null)

        """
        self.env.cr.execute(query)
        dictfetchall =  self.env.cr.dictfetchall()

        projects = {}
        for dic in dictfetchall:
            group = dic['project_id']
            if group not in projects:
                projects[group] ={
                        'project_id':u'Тодорхойгүй',
                        'project_name':u'Тодорхойгүй',
                        'project_start_date':u'Тодорхойгүй',
                        'project_check_date_end':u'Тодорхойгүй',
                        'project_check_date_start':u'Тодорхойгүй',
                        'department_name':u'Тодорхойгүй',
						'task_ids' :{},
                        'email_to':{}
					}
            
            projects[group]['project_id'] = group
            projects[group]['project_name'] = dic['project_name']
            projects[group]['project_start_date'] = dic['project_start_date']
            projects[group]['project_check_date_end'] = dic['project_check_date_end']
            projects[group]['project_check_date_start'] = dic['project_check_date_start']
            projects[group]['department_name'] = dic['department_name']

            group1 = dic['task_id']
            if group1 not in projects[group]['task_ids']:
                projects[group]['task_ids'][group1] ={
                    'task_id' :u'Тодорхойгүй',
                    'task_name' :u'Тодорхойгүй',
                    'task_date_start' :u'Тодорхойгүй',
                    'date_deadline' :u'Тодорхойгүй',
                    'done_date' :u'Тодорхойгүй',				
                }
            projects[group]['task_ids'][group1]['task_name'] = group1
            projects[group]['task_ids'][group1]['task_name'] = dic['task_name']
            projects[group]['task_ids'][group1]['task_date_start'] = dic['task_date_start']
            projects[group]['task_ids'][group1]['date_deadline'] = dic['date_deadline']
            projects[group]['task_ids'][group1]['done_date'] = dic['done_date']

            group2 = dic['work_email']
            if group2 not in projects[group]['email_to']:
                projects[group]['email_to'][group2] = {
                    'work_email':u'Тодорхойгүй'
                }

            projects[group]['email_to'][group2]['work_email'] = group2
                    
        for project in projects.values():
            db_name = request.session.db
            count = 1           
            tasks = ""
            for task_name in sorted(project['task_ids'].values() , key = itemgetter('task_date_start')):
                start_date = project['project_start_date']
                check_date = project['project_check_date_start']
                if task_name['done_date'] > project['project_check_date_start'] and project['project_check_date_end'] >= task_name['done_date']:
                    check_date = project['project_check_date_end']
                    start_date = project['project_check_date_start']
                tasks =tasks+"<p><li>%s) %s. %s - %s</li></p>"%(count,task_name['task_name'],task_name['task_date_start'],task_name['date_deadline'])
                count+=1            
            body_html = u'''
                            <h4>Сайн байна уу? </h4>
                            <br>
                            <p><li>  Таньд  төслийн явцын мэдээллийг хүргэж байна. </li></p>
                            <br>
                            <p><li>  <b>Төслийн нэр:</b> %s </li></p>
                            <p><li>  <b>Хэлтэс:</b> %s </li></p>
                            <p><li>  <b>Тайлант хугацаа:</b> %s - %s </li></p>
                            <p><li>  <b>Тайлант хугацаанд хийгдсэн ажлууд:</b> </li></p>
                            %s
                            <br>
                            <p><li> Энэхүү мэйл нь ERP системээс автоматаар илгээгдэж байгаа болно.<li></p>
                        '''%(project['project_name'],project['department_name'],start_date,check_date,tasks)
            for mail_to in project['email_to'].values():
                email_template = self.env['mail.mail'].create({
                    'name': _('Followup '),
                    'email_from': self.env.user.company_id.email or '',
                    'model_id': self.env['ir.model'].search([('model', '=', 'project.project')]).id,
                    'subject': 'Төслийн явцын мэдээлэл.',
                    'email_to': mail_to['work_email'],
                    'lang': self.env.user.lang,
                    'auto_delete': True,
                    'body_html':body_html,
                })               
                email_template.send()



class control_budget(models.Model):
    '''
        Хяналтын төсөв
    '''
    _name = 'control.budget'
    _description = 'Control budget'
    _inherit = ['mail.thread']
    
    #================================================================
    '''
       зардлуудын ний дүн тооцох
    '''
    @api.one
    @api.depends('material_line_ids.product_uom_qty', 'material_line_ids.price_unit')
    def _amount_material(self):
        material = 0.0
        for obj in self:
            for line in obj.material_line_ids:
                material += line.product_uom_qty * line.price_unit
            obj.material_cost = material
    
    @api.one
    @api.depends('carriage_line_ids.price')    
    def _amount_carriage(self):
        carriage = 0.0
        for obj in self:
            for line in obj.carriage_line_ids:
                carriage += line.price

            obj.carriage_cost = carriage   
    
    @api.one
    @api.depends('equipment_line_ids.product_uom_qty','equipment_line_ids.price_unit')      
    def _amount_equipment(self):
        equipment = 0.0
        for obj in self:
            for line in obj.equipment_line_ids:
                equipment += line.product_uom_qty * line.price_unit
            obj.equipment_cost = equipment 
        
    @api.one
    @api.depends('labor_line_ids.labor_cost_basic')      
    def _amount_labor(self):
        labor = 0.0
        for obj in self:
            for line in obj.labor_line_ids:
                    labor += line.labor_cost_basic
            obj.labor_cost = labor
    @api.one
    @api.depends('postage_line_ids.price')      
    def _amount_postage(self):
        res = {}
        postage = 0.0
        for obj in self:    
            for line in obj.postage_line_ids:
                        postage += line.price
            obj.postage_cost = postage
    @api.one
    @api.depends('other_cost_line_ids.price')          
    def _amount_other(self):
        res = {}
        other = 0.0
        for obj in self:
            for line in obj.other_cost_line_ids:
                other += line.price
            obj.other_cost = other
    
    @api.one
    @api.depends('labor_line_ids.engineer_salary')      
    def _total_engineer_salary(self):
        engineer_salary = 0.0
        for obj in self:
            for line in obj.labor_line_ids:
                    engineer_salary += line.engineer_salary
            obj.total_engineer_salary = engineer_salary

    @api.one
    @api.depends('labor_line_ids.extra_salary','labor_line_ids.product_uom_qty','labor_line_ids.price_unit')      
    def _total_extra_salary(self):
        extra_salary = 0.0
        for obj in self:
            for line in obj.labor_line_ids:
                    extra_salary += line.extra_salary
            obj.total_extra_salary = extra_salary

    @api.one
    @api.depends('labor_line_ids.social_insurance')      
    def _total_social_insurance(self):
        social_insurance = 0.0
        for obj in self:
            for line in obj.labor_line_ids:
                    social_insurance += line.social_insurance
            obj.total_social_insurance = social_insurance

    @api.one
    @api.depends('labor_line_ids.habe')      
    def _total_HABE(self):
        habe = 0.0
        for obj in self:
            for line in obj.labor_line_ids:
                    habe += line.habe
            obj.total_habe = habe
    
    @api.one
    @api.depends('labor_line_ids.total_salary')      
    def _amount_salary(self):
        salary = 0.0
        for obj in self:
            for line in obj.labor_line_ids:
                    salary += line.total_salary
            obj.total_salary = salary
    
    @api.one
    @api.depends('labor_line_ids.product_uom_qty','labor_line_ids.price_unit')      
    def _total_labor_cost(self):
        labor = 0.0
        for obj in self:
            for line in obj.labor_line_ids:
                    labor += line.product_uom_qty * line.price_unit
            obj.total_labor_cost = labor

    @api.one  
    def _amount_total(self):
        for obj in self:
            amount = obj.material_cost + obj.labor_cost + obj.carriage_cost + obj.equipment_cost + obj.postage_cost + obj.other_cost 
            obj.sub_total = amount
            
    @api.one  
    def _amount_total_balance(self):
        amount = 0.0
        util = 0.0
        balance = 0.0
        for obj in self:
            amount = obj.material_cost + obj.labor_cost + obj.carriage_cost + obj.equipment_cost + obj.postage_cost + obj.other_cost
            for material_line in obj.utilization_budget_material:
                util += material_line.price
            for labor_line in obj.utilization_budget_labor:
                util += labor_line.price
            for equipment_line in obj.utilization_budget_equipment:
                util += equipment_line.price
            for carriage_line in obj.utilization_budget_carriage:
                util += carriage_line.price
            for postage_line in obj.utilization_budget_postage:
                util += postage_line.price
            for other_line in obj.utilization_budget_other:
                util += other_line.price
            balance = amount - util
            obj.total_balance = balance

    #================================================================
    @api.multi
    def _step_is_final(self):
#         workflow_obj = self.pool.get('hr.expense.workflow')
        workflow_line_obj = self.env['confirm.workflow.transition']
        for budget in self:
            final = False
            ids = workflow_line_obj.search([('parent_id','=',self.ids)] )
            if budget.state == 'confirm' and budget.check_sequence and ids[0]:
                next_transitions = workflow_line_obj.search([('parent_id','=',ids[0]),
                                                                      ('sequence','>',budget.check_sequence)])
                if not next_transitions:
                    final = True
            budget.step_is_final = final
    
    @api.multi
    def _show_rating_button_user(self):
        emp_obj = self.env['hr.employee']
        #user = self.env['res.users'].browse(['user_id'])
        employees = emp_obj.search([('user_id','=',self.env.user.id)])
        for obj in self:
            if not employees:
                show_confirm = False
            else:
                show_confirm = False
                if employees[-1] in obj.budget_verifier.ids:
                    show_confirm = True
                if obj.state != 'evaluate':
                    show_confirm = False
                for users in obj.evaluate_budget:
                    if employees[0] == users.user_id.id:
                        show_confirm = False
            obj.show_rating_button_user = show_confirm
    
    @api.one
    def _is_budget_confirmer(self):
        '''
           Батлах хэрэглэгч мөн эсэх тооцох
        '''
        emp_obj = self.env['hr.employee']
        employees = emp_obj.sudo().search([('user_id','=',self.env.user.id)])
        for obj in self:      
            if not employees:
                show_confirm = False
            else:
                show_confirm = False
                if employees.ids[0] in obj.budget_confirmer.ids:
                    show_confirm = True
            
            obj.is_budget_confirmer = show_confirm

    @api.one
    def _show_confirm_button_user(self):
        '''
           Батлах хэрэглэгчид харуулах эсэх тооцох
        '''
        emp_obj = self.env['hr.employee']
        employees = emp_obj.sudo().search([('user_id','=',self.env.user.id)])
        for obj in self:
            if not employees:
                show_confirm = False
            else:
                show_confirm = False
                if employees.ids[0] in self.budget_confirmer.ids:
                    show_confirm = True
                if self.state != 'confirm':
                    show_confirm = False
                for users in obj.budget_users:
                        if employees.ids[0] == users.confirmer.id and users.role == 'budget_confirmer':   
                            show_confirm = False 
            obj.show_confirm_button_user = show_confirm
    
    @api.one
    def _is_show_confirmed(self):
        '''
           батлаж дууссан эсэх
        '''
        count = 0
        for obj in self:
            confirmed = False
            for confirmer in obj.budget_confirmer:
                for line in obj.budget_users:
                    if confirmer == line.confirmer and line.role == 'budget_confirmer':
                        count += 1
            if count == len(obj.budget_confirmer):
                confirmed = True
            obj.is_show_confirmed = confirmed

    @api.multi
    def _is_show_evaluate(self):
        count = 0
        for obj in self:
            evaluated = False
            for confirmer in obj.budget_verifier:
                for line in obj.evaluate_budget:
                    if confirmer == line.user_id:
                        count += 1
            if count == len(obj.budget_verifier):
                evaluated = True
            obj.is_show_evaluate = evaluated


    state=fields.Selection([('draft',u'Шинэ'),
                                                          ('start',u'Эхэлсэн'),
                                                          ('confirm',u'Батлах'),
                                                          ('done',u'Батлагдсан'),
                                                          ('close',u'Хаагдсан'),
                                                          ('cancel',u'Цуцлагдсан'),
                                                          ('after',u'Хойшлуулсан')],
                                                         'Status',readonly=True, default='draft',track_visibility='onchange')
    main_id=fields.Many2one('main.specification','Project', index=True)
    project_id=fields.Many2one('project.project','Project', required = True,domain="[('state', 'in',('comfirm','project_started')),('state_comfirm','=',True)]", track_visibility='onchange', index=True) # Төсөл
    user_id=fields.Many2one('res.users', 'Budgeter',required = True, track_visibility='onchange', default=lambda self: self.env.user.id ) # Төсөвчин
    task_id=fields.Many2one('project.task', 'Work Task' ,required = True, track_visibility='onchange', index=True)
    name=fields.Char('Name', required = True) # Хяналтын төсвийн нэр
    budget_code=fields.Char('Code', required = True,readonly=True, default='New')
    res_model=fields.Char('Resource Model', readonly=True)
    budget_verifier=fields.Many2many('hr.employee','project_control_budget_hr_employee_ref','budget_id_id','employee_id',string='Verifier')
    budget_confirmer=fields.Many2many('hr.employee','project_control_budget_budget_hr_employee_ref_ref','budget_id_ids','empl_id',string='Confirmer',required = True)
    check_users=fields.Many2many('res.users', string= 'Checkers', readonly=True, copy=False)
    required_cost=fields.Integer("Required Cost")# Нийт хяналтын төсөв
    date=fields.Date('Budget date', required = True, track_visibility='onchange') # Огноо
    confirm_date=fields.Date('Confirm date', track_visibility='onchange') # Баталсан Огноо
    res_id=fields.Integer('Resource ID', readonly=True)
    
    material_cost=fields.Float(compute='_amount_material',string='Material Cost',type='float') # Бараа материалын зардал
    
    labor_cost=fields.Float(compute=_amount_labor, string='Labor Cost',type='float',digits_compute=dp.get_precision('Account')) #  Ажиллах хүчний зардал
    carriage_cost=fields.Float(compute=_amount_carriage, string='Carriage Cost',digits_compute=dp.get_precision('Account')) # Тээврийн зардал
    equipment_cost=fields.Float(compute=_amount_equipment, string='Equipment Cost',digits_compute=dp.get_precision('Account')) # Машин механизмын зардал,
    postage_cost=fields.Float(compute=_amount_postage,string='Postage Cost',digits_compute=dp.get_precision('Account')) # Шууд зардал
    other_cost=fields.Float(compute=_amount_other,string='Other Cost')# Бусад зардал
    sub_total=fields.Float(compute=_amount_total, digits_compute=dp.get_precision('Account'), string='Sub Total', track_visibility='onchange')
    total_balance=fields.Float(compute=_amount_total_balance, digits_compute=dp.get_precision('Account'), string='Total Balance', track_visibility='onchange')
    check_sequence=fields.Integer('Workflow Step', copy=False, default=0)
    step_is_final=fields.Boolean(compute=_step_is_final, type='boolean', string='Is this accountant step?', store=False)
    show_confirm_button_user=fields.Boolean(compute=_show_confirm_button_user,string = 'show button',type='boolean')
    show_rating_button_user=fields.Boolean(compute=_show_rating_button_user,string = 'show button',type='boolean')
    is_budget_confirmer=fields.Boolean(compute=_is_budget_confirmer,string = 'show button')
    is_show_confirmed=fields.Boolean(compute=_is_show_confirmed, string = 'confirmed',type='boolean' )
    is_show_evaluate=fields.Boolean(compute=_is_show_evaluate, string = 'evaluated',type='boolean' )

    total_engineer_salary= fields.Float(compute=_total_engineer_salary, string="Нийт инженер техникийн ажилчдын цалин")
    total_extra_salary = fields.Float(compute=_total_extra_salary, string="Нийт нэмэгдэл цалин")
    total_social_insurance = fields.Float(compute=_total_social_insurance, string="Нийт нийгмийн даатгал")
    total_habe = fields.Float(compute=_total_HABE, string="Нийт ХАБЭ")
    total_salary = fields.Float(compute=_amount_salary, string="Нийт цалин")
    total_labor_cost=fields.Float(compute=_total_labor_cost, string='Нийт Үндсэн цалин',type='float',digits_compute=dp.get_precision('Account')) #  Ажиллах хүчний зардал

    @api.multi
    def send(self):
        workflow_obj = self.env['confirm.workflow.transition']
        user_obj = self.env['res.users']
        for budget in self:
            next_user_ids = workflow_obj.assign_to_next(budget)
        if next_user_ids:
                self.message_subscribe_users([budget.id], user_ids=next_user_ids)
                next_user_names = u', '.join(map(lambda x:x.name, user_obj.browse(next_user_ids)))
                self.message_post([budget.id], body=u'Хүсэлт ажлын урсгалаар илгээгдлээ. Дараагийн шатанд хянагч:%s'%next_user_names)
                      
        return self.write({'state': 'confirm', 'date_confirm': time.strftime('%Y-%m-%d')})

    @api.multi
    def action_confirm(self):
        workflow_obj = self.env['confirm.workflow.transition']
        user_obj = self.env['res.users']
        action_confirm = self.env['res.users'].browse(self.env.user.id)
        for budget in self:
                self.log_to_history(budget, 'confirm')
                next_user_ids, activity = workflow_obj.assign_to_next(budget)

        if next_user_ids:
                self.message_subscribe_users([budget.id], user_ids=next_user_ids)
                next_user_names = u', '.join(map(lambda x:x.name, user_obj.browse(next_user_ids)))
                expense.message_post(body=u'%s зөвшөөрөв. Ажлын урсгалын дараагийн шатанд илгээгдлээ. Дараагийн шатанд хянагч:%s' \
                                       %( validator, next_user_names))
                for nuid in next_user_ids:
                    self.log_to_history(nuid, budget, activity, 'pending')
        else:
                # Захиалгыг зөвшөөрөх шатууд явагдаж дууссан.
                budget.write({'check_users':[],'check_sequence':0})
                budget.signal_workflow('validate')
                budget = self.browse(budget.id)
                self.message_post([budget.id], 
                        _('Expense request has been approved and payeble account entry generated with %s number.') % \
                                      expense.account_move_id.name_get()[0][1])

    @api.multi
    def log_to_history(self,parent,action):
        history_obj = self.env['confirm.workflow.history']
        todo_delete = []
        existing_pending = history_obj.search([('parent_id', '=', parent.id),
                                                        ('action','=','pending'),
                                                        ('user_id','=',uid)])
        if existing_pending:
            history_obj.write(existing_pending[0], {
                                'action':action,
                                'date':time.strftime('%Y-%m-%d %H:%M:%S')})
            
            if len(existing_pending) > 1:
                todo_delete += existing_pending[1:]
        else:
            history_obj.create({
                    'parent_id': parent.id,
                    'action':action,
                    'user_id':uid,
#                     'name':activity,
                    'date':time.strftime('%Y-%m-%d %H:%M:%S'),
            })
        
        todo_delete += history_obj.search([('parent_id','=',parent.id),
                                ('action','=','pending')])
        if action <> 'pending' and todo_delete:
            history_obj.unlink(todo_delete)
        return True

class CarriageBudgetLine(models.Model):
    _name = 'carriage.budget.line'
    '''
       Тээврийн зардал
    '''

    name            =fields.Char('Name',required = True)
    parent_id       =fields.Many2one('control.budget', 'Control budget', index=True)
    main_id         =fields.Many2one('main.specification','Project', index=True)
    department_id   =fields.Many2one('hr.department',u'Зардал гарах салбар',required = True,domain=[('is_sector', '=',True)])
    price           =fields.Float(string = 'Estimated price',required = True)
                

class MaterialBudgetLine(models.Model):
    '''
        Бараа материалын зардал
    '''
    _name = 'material.budget.line'
    _description = 'Material budget line'
    
    @api.model
    def _amount(self):
        for obj in self:
            obj.material_total = obj.product_uom_qty * obj.price_unit
        # print'___________PP________',self.ids
        # if not self.ids:
        #     return {}
        # self._cr.execute("SELECT l.id,COALESCE(SUM(l.price_unit*l.product_uom_qty),0) AS amount FROM material_budget_line l WHERE id IN %s GROUP BY l.id ",(tuple(self.ids),))
        # res = dict(self._cr.fetchall())
        # return res
    
    state=fields.Selection([('draft',u'Шинэ'),
                            ('confirm',u'Батлагдсан'),
                            ('request',u'Батлах'),
                            ('purchase',u'Худалдан авалтын шаардах үүссэн'),
                            ('tender',u'Тендер үүссэн'),
                            ('comparison',u'Үнийн харьцуулалт үүссэн'),
                            ('order',u'Худалдан авалтын захиалга үүссэн'),],
                            'Status',readonly=True,default='draft')
    cost_choose=fields.Boolean('Choose',default=False) # Захиалга өгөх чагтлах талбар
    department_id=fields.Many2one('hr.department',u'Зардал гарах салбар',required = False,domain=[('is_sector', '=',True)])
    name=fields.Char('Name')
    tender_id=fields.Many2one('create.project.tender',string='tender', index=True)
    purchase_id=fields.Many2one('create.purchase.requisition',string='purchase', index=True)
    parent_id=fields.Many2one('control.budget', string='Control budget', index=True)
    main_id=fields.Many2one('main.specification',string='Project', index=True)
    product_id=fields.Many2one('product.product', string='Product',required = False, domain=[('product_tmpl_id.is_new','=',True),('product_tmpl_id.cost_price','>',0)])
    product_uom=fields.Many2one('product.uom',string='Unit of Measure',required = False)
    product_uom_qty=fields.Float(string = 'Estimated Quantity',required = False,default=1)
    price_unit=fields.Float(string = 'Estimated price',required = False)
    material_total=fields.Float(compute=_amount, digits_compute=dp.get_precision('Account'), string='Total', type='float', help="The material amount.")
    product_name = fields.Char(string = 'Барааны нэр')

    @api.onchange('product_id')
    def onchange_product(self):
        
        if self.product_id:            
            self.update({'product_uom':  self.product_id.uom_id, 'price_unit': self.product_id.cost_price})

    @api.onchange('price_unit','product_uom_qty')
    def onchange_amount(self):
       float = 0.0
       if self.price_unit and self.product_uom_qty:
           float = self.price_unit * self.product_uom_qty
           self.material_total = float
    
    @api.model
    def create(self,vals):
        if vals.get('cost_choose'):
            if vals.get('cost_choose')==True:
                vals.update({'cost_choose':False})
        if vals and 'parent_id' in vals:
            if vals['parent_id'] != False:
                budget = self.env['control.budget'].browse(vals['parent_id'])
                if budget.state not in ('draft','user','start'):
                    raise UserError(_(u'Энэ үед материалын зардлын мөр нэмэх боломжгүй'))
        main = super(MaterialBudgetLine, self).create(vals)
        return main

    
    @api.multi
    def unlink(self):
        for obj in self:
            if obj.parent_id.state not in ('draft','user','start'):
                raise UserError(_(u'Энэ үед материалын зардлын мөр устгах боломжгүй!!!!'))
        return super(MaterialBudgetLine, self).unlink()
    
class LaborBudgetLine(models.Model):
    '''
        Ажиллах хүчний зардал
    '''
    _name = 'labor.budget.line'
    _description = 'Labor budget line'
    
    @api.model
    def _amount(self):
        for obj in self:
            obj.labor_total = obj.product_uom_qty * obj.price_unit

    @api.model
    @api.depends('product_name','product_id','price_unit','product_uom_qty')
    def _set_engineer_salary(self):
        for obj in self:
            if not obj.engineer_salary_percent:
                settings = self.env['labor.cost.settings'].search([(1,'=',1)])
                obj.engineer_salary_percent = settings.engineer_salary

    @api.model
    def _engineer_salary(self):
        for obj in self:            
            obj.engineer_salary = obj.labor_total * obj.engineer_salary_percent / 100
    
    @api.model
    @api.depends('product_name','product_id','price_unit','product_uom_qty')
    def _set_extra_salary(self):
        for obj in self:
            if not obj.extra_salary:
                settings = self.env['labor.cost.settings'].search([(1,'=',1)])
                obj.extra_salary_percent = settings.extra_salary

    @api.model
    @api.depends('product_name','product_id','price_unit','product_uom_qty')
    def _extra_salary(self):
        for obj in self:
            obj.extra_salary = obj.labor_total * obj.extra_salary_percent / 100

    @api.model
    def _total_salary(self):
        for obj in self:
            obj.total_salary = obj.labor_total + obj.engineer_salary + obj.extra_salary
            
    @api.model
    @api.depends('product_name','product_id','price_unit','product_uom_qty')
    def _set_social_insurance_rate(self):
        for obj in self:
            if not obj.social_insurance_rate:
                settings = self.env['labor.cost.settings'].search([(1,'=',1)])
                obj.social_insurance_rate = settings.social_insurance_rate

    @api.model
    def _social_insurance(self):
        for obj in self:
            obj.social_insurance = obj.total_salary * obj.social_insurance_rate / 100
    
    
    @api.model
    @api.depends('product_name','product_id','price_unit','product_uom_qty')
    def _set_HABE(self):
        for obj in self:
            if not obj.habe_percent:
                settings = self.env['labor.cost.settings'].search([(1,'=',1)])
                obj.habe_percent = settings.habe_percent

    @api.model
    def _HABE(self):
        for obj in self:
            obj.habe = obj.total_salary * obj.habe_percent / 100

    @api.model
    def _labor_cost_basic(self):
        for obj in self:
            obj.labor_cost_basic = obj.total_salary + obj.social_insurance + obj.habe

    state=fields.Selection([('draft',u'Шинэ'),
                                                      ('request',u'Батлах'),
                                                      ('confirm',u'Батлагдсан'),
                                                      ('purchase',u'Худалдан авалтын шаардах үүссэн'),
                                                      ('tender',u'Тендер үүссэн'),
                                                      ('comparison',u'Үнийн харьцуулалт үүссэн'),
                                                      ('order',u'Худалдан авалтын захиалга үүссэн'),],
                                                     'Status',readonly=True,default='draft')
    cost_choose=fields.Boolean('Choose',default=False) # Захиалга өгөх чагтлах талбар
    name=fields.Char(string = 'description')
    purchase_id=fields.Many2one('create.purchase.requisition','purchase', index=True)
    tender_id=fields.Many2one('create.project.tender','tender', index=True)
    # partner_comparison_labor_id = fields.Many2one('create.partner.comparison.wizard', index=True)
    department_id=fields.Many2one('hr.department',u'Зардал гарах салбар',required = True,domain=[('is_sector', '=',True)])
    parent_id=fields.Many2one('control.budget', 'Control budget', index=True)
    main_id=fields.Many2one('main.specification','Project', index=True)
    product_uom=fields.Many2one('product.uom', string='Unit of Measure')
    product_id=fields.Many2one('product.product',string = 'Names',domain=[('product_tmpl_id.is_new','=',True),('product_tmpl_id.cost_price','>',0)])
    product_name=fields.Char(string = 'Names' )
    product_uom_qty=fields.Float(string = 'Estimated Quantity',required = False, default=1)
    price_unit=fields.Float(string = 'Estimated price',required = True)
    labor_total=fields.Float(compute=_amount, digits_compute=dp.get_precision('Account'), string='Total', type='float', help="The material amount.")
    engineer_salary= fields.Float(compute=_engineer_salary, string="Инженер техникийн ажилчдын цалин")
    extra_salary = fields.Float(compute=_extra_salary, string="Нэмэгдэл цалин")
    social_insurance = fields.Float(compute=_social_insurance, string="Нийгмийн даатгал")
    habe = fields.Float(compute=_HABE, string="ХАБЭ")
    total_salary = fields.Float(compute=_total_salary, string="Нийт цалин")
    labor_cost_basic = fields.Float(compute=_labor_cost_basic, string="Ажиллах хүчний зардал")
    
    engineer_salary_percent = fields.Float(string="Инженер техникийн ажилчдын цалингийн хувь", compute=_set_engineer_salary ,store=True)
    extra_salary_percent = fields.Float(string="Нэмэгдэл цалингийн хувь" , compute=_set_extra_salary ,store=True)
    social_insurance_rate = fields.Float(string="Нийгмийн даатгалын хувь", compute=_set_social_insurance_rate ,store=True)
    habe_percent = fields.Float(string="ХАБЭ хувь", compute=_set_HABE ,store=True)

    # @api.onchange('product_id')
    # def onchange_product(self):
    #     if self.product_id:
    #         #prod = self.env['product.product'].browse(self.product_id.id)
    #         self.product_uom = self.product_id.uom_id
    #         self.price_unit = self.product_id.standard_price
            #self.update({'product_uom':  prod.uom_id, 'price_unit': prod.standard_price})
    
    @api.onchange('price_unit','product_uom_qty')
    def onchange_amount(self):
        float = 0.0
        if self.price_unit and self.product_uom_qty:
            float = self.price_unit * self.product_uom_qty
            self.labor_total = float

    @api.model
    def create(self,vals):
        if vals.get('cost_choose'):
            if vals.get('cost_choose')==True:
                vals.update({'cost_choose':False})
        if vals and 'parent_id' in vals:
            if vals['parent_id'] != False:
                budget = self.env['control.budget'].browse(vals['parent_id'])
                if budget.state not in ('draft','user','start'):
                    raise UserError(_(u'Энэ үед ажиллах хүчний зардлын мөр нэмэх боломжгүй'))
        main = super(LaborBudgetLine, self).create(vals)
        return main
    
    @api.multi
    def unlink(self):

        for obj in self:
            if obj.parent_id.state not in ('draft','user','start'):
                raise UserError(_(u'Энэ үед ажиллах хүчний зардлын мөр устгах боломжгүй!!!!'))
        return super(LaborBudgetLine, self).unlink()
    
class EquipmentBudgetLine(models.Model):
    '''
        Машин механизмын зардал
    '''
    _name = 'equipment.budget.line'
    _description = 'Equipment budget line'
    
    @api.model
    def _amount(self):
        for obj in self:
            obj.equipment_total = obj.product_uom_qty * obj.price_unit


    state=fields.Selection([('draft',u'Шинэ'),
                                                      ('request',u'Батлах'),
                                                      ('confirm',u'Батлагдсан'),
                                                      ('purchase',u'Худалдан авалтын шаардах үүссэн'),
                                                      ('tender',u'Тендер үүссэн'),
                                                      ('order',u'Худалдан авалтын захиалга үүссэн'),],
                                                     'Status',readonly=True,default='draft')
    cost_choose=fields.Boolean('Choose') # Захиалга өгөх чагтлах талбар
    department_id=fields.Many2one('hr.department',u'Зардал гарах салбар',required = True,domain=[('is_sector', '=',True)])
    name=fields.Char('Name',required = True)
    parent_id=fields.Many2one('control.budget', 'Control budget', index=True)
    main_id=fields.Many2one('main.specification','Project', index=True)
    product_uom=fields.Many2one('product.uom','Unit of Measure')
    product_uom_qty=fields.Float(string = 'Estimated Quantity',required = True, default=1)
    price_unit=fields.Float(string = 'Estimated price',required = True)
    equipment_total=fields.Float(compute=_amount, digits_compute=dp.get_precision('Account'), string='Total', type='float', help="The material amount.")
    

    @api.onchange('price_unit','product_uom_qty')
    def onchange_amount(self):
        float = 0.0
        if self.price_unit and self.product_uom_qty:
            float = self.price_unit * self.product_uom_qty
            self.equipment_total = float

    @api.model
    def create(self,vals):
        if vals and 'parent_id' in vals:
            if vals['parent_id'] != False:
                budget = self.env['control.budget'].browse(vals['parent_id'])
                if budget.state not in ('draft','user','start'):
                    raise UserError(_(u'Энэ үед машин механизмын зардлын мөр нэмэх боломжгүй'))
        main = super(EquipmentBudgetLine, self).create(vals)
        return main

    @api.multi
    def unlink(self):
        for obj in self:
            if obj.parent_id.state not in ('draft','user','start'):
                raise UserError(_(u'Энэ үед машин механизмын зардлын мөр устгах боломжгүй!!!!'))
        return super(EquipmentBudgetLine, self).unlink()
    
class PostageBudgetLine(models.Model):
    '''
        Шууд зардал
    '''
    _name = 'postage.budget.line'
    _description = 'Postage budget line'

    name=fields.Char('Name',required = True)
    parent_id=fields.Many2one('control.budget', 'Control budget', index=True)
    main_id=fields.Many2one('main.specification','Project', index=True)
    department_id=fields.Many2one('hr.department',u'Зардал гарах салбар',required = True,domain=[('is_sector', '=',True)])
    price=fields.Float(string = 'Estimated price',required = True)
    
    @api.model
    def create(self,vals):
        if vals and 'parent_id' in vals:
            if vals['parent_id'] != False:
                budget = self.env['control.budget'].browse(vals['parent_id'])
                if budget.state not in ('draft','user','start'):
                    raise UserError(_(u'Энэ үед шууд зардлын мөр нэмэх боломжгүй'))
        main = super(PostageBudgetLine, self).create(vals)
        return main
    @api.multi
    def unlink(self):
        for obj in self:
            if obj.parent_id.state != 'draft':
                raise UserError(_(u'Энэ үед шууд зардлын мөр устгах боломжгүй'))
        return super(PostageBudgetLine, self).unlink()
    
class OtherCostBudgetLine(models.Model):
    '''
        Бусад зардал
    '''
    _name = 'other.cost.budget.line'
    _description = 'Other budget line'


    name=fields.Char('Name',required = True)
    parent_id=fields.Many2one('control.budget', 'Control budget', index=True)
    main_id=fields.Many2one('main.specification','Project', index=True)
    department_id=fields.Many2one('hr.department',u'Зардал гарах салбар',required = True,domain=[('is_sector', '=',True)])
    price=fields.Float(string = 'Estimated price',required = True)
    
    @api.model
    def create(self,vals):
        if vals and 'parent_id' in vals:
            if vals['parent_id'] != False:
                budget = self.env['control.budget'].browse(vals['parent_id'])
                if budget.state not in ('draft','user','start'):
                    raise UserError(_(u'Энэ үед бусад зардлын мөр нэмэх боломжгүй'))
        main = super(OtherCostBudgetLine, self).create(vals)
        return main
    
    @api.multi
    def unlink(self):
        for obj in self:
            if obj.parent_id.state not in ('draft','user','start'):
                raise UserError(_(u'Энэ үед бусад зардлын мөр устгах боломжгүй'))
        return super(OtherCostBudgetLine, self).unlink()
    
class ConfirmWorkflowTransition(models.Model):
    '''
        Хяналтын төсөв батлах ажлын урсгал
    '''
    _name = 'confirm.workflow.transition'
    _description = 'Confirm Workflow transition'
    
    _order = 'parent_id, sequence'

    sequence=fields.Integer('Sequence', required=True)
    parent_id=fields.Many2one('control.budget','Parent', index=True)
    company_id=fields.Many2one('res.company','Company')
    department_id=fields.Many2one('hr.department','Department')
    job_id=fields.Many2one('hr.job','Job')
    user_id=fields.Many2one('res.users', 'Confirm Employee')
    
    @api.multi
    def _default_sequence(self):
        seq = 0
        if context.get('transitions', False):
            transitions = context['transitions']
            for x in transitions:
                if not x[1] :
                    seq = max(x[2]['sequence'], seq)
                else :
                    seq = max(self.read(['sequence'])['sequence'], seq) 
        return seq + 1
    
    _defaults = {
        'sequence': _default_sequence,
        'state':'draft',
    }
    
    _sql_constraints = [
        ('sequence_nonzero', 'check(sequence > 0)', 'Sequence must be greater than zero!')
    ]
    def assign_to_next(self,budget):
        transition_obj = self.env['confirm.workflow.transition']
        employee_obj = self.env['hr.employee']
        next_steps = transition_obj.search([('parent_id','=',self.id),
                            ('sequence','>',budget.check_sequence)])
        next_users = []
        next_step = False
        user = self.env['res.users'].browse()
        employees = employee_obj.search([('user_id','=',user.id)])
        if not employees:
            raise UserError(_('Configuration Error!'))
            # raise osv.except_osv(_('Configuration Error!'), _('There is no employee defined for this user: %s(id=%s)') % (user.name, user.id))
        employee = employee_obj.browse(employees.id)
        for transition in transition_obj.browse(next_steps):
            if next_step and next_step < transition.sequence:
                break
            if transition.user_id and transition.user_id.active:
                next_users.append(transition.user_id.id)
                if not next_step:
                    next_step = transition.sequence
            
        if next_users:
            budget.write({'check_sequence':next_step,'check_users':[(6,0,next_users)]})
        return next_users
    
class TaskWorkDocument(models.Model):
    _name = 'task.work.document'
     
    @api.multi 
    def _invisible_botton(self):
        for obj in self:
            if obj.task_id.task_state == 't_confirm':
                obj.invisible_botton = True
            else:
                obj.invisible_botton = False
    
    task_id=fields.Many2one('project.task', 'Task', index=True)
    work_confirm_document=fields.One2many('ir.attachment','project_work_confirm_task_document',string='Document', required = False)
    is_confirmed=fields.Boolean('confirmed')
    invisible_botton=fields.Boolean(compute=_invisible_botton,string = 'show button',type='boolean')
    
    _defaults = {
                 'is_confirmed':False
                 }
    @api.multi
    def action_confirm(self):
        doc_ids = []
        for obj in self:
            for line in obj.task_id.work_document:
                if line.id not in doc_ids:
                    doc_ids.append(line.id)
            for line in obj.work_confirm_document:
                if line.id not in doc_ids:
                    doc_ids.append(line.id)
                    
            obj.task_id.work_document = [(6, 0, doc_ids)]
            obj.write({
                       'is_confirmed':True
                       })
            return { 'type': 'ir.actions.client', 'tag': 'reload', }
class ConfirmWorkflowHistory(models.Model):
    _name = 'confirm.workflow.history'
    _description = 'Budget Confirm Workflow History'
    _order = 'parent_id, date'
     
    parent_id=fields.Many2one('control.budget', 'Budget Request', index=True, readonly=True, ondelete='cascade')
    name=fields.Char('Verification Step', required=True, readonly=True)
    user_id=fields.Many2one('res.users', 'Validator', index=True, required=True, readonly=True)
    date=fields.Datetime('Date', required=True, readonly=True)
    action=fields.Selection([('pending','Pending'),('confirm','Confirmed')], 'Action', readonly=True)
    
class ProjectTask(models.Model):
    '''
        Төслийн даалгавар (Ажил)
    '''
    _inherit = 'project.task' 
    _description = 'Project task'
    
    @api.multi
    def control_budget_tree_view(self):
        """ open Control budget view """
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        res_id = ids and ids[0] or False
        project_task = self
        view_context = {
            'default_res_model': [self._name],
            'default_res_id': res_id,
        }
        help = _("""<p class="oe_view_nocontent_create">Record your control budget for the task '%s'.</p>""") % (project_task.name,)

        res = mod_obj.get_object_reference('nomin_project', 'action_control_budget')
        id = res and res[1] or False
        result = act_obj.read()[0]
        result['name'] = _('Control budget')
        result['context'] = view_context
        result['help'] = help
        return result
    

    name=fields.Char('Task Title', track_visibility='onchange', index=True, size=350, required=True, select=True)
    task_date_start=fields.Date('Starting Date', select=True, copy=False, track_visibility='onchange')
    company_id=fields.Many2one('res.company', 'Company')
    planned_hours=fields.Float('Initially Planned Hours', help='Estimated time to do the task, usually set by the project manager when the task is in draft state.', track_visibility='onchange')
    department_id=fields.Many2one('hr.department', 'Department', index=True,required = True, track_visibility='onchange')
    controller=fields.Many2many('hr.employee','project_task_controller_employee','project_task_id','employee_id','Controlled employee' , track_visibility='onchange')# Даалгавар хянагч
    task_type=fields.Selection([('normal',u'Энгийн'), # Энгийн ажил
                                                      ('tariff_task',u'Тарифт ажил'), # Тарифт ажил
                                                      ('work_graph',u'Ажлын зураг'),
                                                      ('work_task',u'Ажлын даалгавар'), # Худалдан авалтын ажил
                                                      ],
                                                     'Task type', required=True, copy=False, default='normal', track_visibility='onchange')
    rating_users=fields.Many2many('hr.employee','project_task_rating_employee_ref','project_task_id','emp_id',string='Rated employee', track_visibility='onchange')# Даалгавар үнэлэгчид
    task_verifier=fields.Many2one('hr.employee', string="Verifier", track_visibility='onchange')
    task_verifier_users=fields.Many2many('hr.employee','project_task_verify_employee','task_id','employee_id',string="Verifier",track_visibility='onchange')
    task_planed_date=fields.Date('Task Planed Date')
    document=fields.One2many('ir.attachment','project_task_document',string='Document', required = False)
    work_document=fields.One2many('ir.attachment','project_work_task_document',string='Confirmed Document', required = False)
    document_line=fields.One2many('task.work.document','task_id','Document line')
    
#     def write(self, cr, uid, ids, vals, context=None):
#         print 'WRITEEEEEE',vals
#         result = super(project_task, self).write(cr, uid, ids, vals, context=context)
#         return result
    _defaults = {
                 'user_id': False,
                 }
class MainSpecification(models.Model):
    _inherit = 'main.specification'
    

    control_budget_ids=fields.One2many('control.budget','main_id','Control Budgets')
    lines_budgets=fields.One2many('main.line.budgets','main_id',u'Төсөв')
    
    
class ControlBudget(models.Model):
    _inherit = 'control.budget'
    

    material_line_ids=fields.One2many('material.budget.line', 'parent_id', 'material_line_ids', copy=True)
    new_material_line_ids=fields.One2many('material.budget.line', 'parent_id', 'new_material_line_ids', copy=True)
    carriage_line_ids=fields.One2many('carriage.budget.line', 'parent_id', 'carriage_line_ids', copy=True)
    labor_line_ids=fields.One2many('labor.budget.line', 'parent_id', 'labor_line_ids', copy=True)
    labor_line_ids1=fields.One2many('labor.budget.line', 'parent_id', 'labor_line_ids1', copy=True)
    equipment_line_ids=fields.One2many('equipment.budget.line', 'parent_id', 'equipment_line_ids', copy=True)
    postage_line_ids=fields.One2many('postage.budget.line', 'parent_id', 'postage_line_ids', copy=True)
    other_cost_line_ids=fields.One2many('other.cost.budget.line', 'parent_id', 'other_cost_line_ids', copy=True)
    transitions=fields.One2many('confirm.workflow.transition','parent_id','Confirmed', copy=True)
    wkf_history=fields.One2many('confirm.workflow.history', 'parent_id', 'Validations', readonly=True, copy=False)
    utilization_budget_material=fields.One2many('utilization.budget.material','budget_id','Utilization budget material')
    utilization_budget_labor=fields.One2many('utilization.budget.labor','budget_id','Utilization budget labor')
    utilization_budget_equipment=fields.One2many('utilization.budget.equipment','budget_id','Utilization budget equipment')
    utilization_budget_carriage=fields.One2many('utilization.budget.carriage','budget_id','Utilization budget material')
    utilization_budget_postage=fields.One2many('utilization.budget.postage','budget_id','Utilization budget labor')
    utilization_budget_other=fields.One2many('utilization.budget.other','budget_id','Utilization budget equipment')
    document=fields.One2many('ir.attachment','control_budget_document', string = 'Document', required = False)



class EmployeeDutyLine(models.Model):
    '''Ажилтны чиг үүрэг
    '''
    _name = 'employee.duty.line'
    

    project_id = fields.Many2one('project.project', string="Project" ,ondelete='cascade')
    employee_id = fields.Many2one('hr.employee' , string="Employee", track_visibility='always')
    employee_department_id = fields.Many2one('hr.department' , string="Department" , readonly=True, track_visibility='always',related='employee_id.department_id')
    employee_duty = fields.Many2one('project.employee.duty',string="Employee duty")
    duty_type=fields.Many2one('project.employee.duty',string="Duty type")