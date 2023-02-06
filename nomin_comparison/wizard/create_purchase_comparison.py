# -*- coding: utf-8 -*-
##############################################################################
#
#    odoo, Open Source Management Solution
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
from odoo.osv import fields, osv
from odoo.tools.translate import _
from odoo import SUPERUSER_ID
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


                    
class purchase_order_comparison_wizard(osv.osv_memory):
    _name = "purchase.order.comparison.wizard"
    _description = "Purchase Order Comparison Creation Wizard"
    
 
    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        """
         Changes the view dynamically
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param context: A standard dictionary
         @return: New arch of view.
        """
        if context is None:
            context={}
        res = super(purchase_order_comparison_wizard, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        orders = self.pool.get('purchase.order').browse(cr, uid, context['active_ids'])
        #for order in orders:
        #    if order.user_id.id != uid:
        #        raise UserError(_('Warning!'), _('Please select your own orders only.'))
        for order in orders: 
            if order.purchase_type == 'direct' and len(orders) > 1:
               raise UserError(_('Warning!'),_(u'Та 1 болон Шууд төрөлтэй худалдан авалтыг харьцуулалт боломжгүй'))
            if order.comparison_id:
               raise UserError(_('Warning!'),_(u'%s дугаартай харьцуулалт үүссэн байна. Үүссэн харьцуулалтыг устгана уу.')%(order.comparison_id.name))
            if context.get('active_model','') == 'purchase.order' and len(orders) < 2:               
                # if orders[0].state not in ['draft']:
                #     raise UserError(_('Warning!'), _(u'Та зөвхөн ноорог төлөвтэй үнийн саналаас харьцуулалт үүсгэж болно'))
                if order.purchase_type not in ['direct']:                                    
                    raise UserError(_('Warning!'), _(u'1 ээс олон нийлүүлэгч харьцуулах хэрэгтэй'))
          
#         else:
#             orders = self.pool.get('purchase.order').browse(cr, uid, context['active_ids'])
#             users = []
#             deps = []
            # for order in orders:
            #     if order.state not in ['draft','sent']:
            #         raise UserError(_('Warning!'), _(u'Та зөвхөн ноорог төлөвтэй үнийн саналаас харьцуулалт үүсгэж болно'))
        return res

   
                                 
    def create_comparison(self, cr, uid, ids, context=None):
        """
             To merge similar type of purchase orders.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs
             @param context: A standard dictionary

             @return: purchase order view

        """
        mod_obj =self.pool.get('ir.model.data')
        if context is None:
            context = {}
        result = mod_obj._get_id(cr, uid, 'nomin_comparison', 'view_purchase_comparison_tree')
        id = mod_obj.read(cr, uid, result, ['res_id'])
        
        orders = self.pool.get('purchase.order').browse(cr, uid, context['active_ids'])
        
        employee_id = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',uid)])
        department_id = self.pool.get('hr.employee').browse(cr, uid, employee_id[0]).department_id.id
        
        sector_id =  self.pool.get('hr.department').get_sector(cr, uid,[], department_id)

        for order in orders:
          if order.state !='back':
            raise UserError(_('Warning!'), _(u'Та зөвхөн Үнийн санал ирсэн (RFQ back) төлөвтэй үнийн саналаас харьцуулалт үүсгэж болно'))
          for line in order.order_line:
                req_line_hist_id = self.pool.get('purchase.requisition.line.state.history').create(cr, SUPERUSER_ID, {
                                                            'state': 'draft',
                                                            'user_id': uid,
                                                            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                                                            'requisition_line_id': line.requisition_line_id.id
                                                            })
           
        comparison_id = self.pool.get('purchase.comparison').create(cr, uid, {
                                                              'date': time.strftime('%Y-%m-%d'),
                                                              # 'date': orders[0].date_order,
                                                              # 'requisition_id': orders[0].requisition_id.id,
                                                              'user_id': uid,
                                                              'department_id': department_id ,
                                                              'sector_id': sector_id,
                                                              'state': 'draft'  
                                                              })
        for order in orders:
            vals ={
              'partner_id':order.partner_id.id,
              'order_id':order.id,
              'comparison_id':comparison_id,
            }
            self.pool.get('purchase.partner.comparison').create(cr, SUPERUSER_ID, vals)
        self.pool.get('purchase.order').write(cr, uid, [order.id for order in orders], {'comparison_id': comparison_id,
                                                                                        'state': 'comparison_created'})
        
        return {
            'domain': "[('id','in', [" + str(comparison_id) + "])]",
            'name': _('Purchase Comparison'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.comparison',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'search_view_id': id['res_id']
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: