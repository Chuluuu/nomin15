# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import json
import time
import datetime
from datetime import datetime,date
from dateutil import relativedelta
from openerp import models, fields, api
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _
from openerp.exceptions import ValidationError
# from openerp.exceptions import UserError, AccessError
# from openerp.tools import html2plaintext
# from openerp.osv import fields, osv, orm
# import calendar


# class project_issue_reason(osv.Model):
#     '''
#         Асуудлын шалтгаан бүртгэх
#     '''
#     _name = 'project.issue.reason'
    
#     _columns = {
#                 'name'          : fields.char('Reason name',required = True),
#                 'description'   : fields.text('Description'),
#                 'issue_ids'     : fields.one2many('project.issue', 'reason_id', string ='Issues'),
#                 }
    
#     def unlink(self, cr, uid, ids, context=None):
#         issue_ids = self.pool.get('project.issue').search(cr, uid, [('reason_id', '=', ids[0])])
#         if len(issue_ids)==0:
#             res = super(project_issue_reason, self).unlink(cr, uid, ids, context=context)
#             return res
#         else: 
#             raise ValidationError(_(u'Энэхүү мэдээллийг бүртгэлд ашигласан тул устгах боломжгүй!'))

# class project_issue_inherit(osv.Model):
#     '''
#         Асуудал
#     '''
#     _inherit = 'project.issue'
    
#     def _add_followers(self,user_ids):
#         '''Add followers
#         '''
#         self.message_subscribe_users(user_ids=user_ids)
    
#     _columns = {
#                 'name'          : fields.char('Issue', required=True,track_visibility='onchange'),
#                 'checker'       : fields.many2one('res.users', index=True,string = u'Хянагч',track_visibility='onchange',required=True),
#                 'date_deadline' : fields.date('Deadline',track_visibility='onchange',required=True),
#                 'date'          : fields.datetime('Date',track_visibility='onchange',required=True),
#                 'tag_ids'       : fields.many2many('project.tags', index=True, string='Tags',track_visibility='onchange'),
#                 'priority'      : fields.selection([('0','Low'), ('1','Normal'), ('2','High')], 'Priority', select=True,track_visibility='onchange'),
#                 'partner_id'    : fields.many2one('res.partner', 'Contact', select=1,track_visibility='onchange'),
#                 'task_id'       : fields.many2one('project.task', 'Task', domain="[('project_id','=',project_id)]", index=True,
#                                                               help="You can link this issue to an existing task or directly create a new one from here", track_visibility='onchange'),
#                 'departmet_id'  : fields.many2one('hr.department',string='Department',required=True,track_visibility='onchange'),
#                 'contract_id'   : fields.many2one('contract.management',string='Contract', domain=['&',('state', 'in',('certified','warranty')),('is_conflicted','=',True)],track_visibility='onchange'),
#                 'reason_id'     : fields.many2one('task.deadline.reason', index=True,string='Reason',track_visibility='onchange'),
#                 'created_task'  : fields.boolean(string = 'Created task',type='boolean'),
#                 'created_ticket': fields.boolean(string = 'Created ticket',type='boolean' ),
#                 'description'   : fields.text('Private Note',track_visibility='onchange'),
#                 'issue_created_user_id': fields.many2one('res.users',string='Created User',readonly=True),
#                 'created_task_id':  fields.many2one('project.task',string=u'Холбоотой даалгавар',readonly=True),
#                 'created_ticket_id':fields.many2one('crm.helpdesk',string=u'Холбоотой тикет',readonly=True),
#                 'issue_created_date_time': fields.date('Created Date',readonly=True)
#                 }
#     _defaults = {
#                  'issue_created_user_id'  :lambda obj,cr,uid,c={}:uid,
#                  'issue_created_date_time':lambda *a: time.strftime('%Y-%m-%d'),
#                  'created_task'     :False,
#                  'created_ticket'   :False,
#                  'date'             :time.strftime('%Y-%m-%d %H:%M:%S')
#                  }
#     @api.model
#     def create(self, vals):
#         '''
#             Асуудлын шалтгаан үүсгэх төсөлрүү дагагч нэмэх
#         '''
#         result = super(project_issue_inherit, self).create(vals)
#         result.sudo()._add_followers(result.user_id.id)
#         result.sudo()._add_followers(result.checker.id)
#         result.sudo()._add_followers(result.project_id.user_id.id)
#         return result
    
#     @api.multi
#     def write(self, vals):
#         '''
#             төсөлрүү дагагч нэмэх
#         '''
#         if vals and 'user_id' in vals:
#             self.sudo()._add_followers(vals['user_id'])
#         if vals and 'checker' in vals:
#             self.sudo()._add_followers(vals['checker'])
#         if vals and 'project_id' in vals:
#             project = self.env['project.project'].search([('id', '=',vals['project_id'])])
#             self.sudo()._add_followers(project.user_id.id)
#         result = super(project_issue_inherit, self).write(vals)
#         return result
    
#     def create_task(self, cr, uid, ids, context=None):
#         '''
#             Асуудлаас даалгавар үүсгэх
#         '''
#         model_obj =self.pool.get('ir.model.data')
#         result = model_obj._get_id(cr, SUPERUSER_ID,'project', 'view_task_form2')
#         view_id = model_obj.browse(cr, uid, result).res_id
#         for issue in self.browse(cr, uid, ids):
#             employee = self.pool.get('hr.employee').search(cr, 1,[('user_id','=',issue.checker.id)])
#             project_task = self.pool.get('project.task')
#             if not employee:
#                 raise ValidationError(_(u'Асуудлын хянагчтай холбоотой ажилтан алга!!!'))
#             vals = {
#                     'name'          : issue.name,
#                     'parent_task'   : None,
#                     'project_id'    : issue.project_id.id,
#                     'department_id' : issue.departmet_id.id,
#                     # 'task_verifier' : employee[0],
#                     'task_verifier_users' : employee[0],
#                     'user_id'       : issue.user_id.id,
#                     'task_date_start'    : time.strftime('%Y-%m-%d %H:%M:%S'),
#                     'date_deadline' : time.strftime('%Y-%m-%d %H:%M:%S'),
#                     'task_type'     : 'normal',
#                     'task_state'    : 't_new'
#                     }
#             project_task = project_task.create(cr, uid, vals)
            
#             issue.update({
#                           'created_task':True,
#                           'created_task_id':project_task
#                           })
#             return {
#                      'type': 'ir.actions.act_window',
#                      'name': _('Register Call'),
#                      'res_model': 'project.task',
#                      'view_type' : 'tree',
#                      'view_mode' : 'form',
#                      'search_view_id' : view_id,
#                      'res_id':create_id,
#                      'target' : 'current',
#                      'nodestroy' : True,
#                  }
            
#     def create_ticket(self, cr, uid, ids, context=None):
#         '''
#             Асуудлаас тикет үүсгэх цонх дуудах
#         '''
#         mod_obj =  self.pool.get('ir.model.data')

#         res = mod_obj.get_object_reference(cr, SUPERUSER_ID,'nomin_project', 'action_create_project_ticket')
#         return {
#             'name': 'Тикет үүсгэх цонх',
#             'view_type': 'form',
#             'view_mode': 'form',
#             'res_model': 'create.project.ticket',
#             'context': context,
#             'type': 'ir.actions.act_window',
#             'nodestroy': True,
#             'target': 'new',
#         }
class project_issue_inherit(models.Model):
    '''
        Асуудал
    '''
    _inherit = 'project.issue'
    
    def _add_followers(self,user_ids):
        '''Add followers
        '''
        self.message_subscribe_users(user_ids=user_ids)
    

    name        = fields.Char('Issue', required=True,track_visibility='onchange')
    checker       = fields.Many2one('res.users', index=True,string = u'Хянагч',track_visibility='onchange',required=True)
    date_deadline =fields.Date('Deadline',track_visibility='onchange',required=True)
    date        = fields.Datetime('Date',track_visibility='onchange',required=True)
    tag_ids       = fields.Many2many('project.tags', index=True, string='Tags',track_visibility='onchange')
    priority      = fields.Selection([('0','Low'), ('1','Normal'), ('2','High')], 'Priority', select=True,track_visibility='onchange')
    partner_id   = fields.Many2one('res.partner', 'Contact', select=1,track_visibility='onchange')
    task_id      = fields.Many2one('project.task', 'Task', domain="[('project_id','=',project_id)]", index=True,
                                                  help="You can link this issue to an existing task or directly create a new one from here", track_visibility='onchange')
    departmet_id  = fields.Many2one('hr.department',string='Department',required=True,track_visibility='onchange')
    contract_id  = fields.Many2one('contract.management',string='Contract', domain=['&',('state', 'in',('certified','warranty')),('is_conflicted','=',True)],track_visibility='onchange')
    reason_id     = fields.Many2one('task.deadline.reason', index=True,string='Reason',track_visibility='onchange')
    created_task  =fields.Boolean(string = 'Created task',type='boolean')
    created_ticket= fields.Boolean(string = 'Created ticket',type='boolean' )
    description   = fields.Text('Private Note',track_visibility='onchange')
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
    
    @api.multi
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

    @api.multi
    def create_task(self, vals):
        '''
            Асуудлаас даалгавар үүсгэх
        '''
        model_obj =self.env['ir.model.data']
        result = model_obj._get_id('project', 'view_task_form2')
        view_id = model_obj.browse(result).res_id
        # res = model_obj.sudo().get_object_reference('project', 'view_task_form2')
        print'_______view_id______',view_id
        print'_______result______',result
        for issue in self:
            print'_______SSS____',issue
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
    @api.multi
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
    