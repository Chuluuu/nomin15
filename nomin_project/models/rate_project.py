# -*- coding: utf-8 -*-
import datetime
import time
from datetime import date, datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from fnmatch import translate
from odoo.http import request
import odoo.tools

class rate_project_perform(models.Model):
    # Changed TransientModel to Model
    _name ='rate.project.perform'
    
    '''
       Төсөл үнэлэх
    '''
    project_id   = fields.Many2one('project.project', index=True, string = 'Task')
    perform_line  = fields.One2many('project.rate','perform_rate_id','Line')
    
    @api.model
    def default_get(self, fields):
        res = super(rate_project_perform, self).default_get(fields) 
        context = dict(self._context or {})   
        active_id = context and context.get('active_id', False) or False
        perform_obj = self.env['project.project']
        performs = perform_obj.browse(active_id)
        perform_line = []
        for project in performs:
            for perform in project.perform:
                perform_line.append((0,0,{
                                         'perform'       : perform.id,
                                         'percent'       : 0.0
                                        }))
#                 perform_line = perform_line.create(vals)
                
        res.update({
                    'project_id' : performs.id,
                    'perform_line':perform_line
                    })
        return res
    
        
    def rate_button(self):
        '''
           Төсөл үнэлэх Товч, үнэлсэн талаар түүх хөтөлнө 1-100 хооронд үнэлнэ
        '''
        project_rate_user = self.env['project.rate.user'].search([('rate_id', '=', self.id)])
        project_project = self.env['project.project'].search([('id', '=', self.project_id.id)])
        main_specification_confirmers = self.env['main.specification.confirmers'].search([('project_id', '=', self.project_id.id)])
        employee = self.env['hr.employee']
        employee_id = employee.sudo().search([('user_id','=',self._uid)])
        
        for line in self.perform_line:
            if line.percent > 0 and line.percent < 101:
                for project_perform_line in self.project_id.perform_line:
                    if project_perform_line.perform == line.perform:
                        values = {
                                  'rate_id':project_perform_line.id,
                                  'employee':employee_id.id ,
                                  'percents': line.percent,
                                  }
                        project_rate_user = project_rate_user.create(values)
            else:
                raise ValidationError(_(u'Та 1-ээс 100 хооронд үнэлгээ өгнө үү'))
        vals = {
                'project_id': self.project_id.id,
                'confirmer' : employee_id.id ,
                'date'      : time.strftime('%Y-%m-%d %H:%M:%S'),
                'role'      : 'evaluator',
                'state'     : 'evaluate',
                }
        main_specification_confirmers = main_specification_confirmers.create(vals)
        if self.project_id.is_evaluate_done == True:
           project_project.sudo().write({
                                  'state': 'evaluate'
                                  })
                            