# -*- coding: utf-8 -*-

from openerp import api, fields, models, _
from openerp.exceptions import UserError, ValidationError

class PurchasePriority(models.Model):
	_name = 'purchase.priority'
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_description = 'Purchase priority'

	name = fields.Char(string='Priority name',track_visibility='onchange')
	priority_day = fields.Integer(string='Priority day',track_visibility='onchange')
	comparison_day = fields.Integer(string='Comparison day',track_visibility='onchange')

	@api.model
	def create(self, vals):
		priority = self.env['purchase.priority'].search([('name', '=', vals.get('name'),('id','!=',self.id))])
		if not priority:
			res = super(PurchasePriority, self).create(vals)
			return res
		else:
			raise ValidationError(_(u'Ийм урьтамж үүссэн байна !!!'))

	@api.multi
	def write(self, vals):

		if vals.get('name'):
			priority_name = vals.get('name')
		else:
			priority_name =self.name
		priority= self.env['purchase.priority'].search([('name','=',priority_name),('id','!=',self.id)])
		if priority:
			raise UserError(_(u'Ийм урьтамж үүссэн байна !!!!'))
		else:
			print'_____priority____'
		return super(PurchasePriority, self).write(vals)





	@api.multi
	def unlink(self):
		'''Урьтамж шаардах дээр ашигласан тохиолдолд устгах боломжгүй'''
		priority = self.env['purchase.requisition'].search([('priority_id.name','=',self.name)])
		if len(priority)==0:
			res = super(PurchasePriority, self).unlink()
			return res
		else: 
			raise ValidationError(_(u'Энэхүү урьтамж ашигласан байгаа тул устгах боломжгүй!'))