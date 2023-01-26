# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import time
from odoo.exceptions import UserError

class ReturnWorkService(models.TransientModel):
	'''
		Ажил үйлчилгээг мөрнөөс буцаах
	'''

	_name = 'return.work.service'


	@api.model
	def default_get(self, fields):

		res = super(ReturnWorkService, self).default_get(fields)	
		request_id = self.env['request.order.line'].browse(self._context.get('active_ids', []))
		res.update({'request_order_line_id':request_id.id})


		return res

	reason = fields.Text(string='Reason')
	request_order_line_id  = fields.Many2one('request.order.line')


	
	def action_to_return(self):
		total = 0
		unit = 0

		request_line_id = self.env['request.order.line'].browse(self.env.context.get('active_id'))

		if self.request_order_line_id.amount:
			unit = self.request_order_line_id.unit_price * 0.2
			total = self.request_order_line_id.amount + unit


		self.request_order_line_id.maintenance +=1
		request_line_history_id = self.env['request.order.line.history']
		request_line_history_id.create({
								'description':self.reason ,
								'maintenance':self.request_order_line_id.maintenance , 
								'service_id':request_line_id.service_id.id , 
								'order_line_id' : request_line_id.id ,
								'unit_price_20':unit,
								'state':'verify' if request_line_id.is_control else request_line_id.state,
								})
		self.request_order_line_id.write({'state':'pending',
										'is_evaluate': False,
										'is_control': False,
											
											})


		request_line_id.order_id.mail_send([request_line_id.perform_employee_id.user_id.id])


		