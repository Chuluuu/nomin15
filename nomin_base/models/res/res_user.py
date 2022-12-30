# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# from . import logging
# from . import openerp
from odoo import SUPERUSER_ID, models
# from . import openerp.exceptions
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import float_is_zero
from odoo.tools import float_compare, float_round
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, ValidationError

import time
import math



# from . from openerp.tools.translate import _
# from openerp.http import request
# from openerp.exceptions import UserError

# from datetime import date, datetime
# from . import time
# from openerp import api, fields, models
# from . import re




SESSION_LIFETIME = 60 * 60 * 24 * 7

# _logger = logging.getLogger(__name__)

def get_sector_id(self,department_id):
    if department_id:
        self.env.cr.execute("select is_sector from hr_department where id=%s"%(department_id))
        fetched = self.env.cr.fetchone()
        if fetched:
            if fetched[0] == True:
                return department_id
            else:
                self.env.cr.execute("select parent_id from hr_department where id=%s"%(department_id))
                pfetched = self.env.cr.fetchone()
                if pfetched:
                    return get_sector_id(self,pfetched[0])

class ResUsers(models.Model):
    _inherit = "res.users"
    
    department_id = fields.Many2one('hr.department',string='Department',readonly=True,index=True)
    sector_id = fields.Many2one('hr.department',string='Sector',readonly=True)
    job_id =fields.Many2one('hr.job',string='Job',readonly=True,index=True)
    project_allowed_departments = fields.Many2many('hr.department','res_users_project_department_rel','uid','depid',string='Project Allowed Departments')    
    payment_request_departments = fields.Many2many('hr.department','res_users_payment_request_rel','uid','depid',string='Payment_Request Allowed Departments')    
    budget_allowed_departments = fields.Many2many('hr.department','res_users_budget_department_rel','uid','depid',string='Budget Allowed Departments')    
    delivery_allowed_departments = fields.Many2many('hr.department','res_users_delivery_department_rel','uid','depid',string='Delivery Allowed Departments')    
    hr_allowed_departments = fields.Many2many('hr.department','res_users_hr_department_rel','uid','depid',string='Hr Allowed Departments')    
    helpdesk_allowed_departments = fields.Many2many('hr.department','res_users_helpdesk_department_rel','uid','depid',string='Helpdesk Allowed Departments')    
    tender_allowed_departments = fields.Many2many('hr.department','res_users_tender_department_rel','uid','depid',string='Tender Allowed Departments')    
    archive_allowed_departments = fields.Many2many('hr.department','res_users_archive_department_rel','uid','depid',string='Archive Allowed Departments')    
    allowed_departments = fields.Many2many('hr.department','res_users_department_rel','uid','depid',string='Allowed Departments')    
    purchase_allowed_departments = fields.Many2many('hr.department','res_users_purchase_department_rel','uid','depid',string='Purchase Allowed Departments')    
    loans_request_allowed_departments = fields.Many2many('hr.department','res_users_loans_request_rel','uid','depid',string='Loans Request Allowed Departments')    
    asset_lease_allowed_departments = fields.Many2many('hr.department', 'res_users_asset_lease_rel', 'uid', 'depid', 'Asset Lease Allowed Departments')
    logistic_allowed_departments = fields.Many2many('hr.department','res_users_logistic_department_rel','user_id','dep_id',string='Logistic Allowed Departments')
    salary_see_allowed_departments = fields.Many2many('hr.department','res_users_pay_see_rel','uid','depid','HR-Allowed Departments')

    allowed_teams = fields.Many2many('hr.team','res_users_team_rel','uid','team_id',string='Зөвшөөрөгдсөн багууд') 
    project_allowed_teams = fields.Many2many('hr.team','res_users_team_rel','uid','team_id',string='Зөвшөөрөгдсөн багууд')
    regulation_confirm_allowed_departments = fields.Many2many('hr.department','res_users_hr_regulation_rel','uid','depid','HR-Regulation Departments')
    arranged = fields.Boolean(string='check',default=False)
    additional_roles = fields.Many2many('res.groups', 'res_users_additional_roles', 'uid', 'roleid', 'Нэмэгдэл эрхийн жагсаалт')

    additional_hr_departments = fields.Many2many('hr.department', 'res_users_add_hr_departments_rel','uid','depid', 'Нэмэлт хэлтэсийн жагсаалт')
    
    additional_project_departments = fields.Many2many('hr.department', 'res_users_add_pro_departments_rel','uid','depid', 'Төсөлийн нэмэгдэл жагсаалт') 

    additional_allowed_departments = fields.Many2many('hr.department', 'res_users_add_allowed_departments_rel','uid','depid', 'Төсөлийн нэмэгдэл жагсаалт')

    additional_purchase_departments = fields.Many2many('hr.department', 'res_users_add_pur_departments_rel','uid','depid', 'Төсөлийн нэмэгдэл жагсаалт')

    additional_budget_departments= fields.Many2many('hr.department', 'res_users_add_bud_departments_rel','uid','depid', 'Төсөлийн нэмэгдэл жагсаалт')

    role_type = fields.Selection ([ ('support_user','Дэмжлэг үйлчилгээний ажилтан')
                                    ,('admin_user','Админ эрх бүхий хэрэглэгч')
                                    ,('non_standard_department_user','Хэлтсийн стандарт зөрчсөн хэрэглэгч')                          
                                    
                                    ,('standard_user','Стандарт эрх бүхий хэрэглэгч') 
                                    ,('multirole_user','Нэмэлт эрх бүхий хэрэглэгч')    
                                    ,('multidepartment_user','Нэмэлт хэлтэс бүхий хэрэглэгч') 
                                    # ,('senior_user','Ахлах хэрэглэгч')
                                    ,('multiresource_user','Нэмэлт эрх ба хэлтэс бүхий хэрэглэгч') 
                                    ], string="Нэмэлт эрх байгаа эсэх")
    count_of_additional_roles = fields.Integer(string = 'Нэмэлт эрхийн тоо',index=True)
    count_of_additional_departments = fields.Integer(string = 'Нэмэлт хэлтсийн тоо',index=True)
    count_of_managerial_roles = fields.Integer(string = 'Менежер эрхийн тоо',index=True)
    count_of_menu_dominant_roles= fields.Integer(string = 'Цэсэнд давамгай эрхийн тоо',index=True)

    tsh_sod_allowed_departments = fields.Many2many('hr.department','res_users_tsh_department_rel','uid','depid',string='Цаг бүртгэл зөвшөөрөгдсөн хэлтсүүд')    
    tsh_sod_flag = fields.Integer('Цаг бүртгэл зөвшөөрөгдсөн хэлтсүүд')
    financial_sod_allowed_departments = fields.Many2many('hr.department','res_users_financial_department_rel','uid','depid',string='Санхүүгийн зөвшөөрөгдсөн хэлтсүүд')    
    financial_sod_flag = fields.Integer('Санхүүгийн зөвшөөрөгдсөн хэлтэсүүд')
    sdlc_config = fields.Char(string='SDLC config')
    odoo15_sync = fields.Boolean(string="Odoo 15 sync",default=False)
    team_id = fields.Many2one('hr.team',
    ondelete='set null', string="Team name", index=True,  track_visibility='onchange')
    

    SOD_ALLOWED_DEPARTMENTS = {
        'tsh_sod_allowed_departments':'tsh_sod_flag',
        'financial_sod_allowed_departments':'financial_sod_flag',
    }

    def _get_current_employee(self): 
        employee_ids = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        if employee_ids:
            return employee_ids.id
        else:
            raise UserError(_('You don\'t have related company. Please contact administrator.'))
        return None


    def validate_email(self,email):
        #pattern = r"\"?([-a-zA-Z0-9.`?{}]+@\w+\.\w+)\"?" 
        pattern = re.compile(r"\"?([-a-zA-Z0-9.`?{}]+@\w+\.\w+)\"?" )
        if re.match(pattern, email):
            return True
        return False
    
    def set_of_departments(self,config_line):

        

        return {

                'project_allowed_departments':[(6,0,config_line.project_allowed_departments.ids)],
                'budget_allowed_departments':[(6,0,config_line.budget_allowed_departments.ids)],
                'delivery_allowed_departments':[(6,0,config_line.delivery_allowed_departments.ids)],
                'hr_allowed_departments':[(6,0,config_line.hr_allowed_departments.ids)],
                'helpdesk_allowed_departments':[(6,0,config_line.helpdesk_allowed_departments.ids)],
                'tender_allowed_departments':[(6,0,config_line.tender_allowed_departments.ids)],
                'archive_allowed_departments':[(6,0,config_line.archive_allowed_departments.ids)],
                'allowed_departments':[(6,0,config_line.allowed_departments.ids)],
                'purchase_allowed_departments':[(6,0,config_line.purchase_allowed_departments.ids)],
                'payment_request_departments':[(6,0,config_line.payment_request_departments.ids)],
                'regulation_confirm_allowed_departments':[(6,0,config_line.regulation_confirm_allowed_departments.ids)],
                'salary_see_allowed_departments':[(6,0,config_line.salary_see_allowed_departments.ids)],
                'loans_request_allowed_departments':[(6,0,config_line.loans_request_allowed_departments.ids)],
                'asset_lease_allowed_departments':[(6,0,config_line.asset_lease_allowed_departments.ids)],
                'logistic_allowed_departments':[(6,0,config_line.logistic_allowed_departments.ids)],
                }


  


    @api.model
    def create(self, vals):
        user_id = super(ResUsers, self).create(vals)        
        
        # if user_id.job_id and user_id.department_id:
        #     user_id.write({
        #         'project_allowed_departments':[(4,user_id.department_id.id)],
        #         'budget_allowed_departments':[(4,get_sector_id(self,user_id.department_id.id))],
        #         'delivery_allowed_departments':[(4,get_sector_id(self,user_id.department_id.id))],
        #         'hr_allowed_departments':[(4,user_id.department_id.id)],
        #         'helpdesk_allowed_departments':[(4,user_id.department_id.id)],
        #         'tender_allowed_departments':[(4,get_sector_id(self,user_id.department_id.id))],
        #         'archive_allowed_departments':[(4,get_sector_id(self,user_id.department_id.id))],
        #         'allowed_departments':[(4,user_id.department_id.id)],
        #         'purchase_allowed_departments':[(4,user_id.department_id.id)],
        #         'payment_request_departments':[(4,user_id.department_id.id)],
        #         'loans_request_allowed_departments':[(4,user_id.department_id.id)],
        #         })
        
            # if self.validate_email(user_id.login):
                # config_id = self.env['res.users.config'].search([('job_id','=',user_id.job_id.id)])                
                # if config_id:
                #     for group in config_id.group_ids:                        
                #         group.write({'users':[(4,user_id.id)]})
                
                # if user_id.department_id.id:                  
                #     config_line = self.env['res.users.config.line'].search([('config_id','=',config_id.id),('department_id','=',user_id.department_id.id)])                    
                #     if config_line.group_ids:
                #             for group in config_line.group_ids:
                #                 group.write({'users':[(4,user_id.id)]})
                    # user_id.write({
                        # 'project_allowed_departments':[(4,user_id.department_id.id)],
                        # 'asset_lease_allowed_departments':[(4,get_sector_id(self,user_id.department_id.id))],
                        # 'delivery_allowed_departments':[(4,get_sector_id(self,user_id.department_id.id))],
                        # 'hr_allowed_departments':[(4,user_id.department_id.id)],
                        # 'helpdesk_allowed_departments':[(4,user_id.department_id.id)],
                        # 'tender_allowed_departments':[(4,get_sector_id(self,user_id.department_id.id))],
                        # 'archive_allowed_departments':[(4,get_sector_id(self,user_id.department_id.id))],
                        # 'allowed_departments':[(4,user_id.department_id.id)],
                        # 'purchase_allowed_departments':[(4,user_id.department_id.id)],
                        # 'payment_request_departments':[(4,user_id.department_id.id)],
                        # })
                    # user_id.write(self.set_of_departments(config_line))
        return user_id

    # @api.multi
    def action_change(self):

        query = """delete from res_groups_users_rel where uid=%s and gid not in (56,51);
            insert into res_groups_users_rel select c.res_groups_id gid,%s uid from res_users_config a
            inner join res_groups_res_users_config_rel c on c.res_users_config_id = a.id 
            left join res_groups_users_rel d on c.res_groups_id=d.gid and d.uid=%s
            where d.uid is null and d.gid is null and a.job_id = %s """ % (self.id,self.id,self.id,self.job_id.id)
        # print 'query ',query
        self.env.cr.execute(query)
        self.additional_departments(self)
    

    def additional_departments(self,user_id):    
        self.additional_department(user_id,'res_users_hr_dep_rel','res_users_hr_department_rel','hr_allowed_departments')
        self.additional_department(user_id,'res_users_project_dep_rel','res_users_project_department_rel','project_allowed_departments')
        self.additional_department(user_id,'res_users_budget_dep_rel','res_users_budget_department_rel','budget_allowed_departments')
        self.additional_department(user_id,'res_users_dep_rel','res_users_department_rel','allowed_departments')
        self.additional_department(user_id,'res_users_purchase_dep_rel','res_users_purchase_department_rel','purchase_allowed_departments')
        self.additional_department(user_id,'res_users_delivery_dep_rel','res_users_delivery_department_rel','delivery_allowed_departments')
        self.additional_department(user_id,'res_users_helpdesk_dep_rel','res_users_helpdesk_department_rel','helpdesk_allowed_departments')
        self.additional_department(user_id,'res_users_tender_dep_rel','res_users_tender_department_rel','tender_allowed_departments')
        self.additional_department(user_id,'res_users_archive_dep_rel','res_users_archive_department_rel','archive_allowed_departments')
        self.additional_department(user_id,'res_users_payment_req_rel','res_users_payment_request_rel','payment_request_departments')
        self.additional_department(user_id,'res_users_loans_req_rel','res_users_loans_request_rel','loans_request_allowed_departments')


        
    def additional_department(self,user_id,table1,table2,additional_field):
        # ХЭЛТЭС ТОХИРУУЛАХ
        query = "CREATE TEMP TABLE temp_department_table(depid int);"
        self.env.cr.execute(query)
        query = "select c.dep_id depid from res_users_config_line a " + \
            "inner join res_users_config b on a.config_id = b.id " + \
            "inner join " + table1 + "  c on c.user_id = a.id " +\
                "where a.department_id = %s and b.job_id = %s " % (user_id.department_id.id,user_id.job_id.id)
        print ('query',query)
        self.env.cr.execute(query)
        user_deps = self.env.cr.dictfetchall()
        dep_ids=[]
        if user_deps:
            for dep in user_deps:
                dep_ids.append(dep['depid'])

        query = "DROP TABLE temp_department_table;"
        self.env.cr.execute(query)
        self.write({additional_field:[(6,0,dep_ids)]})


        # for user_id in self:
        #     if not user_id.job_id:
        #         continue
            
            # Shine comment
            # config_id = self.env['res.users.config'].search([('job_id','=',user_id.job_id.id)])
            # if config_id:
            #     for group in config_id.group_ids:                        
            #         group.write({'users':[(4,user_id.id)]})

            # if user_id.department_id: 
            #     config_line = self.env['res.users.config.line'].search([('config_id','=',config_id.id),('department_id','=',user_id.department_id.id)])
            #     if not config_line:
            #         raise UserError(_('Хэрэглэгчийн тохиргоон дээр хэлтэс тохирууулаагүй байна.'))

            #     if config_line.group_ids:
            #         for group in config_line.group_ids:
            #             group.write({'users':[(4,user_id.id)]})
            #     user_id.write(self.set_of_departments(config_line))
                    
            # Uunees doosh huuchin bsan comment
            # if not user_id.department_id:
            #     continue
            # user_id.write({
            #     'project_allowed_departments':[(4,user_id.department_id.id)],
            #     'budget_allowed_departments':[(4,get_sector_id(self,user_id.department_id.id))],
            #     'delivery_allowed_departments':[(4,get_sector_id(self,user_id.department_id.id))],
            #     'hr_allowed_departments':[(4,user_id.department_id.id)],
            #     'helpdesk_allowed_departments':[(4,user_id.department_id.id)],
            #     'tender_allowed_departments':[(4,get_sector_id(self,user_id.department_id.id))],
            #     'archive_allowed_departments':[(4,get_sector_id(self,user_id.department_id.id))],
            #     'allowed_departments':[(4,user_id.department_id.id)],
            #     'purchase_allowed_departments':[(4,user_id.department_id.id)],
            #     'payment_request_departments':[(4,user_id.department_id.id)],
            #     'loans_request_allowed_departments':[(4,user_id.department_id.id)],
            #     })

            # for line in self.find_line_ids('confirmed'):
            #     for user in line.group_id.users:
            #         deps = self.env['hr.department'].search([('id','in',user.hr_allowed_departments.ids)])
            #         user_dep_set = set(deps.ids)                
            #         if list(user_dep_set.intersection([self.department_id.id])):
            #             if user.id == self.env.user.id:
            #                 self.is_approver = True




    # @api.multi
    # def action_update_additional_roles(self):

    #     for user_id in self.env['res.users'].search([('active','=',True)]):
           
    #         if user_id.job_id.id:
    #             config_id = self.env['res.users.config'].search([('job_id','=',user_id.job_id.id)])
    #             if config_id:
                    
    #                 has_standard_roles = 1 
    #                 count_of_additional_roles = 0

    #                 query = "SELECT gid from res_groups_users_rel where uid= %s" % (user_id.id)
    #                 self.env.cr.execute(query)
    #                 users_groups = self.env.cr.dictfetchall()

    #                 for users_group in users_groups:
    #                     users_group_id = users_group['gid']
    #                     if users_group_id not in config_id.group_ids.ids:    
    #                         count_of_additional_roles += 1
    #                         if user_id.has_group('base.group_hr_manager'):
    #                              has_standard_roles = 2
    #                         if users_group_id not in user_id.additional_roles.ids:
    #                             # user_id.write({'additional_roles':[(4,users_group_id.id)]})   
    #                             self.env.cr.execute('''INSERT into res_users_additional_roles (uid, roleid) 
    #                                 values ( %s,%s)''',(user_id.id, users_group_id))

    #                         if has_standard_roles != 2:
    #                             has_standard_roles = 0   
    #                 if has_standard_roles == 1:
    #                     user_id.write({'additional_roles':False,
    #                                     'role_type':'standard_user' })
    #                 elif has_standard_roles == 2:
    #                     self.env.cr.execute('update res_users set role_type=\'admin_user\',count_of_additional_roles=%s where id=%s'%(count_of_additional_roles,user_id.id))
    #                 else:
    #                     self.env.cr.execute('update res_users set role_type=\'multirole_user\',count_of_additional_roles=%s where id=%s'%(count_of_additional_roles,user_id.id))

    #     print 'n\n\n\n\n\n\n\n\nn\n\n\n\n\n\\n\n\nn\n\n\n+++++  '       



    # @api.multi
    def action_update_additional_roles(self):

        


        print ('self',self)
        if self.job_id.id:

            self.update_additional_roles(self)
            
            print ('self',self)
            self.update_additional_departments(self)
            # self.update_additional_departments(self)
            self.conclution(self)

        user_ids = self.env['res.users'].search([('active','=',True),('arranged','=',False)],limit = 20)

        # if user_ids:

        #     for user_id in user_ids :
        
        #     # if user_id.job_id.id :
        #     # # if user_id.job_id.id and user_id.id == 1417:
        #     #     config_id = self.env['res.users.config'].search([('job_id','=',user_id.job_id.id)])
        #     #     if config_id:        
        #         # print 'user_id',user_id
        #         if user_id.job_id.id:

        #             self.update_additional_roles(user_id)
                    
        #             # print 'user_id',user_id
        #             self.update_additional_departments(user_id)
        #             # self.update_additional_departments(user_id)
        #             self.conclution(user_id)
        #         user_id.arranged = True




    # @api.multi
    def update_additional_roles(self,user_id):


        # for user_id in self.env['res.users'].search([('active','=',True)]):
           
        #     if user_id.job_id.id and user_id.id==639:
        #         config_id = self.env['res.users.config'].search([('job_id','=',user_id.job_id.id)])
        #         if config_id:
                    
        count_of_additional_roles = 0
        count_of_managerial_roles = 0
        count_of_menu_dominant_roles=0
    
        query = "CREATE TEMP TABLE temp_role_table(gid int);"
        self.env.cr.execute(query)
        query = "insert into temp_role_table  select c.res_groups_id roleid from res_users_config a " + \
            "inner join res_groups_res_users_config_rel c on c.res_users_config_id = a.id " +\
            "where a.job_id = %s " % (user_id.job_id.id)
        
        
        # print 'user_id.job_id',user_id.job_id


        self.env.cr.execute(query)

        query = "SELECT gid from res_groups_users_rel  where uid= %s and gid not in (select gid from temp_role_table)" % (user_id.id)
        self.env.cr.execute(query)
        user_roles = self.env.cr.dictfetchall()
        print ('user_',user_roles)


        role_ids=[]
        if user_roles:

            # if self.group_id == res.groups.group_id:
            #     if res.groups.group_type == 'admin_role':
            #         self.role_type = 'admin_user'

            # query = "Select "

            

 
            query = "SELECT sum(case when a.group_type =  'support_role' then 1 else 0 end) support_role," + \
                "sum(case when a.group_type = 'admin_role' then 1 else 0 end) admin_role," +\
                "sum(case when a.group_type = 'managerial_role' then 1 else 0 end) managerial_role," +\
                "sum(case when a.group_type = 'menu_dominant_role' then 1 else 0 end) menu_dominant_role " +\
                "from res_groups a inner join res_groups_users_rel b on b.gid=a.id " +\
                "where b.uid=%s" % ( user_id.id )
            self.env.cr.execute(query)
            support_user = self.env.cr.dictfetchall()
            
            print ('support_user',support_user[0]['support_role'])
            print ('support_user',support_user[0]['admin_role'])
            print ('support_user',support_user[0]['managerial_role'])
            print ('support_user',support_user[0]['menu_dominant_role'])

            if support_user[0]['support_role']>0:

                user_id.role_type = 'support_user'
            elif support_user[0]['admin_role']>0:
                user_id.role_type = 'admin_user'
            for role in user_roles:

                count_of_additional_roles += 1

                role_ids.append(role['gid'])

            query = "UPDATE res_users set count_of_additional_roles =%s, count_of_managerial_roles = %s , count_of_menu_dominant_roles = %s where id = %s "%(count_of_additional_roles,support_user[0]['managerial_role'],support_user[0]['menu_dominant_role'],user_id.id)
            
            print ('query',role_ids)
            
            # query = "UPDATE res_users set count_of_additional_roles = %s, count_of_managerial_roles = %s, count_of_menu_dominant_roles = %s "+\
            #      "where id = %s " % (count_of_additional_roles,count_of_managerial_roles,count_of_menu_dominant_roles,user_id.id)
            # print 'query',query
            self.env.cr.execute(query)
        


        
        query = "DROP TABLE temp_role_table;"
        self.env.cr.execute(query)     
        user_id.write({'additional_roles':[(6,0,role_ids)]})


            # query = "UPDATE res_users set count_of_additional_roles =%s, count_of_managerial_roles = %s , count_of_menu_dominant_roles = %s where id = %s "%(count_of_additional_roles,support_user[0]['managerial_role'],support_user[0]['menu_dominant_role'],user_id.id)
            
            # print 'query',query
            
            # # query = "UPDATE res_users set count_of_additional_roles = %s, count_of_managerial_roles = %s, count_of_menu_dominant_roles = %s "+\
            # #      "where id = %s " % (count_of_additional_roles,count_of_managerial_roles,count_of_menu_dominant_roles,user_id.id)
            # # print 'query',query
            # self.env.cr.execute(query)
        
        
        
        # self.write({'count_of_managerial_roles':[(6,0,count_of_managerial_roles)]})
       
    
    def update_additional_departments(self,user_id):    
    

        self.count_of_additional_departments = 0 
        self.update_additional_department(user_id,'res_users_hr_dep_rel','res_users_hr_department_rel',user_id.hr_allowed_departments, 'additional_hr_departments')
        self.update_additional_department(user_id,'res_users_project_dep_rel','res_users_project_department_rel',user_id.project_allowed_departments,'additional_project_departments')
        self.update_additional_department(user_id,'res_users_budget_dep_rel','res_users_budget_department_rel',user_id.additional_budget_departments,'additional_budget_departments')
        self.update_additional_department(user_id,'res_users_dep_rel','res_users_department_rel',user_id.additional_allowed_departments,'additional_allowed_departments')
        self.update_additional_department(user_id,'res_users_purchase_dep_rel','res_users_purchase_department_rel',user_id.additional_purchase_departments,'additional_purchase_departments')
        self.conclution(user_id)



    def update_additional_department(self,user_id,table1,table2,allowed_departments,additional_field):
        
        count_of_additional_departments = 0

        if user_id.department_id:
            query = "CREATE TEMP TABLE temp_department_table(depid int);"
            self.env.cr.execute(query)
            query = "insert into temp_department_table  select c.dep_id  depid from res_users_config_line a " + \
                "inner join res_users_config b on a.config_id = b.id " + \
                "inner join " + table1 + "  c on c.user_id = a.id " +\
                    "where a.department_id = %s and b.job_id = %s " % (user_id.department_id.id,user_id.job_id.id)

            # query = "insert into temp_department_table SELECT depid from res_users_hr_department_rel  where uid= %s" % (user_id.id)
            self.env.cr.execute(query)
            # query = "select * from temp_department_table;"

            query = "SELECT depid from " + table2 + " where uid= %s and depid not in (select depid from temp_department_table)" % (user_id.id)
            self.env.cr.execute(query)
            user_deps = self.env.cr.dictfetchall()
            # print 'user_deps 0',user_deps['depid']
            # print 'user_deps ===',user_deps[0]['depid']
            # print '\n\n\n depid====', user_deps  
            dep_ids=[]
            if user_deps:
                for dep in user_deps:
                    # for dep in user_deps:
                    # print '\n\n\n depid', dep                
                    count_of_additional_departments += 1
                    dep_ids.append(dep['depid'])

            if user_id.department_id.id not in dep_ids and user_id.department_id in allowed_departments:
                        user_id.role_type = 'non_standard_department_user'
                        # self.env.cr.execute('update res_users set role_type=\'non_standard_department_user\',count_of_additional_departments=%s where id=%s'%(count_of_additional_departments,user_id.id))
            
            user_id.count_of_additional_departments += count_of_additional_departments
        # self.env.cr.execute('update res_users set role_type=\'non_standard_department_user\',count_of_additional_departments=%s where id=%s'%(count_of_additional_departments,user_id.id))
        
        # if has_standard_roles == 3:
        #      self.env.cr.execute('update res_users set role_type=\'non-standard_user\',count_of_additional_roles=%s where id=%s'%(count_of_additional_departments,user_id.id))
      
            
                # dep_ids.append(dep['depid'])
            # print 'additional_field',additional_field
            # print 'count_of_additional_departments',count_of_additional_departments
            query = "DROP TABLE temp_department_table;"
            self.env.cr.execute(query)
            user_id.write({additional_field:[(6,0,dep_ids)]})
            
    
    def conclution(self,user_id):

        # print'\n\n\n\n\n\n\n\n'
      
        # if self.role_type not in ('support_user','admin_user'):    
        #     if self.count_of_additional_departments == 0 and self.count_of_additional_roles !=0:
        #         self.role_type = 'multirole_user'
        #     elif self.count_of_additional_departments != 0  and self.count_of_additional_roles == 0:
        #         self.role_type = 'multidepartment_user'
        #     elif self.count_of_additional_departments != 0  and self.count_of_additional_roles != 0:
        #         self.role_type = 'multiresource_user'
       
        if user_id.role_type in ('support_user','admin_user','non_standard_department_user'):    
            return
        if user_id.count_of_additional_departments == 0 and user_id.count_of_additional_roles ==0:
            user_id.role_type = 'standard_user'
        if user_id.count_of_additional_departments == 0 and user_id.count_of_additional_roles !=0:
            user_id.role_type = 'multirole_user'
        elif user_id.count_of_additional_departments != 0  and user_id.count_of_additional_roles == 0:
            user_id.role_type = 'multidepartment_user'
        elif user_id.count_of_additional_departments != 0  and user_id.count_of_additional_roles != 0:
            user_id.role_type = 'multiresource_user'


        # self.env.cr.execute('update res_users set role_type=\''+self.role_type+ \
        #     '\',count_of_additional_roles=%s ,count_of_additional_departments=%s where id=%s'%(count_of_additional_roles,count_of_additional_departments,user_id.id))

  
   


 #  ==========================================================

                    # if user_id.department_id and user_id.job_id:
                    #     query = "SELECT depid from res_users_hr_department_rel where uid= %s and depid not in " + \
                    #     "(insert into temp_department_table  select c.dep_id  depid from res_users_config_line a " + \
                    #     "inner join res_users_config b on a.config_id = b.id " + \
                    #     "inner join res_users_hr_dep_rel c on c.user_id = a.id " +\
                    #     "where a.department_id = %s and b.job_id = %s );" % (user_id.id,user_id.department_id.id,user_id.job_id.id)
                    #     print 'query',query
                    #     self.env.cr.execute(query)
                    #     user_deps = self.env.cr.dictfetchall()

                    #     print 'user_deps',user_deps[0]['depid']
                    #     print 'user_deps',user_deps
                        # print(date_object)
 #===========================================




                    # user_deps = self.env.cr.dictfetchall()


                    # print 'user_deps',user_deps[0]['depid']
                    # print 'user_deps',user_deps

                        # query = "SELECT depid from res_users_hr_department_rel where uid= %s
                        # (select d.dep_id from res_users_config_line a " + \
                        #     "inner join res_users_config b on a.config_id = b.id " + \
                        #     "inner join res_users_hr_dep_rel c on c.user_id = a.id " +\
                        #     "inner join res_users_hr_department_rel d on d.dep_id = c.dep_id " +\
                        #      "where a.department_id = 254 and b.job_id = 10221) " % (user_id.department_id.id,user_id.job_id.id)


                        # self.env.cr.execute(query)
                        # deps = set(self.env.cr.dictfetchall())
                        # if deps:
                        #     print 'deps',deps
                        #     print 'deps',type(deps)
                        #     print 'user_id.department_id.id',user_id.department_id.id
                        #     print 'user_id',user_id
                        # print 'deps',type(deps)
                        # print 'deps',deps[0]
                        # print 'deps',deps[1]


                    # hasah = []

                    # hasah = list(deps - user_deps)

                    # print 'hasah',hasah
                 
                    # for department in user_deps:	

                    #     department_id = department['depid']
                    #     if department_id not in config_id.line_ids.ids:    
                    #         count_of_additional_roles += 1



                    #     select * from res_users_config_line a 
                    #     inner join res_users_config b on a.config_id = b.id
                    #     where a.department_id = '' and b.job_id = ''

                    #         if line.department_id not in ['res.users.hr_allowed_department']:
                    #              count_of_additional_departments += 1
                                
                    #         if users_line  not in user_id.additional_departments.ids:
                    #                 # user_id.write({'additional_roles':[(4,users_group_id.id)]})   
                    #                 self.env.cr.execute('''INSERT into res_users_additional_departments (uid, roleid) 
                    #                     values ( %s,%s)''',(user_id.id, users_group_id))

                    #         if has_standard_departments != 2:
                    #             has_standard_departments = 0   
                    # if has_standard_departments == 1:
                    #     user_id.write({'additional_departments':False,
                    #                     'role_type':'standard_user' })
                    # elif has_standard_departments == 2:
                    #     self.env.cr.execute('update res_users set role_type=\'admin_user\',count_of_additional_roles=%s where id=%s'%(count_of_additional_departments,user_id.id))
                    # else:
                    #     self.env.cr.execute('update res_users set role_type=\'multirole_user\',count_of_additional_roles=%s where id=%s'%(count_of_additional_departments,dep_id.id))

        # print 'n\n\n\n\n\n\n\n\nn\n\n\n\n\n\\n\n\nn\n\n\n+++++  '       







        #             if dictfetchall:
        #                 for dic in dictfetchall:
        #                     group = dic['extra_id']




        #             print '-----------',user_id.group_ids
        #             for general_group in user_id.group_ids:
        #                 if general_group not in config_id.group_ids:   
        #                     if user_id in general_group.users: 
        #                         count_of_additional_roles += 1
        #                         print '\n+++++group  ', general_group
        #                         if user_id.has_group('base.group_hr_manager'):
        #                             has_standard_roles = 2
        #                         if general_group not in user_id.additional_roles:
        #                             # user_id.write({'additional_roles':[(4,general_group.id)]})   
        #                             self.env.cr.execute('''INSERT into res_users_additional_roles (uid, roleid) 
        #                                 values ( %s,%s)''',(user_id.id, general_group.id))

        #                         if has_standard_roles != 2:
        #                             has_standard_roles = 0   
        #             if has_standard_roles == 1:
        #                 user_id.write({'additional_roles':False,
        #                                 'role_type':'standard_user' })
        #             elif has_standard_roles == 2:
        #                 self.env.cr.execute('update res_users set role_type=\'admin_user\',count_of_additional_roles=%s where id=%s'%(count_of_additional_roles,user_id.id))
        #             else:
        #                 self.env.cr.execute('update res_users set role_type=\'multirole_user\',count_of_additional_roles=%s where id=%s'%(count_of_additional_roles,user_id.id))

        # print 'n\n\n\n\n\n\n\n\nn\n\n\n\n\n\\n\n\nn\n\n\n+++++  '       
















        # config_id = self.env['res.users.config'].search([(1,'=',1)])





        # for user_id in self.env['res.users'].search([('active','=',True)]):
           
        #     if user_id.job_id.id:
        #         config_id = self.env['res.users.config'].search([('job_id','=',user_id.job_id.id)])
        #         if config_id:
                    
        #             has_standard_roles = 1 
        #             count_of_additional_roles = 0
        #             # general_group_ids = self.env['res.groups'].search([(1,'=',1)])

        #             for general_group in user_id.group_ids:
        #                 if general_group not in config_id.group_ids:   
        #                     if user_id in general_group.users: 
        #                         count_of_additional_roles += 1
        #                         print '\n+++++group  ', general_group
        #                         if user_id.has_group('base.group_hr_manager'):
        #                             has_standard_roles = 2
        #                         if general_group not in user_id.additional_roles:
        #                             # user_id.write({'additional_roles':[(4,general_group.id)]})   
        #                             self.env.cr.execute('''INSERT into res_users_additional_roles (uid, roleid) 
        #                                 values ( %s,%s)''',(user_id.id, general_group.id))

        #                         if has_standard_roles != 2:
        #                             has_standard_roles = 0   
        #             if has_standard_roles == 1:
        #                 user_id.write({'additional_roles':False,
        #                                 'role_type':'standard_user' })
        #             elif has_standard_roles == 2:
        #                 self.env.cr.execute('update res_users set role_type=\'admin_user\',count_of_additional_roles=%s where id=%s'%(count_of_additional_roles,user_id.id))
        #             else:
        #                 self.env.cr.execute('update res_users set role_type=\'multirole_user\',count_of_additional_roles=%s where id=%s'%(count_of_additional_roles,user_id.id))

        # print 'n\n\n\n\n\n\n\n\nn\n\n\n\n\n\\n\n\nn\n\n\n+++++  '   

















         



    # _columns = {
    #     'department_id': fields.many2one('hr.department','Department', readonly=True),
    #     'sector_id':fields.many2one('hr.department', 'Sector', readonly=True),
    #     'job_id':fields.many2one('hr.job','Job', readonly=True),        
    #     'project_allowed_departments':fields.many2many('hr.department', 'res_users_project_department_rel', 'uid', 'depid', 'Project Allowed Departments'),
    #     'budget_allowed_departments':fields.many2many('hr.department', 'res_users_budget_department_rel', 'uid', 'depid', 'Budget Allowed Departments'),
    #         'delivery_allowed_departments':fields.many2many('hr.department', 'res_users_delivery_department_rel', 'uid', 'depid', 'Delivery Allowed Departments'),
    #     'hr_allowed_departments':fields.many2many('hr.department', 'res_users_hr_department_rel', 'uid', 'depid', 'Hr Allowed Departments'),
    #     'helpdesk_allowed_departments':fields.many2many('hr.department', 'res_users_helpdesk_department_rel', 'uid', 'depid', 'Helpdesk Allowed Departments'),
    #     'tender_allowed_departments':fields.many2many('hr.department', 'res_users_tender_department_rel', 'uid', 'depid', 'Tender Allowed Departments'),
    #     'archive_allowed_departments':fields.many2many('hr.department', 'res_users_archive_department_rel', 'uid', 'depid', 'Archive Allowed Departments'),
    #     'allowed_departments':fields.many2many('hr.department', 'res_users_department_rel', 'uid', 'depid', 'Allowed Departments'),
    #     'purchase_allowed_departments':fields.many2many('hr.department', 'res_users_purchase_department_rel', 'uid', 'depid', 'Purchase Allowed Departments'),
    #     'asset_lease_allowed_departments':fields.many2many('hr.department', 'res_users_asset_lease_rel', 'uid', 'depid', 'Asset Lease Allowed Departments'),
    #     'payment_request_departments':fields.many2many('hr.department', 'res_users_payment_request_rel', 'uid', 'depid', 'Payment_Request Allowed Departments'),
    #     'loans_request_allowed_departments':fields.many2many('hr.department', 'res_users_loans_request_rel', 'uid', 'depid', 'Loans Request Allowed Departments'),
    # }
    
    
    
    # def regulation_confirm_employee_ids(self):
    #     model_obj = openerp.pooler.get_pool(cr.dbname).get('ir.model.data')
    #     group_id = model_obj.get_object_reference('nomin_archive', 'group_archive_document_see1')
    #     print '\n\n\nTEEEE'
    #     if group_id:
    #         user_ids=self.sudo().search([('groups_id','=',group_id[1])])
    #         return user_ids

#     def odoo_session_gc(self,cr,uid):
#         ''' Odoo session clear '''
#         import os 
#         from os import listdir
#         from os.path import join, isfile, getmtime

#         d1 = datetime.now()
#         session_dir = openerp.tools.config.session_dir
#         files = [f for f in listdir(session_dir) if isfile(join(session_dir, f))]
#         total_session_files = len(files)
#         total_delete = 0
#         last_week = time.time() - SESSION_LIFETIME
#         for fname in files:
#             fpath = join(session_dir, fname)
#             try:
#                 if getmtime(fpath) < last_week:
#                     os.unlink(fpath)
#                     total_delete += 1
#             except OSError:
#                 pass

#         duration = datetime.now() - d1
#         _logger.info("Session clear action success. Total %s session cleared and %s session still there. (duration: %s)" %
#             (total_delete, total_session_files - total_delete, '%sm%ss' % divmod(duration.days * 86400 + duration.seconds, 60)))
#         request.env.cr.execute("""delete from ir_attachment where name like '%.assets_backend.js' """)
#         request.env.cr.commit()
#         return True




# STATE_SELECTION = [
#         ('draft','Draft'),
#         ('confirmed','Confirmed'),
#     ]
        
# class add_user_followers(models.Model):
#     _name = 'add.user.followers'
#     _description = 'Add User Followers'
#     _table = "add_user_followers"
#     _inherit = ['mail.thread', 'ir.needaction_mixin']
#     _order = "id desc"
    
#     old_user_id = fields.Many2one('res.users', string='Old User', required=True, readonly=True, states={'draft': [('readonly', False)]}, track_visibility='always')
#     old_user_department_id = fields.Many2one('hr.department', string='Old User Department', readonly=True, states={'draft': [('readonly', False)]})
#     add_users = fields.Many2many(comodel_name='res.users', string='Add Users', required=True, readonly=True, states={'draft': [('readonly', False)]})
#     state = fields.Selection(STATE_SELECTION, string='State', readonly=True, default='draft', track_visibility='always')
#     note = fields.Text(string='Note',readonly=True, states={'draft': [('readonly', False)]})
    
#     @api.multi
#     def unlink(self):
#         for order in self:
#             if order.state != 'draft':
#                 raise UserError(_('You can only delete draft budget!'))
#         return super(add_user_followers, self).unlink()
    
    
#     @api.onchange('old_user_id')
#     def onchange_old_user(self):
#         if self.old_user_id and self.old_user_id.department_id:
#             self.update({'old_user_department_id':self.old_user_id.department_id.id})
        
#     @api.multi
#     def action_cancel(self):
#         if self.old_user_id and self.add_users:
#             if not self.old_user_id.partner_id:
#                 raise osv.except_osv((u'Warning !'), (u"Холбоотой харилцагч байхгүй байна!"))
            
#             records = self.env['mail.followers'].search([('partner_id','=',self.old_user_id.partner_id.id)])
#             count = 1
#             for rec in records:
#                 for user in self.add_users:
#                     if not user.partner_id:
#                         raise osv.except_osv((u'Warning !'), (u"%s хэрэглэгч дээр Холбоотой харилцагч байхгүй байна!"%(user.name)))
#                     is_exists = self.env['mail.followers'].search([('res_model','=', rec.res_model),('res_id','=',rec.res_id),('partner_id','=',user.partner_id.id)])
#                     if is_exists:
#                         for ex in is_exists:
#                             ex.unlink()
#                 count += 1
#         return self.write({'state':'draft', 'note':'Нийт %s ширхэг бүртгэлтэй бичлэгүүд дээрээс дээрх хэрэглэгч хасагдлаа.'%(str(count))})
    
    
#     @api.multi
#     def confirm(self):
#         if self.old_user_id and self.add_users:
#             if not self.old_user_id.partner_id:
#                 raise osv.except_osv((u'Warning !'), (u"Холбоотой харилцагч байхгүй байна!"))
            
#             records = self.env['mail.followers'].search([('partner_id','=',self.old_user_id.partner_id.id)])
#             count = 1
#             for rec in records:
#                 for user in self.add_users:
#                     if not user.partner_id:
#                         raise osv.except_osv((u'Warning !'), (u"%s хэрэглэгч дээр Холбоотой харилцагч байхгүй байна!"%(user.name)))
#                     is_exists = self.env['mail.followers'].search([('res_model','=', rec.res_model),('res_id','=',rec.res_id),('partner_id','=',user.partner_id.id)])
#                     if not is_exists:
#                         rec.copy(default={'partner_id': user.partner_id.id})
#                 count += 1
#         return self.write({'state':'confirmed', 'note':'Нийт %s ширхэг бүртгэлтэй бичлэгүүд дээр дээрх хэрэглэгч нэмэгдлээ.'%(str(count))})


# # class ResGroups1(models.Model):
# #     _inherit = "res.groups"
    


