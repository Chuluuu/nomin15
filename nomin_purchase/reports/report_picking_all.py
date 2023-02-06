# -*- coding: utf-8 -*-

from odoo.osv import osv
from odoo.tools.translate import _
from odoo.addons.nomin_base.report_helper import verbose_numeric,comma_me, convert_curr
from odoo.exceptions import UserError, AccessError
from operator import itemgetter

class ReportPickingAll(osv.AbstractModel):
    '''Зарлагын баримт
    '''
    _name = 'report.nomin_purchase.report_picking_all'

    def render_html(self, cr, uid, ids, data=None, context=None):
        if context is None:
            context = {}
        report_obj = self.pool['report']
        picking_obj = self.pool['stock.picking']
        report = report_obj._get_report_from_name(cr, uid, 'nomin_purchase.report_picking_all')
        if data and not ids:
            ids = data['ids']
        pickings = picking_obj.browse(cr, uid, ids, context=context)
        lines = {}
        total = {}
        
        for pick in pickings:
            if pick.picking_type_id.code == 'incoming':
                raise UserError((u'Анхааруулга!'), (u'Хүргэх захиалга дээрээс хэвлэх боломжтой!'))
        
        document_name = u"ЗАРЛАГЫН БАРИМТ" 
        amount_total= 0.0
        for pick in pickings:
            line = {}
            for move in pick.move_lines:
                if move.id not in line:
                    line[move.id] = {'name': move.product_id.name_get(context=context)[0][1],
                                      'id': move.product_id.id,
                                      'name': move.product_id.name or '',
                                      'code': move.product_id.code or '',
                                      'uom': move.product_uom.name,
                                      'qty': comma_me(move.product_qty),
                                      'price': comma_me(move.price_unit),
                                      'amount': comma_me(move.price_unit * move.product_qty),
                                      }
                    amount_total += move.price_unit * move.product_qty                   

                lines[pick.id] = sorted(line.values(), key=itemgetter('name'))
                
        if not lines:
            raise UserError((u'Анхааруулга!'), (u'Хүргэх захиалгийн мөр хоосон байна!'))
        
        docargs = {
            'doc_ids': ids,
            'doc_model': report.model,
            'docs': pickings,
            'lines': lines,
            'type': 'out',
            'amount_total':comma_me(amount_total),
            'document_name': document_name
        }
        return report_obj.render(cr, uid, ids, 'nomin_purchase.report_picking_all', docargs, context=context)
