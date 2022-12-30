# -*- coding: utf-8 -*-
from openerp import api, fields, models, _
from datetime import datetime, timedelta,date
import time
from openerp.http import request
import logging
from openerp.exceptions import UserError, AccessError
from openerp.osv import osv
_logger = logging.getLogger(__name__)



class StockRequisition(models.Model):
	_name ='stock.requisition'
	_description = 'Stock requisition'
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_order = 'create_date desc'

	@api.multi
	def _set_company(self):
		
		if self.env.user.department_id.id:
			return self.env.user.department_id.company_id.id
		else:
			raise osv.except_osv(_('Warning!'), _('You don\'t have related department. Please contact administrator.'))

	@api.multi
	def _set_sector(self):
		department_id = self.env['hr.department'].get_sector(self.env.user.department_id.id)
		if department_id :
			return department_id
		else :      
			return self.env.user.department_id.id
		
	@api.one
	def set_request(self):
		config_obj = self.env['request.config']
		config_id = config_obj.sudo().search([('department_ids','=',self.department_id.id),('process','=','purchase.comparison')])
		if config_id:
			return config_id[0]
		else:
			return False

	@api.multi
	def _set_department(self):
		employee_id = self.env['hr.employee'].sudo().search([('user_id','=',self._uid)])
		if employee_id:
			return employee_id.department_id.id
		else:
			raise osv.except_osv(_('Warning!'), _('You don\'t have related department. Please contact administrator.'))
		
	@api.multi
	def _set_user(self):
		
		if self._uid:
			return self._uid
		else:
			raise osv.except_osv(_('Warning!'), _('You don\'t have related user. Please contact administrator.'))
	@api.multi
	def _set_request(self):
		config_id = False
		config_id = self.env['request.config'].search([('department_ids','=',self.env.user.department_id.id),('process','=','stock.requisition')])
		if not config_id:
			raise osv.except_osv(_('Warning !'), _(u"Хэлтэс дээр урсгал %s тохиргоо хийгдээгүй байна. Систем админтайгаа холбогдоно уу")%(self.env.user.department_id.name))
		return config_id[0]
	
	@api.multi
	def check_user(self):
		sel_user_ids= []
		conf_line = self.env['request.config.purchase.line']
		for requisition in self:
			config_id = requisition.request_id.id
			line_ids =conf_line.search([('sequence','=',requisition.active_sequence),('request_id','=',config_id)])
			if line_ids:
				for req in line_ids:
					if req.type == 'group':
						group = req.group_id
						for user in group.users:
							sel_user_ids.append( user)
					elif req.type == 'fixed':
						sel_user_ids.append(req.user_id)
					elif req.type == 'depart':
						user_id = req.department_id.user_id
						if user_id :
							sel_user_ids.append( user_id)
						else :
							raise osv.except_osv(_('Warning !'), _(u"Хэлтэсийн менежер дээр холбоотой хэрэглэгч талбар хоосон байна."))
		conf_users = []
		for user in sel_user_ids:
			if self.department_id.id in  user.purchase_allowed_departments.ids:
				conf_users.append(user.id)
		return conf_users

	@api.multi
	def _is_confirm_user(self):
		users = self.check_user()
		print users
		for requisition in self:
			if self._uid in users:
				requisition.is_confirm_user=True
			
		return False

	

	@api.multi
	def compute_total(self):
		total=0
		for requisition in self:
			for line in requisition.line_ids:
				total=line.product_qty*line.unit_price
			requisition.total = total

	name = fields.Char(string="Name",default='New')
	user_id = fields.Many2one('res.users',string='Хөрөнгө эзэмшигч',default=_set_user)
	sector_id = fields.Many2one('hr.department', string="Салбар",default=_set_sector)
	department_id = fields.Many2one('hr.department', string="Хэлтэс",default=_set_department)
	company_id = fields.Many2one('res.company', string="Компани",default=_set_company)
	description = fields.Text(string='Тайлбар/Тодорхойлолт')
	receiver_user_id = fields.Many2one('res.users',string="Хүлээн авагч")
	receiver_sector_id = fields.Many2one('hr.department', string="Хүлээн авах Салбар")
	receiver_department_id = fields.Many2one('hr.department', string="Хүлээн авах Хэлтэс")
	receiver_company_id = fields.Many2one('res.company', string="Компани")
	is_confirm_user = fields.Boolean(string="Is confirm user", compute=_is_confirm_user,default=False)
	line_ids = fields.One2many('stock.requisition.line','requisition_id',string='Бараанууд')
	history_lines = fields.One2many('request.history','stock_requisition_id',string='Түүхүүд')
	confirm_user_ids = fields.Many2many(comodel_name='res.users',relation='stock_requisition_res_users_rel', string='Confirmed user') #Батлах хэрэглэгчид
	#state	= fields.Selection([('draft','Ноорог'),('sent_to_supply','Бараа Тодорхойлох'),('verify','Хянах'),('confirmed','Зөвшөөрөх'),('receive','Хүлээн авах'),('done','Дууссан'),('cancelled','Цуцлагдсан')],string='Төлөв',default='draft')
	state	= fields.Selection([('draft','Draft'),('sent_to_supply','Sent to supply'),('verify','verify'),('confirmed','Confirmed'),('receive','receive'),('done','Done'),('cancelled','Cancelled')],string='State',default='draft')
	total = fields.Float(string="Дүн",compute=compute_total)	
	request_id=fields.Many2one('request.config',track_visibility='onchange',string='Workflow config',domain="[('department_ids','=',department_id),('process','=','stock.requisition')]",default=_set_request) #Урсгал тохиргоо
	active_sequence = fields.Integer(string='sequence', default=1)

	@api.model
	def create(self,vals):


		if vals.get('name', 'New') == 'New':
			vals['name'] = self.env['ir.sequence'].next_by_code('stock.requisition') or '/'


		return super(StockRequisition,self).create(vals)


	@api.multi
	def unlink(self):
		for order in self:
			if order.state != 'draft':
				raise UserError(_(u'Ноорог төлөвтэй шаардах устгаж болно.'))
		return super(StockRequisition, self).unlink()

	@api.multi
	def action_send(self):
		self.write({'state':'sent_to_supply'})
		if not self.line_ids:
			raise UserError(_(u'Бараанууд оруулж өгнө үү.'))
		self.line_ids.write({'state':'sent_to_supply'})
		user_ids = []
		for line in self.line_ids:
			categ_ids = self.env['purchase.category.config'].search([('category_ids','in',line.product_id.assign_categ_id.id)])
			if categ_ids:
				for cat in categ_ids:
					line.write({'supply_user_id':cat.user_id.id}) 
					user_ids.append(cat.user_id)
			else:
				raise UserError(_(u'%s бараан дээр Барааны хувиарлалтын ангилал тохируулагдаагүй байна. Хангамжид хандаж тухайн бараан дээр Барааны хувиарлалтын ангилал тохируулуулна уу.')%(line.product_id.name))
		# if user_ids:
		# 	self.send_notification(user_ids)
		self.create_history(self.state)	

	@api.multi
	def action_verify(self):
		
		self.write({'state':'confirmed'})
		for line in self.line_ids:
			if line.state!='cancelled':
				line.write({'state':'confirmed'})
		users = []	
		
		users=self.check_user()
		if not users:
			raise UserError(_(u'Дараагийн Батлах хэрэглэгчид олдсонгүй.'))
		self.write( {'confirm_user_ids':[(6,0,users)]})
		users = self.env['res.users'].browse(users)
		# self.send_notification(users)
		self.create_history('verify')	

	@api.multi
	def action_confirm(self):
		
		self.write({'state':'receive','active_sequence':self.active_sequence+1})
		for line in self.line_ids:
			if line.state!='cancelled':
				line.write({'state':'receive'})

		users = []
		for line in self.line_ids:
			if line.receiver_user_id:
				users.append(line.receiver_user_id)
		

		# self.send_notification([self.user_id])
		# if users:
		# 	self.send_notification(users)
		# self.write( {'confirm_user_ids':[(6,0,[self.receiver_user_id.id])],})
		self.create_history('confirmed')	

	@api.multi
	def action_cancel(self):
		
		self.write({'state':'cancelled'})
		# self.send_notification([self.user_id])
		self.create_history(self.state)	

	@api.multi
	def create_history(self,state):

		self.env['request.history'].create({
			'user_id':self._uid,
			'type':'draft',
			'stock_requisition_id':self.id,
			'date': time.strftime('%Y-%m-%d %H:%M:%S'),
			})

	@api.multi
	def send_notification(self,sel_user_ids):
		products={'draft':'Ноорог',
		'sent_to_supply':'Бараа Тодорхойлох',
		'verify':'Хянах',
		'confirmed':'Зөвшөөрөх'
		,'receive':'Хүлээн авах',
		'done':'Дууссан',
		'cancelled':'Цуцлагдсан'
		}
		subject = u'"%s" дугаартай хөрөнгийн шаардах ирлээ.'%( self.name)
		db_name = request.session.db
		base_url = self.env['ir.config_parameter'].get_param('web.base.url')
		action_id = self.env['ir.model.data'].get_object_reference('nomin_purchase_requisition', 'action_stock_requisition')[1]

		body_html = u'''
						<h4>Сайн байна уу?
						    Таньд энэ өдрийн мэнд хүргье! <br/>
						    "%s" дугаартай хөрөнгийн шаардах ирлээ.</h4>
						    <p><li><b>Шаардахын дугаар: </b>%s</li></p>
						    <p><li><b>Тайлбар/Тодорхойлолт: </b>%s</li></p>
						    <p><li><b>Салбар: </b>%s</li></p>
						    <p><li><b>Хэлтэс: </b>%s</li></p>
						    <p><li><b>Хөрөнгө эзэмшигч: </b>%s</li></p>
						    <p><li><b>Төлөв: </b>%s</li></p>

						    
						    </br>
						    <p>"%s" - н мэдээллийг <b><a href=%s/web?db=%s#id=%s&view_type=form&model=stock.requisition&action=%s>Худалдан авалт/Хөрөнгийн шаардах</a></b> цонхоор дамжин харна уу.</p>
						    <p>--</p>
						    <p>Энэхүү имэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
						    <p>Баярлалаа.</p>
				    '''%( self.name, self.name,self.description,self.sector_id.name,
						    self.department_id.name,self.user_id.name,products[self.state], self.name,
						    base_url,
						    db_name,
						    self.id,
						    action_id)
		
		for user in sel_user_ids:
		    email = user.login
		    if email or email.strip():
				email_template = self.env['mail.template'].create({
						'name': _('Followup '),
						'email_from': self.env.user.company_id.email or '',
						'model_id': self.env['ir.model'].search([('model', '=', 'stock.requisition')]).id,
						'subject': subject,
						'email_to': email,
						'lang': self.env.user.lang,
						'auto_delete': True,
						'body_html':body_html,
						#  'attachment_ids': [(6, 0, [attachment.id])],
						})
				email_template.sudo().send_mail(self.id)


class StockRequisitionLine(models.Model):
	_name = 'stock.requisition.line'

	@api.multi
	def compute_total(self):
		for line in self:
			line.total=line.product_qty*line.unit_price

	@api.multi
	def compute_supply(self):
		for line in self:
			if line.supply_user_id.id==self._uid:
				line.is_supply =True


	@api.multi
	def _is_receive_user(self):
		
		for requisition in self:
			if self._uid== requisition.receiver_user_id.id:
				requisition.is_receive_user=True
			
		return False

	product_id = fields.Many2one('product.product',string='Бараа',domain=[('product_tmpl_id.is_new','=',True),('product_tmpl_id.cost_price','>',0)])
	description = fields.Text(string='Тодорхойлолт')
	unit_price = fields.Float(string='Нэгж үнэ')
	product_qty = fields.Float(string='Тоо хэмжээ',default=1)
	product_uom_id = fields.Many2one('product.uom',string='Барааны хэмжих Нэгж')
	requisition_id = fields.Many2one('stock.requisition',string='Шаардахын дугаар')
	supply_user_id = fields.Many2one('res.users',string='Худалдан авалтын ажилтан')
	state	= fields.Selection([('draft',u'Ноорог'),('sent_to_supply',u'Бараа Тодорхойлох'),('verify',u'Хянах'),('confirmed',u'Зөвшөөрөх'),
		('receive',u'Хүлээн авах'),('done',u'Дууссан'),('cancelled',u'Цуцлагдсан')],string=u'Төлөв',default='draft')
	total = fields.Float(string="Дүн",compute=compute_total)	
	is_supply = fields.Boolean(string="Is supply",compute=compute_supply,default=False)
	is_receive_user = fields.Boolean(string="Is receive user", compute=_is_receive_user,default=False)
	user_id = fields.Many2one('res.users',string='Хөрөнгө эзэмшигч',related="requisition_id.user_id", store=True )
	sector_id = fields.Many2one('hr.department', string="Салбар",related="requisition_id.sector_id", store=True )
	department_id = fields.Many2one('hr.department', string="Хэлтэс",related="requisition_id.department_id", store=True)
	receiver_user_id = fields.Many2one('res.users',string="Хүлээн авагч")
	receiver_sector_id = fields.Many2one('hr.department', string="Хүлээн авах Салбар")
	receiver_department_id = fields.Many2one('hr.department', string="Хүлээн авах Хэлтэс")


	@api.multi
	def unlink(self):
		for order in self:
			if order.state != 'draft':
				raise UserError(_(u'Ноорог төлөвтэй шаардахын мөр устгаж болно.'))
		return super(StockRequisition, self).unlink()

	@api.onchange('product_id')
	def onchange_product(self):
		self.unit_price = self.product_id.sudo().cost_price
		self.product_uom_id = self.product_id.uom_id.id

		categ_ids = self.env['purchase.category.config'].sudo().search([('category_ids','in',self.product_id.assign_categ_id.id)])
		if categ_ids:
			self.supply_user_id = categ_ids[0].user_id.id
		# else:
		# 	self.supply_user_id.id = 1148

	@api.onchange('receiver_user_id')
	def onchange_receive(self):

		self.receiver_department_id = self.receiver_user_id.department_id.id
		self.receiver_sector_id =  self.env['hr.department'].get_sector(self.receiver_user_id.department_id.id)


	@api.multi
	def action_send(self):
		
		self.write({'state':'verify'})
		is_send = True
		if not self.receiver_user_id:
				raise UserError(_(u'Хүлээн авах хэрэглэгч сонгож өгнө үү.'))
		for line in self.requisition_id.line_ids:

			if line.state not in ['verify','cancelled']:
				is_send= False
		if is_send:
			users = self.return_users('nomin_purchase_requisition','group_haaa_head')
			self.requisition_id.write({'state':'verify'})
			self.requisition_id.create_history('verify')
			if users:
				# self.send_notification(users)
				conf_users =[]
				for  user in users:
					conf_users.append(user.id)

				self.requisition_id.write( {'confirm_user_ids':[(6,0,conf_users)]})

		return {
		'type': 'ir.actions.client',
		'tag': 'reload',
		}
	
	@api.multi
	def action_verify(self):
		self.write({'state':'confirmed'})
		is_send = True
		for line in self.requisition_id.line_ids:
			
			if line.state not in ['confirmed','cancelled']:
				is_send= False
		if is_send:
			self.requisition_id.action_verify()
		lists= []
		if self.user_id:
			lists.append(self.user_id)
		if self.supply_user_id:
			lists.append(self.supply_user_id)
		# self.send_notification(lists)
		return {
		'type': 'ir.actions.client',
		'tag': 'reload',
		}
	@api.multi
	def action_cancel(self):
		self.write({'state':'cancelled'})
		is_send =True
		for line in self.requisition_id.line_ids:
			if line.state not in ['cancelled']:
				is_send= False
		if is_send:
			self.requisition_id.action_cancel()
		lists= []
		if self.user_id:
			lists.append(self.user_id)
		if self.supply_user_id:
			lists.append(self.supply_user_id)
		# self.send_notification(lists)
		return {
		'type': 'ir.actions.client',
		'tag': 'reload',
		}

	@api.model
	def create(self,vals):

		if vals.get('product_id'):
			product = self.env['product.product'].browse(vals.get('product_id'))
			if product.assign_categ_id:
				categ_ids = self.env['purchase.category.config'].sudo().search([('category_ids','in',product.assign_categ_id.id)])
				if categ_ids:
					vals.update({'supply_user_id':categ_ids[0].user_id.id})
			# else:
			# 	vals.update({'supply_user_id':1148})

		requisition_id = super(StockRequisitionLine,self).create(vals)
		if requisition_id.requisition_id.state !='draft' and vals.get('state')!='confirmed':
			raise UserError(_(u'Ноорог төлөвтэй хөрөнгийн шаардахын мөр дээр нэмж болно.'))

		return requisition_id

	@api.multi
	def write(self,vals):

		if vals.get('product_id'):
			product = self.env['product.product'].browse(vals.get('product_id'))
			if product.assign_categ_id:
				categ_ids = self.env['purchase.category.config'].sudo().search([('category_ids','in',product.assign_categ_id.id)])
				if categ_ids:
					vals.update({'supply_user_id':categ_ids[0].user_id.id})
				else:
					if self.supply_user_id:
						vals.update({'supply_user_id':1148})	

			# else:
			# 	vals.update({'supply_user_id':1148})

		requisition_id = super(StockRequisitionLine,self).write(vals)
		# if requisition_id.requisition_id.state !='draft' and vals.get('state')!='confirmed':
		# 	raise UserError(_(u'Ноорог төлөвтэй хөрөнгийн шаардахын мөр дээр нэмж болно.'))

		return requisition_id


	@api.multi
	def unlink(self):
		for order in self:
			if order.state != 'draft':
				raise UserError(_(u'Ноорог төлөвтэй шаардахын мөр устгаж болно.'))
		return super(StockRequisitionLine, self).unlink()


	@api.multi
	def action_receive(self):
		self.write({'state':'done'})
		is_true =True
		for line in self.requisition_id.line_ids:
			if line.state not in ['done','cancelled']:
				is_true = False
		if is_true:
			self.requisition_id.write({'state':'done'})
			self.requisition_id.create_history('done')
		return {
		'type': 'ir.actions.client',
		'tag': 'reload',
		}


	@api.multi
	def send_notification(self,sel_user_ids):
		products={'draft':'Ноорог',
		'sent_to_supply':'Бараа Тодорхойлох',
		'verify':'Хянах',
		'confirmed':'Зөвшөөрөх'
		,'receive':'Хүлээн авах',
		'done':'Дууссан',
		'cancelled':'Цуцлагдсан'
		}
		subject = u'"%s" дугаартай хөрөнгийн шаардах ирлээ.'%( self.requisition_id.name)
		db_name = request.session.db
		base_url = self.env['ir.config_parameter'].get_param('web.base.url')
		action_id = self.env['ir.model.data'].get_object_reference('nomin_purchase_requisition', 'action_stock_requisition')[1]
       	
		body_html = u'''
						<h4>Сайн байна уу?
						    Таньд энэ өдрийн мэнд хүргье! <br/>
						    "%s" дугаартай хөрөнгийн шаардах ирлээ.</h4>
						    <p><li><b>Шаардахын дугаар: </b>%s</li></p>
						    <p><li><b>Тайлбар/Тодорхойлолт: </b>%s</li></p>
						    <p><li><b>Салбар: </b>%s</li></p>
						    <p><li><b>Хэлтэс: </b>%s</li></p>
						    <p><li><b>Хөрөнгө эзэмшигч: </b>%s</li></p>
						    <p><li><b>Төлөв: </b>%s</li></p>

						    
						    </br>
						    <p>"%s" - н мэдээллийг <b><a href=%s/web?db=%s#id=%s&view_type=form&model=stock.requisition&action=%s>Худалдан авалт/Хөрөнгийн шаардах</a></b> цонхоор дамжин харна уу.</p>
						    <p>--</p>
						    <p>Энэхүү имэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
						    <p>Баярлалаа.</p>
				    '''%( self.requisition_id.name, self.requisition_id.name,self.requisition_id.description,self.requisition_id.sector_id.name,
						    self.requisition_id.department_id.name,self.requisition_id.user_id.name,products[self.requisition_id.state], self.requisition_id.name,
						    base_url,
						    db_name,
						    self.requisition_id.id,
						    action_id)
		
		for user in sel_user_ids:
		    email = user.login
		    if email or email.strip():
				email_template = self.env['mail.template'].create({
						'name': _('Followup '),
						'email_from': self.env.user.company_id.email or '',
						'model_id': self.env['ir.model'].search([('model', '=', 'stock.requisition.line')]).id,
						'subject': subject,
						'email_to': email,
						'lang': self.env.user.lang,
						'auto_delete': True,
						'body_html':body_html,
						#  'attachment_ids': [(6, 0, [attachment.id])],
						})
				email_template.sudo().send_mail(self.id)
	def return_users(self,module, group):
		notif_groups = self.env['ir.model.data'].get_object(module, group)
		sel_user_ids = []
		for user in notif_groups.users:
			sel_user_ids.append(user)
		return sel_user_ids

class RequestHistory(models.Model):
	_inherit = 'request.history'

	stock_requisition_id = fields.Many2one('stock.requisition',string="Stock requisition")