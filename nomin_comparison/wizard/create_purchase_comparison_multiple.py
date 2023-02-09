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
from odoo.exceptions import UserError,ValidationError,Warning
from odoo import SUPERUSER_ID
from fnmatch import translate
from odoo.osv import osv
import time
from odoo.http import request    
import logging
_logger = logging.getLogger(__name__)

class purchaseComparisonMultiple(models.TransientModel):
	_name = 'purchase.comparison.multiple.wizard'

	warranty = fields.Integer(string='Length of warranty', default = 0) #Баталгаат хугацаатай эсэх (сараар)
	is_carriage = fields.Selection([('yes', u"Yes"),('no', u"No"),], string='Carriage') #Тээврийн зардал багтсан эсэх
	is_VAT = fields.Selection(
		[('has_VAT', u"НӨАТ-тай"),
		('hasnt_VAT', u"НӨАТ-гүй"),
		('has_ebarimt', u"ebarimt-тай хувь хүн"),
		('hasnt_ebarimt', u"ebarimt-гүй хувь хүн")
		], string=u'НӨАТ-тай эсэх')
	cost_of_assembling = fields.Integer(string='Cost of assembling', default = 0 )#Угсралтын зардалтай эсэх
	time_of_delivery = fields.Integer(string='Time of delivery', default = 0) #Нийлүүлэх хугацаа (хоногоор)
	cost_of_machine = fields.Integer(string='Cost of machine', default = 0) #Машин механизмийн зардал
	transportation_expense = fields.Integer(string='Transportation expense', default = 0) #Тээвэрлэлтийн зардал
	postage = fields.Integer(string='Postage', default = 0) #Шууд зардал
	other_cost = fields.Integer(string='Other cost', default = 0) #Бусад зардал

	delivery_condition      = fields.Selection([('required', u"Required"),('not_required', u"Not required")], string='Delivery condition') # Хүргэлтийн нөхцөл
	installation_condition   = fields.Selection([('required', u"Required"),('not_required', u"Not required")], string='Installation condition') # Угсралт, суурилуулалтын нөхцөл
	delivery_term       	= fields.Char('Delivery term /day/') # Нийлүүлэх хугацаа /хоног/
	warranty_period     	= fields.Char('Warranty period /day/') # Баталгаат хугацаа /хоног/
	return_condition    	= fields.Char('Return condition') # Буцаалтын нөхцөл
	loan_term           	= fields.Char('Loan term') # Зээлийн хугацаа
	barter_percentage   	= fields.Char('Barter percentage') # Бартерийн хувь
	vat_condition       	= fields.Selection([('required', u"Required"),('not_required', u"Not required")], string='VAT condition', tracking=True) # НӨАТ төлөгч байхыг шаардах эсэх

	partner_ids = fields.One2many('purchase.comparison.multiple.partner','comparison_id',string='Partner')
	product_ids = fields.One2many('purchase.comparison.multiple.product','comparison_id',string='Product')

	
	def create_comparison(self):
		#Үүсгэж буй хэрэглэгчийн дараах мэдээллүүдийг автоматаар авч үүснэ. Хэрэглэгч, огноо, салбар, хэлтэс

		if not self.partner_ids:
			raise ValidationError('Харилцагч сонгоно уу.')
		if not self.product_ids:
			raise ValidationError('Бараа сонгоно уу.')

		employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
		department_id = self.env['hr.department'].browse(employee_id[0].department_id.id)
		sector_id = self.env['hr.department'].get_sector(department_id.id)

		comparison_id = self.env['purchase.comparison'].create({
			'date': time.strftime('%Y-%m-%d'),
			'user_id': self.env.user.id,
			'department_id': department_id.id,
			'sector_id': sector_id,
			'state': 'draft'  
		})


		#Үнийн саналын хүсэлт үүсгэх
		mail_user_ids = []
		for line in self.partner_ids:
			order_id = self.env['purchase.order'].create({
				'partner_id': line.partner_id.id,
				'partner_ref': line.partner_id.nomin_code,
				'state': 'sent_rfq',
				'comparison_id': comparison_id.id,
				# 'equipment_amount': self.cost_of_machine,
				# 'carriage_amount': self.transportation_expense,
				# 'postage_amount': self.postage,
				# 'other_amount': self.other_cost,
				'delivery_condition': self.delivery_condition,
				'installation_condition': self.installation_condition,
				'vat_condition': self.vat_condition,
				'delivery_term': self.delivery_term,
				'warranty_period': self.warranty_period,
				'return_condition': self.return_condition,
				'loan_term': self.loan_term,
				'barter_percentage': self.barter_percentage,
				'purchase_type':'compare',
			})

			mail_user_ids.append((line.partner_id,order_id))

			self.env['purchase.partner.comparison'].create({
				'partner_id': line.partner_id.id,
				'order_id': order_id.id,
				'comparison_id': comparison_id.id,
			})

			for product_line in self.product_ids:
				if product_line.product_qty > 0:
					self.env['purchase.order.line'].create({
						'product_id': product_line.product_id.id,
						'product_qty': product_line.product_qty,
						'order_id': order_id.id,
						'product_uom': product_line.product_id.uom_id.id,
						'name': product_line.product_id.product_mark,
						'price_unit': product_line.price_unit,
						'date_planned': time.strftime('%Y-%m-%d'),
						'market_price': product_line.market_value,
						'market_price_total': product_line.market_price_total,
						'price_subtotal': product_line.price_subtotal,
					})
				else:
					raise UserError(u'Барааны тоо хэмжээ 0-ээс их байх ёстойг анхаарна уу.')

		if mail_user_ids:
			self._send_mail(comparison_id, mail_user_ids, department_id, employee_id)

	def _send_mail(self, comparison_id, mail_user_ids, department_id, employee_id):
		partners_without_emails = []
		for partner_id in mail_user_ids:
			template = self.env['ir.actions.report.xml'].search([('report_name','=','nomin_purchase.report_rfq')])

			subject = u'"Номин Холдинг ХХК Захиалга (Ref %s)".'%(comparison_id.name)
			body_html = u'''
			<p>Сайн байна уу? %s, </p>
			<p>Танд энэ өдрийн мэндийг хүргэе. </p>
			<p>Номин Холдинг ХХК-ийн үнийн саналын хүсэлт илгээж байна. Бараа, ажил үйлчилгээг нийлүүлэх саналаа ирүүлнэ үү. </p>
			<p> &nbsp; &nbsp; RFQ дугаар: %s </p>
			<p> &nbsp; &nbsp; Үнийн санал хүлээн авах хугацаа: %s</p>
			<p> &nbsp; &nbsp; Нийлүүлэгчийн нэр: %s </p>
			<p> &nbsp; &nbsp; Холбогдох ажилтан: %s салбарын %s %s </p>
			<p>
			Та дараах холбоосоор орж үнийн саналаа оруулах боломжтой ба procurement@nomin.net хаяг руу бүртгэлийн мэдээллээ явуулж, системд нэвтрэх эрхээ идэвхжүүлнэ үү.
			</p>
			<p>Бүртгэлийн маягтыг procurement.nomin.net хаягаар орж 'Бүртгүүлэх' товч дарж татан авна уу.</p>
			<h4>Номин Холдинг ХХК</h4>
			<p>Холбоо барих: "Номин Холдинг" ХХК-ийн Номин Юнайтед оффис Хан-Уул дүүрэг, Чингисийн өргөн чөлөө, Улаанбаатар 17042, Монгол Улс, 210136, Ш/Ч-2316 </p>
			<p>Утас: 1800 2888, Факс: 976 75779999, И-мэйл: procurement@nomin.net</p>
			<p>Вэб: procurement.nomin.net</p>
			</br>
			<p>---</p>
			</br>
			<p>Энэхүү мэйл нь "Номин Холдинг" ХХК-ийн худалдан авах ажиллагааны системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
			<p>Баярлалаа.</p>
			'''%( partner_id[0].name,
			comparison_id.name,
			partner_id[1].date_order,
			partner_id[0].name,
			department_id.name,
			employee_id.job_id.name,
			employee_id.name_related
			)
			if partner_id[0].email:					
					email_template = self.env['mail.template'].create({
					'name': _('Followup '),
					'email_from': self.env.user.company_id.email or '',
					'model_id': self.env['ir.model'].search([('model', '=', 'purchase.order')]).id,
					'subject': subject,
					'email_to': partner_id[0].email,
					'lang': self.env.user.lang,
					'auto_delete': True,
					'body_html':body_html,
					'report_template':template[0].id,
					})
					email_template.send_mail(partner_id[1].id)
					self.env.cr.commit()
			else:
				partners_without_emails.append(partner_id[0].name)
				# warning = {
				# 	'title': (u'Анхааруулга!'),
				# 	'message': (u'Хүлээн авах харилцагч сонгогдсон байх шаардлагтай!'),
				# }
			
		# 	# return {
		# 	# 	'name': 'Note',
		# 	# 	'view_mode': 'form',
		# 	# 	'res_model': 'partner.without.email',
		# 	# 	# 'context':{'partners_without_emails':partners_without_emails},
		# 	# 	'type': 'ir.actions.act_window',
		# 	# 	# 'nodestroy': True,
		# 	# 	# 'target': 'new',
		# 	# }
		# 	raise Warning(("%s харилцагчид бүртгэлтэй мэйл хаяг байхгүй байна.") %(partners_without_emails))


class PurchaseComparisonMultiplePartner(models.TransientModel):
	_name = 'purchase.comparison.multiple.partner'

	#Partner tab
	partner_id = fields.Many2one('res.partner', string='Partner')
	partner_lastname = fields.Text(string='Partner last name')
	partner_nomin_code = fields.Text(string='Partner nomin code')
	partner_phone = fields.Text(string='Partner phone')
	partner_email = fields.Text(string='Partner email')
	comparison_id = fields.Many2one('purchase.comparison.multiple.wizard',string = 'Comparison')
	add_partner_id = fields.Many2one('add.comparison.partner',string='Add partner')

	@api.onchange('partner_id')
	def _onchange_partner_id(self):
		if self.partner_id:
			self.partner_name = self.partner_id.name
			self.partner_lastname = self.partner_id.last_name
			self.partner_nomin_code = self.partner_id.nomin_code
			self.partner_phone = self.partner_id.mobile
			self.partner_email = self.partner_id.email

class PurchaseComparisonMultipleProduct(models.TransientModel):
	_name = 'purchase.comparison.multiple.product'

	#Product tab
	product_id = fields.Many2one('product.product', string='Product', domain=[('product_tmpl_id.is_new','=',True),('product_tmpl_id.cost_price','>',0)], change_default=True, required=True)
	product_description = fields.Char(string='Product description') #Тодорхойлолт
	product_qty = fields.Float('Product quantity') #Тоо хэмжээ
	market_value = fields.Float('Market price') #Зах зээлийн үнэ
	market_price_total = fields.Float('Market subtotal') #Зах зээлийн дэд дүн
	price_subtotal = fields.Float('Price subtotal') #Дэд дүн
	price_unit = fields.Float('Price unit') #Нэгж үнэ
	comparison_id = fields.Many2one('purchase.comparison.multiple.wizard',string = 'Comparison')
	add_product_id = fields.Many2one('add.comparison.product',string='Add product')


	@api.onchange('product_id')
	def _onchange_product_id(self):
		if self.product_id:
			self.product_description = self.product_id.product_mark
			self.price_unit = self.product_id.cost_price
			self.market_value = self.product_id.standard_price

	@api.onchange('product_qty')
	def _onchange_product_qty(self):
		self.price_subtotal = self.product_qty * self.price_unit
		self.market_price_total = self.product_qty * self.market_value

	@api.onchange('market_value')
	def _onchange_market_value(self):
		self.price_subtotal = self.product_qty * self.price_unit
		self.market_price_total = self.product_qty * self.market_value
	
	@api.onchange('price_unit')
	def _onchange_price_unit(self):
		self.price_subtotal = self.product_qty * self.price_unit
		self.market_price_total = self.product_qty * self.market_value

class PartnerWithoutEmail(models.TransientModel):
	_name = 'partner.without.email'

	@api.model
	def default_get(self, fields):
		res = super(PartnerWithouthEmail, self).default_get(fields)	
		partners_without_emails = self._context.get('partners_without_emails', [])
		if partners_without_emails:		   
			res.update({'partners':partners_without_emails})
		return res

	partners = fields.Text(string="Partners")
	