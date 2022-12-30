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
import datetime
from datetime import date, datetime, timedelta
from openerp import api, fields, models, _
from openerp.exceptions import UserError, ValidationError
import time

class create_project_tender(models.TransientModel):
    _name = 'create.project.tender'
    '''
       хяналтын төсвөөес Тендер үүсгэх
    '''
    # def default_get(self, cr, uid, fields, context=None):
    #     result = []
    #     if context is None:
    #         context = {}
    #     res = super(create_project_tender, self).default_get(cr, uid, fields, context=context)    
    #     active_id = context and context.get('active_id', False) or False
    #     perform_obj = self.pool.get('control.budget')
    #     perform = perform_obj.browse(cr, uid, active_id)
    #     line_ids = []
    #     line_ids2= []
    #     for line in perform.material_line_ids:
    #         if line.cost_choose == True and line.state == 'confirm':
    #             line_ids.append(line.id)
    #     for line in perform.labor_line_ids:
    #         if line.cost_choose == True and line.state == 'confirm':
    #             line_ids2.append(line.id)
                
    #     res.update({
    #                 'control_budget_id' : perform.id,
    #                 'material_limit' : perform.material_utilization_limit,
    #                 'labor_limit' : perform.labor_utilization_limit,
    #                 'equipment_limit' : perform.equipment_utilization_limit,
    #                 'carriage_limit' : perform.carriage_utilization_limit,
    #                 'postage_limit' : perform.postage_utilization_limit,
    #                 'other_limit' : perform.other_utilization_limit,
    #                 'material_line': [(6, 0, line_ids)],
    #                 'labor_line': [(6, 0, line_ids2)]
    #                 })
    #     return res
    @api.model
    def default_get(self, fields):
        res = super(create_project_tender, self).default_get(fields) 
        context = dict(self._context or {})   
        active_id = context and context.get('active_id', False) or False
        perform_obj = self.env['control.budget']
        perform = perform_obj.browse(active_id)
        line_ids = []
        new_line_ids = []
        line_ids2= []
        line_ids3= []
        total = 0.0
        if perform.is_old2:
            for line in perform.material_line_ids:
                if line.cost_choose == True and line.state == 'confirm':
                    line_ids.append(line.id)
                    total += line.material_total
            res.update({'material_line': line_ids,})            
        else:
            for line in perform.new_material_line_ids:
                print '\n\n\n line' , line , line.material_total
                if line.cost_choose == True and line.state == 'confirm':
                    new_line_ids.append(line.id)
                    print '\n\n\n glg' , new_line_ids
                    total += line.material_total
                    print '\n\n\n total' , total
            res.update({'new_material_line': new_line_ids,})
            print '\n\n\n\ new mat line res' , res 
        if perform.is_old:
            for line in perform.labor_line_ids:
                if line.cost_choose == True and line.state == 'confirm':
                    total += line.labor_cost_basic
                    line_ids2.append((0,0,{'product_id': line.product_id.id,
                                            'product_uom':line.product_uom.id,
                                            'product_uom_qty':line.product_uom_qty,
                                            'price_unit':line.price_unit,
                                            'department_id':perform.m_department_id.id,
                                            'labor_total':line.labor_total,
                                            'engineer_salary':line.engineer_salary,
                                            'extra_salary':line.extra_salary,
                                            'social_insurance':line.social_insurance,
                                            'habe':line.habe,
                                            'engineer_salary_percent':line.engineer_salary_percent,
                                            'extra_salary_percent':line.extra_salary_percent,
                                            'social_insurance_rate':line.social_insurance_rate,
                                            'habe_percent':line.habe_percent,
                                            'total_salary':line.total_salary,
                                            'labor_cost_basic':line.labor_cost_basic,
                                            'name':line.name}))
            res.update({'labor_line': line_ids2,})
        else:
            for line in perform.labor_line_ids1:
                if line.cost_choose == True and line.state == 'confirm':
                    total += line.labor_cost_basic
                    line_ids3.append((0,0,{'product_uom':line.product_uom.id,
                                            'product_name':line.product_name,
                                            'product_uom_qty':line.product_uom_qty,
                                            'price_unit':line.price_unit,
                                            'department_id':perform.m_department_id.id,
                                            'labor_total':line.labor_total,
                                            'engineer_salary':line.engineer_salary,
                                            'extra_salary':line.extra_salary,
                                            'social_insurance':line.social_insurance,
                                            'habe':line.habe,
                                            'engineer_salary_percent':line.engineer_salary_percent,
                                            'extra_salary_percent':line.extra_salary_percent,
                                            'social_insurance_rate':line.social_insurance_rate,
                                            'habe_percent':line.habe_percent,
                                            'total_salary':line.total_salary,
                                            'labor_cost_basic':line.labor_cost_basic,
                                            'name':line.name}))
                    
            res.update({'labor_line1': line_ids3,})
            
        print '\n\n\n task' , perform.task_id.id      
        res.update({
                    'control_budget_id' : perform.id,
                    'material_limit' : perform.material_utilization_limit,
                    'labor_limit' : perform.labor_utilization_limit,
                    'equipment_limit' : perform.equipment_utilization_limit,
                    'carriage_limit' : perform.carriage_utilization_limit,
                    'postage_limit' : perform.postage_utilization_limit,
                    'other_limit' : perform.other_utilization_limit,
                    'is_old' : perform.is_old,
                    'is_old2' : perform.is_old2,
                    'total_amount1' : total,
                    'work_task': perform.task_id.id,
                    'material_line': [(6, 0, line_ids)],
                    'new_material_line': [(6, 0, new_line_ids)],
                    })
        print '\n\n\n res' , res
        return res

    @api.multi
    def _total_amount1(self):
        total = 0.0
        for budget in  self:
            if budget.is_old2:
                for line in budget.control_budget_id.material_line_ids:
                    if line.cost_choose == True and line.state == 'confirm':
                        total += line.material_total
            else:
                for line in budget.control_budget_id.new_material_line_ids:
                    if line.cost_choose == True and line.state == 'confirm':
                        total += line.material_total

            if budget.is_old:
                for line in budget.labor_line:
                    total += line.labor_cost_basic
            else:
                for line in budget.labor_line1:
                    total += line.labor_cost_basic
            total += budget.equipment_create
            total += budget.carriage_create
            total += budget.postage_create
            total += budget.other_create
            budget.total_amount1 = total

    labor_create        = fields.Float(u'Ажиллах хүчний зардал',default=0.0)
    equipment_create    = fields.Float(u'Машин механизм зардал',default=0.0)
    carriage_create     = fields.Float(u'Тээврийн зардал',default=0.0)
    postage_create      = fields.Float(u'Шууд зардал',default=0.0)
    other_create        = fields.Float(u'Бусад зардал',default=0.0)
    
    labor_limit         = fields.Float(u'Ажиллах хүчний зардлын үлдэгдэл')
    equipment_limit     = fields.Float(u'Машин механизмын зардлын үлдэгдэл')
    carriage_limit      = fields.Float(u'Тээврийн зардлын үлдэгдэл')
    postage_limit       = fields.Float(u'Шууд зардлын үлдэгдэл')
    other_limit         = fields.Float(u'Бусад зардлын үлдэгдэл')
    
    material_line       = fields.One2many('material.budget.line','tender_id',string = u'Материалын зардал')
    new_material_line   = fields.One2many('material.budget.line','tender_id',string = u'Материалын зардал')
    labor_line          = fields.One2many('labor.budget.line','tender_id',string = u'Ажиллах хүчний зардал')
    labor_line1         = fields.One2many('labor.budget.line','tender_id',string = u'Ажиллах хүчний зардал')
    type_id             = fields.Many2one('tender.type', index=True, string=u'Тендерийн ангилал',required=True)
    child_type_id       = fields.Many2one('tender.type', string=u'Ангилалын задаргаа',required=True)
    desc_name           = fields.Char(u'Тодорхойлох нэр',required=True)
    control_budget_id   = fields.Many2one('control.budget', string = 'Budget')
    work_task           = fields.Many2one('project.task', index=True,string = u'Ажлын даалгавар',required=True, domain=[('task_type', '=','work_task'),('task_state','in',('t_confirm','t_evaluate','t_done'))])
    work_graph          = fields.Many2one('project.task', index=True,string = u'Ажлын зураг', domain=[('task_type', '=','work_graph'),('task_state','in',('t_confirm','t_evaluate','t_done'))])
    
    total_amount1       = fields.Float(u'Нийт тендер үүсгэх дүн',compute=_total_amount1)
    is_old              = fields.Boolean(string="is old") 
    is_old2              = fields.Boolean(string="is old2") 



    @api.onchange('material_create','labor_create','equipment_create','carriage_create','postage_create','other_create')
    def onchange_types(self):
        '''
           хяналтын төсвийн боломжит үлдэгдэлээс хэтэрсэн эсэх шалгах
        '''
        budget_t=self.env['control.budget'].search([('id','=',self.env.context.get('id2'))])
        project_t=self.env['project.project'].search([('id','=',budget_t.project_id.id)])
        self.update({
            'work_task':budget_t.task_id,
            'work_graph':budget_t.work_graph_id
            })
        total = 0.0
        for budget in  self:
            if budget.is_old2:
                for line in budget.control_budget_id.material_line_ids:
                    if line.cost_choose == True and line.state == 'confirm':
                        total += line.material_total
            else:
                for line in budget.control_budget_id.new_material_line_ids:
                    if line.cost_choose == True and line.state == 'confirm':
                        total += line.material_total

            if budget.is_old:
                for line in budget.labor_line:
                    total += line.labor_cost_basic
            else:
                for line in budget.labor_line1:
                    total += line.labor_cost_basic
            if budget.equipment_create <= budget.equipment_limit:
                total += budget.equipment_create
            else :
                raise ValidationError(_(u'Машин механизмын зардлын дүн хэтэрсэн байна'))
            if budget.carriage_create <= budget.carriage_limit:
                total += budget.carriage_create
            else :
                raise ValidationError(_(u'Тээврийн зардлын дүн хэтэрсэн байна'))
            if budget.postage_create <= budget.postage_limit:
                total += budget.postage_create
            else :  
                raise ValidationError(_(u'Шууд зардлын дүн хэтэрсэн байна'))
            if budget.other_create <= budget.other_limit:
                total += budget.other_create
            else :
                raise ValidationError(_(u'Бусад зардлын дүн хэтэрсэн байна'))
            
            budget.total_amount1 = total
    
    @api.onchange('type_id')
    def onchange_type(self):
        '''
           Тендерийн хүүхэд ангилал домайн
        '''
        self.update({'child_type_id':False})
        child_ids = []
        if self.type_id:
            type_ids = self.env['tender.type'].sudo().search([('parent_id','=',self.type_id.id)])
            child_ids.extend(type_ids.ids)
        return {'domain':{'child_type_id': [('id','=', child_ids)]}}
    
    @api.multi    
    def action_create(self):
        '''
           Тендер үүсгэх товч 
               Хяналтын төсвийн сонгосон талваруудаар тендер үүсгэх мөн хяналтын төсөврүү зардал бүрээр гүйцэтгэл хөтлөх
        '''
        print '\n\n\n tender uusgeh'
        budget  = self.env['control.budget'].search([('id','=', self.control_budget_id.id)])
        print '\n\n\n budget hahaha' , budget , self,self.is_old2
        space = ', '
        names = []
        work_task_employee = []
        work_graph_employee = []
        work_task_namess = ''
        work_graph_namess = ''
        budget_state = ''
        work_task_state = ''
        work_graph_state = ''   
        products = {}
        tender_tender   = self.env['tender.tender']
        tender_line     = self.env['tender.line']
        tender_labor_line = self.env['tender.labor.line']
        model_obj =self.env['ir.model.data']
        result = model_obj._get_id('nomin_tender', 'view_tender_form')
        view_id = model_obj.browse(result).res_id
        utilization_budget_material = self.env['utilization.budget.material']
        utilization_budget_labor =  self.env['utilization.budget.labor']
        utilization_budget_equipment = self.env['utilization.budget.equipment']
        utilization_budget_carriage =  self.env['utilization.budget.carriage']
        utilization_budget_postage = self.env['utilization.budget.postage']
        utilization_budget_other =  self.env['utilization.budget.other']
        
        user = self.env['res.users'].search([('id','=', budget.user_id.id)])
        employee_ids = self.env['hr.employee'].search([('user_id','=',user.id)])
        if not employee_ids:
            raise ValidationError(_(u'Төсөвчинд холбоотой ажилтан алга'))
        else:
            for user in budget.budget_confirmer:
                    names.append(user.name)
            for emp in self.work_task.controller:
                work_task_employee.append(emp.name)
                work_task_namess = ' ; '.join(work_task_employee)
            for emp in self.work_graph.controller:
                work_graph_employee.append(emp.name)
                work_graph_namess = ' ; '.join(work_graph_employee)
            if self.work_task.task_state == 't_confirm':
                work_task_state = u'Батлагдсан'
            if self.work_task.task_state == 't_evaluate':
                work_task_state = u'Үнэлэх'
            if self.work_task.task_state == 't_done':
                work_task_state = u'Дууссан'
            if self.work_graph.task_state == 't_confirm':
                work_graph_state = u'Батлагдсан'
            if self.work_graph.task_state == 't_evaluate':
                work_graph_state = u'Үнэлэх'
            if self.work_graph.task_state == 't_done':
                work_graph_state = u'Дууссан'
            tender_limit_config = self.env['purchase.tender.config'].search([('type','=','control_budget'),('is_active','=',True)])
            if tender_limit_config:
                if self.total_amount1 < tender_limit_config.amount:
                    raise ValidationError(_(u'Тендер зарлах дүнгээс бага байна!!'))
            vals = {
                            'user_id'                   :self._uid,
                            'type_id'                   :self.type_id.id,
                            'child_type_id'             :self.child_type_id.id,
                            'desc_name'                 :self.desc_name,
                            'project_id'                :budget.project_id.id,
                            'control_budget_id'         :budget.id,
                            'control_budget_verifier'   :space.join(names),
                            'control_budget_state'      :budget.state,
                            'work_task_id'              :self.work_task.id,
                            'work_task_verifier'        :work_task_namess,
                            'work_task_state'           :work_task_state,
                            'work_graph_id'             :self.work_graph.id,
                            'work_graph_state'          :work_graph_state,
                            'work_graph_verifier'       :work_graph_namess,
                            'total_budget_amount'       :self.total_amount1,
                            'state'                     :'draft',
                            'is_created_from_budget'    :True
                            }
            
            if self.total_amount1 == 0.0:
                raise ValidationError(_(u'Зардлын төрлүүдээс сонгоно уу!!'))
            tender_tender = tender_tender.create(vals)
            for cpt in self:
                if cpt.is_old2:
                    for line in self.material_line:
                        line_vals = {
                                    'product_id':      line.product_id.id,
                                    'product_uom_id':  line.product_uom.id,
                                    'product_qty':     line.product_uom_qty,
                                    'tender_id':       tender_tender.id
                                    }
                        tender_line = tender_line.create(line_vals)
                else:
                    for line in self.new_material_line:
                        print '\n\n\n line' , line, line.product_name
                        line_vals = {
                                    'product_name':    line.product_name,
                                    'product_uom_id':  line.product_uom.id,
                                    'product_qty':     line.product_uom_qty,
                                    'tender_id':       tender_tender.id
                                    }
                        tender_line = tender_line.create(line_vals)


            if tender_tender.is_old:
                for line in self.labor_line:
                    line_vals = {
                                'product_id':      line.product_id.id,
                                'product_uom_id':  line.product_uom.id,
                                'product_qty':     line.product_uom_qty,
                                'tender_id':       tender_tender.id
                                }
                    tender_line = tender_line.create(line_vals)
            else:
                for line in self.labor_line1:
                    line_vals = {
                                'product_name':   line.product_name,
                                'product_uom_id':   line.product_uom.id,
                                'product_qty':    line.product_uom_qty,
                                'tender_id':      tender_tender.id
                                }
                    tender_labor_line = tender_labor_line.create(line_vals)
            
            if self.material_line != False:
                total = 0.0
                for line in self.material_line:
                    total += line.material_total
                m_vals = {
                        'budget_id'     :budget.id,
                        'tender'        :tender_tender.id,
                        'date'          :time.strftime('%Y-%m-%d %H:%M:%S'),
                        'price'         :total,
                        'map'           :'budget',
                        'state'         :'tender'
                        }
                
                utilization_budget_material = utilization_budget_material.create(m_vals)
                
                for m_line in self.control_budget_id.material_line_ids:
                    if m_line.state == 'confirm' and m_line.cost_choose ==True:
                        m_line.write({
                                  'state' : 'tender'
                                  })
            
            if self.labor_line != False:
                total = 0.0
                for line in self.labor_line:
                    total += line.labor_cost_basic
                l_vals = {
                        'budget_id'     :budget.id,
                        'tender'        :tender_tender.id,
                        'date'          :time.strftime('%Y-%m-%d %H:%M:%S'),
                        'price'         :total,
                        'map'           :'budget',
                        'state'         :'tender'
                        }
                utilization_budget_labor = utilization_budget_labor.create(l_vals)
                
                for m_line in self.control_budget_id.labor_line_ids:
                    if m_line.state == 'confirm' and m_line.cost_choose ==True:
                        m_line.write({
                                  'state' : 'tender'
                                  })
                
            if self.equipment_create > 0.0:
                if self.equipment_create <= self.equipment_limit:
                    e_vals = {
                            'budget_id'     :budget.id,
                            'tender'        :tender_tender.id,
                            'date'          :time.strftime('%Y-%m-%d %H:%M:%S'),
                            'price'         :self.equipment_create,
                            'map'           :'budget',
                            'state'         :'tender'
                            }
                    utilization_budget_equipment = utilization_budget_equipment.create(e_vals)
                else:
                    raise ValidationError(_(u'Машин механизмын зардлын дүн хэтэрсэн байна'))
                
            if self.carriage_create > 0.0:
                if self.carriage_create <= self.carriage_limit:
                    c_vals = {
                            'budget_id'     :budget.id,
                            'tender'        :tender_tender.id,
                            'date'          :time.strftime('%Y-%m-%d %H:%M:%S'),
                            'price'         :self.carriage_create,
                            'map'           :'budget',
                            'state'         :'tender'
                            }
                    utilization_budget_carriage = utilization_budget_carriage.create(c_vals)
                else:
                    raise ValidationError(_(u'Тээврийн зардлын дүн хэтэрсэн байна'))
                
            if self.postage_create > 0.0:
                if self.postage_create <= self.postage_limit:
                    p_vals = {
                            'budget_id'     :budget.id,
                            'tender'        :tender_tender.id,
                            'date'          :time.strftime('%Y-%m-%d %H:%M:%S'),
                            'price'         :self.postage_create,
                            'map'           :'budget',
                            'state'         :'tender'
                            }
                    utilization_budget_postage = utilization_budget_postage.create(p_vals)
                else:
                    raise ValidationError(_(u'Шууд зардлын дүн хэтэрсэн байна'))
                
            if self.other_create > 0.0:
                if self.other_create <= self.other_limit:
                    m_vals = {
                            'budget_id'     :budget.id,
                            'tender'        :tender_tender.id,
                            'date'          :time.strftime('%Y-%m-%d %H:%M:%S'),
                            'price'         :self.other_create,
                            'map'           :'budget',
                            'state'         :'tender'
                            }
                    utilization_budget_other = utilization_budget_other.create(m_vals)
                else:
                    raise ValidationError(_(u'Бусад зардлын дүн хэтэрсэн байна'))
                    
            return {
                     'type': 'ir.actions.act_window',
                     'name': _('Register Call'),
                     'res_model': 'tender.tender',
                     'view_type' : 'tree',
                     'view_mode' : 'form',
                     'search_view_id' : view_id,
                     'res_id':tender_tender.id,
                     'target' : 'current',
                     'nodestroy' : True,
                 }
    
class inherit_tender_tender(models.Model):
    _inherit = 'tender.tender'
    
    '''
       Тендер 
    '''
    # project_id                  = fields.Many2one('project.project', 'Project', domain=[('state','in',['comfirm', 'project_started']), ('state_comfirm','=',True)],required = True)
    project_id                  = fields.Many2one('project.project', 'Project', domain=['|',('state','in',['comfirm', 'project_started']), ('state_new','in',['comfirm','implement_project'])],required = True)
    control_budget_id           = fields.Many2one('control.budget',string = 'Control Budget')
    control_budget_state        = fields.Char(string='Budget State', )
    control_budget_verifier     = fields.Char(string='Budget Verifier', )
    work_graph_id               = fields.Many2one('project.task', string = 'Work Graph')
    work_graph_state            = fields.Char(string='Graph State', )
    work_graph_verifier         = fields.Char(string='Graph Verifier', )
    graph_document_id           = fields.One2many(related='work_graph_id.work_document', string="Graph Document")
    work_task_id                = fields.Many2one('project.task', string = 'Work Tasks')
    work_task_state             = fields.Char(string='Task State', )
    work_task_verifier          = fields.Char(string='Task Verifier', )
    task_document_id            = fields.One2many(related='work_task_id.work_document', string="Task Document")
    total_budget_amount         = fields.Float(string= 'Total amount')
    is_created_from_budget      = fields.Boolean('from control budget',default=False)
    @api.onchange('project_id')
    def onchange_project(self):
        '''
           Төслөөр домайн дамжуулах
        '''
        if self.project_id:
            self.update({
                         'control_budget_id': False,
                         'work_graph_id': False,
                         'work_task_id': False
                         })
            budget_ids = self.env['control.budget'].search([('project_id','=',self.project_id.id),('state','=','done')])
            tender_limit_config = self.env['purchase.tender.config'].search([('is_active','=',True)])
            budget_conf_ids =[]
            for obj in budget_ids:
                amount = 0.0
                util = 0.0
                balance = 0.0
                amount = obj.material_cost + obj.labor_cost + obj.carriage_cost + obj.equipment_cost + obj.postage_cost + obj.other_cost
                for material_line in obj.utilization_budget_material:
                    util += material_line.price
                for labor_line in obj.utilization_budget_labor:
                    util += labor_line.price
                for equipment_line in obj.utilization_budget_equipment:
                    util += equipment_line.price
                for carriage_line in obj.utilization_budget_carriage:
                    util += carriage_line.price
                for postage_line in obj.utilization_budget_postage:
                    util += postage_line.price
                for other_line in obj.utilization_budget_other:
                    util += other_line.price
                balance = amount - util
                    
                if balance >= tender_limit_config.amount:
                    budget_conf_ids.append(obj.id)
            return {'domain':{
                            'control_budget_id' :[('id','in',budget_conf_ids)],
                            'work_graph_id'     :['&',('task_type','=', 'work_graph'),'&',('task_state','in',['t_evaluate','t_done']),('project_id','=',self.project_id.id)],
                            'work_task_id'      :['&',('task_type','=', 'work_task'),'&',('task_state','in',['t_evaluate','t_done']),('project_id','=',self.project_id.id)]
                            }}
        else:
            self.update({
                         'control_budget_id': False,
                         'work_graph_id': False,
                         'work_task_id': False
                         })

    @api.onchange('control_budget_id')
    def onchange_control_budget(self):
        '''
           Хяналтын төсөв солигдоход холбогдох мэдээлэл харуулах
        '''
        for tender in self:
            space = ', '
            names = []
            total_amount = 0.0
            material_amount = 0.0
            material_amount += tender.control_budget_id.material_utilization_limit
            labor_amount = 0.0
            labor_amount += tender.control_budget_id.labor_utilization_limit
            equipment_amount = 0.0
            equipment_amount += tender.control_budget_id.equipment_utilization_limit
            carriage_amount = 0.0
            carriage_amount += tender.control_budget_id.carriage_utilization_limit
            postage_amount = 0.0
            postage_amount += tender.control_budget_id.postage_utilization_limit
            other_amount = 0.0
            other_amount += tender.control_budget_id.other_utilization_limit
            total_amount = material_amount + labor_amount + equipment_amount + carriage_amount + postage_amount + other_amount
            
            if tender.control_budget_id:
                state = ''
                for user in tender.control_budget_id.budget_confirmer:
                    names.append(user.name)
                if tender.control_budget_id.state == 'done':
                    state = u'Батлагдсан'
                if tender.control_budget_id.state == 'close':
                    state = u'Хаагдсан'
                tender.update({
                             'control_budget_state': state,
                             'control_budget_verifier': space.join(names),
                             'total_budget_amount':total_amount
                             })
            else:
                tender.update({
                             'control_budget_state': False,
                             'control_budget_verifier': False,
                             'total_budget_amount':False
                             })

    @api.onchange('work_graph_id')
    def onchange_graph(self):
        '''
           Ажлын зураг солигдоход 
        '''
        employee = []
        work_graph_state = ''
        if self.work_graph_id:
            for emp in self.work_graph_id.controller:
                employee.append(emp.name)
                emp = ' ; '.join(employee)
            if self.work_graph_id.task_state == 't_confirm':
                work_graph_state = u'Батлагдсан'
            if self.work_graph_id.task_state == 't_evaluate':
                work_graph_state = u'Үнэлэх'
            if self.work_graph_id.task_state == 't_done':
                work_graph_state = u'Дууссан'
            self.update({
                         'work_graph_state': work_graph_state,
                         'work_graph_verifier': emp,
                         })
        else:
            self.update({
                         'work_graph_state': False,
                         'work_graph_verifier': False,
                         })
    
    @api.onchange('work_task_id')
    def onchange_task(self):
        '''
           Ажлын Даалгавар солигдоход 
        '''

        employee = []
        work_task_state = ''
        if self.work_task_id:
            for emp in self.work_task_id.controller:
                employee.append(emp.name)
                emp = ' ; '.join(employee)
            if self.work_task_id.task_state == 't_confirm':
                work_task_state = u'Батлагдсан'
            if self.work_task_id.task_state == 't_evaluate':
                work_task_state = u'Үнэлэх'
            if self.work_task_id.task_state == 't_done':
                work_task_state = u'Дууссан'
            self.update({
                         'work_task_state': work_task_state,
                         'work_task_verifier': emp,
                         })
        
        else:
            self.update({
                         'work_task_state': False,
                         'work_task_verifier': False,
                         })
        