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
import time
import datetime
from datetime import date, datetime, timedelta
from openerp import api, fields, models, _
from openerp.http import request
import openerp.tools
# from openerp.exceptions import UserError, ValidationError
# from openerp import tools
# import logging 
# import dateutil 
# from fnmatch import translate
# from gnomekeyring import is_available
# import xlwt
# from xlwt import *
# from dateutil.relativedelta import relativedelta
# import time

class circle_task_dates(models.Model):
    '''
        Даалгавар давтаж үүсгэх огноо
    '''
    _name = 'circle.task.dates'
    
    date = fields.Date(u'Огноо',required=True)
    parent_id = fields.Many2one('project.circle.task', index=True,string='Parent')
    
class project_cicle_task(models.Model):
    '''
        Даалгавар давтаж үүсгэх
    '''
    _name = 'project.circle.task'
    
    date_count = fields.Integer(u'Даалгаврийн гүйцэтгэх хоxног')
    date_lines = fields.One2many('circle.task.dates','parent_id',string = u'Огноо')
    task_id = fields.Many2one('project.task', index=True,string='Task')
    
    # def default_get(self, cr, uid, fields, context=None):
    #     result = []
    #     if context is None:
    #         context = {}
    #     res = super(project_cicle_task, self).default_get(cr, uid, fields, context=context)    
    #     active_id = context and context.get('active_id', False) or False
    #     perform_obj = self.pool.get('project.task')
    #     perform = perform_obj.browse(cr, uid, active_id)
    #     res.update({
    #                 'task_id' : perform.id,
    #                 })
    #     return res
    
    @api.model
    def default_get(self, fields):
        res = super(project_cicle_task, self).default_get(fields) 
        context = dict(self._context or {})   
        active_id = context and context.get('active_id', False) or False
        perform_obj = self.env['project.task']
        perform = perform_obj.browse(active_id)
 
        res.update({
                    'task_id' : perform.id,
                    })
        return res
        
    @api.multi
    def action_create(self):
        '''
            Даалгавар давтаж үүсгэх товч
            Даалгаврыг сонгосон хугацаануудаар давтаж үүсгэх
        '''
        task = self.env['project.task']
        date_count = self.date_count
        for line in self.date_lines:
            start_date = datetime.datetime.strptime(line.date, '%Y-%m-%d')
            end_date = (start_date +  datetime.timedelta(date_count)).strftime('%Y-%m-%d')
            s_date = (start_date).strftime('%Y-%m-%d')
            vals = {
                    'name':self.task_id.name + " '%s - %s' "% (str(s_date),str(end_date)),
                    'project_id':self.task_id.project_id.id,
                    'project_stage':self.task_id.project_stage.id,
                    'task_verifier_users':self.task_id.task_verifier_users.id,
                    'department_id':self.task_id.department_id.id,
                    'user_id':self.task_id.user_id.id,
                    'task_date_start':s_date,
                    'date_deadline':end_date,
                    'planned_hours':self.task_id.planned_hours,
                    'task_type':self.task_id.task_type,
                    'tag_ids':self.task_id.tag_ids.ids,
                    'description':self.task_id.description
                    }
            task = task.create(vals)
