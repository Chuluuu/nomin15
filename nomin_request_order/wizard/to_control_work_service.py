# -*- coding: utf-8 -*-
from openerp import api, fields, models, _
import time
from openerp.exceptions import UserError

class ToControlWorkService(models.TransientModel):
	'''
		Ажил үйлчилгээг мөр дээр үнэлэх
	'''

	_name = 'to.control.work.service'
	

	@api.model
	def default_get(self, fields):

		res = super(ToControlWorkService, self).default_get(fields)	
		request_id = self.env['request.order'].browse(self._context.get('active_ids', []))


		return res

	description = fields.Text(string='Description')
	# rate = fields.Float(string='Assessment' , defaut=100)


	@api.multi
	def action_control(self):

		request_line_id = self.env['request.order.line'].browse(self.env.context.get('active_id'))
		request_line_id.file_attach()
		request_line_id.write({
								'description':self.description , 
								'state' : 'control' ,
								'is_evaluate': False,
								'is_control': False,

								})
		is_change = 0
		for line in request_line_id.order_id.line_ids:
			if line.state in ['control','done','rejected']:
				is_change +=1

		if is_change == len(request_line_id.order_id.line_ids):
			request_line_id.order_id.action_approve()



		request_line_id.order_id.mail_send([request_line_id.perform_employee_id.user_id.id,request_line_id.order_id.employee_id.user_id.id])