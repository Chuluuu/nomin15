# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class purchase_plan(models.Model):
	_name = 'purchase.plan'

	department_id = fields.Many2one('hr.department', string="Department",index=True)
	date = fields.Date(string="Date start")
	user_id = fields.Many2one('res.users', string="User")
	year_id = fields.Many2one('account.fiscalyear', string="Fiscal year")
	line_ids = fields.One2many('purchase.plan.line','plan_id',string="Purchase plan line")

class purchase_plan_line(models.Model):
	_name = 'purchase.plan.line'

	plan_id = fields.Many2one('purchase.plan',string='Purchase Plan',index=True)
	month_id = fields.Many2one('account.period',string="Month period",index=True)
	month_ids = fields.One2many('purchase.plan.month.line', 'line_id',string="Month line")
class purchase_plan_month_line(models.Model):
	_name = 'purchase.plan.month.line'


	line_id = fields.Many2one('purchase.plan.line',string='Month',index=True)
	product_id = fields.Many2one('product.product', string="Product", domain=[('product_tmpl_id.is_new','=',True),('product_tmpl_id.cost_price','>',0)],index=True)
	product_qty = fields.Integer(string="Product qty")
	product_uom = fields.Many2one('product.uom',string="Product uom")

