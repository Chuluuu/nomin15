# -*- coding: utf-8 -*-

from openerp.exceptions import UserError, ValidationError

from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import api, fields, models, _
from openerp.exceptions import UserError, AccessError

class PurchaseCategoryConfig(models.Model):
	_name ='purchase.category.config'
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_description = 'Purchase category config'
	
	name 	= fields.Char(string="Нэр",track_visibility='onchange')
	category_ids = fields.Many2many(comodel_name='assign.category',string="Ангилал",domain=[('is_active','=','True')])
	product_category_ids = fields.Many2many(comodel_name='product.category',string="Дотоод ангилал")
	user_id = fields.Many2one('res.users',string="Хэрэглэгч",track_visibility='onchange')
	before_accountant_id = fields.Many2one('res.users',string="Хуучин нягтлан",track_visibility='onchange')
	new_accountant_id = fields.Many2one('res.users',string="Шинэ нягтлан",track_visibility='onchange')
	team_id = fields.Many2one('team.registration',string="Team registration",track_visibility='onchange')
	sector_ids = fields.Many2many(comodel_name='hr.department',string="Салбар",domain=[('is_sector','=',True)])
	department_ids = fields.Many2many(comodel_name='hr.department',string="Хэлтэс")

	@api.multi
	def action_change(self):
		if self.new_accountant_id:
			self._cr.execute('UPDATE purchase_requisition_line set accountant_id=%s WHERE id in (select id from purchase_requisition_line where state = \'assigned\' and accountant_id = %s)'%(self.new_accountant_id.id,self.before_accountant_id.id))
	
	@api.multi
	def action_change_buyer(self):
		if self.user_id and self.department_ids:
			requisition_line = self.env['purchase.requisition.line'].search([('state','in',['sent','assigned','ready']),('assign_cat','in',self.category_ids.ids),('department_id','in',self.department_ids.ids)])
			for line in requisition_line:
				if line.buyer.id != self.user_id.id:
					line.write({
						'buyer': self.user_id.id,
					})
	
	@api.model
	def create(self, vals):
		category_config = self.env['purchase.category.config']
		if vals.get('category_ids'):
			category_ids = vals.get('category_ids')[0][2]

			if vals.get('department_ids'):
				department_ids = vals.get('department_ids')[0][2]
				exists = category_config.sudo().search([('category_ids','in',category_ids),('department_ids','in',department_ids),('id','!=',self.id)])
				if exists:
					raise UserError('Дээрх бүртгэгдсэн ангилал болон хэлтэс нь худалдан авалтын ажилтан "%s"-д бүртгэгдсэн байна.'%(exists[0].user_id.name))
			else:
				if self.department_ids:
					department_ids = self.department_ids.ids
					exists = category_config.sudo().search([('category_ids','in',category_ids),('department_ids','in',department_ids),('id','!=',self.id)])
					if exists:
						raise UserError('Дээрх бүртгэгдсэн ангилал болон хэлтэс нь худалдан авалтын ажилтан "%s"-д бүртгэгдсэн байна.'%(exists[0].user_id.name))
		
		else:
			if self.category_ids:
				category_ids.append(self.category_ids.ids)

			if vals.get('department_ids'):
				department_ids = vals.get('department_ids')[0][2]
				exists = category_config.sudo().search([('category_ids','in',category_ids),('department_ids','in',department_ids),('id','!=',self.id)])
				if exists:
					raise UserError('Дээрх бүртгэгдсэн ангилал болон хэлтэс нь худалдан авалтын ажилтан "%s"-д бүртгэгдсэн байна.'%(exists[0].user_id.name))
			else:
				if self.department_ids:
					department_ids = self.department_ids.ids
					exists = category_config.sudo().search([('category_ids','in',category_ids),('department_ids','in',department_ids),('id','!=',self.id)])
					if exists:
						raise UserError('Дээрх бүртгэгдсэн ангилал болон хэлтэс нь худалдан авалтын ажилтан "%s"-д бүртгэгдсэн байна.'%(exists[0].user_id.name))
		result = super(PurchaseCategoryConfig,self).create(vals)
		return result

	@api.multi
	def write(self, vals):
		category_config = self.env['purchase.category.config']
		if vals.get('category_ids'):
			category_ids = vals.get('category_ids')[0][2]

			if vals.get('department_ids'):
				department_ids = vals.get('department_ids')[0][2]
				exists = category_config.sudo().search([('category_ids','in',category_ids),('department_ids','in',department_ids),('id','!=',self.id)])
				if exists:
					raise UserError('Дээрх бүртгэгдсэн ангилал болон хэлтэс нь худалдан авалтын ажилтан "%s"-д бүртгэгдсэн байна.'%(exists[0].user_id.name))
			else:
				if self.department_ids:
					department_ids = self.department_ids.ids
				exists = category_config.sudo().search([('category_ids','in',category_ids),('department_ids','in',department_ids),('id','!=',self.id)])
				if exists:
					raise UserError('Дээрх бүртгэгдсэн ангилал болон хэлтэс нь худалдан авалтын ажилтан "%s"-д бүртгэгдсэн байна.'%(exists[0].user_id.name))

		else:
			category_ids = []
			if self.category_ids:
				category_ids = self.category_ids.ids

			if vals.get('department_ids'):
				department_ids = vals.get('department_ids')[0][2]
				exists = category_config.sudo().search([('category_ids','in',category_ids),('department_ids','in',department_ids),('id','!=',self.id)])
				if exists:
					raise UserError('Дээрх бүртгэгдсэн ангилал болон хэлтэс нь худалдан авалтын ажилтан "%s"-д бүртгэгдсэн байна.'%(exists[0].user_id.name))
			else:
				if self.department_ids:
					department_ids = self.department_ids.ids
				exists = category_config.sudo().search([('category_ids','in',category_ids),('department_ids','in',department_ids),('id','!=',self.id)])
				if exists:
					raise UserError('Дээрх бүртгэгдсэн ангилал болон хэлтэс нь худалдан авалтын ажилтан "%s"-д бүртгэгдсэн байна.'%(exists[0].user_id.name))

		result = super(PurchaseCategoryConfig,self).write(vals)
		return result







class AssignCategory(models.Model):
	_name="assign.category"
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_order = 'name asc'

	name = fields.Char(string="Нэр",required="1",track_visibility='onchange')
	product_type = fields.Selection([('furniture','Тавилга эд хогшил Үзүүлэлт '),#
                                         ('other_asset','Бусад хөрөнгө Үзүүлэлт'),#Бусад хөрөнг
                                         ('computer_equip','Компьютер тоног төхөөрөмж Үзүүлэлт'),#Компьютор тоног төхөөрөмж
                                         ('electronic_equip','Бусад цахилгаан хэрэгсэл Үзүүлэлт'),#Бусад цахилгаан хэрэгсэл
                                         ('paper_book','Бичиг хэрэг Үзүүлэлт'),#Бичиг хэрэг
                                         ('cleaing_material','Цэвэрлэгээний материал Үзүүлэлт'),#Цэвэрлэгээний материал
                                         ('work_clothes','Ажлын хувцас Үзүүлэлт'),#Ажлын хувцас
                                         ('other_product','Бусад бараа Үзүүлэлт'),#Бусад бараа
                                         ('construct_material','Барилгын заслын материал Үзүүлэлт'),#Барилгын заслын материал
                                         ('electric_material','Цахилгааны материал Үзүүлэлт'),#Цахилгааны материал
                                         ('plumbing_material','Сан техникийн материал Үзүүлэлт'),#Сан техникийн материал
                                         ('cooling_material','Хөргөлтийн материал Үзүүлэлт'),#Хөргөлтийн материал
                                         ('print_order','Дизайн рекламны материал Үзүүлэлт'),#Дизайн рекламны материал
                                         ('transport_equip','Transport equipment'),#Машин тоног төхөөрөмж,багаж
                                         ('vehicle','Тээврийн хэрэгсэл Үзүүлэлт'),#Тээврийн хэрэгсэл
                                         ('spare',u'Сэлбэг'),#Сэлбэг,
                                         ('service',u'Үйлчилгээ'),
                                         ('construction_work','Барилгын заслын ажил Үзүүлэлт'),#Барилгын заслын ажил
                                         ('plumbing_service','Сантехникийн ажил үйлчилгээ Үзүүлэлт'),#Сантехникийн ажил үйлчилгээ
                                         ],string=u'Үзүүлэлт')
	is_active = fields.Boolean('Is active', default=True)
	product_categ_ids = fields.Many2many(comodel_name='product.category',string='Product Category')

	@api.multi
	def write(self, vals):
		res = super(AssignCategory, self).write(vals)
		
		if vals.get('product_categ_ids'):
			exists = self.env['assign.category'].sudo().search([('product_categ_ids','in',vals.get('product_categ_ids')[0][2]),('id','!=',self.id)])
			if exists:
				raise UserError('Дээр бүртгэгдсэн барааны ангилал нь "%s" ангилалд бүртгэгдсэн байна.'%(exists[0].name))
			else:
				products = self.env['product.template'].search([('categ_id','in',vals.get('product_categ_ids')[0][2])])
				for product in products:
					product.write({'assign_categ_id':self.id})

		return res

	@api.model
	def create(self, vals):
		res = super(AssignCategory, self).create(vals)

		if vals.get('product_categ_ids'):
			exists = self.env['assign.category'].sudo().search([('product_categ_ids','in',vals.get('product_categ_ids')[0][2]),('id','!=',res.id)])
			if exists:
				raise UserError('Дээр бүртгэгдсэн барааны ангилал нь "%s" ангилалд бүртгэгдсэн байна.'%(exists[0].name))
			else:
				products = self.env['product.template'].search([('categ_id','in',vals.get('product_categ_ids')[0][2])])
				for product in products:
					product.write({'assign_categ_id':res.id})

		return res

class ComparisonEmployeeConfig(models.Model):
	_name="comparison.employee.config"
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	# _order = 'create_date desc'

	name = fields.Char(string="Нэр",required="1")
	user_id = fields.Many2one('res.users',string='User',required="1")
	comparison_value = fields.Integer(string='Comparison value')
	category_ids = fields.Many2many('assign.category',string='Category',domain=[('is_active','!=',False)])
	active = fields.Boolean(string="Active",default= True)
	product_category_ids = fields.Many2many(comodel_name='product.category',string="Дотоод ангилал")


	@api.multi
	def action_change_employee(self):
		requisition_line = self.env['purchase.requisition.line'].search([('state','in',['compare','sent_to_supply_manager']),('assign_cat','in',self.category_ids.ids)])
		for line in requisition_line:
			if line.comparison_user_id.id != self.user_id.id:
				line.write({
					'comparison_user_id': self.user_id.id,
				})
	
	@api.multi
	def write(self, vals):
		res = super(ComparisonEmployeeConfig, self).write(vals)
		
		if vals.get('category_ids'):
			exists = self.env['comparison.employee.config'].sudo().search(['|',('active','=',True),('active','=',False),('category_ids','in',vals.get('category_ids')[0][2]),('id','!=',self.id)])
			if exists:
				raise UserError('Дээр бүртгэгдсэн барааны ангилал нь "%s" нэртэй тохиргоонд бүртгэгдсэн байна.'%(exists[0].name))
		return res

	@api.model
	def create(self, vals):
		res = super(ComparisonEmployeeConfig, self).create(vals)

		if vals.get('category_ids'):
			exists = self.env['comparison.employee.config'].sudo().search([('category_ids','in',vals.get('category_ids')[0][2]),('id','!=',res.id)])
			if exists:
				raise UserError('Дээр бүртгэгдсэн барааны ангилал нь "%s" нэртэй тохиргоонд бүртгэгдсэн байна.'%(exists[0].name))
		return res

class TeamRegistration(models.Model):
        _name="team.registration"
        _inherit = ['mail.thread', 'ir.needaction_mixin']
        _order = 'name asc'

        name = fields.Char(string="Name",required="1",track_visibility='onchange')
        code = fields.Char(string="Code")


        @api.model
        def create(self, vals):
                obj = self.env['team.registration'].search([('name', '=', vals.get('name'))])
                if not obj:
                        reason_id = super(TeamRegistration, self).create(vals)
                        return reason_id
                else:
                        raise ValidationError(_(u'Ийм нэр үүссэн байна !'))

        @api.multi
        def write(self, vals):
                if vals.get("name"):
                        obj = self.env['team.registration'].search([('name', '=', vals.get('name'))])
                        if not obj:
                                reason_id = super(TeamRegistration, self).write(vals)
                                return reason_id
                        else:
                                raise ValidationError(_(u'Ийм нэр үүссэн байна !'))
                else:
                        obj = self.env['team.registration'].search([('name', '=', self.name)])
                        if not obj:
                                reason_id = super(TeamRegistration, self).write(vals)
                                return reason_id
                        else:
                                raise ValidationError(_(u'Ийм нэр үүссэн байна !'))
        @api.multi
        def unlink(self):
                '''
                        Ийм нэр ашигласан эсэхийг шалгах
                '''
                obj = self.env['purchase.category.config'].search([('team_id','=',self.id)])
                if len(obj)==0:
                        pass
                        res = super(TeamRegistration, self).unlink()
                        return res
                else: 
                        raise ValidationError(_(u'Энэхүү нэрийг ашигласан байгаа тул устгах боломжгүй!'))

