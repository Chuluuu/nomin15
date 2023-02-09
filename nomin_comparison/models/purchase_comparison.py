# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import time
from odoo.http import request    
import requests 
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class request_history(models.Model):
	_inherit = 'request.history'

	comparison_id = fields.Many2one('purchase.comparison', string='Purchase comparison')
class purchase_comparison(models.Model):
	_name = 'purchase.comparison'
	_inherit = ['mail.thread']
	_order = "create_date desc"
	
	STATE_SELECTION = [('draft', 'Draft'),
                       ('sent', 'Sent'),  # Илгээгдсэн
                       ('approved', 'Approved'),  # Зөвшөөрсөн
                       ('verified', 'Verified'),  # Хянасан
                       ('confirmed', 'Confirmed'),  # Батласан
                       ('canceled', 'Canceled'),  # Цуцлагдсан
					   ('purchase', 'Purchase'), #Худалдан авалт
                                   ]
    

	
	def _set_department(self):
		employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self._uid)])
		if employee_id and employee_id.department_id:
			return employee_id.department_id.id
		# else:
		# 	raise UserError(_('Warning!'), _('You don\'t have related department. Please contact administrator.'))
		return None

	
	def set_request(self):
		config_obj = self.env['request.config']
		config_id = config_obj.sudo().search([('department_ids', '=', self.department_id.id), ('process', '=', 'purchase.comparison')], limit= 1)
		if config_id:
			return config_id
		else:
			return False
    

	
	def _check_user_in_request(self, state):
		sel_user_ids = []
		user_ids = []
		conf_line = self.env['request.config.purchase.line']
		groups = self.env['res.groups']
		config_obj = self.env['request.config']
		for request in self:
			config_id = request.request_id.id
			line_ids = conf_line.search([('sequence', '=', request.active_sequence), ('request_id', '=', config_id)])
			if line_ids:
				for req in line_ids:
					if req.state == state:
						if req.type == 'group':
							group = req.group_id
							# for group in groups.browse(group_id):
							for user in group.users:
								sel_user_ids.append(user.id)
						elif req.type == 'fixed':
							sel_user_ids.append(req.user_id.id)
						elif req.type == 'depart':
							user_id = self.department_id.manager_id.user_id.id
							if user_id :
								sel_user_ids.append(user_id)
							else :
								raise UserError(_('Warning !'), _(u"Хэлтэсийн менежер дээр холбоотой хэрэглэгч талбар хоосон байна."))
		
		user_ids = self.get_possible_users(sel_user_ids)
		return user_ids

	
	def _is_in_sent(self):
		if self.state == 'draft':
			sel_user_ids = self._check_user_in_request('sent')
			if self._uid in sel_user_ids:
				if self.user_id.id == self._uid:
					self.is_in_sent = True
				else:
					self.is_in_sent = False
	
	def _is_in_approve(self):
		sel_user_ids = []
		sel_user_ids = self._check_user_in_request('approved')
		
		if self._uid in sel_user_ids:
			self.is_in_approve = True
		else:
			self.is_in_approve = False	
    
	
	def _is_in_verify(self):

		sel_user_ids = []
		sel_user_ids = self._check_user_in_request('verified')
		if self._uid in sel_user_ids:
			self.is_in_verify = True
		else:
			self.is_in_verify = False	

	
	def _is_in_confirm(self):
		sel_user_ids = []
		sel_user_ids = self._check_user_in_request('confirmed')
		if self._uid in sel_user_ids:
			self.is_in_confirm = True
		else:
			self.is_in_confirm = False	

    

	name = fields.Char(string='Name', readonly=True, default='New')
	date = fields.Date(string="Date", tracking=True)
	user_id = fields.Many2one('res.users', string="User" , readonly=True ,tracking=True, default = lambda self: self.env.user)
	department_id = fields.Many2one('hr.department', string="Department", domain="[('id','in',sector_id)]", required=True, readonly=True,tracking=True, default=_set_department)
	sector_id = fields.Many2one('hr.department', string="Sector", domain="[('is_sector','!=',False)]", tracking=True)
	state = fields.Selection(STATE_SELECTION, string="State" , default='draft', tracking=True)
	partner_ids = fields.One2many('purchase.partner.comparison', 'comparison_id', string='Partner comparisons')
	rate_employee_ids = fields.One2many('purchase.indicator.rate.employee', 'comparison_id', string='Purchase rate indicator rate employee')
	purchase_indicator_ids = fields.One2many('purchase.indicators', 'comparison_id', string="Purchase indicator")
	request_id = fields.Many2one('request.config', string='Request config' , domain="[('department_ids','=',sector_id),('process','=','purchase.comparison')]", tracking=True)
	active_sequence = fields.Integer(string="Active sequence", default=1)
	is_in_sent = fields.Boolean(string='Is in sent', compute=_is_in_sent, default=False)
	is_in_approve = fields.Boolean(string='Is in sent' , compute=_is_in_approve, default=False)
	is_in_confirm = fields.Boolean(string='Is in sent', compute=_is_in_confirm, default=False)
	is_in_verify = fields.Boolean(string='Is in sent', compute=_is_in_verify, default=False)
	order_ids = fields.One2many('purchase.order','comparison_id','Purchase Orders')
	confirmed_person = fields.Many2one('hr.employee', string="Confirmed Person")
	verified_person = fields.Many2one('hr.employee', string="Verified Person")
	approved_person = fields.Many2one('hr.employee', string="Approved Person")
	is_from_purchase = fields.Boolean(string="Is from purchase", default=False)


	@api.model
	def create(self, vals):
		request_obj = self.env['ir.model'].search([('model', '=', 'purchase.comparison')])
		if vals.get('name', 'New') == 'New':
			vals['name'] = self.env['ir.sequence'].next_by_code('purchase.comparison') or '/'		
		if request_obj:
			line_ids = self.env['evaluation.indicators.line'].search([('is_default', '=', True), ('model_id', '=', request_obj.id)])
		comparison_obj = super(purchase_comparison, self).create(vals) 	
		if line_ids:	
			for line in line_ids:
				self.env['purchase.indicators'].create({'indicator_id':line.indicator_id.id, 'comparison_id':comparison_obj.id, })
		comparison_obj.insert_indicators()
		return comparison_obj



	
	def write(self, vals):
		result = super(purchase_comparison, self).write(vals)
		self.insert_indicators()
		return result


	
	def get_possible_users(self, sel_user_ids):
		department_ids = []
		user_ids = self.env['res.users'].browse(sel_user_ids)
		possible_user_ids = []
		for this in self:
			for user in user_ids:
				department_ids = self.env['hr.department'].search([('id', 'in', user.purchase_allowed_departments.ids)])
				user_dep_set = set(department_ids.ids)
				if list(user_dep_set.intersection([this.department_id.id])):
					possible_user_ids.append(user.id)
		return possible_user_ids
    
	
	def action_send(self):
	
		if not self.rate_employee_ids:
			raise UserError(_(u'Анхааруулга!'), _(u"Үнэлгээ өгөх ажилтан сонгож өгнө үү!"))
		if not self.purchase_indicator_ids:
			raise UserError(_(u'Анхааруулга!'), _(u"Үнэлгээ өгөх үзүүлэлт сонгож өгнө үү!"))
		
		for line in self.partner_ids:
			for info_id in line.info_ids:
				if not info_id.info:
					raise UserError(_(u'Анхааруулга!'), _(u"Зарим үнэлгээнд тайлбар бичээгүй бн"))
		
		purchase_orders = self.env['purchase.order'].search([('comparison_id','=',self.id)])
		
		for order in purchase_orders:
			order.write({
				'state': 'comparison_created',
			})
		
		requisition_line = self.env['purchase.requisition.line'].sudo().search([('comparison_id','=',self.id)])
		for line in requisition_line:
			line.write({
				'comparison_sent_date': time.strftime('%Y-%m-%d %H:%M:%S'),
			})

		self.send_request()
		user_ids = []
		for line in self.rate_employee_ids:
			user_ids.append(line.employee_id.user_id.id)
		self.message_subscribe_users(user_ids=user_ids)
		for order in self.partner_ids: 
			order.order_id.message_subscribe_users(user_ids=user_ids)
		# purchase_line = self.env['request.config.purchase.line']		
		
		
	
	def action_verify(self):
		for com in self:
			for emp in com.rate_employee_ids:
				if emp.state =='draft':
					raise UserError(_(u'Анхааруулга!'), _(u"Үнэлгээ өгөх ажилтангууд үнэлгээ өгч дуусаагүй байна.!"))
		self.change_state()
		self.verified_person = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
		# self.send_notification('verified')
	
	def action_approve(self):
		for com in self:
			for emp in com.rate_employee_ids:
				if emp.state =='draft':
					raise UserError(_(u'Анхааруулга!'), _(u"Үнэлгээ өгөх ажилтангууд үнэлгээ өгч дуусаагүй байна.!"))
		self.change_state()
		self.approved_person = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
		# self.send_notification('approved')

	
	def action_confirm(self):
		for com in self:
			for emp in com.rate_employee_ids:
				if emp.state =='draft':
					raise UserError(_(u'Анхааруулга!'), _(u"Үнэлгээ өгөх ажилтангууд үнэлгээ өгч дуусаагүй байна.!"))
		self.send_prices_info()
		self.change_state()
		self.confirmed_person = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
		# self.send_notification('confirmed')

	
	def change_state(self):

		total_percent = 0
		amount = 0.0
		order_id = False
		is_winner = False
		count = 0
		for req in self:
				for partner in req.partner_ids:
					if partner.is_in_confirm_users:
						if partner.is_winner:
							is_winner =  True
							order_id = partner.order_id.id
							count =count+1

		
	
	
		if not is_winner:
			self.send_request()
		else:			
			if count > 1 or count ==0:
				_logger.info(u'\n\n\n\n\n\nНийлүүлэгч  %s Ажилтаны тоо %s \n\n\n'%(is_winner,count))
				raise UserError(_(u'Warning !'), _(u"Та шалгаруулах нэг нийлүүлэгч чагталж өгнө үү  !"))
			self.change_purchase(order_id)
			self.write({'state':'confirmed', 'active_sequence':99})
			requisition_line = self.env['purchase.requisition.line'].sudo().search([('comparison_id','=',self.id)])
			for line in requisition_line:
				line.write({
					'state': 'ready',
					'comparison_state': 'confirmed',
					'comparison_date_end': time.strftime('%Y-%m-%d'),
					'comparison_confirmed_date': time.strftime('%Y-%m-%d %H:%M:%S'),
				})
			self.partner_ids.write({'state':'confirmed'})

	
	def change_purchase(self, order_id):
		for order in self.order_ids:
			if order.id == order_id:
				order.write({'state':'purchase','active_sequence':99})
				order._create_picking()	
			else:
				order.write({'state':'cancel', 'active_sequence':99})
    
	
	def get_token (self):
		url='https://il1.nomin.mn/Inventory/api/auth'
		params = { 
					'username':'nomin',
					'password':'nomin'
				}
            
		result = requests.post(url,params=params)
		if result.status_code not in [200,'200']:
			_logger.info("ERROR DESCRIPTION: %s "%(result.text))
			raise UserError(_(u"ERROR DESCRIPTION: %s!"%(result.text)))

		r = result.json()
		return r[u'token']

	
	def action_connect(self,url,params=None, data_type=None):
		bearer_token = self.get_token()
		header = {'Authorization': "Bearer "+bearer_token,
            'Content-Type':'application/json'}

		res = requests.post(url, data=params, headers=header)
		return res
  
	
	def send_prices_info(self):	
		url = 'https://il1.nomin.mn/Inventory/api/ItemPurchasePrices'
		for partner in self.partner_ids:
			if partner.is_winner:
				query = "select department_id from res_partner where id = %s"%(partner.id)
				self.env.cr.execute(query)
				result =  self.env.cr.fetchall()
				if not result:
					for line in partner.order_id.order_line:
						params = {
							"itemId": line.product_id.product_code,
							"locationId": "24",
							"beginDate": datetime.now().strftime("%Y-%m-%d"),
							"price": line.price_unit
							}
						res = self.action_connect(url,params)
						if res.status_code == 200:
							line.product_id.update({'standard_price':line.price_unit})
							
			


	
	def send_request(self):
		if self._context is None:
			self._context = {}
		employee_obj = self.env['hr.employee']
		history_obj = self.env['request.history']
		config_obj = self.env['request.config']
		count = 0
		for request in self:
			config_id = request.request_id.id
			vals = {}
			if not config_id:
				raise UserError(_('Warning !'), _("You don't have purchase requisition request configure !"))
			next_user_ids, next_seq, next_state = config_obj.purchase_forward('purchase.comparison', request.active_sequence, request.user_id.id, config_id, request.department_id.id)
			next_user_ids1, next_seq1, next_state1 = config_obj.purchase_forward('purchase.comparison', request.active_sequence+1, request.user_id.id, config_id, request.department_id.id)
			user = request.user_id
			if next_user_ids:
				vals.update({'state':next_state, 'active_sequence':request.active_sequence + 1})
				_logger.info(u'\n\n\n\n\n\n send_request next_state %s \n\n\n'%(next_state))

				requisition_line = self.env['purchase.requisition.line'].sudo().search([('comparison_id','=',request.id)])

				if next_state == 'confirmed':
					for line in requisition_line:
						line.write({
							'state': 'ready',
							'comparison_state': 'confirmed',
							'comparison_date_end': time.strftime('%Y-%m-%d'),
							'comparison_confirmed_date': time.strftime('%Y-%m-%d %H:%M:%S'),
						})
				else:
					for line in requisition_line:
						line.write({
							'comparison_state': next_state,
						})
				

			for partner in request.partner_ids:
				if partner.is_in_confirm_users:
					if partner.is_winner:
						count =count+1
			if not next_user_ids1:
				if count > 1 or count ==0:
					_logger.info(u'\n\n\n\n\n\nНийлүүлэгч тоо %s \n\n\n'%(count))
					raise UserError(_(u'Warning !'), _(u"Та шалгаруулах нэг нийлүүлэгч чагталж өгнө үү  !"))
			history_obj.create(
				{'comparison_id': request.id,
				'user_id': self._uid,
				'date': time.strftime('%Y-%m-%d %H:%M:%S'),
				'type': next_state,
				})
		self.write(vals)
		self.partner_ids.write({'state':next_state})
		# self.send_notification(next_state)

	
	def unlink(self):
		for order in self:
			if order.state != 'draft':
				raise UserError(_(u'Ноорог төлөвтэй харьцуулалт устгаж болно.'))
			for com in order.order_ids:
				com.write({'state':'draft'})
			
			requisition_line = self.env['purchase.requisition.line'].sudo().search([('comparison_id','=',order.id)])
			for line in requisition_line:
				if line.state == 'compared':
					line.state = 'compare'
		return super(purchase_comparison, self).unlink()

	
	def action_cancel(self):
		for part  in self.partner_ids:
			for ind in part.indicator_ids:
				# for rate in ind.rate_ids:
					ind.unlink()

		self.write({'state':'draft', 'active_sequence':1})
		self.partner_ids.write({'state':'draft'})

	
	def action_canceled(self):
		for part  in self.partner_ids:
			for ind in part.indicator_ids:
				ind.unlink()

		for order in self:
			for com in order.order_ids:
				com.write({'state':'cancel'})

		requisition_line = self.env['purchase.requisition.line'].sudo().search([('comparison_id','=',order.id)])
		for line in requisition_line:
			if line.state == 'compared':
				line.state = 'compare'
		
		self.write({'state':'canceled'})


	
	
	def insert_indicators(self):

		request_obj = self.env['ir.model'].search([('model', '=', 'purchase.comparison')])
		for partner in self.partner_ids:
			for purch in self.purchase_indicator_ids:
				line_id = self.env['evaluation.indicators.line'].search([('indicator_id', '=', purch.indicator_id.id), ('model_id', '=', request_obj.id)])[0]
				if line_id:
					if line_id.evalution_method=='by_scale':
						exists = self.env['purchase.evaluation.indicators'].search([('indicator_id', '=', purch.indicator_id.id),('partner_id', '=', partner.id)])
						if not exists:
							self.env['purchase.evaluation.indicators'].create({'indicator_id':purch.indicator_id.id, 'partner_id':partner.id})
					else:
						exists = self.env['purchase.evaluation.infos'].search([('indicator_id', '=', purch.indicator_id.id),('partner_id', '=', partner.id)])
						if not exists:
							self.env['purchase.evaluation.infos'].create({'indicator_id':purch.indicator_id.id, 'partner_id':partner.id})

	
	def add_comparison_partner_action(self):
		return {
			'name': 'Note',
			'view_mode': 'form',
			'res_model': 'add.comparison.partner',
			'context': self._context,
			'type': 'ir.actions.act_window',
			'nodestroy': True,
			'target': 'new',
		}

	
	def add_comparison_product_action(self):
		return {
			'name': 'Note',
			'view_mode': 'form',
			'res_model': 'add.comparison.product',
			'context': self._context,
			'type': 'ir.actions.act_window',
			'nodestroy': True,
			'target': 'new',
		}

	
	def action_cancel_wizard(self):
		return {
			'name': 'Note',
			'view_mode': 'form',
			'res_model': 'cancel.comparison',
			'context': self._context,
			'type': 'ir.actions.act_window',
			'nodestroy': True,
			'target': 'new',
		}


	def send_notification(self,state):
#         model_obj = odoo.pooler.get_pool(cr.dbname).get('ir.model.data')
		sel_user_ids = []
		conf_line = self.env['request.config.purchase.line']
		groups = self.env['res.groups']
		config_obj = self.env['request.config']


		for contract in self:
			config_id = contract.request_id.id
			line_id =conf_line.search([('sequence','=',contract.active_sequence+1),('request_id','=',config_id)])
		# if signal not in ['purchase','done','draft','sent_rfq','back']:
		mail_user_ids= self._check_user_in_request(state)	
		

		states = {
		'draft':u'Ноорог',
		'sent':u'Илгээгдсэн',
		'sent_rfq':u'Үнийн санал илгээгдсэн',
		'back':u'Үнийн санал хүлээн авсан',
		'approved':u'Зөвшөөрсөн',
		'confirmed':u'Баталсан',
		'verified':u'Хянасан',
		'rejected':u'Буцаагдсан',
		'warranty':u'Баталгаат хугацаа',
		'purchase':u'Худалдан авах захиалга',
		'certified':u'Баталгаажсан',
		'canceled':u'Цуцлагдсан',
		'closed':u'Хаагдсан',
		'done':u'Дууссан',
		}
		# mail_user_ids = self.get_possible_users(sel_user_ids)
		mail_user_ids.append(self.user_id.id)
		
		for com in self:
			for emp in com.rate_employee_ids:
				if emp.employee_id.user_id.id not in mail_user_ids:
					mail_user_ids.append(emp.employee_id.user_id.id)

		user_obj = self.env['res.users']

		base_url = self.env['ir.config_parameter'].get_param('web.base.url')
		action_id = self.env['ir.model.data']._xmlid_to_res_id('nomin_purchase.purchase_mail_template')
		db_name = request.session.db
		user_emails = []
		mail_user_ids = list(set(mail_user_ids))
		for email in  self.env['res.users'].browse(mail_user_ids):
			user_emails.append(email.login)
			subject = u'"Харьцуулалтын дугаар %s".'%(self.name)
			body_html = u'''
			<h4>Сайн байна уу,\n Таньд энэ өдрийн мэнд хүргье! </h4>
			<p>
			ERP системд %s салбарын %s хэлтэсийн %s дугаартай харьцуулалт %s төлөвт орлоо.

			</p>
			<p><b><li> Харьцуулалтын дугаар: %s</li></b></p>
			<p><b><li> Салбар: %s</li></b></p>
			<p><b><li> Хэлтэс: %s</li></b></p>
			
			<p><li> <b><a href=%s/web?db=%s#id=%s&view_type=form&model=purchase.comparison&action=%s>Харьцуулалтын мэдэгдэл</a></b> цонхоор дамжин харна уу.</li></p>

			</br>
			<p>---</p>
			</br>
			<p>Энэхүү мэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
			<p>Баярлалаа.</p>
			'''%( self.sector_id.name,
			self.department_id.name,
			self.name,
			states[state],
			self.name,
			self.sector_id.name,
			self.department_id.name,
			base_url,
			db_name,
			self.id,
			action_id
			)

			if email.login and email.login.strip():
				email_template = self.env['mail.template'].create({
				'name': _('Followup '),
				'email_from': self.env.user.company_id.email or '',
				'model_id': self.env['ir.model'].search([('model', '=', 'purchase.comparison')]).id,
				'subject': subject,
				'email_to': email.login,
				'lang': self.env.user.lang,
				'auto_delete': True,
				'body_html':body_html,
				#  'attachment_ids': [(6, 0, [attachment.id])],
				})
				email_template.send_mail(self.id)
 		# email = u'' + states[state] +u'\n Дараах хэрэглэгчид рүү имэйл илгээгдэв: ' + ('<b>' + ('</b>, <b>'.join(user_emails)) + '</b>')


		# self.message_subscribe_users(mail_user_ids)
		# self.message_post(body=email)

class purchase_partner_comparison(models.Model):
	_name = 'purchase.partner.comparison'

	STATE_SELECTION = [('draft', 'Draft'),
                       ('sent', 'Sent'),  # Илгээгдсэн
                       ('approved', 'Approved'),  # Зөвшөөрсөн
                       ('verified', 'Verified'),  # Хянасан
                       ('confirmed', 'Confirmed'),  # Батласан
                       ('canceled', 'Canceled'),  # Цуцлагдсан
                                   ]

	
	def get_possible_users(self, sel_user_ids):
		department_ids = []
		user_ids = self.env['res.users'].browse(sel_user_ids)
		possible_user_ids = []
		for this in self:
			for user in user_ids:
				department_ids = self.env['hr.department'].search([('id', 'in', user.purchase_allowed_departments.ids)])
				user_dep_set = set(department_ids.ids)
				if list(user_dep_set.intersection([this.comparison_id.department_id.id])):
					possible_user_ids.append(user.id)
		return possible_user_ids

	
	def _check_user_in_request(self):
		sel_user_ids = []
		user_ids = []
		conf_line = self.env['request.config.purchase.line']
		groups = self.env['res.groups']
		config_obj = self.env['request.config']
		is_amount = False
		percent= 0
		amount_total = 0
		for request in self:
			config_id = request.comparison_id.request_id.id
			line_ids = conf_line.search([('sequence', '=', request.comparison_id.active_sequence), ('request_id', '=', config_id)])
			if line_ids:
				for part in request.comparison_id.partner_ids:
					if part.total_percent >=percent:
						percent = part.total_percent
						is_amount = True
						amount_total = part.order_id.amount_total					

			if is_amount:
				for req in line_ids:
					if req.limit >= amount_total or req.limit==0:	
						if req.type == 'group':
							group = req.group_id
							# for group in groups.browse(group_id):
							for user in group.users:
								sel_user_ids.append(user.id)
						elif req.type == 'fixed':
							sel_user_ids.append(req.user_id.id)
						elif req.type == 'depart':
							user_id = request.comparison_id.department_id.manager_id.user_id.id
							if user_id :
								sel_user_ids.append(user_id)
							else :
								raise UserError(_('Warning !'), _(u"Хэлтэсийн менежер дээр холбоотой хэрэглэгч талбар хоосон байна."))
		user_ids = self.get_possible_users(sel_user_ids)
		return user_ids


	
	def _total_percent(self):
		total_percent = 0.0
		count = 0
		for ind in self.indicator_ids:
			total_percent += ind.total_percent 
			count += 1
		if total_percent == 0:
			count = 1
		self.total_percent = total_percent / 	count

	
	def _is_in_raters(self):
		employee_ids = []
		rate_employee_ids = []
		user_ids = []
		employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self._uid)])
		if self.comparison_id:
			for emp in self.comparison_id.rate_employee_ids:
				if emp.state == 'draft':
					user_ids.append(emp.employee_id.user_id.id)
					rate_employee_ids.append(emp.id)

			for ind in self.indicator_ids:
				for rate in ind.rate_ids:
					employee_ids.append(rate.employee_id.id)
			if self._uid in user_ids:
				if employee_id.id in employee_ids:
					self.is_in_raters = False
				else:
					self.is_in_raters = True

	
	def _is_in_confirm_users(self):
		employee_ids = []
		rate_employee_ids = []
		user_ids = []
		sel_user_ids = self._check_user_in_request()
		employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self._uid)])
		if self.comparison_id:
			for emp in self.comparison_id.request_id:
				if emp.sequence == 2:
					if self.state == 'verified':
						if self._uid in sel_user_ids:
								self.is_in_confirm_users = True
						else:
								self.is_in_confirm_users = False
					else:
							self.is_in_confirm_users = False

				elif emp.sequence == 1:
					if self._uid in sel_user_ids:
						self.is_in_confirm_users = True
					else:
						self.is_in_confirm_users = False

	total_percent = fields.Float(string="Total percent", compute=_total_percent, default=False)
	partner_id = fields.Many2one('res.partner', string='Partner', required=True)
	order_id = fields.Many2one('purchase.order', domain="[('partner_id','=',partner_id)]", string="Purchase order")
	comparison_id = fields.Many2one('purchase.comparison', string='Purchase comparison')
	indicator_ids = fields.One2many('purchase.evaluation.indicators', 'partner_id', string='Purchase evaluation indicator')
	info_ids = fields.One2many('purchase.evaluation.infos', 'partner_id', string='Purchase evaluation info')
	is_in_raters = fields.Boolean(string='Is in raters', default=False, compute=_is_in_raters)
	is_in_confirm_users = fields.Boolean(string='Is in is_in_confirm_users', default=False, compute=_is_in_confirm_users)
	state = fields.Selection(STATE_SELECTION, string="State" , default='draft' , tracking=True)
	is_winner = fields.Boolean(string=u'Шалгарсан')
	description = fields.Text(string="Description")
	win_date = fields.Date(string='Шалгарсан огноо')


	
	def action_rate(self):
		       raise UserError(_(u'Анхааруулга'), _(u'Үнэлгээ өгөх хэсэг хийгдээгүй байнa'))

class purchase_evaluation_indicators(models.Model):
	_name = 'purchase.evaluation.indicators'
	
	
	def _total_percent(self):
		total_percent = 0.0
		count = 0
		scale = 0.0
		if self.indicator_id.line_ids:
			for line in self.indicator_id.line_ids:
				if line.model_id.model == 'purchase.comparison':
					if line.scale:
						scale = line.scale
		for ind in self.rate_ids:
			total_percent += ind.percent 
			count += 1
		if total_percent == 0:
			count = 1
		self.total_percent = ((total_percent / count)*scale)/100
		

	indicator_id = fields.Many2one('evaluation.indicators', string="Evaluation indicators")
	total_percent = fields.Float(string='Total Percent', compute=_total_percent, default=False)
	partner_id = fields.Many2one('purchase.partner.comparison', string='Purchase comparison partner')
	rate_ids = fields.One2many('purchase.employee.rate', 'evaluation_id', string='Purchase employee indicators')


class purchase_evaluation_infos(models.Model):
	_name = 'purchase.evaluation.infos'
	

	indicator_id = fields.Many2one('evaluation.indicators', string="Evaluation question")
	info = fields.Char(string='Info')

	partner_id = fields.Many2one('purchase.partner.comparison', string='Purchase comparison partner')
	parent_state = fields.Selection(related = 'partner_id.state', string='state',readonly=True)



class purchase_employee_indicators(models.Model):
	_name = 'purchase.employee.rate'

	employee_id = fields.Many2one('hr.employee', string='Employee')
	percent = fields.Float(string='Percent')
	evaluation_id = fields.Many2one('purchase.evaluation.indicators', string='Purchase evaluation indicator')

	
class purchase_indicator_rate_employee(models.Model):
	_name = 'purchase.indicator.rate.employee'


	
	def _compute_state(self):
		employee_ids = []
		rate_employee_ids = []
		user_ids = []
		is_rated = True
		partner_count = 0
		employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self._uid)])
		if self.comparison_id:
			for emp in self.comparison_id.partner_ids:
				for part in emp.indicator_ids:
					partner_count+=1
		if self.comparison_id:
			for emp in self.comparison_id.partner_ids:
				for part in emp.indicator_ids:
					for rate in part.rate_ids:
						if rate.employee_id.id:
							employee_ids.append(rate.employee_id.id)
			
			_logger.info(u'Нийлүүлэгч тоо %s Ажилтаны тоо %s'%(partner_count,employee_ids.count(self.employee_id.id)))
			if employee_ids.count(self.employee_id.id) !=partner_count:					
				is_rated = False

			if is_rated :
				self.state = 'done'
			else :
				self.state = 'draft'



	employee_id = fields.Many2one('hr.employee', string="Employee")
	comparison_id = fields.Many2one('purchase.comparison', string='Purchase comparison')
	job_position = fields.Char(string='Job position', related='employee_id.job_id.name', )
	is_rater = fields.Boolean(string='Is rate')
	state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], compute=_compute_state, default='draft', string="State")

	@api.onchange('employee_id')
	def onchange_employee(self):
		self.job_position = self.employee_id.job_id.name
class purchase_indicators(models.Model):
	_name = 'purchase.indicators'

	comparison_id = fields.Many2one('purchase.comparison', string='Purchase comparison')
	indicator_id = fields.Many2one('evaluation.indicators', string='Evalution indicators')


class InheritEvaluationIndicators (models.Model):
	_inherit = 'evaluation.indicators.line'

	scale = fields.Float(string='Indicator scale')
	evalution_method = fields.Selection([('by_scale', 'Эзлэх жингээр'), 
									('by_descriptio', 'Үгэн тайлбараар')
									], default='by_scale', string="Үнэлгээний арга",required=True)


class CancelComparison(models.TransientModel):
	_name = 'cancel.comparison'

	@api.model
	def _get_comparison(self):
		if self._context.get('comparison_id'):
			return self._context.get('comparison_id')
		return None

	@api.onchange('comparison_id')
	def _get_parent_domain(self):
		if self.comparison_id:
			partners = [order_id.partner_id.id for order_id in self.comparison_id.order_ids]
			return {'domain': {'partner_id': [('id','in',partners)]}}


	comparison_id = fields.Many2one('purchase.comparison', default=_get_comparison)
	partner_id = fields.Many2one('res.partner',string='Purchase employee')

	
	def action_cancel(self):
		partner_id = self.comparison_id.partner_ids.search([('partner_id','=',self.partner_id.id),('comparison_id','=',self.comparison_id.id)])
		if partner_id:
			partner_id[0].is_winner = True
			for order_id in self.comparison_id.order_ids:
				if order_id.partner_id.id == self.partner_id.id:
					order_id.write({
						'state': 'purchase',
					})
				else:
					order_id.write({
						'state': 'cancel',
					})
		else:
			for order_id in self.comparison_id.order_ids:
				order_id.write({
					'state': 'cancel',
				})

			mail_user_ids = []
			purchase_order = self.env['purchase.order'].search([('comparison_id','=',self.comparison_id.id)], limit=1)
			if self.partner_id:
				order_id = self.env['purchase.order'].create({
					'partner_id': self.partner_id.id,
					'partner_ref': self.partner_id.nomin_code,
					'state': 'purchase',
					'comparison_id': self.comparison_id.id,
					'rfq_date_term': time.strftime('%Y-%m-%d'),
					'delivery_condition': purchase_order.delivery_condition,
					'installation_condition': purchase_order.installation_condition,
					'vat_condition': purchase_order.vat_condition,
					'delivery_term': purchase_order.delivery_term,
					'warranty_period': purchase_order.warranty_period,
					'return_condition': purchase_order.return_condition,
					'loan_term': purchase_order.loan_term,
					'barter_percentage': purchase_order.barter_percentage,
					'purchase_type':'compare',
				})
				mail_user_ids.append((self.partner_id,order_id))

			self.env['purchase.partner.comparison'].create({
				'partner_id': self.partner_id.id,
				'order_id': order_id.id,
				'comparison_id': self.comparison_id.id,
				'is_winner': True,
			})

			for partner in self.comparison_id.order_ids:
				if partner != order_id:
					for order in partner.order_line:
						if not self.env['purchase.order.line'].search([('product_id','=',order.product_id.id),('order_id','=',order_id.id)]):
							self.env['purchase.order.line'].create({
								'product_id': order.product_id.id,
								'product_qty': order.product_qty,
								'order_id': order_id.id,
								'product_uom': order.product_id.uom_id.id,
								'name': order.product_id.product_mark,
								'price_unit': 0,
								'date_planned': time.strftime('%Y-%m-%d'),
								'market_price': order.market_price,
								'market_price_total': 0,
								'price_subtotal': 0,
							})
			# if mail_user_ids:
			# 	self._send_mail(self.comparison_id, mail_user_ids, self.comparison_id.department_id, employee_id)

		self.comparison_id.write({
			'state': 'purchase',
		})

		requisition_line = self.env['purchase.requisition.line'].sudo().search([('comparison_id','=',self.comparison_id.id)])
		for line in requisition_line:
			line.write({
				'state': 'ready',
				'comparison_state': 'purchase',
				'comparison_date_end': time.strftime('%Y-%m-%d'),
				'comparison_confirmed_date': time.strftime('%Y-%m-%d %H:%M:%S'),
			})


		return {'type': 'ir.actions.act_window_close'}