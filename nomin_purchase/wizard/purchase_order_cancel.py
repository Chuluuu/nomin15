# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class purchase_order_cancel(models.TransientModel):    
    _name ='purchase.order.cancel'
    
    note = fields.Text(string='Note') #Тэмдэглэл
    
    def order_cancel(self):
        active_ids = self.env.context.get('active_ids', [])
        purchase = self.env['purchase.order'].browse(active_ids)
        # purchase.button_cancel()
        purchase.write({'active_sequence':'1','state':'draft'})
        purchase.message_post(body= u"Буцаасан шалтгаан: "+self.note)
        return {'type': 'ir.actions.act_window_close'}