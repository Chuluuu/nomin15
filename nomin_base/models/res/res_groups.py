# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2009-2014 Monos Group (<http://monos.mn>).
#
##############################################################################

import re

from openerp import api, fields, models, _
from openerp.osv import expression
from openerp.exceptions import UserError
from openerp.tools import float_round, float_repr

class ResGroups(models.Model):
    _inherit = 'res.groups'

    group_id = fields.Char('Group id')
    allowed_resource = fields.Many2one('ir.model.fields',string = 'Хандах нөөц', domain="[('model','=','res.users'),('name','like','allowed')]" )
    group_type = fields.Selection([('support_role','1. Дэмжлэг үйлчилгээний ажилтны эрх')
                                    ,('admin_role','2. Админ эрх - тохиргоотой ажиллах эрх')
                                    ,('managerial_role','3. Менежерийн эрх - зөвшөөрөгдсөн нөөцтэй ажиллах эрх')
                                    ,('menu_dominant_role','4. Цэсэнд давамгай эрх - бүх бичлэгтэй ажиллах эрх')
                                    ,('personal_role','5. Энгийн эрх - өөрийн оролцоот зүйлстэй ажиллах эрх')
                                  
                                  ], string="Хандах дүр", required=True)
    type_name = fields.Char(string = 'Группын төрөл',readonly=True)



    @api.multi
    def action_to_get_group_ids(self):
        res_group_ids = self.env['res.groups'].sudo().search([('group_id','=',False)])
        for res_group in res_group_ids:
            ir_model_data = self.env['ir.model.data'].sudo().search([('res_id','=',res_group.id),('model','=','res.groups')], limit = 1)
            if ir_model_data:
           

                group_id = str(ir_model_data.module) + "." + str(ir_model_data.name)
                res_group.sudo().write({'group_id':group_id})
    
    # @api.multi
    # def write(self, vals):
    #     user_id = super(ResGroups, self).write(vals)        
    #     if not vals:
    #         print "\n\n\n\n",vals,"\n\n\n\n"
    #         raise UserError(_('The code already exists'))
    #     return user_id


    @api.multi
    def write(self, vals):

        result = super(ResGroups, self).write(vals)

        if vals.get('group_type') or vals.get('allowed_resource'):

            group_type = '5. Энгийн эрх - өөрийн оролцоот зүйлстэй ажиллах эрх'
            if self.group_type == 'support_role':
                group_type = '1. Дэмжлэг үйлчилгээний ажилтны эрх'
            if self.group_type == 'admin_role':
                group_type = '2. Админ эрх - тохиргоотой ажиллах эрх'
            elif self.group_type == 'managerial_role':
                group_type = '3. Менежерийн эрх - зөвшөөрөгдсөн нөөцтэй ажиллах эрх'
            elif self.group_type == 'menu_dominant_role':
                group_type = '4. Цэсэнд давамгай эрх - бүх бичлэгтэй ажиллах эрх'
            # elif self.group_type == 'workflow_role':
            #     group_type = '4. Урсгалд оролцдог эрх'                

            allowed_resource = ''
            if self.group_type not in ['managerial_role']:
                self.allowed_resource = False
            elif self.allowed_resource.field_description and self.group_type in ['managerial_role']:
                allowed_resource = ' #' + self.allowed_resource.field_description
            self.type_name = group_type + allowed_resource


            # query = "update res_users set arranged=False;"
            # self.env.cr.execute(query)


            query = "update res_users set arranged=False from res_groups_users_rel b  where b.gid= %s" %(self.id)
            self.env.cr.execute(query)
            print'ir_model_data',self.id
            
            # if self.group_type and self.allowed_resource:
            #     if self.group_type not in ['managerial_role','workflow_role']:
            #         self.allowed_resource = False
            #     elif self.allowed_resource.field_description and self.group_type=='workflow_role':
            #         allowed_resource = ' #' + self.allowed_resource.field_description
            # self.type_name = group_type + allowed_resource

        return result




