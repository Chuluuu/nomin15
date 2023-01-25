# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
import time
from openerp.tools.translate import _
from openerp.exceptions import UserError, ValidationError

class AddComparisonProduct(models.TransientModel):
    _name = 'add.comparison.product'

    @api.model
    def _get_comparison(self):
        if self._context.get('comparison_id'):
            return self._context.get('comparison_id')
        return None

    comparison_id = fields.Many2one('purchase.comparison', default=_get_comparison)
    product_ids = fields.One2many('purchase.comparison.multiple.product','add_product_id',string='Product')

    @api.multi
    def action_add_product(self):
        is_product_created = None
        for line in self.comparison_id.order_ids:
            for product_line in self.product_ids:
                if not self.env['purchase.order.line'].search([('product_id','=',product_line.product_id.id),('order_id','=',line.id)]):
                    if product_line.product_qty > 0:
                        is_product_created = self.env['purchase.order.line'].create({
                            'product_id': product_line.product_id.id,
                            'product_qty': product_line.product_qty,
                            'order_id': line.id,
                            'product_uom': product_line.product_id.uom_id.id,
                            'name': product_line.product_id.product_mark,
                            'price_unit': product_line.price_unit,
                            'date_planned': time.strftime('%Y-%m-%d'),
                            'market_price': product_line.market_value,
                            'market_price_total': product_line.market_price_total,
                            'price_subtotal': product_line.price_subtotal,
                        })
                    else:
					    raise UserError(u'Барааны тоо хэмжээ 0-ээс их байх ёстойг анхаарна уу.')


        if not is_product_created:
            raise UserError(u'Бүх харилцагчид бүртгэлтэй бараа байна.')

        return {'type': 'ir.actions.act_window_close'}