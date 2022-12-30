# -*- coding: utf-8 -*-

from openerp import api, fields, models, _
from openerp.exceptions import UserError, ValidationError

class StandartProductList(models.Model):
	_name = 'standart.product.list'
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_description = 'standart product list'

	name = fields.Char(string='Name',track_visibility='onchange',)
	standart_product_ids = fields.One2many('standart.product.line','standart_id',string='standart product line')
	state = fields.Selection([('draft','Ноорог'),('confirmed','Батлагдсан')], default='draft',track_visibility='onchange')
	product_type = fields.Selection([('standart','Стандартчилагдсан бараа'),('normalized','Нормчилогдсон бараа'),('new_set','Шинэ дэлгүүрийн багц')], string='Барааны төрөл',track_visibility='onchange')

	@api.multi
	def action_confirm(self):
		if not self.standart_product_ids:
			raise UserError(_('Бараа сонгогдоогүй байна.'))
		for line in self.standart_product_ids:
			if self.product_type == "standart":
				if line.product_product_id.is_purchase_standard:
					raise UserError(_(u"'%s' бараа давхардаж орсон байна."%(line.product_product_id.name)))
				line.product_product_id.update({'is_purchase_standard' :True})
			elif self.product_type == "normalized":
				if line.product_product_id.is_normalized:
					raise UserError(_(u"'%s' бараа давхардаж орсон байна."%(line.product_product_id.name)))
				line.product_product_id.update({'is_normalized' :True})
			elif self.product_type == "new_set":
				if line.product_product_id.is_new_set:
					raise UserError(_(u"'%s' бараа давхардаж орсон байна."%(line.product_product_id.name)))
				line.product_product_id.update({'is_new_set' :True})
		self.update({'state':'confirmed'})
    
	@api.multi
	def action_cancel(self):
		for line in self.standart_product_ids:
			if self.product_type == "standart":
				line.product_product_id.update({'is_purchase_standard' :False})
			elif self.product_type == "normalized":
				line.product_product_id.update({'is_normalized' :False})
			elif self.product_type == "new_set":
				line.product_product_id.update({'is_new_set' :False})
		self.update({'state':'draft'})

	@api.multi
	def unlink(self):
		for obj in self:
			if obj.state != 'draft':
				raise UserError(_(u'Ноорог төлөвт устгаж болно.'))
		return super(StandartProductList, self).unlink()
class StandartProductLine(models.Model):
	_name = 'standart.product.line'


	standart_id = fields.Many2one('standart.product.list', string='standart product list')
	product_product_id = fields.Many2one('product.product', string="Product" ,domain=[('product_tmpl_id.is_new','=',True),('product_tmpl_id.cost_price','>',0)] ,track_visibility='onchange')
	product_category_id = fields.Many2one('product.category', string="Product category",track_visibility='onchange')
	
	@api.onchange('product_product_id')
	def onchange_product(self):
		if self.product_product_id and self.product_product_id.product_tmpl_id.categ_id:
			self.update({'product_category_id':self.product_product_id.product_tmpl_id.categ_id})

	
	@api.model
	def create(self, vals):
		if vals.get('product_product_id'):
			product_id = self.env['product.product'].browse(vals.get('product_product_id'))
			if product_id:
				vals.update({'product_category_id':product_id.product_tmpl_id.categ_id.id})
		return super(StandartProductLine, self).create(vals)
	
	@api.multi
	def write(self, vals):
		if vals.get('product_product_id'):
			product_id = self.env['product.product'].browse(vals.get('product_product_id'))
			if product_id:
				vals.update({'product_category_id':product_id.product_tmpl_id.categ_id.id})
					
		return super(StandartProductLine, self).write(vals)