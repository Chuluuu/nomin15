# -*- coding: utf-8 -*-
from openerp import api, fields, models, _
import time
from openerp.exceptions import UserError

class RejectWorkService(models.TransientModel):
	'''
		Ажил үйлчилгээг мөр дээр цуцлах
	'''

	_name = 'reject.work.service'


	@api.model
	def default_get(self, fields):

		res = super(RejectWorkService, self).default_get(fields)	
		request_id = self.env['request.order'].browse(self._context.get('active_ids', []))


		return res

	
	reason = fields.Text(string="Reason")

	@api.multi
	def action_reject(self):

		request_line_id = self.env['request.order.line'].browse(self.env.context.get('active_id'))
		if request_line_id.amount:
				unit = request_line_id.unit_price * 0.2
				total = request_line_id.amount + unit
		
		request_line_history_id = self.env['request.order.line.history']
		if request_line_id.is_control:
			request_line_history_id.create({
									'description':self.reason ,
									'maintenance':request_line_id.maintenance , 
									'service_id':request_line_id.service_id.id , 
									'order_line_id' : request_line_id.id ,
									'unit_price_20':unit,
									'state':'verify' if request_line_id.is_control else request_line_id.state,
									})
		request_line_id.write({
								'description':self.reason , 
								'state' : 'rejected' ,
								'is_evaluate': False,
								'is_control': False,

								})
		is_change = True
		if request_line_id:
			for line in request_line_id.order_id.line_ids:            
				if line.state !='rejected':
					is_change =False
		if is_change:
			request_line_id.order_id.action_cancel()



		request_line_id.order_id.mail_send([request_line_id.order_id.employee_id.user_id.id])


