# -*- coding: utf-8 -*-

import datetime
from re import L
import time
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
import json
# import time
# from _smbc import Context
class main_line_budgets(models.Model):
    '''
        Төслийн хөрөнгө оруулалтын зардлын төрлүүд
    '''
    
    _name = 'main.line.budgets'
    
    main_id = fields.Many2one('main.specification', index=True)
    sel_bud = fields.Selection([
                                         ('material', u'Материалын зардал'),
                                         ('labor', u'Ажиллах хүчний зардал'),
                                         ('equipment', u'Машин механизмын зардал'),
                                         ('carriage',u'Тээврийн зардал'),
                                         ('postage',u'Шууд зардал'),
                                         ('other',u'Бусад зардал')
                                         ],string=u'Зардлын төрөл',required=True)
    text = fields.Char(u'Зардлын утга',required=True)
    price = fields.Float(u'Төлөвлөсөн дүн',required=True)
    descrition = fields.Char(u'Тайлбар',required=False)

class CancelProject(models.Model):
    '''
        Төсөл шалтгаан бичээд цуцлах
    '''
    
    _name = 'cancel.project.project'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    description = fields.Text('Description')
    project_id  = fields.Many2one('project.project', index=True)
    
    def default_get(self, fields):
        result = []
        
        res = super(CancelProject, self).default_get(fields)    
        active_id = self.env.context and self.env.context.get('active_id', False) or False
        perform_obj = self.env['project.project']
        perform = perform_obj.browse(active_id)
 
        res.update({
                    'project_id' : perform.id,
                    })
        return res
    
    
    def send_mail(self):
        '''
            Төсөл шалтгаан бичээд цуцлах
                цуцлагдсан талаарх шалгтаан дагагчидад имайл илгээх
        '''
        main_specification_confirmers   = self.env['main.specification.confirmers']
        employee                        = self.env['hr.employee']
        employee_id                     = employee.sudo().search([('user_id','=',self._uid)])
        
        vals = {
                'project_id'    : self.project_id.id,
                'confirmer'     : employee_id.id ,
                'date'          : fields.Date.context_today(self),
                'role'          : 'project_verifier',
                'state'         : 'reject',
                }
        main_specification_confirmers   = main_specification_confirmers.create(vals)
        
        if not self.project_id.message_follower_ids:
            raise UserError(_('Cannot send email: This project not choose partner.'))
        for partner in self.project_id.message_follower_ids:
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            action_id = self.env['ir.model.data']._xmlid_to_res_id('project.open_view_project_all')
            db_name = request.session.db
            email = partner.partner_id.email
            subject = u'"%s" нэртэй төсөл Цуцлагдсан төлөвт орлоо.'%(self.project_id.name)
            body_html = u'''
                            <h4>Сайн байна уу, Таньд энэ өдрийн мэнд хүргье!</h4>
                            <p><li>"%s" нэртэй төсөл Цуцлагдсан төлөвт орлоо.</li></p>
                            <p><li>Шийдвэрлэсэн тайлбар: %s</li></p>
                            </br>
                            <p><li>"%s" - н мэдээллийг <b><a href=%s/web?db=%s#id=%s&view_type=form&model=project.project&action=%s>Төсөл/Төслүүд</a></b> цонхоор дамжин харна уу.</li></p>
                            <p>--</p>
                            <p>Баярлалаа..</p>
                        '''%( self.project_id.name,
                            self.description,self.project_id.name,
                            base_url,
                            db_name,
                            self.project_id.id,
                            action_id)
     
            if email and email.strip():
                email_template = self.env['mail.template'].create({
                    'name': _('Followup '),
                    'email_from': self.env.user.company_id.email or '',
                    'model_id': self.env['ir.model'].search([('model', '=', 'project.project')]).id,
                    'subject': subject,
                    'email_to': email,
                    'lang': self.env.user.lang,
                    'auto_delete': True,
                    'body_html':body_html,
                })
                email_template.send_mail(self.project_id.id)
                
        self.project_id.write({'state':'cancelled'})
       
        
class EvaluateTasks(models.Model):
    _name = 'evaluate.tasks'
    '''
        Даалгаварыг үнэлсэн үнэлгээ харуулах
    '''
    task_id     = fields.Many2one('project.task', index=True, string = 'Task')
    budget_id   = fields.Many2one('control.budget', index=True, string = 'Budget')
    user_id     = fields.Many2one('hr.employee',string = 'User')
    percent     = fields.Float('Percent')
    

class TransferUser(models.Model):
    _name = 'transfer.user'
    
    '''
        Төсөл санал өгөх эрхтэй хүн саналын эрхээ ацаглах(өөр хүнд шилжүүлэх)
    '''
    
    project_id = fields.Many2one('project.project','Project', index=True,required=True)
    employee = fields.Many2one('hr.employee',u'Ацаглах ажилтан',required=True)
    
    def default_get(self, fields):
        result = []
        res = super(TransferUser, self).default_get(fields)    
        active_id = self.env.context and self.env.context.get('active_id', False) or False
        perform_obj = self.env['project.project']
        perform = perform_obj.browse(active_id)
 
        res.update({
                    'project_id' : perform.id,
                    })
        return res
    
    @api.onchange('project_id')
    def onchange_evaluator(self):
        group_id        = self.env['ir.model.data']._xmlid_to_res_id('nomin_project.group_project_checker')[1]
        sel_user_ids    = self.env['res.users'].sudo().search([('groups_id','in',group_id)])
        emp_ids         = self.env['hr.employee'].sudo().search([('user_id','in',sel_user_ids.ids)])
        project_checker_ids = []
        for emp in self.project_id.project_checkers:
            project_checker_ids.append(emp.id)
        return {'domain':{'employee':[('id','in',emp_ids.ids),('id','not in',project_checker_ids)]}}
    
    
    def transfer_action(self):
        '''
            Ацагласан ажилчин санал өгөх ажилчид дээр нэмэгдэж ажилчин ацагласан талаар баталсан түүх талбарт лог хөтлөх 
        '''
        for obj in self:
            user_ids = []
            for checkers in obj.project_id.project_checkers:
                user_ids.append(checkers.id)
            user_ids.append(obj.employee.id)
            obj.project_id.sudo().update({
                                   'project_checkers' :  [(6, 0, user_ids)]
                                   })
             
            main_specification_confirmers   = self.env['main.specification.confirmers']
            employee                        = self.env['hr.employee']
            employee_id                     = employee.sudo().search([('user_id','=',obj._uid)])
            vals = {
                    'project_id'    : obj.project_id.id,
                    'confirmer'     : employee_id.id ,
                    'date'          : time.strftime('%Y-%m-%d %H:%M:%S'),
                    'role'          : 'project_checkers',
                    'state'         : 'transfer',
                    }
            main_specification_confirmers   = main_specification_confirmers.sudo().create(vals)
            
class ProjectProject(models.Model):
    _inherit = 'project.project'
    _order = 'start_date' 
    '''
       Төсөл
    ''' 


    def get_state_by_query(self):
        query = "SELECT state FROM project_project WHERE id = %s;" % (self.id)
        self.env.cr.execute(query)
        return self.env.cr.fetchone()[0]


    
    def _is_show_project_checkers(self):
        '''
           Нэвтэрсэн хэрэглэгчийн холбоотой ажилтан нь төслийн хянагч мөн эсэх
        ''' 
        
        emp_obj = self.env['hr.employee']
        emp = emp_obj.sudo().search([('user_id','=',self._uid)])
        for project in self:
            project.is_show_project_checkers = False
            if emp in project.project_checkers:
                project.is_show_project_checkers = True
            for users in project.project_users:
                if emp == users.confirmer and users.role == 'project_checkers':
                    project.is_show_project_checkers = False
            if project.state != 'request':
                project.is_show_project_checkers = False
                
    
    def _is_show_project_team(self):
        '''
           Нэвтэрсэн хэрэглэгчийн холбоотой ажилтан нь төслийн багт байгаа эсэх
        ''' 
        emp_obj = self.env['hr.employee']
        emp = emp_obj.sudo().search([('user_id','=',self._uid)])
        for project in self:
            project.is_show_project_team = False
            if emp in project.team_users:
                project.is_show_project_team = True

    
    def _is_show_project_evaluator(self):
        '''
           Нэвтэрсэн хэрэглэгчийн холбоотой ажилтан нь төслийн батлагч мөн эсэх
        '''
        emp_obj = self.env['hr.employee']
        emp = emp_obj.sudo().search([('user_id','=',self._uid)])
        for project in self:
            project.is_show_project_evaluator = False
            if emp in project.evaluator:
                project.is_show_project_evaluator = True
            for users in project.project_users:
                if emp == users.confirmer and users.role == 'evaluator':
                    project.is_show_project_evaluator = False
    
    
    def _is_comfirm(self):
        '''
           Төслийн Хянагчид санал өгч дууссан эсэх
        '''
        count = 0
        users = []
        for project in self:
            project.is_comfirm = False
            for checker in project.project_checkers:
                for user in project.project_users:
                    if checker == user.confirmer and user.role == 'project_checkers':
                        if user.confirmer not in users:
                            count += 1  
                            users.append(user.confirmer)
            if count == len(project.project_checkers):
                project.is_comfirm = True
    
    
    def _is_done(self):
        '''
           Төслийн Үнэлэгчид үнэлгээ өгч дууссан эсэх
        '''
        count = 0
        for project in self:
            project.is_done = False
            for checker in project.evaluator:
                for user in project.project_users:
                    if checker == user.confirmer and user.role == 'evaluator':
                        count += 1
            if count == len(project.evaluator):
                project.is_done = True
    
    
    def _is_show_project_verifier(self):
        '''
           Батлах хэрэглэгч мөн эсэх
        '''
        emp_obj = self.env['hr.employee']
        emp = emp_obj.sudo().search([('user_id','=',self._uid)])
        for project in self:
            project.is_show_project_verifier = False
            if emp in project.project_verifier:
                project.is_show_project_verifier = True
            if project.state != 'request':
                project.is_show_project_verifier = False
                
    
    def _show_button_request(self):
        '''
           Хүсэлт товч харагдах эсэх
        '''
        for project in self:
            if project.state == 'draft' and project.state_comfirm == True:
                project.show_button_request = True
            else: 
                project.show_button_request = False
    
    
    def _show_button_eval(self):
        '''
           Төсөл үнэлэх эсэх
        '''
        for project in self:
            if project.state == 'finished' and project.state_eval == True:
                project.show_button_eval = True
            else: 
                project.show_button_eval = False
    
    
    def _show_button_start(self):
        '''
           Эхлэх товч харагдах нөхцөл
        '''
        for project in self:
            if project.state == 'draft' and project.state_comfirm == False:
                project.show_button_start = True
            else:
                if project.state == 'comfirm': 
                    project.show_button_start = True
                else:
                    project.show_button_start = False
            
    
    def _total_percent(self):
        '''
          Нийт үнэлгээний дундаж
        '''
        for project in self:
            if project.perform_line:
                total = 0.0
                count = 0
                for line in project.perform_line:
                    total += line.total_percent
                    count += 1
                if count!=0:
                    project.total_percent = total/count
                else:
                    project.total_percent = 0
            else:
                    project.total_percent = 0
        
    
    def _is_done_all_task(self):
        '''
          Бүх даалгавар дууссан эсэх
        '''
        for project in self:
            project.is_done_all_task = True
            for task in project.task_ids:
                if task.task_state != 't_done' and task.task_state != 't_cancel':
                    project.is_done_all_task = False
                    
    
    
    def _is_done_all_control_budget(self):
        '''
          Бүх Хяналтын төсөв дууссан эсэх
        '''
        for project in self:
            budgets = self.env['control.budget'].search([('project_id','=',project.id)])
            project.is_done_all_control_budget = True
            for budget in budgets:
                if budget.state != 'done' and budget.state != 'cancel' and budget.state != 'close':
                    project.is_done_all_control_budget = False
    
    
    def _is_project_evaluater(self):
        '''
          Төслийн үнэлэгч мөн эсэх 
        '''
        emp_obj = self.env['hr.employee']
        emp = emp_obj.sudo().search([('user_id','=',self._uid)])
        for project in self:
            project.is_project_evaluater = False
            if emp in project.evaluator:
                project.is_project_evaluater = True
            for users in project.project_users:
                if emp == users.confirmer and users.role == 'evaluator':
                    project.is_project_evaluater = False
    
    def _is_evaluate_done(self):
        '''
          Төсөлд үнэлгээ өгч дууссан эсэх 
        '''
        count = 0
        for project in self:
            project.is_evaluate_done = False
            for evaluater in project.evaluator:
                for user in project.project_users:
                    if evaluater == user.confirmer and user.role == 'evaluator':
                        count += 1
            if count == len(project.evaluator):
                project.is_evaluate_done = True
    
    
    def _control_budget_count(self):
        '''Хяналтын төсвийн тоо
        '''
        for order in self:
            order.control_budget_count = len(self.env['control.budget'].sudo().search([('project_id','=',order.id),('state','not in',['draft','cancel'])])) or 0
        return True
    
    
    def _control_budget_count_of_parent(self):
        '''эцэг төслөөс үүссэн дэд төслүүдийн Хяналтын төсвийн тоо
        '''
        for order in self:
            order.control_budget_count_of_parent = len(self.env['control.budget'].sudo().search([('project_id.parent_project','=',order.id),('state','not in',['draft','cancel'])])) or 0
        return True
    
    
    def _contract_count(self):
        '''Гэрээний тоо
        '''
        for order in self:
            order.contract_count = len(self.env['contract.management'].sudo().search([('project_id','=',order.id),('state','not in',['draft','canceled'])])) or 0
        return True
    
    
    def _contract_count_of_parent(self):
        '''эцэг төслөөс үүссэн дэд төслүүдийн Гэрээний тоо
        '''
        for order in self:
            order.contract_count_of_parent = len(self.env['contract.management'].sudo().search([('project_id.parent_project','=',order.id),('state','not in',['draft','canceled'])])) or 0
        return True

    
    def _payment_request_count(self):
        '''Дэд төсөл дээрх төлбөрийн хүсэлтийн тоо
        '''
        for order in self:
            order.payment_request_count = len(self.env['payment.request'].sudo().search([('project_id','=',order.id),('state','not in',['draft','cancel'])])) or 0
        return True
    
    
    def _payment_request_count_of_parent(self):
        '''эцэг төслөөс үүссэн дэд төслүүдийн төлбөрийн хүсэлтийн тоо
        '''
        for order in self:
            order.payment_request_count_of_parent = len(self.env['payment.request'].sudo().search([('project_id.parent_project','=',order.id),('state','not in',['draft','cancel'])])) or 0
        return True

    
    def _purchase_requisition_count(self):
        '''Худалдан авалтын шаардахын тоо
        '''
        for order in self:
            order.purchase_requisition_count = len(self.env['purchase.requisition'].sudo().search([('project_id','=',order.id),('state','not in',['draft','canceled'])])) or 0
        return True
    

    
    def _purchase_requisition_count_of_parent(self):
        '''Эцэг төслөөс үүссэн дэд төслүүдийн худалдан авалтын шаардахын тоо
        '''
        for order in self:
            order.purchase_requisition_count_of_parent = len(self.env['purchase.requisition'].sudo().search([('project_id.parent_project','=',order.id),('state','not in',['draft','canceled'])])) or 0
        return True

    
    def _subproject_count(self):
        '''Дэд төслүүдийн тоо
        '''
        for order in self:
            order.subproject_count = len(self.env['project.project'].sudo().search([('parent_project','=',order.id)])) or 0            
        return True
     
    
    def _contract_performance(self):
        '''Гэрээний гүйцэтгэлийн үнэлгээ
        '''
        count = 0
        total = 0
        percent = 0
        for project in self:
            contract_ids = self.env['contract.management'].sudo().search([('project_id','=',project.id)])
            performance_ids = self.env['contract.performance'].sudo().search([('contract_id', 'in', contract_ids.ids),('state','=','confirmed')])
            if performance_ids:
                for perf in performance_ids:
                    total +=perf.total_percent
                    count +=1
                percent = total/ count
            project.contract_percent =percent
            
    STATE_SELECTION = [('draft',u'Ноорог'),
                        ('request',u'Хүсэлт'),                        
                        ('project_started',u'Эхэлсэн'),                        
                        ('evaluate',u'Үнэлэгдсэн'),
                                               
                        
                        ('comfirm',u'Батлагдсан'),
                       
                        ('ready', u'Үнэлэх'),
                        ('finished',u'Дууссан'),
                        
                        ('cancelled', u'Цуцлагдсан'),
                        ]
    
    STATE_SELECTION_NEW = [('draft',u'Ноорог'),
                        ('request',u'Хүсэлт'),                        
                        ('project_started',u'Эхэлсэн'),                        
                        ('evaluate',u'Үнэлэгдсэн'),
                                               
                        ('verify_by_economist', u'ЭЗ Хянах'),
                        ('approve_by_director', u'СЗ Батлах'),
                        ('approve_by_business_director', u'БХЗ Батлах'),
                        ('approve_by_ceo', u'ХГЗ Батлах'),
                        ('approve_by_board_member', u'ТУЗ Батлах'),
                        ('comfirm',u'Батлагдсан'),
                        ('implement_project', u'Хэрэгжүүлэлт'),
                        ('ready', u'Үнэлэх'),
                        ('finished',u'Дууссан'),
                        ('surplus_by_economist',u'Тодотгол эдийн засагч хянах'),
                        ('surplus_by_director',u'СЗ Тодотгох'),
                        ('surplus_by_business_director',u'БХЗ Тодотгох'),
                        ('surplus_confirm_branch',u'Тодотгол салбар дээр батлагдсан'),
                        ('surplus_by_ceo',u'ХГЗ Тодотгох'),
                        ('delayed',u'Хойшлогдсон'),
                        ('cancelled', u'Цуцлагдсан'),
                        ]
    
    def _add_followers(self,user_ids):
        '''Add followers
        '''
        partner_ids = [user.partner_id.id for user in self.env['res.users'].browse(user_ids) if user.partner_id]
        self.message_subscribe(partner_ids=partner_ids)
    
    @api.depends('is_show_project_checkers')
    def _is_voter(self):
        for project in self:
            emp_obj = self.env['hr.employee']
            emp = emp_obj.sudo().search([('user_id','=',self._uid)])           
            if emp in project.project_checkers and emp not in project.voters:                            
                project.is_voter = True
            else:
                project.is_voter = False
    
    
    def _is_button_clicker(self):
        for project in self:	
            project.button_clicker=project.state_handler(project.state_new,'validate_button_clicker')
    

    department_id               = fields.Many2one('hr.department', string = 'Department',required = True, tracking=True)
    project_stage               = fields.Many2many('project.stage','project_projetc_stages','project_id','stage_id', string = 'Project Stage', required = True, tracking=True)
    perform                     = fields.Many2many('evaluation.indicators', string = 'Rating perform' ,states={'finished': [('required', True)]}, tracking=True)
    perform_new                 = fields.Many2many('evaluation.indicators', 'project_perform_rel','project_id','perform_id',string = 'Perform new' , tracking=True)
    transfer_user               = fields.Many2one('hr.employee',string=u'Ацаглах ажилтан')
    state                       = fields.Selection(STATE_SELECTION,string = 'Status', required=True, copy=False , default = 'draft', tracking=True)
    state_new                   = fields.Selection(STATE_SELECTION_NEW,string = 'Status', required=True, copy=False , default = 'draft', tracking=True)
    state_comfirm               = fields.Boolean(string='Project confirm',default = True, readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    state_eval                  = fields.Boolean(string='Project evaluate',default = True, readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    is_show_project_checkers    = fields.Boolean(u'Санал өгөх ажилчид',compute = _is_show_project_checkers)
    is_show_project_team        = fields.Boolean(u'Төслийн баг',compute = _is_show_project_team)
    is_show_project_evaluator   = fields.Boolean(u'Төслийн үнэлэгч',compute = _is_show_project_evaluator)
    is_show_project_verifier    = fields.Boolean(u'Төсөл батлагч',compute = _is_show_project_verifier)
    is_comfirm                  = fields.Boolean(u'Төсөл батлах',compute = _is_comfirm)
    is_done                     = fields.Boolean('Done?',compute=_is_done)
    reject_choose               = fields.Boolean(u'Татгалзах')
    transfer_choose             = fields.Boolean(u'Ацаглах')
    show_button_request         = fields.Boolean('button request', compute = _show_button_request)
    show_button_eval            = fields.Boolean('button request', compute = _show_button_eval)
    show_button_start           = fields.Boolean('button request', compute = _show_button_start)
    is_done_all_task            = fields.Boolean('Done tasks?',compute = _is_done_all_task)
    is_done_all_control_budget  = fields.Boolean('Done budgets?',compute = _is_done_all_control_budget)
    total_percent               = fields.Float('Total Percent %',compute=_total_percent)
    perform_line                = fields.One2many('project.rate','project_id',string='Perform Line')
    project_perform             = fields.One2many('project.perform','project_id',string='Project perform Line')
    project_users               = fields.One2many('main.specification.confirmers','project_id','Project users')
    main_line_ids               = fields.One2many('main.specification', 'parent_project_id', string = 'Main specifications')
    is_evaluate_done            = fields.Boolean('is evaluate done',default=False,compute=_is_evaluate_done)
    is_project_evaluater        = fields.Boolean('is project evaluater',default=False,compute=_is_project_evaluater)
    control_budget_count        = fields.Integer(compute=_control_budget_count,string=u'Хяналтын төсөв')
    control_budget_count_of_parent        = fields.Integer(compute=_control_budget_count_of_parent,string=u'Хяналтын төсөв')
    contract_count              = fields.Integer(compute=_contract_count, string=u'Гэрээ')
    contract_count_of_parent              = fields.Integer(compute=_contract_count_of_parent, string=u'Гэрээ')
    payment_request_count       = fields.Integer(compute=_payment_request_count, string=u'Төлбөрийн хүсэлт')
    payment_request_count_of_parent       = fields.Integer(compute=_payment_request_count_of_parent, string=u'Төлбөрийн хүсэлт эцэг')
    purchase_requisition_count       = fields.Integer(compute=_purchase_requisition_count, string=u'Худалдан авалтын шаардах')
    purchase_requisition_count_of_parent   = fields.Integer(compute=_purchase_requisition_count_of_parent, string=u'Худалдан авалтын шаардах')
    contract_percent            = fields.Float(compute=_contract_performance,string=u'Гэрээ гүйцэтгэл')
    project_flow                = fields.Float(u'Төслийн явц (%)',readonly=True)
    subproject_count            = fields.Integer(compute=_subproject_count, string=u'Дэд төслүүд')
    json_data = fields.Char(string='Json data')
    voters = fields.Many2many('hr.employee','project_main_hr_employee_rel','project_id','emp_id',string = u'Санал өгсөн ажилчид new')
    is_voter              = fields.Boolean(string='Is voter',default=False, compute=_is_voter)
    button_clicker             = fields.Boolean(string='Button clicker',default=False, compute=_is_button_clicker)
    return_reason = fields.Char(string="Буцаасан шалтгаан" , tracking=True )
    cancel_reason = fields.Char(string="Цуцалсан шалтгаан" , tracking=True )
    back_reason = fields.Char(string="Хойшлуулсан шалтгаан" , tracking=True )
    
    @api.model
    def _project_flow_cron(self):
        '''Төслийн явцийн хувь тооцох крон функц
        '''
        query = "SELECT id FROM project_project"
        self.env.cr.execute(query)
        records = self.env.cr.dictfetchall()
        for record in records:
            project_status = 0
            project = self.env['project.project'].browse(record['id'])
            status_tasks = self.env['project.task'].search([('project_id','=',project.id)])
            tasks_total_day = 0
            complete_percent_day = 0
            for task in status_tasks:
                if task.task_state != 't_cancel':
                    if task.date_deadline and task.task_date_start:
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
            project.project_flow = project_status

    @api.model
    def create(self, vals):
        '''
          Төсөл үүсгэх дагагчид нэмэх
              мөн эхлэх огноо дуусах огнооноос бага байгаа эсэхийг шалгах
        '''

        if self.env.context is None:
            self.env.context = {}
        create_context = dict(self.env.context, project_creation_in_progress=True,
                              alias_model_name=vals.get('alias_model', 'project.task'),
                              alias_parent_model_name=self._name,
                              mail_create_nosubscribe=True)

        # ir_values = self.env['ir.values'].get_default('project.config.settings', 'generate_project_alias')
        # if ir_values:
        #     vals['alias_name'] = vals.get('alias_name') or vals.get('name')
        

        if vals['budget_line_ids'] and  vals['parent_project']:
            
            raise ValidationError(_(u'Дэд төслийн төлөвлөлт мөр сонгосон эцэг төслийн хөрөнгө оруулалтын мөрөөс үүснэ.'))
        
        if vals['budget_line_ids'] and  vals['project_type'] in ['operational_project', 'general_project']:
            
            raise ValidationError(_(u'Ерөнхий болон Үйл ажиллагааны төсөл дээр хөрөнгө оруулалт үүсгэхгүй.'))
        

        if 'privacy_visibility' in vals and not vals['privacy_visibility']:
            raise ValidationError(_(u'Төслийн хандалтын эрх тохируулна уу.'))
        if vals['project_type'] not in ['operational_project', 'general_project']:
            if 'sales_revenue' in vals and not vals['sales_revenue']:
                raise ValidationError(_(u'Борлуулалтын орлого 0 дүнтэй байна.'))
                
            if 'present_value' in vals and not vals['present_value']:
                raise ValidationError(_(u'Цэвэр өнөөгийн үнэ 0 дүнтэй байна.'))
            if 'gross_probit_percent' in vals and not vals['gross_probit_percent']:
                raise ValidationError(_(u'Нийт ашгийн хувь 0 дүнтэй байна.'))
            if 'return_of_investment' in vals and not vals['return_of_investment']:
                raise ValidationError(_(u'Хөрөнгө оруулалтын өгөөж 0 дүнтэй байна.'))
            if 'compensate_of_investment' in vals and not vals['compensate_of_investment']:
                raise ValidationError(_(u'Хөрөнгө оруулалтыг нөхөх хугацаа /жил/ 0 утгатай байна.'))
            

                
             
        project_id = super(ProjectProject, self).create(vals, context=create_context)
        project_rec = self.browse(project_id)
        project_rec._add_followers(project_rec.user_id.id)
        if vals.get('end_date') or vals.get('start_date'):
            if vals.get('end_date') < vals.get('start_date'):
                raise ValidationError(_(u'Төсөл дуусах огноо эхлэх огнооноос бага байна!!!'))
        
        if project_rec.parent_project:
            if vals.get('start_date'):
                if project_rec.parent_project.start_date > vals.get('start_date'):
                    raise ValidationError(_(u'Эцэг төслийн эхлэх огноонд багтахгүй байна'))
            if vals.get('end_date'):
                if project_rec.parent_project.end_date < vals.get('end_date'):
                    raise ValidationError(_(u'Эцэг төслийн дуусах огноонд багтахгүй байна!'))
        
        if vals.get('user_id'):
             project_rec._add_followers(project_rec.created_user_id.id)
        if vals.get('evaluator') or vals.get('project_checkers') or vals.get('team_users') or vals.get('project_verifier'):
            for checkers in project_rec.project_checkers:
                project_rec._add_followers(checkers.user_id.id)
                                
            for eval in project_rec.evaluator:
                project_rec._add_followers(eval.user_id.id)
                    
            for team in project_rec.team_users:
                project_rec._add_followers(team.user_id.id)
                    
            if project_rec.project_verifier.address_home_id.id:
                project_rec._add_followers(project_rec.project_verifier.user_id.id)
                
        values = {'alias_parent_thread_id': project_id, 'alias_defaults': {'project_id': project_id}}
        self.env['mail.alias'].browse(project_rec.alias_id.id).write([], values)
        json_data = {
            'workflow_name' :'unknown',
            'next_state':'verify_by_economist',
            }
        project_rec.json_data = json.dumps(json_data)
        return project_id

    def write(self, vals):
        '''
          Төсөлд дагагчид нэмэх
              мөн эхлэх огноо дуусах огнооноос бага байгаа эсэхийг шалгах
        '''
        
        res = super(ProjectProject, self).write(vals)
        project_id = self
        # json_data = {
        #     'workflow_name' :'unknown',
        #     'next_state':'verify_by_economist',
        #     }
        # self.json_data = json.dumps(json_data)
        if project_id.parent_project:
            if vals.get('start_date'):
                if project_id.parent_project.start_date > vals.get('start_date'):                    
                    raise ValidationError(_(u'Эцэг төслийн эхлэх огноонд багтахгүй байна!!! write'))

            if vals.get('end_date'):
                if project_id.parent_project.end_date < vals.get('end_date'):
                    raise ValidationError(_(u'Эцэг төслийн дуусах огноонд багтахгүй байна!!! write'))

        if  vals.get('end_date') or vals.get('start_date'):
            if project_id.end_date < project_id.start_date:
                raise ValidationError(_(u'Төсөл дуусах огноо эхлэх огнооноос бага байна!!!'))
        if vals.get('user_id'):
             project_id._add_followers(project_id.user_id.id)
        if vals.get('evaluator') or vals.get('project_checkers') or vals.get('team_users') or vals.get('project_verifier'):
            for checkers in project_id.project_checkers:
                project_id._add_followers(checkers.user_id.id)
                                 
            for eval in project_id.evaluator:
                project_id._add_followers(eval.user_id.id)
                     
            for team in project_id.team_users:
                project_id._add_followers(team.user_id.id)
                     
            if project_id.project_verifier.address_home_id.id:
                project_id._add_followers(project_id.project_verifier.user_id.id)
        if 'active' in vals:
            tasks = project_id.with_context(active_test=False).mapped('tasks')
            tasks.write({'active': vals['active']})
        return res

   
    @api.onchange('parent_project')
    def onchange_parent_project(self):

        if self.parent_project:
            self.update({ 'partner_id' : self.parent_project.partner_id,
                          'project_stage' : self.parent_project.project_stage,
                          'perform' : self.parent_project.perform,
                          'project_verifier' : self.parent_project.project_verifier,
                          'project_checkers' : self.parent_project.project_checkers,
                          'evaluator' : self.parent_project.evaluator,
                          })
    @api.onchange('is_parent_project')
    def onchange_is_parent_project(self):
        for project in self:
            if project.is_parent_project:
                if project.budget_line_ids:
                    for budget_line in project.budget_line_ids:
                        budget_line.is_required = True
                        budget_line.is_readonly = True
                        budget_line.is_invisible = True
            else:
                if project.budget_line_ids:
                    for budget_line in project.budget_line_ids:
                        budget_line.is_required = False
                        budget_line.is_invisible = False
                        budget_line.is_readonly = False

                            
                
            
    @api.onchange('project_categ')
    def onchange_project_categ(self):
        '''project_categ өөрчлөгдөхөд ,project_checkers,user_id домайн буцаах
        '''
        documents = []
        for project in self:
            config_id = self.env['project.category'].search([('name','=',project.project_categ.name)])
            config_line_id = self.env['project.category.line'].search([('parent_id','=',config_id.id),('project_type','=',project.project_type),('project_state','=',project.state)])
        if config_line_id:
            for line in config_line_id:
                documents.append((0,0,{ 'name' : line.name,'type':'binary','attach_required':line.is_confirm}))
            
        self.update({'document' : documents})
      

    @api.onchange('project_type')
    def onchange_project_type(self):
        '''project_type өөрчлөгдөхөд  тохиргооноос document буцаах
        '''
        documents = []
        for project in self:
            config_id = self.env['project.category'].search([('name','=',project.project_categ.name)])
            config_line_id = self.env['project.category.line'].search([('parent_id','=',config_id.id),('project_type','=',project.project_type),('project_state','=',project.state)])
        if config_line_id:
            for line in config_line_id:
                documents.append((0,0,{ 'name' : line.name,'type':'binary','attach_required':line.is_confirm}))
            
        self.update({'document' : documents})
        
        confirmer_group_id        = self.env['ir.model.data']._xmlid_to_res_id('nomin_project.group_project_confirmer')
        conf_user_ids             = self.env['res.users'].sudo().search([('groups_id','in',confirmer_group_id)])
        conf_emp_ids              = self.env['hr.employee'].sudo().search([('user_id','in',conf_user_ids.ids)])
        
        checker_group_id        = self.env['ir.model.data']._xmlid_to_res_id('nomin_project.group_project_checker')
        check_user_ids          = self.env['res.users'].sudo().search([('groups_id','in',checker_group_id)])
        check_emp_ids           = self.env['hr.employee'].sudo().search([('user_id','in',check_user_ids.ids)])
        
        manager_group_id        = self.env['ir.model.data']._xmlid_to_res_id('nomin_project.group_project_manager')
        manager_user_ids          = self.env['res.users'].sudo().search([('groups_id','in',manager_group_id)])
        
        return {'domain':{
                          'project_verifier':[('id','in',conf_emp_ids.ids)],
                          'project_checkers':[('id','in',check_emp_ids.ids)],
                          'user_id':[('id','in',manager_user_ids.ids)]
                          }}
    
    
    def transfer_button(self):
        '''Ацаглах товч
        '''
        return {
            'name': 'Note',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'transfer.user',
            'context': self._context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }
    
    
    def action_import(self):
        ''' Төсөл хөрөнгө оруулалт
        '''        
        
        return {
            'name': 'Note',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'project.budget.export.import',
            # 'context': self._context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }

    
    def project_rate_button(self):
        '''Үнэлэх товч
        '''
        return {
            'name': 'Note',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rate.project.perform',
            'context': self._context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }
    
    
    def reject_button(self):
        '''Татгалзах товч
        '''
        for project in self:
            main_specification_confirmers   = project.env['main.specification.confirmers']
            employee                        = project.env['hr.employee']
            employee_id                     = employee.sudo().search([('user_id','=',project._uid)])
            vals = {
                    'project_id'    : project.id,
                    'confirmer'     : employee_id.id ,
                    'date'          : time.strftime('%Y-%m-%d %H:%M:%S'),
                    'role'          : 'project_checkers',
                    'state'         : 'reject',
                    }
            main_specification_confirmers = main_specification_confirmers.create(vals)
            project.reject_choose = False
            
    @api.onchange('reject_choose')
    def onchange_reject_choose(self):
        if self.transfer_choose == True:
            self.transfer_choose = False
    
    @api.onchange('transfer_choose')
    def onchange_transfer_choose(self):
        if self.reject_choose == True:
            self.reject_choose = False
        
    # Цуцлах товч дээр дарахад ажиллах функц
    
    def action_cancel(self):
        '''Цуцлах товч
        '''
        emp_obj = self.env['hr.employee']
        emp = emp_obj.sudo().search([('user_id','=',self._uid)])
        for task in self:
            if not task.project_verifier == emp:
                raise ValidationError(_(u'Төсөл батлах эрхтэй хүн цуцална'))
            return {
                'name': 'Note',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'cancel.project.project',
                'context': task._context,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
            }
    
    # Батлах товч дээр дарахад ажиллах функц
    
    def action_start(self):
        '''Эхлэх товч
        '''
        for task in self:
            if not task.user_id.id == self._uid:
                raise ValidationError(_(u'Төслийн менежер эхлэх товч дарна'))
            task.write({'state':'project_started'})
    
    # Батлах товч дээр дарахад ажиллах функц
    
    def action_start_new(self):
        '''Эхлэх товч
        '''

        for task in self:
            if not task.user_id.id == self._uid:
                raise ValidationError(_(u'Төслийн менежер эхлэх товч дарна'))
            task.write({'state_new':'implement_project'})
    
    
    def action_send(self):
        '''Илгээх
        '''

        for project in self:
            

            if not project.user_id.id == self._uid:
                raise ValidationError(_(u'Төслийн менежер илгээх боломжтой'))
            
            if not project.is_parent_project and project.parent_project:
                if not project.budgeted_line_ids:
                    raise ValidationError(_(u'Зардлын задаргааны мөрийг оруулна уу'))
            
            if not project.is_parent_project and not project.parent_project:
                if not project.budgeted_line_ids:
                    raise ValidationError(_(u'Зардлын задаргааны мөрийг оруулна уу!'))

        
            if project.project_type in ('investment_project','construction_project') and not project.parent_budget_line_ids and not project.budget_line_ids:
                raise ValidationError(_(u'Хөрөнгө оруулалтын мөрийг оруулна уу'))
        
            if project.document:
                for line in project.document :
                    if not line.datas:
                        raise ValidationError(_(u'хавсралт хэсэгт %s хавсралтыг оруулаагүй байна.'%line.name))
            
                    if line.attach_required and not line.confirmed_date: 
                        raise ValidationError(_(u'%s - нэртэй хавсралтыг батлана уу.'%line.name))     


            if not project.is_parent_project:    
                
                project.budgeted_line_ids.write({'parent_project_id':project.parent_project.id,
                                            })
                


                if project.parent_project.parent_budget_line_ids:
                    for budget_line in project.parent_project.parent_budget_line_ids:         
                        if project.department_id == budget_line.department_id :                
                            
                            # if budget_line:        
                            #     print '\n\n\n line hahaha' , budget_line , budget_line.approximate_amount , budget_line.sum_of_subproject , budget_line.possible_amount_create_project            
                            #     if project.total_limit > budget_line.possible_budgeting:
                            #         print '\n\n\n sonin in' , budget_line.possible_budgeting , budget_line
                            #         raise ValidationError(_(u'Төлөвлөсөн дүнгийн утга батлагдсан дүнгээс хэтэрсэн байна'))
                            if budget_line:

                                total = 0
                                balance = 0
                                if budget_line.sum_of_subproject:
                                    total = budget_line.sum_of_subproject + project.budgeted_line_ids.budgeted_amount
                                    balance = budget_line.approximate_amount - total
                                    
                                else:
                                    total = project.budgeted_line_ids.budgeted_amount
                                    balance = budget_line.approximate_amount - total
            
                                budget_line.update({'sum_of_subproject':total,  
                                                        'parent_project_id':project.parent_project.id,
                                                        'possible_amount_create_project':balance
                                                        })   
                total_material_cost = 0
                total_labor_cost = 0
                total_equipment_cost = 0
                total_carriage_cost = 0
                total_postage_cost = 0
                total_other_cost = 0

                if project.budget_line_ids:
                    for budget_line in project.budget_line_ids:
                        for line in budget_line.line_ids:
                            if line.material_cost:
                                total_material_cost += line.material_cost
                            if line.labor_cost:
                                total_labor_cost += line.labor_cost
                            if line.equipment_cost:
                                total_equipment_cost += line.equipment_cost
                            if line.carriage_cost:
                                total_carriage_cost += line.carriage_cost
                            if line.postage_cost:
                                total_postage_cost += line.postage_cost
                            if line.other_cost:
                                total_other_cost += line.other_cost

                project.material_budget_new = total_material_cost
                project.labour_budget_new = total_labor_cost
                project.equipment_budget_new = total_equipment_cost
                project.transport_budget_new = total_carriage_cost
                project.direct_budget_new = total_postage_cost
                project.other_budget_new = total_other_cost


                            
                


                # query = """UPDATE 
                #     project_budget pb
                # SET                 
                #     surplus_amount = %s,
                #     sum_of_budgeted_amount = %s,
                #     possible_amount_create_project = %s - %s

                # FROM 
                #     project_project pp
                # WHERE 
                #     pb.project_id = pp.id and pp.parent_project=%s"""%(vals.get('surplus_amount'),vals.get('sum_of_budgeted_amount'),vals.get('surplus_amount'),vals.get('sum_of_budgeted_amount'),self.parent_project_id.id)
                
                # if self.is_parent_project:

                #     self.env.cr.execute(query)   
                                     
                                               
                                
        


            project.state_handler(project.state_new,'next_state')
            # project.write({'previous_state':project.state,
            #     'state':json.loads(project.json_data)['next_state']})

            
            project.create_history('sent','Илгээсэн')
            user_ids=[]
            for user in project.button_clickers.ids:
                if user not in project.c_user_ids.ids:
                    user_ids.append(user)
            project.update({'c_user_ids':[(6,0,user_ids+project.c_user_ids.ids)]})
        
                

                
        

    
    def action_confirm(self):
        '''Батлах
        '''

        # if self.get_state_by_query():
        #     return
        for project in self:
            user_ids=[]
            for user in project.button_clickers.ids:
                if user not in project.c_user_ids.ids:
                    user_ids.append(user)
            # project.update({'c_user_ids':[(6,0,user_ids)]})
            project.update({'c_user_ids':[(6,0,user_ids+project.c_user_ids.ids)]})
            if project.is_parent_project and project.project_type in ('investment_project','construction_project'):
                if project.state_new == 'approve_by_director':
                    if project.project_checkers:
                        if len(project.voters) != len (project.project_checkers):
                            raise UserError(_('Санал өгч дуусаагүй байгаа тул батлах боломжгүй.'))
            
            project.state_handler(project.state_new,'next_state')
        # self.state_handler(self.state)
        # self.write({'previous_state':self.state,
        #     'state':json.loads(self.json_data)['next_state']})
        
            project.create_history('approve','Баталсан')

        


        



    
    def vote_button(self):
        '''Санал өгөх 
            Санал өгсөн мөр дээр санал өгсөн ажилтны нэрийг санал өгсөн ажилчид талбарт нэмэх
            сүүлийн хүн санал өгөхөд батлах хэрэглэгчид емайл илгээх
        '''
        # main_specification_confirmers   = self.env['main.specification.confirmers']
        employee                        = self.env['hr.employee']
        employee_id                     = employee.sudo().search([('user_id','=',self._uid)])
        for project in self:
            vals = {
                    'project_id'    : project.id,
                    'confirmer'     : employee_id.id ,
                    'date'          : time.strftime('%Y-%m-%d %H:%M:%S'),
                    'role'          : 'project_checkers',
                    'state'         : 'voted',
                    }
            # main_specification_confirmers   = main_specification_confirmers.create(vals)
            ids = []
            for user in project.voters:
                ids.append(user.id)
            ids.append(employee_id.id)
            project.write({
                       'voters' :  [(6, 0, ids)]
                       })
        self.create_history('voted','Санал өгсөн')   


     
        return { 'type': 'ir.actions.client', 'tag': 'reload', }


        
    
            
            
    
    
    def action_done(self):
        '''Дуусгах товч
        '''
        for project in self:
            if not project.user_id.id == self._uid:
                raise ValidationError(_(u'Төслийн менежер дуусгах товч дарна'))
            if project.project_flag:
               self.write({'state_new':'finished'}) 
            if project.is_done_all_task == True:
                if project.is_done_all_control_budget == True:
                    self.write({'state':'finished'})
                else:
                    raise ValidationError(_(u'Төслийн хяналтын төсөвүүд дуусаагүй байна'))
            else:
                raise ValidationError(_(u'Төслийн даалгаварууд дуусаагүй байна'))
        
    
    def action_request(self):
        '''Хүсэлт товч
        '''
        for project in self:
            if project.main_line_ids:
                project.write({'state':'request'})
                
                for line in project.main_line_ids:
                    line.write({
                                'edit_click':False
                                })
                if not project.project_checkers:
                    raise UserError(_('Cannot send email: This project not choose partner.'))
                for checkers in project.project_checkers:
                    base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                    action_id = self.env['ir.model.data']._xmlid_to_res_id('project.open_view_project_all')
                    db_name = request.session.db
                    email = checkers.work_email
                    subject = u'"%s" нэртэй төслийн хөрөнгө оруулалт батлахад санал өгнө үү.'%(project.name)
                    body_html = u'''
                                    <h4>Сайн байна уу, Таньд энэ өдрийн мэнд хүргье! </h4>
                                    <p><li>"%s" нэртэй төслийн хөрөнгө оруулалт батлахад санал өгнө үү.</li></p>
                                    </br>
                                    <p><li>"%s" - н мэдээллийг <b><a href=%s/web?db=%s#id=%s&view_type=form&model=project.project&action=%s>Төсөл/Төслүүд</a></b> цонхоор дамжин харна уу.</li></p>
                                    <p>--</p>
                                    <p>Баярлалаа..</p>
                                '''%( project.name,project.name,base_url,
                                    db_name,
                                    project.id,
                                    action_id)
             
                    if email and email.strip():
                        email_template = self.env['mail.template'].create({
                            'name': _('Followup '),
                            'email_from': self.env.user.company_id.email or '',
                            'model_id': self.env['ir.model'].search([('model', '=', 'project.project')]).id,
                            'subject': subject,
                            'email_to': email,
                            'lang': self.env.user.lang,
                            'auto_delete': True,
                            'body_html':body_html,
                        })
                        email_template.send_mail(project.id)
                if  project.is_parent_project and project.document:
                    for line in project.document :
                        if not line.datas:
                            raise ValidationError(_(u'хавсралт хэсэгт %s хавсралтыг оруулаагүй байна.'%line.name))
                
            else:
                raise ValidationError(_(u'Төслийн хөрөнгө оруулалтын мөрийг оруулаагүй байна'))
            

    
    def action_evaluate(self):
        '''Үнэлэх төлөвт оруулах 
        '''

        for task in self:
            if not task.user_id.id == self._uid:
                raise ValidationError(_(u'Төслийн менежер үнэлүүлэх товч дарна'))


            task.state_handler(task.state_new,'next_state')
        
        # self.state_handler(self.state)
        # self.write({'previous_state':self.state,
        #     'state':json.loads(self.json_data)['next_state']})
        # self.write({'state':'ready'})
        project_perform = self.env['project.rate']
        for project in self:
            for perform in project.perform:
                vals = {
                        'project_id'    : self.id,
                        'perform'       : perform.id,
                        'percent'       : 0.0,
                        }
                project_perform = project_perform.create(vals)     

    
    def to_assess(self):
        '''Үнэлэхээс дууссан төлөвт оруулах
        '''

        return {
            'name': 'Note',            
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'to.evaluate.perform',          
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',  
                    
        }

          
            
    
    def action_perform(self):
        '''Үнэлэх шатанд оруулах товч
        '''
        self.write({'state':'ready'})
        project_perform = self.env['project.rate']
        for project in self:
            for perform in project.perform:
                vals = {
                        'project_id'    : self.id,
                        'perform'       : perform.id,
                        'percent'       : 0.0,
                        }
                project_perform = project_perform.create(vals)
        
    
    def history_evaluator(self):
        '''Ноорог шатанд оруулах товч
        '''
        main_specification_confirmers = self.env['main.specification.confirmers']
        vals = {
                'project_id'    : self.id,
                'confirmer'     : user.id ,
                'date'          : time.strftime('%Y-%m-%d %H:%M:%S'),
                'role'          : 'evaluator',
                'state'         : 'new',
                }
        main_specification_confirmers = main_specification_confirmers.create(vals)
    
    
    def action_draft(self):
        '''Ноорог шатанд оруулах товч
        '''
        self.write({'state':'draft'})
    

    
    def action_return(self):
        ''' Төлөв буцаах
        '''


        return {
            'name': 'Note',            
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'return.state',          
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',  
                    
        }
    

    
    def project_cancel(self):
        ''' Цуцлах
        '''


        return {
            'name': 'Note',            
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'project.cancel',          
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',  
                    
        }
    

    
    def back_comfirm(self):
        ''' Батлагдсан руу буцаах
        '''
        for project in self:
            project.write({'state':'comfirm'})


    
    def project_back(self):
        ''' Хойшлуулах
        '''


        return {
            'name': 'Note',            
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'project.back',          
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',  
                    
        }
        
        
    
class ProjectStage(models.Model):
    '''Төслийн даалгаврын үе шат
    '''
    
    _name = 'project.stage'
    _description = 'Project Stage'
    _inherit = ['mail.thread']
    
    name        = fields.Char(u'Нэр',required = True , tracking=True)
    sequense    = fields.Integer(u'Дараалал',default = 1, required = True)
    description = fields.Text(u'Тайлбар' , tracking=True)
    project_ids = fields.Many2many('project.project', 'project_stage_relat', 'project_stage_id', 'project_id', 'Project_stages')
    
    @api.model
    def create(self,vals):
        '''Төслийн даалгаврын үе шат үүсгэх нэрний давхардал шалгах
    '''
        
        tags = self.env['project.stage'].search([('name', '=', vals.get('name'))])
        if not tags:
            project_id = super(ProjectStage, self).create(vals)
            return project_id
        else:
            raise ValidationError(_(u'Ийм нэртэй Төслийн даалгаварын үе үүссэн байна !'))
        
    def unlink(self):
        '''Төслийн даалгаврын үе шат устгах төсөлд ашигласан эсэхийг шалгах
        '''
        issue_ids = self.env['project.project'].sudo().search([('project_stage', '=', self.id)])
        if len(issue_ids)==0:
            res = super(ProjectStage, self).unlink()
            return res
        else: 
            raise ValidationError(_(u'Энэхүү мэдээллийг бүртгэлд ашигласан тул устгах боломжгүй!'))
    
class MainSpecificationn(models.Model):
    '''Төслийн Хөрөнгө оруулалтын мөр
    '''
    _inherit = 'main.specification'
        
    @api.depends('parent_project_id.is_show_project_checkers')
    def _get_bool(self):
        for line in self:
            emp_obj = self.env['hr.employee']
            emp = emp_obj.sudo().search([('user_id','=',self._uid)])           
            if emp in line.parent_project_id.project_checkers and emp not in line.voters:                            
                line.is_checker = True
            else:
                line.is_checker = False
            
            

            if line.parent_project_id.is_show_project_verifier == True:
                line.is_show_project_verifier = True
            else:
                line.is_show_project_verifier = False
            
    
    @api.depends('parent_project_id.is_comfirm')
    def _is_comfirm_project(self):
        for line in self:
            if line.parent_project_id.is_comfirm == True:
                line.is_comfirm_project = True
            else:
                line.is_comfirm_project = False
                
    
    def _material_line_total(self):
        '''Хөрөнгө оруулалтын батлагдахаар хүлээж буй хяналтын төсвүүдийн материалын зардлын нийт дүн
        '''

        for main in self:
            if main.parent_project_id.id:
                self.env.cr.execute("select sum(product_uom_qty*price_unit) from material_budget_line where parent_id in (select id from control_budget where project_id= %s and state in ('close','confirm'))"%(main.parent_project_id.id))
                res = self.env.cr.fetchone()[0] or 0.0
                main.material_line_total =  main.material_line_limit - res

    
    def _material_line_real(self):
        '''Хөрөнгө оруулалтын батлагдсан хяналтын төсвүүдийн материалын зардлын нийт дүн
        '''
        for main in self:
            if main.parent_project_id.id:
                self.env.cr.execute("select sum(product_uom_qty*price_unit) from material_budget_line where parent_id in (select id from control_budget where project_id= %s and state in ('done','close'))"%(main.parent_project_id.id))
                res = self.env.cr.fetchone()[0] or 0.0
                main.material_line_real =  main.material_line_limit - res

    
    @api.depends('lines_budgets')
    def _material_line_limit(self):
        '''Хөрөнгө оруулалтын батлагдсан хяналтын төсвүүдийн материалын зардлын нийт дүНгээр үлдэгдэл тооцох
        '''
        for main in self:
            total = 0.0
            for line in main.lines_budgets:
                if line.sel_bud == 'material':
                    total += line.price
            main.material_line_limit = total
    
    
    def _labor_line_total(self):
        '''Хөрөнгө оруулалтын батлагдахаар хүлээж буй хяналтын төсвүүдийн ажиллах хүчний зардлын нийт дүн
        '''

        for main in self:
            if main.parent_project_id.id:
                self.env.cr.execute("select sum(product_uom_qty*price_unit + \
                                                product_uom_qty*price_unit *engineer_salary_percent /100 + \
                                                product_uom_qty*price_unit*extra_salary_percent/100 + \
                                                product_uom_qty*price_unit*habe_percent/100 + \
                                                product_uom_qty*price_unit*social_insurance_rate/100) \
                                                    from labor_budget_line where parent_id in \
                                                        (select id from control_budget where project_id= %s and state in ('done','close','confirm'))"%(main.parent_project_id.id))
                res = self.env.cr.fetchone()[0] or 0.0
                main.labor_line_total = main.labor_line_limit - res

    
    def _labor_line_real(self):
        '''Хөрөнгө оруулалтын батлагдсан хяналтын төсвүүдийн ажиллах хүчний зардлын нийт дүн
        '''
        for main in self:
            if main.parent_project_id.id:
                self.env.cr.execute("select sum(product_uom_qty*price_unit + \
                                                product_uom_qty*price_unit *engineer_salary_percent /100 + \
                                                product_uom_qty*price_unit*extra_salary_percent/100 + \
                                                product_uom_qty*price_unit*habe_percent/100 + \
                                                product_uom_qty*price_unit*social_insurance_rate/100) \
                                                    from labor_budget_line where parent_id in \
                                                        (select id from control_budget where project_id= %s and state in ('done','close'))"%(main.parent_project_id.id))
                res = self.env.cr.fetchone()[0] or 0.0
                main.labor_line_real = main.labor_line_limit - res

    
    @api.depends('lines_budgets')
    def _labor_line_limit(self):
        '''Хөрөнгө оруулалтын батлагдсан хяналтын төсвүүдийн ажиллах хүчний зардлын нийт дүНгээр үлдэгдэл тооцох
        '''
        for main in self:
            total = 0.0
            for line in main.lines_budgets:
                if line.sel_bud == 'labor':
                    total += line.price
            main.labor_line_limit = total

    
    def _equipment_line_total(self):
        '''Хөрөнгө оруулалтын батлагдахаар хүлээж буй хяналтын төсвүүдийн машин механизм зардлын нийт дүн
        '''
        for main in self:
            if main.parent_project_id.id:
                self.env.cr.execute("select sum(product_uom_qty*price_unit) from equipment_budget_line where parent_id in (select id from control_budget where project_id= %s and state in ('done','close','confirm'))"%(main.parent_project_id.id))
                res = self.env.cr.fetchone()[0] or 0.0
                main.equipment_line_total = main.equipment_line_limit - res

    
    def _equipment_line_real(self):
        '''Хөрөнгө оруулалтын батлагдсан хяналтын төсвүүдийн машин механизм зардлын нийт дүн
        '''
        for main in self:
            if main.parent_project_id.id:
                self.env.cr.execute("select sum(product_uom_qty*price_unit) from equipment_budget_line where parent_id in (select id from control_budget where project_id= %s and state in ('done','close'))"%(main.parent_project_id.id))
                res = self.env.cr.fetchone()[0] or 0.0
                main.equipment_line_real = main.equipment_line_limit - res

    
    @api.depends('lines_budgets')
    def _equipment_line_limit(self):
        '''Хөрөнгө оруулалтын батлагдсан хяналтын төсвүүдийн машин механизм зардлын нийт дүНгээр үлдэгдэл тооцох
        '''
        for main in self:
            total = 0.0
            for line in main.lines_budgets:
                if line.sel_bud == 'equipment':
                    total += line.price
            main.equipment_line_limit = total

    
    def _postage_line_total(self):
        '''Хөрөнгө оруулалтын батлагдахаар хүлээж буй хяналтын төсвүүдийн шууд зардлын нийт дүн
        '''
        for main in self:
            if main.parent_project_id.id:
                self.env.cr.execute("select sum(price) from postage_budget_line where parent_id in (select id from control_budget where project_id= %s and state in ('done','close','confirm'))"%(main.parent_project_id.id))
                res = self.env.cr.fetchone()[0] or 0.0
                main.postage_line_total = main.postage_line_limit - res

    
    def _postage_line_real(self):
        '''Хөрөнгө оруулалтын батлагдсан хяналтын төсвүүдийн шууд зардлын нийт дүн
        '''
        for main in self:
            if main.parent_project_id.id:
                self.env.cr.execute("select sum(price) from postage_budget_line where parent_id in (select id from control_budget where project_id= %s and state in ('done','close'))"%(main.parent_project_id.id))
                res = self.env.cr.fetchone()[0] or 0.0
                main.postage_line_real = main.postage_line_limit - res
    
    
    @api.depends('lines_budgets')
    def _postage_line_limit(self):
        '''Хөрөнгө оруулалтын батлагдсан хяналтын төсвүүдийн Шууд зардлын нийт дүНгээр үлдэгдэл тооцох
        '''
        for main in self:
            total = 0.0
            for line in main.lines_budgets:
                if line.sel_bud == 'postage':
                    total += line.price
            main.postage_line_limit = total
    
    
    def _other_line_total(self):
        '''Хөрөнгө оруулалтын батлагдахаар хүлээж буй хяналтын төсвүүдийн бусад зардлын нийт дүн
        '''
        for main in self:
            if main.parent_project_id.id:
                self.env.cr.execute("select sum(price) from other_cost_budget_line where parent_id in (select id from control_budget where project_id= %s and state in ('done','close','confirm'))"%(main.parent_project_id.id))
                res = self.env.cr.fetchone()[0] or 0.0
                main.other_line_total = main.other_line_limit - res

    
    def _other_line_real(self):
        '''Хөрөнгө оруулалтын батлагдсан хяналтын төсвүүдийн  бусад зардлын нийт дүн
        '''
        for main in self:
            if main.parent_project_id.id:
                self.env.cr.execute("select sum(price) from other_cost_budget_line where parent_id in (select id from control_budget where project_id= %s and state in ('done','close'))"%(main.parent_project_id.id))
                res = self.env.cr.fetchone()[0] or 0.0
                main.other_line_real = main.other_line_limit - res
    
    
    @api.depends('lines_budgets')
    def _other_line_limit(self):
        '''Хөрөнгө оруулалтын батлагдсан хяналтын төсвүүдийн бусад зардлын нийт дүНгээр үлдэгдэл тооцох
        '''
        for main in self:

            total = 0.0
            for line in main.lines_budgets:
                if line.sel_bud == 'other':
                    total += line.price
            main.other_line_limit = total
    
    
    def _carriage_cost(self):
        '''Хөрөнгө оруулалтын батлагдахаар хүлээж буй хяналтын төсвүүдийн тээврийн зардлын нийт дүн
        '''
        for main in self:
            if main.parent_project_id.id:
                self.env.cr.execute("select sum(price) from carriage_budget_line where parent_id in (select id from control_budget where project_id= %s and state in ('done','close','confirm'))"%(main.parent_project_id.id))
                res = self.env.cr.fetchone()[0] or 0.0
                main.carriage_cost = main.carriage_limit - res

    
    def _carriage_real(self):
        '''Хөрөнгө оруулалтын батлагдсан хяналтын төсвүүдийн  тээврийн зардлын нийт дүн
        '''
        for main in self:
            if main.parent_project_id.id:
                self.env.cr.execute("select sum(price) from carriage_budget_line where parent_id in (select id from control_budget where project_id= %s and state in ('done','close'))"%(main.parent_project_id.id))
                res = self.env.cr.fetchone()[0] or 0.0
                main.carriage_real = main.carriage_limit - res
    
    
    @api.depends('lines_budgets')
    def _carriage_limit(self):
        '''Хөрөнгө оруулалтын батлагдсан хяналтын төсвүүдийн тээврийн зардлын нийт дүНгээр үлдэгдэл тооцох
        '''
        for main in self:
            total = 0.0
            for line in main.lines_budgets:
                if line.sel_bud == 'carriage':
                    total += line.price
            main.carriage_limit = total
    
    def _get_total_investment(self):
        '''Нийт хөрөнгө оруулалт тооцох
        '''
        for main in self:
            total = 0.0
            for line in main.lines_budgets:
                total += line.price
            main.total_investment = total
            
    
    def _get_total_real(self):
        '''Нийт гүйцэтгэл
        '''
        for main in self:
            main.total_real = main.material_line_real + main.labor_line_real + main.equipment_line_real + main.postage_line_real + main.other_line_real + main.carriage_real
    
    def _get_modify_user(self):
        '''Тодотгол хийх хүн мөн эсэх
        '''
        emp_obj = self.env['hr.employee']
        emp = emp_obj.sudo().search([('user_id','=',self._uid)])
        res = {}
        for obj in self:
            if obj.parent_project_id.project_verifier == emp:
                obj.is_modify_user = True
    
    edit_click              = fields.Boolean('edit', default = True, store=True)
    modify_click            = fields.Boolean('edits', default = False)
    confirm                 = fields.Boolean('confimed ?', default = False)
    is_checker              = fields.Boolean('checkers?',default=False, compute=_get_bool)
    is_show_project_verifier= fields.Boolean('IS show' ,default=False , compute=_get_bool)
    is_comfirm_project      = fields.Boolean('confirm ?',default=False, compute =_is_comfirm_project)
    is_modify_user          = fields.Boolean('confirm user?',default=False,compute=_get_modify_user)
    
    total_investment        = fields.Float(u'Хөрөнгө оруулалт',compute=_get_total_investment)
    total_real              = fields.Float(u'Нийт төсвийн үлдэгдэл',compute=_get_total_real) 
    
    material_line_total     = fields.Float(u'Боломжит үлдэгдэл',compute=_material_line_total)
    labor_line_total        = fields.Float(u'Боломжит үлдэгдэл',compute=_labor_line_total)
    equipment_line_total    = fields.Float(u'Боломжит үлдэгдэл',compute=_equipment_line_total)
    postage_line_total      = fields.Float(u'Боломжит үлдэгдэл',compute=_postage_line_total)
    other_line_total        = fields.Float(u'Боломжит үлдэгдэл',compute=_other_line_total)
    carriage_cost           = fields.Float(u'Боломжит үлдэгдэл',compute=_carriage_cost)
    
    material_line_limit     = fields.Float(u'Материалын зардлын төсөвлөсөн дүн',        compute = _material_line_limit)
    labor_line_limit        = fields.Float(u'Ажиллах хүчний зардлын төсөвлөсөн дүн',    compute = _labor_line_limit)
    equipment_line_limit    = fields.Float(u'Машин механизмын зардлын төсөвлөсөн дүн',  compute = _equipment_line_limit)
    postage_line_limit      = fields.Float(u'Шууд зардлын төсөвлөсөн дүн',              compute = _postage_line_limit)
    other_line_limit        = fields.Float(u'Бусад зардлын төсөвлөсөн дүн',             compute = _other_line_limit)
    carriage_limit          = fields.Float(u'Тээврийн зардлын төсөвлөсөн дүн',          compute = _carriage_limit)
    
    material_line_real      = fields.Float(u'Үлдэгдэл',compute = _material_line_real, store=False)
    labor_line_real         = fields.Float(u'Үлдэгдэл',compute = _labor_line_real, store=False)
    equipment_line_real     = fields.Float(u'Үлдэгдэл',compute = _equipment_line_real, store=False)
    postage_line_real       = fields.Float(u'Үлдэгдэл',compute = _postage_line_real, store=False)
    other_line_real         = fields.Float(u'Үлдэгдэл',compute = _other_line_real, store=False)
    carriage_real           = fields.Float(u'Үлдэгдэл',compute = _carriage_real, store=False)
    
    @api.onchange('lines_budgets')
    def onchange_lines_budgets(self):
        for main in self:
            total = 0.0
            for line in main.lines_budgets:
                total += line.price
            main.update({
                        'total_investment':total,
                        })
    
    
    def confirm_button(self):
        '''Батлах 
            батлагдаагүй хөрөнгө оруулалтын хувилбаруудыг сонгогдоогүй болгох
        '''
        main_specification_confirmers   = self.env['main.specification.confirmers']
        employee                        = self.env['hr.employee']
        for line in self:
            employee_id                     = employee.sudo().search([('user_id','=',line._uid)])
            if line.is_comfirm_project == True:
                line.write({
                            'confirm':True,
                            'state':'confirm',
                            'modify_click':True
                            })
                for other_line in line.parent_project_id.main_line_ids:
                    if other_line.confirm == False:
                        other_line.write({
                                          'state':'cancel'
                                          })
                vals = {
                        'project_id'    : line.sudo().parent_project_id.id,
                        'confirmer'     : employee_id.id ,
                        'date'          : time.strftime('%Y-%m-%d %H:%M:%S'),
                        'role'          : 'project_verifier',
                        'state'         : 'confirmed',
                        }
                main_specification_confirmers   = main_specification_confirmers.create(vals)
                line.parent_project_id.state    = 'comfirm'
                return { 'type': 'ir.actions.client', 'tag': 'reload', }
            else:
                raise ValidationError(_(u'Төсөл дээр санал өгч дуусаагүй тул батлах боломжгүй'))
        
    
    def vote_button(self):
        '''Санал өгөх 
            Санал өгсөн мөр дээр санал өгсөн ажилтны нэрийг санал өгсөн ажилчид талбарт нэмэх
            сүүлийн хүн санал өгөхөд батлах хэрэглэгчид емайл илгээх
        '''
        main_specification_confirmers   = self.env['main.specification.confirmers']
        employee                        = self.env['hr.employee']
        employee_id                     = employee.sudo().search([('user_id','=',self._uid)])
        for project in self:
            vals = {
                    'project_id'    : project.parent_project_id.id,
                    'confirmer'     : employee_id.id ,
                    'date'          : time.strftime('%Y-%m-%d %H:%M:%S'),
                    'role'          : 'project_checkers',
                    'state'         : 'voted',
                    }
            main_specification_confirmers   = main_specification_confirmers.create(vals)
            ids = []
            for user in project.voters:
                ids.append(user.id)
            ids.append(employee_id.id)
            project.write({
                       'voters' :  [(6, 0, ids)]
                       })
            if project.is_comfirm_project == True:
                if not project.parent_project_id.project_verifier:
                    raise UserError(_('Cannot send email: This project not choose partner.'))
                for verifier in project.parent_project_id.project_verifier:
                    base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                    action_id = self.env['ir.model.data']._xmlid_to_res_id('project.open_view_project_all')[1]
                    db_name = request.session.db
                    email = verifier.work_email
                    subject = u'"%s" нэртэй төслийг батална уу.'%( project.parent_project_id.name)
                    body_html = u'''
                                    <h4>Сайн байна уу, Таньд энэ өдрийн мэнд хүргье! </h4>
                                    <p><li>"%s" нэртэй төслийг батална уу.</li></p>
                                    </br>
                                    <p><li>"%s" - н мэдээллийг<b><a href=%s/web?db=%s#id=%s&view_type=form&model=project.project&action=%s>Төсөл/Төслүүд</a></b> цонхоор дамжин харна уу.</li></p>
                                    <p>--</p>
                                    <p>Баярлалаа.</p>
                                '''%( project.parent_project_id.name,project.parent_project_id.name,base_url,
                                    db_name,
                                    project.parent_project_id.id,
                                    action_id)
             
                    if email and email.strip():
                        email_template = self.env['mail.template'].sudo().create({
                            'name': _('Followup '),
                            'email_from': self.env.user.company_id.email or '',
                            'model_id': self.env['ir.model'].search([('model', '=', 'project.project')]).id,
                            'subject': subject,
                            'email_to': email,
                            'lang': self.env.user.lang,
                            'auto_delete': True,
                            'body_html':body_html,
                          #  'attachment_ids': [(6, 0, [attachment.id])],
                        })
                        email_template.sudo().send_mail(project.parent_project_id.id)
        return { 'type': 'ir.actions.client', 'tag': 'reload', }
    
    
    def modify_button(self):
        '''Тодотгох 
            Тодотгож буй мөрийг хуулбарлан үүсгэх засах боломжтой
        '''
        main_specification = self.env['main.specification']
        main_specification_confirmers   = self.env['main.specification.confirmers']
        employee                        = self.env['hr.employee']
        employee_id                     = employee.sudo().search([('user_id','=',self._uid)])
        budget_line                     = self.env['main.line.budgets']
        ctx = dict(self._context)
        self.confirm = False
            
        vals = {
                'project_id'    : self.sudo().parent_project_id.id,
                'confirmer'     : employee_id.id ,
                'date'          : time.strftime('%Y-%m-%d %H:%M:%S'),
                'role'          : 'project_verifier',
                'state'         : 'modify',
                }
        line_vals = {
                     'parent_project_id'            :self.parent_project_id.id,
                     'name'                         :self.name,
                     'area'                         :self.area,
                     'control_budget_ids'           :[(6, 0, self.control_budget_ids.ids)],
                     'sales_revenue'                :self.sales_revenue,
                     'irr'                          :self.irr,
                     'roi'                          :self.roi,
                     'recovery_of_investment_time'  :self.recovery_of_investment_time,
                     'voters'                       :[(6, 0, self.voters.ids)],
                    #  'document'                     :[(6, 0, self.document.ids)],
                     'confirm'                      :False,
                     'text'                         :self.text,
                     'modify_click'                 :False,
                     'edit_click'                   :True,
                     'state'                        :'ready'
                     }
        ctx['l_name'] = self.name
        ctx_nolang = ctx.copy()
        ctx_nolang.pop('lang', None)
#         helpdesk = helpdesk.with_context(ctx_nolang).create(vals)
        
        result = super(main_pec, main_specification).with_context(ctx_nolang).create(line_vals)
        
        for line in self.lines_budgets:
            vals = {
                    'main_id':result.id,
                    'sel_bud':line.sel_bud,
                    'text':line.text,
                    'price':line.price,
                    'description':line.descrition
                    }
            budget_line = budget_line.create(vals)
        self.modify_click = False
        main_specification_confirmers   = main_specification_confirmers.create(vals)
        return { 'type': 'ir.actions.client', 'tag': 'reload', }
    
    
    def modify_confirm_button(self):
        '''Тодотгосөнг баталгаажуулах 
            Тодотгол оруулсан мөрийг баталгаажуулж засварлах боломжгүй болгох
        '''
        main_specification_confirmers = self.env['main.specification.confirmers']
        employee                        = self.env['hr.employee']
        employee_id                     = employee.sudo().search([('user_id','=',self._uid)])
        if self.material_line_real < 0:
            raise UserError(_('Материалын зардлын үлдэгдэл хасах дүнтэй орсон байна.'))
        if self.labor_line_real < 0:
            raise UserError(_('Ажиллах хүчний зардлын үлдэгдэл хасах дүнтэй орсон байна.'))
        if self.equipment_line_real < 0:
            raise UserError(_('Машин механизмын зардлын үлдэгдэл хасах дүнтэй орсон байна.'))
        if self.postage_line_real < 0:
            raise UserError(_('Шууд зардлын үлдэгдэл хасах дүнтэй орсон байна.'))
        if self.other_line_real < 0:
            raise UserError(_('Бусад зардлын үлдэгдэл хасах дүнтэй орсон байна.'))
        if self.carriage_real < 0:
            raise UserError(_('Тээврийн зардлын үлдэгдэл хасах дүнтэй орсон байна.'))
        self.write({
                      'state':'modify',
                      'modify_click':True,
                      'confirm':True,
                      })
        for line in self.parent_project_id.main_line_ids:
            if line.confirm == True and line.state != 'modify':
                line.write({'confirm': False})
        
        vals = {
                'project_id': self.sudo().parent_project_id.id,
                'confirmer' : employee_id.id ,
                'date'      : time.strftime('%Y-%m-%d %H:%M:%S'),
                'role'      : 'project_verifier',
                'state'     : 'modified',
                }
        main_specification_confirmers = main_specification_confirmers.create(vals)
        
        return { 'type': 'ir.actions.client', 'tag': 'reload', }
class main_specification_confirm(models.Model):
    '''Төслийн баталсан түүх 
    '''
    _name = 'main.specification.confirmers'
    _description = 'Main specifications confirmers'
    
    project_id  = fields.Many2one('project.project', string = 'Project')
    budget_id   = fields.Many2one('control.budget', string = 'Budget')
    confirmer   = fields.Many2one('hr.employee', string = 'Confirmer')
    date        = fields.Date(string = 'Date')
    
    role = fields.Selection([
                             ('project_checkers', u'Төслийн хянагч'),
                             ('project_verifier', u'Төсөл батлагч'),
                             ('evaluator', u'Төслийн үнэлэгч'),
                             ('budget_confirmer',u'Төсөв батлагч'),
                             ('budget_evaluater',u'Төсөв үнэлэгч')
                             ])
    state = fields.Selection([
                              ('new', u'Шинэ'),
                              ('confirmed', u'Баталсан'),
                              ('voted', u'Санал өгсөн'),
                              ('reject',u'Татгалзсан'),
                              ('evaluate',u'Үнэлсэн'),
                              ('transfer',u'Ацагласан'),
                              ('modify',u'Тодотгосон'),
                              ('modified',u'Баталгаажуулсан'),
                              ('sent',u'Илгээсэн'),
                              ('modified',u'Баталгаажуулсан'),
                              ])
    
class project_rate(models.Model):
    '''Төслийн Үнэлгээ 
    '''
    _name = 'project.rate'
    
    
    def _get_total(self):
        for rate in self:
            if rate.users:
                total = 0.0
                count = 0
                for line in rate.users:
                    total += line.percents
                    count += 1
                rate.total_percent = total/count
 
    perform_rate_id = fields.Many2one('rate.project.perform')
    project_id      = fields.Many2one('project.project',string = 'Project')
    perform         = fields.Many2one('evaluation.indicators','Rating Perform')
    percent         = fields.Integer('Percent')
    total_percent   = fields.Float('Total Percent',compute=_get_total)
    users           = fields.One2many('project.rate.user','rate_id')

class ProjectPerform(models.Model):
    '''Үнэлгээ 
    '''
    _name = 'project.perform'
    
 
    project_id      = fields.Many2one('project.project',string = 'Project')
    perform_new         = fields.Many2one('evaluation.indicators','Perform new')
    percent         = fields.Integer('Percent')
        
        
class project_rate_user(models.Model):
    '''Төслийн Үнэлгээний мөр ажилтан хувь
    '''
    _name = 'project.rate.user'
    
    rate_id = fields.Many2one('project.rate')
    employee = fields.Many2one('hr.employee',string = u'Ажилтан')
    percents = fields.Float(u'Хувь')






        
