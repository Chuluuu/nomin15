# -*- coding: utf-8 -*-
##############################################################################
#
#    ShineERP, Enterprise Management Solution    
#    Copyright (C) 2014-2020 ShineERP Co.,ltd (<http://www.serp.mn>). All Rights Reserved
#
#    Address : Suhkbaatar District, National ITPark, 205, ShineERP LLC
#    Email : info@serp.mn
#    Phone : 976 + 99229932
#
##############################################################################
from openerp import api, fields, models, _
import time
# from openerp.osv import fields, osv
# from openerp import api, _
# import time

# class Task(osv.osv):
#     _name = 'project.task'
#     _inherit = ['project.task']
    
#     _columns = {
#         'rating':                       fields.boolean('Rated'), # Үнэлгээ
#         'rating_transitions':            fields.one2many('rating.workflow.transition','task_id','Rating'),
#         'validate':                      fields.boolean('Validate'), # Батлах
#         'confirm_transitions':           fields.one2many('confirm.workflow.transitions','task_id','Confirm'),}
        
# class rating_task_transition(osv.osv):
#     '''
#         Даалгавар үнэлэх ажлын урсгал
#     '''
#     _name = 'rating.workflow.transition'
#     _description = 'Rating Workflow transition'
    
#     _columns = {
#         'task_id':      fields.many2one('project.task', index=True, 'Task' ),
#         'company_id':   fields.many2one('res.company','Company'),
#         'department_id':fields.many2one('hr.department','Department'),
#         'job_id':       fields.many2one('hr.job','Job'),
#         'user_id':      fields.many2one('res.users', 'Rating Employee'),
#         'rating':       fields.integer('Rating Grade'),
#     }
# class confirm_workflow_transition(osv.osv):
#     '''
#         Даалгавар батлах ажлын урсгал
#     '''
#     _name = 'confirm.workflow.transitions'
#     _description = 'Confirm Workflow transition'
      
#     _columns = {
#         'task_id':      fields.many2one('project.task', index=True, 'Task' ),
#         'company_id':   fields.many2one('res.company','Company'),
#         'department_id':fields.many2one('hr.department','Department'),
#         'job_id':       fields.many2one('hr.job','Job'),
#         'user_id':      fields.many2one('res.users', 'Confirm Employee'),
#     }       


class Task(models.Model):
    _name = 'project.task'
    _inherit = ['project.task']
    

    rating=fields.Boolean('Rated') # Үнэлгээ
    rating_transitions=fields.One2many('rating.workflow.transition','task_id','Rating')
    validate=fields.Boolean('Validate') # Батлах
    confirm_transitions=fields.One2many('confirm.workflow.transitions','task_id','Confirm')
        
class rating_task_transition(models.Model):
    '''
        Даалгавар үнэлэх ажлын урсгал
    '''
    _name = 'rating.workflow.transition'
    _description = 'Rating Workflow transition'
    
    
    task_id=fields.Many2one('project.task', index=True, 'Task' )
    company_id=fields.Many2one('res.company','Company')
    department_id=fields.Many2one('hr.department','Department')
    job_id=fields.Many2one('hr.job','Job')
    user_id=fields.Many2one('res.users', 'Rating Employee')
    rating=fields.Integer('Rating Grade')

class confirm_workflow_transition(models.Model):
    '''
        Даалгавар батлах ажлын урсгал
    '''
    _name = 'confirm.workflow.transitions'
    _description = 'Confirm Workflow transition'
      

    task_id=fields.Many2one('project.task', index=True, 'Task' )
    company_id=fields.Many2one('res.company','Company')
    department_id=fields.Many2one('hr.department','Department')
    job_id=fields.Many2one('hr.job','Job')
    user_id=fields.Many2one('res.users', 'Confirm Employee')     