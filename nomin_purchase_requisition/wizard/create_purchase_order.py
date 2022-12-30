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


class creat_stock_picking(models.TransientModel):
    _name = "create.stock.picking"
    _description = "Purchase Order Creation Wizard"


    @api.multi
    def create_stock_picking(self):

        active_ids = self.env.context.get('active_ids', [])
        for line in self.env['purchase.requisition.line'].browse(active_ids[0]):
          employee_id = self.env['hr.employee'].sudo().search([('user_id','=',self._uid)])
        purchase_order = self.env['purchase.order']
        picking_obj = self.env['stock.picking']
        picking_type_obj = self.env['stock.picking.type']
        sector_id = self.env['hr.department'].get_sector(self.env.user.department_id.id)


        purchase_order_line = self.env['purchase.order.line']
        res_partner = self.env['res.partner']
        
        partner = self.env['hr.department'].search([('id','=',sector_id)]).partner_id
        fiscal_position_id = self.env['account.fiscal.position']
        return_picking = self.env['stock.return.picking']
        company_id = employee_id.department_id.company_id.id
        sector_id = self.env['hr.department'].get_sector(self.env.user.department_id.id)
        for dep in self.env['hr.department'].browse(sector_id):
            department_name = dep.name

        picking_type_ids = picking_type_obj.search([('code','=','outgoing'),('warehouse_id.department_of_id','=',sector_id)])
        picking_type_ids = picking_type_ids[0]
        if not picking_type_ids:
             raise osv.except_osv(_('Warning !'), _(u"%s компани дээр %s салбар агуулах үүсгэнэ үү!",)%(company_name,department_name))
        
        if not  picking_type_ids.default_location_dest_id.id:
                  raise osv.except_osv(_('Warning !'), _(u"%s агуулахын %s бэлтгэх төрөл дээр анхны эх хүргэх байрлал алга байна!",)%(picking_type_ids.warehouse_id.name,picking_type_ids.name))
        for line in self.env['purchase.requisition.line'].sudo().browse(active_ids[0]):
          
            line_values = {
                        'origin': line.requisition_id.name,
                        'date_order':line.requisition_id.ordering_date if line.requisition_id.ordering_date else time.strftime('%Y-%m-%d %H:%M:%S'),
                        'partner_id': partner.id,
                        'is_direct':True,
                        'is_in':True,
                        'is_out':True,
                        # 'rfq_department_id':line.requisition_id.department_id.id,
                        'order_department_id':line.requisition_id.department_id.id,
                        'location_id':picking_type_ids.default_location_dest_id.id,
                        'location_dest_id':picking_type_ids.default_location_dest_id.id,
                        'picking_type_id': picking_type_ids.id,
                        'warehouse_id':picking_type_ids.warehouse_id.id ,
                        'state':  'assigned',
                        }
        department_ids = []
        requisition_ids = []
        for line in self.env['purchase.requisition.line'].browse(active_ids):
            if line.buyer.id !=self._uid:
                raise osv.except_osv(_(u'Анхааруулга!'), _(u'Та зөвхөн өөрт хуваариласан шаардахын мөрөөр шууд хүргэх захиалга үүсгэх боломжтой'))
            if line.state not in ['assigned']:
                raise osv.except_osv(_(u'Анхааруулга!'), _(u'Та зөвхөн хуваарилагдсан шаардахын мөрөөр шууд хүргэх захиалга үүсгэх боломжтой'))
            if line.requisition_id.id not in requisition_ids:
                requisition_ids.append(line.requisition_id.id)
            if line.sector_id.id not in department_ids:
                department_ids.append(line.sector_id.id)
        
        if len(requisition_ids)>1:
            raise osv.except_osv(_(u'Анхааруулга!'), _(u'Та зөвхөн нэг шаардахын дугаартай барааг агуулахаас гаргах боломжтой'))
        if len(department_ids)>1:
            raise osv.except_osv(_(u'Анхааруулга!'), _(u'Та зөвхөн нэг шаардахын дугаартай барааг агуулахаас гаргах боломжтой'))




        picking_id = picking_obj.create(line_values)
        move_ids = []
        for line in self.env['purchase.requisition.line'].browse(active_ids):
            template = {
                'name': line.product_desc or '',

                'requisition_line_id':line.id or False,
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id.id,
                'product_uom_qty':line.allowed_qty,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'date_expected': time.strftime('%Y-%m-%d %H:%M:%S'),
                'location_id': partner.property_stock_supplier.id,
                'location_dest_id': picking_type_ids.default_location_dest_id.id,
                'picking_id': picking_id.id,
                'partner_id': partner.id,
                'move_dest_id': False,
                'state': 'draft',
                'location_id':picking_type_ids.default_location_dest_id.id,
                # 'purchase_line_id': line.id,
                'company_id': line.company_id.id,
                'price_unit': line.product_price,
                'picking_type_id': picking_type_ids.id,
                # 'group_id': line.order_id.group_id.id,
                'procurement_id': False,
                # 'origin': line.order_id.name,
                'route_ids': picking_type_ids.warehouse_id and [(6, 0, [x.id for x in picking_type_ids.warehouse_id.route_ids])] or [],
                'warehouse_id':picking_type_ids.warehouse_id.id,
            }
            move_ids.append(self.env['stock.move'].create(template))

        # move_ids.force_assign()    
        # for line in self.env['purchase.requisition.line'].browse(active_ids):
        #     line.write({'':''})
        picking_id.action_confirm()
        picking_id.force_assign()
        for line in self.env['purchase.requisition.line'].browse(active_ids):
            line.write({'state':'ready'})
        return {
                'res_id': picking_id.id,
                'name': _('New'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'stock.picking',
                'view_id': False,
                'views':[(False,'form')],
                'type': 'ir.actions.act_window',
            }

class purchase_order_wizard(osv.osv_memory):
    _name = "purchase.order.wizard"
    _description = "Purchase Order Creation Wizard"

    _columns = {
        'partners_ids' : fields.one2many('purchase.order.wizard.line','wizard_id','Supplier Lines'),
    }

    
    def make_purchase_order(self, cr, uid, ids, data, context=None):
        """
        Create New RFQ for Supplier
        """
        picking_obj = self.pool.get('stock.picking.type')
        employee_ids = self.pool.get('hr.employee').search(cr, uid,[('user_id','=',uid)])
        company_id = False
        company_name = False
        department_id = False
        department_name = False
        if employee_ids:
            employee = self.pool.get('hr.employee').browse(cr, uid, employee_ids)[0]
            company_id = employee.department_id.company_id.id
            company_name = employee.department_id.company_id.name
            department_id = employee.department_id.id
         
        sector_id = self.pool.get('hr.department').get_sector(cr, uid,[],department_id) 
        for dep in self.pool.get('hr.department').browse(cr, 1, sector_id):
            department_name = dep.name

        picking_ids = picking_obj.search(cr, 1, [('code','=','incoming'),('warehouse_id.department_of_id','=',sector_id)])
        if not picking_ids:
             raise osv.except_osv(_('Warning !'), _(u"%s компани дээр %s салбар агуулах үүсгэнэ үү!",)%(company_name,department_name))

        picking_id = picking_obj.browse(cr, uid, picking_ids[0])

        if context is None:
            context = {}
       
        purchase_order = self.pool.get('purchase.order')
        purchase_order_line = self.pool.get('purchase.order.line')
        res_partner = self.pool.get('res.partner')
        fiscal_position_id = self.pool.get('account.fiscal.position')
        res = []
        active_ids = context and context.get('active_ids', [])
        line_ids=self.pool.get('purchase.requisition.line').browse(cr,uid,active_ids,context=None)
        requisition_ids = []
        department_ids = []
        for line in line_ids:
            
            if line.buyer.id !=uid:
                raise osv.except_osv(_(u'Анхааруулга!'), _(u'Та зөвхөн өөрт хуваариласан шаардахын мөрөөр үнийн санал үүсгэх боломжтой'))
            if line.state not in ['assigned','rfq_created']:
                raise osv.except_osv(_(u'Анхааруулга!'), _(u'Та зөвхөн хуваариласан төлөвтэй шаардахын мөрөөр үнийн санал үүсгэх боломжтой'))
            if line.requisition_id.id not in requisition_ids:
                requisition_ids.append(line.requisition_id.id)
            if line.sector_id.id not in department_ids:
                department_ids.append(line.sector_id.id)
        
        # if len(requisition_ids)>1:
        #     raise osv.except_osv(_(u'Анхааруулга!'), _('Cant perform this action. You can choose products from only one requisition'))
        # if len(department_ids)>1:
        #     raise osv.except_osv(_(u'Анхааруулга!'), _(u'Та зөвхөн нэг салбарын барааг үүсгэх боломжтой'))
        requisition = self.pool.get('purchase.requisition').browse(cr,uid,requisition_ids)
        names ="" 
        for req in requisition :
            names = names +"/ "+ req.name 
        requisition = requisition[0]
#         if requisition.warehouse_id.wh_input_stock_loc_id:
#             # print "\n\nIDID", requisition.warehouse_id.lot_input_id.id
#             location_id = requisition.warehouse_id.wh_input_stock_loc_id.id
        context.update({'mail_create_nolog': True})
        order_line_id = False
        for partner in data.partners_ids:
              purchase_id = purchase_order.create(cr, uid, {
                        'origin': names,
                        'company_id': requisition.company_id.id,
                        'date_order':requisition.ordering_date if requisition.ordering_date else time.strftime('%Y-%m-%d %H:%M:%S'),
                        'partner_id': partner.partner_id.id,
#                         'location_id': requisition.procurement_id and requisition.procurement_id.location_id.id or requisition.picking_type_id.default_location_dest_id.id,
                       'purchase_type': 'direct' if len(data.partners_ids.ids) == 1 else 'compare',
                        'user_id': uid,
                        'fiscal_position_id': partner.partner_id.property_account_position_id and partner.partner_id.property_account_position_id.id or False,
                        
                        'rfq_department_id':requisition.department_id.id,
#                         'pricelist_id': partner.partner_id.property_product_pricelist_purchase.id if  partner.partner_id.property_product_pricelist_purchase else False,
                        'notes': requisition.description,
                        'picking_type_id': picking_id.id,
                        # 'requisition_id':requisition.id,
                        'invoice_method':'picking',
                        'warehouse_id':picking_id.warehouse_id.id ,
                        'state':  'draft',
                        })

              purchase_order.message_post(cr, uid, [purchase_id], body=_("RFQ created"), context=context)

              res.append( purchase_id)
              product_ids = []
              
                    
              for line in line_ids:
                quantity = 0
                vals = {}
                for line1 in line_ids:
                    if line1.product_id.id == line.product_id.id:
                                             
                            quantity = quantity+line1.allowed_qty
                            product = line.product_id
                            taxes_ids = product.supplier_taxes_id
                            taxes = fiscal_position_id.map_tax(cr, uid, partner.partner_id.property_account_position_id, taxes_ids)
                
                            vals = {
                                                         'order_id': purchase_id,
                                                         'name': product.id,

                                                         # 'requisition_line_id': line.id,
                                                         'product_qty': quantity,
                                                         'product_id': product.id,
                                                         'product_uom': line.product_id.uom_id.id,
                                                         'market_price': line.product_price,
                                                          'price_unit': 0.0,
                                                         # 'price_unit_mnt': line.market_price,
                                                         'date_planned': time.strftime('%Y-%m-%d'),
                                    }
                            
                if line.product_id.id not in product_ids:  
                    product_ids.append(line.product_id.id)                         
                    order_line_id = purchase_order_line.create(cr, uid, vals, context=context)
                
                self.pool.get('purchase.requisition.line.order.line').create(cr, 1, {'order_line_id':order_line_id,'requisition_line_id':line.id}, context=context)
            
        return res
    
    def add_state_history(self, cr, uid, ids, line, state):
        new_state_id = self.pool.get('purchase.requisition.line.state.history').create(cr, uid, {
                                                                'requisition_line_id': line.id,
                                                                'user_id': uid,
                                                                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                                                                'state': state
                                                                })
    def create_order(self, cr, uid, ids, context=None):
        active_ids = context and context.get('active_ids', [])
        data =  self.browse(cr, uid, ids, context=context)[0]
        if not  data.partners_ids:
            raise osv.except_osv(_('Warning!'), _('Please select supplier'))
        assert data.partners_ids, 'Supplier should be specified'
        dep_ids = []
        line_obj = self.pool.get('purchase.requisition.line')
        if active_ids:
            lines = line_obj.browse(cr, uid, active_ids)
            for line in lines:
                if line.state =='draft':
                    raise osv.except_osv(_(u'Анхааруулга!'), _(u'Үнийн санал үүсгэж болохгүй'))    
                dep_ids.append(line.department_id.id)
                # line_obj.write(cr, uid, line.id,{
                #                                'state': 'rfq_created',
                #                                })



            # if self.has_direct_quotation(cr, uid, ids, lines):
            #     pass

       

        deps = []
    

        order_ids = self.make_purchase_order(cr, uid, active_ids, data, context=context)
        line_ids=self.pool.get('purchase.requisition.line').browse(cr,uid,active_ids,context=None)
        for line in line_ids:
                for order in order_ids:
                    self.pool.get('purchase.requisition.line.state.history').create(cr, uid, {
                                                                'requisition_line_id': line.id,
                                                                'user_id': uid, 
                                                                'order_id':order,
                                                                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                                                                'state': 'rfq_created'
                                                                })
                line_obj.write(cr, uid, line.id,{
                                               'state': 'rfq_created',
                                               })        
            
        product_qty_wizard = line.product_qty
#         print 'product_qty_wizard:', product_qty_wizard
        
        # self.add_state_history(cr, uid, ids, line, 'order_draft')
        # self.write(cr, uid, active_ids, {'state':'quotation_created'} ,context=None)
      
        mod_obj =self.pool.get('ir.model.data')
        if context is None:
            context = {}
        result = mod_obj._get_id(cr, uid, 'purchase', 'purchase_order_tree')
        id = mod_obj.read(cr, uid, result, ['res_id'])
        
        return {
           # 'domain': "[('id','in', [" + ','.join(str(order) for order in order_ids) + "])]",
               'domain': "[('id','in', [%s])]" % ','.join([str(p) for p in order_ids]),
            'name': _('Purchase Order'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'search_view_id': id['res_id']
        }


class create_purchase_order_wizard_line(osv.osv_memory):
    _name = "purchase.order.wizard.line"
    _description = "Create  Quotation Wizard"
    _columns = {
     
        'wizard_id' : fields.many2one('purchase.order.wizard','Wizard'),
        'order_id' : fields.many2one('create.purchase.order.wizard','Wizard'),
        'partner_id':fields.many2one('res.partner','Partner',required=True,domain=[('supplier', '=', True)],)
#         'line_ids' : fields.one2many('purchase.requisition.line','po_create_wizard_id','Products to Purchase'),
    }
create_purchase_order_wizard_line()


class create_purchase_order_wizard(osv.osv_memory):
    _name ='create.purchase.order.wizard'

    _columns= {
        'partner_id': fields.many2one('res.partner','Partner',domain=[('supplier', '=', True)]),
        'partner_ids' : fields.one2many('purchase.order.wizard.line','order_id','Supplier Lines'),
    }

    # def default_get(self, cr, uid, fields, context=None):
    #     result = []
    #     if context is None:
    #         context = {}
    #     res = super(get_rating, self).default_get(cr, uid, fields, context=context)    
    #     active_id = context and context.get('active_id', False) or False
    #     perform_obj = self.pool.get('contract.performance')
    #     perform = perform_obj.browse(cr, uid, active_id)
        
    #     if perform:
    #         for rate in perform.rating_line:
    #             result.append((0,0, {'rate_id':rate.indicator_id.id,'percent':0,'rating_id':rate.id}))
    #     res.update({'line_id': result})
    #     return res

    @api.multi
    def create_purchase_order(self):
        active_id = self._context and self._context.get('active_id', False) or False
        requisition = self.env['purchase.requisition'].search([('id','=',active_id)])
        fiscal_position_id = self.env['account.fiscal.position']
        order_ids = []
        for partner in self.partner_ids:    
            vals= {
                        'origin': requisition.name,
                        'company_id': requisition.company_id.id,
                        'date_order':requisition.ordering_date if requisition.ordering_date else time.strftime('%Y-%m-%d %H:%M:%S'),
                        'partner_id': partner.partner_id.id,
                        'partner_ref':partner.partner_id.nomin_code,
                        'rfq_department_id':requisition.department_id.id,
                        # 'sector_id':requisition.sector_id.id,
                        'purchase_type': 'direct' if len(self.partner_ids.ids) <= 1 else 'compare',
    #                         'location_id': requisition.procurement_id and requisition.procurement_id.location_id.id or requisition.picking_type_id.default_location_dest_id.id,
            
                        # 'user_id':self._uid,
                        'fiscal_position_id': partner.partner_id.property_account_position_id and partner.partner_id.property_account_position_id.id or False,
                        
                        # 'department_id':requisition.department_id.id,
                        'notes': requisition.description,
                        'picking_type_id': requisition.picking_type_id.id,
                        'requisition_id':requisition.id,
                        'other_amount':requisition.other_amount,
                        'carriage_amount':requisition.carriage_amount,
                        'postage_amount':requisition.postage_amount,
                        'equipment_amount':requisition.equipment_amount,
                        'invoice_method':'picking',
                        'warehouse_id':requisition.warehouse_id.id ,
                        'state':  'draft',
            }
            order_id = self.env['purchase.order'].create(vals)
            users = []
            order_ids.append(order_id.id)
            for line in requisition.line_ids:
                if line.buyer :
                    users.append(line.buyer.id)
                product = line.product_id
                taxes_ids = product.supplier_taxes_id
                taxes = fiscal_position_id.map_tax(taxes_ids)
        
                    
                values = {
                                                         'order_id': order_id.id,
                                                         'name': product.id,
                                                         'requisition_line_id': line.id,
                                                         'product_qty': line.product_qty,
                                                         'product_id': product.id,
                                                         'product_uom': line.product_id.uom_id.id,
                                                         'price_unit': 0.0,
                                                         'market_price': line.product_price,
                                                         # 'price_unit_mnt': line.market_price,
                                                         'date_planned': time.strftime('%Y-%m-%d'),
                }
                self.env['purchase.order.line'].create(values)
                values = {}
        order_id.message_subscribe_users(users)
        if requisition.priority =='urgent':
            days = 5
        else:
            days = 3
        requisition.write({'state': 'purchased', 'ordering_date':date.today()+timedelta(days=days)})
        requisition.line_ids.write({'state':'purchased'})
        # mod_obj =self.pool.get('ir.model.data')
        # if context is None:
        #     context = {}
        # result = mod_obj._get_id(cr, uid, 'purchase', 'purchase_order_tree')
        # id = mod_obj.read(cr, uid, result, ['res_id'])
        # # return {
        # #         # 'res_id':order_ids ,
        # #         'domain': "[('id','in', [" + str(order_id.values()[0]) + "])]",
        # #         'name': _('New'),
        # #         'view_type': 'form',
        # #         'view_mode': 'tree,form',
        # #         'res_model': 'purchase.order',
        # #         'view_id': False,
        # #         'views':[(False,'form')],
        # #         'type': 'ir.actions.act_window',
        # #     }