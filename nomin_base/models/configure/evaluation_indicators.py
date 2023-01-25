# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from openerp import api, fields, models, _
from openerp.exceptions import UserError


CATEG_SELECTION = [
        ('purchase','Purchase'),
        ('project','Project'),
        ('helpdesk','Helpdesk'),
        ('tender','Tender'),
        ('contract','Contract'),
    ]
class evaluation_indicators_line (models.Model):
    _name = 'evaluation.indicators.line'
    
    model_id = fields.Many2one('ir.model', string='Object', required=True, ondelete='cascade')
    indicator_id = fields.Many2one('evaluation.indicators', string='Evaluation indicators')
    is_default = fields.Boolean('Is default')
    # scale = fields.Float(string='Indicator scale')
    
class EvaluationIndicators(models.Model):
    _name = 'evaluation.indicators'
    _description = 'Evaluation Indicators'
    _table = "evaluation_indicators"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Name', required=True, size=128)
    category = fields.Selection(CATEG_SELECTION, string='Category',default='contract', )
    line_ids = fields.One2many('evaluation.indicators.line','indicator_id',string='Evaluation indicators line')
    
    
    
    