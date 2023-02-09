# -*- coding: utf-8 -*-
##############################################################################
#
#    Asterisk Technologies LLC, Enterprise Management Solution    
#    Copyright (C) 2013-2013 Asterisk Technologies LLC (<http://www.erp.mn>). All Rights Reserved
#
#    Email : unuruu25@gmail.com
#    Phone : 976 + 88005462
#
##############################################################################

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.translate import _
from odoo.tools.float_utils import float_is_zero, float_compare
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, AccessError
import time
from odoo.osv import osv
from odoo.http import request    


class stock_picking_out_line(models.Model):
    _name = 'stock.picking.out.line'
    
    picking_id = fields.Many2one('stock.picking',string=u'Хүлээн авах баримт')
    out_picking_id =fields.Many2one('stock.picking', string=u'Хүргэх захиалгууд')

class stock_picking(models.Model):
    _inherit = 'stock.picking'
    
    
    def _set_sector(self):
            if self.env.user.department:
                department_ids = self.env['hr.department'].get_sector(self.env.user.department_id.id)
                if department_ids :
                    return department_ids
                else :      
                    return self.env.user.department_id.id
            return None
    
    
    def _set_department(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id','=',self._uid)])
        if employee_id and employee_id.department_id:
            return employee_id.department_id.id
        # else:
        #     raise UserError(_('Warning!'), _('You don\'t have related department. Please contact administrator.'))
        return None
    
    sector_id = fields.Many2one('hr.department',u'Гүйцэтгэгч салбар', domain="[('is_sector','=',True)]", default=_set_sector)
    department_id = fields.Many2one('hr.department', u'Гүйцэтгэгч хэлтэс',default= _set_department)
    rfq_department_id = fields.Many2one('hr.department', u'Захиалагч хэлтэс')
    order_department_id = fields.Many2one('hr.department', u'Хүлээн авах хэлтэс',default= _set_department)
    order_type = fields.Selection([('from_warehouse','From warehouse'),('to_warehouse','To warehouse')], string=u'Төрөл', default='from_warehouse')
    picking_id = fields.Many2one('stock.picking',string=u'Агуулах үйл ажиллагаа')
    requisition_id = fields.Many2one('purchase.requisition',string=u'Шаардахын дугаар')
    out_picking_line = fields.One2many('stock.picking.out.line','picking_id',string=u'Хүргэх захиалгууд')
    is_out = fields.Boolean(string='Is out',default=False)
    is_in = fields.Boolean(string='Is in',default=False)
    is_direct = fields.Boolean(string="Direct" , default=False)
    
    def action_to_hand_over(self):
        
        sector_id = self.env['hr.department'].get_sector(self.env.user.department_id.id)     

        sector_obj_id = self.env['hr.department'].browse(sector_id)

        picking_type_obj  = self.env['stock.picking.type']
        picking_type_id = picking_type_obj.sudo().search([('code','=','incoming'),('warehouse_id.department_of_id','=',sector_id)])

        
        
        picking = self.copy({
            'partner_id': self.partner_id.id ,
            'picking_id':self.id,
            'order_department_id':self.order_department_id.id,
           # 'rfq_department_id':pick.rfq_department_id.id,
            'sector_id':self.sector_id.id,
            'department_id':self.department_id.id,
            'move_lines': [],
            'is_in':False,
            # 'order_type':'to_warehouse' if pick.order_type =='from_warehouse' else 'from_warehouse',
            'picking_type_id': picking_type_id.id,
            'state': 'draft',
            'origin': self.name,
            'location_id':picking_type_id.default_location_dest_id.id if picking_type_id.default_location_dest_id.id else False,
            # 'location_dest_id':picking_type_id.default_location_dest_id.id,
        })
        self.env['stock.picking.out.line'].create({'picking_id':self.id,'out_picking_id':picking.id})
        for move in self.move_lines:
                move.copy( {
                    # 'product_id': data_get.product_id.id,
                    # 'product_uom_qty': new_qty,
                    'picking_id': picking.id,
                    'state': 'draft',
                    'location_id': picking_type_id.default_location_dest_id.id,
                    'requisition_line_id':move.requisition_line_id.id,
                    # 'location_dest_id': picking_type_id.default_location_dest_id.id if picking_type_id.default_location_dest_id.id else False,
                    'picking_type_id': picking_type_id.id,
                    'warehouse_id': picking_type_id.warehouse_id.id,
                    # 'origin_returned_move_id': move.id,
                    'procure_method': 'make_to_stock',
                    # 'move_dest_id': move_dest_id,
                })

        picking.action_confirm()
        picking.force_assign()
        
        self.write({'is_in':False})

        # return {
        #         'res_id': picking.id,
        #         'name': _('New'),
        #         'view_mode': 'tree,form',
        #         'res_model': 'stock.picking',
        #         'view_id': False,
        #         'views':[(False,'form')],
        #         'type': 'ir.actions.act_window',
        #     }


class stock_return_picking(osv.osv_memory):
    _inherit = 'stock.return.picking'
    
    def default_get(self, cr, uid, fields, context=None):
        """
         To get default values for the object.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: List of fields for which we want default values
         @param context: A standard dictionary
         @return: A dictionary with default values for all field in ``fields``
        """
        result1 = []
        
        if context is None:
            context = {}
        if context and context.get('active_ids', False):
            if len(context.get('active_ids')) > 1:
                raise UserError(_("You may only return one picking at a time!"))
        res = super(stock_return_picking, self).default_get(cr, uid, fields, context=context)
        record_id = context and context.get('active_id', False) or False
        uom_obj = self.pool.get('product.uom')
        pick_obj = self.pool.get('stock.picking')
        pick = pick_obj.browse(cr, uid, record_id, context=context)
        quant_obj = self.pool.get("stock.quant")
        chained_move_exist = False
        if pick:
            if pick.state != 'done':
                raise UserError(_("You may only return pickings that are Done!"))

            for move in pick.move_lines:
                if move.scrapped:
                    continue
                if move.move_dest_id:
                    chained_move_exist = True
                #Sum the quants in that location that can be returned (they should have been moved by the moves that were included in the returned picking)
                qty = 0
                quant_search = quant_obj.search(cr, uid, [('history_ids', 'in', move.id), ('qty', '>', 0.0), ('location_id', 'child_of', move.location_dest_id.id)], context=context)
                for quant in quant_obj.browse(cr, uid, quant_search, context=context):
                    if not quant.reservation_id or quant.reservation_id.origin_returned_move_id.id != move.id:
                        qty += quant.qty
                qty = uom_obj._compute_qty(cr, uid, move.product_id.uom_id.id, qty, move.product_uom.id)
                result1.append((0, 0, {'product_id': move.product_id.id, 'quantity': qty, 'move_id': move.id}))
           
            if len(result1) == 0:
                raise UserError(_("No products to return (only lines in Done state and not fully returned yet can be returned)!"))
            if 'product_return_moves' in fields:
                res.update({'product_return_moves': result1})
            if 'move_dest_exists' in fields:
                res.update({'move_dest_exists': chained_move_exist})
            if 'parent_location_id' in fields and pick.location_id.usage == 'internal':
                res.update({'parent_location_id':pick.picking_type_id.warehouse_id and pick.picking_type_id.warehouse_id.view_location_id.id or pick.location_id.location_id.id})
            if 'original_location_id' in fields:
                res.update({'original_location_id': pick.location_id.id})
            
            if 'location_id' in fields:
                res.update({'location_id': pick.location_id.id})
        return res
    
    
    def _create_returns(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        record_id = context and context.get('active_id', False) or False
        move_obj = self.pool.get('stock.move')
        pick_obj = self.pool.get('stock.picking')
        uom_obj = self.pool.get('product.uom')
        data_obj = self.pool.get('stock.return.picking.line')
        pick = pick_obj.browse(cr, uid, record_id, context=context)
        data = self.read(cr, uid, ids[0], context=context)
        returned_lines = 0

        # Cancel assignment of existing chained assigned moves
        moves_to_unreserve = []
        for move in pick.move_lines:
            to_check_moves = [move.move_dest_id] if move.move_dest_id.id else []
            while to_check_moves:
                current_move = to_check_moves.pop()
                if current_move.state not in ('done', 'cancel') and current_move.reserved_quant_ids:
                    moves_to_unreserve.append(current_move.id)
                split_move_ids = move_obj.search(cr, uid, [('split_from', '=', current_move.id)], context=context)
                if split_move_ids:
                    to_check_moves += move_obj.browse(cr, uid, split_move_ids, context=context)

        if moves_to_unreserve:
            move_obj.do_unreserve(cr, uid, moves_to_unreserve, context=context)
            #break the link between moves in order to be able to fix them later if needed
            move_obj.write(cr, uid, moves_to_unreserve, {'move_orig_ids': False}, context=context)
  
        #Create new picking for returned products
        pick_type_id = pick.picking_type_id.return_picking_type_id and pick.picking_type_id.return_picking_type_id.id or pick.picking_type_id.id
        
        sector_obj_id = False
        record_type = context.get('order_type')
       

        new_picking = pick_obj.copy(cr, uid, pick.id, {
            'partner_id': pick.partner_id.id ,
           'picking_id':pick.id,
           'order_department_id':pick.order_department_id.id,
           'rfq_department_id':pick.rfq_department_id.id,
           'sector_id':pick.sector_id.id,
           'department_id':pick.department_id.id,
            'move_lines': [],
            'order_type':'to_warehouse' if pick.order_type =='from_warehouse' else 'from_warehouse',
            'picking_type_id': pick_type_id,
            'state': 'draft',
            'origin': pick.name,
            'location_id': pick.location_dest_id.id,
            'location_dest_id': data['location_id'] and data['location_id'][0] or pick.location_id.id,
        }, context=context)

        for data_get in data_obj.browse(cr, uid, data['product_return_moves'], context=context):
            move = data_get.move_id
            if not move:
                raise UserError(_("You have manually created product lines, please delete them to proceed"))
            new_qty = data_get.quantity
            if new_qty:
                # The return of a return should be linked with the original's destination move if it was not cancelled
                if move.origin_returned_move_id.move_dest_id.id and move.origin_returned_move_id.move_dest_id.state != 'cancel':
                    move_dest_id = move.origin_returned_move_id.move_dest_id.id
                else:
                    move_dest_id = False

                returned_lines += 1
                location_id = data['location_id'] and data['location_id'][0] or move.location_id.id
                move_obj.copy(cr, uid, move.id, {
                    'product_id': data_get.product_id.id,
                    'product_uom_qty': new_qty,
                    'picking_id': new_picking,
                    'state': 'draft',
                    'location_id': move.location_dest_id.id,
                    'requisition_line_id':move.requisition_line_id.id,
                    'location_dest_id': location_id,
                    'picking_type_id': pick_type_id,
                    'warehouse_id': pick.picking_type_id.warehouse_id.id,
                    'origin_returned_move_id': move.id,
                    'procure_method': 'make_to_stock',
                    'move_dest_id': move_dest_id,
                })

        if not returned_lines:
            raise UserError(_("Please specify at least one non-zero quantity."))

        pick_obj.action_confirm(cr, uid, [new_picking], context=context)
        pick_obj.action_assign(cr, uid, [new_picking], context=context)
        return new_picking, pick_type_id


    
class stock_move(models.Model):
    _inherit = 'stock.move'   
     
    requisition_line_id = fields.Many2one('purchase.requisition.line',string=u'Шаардах мөрийн дугаар')
     
     
    # @api.model
    # def create(self, vals):

        
    #     requisition_line_id = vals.get('requisition_line_id')
    #     if vals.get('state') =='draft':
    #         if requisition_line_id and 'requisition_line_id' in vals:
    #             vals.update({'requisition_line_id':False})

    #     return super(stock_move, self).create(vals)