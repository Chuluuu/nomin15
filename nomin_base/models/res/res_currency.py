# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2009-2014 Monos Group (<http://monos.mn>).
#
##############################################################################

import re

from openerp import api, fields, models, _
from openerp.osv import expression
from openerp.exceptions import UserError
from openerp.tools import float_round, float_repr

class res_currency(models.Model):
    _inherit = 'res.currency'
    
    integer = fields.Char('Integer')
    divisible = fields.Char('Divisible')
    custom_order = fields.Integer('Custom order',default=1000)
