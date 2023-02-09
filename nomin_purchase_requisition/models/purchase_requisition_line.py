# -*- coding: utf-8 -*-
# from email.policy import default
#from email.policy import default
from this import d
from datetime import date, datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PurchaseRequisitionLine(models.Model):
	_inherit = 'purchase.requisition.line'
	_description = "Purchase Requisition Line"
	_rec_name = 'product_id'
	

	def _add_followers(self,user_ids): 
		'''Дагагч нэмнэ'''
		partner_ids = [user.partner_id.id for user in self.env['res.users'].browse(user_ids) if user.partner_id]
		self.message_subscribe(partner_ids=partner_ids)

	# 
	# @api.depends('supplied_quantities.supplied_product_quantity')
	# def _supplied_quantity(self):

	# 	for obj in self:
	# 		obj.supplied_quantity = sum([line.supplied_product_quantity for line in obj.supplied_quantities])

	# 
	# @api.depends('supplied_quantities.supplied_amount')
	# def _supplied_amount(self):

	# 	for obj in self:
	# 		obj.supplied_amount = sum([line.supplied_amount for line in obj.supplied_quantities])

	@api.onchange('assign_cat')
	def find_comparison(self):
		if self.assign_cat:
			comparison_employee = self.find_comparison_employee(self.assign_cat, self.allowed_amount)
			if comparison_employee:
				self.comparison_user_id = comparison_employee
	
	@api.onchange('category_id')
	def find_comparison_category(self):
		if self.category_id:
			comparison_employee = self.find_comparison_employee(self.category_id, self.allowed_amount)
			if comparison_employee:
				self.comparison_user_id = comparison_employee

	def _get_comparison_date(self):
		if self.date_start:
			if self.requisition_id:
				if self.requisition_id.priority_id:
					if self.requisition_id.priority_id.comparison_day:
						add_days = self.requisition_id.priority_id.comparison_day
						current_date = datetime.strptime(self.date_start, "%Y-%m-%d")
						while add_days > 0:
							current_date += timedelta(days=1)
							weekday = current_date.weekday()
							if weekday >= 5:
								continue
							add_days -= 1
						self.comparison_date = current_date
					else:
						raise UserError(u'Урьтамж дээр харьцуулалт хийх хоног тохируулагдаагүй байна.')
				else:
					raise UserError(u'Урьтамж сонгогдоогүй байна.')
	
	
	def _is_new_requisition(self):
		if datetime.now() > datetime.strptime('2022-09-29','%Y-%m-%d'):
			return True
		else:
			return False

	def _get_product_domain(self):
		context = self._context
		domain = []
		if not context.get('is_new_requisition'):
			domain = [(1,'=',1)]
		else:
			domain = [('product_tmpl_id.cost_price','>',0)]
			# domain = [('product_tmpl_id.is_new','=',True),('product_tmpl_id.cost_price','>',0)]
		if context.get('product_list_type') == 'normalized':
			domain += [('is_normalized','=',True)]
		if context.get('product_list_type') == 'new_set':
			domain += [('is_new_set','=',True)]
		return domain

	
	def _supplied_partner_count(self):
		for obj in self:
			obj.supplied_partner_count = 0
			if obj.supplied_quantities:
				obj.supplied_partner_count= len(obj.supplied_quantities)
	def _is_purchase_manager(self):
		purchase_manager = self.env.user.has_group('purchase.group_purchase_manager')
		if purchase_manager:
			self.is_purchase_manager = True
	
	def _get_comparison_users(self):
		user_ids = []
		comparison_emp_obj = self.env['comparison.employee.config'].search([(1,'=',1)])
		for item in comparison_emp_obj:
			if item.user_id:
				user_ids.append(item.user_id.id)
		return [('id','in',user_ids)]
	
	def _get_buyer(self):
		user_ids = []
		purchase_emp_obj = self.env['purchase.category.config'].search([(1,'=',1)])
		for item in purchase_emp_obj:
			if item.user_id:
				user_ids.append(item.user_id.id)
		return [('id','in',user_ids)]

	COMPARISON_STATE_SELECTION = [('draft', 'Draft'),
						('sent', 'Sent'),  # Илгээгдсэн
						('approved', 'Approved'),  # Зөвшөөрсөн
						('verified', 'Verified'),  # Хянасан
						('confirmed', 'Confirmed'),  # Батласан
						('canceled', 'Canceled'),  # Цуцлагдсан
						('purchase', 'Purchase'), #Худалдан авалт
									]

	STATE_SELECTION=[('draft',u'Ноорог'),
											 ('sent','Илгээгдсэн'),#Илгээгдсэн
											 ('approved','Зөвшөөрсөн'),#Зөвшөөрсөн
											 ('verified','Хянасан'),#Хянасан
											 ('next_confirm_user','Дараагийн батлах хэрэглэгчид илгээгдсэн'),#Дараагийн батлах хэрэглэгчид илгээгдсэн
											 ('confirmed','Батласан'),#Батласан
											 ('tender_created','Тендер үүссэн'),#Тендер үүссэн
											#  ('tender_request','Тендер зарлуулах хүсэлт'),#Тендер зарлуулах хүсэлт
											#  ('sent_to_supply','Хангамжаарх худалдан авалт'),#Хангамжаарх худалдан авалт
											#  ('fulfil_request','Биелүүлэх хүсэлт'),# Биелүүлэх хүсэлт
											#  ('rfq_created','Үнийн санал үүссэн'),#Үнийн санал үүссэн
											#  ('fulfill','Биелүүлэх'),# Биелүүлэх
											 ('compare','Харьцуулалт хийх'),# Харьцуулалт хийх
											 ('compared','Харьцуулалт үүссэн'),# Харьцуулалт хийх
											 ('sent_to_accountant','Салбарын нягтланд илгээгдсэн'), # Салбарын нягтланд илгээгдсэн
											 ('assigned','Assigned'),#Хуваарилагдсан
											 ('retrived','Буцаагдсан'),# Буцаагдсан
											#  ('retrive_request','Буцаагдах хүсэлт'),# Буцаагдах хүсэлт
											 ('rejected','Татгалзсан'),
											 ('canceled','Цуцлагдсан'),#Цуцлагдсан
											 ('ready','Хүлээлгэж өгөхөд бэлэн'),
											#  ('purchased','Худалдан авалт үүссэн'),#Худалдан авалт үүссэн
											 ('sent_to_supply_manager','Бараа тодорхойлох'),#Хангамж импортын менежер
											 ('done',u'Дууссан'),
											 ('sent_nybo',u'Нягтлан бодогчид илгээгдсэн')
											 # ('rated',u'Үнэлэгдсэн'),
																	 ]
	state_history_ids = fields.One2many('purchase.requisition.line.state.history', 'requisition_line_id', string='Purchase Requisition Line State History')
	product_id = fields.Many2one('product.product', string='Product', domain=_get_product_domain)
	category_id = fields.Many2one('product.category',string='Product category')
	department_id = fields.Many2one(related='requisition_id.department_id', string='Department', store=True, readonly=True)
	sector_id = fields.Many2one(related='requisition_id.sector_id', string='Sector', store=True, readonly=True)
	checkbox =  fields.Boolean(string='Checkbox')
	market_price = fields.Float(string='Market Price', readonly=True)
	product_type = fields.Selection([('furniture','Furniture'),#Тавилга эд хогшил
																			 ('other_asset','Other asset'),#Бусад хөрөнг
																			 ('computer_equip','Computer equipment'),#Компьютор тоног төхөөрөмж
																			 ('electronic_equip','Electronic equipment'),#Бусад цахилгаан хэрэгсэл
																			 ('paper_book','Paper book'),#Бичиг хэрэг
																			 ('cleaing_material','Cleaning material'),#Цэвэрлэгээний материал
																			 ('work_clothes','Work clothes'),#Ажлын хувцас
																			 ('other_product','Other product'),#Бусад бараа
																			 ('construct_material','Contstruct material'),#Барилгын заслын материал
																			 ('electric_material','Electric material'),#Цахилгааны материал
																			 ('plumbing_material','Plumbin material'),#Сан техникийн материал
																			 ('cooling_material','Cooling material'),#Хөргөлтийн материал
																			 ('print_order','Print order'),#Дизайн рекламны материал
																			 ('transport_equip','Transport equipment'),#Машин тоног төхөөрөмж,багаж
																			 ('vehicle','Vehicle'),#Тээврийн хэрэгсэл
																			 ('spare',u'Сэлбэг'),#Сэлбэг,
																			 ('service',u'Үйлчилгээ'),
																			 ('construction_work','Construction work'),#Барилгын заслын ажил
																			 ('plumbing_service','Plumbing service'),#Сантехникийн ажил үйлчилгээ
																			 ],string=u'Төрөл')
	product_desc= fields.Text(string='Description')
	purpose = fields.Char(string='Purpose')
	oversize = fields.Char(string='Oversize')
	color = fields.Char(string='Color')
	material = fields.Char(string='Material')
	rating = fields.Char(string='Rating')
	brand = fields.Char(string='brand')
	attachment_id = fields.Many2many('ir.attachment','purchase_requisition_attachment_id','line_id','attach_id',string='Ir attachment', domain="[('requisition_id','=',id)]")
	the_size = fields.Char( string='The size of work')
	country = fields.Char(string='Country')
	product_price = fields.Float(string='Product unit price')
	buyer = fields.Many2one('res.users', string='Buyer', tracking=True,domain=_get_buyer)
	state = fields.Selection(STATE_SELECTION,
				string='Status', tracking=True, required=True)
	user_id = fields.Many2one(related='requisition_id.user_id',string='User', store=True, readonly=True)
	date_start = fields.Date(string='date start', tracking=True)
	date_end = fields.Date(string='date end', tracking=True)
	reg_file = fields.Many2one('ir.attachment',string='Ir attachment')
	accountant_id = fields.Many2one('res.users', string='Accountant', tracking=True)
	accountant_ids = fields.Many2many('res.users', string='Accountant', tracking=True)
	supplied_quantities = fields.One2many('purchase.requisition.supplied.quantity', 'line_id', string='Supplied Quantities')
	_defaults = {
							'product_qty':1,
							'product_type':'other_product',
							'state':'draft',
								 }

	comparison_user_id = fields.Many2one('res.users',string='Comparison employee', domain=_get_comparison_users , tracking=True)
	comparison_id = fields.Many2one('purchase.comparison',string='Comparison')
	comparison_state = fields.Selection(COMPARISON_STATE_SELECTION, string='Comparison state')
	comparison_date_end = fields.Date(string='Comparison date end')
	comparison_date = fields.Date(string='Comparison date')
	comparison_sent_date = fields.Datetime(string='Comparison sent date')
	comparison_confirmed_date = fields.Datetime(string='Comparison confirmed date')
	partner_id = fields.Many2one('res.partner', string="Харилцагч")
	supplied_quantity = fields.Float(string='Нийлүүлсэн тоо')
	supplied_amount = fields.Float(string='Нийлүүлсэн Дүн')
	supplied_price = fields.Float(string='Нийлүүлсэн нэгж үнэ')
	deliver_product_id = fields.Many2one('product.product', string='Нийлүүлсэн барааны нэр', domain=_get_product_domain)
	is_new_requisition = fields.Boolean(string='is_new_requisition',default=_is_new_requisition)
	supplied_partner_count = fields.Float(string='Нийлүүлсэн харилцагчийн тоо', compute=_supplied_partner_count)
	is_purchase_manager = fields.Boolean(string='is purchase manager',compute=_is_purchase_manager)


	# @api.onchange('partner_id')
	# def onchange_partner_id(self):
	# 	if self.product_id:
	# 		self.deliver_product_id = self.product_id
	# 		self.supplied_quantity = self.product_qty

	@api.onchange('deliver_product_id')
	def onchange_deliver_product(self):
		try:
			# USED Try except for cost_price field bcuz cost_price field is in other module
			self.supplied_price = self.deliver_product_id.sudo().cost_price
		except Exception:
			self.supplied_price = self.deliver_product_id.sudo().standard_price
			pass

	@api.onchange('supplied_quantity','supplied_price')
	def onchange_supplied_quantity(self):
		if self.supplied_price:
			self.update({'supplied_amount': self.supplied_quantity * self.supplied_price})

	# @api.model
	# def create(self, vals):
	# 	result = super(PurchaseRequisitionLine,self).create(vals)

	# 	if vals.get('deliver_product_id'):
	# 		result.supplied_price = result.deliver_product_id.sudo().lst_price
	# 	if vals.get('supplied_quantity'):
	# 		result.update({'supplied_amount': vals.get('supplied_quantity') * result.supplied_price})


	
	def write(self, vals):
		if vals.get('state'):
			for line in self:
				line_vals = {
					'user_id':self.env.user.id,
					'state': vals.get('state') if 'state' in vals else line.state,
					'requisition_line_id':line.id,
					'date': date.today(),
					}
				self.env['purchase.requisition.line.state.history'].create(line_vals)
		if vals.get('deliver_product_id'):
			try:
				self.supplied_price = self.deliver_product_id.sudo().cost_price
			except Exception:
				self.supplied_price = self.deliver_product_id.sudo().standard_price
				pass
		if vals.get('supplied_quantity'):
			self.update({'supplied_amount': vals.get('supplied_quantity') * self.supplied_price})
				
		result = super(PurchaseRequisitionLine,self).write(vals)
		if vals.get('partner_id') or vals.get('supplied_quantity'):
			if len(self.supplied_quantities) == 0:
				vals = {
					'line_id': self.id,
					'partner_id': vals.get('partner_id'),
					'supplied_product_id':self.deliver_product_id.id,
					'supplied_product_price':self.supplied_price,
					'supplied_product_quantity':self.supplied_quantity,
					'supplied_amount':self.supplied_amount,
					'user_id':self.env.user.id
				}
				supplied_obj = self.env['purchase.requisition.supplied.quantity'].create(vals)
			elif len(self.supplied_quantities) == 1: 
				self.supplied_quantities.update({'partner_id': vals.get('partner_id'),
												 'supplied_product_quantity':self.supplied_quantity,
												 'supplied_amount':self.supplied_quantity * self.product_price,})
			else:
				raise UserError('Харилцагч нэмэх товч дарж нийлүүлсэн бараагаа оруулана.')
		# for line in self:
		# 	if line.supplied_quantity>line.allowed_qty :
		# 		raise UserError('Зөвшөөрөгдсөн тооноос олныг олгож болохгүй!!!')

		# 	if line.supplied_amount>line.allowed_amount :
		# 		raise UserError('Зөвшөөрөгдсөн дүнгээс их дүнтэй бараа олгож болохгүй!!!')

		return result

	
	def action_purchase_line_open(self):

		mod_obj = self.env['ir.model.data']

		return {
			'name': 'Note',
			'view_mode': 'form',
			'res_model': 'purchase.requisition.line.wizard',
			'context': self._context,
			'type': 'ir.actions.act_window',
			'nodestroy': True,
			'target': 'new',
		}

class purchase_requisition_supplied_quantity(models.Model):
	_name = 'purchase.requisition.supplied.quantity'

	def _supplied_product_price(self):

		line_id = self.env['purchase.requisition.line'].browse(self.env.context.get('id2'))
		return line_id.product_price

	user_id = fields.Many2one('res.users', string="Sales person",default=lambda self: self.env.user)
	line_id = fields.Many2one('purchase.requisition.line', string="Requisition Line")
	partner_id = fields.Many2one('res.partner', string="Харилцагч")

	supplied_product_id = fields.Many2one('product.product', string='Нийлүүлсэн барааны нэр', domain=[('product_tmpl_id.cost_price','>',0)])
	# supplied_product_id = fields.Many2one('product.product', string='Нийлүүлсэн барааны нэр', domain=[('product_tmpl_id.is_new','=',True),('product_tmpl_id.cost_price','>',0)])
	# supplied_product_description = fields.Char(string='Нийлүүлсэн барааны тодорхойлолт')  
	supplied_product_price = fields.Float(string='Supplied Product Price', default=_supplied_product_price)
	supplied_product_quantity = fields.Float(string='Supplied Product Quantity')
	supplied_amount = fields.Float(string='Supplied Amount')

	@api.model
	def create(self, vals):


		result = super(purchase_requisition_supplied_quantity, self).create(vals)

		if result.supplied_product_id:
			try:
				result.update({'supplied_product_price':result.supplied_product_id.sudo().cost_price})
			except Exception:
				result.update({'supplied_product_price':result.supplied_product_id.sudo().standard_price})
				pass
		if vals.get('supplied_product_quantity'):
			result.update({'supplied_amount':result.supplied_product_quantity * result.supplied_product_price})

		# if result.supplied_product_price == 0.0:
		# 	raise UserError('Барааны үнийг 0.00-р оруулж болохгүй!!!')
		# if result.supplied_product_quantity == 0.0:
		# 	raise UserError('Барааны тоо ширхэгийг 0-р оруулж болохгүй!!!')
		
		return result
		


	
	def write(self, vals):


		supplied_product_quantity = self.supplied_product_quantity
		if vals.get('supplied_product_quantity'):
			supplied_product_quantity = vals.get('supplied_product_quantity')

		supplied_product_price = self.supplied_product_price
		if vals.get('supplied_product_price'):
			supplied_product_price = vals.get('supplied_product_price')

		vals.update({
				'supplied_amount':supplied_product_price*supplied_product_quantity
				})

		return super(purchase_requisition_supplied_quantity, self).write(vals)    


	@api.onchange('supplied_product_price','supplied_product_quantity')
	def onchange_supplied_amount(self):
		self.supplied_amount = self.supplied_product_quantity * self.supplied_product_price
		

	
	def unlink(self):

		for self1 in self:
			
			if self1.env.user.id == self1.user_id.id or self1.env.user.has_group('nomin_hr.group_hr_admin'):
				return super(purchase_requisition_supplied_quantity, self1).unlink() 
			else:
				raise UserError(_(u'Та зөвхөн өөрийнхөө үүсгэсэнг л устгах боломжтой'))

class purchase_order_line(models.Model):
	_inherit = 'purchase.order.line'
	

	requisition_line_id = fields.Many2one('purchase.requisition.line',string="requisition line")

	




