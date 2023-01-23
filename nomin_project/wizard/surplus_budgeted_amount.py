# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import time
from odoo.exceptions import UserError
import json

class SurplusBudgetedAmount(models.TransientModel):
    '''
        Төлөвлөсөн дүнг тодотгох
    '''

    _name = 'surplus.budgeted.amount'


    @api.model
    def default_get(self, fields):

        res = super(SurplusBudgetedAmount, self).default_get(fields)	
        project = self.env['project.project'].browse(self._context.get('active_ids', []))
        for line in project.budgeted_line_ids:
            # if line.total_possible_balance == 0:
            res.update({'budgeted_amount':line.budgeted_amount}) 
            # else:
            #     res.update({'budgeted_amount':line.total_possible_balance})

            
            lines = self.env['project.budget.line'].sudo().search([('project_budget_id.project_id','=',project.id)])
            for line in lines:
                if line.state == 'new':
                   
                    res.update({
                            'project_id'    : project.id,
                            'material_cost':line.material_cost,
                            'labor_cost':line.labor_cost,
                            'equipment_cost':line.equipment_cost,
                            'carriage_cost':line.carriage_cost,
                            'postage_cost':line.postage_cost,
                            'other_cost':line.other_cost,
                            'total_cost':line.total_cost,

                            'surplus_material_cost':line.material_cost,
                            'surplus_labor_cost':line.labor_cost,
                            'surplus_equipment_cost':line.equipment_cost,
                            'surplus_carriage_cost':line.carriage_cost,
                            'surplus_postage_cost':line.postage_cost,
                            'surplus_other_cost':line.other_cost,
                            'surplus_total_cost':line.total_cost
                            })
                elif line.state == 'modified':
                    
                    res.update({
                            'project_id'    : project.id,
                            'material_cost':line.material_cost,
                            'labor_cost':line.labor_cost,
                            'equipment_cost':line.equipment_cost,
                            'carriage_cost':line.carriage_cost,
                            'postage_cost':line.postage_cost,
                            'other_cost':line.other_cost,
                            'total_cost':line.total_cost,

                            'surplus_material_cost':line.material_cost,
                            'surplus_labor_cost':line.labor_cost,
                            'surplus_equipment_cost':line.equipment_cost,
                            'surplus_carriage_cost':line.carriage_cost,
                            'surplus_postage_cost':line.postage_cost,
                            'surplus_other_cost':line.other_cost,
                            'surplus_total_cost':line.total_cost
                            })

        return res
        
    material_cost = fields.Float(string="Cost of material")
    labor_cost = fields.Float(string="Cost of labor")
    equipment_cost = fields.Float(string="Cost of equipments")
    carriage_cost = fields.Float(string="Cost of transportations")
    postage_cost = fields.Float(string="Postage costs")
    other_cost = fields.Float(string="Other costs")
    total_cost = fields.Float(string = 'Total cost')
    
    surplus_material_cost = fields.Float(string="Surplus Cost of material")
    surplus_labor_cost = fields.Float(string="Surplus Cost of labor")
    surplus_equipment_cost = fields.Float(string="Surplus Cost of equipments")
    surplus_carriage_cost = fields.Float(string="Surplus Cost of transportations")
    surplus_postage_cost = fields.Float(string="Surplus Postage costs")
    surplus_other_cost = fields.Float(string="Surplus Other costs")
    surplus_total_cost = fields.Float(string ='Surplus Total cost')

    budgeted_amount = fields.Float(string='Budgeted amount' , readonly="1")


    @api.onchange('surplus_material_cost','surplus_labor_cost','surplus_equipment_cost','surplus_carriage_cost','surplus_postage_cost','surplus_other_cost')
    def onchange_amount(self):
        total = 0

        for cost in self:
            total =  cost.surplus_material_cost + cost.surplus_labor_cost + cost.surplus_equipment_cost + cost.surplus_carriage_cost + cost.surplus_postage_cost + cost.surplus_other_cost
        self.surplus_total_cost = total
    


    
    def action_surplus(self):
        project = self.env['project.project'].browse(self._context.get('active_ids', []))
        project.button_check = True
        for cost in self:
            total =  cost.surplus_material_cost + cost.surplus_labor_cost + cost.surplus_equipment_cost + cost.surplus_carriage_cost + cost.surplus_postage_cost + cost.surplus_other_cost
        self.surplus_total_cost = total

        if self.surplus_total_cost < self.total_cost:
            raise UserError(_(u'Тодотголын дүн төлөвлөсөн дүнгээс бага байна')) 

        
        project_budgeted_lines = self.env['project.budget.line'].sudo().search([('project_budget_id.project_id','=',project.id)])
        for project_budgeted_line in project_budgeted_lines:
            if project_budgeted_line.state == 'new':
                budget_id = project_budgeted_line.project_budget_id

                project_budgeted_line.create({  'project_budget_id':budget_id.id,
                                                'material_cost':cost.surplus_material_cost,
                                                'labor_cost':cost.surplus_labor_cost,
                                                'equipment_cost':cost.surplus_equipment_cost,
                                                'carriage_cost':cost.surplus_carriage_cost,
                                                'postage_cost':cost.surplus_postage_cost,
                                                'other_cost':cost.surplus_other_cost,
                                                'total_cost':cost.surplus_total_cost,
                                                'state':'sent',
                                                            
                                            })            
    
        surplus_line = self.env['surplus.budget'].create({'surplus_amount':self.surplus_total_cost,
                                                            'budgeted_amount':self.budgeted_amount,
                                                            'surplus_date':time.strftime('%Y-%m-%d %H:%M:%S'),
                                                            'project_id':project.id,
                                                            'parent_project_id':project.parent_project.id,
                                                            'state':'draft'
                                                            })

        project.state_handler(project.state_new,'next_state')
        # project.state_handler(project.state)
        # project.write({'previous_state':project.state,
        #     'state':json.loads(project.json_data)['next_state']})

        
        project.create_history('surplus_budget','Тодотгосон')
        user_ids=[]
        for user in project.button_clickers.ids:
            if user not in project.c_user_ids.ids:
                user_ids.append(user)
        project.update({'c_user_ids':[(6,0,user_ids+project.c_user_ids.ids)]})



class EvaluatePerform(models.TransientModel):
    '''
        Үнэлгээний үзүүлэлтүүдийг хувиар үнэлэх
    '''

    _name = 'to.evaluate.perform'



    @api.model
    def default_get(self, fields):

        perform_ids = []
        res = super(EvaluatePerform, self).default_get(fields)	
        project = self.env['project.project'].browse(self._context.get('active_ids', []))
        for perform in project.perform_new:                        
            vals = {
                    'project_id'    : project.id,
                    'perform'       : perform.id,
                    'percent'       : 0.0,
                    }
            perform_ids.append((0,0,vals))
        
        res.update({'line_ids':perform_ids})
        return res
    

    line_ids = fields.One2many('perform.line','perform_id', string="Perform line")

  
    
    def action_evaluate(self):    
        project = self.env['project.project'].browse(self._context.get('active_ids', []))
        project_perform = self.env['project.perform']
        for line in self.line_ids: 
            vals = {
                    'project_id'    : project.id,
                    'perform_new'       : line.perform.id,
                    'percent'       : line.percent,
                    }
            project_perform = project_perform.create(vals)
            project.write({'state_new':'finished'})

        
    

class PerformLine(models.TransientModel):
    '''
        Үнэлгээний үзүүлэлтүүдийг хувиар үнэлэх
    '''

    _name = 'perform.line'


    perform = fields.Many2one('evaluation.indicators',string='Perform')
    percent = fields.Float(string='Percent')
    perform_id = fields.Many2one('to.evaluate.perform', string="To evaluate perform" ,ondelete='cascade')
    
           

class ReturnState(models.TransientModel):
    '''
        Төлөв буцаах
    '''

    _name = 'return.state'



    @api.model
    def default_get(self, fields):

        res = super(ReturnState, self).default_get(fields)	
        
        return res
    

    reason = fields.Text(string="Шалтгаан")

  
    
    def action_return(self):    
        project = self.env['project.project'].browse(self._context.get('active_ids', []))

        # {"workflow_name": "get_branch_economist", "next_state": 'verify_by_economist'} 
        json_data = {
            'workflow_name' :'unknown',
            'next_state':'verify_by_economist',
            }
        project.json_data = json.dumps(json_data)

        if project.state_new == 'ready':
            project.write({'state_new':'implement_project',
                            'button_check':False,
                            'return_reason':self.reason    
                        })  
                       
        elif project.state_new in ('implement_project','surplus_by_economist','surplus_by_director','surplus_by_business_director','surplus_by_ceo','surplus_confirm_branch'):
            project.write({'state_new':'comfirm',
                            'button_check':False,
                            'return_reason':self.reason
                            })
            
            surplus_lines = self.env['surplus.budget'].search([('project_id','=',project.id),('state','=','draft')])
            for surplus_line in surplus_lines: 
                if surplus_line:
                    surplus_line.update({   'project_id':project.id,
                                            'parent_project_id':project.parent_project.id,
                                            'state':'rejected'
                                            })



            # project_budgeted_line = self.env['project.budget.line'].sudo().search([('project_budget_id.project_id','=',project.id),('state','=','sent')])
            # if project_budgeted_line:
            #     project_budgeted_line.update({ 
            #                             'state':'rejected'                                                
                                        
            #                              })
        else:
            project.write({'state_new':'draft',
                            'return_reason':self.reason,
                            'button_check':False,
                            'json_data':project.json_data,
                            'previous_state':'draft',
                            'sod_msg':False,
                            'button_clickers':[(6, 0, [])],
                            'workflow_name':False,
                            'voters': [(6, 0, [])]
                              
                            })
        # if project.parent_project:
        #     print '\n\n\n wtf'
        #     line = self.env['budgeted.line'].search([('parent_project_id','=',project.parent_project.id)])
        #     print '\n\n\n line' , line
        #     project.parent_project.write({'parent_budgeted_line_ids':[(6, 0, [])]})



class ProjectCancel(models.TransientModel):
    '''
        Цуцлах
    '''

    _name = 'project.cancel'



    @api.model
    def default_get(self, fields):

        res = super(ProjectCancel, self).default_get(fields)	
        
        return res
    

    cancel_reason = fields.Text(string="Цуцлах шалтгаан")

  
    
    def action_cancel(self):    
        project = self.env['project.project'].browse(self._context.get('active_ids', []))

        
        project.write({'state':'cancelled',
                        'cancel_reason':self.cancel_reason,
                        'button_check':False,                        
                            
                     })

class ProjectBack(models.TransientModel):
    '''
        Цуцлах
    '''

    _name = 'project.back'



    @api.model
    def default_get(self, fields):

        res = super(ProjectBack, self).default_get(fields)	
        
        return res
    

    project_back_reason = fields.Text(string="Хойшлуулах шалтгаан")
    project_back_day = fields.Integer(string="Хойшлуулах өдрийн тоо")

  
    
    def action_back(self):    
        project = self.env['project.project'].browse(self._context.get('active_ids', []))

        
        project.write({'state':'delayed',
                        'back_reason':self.project_back_reason,
                        'project_back_day':self.project_back_day,
                        'button_check':False,                        
                            
                     })
    
            




