# -*- coding: utf-8 -*-
from openerp import api, fields, models, _
from openerp.exceptions import UserError
from fnmatch import translate
from openerp.osv import osv
from openerp.osv import expression
from datetime import date
from datetime import datetime, timedelta
import time
from openerp.http import request
import logging
from _abcoll import Sequence
_logger = logging.getLogger(__name__)

class purchase_requisition_line_order_line(models.Model):
	_name = 'purchase.requisition.line.order.line'

	requisition_line_id = fields.Many2one('purchase.requisition.line',string='Purchase requisition line number') #Шаардахын мөрийн дугаар
	order_line_id = fields.Many2one('purchase.order.line', string='Order line') #Захиалгын мөр

