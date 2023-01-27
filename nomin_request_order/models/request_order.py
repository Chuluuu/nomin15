# -*- coding: utf-8 -*-
# from typing import DefaultDict
from odoo import tools, api, models, fields ,_
from odoo.exceptions import UserError 
from time import strftime
import time
from odoo.http import request
from datetime import date
from datetime import datetime, timedelta

class RequestOrder (models.Model):
    _name = "request.order"
    _description = "Request order"
    _inherit = ['mail.thread']
    _order = "create_date DESC"


    
    def _add_followers(self,user_ids):
        '''Add followers
        '''
        partner_ids = [user.partner_id.id for user in self.env['res.users'].browse(user_ids) if user.partner_id]
        self.message_subscribe(partner_ids=partner_ids)


    
    def create_history(self,state,sequence,note):
        history_obj = self.env['request.history']
        history_obj.create({'user_id':self._uid,
                                'sequence':sequence,
                                'request_order_id':self.id,
                                # 'date':fields.Date.context_today(self),
                                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'comment':self.request_config_id.name
                            })
        
    def _set_company(self):
        ''''''

        if self.env.user.company_id.id:
            return self.env.user.company_id.id
        else:
            raise Warning(('You don\'t have related company. Please contact administrator.'))
        return None

   

    def _set_employee(self):
        '''хэрэглэгчийн ажилтныг авна
        '''
        employee_ids = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        if employee_ids:
            return employee_ids.id
        else:
            raise UserError((u'Ажилтан олдсонгүй'))

    @api.model
    def _set_department(self):
        if self.env.user.department_id:
            return self.env.user.department_id.id
        return None

    @api.model
    def _set_sector(self):
        if not self.env.user.department_id:
            raise UserError((u'Та ямар нэгэн хэлтэст хамааралгүй байна!.'))
        if self.env.user.department_id:
            sector_id = self.env['hr.department'].get_sector(self.env.user.department_id.id)
            if sector_id:
                return sector_id
            else:
                return None

        


    @api.model
    def _set_job(self):
        emp_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        if emp_id:
            return emp_id.job_id.id
        return None

    
    @api.model
    def _get_default_request_id(self):
        """ Gives default perform_department_id """
        perform_department_id = self.env.context.get('perform_department_id')
        if not perform_department_id:
            return False
        return self.stage_find(perform_department_id)

    def _get_holidays(self, date_due, finished_order_date):
        """Returns a float equals to the timedelta between two dates given as string."""

        DATE_FORMAT = "%Y-%m-%d"
        from_dt = datetime.strptime(date_due, DATE_FORMAT)
        to_dt = datetime.strptime(finished_order_date, DATE_FORMAT)
        query = """SELECT count(*) AS count_days_no_weekend FROM   generate_series(timestamp '%s', timestamp '%s', interval '1 day') the_day WHERE  extract('ISODOW' FROM the_day) < 6"""%(from_dt, to_dt)
        self.env.cr.execute(query)
        working_day = self.env.cr.fetchone()[0]
        self.env.cr.execute("select count(id) from hr_public_holiday where extract(ISODOW from days_date) not in (6,7) and days_date between %s and %s",(from_dt,to_dt))
        public_holidays = self.env.cr.fetchone()[0]
        return working_day - public_holidays
                

    @api.model
    def _exceeded_day(self):
        days = 0
        for order in self:
            if order.date_due and order.order_finished_date:
                if order.date_due < order.order_finished_date:
                    days = self._get_holidays(order.date_due,order.order_finished_date)
                    order.write({'exceeded_day':days-1})
                else:
                    days = self._get_holidays(order.date_due,order.order_finished_date)
                    order.write({'exceeded_day':days-1})


    
    def _is_approve_user(self):
        user_ids = []
        for order in self:
            order.is_approve_user = False
            if not order.is_sent:
                if order.request_config_id.select_dep =='perform':
                    if order.request_config_id.type =='group':
                        for group in order.request_config_id.group_ids:                        
                                for user in group.users:
                                    # if  user in order.request_config_id.department_ids: 
                                    user_ids.append( user.id)

                    elif order.request_config_id.type == 'fixed':
                        user_ids.append(order.request_config_id.user_id.id)
                    elif order.request_config_id.type == 'distribute':
                        for user in order.request_config_id.user_ids:
                            user_ids.append(user.id)
                    elif order.request_config_id.type == 'department':
                        user_id = order.perform_department_id.manager_id.id
                        if user_id :
                            user_ids.append( user_id)
                    if self._uid in user_ids:
                        order.is_approve_user = True

                elif order.request_config_id.select_dep =='customer':
                    if self._uid  == order.employee_id.user_id.id :
                        order.is_approve_user = True
                    # if order.request_config_id.type =='group':
                    #     for group in order.request_config_id.group_ids:                        
                    #             for user in group.users:
                    #                 user_ids.append( user.id)

    
    @api.depends('line_ids.state')
    def _compute_percent(self):
        for order in self:
            if order.line_ids:
                
                count = 0
                length = 0
                for line in order.line_ids:
                    if line.state in ['control','done']:
                        length +=1
                        count+=1                        
                if count==0:
                    order.progress_percentage = 0
                else:
                    order.progress_percentage = count * 100 / length

    @api.depends('line_ids.amount')
    def _total_amount(self):
        total_amount = 0
        for order in self:
            for line in order.line_ids:            
                total_amount += line.amount

            order.total_amount = total_amount

    @api.depends('line_ids.amount')
    def _sum_amount(self):
        cost_amount = 0
        for order in self:
            for line in order.line_ids:
                if line.category_id.call_cost:
                    cost_amount = line.category_id.call_cost_tarif
        order.sum_amount = order.total_amount + cost_amount

    @api.onchange('employee_id')
    def _onchange_employee(self):
        for order in self:
            if order.employee_id:
                order.job_id = order.employee_id.job_id.id
                order.department_id = order.employee_id.department_id.id
                order.sector_id = order.employee_id.department_id.parent_id.id
    


    name            = fields.Char(string='Захиалгын дугаар', readonly=True , default="New")
    request_name    = fields.Char(string='Request name', tracking=True)
    sector_id       = fields.Many2one('hr.department', string = 'Захиалагч Салбар', ondelete="restrict", tracking=True, readonly="1" ,default=lambda self: self._set_sector())
    department_id   = fields.Many2one('hr.department', string = 'Захиалагч хэлтэс', ondelete="restrict", tracking=True, default=lambda self: self._set_department())
    job_id     = fields.Many2one('hr.job',string = 'Албан тушаал', ondelete="restrict", tracking=True, default=lambda self: self._set_job())
    phone_number   = fields.Char(string = 'Утасны дугаар', ondelete="restrict", tracking=True, related='employee_id.mobile_phone')
    employee_id     = fields.Many2one('hr.employee',string = 'Захиалагч', ondelete="restrict", tracking=True, default=_set_employee)
    cost_sector_id  = fields.Many2one('hr.department', string = 'Зардал гаргах Салбар', ondelete="restrict", tracking=True, default=lambda self: self._set_sector())
    date_order      = fields.Date(string='Захиалга өгсөн огноо', tracking=True, required=True, default=time.strftime("%Y-%m-%d"))
    perform_department_id = fields.Many2one('hr.department' , string='Perform department' , tracking=True)
    confirm_employee_id   = fields.Many2one('hr.employee', string='Батлах ажилтан',tracking=True)
    date_due              =fields.Date(string='Дуусах хугацаа')
    description           = fields.Text(string='Тайлбар' , tracking=True)
    request_config_id     = fields.Many2one('request.order.config',string="Төлөв", domain="[('department_ids','=',perform_department_id)]",default=_get_default_request_id, tracking=True)
    line_ids              = fields.One2many('request.order.line','order_id', string="Work Service")
    case_history_ids      = fields.One2many('request.order.line','order_id', string="Case history")
    line_history_ids      = fields.One2many('request.order.line','history_id',string = 'Line history')
    attach_line_ids              = fields.One2many('request.order.attachment','order_id', string="Хавсралт")
    history_ids              = fields.One2many('request.history','request_order_id', string="Request History")
    is_invisible             = fields.Boolean(string='Is invisible' , default=False)
    is_urgent             = fields.Boolean(string='Is Urgent' , default=False , tracking=True)
    is_skip_control       = fields.Boolean(string='Is skip control' , default=False , tracking=True)
    active_sequence       = fields.Integer(string="Sequence", default=1)
    is_done               = fields.Boolean(string='Is done' , default=False)
    is_sent               = fields.Boolean(string='Is sent' , default=True )
    is_cancel             = fields.Boolean(string='Is sent' , default=False )
    is_draft           = fields.Boolean(string='Is draft' , default=False )
    is_approve_user      = fields.Boolean(string='Is approve user' , default=False , compute="_is_approve_user")
    is_readonly = fields.Boolean(string="Is readonly" , default=False )
    progress_percentage = fields.Float(string="Progress percentage" , compute='_compute_percent' ,store=True)
    total_amount = fields.Float(string="Дүн" , tracking=True , compute="_total_amount" , store=True)
    sum_amount = fields.Float(string="Нийт дүн" , tracking=True , compute="_sum_amount")
    work_type = fields.Selection([('tarif','Тарифт ажлууд'),('order','Захиалгат ажлууд')],string='Зардлын төрөл')
    is_invisible_field = fields.Boolean(string="Invisible field" , default=False)
    doctor_field = fields.Boolean(string="Doctor flow" , default=False)
    # TODO FIX LATER
    # age = fields.Integer(string="Age" , related="employee_id.age")
    # cost_share_id = fields.Many2one('account.cost.sharing', string="Зардал хувиарлалт")
    
    age = fields.Integer(string="Age" )
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender',related="employee_id.gender")
    order_finished_date = fields.Date(string='Дуусгасан огноо',tracking=True)
    exceeded_day = fields.Integer(string='Хэтэрсэн хоног',tracking=True,store=True,compute ="_exceeded_day")

    @api.model
    def create(self, vals):                              
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('request.order') or '/'       
        if vals.get('employee_id'):
            emp = self.env['hr.employee'].browse(vals.get('employee_id'))
            vals.update({
				'employee_id': emp.id,
				'department_id': emp.department_id.id,
				'sector_id': emp.department_id.parent_id.id,
				'job_id': emp.job_id.id,
				'phone_number': emp.mobile_phone,
				})
        result = super(RequestOrder, self).create(vals)
        return result
    
    
    def stage_find(self, section_id, domain=[], order='sequence asc'):
        """ Override of the base.stage method
        """
        # collect all section_ids
        section_ids = []
        if section_id:
            section_ids.append(section_id)
        section_ids.extend(self.mapped('perform_department_id').ids)
        search_domain = []
        if section_ids:
            search_domain = [('|')] * (len(section_ids) - 1)
            for section_id in section_ids:
                search_domain.append(('department_ids', '=', section_id))
        search_domain += list(domain)
        # perform search, return the first found
        config_id = self.env['request.order.config'].search(search_domain, order=order, limit=1).id
        
        return config_id

    @api.onchange('sector_id')
    def onchange_state(self):
        department_ids = []
        config_ids = self.env['request.order.config'].search([('sequence','=',1),('is_fold','=',False)])
        if config_ids:
            for conf in config_ids:            
                department_ids.extend(conf.department_ids.ids)
        return {'domain':{
                          'perform_department_id':[('id','in',department_ids)]                          
                          },
                          } 

    @api.onchange('perform_department_id')
    def _onchange_perform_department(self):
        if self.perform_department_id and self.active_sequence == 1:
            self.request_config_id = self.stage_find(self.perform_department_id.id)
        else:
            self.request_config_id = False
        
        for order in self:
            request_config_id = self.env['request.order.config'].search([('department_ids','in',order.perform_department_id.id),('field_invisible','=',True)],limit=1)
            request_config_doctor = self.env['request.order.config'].search([('department_ids','in',order.perform_department_id.id),('field_doctor','=',True)],limit=1)
            if request_config_id:
                order.is_invisible_field = True
                order.doctor_field = False
            elif request_config_doctor:
                order.doctor_field = True
            else:
                order.is_invisible_field = False
                order.doctor_field = False
                

    @api.onchange('is_urgent')
    def onchange_is_urgent(self):
        for order in self:
            # if order.is_urgent:
            #     raise UserError((u'Анхаар. Төлбөр 3 дахин нэмэгдэнэ'))
            for line in order.line_ids:
                if line.order_id.is_urgent and line.service_id.is_calculated_percent:
                    line.order_id.write({'is_urgent':True})
                    line.write({'percent_change':3,'is_percent':True})
                else:
                    line.order_id.write({'is_urgent':False})
                    line.write({'percent_change':1,'is_percent':True})


    @api.onchange('employee_id')
    def onchange_employee_id(self):
        line_ids = self.env['request.order.line'].search([('employee_id','=',self.employee_id.id),('order_id.doctor_field','=',True)])
        self.update({'line_history_ids':line_ids.ids})
   

    
    def action_approve(self):
        for order in self:
            config_id = self.env['request.order.config'].search([('sequence','=',order.active_sequence+1),('department_ids','=',order.perform_department_id.id),('is_fold','=',False)])
            if len(config_id)>1 or not config_id:
                raise UserError((u'Хэлтэс дээр урсгал тохиргоо давхар хийгдсэн эсвэл дараагийн урсгал тохиргоо хийгдээгүй байна. Систем админтайгаа холбогдоно уу'))

            order.write({'request_config_id':config_id.id,'active_sequence':order.active_sequence+1})
            order.line_ids.write({'department_id':order.perform_department_id.id})
            if order.request_config_id.python_code:                
                exec(order.request_config_id.python_code)
        self.create_history('Approve',self.active_sequence,'Approve')

    
    def calculate_exceed_day(self):
        for order in self:
            order._exceeded_day()

    
    def action_sent(self):
        
        for order in self:   
                    
            if not order.line_ids :
                raise UserError((u'Ажил үйлчилгээ  сонгоогүй байна.'))
        # TODO FIX LATER
        # employee_obj = self.env['case.history.line']
        # request_config_doctor = self.env['request.order.config'].search([('department_ids','in',order.perform_department_id.id),('field_doctor','=',True)],limit=1)
        # if request_config_doctor:
        #     for line in self.case_history_ids:
        #         employee_obj.create({
        #         'diagnosis':line.diagnosis,
        #         'treatment_adv':line.treatment_adv,
        #         'pain': line.pain,
        #         'vital_signs':line.vital_signs,
        #         'employee_id':line.employee_id.id,
        #     }) 
            
        for order in self:
            config_id = self.env['request.order.config'].search([('sequence','=',order.active_sequence+1),('department_ids','=',order.perform_department_id.id),('is_fold','=',False)])
            
            if len(config_id)>1 or not config_id:
                raise UserError((u'Хэлтэс дээр урсгал тохиргоо давхар хийгдсэн эсвэл дараагийн урсгал тохиргоо хийгдээгүй байна. Систем админтайгаа холбогдоно уу'))
        
            order.write({'request_config_id':config_id.id,'active_sequence':order.active_sequence+1,'is_sent':False})
            order.line_ids.write({'department_id':order.perform_department_id.id})
            if order.request_config_id.python_code:                
                exec(order.request_config_id.python_code)
        
        self.create_history('sent',self.active_sequence,'Илгээсэн')
        
        user_ids = self.mail_users()
        
        if user_ids :
            
            self.mail_send(user_ids)

    
    def action_cancel(self):
        for order in self:
            config_id = self.env['request.order.config'].search([('department_ids','=',order.perform_department_id.id),('is_fold','=',True)])
            if len(config_id)>1 or not config_id:
                raise UserError((u'Хэлтэс дээр урсгал тохиргоо давхар хийгдсэн эсвэл дараагийн урсгал тохиргоо хийгдээгүй байна. Систем админтайгаа холбогдоно уу'))

            order.write({'request_config_id':config_id.id,'active_sequence':config_id.sequence,'is_done':True,'is_cancel':True})
            if order.request_config_id.python_code:                
                exec(order.request_config_id.python_code)
    

    
    def return_draft(self):
        for order in self:
            config_id = self.env['request.order.config'].search([('department_ids','=',order.perform_department_id.id)])
            if not config_id:
                raise UserError((u'Хэлтэс дээр урсгал тохиргоо олдсонгүй. Систем админтайгаа холбогдоно уу'))

            order.write({'request_config_id':1,'active_sequence':1,'is_sent':True,'is_done':False})
            for line in order.line_ids:
                line.write({'state':'draft'})
            if order.request_config_id.python_code:                
                exec(order.request_config_id.python_code)
           

    
    def action_return(self):
        for order in self:
            config_id = self.env['request.order.config'].search([('sequence','=',order.active_sequence-1),('department_ids','=',order.perform_department_id.id),('is_fold','=',False)])
            if len(config_id)>1 or not config_id:
                raise UserError((u'Хэлтэс дээр урсгал тохиргоо давхар хийгдсэн эсвэл дараагийн урсгал тохиргоо хийгдээгүй байна. Систем админтайгаа холбогдоно уу'))

            order.write({'request_config_id':config_id.id,'active_sequence':order.active_sequence-1,'is_sent':True})
            if order.request_config_id.python_code:                
                exec(order.request_config_id.python_code)



    
    def mail_send(self, user_ids):

        
        user_emails = []
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        action_id = self.env['ir.model.data'].get_object_reference('nomin_request_order', 'action_request_order')[1]
        db_name = request.session.db
        
        for email in  self.env['res.users'].browse(user_ids):
            user_emails.append(email.login)
            email_template = self.env['mail.mail'].create({
                    'name': _('Followup '),
                    'email_from': self.env.user.company_id.email or '',
                    'model_id': self.env['ir.model'].search([('model', '=', 'request.order')]).id,
                    # 'subject': subject,
                    # 'email_to': email.login,
                    'lang': self.env.user.lang,
                    'auto_delete': True,
                    # 'body_html':body_html,
                })
            subject = u'"Захиалгын дугаар %s".'%(self.name)
            body_html = u'''
                            <h4>Сайн байна уу, \n Таньд энэ өдрийн мэнд хүргье! </h4>
                            <p>
                               ERP системд %s салбарын %s (хэлтэс) дэх %s дугаартай захиалга %s төлөвт орлоо.                               
                            </p>
                            <p><b><li> Захиалгын дугаар: %s</li></b></p>
                            <p><b><li> Салбар: %s</li></b></p>
                            <p><b><li> Хэлтэс: %s</li></b></p>
                            <p><b><li> Хүсч буй хугацаа: %s</li></b></p>
                            <p><li> <b><a href=%s/web?#id=%s&view_type=form&model=request.order&action=%s>Захиалгын хүсэлт</a></b> цонхоор дамжин харна уу.</li></p>

                            </br>
                            <p>---</p>
                            </br>
                            <p>Энэхүү мэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
                            <p>Баярлалаа.</p>
                        '''%( self.sector_id.name,
                            self.department_id.name,
                            self.name,
                            self.request_config_id.name,
                            self.name,
                             self.sector_id.name,
                            self.department_id.name,
                            self.date_order if self.date_order else " ......... ",
                            base_url,
                            self.id,
                            action_id
                            )
     
            if email.login and email.login.strip():
                email_template.write({'body_html':body_html,'subject':subject,'email_to':email.login})
                email_template.send()
                # email_template.sudo().unlink()
        email = u'\n Дараах хэрэглэгчид рүү имэйл илгээгдэв: ' + ('<b>' + ('</b>, <b>'.join(user_emails)) + '</b>')
        
        self._add_followers(user_ids)
        self.message_post(body=email)

        return True


    
    def unlink(self):
        for order in self:
            if order.active_sequence !=1:
                raise UserError((u'Ноорог төлөв дээр устгах боломжтой.'))

        return super(RequestOrder, self).unlink()


    
    def copy(self):
        raise UserError((u"Хуулбарлан үүсгэх боломжгүй!"))
        return super(RequestOrder, self).copy()


    def get_possible_users(self,sel_user_ids ):
        """Зөвшөөрөгдсөн хэлтэс шалгах"""
        department_ids = []
        user_ids = self.env['res.users'].browse(sel_user_ids)
        
        possible_user_ids = []
        for this in self:
            for user in user_ids:
                department_ids = self.env['hr.department'].search([('id','child_of',user.project_allowed_departments.ids)])
                if department_ids:
                    if this.perform_department_id.id in department_ids.ids:
                        possible_user_ids.append(user.id)    
        
        return possible_user_ids


    def mail_users(self):
        sel_user_ids= []
        user_ids = []
        for order in self:
            if order.request_config_id.select_dep =='perform':
                if order.request_config_id.type =='group':
                    for group in order.request_config_id.group_ids:   
                            for user in group.users:
                                sel_user_ids.append( user.id)
                elif order.request_config_id.type =='distribute':
                    for user in order.request_config_id.user_ids:                        
                        sel_user_ids.append( user.id)
                elif order.request_config_id.type == 'fixed':
                    sel_user_ids.append(order.request_config_id.user_id.id)
                elif order.request_config_id.type == 'department':
                    user_id = order.perform_department_id.manager_id.user_id.id
                    if user_id :
                        sel_user_ids.append( user_id)
            elif order.request_config_id.select_dep =='customer':
                if order.request_config_id.type== 'group':
                    for group in order.request_config_id.group_ids:
                        for user in group.users:
                            sel_user_ids.append(user.id)
                elif order.request_config_id.type == 'fixed':
                    sel_user_ids.append(order.request_config_id.user_id.id)
                elif order.request_config_id.type == 'department':
                    user_id = order.perform_department_id.manager_id.id
                    if user_id :
                        sel_user_ids.append(user_id)
        if sel_user_ids:   
            user_ids = self.get_possible_users(sel_user_ids)
        return user_ids


 
class RequestOrderLine(models.Model):
    _name = 'request.order.line'
    _description = "Request order line"
    _inherit = ['mail.thread']
    _order = 'create_date desc'


    
    def _add_followers(self,user_ids):
        '''Add followers
        '''
        partner_ids = [user.partner_id.id for user in self.env['res.users'].browse(user_ids) if user.partner_id]
        self.message_subscribe(partner_ids=partner_ids)

    
    def action_reject(self):
        '''Цуцлах
        '''      
        self.write({'state':'rejected'})        
        is_change = True
        for line in self.order_id.line_ids:            
            if line.state !='rejected':
                is_change =False
        if is_change:
            self.order_id.action_cancel()
    
    
    def line_reject(self):
        '''Ажил үйлчилгээг мөрөөр цуцлах
        '''      
        return {
            'name': 'Note',            
            'view_mode': 'form',
            'res_model': 'line.reject',          
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',            
        } 


    
    def to_change_price(self):
        '''Нэгж үнэ өөрчлөх
        '''   
        return {
            'name': 'Note',            
            'view_mode': 'form',
            'res_model': 'to.change.price',          
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',            
        }       
        

    
    def action_start(self):
        '''Эхлэх
        '''      
        self.write({'state':'pending'})       

        is_change = 0
        for line in self.order_id.line_ids:            
            if line.state in ['pending','verify','control','done']: 
                is_change +=1 
        if is_change==1:
            self.order_id.action_approve()


    
    def action_done(self):
        '''Дуусгах
        '''       

        line_history_id = self.env['request.order.line.history'].search([('order_line_id','=',self.id)],limit=1,order="create_date desc")

        
        if line_history_id and line_history_id.state == 'verify' or self.is_control:
            self.write({'state':'verify','is_evaluate':False,'is_control':True})
        elif self.state == 'pending' and self.all_done:
            self.write({'state':'done','finished_date':time.strftime("%Y-%m-%d")})
            self.order_id.write({'order_finished_date':time.strftime("%Y-%m-%d")})
        else:
            self.write({'state':'control','finished_date':time.strftime("%Y-%m-%d"),'is_evaluate':True})
            self.order_id.write({'order_finished_date':time.strftime("%Y-%m-%d")})
        for line in self:
            line.order_id._exceeded_day()

        is_change = 0
        length = 0
        count = 0
        length = len(self.order_id.line_ids)
        for line in self.order_id.line_ids:        
            if line.state == 'done':
                count+=1
            if length == count:
                line.order_id.action_approve()
            if line.state in ['control','verify']:
                is_change +=1

            if len (line.line_history_ids) >=1 :                    
                is_change = 99

        if is_change == 1 :
            self.order_id.action_approve()
        
        if self.task_id:
            for attach in self.attach_line_ids:
                if attach.attachment_ids.datas:
                    task_att_ids = request.env['ir.attachment'].sudo().create({  
                                                                        'name':attach.description ,
                                                                        'datas_fname':attach.attachment_ids.datas_fname ,                                                                        
                                                                        'create_date':self.create_date,
                                                                        'datas':attach.attachment_ids.datas,
                                                                        'project_task_document':self.task_id.id,
                                                                        })
    
    def file_attach(self):
        '''Хавсралт даалгавар луу бичих
        ''' 
        
        if self.task_id:
            for attach in self.attach_line_ids:
                if attach.attachment_ids.datas:
                    task_att_ids = request.env['ir.attachment'].sudo().create({  
                                                                        'name':attach.description ,
                                                                        'datas_fname':attach.attachment_ids.datas_fname ,                                                                        
                                                                        'create_date':self.create_date,
                                                                        'datas':attach.attachment_ids.datas,
                                                                        'project_task_document':self.task_id.id,
                                                                        })
            self.is_invisible_button = True
    
    
    def action_evaluate(self):
        
        return {
            'name': 'Note',            
            'view_mode': 'form',
            'res_model': 'to.evaluate.employee',          
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',            
        }

    
    def action_reject(self):
        
        return {
            'name': 'Note',
            'context':{'reject':'reject'},
            'view_mode': 'form',
            'res_model': 'reject.work.service',          
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'state' : 'rejected' ,
        }

    
    def action_control(self):
        
        return {
            'name': 'Note',
            'context':{'control':'control'},
            'view_mode': 'form',
            'res_model': 'to.control.work.service',          
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'state' : 'rejected' ,
        }

    
    def action_return(self):

        return {
            'name': 'Note',
            'context':{'return':'return'},
            'view_mode': 'form',
            'res_model': 'return.work.service',          
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'state' : 'pending' ,
        }



    @api.depends('service_id','unit_price','qty','percent_change','maintenance','is_urgent')    
    def _total_amount(self):

        for line in self:  
            if line.service_id.is_calculated_percent and line.order_id.is_urgent:
                line.percent_change = 3
                line.amount = (line.unit_price * line.qty * line.percent_change)
                if line.maintenance >0:
                    line.amount = (((line.unit_price * line.qty) + ((line.maintenance * line.unit_price) * 0.2)) * line.percent_change )
            elif line.service_id.is_calculated_percent and not line.order_id.is_urgent:
                line.amount = (line.unit_price * line.qty) 
                if line.maintenance >0:                    
                    line.amount = (((line.unit_price * line.qty) + ((line.maintenance * line.unit_price) * 0.2)) * line.percent_change ) 
            elif not line.service_id.is_calculated_percent and not line.order_id.is_urgent:
                line.amount = (line.qty * line.unit_price * line.percent_change)
            elif not line.service_id.is_calculated_percent and  line.order_id.is_urgent:
                line.amount = (line.qty * line.unit_price * line.percent_change)
    
    @api.depends('amount')    
    def _total_score(self):

        for line in self:  
            if line.amount:
                line.total_score = line.amount/1000

    def _is_perform_user(self):
        for line in self:
            line.is_perform_user = False
            if line.perform_employee_id.user_id.id == self._uid:
                line.is_perform_user = True
    
    def _is_evaluate_user(self):
        for line in self:
            line.is_evaluate_user = False
            if line.order_id.employee_id.user_id.id == self._uid:
                line.is_evaluate_user = True

    def _is_control_user(self):
        for line in self:
            line.is_control_user = line.order_id.is_approve_user

    # TODO FIX LATER
    # category_id = fields.Many2one('knowledge.store.category', string="Ангилал" , domain="[('id','in',category_ids[0][2])]" )
    category_id = fields.Many2one('knowledge.store.category', string="Ангилал" ,  )
    service_id = fields.Many2one('work.service',string="Ажил үйлчилгээ" , domain = "[('category_id','=',category_id)]" , required="1")
    order_id = fields.Many2one('request.order', string="Request order" ,ondelete='cascade')
    unit_price = fields.Float(string="Нэгж үнэ" , related='service_id.unit_price')
    unit_price_change = fields.Float(string="Өөрчилсөн үнэ" , tracking=True )
    measurement = fields.Many2one('work.service.measurement',string="Хэмжих нэгж" , related='service_id.measurement')
    employee_id = fields.Many2one('hr.employee',string = 'Захиалагч', ondelete="restrict", related='order_id.employee_id')
    phone_number = fields.Char(string='Утасны дугаар', ondelete="restrict",related='order_id.phone_number')
    department_id = fields.Many2one('hr.department',string="Хэлтэс" , ondelete="restrict",related='order_id.department_id')
    job_id = fields.Many2one('hr.job',string="Албан тушаал" , ondelete="restrict",related='order_id.job_id')
    qty  = fields.Integer(string="Тоо хэмжээ" , required="1" , default=1)
    amount  = fields.Float(string="Дүн" , compute="_total_amount", store=True)
    department_id = fields.Many2one('hr.department' , string='Department' )
    perform_employee_id   = fields.Many2one('hr.employee', string='Гүйцэтгэгч ажилтан',tracking=True)
    date  = fields.Date(string='Хуваариласан  огноо', tracking=True, required=True, default=time.strftime("%Y-%m-%d"))
    date_evaluate = fields.Datetime(string='Date evaluate')
    percent_change = fields.Float(string='Percentage of change' , default=1)    
    maintenance = fields.Integer(string='Maintenance' , tracking=True )
    rate = fields.Float(string="Assessment" , tracking=True)
    description = fields.Text(string="Description")
    change_description = fields.Text(string="Change description")
    is_evaluate = fields.Boolean(string="Is evaluate", default=False)
    is_required = fields.Boolean(string="Is required", default=False)
    is_percent = fields.Boolean(string="Is percent" , default=False )
    is_urgent = fields.Boolean(string="Is urgent" , default=False , ondelete="restrict", related='order_id.is_urgent')
    is_control = fields.Boolean(string="Is control" , default=False)
    finished_date = fields.Date(string='Дуусгасан огноо',tracking=True)
    attach_line_ids              = fields.One2many('request.order.attachment','order_line_id', string="Хавсралт")
    total_score = fields.Integer(string="Total score" ,compute="_total_score",  store=True)

    state = fields.Selection(
                [('draft', 'Ноорог'),
                ('open', 'Хариуцагчтай'),
                 ('pending', 'Хийгдэж буй'),
                 ('verify', 'Шалгуулах'),
                 ('control', 'Хянах'),
                 ('done', 'Хаагдсан'),
                 ('rejected', 'Цуцалсан')], string='Status', readonly=True, tracking=True, copy=False, index=True, default='draft')

    line_history_ids     = fields.One2many('request.order.line.history','order_line_id', string="Request History")
    category_ids = fields.Many2many('knowledge.store.category','knowledge_store_category_order_line_rel','request_line_id','categ_id' ,string='category ids')

    is_perform_user = fields.Boolean(string="Гүйцэтгэгч ажилтан" , default=False, compute='_is_perform_user')
    is_evaluate_user = fields.Boolean(string="Захиалагч ажилтан" , compute="_is_evaluate_user")
    is_control_user = fields.Boolean(string="Гүйцэтгэгч тал хянах" , compute="_is_control_user")
    enter_price = fields.Boolean(string="Enter price" , default=False)
    all_done = fields.Boolean(string='all done' , default=False)
    car_tarif = fields.Float(string="Тээврийн зардал" ,related='category_id.call_cost_tarif')
    is_reject = fields.Boolean(string="Is reject" , default=False)
    project_id = fields.Many2one('project.project',string='Төсөл')
    task_id = fields.Many2one('project.task',domain="[('project_id','=',project_id)]" ,string="Даалгавар")
    is_invisible_button    = fields.Boolean(string='Is invisible button' , default=False)
    diagnosis = fields.Many2one('diagnosis.list',string="Diagnosis")
    treatment_adv = fields.Char(string="Treatment adv")
    pain = fields.Char(string="Pain")
    vital_signs =  fields.Char(string="VItal signs")
    history_id = fields.Many2one('request.order',string = 'Request order1')
    end_date = fields.Date(string='Хаасан огноо', tracking=True, required=True, default=time.strftime("%Y-%m-%d"))


    @api.onchange('state')
    def onchange_state(self):
        '''Гүйцэтгэгч хэлтэст хамаарах ангиллыг харуулах'''
        category_ids = []
        category_ids1 = []
        for line in self:
            service_ids = self.env['work.service'].search([('department_ids','in',line.department_id.id)])
            for service in service_ids:
                if service.category_id:
                    if service.category_id.types == 'tarif':
                        category_ids.append(service.category_id.id)
                    else:
                        category_ids1.append(service.category_id.id)
            if line.order_id.work_type == 'tarif':  
                if category_ids:
                    line.category_ids =[(6, 0, category_ids)]
                    return {'domain':{
                                'category_id':[('id','in',category_ids)]                          
                                },
                                } 
            else:
                if category_ids1:
                    line.category_ids =[(6, 0, category_ids1)]
                    return {'domain':{
                                'category_id':[('id','in',category_ids1)]                          
                                },
                                } 
    # @api.onchange('order_id.work_type')
    # def onchange_work_type(self):
    #     '''ажлын төрлөөс хамаарч харуулах'''
    #     category_ids = []
    #     category_ids1 = []
    #     for line in self:
    #         service_ids = self.env['work.service'].search([('department_ids','in',line.department_id.id)])
    #         for service in service_ids:
    #             if service.category_id:
    #                 if service.category_id.types == 'tarif':
    #                     category_ids.append(service.category_id.id)
    #                 else:
    #                     category_ids1.append(service.category_id.id)
    #         if line.order_id.work_type == 'tarif':  
    #             if category_ids:
    #                 line.category_ids =[(6, 0, category_ids)]
    #                 return {'domain':{
    #                             'category_id':[('id','in',category_ids)]                          
    #                             },
    #                             } 
    #         else:
    #             if category_ids1:
    #                 line.category_ids =[(6, 0, category_ids1)]
    #                 return {'domain':{
    #                             'category_id':[('id','in',category_ids1)]                          
    #                             },
    #                             } 



    @api.onchange('category_id')
    def onchange_category(self):
        for line in self:
            if line.category_id.enter_price:
                line.enter_price = True
            else:
                line.enter_price = False
            
    @api.onchange('service_id')
    def onchange_service(self):
        for line in self:
            if line.order_id.is_urgent and line.service_id.is_calculated_percent :
                line.percent_change = 3
                line.is_percent = True
            else:
                line.percent_change = 1
                line.is_percent = True

    @api.model
    def create(self, vals):
        
        result =  super(RequestOrderLine, self).create(vals)
        if result.order_id.is_urgent and result.service_id.is_calculated_percent :
            result.percent_change = 3
            result.is_percent = True
        else:
            result.percent_change = 1
            result.is_percent = True

        for line in result:
            if line.order_id.active_sequence !=1 and line.order_id.active_sequence !=2:
                raise UserError((u'Энэ төлөв дээр зүйл нэмэх боломжгүй.'))
        return result
    
    def write(self, vals):
        result = super(RequestOrderLine, self).write(vals)  
        if  vals.get('service_id') or vals.get('unit_price'):
            for line in self:
                if line.order_id and line.order_id.is_urgent and line.service_id.is_calculated_percent:
                    line.percent_change = 3
                    line.is_percent = True
                else:
                    line.percent_change = 1
                    line.is_percent = True
  
        return result

class WorkService(models.Model):
    '''Ажил үйлчилгээ
    '''
    _inherit = "work.service"
    
    is_calculated_percent = fields.Boolean(string='Is calculated percent' , default=False , tracking=True)
    collect_amount = fields.Float(string='Collect amount', tracking=True)
    department_ids = fields.Many2many('hr.department' , string='Хэлтсүүд')
    # TODO FIX LATER REMOVE BELOW FIELDS
    unit_price = fields.Float(string='Unit price')
    category_id = fields.Many2one('knowledge.store.category',string='Measure')
class WorkServiceCategory(models.Model):
    '''Ангилал
    '''
    # TODO FIX LATER
    # _inherit = "knowledge.store.category"
    _name = "knowledge.store.category"
    
    
    call_cost = fields.Boolean(string="Call cost" , default=False)
    call_cost_tarif = fields.Float(string="Call cost tarif")
    enter_price = fields.Boolean(string="Enter unit price ")
    types = fields.Selection([('tarif','Тарифт ажлууд'),('order','Захиалгат ажлууд')],string='Зардлын төрөл')
    # TODO FIX LATER REMOVE BELOW FIELDS
    

class RequestOrderHistory(models.Model):
    _inherit = 'request.history'

    request_order_id = fields.Many2one('request.order', string='Request order history', ondelete="cascade")

class DiagnosisList(models.Model):
    '''Оношийн бүртгэл
    '''
    _name = "diagnosis.list"
    _inherit = ['mail.thread']
    
    name = fields.Char(string='Name', tracking=True)
class RequestOrderLineHistory(models.Model): 
    _name = 'request.order.line.history'
    _description = "Request order line history"

    order_line_id = fields.Many2one('request.order.line' , string='Request')
    service_id = fields.Many2one('work.service', string="work service")
    maintenance = fields.Integer(string='Maintenance' , tracking=True )
    description = fields.Text(string="Description")
    unit_price_20 = fields.Float(string="Нэгж үнэ * 20%" , tracking=True) 
    state = fields.Selection(
                [('draft', 'Ноорог'),
                ('open', 'Хариуцагчтай'),
                 ('pending', 'Хийгдэж буй'),
                 ('verify', 'Шалгуулах'),
                 ('control', 'Хянах'),
                 ('done', 'Хаагдсан'),
                 ('rejected', 'Цуцалсан')], string='Status', readonly=True, tracking=True, copy=False, index=True, default='draft')

class RequestOrderAttachment(models.Model):
    _name = 'request.order.attachment'


    order_id = fields.Many2one('request.order', string="Request order")
    order_line_id = fields.Many2one('request.order.line', string="Request order",)
    attachment_ids = fields.Many2many('ir.attachment',string="Хавсралт")
    description = fields.Char(string='Тайлбар')
    date = fields.Datetime(string='Огноо', default=fields.Date.context_today)
    state= fields.Selection([('draft','Ноорог'),('confirmed','Баталгаажсан')],string="Төлөв",default='draft')

    def action_confirm(self):
        self.write({'state':'confirmed'})
        if self.order_line_id:
            self.write({'order_id':self.order_line_id.order_id.id})

    def unlink(self):
        for order in self:
            if order.state !='draft' :
                raise UserError((u'Ноорог төлөвтэй хавсралт устгах боломжтой.'))
        return super(RequestOrderAttachment, self).unlink()



        
