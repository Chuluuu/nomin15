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
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from openerp import models, fields, api, _
from dateutil.relativedelta import relativedelta
from lxml import etree
from openerp.exceptions import UserError

class PurchaseOrderSeparation(models.TransientModel):
    
    _name = 'purchase.order.separation'
    _description = 'Purchase Order Separation'
    
    basic_id = fields.Many2one("purchase.order", string="Basic Purchase Order",required=True)  #default=_get_default_basic,
    follow_ids = fields.Many2many("purchase.order", "purchase_order_separation_rel", "wizard_id", "purchase_order_id", "Purchase Order",  required=True) #default=_get_default_follow,
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(PurchaseOrderSeparation, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        context = self._context
        doc = etree.XML(res['arch'])
        model = self.env.context.get('active_model', False)
        record = self.env[model].browse(self.env.context.get('active_id',False))
        domain_ids = []
        
        res['arch'] = etree.tostring(doc)
        return res
    
    @api.multi
    def action_separation(self):
        purchase_obj = self.env['purchase.order']
        if self.follow_ids:
            self.follow_ids.write({'parent_id': False})
