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
from openerp import api, fields, models, _
import time
import datetime
# from datetime import date, datetime, timedelta
# from openerp.exceptions import UserError, ValidationError
# import time
class create_project_ticket(models.Model):
    _name ='create.project.ticket'
    
    '''
        Асуудлаас тикет үүсгэх
    '''
    
    type_id     = fields.Many2one('knowledge.root.category',string = 'Type')
    channel_id  = fields.Many2one('crm.channel',string = 'Channel')
    issue_id    = fields.Many2one('project.issue', index=True,string='Issue')
    category_id = fields.Many2one('knowledge.store.category',string='Category')
    
    # def default_get(self, cr, uid, fields, context=None):
    #     result = []
    #     if context is None:
    #         context = {}
    #     res = super(create_project_ticket, self).default_get(cr, uid, fields, context=context)    
    #     active_id = context and context.get('active_id', False) or False
    #     perform_obj = self.pool.get('project.issue')
    #     perform = perform_obj.browse(cr, uid, active_id)
 
    #     res.update({
    #                 'issue_id' : perform.id,
    #                 })
    #     return res
    
    @api.model
    def default_get(self, fields):
        res = super(create_project_ticket, self).default_get(fields) 
        context = dict(self._context or {})   
        active_id = context and context.get('active_id', False) or False
        perform_obj = self.env['project.issue']
        perform = perform_obj.browse(active_id)
 
        res.update({
                    'issue_id' : perform.id,
                    })
        return res

    @api.multi
    def action_create(self):
        '''
            Асуудлаас тикет үүсгэх товч
                Тикет асуудлаас үүссэн эсэхийг ялгах issue_id гэсэн context дамжуулж байгаа
        '''
        model_obj =self.env['ir.model.data']
        result = model_obj._get_id('nomin_helpdesk', 'view_helpdesk_form')
        view_id = model_obj.browse(result).res_id
        
        helpdesk = self.env['crm.helpdesk']
        emp_ids = self.env['hr.employee'].search([('user_id','=',self.issue_id.user_id.id)])
        ctx = dict(self._context)
        vals = {
                'create_date'       : time.strftime('%Y-%m-%d %H:%M:%S'),
                'phone_number'      : 999999,
                'user_id'           : self.issue_id.user_id.id,
                'user_of_department_id': emp_ids.department_id.id,
                'department_id'     : self.issue_id.departmet_id.id,
                'performer_team_id' : self.issue_id.departmet_id.id,
                'state'             : 'open',
                'date'              : self.issue_id.date_deadline,
                'type_id'           : self.type_id.id,
                'category_id'       : self.category_id.id,
                'channel_id'        : self.channel_id.id,
                'origin'            : self.issue_id.name,
                'description'       : self.issue_id.description,
                }
        ctx['issue_id'] = self.issue_id.id
        ctx_nolang = ctx.copy()
        ctx_nolang.pop('lang', None)
        helpdesk = helpdesk.with_context(ctx_nolang).create(vals)
        
        self.issue_id.update({
                          'created_ticket':True,
                          'created_ticket_id':helpdesk.id
                          })
        
        return {
                     'type': 'ir.actions.act_window',
                     'name': _('Register Call'),
                     'res_model': 'crm.helpdesk',
                     'view_type' : 'tree',
                     'view_mode' : 'form',
                     'search_view_id' : view_id,
                     'res_id':helpdesk.id,
                     'target' : 'current',
                     'nodestroy' : True,
                 }