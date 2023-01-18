# -*- coding: utf-8 -*-

import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from datetime import datetime, date, timedelta
# import datetime 
# import time 
# from datetime import date
# from datetime import date, datetime, timedelta

def set_deadline(self,child_task):
    '''
        холбоотой даалгаврын эхлэх дуусах огноог өөрчлөх requsive function
    '''
    for task in self:
        for task_id in child_task:
            date = datetime.strptime(task.date_deadline, '%Y-%m-%d')
            if task.date_deadline > task_id.task_date_start:
                task_id.write({
                              'task_date_start'    : (date +  timedelta(days=1)).strftime('%Y-%m-%d'),
                              'date_deadline' : (date +  timedelta(days=1)).strftime('%Y-%m-%d')
                              })
            child_ids = self.env['project.task'].search([('parent_task', '=', task_id.id)])
            if child_ids:
                set_deadline(task_id,child_ids)

class deadline_reason(models.Model):
    '''
        Төслийн даалгаварын үе
    '''
    _name = 'task.deadline.reason'
    _description ='Issue reason'
    _inherit = ['mail.thread']
    
    name        = fields.Char(u'Нэр',required = True, track_visibility='onchange')
    description = fields.Text(u'Тайлбар', track_visibility='onchange') 

    @api.model    
    def create(self,vals):
        '''
            Төслийн даалгаварын үе үүсгэх, нэрний давхардал шалгах
        '''
        tags = self.env['task.deadline.reason'].search([('name', '=', vals.get('name'))])
        if not tags:
            project_id = super(deadline_reason, self).create(vals)
            return project_id
        else:
            raise ValidationError(_(u'Ийм нэртэй Төслийн даалгаварын үе үүссэн байна !'))

    @api.multi    
    def unlink(self):
        '''
            Төслийн даалгаварын үе устгах, Төсөлд ашигласан эсэхийг шалгах
        '''
        tasks = self.env['task.deadline.reason.line'].search([('reason_id','=',self.id)])
        if len(tasks)==0:
            pass
            res = super(deadline_reason, self).unlink()
            return res
        else: 
            raise ValidationError(_(u'Энэхүү мэдээллийг бүртгэлд ашигласан тул устгах боломжгүй!'))
    
class deadline_reason_line(models.Model):
    '''
        Даалгаварын хугацаа хойшилсон шалтгаан
    '''
    
    _name = 'task.deadline.reason.line'
    
    task_id     = fields.Many2one('project.task')
    reason_id  = fields.Many2one('task.deadline.reason',required = True,string=u'Шалтгаан')
    description = fields.Text(string=u'Тайлбар')
    count       = fields.Float(string=u'Хугацаа хойшлуулсан хоногийн тоо',required = True)
    

    @api.multi
    def unlink(self):
        '''
            Даалгаварын хугацаа хойшилсон шалтгаан устгах даалгаварт ашигласан бол устгах боломжгүй
        '''
        for order in self:
            if order.task_id:
                raise UserError(_('Устгах боломжгүй'))
        return super(deadline_reason_line, self).unlink()

class task_stages_history(models.Model):
    _name = 'task.stages.history'
    
    stages      = fields.Many2one('project.task.type', index=True, string = 'Stages')
    task_id     = fields.Many2one('project.task', index=True,string='Task')
    description = fields.Char('Description',required=True)
    unit_amount = fields.Float('time',required=True)
    date        = fields.Date('Date',required=True)
    
class task_confirm_users(models.Model):
    '''
        Даалгаварын Баталсан түүх
    '''
    _name = 'task.confirm.users'
    _description = 'Task Confirm User'
    
    task_id     = fields.Many2one('project.task', index=True, string = 'Project')
    confirmer   = fields.Many2one('hr.employee', index=True, string = 'Confirmer')
    date        = fields.Date(string = 'Date')
    role        = fields.Selection([('confirmer', u'Батлагч')])
    state       = fields.Selection([('confirmed', u'Баталсан')])

class task_rating_users(models.Model):
    '''
        Даалгаварын Үнэлсэн түүх
    '''
    _name = 'task.rating.users'
    _description = 'Task Rating User'
    
    task_id     = fields.Many2one('project.task', index=True, string = 'Project')
    confirmer   = fields.Many2one('hr.employee', index=True, string = 'Confirmer')
    percent     = fields.Integer('Percent',default=0)
    date        = fields.Date(string = 'Date')
    role        = fields.Selection([('rating_user', u'Үнэлэгч')])
    state       = fields.Selection([('rating',u'Үнэлсэн')])
    
class task_tarif_line(models.Model):
    _name = 'task.tarif.line'
    '''
        Даалгаварын Тарифт ажил
    '''
    @api.multi
    def _get_price(self):
        total = 0.0
        for line in self:
            total = line.work_id.unit_price
            line.price= total
    
    @api.multi
    def _get_total_price(self):
        total = 0.0
        for line in self:
            total = line.qty * line.price
            line.total_price = total
    
    task_id = fields.Many2one('project.task', index=True,string = 'Task')
    work_id = fields.Many2one('work.service', index=True, string = 'Work')
    qty     = fields.Integer(string = 'Quantity',default =1)
    price   = fields.Float(string = 'Price',compute=_get_price)
    total_price = fields.Float(string = 'Total price',compute=_get_total_price)
    agreed_price = fields.Float(string = 'Agreed price')
    description = fields.Char(string = 'Description')
    
    @api.onchange('price','qty')
    def onchange_price(self):
        '''
            Нийт үнэ тооцох
        '''
        total = 0.0
        for line in self:
            total = line.qty * line.price
            line.total_price = total
    
    @api.onchange('work_id')
    def onchange_work_id(self):
        '''
            Ажил үйлчилгээний үнэ
        '''
        total = 0.0
        for line in self:
            total = line.work_id.unit_price
            line.update({
                         'price':total
                         }) 
    
class ProjecTaskInherit(models.Model):
    _inherit = 'project.task'
    _order ="create_date desc"
    '''
        Даалгавар
    '''
    @api.multi
    @api.depends('task_work_service')
    def _get_total(self):
        '''
            тарифт ажлын Нийт үнэ тооцох
        '''
        for task in self:
            price = 0.0
            for work in task.task_work_service:
                price += work.unit_price
                task.update({
                             'tariff_price' : price 
                             })
    
    @api.multi
    def _is_user(self):
        '''
            Даалгавар хариуцагч эсэх мөн хариуцагчтай төлөвт байгаа эсэх
        '''
        for task in self:
            task.is_user = False
            if task.user_id.id == task._uid and task.task_state == 't_user':
                task.is_user = True


    
    @api.multi
    def _is_confirm_user(self):
        '''
            Даалгавар хариуцагч эсэх мөн хариуцагчтай төлөвт байгаа эсэх
        '''
        for task in self:
            task.is_user = False
            if task.user_id.id == task._uid and task.task_state == 't_user':
                task.is_user = True
    
    def _is_show_confirm_user(self):
        '''
            Батлах хэрэглэгчид харуулах эсэх баталсан бол харуулахгүй
        '''
        emp_obj = self.env['hr.employee']
        emp = emp_obj.search([('user_id','=',self._uid)])
        for project in self:
            project.is_show_confirm_user = False
            if emp in project.controller:
                project.is_show_confirm_user = True
            for users in project.task_users:
                if emp == users.confirmer and users.role == 'confirmer':
                    project.is_show_confirm_user = False
            if project.task_state != 't_confirm':
                project.is_show_confirm_user = False
            
    def _is_show_rating_user(self):
        '''
            Даалгавар үнэлэгч мөн эсэх үнэлсэн бол харуулахгүй
        '''
        emp_obj = self.env['hr.employee']
        emp = emp_obj.search([('user_id','=',self._uid)])
        for project in self:
            project.is_show_rating_user = False
            if emp in project.rating_users:
                project.is_show_rating_user = True
            for users in project.task_rating_users:
                if emp == users.confirmer and users.role == 'rating_user':
                    project.is_show_rating_user = False
            if project.task_state != 't_evaluate':
                project.is_show_rating_user = False
            
    @api.multi
    def _is_comfirm(self):
        '''
            баталж дууссан эсэх
        '''
        for task in self:
            count = 0
            task.is_confirm = False
            for checker in task.controller:
                for user in task.task_users:
                    if checker == user.confirmer and user.role == 'confirmer':
                        count += 1
            if count == len(task.controller):
                task.is_confirm = True
    
    @api.multi
    def _is_rating(self):
        '''
            Үнэлж дууссан эсэх
        '''
        count = 0
        for task in self:
            task.is_rating = False
            for checker in task.rating_users:
                for user in task.task_rating_users:
                    if checker == user.confirmer and user.role == 'rating_user':
                        count += 1
            if count == len(task.rating_users):
                task.is_rating = True
    
    @api.multi
    def _get_total_percent(self):
        '''
            Үнэлгээний дундаж
        '''
        for task in self:
            total = 0
            percent = 0
            count = 0
            if task.task_rating_users:
                for user in task.task_rating_users:
                    percent += user.percent
                    count += 1
                total = percent/count
            task.total_percent = total
    
    @api.multi
    def _is_show_evaluate_button(self):
        '''
            Үнэлэх төлөвт оруулах товч харагдах эсэх
        '''
        for task in self:
            if task.task_type == 'tariff_task' and task.task_state == 't_start':
                task.is_show_evaluate_button = True
            else:
                task.is_show_evaluate_button = False
            
    @api.multi
    def _is_show_user_button(self):
        '''
            Хариуцагчид оноох товч харагдах эсэх
        '''
        for task in self:
            if task.task_type == 'normal' and task.task_state == 't_new':
                task.is_show_user_button = True
            else:
                if task.task_type != 'normal'and task.task_state == 't_cheapened':
                    task.is_show_user_button = True
                else:
                    task.is_show_user_button = False
    
    @api.multi
    def _is_show_done(self):
        '''
            Хянах товч харагдах эсэх
        '''
        emp_obj = self.env['hr.employee']
        emp = emp_obj.search([('user_id','=',self._uid)])
        employees=[]
        for task in self:
            if task.task_verifier:
                if emp in task.task_verifier:
                    task.is_show_done = True
                else:
                    task.is_show_done = False
            else:
                for user in task.verify_user_ids:
                    employees.append(user.employee_id.id)
                if emp.id in task.task_verifier_users.ids:
                    if emp.id not in employees :
                        task.is_show_done = True
                    else:
                        task.is_show_done = False
                else:
                    task.is_show_done = False
    @api.multi
    def _is_user_and_verifier(self):
        '''
            Даалгавар хариуцгагч , хянагч , төслийн менежер мөн эсэх
        '''
        emp_obj = self.env['hr.employee']
        emp = emp_obj.search([('user_id','=',self._uid)])
        for task in self:
            if task.user_id.id == task._uid:
                task.is_user_and_verifier = True
            else:
                if task.project_id.sudo().user_id.id == task._uid:
                    task.is_user_and_verifier = True
                else:
                    task.is_user_and_verifier = False
    
    def _hours_get(self):
        '''
            ажилласан цагийн явц тооцоолох
        '''
        for task in self:
            progress = 0.0
            total = 0.0
            for line in task.timesheet_ids:
                total += line.unit_amount
            if task.planned_hours > 0.0:
                progress = round(min(100.0 * total / task.planned_hours, 99.99),2)
            # TDE CHECK: if task.state in ('done','cancelled'):
            if task.task_state == 't_done':
                progress = 100.0
            task.progress1 = progress
            
    def _count_date_deadline(self):
        '''
            Хугацаа хойшлуулсан шалтгаан оруулсан хоногын тоо тооцоолох
        '''
        for task in self:
            count = 0.0
            for line in task.deadline_task:
                count += line.count
            task.count_date_deadline = count
            
    def _get_phone(self):
        '''
            захиалгагч ажилтны ажлын гар утас
        '''
        for task in self:
            task.phone = task.customer_id.mobile_phone
    
    def _get_email(self):
        '''
            захиалгагч ажилтны ажлын емайл
        '''
        for task in self:
            task.email = task.customer_id.work_email
    
    def _is_customer_id(self):
        '''
            захиалгагч ажилтан мөн эсэх
        '''
        emp_obj = self.env['hr.employee']
        emp = emp_obj.search([('user_id','=',self._uid)])
        for task in self:
            if emp in task.customer_id:
                task.is_customer_id = True
            else:
                task.is_customer_id = False
    def _is_task_user(self):

        for user in self:
            if user.task_verifier:
                user.is_task_user = True
            else:
                user.is_task_user = False
    def _add_followers(self,user_ids):
        '''Add followers
        '''
        self.message_subscribe_users(user_ids=user_ids)
            
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
                                   ('t_back',u'Хойшлуулсан')],default = 't_new',string='State', track_visibility='onchange')
    
#     child_task              = fields.Many2many('project.task','project_task_child_ids','parent_task_id','tasks_id', string = 'Child Task', compute=_get_parent)
    task_work_service       = fields.Many2many('work.service','project_task_work_sevice_id','work_id','task_id',string = 'Work service')
    parent_task             = fields.Many2one('project.task', index=True,string = 'Parent Task', track_visibility='onchange')
    work_graph              = fields.Many2one('project.task', index=True, string = 'Work Graph')
    project_stage           = fields.Many2one('project.stage', index=True, string = 'Project Stage', track_visibility='onchange')
    work_name               = fields.Char('Work Name', track_visibility='onchange')
    back_state              = fields.Char('back_stage')
    work_description        = fields.Text('Work Description', track_visibility='onchange')
    description             = fields.Text('Description', track_visibility='onchange')
    is_user                 = fields.Boolean('is user',compute = _is_user)
    
    is_confirm_user         = fields.Boolean('is confirm user',compute = _is_confirm_user)
    is_confirm              = fields.Boolean('is confirm',compute = _is_comfirm)
    is_rating               = fields.Boolean('is rating',compute = _is_rating)
    is_show_confirm_user    = fields.Boolean('is show rating user',compute = _is_show_confirm_user)
    is_show_rating_user     = fields.Boolean('is show rating user',compute = _is_show_rating_user)
    is_show_evaluate_button = fields.Boolean('is show evaluate', compute = _is_show_evaluate_button)
    is_show_user_button     = fields.Boolean('is show user', compute = _is_show_user_button)
    is_show_done            = fields.Boolean('is show done',compute = _is_show_done)
    is_user_and_verifier    = fields.Boolean(string = 'is user and verifier', compute = _is_user_and_verifier)
    tariff_price            = fields.Float('Tariff price' , compute = _get_total,store=True)
    agreed_price            = fields.Float('Agreed price')
    percent                 = fields.Integer('Rating percent')
    total_percent           = fields.Integer('Total percent',compute = _get_total_percent)
    flow                    = fields.Integer('Flow', track_visibility='onchange')
    stages                  = fields.One2many('task.stages.history','task_id')
    task_users              = fields.One2many('task.confirm.users','task_id','Task users')
    task_rating_users       = fields.One2many('task.rating.users','task_id','Task users')
    deadline_task           = fields.One2many('task.deadline.reason.line','task_id')
    progress1               = fields.Float('Ажилласан цагийн явц (%)',compute=_hours_get)
    date_deadline           = fields.Date('Deadline', select=True, copy=False,track_visibility='onchange')
    count_date_deadline     = fields.Float(u'Хойшилсон хоногийн тоо',compute=_count_date_deadline)
    tarif_line              = fields.One2many('task.tarif.line','task_id',string = 'Tariff line')
    customer_id             = fields.Many2one('hr.employee', 'Customer name', index=True, track_visibility='onchange')
    customer_department     = fields.Many2one('hr.department', 'Customer Department', index=True, track_visibility='onchange')
    phone                   = fields.Char('Phone',compute=_get_phone)
    email                   = fields.Char('Email',compute=_get_email)
    planned_start_date      = fields.Date('Planned start date',readonly = True)
    planned_end_date        = fields.Date('Planned end date',readonly = True)
    ticket_id               = fields.Many2one('crm.helpdesk', index=True,string = u'Тикет')
    is_customer_id          = fields.Boolean(compute=_is_customer_id,string = 'Customer')
    done_date = fields.Date(string="Done date", readonly=True, track_visibility='always', copy=False)
    operation_ids = fields.One2many('task.operation','task_id',string="Operation")
    verify_user_ids = fields.One2many('task.verify.users','task_id',string="task verify users")
    is_task_user = fields.Boolean(string="Bool",compute=_is_task_user)
    @api.onchange('customer_id')
    def onchange_customer_id(self):
        self.update({
                    'customer_department':self.customer_id.department_id.id
                    })
     
    @api.one
    def copy(self, default=None):
        if default is None:
            default = {}
        if self.task_state == 't_new':
            newtask = super(ProjecTaskInherit, self).copy(default=default)
            newtask.write({
                            'task_date_start':self.task_date_start,
                            'date_deadline':self.date_deadline,
                            })
        else : 
            raise ValidationError(_(u'Шинэ төлөвтөй үед хуулбарлан үүсгэх боломжтой'))
        return newtask

    @api.onchange('task_work_service')
    def onchange_task_work_service(self):
        '''
            тохирсон үнэ талбарт ажил үйлчилгээний үнэ оноох
        '''
        for task in self:
            price = 0.0
            if task.task_work_service:
                for work in task.task_work_service:
                    price += work.unit_price
                    task.update({
                                 'agreed_price' : price 
                                 })
            else:
                task.update({
                                 'agreed_price' : price 
                                 })
    @api.multi
    def write(self, vals):
        '''
            Дагагчид нэмэх
                Хариуцагчтай төлөв дээр хариуцагч солиход емайл илгээх
                Дууссан төлөвт ороход төслийн менежерт дуусан талаар емайл илгээх, Холбоотой даалгаварын хариуцагчид мөн емайл илгээх
                хавсралт оруулах шаардлагатай эсэхийг тооцох
        '''
        
        result = super(ProjecTaskInherit, self).write(vals)
        state = ''
        description = ''
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        action_id = self.env['ir.model.data'].get_object_reference('project', 'action_view_task')[1]
        db_name = request.session.db
        
        if vals and 'user_id' in vals:
            self.project_id.sudo()._add_followers(vals['user_id'])
            # self.project_id.sudo().add_raci_users('I',vals['user_id'])
            self.sudo()._add_followers(vals['user_id'])
            if self.task_state in ('t_user','t_start'):
                if self.task_state == 't_new':
                    state =  u'Шинэ'
                if self.task_state == 't_cheapen':
                    state =  u'Үнэ тохирох'
                if self.task_state == 't_cheapened':
                    state =  u'Үнэ тохирсон'
                if self.task_state == 't_user':
                    state =  u'Хариуцагчтай'
                if self.task_state == 't_start':
                    state =  u'Хийгдэж буй'
                if self.task_state == 't_control':
                    state =  u'Хянах'
                if self.task_state == 't_confirm':
                    state =  u'Батлах'
                if self.task_state == 't_evaluate':
                    state =  u'Үнэлэх'
                if self.task_state == 't_done':
                    state =  u'Дууссан'
                if self.task_state == 't_cancel':
                    state =  u'Цуцалсан'
                if self.task_state == 't_back':
                    state =  u'Хойшлуулсан'
                if self.description:
                    description = self.description
                user = self.env['res.users'].search([('id', '=',vals['user_id'])])
                email = user.login
                subject = u'Таньд "%s" төслийн "%s" таскыг гүйцэтгэх захиалга ирлээ.'%(self.project_id.name , self.name)
                body_html = u'''
                            <h4>Сайн байна уу ?, 
                            Таньд энэ өдрийн мэнд хүргье! 
                            Таньд %s" төслийн "%s" таскыг гүйцэтгэх захиалга ирлээ.</h4>
                            <p><li><b>Төсөл: </b>%s</li></p>
                            <p><li><b>Даалгавар: </b>%s</li></p>
                            <p><li><b>Эхлэх огноо: </b>%s</li></p>
                            <p><li><b>Дуусах огноо: </b>%s</li></p>
                            <p><li><b>Хариуцагч хэлтэс: </b>%s</li></p>
                            <p><li><b>Төлөв: </b>%s</li></p>
                            <p><li><b>Даалгаврын дэлгэрэнгүй: </b>%s</li></p>
                            </br>
                            <p><li>"%s" / "%s" -н мэдээллийг <b><a href=%s/web?db=%s#id=%s&view_type=form&model=project.task&action=%s>Төсөл/Даалгаварууд</a></b> цонхоор дамжин харна уу.</li></p>
                            <p>--</p>
                            <p>Энэхүү мэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
                            <p>Баярлалаа..</p>
                        '''%( self.project_id.name , self.name,self.project_id.name,self.name,self.task_date_start,self.date_deadline,
                                      self.department_id.name,state,description,self.project_id.name,self.name,
                                        base_url,
                                        db_name,
                                        self.id,
                                        action_id)
                if email and email.strip():
                    email_template = self.env['mail.template'].sudo().create({
                        'name': _('Followup '),
                        'email_from': self.env.user.company_id.email or '',
                        'model_id': self.env['ir.model'].search([('model', '=', 'project.task')]).id,
                        'subject': subject,
                        'email_to': email,
                        'lang': self.env.user.lang,
                        'auto_delete': True,
                        'body_html':body_html,
                    })
                    email_template.sudo().send_mail(self.id)
        
        if vals and 'customer_id' in vals:
            user = self.env['hr.employee'].search([('id', '=',vals['customer_id'])])
            if user:
                self.project_id.sudo()._add_followers(user.user_id.id)
                # self.project_id.sudo().add_raci_users('I',user.user_id.id)
                self.sudo()._add_followers(user.user_id.id)
        if vals and 'task_verifier' in vals:
            user = self.env['hr.employee'].search([('id', '=',vals['task_verifier'])])
            if user:
                self.project_id.sudo()._add_followers(user.user_id.id)
                self.sudo()._add_followers(user.user_id.id)
                # self.project_id.sudo().add_raci_users('I',user.user_id.id)
            
        if vals and 'project_id' in vals:
            project = self.env['project.project'].search([('id', '=',vals['project_id'])])
            self.sudo()._add_followers(project.user_id.id)
            project.sudo()._add_followers(self.department_id.manager_id.user_id.id)
            project.sudo()._add_followers(self.user_id.id)
            project.sudo()._add_followers(self.customer_id.user_id.id)
            
        if vals and 'department_id' in vals:
            dep = self.env['hr.department'].search([('id', '=',vals['department_id'])])
            self.sudo()._add_followers(dep.manager_id.user_id.id)
            self.project_id.sudo()._add_followers(dep.manager_id.user_id.id)
        if vals and 'task_verifier_users' in vals:
            for emp in self.task_verifier_users:
                if emp.user_id:
                    self._add_followers(emp.user_id.id) 
                    self.project_id.sudo()._add_followers(emp.user_id.id)
                    # self.project_id.sudo().add_raci_users('I',emp.user_id.id)   
                    
        if vals and 'task_state' in vals:
            child_ids = self.env['project.task'].search([('parent_task', '=', self.id)])
            
            if vals['task_state'] == 't_confirm':
                if not self.document_line:
                    raise ValidationError(_(u'Батлах ажилчидад илгээхээс өмнө хавсралт оруулах шаардлагатай'))
                else:
                    for user in self.controller:
                        self.sudo()._add_followers(user.user_id.id)
                        # self.project_id.sudo().add_raci_users('C',user.user_id.id)
                        self.project_id.sudo()._add_followers(user.user_id.id)
            
            if vals['task_state'] == 't_evaluate' and self.task_type in ('work_task','work_graph'):
                if not self.work_document:
                    raise ValidationError(_(u'Дараагийн төлөвт шилжүүлэхээс өмнө батлагдсан хавсралт оруулах шаардлагатай'))
            
            if vals['task_state'] == 't_evaluate':
                for user in self.rating_users:
                    self.sudo()._add_followers(user.user_id.id)
                    self.project_id.sudo()._add_followers(user.user_id.id)
                    # self.project_id.sudo().add_raci_users('I',user.user_id.id)
            
            if vals['task_state'] == 't_done' and self.project_id:
                employee = self.env['hr.employee']
                employee_id = employee.sudo().search([('user_id','=',self.project_id.user_id.id)])
                
                email = employee_id.work_email
                if self.task_state == 't_new':
                    state =  u'Шинэ'
                if self.task_state == 't_cheapen':
                    state =  u'Үнэ тохирох'
                if self.task_state == 't_cheapened':
                    state =  u'Үнэ тохирсон'
                if self.task_state == 't_user':
                    state =  u'Хариуцагчтай'
                if self.task_state == 't_start':
                    state =  u'Хийгдэж буй'
                if self.task_state == 't_control':
                    state =  u'Хянах'
                if self.task_state == 't_confirm':
                    state =  u'Батлах'
                if self.task_state == 't_evaluate':
                    state =  u'Үнэлэх'
                if self.task_state == 't_done':
                    state =  u'Дууссан'
                if self.task_state == 't_cancel':
                    state =  u'Цуцалсан'
                if self.task_state == 't_back':
                    state =  u'Хойшлуулсан'
                if self.description:
                    description = self.description
                subject = u'"%s" төслийн "%s" ID-тай "%s" таск дууссан төлөвт орлоо.'%( self.project_id.name,self.id, self.name)
                body_html = u'''
                                <h4>Сайн байна уу ?, 
                                    Таньд энэ өдрийн мэнд хүргье! 
                                    "%s" төслийн "%s" ID-тай "%s" таск дууссан төлөвт орлоо.</h4>
                                    <p><li><b>Төсөл: </b>%s</li></p>
                                    <p><li><b>Даалгавар: </b>%s</li></p>
                                    <p><li><b>Эхлэх огноо: </b>%s</li></p>
                                    <p><li><b>Дуусах огноо: </b>%s</li></p>
                                    <p><li><b>Хариуцагч хэлтэс: </b>%s</li></p>
                                    <p><li><b>Хариуцагч: </b>%s</li></p>
                                    <p><li><b>Төлөв: </b>%s</li></p>
                                    <p><li><b>Даалгаврын дэлгэрэнгүй: </b>%s</li></p>
                                    </br>
                                    <p><li>"%s" / "%s" - н мэдээллийг <b><a href=%s/web?db=%s#id=%s&view_type=form&model=project.task&action=%s>Төсөл/Даалгаварууд</a></b> цонхоор дамжин харна уу.</li></p>
                                    <p>--</p>
                                    <p>Энэхүү мэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
                                    <p>Баярлалаа..</p>
                            '''%( self.project_id.name,self.id, self.name,self.project_id.name,self.name,self.task_date_start,self.date_deadline,
                                      self.department_id.name,self.user_id.name,state,description,self.project_id.name,self.name,
                                        base_url,
                                        db_name,
                                        self.id,
                                        action_id)
         
                if email and email.strip():
                    email_template = self.env['mail.template'].sudo().create({
                        'name': _('Followup '),
                        'email_from': self.env.user.company_id.email or '',
                        'model_id': self.env['ir.model'].search([('model', '=', 'project.task')]).id,
                        'subject': subject,
                        'email_to': email,
                        'lang': self.env.user.lang,
                        'auto_delete': True,
                        'body_html':body_html,
                    })
                    email_template.sudo().send_mail(self.id)
            if vals['task_state'] == 't_done' and child_ids:
                for task in child_ids:
                    employee = self.env['hr.employee']
                    employee_id = employee.sudo().search([('user_id','=',task.user_id.id)])
                    email = employee_id.work_email
                    if task.task_state == 't_new':
                       state =  u'Шинэ'
                    if task.task_state == 't_cheapen':
                       state =  u'Үнэ тохирох'
                    if task.task_state == 't_cheapened':
                       state =  u'Үнэ тохирсон'
                    if task.task_state == 't_user':
                       state =  u'Хариуцагчтай'
                    if task.task_state == 't_start':
                       state =  u'Хийгдэж буй'
                    if task.task_state == 't_control':
                       state =  u'Хянах'
                    if task.task_state == 't_confirm':
                       state =  u'Батлах'
                    if task.task_state == 't_evaluate':
                       state =  u'Үнэлэх'
                    if task.task_state == 't_done':
                       state =  u'Дууссан'
                    if task.task_state == 't_cancel':
                       state =  u'Цуцалсан'
                    if task.task_state == 't_back':
                       state =  u'Хойшлуулсан'
                    if task.description:
                        description = task.description
                    subject = u'Таны "%s" даалгаварын өмнө хийгдэх "%s" даалгавар дууссан төлөвт орлоо.'%( task.name,self.name)
                    body_html = u'''
                                    <h4>Сайн байна уу ?, 
                                    Таньд энэ өдрийн мэнд хүргье! 
                                    Таны "%s" даалгаварын өмнө хийгдэх "%s" даалгавар дууссан төлөвт орлоо.</h4>
                                    <p><li><b>Төсөл: </b>%s</li></p>
                                    <p><li><b>Даалгавар: </b>%s</li></p>
                                    <p><li><b>Эхлэх огноо: </b>%s</li></p>
                                    <p><li><b>Дуусах огноо: </b>%s</li></p>
                                    <p><li><b>Хариуцагч хэлтэс: </b>%s</li></p>
                                    <p><li><b>Хариуцагч: </b>%s</li></p>
                                    <p><li><b>Төлөв: </b>%s</li></p>
                                    <p><li><b>Холбоотой даалгавар: </b>%s</li></p>
                                    <p><li><b>Даалгаврын дэлгэрэнгүй: </b>%s</li></p>
                                    </br>
                                    <p><li>"%s" / "%s" - н мэдээллийг <b><a href=%s/web?db=%s#id=%s&view_type=form&model=project.task&action=%s>Төсөл/Даалгаварууд</a></b> цонхоор дамжин харна уу.</li></p>
                                    <p>--</p>
                                    <p>Энэхүү мэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
                                    <p>Баярлалаа..</p>
                                '''%(task.name,self.name, self.project_id.name,task.name,task.task_date_start,task.date_deadline,
                                      task.department_id.name,task.user_id.name,state,self.name,description,self.project_id.name,task.name,
                                        base_url,
                                        db_name,
                                        task.id,
                                        action_id)
             
                    if email and email.strip():
                        email_template = self.env['mail.template'].sudo().create({
                            'name': _('Followup '),
                            'email_from': self.env.user.company_id.email or '',
                            'model_id': self.env['ir.model'].search([('model', '=', 'project.task')]).id,
                            'subject': subject,
                            'email_to': email,
                            'lang': self.env.user.lang,
                            'auto_delete': True,
                            'body_html':body_html,
                        })
                        email_template.sudo().send_mail(self.id)
        if vals and 'date_deadline' in vals:
            child_ids = self.env['project.task'].search([('parent_task', '=', self.id)])
            if child_ids:
                set_deadline(self,child_ids)
        if  vals.get('date_deadline') or vals.get('task_date_start'):
            if self.date_deadline < self.task_date_start:                
                raise ValidationError(_(u'Даалгаврын дуусах огноо эхлэх огнооноос бага байна!!!'))
        
        if  vals.get('date_deadline') or vals.get('task_date_start'):
            is_verifier = False
            emp_obj = self.env['hr.employee']
            emp = emp_obj.search([('user_id','=',self._uid)])
            if emp in self.task_verifier_users or self.env.user.has_group('project.group_project_admin'):
                is_verifier =True
            if not is_verifier:
                raise ValidationError(_(u'Даалгаврын дуусах огноог өөрчлөх эрхгүй байна !!!'))

        return result
    
    @api.model
    def create(self, vals):
        '''
            Үүсгэх , дагагчид нэмэх
        '''
        result = super(ProjecTaskInherit, self).create(vals)
        if vals.get('date_deadline') and vals.get('task_date_start') and vals.get('date_deadline') < vals.get('task_date_start'):    
            date_deadline = datetime.strptime(vals.get('date_deadline'), '%Y-%m-%d')
            date_start = datetime.strptime(vals.get('task_date_start'), '%Y-%m-%d')
            if date_deadline <date_start:            
                raise ValidationError(_(u'Даалгаврын дуусах огноо эхлэх огнооноос бага байна!!!'))
#             ADD FOLLOWERS
        result.project_id.sudo()._add_followers(result.department_id.manager_id.user_id.id)
        result.project_id.sudo()._add_followers(result.user_id.id)
        # result.project_id.sudo().add_raci_users('I',result.task_verifier.user_id.id)
        # result.project_id.sudo().add_raci_users('C',result.controller.user_id.id)
        result.project_id.sudo()._add_followers(result.task_verifier.user_id.id)
        # result.project_id.sudo().add_raci_users('I',result.task_verifier.user_id.id)
        for emp in result.task_verifier_users:
            if emp.user_id:
                result.sudo()._add_followers(emp.user_id.id)
                # result.project_id.sudo().add_raci_users('I',emp.user_id.id)
        result.project_id.sudo()._add_followers(result.customer_id.user_id.id)
        # result.project_id.sudo().add_raci_users('I',result.customer_id.user_id.id)
        result.sudo()._add_followers(result.user_id.id)
        result.sudo()._add_followers(result.project_id.user_id.id)
        result.sudo()._add_followers(result.customer_id.user_id.id)
        result.sudo()._add_followers(result.department_id.manager_id.user_id.id)
        
        return result
    
    @api.multi
    def unlink(self):
        for line in self:
            if line.task_state != 't_new':
                raise ValidationError(_(u'Ноорог төлөвтөй үед устгах боломжтой'))
        else:
            return super(ProjecTaskInherit, self).unlink()
    
    @api.multi
    def action_test(self):
        tasks = self.env['project.task'].search([('planned_start_date', '=', False)])
        for task in tasks:
            if task.task_date_start:
                task.write({'planned_start_date':task.task_date_start
                            })
            if task.date_deadline:
                task.write({
                            'planned_end_date':task.date_deadline
                            })
                
    @api.onchange('project_id')
    def onchange_project_id(self):
        '''
            Төсөл солигдогохд домайн дамжуулах
        '''
        return {'domain': {'parent_task'   :[('project_id','=',self.project_id.id)],
                           'project_stage':[('id','in',self.project_id.project_stage.ids)]}}
    
    @api.onchange('parent_task')
    def onchange_parent_task(self):
        '''
            Эцэг даалгавар сонгоход эцэг даалгаварийн дуусах огноогоор даалгаврын эхлэх огноог тавих
        '''
        for task in self:
            if task.parent_task:
                task.update({
                            'task_date_start':task.parent_task.date_deadline
                            })

    @api.multi
    def action_cheapen(self):
        '''
            Үнэ тохирох төлөвт оруулах
        '''
        self.write({
                    'task_state':'t_cheapen',
                    'planned_start_date':self.task_date_start,
                    'planned_end_date':self.date_deadline
                    })
        
    @api.multi
    def action_cheapened(self):
        '''
            Үнэ тохирсон төлөвт оруулах
        '''
        self.write({'task_state':'t_cheapened'})
    
        
    @api.multi
    def action_user(self):
        '''
            Хариуцагчид оноох
                Хариуцагчид емайл илгээх хоосон байвал салбарын менежерт емайл илгээх
        '''
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        action_id = self.env['ir.model.data'].get_object_reference('project', 'action_view_task')[1]
        db_name = request.session.db
        state = ''
        description = ''
        if self.task_state == 't_new':
           state =  u'Шинэ'
        if self.task_state == 't_cheapen':
           state =  u'Үнэ тохирох'
        if self.task_state == 't_cheapened':
           state =  u'Үнэ тохирсон'
        if self.task_state == 't_user':
           state =  u'Хариуцагчтай'
        if self.task_state == 't_start':
           state =  u'Хийгдэж буй'
        if self.task_state == 't_control':
           state =  u'Хянах'
        if self.task_state == 't_confirm':
           state =  u'Батлах'
        if self.task_state == 't_evaluate':
           state =  u'Үнэлэх'
        if self.task_state == 't_done':
           state =  u'Дууссан'
        if self.task_state == 't_cancel':
           state =  u'Цуцалсан'
        if self.task_state == 't_back':
           state =  u'Хойшлуулсан'
        if self.description:
            description = self.description
            
        if not self.user_id:
            if not self.department_id.manager_id:
                raise ValidationError(_(u'%s Хэлтэсд менежер байхгүй'%self.department_id.name))
            email = self.department_id.manager_id.work_email
            subject = u'"%s" салбарт "%s" төслийн "%s" таскыг гүйцэтгэх захиалга ирлээ.'%( self.department_id.name, self.project_id.name , self.name)
            body_html = u'''
                            <h4>Сайн байна уу ?, 
                            Таньд энэ өдрийн мэнд хүргье! 
                            "%s" салбарт "%s" төслийн "%s" таскыг гүйцэтгэх захиалга ирлээ.</h4>
                            <p><li><b>Төсөл: </b>%s</li></p>
                            <p><li><b>Даалгавар: </b>%s</li></p>
                            <p><li><b>Эхлэх огноо: </b>%s</li></p>
                            <p><li><b>Дуусах огноо: </b>%s</li></p>
                            <p><li><b>Хариуцагч хэлтэс: </b>%s</li></p>
                            <p><li><b>Төлөв: </b>%s</li></p>
                            <p><li><b>Даалгаврын дэлгэрэнгүй: </b>%s</li></p>
                            </br>
                            <p><li>"%s" / "%s" -н мэдээллийг <b><a href=%s/web?db=%s#id=%s&view_type=form&model=project.task&action=%s>Төсөл/Даалгаварууд</a></b> цонхоор дамжин харна уу.</li></p>
                            <p>--</p>
                            <p>Энэхүү мэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
                            <p>Баярлалаа..</p>
                        '''%(self.department_id.name, self.project_id.name , self.name,self.project_id.name,self.name,self.task_date_start,self.date_deadline,
                                      self.department_id.name,state,description,self.project_id.name,self.name,
                                        base_url,
                                        db_name,
                                        self.id,
                                        action_id)
     
            if email and email.strip():
                email_template = self.env['mail.template'].sudo().create({
                    'name': _('Followup '),
                    'email_from': self.env.user.company_id.email or '',
                    'model_id': self.env['ir.model'].search([('model', '=', 'project.task')]).id,
                    'subject': subject,
                    'email_to': email,
                    'lang': self.env.user.lang,
                    'auto_delete': True,
                    'body_html':body_html,
                })
                email_template.sudo().send_mail(self.id)
        else :
            email = self.user_id.login
            subject = u'Таньд "%s" төслийн "%s" таскыг гүйцэтгэх захиалга ирлээ.'%(self.project_id.name , self.name)
            body_html = u'''
                            <h4>Сайн байна уу ?, 
                            Таньд энэ өдрийн мэнд хүргье! 
                            Таньд %s" төслийн "%s" таскыг гүйцэтгэх захиалга ирлээ.</h4>
                            <p><li><b>Төсөл: </b>%s</li></p>
                            <p><li><b>Даалгавар: </b>%s</li></p>
                            <p><li><b>Эхлэх огноо: </b>%s</li></p>
                            <p><li><b>Дуусах огноо: </b>%s</li></p>
                            <p><li><b>Хариуцагч хэлтэс: </b>%s</li></p>
                            <p><li><b>Төлөв: </b>%s</li></p>
                            <p><li><b>Даалгаврын дэлгэрэнгүй: </b>%s</li></p>
                            </br>
                            <p><li>"%s" / "%s" -н мэдээллийг <b><a href=%s/web?db=%s#id=%s&view_type=form&model=project.task&action=%s>Төсөл/Даалгаварууд</a></b> цонхоор дамжин харна уу.</li></p>
                            <p>--</p>
                            <p>Энэхүү мэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
                            <p>Баярлалаа..</p>
                        '''%( self.project_id.name , self.name,self.project_id.name,self.name,self.task_date_start,self.date_deadline,
                                      self.department_id.name,state,description,self.project_id.name,self.name,
                                        base_url,
                                        db_name,
                                        self.id,
                                        action_id)
     
            if email and email.strip():
                email_template = self.env['mail.template'].sudo().create({
                    'name': _('Followup '),
                    'email_from': self.env.user.company_id.email or '',
                    'model_id': self.env['ir.model'].search([('model', '=', 'project.task')]).id,
                    'subject': subject,
                    'email_to': email,
                    'lang': self.env.user.lang,
                    'auto_delete': True,
                    'body_html':body_html,
                })
                email_template.sudo().send_mail(self.id)
            
        self.write({
                    'task_state':'t_user',
                    'planned_start_date':self.task_date_start,
                    'planned_end_date':self.date_deadline
                    })
        
    @api.multi
    def action_back_user(self):
        '''
            хариуцагчид буцаан оноох
        '''
        history_confirm = self.env['task.confirm.users'].search([('task_id', '=',self.id)])
        history_rating = self.env['task.rating.users'].search([('task_id', '=',self.id)])
        users =[]
        if history_rating:
            history_rating.unlink()
        if history_confirm:
            history_confirm.unlink()
        if self.verify_user_ids :
            self.verify_user_ids.unlink()
        if self.task_state == 't_done':
            #тухайн хэрэглэгч нь тухайн даалгаврын хамаарах төслийн менежер мөн үед дууссан төлвөөс буцаах эрхтэй
            if self.task_verifier:
                users.append(self.task_verifier.id)
            if self.task_verifier_users:    
                for us in self.task_verifier_users:
                    users.append(us.user_id.id)

            if self._uid == self.project_id.user_id.id or self._uid in users:
                self.write({'task_state':'t_user',
                            'done_date': None,})
            else:
                raise UserError(_(u'Зөвхөн Төслийн менежер, Хянагч нар Дууссан төлвөөс "Хариуцагчид буцаан оноох" боломжтой !!!'))
        else:
            self.write({'task_state':'t_user',
                        'done_date': None,})
        
    @api.multi
    def action_start(self):
        '''
            Хийгдэж буй төлөвт оруулах хариуцагч байгаа эсэхийг шалгана
        '''
        if self.user_id:
            self.write({'task_state':'t_start'})

        else:
            raise ValidationError(_(u'Хариуцагч онооно уу!!!'))
        
    @api.multi
    def action_to_confirm(self):
        '''
            Батлах шатанд оруулах
        '''
        if self.flow == 100:
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            action_id = self.env['ir.model.data'].get_object_reference('project', 'action_view_task')[1]
            db_name = request.session.db
            state = ''
            description = ''
            if self.task_state == 't_new':
               state =  u'Шинэ'
            if self.task_state == 't_cheapen':
               state =  u'Үнэ тохирох'
            if self.task_state == 't_cheapened':
               state =  u'Үнэ тохирсон'
            if self.task_state == 't_user':
               state =  u'Хариуцагчтай'
            if self.task_state == 't_start':
               state =  u'Хийгдэж буй'
            if self.task_state == 't_control':
               state =  u'Хянах'
            if self.task_state == 't_confirm':
               state =  u'Батлах'
            if self.task_state == 't_evaluate':
               state =  u'Үнэлэх'
            if self.task_state == 't_done':
               state =  u'Дууссан'
            if self.task_state == 't_cancel':
               state =  u'Цуцалсан'
            if self.task_state == 't_back':
               state =  u'Хойшлуулсан'
            if self.description:
                description = self.description
            
            if self.controller:
                for line in self.controller:
                    email = line.work_email
                    subject = u'"%s" салбарт "%s" төслийн "%s" таскыг батлах хүсэлт ирлээ.'%( self.department_id.name, self.project_id.name , self.name)
                    body_html = u'''
                                    <h4>Сайн байна уу ?, 
                                    Таньд энэ өдрийн мэнд хүргье! 
                                    "%s" салбарт "%s" төслийн "%s" таскыг батлах хүсэлт ирлээ.</h4>
                                    <p><li><b>Төсөл: </b>%s</li></p>
                                    <p><li><b>Даалгавар: </b>%s</li></p>
                                    <p><li><b>Эхлэх огноо: </b>%s</li></p>
                                    <p><li><b>Дуусах огноо: </b>%s</li></p>
                                    <p><li><b>Хариуцагч хэлтэс: </b>%s</li></p>
                                    <p><li><b>Төлөв: </b>%s</li></p>
                                    <p><li><b>Даалгаврын дэлгэрэнгүй: </b>%s</li></p>
                                    </br>
                                    <p><li>"%s" / "%s" -н мэдээллийг <b><a href=%s/web?db=%s#id=%s&view_type=form&model=project.task&action=%s>Төсөл/Даалгаварууд</a></b> цонхоор дамжин харна уу.</li></p>
                                    <p>--</p>
                                    <p>Энэхүү мэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
                                    <p>Баярлалаа..</p>
                                '''%(self.department_id.name, self.project_id.name , self.name,self.project_id.name,self.name,self.task_date_start,self.date_deadline,
                                              self.department_id.name,state,description,self.project_id.name,self.name,
                                                base_url,
                                                db_name,
                                                self.id,
                                                action_id)
             
                    if email and email.strip():
                        email_template = self.env['mail.template'].sudo().create({
                            'name': _('Followup '),
                            'email_from': self.env.user.company_id.email or '',
                            'model_id': self.env['ir.model'].search([('model', '=', 'project.task')]).id,
                            'subject': subject,
                            'email_to': email,
                            'lang': self.env.user.lang,
                            'auto_delete': True,
                            'body_html':body_html,
                        })
                        email_template.sudo().send_mail(self.id)
            self.write({'task_state':'t_confirm'})
        else:
            raise ValidationError(_(u'Явцын хувь талбар 100 хувь болоогүй байна!!!'))
    @api.multi
    def action_to_evaluate(self):
        '''
            Үнэлэх шатанд оруулах
        '''
        if self.flow == 100:
            self.write({'task_state':'t_evaluate'})
        else:
            raise ValidationError(_(u'Явцын хувь талбар 100 хувь болоогүй байна!!!'))
        
    @api.multi
    def action_cancel(self):
        '''
            цуцлах , төслийн менежер мөн эсэхийг шалгана
        '''
        if self.verify_user_ids :
            self.verify_user_ids.unlink()
        for task in self:
            if task.project_id.user_id.id == self._uid:
                self.write({'task_state':'t_cancel'})
            else:
                raise ValidationError(_(u'Төслийн менежер цуцлах эрхтэй'))
        
    @api.multi
    def action_draft(self):
        '''
            Шинэ төлөвт оруулах үнэлэсэн болон баталсан түүх цэвэрлэнэ
        '''
        history_confirm = self.env['task.confirm.users'].search([('task_id', '=',self.id)])
        history_rating = self.env['task.rating.users'].search([('task_id', '=',self.id)])
        if history_rating:
            history_rating.unlink()
        if history_confirm:
            history_confirm.unlink()
        self.write({'task_state':'t_new'})
        
    @api.multi
    def action_to_control(self):
        '''
            Хянах төлөвт оруулна явцын хувь талбар 100 болсон эсэхийг шалгана
        '''
        if self.flow == 100:
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            action_id = self.env['ir.model.data'].get_object_reference('project', 'action_view_task')[1]
            db_name = request.session.db
            state = ''
            description = ''
            if self.task_state == 't_new':
               state =  u'Шинэ'
            if self.task_state == 't_cheapen':
               state =  u'Үнэ тохирох'
            if self.task_state == 't_cheapened':
               state =  u'Үнэ тохирсон'
            if self.task_state == 't_user':
               state =  u'Хариуцагчтай'
            if self.task_state == 't_start':
               state =  u'Хийгдэж буй'
            if self.task_state == 't_control':
               state =  u'Хянах'
            if self.task_state == 't_confirm':
               state =  u'Батлах'
            if self.task_state == 't_evaluate':
               state =  u'Үнэлэх'
            if self.task_state == 't_done':
               state =  u'Дууссан'
            if self.task_state == 't_cancel':
               state =  u'Цуцалсан'
            if self.task_state == 't_back':
               state =  u'Хойшлуулсан'
            if self.description:
                description = self.description
            
            if self.task_verifier_users:
                for line in self.task_verifier_users:
                    email = line.work_email
                    subject = u'"%s" салбарт "%s" төслийн "%s" таскыг хянах хүсэлт ирлээ.'%( self.department_id.name, self.project_id.name , self.name)
                    body_html = u'''
                                    <h4>Сайн байна уу ?, 
                                    Таньд энэ өдрийн мэнд хүргье! 
                                    "%s" салбарт "%s" төслийн "%s" таскыг хянах хүсэлт ирлээ.</h4>
                                    <p><li><b>Төсөл: </b>%s</li></p>
                                    <p><li><b>Даалгавар: </b>%s</li></p>
                                    <p><li><b>Эхлэх огноо: </b>%s</li></p>
                                    <p><li><b>Дуусах огноо: </b>%s</li></p>
                                    <p><li><b>Хариуцагч хэлтэс: </b>%s</li></p>
                                    <p><li><b>Төлөв: </b>%s</li></p>
                                    <p><li><b>Даалгаврын дэлгэрэнгүй: </b>%s</li></p>
                                    </br>
                                    <p><li>"%s" / "%s" -н мэдээллийг <b><a href=%s/web?db=%s#id=%s&view_type=form&model=project.task&action=%s>Төсөл/Даалгаварууд</a></b> цонхоор дамжин харна уу.</li></p>
                                    <p>--</p>
                                    <p>Энэхүү мэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
                                    <p>Баярлалаа..</p>
                                '''%(self.department_id.name, self.project_id.name , self.name,self.project_id.name,self.name,self.task_date_start,self.date_deadline,
                                              self.department_id.name,state,description,self.project_id.name,self.name,
                                                base_url,
                                                db_name,
                                                self.id,
                                                action_id)
             
                    if email and email.strip():
                        email_template = self.env['mail.template'].sudo().create({
                            'name': _('Followup '),
                            'email_from': self.env.user.company_id.email or '',
                            'model_id': self.env['ir.model'].search([('model', '=', 'project.task')]).id,
                            'subject': subject,
                            'email_to': email,
                            'lang': self.env.user.lang,
                            'auto_delete': True,
                            'body_html':body_html,
                        })
                        email_template.sudo().send_mail(self.id)
            self.write({'task_state':'t_control'})
        else:
            raise ValidationError(_(u'Явцын хувь талбар 100 хувь болоогүй байна!!!'))
        
    @api.multi
    def action_done(self):
        '''
            Дууссан төлөвт оруулах
        '''
        emp = self.env['hr.employee'].sudo().search([('user_id','=',self._uid)])[0]
        
        self.env['task.verify.users'].create({'employee_id':emp.id,'date':time.strftime('%Y-%m-%d'),'state':'verify','task_id':self.id})
        if self.task_verifier:
            if self.task_type=='normal':
                self.write({'task_state':'t_done',
                        'done_date': time.strftime('%Y-%m-%d'),                    
                        })
            elif self.task_type=='tariff_task':
                base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                action_id = self.env['ir.model.data'].get_object_reference('project', 'action_view_task')[1]
                db_name = request.session.db
                state = ''
                description = ''
                if self.task_state == 't_new':
                   state =  u'Шинэ'
                if self.task_state == 't_cheapen':
                   state =  u'Үнэ тохирох'
                if self.task_state == 't_cheapened':
                   state =  u'Үнэ тохирсон'
                if self.task_state == 't_user':
                   state =  u'Хариуцагчтай'
                if self.task_state == 't_start':
                   state =  u'Хийгдэж буй'
                if self.task_state == 't_control':
                   state =  u'Хянах'
                if self.task_state == 't_confirm':
                   state =  u'Батлах'
                if self.task_state == 't_evaluate':
                   state =  u'Үнэлэх'
                if self.task_state == 't_done':
                   state =  u'Дууссан'
                if self.task_state == 't_cancel':
                   state =  u'Цуцалсан'
                if self.task_state == 't_back':
                   state =  u'Хойшлуулсан'
                if self.description:
                    description = self.description
                
                if self.rating_users:
                    for line in self.rating_users:
                        email = line.work_email
                        subject = u'"%s" салбарт "%s" төслийн "%s" таскыг үнэлэх хүсэлт ирлээ.'%( self.department_id.name, self.project_id.name , self.name)
                        body_html = u'''
                                        <h4>Сайн байна уу ?, 
                                        Таньд энэ өдрийн мэнд хүргье! 
                                        "%s" салбарт "%s" төслийн "%s" таскыг үнэлэх хүсэлт ирлээ.</h4>
                                        <p><li><b>Төсөл: </b>%s</li></p>
                                        <p><li><b>Даалгавар: </b>%s</li></p>
                                        <p><li><b>Эхлэх огноо: </b>%s</li></p>
                                        <p><li><b>Дуусах огноо: </b>%s</li></p>
                                        <p><li><b>Хариуцагч хэлтэс: </b>%s</li></p>
                                        <p><li><b>Төлөв: </b>%s</li></p>
                                        <p><li><b>Даалгаврын дэлгэрэнгүй: </b>%s</li></p>
                                        </br>
                                        <p><li>"%s" / "%s" -н мэдээллийг <b><a href=%s/web?db=%s#id=%s&view_type=form&model=project.task&action=%s>Төсөл/Даалгаварууд</a></b> цонхоор дамжин харна уу.</li></p>
                                        <p>--</p>
                                        <p>Энэхүү мэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
                                        <p>Баярлалаа..</p>
                                    '''%(self.department_id.name, self.project_id.name , self.name,self.project_id.name,self.name,self.task_date_start,self.date_deadline,
                                                  self.department_id.name,state,description,self.project_id.name,self.name,
                                                    base_url,
                                                    db_name,
                                                    self.id,
                                                    action_id)
                 
                        if email and email.strip():
                            email_template = self.env['mail.template'].sudo().create({
                                'name': _('Followup '),
                                'email_from': self.env.user.company_id.email or '',
                                'model_id': self.env['ir.model'].search([('model', '=', 'project.task')]).id,
                                'subject': subject,
                                'email_to': email,
                                'lang': self.env.user.lang,
                                'auto_delete': True,
                                'body_html':body_html,
                            })
                            email_template.sudo().send_mail(self.id)
                self.write({'task_state':'t_evaluate'})
            elif self.task_type in ('work_graph','work_task'):
                print'_________POLO_____________',self.controller
                base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                action_id = self.env['ir.model.data'].get_object_reference('project', 'action_view_task')[1]
                db_name = request.session.db
                state = ''
                description = ''
                if self.task_state == 't_new':
                   state =  u'Шинэ'
                if self.task_state == 't_cheapen':
                   state =  u'Үнэ тохирох'
                if self.task_state == 't_cheapened':
                   state =  u'Үнэ тохирсон'
                if self.task_state == 't_user':
                   state =  u'Хариуцагчтай'
                if self.task_state == 't_start':
                   state =  u'Хийгдэж буй'
                if self.task_state == 't_control':
                   state =  u'Хянах'
                if self.task_state == 't_confirm':
                   state =  u'Батлах'
                if self.task_state == 't_evaluate':
                   state =  u'Үнэлэх'
                if self.task_state == 't_done':
                   state =  u'Дууссан'
                if self.task_state == 't_cancel':
                   state =  u'Цуцалсан'
                if self.task_state == 't_back':
                   state =  u'Хойшлуулсан'
                if self.description:
                    description = self.description
                
                if self.controller:
                    print'_________POLO_____________',self.controller
                    for line in self.controller:
                        email = line.work_email
                        subject = u'"%s" салбарт "%s" төслийн "%s" таскыг батлах хүсэлт ирлээ.'%( self.department_id.name, self.project_id.name , self.name)
                        body_html = u'''
                                        <h4>Сайн байна уу ?, 
                                        Таньд энэ өдрийн мэнд хүргье! 
                                        "%s" салбарт "%s" төслийн "%s" таскыг батлах хүсэлт ирлээ.</h4>
                                        <p><li><b>Төсөл: </b>%s</li></p>
                                        <p><li><b>Даалгавар: </b>%s</li></p>
                                        <p><li><b>Эхлэх огноо: </b>%s</li></p>
                                        <p><li><b>Дуусах огноо: </b>%s</li></p>
                                        <p><li><b>Хариуцагч хэлтэс: </b>%s</li></p>
                                        <p><li><b>Төлөв: </b>%s</li></p>
                                        <p><li><b>Даалгаврын дэлгэрэнгүй: </b>%s</li></p>
                                        </br>
                                        <p><li>"%s" / "%s" -н мэдээллийг <b><a href=%s/web?db=%s#id=%s&view_type=form&model=project.task&action=%s>Төсөл/Даалгаварууд</a></b> цонхоор дамжин харна уу.</li></p>
                                        <p>--</p>
                                        <p>Энэхүү мэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
                                        <p>Баярлалаа..</p>
                                    '''%(self.department_id.name, self.project_id.name , self.name,self.project_id.name,self.name,self.task_date_start,self.date_deadline,
                                                  self.department_id.name,state,description,self.project_id.name,self.name,
                                                    base_url,
                                                    db_name,
                                                    self.id,
                                                    action_id)
                 
                        if email and email.strip():
                            email_template = self.env['mail.template'].sudo().create({
                                'name': _('Followup '),
                                'email_from': self.env.user.company_id.email or '',
                                'model_id': self.env['ir.model'].search([('model', '=', 'project.task')]).id,
                                'subject': subject,
                                'email_to': email,
                                'lang': self.env.user.lang,
                                'auto_delete': True,
                                'body_html':body_html,
                            })
                            email_template.sudo().send_mail(self.id)
                self.write({'task_state':'t_confirm'})
        else:
            if self.task_verifier_users:
                users = []
                is_done = True
                if len(self.verify_user_ids) ==len(self.task_verifier_users):
                    
                    if self.task_type=='normal':
                        self.write({'task_state':'t_done',
                        'done_date': time.strftime('%Y-%m-%d'),                    
                        })
                    elif self.task_type=='tariff_task':
                        self.write({'task_state':'t_evaluate'})
                    elif self.task_type =='work_graph':
                        self.write({'task_state':'t_confirm'})
                    else :
                        self.write({'task_state':'t_confirm'})
        
    @api.multi
    def action_after(self):
        '''
            Хойшлуулсан төлөвт оруулах аль төлөвөөс хойшилсонг бүртгэх
        '''
        state = self.task_state
        self.write({
                    'back_state':state,
                    'task_state':'t_back'
                    })
        
    @api.multi
    def action_back(self):
        if self.back_state == 't_cheapen':
            self.write({'task_state':'t_cheapen'})
        if self.back_state == 't_cheapened':
            self.write({'task_state':'t_cheapened'})
        if self.back_state == 't_user':
            self.write({'task_state':'t_user'})
        if self.back_state == 't_start':
            self.write({'task_state':'t_start'})
        if self.back_state == 't_confirm':
            self.write({'task_state':'t_confirm'})
        if self.back_state == 't_evaluate':
            self.write({'task_state':'t_evaluate'})
        if self.verify_user_ids :
            self.verify_user_ids.unlink()
        
    @api.multi
    def action_confirm(self):
        '''
            Батлах товч, баталсан түүх хөтөлнө , сүүлийн хүн  баталхад баталсан төлөвт орно
        '''
        for task in self:
            emp_obj = task.env['hr.employee']
            emp = emp_obj.search([('user_id','=',task._uid)])
            if emp in task.controller:
                task_confirm_users = task.env['task.confirm.users']
                employee = task.env['hr.employee']
                employee_id = employee.sudo().search([('user_id','=',task._uid)])
                vals = {
                        'task_id'       : task.id,
                        'confirmer'     : employee_id.id ,
                        'date'          : time.strftime('%Y-%m-%d %H:%M:%S'),
                        'role'          : 'confirmer',
                        'state'         : 'confirmed',
                        }
                task_confirm_users = task_confirm_users.create(vals)
            else:
                raise ValidationError(_(u'Энэ үйлдлийг хийх эрхгүй байна'))
            if task.is_confirm == True:
                base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                action_id = self.env['ir.model.data'].get_object_reference('project', 'action_view_task')[1]
                db_name = request.session.db
                state = ''
                description = ''
                if self.task_state == 't_new':
                   state =  u'Шинэ'
                if self.task_state == 't_cheapen':
                   state =  u'Үнэ тохирох'
                if self.task_state == 't_cheapened':
                   state =  u'Үнэ тохирсон'
                if self.task_state == 't_user':
                   state =  u'Хариуцагчтай'
                if self.task_state == 't_start':
                   state =  u'Хийгдэж буй'
                if self.task_state == 't_control':
                   state =  u'Хянах'
                if self.task_state == 't_confirm':
                   state =  u'Батлах'
                if self.task_state == 't_evaluate':
                   state =  u'Үнэлэх'
                if self.task_state == 't_done':
                   state =  u'Дууссан'
                if self.task_state == 't_cancel':
                   state =  u'Цуцалсан'
                if self.task_state == 't_back':
                   state =  u'Хойшлуулсан'
                if self.description:
                    description = self.description
                
                if self.rating_users:
                    print'_________POLO_____________',self.rating_users
                    for line in self.rating_users:
                        email = line.work_email
                        subject = u'"%s" салбарт "%s" төслийн "%s" таскыг үнэлэх хүсэлт ирлээ.'%( self.department_id.name, self.project_id.name , self.name)
                        body_html = u'''
                                        <h4>Сайн байна уу ?, 
                                        Таньд энэ өдрийн мэнд хүргье! 
                                        "%s" салбарт "%s" төслийн "%s" таскыг үнэлэх хүсэлт ирлээ.</h4>
                                        <p><li><b>Төсөл: </b>%s</li></p>
                                        <p><li><b>Даалгавар: </b>%s</li></p>
                                        <p><li><b>Эхлэх огноо: </b>%s</li></p>
                                        <p><li><b>Дуусах огноо: </b>%s</li></p>
                                        <p><li><b>Хариуцагч хэлтэс: </b>%s</li></p>
                                        <p><li><b>Төлөв: </b>%s</li></p>
                                        <p><li><b>Даалгаврын дэлгэрэнгүй: </b>%s</li></p>
                                        </br>
                                        <p><li>"%s" / "%s" -н мэдээллийг <b><a href=%s/web?db=%s#id=%s&view_type=form&model=project.task&action=%s>Төсөл/Даалгаварууд</a></b> цонхоор дамжин харна уу.</li></p>
                                        <p>--</p>
                                        <p>Энэхүү мэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
                                        <p>Баярлалаа..</p>
                                    '''%(self.department_id.name, self.project_id.name , self.name,self.project_id.name,self.name,self.task_date_start,self.date_deadline,
                                                  self.department_id.name,state,description,self.project_id.name,self.name,
                                                    base_url,
                                                    db_name,
                                                    self.id,
                                                    action_id)
                 
                        if email and email.strip():
                            email_template = self.env['mail.template'].sudo().create({
                                'name': _('Followup '),
                                'email_from': self.env.user.company_id.email or '',
                                'model_id': self.env['ir.model'].search([('model', '=', 'project.task')]).id,
                                'subject': subject,
                                'email_to': email,
                                'lang': self.env.user.lang,
                                'auto_delete': True,
                                'body_html':body_html,
                            })
                            email_template.sudo().send_mail(self.id)
                task.write({'task_state':'t_evaluate'})
    
    @api.multi
    def action_circle(self):
        '''
            Даалгавар давтаж үүсгэх цонх дуудах
        '''
        for task in self:
            
            mod_obj = task.env['ir.model.data']

            res = mod_obj.get_object_reference('nomin_project', 'action_create_circle_task2')
            return {
                'name': 'Даалгавар давтаж үүсгэх',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'project.circle.task',
                'context': task._context,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
            }
    @api.multi
    def action_evaluate(self):
        '''
            Даалгавар үнэлэх цонх дуудах
        '''
        for task in self:
            mod_obj = task.env['ir.model.data']
            res = mod_obj.get_object_reference('nomin_project', 'action_rate_project_task1')
            return {
                'name': 'Даалгавар үнэлэх цонх',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'rate.project.task',
                'context':{'task_id':self.id},
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
            }
    
    def _project_task_alarm_deadline(self):
        '''
            Даалгаварын гүйцэтгэх хугацаа хэтэрсэн майл илгээх cron
        '''
        query = "SELECT id FROM project_task WHERE task_state not in ('t_done','t_cancel','t_back')";
        cr.execute(query)
        records = cr.dictfetchall()
        template_id2 = self.env['ir.model.data'].get_object_reference('nomin_project', 'project_task_alarm_email_template2')[1]
        
        for record in records:
            task = self.env['project.task'].browse(record['id'])
            if task.user_id and task.date_deadline:
                description = ''
                state = ''
                if task.description:
                    description = task.description
                if task.task_state == 't_new':
                   state =  u'Шинэ'
                if task.task_state == 't_cheapen':
                   state =  u'Үнэ тохирох'
                if task.task_state == 't_cheapened':
                   state =  u'Үнэ тохирсон'
                if task.task_state == 't_user':
                   state =  u'Хариуцагчтай'
                if task.task_state == 't_start':
                   state =  u'Хийгдэж буй'
                if task.task_state == 't_control':
                   state =  u'Хянах'
                if task.task_state == 't_confirm':
                   state =  u'Батлах'
                if task.task_state == 't_evaluate':
                   state =  u'Үнэлэх'
                if task.task_state == 't_done':
                   state =  u'Дууссан'
                if task.task_state == 't_cancel':
                   state =  u'Цуцалсан'
                if task.task_state == 't_back':
                   state =  u'Хойшлуулсан'
                date_now = datetime.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d')
                date_now.date()
                date = datetime.strptime(task.task_date_start, '%Y-%m-%d')
                end_date = datetime.strptime(task.date_deadline, '%Y-%m-%d')
               
                if (end_date.date() - date_now.date()).days < 0:
                    data = {
                        'name': task.name,
                        'project':task.project_id.name,
                        'start_date':task.task_date_start,
                        'end_date':task.date_deadline,
                        'department':task.department_id.name,
                        'user':task.user_id.name,
                        'state':state,
                        'description':description,
                        'day':(date_now.date() - end_date.date()).days,
                        'subject':u'"%s" төслийн "%s" даалгаварын гүйцэтгэх хугацаа хэтэрсэн байна.'%(task.project_id.name,task.name),
                        'base_url': self.env['ir.config_parameter'].get_param('web.base.url'),
                        'action_id': self.env['ir.model.data'].get_object_reference('project', 'action_view_task'),
                        'id': record['id'],
                        'db_name': cr.dbname,
                        }
                    self.env.context = data
                    self.pool['mail.template'].send_mail(self.env.cr, 1, template_id2, task.user_id.id, force_send=True, context=self.env.context)
                    # self.env['mail.template'].send_mail(template_id2, task.user_id.id, force_send=True, context=data)

    def _project_task_alarm(self):
        '''
            Даалгаварын эхлэх хугацаа болсон , эсвэл эхлэх хугацаа болоход 1 хоног дутуу байгаа талаар емайл илгээх
        '''
        query = "SELECT id FROM project_task WHERE task_state in ('t_new','t_cheapen','t_cheapened','t_user')";
        cr.execute(query)
        records = cr.dictfetchall()
        template_id = self.env['ir.model.data'].get_object_reference('nomin_project', 'project_task_alarm_email_template')[1]
        template_id1 = self.env['ir.model.data'].get_object_reference('nomin_project', 'project_task_alarm_email_template1')[1]
        
        for record in records:
            task = self.env['project.task'].browse(record['id'])
            if task.user_id and task.task_date_start:
                description = ''
                state = ''
                if task.description:
                    description = task.description
                if task.task_state == 't_new':
                   state =  u'Шинэ'
                if task.task_state == 't_cheapen':
                   state =  u'Үнэ тохирох'
                if task.task_state == 't_cheapened':
                   state =  u'Үнэ тохирсон'
                if task.task_state == 't_user':
                   state =  u'Хариуцагчтай'
                if task.task_state == 't_start':
                   state =  u'Хийгдэж буй'
                if task.task_state == 't_control':
                   state =  u'Хянах'
                if task.task_state == 't_confirm':
                   state =  u'Батлах'
                if task.task_state == 't_evaluate':
                   state =  u'Үнэлэх'
                if task.task_state == 't_done':
                   state =  u'Дууссан'
                if task.task_state == 't_cancel':
                   state =  u'Цуцалсан'
                if task.task_state == 't_back':
                   state =  u'Хойшлуулсан'
                date_now = datetime.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d')
                date_now.date()
                date = datetime.strptime(task.task_date_start, '%Y-%m-%d')
                if (date.date() - date_now.date()).days == 1:
                    print 'task',task.name
                    data = {
                        'name': task.name,
                        'project':task.project_id.name,
                        'start_date':task.task_date_start,
                        'end_date':task.date_deadline,
                        'department':task.department_id.name,
                        'user':task.user_id.name,
                        'state':state,
                        'description':description,
                        'subject':u'"%s" төслийн "%s" даалгавар эхлэх хугацаа болоход 1 хоног үлдлээ.'%(task.project_id.name,task.name),
                        'base_url': self.env['ir.config_parameter'].get_param('web.base.url'),
                        'action_id': self.env['ir.model.data'].get_object_reference('project', 'action_view_task')[1],
                        'id': record['id'],
                        'db_name': cr.dbname,
                        }
                    # self.pool.get('mail.template').send_mail(cr, uid, template_id, task.user_id.id, force_send=True, context=data)
                    self.env.context = data
                    self.pool['mail.template'].send_mail(self.env.cr, 1, template_id, task.user_id.id, force_send=True, context=self.env.context)
                if (date.date() - date_now.date()).days == 0:
                    data = {
                        'name': task.name,
                        'project':task.project_id.name,
                        'start_date':task.task_date_start,
                        'end_date':task.date_deadline,
                        'department':task.department_id.name,
                        'user':task.user_id.name,
                        'state':state,
                        'description':description,
                        'subject':u'Өнөөдөр буюу "%s"-нд "%s" Төслийн "%s" Даалгаварыг хийж эхлэхээр төлөвлөсөн байна.'%(date_now,task.project_id.id,task.name),
                        'base_url': self.env['ir.config_parameter'].get_param('web.base.url'),
                        'action_id': self.env['ir.model.data'].get_object_reference('project', 'action_view_task')[1],
                        'id': record['id'],
                        'db_name': cr.dbname,
                        }
                    
                    # self.pool.get('mail.template').send_mail(cr, uid, template_id1, task.user_id.id, force_send=True, context=data)
                    self.env.context = data
                    self.pool['mail.template'].send_mail(self.env.cr, 1, template_id1, task.user_id.id, force_send=True, context=self.env.context)

class TaskOperation(models.Model):
    _name='task.operation'
    _description ='Task operation'

    name = fields.Char(string="Operation")
    quantity = fields.Float(string="Quantity")
    uom_id = fields.Many2one('product.uom',string="UOM")
    material_claim = fields.Text(string="Material claim")
    description = fields.Text(string="Description")
    task_id = fields.Many2one('project.task',string="Task")
class TaskVerifyUsers(models.Model):
    _name ='task.verify.users'

    employee_id = fields.Many2one('hr.employee',string="Employee")
    state = fields.Selection([('draft','Draft'),('verify','Verify')],default="draft",string="State")
    date = fields.Date(string="Date")
    task_id = fields.Many2one('project.task',string="Task")
