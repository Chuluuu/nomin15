# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.tools.translate import _
from odoo.exceptions import UserError

class SkipPurchaseComparison(models.TransientModel):
    _name = 'skip.purchase.comparison'
    _description = 'skip purchase comparison'
    
        
    
    def action_skip_comparison(self):

        active_ids = self.env.context.get('active_ids', [])
        for line in self.env['purchase.requisition.line'].browse(active_ids):
            if line.state != 'compare':
                raise UserError(_(u'Харцуулалт хийх төлөвтэй шаардахын мөрийг харьцуулалт алгасах боломжтой.'))
            if line.allowed_amount != 0:
                comparison_config_obj = self.env['comparison.employee.config'].search([('category_ids','in',line.category_id.id),('user_id','=',line.comparison_user_id.id)])
                if line.allowed_amount < comparison_config_obj.comparison_value:
                    raise UserError(_(u'%s дугаартай шаардахын мөрийг харьцуулалтын ажилтан харьцуулалт алгасах боломжтой.'%(line.requisition_id.name)))
            
            line.write({'state': 'ready'})
