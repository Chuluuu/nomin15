# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError




class refuse_reason_order(models.TransientModel):
    _name = 'refuse.reason.order'
    _description = 'Refuse reason order'
    
    comment = fields.Text('Commit', required=True)
    
    @api.multi
    def refuse_order(self):
        context = self._context
        #commet = u'Татгалзсан шалтгаан: %s'%(self.comment)
        if context.get('active_model') and context.get('active_id'):
            if context['active_model'] == 'order.page' and context['active_id']:
                active_obj = self.env['order.page'].browse(context['active_id'])
                active_obj.rejection_reason = self.comment
                active_obj.state = 'rejected'
                 
        return {'type': 'ir.actions.act_window_close'}