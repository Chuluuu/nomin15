# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
import odoo.addons.decimal_precision as dp
import time
from datetime import datetime, timedelta
from odoo.http import request

class PurchaseRequisitionLineWizard(models.TransientModel):
    _name = 'purchase.requisition.line.wizard'
    _description = 'purchase requisition line wizard'
    

    result = []

    @api.model
    def default_get(self, fields):
        res = super(PurchaseRequisitionLineWizard, self).default_get(fields) 
        context = dict(self._context or {})   
        active_id = context and context.get('active_id', False) or False
        perform_obj = self.env['purchase.requisition.line']
        perform = perform_obj.browse(active_id)
        supplied_quantities = []
        for line in perform.supplied_quantities:
            supplied_quantities.append((0,0,{'line_id': perform.id,
                                             'supplied_id': line.id,
                                             'partner_id': line.partner_id.id,
                                             'supplied_product_id':line.supplied_product_id.id,
                                             'supplied_product_price':line.supplied_product_price,
                                             'supplied_product_quantity':line.supplied_product_quantity,
                                             'supplied_amount':line.supplied_amount,
                                             'create_date':line.create_date,
                                             'user_id':line.user_id.id
                                            }))
        if perform.category_id:
            res.update({'category_id':perform.category_id.id})
        if perform.assign_cat:
            res.update({'assign_cat':perform.assign_cat.id})

        res.update({'requisition_line_id': perform.id,
                'requisition_id' : perform.requisition_id.id,
                'product_id' : perform.product_id.id,
                'allowed_qty' : perform.allowed_qty,
                'allowed_amount' : perform.allowed_amount,
                'product_price' : perform.product_id.sudo().cost_price,
                'product_mark' : perform.product_id.product_mark,
                'is_new_requisition' : perform.is_new_requisition,
                'supplied_quantities': supplied_quantities
                })
        
        return res
    
    
    def _compute_allowed_amount(self):
        for purchase in self:
            purchase.allowed_amount = purchase.allowed_qty * purchase.product_price

    requisition_line_id = fields.Many2one('purchase.requisition.line',string='Requisition Line')
    requisition_id = fields.Many2one('purchase.requisition',string='Requisition')
    product_id = fields.Many2one('product.product', string='Product')
    category_id = fields.Many2one('product.category',string='Product category')
    market_price = fields.Float(string='Market Price', readonly=True)
    product_price = fields.Float(string='Product unit price')
    supplied_quantities = fields.One2many('purchase.requisition.supplied.quantity.wizard', 'line_id', string='Supplied Quantities')
    partner_id = fields.Many2one('res.partner', string="Харилцагч")
    supplied_quantity = fields.Float(string='Нийлүүлсэн тоо')
    supplied_amount = fields.Float(string='Нийлүүлсэн Дүн')
    supplied_price = fields.Float(string='Нийлүүлсэн нэгж үнэ')
    deliver_product_id = fields.Many2one('product.product', string='Нийлүүлсэн барааны нэр', domain=[('product_tmpl_id.is_new','=',True),('product_tmpl_id.cost_price','>',0)])
    is_new_requisition = fields.Boolean(string='is_new_requisition')
    allowed_qty = fields.Float(string='Allowed qty') #Зөвшөөрөгдсөн тоо хэмжээ
    allowed_amount = fields.Float(string='Allowed amount', compute=_compute_allowed_amount) #Зөвшөөрөгдөх дүн
    assign_cat = fields.Many2one('assign.category',string="Хуваарилалтын ангилал",domain=[('is_active','=',True)])
    
    
    
    def action_create(self):
        count = 0.00
        supplied_obj = self.env['purchase.requisition.supplied.quantity']
        supplied_ids = []
        for line in self.supplied_quantities:
            # line.unlink()

            count+=line.supplied_product_quantity
            # supplied_quantities.append((0,0,{}))
            supplied_ids = supplied_obj.search([('line_id','=',self.requisition_line_id.id)])
            vals = {
                'line_id': self.requisition_line_id.id,
                'partner_id': line.partner_id.id,
                'supplied_product_id':line.supplied_product_id.id,
                'supplied_product_price':line.supplied_product_price,
                'supplied_product_quantity':line.supplied_product_quantity,
                'supplied_amount':line.supplied_amount,
                'user_id':line.user_id.id
            }
            if line.supplied_id.id == False:
                supplied_obj = supplied_obj.create(vals)
            if line.supplied_id in supplied_ids:
                line.supplied_id.update(vals)
                # line.supplied_id.unlink()
                # if len(supplied_ids) > len(self.supplied_quantities)
            # elif :
            # for item in supplied_ids:
            #     if line.supplied_id != item:

                    # print '\n\n item',item
            #         print 'aaaaaaaaaaaaaaa',line.supplied_id
            #     else:
            #         print '\n\n\n bbbbbbbbbbbbbbb',supplied_obj

            

    
        # return {
        #              'type': 'ir.actions.act_window',
        #              'name': _('Register Call'),
        #              'res_model': 'budget.partner.comparison',
        #              'view_mode' : 'form',
        #              'search_view_id' : view_id,
        #              'res_id':budget_partner_comparison.id,
        #              'target' : 'current',
        #              'nodestroy' : True,
        #          }
    
    def write(self, vals):
        return super(PurchaseRequisitionLineWizard, self).write(vals)
class PurchaseRequisitionSuppliedQuantityWizard(models.TransientModel):
    _name = 'purchase.requisition.supplied.quantity.wizard'
    _description = 'purchase requisition supplied quantity wizard'

    
    supplied_id = fields.Many2one('purchase.requisition.supplied.quantity', string="supplied_id")
    user_id = fields.Many2one('res.users', string="Sales person",default=lambda self: self.env.user)
    line_id = fields.Many2one('purchase.requisition.line.wizard', string="Requisition Line")
    partner_id = fields.Many2one('res.partner', string="Харилцагч")
    supplied_product_id = fields.Many2one('product.product', string='Нийлүүлсэн барааны нэр', domain=[('product_tmpl_id.is_new','=',True),('product_tmpl_id.cost_price','>',0)])
    # supplied_product_description = fields.Char(string='Нийлүүлсэн барааны тодорхойлолт')  
    supplied_product_price = fields.Float(string='Supplied Product Price')
    supplied_product_quantity = fields.Float(string='Supplied Product Quantity')
    supplied_amount = fields.Float(string='Supplied Amount')

    @api.onchange('supplied_product_id')
    def onchange_product(self):
        if self.supplied_product_id:
            self.update({'supplied_product_price':self.supplied_product_id.sudo().cost_price})
    
    @api.onchange('supplied_product_price','supplied_product_quantity')
    def onchange_supplied_amount(self):
        self.supplied_amount = self.supplied_product_quantity * self.supplied_product_price

    # @api.model
    # def create(self, vals):

    #     result = super(PurchaseRequisitionSuppliedQuantityWizard, self).create(vals)
    #     if result.supplied_product_id:
    #         result.update({'supplied_product_price':result.supplied_product_id.sudo().lst_price})
    #     if vals.get('supplied_product_quantity'):
    #         result.update({'supplied_amount':result.supplied_product_quantity * result.supplied_product_price})

        

    #     return result
        


    
    def write(self, vals):
        if vals.get('supplied_product_id'):
            vals.update({'supplied_product_price':self.supplied_product_id.sudo().cost_price})
        if vals.get('supplied_amount'):
            vals.update({'supplied_amount':vals.get('supplied_amount')})

        return super(PurchaseRequisitionSuppliedQuantityWizard, self).write(vals)    



        

    
    def unlink(self):
        for self1 in self:
            return super(PurchaseRequisitionSuppliedQuantityWizard, self1).unlink() 