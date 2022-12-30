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
from openerp import fields, osv
from openerp import api
from openerp.tools.translate import _
from openerp import models,  api, _
from datetime import timedelta
from datetime import datetime, date
from openerp.exceptions import UserError, AccessError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

class stock_picking_seperate(models.TransientModel):
	_name = 'stock.picking.requisition.line'

	requisition_line_id = fields.Many2one('purchase.requisition.line',string='Requisition line') #Шаардахын мөр
	line_id = fields.Many2one('stock.picking.seperate.line',string='Line number') #Мөрийн дугаар
	product_qty = fields.Float(string='Qty') #Тоо хэмжээ
	receive_qty = fields.Float(string='Receive qty') #Хүлээлгэн өгөх тоо хэмжээ

class stock_picking_seperate(models.TransientModel):
	_name = 'stock.picking.seperate.line'

	requisition_id = fields.Many2one('purchase.requisition',string='Requisition number') #Шаардахын дугаар
	requisition_line_ids = fields.One2many('stock.picking.requisition.line','line_id',string='Requisition line') #Шаардахын мөрүүд
	wizard_id  = fields.Many2one('stock.picking.seperate',string='Wizard') #Шаардахаар хүлээлгэн өгөх

class stock_picking_seperate(models.TransientModel):
	_name = 'stock.picking.seperate'

	requisition_ids = fields.One2many('stock.picking.seperate.line','wizard_id',string='Requisition line') #Шаардахын мөрүүд

	@api.model
	def default_get(self, fields):
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
		result2 = []

		if self._context is None:
			self._context = {}

		res = super(stock_picking_seperate, self).default_get(fields)



		record_id = self._context and self._context.get('active_id', False) or False

		uom_obj = self.env['product.uom']
		pick_obj = self.env['stock.picking']
		pick = pick_obj.browse(record_id)

		requisition_ids = []
		if pick:
			if pick.state != 'done':
				raise UserError(_(u"Та зөвхөн дууссан төлөвтэй агуулахын үйл ажиллагаа дээр шаардахын бараа хүлээлгэн өгнө"))


		pr_line = []
		if not pick.is_direct:
			for move in pick.move_lines:

				for line in move.purchase_line_id.purchase_line_order_ids:
					
					if line.requisition_line_id.requisition_id.id not in requisition_ids:
						requisition_ids.append(line.requisition_line_id.requisition_id.id)
					pr_line.append({'parent_id':line.requisition_line_id.requisition_id.id, 'requisition_line_id': line.requisition_line_id.id,'product_qty':line.requisition_line_id.product_qty})
						
					
			for line in requisition_ids:
				result2=[]
				for rline in pr_line:
					if rline['parent_id'] == line:
						result2.append((0, 0, {'requisition_line_id': rline['requisition_line_id'],'product_qty':rline['product_qty']}))
				result1.append((0, 0, {'requisition_id': line,'requisition_line_ids':result2}))

			if result1:
				res.update({'requisition_ids': result1})
			else:
				raise UserError(_(u"Та зөвхөн шаардахын бараа хүлээлгэн өгнө"))
		else:
			for move in pick.move_lines:

				
					if move.requisition_line_id.requisition_id.id not in requisition_ids:
						requisition_ids.append(move.requisition_line_id.requisition_id.id)
					pr_line.append({'parent_id':move.requisition_line_id.requisition_id.id, 'requisition_line_id': move.requisition_line_id.id,'product_qty':move.requisition_line_id.product_qty})
						
					
			for line in requisition_ids:
				result2=[]
				for rline in pr_line:
					if rline['parent_id'] == line:
						result2.append((0, 0, {'requisition_line_id': rline['requisition_line_id'],'product_qty':rline['product_qty']}))
				result1.append((0, 0, {'requisition_id': line,'requisition_line_ids':result2}))

			if result1:
				res.update({'requisition_ids': result1})
			else:
				raise UserError(_(u"Та зөвхөн шаардахын бараа хүлээлгэн өгнө"))
		return res
	


	def create_seperate_stock(self,cr, uid, ids,context=None):
		if context is None:
			context = {}
		record_id = context and context.get('active_id', False) or False

		move_obj = self.pool.get('stock.move')
		pick_obj = self.pool.get('stock.picking')
		uom_obj = self.pool.get('product.uom')
		data_obj = self.pool.get('stock.picking.seperate.line')

		pick = pick_obj.browse(cr, uid, record_id)
		datas = self.browse(cr, uid, ids[0],context=context)

		returned_lines = 0
		picking_ids = []
		
		# Cancel assignment of existing chained assigned moves

		# for data in datas.requisition_ids:
		# 	for line in data.requisition_line_ids:
		# 		if not line.receive_qty:
		# 			raise UserError(_(u"хүлээлгэн өгөх тоо хэмжээ алга байна"))
		# 		if line.receive_qty > line.product_qty:
		# 			raise UserError(_(u"хүлээлгэн өгөх тоо хэмжээ шаардахын барааны тоо хэмжээгээс их байна"))
		for data in datas.requisition_ids:
			# pick_type_id = data.requisition_id.picking_type_id.return_picking_type_id and data.requisition_id.picking_type_id.return_picking_type_id.id or data.requisition_id.picking_type_id.id

			sector_obj_id = False
			record_type = context.get('order_type')



			sector_id = self.pool.get('hr.department').get_sector(cr, uid,[],pick.order_department_id.id) 
			sector_obj_id = self.pool.get('hr.department').browse(cr, uid,sector_id)
			picking_type_obj  = self.pool.get('stock.picking.type')
			picking_type_ids = picking_type_obj.search(cr, 1,[('code','=','outgoing'),('warehouse_id.department_of_id','=',sector_id)])

			picking_type_id = picking_type_obj.browse(cr, 1,picking_type_ids)[0]		

			new_picking = pick_obj.create(cr, uid, {
				'partner_id': pick.partner_id.id if not data.requisition_id.sector_id.partner_id.id else data.requisition_id.sector_id.partner_id.id,
				'picking_id':pick.id,
				'order_department_id':data.requisition_id.department_id.id,
				'requisition_id':data.requisition_id.id,
				'is_in':True,
				'is_out':True,
				# 'rfq_department_id':pick.rfq_department_id.id,
				'sector_id':pick.sector_id.id,
				'department_id':pick.department_id.id,
				# 'move_lines': [],
				# 'order_type':'to_warehouse' if pick.order_type =='from_warehouse' else 'from_warehouse',
				'picking_type_id': pick.picking_type_id.id if not picking_type_id.id else picking_type_id.id,
				'state': 'draft',
				'origin': pick.name,
				'location_id': pick.location_id.id if not picking_type_id.default_location_src_id.id else picking_type_id.default_location_src_id.id,
				'location_dest_id': pick.location_dest_id.id if not picking_type_id.default_location_dest_id.id else picking_type_id.default_location_dest_id.id,
			}, context=context)

			for line in data.requisition_line_ids:
				if new_picking:
					vals = {
			            'name': _('INV:') + (line.requisition_line_id.product_id.name or ''),
			            'product_id': line.requisition_line_id.product_id.id,
			            'product_uom': line.requisition_line_id.product_id.uom_id.id,
			            'date':datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
			            'company_id': line.requisition_line_id.company_id.id,
			            'requisition_line_id':line.requisition_line_id.id,
			           # 'inventory_id': inventory_line.inventory_id.id,
			            'state': 'draft',
			           'location_id': pick.location_id.id if not picking_type_id.default_location_src_id.id else picking_type_id.default_location_src_id.id,
						'location_dest_id': pick.location_dest_id.id if not picking_type_id.default_location_dest_id.id else picking_type_id.default_location_dest_id.id,
			            'product_uom_qty':line.product_qty,
			            'picking_id': new_picking,
			            # 'price_unit':line.price_unit,
			       #     'restrict_lot_id': inventory_line.prod_lot_id.id,
			         #   'restrict_partner_id': inventory_line.partner_id.id,
			         }
			        
			        move_id = move_obj.create(cr, uid, vals, context=context)

			picking_ids.append(new_picking)																			
			pick_obj.action_confirm(cr, uid, [new_picking], context=context)
			pick_obj.force_assign(cr, uid, [new_picking], context=context)
			
			for pick_id in picking_ids:
					self.pool.get('stock.picking.out.line').create(cr, uid,{'picking_id':record_id,'out_picking_id':pick_id})

		mod_obj =self.pool.get('ir.model.data')
		pick_obj.write(cr, uid, record_id, {'is_out':True},context=context)
		result = mod_obj._get_id(cr, uid, 'stock', 'vpicktree')
		id = mod_obj.read(cr, uid, result, ['res_id'])

		return {
		# 'domain': "[('id','in', [" + ','.join(str(order) for order in order_ids) + "])]",
		'domain': "[('id','in', [%s])]" % ','.join([str(p) for p in picking_ids]),
		'name': _(u'Хүргэх захиалгууд'),
		'view_type': 'form',
		'view_mode': 'tree,form',
		'res_model': 'stock.picking',
		'view_id': False,
		'type': 'ir.actions.act_window',
		'search_view_id': id['res_id']
		}
