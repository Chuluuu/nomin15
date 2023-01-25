# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from dateutil import relativedelta 
import logging
import time
import traceback
import base64
from odoo import api, fields, models, SUPERUSER_ID, _
import odoo.tools
from odoo import tools
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)

class TenderTender(models.Model):
    _inherit = ['tender.tender']
    
    
    def _is_in_wanted_group(self):
        '''Тендерийн хүсэгч салбарын захирал 
           мөн эсэхийг шалгаж байна
        '''
        user_obj = self.env['res.users']
        emp_obj = self.env['hr.employee']
        notif_groups = self.env['ir.model.data'].get_object_reference('nomin_tender', 'group_tender_wanter_manager')
        sel_user_ids = user_obj.search([('groups_id','in',notif_groups[1])])
        for tender in self:
            tender.is_in_wanted_group = False
            if self._uid in sel_user_ids._ids:
#                 allowed_deps = self.env['res.users'].browse(self._uid).tender_allowed_departments.ids
#                 emp = emp_obj.search([('user_id','=',self._uid)])
                if tender.sector_id.id in self.env.user.tender_allowed_departments.ids:
                    tender.is_in_wanted_group = True


    
    def _is_tender_disabled_user(self):
        '''Тендерийн хүсэгч салбарын захирал эсэх мөн тендерийн хорооны дарга
           мөн эсэхийг шалгаж байна
        '''
        user_obj = self.env['res.users']
        emp_obj = self.env['hr.employee']
        notif_groups = self.env['ir.model.data'].get_object_reference('nomin_tender', 'group_tender_wanter_manager')
        sel_user_ids = user_obj.search([('groups_id','in',notif_groups[1])])
        for tender in self:
            is_manager= self.env.user.has_group('nomin_tender.group_tender_manager')
            tender.is_tender_disabled_user = False
            if self._uid in sel_user_ids._ids:
                if tender.sector_id.id in self.env.user.tender_allowed_departments.ids:
                    tender.is_tender_disabled_user = True
            elif is_manager:
                tender.is_tender_disabled_user = True
    
    
    def _is_in_branch_group(self):
        '''Тендерийн зарлах салбарын эрхлэгч
           мөн эсэхийг шалгаж байна
        '''
        user_obj = self.env['res.users']
        employee_obj = self.env['hr.employee']
        
        notif_groups = self.env['ir.model.data'].get_object_reference('nomin_tender', 'group_tender_branch_manager')
        sel_user_ids = user_obj.search([('groups_id','in',notif_groups[1])])
        # tender = self.env['tender.tender').browse(cr, uid, ids[0]]
        for tender in self:
            tender.is_in_branch_group = False
            if self._uid in sel_user_ids._ids:
                emp_id = employee_obj.search([('user_id','=',self._uid)])
                if tender.respondent_employee_id in emp_id:
                    tender.is_in_branch_group = True

                    
    
    def _is_in_confirmed_group(self):
        '''Тендерийн хүсэлт батлах удирдлагууд 
           мөн эсэхийг шалгаж байна
        '''
        user_obj = self.env['res.users']
        tender_obj =  self.env['tender.tender']
        line_obj = self.env['tender.employee.line']
        notif_groups = self.env['ir.model.data'].get_object_reference('nomin_tender', 'group_tender_requist_approval_leaders')
        sel_user_ids = user_obj.search([('groups_id','in',notif_groups[1])])
        sel_user = user_obj.browse(sel_user_ids)
        for tender in self:
            tender.is_in_confirmed_group = False
            if self._uid in sel_user_ids._ids:
                emp_id = self.env['hr.employee'].search([('user_id','=',self._uid)])
                for line in tender.confirmed_member_ids:
                    if line.employee_id and line.employee_id in emp_id:
                        if line.state not in ['approved', 'cancel']:
                            tender.is_in_confirmed_group = True
    
    is_in_wanted_group  = fields.Boolean('Is in wanted', compute=_is_in_wanted_group)
    is_in_branch_group  = fields.Boolean('Is in branch', compute=_is_in_branch_group)
    is_in_confirmed_group  = fields.Boolean('Is in confirm', compute=_is_in_confirmed_group)
    is_tender_disabled_user  = fields.Boolean('Is tender disabled user', compute=_is_tender_disabled_user)


    @api.model
    def tender_tender_alarm(self):
        _logger.info(u'\nТендерийн cron ажиллаж байна')
        '''Тендерийн хаах огноо болох үед 
           систем автоматаар төлөв солино
        '''
        query = "select tender.id as tid, tender.name as tnumber, tender.desc_name tname, type.name as parent_type, child_type.name as child_type, \
                    tender.ordering_date orderdate, tender.state state, tender.date_end \
                    from tender_tender as tender, tender_type as type, tender_type as child_type \
                    where tender.state = 'published' and type.id = tender.type_id and child_type.id = tender.child_type_id"
        self.env.cr.execute(query)
        records = self.env.cr.dictfetchall()
        # template_id = self.env['ir.model.data'].get_object_reference('nomin_tender', 'tender_tender_closed_state_email_template')[1]
        tender_obj=self.env['tender.tender']
        if records:
            for record in records:
                # date_end = record['date_end']
                # ADD time 8 hours
                date_end =datetime.datetime.strptime(record['date_end'], "%Y-%m-%d %H:%M:%S")
                date_now=datetime.datetime.now()
                if date_end <= date_now:
                    tender_obj.sudo().browse(record['tid']).write( {'state':'bid_expire'})
                    self.env.cr.commit()   