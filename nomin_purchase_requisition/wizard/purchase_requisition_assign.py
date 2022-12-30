# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.http import request
import time
import datetime
import openerp.pooler
import openerp.addons.decimal_precision as dp

class purchase_requisition_assign(models.TransientModel):
    _name = "purchase.requisition.assign"
    _description = "Purchase Requisition Assign"
    
    buyer = fields.Many2one('res.users', 'Buyer', required=True)
    helper = fields.Many2one('res.users', 'Helper')
    
    @api.multi
    def add_req_line_state_history(self,line, state):
        self.env['purchase.requisition.line.state.history'].create({
                                                                'requisition_line_id': line.id,
                                                                'user_id': self._uid,
                                                                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                                                                'state': state
                                                                })
    @api.multi
    def create_assignment(self):
        active_ids = self._context and self._context.get('active_ids', [])
        requisition_ids = []
        buyers = []
        
        requisition_obj = self.env['purchase.requisition.line'].browse(active_ids)
        for line in requisition_obj:
            if line.requisition_id not in requisition_ids:    
                requisition_ids.append(line.requisition_id)
        for line in requisition_obj:            
            if line.state in ['fulfill','assigned']:                
                line.write({'buyer': data.buyer.id,'state': 'assigned'})
                if data.buyer.partner_id.id not in line.requisition_id.message_partner_ids.ids:
                    self.env['mail.followers'].create({'subtype_ids':[(6, 0, [1])],'res_model':'purchase.requisition',
                        'res_id':line.requisition_id.id, 
                        'partner_id':data.buyer.partner_id.id})
                self.add_req_line_state_history( line, 'assigned')
            else:
                raise osv.except_osv(_(u'Анхааруулга!'), _(u'Та зөвхөн биелүүлэх төлөв дээр ажилтан хувиарлаж болно'))
        is_state = False
        if buyers:
            buyers = list(set(buyers))
            
        for req in requisition_ids:

            for line in  req.line_ids:
                if line.state !='assigned':
                    is_state =True
            if not is_state:
                req.write({'state':'assigned'})

        return {'type': 'ir.actions.act_window_close'}
