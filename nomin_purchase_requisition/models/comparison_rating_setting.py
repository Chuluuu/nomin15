# -*- coding: utf-8 -*-

from openerp import api, fields, models, _
from openerp.exceptions import UserError, ValidationError

class ComparisonRatingSetting(models.Model):
	_name = 'comparison.rating.setting'
	_inherit = ['mail.thread', 'ir.needaction_mixin']
	_description = 'Comparison rating setting'

	name = fields.Char(string='Comparison rating name',track_visibility='onchange')
	is_default = fields.Boolean(string='Is default',track_visibility='onchange')
	purchase_comparison_id = fields.Many2one('purchase.comparison',string='Purchase comparison',track_visibility='onchange')

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
