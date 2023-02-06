# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class purchase_requisition_line_order_line(models.Model):
	_name = 'purchase.requisition.line.order.line'

	requisition_line_id = fields.Many2one('purchase.requisition.line',string='Purchase requisition line number') #Шаардахын мөрийн дугаар
	order_line_id = fields.Many2one('purchase.order.line', string='Order line') #Захиалгын мөр

