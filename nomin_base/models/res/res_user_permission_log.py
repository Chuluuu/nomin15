# -*- coding: utf-8 -*-
import logging
import openerp
from openerp import SUPERUSER_ID, models
import openerp.exceptions

from openerp.tools.translate import _
from openerp.http import request
from openerp.exceptions import UserError

from datetime import date, datetime
import time
from openerp import api, fields, models
import re

_logger = logging.getLogger(__name__)

class ResUsersPermissionLog(models.Model):
    _name = "res.users.permission.log"
    _description = "User permission - Log"
    _order = "create_date desc"

    user_id = fields.Many2one('res.users', string='User')

    log_type = fields.Selection([
            ('project_allowed_departments', 'Project Allowed Departments'),
            ('payment_request_departments', 'Payment_Request Allowed Departments'),
            ('budget_allowed_departments', 'Budget Allowed Departments'),
            ('delivery_allowed_departments', 'Delivery Allowed Departments'),
            ('hr_allowed_departments', 'Hr Allowed Departments'),    
            ('helpdesk_allowed_departments', 'Helpdesk Allowed Departments'),
            ('tender_allowed_departments', 'Tender Allowed Departments'),    
            ('archive_allowed_departments','Archive Allowed Departments'),
            ('allowed_departments','Allowed Departments'),    
            ('purchase_allowed_departments','Purchase Allowed Departments'),    
            ('loans_request_allowed_departments','Loans Request Allowed Departments'),
            ('asset_lease_allowed_departments','Asset Lease Allowed Departments'),
            ('salary_see_allowed_departments','HR-Allowed Departments'),
            ('regulation_confirm_allowed_departments','HR-Regulation Departments'),
            ('tsh_sod_allowed_departments', 'Timesheet allowed departments'),  
            ('financial_sod_allowed_departments', 'Financial allowed departments'),  
            ('group', 'Group'),
        ], string='Log type', default='department')

    action = fields.Selection([
            ('add', 'Add'),
            ('remove', 'Remove'),
        ], string='Action type', default='add')
    department_ids = fields.Many2many(
        comodel_name='hr.department', 
        string='Departments'
        )
    group_ids = fields.Many2many(
        comodel_name='res.groups', 
        string='Groups'
        )


class ResUsers(models.Model):
    _inherit = "res.users"

    def create_user_permission_log(self, log_type, action, data):
        if not data:
            return
        vals = {
                'log_type': log_type,
                'action': action,
                'user_id': self.id,
                }

        if log_type == 'group':
            vals['group_ids'] = [(6,0,data)]
        else:
            vals['department_ids'] = [(6,0,data)]

        self.env['res.users.permission.log'].create(vals)

    def create_allowed_department_log(self, vals):
        log_type = vals.get('log_type') 
        before_change_list = vals.get('before_change_list') 
        after_change_list = vals.get('after_change_list')
        to_add_department = list(after_change_list - before_change_list)
        to_remove_department = list(before_change_list - after_change_list)
        
        if to_remove_department != [] or to_add_department != []:
            self.arranged=False

        self.create_user_permission_log(log_type,'remove',to_remove_department)
        self.create_user_permission_log(log_type,'add',to_add_department)

    def get_allowed_department_ids(self, field_name):
        if field_name == 'project_allowed_departments':
            return self.project_allowed_departments.ids
        elif field_name == 'payment_request_departments':
            return self.payment_request_departments.ids
        elif field_name == 'budget_allowed_departments':
            return self.budget_allowed_departments.ids
        elif field_name == 'delivery_allowed_departments':
            return self.delivery_allowed_departments.ids
        elif field_name == 'hr_allowed_departments':
            return self.hr_allowed_departments.ids
        elif field_name == 'helpdesk_allowed_departments':
            return self.helpdesk_allowed_departments.ids
        elif field_name == 'tender_allowed_departments':
            return self.tender_allowed_departments.ids
        elif field_name == 'archive_allowed_departments':
            return self.archive_allowed_departments.ids
        elif field_name == 'allowed_departments':
            return self.allowed_departments.ids
        elif field_name == 'purchase_allowed_departments':
            return self.purchase_allowed_departments.ids
        elif field_name == 'loans_request_allowed_departments':
            return self.loans_request_allowed_departments.ids
        elif field_name == 'asset_lease_allowed_departments':
            return self.asset_lease_allowed_departments.ids
        elif field_name == 'salary_see_allowed_departments':
            return self.salary_see_allowed_departments.ids
        elif field_name == 'regulation_confirm_allowed_departments':
            return self.regulation_confirm_allowed_departments.ids



        elif field_name == 'tsh_sod_allowed_departments':
            return self.tsh_sod_allowed_departments.ids
        elif field_name == 'financial_sod_allowed_departments':
            return self.financial_sod_allowed_departments.ids


    def update_sod_allowed_departments_flags(self, group_id, parameter):

        group_obj = self.env['res.groups'].browse(group_id)
        if group_obj.allowed_resource:
            if not self.SOD_ALLOWED_DEPARTMENTS.has_key(group_obj.allowed_resource.name):
                raise UserError(_('SOD хандах нөөцийг Тохиргоо/Users/Group дээр буруу тохируулсан байна.\nЗөвшөөрөгдөөгүй нөөц:  [%s] - [%s]'% (group_obj.name, group_obj.allowed_resource.field_description)))
            qry = 'select ' + self.SOD_ALLOWED_DEPARTMENTS[group_obj.allowed_resource.name] + ' from res_users where id=' + str(self.id)

            self.env.cr.execute(qry)
            fetchall = self.env.cr.fetchall()

            count = 0
            if fetchall[0][0]:
                count = fetchall[0][0]

            if parameter == 'increment':
                count += 1
            elif count>0:
                count -= 1
            # if count == 0:
            #     self.write({group_obj.allowed_resource.name:[(6, 0, [])]})

            self.write({
                self.SOD_ALLOWED_DEPARTMENTS[group_obj.allowed_resource.name]:count
            })



    @api.multi
    def write(self, vals):
        department_log_check_list = [ 'project_allowed_departments','payment_request_departments',
            'budget_allowed_departments','delivery_allowed_departments',
            'hr_allowed_departments','helpdesk_allowed_departments',
            'tender_allowed_departments','archive_allowed_departments',
            'allowed_departments','purchase_allowed_departments',
            'loans_request_allowed_departments','asset_lease_allowed_departments',
            'salary_see_allowed_departments','regulation_confirm_allowed_departments',]

        department_log_list = []
        for field_name in department_log_check_list:
            if vals.has_key(field_name):
                department_log_list.append({ 'log_type': field_name,
                                             'before_change_list': set(self.get_allowed_department_ids(field_name)),
                                            })

        result = super(ResUsers, self).write(vals)    

        for department_log in department_log_list:
            department_log['after_change_list'] = set(self.get_allowed_department_ids(department_log['log_type']))
            self.create_allowed_department_log(department_log)
            self.action_update_additional_roles()

        to_remove_group = []
        to_add_group = []
        for group_name in vals.keys():
            group_id = group_name
            if 'in_group' in group_id:
                group_id = int(group_id.replace('in_group_',''))   
                if vals.get(group_name):
                    self.update_sod_allowed_departments_flags(group_id,'increment')
                    to_add_group.append(group_id)
                else:
                    self.update_sod_allowed_departments_flags(group_id,'decrement')
                    to_remove_group.append(group_id)
                self.action_update_additional_roles()
        if to_remove_group != [] or to_add_group != []:
            self.arranged=False

        self.create_user_permission_log('group','remove',to_remove_group)
        self.create_user_permission_log('group','add',to_add_group)
            
        return result
