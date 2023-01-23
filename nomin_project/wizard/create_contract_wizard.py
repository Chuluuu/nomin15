# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError




class CreateContractWizard(models.TransientModel):
    _name = 'create.contract.wizard'
    _description = 'create contract wizard'
    


    @api.model
    def default_get(self, fields):
        res = super(CreateContractWizard, self).default_get(fields) 
        context = dict(self._context or {})   
        active_id = context and context.get('active_id', False) or False
        perform_obj = self.env['control.budget']
        perform = perform_obj.browse(active_id)

        res.update({
            'control_budget_id' : perform.id,
            # 'project_id' : perform.project_id.id,
            })

        return res

    control_budget_id = fields.Many2one('control.budget', string = 'Budget')
    employee_id = fields.Many2one('hr.employee',string = u'Хариуцагч')
    
    def action_create(self):
        budget = self.env['control.budget'].search([('id','=', self.control_budget_id.id)])
        budget_partner_comparison = self.env['budget.partner.comparison']
        model_obj =self.env['ir.model.data']
        result = model_obj._get_id('nomin_project', 'view_budget_partner_comparison_form')
        view_id = model_obj.browse(result).res_id

        if budget:
            vals = {
                'control_budget_id':budget.id,
                'project_id' : budget.project_id.id,
                'employee_id' : self.employee_id.id,
                'task_id' : budget.task_id.id,
                'task_graph_id' : budget.work_graph_id.id,
                'material_cost' : budget.material_cost,
                'labor_cost' : budget.labor_cost,
                'equipment_cost' : budget.equipment_cost,
                'carriage_cost' : budget.carriage_cost,
                'postage_cost' : budget.postage_cost,
                'other_cost' : budget.other_cost,
                'department_id' : self.employee_id.department_id.id
            }
            

        budget_partner_comparison = budget_partner_comparison.create(vals)
        return {
                     'type': 'ir.actions.act_window',
                     'name': _('Register Call'),
                     'res_model': 'budget.partner.comparison',
                     'view_mode' : 'form',
                     'search_view_id' : view_id,
                     'res_id':budget_partner_comparison.id,
                     'target' : 'current',
                     'nodestroy' : True,
                 }