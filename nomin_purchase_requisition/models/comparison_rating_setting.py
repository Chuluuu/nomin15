# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class ComparisonRatingSetting(models.Model):
	_name = 'comparison.rating.setting'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_description = 'Comparison rating setting'

	name = fields.Char(string='Comparison rating name',tracking=True)
	is_default = fields.Boolean(string='Is default',tracking=True)
	purchase_comparison_id = fields.Many2one('purchase.comparison',string='Purchase comparison',tracking=True)

class InheritPurchaseComparison(models.Model):
	_inherit = 'purchase.comparison'


	purchase_rate_indicator_ids = fields.One2many('purchase.comparison.indicators', 'comparison_id', string="Purchase rate")


class PurchaseComparisonIndicators(models.Model):
	_name = 'purchase.comparison.indicators'

	comparison_id = fields.Many2one('purchase.comparison', string='Purchase comparison')
	indicator_id = fields.Many2one('comparison.rating.setting', string='Evalution indicators')


class InheritPurchaseEvaluation(models.Model):
	_inherit = 'purchase.evaluation.indicators'

	rating_indicator_id = fields.Many2one('comparison.rating.setting', string='Rate evalution indicators')
