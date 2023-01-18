# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import time
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
    
    
    task_id=fields.Many2one('project.task', index=True, string ='Task' )
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
      

    task_id=fields.Many2one('project.task', index=True, string= 'Task' )
    company_id=fields.Many2one('res.company','Company')
    department_id=fields.Many2one('hr.department','Department')
    job_id=fields.Many2one('hr.job','Job')
    user_id=fields.Many2one('res.users', 'Confirm Employee')     