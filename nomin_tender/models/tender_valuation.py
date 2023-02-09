# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from dateutil import relativedelta 
import time
import traceback
import base64

from odoo import api, fields, models, SUPERUSER_ID, _
import odoo.tools
from odoo import tools

from odoo.http import request
from odoo.exceptions import UserError, ValidationError
from fnmatch import translate
import logging
_logger = logging.getLogger(__name__)

"""Тендерийн үнэлгээ: Тендерийн үзүүлэлтүүдийн нэр, анхны утга орж ирнэ. Макс утга нь орж ирнэ. 
	- Макс утга
	- Тендерийн төрөл
	- үнэлгээ өгч байгаа хсэг хэрэглэгчин хувьд
"""

STATE_SELECTION = [
        ('draft','Draft'),
        ('open','Open Valuation'),
        ('completed','Completed Valuation'),
        ('approved','Approved'),
    ]

class TenderRate(models.Model):
	_name = 'tender.rate'
	_description = "Tender Rate"
	_inherit = ['mail.thread', 'mail.activity.mixin']
	'''Тендерийн үзүүлэлт
	'''
# 	
# 	def _get_avg_value(self):
# 		for this in self:
# 			this.avg_value = 0
		
	
	@api.depends('child_ids','child_ids.default_max_value')
	def _get_avg_value(self):
		'''Үзүүлэлтийн мөрүүдээс дундаж оноог тооцоолох'''
		for this in self:
			lenth=len(this.child_ids.ids)
			this.default_avg_value = 0
			if lenth:
				this.default_avg_value = sum([val.default_max_value for val in this.child_ids])/len(this.child_ids.ids)
				
	name		 		= fields.Char('Name', required=True,tracking=True)
	parent_id	 		= fields.Many2one('tender.rate', 'Parent Rate',tracking=True)
	default_max_value	= fields.Float('Default Max Value', default=10,tracking=True)
	default_avg_value  	= fields.Float('Default Average Value', compute=_get_avg_value, store=True,tracking=True)
	child_ids			= fields.One2many('tender.rate', 'parent_id', string="Child Rate",tracking=True)
 	
	
	def name_get(self):
		'''Үзүүлэлтийн нэр, дэд үзүүлэлтийн нэр залгаж харуулна'''
		result = []
		for rate in self:
			name = rate.name or ''
			if rate.parent_id:
				name = rate.parent_id.name + ' / ' + name
			result.append((rate.id,name))
		return result
	   
	
	def write(self, vals):
		'''Эцэг үзүүлэлт дээр өөрийгөө сонгох боломжгүй байна'''
		parent_id=False
		if vals.get('parent_id'):
			parent_id = vals.get('parent_id')
		else:
			parent_id = self.parent_id.id
		    
		if parent_id == self.id:
			raise UserError(_(u'Өөрөө өөрийгөө эцэг үзүүлэлтээр сонгох боломжгүй !'))
		result = super(TenderRate, self).write(vals)
		return result
    
	
	def unlink(self):
		'''Үзүүлэлт дэд төрөлтэй бол устгах боломжгүй байна'''
		for order in self:
			if order.child_ids:
				raise UserError(_(u'Та дэд төрөлтэй тендерийн үзүүлэлтийг устгах боломжгүй.'))
		return super(tender_rate, self).unlink()

"""Тендерийн төрлийн үнэлгэнйи макс оноо тохируулах"""
class TenderTypeRateMax(models.Model):
	_name = 'tender.type.rate.max'
	_description = "Tender Rate Rate Max"
	_inherit = ['mail.thread', 'mail.activity.mixin']
	
	rate_id 		= fields.Many2one('tender.rate','Rate', required=True,tracking=True)
	tender_type_id 	= fields.Many2one('tender.type','Tender Type', domain=[('parent_id','=',False)],tracking=True)
	max_value	 	= fields.Float('Max Value', required=True,tracking=True)

	def get_max_value(self):
		'''Макс оноо тохируулах'''
		max_value = 0
		rate_id = self.rate_id
		while(rate_id):
			if rate_id.default_max_value:
				max_value = rate_id.default_max_value
				break
			else:
				rate_id = rate_id.parent_id
		return max_value
	
	@api.onchange('rate_id')
	def _onchange_rate_id(self):
		'''Үзүүлэлийг солиход үзүүлэлтийн оноо шинэчилнэ'''
		
		self.max_value = self.get_max_value()
		
	@api.onchange('max_value')
	def _onchange_max_value(self):
		'''Үзүүлэлийг макс оноо 0.1ээс их байна'''
		if self.max_value < 0.1:
			self.max_value = self.get_max_value()

	@api.model
	def create(self, vals):
		'''Үзүүлэлтийн оноо тохируулах үед нэг төрөл 
		   дээр, ижил үзүүлэлт байж болохгүй
	    '''
		if vals.get('tender_type_id') or vals.get('rate_id'):
			type = self.env['tender.type.rate.max'].search([('tender_type_id','=',vals.get('tender_type_id')),('rate_id','=',vals.get('rate_id'))])
			if type:
				raise UserError(_(u'Нэг төрөл дээр ижил үзүүлэлт тохируулах боломжгүй !'))
		result = super(TenderTypeRateMax, self).create(vals)
		return result
    
	
	def write(self, vals):
		'''Үзүүлэлтийн оноо тохируулах үед нэг төрөл 
		   дээр, ижил үзүүлэлт байж болохгүй
	    '''
		max_vals = {}
		tender_type_id=False
		rate_id=False
		if vals.get('tender_type_id'):
			tender_type_id = vals.get('tender_type_id')
		else:
			tender_type_id = self.tender_type_id.id
		if vals.get('rate_id'):
			rate_id = vals.get('rate_id')
		else:
			rate_id = self.rate_id.id
		    
		if tender_type_id or rate_id:
			type = self.env['tender.type.rate.max'].search([('tender_type_id','=',tender_type_id),('rate_id','=',rate_id)])
			if type:
				if type[0].id != self.id:
					raise UserError(_(u'Нэг төрөл дээр ижил үзүүлэлт тохируулах боломжгүй !'))
		result = super(TenderTypeRateMax, self).write(vals)
		return result
    
"""MТендерийн төрөл: Үнэлгээний макс оноо өгч байгаа хэсэг"""
class TenderType(models.Model):
	_inherit = ["tender.type"]

	rate_max_ids = fields.One2many('tender.type.rate.max', 'tender_type_id', string="Rate Max Values")

"""Тендерийн үнэлгээ: """
class TenderValuation(models.Model):
	_name = 'tender.valuation'
	_description = "Tender Valuation"
	_order = "create_date desc"
	_inherit = ['mail.thread', 'mail.activity.mixin']
	
	# 
	# def _get_avg_value(self):
	# 	for this in self:
	# 		this.avg_value = 0

	name					= fields.Char('Valuation name or code', tracking=True)
	tender_id 				= fields.Many2one('tender.tender', string='Tender', tracking=True, ondelete="restrict")
	valuation_partner_ids	= fields.One2many('tender.valuation.partner', 'tender_valuation_id', 'Participants')
	valuation_employee_ids	= fields.One2many('tender.valuation.employee.valuation', 'tender_valuation_id', 'Commission Members')
	bidding_line_ids		= fields.One2many('tender.participants.control.budget.line', 'valuation_id', 'Commission Members')
	confirm_date			= fields.Date(string='Date')
	is_choose				= fields.Boolean(string="Is Choose Partner", default=False)
	state					= fields.Selection(STATE_SELECTION, string='State', readonly=True, default='draft', tracking=True)
	
	
	def send_tender_valuation(self):
		'''Тендер шалгаруулалтын үр дүн гарахад имэйл илгээнэ'''
		base_url = self.env['ir.config_parameter'].get_param('web.base.url')
		action_id = self.env['ir.model.data']._xmlid_to_res_id('nomin_tender.tender_valuation_list_menu_action')
		db_name = request.session.db
		group_user = self.env['ir.model.data']._xmlid_to_res_id('nomin_tender.group_tender_manager')
		
		sel_user_ids = []
		sel_user_ids = self.env['res.users'].search([('groups_id','in',group_user)])
		state = u'Тендерийн хүсэлт'
		if self.tender_id.state == 'published':
			state =  u'Нийтлэгдсэн'
		elif self.tender_id.state == 'bid_expire':
			state =  u'Бичиг баримт хүлээн авч дууссан'
		elif self.tender_id.state == 'closed':
			state =  u'Бичиг баримт хүлээн авч дууссан'
		elif self.tender_id.state == 'in_selection':
			state =  u'Сонгон шалгаруулалт'
		elif self.tender_id.state == 'finished':
			state =  u'Дууссан'
		elif self.tender_id.state == 'cancelled':
			state =  u'Хүчингүй болсон'
		subject = u'"%s" дугаартай "%s" тендерт бүх гишүүд санал өгч дууслаа. Үнэлгээг баталгаажуулна уу.'%( self.tender_id.name,self.tender_id.desc_name)
		body_html = u'''
		                <h4>Сайн байна уу ?, 
		                    Таньд энэ өдрийн мэнд хүргье! <br/>
		                    "%s" дугаартай "%s" тендерт бүх гишүүд санал өгч дууслаа. Үнэлгээг баталгаажуулна уу.</h4>
		                    <p><li><b>Тендерийн дугаар: </b>%s</li></p>
		                    <p><li><b>Тендерийн нэр: </b>%s</li></p>
		                    <p><li><b>Тендерийн ангилал: </b>%s</li></p>
		                    <p><li><b>Дэд ангилал: </b>%s</li></p>
		                    <p><li><b>Товлосон захиалгын огноо: </b>%s</li></p>
		                    <p><li><b>Төлөв: </b>%s</li></p>
		                    </br>
		                    <p>"%s" - н мэдээллийг <b><a href=%s/web?db=%s#id=%s&model=tender.valuation&action=%s>Тендер/Тендерийн үнэлгээ/Тендерийн үнэлгээ</a></b> цонхоор дамжин харна уу.</p>
		                    <p>--</p>
		                    <p>Энэхүү мэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
		                    <p>Баярлалаа..</p>
		            '''%( self.tender_id.name,self.tender_id.desc_name, self.tender_id.name,self.tender_id.desc_name,self.tender_id.type_id.name,
							self.tender_id.child_type_id.name,self.tender_id.ordering_date,state,self.name,
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
						'model_id': self.env['ir.model'].search([('model', '=', 'tender.valuation')]).id,
						'subject': subject,
						'email_to': email,
						'lang': self.env.user.lang,
						'auto_delete': True,
						'body_html':body_html,
						#  'attachment_ids': [(6, 0, [attachment.id])],
						})
				email_template.sudo().send_mail(self.id)
#	Түр комммент болгов.	
	
	def write(self, vals):
		'''Төлвөөс хамаарч имэйл илгээнэ, дагагч нэмнэ'''
		partner_ids = []
		for add in self:
			if vals.get('state')=='completed':
				add.send_tender_valuation()
			if vals.get('state')=='approved':
				for emp in add.valuation_employee_ids:
					partner_ids.append(emp.employee_id.user_id.partner_id.id)
				add.message_subscribe(partner_ids=partner_ids)
				
		return super(TenderValuation, self).write(vals)		
	
	
	def action_confirm(self):
		'''Комиссын гишүүд өөрсдийнхөө үнэлгээг дууссан төлөвт оруулна
	    '''
		employee_val_obj=self.env['tender.valuation.employee.valuation']
		for valuation in self:
# 			if valuation.tender_id.meeting_ids:
# 				for order in valuation.tender_id.meeting_ids:
# 					if order.state == 'confirmed':
# 						if order.meeting_from_date >= time.strftime('%Y-%m-%d %H:%M:%S'):
# 							raise UserError(_(u'Хурлын цаг болоогүй байна !'))
# 					else:
# 						raise UserError(_(u'Хурлын цаг батлагдаагүй байна !'))
# 			else:
# 				raise UserError(_(u'Хурлын цаг товлогдоогүй байна !'))
#  				
				for row in valuation.sudo().valuation_employee_ids:
# 					row.partner_valuation_ids.write({'state':'open'})
					row.line_ids.sudo().write({'state':'open'})
				for line in valuation.valuation_partner_ids:
# 					line.partner_valuation_ids.sudo().write({'state':'open'})
					line.employee_partner_ids.sudo().write({'state':'open'})
					self.env['tender.participants.control.budget.line'].create({
																			'tender_id': valuation.tender_id.id,
																			'valuation_id': valuation.id, 
																			'participant_id': line.participant_id.id,
																			})
				valuation.valuation_partner_ids.write({'state':'open'})
				valuation.sudo().valuation_employee_ids.write({'state':'open'})
				valuation.write({'state': 'open'})
	
	
	def action_update(self):
		'''Тендер менежер
	    '''
		
		for valuation in self:
				valuation.bidding_line_ids.sudo().unlink()
				for line in valuation.valuation_partner_ids:
					# line.employee_partner_ids.sudo().write({'state':'open'})
					self.env['tender.participants.control.budget.line'].create({
																			'tender_id': valuation.tender_id.id,
																			'valuation_id': valuation.id, 
																			'participant_id': line.participant_id.id,
																			})
				# valuation.valuation_partner_ids.write({'state':'open'})
				# valuation.sudo().valuation_employee_ids.write({'state':'open'})
				# valuation.write({'state': 'open'})

		
	
	def action_completed(self):
		for order in self:
			order.write({'state': 'completed'})


	
	def action_back_open(self):
		employee_valuation = self.env['tender.valuation.employee.valuation'].search([('tender_valuation_id','=',self.id)])
		if employee_valuation:
			for line in employee_valuation:
				for employee in line.line_ids:
					employee.write({'state': 'open'})
				for partner in line.employee_partner_ids:
					partner.write({'state': 'open'})
		if self.valuation_employee_ids:
			for line in self.valuation_employee_ids:
				line.write({'state': 'open'})
		if self.valuation_partner_ids:
			for line in self.valuation_partner_ids:
				line.write({'state': 'open'})

		self.write({'state': 'open'})

	
	
	def action_approved(self):
		'''Тендерийн хорооны дарга үнэлгээний 
			төлвийг зөвшөөрсөн төлөвт оруулна
		'''
		
		for valuation in self:
			max_obj = []
			for line in valuation.sudo().valuation_partner_ids:
				max_obj.append(line.total_value)
				_logger.info(u'\n\n\n\n\nГишүүний оноо update %s', line)
				line.sudo().employee_partner_ids.write({'state': 'approved'})
			count=0
			for lists in max_obj:
				if max(max_obj) == lists:
					count+=1
			if count >= 2:
				raise UserError(_(u'Оноо тэнцсэн байна.'))
			for row in valuation.sudo().valuation_employee_ids:
				row.line_ids.sudo().write({'state': 'approved'})
			valuation.valuation_partner_ids.write({'state': 'approved'})
			valuation.sudo().valuation_employee_ids.write({'state': 'approved'})
			valuation.tender_id.write({'is_valuation_finished': True,'state': 'finished'})
			valuation.write({'state': 'approved'})
			for line in valuation.sudo().valuation_partner_ids:
				if line.total_value == max(max_obj):
					line.confirm_partner()

	
	def unlink(self):
		'''Тендерийн үнэлгээг нооргоос бусад үед устгах боломжгүй'''
		for order in self:
			if order.state != 'draft':
				raise UserError(_(u'Та зөвхөн ноорог үнэлгээг устгах боломжтой !'))
		return super(TenderValuation, self).unlink()

"""Тендерийн харилцагчийн нийт үнэлгээний дундаж: Харилцагчийн бүх шинжийн нийт оноо"""
class TenderValuationPartner(models.Model):
	_name = 'tender.valuation.partner'
	_description = "Tender Valuation Partner"
	_order = "create_date desc"
	_inherit = ['mail.thread', 'mail.activity.mixin']
	
	
	def name_get(self):
		'''Харилцагчийн нэр, тендерийн үнэлгээний нэрийг залгаж харуулна'''
		result = []
		for rate in self:
			name = rate.tender_valuation_id.name or ''
			if rate.partner_id:
				name = name + ' / ' + rate.partner_id.name
			result.append((rate.id,name))
		return result
	       
	
	def _get_total_value(self):
		'''Мөрийн нийлбэр нийт оноог тооцоолно'''
		self.total_value = sum([val.total_value for val in self.employee_partner_ids])

	tender_id 				= fields.Many2one('tender.tender', string='Tender', tracking=True, ondelete="restrict", index=True)
	tender_valuation_id 	= fields.Many2one('tender.valuation', 'Tender Valuation', ondelete="cascade", tracking=True)
	participant_id			= fields.Many2one('tender.participants.bid', u'Үнийн санал', ondelete="restrict")
	partner_id 				= fields.Many2one('res.partner','Participants Of Tender', tracking=True, ondelete="restrict")
	total_value  			= fields.Float('Total Value', compute=_get_total_value, tracking=True)
	employee_partner_ids	= fields.One2many('tender.valuation.employee.partner', 'tender_valuation_partner_id', 'Partner Valuations Of Employee')
	state					= fields.Selection(STATE_SELECTION, string='State', readonly=True, default='draft', tracking=True)
	is_win					= fields.Boolean(string="Is Partner Win", default=False)
	is_sent					= fields.Boolean(string="Is sent", default=False)
	is_choose				= fields.Boolean(string="Is Choose Partner ?", default=False)
	reason					= fields.Text(string="Reason", tracking=True)
	# fields_view_get функц ашиглах
	
	
	def send_tender_result(self):
		'''Тендерийн үр дүн гарахад имэйл илгээнэ'''
		template_id = self.env['ir.model.data']._xmlid_to_res_id('nomin_tender.tender_valuation_result_email_template')
		val_obj = self
		tender_obj = self.env['tender.tender'].browse(val_obj.tender_id.id)
		
		data = {
		        'subject': u'"Номин Холдинг" ХХК-ийн "%s" тендерийн үр дүн гарлаа.'%(tender_obj.desc_name),
		        'company': tender_obj.company_id.name,
		        'name': tender_obj.name,
		        'desc_name': tender_obj.desc_name,
		        'is_win': self.is_win,
		        'description': val_obj.reason,
		        'model': 'tender.tender',
		        }
		self.env.context = data
		self.pool['mail.template'].send_mail(self.env.cr, 1, template_id, val_obj.partner_id.id, force_send=True, context=self.env.context)
		return True
    
	
	def confirm_partner(self):
		'''Гэрээ байгуулах харилцагчийг баталгаажуулна'''
		for order in self:
			obj = self.env['tender.valuation.partner'].search([('tender_id','=',self.tender_id.id),('tender_valuation_id','=',self.tender_valuation_id.id),('is_win','=',True)])
			if not obj:
				order.write({'is_win':True, 'is_choose':True})
				order.tender_valuation_id.write({'is_choose':True})
				order.tender_valuation_id.valuation_partner_ids.write({'is_choose':True})
			else:
				raise UserError(_(u'Харилцагч баталгаажсан байна.'))
			
				
		return {
		    'type': 'ir.actions.client',
		    'tag': 'reload',
		}
	
	
	def unlink(self):
		'''Ноорог үнэлгээг устгах боломжтой'''
		for order in self:
			if order.tender_valuation_id.state != 'draft':
				raise UserError(_(u'Та зөвхөн ноорог үнэлгээг устгах боломжтой !'))
		return super(TenderValuationPartner, self).unlink()

"""Ажилтаны үнэлсэн төлөв, байдал"""
class TenderValuationEmployeeValuation(models.Model):
	_name = 'tender.valuation.employee.valuation'
	_description = "Tender Valuation Employee Valuation"
	_order = "create_date desc"
	_inherit = ['mail.thread', 'mail.activity.mixin']
# 5723116

	
	def _is_in_commission_group(self):
		'''Үнэлгээ өгөх комиссын гишүүн мөн эсэхийг шалгана'''
		user_obj = self.env['res.users']
		emp_obj = self.env['hr.employee']
		notif_groups = self.env['ir.model.data']._xmlid_to_res_id('nomin_tender.group_tender_committee_members')
		sel_user_ids = user_obj.search([('groups_id','in',notif_groups)])
		for valuation in self:
			valuation.is_in_commission = False
			if self._uid in sel_user_ids._ids:
				emp = emp_obj.search([('user_id','=',self._uid)])
				if emp.id == valuation.employee_id.id:
					valuation.is_in_commission = True
	
	name 						= fields.Char('Tender Valuation', related="tender_valuation_id.name")				
	is_in_commission			= fields.Boolean('Is in Commission', compute=_is_in_commission_group)
	tender_id 					= fields.Many2one('tender.tender', string='Tender', tracking=True, ondelete="restrict")
	tender_valuation_id 		= fields.Many2one('tender.valuation', 'Tender Valuation', ondelete="cascade", tracking=True)
	employee_id					= fields.Many2one('hr.employee', 'Rate of Employee', tracking=True, ondelete="restrict")
	employee_partner_ids		= fields.One2many('tender.valuation.employee.partner', 'employee_valuation_id', 'Partner Valuations Of Employee')
	line_ids					= fields.One2many('tender.valuation.rate.line', 'employee_valuation_id', 'Valuation line')
	state						= fields.Selection(STATE_SELECTION, string='State', readonly=True, default='draft', tracking=True)
	
	
	def write(self, vals):
		'''Дагагч нэмнэ'''
		partner_ids = []
		for emp_val in self:	
			if vals.get('state')=='approved':
				for emp in emp_val.tender_valuation_id.valuation_employee_ids:
					partner_ids.append(emp.employee_id.user_id.partner_id.id)
				emp_val.message_subscribe(partner_ids=partner_ids)
				
		return super(TenderValuationEmployeeValuation, self).write(vals)		
 	
	
	def action_complete(self):
		'''Комиссын гишүүн өөрийн үнэлгээг дууссан төлөвт шилжүүлнэ'''
		ratename = ''
		rate = ''
		rates_m = []
		rates_l = []
		member_m = ''
		member_l = ''
		empComment = ''
		comment = []
		comments = ''
		committee_member_obj = self.env['tender.committee.member']
		for order in self:
			protocol_obj = self.env['tender.protocol'].sudo().search([('tender_id','=',order.tender_id.id),('state','in',['open','done','sent'])])
			_logger.info(u'\n\n\n\n\n Коммент бичих протокол %s', protocol_obj)
			if not protocol_obj:
				raise UserError(_(u'Хурлын протокол үүсч баталгаажсаны дараа үнэлгээгээ илгээнэ үү !'))
			else:
				protocol_id = protocol_obj[0]
 				
			member_id = committee_member_obj.sudo().search([('tender_id','=',order.tender_id.id),('employee_id','=',order.employee_id.id)])
			member_id.write({'state': 'complete'})
			for line in order.line_ids:
 
				if line.rate_value > line.max_value:
					ratename=line.rate_id.name
					rates_m.append(ratename)
					member_m = ' ; '.join(rates_m)
 
# 				if line.rate_value <= 0.0:
# 					rate=line.rate_id.name
# 					rates_l.append(rate)
# 					member_l = ' ; '.join(rates_l)
 			
# 			
			if member_m:
				raise UserError(_(u'Таны үнэлгээний оноо үзүүлэлтийн боломжит онооноос хэтэрсэн байна. Үзүүлэлт: %s' %(member_m)))
# 			if member_l:
# 				raise UserError(_(u'Таны үнэлгээний оноо үзүүлэлтийн боломжит оноонд хүрэхгүй байна. Үзүүлэлт: %s' %(member_l)))
             
			empname=order.employee_id.name
			for emp_part in order.employee_partner_ids:
				if emp_part.comment:
					empComment = emp_part.comment
					comment.append(emp_part.partner_id.name+":"+empComment)
					comments = ' ; '.join(comment)
            	
            	
             
			order.tender_valuation_id.sudo().message_subscribe(partner_ids =[self.env.user.partner_id.id])
			order.write({'state': 'completed'})
			for emp in order.employee_partner_ids:
				emp.write({'state': 'completed'})
			for row in order.line_ids:
				row.write({'state': 'completed'})
				
			order.line_ids.write({'state': 'completed'})
			line_res = self.env['tender.valuation.employee.valuation'].sudo().search([('tender_valuation_id','=',order.tender_valuation_id.id),('tender_id','=',order.tender_id.id),('state','in',['open'])])
			if not line_res:
				order.tender_valuation_id.sudo().write({'state':'completed'})
				for partner_val in order.tender_valuation_id.sudo().valuation_partner_ids:
					partner_val.write({'state':'completed'})
					for part_val in partner_val.employee_partner_ids:
						part_val.write({'state':'completed'})
						for part_line in part_val.line_ids:
							part_line.write({'state':'completed'})
				
				for employee_val in order.tender_valuation_id.sudo().valuation_employee_ids:
					employee_val.write({'state':'completed'})
					for emp_line in employee_val.line_ids:
						emp_line.write({'state':'completed'})
 						
			text = ''
			if comments:
				title = unicode('{ ' + str(empname)+' бичсэн сэтгэгдэл: '+str(comments)+' .}','utf-8')
				body=""
				if protocol_id.employee_comments:
					text=protocol_id.employee_comments
				if protocol_id.employee_html_comments:
					if 'body' in protocol_id.employee_html_comments:
						
						comment_body = str(protocol_id.employee_html_comments).split("body")[1]
						count = len(comment_body)-3
						body=comment_body[1:count]

				body=body+"""<tr class=""><td style="width:200px" class="oe_list_field_cell oe_list_field_many2one    ">%s</td><td style="width:100px"   class="oe_list_field_cell oe_list_field_float oe_readonly ">%s</td><td class="oe_list_field_cell oe_list_field_float oe_readonly ">%s</td><td  style="width:100px" class="oe_list_field_cell oe_list_field_float oe_readonly ">%s</td></tr>"""%(order.employee_id.job_id.name,empname,comments,str(order.write_date)[0:10])

				html_text="""<table class="oe_list_content table table-bordered"><thead><tr class="oe_list_header_columns"><th style="width:200px" class="oe_list_header_many2one oe_sortable"><div>Албан тушаал<span>&nbsp;</span></div></th><th style="width:100px" class="oe_list_header_float oe_sortable"><div>Овог нэр<span>&nbsp;</span></div></th><th  class="oe_list_header_float oe_sortable"><div>Сэтгэгдэл<span>&nbsp;</span></div></th><th  style="width:100px" class="oe_list_header_float oe_sortable"><div>Огноо<span>&nbsp;</span></div></th></tr></thead><tbody>%s</tbody></table>"""%body
				protocol_id.write({'employee_comments':text+'\n'+title,'employee_html_comments':html_text})


 			
	#===========================================================================
	# 
	# def action_complete(self):
	# 	ratename = ''
	# 	rate = ''
	# 	rates_m = []
	# 	rates_l = []
	# 	member_m = ''
	# 	member_l = ''
	# 	empComment = ''
	# 	comment = []
	# 	comments = ''
	# 	committee_member_obj = self.env['tender.committee.member']
	# 	for order in self:
 # 			
	# 		member_id = committee_member_obj.sudo().search([('tender_id','=',order.tender_id.id),('employee_id','=',order.employee_id.id)])
	# 		member_id.write({'state': 'complete'})
 # 
	# 		order.write({'state': 'completed'})
	# 		line_res = self.sudo().search([('tender_valuation_id','=',order.tender_valuation_id.id),('tender_id','=',order.tender_id.id),('state','in',['open'])])
	# 		if not line_res:
	# 		    order.tender_valuation_id.write({'state':'completed'})
	# 		    order.employee_partner_ids.write({'state':'completed'})
	# 		    order.line_ids.write({'state':'completed'})
	# 		    for line in order.tender_valuation_id.valuation_partner_ids:
	# 		    	line.write({'state':'completed'})
	# 		    	for row in line.partner_valuation_ids:
	# 					row.write({'state':'completed'})
	#===========================================================================
						

	
	def unlink(self):
		'''Ноорог төлөвтэй үнэлгээг устгах боломжтой'''
		for order in self:
			if order.tender_valuation_id.state != 'draft':
				raise UserError(_(u'Та зөвхөн ноорог үнэлгээг устгах боломжтой !'))
		return super(TenderValuationEmployeeValuation, self).unlink()
	
"""Харилцагчийн нийт үнэлэмжийн хувьд үнэлсэн байдал нэг үнэлэгчийн үзүүлэлт"""
class TenderValuationEmployeePartner(models.Model):
	_name = 'tender.valuation.employee.partner'
	_description = "Tender Valuation Employee Partner"
	_order = "create_date desc"
	_inherit = ['mail.thread', 'mail.activity.mixin']
	
	
	def _get_avg_value(self):
		'''Дундаж оноог тооцоолно'''
		for this in self:
			lenth=len(this.line_ids.ids)
			this.avg_value = 0
			if lenth:
				this.avg_value = sum([val.rate_value for val in this.line_ids])/len(this.line_ids.ids)
							   
	
	def _get_total_value(self):
		'''Нийт оноог тооцоолно'''
		self.total_value = sum([val.rate_value for val in self.line_ids])	

	tender_id 						= fields.Many2one('tender.tender', string='Tender', tracking=True, ondelete="restrict")
	tender_valuation_id 			= fields.Many2one('tender.valuation', 'Tender Valuation', ondelete="cascade", tracking=True)
	employee_valuation_id			= fields.Many2one('tender.valuation.employee.valuation','Tender Valuation Employee', ondelete="cascade", tracking=True)
	employee_id 					= fields.Many2one('hr.employee','Rate of Employee', tracking=True)
	tender_valuation_partner_id 	= fields.Many2one('tender.valuation.partner','Tender Valuation Partner', ondelete="cascade", tracking=True)
	partner_id 						= fields.Many2one('res.partner', 'Participants Of Tender', related="tender_valuation_partner_id.partner_id", store=True, tracking=True)
	total_value						= fields.Float('Total Value', compute=_get_total_value)
	avg_value  						= fields.Float('Average Value', compute=_get_avg_value)
	line_ids						= fields.One2many('tender.valuation.rate.line', 'employee_partner_id', 'Valuation line')
	comment 						= fields.Text(string='Content', tracking=True)
	state							= fields.Selection(STATE_SELECTION, string='State', readonly=True, default='draft', tracking=True)

	
	def unlink(self):
		'''Ноорог төлөвтэй үнэлгээг устгана'''
		for order in self:
			if order.tender_valuation_id.state != 'draft':
				raise UserError(_(u'Та зөвхөн ноорог үнэлгээг устгах боломжтой !'))
		return super(TenderValuationEmployeePartner, self).unlink()
	
"""Үнэлэгчийн нэг бүрчлэн өгч байгаа оноо: Хамгийн дэлгэрэнгүй оноо. Тайланд ашиглана."""
class TenderValuationRateLine(models.Model):
	_name = 'tender.valuation.rate.line'
	_description = "Tender Valuation Rate Line"
	_order = "create_date desc"
	_inherit = ['mail.thread', 'mail.activity.mixin']
	
	
	
	@api.depends('max_value')
	def _get_condition(self):
		'''Боломжит дээд оноог шалгана'''
		self.condition = str(self.max_value) + ' => '
		
	tender_id 							= fields.Many2one('tender.tender', string='Tender', tracking=True, ondelete="restrict")
	tender_valuation_id			 		= fields.Many2one('tender.valuation','Tender Valuation', ondelete="cascade", tracking=True)
	tender_valuation_partner_id 		= fields.Many2one('tender.valuation.partner','Tender Valuation Partner', ondelete="cascade", tracking=True)
	partner_id 							= fields.Many2one('res.partner','Participants Of Tender',related="tender_valuation_partner_id.partner_id", store=True, tracking=True)
	employee_valuation_id				= fields.Many2one('tender.valuation.employee.valuation', string='Tender Valuation Employee', ondelete="cascade", tracking=True)
	employee_partner_id 				= fields.Many2one('tender.valuation.employee.partner', string='Employee Rate Valuation', ondelete="cascade", tracking=True)
	employee_id 						= fields.Many2one('hr.employee','Rate of Employee', related="employee_valuation_id.employee_id", store=True, tracking=True)
	rate_id 							= fields.Many2one('tender.rate','Tender Rate', tracking=True)
	max_value 							= fields.Float('Max Value', tracking=True)
	rate_name 							= fields.Char('Tender Rate Old', tracking=True)
	condition							= fields.Char('Condition', compute=_get_condition, store=True, tracking=True)
	rate_value 							= fields.Float('Rate Value', tracking=True)
	comment 							= fields.Text(string='Content', tracking=True)
	state								= fields.Selection(STATE_SELECTION, string='Status', readonly=True, default='draft', tracking=True)
    
	
	def unlink(self):
		'''Ноорог үнэлгээг устгана'''
		for order in self:
			if order.state != 'draft':
				raise UserError(_(u'Та зөвхөн ноорог үнэлгээг устгах боломжтой !'))
		return super(TenderValuationRateLine, self).unlink()


class TenderParticipantsControlBudgetLine(models.Model):
	_name = 'tender.participants.control.budget.line'
	_description = "Tender Participants Budget Line"
	_order = "amount asc"

	'''Үнийн санал хяналтын төсөвтэй харьцуулах
	'''
	
	
	def _control_amount_compute(self):
		'''Тендер дээрх хяналтын төсвийн үнийн 
			дүнг хяналтын төсөв талбарт авна
		'''
		for order in self:
			order.control_budget_amount = order.tender_id.total_budget_amount
		
	
	def _diff_amount_compute(self):
		'''Оролцогчдын үнийн санал, хяналтын 
		    төсвийн зөрүү дүн тооцоолох
	    '''
		for order in self:
			order.diff_amount =  order.amount-order.control_budget_amount
			if order.control_budget_amount:
				order.diff_percent =-1*(100- order.amount*100/order.control_budget_amount)
			else:
				order.diff_percent = 0

	
	def _diff_percent_compute(self):
		for order in self:
			if order.control_budget_amount:

				order.diff_percent =-1*(100- order.amount*100/order.control_budget_amount)
			else:
				order.diff_percent = 0

	valuation_id = fields.Many2one('tender.valuation',string=u'Үнэлгээ')
	tender_id = fields.Many2one('tender.tender',string=u'Үнэлгээ')
	participant_id = fields.Many2one('tender.participants.bid',string=u'Тендерт оролцогч')
	amount = fields.Float(related='participant_id.amount_total',store=True, string=u'Үнийн санал')
	control_budget_amount = fields.Float(string=u'Хяналтын төсөв',compute=_control_amount_compute)
	diff_amount = fields.Float(string=u'Зөрүү дүн',compute=_diff_amount_compute)
	diff_percent = fields.Float(string=u"Зөрүү хувь (%)",compute=_diff_percent_compute)
	warranty = fields.Char(related='participant_id.warranty_time',string=u'Баталгаат хугацаа')
	performance_time = fields.Char(related='participant_id.execute_time',string=u'Гүйцэтгэлийн хугацаа')