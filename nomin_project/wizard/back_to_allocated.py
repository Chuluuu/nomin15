# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import time
from odoo.exceptions import UserError

class BackToAllocated(models.TransientModel):
	'''
		Хуваарилагдсан төлөв рүү буцаах
	'''

	_name = 'back.to.allocated'
		

	@api.model
	def default_get(self, fields):

		res = super(BackToAllocated, self).default_get(fields)	
		order_id = self.env['order.page'].browse(self._context.get('active_ids', []))
		return res

	description = fields.Text(string='Description')
	
	def action_confirm(self):
		active_id = self._context.get('active_id')
		order_id = self.env['order.page'].browse(active_id)
		order_id.write({
                        	'description':self.description , 
                            'state' : 'allocated'})
		