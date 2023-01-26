# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import time
from odoo.exceptions import UserError

class ToEvaluateEmployee(models.TransientModel):
	'''
		Ажил үйлчилгээг мөр дээр үнэлэх
	'''

	_name = 'to.evaluate.employee'
		

	@api.model
	def default_get(self, fields):

		res = super(ToEvaluateEmployee, self).default_get(fields)	
		request_id = self.env['request.order'].browse(self._context.get('active_ids', []))


		return res

	description = fields.Text(string='Description')
	assessment = fields.Float(string='Үнэлгээ' , default=100)


	
	def action_to_evaluate(self):

		request_line_id = self.env['request.order.line'].browse(self.env.context.get('active_id'))
		request_line_id.file_attach()
		# attach_ids = request_line_id.order_id.attach_line_ids.ids
		# if attach_ids:
		# 	self.env.cr.execute('select ir_attachment_id from ir_attachment_request_order_attachment_rel where request_order_attachment_id in %s'%(str(tuple(attach_ids))))
		# fetchall = self.env.cr.fetchall()
		# for fetch in fetchall:
		# 	for line in request_line_id.order_id.line_ids: 
		# 		if line.task_id and line.task_id.task_state not in ['t_evaluate','t_canceled','t_back','t_done']:
		# 			self._cr.execute('UPDATE ir_attachment set project_task_document=%s WHERE id =%s'%(line.task_id.id,fetch[0]))
		request_line_id.write({
								'description':self.description , 
								'rate' : self.assessment ,
								'state' : 'done' ,
								'is_evaluate': False,
								'date_evaluate': time.strftime("%Y-%m-%d") ,

								})
		is_change = True
		if request_line_id:
			for line in request_line_id.order_id.line_ids:            
				if line.state not in ['done','rejected']:
					is_change =False
		if is_change:
			request_line_id.order_id.action_approve()



		request_line_id.order_id.sudo().mail_send([request_line_id.perform_employee_id.user_id.id,request_line_id.order_id.employee_id.user_id.id])
		
		


							
	
		
