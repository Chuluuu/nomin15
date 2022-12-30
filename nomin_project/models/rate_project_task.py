# -*- coding: utf-8 -*-
import datetime
import time
from datetime import date, datetime, timedelta
# from dateutil.relativedelta import relativedelta
# import time
# from openerp.osv import osv, fields 
from openerp import api, fields, models, _
from openerp.exceptions import UserError, ValidationError
from fnmatch import translate
from openerp.http import request
import openerp.tools
# from openerp import tools
# from gnomekeyring import is_available
# import xlwt
# from xlwt import *

class RateProjecTask(models.TransientModel):
    '''
       Даалгавар үнэлэх
    '''
    _name ='rate.project.task'
    
    rate = fields.Float(string='rate',required=True)
    task_id   = fields.Many2one('project.task', string = 'Task')
    
    
    # def default_get(self, cr, uid, fields, context=None):
    #     result = []
    #     if context is None:
    #         context = {}
    #     res = super(rate_project_task, self).default_get(cr, uid, fields, context=context)    
    #     active_id = context and context.get('active_id', False) or False
    #     perform_obj = self.pool.get('project.task')
    #     perform = perform_obj.browse(cr, uid, active_id)
        
    #     res.update({
    #                 'task_id' : perform.id,
    #                 })
    #     return res

    @api.model
    def default_get(self, fields):
        res = super(RateProjecTask, self).default_get(fields) 
        context = dict(self._context or {})   
        
        if 'task_id' in context:
            active_id = context.get("task_id")
            perform_obj = self.env['project.task']
            perform = perform_obj.browse(active_id)            
            res.update({
                        'task_id' : perform.id,
                        })
        return res
        
    @api.multi    
    def rate_button(self):
        '''
           1-100 хооронд даалгавар үнэлэх
        '''
        active_id = self._context.get('active_id', False)
        task_rating_user = self.env['task.rating.users']
        employee = self.env['hr.employee']
        employee_id = employee.sudo().search([('user_id','=',self._uid)])        
        task  = self.env['project.task'].browse(active_id)            
        # print "\n\nRating",active_id,task_rating_user,employee,employee_id,task,"\n\n"
        if self.rate > 100 or self.rate == 0.0:
            raise ValidationError(_(u'1-ээс 100-н хооронд үнэлгээ өгнө үү'))
        vals = {
                'task_id' : self.task_id.id,
                'confirmer':   employee_id.id,
                'percent':self.rate,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'role': 'rating_user',
                'state': 'rating'
                }
        task_rating_user = task_rating_user.create(vals)
        # print "\n\nOk it's ok\n\n"
        if task.is_rating == True:
                task.write({'task_state':'t_done',
                            'done_date': time.strftime('%Y-%m-%d'),})
                
                