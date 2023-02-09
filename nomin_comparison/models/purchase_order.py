# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from fnmatch import translate
from odoo.osv import osv

class purchase_order(models.Model):
	_inherit = 'purchase.order'

	STATE_SELECTION = [
	('draft', u'Ноорог PO'),
        ('sent', u'Илгээгдсэн'),
        ('sent_rfq', u'Үнийн санал авах'),
        ('back', u'Үнийн санал ирсэн'),
        ('comparison_created',u'Харьцуулалт үүссэн'),
        ('to approve', u'Зөвшөөрөх'),
        ('approved', u'Зөвшөөрсөн'),
        ('purchase', u'Худалдан авах захиалга'),
        ('verified',u'Хянасан'),
        ('confirmed',u'Батласан'),
        ('done', u'Дууссан'),
        ('cancel', u'Цуцлагдсан')
        
#         ('draft', 'Draft PO'),
#         ('sent', 'Sent'),
#         ('sent_rfq', 'RFQ Sent'),
#         ('back', 'RFQ Back'),
#         
#         ('to approve', 'To Approve'),
#         ('approved', 'Approved'),
#         ('purchase', 'Purchase Order'),
#         ('verified','Verified'),
#         ('confirmed','Confirmed'),
#         ('done', 'Done'),
#         ('cancel', 'Cancelled')
        ]
	purchase_type= fields.Selection([('direct','Direct',),('compare','compare')],string="Purchase type",default='direct',tracking=True)
	state = fields.Selection(STATE_SELECTION, string='Status', readonly=True, select=True, copy=False, default='draft', tracking=True)
	# comparison_id= fields.Many2one('purchase.comparison',string='Purchase Comparison')
	comparison_id = fields.Many2one('purchase.comparison', string="Purchase comparison",tracking=True)
	contract_id = fields.Many2one('contract.management', string="Contract" ,tracking=True) #Гэрээ

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
            'view_mode': 'tree,form',
            'res_model': 'contract.management',
            'view_id': False,
            'views':[(False,'form')],
            'type': 'ir.actions.act_window',
        }