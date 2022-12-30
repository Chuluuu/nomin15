# -*- coding: utf-8 -*-

import datetime
from datetime import date, datetime, timedelta
import time
from openerp import api, fields, models, _
from openerp.exceptions import UserError, ValidationError
import random
import logging
import string 
import os
import pyqrcode

_logger = logging.getLogger(__name__)

def random_generator(size=16, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

def get_sector(self,department_id):
    if department_id:
        self.env.cr.execute("select is_sector from hr_department where id=%s"%(department_id))
        fetched = self.env.cr.fetchone()
        if fetched:
            if fetched[0] == True:
                return department_id
            else:
                self.env.cr.execute("select parent_id from hr_department where id=%s"%(department_id))
                pfetched = self.env.cr.fetchone()
                if pfetched:
                    return get_sector(self,pfetched[0])
                
class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'
    '''
        Худалдан авалтын шаардах дээр тээвэр, машин механизм, шууд ба бусад зардлууд оруулах талбарууд
    '''
    material_amount    = fields.Float(u'Материалын зардал')
    equipment_amount    = fields.Float(u'Машин механизмын зардал')
    carriage_amount     = fields.Float(u'Тээврийн зардал')
    postage_amount      = fields.Float(u'Шууд зардал')
    other_amount        = fields.Float(u'Бусад зардал')
    
class PurchaseRequisitionLine(models.Model):
    _inherit = 'purchase.requisition.line'
    '''
        Худалдан авалтын шаардахын мөр дээр материал эсвэл ажиллах хүчний зардал эсэхийг ялгах талбар
    '''
    
    c_budget_type = fields.Selection([
                                    ('material', u'Материалын'),
                                    ('labor',u'Ажиллах хүчний')
                                    ],default = 'material' ,string = u'Төсвийн төрөл')
    
class CreatePurchaseRequisition(models.Model):
    _name ='create.purchase.requisition'
    
    '''
        Худалдан авалтын шаардах үүсгэх
    '''
    
    urgent = fields.Selection([
                            ('general', u'Хэвийн'),
                            ('urgent',u'Яаралтай')
                            ],string = u'Урьтамж')
    budget_id = fields.Many2one('control.budget', index=True, string = 'Budget')
    priority_id = fields.Many2one('purchase.priority',string='Purchase priority',track_visibility='onchange')
    location = fields.Char(u'Хүлээн авах байршил', required=True)
    m_line = fields.One2many('material.budget.line','purchase_id',string = u'Материалын зардал')
    l_line = fields.One2many('labor.budget.line','purchase_id',string = u'Ажиллах хүчний зардал')
    
    equipment_create    = fields.Float(u'Машин механизм зардал',default=0.0)
    carriage_create     = fields.Float(u'Тээврийн зардал',default=0.0)
    postage_create      = fields.Float(u'Шууд зардал',default=0.0)
    other_create        = fields.Float(u'Бусад зардал',default=0.0)
    
    material_limit      = fields.Float(u'Материалын зардлын үлдэгдэл')
    labor_limit         = fields.Float(u'Ажиллах хүчний зардлын үлдэгдэл')
    equipment_limit     = fields.Float(u'Машин механизмын зардлын үлдэгдэл')
    carriage_limit      = fields.Float(u'Тээврийн зардлын үлдэгдэл')
    postage_limit       = fields.Float(u'Шууд зардлын үлдэгдэл')
    other_limit         = fields.Float(u'Бусад зардлын үлдэгдэл')
    
    # def default_get(self, cr, uid, fields, context=None):
    #     '''
    #         Хяналтын төсвийн материал болон ажиллах хүчний зардлын сонгосон мөр болон бусад зардлуудын оруулсан дүн, хяналтын төсвийг буцаана
    #     '''
    #     result = []
    #     if context is None:
    #         context = {}
    #     res = super(create_purchase_requisition, self).default_get(cr, uid, fields, context=context)    
    #     active_id = context and context.get('active_id', False) or False
    #     perform_obj = self.pool.get('control.budget')
    #     perform = perform_obj.browse(cr, uid, active_id)
    #     m_line_ids = []
    #     for line in perform.material_line_ids:
    #         if line.cost_choose == True and line.state == 'confirm':
    #             m_line_ids.append(line.id)
    #     l_line_ids = []
    #     for line in perform.labor_line_ids:
    #         if line.cost_choose == True and line.state == 'confirm':
    #             l_line_ids.append(line.id)
    #     res.update({
    #                 'budget_id' : perform.id,
    #                 'material_limit':perform.material_utilization_limit,
    #                 'labor_limit':perform.labor_utilization_limit,
    #                 'equipment_limit' : perform.equipment_utilization_limit,
    #                 'carriage_limit' : perform.carriage_utilization_limit,
    #                 'postage_limit' : perform.postage_utilization_limit,
    #                 'other_limit' : perform.other_utilization_limit,
    #                 'm_line':[(6, 0, m_line_ids)],
    #                 'l_line':[(6, 0, l_line_ids)]
    #                 })
    #     return res

    @api.model
    def default_get(self, fields):
        '''
            Хяналтын төсвийн материал болон ажиллах хүчний зардлын сонгосон мөр болон бусад зардлуудын оруулсан дүн, хяналтын төсвийг буцаана
        '''
        _logger.info(u'_______________________________________________________________________________________EEE8, %s ',fields)
        
        res = super(CreatePurchaseRequisition, self).default_get(fields) 
        context = dict(self._context or {})   
        active_id = context and context.get('active_id', False) or False
        _logger.info(u'_______________________________________________________________________________________EEE9, %s - %s ',active_id,context)
        
        perform_obj = self.env['control.budget']
        perform = perform_obj.browse(active_id)
        m_line_ids = []
        _logger.info(u'_______________________________________________________________________________________EEE1, %s ',perform)
        for line in perform.material_line_ids:
            if line.cost_choose == True and line.state == 'confirm':
                m_line_ids.append(line.id)
        l_line_ids = []
        for line in perform.labor_line_ids:
            if line.cost_choose == True and line.state == 'confirm':
                l_line_ids.append(line.id)

        _logger.info(u'_______________________________________________________________________________________EEE, %s - %s',
            perform.material_line_ids,perform.labor_line_ids)
        res.update({
                    'budget_id' : perform.id,
                    'material_limit':perform.material_utilization_limit,
                    'labor_limit':perform.labor_utilization_limit,
                    'equipment_limit' : perform.equipment_utilization_limit,
                    'carriage_limit' : perform.carriage_utilization_limit,
                    'postage_limit' : perform.postage_utilization_limit,
                    'other_limit' : perform.other_utilization_limit,
                    'm_line':[(6, 0, m_line_ids)],
                    'l_line':[(6, 0, l_line_ids)]
                    })
        return res

    @api.multi    
    def create_purchase_button(self):
        '''
            Худалдан авалтын шаардах үүсгэх
                Зардлуудын үлдэгдэл хүрж байгаа эсэхийг тооцолж үүсгэнэ
                Мөн үүссэн дүнгээр хяналтын төсвийн зардал тус бүр дээр гүйцэтгэл хөтөлнө
        '''
        budget  = self.env['control.budget'].search([('id','=', self.budget_id.id)])
        model_obj =self.env['ir.model.data']
        result = model_obj._get_id('purchase_requisition', 'view_purchase_requisition_form')
        view_id = model_obj.browse(result).res_id
        
        purchase_requisition = self.env['purchase.requisition']
        purchase_requisition_line = self.env['purchase.requisition.line']
        utilization_budget_material = self.env['utilization.budget.material']
        utilization_budget_labor =  self.env['utilization.budget.labor']
        utilization_budget_equipment = self.env['utilization.budget.equipment']
        utilization_budget_carriage =  self.env['utilization.budget.carriage']
        utilization_budget_postage = self.env['utilization.budget.postage']
        utilization_budget_other =  self.env['utilization.budget.other']
        
        emp_obj = self.env['hr.employee']
        emp = emp_obj.sudo().search([('user_id','=',budget.user_id.id)])
        config_obj = self.env['request.config'].search([('department_ids','=', emp.department_id.id),('process','=','purchase.requisition')])
        
        material_line_count = 0
        labor_line_count = 0
        
        material_product_limit = 0.0
        labor_product_limit = 0.0
        
        material_cost = 0.0
        labor_cost = 0.0
        
        amount = 0.0
        sector_id = get_sector(self,self.env.user.department_id.id) 
        warehouse_id = self.env['stock.warehouse'].sudo().search([('department_of_id','=',sector_id)])[0]
        if not config_obj:
            raise ValidationError(_(u'Урсгал тохиргоо байхгүй байна'))
        if not emp:
            raise ValidationError(_(u'Төсөвчинд холбоотой ажилтан байхгүй байна'))
        for material_line in budget.material_line_ids:
            if material_line.cost_choose == True and material_line.state == 'confirm':
                material_line_count += 1
                material_cost += material_line.material_total
                amount += material_line.material_total
                material_product_limit += material_line.price_unit * material_line.product_uom_qty
                
        if material_product_limit > self.material_limit:
            raise ValidationError(_(u'Материалын зардлын дүн хэтэрсэн байна'))
        
        for labor_line in budget.labor_line_ids:
            if labor_line.cost_choose == True and labor_line.state == 'confirm':
                labor_line_count += 1
                labor_cost += labor_line.labor_total
                amount += labor_line.labor_total
                labor_product_limit += labor_line.price_unit * labor_line.product_uom_qty
                
        if labor_product_limit > self.labor_limit:
            raise ValidationError(_(u'Ажиллах хүчний зардлын дүн хэтэрсэн байна'))
        
        if self.equipment_create > 0.0:
            if self.equipment_create <= self.equipment_limit:
                amount += self.equipment_create
            else:
                raise ValidationError(_(u'Машин механизмын зардлын дүн хэтэрсэн байна'))
            
        if self.carriage_create > 0.0:
            if self.carriage_create <= self.carriage_limit:
                amount += self.carriage_create
            else:
                raise ValidationError(_(u'Тээврийн зардлын дүн хэтэрсэн байна'))
            
        if self.postage_create > 0.0:
            if self.postage_create <= self.postage_limit:
                amount += self.postage_create
            else:
                raise ValidationError(_(u'Шууд зардлын дүн хэтэрсэн байна'))
            
        if self.other_create > 0.0:
            if self.other_create <= self.other_limit:
                amount += self.other_create
            else:
                raise ValidationError(_(u'Бусад зардлын дүн хэтэрсэн байна'))
            
        if material_line_count == 0 and labor_line_count == 0:
            raise ValidationError(_(u'Зардлын мөр сонгогдоогүй байна'))
        else:
            vals = {
                    'task_id'           :budget.task_id.id,
                    'project_id'        :budget.project_id.id,
                    'control_budget_id' :budget.id,
                    'origin'            :budget.name,
                    'priority_id'       :self.priority_id.id,
                    'equipment_amount'  :self.equipment_create,
                    'carriage_amount'   :self.carriage_create,
                    'postage_amount'    :self.postage_create,
                    'other_amount'      :self.other_create,
                    'is_in_control_budget' :True,
                    'warehouse_id'      :warehouse_id.id,
                    'location'          :self.location,
                    'comment'           :u'"%s"Хяналтын төсвөөс үүссэн'%(budget.name),
                    'state'             :'draft'
                    }
            purchase_requisition = purchase_requisition.create(vals)
             
            for material_line in budget.material_line_ids:
                if material_line.cost_choose == True and material_line.state == 'confirm':
                    line_vals = {
                                 'requisition_id'    :purchase_requisition.id,
                                 'product_id'        :material_line.product_id.id,
                                 'product_price'     :material_line.price_unit,
                                 'product_qty'       :material_line.product_uom_qty,
                                 'supplied_quantity' :material_line.product_uom_qty,
                                 'product_uom_id'    :material_line.product_uom.id,
                                 'product_desc'      :material_line.name or material_line.product_id.name,
                                 'c_budget_type'     :'material',
                                 'state'             :'confirmed',
                                 'is_new_requisition':material_line.product_id.is_new
                                 }

                    if material_line.product_id.is_new and material_line.product_id.categ_id:
                        line_vals.update({'category_id':material_line.product_id.categ_id.id})
                    if not material_line.product_id.is_new and material_line.product_id.assign_categ_id:
                        line_vals.update({'assign_cat':material_line.product_id.assign_categ_id.id})
                    purchase_requisition_line = purchase_requisition_line.create(line_vals)
                    material_line.write({'state'    :'purchase'})
           
            for labor_line in budget.labor_line_ids:
                if labor_line.cost_choose == True and labor_line.state == 'confirm':
                    labor_vals = {
                                  'requisition_id'    :purchase_requisition.id,
                                  'product_id'        :labor_line.product_id.id,
                                  'product_price'     :labor_line.price_unit,
                                  'product_qty'       :labor_line.product_uom_qty,
                                  'supplied_quantity' :labor_line.product_uom_qty,
                                  'product_uom_id'    :labor_line.product_uom.id,
                                  'product_desc'      :labor_line.name or labor_line.product_id.name,
                                  'c_budget_type'     :'labor',
                                  'state'             :'confirmed',
                                  'is_new_requisition':labor_line.product_id.is_new
                                  }
                    if labor_line.product_id.is_new and labor_line.product_id.categ_id:
                        line_vals.update({'category_id':labor_line.product_id.categ_id.id})
                    if not labor_line.product_id.is_new and labor_line.product_id.assign_categ_id:
                        line_vals.update({'assign_cat':labor_line.product_id.assign_categ_id.id})
                    purchase_requisition_line = purchase_requisition_line.create(labor_vals)
                    labor_line.write({'state'    :'purchase'})
            purchase_line = self.env['request.config.purchase.line']
            sequence =99
            line_ids = purchase_line.search([('state','=','sent_to_supply'),('request_id','=',purchase_requisition.request_id.id)])
            if line_ids:
                sequence = line_ids[0].sequence    
            # purchase_requisition.write({'state':'confirmed','active_sequence':sequence})        
            # purchase_requisition.line_ids.write({'state':'confirmed'})
            purchase_requisition.write_state('confirmed')
            if not purchase_requisition.verify_code and not purchase_requisition.qr_code:
                qr_verify = random_generator()
                path = os.path.abspath("/mnt/data_new/master/empire/odoo_ext/nomin_purchase_requisition/data/")	
                # path = os.path.abspath("/mnt/data_new/master/empire/odoo_ext/nomin_purchase_requisition/data/")	
                # path = os.path.abspath("/home/nominerp/empire/odoo_ext/nomin_purchase_requisition/data/")
                # path = os.path.abspath("/home/erdeneochir.sh/dev/empire/odoo_ext/nomin_purchase_requisition/data/")	
                big_code = pyqrcode.create('http://erp.nomin.mn/verification?search=%s'%(qr_verify))
                big_code.png(path+'/qrcode.png', scale=6, module_color=[0, 0, 0, 128], background=[255, 255, 255])
                img_path=path+"/qrcode.png"
                with open(img_path, 'rb') as f:
                    image = f.read()
                    purchase_requisition.write({'qr_code':image.encode('base64'),'verify_code':qr_verify})
            # purchase_requisition._requisition_amount()
            if material_line_count != 0:
                u_vals = {
                        'budget_id'     :budget.id,
                        'purchase'      :purchase_requisition.id,
                        'date'          :time.strftime('%Y-%m-%d %H:%M:%S'),
                        'price'         :material_product_limit,
                        'map'           :'budget',
                        'state'         :'purchase'
                        }
                utilization_budget_material = utilization_budget_material.create(u_vals)
            if labor_line_count != 0:
                l_vals = {
                        'budget_id'     :budget.id,
                        'purchase'      :purchase_requisition.id,
                        'date'          :time.strftime('%Y-%m-%d %H:%M:%S'),
                        'price'         :labor_product_limit,
                        'map'           :'budget',
                        'state'         :'purchase'
                        }
                utilization_budget_labor = utilization_budget_labor.create(l_vals)
            
            if self.equipment_create > 0.0:
                e_vals = {
                        'budget_id'     :budget.id,
                        'purchase'      :purchase_requisition.id,
                        'date'          :time.strftime('%Y-%m-%d %H:%M:%S'),
                        'price'         :self.equipment_create,
                        'map'           :'budget',
                        'state'         :'purchase'
                        }
                utilization_budget_equipment = utilization_budget_equipment.create(e_vals)
                
            if self.carriage_create > 0.0:
                c_vals = {
                        'budget_id'     :budget.id,
                        'purchase'      :purchase_requisition.id,
                        'date'          :time.strftime('%Y-%m-%d %H:%M:%S'),
                        'price'         :self.carriage_create,
                        'map'           :'budget',
                        'state'         :'purchase'
                        }
                utilization_budget_carriage = utilization_budget_carriage.create(c_vals)
            if self.postage_create > 0.0:
                p_vals = {
                        'budget_id'     :budget.id,
                        'purchase'      :purchase_requisition.id,
                        'date'          :time.strftime('%Y-%m-%d %H:%M:%S'),
                        'price'         :self.postage_create,
                        'map'           :'budget',
                        'state'         :'purchase'
                        }
                utilization_budget_postage = utilization_budget_postage.create(p_vals)
            if self.other_create > 0.0:
                m_vals = {
                        'budget_id'     :budget.id,
                        'purchase'      :purchase_requisition.id,
                        'date'          :time.strftime('%Y-%m-%d %H:%M:%S'),
                        'price'         :self.other_create,
                        'map'           :'budget',
                        'state'         :'purchase'
                        }
                utilization_budget_other = utilization_budget_other.create(m_vals)
            
            return {
                     'type': 'ir.actions.act_window',
                     'name': _('Register Call'),
                     'res_model': 'purchase.requisition',
                     'view_type' : 'tree',
                     'view_mode' : 'form',
                     'search_view_id' : view_id,
                     'res_id':purchase_requisition.id,
                     'target' : 'current',
                     'nodestroy' : True,
                 }