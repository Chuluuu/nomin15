# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import time
from odoo.exceptions import UserError

class ImplementedTasks(models.TransientModel):
	'''Хийгдсэн ажлууд
	'''

	_name = 'implemented.tasks'

	@api.model
	def default_get(self, fields):
		res = super(ImplementedTasks, self).default_get(fields)	
		active_id = self._context.get('active_id')
		order_id= self.env['order.page'].browse(active_id)
		res.update({'employee_id':order_id.employee_id.id,
					'control_employee_id':order_id.control_employee_id.id,
					'confirm_employee_id':order_id.confirm_employee_id.id,
					})
		return res
	

	employee_id = fields.Many2one('hr.employee',string='Захиалагч ажилтан')
	control_employee_id = fields.Many2one('hr.employee',string='Хянах ажилтан')
	confirm_employee_id = fields.Many2one('hr.employee',string='Батлах ажилтан')
	
	line_ids = fields.One2many('implemented.task.line','line_id',string="Хийгдсэн ажлууд")


	
	def _add_followers(self,user_ids):
		'''Add followers
		'''
		partner_ids = [user.partner_id.id for user in self.env['res.users'].browse(user_ids) if user.partner_id]
		self.message_subscribe(partner_ids=partner_ids)

	def action_send(self):

		active_id = self._context.get('active_id')
		order_id = self.env['order.page'].browse(active_id)
		if self.employee_id.user_id.id :
			order_id.write({'receive_employee_id1':self.employee_id.id})
			order_id.sudo()._add_followers(self.employee_id.user_id.id)
		if self.control_employee_id.user_id.id :
			order_id.write({'receive_employee_id2':self.control_employee_id.id})
			order_id.sudo()._add_followers(self.control_employee_id.user_id.id)
		if self.confirm_employee_id.user_id.id :
			order_id.write({'receive_employee_id3':self.confirm_employee_id.id})
			order_id.sudo()._add_followers(self.confirm_employee_id.user_id.id)
		request_id = self.env['order.page'].browse(self._context.get('active_ids', []))	
		if self.line_ids:	
			for line in self.line_ids:
				self.env['server.info'].create({'task_id':request_id.id,
												'implemented_task':line.task , 
												'explanation' : line.description ,
												})
		request_id.write({'state':'handover',
						'handover_date':time.strftime("%Y-%m-%d")			
						})

class ImplementedTaskLine(models.TransientModel):
	'''Хийгдсэн ажлууд
	'''

	_name = 'implemented.task.line'

	line_id = fields.Many2one('implemented.tasks',string='Implemented task')

	task = fields.Char(string="Хийгдсэн ажил" )
	description = fields.Char(string="Тайлбар")
	
	

class OrderPageReceive(models.TransientModel):
	'''Хүлээн авах
	'''

	_name = 'order.page.receive'

	@api.model
	def default_get(self, fields):
		res = super(OrderPageReceive, self).default_get(fields)	
		active_id = self._context.get('active_id')
		order_id= self.env['order.page'].browse(active_id)
		res.update({'order_name':order_id.order_name,
					'order_description':order_id.result,
					'cost_type':order_id.cost_types,
					})
					
		if order_id.is_receive:
			res.update({'is_approve':order_id.is_receive})
		lines = []		
		is_checked = False
		for task in order_id.task_info:
			if task.is_check:
				is_checked= True 
		for task in order_id.task_info:
			# if is_checked and task.is_check:
			# 	lines.append((0,0,{'task':task.implemented_task,
			# 						'description':task.explanation,
			# 						'is_check':task.is_check,
			# 						'task_info_id':task.id # ID хадгалаах integer 
			# 					}))
			# elif not is_checked:
				lines.append((0,0,{'task':task.implemented_task,
									'description':task.explanation,
									'is_check':task.is_check,
									'comment':task.comment,
									'task_info_id':task.id # ID хадгалаах integer 
								}))
		res.update({'line_ids':lines})
		return res
		
	order_name = fields.Char(string='Захиалгын нэр')
	order_description = fields.Char(string='Зорилт')
	cost_type = fields.Selection([('cost_in','Дотоод зардал'),('payment','Нэг удаагийн төлбөр'),('rent_cost','Түрээсийн зардалд шингээх (МТС)'),('rent_cost_other','Түрээсийн зардалд шингээх (Бусад: __________________)')], string='Зардлын төрөл')
	is_approve = fields.Boolean(string='Захиалгатай холбоотой ажлуудыг хүлээн авч баталгаажуулж байна', default=False)
	is_reject = fields.Boolean(string='Дээр дутуу хэмээн тэмдэглэгдсэн ажлуудын гүйцэтгэлийг хүлээн авахаас өмнө баталгаажуулах боломжгүй', default=False)
	line_ids = fields.One2many('order.page.receive.line','line_id',string="Order page receive line")

	
	def to_receive(self):

		
	
		request_id = self.env['order.page'].browse(self._context.get('active_ids', []))

		request_id.message_post(body=u"Хүлээн авсан огноо haha %s " %(time.strftime("%Y-%m-%d")))
		#Визардын мөрөөр давтана чагталсан захиалгын хийгдсэн ажиллуудыг чагтлана
		for line in self.line_ids:
			if int(line.task_info_id) and line.is_check:
				info_id = self.env['server.info'].browse(int(line.task_info_id)) #Хадгалсан хийгдсэн ажиллалын мөрөөр browse хийнэ
				info_id.write({'is_check':line.is_check,
								'comment':line.comment
								}) # чагтлана

		count = []

		if self._uid not in request_id.confirmed_user_ids.ids:
			request_id.write({'confirmed_user_ids':[(6,0,[self._uid]+request_id.confirmed_user_ids.ids)]})

		if request_id.receive_employee_id1.id and request_id.receive_employee_id1.id not in count:
			count.append(request_id.receive_employee_id1.id)
		if request_id.receive_employee_id2.id and request_id.receive_employee_id2.id not in count:
			count.append(request_id.receive_employee_id2.id) 
		if request_id.receive_employee_id3.id and request_id.receive_employee_id3.id not in count:
			count.append(request_id.receive_employee_id3.id) 

		if self.is_approve and self.is_reject:
			raise UserError(_(u'Баталгаажуулалт буруу байна.'))

		if len(request_id.confirmed_user_ids)== len(count) and self.is_approve: 
			request_id.write({'state':'estimated',
							'review_date':time.strftime("%Y-%m-%d")	
								})
		if not self.is_approve :
			raise UserError(_(u'Баталгаажуулалт хийгдээгүй байна.'))
		if self.is_approve:
			request_id.write({'is_receive':self.is_approve,
								}) 

		

class OrderPageReceiveLine(models.TransientModel):


	_name = 'order.page.receive.line'

	line_id = fields.Many2one('order.page.receive',string='Implemented task')

	task = fields.Char(string="Хийгдсэн ажил" )
	description = fields.Char(string="Тайлбар")
	is_check = fields.Boolean(string="Чек",default=False)
	task_info_id = fields.Integer(string="Task info")
	comment = fields.Char(string="Хүлээн авсан ажилтны тайлбар")


	



