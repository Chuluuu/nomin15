# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
from openerp import api, fields, models, _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _
from openerp.tools.float_utils import float_is_zero, float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools import email_split
from openerp.exceptions import UserError, AccessError
import logging
_logger = logging.getLogger(__name__)

def extract_email(email):
	""" extract the email address from a user-friendly email address """
	addresses = email_split(email)
	return addresses[0] if addresses else ''


class ResPartnerRequest(models.Model):
	_name ='res.partner.request'
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_order = "create_date DESC"
	_description = "Partner register request"

	name 		= fields.Char(string="Нэр",track_visibility='onchange')
	street		= fields.Char(string="Хаяг",track_visibility='onchange')
	website		= fields.Char(string="Вэбсайт",track_visibility='onchange')
	phone		= fields.Char(string="Утас",track_visibility='onchange')
	email 		= fields.Char(string="Имэйл",track_visibility='onchange')
	tax_number	= fields.Char(string="Татвар төлөгчийн дугаар",track_visibility='onchange')
	nomin_code 	= fields.Char(string="Номин код",track_visibility='onchange')
	register_number = fields.Char(string="Регистерийн дугаар",track_visibility='onchange')
	partner_id 	= fields.Many2one('res.partner',string="Харилцагч",track_visibility='onchange')
	state 		= fields.Selection([('draft','Ноорог'),('confirmed','Батлагдсан')],string="Төлөв",default="draft",track_visibility='onchange')
	type		= fields.Selection([('edit','Засах'),('create','Үүсгэх'),('portal','Портал')], string="Төрөл",track_visibility='onchange',default='edit')
	area_ids	= fields.Many2many(comodel_name='area.activity',string="Үйл ажиллагааны чиглэл")
	description = fields.Text(string="Тайлбар")


	@api.multi
	def action_create_partner(self):

		partner_id = self.env['res.partner'].create({'name':self.name,'street':self.street,
			'website':self.website,'phone':self.phone,'mobile':self.phone,'email':self.email,'tax_number':self.register_number,
			'registry_number':self.register_number,'nomin_code':self.register_number,'code':self.register_number,'is_company':True})
		self.write({'state':'confirmed','partner_id':partner_id.id})
		self.action_apply()			

	@api.multi
	def action_portal_partner(self):

		# partner_id = self.env['res.partner'].create({'name':self.name,'street':self.street,
		# 	'website':self.website,'phone':self.phone,'email':self.email,'tax_number':self.tax_number,
		# 	'register_number':self.register_number,'nomin_code':self.nomin_code})
		
		# self.write({'state':'confirmed','partner_id':partner_id.id})

		self.action_apply()			
		self.partner_id.write({'name':self.name,'street':self.street,
			'website':self.website,'phone':self.phone,'mobile':self.phone,'email':self.email,'tax_number':self.register_number,
			'registry_number':self.register_number,'nomin_code':self.register_number,'code':self.register_number,'is_company':True})
		# self.write({'state':'confirmed','partner_id':partner_id.id})
		self.write({'state':'confirmed'})

	@api.multi
	def action_edit_partner(self):

		request_ids= self.env['res.partner.request'].sudo().search([('create_date','<',self.create_date),('register_number','=',self.register_number),('id','!=',self.id),('state','=','draft')],order="create_date desc" )
		if request_ids:
			create_date = datetime.strptime(request_ids[0].create_date, '%Y-%m-%d %H:%M:%S')  + timedelta(hours=8)
			raise UserError(_('%s ID-тай хүсэлт %s өдөр үүссэн байна.Үүсгэсэн өдрийн дагуу батална уу')%(request_ids[0].id,create_date))
		values ={}
		if self.street:
			values['street']=self.street
		if self.description:
			values['description'] = self.description
		if self.phone:
			values['phone']=self.phone
			values['mobile']=self.phone
		if self.email:
			values['email'] = self.email
		if self.name:
			values['name'] = self.name

		
		self.partner_id.write(values)
		self.write({'state':'confirmed'})

	@api.multi
	def action_apply(self):
		
		self.env['res.partner'].check_access_rights('write')

		user_id = False
		user_id = self.env['res.users'].sudo().search([('partner_id','=',self.partner_id.id)])

		if not user_id:
			user_id = self.sudo()._create_user()
		else:			
			user_id = user_id[0]

		user_id.partner_id.signup_prepare()

		self._send_email(user_id)
		# user_id.write({'groups_id': [(6,0, portal.id)]})
        


	@api.multi   
	def _create_user(self):
		res_users = self.env['res.users']

		create_context = dict(self._context or {}, noshortcut=True, no_reset_password=True)       # to prevent shortcut creation
		portal_id = self.env['res.groups'].sudo().search([('is_portal', '=', True)])
		values = {
		'company_id': self.partner_id.company_id.id,
		'company_ids': [(6, 0, [self.partner_id.company_id.id])],
		'email': extract_email(self.email),
		'login': extract_email(self.email),
		'partner_id': self.partner_id.id,
		'groups_id': [(6, 0, [portal_id.id])],
		}
		return res_users.create(values)


	def _send_email(self,user_id ):
		res_partner = self.pool['res.partner']
		this_user = self.env['res.users'].sudo().browse(self._uid)
		if not this_user.email:
			raise UserError(_('You must have an email address in your User Preferences to send emails.'))
		user = user_id
		context = dict(self._context or {}, lang=user.lang)
		ctx_portal_url = dict(context, signup_force_type_in_url='')
		portal_url = res_partner._get_signup_url_for_action(self._cr, self._uid,
                                                            [user.partner_id.id],
                                                            context=ctx_portal_url)[user.partner_id.id]
		res_partner.signup_prepare(self._cr, self._uid, [user.partner_id.id], context=context)

		context.update({'dbname': self._cr.dbname, 'portal_url': portal_url})
		template_id = self.pool['ir.model.data'].xmlid_to_res_id(self._cr, self._uid, 'portal.mail_template_data_portal_welcome')
		portal_id = self.env['res.groups'].sudo().search([('is_portal', '=', True)])
		wizard_id = self.env['portal.wizard'].create({'portal_id':portal_id.id})

		wizard_user_id = self.env['portal.wizard.user'].create({'user_id':user.id,
			'wizard_id':wizard_id.id,'email':this_user.email,'in_portal':True,'partner_id':user.partner_id.id})
		
		if template_id:
			self.pool['mail.template'].send_mail(self._cr, self._uid, template_id, wizard_user_id.id, force_send=True, context=context)
		else:
			_logger.warning("No email template found for sending email to the portal user")
		return True

class AreasOfActivity(models.Model):
	_name='area.activity'
	_description = 'Areas of activity'
	

	name = fields.Char(string="Нэр")
	parent_id = fields.Many2one('area.activity',string="Эцэг чиглэл")
