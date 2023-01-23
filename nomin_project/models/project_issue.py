# -*- coding: utf-8 -*-

import json
import time
import datetime
from datetime import datetime,date
from dateutil import relativedelta
from odoo import models, fields, api
from odoo import SUPERUSER_ID
from odoo import tools
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.translate import _
from odoo.exceptions import ValidationError
class project_issue_inherit(models.Model):
    '''
        Асуудал
    '''
    _inherit = 'project.issue'
    
    def _add_followers(self,user_ids):
        '''Add followers
        '''
        self.message_subscribe_users(user_ids=user_ids)
    

    name        = fields.Char('Issue', required=True,tracking=True)
    checker       = fields.Many2one('res.users', index=True,string = u'Хянагч',tracking=True,required=True)
    date_deadline =fields.Date('Deadline',tracking=True,required=True)
    date        = fields.Datetime('Date',tracking=True,required=True)
    tag_ids       = fields.Many2many('project.tags', index=True, string='Tags',tracking=True)
    priority      = fields.Selection([('0','Low'), ('1','Normal'), ('2','High')], 'Priority', select=True,tracking=True)
    partner_id   = fields.Many2one('res.partner', 'Contact', select=1,tracking=True)
    task_id      = fields.Many2one('project.task', 'Task', domain="[('project_id','=',project_id)]", index=True,
                                                  help="You can link this issue to an existing task or directly create a new one from here", tracking=True)
    departmet_id  = fields.Many2one('hr.department',string='Department',required=True,tracking=True)
    contract_id  = fields.Many2one('contract.management',string='Contract', domain=['&',('state', 'in',('certified','warranty')),('is_conflicted','=',True)],tracking=True)
    reason_id     = fields.Many2one('task.deadline.reason', index=True,string='Reason',tracking=True)
    created_task  =fields.Boolean(string = 'Created task',type='boolean')
    created_ticket= fields.Boolean(string = 'Created ticket',type='boolean' )
    description   = fields.Text('Private Note',tracking=True)
    issue_created_user_id= fields.Many2one('res.users',string='Created User',readonly=True)
    created_task_id=  fields.Many2one('project.task',string=u'Холбоотой даалгавар',readonly=True)
    created_ticket_id=fields.Many2one('crm.helpdesk',string=u'Холбоотой тикет',readonly=True)
    issue_created_date_time= fields.Date('Created Date',readonly=True)
 
    _defaults = {
                 'issue_created_user_id'  :lambda obj,cr,uid,c={}:uid,
                 'issue_created_date_time':lambda *a: time.strftime('%Y-%m-%d'),
                 'created_task'     :False,
                 'created_ticket'   :False,
                 'date'             :time.strftime('%Y-%m-%d %H:%M:%S')
                 }
    @api.model
    def create(self, vals):
        '''
            Асуудлын шалтгаан үүсгэх төсөлрүү дагагч нэмэх
        '''
        result = super(project_issue_inherit, self).create(vals)
        result.sudo()._add_followers(result.user_id.id)
        result.sudo()._add_followers(result.checker.id)
        result.sudo()._add_followers(result.project_id.user_id.id)
        return result
    
    
    def write(self, vals):
        '''
            төсөлрүү дагагч нэмэх
        '''
        if vals and 'user_id' in vals:
            self.sudo()._add_followers(vals['user_id'])
        if vals and 'checker' in vals:
            self.sudo()._add_followers(vals['checker'])
        if vals and 'project_id' in vals:
            project = self.env['project.project'].search([('id', '=',vals['project_id'])])
            self.sudo()._add_followers(project.user_id.id)
        result = super(project_issue_inherit, self).write(vals)
        return result

    
    def create_task(self, vals):
        '''
            Асуудлаас даалгавар үүсгэх
        '''
        model_obj =self.env['ir.model.data']
        result = model_obj._get_id('project', 'view_task_form2')
        view_id = model_obj.browse(result).res_id
        # res = model_obj.sudo().get_object_reference('project', 'view_task_form2')
        for issue in self:
            employee = self.env['hr.employee'].search([('user_id','=',issue.checker.id)])
            project_task = self.env['project.task']
            if not employee:
                raise ValidationError(_(u'Асуудлын хянагчтай холбоотой ажилтан алга!!!'))
            vals = {
                    'name'          : issue.name,
                    'parent_task'   : None,
                    'project_id'    : issue.project_id.id,
                    'department_id' : issue.departmet_id.id,
                    # 'task_verifier' : employee[0],
                    'task_verifier_users' : employee[0],
                    'user_id'       : issue.user_id.id,
                    'task_date_start'    : time.strftime('%Y-%m-%d %H:%M:%S'),
                    'date_deadline' : time.strftime('%Y-%m-%d %H:%M:%S'),
                    'task_type'     : 'normal',
                    'task_state'    : 't_new'
                    }
            project_task = project_task.create(vals)
            issue.update({
                          'created_task':True,
                          'created_task_id':project_task
                          })
            # return {
            #          'type': 'ir.actions.act_window',
            #          'name': _('Register Call'),
            #          'res_model': 'project.task',
            #          'view_type' : 'tree',
            #          'view_mode' : 'form',
            #          'search_view_id' : view_id,
            #          'res_id':project_task,
            #          'target' : 'current',
            #          'nodestroy' : True,
            #      }
    
    def create_ticket(self):
        '''
            Асуудлаас тикет үүсгэх цонх дуудах
        '''
        mod_obj =  self.env['ir.model.data']

        res = mod_obj.sudo().get_object_reference('nomin_project', 'action_create_project_ticket')
        return {
            'name': 'Тикет үүсгэх цонх',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'create.project.ticket',
            'context': self.env.context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }
    