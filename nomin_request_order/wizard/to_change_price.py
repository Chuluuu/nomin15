# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import time
from lxml import etree
from odoo.exceptions import UserError

class ChangePrice(models.TransientModel):
	'''
		Үнэ өөрчлөх
	'''

	_name = 'to.change.price'
		

	@api.model
	def default_get(self, fields):

		res = super(ChangePrice, self).default_get(fields)	
		request_id = self.env['request.order'].browse(self._context.get('active_ids', []))

		return res

	change_description = fields.Text(string='Change price description')
	change_price = fields.Float(string="Unit price")
	amount  = fields.Float(string="Дүн" , store=True)
	


	
	def to_change_price(self):

		request_line_id = self.env['request.order.line'].browse(self.env.context.get('active_id'))
		request_line_id.write({'change_description':self.change_description ,
								'unit_price_change':self.change_price,
								'is_invisible_button':True								
								})
		self.amount = request_line_id.qty * request_line_id.percent_change * request_line_id.unit_price_change
		request_line_id.write({
								'amount':self.amount
								})

class LineReject(models.TransientModel):
	'''
		Мөрөөр цуцлах
	'''

	_name = 'line.reject'
		

	@api.model
	def default_get(self, fields):

		res = super(LineReject, self).default_get(fields)	
		request_id = self.env['request.order'].browse(self._context.get('active_ids', []))

		return res

	reject_description = fields.Text(string='Reject description')
	
	


	
	def line_reject(self):

		request_line_id = self.env['request.order.line'].browse(self.env.context.get('active_id'))
		is_change = 0
		for line in request_line_id:		
			line.write({'state':'rejected',
						'is_reject':True,		      
						'amount':0.0 ,
						'is_control':False  })
		for line in request_line_id.order_id.line_ids:
			if line.state in ['control','done','rejected']:
				is_change +=1

		if is_change == len(request_line_id.order_id.line_ids):
			request_line_id.order_id.action_approve()
		elif len(request_line_id.order_id.line_ids) == 1:
			request_line_id.order_id.action_cancel()

		request_line_id.write({'description':self.reject_description})
		
		
		
