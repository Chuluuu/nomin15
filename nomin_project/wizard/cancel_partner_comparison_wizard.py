# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.tools.translate import _
from openerp.exceptions import UserError, ValidationError




class CancelPartnerComparisonWizard(models.TransientModel):
    _name = 'cancel.partner.comparison.wizard'
    _description = 'Cancel reason comparison wizard'
    
    comment = fields.Text('Comment', required=True)
    
    @api.multi
    def action_cancel(self):
        context = self._context
        if context.get('active_model') and context.get('active_id'):
            if context['active_model'] == 'budget.partner.comparison' and context['active_id']:
                comparison_obj = self.env['budget.partner.comparison'].sudo().browse(context['active_id'])
                #Ажиллах хүчний зардлын гүйцэтгэл цуцлах
                if comparison_obj.control_budget_id and comparison_obj.control_budget_id.labor_line_ids:
                    for line in comparison_obj.sudo().control_budget_id.labor_line_ids:
                        for labor in comparison_obj.labor_cost_ids:
                            if line.state == 'comparison' and line.product_id.id == labor.product_id.id:
                                line.write({'state' : 'confirm','cost_choose' : False})
                        for utilization in comparison_obj.control_budget_id.utilization_budget_labor:
                            if comparison_obj == utilization.budget_comparison:
                                utilization.unlink()
                #Материалын зардлын гүйцэтгэл цуцлах
                if comparison_obj.control_budget_id and comparison_obj.control_budget_id.material_line_ids:
                    for line in comparison_obj.sudo().control_budget_id.material_line_ids:
                        for material in comparison_obj.material_cost_ids:
                            if line.state == 'comparison' and line.product_id.id == material.product_id.id:
                                line.write({'state' : 'confirm','cost_choose' : False})
                        for utilization in comparison_obj.control_budget_id.utilization_budget_material:
                            if comparison_obj == utilization.budget_comparison:
                                utilization.unlink()
                #Машин механизмын зардлын гүйцэтгэл цуцлах
                if comparison_obj.control_budget_id and comparison_obj.equipment_cost > 0:
                    for line in comparison_obj.control_budget_id.utilization_budget_equipment:
                        if line.state == 'comparison' and comparison_obj.equipment_cost == line.price:
                            line.unlink()
                #Тээврийн зардлын гүйцэтгэл цуцлах
                if comparison_obj.control_budget_id and comparison_obj.carriage_cost > 0:
                    for line in comparison_obj.control_budget_id.utilization_budget_carriage:
                        if line.state == 'comparison' and comparison_obj.carriage_cost == line.price:
                            line.unlink()
                #Шууд зардлын гүйцэтгэл цуцлах
                if comparison_obj.control_budget_id and comparison_obj.postage_cost > 0:
                    for line in comparison_obj.control_budget_id.utilization_budget_postage:
                        if line.state == 'comparison' and comparison_obj.postage_cost == line.price:
                            line.unlink()
                #Бусад зардлын гүйцэтгэл цуцлах
                if comparison_obj.control_budget_id and comparison_obj.other_cost > 0:
                    for line in comparison_obj.control_budget_id.utilization_budget_other:
                        if line.state == 'comparison' and comparison_obj.other_cost == line.price:
                            line.unlink()
                comparison_obj.write({'state':'cancelled','rejection_reason' : self.comment})
                 
        return {'type': 'ir.actions.act_window_close'}