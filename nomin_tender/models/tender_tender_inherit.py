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
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from dateutil import relativedelta 
import logging
import time
import traceback
import base64
from openerp.osv import osv, fields
from openerp import api, fields, models, SUPERUSER_ID, _
import openerp.tools
from openerp import tools
from openerp.http import request
import logging
_logger = logging.getLogger(__name__)

class tender_tender(models.Model):
    _inherit = ['tender.tender']
    
    @api.multi
    def _is_in_wanted_group(self):
        '''Тендерийн хүсэгч салбарын захирал 
           мөн эсэхийг шалгаж байна
        '''
        user_obj = self.env['res.users']
        emp_obj = self.env['hr.employee']
        model_obj = openerp.pooler.get_pool(self._cr.dbname).get('ir.model.data')
        notif_groups = model_obj.get_object_reference(self._cr, self._uid,  'nomin_tender', 'group_tender_wanter_manager')
        sel_user_ids = user_obj.search([('groups_id','in',notif_groups[1])])
        for tender in self:
            tender.is_in_wanted_group = False
            if self._uid in sel_user_ids._ids:
#                 allowed_deps = self.env['res.users'].browse(self._uid).tender_allowed_departments.ids
#                 emp = emp_obj.search([('user_id','=',self._uid)])
                if tender.sector_id.id in self.env.user.tender_allowed_departments.ids:
                    tender.is_in_wanted_group = True


    @api.multi
    def _is_tender_disabled_user(self):
        '''Тендерийн хүсэгч салбарын захирал эсэх мөн тендерийн хорооны дарга
           мөн эсэхийг шалгаж байна
        '''
        user_obj = self.env['res.users']
        emp_obj = self.env['hr.employee']
        model_obj = openerp.pooler.get_pool(self._cr.dbname).get('ir.model.data')
        notif_groups = model_obj.get_object_reference(self._cr, self._uid,  'nomin_tender', 'group_tender_wanter_manager')
        sel_user_ids = user_obj.search([('groups_id','in',notif_groups[1])])
        for tender in self:
            is_manager= self.env.user.has_group('nomin_tender.group_tender_manager')
            tender.is_tender_disabled_user = False
            if self._uid in sel_user_ids._ids:
                if tender.sector_id.id in self.env.user.tender_allowed_departments.ids:
                    tender.is_tender_disabled_user = True
            elif is_manager:
                tender.is_tender_disabled_user = True
    
    @api.multi
    def _is_in_branch_group(self):
        '''Тендерийн зарлах салбарын эрхлэгч
           мөн эсэхийг шалгаж байна
        '''
        user_obj = self.env['res.users']
        employee_obj = self.env['hr.employee']
        model_obj = openerp.pooler.get_pool(self._cr.dbname).get('ir.model.data')
        notif_groups = model_obj.get_object_reference(self._cr, self._uid,  'nomin_tender', 'group_tender_branch_manager')
        sel_user_ids = user_obj.search([('groups_id','in',notif_groups[1])])
        # print '__________ el_user_ids___________ ',sel_user_ids
        # tender = self.env['tender.tender').browse(cr, uid, ids[0]]
        for tender in self:
            tender.is_in_branch_group = False
            if self._uid in sel_user_ids._ids:
                emp_id = employee_obj.search([('user_id','=',self._uid)])
                if tender.respondent_employee_id in emp_id:
                    tender.is_in_branch_group = True

                    
    @api.multi
    def _is_in_confirmed_group(self):
        '''Тендерийн хүсэлт батлах удирдлагууд 
           мөн эсэхийг шалгаж байна
        '''
        user_obj = self.env['res.users']
        tender_obj =  self.env['tender.tender']
        line_obj = self.env['tender.employee.line']
        model_obj = openerp.pooler.get_pool(self._cr.dbname).get('ir.model.data')
        notif_groups = model_obj.get_object_reference(self._cr, self._uid, 'nomin_tender', 'group_tender_requist_approval_leaders')
        sel_user_ids = user_obj.search([('groups_id','in',notif_groups[1])])
        sel_user = user_obj.browse(sel_user_ids)
        for tender in self:
            tender.is_in_confirmed_group = False
            if self._uid in sel_user_ids._ids:
                emp_id = self.env['hr.employee'].search([('user_id','=',self._uid)])
                for line in tender.confirmed_member_ids:
                    if line.employee_id and line.employee_id in emp_id:
                        if line.state not in ['approved', 'cancel']:
                        #print "IN TUPLE",line.employee_id, emp_id, line.employee_id in emp_id
                            tender.is_in_confirmed_group = True
    
    is_in_wanted_group  = fields.Boolean('Is in wanted', compute=_is_in_wanted_group)
    is_in_branch_group  = fields.Boolean('Is in branch', compute=_is_in_branch_group)
    is_in_confirmed_group  = fields.Boolean('Is in confirm', compute=_is_in_confirmed_group)
    is_tender_disabled_user  = fields.Boolean('Is tender disabled user', compute=_is_tender_disabled_user)


    