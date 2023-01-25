# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.tools.translate import _
import time
from openerp.http import request    
from openerp.exceptions import UserError, ValidationError

class AddComparisonPartner(models.TransientModel):
	_name = 'add.comparison.partner'

	@api.model
	def _get_comparison(self):
		if self._context.get('comparison_id'):
			return self._context.get('comparison_id')
		return None

	comparison_id = fields.Many2one('purchase.comparison', default=_get_comparison)
	partner_ids = fields.One2many('purchase.comparison.multiple.partner','add_partner_id',string='Partner')

	@api.multi
	def action_add_partner(self):
		mail_user_ids = []
		employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
		purchase_order = self.env['purchase.order'].search([('comparison_id','=',self.comparison_id.id)], limit=1)
		if self.comparison_id.state == 'sent':
			state = 'comparison_created'
			is_created_in_sent = True
		else:
			state = 'sent_rfq'
			is_created_in_sent = False
		for line in self.partner_ids:
			existing_partners = [order_id.partner_id for order_id in self.comparison_id.order_ids]
			if line.partner_id not in existing_partners:
				order_id = self.env['purchase.order'].create({
					'partner_id': line.partner_id.id,
					'partner_ref': line.partner_id.nomin_code,
					'state': state,
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
					'is_created_in_sent': is_created_in_sent
				})
				mail_user_ids.append((line.partner_id,order_id))
			else:
				raise UserError(u'%s харилцагч бүртгэгдсэн эсвэл давтагдсан байна.'%(line.partner_id.name))

			partner_comparison = self.env['purchase.partner.comparison'].create({
				'partner_id': line.partner_id.id,
				'order_id': order_id.id,
				'comparison_id': self.comparison_id.id,
				'state': 'draft',
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

		if is_created_in_sent:
			self.comparison_id.insert_indicators()
			partner_comparison.write({
				'state': 'sent',
			})

		if mail_user_ids:
			self._send_mail(self.comparison_id, mail_user_ids, self.comparison_id.department_id, employee_id)

		return {'type': 'ir.actions.act_window_close'}

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
		# if partners_without_emails:
		# 	print '\n\n\n\partners_without_emails',partners_without_emails
			
		# 	# return {
		# 	# 	'name': 'Note',
		# 	# 	'view_type': 'form',
		# 	# 	'view_mode': 'form',
		# 	# 	'res_model': 'partner.without.email',
		# 	# 	# 'context':{'partners_without_emails':partners_without_emails},
		# 	# 	'type': 'ir.actions.act_window',
		# 	# 	# 'nodestroy': True,
		# 	# 	# 'target': 'new',
		# 	# }
		# 	raise Warning(("%s харилцагчид бүртгэлтэй мэйл хаяг байхгүй байна.") %(partners_without_emails))