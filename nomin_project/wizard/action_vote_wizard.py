# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
import time
from datetime import date, datetime, timedelta




class ActionVoteWizard(models.TransientModel):
    _name = 'action.vote.wizard'
    _description = 'action vote wizard'
    
    
    comparison_id  = fields.Many2one('budget.partner.comparison', string = 'budget partner comparison')
    participants_ids = fields.One2many('budget.partners.line', 'wizard_id', string = "budget partner")

class BudgetPartnersLine(models.TransientModel):
    _name="budget.partners.line"
    _description = "Budget Partners Line"


    wizard_id = fields.Many2one('action.vote.wizard', string = 'Budget partner comparison')
    partner_id = fields.Many2one('res.partner' , string = 'Харилцагчийн нэр')
    price_amount = fields.Float(string = 'Үнийн санал')
    is_winner = fields.Boolean(string = 'is winner', default=False )
    date_win = fields.Date(string = 'Date win')
    employee_ids = fields.Many2many('hr.employee', string="Voted employees")


    
    def action_vote(self):
        for partner in self:
            if partner.wizard_id.comparison_id:
                for line in partner.wizard_id.comparison_id.participants_ids:
                    if line.partner_id == partner.partner_id:
                        line.is_winner = True
                        partner.wizard_id.comparison_id.write({'state':'winner','date_win': datetime.today().strftime("%Y-%m-%d")})

            