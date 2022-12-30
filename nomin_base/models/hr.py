# -*- coding: utf-8 -*-

import json
from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

from odoo.exceptions import UserError, RedirectWarning, ValidationError

import odoo.addons.decimal_precision as dp


class nomin_report_footer_config(models.Model):
    _name = 'nomin.report.footer.config'
    _description = 'Nomin Report Footer Config'
    
    TYPE = [
        ('account','Senior Account'),
        ('department_chief','Department Chief')
    ]
    
    SIGNATURE_TYPE = [
        ('1','1 Signature'),
        ('2','2 Signature'),
        ('3','3 Signature')
    ]
        
    department_id = fields.Many2one('hr.department', string='Department')
    type = fields.Selection(TYPE, string='Job Type', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    
class hr_department(models.Model):
    _inherit = "hr.department"
    
    
    def check_adviser_group(self, user_ids):
        remove_user_ids=[]
        for uid in user_ids:
            if self.users_has_groups(self.env['res.users'].browse(uid), 'nomin_budget.group_budget_manager'):
                remove_user_ids.append(uid)
            if self.users_has_groups(self.env['res.users'].browse(uid), 'nomin_budget.group_budget_admin'):
                remove_user_ids.append(uid)
            if self.users_has_groups(self.env['res.users'].browse(uid), 'account.group_account_manager'):
                remove_user_ids.append(uid)
        remove_user_ids = list(set(remove_user_ids))
        if remove_user_ids:
            for rem_user in remove_user_ids:
                user_ids.remove(rem_user)
        return user_ids
    

    
    def check_support_group(self, user_ids):
        remove_user_ids=[]
        for uid in user_ids:
            if self.users_has_groups(self.env['res.users'].browse(uid), 'nomin_base.group_support_assistant'):
                remove_user_ids.append(uid)
        remove_user_ids = list(set(remove_user_ids))
        if remove_user_ids:
            for rem_user in remove_user_ids:
                user_ids.remove(rem_user)
        return user_ids


    @api.model
    def users_has_groups(self, user, groups):
        has_groups = []
        not_has_groups = []
        for group_ext_id in groups.split(','):
            group_ext_id = group_ext_id.strip()
            if group_ext_id[0] == '!':
                not_has_groups.append(group_ext_id[1:])
            else:
                has_groups.append(group_ext_id)

        for group_ext_id in not_has_groups:
            if user.has_group(group_ext_id):
                return False

        for group_ext_id in has_groups:
            if user.has_group(group_ext_id):
                return True
        return not has_groups
    

    
    def get_location_id(self):
        department_id = self.get_sector(self.id)
        if department_id:
            profit_centre = self.env['hr.department'].sudo().browse(department_id)
            if profit_centre.location_id:
                return profit_centre.location_id, False if profit_centre.location_id.name == 'Улаанбаатар хот' else profit_centre.location_id.name
            else:
                location_id = self.env['hr.employee.location'].sudo().search([('name','=','Улаанбаатар хот')])[0]
                return location_id, False
        else:
            location_id = self.env['hr.employee.location'].sudo().search([('name','=','Улаанбаатар хот')])[0]
            return location_id, False
                


    
    def _company_default_location(self):

#         if self.company_id.location_id:
#             return self.company_id.location_id
#         else:
            return self.env['hr.employee.location'].sudo().search([('name','=','Улаанбаатар хот')],limit=1)
        





    
    def get_sector(self, department_id):
        if department_id:
            self._cr.execute("select is_sector from hr_department where id=%s"%(department_id))
            fetched = self._cr.fetchone()
            if fetched:
                if fetched[0]:
                    return department_id
                else:
                    self._cr.execute("select parent_id from hr_department where id=%s"%(department_id))
                    pfetched = self._cr.fetchone()
                    if pfetched:
                        return self.get_sector(pfetched[0])
    
    def get_child_deparments(self, department_ids, only_sector=True):
        if department_ids:
            search_domain = [('id', 'child_of',department_ids)]
            if only_sector:
                search_domain.append(('is_sector', '=', True))
            child_deps = self.env['hr.department'].search(search_domain)
            if child_deps:
                return child_deps.ids
            else:
                return department_ids
        
#     def name_get(self, cr, uid, ids, context=None):
#         if not ids:
#             return []
#         if isinstance(ids, (int, long)):
#             ids = [ids]
#         if context is None:
#             context = {}
#         reads = self.read(cr, uid, ids, ['name','code', 'nomin_code', 'is_sector'], context=context)
#         res = []
#         for record in reads:
#             name = u'%s. %s'%(record['code'],record['name'])
#             if record['is_sector']:
#                 name = '%s %s'%(record['nomin_code'],record['name'])
#             res.append((record['id'], name))
#         return res
    
    
    def _dept_name_get_fnc(self):
        for record in self:
            name = record.name
            if record.is_sector:
                if record.nomin_code:
                    name = u'%s. %s'%(record.nomin_code,name)
            else:
                if record.code:
                    name = u'%s. %s'%(record.code,name)
            record.complete_name = name
    
#     @api.model
#     def name_search(self, name, args=None, operator='ilike', limit=100):
#         args = args or []
#         domain = []
#         if name:
#             domain = ['|', ('code', '=ilike', name + '%'), '|',('nomin_code', '=ilike', '%' + name),('name', operator, name)]
#             if operator in expression.NEGATIVE_TERM_OPERATORS:
#                 domain = [('name', operator, name)]
#         departs = self.search(domain + args, limit=limit)
#         return departs.name_get()
    
    type = fields.Selection([('company', 'Company'),
                             ('department01', 'Department01'), #Газар
                             ('sector', 'Sector'), #Салбар
                             ('department', 'Department'), #Хэлтэс, нэгж
                             ('head', 'Head')], 'Type', required=True, default='department')
    code = fields.Char(string="Code" , required=True, size=64, index=True ,track_visibility='onchange')
    word_code = fields.Char(string='Үсгэн код',required=False,track_visibility='onchange')
    is_sector = fields.Boolean(string='Is Sector?', index=True,track_visibility='onchange')
    active = fields.Boolean(string='Active',default=True,track_visibility='onchange')
    nomin_code = fields.Char(string='Nomin code', size=64, index=True,track_visibility='onchange')
    company_dep_id = fields.Many2one('hr.department', string='Company', select=True, domain="[('type','=','company')]")
    partner_id = fields.Many2one('res.partner', string='Partner')
  #  is_partner = fields.Boolean(string='Is Partner?')
    complete_name = fields.Char(string='Name', compute='_dept_name_get_fnc', size=256)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic account',track_visibility='onchange')
    nes_bank_id = fields.Char(string='NES Company number', size=2, track_visibility='onchange')
    report_footer_ids = fields.One2many('nomin.report.footer.config','department_id', string='Report Footer')
    unperformed_exchange_gain_account_id = fields.Many2one('account.account', string='Unperformed Rate Exchange Gain Account',
                                                                help="This account will be used when compute currency rate exchange unperformed gain or loss.",track_visibility='onchange')
    unperformed_exchange_loss_account_id = fields.Many2one('account.account', string='Unperformed Rate Exchange Loss Account',
                                                                help="This account will be used when compute currency rate exchange unperformed gain or loss.",track_visibility='onchange')
    
    payable_account_id = fields.Many2one('account.account', string='Payable Account')
    business_id = fields.Many2one('business.direction',string="Бизнесийн чиглэл",track_visibility="onchange")
    business_type_id = fields.Many2one('business.type',string="Дэлгүүрийн ангилал",track_visibility="onchange")
    is_lending_sector = fields.Boolean(string='Is lending sector?',track_visibility='onchange')
    senior_manager = fields.Many2one('hr.employee', string='Senior manager')
    # hr_migration_planning_ids = fields.One2many('hr.migration.planning','department_id',string='Hr migration planning',track_visibility='always')
    accountant_id = fields.Many2one('res.users',string='Accountant id',track_visibility='onchange')
    possessive_adjective = fields.Char(string='Possessive adjective', track_visibility='onchange')
    foreign_name = fields.Char(string='Хэлтсийн гадаад нэр')
    allow_to_edit = fields.Boolean(string="Allow to edit",default=False)
    local_sync_state = fields.Boolean(string='Local sync state',default=False)
    department_history_ids = fields.One2many('contract.department.history','department_id', string='department history')
    location_id = fields.Many2one('hr.employee.location', string='Салбарын байрших хот', default = _company_default_location)


    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            self.update({"possessive_adjective":self.name})



    # @api.onchange('company_id')
    # def onchange_company_name(self):
    #     print'\n\n\n\nOnchange'
    #     if self.is_sector:
    #         print '\n\n\n\ print 11' , self.company_id , self
    #         accounts = self.env['account.account'].sudo().search([('department_id','=',self.id)])
                
    #         if accounts:
    #             print'\n\n\n\n accounts',accounts
    #             accounts.update({'company_id':self.company_id.id})

            # self.unperformed_exchange_gain_account_id.company_id = self.company_id



        
    
    
    
    @api.model
    def create(self, vals):

        is_true = False
        is_true= self.env.user.has_group('nomin_hr.group_hr_admin')
        if is_true:
            if 'name' in vals:
                vals.update({'possessive_adjective':vals.get('name')})
            result = super(hr_department, self).create(vals)
            for his in self.department_history_ids:
                if not his.end_date:
                    his.write({'end_date':fields.Date.context_today(self)})
            history_new = self.env['contract.department.history']
            history_new.create({
                        'department_id': result.id,
                        'start_date': datetime.now().strftime('%Y-%m-%d'),
                        'name'  : result.name ,
            })
            return result
        else:
            raise UserError(_(u'Үүсгэх боломжгүй'))


    def write(self, vals):
        if 'company_id' in vals:
            query="update  account_account set company_id= %s where department_id =%s" %(vals.get('company_id'),self.id)
            self.env.cr.execute(query)
            query2="update  account_journal set company_id =%s where department_id =%s"%(vals.get('company_id'),self.id)
            self.env.cr.execute(query2)
            query3=" update  account_tax set company_id =%s where department_id =%s"%(vals.get('company_id'),self.id)
            self.env.cr.execute(query3)
            
        if vals.get('name'):
            history_obj = self.env['contract.department.history'].search([('start_date','=',fields.Date.context_today(self)),('department_id','=',self.id)])
            for history in history_obj:
                history.write({
                                'name' : vals.get('name') ,
                            })
            if not history_obj:
                for his in self.department_history_ids:
                    if not his.end_date:
                        his.write({'end_date':fields.Date.context_today(self)})
                history_new = self.env['contract.department.history']
                history_new.create({
                            'department_id' : self.id,
                            'start_date'    : datetime.now().strftime('%Y-%m-%d'),
                            'name'      : vals.get('name'),
                })
        if 'name' in vals:
            vals.update({'possessive_adjective':vals.get('name')})
        if 'nomin_code' in vals:
            nomin_code = vals.get("nomin_code")
            for department in self:
                if department.partner_id:
                    department.partner_id({'nomin_code': nomin_code, 'code':nomin_code})
                    
        if 'manager_id' in vals:
            manager_id = vals.get("manager_id")
            if manager_id:
                # print manager_id
                employee = self.env['hr.employee'].browse(manager_id)
                # print employee.user_id
                
            if employee.user_id:
                    self.message_subscribe_users(employee.user_id.id)            
        return super(hr_department, self).write(vals)


    
    def create_partner(self):
        # print'______TEST____',ids
        partner_obj = self.env['res.partner']
        if self.id:
            if self.partner_id:
                raise UserError(_('The partner already exists !'))
            
            partner_id = partner_obj.create({'name': '%s [%s]'%(self.name,self.code), 
                                                    'department_id':self.id, 
                                                    'code':self.nomin_code,
                                                    'company_type':'company',
                                                    'nomin_code':self.nomin_code,
                                                    'customer':True,
                                                    'supplier':True})
            return self.write({'partner_id':partner_id.id})

    
    def unlink(self):

        for dep in self:
            employee_id=self.env['hr.employee'].sudo().search([('department_id','=',dep.id)])
            if employee_id:
                raise UserError(_(u'Энэхүү хэлтэсийг %s ажилтан дээр сонгосн байгаа тул устгах боломжгүй!,\n Устгахын тулд ажилтнаас хэлтэсийг нь авна уу')%(employee_id.name))
        res = super(hr_department, self).unlink()
        return res


    @api.model
    def _action_sync_local_department_from_cron(self):

        self.action_sync_all()


    
    def action_sync_all(self):

        self.env['integration.config'].sudo().integration_handler(self)

    #     self.post_self_details('local_sync_department')

    # def post_self_details(self,integration_name):

    #     self.env['integration.config'].sudo().integration_handler(self)

    #     config = self.env['proactive.notification'].sudo().search([('code','=','local_sync_department')])
    #     if config:

    #         body = {
    #             'id':self.id,
    #             'name':self.name,
    #             'parent_id':self.parent_id.id if self.parent_id else 0,
    #             'active':1  if self.active else 0,
    #             'create_date': self.create_date,
    #         }

    #         config.integration_handler(self.id,body)

class ContractDepartmentHistory(models.Model):
    _name = 'contract.department.history'
    _descpription = 'Contract department history'
    _order = 'start_date desc'

    name = fields.Text(string="Department name")
    department_id = fields.Many2one('hr.department',string="Department" )
    start_date = fields.Date(string="Start date")
    end_date = fields.Date(string="End date")


# class BusinessDirection(models.Model):
#     _name = 'business.direction'
#     _description= 'Business Direction'
#     _inherit = ['mail.thread']
# 
#     name = fields.Char(string="Нэр",track_visibility='onchange')
# 
# 
# class BusinessType(models.Model):
#     _name = 'business.type'
#     _description= 'Business Type'
#     _inherit = ['mail.thread']
# 
#     name = fields.Char(string="Нэр",track_visibility='onchange')



# class HrMigrationPlanning(models.Model):
#     _name = 'hr.migration.planning'
#     _description= 'Hr migration planning'
#     _inherit = ['mail.thread', 'ir.needaction_mixin']

#     name = fields.Char(string="Нэр",track_visibility='onchange')
#     account_period_id = fields.Many2one('account.period',string='Hr Account period',track_visibility='always')
#     hr_planning_percent = fields.Float(string='Hr planning percent',track_visibility='always')
#     department_id = fields.Many2one('hr.department',string='Hr department',track_visibility='always')
