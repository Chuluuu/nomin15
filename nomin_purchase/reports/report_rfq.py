# -*- coding: utf-8 -*-
##############################################################################
#
#    odoo, Open Source Management Solution
#    Copyright (C) 2014-Today odoo SA (<http://www.odoo.com>).
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

from odoo.osv import osv
from odoo.tools.translate import _
from odoo.addons.nomin_base.report_helper import verbose_numeric,comma_me, convert_curr
from operator import itemgetter
from odoo.exceptions import UserError, AccessError

class ReportRfq(osv.AbstractModel):
    '''Үний санал
    '''
    _name = 'report.nomin_purchase.report_rfq'

    def render_html(self, cr, uid, ids, data=None, context=None):
        if context is None:
            context = {}
        report_obj = self.pool['report']
        purchase_obj = self.pool['purchase.order']
        report = report_obj._get_report_from_name(cr, uid, 'nomin_purchase.report_rfq')
        if data and not ids:
            ids = data['ids']
        purchases = purchase_obj.browse(cr, uid, ids, context=context)
        lines = {}
        total = {}
        
#         for pur in purchases:
#             if pick.picking_type_id.code == 'incoming':
#                 raise UserError((u'Анхааруулга!'), (u'Хүргэх захиалга дээрээс хэвлэх боломжтой!'))
        
        document_name = u"ҮНИЙН САНАЛ" 
        for pur in purchases:
            line = {}
            document_name = u"ҮНИЙН САНАЛ №%s"%(pur.name) 
            for pline in pur.order_line:
                if pline.id not in line:
                    line[pline.id] = {'name': pline.product_id.name or '',
                                      'code': pline.product_id.default_code or '',
                                      'uom': pline.product_uom.name,
                                      'qty': comma_me(pline.product_qty),
                                      'purchase_date_planned':pline.purchase_date_planned,
                                      'warranty': pline.warranty or '',
                                      'desc': pline.name or '',
                                      }
                lines[pur.id] = sorted(line.values(), key=itemgetter('name'))
                
        if not lines:
            raise UserError((u'Анхааруулга!'), (u'Үнийн саналын мөр хоосон байна!'))
        
        docargs = {
            'doc_ids': ids,
            'doc_model': report.model,
            'docs': purchases,
            'lines': lines,
            'type': 'out',
            'document_name': document_name
        }
        return report_obj.render(cr, uid, ids, 'nomin_purchase.report_rfq', docargs, context=context)
