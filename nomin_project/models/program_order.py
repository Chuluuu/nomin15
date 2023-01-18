# -*- coding: utf-8 -*-
import math
import time
from odoo import tools, api, models, fields # 
from datetime import timedelta
from datetime import datetime
import dateutil.relativedelta as relativedelta
from dateutil.relativedelta import relativedelta
import re
from odoo.exceptions import UserError #
import logging
from time import strftime
_logger = logging.getLogger(__name__)

class ir_attachment(models.Model):
    _inherit = 'ir.attachment'

    
    order_file_id = fields.Many2one('order.page','order Number')
    order_id = fields.Many2one('order.page','order Number')

    # create_date = fields.Date(string='Огноо', track_visibility='onchange', default=time.strftime("%Y-%m-%d"))

class BatchName(models.Model):
    _name = 'batch.name'
    _description = 'Batch'
    _order = "name"

    name = fields.Char(string='Багцын нэр', size=80)

class PrSpecDt(models.Model):
    _name = 'pr.spec.dt'
    _description = 'IndicatorName'
    _order = "name"

    name = fields.Char(string='Шаардагдах үзүүлэлт нэр', size=80)
    

class PrSpec(models.Model):
    _name = 'pr.spec'
    _description = 'indicators'
    _order = "name"

    performance_name = fields.Many2one('pr.spec.dt', string='Шаардагдах үзүүлэлт ')
    name = fields.Char(string='Үзүүлэлт', size=80)

class JobName(models.Model):
    _name = 'job.name'
    _description = 'Job name'
    _inherit = ['mail.thread']
    _order = "name"

    
    def _is_senior_manager(self): 

        if self.env.user.has_group('project.group_program_admin'):
            self.is_senior_manager = True
        else:
            self.is_senior_manager = False
        
    name = fields.Char(string='Албан тушаал', size=80 , track_visibility='onchange')
    rate = fields.Float(string='Тариф',track_visibility='onchange')
    is_select = fields.Boolean(string="Сонголтонд харуулах",track_visibility='onchange')
    is_senior_manager = fields.Boolean(string='Ахлах төслийн менежер', compute=_is_senior_manager)

class netSpec(models.Model):
    _name = 'net.spec'
    _description = 'internet'
    _order = 'name'    

    name = fields.Char(string='Суваг нэр', size=80)

class NatPatAccess(models.Model):
    _name = 'nat.pat.access'
    _description = 'nat pat access'
    _order = 'name'    

    name = fields.Char(string='Сувгийн нэр', size=80)


class ProjectStateName(models.Model):
    _name = 'project.state.name'
    _description = 'Project state name'

    name = fields.Char(string='Явц', size=80)

class selType(models.Model):
    _name = 'sel.type'
    _description = 'request type'


    name = fields.Char(string='Хүсэлтиийн төрөл')
    request_name = fields.Char(string="Request name")
    attr =  fields.Boolean(string="Зөвхөн ПХУА-д харагдах")

class BackingUp(models.Model):
    _name = 'backing.up'
    _description = 'internet'
    _order = 'name'    

    name = fields.Char(string='Нөөцлөх мэдээллийн төрөл', size=80)

@api.multi
def check_attachment(self, res_model, res_id):
    '''Ирсэн бичиг дээрх хавсралтыг зөвхөн ноорог төлөв дээр устгах'''
    self._cr.execute("select id from ir_attachment where res_model='%s' and res_id=%s"%(res_model,res_id))
    fetched = self._cr.fetchall()
    if fetched:
        for f in fetched:
            self.env['ir.attachment'].unlink()

class OrderArchived(models.TransientModel):
    _name = 'order.archived'
    _description = u'Order archived'



    @api.multi
    def action_archived(self):
    
        context = self._context
        if context.get('active_model') and context.get('active_id'):
            active_ids = context.get('active_ids')
            
            order_id = self.env['order.page'].browse(active_ids)
            for order in order_id:                
                order_id.write({'state':'archived',
                                'previous_state':order.state
                                })

            
                
            

          
        
        



class OrderPage (models.Model):
    """ Order page """

    _name = "order.page"
    _description = "Order page"
    _inherit = ['mail.thread']
    _order = "create_date DESC"


    @api.multi
    def _add_followers(self,user_ids):
        '''Add followers
        '''
        self.message_subscribe_users(user_ids=user_ids)


    @api.multi
    def name_get(self):
        res = []
        for obj in self:
            name = obj.name
            if not name:
                name = ''
            if obj.order_name:
                name += ' %s' % (obj.order_name,)
            res.append((obj.id,name))
        return res


 
    @api.multi
    def action_to_confirm(self):
        '''Хянах
        '''

        template_id = self.env['ir.model.data'].get_object_reference('nomin_project', 'email_template_of_ordering')[1]
        title = unicode(' Захиалгын мэдэгдэл','utf-8')

        for exec1 in self.confirm_user_ids:


            data = {
                    'email_title': title,
                    'request': self.request_type.name,
                    'name': self.name,
                    'order_name': self.order_name,
                    'email_to': exec1.login,
                    'content': self.state, 
                    'model': 'order.page',                   
                    'department_id': self.department_id.name,
                    'states': 'Батлагдсан',
                    'requested_date': str(self.start_date),        
                    'process_employee': self.employee_id.name,
                    'email_from': self.employee_id.name,
                    }
            email_obj = self.env['mail.template']

            self.env.context = data
            if template_id and exec1:
                self.pool['mail.template'].send_mail(self.env.cr, 1, template_id, exec1.id, force_send=True, context=self.env.context)
       
        self.write({'state':'confirmed'})


    @api.multi
    def action_to_approved1(self):
        '''Хянах
        '''       
       
        self.write({'state':'approved1'})
    
    @api.multi
    def skip_state(self):
        '''төлөв алгасах
        '''
        for order in self:
            if not  order.is_cost_approved and  not order.cost_approved_fully:
                raise UserError(('Зардал батлагдсан,Зардал бүрэн батлагдсан талбарын аль нэгийг нь чеклэнэ үү'))
            if order.is_cost_approved:
                order.write({'state':'cost_done'})
            if order.cost_approved_fully:
                order.write({'state':'estimated'})
    

    @api.multi
    def order_recovery(self):
        '''Архиваас сэргээх
        '''
        for order in self:
            if order.previous_state:                              
                self._cr.execute('UPDATE order_page '\
                       'SET state=%s '\
                       'WHERE id = %s', (order.previous_state, (self.id)))


    @api.multi
    def action_to_approve_cost(self):
        '''Хянах
        '''

        template_id = self.env['ir.model.data'].get_object_reference('nomin_project', 'email_template_of_ordering')[1]
        title = unicode(' Захиалгын мэдэгдэл','utf-8')

        for exec1 in self.confirmed_employee_id:


            data = {
                    'email_title': title,
                    'request': self.request_type.name,
                    'name': self.name,
                    'order_name': self.order_name,
                    'email_to': exec1.login,
                    'content': self.state, 
                    'model': 'order.page',                   
                    'department_id': self.department_id.name,
                    'states': 'Зардал батлуулах',
                    'requested_date': str(self.start_date),        
                    'process_employee': self.employee_id.name,
                    'email_from': self.employee_id.name,
                    }

            self.env.context = data
            if template_id and exec1:
                self.pool['mail.template'].send_mail(self.env.cr, 1, template_id, exec1.user_id.id, force_send=True, context=self.env.context)
        
        for order in self:

            if not order.project_started_date:
                raise UserError(('Төсөл эхлэх огноог заавал тохируулж өгнө үү!!!'))
            if not order.project_finished_date:
                raise UserError(('Төслийн дуусах огноог заавал тохируулж өгнө үү!!!'))
            if order.project_progress_percentage == 0:
                raise UserError(('Төслийн явцыг хувиар заавал тохируулж өгнө үү!!!'))
            # if order.is_cost_approved:
            #     order.write({'state':'cost_done'})
            # elif order.cost_approved_fully:
            #     order.write({'state':'estimated'})
            # else:
            #     order.write({'state':'approve_cost'})

            if order.approve_employee_id:
                self.write({'confirmed_employee_id2':order.approve_employee_id.id})    
        self.write({'state':'approve_cost'})
        

    @api.multi
    def action_to_approve_cost_in(self):
        '''Хянах
        '''

        for order in self:
            if not order.project_started_date:
                raise UserError(('Төсөл эхлэх огноог заавал тохируулж өгнө үү!!!'))
            if not order.project_finished_date:
                raise UserError(('Төслийн дуусах огноог заавал тохируулж өгнө үү!!!'))
                
            if order.project_progress_percentage == 0:
                raise UserError(('Төслийн явцыг хувиар заавал тохируулж өгнө үү!!!'))
            # if order.is_cost_approved:
            #     order.write({'state':'cost_done'})
            # elif order.cost_approved_fully:
            #     order.write({'state':'estimated'})
            # else:
            #     order.write({'state':'approve_cost'})
            if order.approve_employee_id:
                self.write({'confirmed_employee_id2':order.approve_employee_id.id})
           
        self.write({'state':'approve_cost'})
        
        
    @api.multi
    def action_handover(self):
           
        return {
            'name': 'Note',            
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'implemented.tasks',          
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',            
        }
    
    @api.multi
    def to_receive(self):
        # self.message_post(body=u"Хүлээн авсан огноо %s " %(self.create_date))
        # self.message_post(body=u"Хүлээн авсан огноо test %s " %(time.strftime("%Y-%m-%d")))
       
        return {
            'name': 'Note',            
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'order.page.receive',          
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',            
        }
    
    @api.one
    def _is_confirm_user(self):
        for order in self:
            if self._uid not in order.confirmed_user_ids.ids and self._uid == order.receive_employee_id1.user_id.id:                
                order.is_confirm_user =True
            if self._uid not in order.confirmed_user_ids.ids and self._uid == order.receive_employee_id2.user_id.id:                
                order.is_confirm_user =True
            if self._uid not in order.confirmed_user_ids.ids and self._uid == order.receive_employee_id3.user_id.id:                
                order.is_confirm_user =True


    @api.multi
    def action_confirmed(self):

        '''Батлах
        '''
        employee = self.env['hr.employee']
        employee_id = employee.sudo().search([('user_id','=',self._uid)])
        for order in self:
            order.get_engineer()
            order.write({'state':'approved1','confirmed_employee_id':employee_id.id})
            for user in order.engineer_ids:
                if user:
                    order.sudo()._add_followers(user.id)
       

        



    @api.multi
    def action_to_estimate(self):
        '''Ирсэн захиалгыг хянуулах төлөвт оруулж байна.
        '''

        request_line = self.env['request.config.ordering.flow']
        dep_obj = self.env['hr.department']


        line_ids = request_line.search([('request_id','=',self.request_id.id),('state','=','estimated')])

        confirm_user_ids = []
        for line in line_ids:
            for user in line.group_id.users:

                confirm_user_ids.append(user.id)


        if confirm_user_ids != []:
            self.write({'confirm_user_ids':[(6,0,confirm_user_ids)]})
            self.message_subscribe_users(confirm_user_ids)  
           
        else:
            raise UserError(('Confirm users not found.'))
        
        self.write({'state': 'estimated', 'project_progress_percentage':100})

        template_id = self.env['ir.model.data'].get_object_reference('nomin_project', 'email_template_of_ordering')[1]
        title = unicode(' Захиалгын мэдэгдэл','utf-8')

        for exec1 in self.confirm_user_ids:


            data = {
                    'email_title': title,
                    'request': self.request_type.name,
                    'name': self.name,
                    'order_name': self.order_name,
                    'email_to': exec1.login,
                    'content': self.state, 
                    'model': 'order.page',                   
                    'department_id': self.department_id.name,
                    'states': 'Хянуулах',
                    'requested_date': str(self.start_date),        
                    'process_employee': self.employee_id.name,
                    }
            email_obj = self.env['mail.template']

            self.env.context = data
            if template_id and exec1:
                self.pool['mail.template'].send_mail(self.env.cr, 1, template_id, exec1.id, force_send=True, context=self.env.context)



    @api.multi
    def action_to_approve(self):
        '''Ирсэн захиалгыг хянасан төлөвт оруулж байна.
        '''

        body = u'Төлөв: → ' + u'  Хянасан '

        if self.accountant_id:
            self.sudo()._add_followers(self.accountant_id.user_id.id)




        self.message_post(cbody= body)
        self.write({'state':'approved'})



    @api.multi
    def action_to_slow_up(self):
        '''Ирсэн захиалгыг хойшлогдсон төлөвт оруулж байна.
        '''
        if self.rejection_reason == False:
            raise UserError(('Хойшлуулах болсон шалтгаанаа бичнэ үү!'))
        else:
            self.write({'state':'slow_up'})

    @api.multi
    def action_to_reject(self):
        '''Ирсэн захиалгыг цуцлагдсан төлөвт оруулж байна.
        '''
        if self.rejection_reason == False:
            raise UserError(('Татгалзсан шалтгаанаа бичнэ үү!'))
        else:
            self.write({'state':'rejected'})





    # @api.multi
    # def reject_to_director(self):
    #     '''Ирсэн захиалгыг цуцлагдсан төлөвт оруулж байна.
    #     '''
    #     if self.rejection_reason == False:
    #         raise UserError(('Шалтгаан талбарыг бөглөнө үү!'))
    #     else:
    #         self.write({'state':'sent_director'})

    # @api.multi
    # def slow_up_to_director(self):
    #     '''Ирсэн захиалгыг цуцлагдсан төлөвт оруулж байна.
    #     '''
    #     if self.rejection_reason == False:
    #         raise UserError(('Шалтгаан талбарыг бөглөнө үү!'))
    #     else:
    #         self.write({'state':'sent_director'})


    @api.multi
    def action_to_done_cost(self):

        # body = u'Төлөв: → ' + u' Зардал батлуулах. '

        # self.message_post(body=u"Зардал баталсан огноо %s " %(self.create_date))
        self.message_post(body=u"Зардал баталсан огноо %s " %(time.strftime("%Y-%m-%d")))



        # self.message_post(cbody= body)
        count = []        

        for order in self:
            if self._uid not in order.confirmed_user_ids2.ids:
               order.write({'confirmed_user_ids2':[(6,0,[self._uid]+order.confirmed_user_ids2.ids)]})

            if order.confirmed_employee_id.id and order.confirmed_employee_id.id not in count:
                count.append(order.confirmed_employee_id.id) 
            if order.confirmed_employee_id2.id and order.confirmed_employee_id2.id not in count:
                count.append(order.confirmed_employee_id2.id) 


        if len(order.confirmed_user_ids2)== len(count) : 
            order.write({'state':'cost_done',
                        'confirmed_date1':time.strftime("%Y-%m-%d")
            		    })



    @api.multi
    def action_to_done_cost_in(self):

        # body = u'Төлөв: → ' + u' Дотоодод зардал батлуулах. '

        # self.message_post(cbody= body)

        # self.message_post(body=u"Зардал баталсан огноо %s " %(self.create_date))
        self.message_post(body=u"Зардал баталсан огноо %s " %(time.strftime("%Y-%m-%d")))
        

        count = []        

        for order in self:
            if self._uid not in order.confirmed_user_ids2.ids:
               order.write({'confirmed_user_ids2':[(6,0,[self._uid]+order.confirmed_user_ids2.ids)]})

            if order.confirmed_employee_id.id and order.confirmed_employee_id.id not in count:
                count.append(order.confirmed_employee_id.id) 
            if order.confirmed_employee_id2.id and order.confirmed_employee_id2.id not in count:
                count.append(order.confirmed_employee_id2.id) 
            


        if len(order.confirmed_user_ids2)== len(count) : 

            order.write({'state':'cost_done',
                        'confirmed_date1':time.strftime("%Y-%m-%d")
            		    })


       


    @api.multi
    def action_to_allocate(self):
        '''Ирсэн захиалгыг хуваарилагдсан төлөвт оруулж байна.
        '''
        body = u'Төлөв: → ' + u' Хуваарилах. '
        for order in self:            
            if not order.project_senior_manager_id  :
                raise UserError((u'Ахлах төслийн менежер сонгоно уу.'))
            if not order.project_manager_id  :
                raise UserError((u'Төслийн менежерт онооно уу.'))
            if not order.cost_types  :
                raise UserError((u'Зардлын төрлөө сонгоно уу.'))

        if self.project_manager_id:
                self.sudo()._add_followers(self.project_manager_id.user_id.id)

        self.message_post(cbody= body)
        self.write({'state':'allocated','assigned_date':time.strftime("%Y-%m-%d")})
        template_id = self.env['ir.model.data'].get_object_reference('nomin_project', 'email_template_of_ordering')[1]
        title = unicode(' Захиалгын мэдэгдэл','utf-8')

        data = {
                    'email_title': title,
                    'request': self.request_type.name,
                    'name': self.name,
                    'order_name': self.order_name,
                    'email_to': self.project_manager_id.user_id.login,
                    'content': self.state, 
                    'model': 'order.page',                   
                    'department_id': self.department_id.name,
                    'states': 'Хуваарилагдсан',
                    'requested_date': str(self.start_date),        
                    'process_employee': self.employee_id.name,
                    }
        email_obj = self.env['mail.template']

        self.env.context = data
        self.pool['mail.template'].send_mail(self.env.cr, 1, template_id, self.project_manager_id.user_id.id, force_send=True, context=self.env.context)


    @api.multi
    def action_to_allocate_sys_admin(self):
        '''Ирсэн захиалгыг хуваарилагдсан төлөвт оруулж байна.
        '''
        body = u'Төлөв: → ' + u' Систем админ руу хуваарилах. '
        if self.request_type.id == 2 or self.request_type.id == 3 or self.request_type.id == 51 or self.request_type.id == 6:

            if self.system_admin_id:
                    self.sudo()._add_followers(self.system_admin_id.user_id.id)

    

            self.message_post(cbody= body)
            self.write({'state':'allocated','assigned_date':time.strftime("%Y-%m-%d")})

            template_id = self.env['ir.model.data'].get_object_reference('nomin_project', 'email_template_of_ordering')[1]
            title = unicode(' Захиалгын мэдэгдэл','utf-8')

            data = {
                        'email_title': title,
                        'request': self.request_type.name,
                        'name': self.name,
                        'email_to': self.system_admin_id.user_id.login,
                        'content': self.state, 
                        'model': 'order.page',                   
                        'department_id': self.department_id.name,
                        'states': 'Хуваарилагдсан',
                        'requested_date': str(self.start_date),        
                        'process_employee': self.employee_id.name,
                        }
            email_obj = self.env['mail.template']

            self.env.context = data
            self.pool['mail.template'].send_mail(self.env.cr, 1, template_id, self.system_admin_id.user_id.id, force_send=True, context=self.env.context)

        if self.request_type.id == 17:

            if self.project_manager_id:
                    self.sudo()._add_followers(self.project_manager_id.user_id.id)

            self.message_post(cbody= body)
            self.write({'state':'allocated','assigned_date':time.strftime("%Y-%m-%d")})

            template_id = self.env['ir.model.data'].get_object_reference('nomin_project', 'email_template_of_ordering')[1]
            title = unicode(' Захиалгын мэдэгдэл','utf-8')

            data = {
                        'email_title': title,
                        'request': self.request_type.name,
                        'name': self.name,
                        'email_to': self.project_manager_id.user_id.login,
                        'content': self.state, 
                        'model': 'order.page',                   
                        'department_id': self.department_id.name,
                        'states': 'Хуваарилагдсан',
                        'requested_date': str(self.start_date),        
                        'process_employee': self.employee_id.name,
                        }
            email_obj = self.env['mail.template']

            self.env.context = data
            self.pool['mail.template'].send_mail(self.env.cr, 1, template_id, self.project_manager_id.user_id.id, force_send=True, context=self.env.context)



    @api.multi
    def action_to_done(self):
        '''Ирсэн захиалгыг done төлөвт оруулж байна.
        '''
        body = u'Төлөв: → ' + u' Дуусгах. '
        self.message_post(cbody= body)
        self.write({'state':'done'})
    
    @api.multi
    def training_done(self):
        '''Сургалтын захиалгыг дуусгах
        '''
        body = u'Төлөв: → ' + u' Дуусгах. '
        self.message_post(cbody= body)
        self.write({'state':'done'})
    
    @api.multi
    def action_done(self):
        '''Эрхийн хүсэлтийн захиалгыг дуусгах
        '''
        body = u'Төлөв: → ' + u' Дуусгах. '
        self.message_post(cbody= body)
        self.write({'state':'done'})

    @api.multi
    def action_to_done1(self):
        '''Ирсэн захиалгыг дууссан төлөвт оруулж байна.
        '''
        body = u'Төлөв: → ' + u' дуусгах. '
        self.message_post(cbody= body)
        self.write({'state':'done'})

    @api.multi
    def action_to_order_done(self):
        '''Ирсэн захиалгыг цуцлагдсан төлөвт оруулж байна.
        '''
        body = u'Төлөв: → ' + u' дуусгах. '
        self.message_post(cbody= body)
        self.write({'state':'done'})


    @api.multi
    def action_to_draft(self):
        '''Ирсэн захиалгыг ноорог төлөвт оруулж байна.
        '''
        body = u'Төлөв: → ' + u' Буцаасан. '
        self.message_post(cbody= body)       
        self.write({'state':'draft','sequence':0, 'rejection_reason':' '})


    @api.multi
    def action_to_stop(self):
        '''Ирсэн захиалгыг зогссон төлөвт оруулж байна.
        '''
        body = u'Төлөв: → ' + u' Буцаасан. '

        if self.rejection_reason == False:
            raise UserError(('Зогсох төлөвт оруулах болсон шалтгаанаа бичнэ үү!'))
        else:
            self.write({'state':'stop'})



    @api.multi
    def action_to_allocated(self):
        '''Ирсэн захиалгыг зогссон төлөвт оруулж байна.
        '''
        body = u'Төлөв: → ' + u' Буцаасан. '
        self.message_post(cbody= body)       
        self.write({'state':'allocated'})





    @api.multi
    def unlink(self):
        '''Нооргоос бусад үед устгахгүй байх.
        '''
        for main in self:
            if main.state != 'draft':
                raise UserError((u'Ноорог төлөвтэй үед устгах боломжтой'))
            check_attachment(self, 'order.page', main.id)
        return super(OrderPage, self).unlink()
    




    def _set_employee1(self):
        '''хэрэглэгчийн ажилтныг авна
        '''
        employee_ids = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        if employee_ids:
            return employee_ids
        else:
            raise UserError((u'Хэлтэс дээр урсгал тохиргоо хийгдээгүй байна. Систем админтайгаа холбогдоно уу'))

    # @api.model
    # def _set_department(self):
    #     if self.env.user.department_id:
    #         return self.env.user.department_id.id
    #     return None

    # def _set_employee_telephone(self):
    #     '''хэрэглэгчийн ажилтаныг авна
    #     '''
    #     employee_ids = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
    #     if employee_ids:
    #         return employee_ids.mobile_phone
    #     else:
    #         raise UserError(('You don\'t have mobile phone employee.'))

    # def _set_employee_email(self):
    #     '''хэрэглэгчийн ажилтаныг авна
    #     '''
    #     employee_ids = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
    #     if employee_ids:
    #         return employee_ids.work_email
    #     else:
    #         raise UserError(('You don\'t have email.'))



    def _request_id(self):


        if self.request_type.id == 1 :
            config = self.env['request.config'].search([('department_ids','in',self.env.user.department_id.id),('process','=','program.order.flow'),('ordering_type_id','=','program')])
        elif (self.request_type.id == 2 or self.request_type.id == 3 or self.request_type.id == 51 or self.request_type.request_name == 'installation_order'):
            config = self.env['request.config'].search([('department_ids','in',self.env.user.department_id.id),('process','=','program.order.flow'),('ordering_type_id','=','system')])
        elif (self.request_type.id == 16 or self.request_type.id == 17 ):
            config = self.env['request.config'].search([('department_ids','in',self.env.user.department_id.id),('process','=','program.order.flow'),('ordering_type_id','=','training')])
        else:
            config = self.env['request.config'].search([('department_ids','in',self.env.user.department_id.id),('process','=','program.order.flow'),('ordering_type_id','=','system_senior')])

        if config:

            return config.id

        else:
            raise UserError((u'Хэлтэс дээр урсгал тохиргоо хийгдээгүй байна. Систем админтайгаа холбогдоно уу'))



    @api.one
    def _show_control_button(self):       

        if self.control_employee_id:         
            if self.control_employee_id.user_id.id == self.env.user.id:

                self.show_control_button = True

    @api.one
    def _is_employee (self):       

        if self.employee_id:         
            if self.employee_id.user_id.id == self.env.user.id:

                self.is_employee = True



    # @api.one
    # def _show_confirm_button(self):
    #     '''
    #        Батлах хэрэглэгчид харуулах эсэх тооцох
    #     '''
    #     if self.confirm_employee_id or self.approve_employee_id:
    #          if self.confirm_employee_id.user_id.id == self.env.user.id or  self.approve_employee_id.user_id.id == self.env.user.id  :
    #            self.show_confirm_button = True

    @api.one
    def _show_confirm_button(self):
        for order in self:
            if self._uid not in order.confirmed_user_ids2.ids and self._uid == order.confirm_employee_id.user_id.id:                
                order.show_confirm_button =True
            if self._uid not in order.confirmed_user_ids2.ids and self._uid == order.approve_employee_id.user_id.id:                
                order.show_confirm_button =True
          

    @api.one
    def _show_done_button(self):
        '''
           Нягтланд дуусгах товч харуулах 
        '''
        if self.accountant_id:
             if self.accountant_id.user_id.id == self.env.user.id :
               self.show_done_button = True



    @api.one
    def _is_inlist(self):        

        for line in self.project_manager_id:
         
            if line.user_id.id == self.env.user.id:                
                self.is_inlist = True
    
    @api.one
    def _senior_manager(self):        
        
        for line in self.project_senior_manager_id:
         
            if line.user_id.id == self.env.user.id:                
                self.senior_manager = True




    @api.one
    def _is_list(self):        

        for line in self.system_admin_id:
         
            if line.user_id.id == self.env.user.id:                
                self.is_list = True
    
    @api.one
    def _is_training_manager(self):        

        if self.training_manager_id:
            if self.training_manager_id.user_id.id == self.env.user.id:                
                self.is_training_manager = True


    @api.one
    def _is_project_manager(self):
        for line in self.request_id.program_order_flow_lines:
            if self.request_type.id == 1:
                if line.state == 'approved1' or line.state == 'estimated':
                    for user in line.group_id.users:
                        if user.id == self.env.user.id:
                            self.is_project_manager = True
                            break
    @api.one
    def _is_manager_of_the_project(self):
        if self.project_manager_id.user_id == self.env.user:
            self.is_manager_of_the_project = True

    @api.one
    def _is_system_admin(self):
        for order in self:
            if order.request_type.request_name == 'installation_order':
                for user in order.engineer_ids:                    
                    if user.id == self.env.user.id:
                        order.is_system_admin = True
                        break
            else:
                for line in order.request_id.program_order_flow_lines:
                    if order.request_type.id == 2 or order.request_type.id == 3 or order.request_type.id == 51:
                        if line.state == 'approved1':
                            for user in line.group_id.users:
                                if user.id == order.env.user.id:
                                    order.is_system_admin = True
                                    break
            
    @api.one
    def _is_system_senior(self):
       for line in self.request_id.program_order_flow_lines:
            if self.request_type.id == 4 or self.request_type.id == 5 or self.request_type.id == 6 or self.request_type.id == 11 or self.request_type.id == 12 or self.request_type.id == 13:
                if line.state == 'approved1':
                    for user in line.group_id.users:
                        if user.id == self.env.user.id:
                            self.is_system_senior = True
                            break
    
    @api.one
    def _is_system_quality_assurance(self):
       for line in self.request_id.program_order_flow_lines:
            if self.request_type.id == 17 or self.request_type.id == 16:
                if line.state == 'approved1':
                    for user in line.group_id.users:
                        if user.id == self.env.user.id:
                            self.is_system_quality_assurance = True
                            break
            



    @api.onchange('request_type')
    def onchange_request_type(self):

        if self.env.user.department_id.id != 88:

            return {'domain':
                            {'request_type':[('attr','=', True)]}}


    @api.one
    def planned_time_cost(self):
        time = 0
        cost = 0
        total = 0
        sum_total = 0 
        for line in self.cost_info:
            time = line.time_info
            cost = line.rate
            total = time * cost
            sum_total += total

        self.time_cost_info = sum_total 




    def _get_senior_manager_domain(self): 

        group_ids = [
                self.env['ir.model.data'].get_object_reference('project', 'group_program_admin')[1]]

        return [('user_id.groups_id','in',group_ids)]

    confirmed_user_ids = fields.Many2many('res.users','order_res_users_rel','order_id','user_id', string='Employees1')
    confirmed_user_ids2 = fields.Many2many('res.users','order_res_users_rel2','order_id','user_id', string='Employees2')
    is_confirm_user = fields.Boolean(string="is Confirm user",compute='_is_confirm_user', default=False)

    confirmed_employee_id = fields.Many2one('hr.employee', 'Зардал батлах ажилтан 1', readonly=True)
    confirmed_employee_id2 = fields.Many2one('hr.employee', 'Зардал батлах ажилтан 2', readonly=True)
    receive_employee_id1 = fields.Many2one('hr.employee', 'Хүлээн авах ажилтан 1', readonly=True)
    receive_employee_id2 = fields.Many2one('hr.employee', 'Хүлээн авах ажилтан 2', readonly=True)
    receive_employee_id3 = fields.Many2one('hr.employee', 'Хүлээн авах ажилтан 3', readonly=True)
    receive_date1 = fields.Date(string='Хүлээн авсан огноо')
    receive_date2 = fields.Date(string='Хүлээн авсан огноо')
    receive_date3 = fields.Date(string='Хүлээн авсан огноо')
    control_employee_id = fields.Many2one('hr.employee', string='Хянах ажилтан',track_visibility='onchange')
    confirm_employee_id = fields.Many2one('hr.employee', string='Батлах ажилтан',track_visibility='onchange')
    is_cost_approved = fields.Boolean(string='Зардал батлагдсан', default=False,track_visibility='onchange')
    cost_approved_fully = fields.Boolean(string='Зардал бүрэн батлагдсан', default=False,track_visibility='onchange')
    is_control = fields.Boolean(string='Хянах процессыг алгасах эсэх', default=False,track_visibility='onchange')
    is_handover = fields.Boolean(string='Системээр акт хүлээлцэх эсэх', default=False,track_visibility='onchange')
    is_receive = fields.Boolean(string='Захиалгатай холбоотой ажлуудыг хүлээн авч баталгаажуулж байна')
    technical_info_choose = fields.Selection([('batch','Багц сонгох'),('other','Бусад')], string="Техник үзүүлэлт" , default="batch")
    email = fields.Char('Имэйл',readonly=True, track_visibility='always',related='employee_id.work_email')
    dedication = fields.Selection([('ded1','Зориулалт1'),('ded2','Зориулалт2'),('ded3','Зориулалт3')], string='Зориулалт', default='ded1', required=True)
    telephone = fields.Char('Утас',readonly=True, track_visibility='always',related='employee_id.mobile_phone')
    name = fields.Char(string='Дугаар', readonly=True , default="New")
    employee_id = fields.Many2one('hr.employee',string = 'Захиалга үүсгэгч', ondelete="restrict", track_visibility='always', default=_set_employee1)
    department_id = fields.Many2one('hr.department', string = 'Захиалагч салбар', ondelete="restrict", track_visibility='always', related='employee_id.department_id')
    # job_id = fields.Many2one('hr.job', string='Jobs', ondelete="restrict", track_visibility='always')
    date=fields.Date(string='Хүлээн авах эцсийн хугацаа' ,default=(datetime.today()+relativedelta(days=7)).strftime('%Y-%m-%d'))
    start_date = fields.Date(string='Захиалга өгсөн огноо', track_visibility='onchange', required=True, default=time.strftime("%Y-%m-%d"))
    assigned_date = fields.Date(string='Хуваарилагдсан огноо',track_visibility='onchange')
    project_progress_percentage=fields.Integer(string='Төслийн явц%(enter дарна уу!)',track_visibility='onchange')
    project_started_date=fields.Date(string='Төсөл эхлэх огноо', track_visibility='onchange')
    project_finished_date=fields.Date(string='Tөсөл дуусах огноо', track_visibility='onchange', default=time.strftime("%Y-%m-%d"))
    confirmed_date = fields.Date(string='Батлагдсан огноо',track_visibility='onchange', default=time.strftime("%Y-%m-%d"))
    confirmed_date1 = fields.Date(string='Зардал баталсан огноо',track_visibility='onchange' )
    confirmed_date2 = fields.Date(string='Зардал баталсан огноо',track_visibility='onchange')
    handover_date = fields.Date(string='Хүлээлгэн өгөх дарсан огноо',track_visibility='onchange', default=time.strftime("%Y-%m-%d"))
    review_date = fields.Date(string='Хянуулах төлөвт орсон огноо',track_visibility='onchange', default=time.strftime("%Y-%m-%d"))


    request_type = fields.Many2one('sel.type', string="Хүсэлтийн төрөл")

    purpose = fields.Text(string="Зорилго")
    result = fields.Text(string="Үр ашиг, хүлээж буй үр дүн")
    order_offer = fields.Text(string='Одоогийн үйл ажиллагаа')
    difficulty = fields.Text(string='Тулгарч байгаа хүндрэл бэрхшээл')
    order_name = fields.Char (string='Ажлын нэр')

    reg_file = fields.Many2one('ir.attachment','File', readonly=True)
    req_file = fields.One2many('ir.attachment','order_id',u'Шаардлага / Хавсралт')
    annex_file = fields.One2many('ir.attachment','order_file_id', string='Хавсралт')
    datas_fname =  fields.Char(related = 'reg_file.datas_fname', string='File name', store=True, readonly=True)


    show_confirm_button=fields.Boolean(compute=_show_confirm_button,string = 'Батлах',type='boolean')
    show_control_button=fields.Boolean(compute=_show_control_button,string = 'хянах',type='boolean')
    is_employee=fields.Boolean(compute=_is_employee,string = 'Захиалга үүсгэгч',type='boolean')
    show_done_button=fields.Boolean(compute=_show_done_button,string = 'дуусгах',type='boolean')

    is_inlist = fields.Boolean(string="is in list", compute=_is_inlist, default=False)
    senior_manager = fields.Boolean(string="is senior manager", compute=_senior_manager, default=False)
    is_list = fields.Boolean(string="is list", compute=_is_list, default=False)
    is_training_manager = fields.Boolean(string="is training manager", compute=_is_training_manager, default=False)
    is_project_manager = fields.Boolean(string="Is project manager", compute=_is_project_manager, default=False)
    is_manager_of_the_project = fields.Boolean(string="Is manager of the project", compute=_is_manager_of_the_project, default=False)
    is_system_admin = fields.Boolean(string="Is system admin", compute=_is_system_admin, default=False)
    engineer_ids = fields.Many2many('res.users','order_res_users_rel_engineer','order_id','user_id',string="Installation engineer")
    is_system_senior = fields.Boolean(string="Is system senior", compute=_is_system_senior, default=False)
    is_system_quality_assurance = fields.Boolean(string="Is system quality assurance", compute=_is_system_quality_assurance, default=False)
    rejection_reason = fields.Text(string="Татгалзсан шалтгаан" , track_visibility='onchange')
    description_admin = fields.Text(string="Тайлбар " , track_visibility='onchange')
    description_admin1 = fields.Text(string="Тайлбар " , track_visibility='onchange')

    # job_id=fields.Many2one(related='employee_id.job_id', store=True , string="Албан тушаал tets")
    job =fields.Many2one(related='employee_id.job_id' , string="Албан тушаал new")
    request_rating = fields.Selection([('0','Хэвийн'),('1','Яаралтай'),('2','Нэн яаралтай')], string='Хүсэлтийн зэрэглэл',required=True)
    company_id = fields.Many2one('res.company', 'Компани', readonly=True, ondelete='restrict', track_visibility='always',related='employee_id.department_id.company_id')
    logged_in_employee_id = fields.Many2one('hr.employee',string = 'Employee', readonly=True, ondelete="restrict", track_visibility='always', default=lambda self: self._set_employee1())
    request_id = fields.Many2one('request.config', string='Request config',  track_visibility='onchange')
    confirm_user_ids = fields.Many2many('res.users', string='Agreed Users')
    leave_flow = fields.Integer(string = 'Leave Flow')
    state = fields.Selection([
                                ('draft',u'Ноорог'),
                                ('control',u'Хянах'),
                                ('confirmed',u'Батлах'),
                                ('approved1',u'Батлагдсан'),                            
                                ('allocated',u'Хуваарилагдсан'),
                                ('approve_cost',u'Зардал батлуулах'),
                                ('cost_done',u'Зардал батлагдсан'),
                                ('sent_director',u'Захирал хянах'),
                                ('handover',u'Хүлээлцэх'),
                                ('estimated',u'Хянуулах'),
                                ('approved',u'Хянасан'),
                                ('archived',u'Архивлагдсан'),
                                ('done',u'Дууссан'),                                
                                ('slow_up',u'Хойшлогдсон'),
                                ('rejected',u'Татгалзсан'),
                                ('stop',u'Зогссон'),
                                ], u'Төлөв', track_visibility='always', default = 'draft')
    state_sequence = fields.Char(string = 'State sequence')

    technical_infos = fields.One2many('server.info','server_id', string='Үзүүлэлт')    
    plan_info = fields.One2many('server.info','plan_id' , string='Ерөнхий төлөвлөгөө')
    cost_info = fields.One2many('server.info','cost_id' , string='Зардлын мэдээлэл')
    task_info = fields.One2many('server.info','task_id' , string='Хийгдсэн ажлууд')
    access_info = fields.One2many('server.info','nat_access_id')
    pat_access_info = fields.One2many('server.info','pat_access_id')
    internet_infos = fields.One2many('server.info','net_id' , string="Интернэтийн мэдээлэл")
    server_net_info = fields.One2many('server.info','server_net_id' , string="Серверийн интернэтийн мэдээлэл")
    vpn_infos = fields.One2many('server.info','vpn_id', string='Дотоод төрөл')
    vpn_out_infos = fields.One2many('server.info','vpn_out_id', string='Гадаад төрөл')
    server_access_infos = fields.One2many('server.info','access_id', string='Гадаад төрөл')
    backing_info = fields.One2many('server.info','backing_id', string=' Мэдээлэл нөөцлөх') 
    sequence = fields.Integer(string = 'Sequence') 
    allocate_infos = fields.One2many('server.info','allocate_id')
        
    project_manager_id = fields.Many2one('hr.employee', string='Төслийн менежер' , domain=[('parent_department','=',254)],track_visibility='always')
    training_manager_id = fields.Many2one('hr.employee', string='Сургалт өгөх төслийн менежер' , domain=[('parent_department','=',254)],track_visibility='always')
    project_senior_manager_id = fields.Many2one('hr.employee' , string='Ахлах төслийн менежер', domain=_get_senior_manager_domain)
    # senior_manager_id = fields.Many2one('res.users', 'Ахлах төслийн менежер',  domain="[('groups_id','=',887)]")
    system_admin_id = fields.Many2one('hr.employee', string='Систем админ',domain=[('department_id','in',[89,1786])])
    system_quality_assurance = fields.Many2one('res.users', string='Системийн чанар баталгаажуулагч',domain="[('groups_id','=',1001)]")
    choose_batch = fields.Many2one('batch.name', string='Багцын нэр')
    
    project_state_name = fields.Many2one('project.state.name' , string='Ажлын явц' )

    time_cost_info = fields.Integer(string="Time cost info" , compute="planned_time_cost")



    cost_type = fields.Selection([('cost1','Нэг удаагийн төлбөр'),('cost2','Тарифт тусгах'),('cost3','Дэмжлэг')], string='Зардлын төрөл' , default="cost1")
    cost_types = fields.Selection([('cost_in','Дотоод зардал'),('payment','Нэг удаагийн төлбөр'),('rent_cost','Түрээсийн зардалд шингээх (МТС)'),('rent_cost_other','Түрээсийн зардалд шингээх (Бусад: __________________)')], string='Зардлын төрөл')

    accountant_id = fields.Many2one('hr.employee',string='Accountant name')
    accountant_description = fields.Char(string='Accountant description')
    
    job_selection = fields.Selection([
                                ('network',u'Сүлжээ'),
                                ('control_box',u'Узель'),
                                ('camera',u'Камер'),
                                ('temp_n_humidity',u'Температур чийгшил'),
                                ('eas_am_system',u'Дохиоллын антен'),
                                ('parking_equipment',u'Зогсоол'),
                                ('entrance_conrol',u'Орохын камер'),
                                ('other',u'Бусад'),
                                ], u'Хийгдэх ажил', track_visibility='onchange', default = 'network')   

    location = fields.Char (string='Байршил')

    is_confirm = fields.Boolean(string='Зардал батлах ажилтан нэмэх', default=False,track_visibility='onchange')

    approve_employee_id = fields.Many2one('hr.employee' , string='Батлах ажилтан')
    # system_line_ids              = fields.One2many('list.other.systems.line','order_id', string="List other systems line")
    line_ids              = fields.One2many('order.page.line','order_id', string="Work Service")
    description = fields.Char(string="Тайлбар")
    is_invisible = fields.Boolean(string="Is invisible" ,default=False)

    previous_state = fields.Selection([
                                ('draft',u'Ноорог'),
                                ('control',u'Хянах'),
                                ('confirmed',u'Батлах'),
                                ('approved1',u'Батлагдсан'),                            
                                ('allocated',u'Хуваарилагдсан'),
                                ('approve_cost',u'Зардал батлуулах'),
                                ('cost_done',u'Зардал батлагдсан'),
                                ('sent_director',u'Захирал хянах'),
                                ('handover',u'Хүлээлцэх'),
                                ('estimated',u'Хянуулах'),
                                ('approved',u'Хянасан'),
                                ('archived',u'Архивлагдсан'),
                                ('done',u'Дууссан'),                                
                                ('slow_up',u'Хойшлогдсон'),
                                ('rejected',u'Татгалзсан'),
                                ('stop',u'Зогссон'),
                                ], u'Төлөв')
    change_name = fields.Char(string = "Change name")
    change_description = fields.Char(string="Change description")
    change_result = fields.Char(string="Change result")
    change_system_name = fields.Char(string="Change system name")
    impact_organization = fields.Char(string="Impact on the organization")
    effect_of_not_allowing_change = fields.Char(string="The effect of not allowing change" )
    interruption_registration_period = fields.Char(string="Interruption registration period")
    location_modification_system = fields.Char(string="Location of the modification system" )
    system_lists = fields.Many2many('hr.system.list', string="List other systems line")
    rate = fields.Integer(string="Үнэлгээ" , compute='_rate_risk',track_visibility="onchange")
    risk_level = fields.Selection([
                                    ('low',u'Бага'), 
                                    ('middle',u'Дунд'),
                                    ('real',u'Бодит'),
                                    ('solid',u'Хатуу'),
                                    ('serious',u'Ноцтой'),
                                    ], u'Эрсдлийн түвшин' , default='low',compute='_rate_risk')
    approve_request_date  = fields.Selection([
                                    ('1hour',u'1 цаг'), 
                                    ('1-3hour',u'1-3 цаг'),
                                    ('3-6hour',u'3-6 цаг'),
                                    ('1day',u'1 өдөр'),
                                    ('2day',u'2 өдөр'),
                                    ('3day',u'3 өдөр'),
                                    ('4day',u'4 өдөр'),
                                    ('5day',u'5 өдөр'),
                                    ('6day',u'6 өдөр'),
                                    ('7day',u'7 өдөр'),
                                    ('8day',u'8 өдөр'),
                                    ('10day',u'10 өдөр'),
                                    ('12day',u'12 өдөр'),
                                    ('14day',u'14 өдөр'),
                                    ('16day',u'16 өдөр'),
                                    ('20day',u'20 өдөр'),
                                    ('22day',u'22 өдөр'),
                                    ('24day',u'24 өдөр'),
                                    ('26day',u'26 өдөр'),
                                    ], u'Хүсэлт үүсгэх батлуулах'  , default='1hour' , compute='_rate_risk')
    implementation_period = fields.Selection([
                                    ('1-2hour',u'1-2 цаг'), 
                                    ('4-6hour',u'4-6 цаг'),
                                    ('1day',u'1 өдөр'),
                                    ('2day',u'2 өдөр'),
                                    ('3day',u'3 өдөр'),
                                    ('5day',u'5 өдөр'),
                                    ('7day',u'7 өдөр'),
                                    ('8day',u'8 өдөр'),
                                    ('10day',u'10 өдөр'),
                                    ('11day',u'11 өдөр'),
                                    ('14day',u'14 өдөр'),
                                    ('17day',u'17 өдөр'),
                                    ('20day',u'20 өдөр'),
                                    ('24day',u'24 өдөр'),
                                    ('25day',u'25 өдөр'),
                                    ('27day',u'27 өдөр'),
                                    ('30day',u'30 өдөр'),
                                    ('33day',u'33 өдөр'),
                                    ('34day',u'34 өдөр'),
                                    ], u'Хэрэгжүүлэх хугацаа', default='1-2hour',compute='_rate_risk')


    determine_degree_importance = fields.Selection([
                                ('very_important',u'Нэн чухал'),
                                ('important',u'Чухал'),
                                ('simple',u'Энгийн'),
                                ('not_important',u'Чухал биш'),                            
                               
                                ], u'Чухлын зэрэг тодорхойлох', default = 'simple')
    technical_impact = fields.Selection([
                                ('high',u'Өндөр'),
                                ('middle',u'Дунд'),
                                ('low_impact',u'Нөлөөлөл бага'),                                                           
                               
                                ], u'Техникийн нөлөөлөл',  default = 'high')
    
    influence_customers_clients = fields.Selection([
                                ('5',u'Ноцтой эрсдэлтэй'),
                                ('4',u'Хатуу эрсдэлтэй'),
                                ('3',u'Бодит эрсдэлтэй'),
                                ('2',u'Дунд эрсдэлтэй'),                            
                                ('1' , u'Бага эрсдэлтэй')
                                ], u'Хэрэглэгч, харилцагчид нөлөөлөх',  default = '5')
    influence_information_technology_resources = fields.Selection([
                                ('5',u'Ноцтой эрсдэлтэй'),
                                ('4',u'Хатуу эрсдэлтэй'),
                                ('3',u'Бодит эрсдэлтэй'),
                                ('2',u'Дунд эрсдэлтэй'),                            
                                ('1' , u'Бага эрсдэлтэй')
                                ], u'Мэдээллийн технологийн нөөцөд нөлөөлөх',  default = '5')
    difficulty_implementing_change = fields.Selection([
                                ('5',u'Ноцтой эрсдэлтэй'),
                                ('4',u'Хатуу эрсдэлтэй'),
                                ('3',u'Бодит эрсдэлтэй'),
                                ('2',u'Дунд эрсдэлтэй'),                            
                                ('1' , u'Бага эрсдэлтэй')
                                ], u'Өөрчлөлтийг хэрэгжүүлэх төвөгшилт',  default = '5')
    safety = fields.Selection([
                                ('5',u'Ноцтой эрсдэлтэй'),
                                ('4',u'Хатуу эрсдэлтэй'),
                                ('3',u'Бодит эрсдэлтэй'),
                                ('2',u'Дунд эрсдэлтэй'),                            
                                ('1' , u'Бага эрсдэлтэй')
                                ], u'Аюулгүй байдал',  default = '5')
    impact_service_contracts = fields.Selection([
                                ('5',u'Ноцтой эрсдэлтэй'),
                                ('4',u'Хатуу эрсдэлтэй'),
                                ('3',u'Бодит эрсдэлтэй'),
                                ('2',u'Дунд эрсдэлтэй'),                            
                                ('1' , u'Бага эрсдэлтэй')
                                ], u'Үйлчилгээний гэрээнд үзүүлэх нөлөөлөх', default = '5')


    def handle_serv_info(self):

        hr_holidays_id = self.env['server.info'].search([('server_id','=',self.id)])


        if hr_holidays_id: 

            print'_________'

        else:
            hhhh = self.env['pr.spec.dt'].search([(1,'=',1)])
            for i in hhhh:
                hr_holidays_id1 = hr_holidays_id.create({
                    'server_id': self.id,
                    'indicator_name':i.id,
                    }) 
   
    @api.one
    def _rate_risk(self):
        for order in self:
            # if order.request_type.id == 51:
            if order.request_type.request_name == 'change_request':
                print '\n\n\n ffffffffffffff' , order.request_type
                total_risk = 0
                risk_1 = 0
                risk_2 = 0
                risk_3 = 0
                risk_4 = 0
                risk_5 = 0
                if order.influence_customers_clients == '5': 
                    risk_1 = 5
                if order.influence_customers_clients == '4': 
                    risk_1 = 4
                if order.influence_customers_clients == '3': 
                    risk_1 = 3
                if order.influence_customers_clients == '2': 
                    risk_1 = 2
                if order.influence_customers_clients == '1': 
                    risk_1 = 1
                
                if order.influence_information_technology_resources == '5': 
                    risk_2 = 5
                if order.influence_information_technology_resources == '4': 
                    risk_2 = 4
                if order.influence_information_technology_resources == '3': 
                    risk_2 = 3
                if order.influence_information_technology_resources == '2': 
                    risk_2 = 2
                if order.influence_information_technology_resources == '1': 
                    risk_2 = 1

                if order.difficulty_implementing_change == '5': 
                    risk_3 = 5
                if order.difficulty_implementing_change == '4': 
                    risk_3 = 4
                if order.difficulty_implementing_change == '3': 
                    risk_3 = 3
                if order.difficulty_implementing_change == '2': 
                    risk_3 = 2
                if order.difficulty_implementing_change == '1': 
                    risk_3 = 1

                if order.safety == '5': 
                    risk_4 = 5
                if order.safety == '4': 
                    risk_4 = 4
                if order.safety == '3': 
                    risk_4 = 3
                if order.safety == '2': 
                    risk_4 = 2
                if order.safety == '1': 
                    risk_4 = 1

                if order.impact_service_contracts == '5': 
                    risk_5 = 5
                if order.impact_service_contracts == '4': 
                    risk_5 = 4
                if order.impact_service_contracts == '3': 
                    risk_5 = 3
                if order.impact_service_contracts == '2': 
                    risk_5 = 2
                if order.impact_service_contracts == '1': 
                    risk_5 = 1

                
                total_risk += risk_1 + risk_2 + risk_3 + risk_4 + risk_5
                print '\n\n\n total risk' , total_risk
                order.rate = total_risk
                if total_risk in range(1,6):
                    order.risk_level = 'low'
                if total_risk in  range(6,11):
                    order.risk_level = 'middle'
                if total_risk in  range(11,16):
                    order.risk_level = 'real'
                if total_risk in  range(16,21):
                    order.risk_level = 'solid'
                if total_risk in  range(21,26):
                    order.risk_level = 'serious'
                
                if order.determine_degree_importance == 'very_important' and order.risk_level == 'serious':
                    order.approve_request_date = '1hour'
                    order.implementation_period = '1-2hour'
                if order.determine_degree_importance == 'very_important' and order.risk_level == 'solid':
                    order.approve_request_date = '1-3hour'
                    order.implementation_period = '4-6hour'
                if order.determine_degree_importance == 'very_important' and order.risk_level == 'real':
                    order.approve_request_date = '3-6hour'
                    order.implementation_period = '1day'
                if order.determine_degree_importance == 'very_important' and order.risk_level == 'middle':
                    order.approve_request_date = '1day'
                    order.implementation_period = '2day'
                if order.determine_degree_importance == 'very_important' and order.risk_level == 'low':
                    order.approve_request_date = '2day'
                    order.implementation_period = '3day'


                if order.determine_degree_importance == 'important' and order.risk_level == 'serious':
                    order.approve_request_date = '2day'
                    order.implementation_period = '3day'
                if order.determine_degree_importance == 'important' and order.risk_level == 'solid':
                    order.approve_request_date = '3day'
                    order.implementation_period = '5day'
                if order.determine_degree_importance == 'important' and order.risk_level == 'real':
                    order.approve_request_date = '4day'
                    order.implementation_period = '7day'
                if order.determine_degree_importance == 'important' and order.risk_level == 'middle':
                    order.approve_request_date = '5day'
                    order.implementation_period = '8day'
                if order.determine_degree_importance == 'important' and order.risk_level == 'low':
                    order.approve_request_date = '6day'
                    order.implementation_period = '10day'


                if order.determine_degree_importance == 'simple' and order.risk_level == 'serious':
                    order.approve_request_date = '7day'
                    order.implementation_period = '11day'
                if order.determine_degree_importance == 'simple' and order.risk_level == 'solid':
                    order.approve_request_date = '8day'
                    order.implementation_period = '14day'
                if order.determine_degree_importance == 'simple' and order.risk_level == 'real':
                    order.approve_request_date = '10day'
                    order.implementation_period = '17day'
                if order.determine_degree_importance == 'simple' and order.risk_level == 'middle':
                    order.approve_request_date = '12day'
                    order.implementation_period = '20day'
                if order.determine_degree_importance == 'simple' and order.risk_level == 'low':
                    order.approve_request_date = '14day'
                    order.implementation_period = '24day'

                if order.determine_degree_importance == 'non_important' and order.risk_level == 'serious':
                    order.approve_request_date = '16day'
                    order.implementation_period = '25day'
                if order.determine_degree_importance == 'non_important' and order.risk_level == 'solid':
                    order.approve_request_date = '20day'
                    order.implementation_period = '27day'
                if order.determine_degree_importance == 'non_important' and order.risk_level == 'real':
                    order.approve_request_date = '22day'
                    order.implementation_period = '3day'
                if order.determine_degree_importance == 'non_important' and order.risk_level == 'middle':
                    order.approve_request_date = '24day'
                    order.implementation_period = '33day'
                if order.determine_degree_importance == 'non_important' and order.risk_level == 'low':
                    order.approve_request_date = '26day'
                    order.implementation_period = '34day'     


    @api.multi
    def write(self, vals):
        if vals.get('project_manager_id'):
            employee_obj = self.env['hr.employee'].browse(vals.get('project_manager_id'))
            user_id =  employee_obj.user_id
            self.sudo()._add_followers(user_id.id)
        result = super(OrderPage, self).write(vals)
        if vals.get('state'):
            if self.state == 'draft':
                self.state_sequence = '01.Ноорог'
            elif self.state == 'control':
                self.state_sequence = '02.Хянах'
            elif self.state == 'confirmed':
                self.state_sequence = '03.Батлах'
            elif self.state == 'approved1':
                self.state_sequence = '04.Батлагдсан'
            elif self.state == 'allocated':
                self.state_sequence = '05.Хуваарилагдсан'
            elif self.state == 'approve_cost':
                self.state_sequence = '06.Зардал батлуулах'
            elif self.state == 'cost_done':
                self.state_sequence = '07.Зардал батлагдсан'
            elif self.state == 'sent_director':
                self.state_sequence = '08.Захирал хянах'
            elif self.state == 'handover':
                self.state_sequence = '09.Хүлээлцэх'
            elif self.state == 'estimated':
                self.state_sequence = '10.Хянуулах'
            elif self.state == 'approved':
                self.state_sequence = '11.Хянасан'
            elif self.state == 'archived':
                self.state_sequence = '12.Архивлагдсан'
            elif self.state == 'done':
                self.state_sequence = '13.Дууссан'
            elif self.state == 'slow_up':
                self.state_sequence = '14.Хойшлогдсон'
            elif self.state == 'rejected':
                self.state_sequence = '15.Татгалзсан'
            elif self.state == 'stop':
                self.state_sequence = '16.Зогссон'

        return result


    @api.model
    def create(self, vals):
        result = super(OrderPage, self).create(vals)
        name = self.env['ir.sequence'].get('order.page')
        result.update({'name': name})
        result.handle_serv_info()

        return result
    

    @api.multi
    def back_to_allocated(self):

        self.write({'is_invisible':True})
        
        return {
            'name': 'Note',            
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'back.to.allocated',          
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',            
        }

    @api.multi
    def get_engineer(self):
        ''' Хуваарилах менежерийг олох.
        '''

        sod_workflow = self.env['sod.workflow.name'].search([('code','=','get_installation_engineer')])
        if sod_workflow:
            result_values = sod_workflow.get_nominees(self.department_id,self.employee_id)
            if result_values['button_clickers'] and self.request_type.request_name == 'installation_order':                
                self.write({'engineer_ids':result_values['button_clickers']})
                



    @api.multi
    def action_to_send(self):
        ''' Хянах руу илгээх.
        '''

        request_line = self.env['request.config.ordering.flow']
        dep_obj = self.env['hr.department']


        line_ids = request_line.search([('request_id','=',self._request_id()),('state','=','approved1')])       
        confirm_user_ids = []
        for line in line_ids:
            for user in line.group_id.users:
               
                confirm_user_ids.append(user.id)


        if confirm_user_ids != []:
            self.write({'confirm_user_ids':[  (6,0,confirm_user_ids)]})
            self.message_subscribe_users(confirm_user_ids)             

        else:
            raise UserError(('Confirm users not found.'))

        if self.is_control == True:
            self.write({'state':'confirmed',
                        'request_id': self._request_id()
                        })
            
            

            template_id = self.env['ir.model.data'].get_object_reference('nomin_project', 'email_template_of_ordering')[1]
            title = unicode(' Захиалгын мэдэгдэл','utf-8')

            for exec1 in self.confirm_employee_id:

                data = {
                        'email_title': title,
                        'request': self.request_type.name,
                        'name': self.name,
                        'order_name': self.order_name,
                        'email_to': exec1.login,
                        'content': self.state, 
                        'model': 'order.page',                   
                        'department_id': self.department_id.name,
                        'states': 'Батлах',
                        'requested_date': str(self.start_date),        
                        'process_employee': self.employee_id.name,
                        'email_from': self.employee_id.name,
                        }

                self.env.context = data
                if template_id and exec1:
                    self.pool['mail.template'].send_mail(self.env.cr, 1, template_id, exec1.user_id.id, force_send=True, context=self.env.context)
        else:
            self.write({'state':'control',
                        'request_id': self._request_id()
            })


            template_id = self.env['ir.model.data'].get_object_reference('nomin_project', 'email_template_of_ordering')[1]
            title = unicode(' Захиалгын мэдэгдэл','utf-8')

            for exec1 in self.control_employee_id:


                data = {
                        'email_title': title,
                        'request': self.request_type.name,
                        'name': self.name,
                        'order_name': self.order_name,
                        'email_to': exec1.login,
                        'content': self.state, 
                        'model': 'order.page',                   
                        'department_id': self.department_id.name,
                        'states': 'Хянах',
                        'requested_date': str(self.start_date),        
                        'process_employee': self.employee_id.name,
                        'email_from': self.employee_id.name,
                        }

                self.env.context = data
                if template_id and exec1:
                    self.pool['mail.template'].send_mail(self.env.cr, 1, template_id, exec1.user_id.id, force_send=True, context=self.env.context)

        if self.control_employee_id: 
                self.sudo()._add_followers(self.control_employee_id.user_id.id)

        if self.confirm_employee_id:
                self.sudo()._add_followers(self.confirm_employee_id.user_id.id)


    # @api.onchange('project_manager_id')
    # def onchange_project_manager(self):
    #     print '\n\n\n\nddddddddddddddddddddddddddddddddddd ' 
    #     if self.project_manager_id:
    #         print '\n\n\n\n manager' , self.project_manager_id.user_id
    #         self.sudo()._add_followers(self.project_manager_id.user_id.id)

# class ListOtherSystems(models.Model):
#     _name = 'list.other.systems.line'
#     _description = "List Other Systems Affected Line"
    

#     order_id = fields.Many2one('order.page', string="Order page" ,ondelete='cascade')
#     system_name = fields.Char(string = "System name")



class OrderPageLine(models.Model):
    _name = 'order.page.line'
    _description = "Order Page line"
    _order = 'create_date desc'


    order_id = fields.Many2one('order.page', string="Order page" ,ondelete='cascade')
    category_id = fields.Many2one('knowledge.store.category', string="Ангилал" ,domain="[('id','in',category_ids[0][2])]" )
    service_id = fields.Many2one('work.service',string="Ажил үйлчилгээ" , domain = "[('category_id','=',category_id)]" , required="1")
    category_ids = fields.Many2many('knowledge.store.category','knowledge_store_category_order_page_line_rel','order_line_id','categor_id' ,string='category ids')
    employee_name = fields.Char(string='Employee name')
    product_category = fields.Char(string='Product category name')
    add_role = fields.Char(string='Нэмж тохируулах эрх')
    sub_role = fields.Char(string='Хасуулах эрх')
    reason = fields.Char(string='Шалтгаан')
    explanation = fields.Char(string='Тайлбар')
    department_ids = fields.Many2many('hr.department', string="Тохируулах салбарууд" , domain=[('is_sector','=',True)])
    latin_name = fields.Char(string="Latin name" , related='service_id.latin_name')
    is_new_vacancy = fields.Selection([('yes','Тийм'),('no','Үгүй')],default='no',string='Шинэ орон тоо эсэх')
    crud = fields.Selection([('create','Create'),('read','Read'),('update','Update'),('delete','Delete'),('all','All')],default='read',string='CRUD')
    is_install_program = fields.Selection([('useful','Useful'),('recruitment_program','Recruitment program'),('buy_program','Buy program')],default='useful',string='CRUD')

    @api.onchange('category_id')
    def onchange_category(self):   
        '''Гүйцэтгэгч хэлтэст хамаарах ангиллыг харуулах'''
        category_ids = []
        for line in self:
            service_ids = self.env['work.service'].search([('department_ids','in',[88,1666,89])])
            for service in service_ids:
                if service.category_id:
                    category_ids.append(service.category_id.id)

            if category_ids:
                line.category_ids =[(6, 0, category_ids)]
                return {'domain':{
                              'category_id':[('id','in',category_ids)]                          
                              },
                              } 

class WorkService(models.Model):
    '''Ажил үйлчилгээ
    '''
    _inherit = "work.service"
    
    latin_name = fields.Char(string='Latin name')


class ServerInfo(models.Model):
    _name = "server.info"
    _description = "df"
    _inherit = ['mail.thread']


    @api.one
    def line_cost(self):
        time = 0
        cost = 0
        total = 0
        sum_total = 0 
        for line in self:
            time = line.time_info
            cost = line.rate
            total = time * cost

        self.total = total 






    allocate_id = fields.Many2one('order.page', string='Allocate id')
    vpn_id = fields.Many2one('order.page', string='vpn in')
    backing_id = fields.Many2one('order.page', string='back up')
    vpn_out_id = fields.Many2one('order.page', string='vpn out')
    nat_access_id = fields.Many2one('order.page', string='nat access info')
    pat_access_id = fields.Many2one('order.page', string='pat access info')
    server_id =fields.Many2one('order.page', string='technical info')
    net_id =fields.Many2one('order.page', string='Интернэтийн мэдээлэл')
    server_net_id =fields.Many2one('order.page', string='Серверийн интернэтийн мэдээлэл')
    access_id =fields.Many2one('order.page', string='access info')
    plan_id = fields.Many2one('order.page', string='Plan info')
    cost_id = fields.Many2one('order.page', string='Cost info')
    task_id = fields.Many2one('order.page', string='Task info')

    saved = fields.Boolean(string="test" , default=False)

    indicator_name = fields.Many2one('pr.spec.dt', string='Шаардагдах үзүүлэлт нэр')
    performance = fields.Many2one('pr.spec',string = 'Үзүүлэлт' , domain="[('performance_name','=',indicator_name)]")


    reference = fields.Char(string='Хэрэгцээ/шаардлага тайлбар')
    price = fields.Float(string='Үнэ')
    ip_address = fields.Char(string="хэрэглэгчийн IP хаяг")
    source_port = fields.Char(string="Source Port")
    requirement = fields.Selection([('service','Албаны шаардлага'),('personal','Хувийн шаардлага')], default="service" , string="Зориулалт")
    duration = fields.Float('Хугацаа', readonly=True)
    name = fields.Many2one('net.spec', string='Суваг нэр', size=80 )
    
    backingup = fields.Many2one('backing.up', string='Нөөцлөх мэдээллийн төрөл', size=80)
    backing_way = fields.Char(string="Нөөцлөх мэдээллийн зам")
    backing_time = fields.Selection([('year','Жил'),('season','Улирал'),('month','Сар'),('week','7 хоног'),('day','Өдөрт')], string="Нөөцлөх хугацаа төрөл")
    backing_frequency = fields.Integer(string='Нөөцлөх давтамж')
    date_from = fields.Date('Эхлэх хугацаа', track_visibility='onchange' , default=fields.Date.today)
    date_to = fields.Date('Дуусах хугацаа', track_visibility='onchange', default=fields.Date.today)
    number_of_days_temp = fields.Float('Хугацаа/хоногоор/', readonly=True)
    unit_amount1 = fields.Float('Эхлэх цаг', default=0.0)
    unit_amount1a = fields.Float('Дуусах цаг', default=0.0)
    partner_id = fields.Many2one('res.partner', string='Байгууллагын нэр',  states={'draft': [('readonly', False)]},track_visibility='onchange')
    user_name = fields.Char(string="Хэрэглэгчийн нэр")
    user_position = fields.Char(string="Албан тушаал")
    user_phone = fields.Char(string="Утас")
    user_mail = fields.Char(string="Email")

    system = fields.Selection([('erp','ERP систем'),('nomin','Nomin систем')], string='Систем', default='erp')
    departments = fields.Many2many('hr.department', string='Салбар', track_visibility='onchange')

    year_id = fields.Many2one('account.fiscalyear',string="Year")
    month_id = fields.Many2one('account.period', string="Month",domain="[('fiscalyear_id','=',year_id)]")
    plan_name = fields.Char(string='Plan information',track_visibility='onchange')
    first_week = fields.Char(string='first week',track_visibility='onchange')
    second_week = fields.Char(string='second week')
    third_week = fields.Char(string='third week')
    fourth_week = fields.Char(string='fourth week')

    position_name = fields.Many2one('job.name', string='Job name',track_visibility='onchange',domain="[('is_select','=',True)]")
    rate = fields.Float(string='Rate' , related='position_name.rate',track_visibility='onchange')
    time_info = fields.Float(string="Time info",track_visibility='onchange')
    cost_reference = fields.Char(string='Cost reference',track_visibility='onchange')
    total = fields.Integer(string="Total" , compute="line_cost")

    is_check = fields.Boolean(string='Check')
    
    implemented_task = fields.Char(string='Implemented task',track_visibility='onchange')
    explanation = fields.Char(string='Explanation',track_visibility='onchange')
    comment = fields.Char(string='employee explanation',track_visibility='onchange')

    
    
    nat_name = fields.Many2one('nat.pat.access', string='Сувгийн нэр ', size=80 )
    
    nat_requirement = fields.Char(string="Зориулалт")
    nat_environment = fields.Char(string="Орчин")
    port =  fields.Char(string="Port")
    source = fields.Char(string="Source IP")
    destination_ip = fields.Char(string="Destination IP")
    destination_port = fields.Char(string="Destination Port")
    date = fields.Date(string="Дуусах хугацаа", size=60)
    server_ip = fields.Char(string="Server IP")

    def _get_number_of_days(self, date_from, date_to):
        """Returns a float equals to the timedelta between two dates given as string."""

        DATETIME_FORMAT = "%Y-%m-%d"
        from_dt = datetime.strptime(date_from, DATETIME_FORMAT)
        to_dt =datetime.strptime(date_to, DATETIME_FORMAT)
        timedelta = to_dt - from_dt
        diff_day = timedelta.days + float(timedelta.seconds) / 86400
        return diff_day

    def _get_number_of_hours(self, date_from, date_to):
        """Returns a float equals to the timedelta between two dates given as string."""
        if self.date_from and self.date_to:
            DATETIME_FORMAT = "%Y-%m-%d"
            from_dt = datetime.strptime(date_from, DATETIME_FORMAT)
            to_dt = datetime.strptime(date_to, DATETIME_FORMAT)
            timedelta = to_dt - from_dt
            return timedelta.days * 24 + float(timedelta.seconds) / 3600
        else:
            return 0

    def _get_number_of_minutes(self, date_from, date_to):
        """Returns a float equals to the timedelta between two dates given as string."""

        if self.date_from and self.date_to:
            DATETIME_FORMAT = "%Y-%m-%d"
            from_dt = datetime.strptime(date_from, DATETIME_FORMAT)
            to_dt = datetime.strptime(date_to, DATETIME_FORMAT)
            timedelta = to_dt - from_dt 
            return float(timedelta.seconds) / 60
        else:
            return 0
   
    @api.model
    def create(self, vals):     

        req = self.env['order.page'].search([('id','=',vals.get('server_id'))])
        if req.request_type.id == 5:
            vals.update({'saved':True})
        result = super(ServerInfo, self).create(vals)

        diff_day = result._get_number_of_days(result.date_from, result.date_to)
        number_of_hours = result._get_number_of_hours(result.date_from, result.date_to)
        number_of_minutes = result._get_number_of_minutes(result.date_from, result.date_to)

        number_of_days_temp = round(math.floor(diff_day))
        number_of_hours = number_of_hours-math.floor(number_of_hours/24)*24
        number_of_minutes = number_of_minutes-math.floor(number_of_minutes/60)*60

        result.update({
                
                'number_of_days_temp':number_of_days_temp,
                })

        return result

    @api.multi 
    def write(self, vals):

        d = datetime.now().date() - timedelta(days=40)
        d1 = datetime.strftime(d, "%Y-%m-%d")

        if vals.get('date_from') and vals.get('date_to'):
            date_from = vals.get('date_from')
            date_to = vals.get('date_to')
        elif vals.get('date_from'):
            date_from = vals.get('date_from')
            date_to = self.date_to
        elif vals.get('date_to'):
            date_from = self.date_from
            date_to = vals.get('date_to')   
        else: 
            date_from = self.date_from
            date_to = self.date_to   

        diff_day = self._get_number_of_days(date_from, date_to)
        number_of_hours = self._get_number_of_hours(date_from, date_to)
        number_of_minutes = self._get_number_of_minutes(date_from, date_to)

        number_of_days_temp = round(math.floor(diff_day))
        number_of_hours = number_of_hours-math.floor(number_of_hours/24)*24
        number_of_minutes = number_of_minutes-math.floor(number_of_minutes/60)*60
 
        vals.update({
        
            'number_of_minutes':number_of_minutes,
            'number_of_hours':number_of_hours,
            'number_of_days_temp':number_of_days_temp
            })

        return super(ServerInfo, self).write(vals)


    @api.onchange('date_from')
    def onchange_date_from(self):

        DATETIME_FORMAT = "%Y-%m-%d"
        from_dt = datetime.strptime(self.date_from, DATETIME_FORMAT)
     

        if (self.date_to and self.date_from) and (self.date_from <= self.date_to):

            diff_day = self._get_number_of_days(self.date_from, self.date_to)
            number_of_hours = self._get_number_of_hours(self.date_from, self.date_to)
            number_of_minutes = self._get_number_of_minutes(self.date_from, self.date_to)

            self.number_of_days_temp = round(math.floor(diff_day))
            self.number_of_hours = number_of_hours-math.floor(number_of_hours/24)*24
            self.number_of_minutes = number_of_minutes-math.floor(number_of_minutes/60)*60

        else:
            self.number_of_days_temp = 0


    @api.onchange('date_to')
    def onchange_date_to(self):
        """
        Update the number_of_days.
        """
        if (self.date_from and self.date_to) and (self.date_from > self.date_to):
            raise UserError(('Дуусах огноо эхлэх огнооны өмнө байж болохгүй.'))
        if (self.date_from and self.date_to) and (self.date_from == self.date_to):
            raise UserError(('Дуусах огноо эхлэх огноотой ижил байж болохгүй '))

        if (self.date_to and self.date_from) and (self.date_from <= self.date_to):
            
            diff_day = self._get_number_of_days(self.date_from, self.date_to)
            number_of_hours = self._get_number_of_hours(self.date_from, self.date_to)
            number_of_minutes = self._get_number_of_minutes(self.date_from, self.date_to)

            self.number_of_days_temp = round(math.floor(diff_day))
            self.number_of_hours = number_of_hours-math.floor(number_of_hours/24)*24
            self.number_of_minutes = number_of_minutes-math.floor(number_of_minutes/60)*60

        else:
            self.number_of_days_temp = 0

