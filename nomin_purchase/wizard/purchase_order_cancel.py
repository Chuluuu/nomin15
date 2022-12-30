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
import time
from openerp.osv import fields, osv
from openerp import api
from openerp.tools.translate import _
from openerp import models,  api, _
from datetime import timedelta
from datetime import datetime, date


class purchase_order_cancel(models.TransientModel):    
    _name ='purchase.order.cancel'
    _columns = {
                'note':fields.text(string='Note') #Тэмдэглэл
    }
    @api.multi
    def order_cancel(self):
        active_ids = self.env.context.get('active_ids', [])
        purchase = self.env['purchase.order'].browse(active_ids)
        print 'asdasdasdasdasdasdasdasdasdasd',purchase
        # purchase.button_cancel()
        purchase.write({'active_sequence':'1','state':'draft'})
        purchase.message_post(body= u"Буцаасан шалтгаан: "+self.note)
        return {'type': 'ir.actions.act_window_close'}