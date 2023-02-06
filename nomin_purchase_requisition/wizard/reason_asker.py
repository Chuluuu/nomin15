# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ReasonAsker(models.TransientModel):
    _name = 'nomin.purchase.requisition.asker'

    reason = fields.Selection([
                        ('missing_something','Өгөгдөл дутуу оруулсан'),
                        ('wrong_data','Буруу өгөгдөл сонгосон'),
                        ], 'Reason', default = 'missing_something')
    description = fields.Text('Description')

    
    def button_accept(self):
        context = self._context
        if not context.get('active_model') and not context.get('active_id'):
            return {'type': 'ir.actions.act_window_close'}

        if context['active_model'] != 'asset.transfer.request' and not context['active_id']:
            return {'type': 'ir.actions.act_window_close'}

        active_obj = self.env['asset.transfer.request'].browse(context['active_id'])
        # active_obj.returned_reason = dict(self._fields['reason'].selection).get(self.reason)
        # active_obj.returned_reason = self.reason
        if self.description:
            active_obj.returned_description = self.description


        if active_obj.reverse():
            active_obj.state = 'returned'
                


        return {'type': 'ir.actions.act_window_close'}

  