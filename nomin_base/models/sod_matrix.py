# # -*- coding: utf-8 -*-

# from openerp import tools
# import math
# import openerp.tools
# import openerp.netsvc
# from openerp import SUPERUSER_ID #
# from openerp import tools, api, models #

# import sys
# import logging

# import time

# from datetime import timedelta
# from datetime import date,datetime

# import dateutil.relativedelta as relativedelta  

# from dateutil.parser import *
# from openerp.tools.translate import _
# import re
# from openerp import models, fields

# import openerp.netsvc as netsvc
# from openerp.exceptions import UserError, ValidationError
# from openerp.osv import expression

# from openerp.http import request
# import requests 
# import json
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import socket
import re
from lxml import etree
from requests.auth import HTTPBasicAuth
from odoo import SUPERUSER_ID, models
# from . import openerp.exceptions
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import float_is_zero
from odoo.tools import float_compare, float_round
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, ValidationError
class SodActivityName(models.Model):
    _name = 'sod.activity.name'
    _description = "activity"

    name = fields.Char('Үйлдлийн нэр')



class SodActivity(models.Model):
    _name = 'sod.activity'
    #_inherit = 'mail.thread'
    _description = "Hr system role"

    state_id = fields.Many2one('sod.state','Designer')
    name_id = fields.Many2one('sod.activity.name','Үйлдлийн нэр')
    name = fields.Char('Procedure name')
    type = fields.Selection([
            ('button',u'Товч'),
            ('modify',u'Өөрчлөх үйлдэл'),
            ], u'Type', track_visibility='always', default = 'button')
    python = fields.Text('Python')






class SodWorkflowGroupLine(models.Model):
    _name = 'sod.workflow.group.line'
    #_inherit = 'mail.thread'
    _description = "Sod workflow group line"
    _order = "level_number"

    line_id = fields.Many2one('sod.workflow.line','Workflow line')


    level_number = fields.Integer('Түвшингийн дугаар')
    group_id = fields.Many2one('res.groups', string='Group')
    exclude = fields.Boolean('Exclude')
    department_id = fields.Many2one('hr.department',string='Хэлтэс')


    # #@api.multi
    def write(self, vals):
        if self.line_id:
            if vals.get('level_number'):            
                if (self.level_number != vals.get('level_number')):             
                    before_level_number= self.level_number
                    after_level_number = vals.get('level_number')
                    message= str(self.line_id.id) + " дугаартай мөрийн " + str(before_level_number)+ " түвшингийн дугаарыг " + str(after_level_number) + " болгон өөрчлөв "
                    self.line_id.name_id.message_post(message) 
            if vals.get('group_id'):            
                if (self.group_id != vals.get('group_id')):             
                    before_group_id= self.group_id
                    after_group_id = vals.get('group_id')
                    message= str(self.line_id.id) + " дугаартай мөрийн  " + str(self.level_number) + " түвшингийн дугаартай мөрийн " + str(before_group_id.category_id.name) + '/' + str(before_group_id.name)+ " группийг " + str(after_group_id) + " -id тай группээр " + " солив "
                    self.line_id.name_id.message_post(message) 
            if vals.get('department_id'):            
                if (self.department_id != vals.get('department_id')):             
                    before_department_id= self.department_id
                    after_department_id = vals.get('department_id')
                    message= str(self.line_id.id) + " дугаартай мөрийн  " + str(self.level_number) + " түвшингийн дугаартай мөрийн " + str(before_department_id.name)+ " хэлтсийг " + str(after_department_id) + " -id тай хэлтсээр " + " солив "
                    self.line_id.name_id.message_post(message)  
        result = super(SodWorkflowGroupLine, self).write(vals)
        return result


    

class SodWorkflowLine(models.Model):
    _name = 'sod.workflow.line'
    #_inherit = 'mail.thread'
    _description = "Sod workflow line"

    name_id = fields.Many2one('sod.workflow.name','Workflow')


    department_ids = fields.Many2many('hr.department', 'hr_department_workflow_ref', 'line_id', 'department_id', string=u'Хэлтэсүүд', required=True)
    group_id = fields.Many2one('res.groups', string='Group')
    group_ids = fields.One2many('sod.workflow.group.line', 'line_id', string='Workflow groups')
    user_ids = fields.Many2many('res.users' , string='Users')
  
#
    
    #@api.multi
    def write(self, vals):

      
    
        hasah = []
        nemeh = []


        if vals.get('department_ids',False) and self.department_ids:
            
            if (self.department_ids != vals.get('department_ids')):
               
                before_department_ids= set(self.department_ids.ids)

                after_department_ids = set(tuple(vals.get('department_ids')[0][2]))

             
                hasah = list(before_department_ids - after_department_ids)
                if hasah:  
                    

                    self.name_id.write({'temp_department_ids':[(6,0,hasah)]})

                    str1 =''
                    str2 =','
                    len1 = len(self.name_id.temp_department_ids)
#
                    counter = 0
                    for department in self.name_id.temp_department_ids:
                        counter += 1
                        if len1 == counter:
                            str2=''


                        str1 = str1 + '\"'+str(department.name) +'\"'+str2


                    message= str(self.id)+ " дугаарын id-тай мөрнөөс" + str(str1) + " хэлтэс хасагдав"



                else:
                
                    nemeh = list(after_department_ids - before_department_ids)
#
                    self.name_id.write({'temp_add_department_ids':[(6,0,nemeh)]})

                    str3 =''
                    str4 =','
                    
                    len2 = len(self.name_id.temp_add_department_ids)
                    counter = 0
                    for department in self.name_id.temp_add_department_ids:
                        counter += 1
                        if len2 == counter:
                            str4=''
                        str3 = str3 + '\"'+str(department.name) +'\"'+str4
 #
                    message= str(self.id)+ " дугаарын id-тай мөрөнд" +str(str3) + " хэлтэс нэмэгдэв"
        

                self.name_id.message_post(message)  
        result = super(SodWorkflowLine, self).write(vals)
        return result

    
    #@api.multi
    def _check_department(self):
        normal = True
        for current_self in self:
            if current_self.name_id:
                line_ids = current_self.env['sod.workflow.line'].search([('name_id','=',current_self.name_id.id)])
                for line in line_ids:
                    if line != current_self:
                        for department_id in line.department_ids:
                            for current_dep_id in current_self.department_ids: 
                                if current_dep_id == department_id:
                                    normal = False
        
        return normal

    # _constraints = [
    #     (_check_department, u'Хэлтэс давхардуулж болохгүй', ['department_ids']),
    # ]



class SodWorkflowName(models.Model):
    _name = 'sod.workflow.name'
    #_inherit = 'mail.thread'
    _description = "Hr system role"


    type = fields.Selection([
            ('get_one_user',u'Заагдсан хэрэглэгч авах'),
            ('search_in_group',u'Групп доторх хайлт'),
            ('search_in_dynamic_group',u'Динамик групп доторх хайлт'),
            ('hierarchy_level_up',u'Хаaяраки шатлал өгсөх'),
            ('get_users_related_to_department',u'Хэлтэс дээрх заагдсан хэрэглэгч авах'),
            ('search_in_department_group',u'Зөвшөөрөгдсөн хэлтэс бүхий групп доторх хайлт'),
            
            ], u'Төрөл', required=True ,track_vissiblity='onchange')
    name = fields.Char('Урсгалын нэр',track_vissiblity='onchange')
    code = fields.Char('Урсгалын код',track_vissiblity='onchange')
    active = fields.Boolean(string='Active', default=True)
    line_ids = fields.One2many('sod.workflow.line', 'name_id', string='Workflows')
    line_ids_for_users = fields.One2many('sod.workflow.line', 'name_id', string='Workflows')
    line_ids_for_hierarchy = fields.One2many('sod.workflow.line', 'name_id', string='Workflows')
    group_id = fields.Many2one('res.groups', string='Group')
    # button_clickers = fields.Many2many('res.users',string='Товч дарах хэрэглэгчид')
    department_id = fields.Many2one('hr.department',string='Хэлтэс')
    sod_msg = fields.Char('Алдааны мэдээлэл')
    user_id = fields.Many2one('res.users', string='Хэрэглэгч',default = 1)
    employee_id = fields.Many2one('hr.employee', string='Ажилтан',default = 215)
    user_ids = fields.Many2many('res.users',string='Хэрэглэгчид',track_vissiblity='onchange')
    has_follower = fields.Boolean('Дагагчаар нэмэх эсэх',track_vissiblity='onchange')
    skip_workflow = fields.Boolean('Урсгал алгасах эсэх',default=False,track_vissiblity='onchange')
    temp_department_ids= fields.Many2many('hr.department',string='хасалт хийгдэж байгаа хэлтэсүүд')
    # temp_add_department_ids= fields.Many2many('hr.department',string='хасалт хийгдэж байгаа хэлтэсүүд')
    i_m_support_user= fields.Boolean('support user'  , default=False)

    

    
    
    is_config_allowed_resource = fields.Boolean(string="Тохиргооны цонхны хандах нөөцөөс тохируулах",default=False ,track_vissiblity='always')
    allowed_resources = fields.Many2many('ir.model.fields',string = 'Хандах нөөц', domain="[('model','=','res.users'),('name','like','allowed')]" ,track_visibility='always' )


    #@api.multi
    def write(self, vals):

        if vals.get('name'):            
            if (self.name != vals.get('name')):             
                before_name= self.name
                after_name = vals.get('name')
                message= str(before_name)+ " урсгалын нэрийг " + str(after_name) + " болгон өөрчлөв "
                self.message_post(message)

        if vals.get('code'):            
            if (self.code != vals.get('code')):             
                before_code= self.code
                after_code = vals.get('code')
                message= str(before_code)+ " урсгалын нэрийг " + str(after_code) + " болгон өөрчлөв "
                self.message_post(message)

        if vals.get('type'):            
            if (self.type != vals.get('type')):             
                before_type= self.type
                after_type = vals.get('type')
                message= str(before_type)+ " урсгалын төрлийг " + str(after_type) + " болгон өөрчлөв "
                self.message_post(message) 
        
         
        result = super(SodWorkflowName, self).write(vals)
        return result
    
    #@api.multi
    def test_button(self):

        button_clickers = {}
        self.write(button_clickers)


        if self.department_id:
            button_clickers = self.get_nominees(self.department_id,self.user_id)
            
            if button_clickers:
                self.write(button_clickers)


    #@api.multi
    def test_button_for_employees(self):

        button_clickers = {}
        self.write(button_clickers)

        if self.department_id:
            
            button_clickers = self.get_nominees(self.department_id,self.employee_id)
            
            if button_clickers:
                self.write(button_clickers)



#

    #@api.multi
    def get_nominees(self,department_id,employee_id):

        return_values={}
        button_clickers = []
        users = ''
        user_id = False

        if employee_id:

            if type(employee_id).__name__ == 'hr.employee':
                
                if not department_id:
                    if employee_id: 
                        department_id = employee_id.department_id

                    elif self.env.user.department_id:
                        department_id = self.env.user.department_id

                    else:
                        return_values.update({'button_clickers':[(6,0,button_clickers)],
                            'sod_msg':'Хэлтэс тохируулагдаагүй байна',
                            'has_follower':self.has_follower,
                            'skip_workflow':self.skip_workflow,
                            })

                        return return_values

                user_id = employee_id.user_id 

            else:
                user_id = employee_id

        else:
            user_id = self.env.user


        if not department_id:        
            return_values.update({'button_clickers':[(6,0,button_clickers)],
                'sod_msg':u'Ajiltan heltesgvi baina!',
                'has_follower':self.has_follower,
                'skip_workflow':self.skip_workflow,
                })
            return return_values  

        i_m_support_user = False
        if self.env.user.role_type == 'support_user':
            i_m_support_user = True
        
        if self.type == 'search_in_group':
            remove_users=[]
            # confirm_user_ids=button_clickers.id

            for user in self.group_id.users:
                # if i_m_support_user and user.role_type == 'support_user':
                #         button_clickers.append(user.id)
                #         users += ' -- ' + user.name
                # else:               
                #     button_clickers.append(user.id)
                #     users += ' -- ' + user.name


                if i_m_support_user:
                    button_clickers.append(user.id)
                    users += ' -- ' + user.name
                elif user.role_type != 'support_user':               
                    button_clickers.append(user.id)
                    users += ' -- ' + user.name

                
            if button_clickers == []:
                return_values.update({'button_clickers':[(6,0,button_clickers)],
                    'sod_msg':'Товч дарах хэрэглэгч олдсонгүй!',
                    'has_follower':self.has_follower,
                    'skip_workflow':self.skip_workflow,
                    })
            else:
                return_values.update({'button_clickers':[(6,0,button_clickers)],
                    'sod_msg':u'Товч дарах боломжит хэрэглэгчид: ' + users,
                    'has_follower':self.has_follower,
                    'skip_workflow':self.skip_workflow,
                    })
            
            return return_values

        allowed_resource = self.group_id.allowed_resource
        if self.is_config_allowed_resource:
            # print '\n\n\n\n check aaaaaaaaaaaa' , self , self.is_config_allowed_resource
            allowed_resource = self.allowed_resources
        if self.type == 'search_in_department_group' and self.group_id.allowed_resource:

            if allowed_resource:            

                for user in self.group_id.users:

                    # if i_m_support_user and user.role_type == 'support_user':
                    #     button_clickers.append(user.id)
                    #     users += ' -- ' + user.name
                    # elif  :
                    #     button_clickers.append(user.id)
                    #     users += ' -- ' + user.name
                

                    deps = self.env['hr.department'].search([('id','in',user.get_allowed_department_ids(self.group_id.allowed_resource.name))])
                    user_dep_set = set(deps.ids)           
                    if list(user_dep_set.intersection([department_id.id])):
                        if i_m_support_user:
                            button_clickers.append(user.id)
                            users += ' -- ' + user.name
                        elif user.role_type != 'support_user':
                            button_clickers.append(user.id)
                            users += ' -- ' + user.name

                        

                if button_clickers == []:
                    return_values.update({'button_clickers':[(6,0,button_clickers)],
                        'sod_msg':'Товч дарах хэрэглэгч олдсонгүй!',
                        'has_follower':self.has_follower,
                        'skip_workflow':self.skip_workflow,
                        })

                else:
                    return_values.update({'button_clickers':[(6,0,button_clickers)],
                        'sod_msg':u'Товч дарах боломжит хэрэглэгчид: ' + users,
                        'has_follower':self.has_follower,
                        'skip_workflow':self.skip_workflow,
                        })
                    
            else:
                
                return_values.update({'button_clickers':[],
                    'sod_msg':self.group_id.name + ' гэсэн группэд зөвшөөрөгдсөн нөөц тохируулагдаагүй байна',
                    'has_follower':self.has_follower,
                    'skip_workflow':self.skip_workflow,
                    })


            return return_values


        elif self.type == 'get_one_user':
            for user in self.user_ids:

                button_clickers.append(user.id)
                users += ' -- ' + user.name
                

            if button_clickers == []:
                return_values.update({'button_clickers':[(6,0,button_clickers)],
                    'sod_msg':'Товч дарах хэрэглэгч олдсонгүй!',
                    'has_follower':self.has_follower,
                    'skip_workflow':self.skip_workflow,
                    })
            else:
                return_values.update({'button_clickers':[(6,0,button_clickers)],
                    'sod_msg':'Товч дарах боломжит хэрэглэгчид: ' + users,
                    'has_follower':self.has_follower,
                    'skip_workflow':self.skip_workflow,
                    })

            return return_values
        
        elif self.type == 'get_users_related_to_department':

            line_id = self.env['sod.workflow.line'].search([('department_ids','in',department_id.id),('name_id','=',self.id)])
            
            if not line_id:

                return_values.update({'button_clickers':[(6,0,button_clickers)],
                    'sod_msg':u'Урсгал дотор хэлтэс тохируулагдаагүй байна!',
                    'has_follower':self.has_follower,
                    'skip_workflow':self.skip_workflow,
                    })
                return return_values

            for user in line_id.user_ids:
                
                if i_m_support_user:
                    button_clickers.append(user.id)
                    users += ' -- ' + user.name
                elif user.role_type != 'support_user':
                    button_clickers.append(user.id)
                    users += ' -- ' + user.name



            if button_clickers == []:
                return_values.update({'button_clickers':[(6,0,button_clickers)],
                    'sod_msg':'Товч дарах хэрэглэгч олдсонгүй!',
                    'has_follower':self.has_follower,
                    'skip_workflow':self.skip_workflow,
                    })

            else:
                return_values.update({'button_clickers':[(6,0,button_clickers)],
                    'sod_msg':'Товч дарах боломжит хэрэглэгчид: ' + users,
                    'has_follower':self.has_follower,
                    'skip_workflow':self.skip_workflow,
                    })
            
            return return_values

            

        elif self.type == 'search_in_dynamic_group':

            line_id = self.env['sod.workflow.line'].search([('department_ids','in',department_id.id),('name_id','=',self.id)])
            
            if not line_id:

                return_values.update({'button_clickers':[(6,0,button_clickers)],
                    'sod_msg':u'Урсгал дотор хэлтэс тохируулагдаагүй байна!',
                    'has_follower':self.has_follower,
                    'skip_workflow':self.skip_workflow,
                    })
                return return_values


            if not line_id.group_id:

                return_values.update({'button_clickers':[(6,0,button_clickers)],
                    'sod_msg':u'Урсгал дотор групп тохируулагдаагүй байна!',
                    'has_follower':self.has_follower,
                    'skip_workflow':self.skip_workflow,
                    })
                return return_values

            line = line_id.group_id
            if self.is_config_allowed_resource:
                line = line_id.name_id
            if not line.allowed_resource:

                return_values.update({'button_clickers':[(6,0,button_clickers)],
                    'sod_msg':line_id.group_id.name + u' гэсэн группэд зөвшөөрөгдсөн нөөц тохируулагдаагүй байна',
                    'has_follower':self.has_follower,
                    'skip_workflow':self.skip_workflow,
                    })
                return return_values


            for user in line.users:
                
                deps = self.env['hr.department'].search([('id','in',user.get_allowed_department_ids(line.allowed_resource.name))])
                user_dep_set = set(deps.ids)                
                if list(user_dep_set.intersection([department_id.id])):
                    button_clickers.append(user.id)
                    users += ' -- ' + user.name

            if button_clickers == []:
                return_values.update({'button_clickers':[(6,0,button_clickers)],
                    'sod_msg':'Товч дарах хэрэглэгч олдсонгүй!',
                    'has_follower':self.has_follower,
                    'skip_workflow':self.skip_workflow,
                    })

            else:
                return_values.update({'button_clickers':[(6,0,button_clickers)],
                    'sod_msg':u'Товч дарах боломжит хэрэглэгчид:' + users,
                    'has_follower':self.has_follower,
                    'skip_workflow':self.skip_workflow,
                    })

            return return_values

            
        elif self.type == 'hierarchy_level_up':

            return self.calculate_hierarchy_level(department_id,user_id,i_m_support_user)
        

    #@api.multi
    def calculate_hierarchy_level(self,department_id,user_id,i_m_support_user):

        return_values={}
        temp_department_id = department_id
        logged_in_user_level = 0
        
        button_clickers = []
        
        

        max_level = 0

        line_id = self.env['sod.workflow.line'].search([('department_ids','in',department_id.id),('name_id','=',self.id)])
        

        if not line_id:
            return_values.update({'button_clickers':[(6,0,button_clickers)],
                'sod_msg':u'Урсгал дотор хэлтэс тохируулагдаагүй байна!',
                'has_follower':self.has_follower,
                'skip_workflow':self.skip_workflow,
                })
            return return_values

 
        for level in line_id.group_ids:

            if max_level <= level.level_number:
                max_level = level.level_number

            if not level.group_id:
                return_values.update({'button_clickers':[],
                    'sod_msg':'%s idтай %s урсгал тохиргоонд тухайн хэлтэсийн урсгалын дараалал /групп/ хоосон байна /дараалалын дугаар %s /' %(line_id.name_id,line_id.name_id.name,line_id),
                    'has_follower':self.has_follower,
                    'skip_workflow':self.skip_workflow,
                    })
                return return_values
            #print '\n\nlevelgroup',line_id,line_id.name_id,level,level.group_id,level.group_id.name, '\n\n'

            if not level.group_id.allowed_resource:
                
                return_values.update({'button_clickers':[],
                    'sod_msg':level.group_id.name + ' гэсэн группэд зөвшөөрөгдсөн нөөц тохируулагдаагүй байна',
                    'has_follower':self.has_follower,
                    'skip_workflow':self.skip_workflow,
                    })
                return return_values

            level_group = level.group_id
            if self.is_config_allowed_resource:
                level_group = level.line_id.name_id
            for user in level.group_id.users:

                
                
                
                deps = self.env['hr.department'].search([('id','in',user.get_allowed_department_ids(level.group_id.allowed_resource.name))])
                
                user_dep_set = set(deps.ids)

                if level.exclude and level.department_id:

                    if list(user_dep_set.intersection([department_id.id])):
                        if not list(user_dep_set.intersection([level.department_id.id])):
                            button_clickers.append(user.id)

                else:
                    
                    if level.department_id:
                        temp_department_id = level.department_id

                    if list(user_dep_set.intersection([temp_department_id.id])):
                        if user.id == user_id.id: 
                            logged_in_user_level = level.level_number
                        button_clickers.append(user.id)



            if button_clickers == []:
                return {'button_clickers':[(6,0,button_clickers)],
                    'sod_msg':str(level.level_number) + u'-р алхам дээр товч дарах хэрэглэгч олдсонгүй.',

                    'has_follower':self.has_follower,
                    'skip_workflow':self.skip_workflow,
                    }



        button_clickers = []
        users = ''

        if max_level <= logged_in_user_level:
            return_values.update({'button_clickers':[(6,0,button_clickers)],
                'sod_msg':u'Та хамгийн өндөр албан тушаалтан тул таныг батлах хүн байхгүй!',
                'has_follower':self.has_follower,
                'skip_workflow':self.skip_workflow,
                })
            return return_values



        approver_level = logged_in_user_level + 1
        temp_department_id = department_id

        group_line_ids = self.env['sod.workflow.group.line'].search([('level_number','=',approver_level),('line_id','=',line_id.id)])





        for line in group_line_ids:

            line_group = line.group_id
            if self.is_config_allowed_resource: 
                line_group = line.line_id.name_id
            if not line_group.allowed_resource:
                
                return_values.update({'button_clickers':[],
                    'sod_msg':line.group_id.name + ' гэсэн группэд зөвшөөрөгдсөн нөөц тохируулагдаагүй байна',
                    'has_follower':self.has_follower,
                    'skip_workflow':self.skip_workflow,
                    })
                return return_values


            for user in line_group.users:
                deps = self.env['hr.department'].search([('id','in',user.get_allowed_department_ids(line_group.allowed_resource.name))])
                user_dep_set = set(deps.ids) 


                if line.exclude and line.department_id:
                    if list(user_dep_set.intersection([department_id.id])):
                        #print 'user333',user.name
                        if not list(user_dep_set.intersection([line.department_id.id])):
                            if i_m_support_user:
                                button_clickers.append(user.id)
                                users += ' -- ' + user.name
                            elif user.role_type != 'support_user':
                                button_clickers.append(user.id)
                                users += ' -- ' + user.name


                            # button_clickers.append(user.id)
                            # users += ' -- ' + user.name

                else:
                    if line.department_id:
                        temp_department_id = line.department_id                                
                    if list(user_dep_set.intersection([temp_department_id.id])):
                        #print 'user3334',user.name
                        if i_m_support_user:
                            button_clickers.append(user.id)
                            users += ' -- ' + user.name
                        elif user.role_type != 'support_user':
                            button_clickers.append(user.id)
                            users += ' -- ' + user.name

                        # button_clickers.append(user.id)
                        # users += ' -- ' + user.name


        return_values.update({'button_clickers':[(6,0,button_clickers)],
            'sod_msg':str(approver_level) + u'-р алхам дээрх хэрэглэгчид: ' + users,
            'has_follower':self.has_follower,
            'skip_workflow':self.skip_workflow,
            })
        return return_values







class SodWorkflow(models.Model):
    _name = 'sod.workflow'
    #_inherit = 'mail.thread'
    _description = "Hr system role"
    _order = "activity_id"

    #@api.multi
    def name_get(self):
        result = []
        for field in self:
            name = field.workflow_name
            result.append((field.id, name))
        return result


    designer_id = fields.Many2one('sod.designer','Designer')

    workflow_name = fields.Many2one('sod.workflow.name','Урсгалын нэр')
    code = fields.Char('Урсгалын код')
    type = fields.Char('Урсгалын төрөл')
    activity_id = fields.Many2one('sod.state','Хийх үйлдлийн нэр')
    custom_number = fields.Char('Custom number')
    custom_name = fields.Char('Custom name')


    @api.onchange('workflow_name')
    def onchange_workflow_name(self):

        if self.workflow_name: 
            type = u'Хаaяраки шатлал өгсөх'
            if self.workflow_name.type == 'get_one_user':
                type = u'Заагдсан хэрэглэгч авах'
            if self.workflow_name.type == 'get_users_related_to_department':
                type = u'Хэлтэс дээрх заагдсан хэрэглэгч авах'
            if self.workflow_name.type == 'search_in_group':
                type = u'Групп доторх хайлт'
            if self.workflow_name.type == 'search_in_department_group':
                type = u'Зөвшөөрөгдсөн хэлтэс бүхий групп доторх хайлт'
            if self.workflow_name.type == 'search_in_dynamic_group':
                type = u'Динамик групп доторх хайлт'
            self.update({
                'code': self.workflow_name.code or False,
                'type': type,
            })




class SodFieldName(models.Model):
    _name = 'sod.field.name'
    #_inherit = 'mail.thread'
    _description = "Sod field name"

    name = fields.Char('Талбарын нэр')
    name_in_english = fields.Char(string = 'Field name')
    field_type = fields.Selection([
            ('many2one',u'Many2one'),
            ('char',u'Char'),
            ('selection',u'Selection'),
            ('compute_char',u'ComputeChar'),
            ], u'Field type', track_visibility='always',required=True)


class SodField(models.Model):
    _name = 'sod.field'
    #_inherit = 'mail.thread'

    _description = "SOD field"
    _order = "location,field_type,field_name_in_english"


    #@api.multi
    def name_get(self):
        result = []
        for field in self:
            name = field.field_name_in_english
            result.append((field.id, name))
        return result


    
    designer_id = fields.Many2one('sod.designer','Designer')
    state = fields.Selection([
            ('draft',u'Ноорог'),
            ('verify',u' Хянах'),
            ('approve',u'Батлах'),
            ], u'State', track_visibility='always', default = 'draft')
    field_name = fields.Many2one('sod.field.name','Талбарын нэр',required=True)
    field_name_in_english = fields.Char(string = 'Талбарын Англи нэр')
    field_type = fields.Selection([
            ('many2one',u'Many2one'),
            ('char',u'Char'),
            ('selection',u'Selection'),
            ('compute_char',u'ComputeChar'),
            ], u'Талбарын төрөл', track_visibility='always',required=True)
    has_default_value = fields.Boolean('Default-тай эсэх')
                
    location = fields.Selection([
            ('l1',u'Left 1'),
            ('l2',u'Left 2'),
            ('l3',u'Left 3'),
            ('l4',u'Left 4'),
            ('l5',u'Left 5'),
            ('l6',u'Left 6'),
            ('l7',u'Left 7'),
            ('l8',u'Left 8'),   
            ('l9',u'Left 9'),            

            ('r1',u'Right 1'),
            ('r2',u'Right 2'),
            ('r3',u'Right 3'),
            ('r4',u'Right 4'),
            ('r5',u'Right 5'),
            ('r6',u'Right 6'),
            ('r7',u'Right 7'),
            ('r8',u'Right 8'),   
            ('r9',u'Right 9'),  

            ('invisible',u'Invisible'),
            ], u'Талбарын байршил', track_visibility='always',required=True)

    has_attrs = fields.Boolean('Attrs-тай эсэх')
    tree_view = fields.Integer('Мод харагдац')
    group_by = fields.Integer('Групп')
    filter_by = fields.Selection([
            ('default',u'1 default'),
            ('two_default',u'2 default'),
            ('one',u'1'),
            ('two',u'2'),
            ('three',u'3'),
            ('four',u'4'),
            ('five',u'5'),
            ('six',u'6'),
            ('seven',u'7'),
            ], u'Шүүлтүүр')
    search_by = fields.Integer('Хайлт')
    managerial_group_id = fields.Many2many('res.groups',string = 'Өгөгдсөн нөөцтэй ажиллах групп')
    python = fields.Text('Python')



    @api.onchange('field_type','managerial_group_id')
    def onchange_field_type(self):
        if self.field_type != 'many2one':
            self.managerial_group_id = False




    @api.onchange('field_name')
    def onchange_field_name(self):

        if self.field_name: 

            self.update({
                'field_name_in_english': self.field_name.name_in_english,
                'field_type': self.field_name.field_type,
            })

    



class SodStateName(models.Model):
    _name = 'sod.state.name'
    #_inherit = 'mail.thread'
    _description = "Hr system resource"


    type = fields.Selection([
            ('uv',u'uv - Урсгалтай үйдэлтэй төлөв'),
            ('vt',u'vt - Үйдэлтэй төлөв'),
            ('vi',u'vi - Үйлдэл хийх'),
            ('vd',u'vd - Үр дүн харах'),
            ('dt',u'dt'),
            ], u'Type', track_visibility='always', required=True)

    ident_resource_id = fields.Char('Ident Resource ID')
    code = fields.Char('Code')
    name = fields.Char('State name')
    workflow_is_allowed = fields.Boolean('Workflow is allowed')




class SodCategory(models.Model):
    _name = 'sod.category'
    #_inherit = 'mail.thread'
    _description = "Hr system resource"
    designer_id = fields.Many2one('sod.designer','Designer')

    sequence = fields.Integer(string = 'Дараалал')
    code = fields.Char('Code')
    name = fields.Char('Ангилал')
    reference_ids = fields.One2many('sod.reference', 'category_id', string='Fields')






class SodReference(models.Model):
    _name = 'sod.reference'
    #_inherit = 'mail.thread'

    _description = "SOD reference"
    # _order = "sequence"

    # sequence = fields.Integer(string = 'Дараалал')
    category_id = fields.Many2one('sod.category',string = 'Ангилалын нэр',required=True)
    element_id = fields.Many2one('sod.element',string = 'Ангилалын нэр',required=True)
    name = fields.Char(string = 'Нэр')
    code = fields.Char('Code')


class SodElement(models.Model):
    _name = 'sod.element'
    #_inherit = 'mail.thread'

    _description = "SOD reference"
    _order = "sequence"

    
    designer_id = fields.Many2one('sod.designer','Designer')


    sequence = fields.Integer(string = 'Дараалал')
    name = fields.Char(string = 'Үндсэн ангилал')
    reference_ids = fields.One2many('sod.reference', 'element_id', string='Fields')
    code = fields.Char('Code')





class SodState(models.Model):
    _name = 'sod.state'
    #_inherit = 'mail.thread'

    _description = "SOD state"
    _order = "sequence"


    #@api.multi
    def name_get(self):
        result = []
        for state in self:
            

            name = (state.name_id.type[:2]  + ' - ' if state.name_id.type else '') + state.name_id.name if state.name_id.type else ''
            if state.name_id.type[:2] == 'vi':
                name = state.name_id.name + ' товч дарах' if state.name_id.type else '' 

            if state.code:
                if state.name_id.type[:2] != 'vi':
                    name += ' %s' % (state.code,)
            result.append((state.id, name))
        return result

    
    designer_id = fields.Many2one('sod.designer','Designer')
    state = fields.Selection([
            ('draft',u'Ноорог'),
            ('verify',u' Хянах'),
            ('approve',u'Батлах'),
            ], u'State', track_visibility='always', default = 'draft')


    employee_id = fields.Many2one('hr.employee',string = 'Ажилтан')
    sequence = fields.Integer(string = 'Дараалал')
    name_id = fields.Many2one('sod.state.name',string = 'Төлөвийн нэр',required=True)
    code = fields.Char(string = 'Төлөвийн код')
    type = fields.Char(string = 'Төлөвийн төрөл')
    activity_ids = fields.One2many('sod.activity', 'state_id', string='Үйлдэлүүд')
    workflow_ids = fields.One2many('sod.workflow', 'activity_id', string='ttttt')
    # line_ids = fields.One2many('sod.matrix', 'state_id', string='Матриксууд')
    python = fields.Text('Товч харах дүрэм')
    state_ids = fields.Many2many('sod.state', 'state_id','activity_id', string='Үйлдэлүүд')
    python_for_activity = fields.Text('Товч дарахаар хийх үйлдэл')


    @api.onchange('name_id')
    def onchange_name_id(self):

        if self.name_id: 
            type = u'uv - Урсгалтай үйдэлтэй төлөв'
            if self.name_id.type == 'vt':
                type = u'vt - Үйдэлтэй төлөв'            
            if self.name_id.type == 'vi':
                type = u'vi - Үйлдэл хийх'
            if self.name_id.type == 'vd':
                type = u'vd - Үр дүн харах'
            self.update({
                'code': self.name_id.code,
                'type': type,
            })


    #@api.multi
    def write(self, vals):

        if vals.get('python',False) and self.python:
          
            if (self.python != vals.get('python')):
             
                before_python= self.python
              
                after_python = str(vals.get('python'))
               
                message= (before_python)+"кодийг"+ (after_python)+ "болгож өөрчлөв."

            self.designer_id.message_post(message)
        result = super(SodState, self).write(vals)



        if vals.get('parent_menu') or vals.get('menu_name'):
            self.name = self.parent_menu.name + ' => ' + self.menu_name
        return result




class SodDesigner(models.Model):
    _name = 'sod.designer'
    #_inherit = 'mail.thread'

    _description = "SOD Дизайнер"
    _order = "create_date desc"


    state = fields.Selection([
            ('draft',u'Ноорог'),
            ('verify',u'Хянах'),
            ('approve',u'Батлах'),
            ('codes_created',u'Код үүсгэгдсэн'),
            ], u'State', track_visibility='always', default = 'draft')

    name = fields.Char(string = 'Model name')
    module_name = fields.Many2one('ir.module.module',string = 'Module name')
    model_name = fields.Char(string = 'Model name',required=True)
    menu_name = fields.Char(string = 'Менюний Монгол нэр',required=True)
    parent_menu = fields.Many2one('ir.ui.menu',string = 'Эцэг меню',required=True)
    employee_id = fields.Many2one('hr.employee',string = 'Боловсруулсан ажилтан')
    verify_employee_id = fields.Many2one('hr.employee', string = 'Хянах ажилтан')
    approve_employee_id = fields.Many2one('hr.employee', string = 'Батлах ажилтан')
    admin_group_id = fields.Many2one('res.groups',string = 'Aдмин групп')#     set_employee_id = fields.Many2one('hr.employee',string = 'Set Employee')
    
    menu_dominant_group_id = fields.Many2one('res.groups',string = 'Цэсэн дээрх давуу эрхийн групп')#
    personal_group_id = fields.Many2one('res.groups',string = ' Цонхыг үүсгэх эрхийн групп')#

    menu_type = fields.Selection([
            ('ar',u'ar - Тохиргооны цонх'),
            ('md',u'md - Зохицуулагч ажилладаг цонх'),
            ('mr',u'mr - Менежер ажилладаг цонх'),
            ('pr_mr',u'pr_mr - Ажилтан ба менежерийн оролцоотой цонх'),
            ('pr_mr_md',u'pr_mr_md - Ажилтан, менежер, зохицуулагч ажилладаг цонх'),
            ], u'Төрөл (pr_mr_md_ar)', track_visibility='always', required=True)  

    field_ids = fields.One2many('sod.field', 'designer_id', string='Fields')

    state_ids = fields.One2many('sod.state', 'designer_id', string='States') 
    workflow_ids = fields.One2many('sod.workflow', 'designer_id', string='Workflows')
    category_ids = fields.One2many('sod.category', 'designer_id', string='Categories')
    element_ids = fields.One2many('sod.element', 'designer_id', string='Elements')
    matrix_ids = fields.One2many('sod.matrix', 'designer_id', string='Matrixes')
    


    #@api.multi
    def write(self, vals):

        result = super(SodDesigner, self).write(vals)

        
        if vals.get('parent_menu') or vals.get('menu_name'):
            self.name = self.parent_menu.name + ' => ' + self.menu_name
        return result



  
    # @api.one
    # def state_handler(self,current_state):

    #     object_id = self.env['sod.state'].search([('designer_id','=',self.id),('code','=',current_state)])

    #     if not object_id:
    #         return False

    #     if object_id.type[:2] not in ('vi','vd'):
    #         return False    # @api.one
    # def state_handler(self,current_state):

    #     object_id = self.env['sod.state'].search([('designer_id','=',self.id),('code','=',current_state)])

    #     if not object_id:
    #         return False

    #     if object_id.type[:2] not in ('vi','vd'):
    #         return False

    #     if object_id[0].python:
    #         exec(object_id[0].python)

    #     else:
    #         return False

    #     if object_id[0].python:
    #         exec(object_id[0].python)

    #     else:
    #         return False

    #hhh

    
    def workflow_handler(self,workflow_id,department_id,employee_id,res_id,next_state):


        
        result_values = {'button_clickers':[(6, 0,[])],'sod_msg':''}
        if workflow_id:

            object_id = self.env['sod.workflow'].search([('designer_id','=',self.id),('code','=',workflow_id.code)])
            if not object_id:
                return {'button_clickers':[(6, 0,[])],'sod_msg':u'SOD дизайнер дотор өгөгдсөн урсгалын мөрийг үүсгээгүй байна'}
                
            workflow_id_id = object_id[0].workflow_name
            if not workflow_id_id:
                return {'button_clickers':[(6, 0,[])],'sod_msg':u'SOD урсгал нь үүсгэгдээгүй байна'}
            #print '\n\n\n\n next_state line-1053',next_state
            next_state_id = self.env['sod.state'].search([('designer_id','=',self.id),('code','=',next_state)])


            if next_state_id.type[:2] != 'vd':
                
                result_values = workflow_id_id[0].get_nominees(department_id,employee_id)

            
            if result_values['button_clickers']:
                self.prepare_proactive_notification(result_values['button_clickers'][0][2],res_id,self.model_name)


            if self.model_name == 'hr.regulation' and result_values['sod_msg'] != '':
                if result_values['sod_msg'][0] == '1':
                    result_values = {'button_clickers':[(6, 0,[])],
                        'sod_msg':u'Тушаалын салбарыг боловсруулсан ажилтны зөвшөөрөгдсөн хэлтсүүд дотор нэмж өгөх хэрэгтэй!'
                        }

        return result_values
    
        
    # def workflow_handler(self,workflow_id,department_id,employee_id,res_id,next_state):


    #     print 'ssssssss2342333333',workflow_id,next_state
    #     result_values = {'button_clickers':[(6, 0,[])],'sod_msg':''}
    #     if workflow_id:

    #         object_id = self.env['sod.workflow'].search([('designer_id','=',self.id),('code','=',workflow_id.code)])
    #         if not object_id:
    #             return {'button_clickers':[(6, 0,[])],'sod_msg':u'SOD дизайнер дотор өгөгдсөн урсгалын мөрийг үүсгээгүй байна'}
                
    #         workflow_id_id = object_id[0].workflow_name
    #         if not workflow_id_id:
    #             return {'button_clickers':[(6, 0,[])],'sod_msg':u'SOD урсгал нь үүсгэгдээгүй байна'}
    #         next_state_id = self.env['sod.state'].search([('designer_id','=',self.id),('code','=',next_state)])

    # def workflow_handler_by_user(self,workflow_name,department_id,user_id):       
    #     object_id = self.env['sod.workflow'].search([('designer_id','=',self.id),('code','=',workflow_name)])
    #     if not object_id:
    #         return {'button_clickers':[],
    #             'sod_msg':u'SOD дизайнер дотор өгөгдсөн урсгалын мөрийг үүсгээгүй байна'
    #         }

    #         if next_state_id.type[:2] != 'vd':
    #             result_values = workflow_id_id[0].get_nominees(department_id,employee_id)
    #         self.prepare_proactive_notification(result_values['button_clickers'][0][2],res_id,self.model_name)


    #         if self.model_name == 'hr.regulation' and result_values['sod_msg'] != '':
    #             if result_values['sod_msg'][0] == '1':
    #                 result_values = {'button_clickers':[(6, 0,[])],
    #                     'sod_msg':u'Тушаалын салбарыг боловсруулсан ажилтны зөвшөөрөгдсөн хэлтсүүд дотор нэмж өгөх хэрэгтэй!'
    #                     }

    #     return result_values


    def is_nominee(self,object_id,target):

        if not object_id:
            return False

        query = """SELECT a.user_id from proactive_notification a
            inner join proactive_line b on b.notification_id=a.id 
            where a.model=\'%s\' and b.res_id=%s and a.user_id=%s""" % (type(object_id).__name__, object_id.id,self.env.user.id)
        #print '\n\n\n\nmmmmmmmmmmmmmm',query
        self.env.cr.execute(query)
        user_exists = self.env.cr.fetchall()
        

        if user_exists:
            return True

        else: 
            return False 
        

        #
        # 


    def state_handler(self,object_id,current_state,department_id,employee_id,target):



        if target == 'validate_button_clicker':

            return self.is_nominee(object_id,target)

        elif object_id:
            designer_id = self.env['sod.designer'].search([('model_name','=',type(object_id).__name__)])
            if designer_id:
                state_id = self.env['sod.state'].search([('designer_id','=',designer_id.id),('code','=',current_state)])
                
                if state_id:

                    if state_id[0].python:
                        
                        exec(state_id[0].python)
                        next_state = object_id.state
                        #print '\n\n\n next state before----------' , next_state
                        if target != 'previous_state':
                            next_state = json.loads(object_id.json_data)[target] 
                            #print '\n\n\n next state after----------' , next_state
                        if type(object_id).__name__ == 'hr.regulation':
                            object_id.update(designer_id[0].workflow_handler(object_id.workflow_id,department_id,employee_id,object_id.id,next_state))
                        else:                            
                            other_obj = designer_id[0].workflow_handler(object_id.workflow_id,department_id,employee_id,object_id.id,next_state)
                            object_id.update({'sod_msg':other_obj['sod_msg'],
                                                'button_clickers':other_obj['button_clickers']
                                            })
                        if type(object_id).__name__ == 'project.project' and target != 'previous_state':
                            object_id.write({'previous_state':current_state,'state_new':next_state})
                        elif target != 'previous_state':
                            object_id.write({'previous_state':current_state,'state':next_state})
                        								
                    else:
                        object_id.update({'button_clickers':[(6,0,[])],'sod_msg':u'sod төлөв цонхонд python тохируулаагүй байна'})

#
    
    def prepare_proactive_notification(self,button_clickers,res_id,object_name):

 
        query = """DELETE 
            FROM proactive_line a  
            USING proactive_notification b 
            WHERE a.notification_id=b.id AND 
            a.res_id=%s and b.model=\'%s\'"""%(res_id,object_name)
        
        self.env.cr.execute(query)

        for user in button_clickers:
            notification_id = self.env['proactive.notification'].sudo().search([('model','=',object_name),('code','=','notification'),('user_id','=',user)])
            if not notification_id:
                notification_id = self.env['proactive.notification'].sudo().create({
                    'model':object_name,
                    'code':'notification',
                    'user_id':user,
                    'name':'',
                })

                object_name_mongolia = self.convert_to_mongolian_language(object_name)
                notification_id.sudo().write({
                    'name':object_name_mongolia + str(user) + ' ' + str(notification_id.user_id.name)
                })


            line_id = self.env['proactive.line'].sudo().search([('notification_id','=',notification_id.id),('res_id','=',res_id)])
            if not line_id:
                self.env['proactive.line'].sudo().create({
                    'notification_id':notification_id.id,
                    'res_id':res_id,
                    'state':'need_a_solution'
                })


    def convert_to_mongolian_language(self,object_name):

        if object_name == 'hr.regulation':
            return 'Тушаал - товч дарах ажилтан - '
        elif object_name == 'project.project':
            return 'Төсөл - товч дарах ажилтан - '
        elif object_name == 'hr.extra.hours':
            return 'Гадуур ажил '
        else:
            return object_name + ' - '


        return workflow_name_id[0].get_button_clickers(department_id,user_id)

    def get_details(self, key_word):


        dict1 = {
                'line_ids': []
            }

        element_id = self.env['sod.element'].search([('code','=',key_word)])
        for reference in element_id.reference_ids:

            dict1['line_ids'].append([0, False, {u'task_type': reference.category_id.id, u'name': reference.name }])


        return dict1

class SodMatrix(models.Model):
    _name = 'sod.matrix'
    #_inherit = 'mail.thread'

    _description = "SOD matrix"
    # _order = "role_id,resource_id"


    
    designer_id = fields.Many2one('sod.designer','Designer')


    duty_id = fields.Many2one('sod.duty',string = 'Үүрэг')
    duty_name = fields.Char(string = 'Нэр')
    duty_description = fields.Char(string = 'Тайлбар')
    crud = fields.Char('Crud')
    role_id = fields.Many2one('res.groups',string = 'Дүр',required=True)



class SodDuty(models.Model):
    _name = 'sod.duty'
    #_inherit = 'mail.thread'
    _description = "Hr system role"


    name = fields.Char('Name')
    description = fields.Char('Description')
    crud = fields.Char('Crud')



