# -*- coding: utf-8 -*-

import time
from odoo.tools.translate import _
from odoo import api, fields, models, _

class wizard_rate_purchase_partner(models.TransientModel):
	_name = 'wizard.rate.purchase.partner'

	partner_id = fields.Many2one('purchase.partner.comparison',string="Partner")
	partner_partner_id = fields.Many2one('res.partner',u'Нийлүүлэгч')
	order_id = fields.Many2one('purchase.order',u'Үнийн саналын дугаар')
	line_ids = fields.One2many('wizard.rate.purchase.partner.line','wizard_id',string="Wizard line")
	info_ids = fields.One2many('wizard.description.purchase.partner.line','wizard_id',string="Info line")

	@api.model
	def default_get(self, fields):
		rec = super(wizard_rate_purchase_partner, self).default_get(fields)
		context = dict(self._context or {})
		record_id = context.get('record_id')
		partner_id = self.env['purchase.partner.comparison'].browse(record_id)

		wizard_ids =[]
		evaluation_indicator_ids = self.env['purchase.evaluation.indicators'].search([('partner_id', '=', record_id)])
		for line in evaluation_indicator_ids:
			wizard_ids.append((0,0,{ 'indicator_id':line.indicator_id.id}))
		# request_obj = self.env['ir.model'].search([('model', '=', 'purchase.comparison')])
		# for line in partner_id.comparison_id.purchase_indicator_ids:
		# 	line_id = self.env['evaluation.indicators.line'].search([('indicator_id', '=', line.indicator_id.id), ('model_id', '=', request_obj.id)])[0]
		# 	if line_id:
		# 		if line_id.evalution_method=='by_scale':
		# 			wizard_ids.append((0,0,{ 'indicator_id':line.indicator_id.id}))

		info_ids = []
		evaluation_info_ids = self.env['purchase.evaluation.infos'].search([('partner_id', '=', record_id)])
		for line in evaluation_info_ids:

			info_ids.append((0,0,{ 'indicator_id':line.indicator_id.id,'info':line.info}))

		rec.update({
			'partner_partner_id':partner_id.partner_id.id ,
			'order_id':partner_id.order_id.id,
			'partner_id':record_id,
			'line_ids':wizard_ids,
			'info_ids':info_ids,
			})
		return rec

	
	def rate(self):
		rate_obj = self.env['purchase.employee.rate']
		# self.env['purchase.evaluation.indicators']
		employee_id = self.env['hr.employee'].sudo().search([('user_id','=',self._uid)])
		for part in  self.partner_id.indicator_ids:
			for line in self.line_ids:
				if part.indicator_id.id ==line.indicator_id.id:
					rate_obj.create({'employee_id':employee_id.id,'percent':line.percent,'evaluation_id':part.id})
				
class wizard_rate_purchase_partner_line(models.TransientModel):
	_name ='wizard.rate.purchase.partner.line'

	indicator_id = fields.Many2one('evaluation.indicators',string="Evaluation indicators")
	percent = fields.Float(string='Percent')
	wizard_id = fields.Many2one('wizard.rate.purchase.partner',string="Wizard")
	@api.onchange('percent')
	def onchange_percent(self):
		if self.percent >100 or self.percent < 0:
			self.percent = 0.0


class wizard_description_purchase_partner_line(models.TransientModel):
	_name ='wizard.description.purchase.partner.line'

	indicator_id = fields.Many2one('evaluation.indicators',string="Evaluation indicators")
	info = fields.Char(string='Info')
	wizard_id = fields.Many2one('wizard.rate.purchase.partner',string="Wizard")
	