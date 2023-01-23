# -*- coding: utf-8 -*-


from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class purchase_tender(models.TransientModel):
    _name = "purchase.tender.wizard"
    _description = "Purchase Tender"
    
    partner_ids = fields.One2many('purchase.tender.line', 'wizard_id', 'Partner')
    
    
    def create_order(self):
        '''Хаалттай тендерийг цуцалж худалдан авалт үүсгэх'''
        active_ids = self._context and self._context.get('active_ids', [])
        
        if not self.partner_ids:
            raise UserError(_('Warning!'),_(u'Эхлэх огноо одоогийн цагаас бага байна.'))
            
        
        purchase_obj = self.env['purchase.order']
        purchase_line_obj = self.env['purchase.order.line']
        tender_obj = self.env['tender.tender']
        tender = tender_obj.browse(active_ids)
        values = {}
        
        for line in self.partner_ids:
            values = {
                      'tender_id': active_ids[0],
                      'rfq_department_id':tender.department_id.id,
                      'department_id':tender.respondent_department_id.id,
                      'sector_id':tender.respondent_department_id.id,
                      'date_planned':tender.ordering_date,
                      'requisition_id':tender.requisition_id.id,
                      'partner_id':line.partner_id.id,
                      'user_id': self._uid
                      }
            order_id = purchase_obj.create(values)

            for product in tender.tender_line_ids:
                vals = {
                        'order_id': order_id.id,
                        'product_id':product.product_id.id,
                        'product_qty':product.product_qty,
                        'name':product.product_id.name,
                        'date_planned':tender.ordering_date,
                        'price_unit':0.0,
                        'product_uom':product.product_uom_id.id,
                        } 
                purchase_line_obj.create(vals)
        tender.write({
                      'state': 'open_purchase',
                    })
        tender.send_notification('open_purchase')

class purchase_tender_line(models.TransientModel):
    _name = "purchase.tender.line"
    _description = "Purchase Tender Line"
    '''Тендерээс худалдан авалт үүсгэх
    '''
    wizard_id   = fields.Many2one('purchase.tender.wizard', 'Purchase', )
    partner_id  = fields.Many2one('res.partner', 'Partner', required=True)
    
