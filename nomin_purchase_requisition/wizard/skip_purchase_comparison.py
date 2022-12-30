# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import api, fields, models, _
from openerp.tools.translate import _
import time
import xlwt
from xlwt import *
from StringIO import StringIO
from operator import itemgetter
from openerp.exceptions import UserError, AccessError
import logging
_logger = logging.getLogger(__name__)
class SkipPurchaseComparison(models.TransientModel):
    _name = 'skip.purchase.comparison'
    _description = 'skip purchase comparison'
    
        
    @api.multi
    def action_skip_comparison(self):

        active_ids = self.env.context.get('active_ids', [])
        for line in self.env['purchase.requisition.line'].browse(active_ids):
            if line.state != 'compare':
                raise UserError(_(u'Харцуулалт хийх төлөвтэй шаардахын мөрийг харьцуулалт алгасах боломжтой.'))
            if line.allowed_amount != 0:
                comparison_config_obj = self.env['comparison.employee.config'].search([('category_ids','in',line.category_id.id),('user_id','=',line.comparison_user_id.id)])
                if line.allowed_amount < comparison_config_obj.comparison_value:
                    raise UserError(_(u'%s дугаартай шаардахын мөрийг харьцуулалтын ажилтан харьцуулалт алгасах боломжтой.'%(line.requisition_id.name)))
            
            line.write({'state': 'ready'})
