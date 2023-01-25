# -*- coding: utf-8 -*-


from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import api, fields, models, _
from openerp.exceptions import UserError, AccessError


class PurchaseOrder(models.Model):
  _inherit = 'purchase.order'

  contract_id = fields.Many2one('contract.management', string="Contract" , domain="[('customer_company','=',partner_id)]",track_visibility='onchange') #Гэрээ



  @api.multi
  def create_contract(self):
    vals = {
           'customer_company':self.partner_id.id,
           'agreed_currency':0.0,
           'contract_content':self.name +" ",
           'purchase_id':self.id,
           'contract_amount':self.amount_total,
                       }
    contract_id = self.env['contract.management'].create(vals)
    self.write({'contract_id':contract_id.id})
    return {
            'res_id': contract_id.id,
            'name': _('New'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'contract.management',
            'view_id': False,
            'views':[(False,'form')],
            'type': 'ir.actions.act_window',
        }