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

class PurchaseOrderMerge(models.TransientModel):
    
    _name = 'purchase.order.merge'
    _description = 'Purchase Order Merge'
    
    @api.model
    def _get_default_basic(self):
        active_id = self.env.context.get('active_id', False)
        return active_id

    
    basic_id = fields.Many2one("purchase.order", string="Basic order",
                                 default=_get_default_basic, readonly=True)
    
    follow_ids = fields.Many2many("purchase.order", "purchase_order_merge_rel", "wizard_id", 
                                  "purchase_order_id", "Purchase Order", required=True)
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(PurchaseOrderMerge, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        context = self._context
        doc = etree.XML(res['arch'])
        active_ids = self.env.context.get('active_ids', [])
        active_id = self.env.context.get('active_id', False)
        domain_ids = active_ids
        if len(active_ids) == 1:
            model = self.env.context.get('active_model', False)
            record = self.env[model].browse(self.env.context.get('active_id',False))
                
        active_id=self._get_default_basic()
        if active_id:
            domain_ids.remove(active_id)
        domain_ids = sorted(domain_ids)
        for node in doc.xpath("//field[@name='follow_ids']"):
            node.set('domain', "[('id', 'in',["+','.join(map(str,domain_ids))+"])]")
        res['arch'] = etree.tostring(doc)
        return res
    
    
    @api.multi
    def action_merge(self):
        purchase_obj = self.env['purchase.order']
        if self.follow_ids and self.basic_id:
            if self.follow_ids.ids:
                partner_id = self.follow_ids[0].partner_id
                for follow in self.follow_ids:
                    if follow.partner_id != partner_id:
                        raise UserError(_('You can not merge a %s this purchase order . Because, This orders partner in wrong !.'%(follow.name)))
                self.follow_ids.write({'parent_id': self.basic_id.id})
                for line in self.follow_ids:
                    for line1 in line.order_line:
                        line1.write({
                                     'order_id': self.basic_id.id
                                     })

            