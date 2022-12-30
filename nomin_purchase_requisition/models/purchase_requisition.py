# -*- coding: utf-8 -*-
from re import L
from openerp import api, fields, models, _
from openerp.exceptions import UserError
from fnmatch import translate
from openerp.osv import osv
from datetime import date
from datetime import datetime, timedelta
from openerp.http import request
import time
import logging
_logger = logging.getLogger(__name__)
from openerp.exceptions import UserError, AccessError
from PIL import Image
import string
import random
import os
import pyqrcode
from dateutil.relativedelta import relativedelta
import workdays

from zeep import Client, Settings
from zeep.transports import Transport
from requests import Session
from requests.auth import HTTPBasicAuth


def random_generator(size=16, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

def check_attachment(self, cr, uid, res_model, res_id):
    cr.execute("select id from ir_attachment where res_model='%s' and res_id=%s"%(res_model,res_id))
    fetched = cr.fetchall()
    if fetched:
        for f in fetched:
            self.pool.get('ir.attachment').unlink(cr, uid, [f[0]])
class purchase_rate_employee(models.TransientModel):
    _name = 'purchase.rate.employee'

    percent = fields.Float(string='Percent', required=True)  #Хувь
    description = fields.Text(string='Description' ,required=True) #Тайлбар

    @api.onchange('percent')
    def onchange_percent(self):
        if self.percent >100 or self.percent <0:
            self.percent = 0

    @api.multi
    def rate(self):
        active_id = self.env.context.get('active_id', False)
        requisition_id = self.env['purchase.requisition.line'].browse(active_id)
        requisition_id.write({'rate_percent':self.percent})
        return {'type': 'ir.actions.act_window_close'}

class purchase_requision_line(models.Model):
    _inherit = 'purchase.requisition.line'
    
    # @api.multi
    # def _compute_users(self):


    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(purchase_requision_line, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    #     allowed_deps = self.env.user.budget_allowed_departments.ids
    #     doc = etree.XML(res['arch'])
    #     for node in doc.xpath("//field[@name='from_partner_id']"):
    #         user_filter =  "[('id', 'in',"+str(allowed_deps)+")]"
    #         node.set('domain',user_filter)
    #     res['arch'] = etree.tostring(doc)
    #     return res

    @api.multi
    def _is_in_supply_manager(self):
        for line in self:
            notif_groups = self.env['ir.model.data'].get_object_reference( 'nomin_purchase_requisition', 'group_supply_import_manager')[1]
            
            next_user_ids = self.env['res.users'].search([('groups_id','in',[notif_groups])])
            if line._uid in next_user_ids.ids:
                line.is_in_supply_manager =True
            
            notif_groups_ids = self.env['ir.model.data'].get_object_reference( 'nomin_purchase_requisition', 'group_haaa_head')[1]
            
            supply_user_ids = self.env['res.users'].search([('groups_id','in',[notif_groups_ids])])
            if line.state in ['assigned']:
                if line._uid in supply_user_ids.ids:
                    line.is_in_supply_chiefs = True
                    
                notif_user_ids = self.env['ir.model.data'].get_object_reference( 'nomin_purchase_requisition', 'group_haaa_director')[1]        
                supply_ids = self.env['res.users'].search([('groups_id','in',[notif_user_ids])])
                if line._uid in supply_ids.ids:
                    line.is_in_supply_chiefs = True
            else:
                if line.requisition_id.is_in_confirm:
                    line.is_in_supply_chiefs = True
    @api.multi
    def _compute_amount(self):
        
        for purchase in self:
            if purchase.state in ['confirmed','ready','assigned','done']:
                if self._uid == purchase.buyer.id:
                    purchase.is_user = True
                if self._uid == purchase.requisition_id.user_id.id:
                    purchase.is_receive_user = True
            
            elif purchase.state in ['compare']:
                if purchase.allowed_amount != 0 and purchase.category_id and purchase.comparison_user_id and purchase.buyer:
                    comparison_config_obj = self.env['comparison.employee.config'].search([('category_ids','in',purchase.category_id.id),('user_id','=',purchase.comparison_user_id.id)])
                    if comparison_config_obj:
                        if purchase.allowed_amount >= comparison_config_obj[0].comparison_value:
                            purchase.is_skip_user = True
                if self._uid == purchase.comparison_user_id.id:
                    purchase.is_comparison_user = True
                if self._uid == purchase.buyer.id and not purchase.comparison_user_id:
                    purchase.is_buyer = True

            purchase.amount = purchase.product_qty * purchase.product_price
       
    @api.multi
    def _compute_allowed_amount(self):
        for purchase in self:
            purchase.allowed_amount = purchase.allowed_qty * purchase.product_price

    @api.multi
    def _compute_received_qty(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id','=',self._uid)])
        company_id = employee_id.department_id.company_id.id
        sector_id = self.env['hr.department'].get_sector(self.env.user.department_id.id)
        picking_type_obj = self.env['stock.picking.type']
        picking_type_ids = picking_type_obj.sudo().search([('code','=','incoming'),('warehouse_id.department_of_id','=',sector_id)])
        for line in self: 
            received_qty = 0
            line_ids = self.env['stock.move'].sudo().search([('requisition_line_id','=',line.id),('state','=','done'),('picking_type_id','in',picking_type_ids.ids)])
            for  move in line_ids:
                received_qty = received_qty+move.product_uom_qty 
            line.received_qty = received_qty

    @api.multi
    def _is_control(self):
        for line in self:
            
            if line.requisition_id.control_budget_id:
            
                line.is_control =True
            else:
            
                line.is_control =False

    @api.multi
    def _is_accountant(self):
        for line in self:
            if line.state == 'sent_nybo':
                user_ids = line.requisition_id._check_user_in_request('sent_nybo', True)
                if user_ids:
                    if self.env.user.id in user_ids:
                        line.is_accountant = True
     


    @api.multi
    def _product_mark(self):
        
        for line in self:
            if line.product_id:
                line.product_mark = line.product_id.product_mark
    @api.multi
    def _compute_purchase_users(self):
        purchase_user_ids = []
        group_ids=[]
        group_ids.append(self.env['ir.model.data'].get_object_reference('nomin_purchase_requisition', 'group_procurement_buyer')[1])
        group_ids.append(self.env['ir.model.data'].get_object_reference('nomin_purchase_requisition', 'group_complex_manager')[1])
        group_ids.append(self.env['ir.model.data'].get_object_reference('nomin_purchase_requisition', 'group_nyrav_department')[1])
        group_ids.append(self.env['ir.model.data'].get_object_reference('nomin_purchase_requisition', 'group_supply_import_manager')[1])

        buyer_ids = self.env['res.users'].sudo().search([('groups_id','in',group_ids)])
        for line in self:
            if buyer_ids:
                line.purchase_user_ids = buyer_ids.ids

    received_qty = fields.Float(string='Received qty', compute= _compute_received_qty) #Хүлээн авсан тоо хэмжээ
    product_mark = fields.Char(string='Product rate', compute = _product_mark) #Барааны үзүүлэлт
    purchase_user_ids = fields.Many2many(comodel_name='res.users',relation='purhase_requisition_line_res_users_rel', compute=_compute_purchase_users,string='Purchase user') #Худалдан авалт хийх хэрэглэгч
    amount = fields.Float(string='Amount', compute='_compute_amount')
    is_control = fields.Boolean(string='Is control', default= False)
    rate_percent = fields.Float(string='Percent') #Хувь
    is_in_supply_chiefs = fields.Boolean(string='Supply manager state' , compute = _is_in_supply_manager, default=False) #Хангамж менежер төлөв
    is_in_supply_manager = fields.Boolean(string='Supply manager' , compute = _is_in_supply_manager, default=False) #Хангамж менежер
    is_user = fields.Boolean(string='Is user', default=False, compute= _compute_amount) #Мөн
    is_receive_user = fields.Boolean(string='Is receive user', default=False, compute= _compute_amount) #Мөн
    is_comparison_user = fields.Boolean(string='Is comparison user', default=False, compute=_compute_amount)
    is_skip_user = fields.Boolean(string='Is skip user', default=False, compute=_compute_amount)
    is_buyer = fields.Boolean(string='Is buyer', default=False, compute=_compute_amount)
    allowed_qty = fields.Float(string='Allowed qty') #Зөвшөөрөгдсөн тоо хэмжээ
    allowed_amount = fields.Float(string='Allowed amount', compute=_compute_allowed_amount) #Зөвшөөрөгдөх дүн
    confirmed_date = fields.Date(string='Confirmed date') #Батлагдсан огноо
    allowed_date = fields.Date(string='Allowed date') #Зөвшөөрөгдсөн хугацаа
    assign_cat = fields.Many2one('assign.category',string="Хуваарилалтын ангилал",domain=[('is_active','=',True)])
    is_accountant = fields.Boolean(string='Is accountant', compute=_is_accountant)
    # user_ids = fields.Many2many('res.users', 'user_id', 'requisition_id', 'Project_stages')

    @api.multi
    def write(self, vals):
        states = []
        product_obj = self.env['product.product']

        for line in self:
       
            if vals.get('product_qty'):
                vals.update({'allowed_qty':vals.get('product_qty')})
            if vals.get('allowed_qty'):
                vals.update({'allowed_qty':vals.get('allowed_qty')})

            if vals.get('product_id'):
                product_id = product_obj.search([('id','=',vals.get('product_id'))])
                vals.update({'product_price':product_id.sudo().cost_price})
                if product_id.assign_categ_id:
                    categ_ids = line.find_buyer(product_id.assign_categ_id.id,line.requisition_id.department_id)
                    if categ_ids:
                        vals.update({'buyer':categ_ids[0].user_id.id,'assign_cat':product_id.assign_categ_id.id})
                if product_id.categ_id:
                    categ_ids = line.find_buyer(product_id.categ_id.id,line.requisition_id.department_id)
                    if categ_ids:
                        vals.update({'buyer':categ_ids[0].user_id.id,'category_id':product_id.categ_id.id})
                    # else:
                    #     raise UserError('"%s"-н "%s" ангилалд харгалзах худалдан авалтын ажилтан тохируулагдаагүй байна. Худалдан авалтын ахлах менежерт хандаж тохиргоогоо хийлгэнэ үү.'%(self.requisition_id.department_id.name, self.assign_cat.name))
                self.deliver_product_id = product_id
                self.supplied_quantity = vals.get('product_qty')
            
            if vals.get('category_id'):
                categ_ids = line.find_buyer(vals.get('category_id'),line.requisition_id.department_id)
                if categ_ids:
                    vals.update({'buyer':categ_ids[0].user_id.id,'category_id':vals.get('category_id')})

                category_id = self.env['product.category'].search([('id','=',vals.get('category_id'))])
                if category_id:
                    comparison_emp_id = line.find_comparison_employee(category_id,line.allowed_amount)
                    if comparison_emp_id:
                        vals.update({'comparison_user_id':comparison_emp_id})
                        
            previous_buyer = ""
            if vals.has_key('buyer') and line.requisition_id.state in ('assigned'):
                previous_buyer = line.buyer.name if line.buyer else "-"
        line_id = super(purchase_requision_line, self).write(vals)

        for line in self:
            if line.requisition_id:
                line.requisition_id.message_subscribe_users(line.buyer.id)
                for req in line.requisition_id.line_ids:
                    if req.state not in states:
                        states.append(req.state)
                if len(states)<= 1:
                    # if 'purchased' in states:
                    #     line.requisition_id.state ='purchased'
                    if 'done' in states:
                        req.requisition_id.state ='done'

            # if previous_buyer != "":
            #     new_buyer = line.buyer.name if line.buyer else "-"
            #     message = '"%s" барааны худалдан авах ажилтан "%s" - г "%s" болгож өөрчиллөө' % (line.product_id.name,previous_buyer,new_buyer)
            #     line.requisition_id.message_post(message)

        return line_id


    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            if self.product_id.partner_type in ('C','N'):
                partner = self.env['res.partner'].search([('partner_id','=',68293)])
                if partner:
                    self.partner_id = partner
            self.deliver_product_id = self.product_id
            group_ids        = self.env['ir.model.data'].get_object_reference('nomin_purchase_requisition', 'group_procurement_buyer')[1]
            buyer_ids = self.env['res.users'].sudo().search([('groups_id','in',group_ids)])
            self.product_price = self.product_id.sudo().cost_price
            self.supplied_price = self.product_id.sudo().cost_price
            self.allowed_qty = self.product_qty
            # self.supplied_quantity = self.allowed_qty
            # self.product_uom = self.product_id.
            # self.write({'allowed_qty':self.product_qty})
            self.allowed_amount = self.product_qty * self.product_price
            self.supplied_amount = self.product_qty * self.product_price
            self.product_uom_id = self.product_id.uom_id.id
            
            name = ''
            product_name =''
            if self.product_id.name:
                product_name = self.product_id.name 
            if  self.product_desc:
                name = self.product_desc
            # self.product_desc = name+' ' + str(product_name)
            self.product_mark = self.product_id.product_mark
            if self.product_id.categ_id and self.is_new_requisition:
                self.category_id = self.product_id.categ_id

    @api.onchange('category_id')
    def onchange_category_id(self):
        # self.product_type = self.assign_cat.product_type
        categ_ids = self.find_buyer(self.category_id.id,self.requisition_id.department_id)
        if categ_ids:
            self.buyer = categ_ids[0].user_id.id

    @api.onchange('assign_cat')
    def onchange_assign_cat(self):
        self.product_type = self.assign_cat.product_type
        categ_ids = self.find_buyer(self.assign_cat.id,self.requisition_id.department_id)
        if categ_ids:
            self.buyer = categ_ids[0].user_id.id

    def find_buyer(self, category_id, department_id):
        if not self.is_new_requisition:
            categ_ids = self.env['purchase.category.config'].sudo().search([('category_ids','in',category_id),('department_ids','in',department_id.id)])
        else:
            categ_ids = self.env['purchase.category.config'].sudo().search([('product_category_ids','in',category_id),('department_ids','in',department_id.id)])

        if categ_ids:
            return categ_ids
        else:
            if department_id.parent_id:
                if not self.is_new_requisition:
                    categ_ids = self.env['purchase.category.config'].sudo().search([('category_ids','in',category_id),('department_ids','in',department_id.parent_id.id)])
                else:
                    categ_ids = self.env['purchase.category.config'].sudo().search([('product_category_ids','in',category_id),('department_ids','in',department_id.parent_id.id)])
                if categ_ids:
                    return categ_ids
                
        
        return False

    def find_comparison_employee(self, category_id, allowed_amount = 0):
        if not category_id:
            raise UserError(_(u'Ангилал тохируулагдаагүй байна.'))
        if not self.is_new_requisition:
            comparison_employee = self.env['comparison.employee.config'].search([('category_ids','in',category_id.id)])
        else:
            comparison_employee = self.env['comparison.employee.config'].search([('product_category_ids','in',category_id.id)])

        if not comparison_employee:
            raise UserError(_(u'Харьцуулалт хийх ажилтны %s ангилал дээр тохиргоо хийгдээгүй байна. Худалдан авалтын ахлах менежерт хандаж тохиргоогоо хийлгэнэ үү'%(category_id.name)))
            
        if allowed_amount != 0:
            if not self.is_new_requisition:
                comparison_employee = self.env['comparison.employee.config'].search([('category_ids','in',category_id.id),('comparison_value','<=',allowed_amount)])
            else:
                comparison_employee = self.env['comparison.employee.config'].search([('product_category_ids','in',category_id.id),('comparison_value','<=',allowed_amount)])

        if comparison_employee:
            self.comparison_user_id = comparison_employee[0].user_id.id
            return comparison_employee[0].user_id.id


    @api.onchange('allowed_amount')
    def onchange_purchase(self):
        purchase_user_ids = []
        group_ids=[]
        group_ids.append(self.env['ir.model.data'].get_object_reference('nomin_purchase_requisition', 'group_procurement_buyer')[1])
        group_ids.append(self.env['ir.model.data'].get_object_reference('nomin_purchase_requisition', 'group_complex_manager')[1])
        group_ids.append(self.env['ir.model.data'].get_object_reference('nomin_purchase_requisition', 'group_nyrav_department')[1])
        group_ids.append(self.env['ir.model.data'].get_object_reference('nomin_purchase_requisition', 'group_supply_import_manager')[1])

        buyer_ids = self.env['res.users'].sudo().search([('groups_id','in',group_ids)])
        for line in self:
            if buyer_ids:
                purchase_user_ids = buyer_ids.ids

        return {'domain':{'buyer':[('id','in',purchase_user_ids)]}}

    @api.onchange('product_price')
    def onchange_price(self):

        # self.product_price = self.product_id.standard_price
        # self.allowed_qty = self.product_qty
        # self.product_uom = self.product_id.
        # self.write({'allowed_qty':self.product_qty})
        self.allowed_amount = self.product_qty * self.product_price
        self.amount = self.product_qty * self.product_price
        # self.product_desc = '/ '+ str(self.product_id.name)

    @api.onchange('product_qty')
    def onchange_product_qty(self):
        group_ids        = self.env['ir.model.data'].get_object_reference('nomin_purchase_requisition', 'group_procurement_buyer')[1]
        buyer_ids = self.env['res.users'].sudo().search([('groups_id','in',group_ids)])
        # self.product_price = self.product_id.standard_price
        self.allowed_qty = self.product_qty
        self.supplied_quantity = self.product_qty
        # self.product_uom = self.product_id.
        # self.write({'allowed_qty':self.product_qty})
        self.allowed_amount = self.product_qty * self.product_price
        self.amount = self.product_qty * self.product_price
        self.supplied_amount = self.product_qty * self.product_price
        
    @api.onchange('allowed_qty')
    def onchange_allowed_qty(self):
        self.allowed_amount = self.allowed_qty * self.product_price
    @api.multi
    def unlink(self):
        for order in self:
            if order.state != 'draft':
                raise UserError(_(u'Ноорог төлөвтэй шаардахын мөр устгаж болно.'))
        return super(purchase_requision_line, self).unlink()

    @api.model
    def create(self, vals):
        product_obj = self.env['product.product']
        # if not vals.('schedule_date'):
        #     vals.update({'':})
        if vals.get('product_id'):
            product_id = product_obj.search([('id','=',vals.get('product_id'))])
            vals.update({'product_price':product_id.sudo().cost_price,
                         'deliver_product_id':product_id.id})

            if vals.get('requisition_id'):
                purchase_requisition = self.env['purchase.requisition'].search([('id','=',vals.get('requisition_id'))])
                if purchase_requisition.is_new_requisition:
                    categ_ids = self.find_buyer(product_id.categ_id.id,purchase_requisition.department_id)
                else:
                    categ_ids = self.find_buyer(product_id.assign_categ_id.id,purchase_requisition.department_id)

                if categ_ids:
                    vals.update({'buyer':categ_ids[0].user_id.id,'assign_cat':product_id.assign_categ_id.id})
                # else:
                #     raise UserError('"%s"-н "%s" ангилалд харгалзах худалдан авалтын ажилтан тохируулагдаагүй байна. Худалдан авалтын ахлах менежерт хандаж тохиргоогоо хийлгэнэ үү.'%(self.requisition_id.department_id.name, self.assign_cat.name))
            # if vals.get('partner_id'):
            #     if product_id.partner_type in ('C','N'):
            #         print '\n\n acacacac'
            #         self.update({'partner_id':vals.get('partner_id')})
        if vals.get('product_qty'):
            vals.update({'allowed_qty':vals.get('product_qty')})
        requsiton_id = super(purchase_requision_line,self).create(vals)
        # if requsiton_id.requisition_id.state !='draft' and vals.get('state')!='confirmed':
        #             raise UserError(_(u'Ноорог төлөвтэй шаардахын мөр дээр нэмж болно.'))
        if vals.get('deliver_product_id'):
            requsiton_id.supplied_price = requsiton_id.deliver_product_id.sudo().cost_price
        if vals.get('supplied_quantity'):
            requsiton_id.update({'supplied_amount': vals.get('supplied_quantity') * requsiton_id.supplied_price})
        return requsiton_id  



    @api.multi
    def action_sent_nybo(self):        
        user_ids = self.requisition_id._check_user_in_request('sent_nybo', True)
        if not self.partner_id:
            raise UserError(u'Харилцагч талбарыг бөглөнө үү')
        if user_ids:
            self.requisition_id.message_subscribe_users(user_ids)
            self.write({'accountant_ids': [(6,0,user_ids)],
                        'state':'sent_nybo',
                        'product_delivery_date':time.strftime('%Y-%m-%d')
                        })
            self.requisition_id._ordering_date_new()
            self.requisition_id._exceed_days_1()
        else:
            raise UserError(u'Тухайн салбарыг хариуцсан нягтлан бодогч алга.')
        
        # self.update_sap_account_assignment_category()
                        


    @api.multi
    def action_done(self):
        self.write({'state':'done','date_end':time.strftime('%Y-%m-%d')})
        is_false= True
        for line in self:
            for req in line.requisition_id.line_ids:
                if req.state!='done':
                    is_false = False
            if is_false:
                line.requisition_id.write({'state':'done'})
                if not line.requisition_id.tender_id:
                    line.requisition_id.create_history('done')
                # line.requisition_id.action_send_email('done',[line.requisition_id.user_id.id])
        # self.update_sap_account_assignment_category()

    @api.multi
    def action_send(self):
        #Хангамжийн мэргэжилтэн бараа тодорхойлоод илгээх
        for line in self:
            if line.product_price==0.0:
                raise UserError(_(u'Барааны үнэ оруулж өгнө үү.'))
            if line.product_id:
                if not self.requisition_id.is_new_requisition:
                    if not line.product_id.assign_categ_id==line.assign_cat:
                        if line.product_id.assign_categ_id:
                            categ_ids = line.find_buyer(line.product_id.assign_categ_id.id,line.requisition_id.department_id)
                            if not categ_ids:
                                raise UserError('"%s"-н "%s" ангилалд харгалзах худалдан авалтын ажилтан тохируулагдаагүй байна. Худалдан авалтын ахлах менежерт хандаж тохиргоогоо хийлгэнэ үү.'%(line.requisition_id.department_id.name, line.product_id.assign_categ_id.name))
                            line.write({'buyer':categ_ids[0].user_id.id,'assign_cat':line.product_id.assign_categ_id.id}) 
                        else:
                            categ_ids = line.find_buyer(line.assign_cat.id,line.requisition_id.department_id)
                            if not categ_ids:
                                raise UserError('"%s"-н "%s" ангилалд харгалзах худалдан авалтын ажилтан тохируулагдаагүй байна. Худалдан авалтын ахлах менежерт хандаж тохиргоогоо хийлгэнэ үү.'%(line.requisition_id.department_id.name, line.assign_cat.name))
                            line.write({'buyer':categ_ids[0].user_id.id})
                else:
                    if not line.product_id.categ_id==line.category_id:
                        if line.product_id.categ_id:
                            categ_ids = line.find_buyer(line.product_id.categ_id.id,line.requisition_id.department_id)
                            if not categ_ids:
                                raise UserError('"%s"-н "%s" ангилалд харгалзах худалдан авалтын ажилтан тохируулагдаагүй байна. Худалдан авалтын ахлах менежерт хандаж тохиргоогоо хийлгэнэ үү.'%(line.requisition_id.department_id.name, line.product_id.categ_id.name))
                            line.write({'buyer':categ_ids[0].user_id.id,'category_id':line.product_id.categ_id.id}) 
                        else:
                            categ_ids = line.find_buyer(line.category_id.id,line.requisition_id.department_id)
                            if not categ_ids:
                                raise UserError('"%s"-н "%s" ангилалд харгалзах худалдан авалтын ажилтан тохируулагдаагүй байна. Худалдан авалтын ахлах менежерт хандаж тохиргоогоо хийлгэнэ үү.'%(line.requisition_id.department_id.name, line.category_id.name))
                            line.write({'buyer':categ_ids[0].user_id.id})
            else:
                raise UserError(_(u'Бараа сонгож өгнө үү.'))
            line.write({'state':'sent'})
            is_sent =True
            for line in line.requisition_id.line_ids:
                if line.state!='sent':
                    is_sent=False
            if is_sent:
                line.requisition_id.send_request()
                # self.requisition_id.write({'state':'sent'})


                
    @api.multi
    def rate_employee(self):

        return {
            'name': 'Note',
            'view_type': 'form',
            'view_mode': 'form',
            #'view_id': [res and res[1] or False],
            'res_model': 'purchase.rate.employee',
            'context': self._context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            #'res_id': ids[0]  or False,
        }
    
    @api.multi
    def action_user_return(self):

        return {
            'name': 'Note',
            'view_type': 'form',
            'view_mode': 'form',
            #'view_id': [res and res[1] or False],
            'res_model': 'purchase.requisition.set.done',
            'context': self._context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            #'res_id': ids[0]  or False,
        }   

    # @api.multi
    # def update_sap_account_assignment_category(self):
    #     for lines in self:
    #         for line in lines:
    #             if line.sap_account_assignment_category:
    #                 print '\n\n\n print line -----------' , line , line.sap_account_assignment_category , line.product_id 
    #                 print '\n\n\n baraa' , line.product_id.account_assignment_category
    #                 line.product_id.account_assignment_category = line.sap_account_assignment_category

    @api.multi
    def action_skip_comparison(self):
        for line in self:
            line.write({
                'state': 'ready'
            })
        print '\n\n\n aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        # self.update_sap_account_assignment_category()

    

class internal_purchase_limit_month(models.Model):
    _name = 'purchase.limit.month'
    
    employee_id = fields.Many2one('hr.employee',string='Employee')
    job_name   = fields.Char(string='Албан тушаал', related="employee_id.job_id.name")               
    department_id   = fields.Char(string='Хэлтэс', related="employee_id.department_id.name")      
    month_id = fields.Many2one('account.period', string="Month period")
    purchase_month_limit = fields.Float(string='External Month limit balance')
    month_limit = fields.Float(string=u"Сарын лимит")
    
    
class job_position_limit_line(models.Model):
    _name = 'job.position.limit.line'
    job_id = fields.Many2one('hr.job',string='Job position', required=True)
    # group_id = fields.Many2one('res.groups', string="Groups" ,required=True)
    purchase_limit_month = fields.Float('External Purchase limit month', digits = (16,2))
    config_id = fields.Many2one('job.position.limit.config', string="Limit config")
class job_position_limit_config(models.Model):
    _name = 'job.position.limit.config'
    name =  fields.Char('Name', required=True)
    year_id = fields.Many2one('account.fiscalyear','Fiscal year')
    line_id = fields.One2many('job.position.limit.line','config_id','Job position limit line', copy=True)

    @api.one
    def copy(self, default=None):
        """ Need to set origin after copy because original copy clears origin

        """

        if default is None:
            default = {}

        
        default.update({'year_id':False,'name':''})
        newpo = super(job_position_limit_config, self).copy(default=default)

        return newpo    
    @api.one
    @api.constrains('name', 'year_id')
    def _check_description(self):
        if self.name:
            name = self.env['job.position.limit.config'].search([('name','=',self.name)])

            if len(name)>1:
                raise UserError(_(u'Худалдан авалт лимит тохиргооны нэр давхцаж болохгүй.'))
            year = self.env['job.position.limit.config'].search([('year_id','=',self.year_id.id)])
            if len(year)>1:
                raise UserError(_(u'Худалдан авалт лимит тохиргооны жил давхцаж болохгүй..'))
class purchase_confirm_history_lines(models.Model):
    _name ='purchase.confirm.history.lines'

    requisition_id = fields.Many2one('purchase.requisition',string='Requisition')
    user_id = fields.Many2one('res.users', string='User')


class purchase_requisition(models.Model):
    _inherit = ['purchase.requisition']
    _order = "create_date desc"

    
    """New api compute function doesnt return True"""
    STATE_SELECTION=[('draft','Ноорог'),
                       ('sent','Илгээгдсэн'),#Илгээгдсэн
                       ('approved','Зөвшөөрсөн'),#Зөвшөөрсөн
                       ('verified','Хянасан'),#Хянасан
                       ('next_confirm_user','Дараагийн батлах хэрэглэгчид илгээгдсэн'),#Дараагийн батлах хэрэглэгчид илгээгдсэн
                       ('confirmed','Баталсан'),#Батласан
                       ('tender_created','Тендер үүссэн'),#Тендер үүссэн
                    #    ('sent_to_supply','Хангамжид илгээгдсэн'),#Хангамжаарх худалдан авалт
                    #    ('tender_request','Тендер зарлуулах хүсэлт'),#Тендер зарлуулах хүсэлт
                    #    ('fulfil_request','Биелүүлэх хүсэлт'),# Биелүүлэх хүсэлт
                    #    ('retrive_request','Буцаагдах хүсэлт'),# Буцаагдах хүсэлт
                    #    ('rfq_created','Үнийн санал үүссэн'),#Үнийн санал үүссэн
                    #    ('fulfill','Fulfil'),# Биелүүлэх
                       ('assigned',u'Хуваарилагдсан'),#Хуваарилагдсан
                       ('retrived','Буцаагдсан'),# Буцаагдсан
                       ('rejected','Татгалзсан'),
                       ('canceled','Цуцлагдсан'),#Цуцлагдсан
                    #    ('purchased','Худалдан авалт үүссэн'),#Худалдан авалт үүссэн
                       ('sent_to_supply_manager','Бараа тодорхойлох'),#Хангамж импортын менежер
                       ('done','Дууссан'),
                                   ]
    
    @api.multi
    def _color_change(self):
        today = datetime.strptime(time.strftime('%Y-%m-%d'), "%Y-%m-%d")
        for purchase in self:
            if purchase.state in ['confirmed','tender_created','assigned']:
                if purchase.ordering_date:
                    if datetime.strptime(purchase.ordering_date,'%Y-%m-%d') < today:
                        purchase.exceed_days = (today -datetime.strptime(purchase.ordering_date,'%Y-%m-%d')).days
                        purchase.change_color ='red'

    def _get_holidays(self, date_from, date_to):
        """Returns a float equals to the timedelta between two dates given as string."""

        DATE_FORMAT = "%Y-%m-%d"
        from_dt = datetime.strptime(date_from, DATE_FORMAT)
        to_dt = datetime.strptime(date_to, DATE_FORMAT)
        
        query = """SELECT count(*) AS count_days_no_weekend FROM   generate_series(timestamp '%s', timestamp '%s', interval '1 day') the_day WHERE  extract('ISODOW' FROM the_day) < 6"""%(from_dt, to_dt)
        self.env.cr.execute(query)
        working_day = self.env.cr.fetchone()[0]
        self.env.cr.execute("select count(id) from hr_public_holiday where extract(ISODOW from days_date) not in (6,7) and days_date between %s and %s",(from_dt,to_dt))
        public_holidays = self.env.cr.fetchone()[0]

        return working_day - public_holidays
    
    def _get_public_holidays(self,date_from):

        public_holidays = []
        
        public_holidays_ids = self.env['hr.public.holiday'].search([('days_date','>',date_from)])
        for item in public_holidays_ids:
            public_holidays.append(datetime.strptime(item.days_date, '%Y-%m-%d'))
            
        return  public_holidays
    
    

    @api.multi
    def _exceed_days_1(self):
        days = 0
        for purchase in self:
            for lines in purchase.line_ids:
                for line in lines:
                    if line.state_history_ids:
                        for his in line.state_history_ids:
                            if his.state == 'sent_nybo' and his.date and purchase.ordering_date_new:
                                if his.date < purchase.ordering_date_new:
                                    days = self._get_holidays(his.date,purchase.ordering_date_new)
                                    days = days * -1
                                    purchase.write({'exceed_days_1':days})
                                else:
                                    days = self._get_holidays(purchase.ordering_date_new,his.date,)
                                    purchase.write({'exceed_days_1':days})
                                # his_date = datetime.strptime(his.date, '%Y-%m-%d')
                                # all_days = (his_date -datetime.strptime(purchase.ordering_date_new,'%Y-%m-%d')).days 

    @api.multi
    def _ordering_date_new(self):
        sum_day = 0
        conf_day = 0
        public_holidays = []
        for purchase in self:
            if purchase.priority_id and purchase.confirmed_date:
                sum_day = purchase.priority_id.priority_day + purchase.priority_id.comparison_day 
                conf_day = datetime.strptime(purchase.confirmed_date, '%Y-%m-%d')
                public_holidays = self._get_public_holidays(purchase.confirmed_date)
                working_days = workdays.workday(conf_day,sum_day,public_holidays)
                purchase.ordering_date_new = working_days 
                purchase.write({'ordering_date_new':working_days})

    @api.multi
    def unlink(self):
        for order in self:
            if order.state != 'draft':
                raise UserError(_(u'Ноорог төлөвтэй шаардах устгаж болно.'))
            check_attachment(self, self._cr, self._uid, 'purchase.requisition', order.id)
        return super(purchase_requisition, self).unlink()

    @api.multi
    def _check_user_in_request(self, state, from_line = False):
        sel_user_ids= []
        user_ids = []
        conf_line = self.env['request.config.purchase.line']
        groups = self.env['res.groups']
        config_obj = self.env['request.config']
        group_ids = []
        for request in self:
            config_id = request.request_id.id
            line_ids =conf_line.search([('sequence','=',request.active_sequence),('request_id','=',config_id)])

            if from_line:
                line_ids =conf_line.search([('state','=',state),('request_id','=',config_id)])

            if line_ids:
                for req in line_ids:
                    if req.state == state:
                        if req.type == 'group':
                            group = req.group_id
                            group_ids.append(req.group_id.id)
                            # for group in groups.browse(group_id):
                            for user in group.users:
                                sel_user_ids.append( user.id)
                        elif req.type == 'fixed':
                            sel_user_ids.append(req.user_id.id)
                        elif req.type == 'depart':
                            user_id = self.department_id.user_id.id
                            if user_id :
                                sel_user_ids.append( user_id)
                            else :
                                raise osv.except_osv(_('Warning !'), _(u"Хэлтэсийн менежер дээр холбоотой хэрэглэгч талбар хоосон байна."))
        # if self.state=='sent_to_supply' or self.state=='fulfil_request':
        #     user_ids = sel_user_ids
        # else:
        user_ids = self.get_possible_users( sel_user_ids)
        if group_ids :
            group_id= self.env['ir.model.data'].get_object_reference('nomin_base', 'group_financial_business_chief')[1]
            if group_id in group_ids:
                group = groups.search([('id','=',group_id)])
                for user in group.users:
                    user_ids.append(user.id)
            group_id= self.env['ir.model.data'].get_object_reference('nomin_base', 'group_president')[1]
            if group_id in group_ids:        
                group = groups.search([('id','=',group_id)])
                for user in group.users:
                    user_ids.append(user.id)
            group_id= self.env['ir.model.data'].get_object_reference('nomin_base', 'group_holding_ceo')[1]
            if group_id in group_ids:        
                group = groups.search([('id','=',group_id)])
                for user in group.users:
                    user_ids.append(user.id)
           
        user_ids = list(set(user_ids))
        return user_ids

    @api.one
    def _is_in_sent(self):
        # if self.state=='draft':
            sel_user_ids = self._check_user_in_request('sent')
            if self.state in ['sent_to_supply_manager']:
                    self.is_in_sent = False
            elif self._uid in sel_user_ids:
                self.is_in_sent = True
            else:
                self.is_in_sent = False
    @api.one
    def _is_in_approve(self):
        sel_user_ids = []
        sel_user_ids = self._check_user_in_request('approved')
        if self._uid in sel_user_ids:
            self.is_in_approve = True
        else:
            self.is_in_approve = False  
    
    @api.one
    def _is_in_verify(self):
        self._ordering_date_new()
        self._exceed_days_1()
        sel_user_ids = []
        sel_user_ids = self._check_user_in_request('verified')
        if self._uid in sel_user_ids:
            self.is_in_verify = True
        else:
            self.is_in_verify = False   

    @api.one
    def _auto_change_statee(self):
        states = []
        self.auto_change_state=False
        for line in self.line_ids:
            if line.state not in states:
                states.append(line.state)
        if len(states)<= 1:
            # if 'purchased' in states:
            #     self.state ='purchased'
            if 'done' in states:
                self.state ='done'

    @api.one
    def _is_in_confirm(self):
        sel_user_ids = []
#         sel_user_ids = self._check_user_in_request('confirmed')
        sel_user_ids = self.get_confirm_users('confirmed')
#         sel_user_ids = sel_user_ids+confirm_user_ids
        if self.state in ['draft','sent_to_supply_manager','confirmed','done','tender_created','retrived','assigned','rejected','canceled']:
            self.is_in_confirm= False
        elif self._uid in sel_user_ids:
            self.is_in_confirm= True
        else:
            self.is_in_confirm = False  

#     @api.one
#     def _is_in_sent_supply(self):
#         sel_user_ids = []
# #         sel_user_ids = self._check_user_in_request('confirmed')
#         sel_user_ids = self._check_user_in_request('sent_to_supply')
        
# #         sel_user_ids = sel_user_ids+confirm_user_ids

#         if self.state =='sent_to_supply':
#             if self._uid in sel_user_ids:
#                 self.is_in_sent_supply= True
#             else:
#                 self.is_in_sent_supply= False
#         else:
#             self.is_in_sent_supply = False  

#     @api.one
#     def _is_in_fullfil(self):
#         sel_user_ids = []
# #         sel_user_ids = self._check_user_in_request('confirmed')
#         sel_user_ids = self._check_user_in_request('fulfil_request')
        
# #         sel_user_ids = sel_user_ids+confirm_user_ids
#         if self.state in ['fulfil_request','retrive_request']:
#             if self._uid in sel_user_ids:
#                 self.is_in_fullfil= True
#             else:
#                 self.is_in_fullfil= False
#         else:
#             self.is_in_fullfil = False  



    @api.multi
    def zzzzzzzzz(self):
        self.run_years(2017)
    
    @api.multi
    def z2018(self):
        self.run_years(2018)  

    @api.multi
    def z2019(self):
        self.run_years(2019) 

    @api.multi
    def z2020(self):
        self.run_years(2020) 

    @api.multi
    def z2021(self):
        self.run_years(2021) 
    
    @api.multi
    def total_amount(self):
        '''
            Боломжит үлдэгдэл шалгах
        '''       
        for purchase in self:
            if purchase.project_id:
                
                if purchase.project_id.budgeted_line_ids:
                    total = 0
                    for line in purchase.project_id.budgeted_line_ids:
                        if line.total_possible_balance:
                            if line.total_possible_balance < purchase.amount:
                                raise UserError(_(u'Шаардахын  дүн боломжит үлдэгдэлээс хэтэрсэн байна'))
                        
                        if line.total_amount_of_purchase_requisition == 0:
                            total = purchase.amount
                        else:
                            total = line.total_amount_of_purchase_requisition + purchase.amount

                        line.sudo().write({'total_amount_of_purchase_requisition':total})
        
   
        
    
    @api.multi
    def run_years(self,year):
    
        date_str = str(year) + '-01-01'
        date_str_next = str(year+1) + '-01-01' 
        res = {}

        requisition_ids = self.env['purchase.requisition'].search([('create_date','>=',date_str),('create_date','<',date_str_next)])
        for req in requisition_ids:
            amount = amount_total=0.0
            control_amount = 0

            for line in req.line_ids:
                amount_total+= line.amount
                amount += line.allowed_amount
            if req.control_budget_id:
                control_amount = req.equipment_amount + req.carriage_amount+req.postage_amount +req.other_amount
            req.amount = amount_total+control_amount
            req.allowed_amount = amount +control_amount




    @api.one
    @api.depends('line_ids.amount','line_ids.allowed_amount','line_ids.allowed_qty','line_ids.product_price')
    def _requisition_amount(self):
        res = {}
        amount = amount_total=0.0
        control_amount = 0
        for req in self:
            for line in req.line_ids:
                amount_total+= line.amount
                amount += line.allowed_amount
            if req.control_budget_id:
                control_amount = req.equipment_amount + req.carriage_amount+req.postage_amount +req.other_amount
            req.amount = amount_total+control_amount
            req.allowed_amount = amount +control_amount


    @api.one        
    def _is_sent_user(self):
        if  self.user_id.id ==self._uid:
            
            self.is_sent_user= True
             
    @api.multi
    def _set_sector(self):
            department_ids = self.env['hr.department'].get_sector(self.env.user.department_id.id)
            if department_ids :
                return department_ids
            else :      
              return self.env.user.department_id.id
    @api.multi          
    def _set_department(self):
        
        if self.env.user.department_id.id:
            
            return self.env.user.department_id.id
        else:
            raise osv.except_osv(_('Warning!'), _('You don\'t have related employee. Please contact administrator.'))
    
    # sector_id = fields.Many2one('hr.department', string='Sector'), #Салбар

    @api.multi
    def _set_request(self):
        config_id = False
        if self.product_list_type == 'normalized':
            config_id = self.env['request.config'].search([('process','=','purchase.requisition'),('is_purchase_normalized','=',True)])
            if not config_id:
                raise osv.except_osv(_('Warning !'), _(u"Нормчилогдсон барааны урсгал хийгдээгүй байна. Систем админтайгаа холбогдоно уу"))
        else:
            config_id = self.env['request.config'].search([('department_ids','=',self.env.user.department_id.id),('process','=','purchase.requisition')])
            if not config_id:
                raise osv.except_osv(_('Warning !'), _(u"Хэлтэсийн дээр урсгал %s тохиргоо хийгдээгүй байна. Систем админтайгаа холбогдоно уу")%(self.env.user.department_id.name))
        return config_id[0]


    def _get_number_of_days(self, date_from, date_to):

        """Returns a float equals to the timedelta between two dates given as string."""

        DATE_FORMAT = "%Y-%m-%d"
        from_dt = datetime.strptime(date_from, DATE_FORMAT)
        self.env.cr.execute("SELECT count(*) AS count_days_no_weekend FROM   generate_series(timestamp %s, timestamp %s, interval '1 day') the_day WHERE  extract('ISODOW' FROM the_day) < 6",(from_dt, date_to))
        work_day = self.env.cr.fetchone()[0]
        self.env.cr.execute("select count(id) from hr_public_holiday where extract(ISODOW from days_date) not in (6,7) and days_date between %s and %s",(from_dt,date_to))
        public_holidays = self.env.cr.fetchone()[0]
        return work_day - public_holidays

    def date_by_adding_business_days(self,from_date, add_days):

        days = datetime.strptime(from_date, "%Y-%m-%d")
        work_day = 0
        while 60 > work_day:
            day = days + timedelta(days=work_day)
            if add_days + 1 == self._get_number_of_days(from_date, day) :
                return day
            work_day += 1
    
    @api.multi
    def _is_new_requisition(self):
        if datetime.now() > datetime.strptime('2022-09-29','%Y-%m-%d'):
            return True
        else:
            return False

    is_in_control_budget = fields.Boolean(string="Is in control budget" ,default=False)
    payment_request_id = fields.Many2one('payment.request',string='Payment request', index=True,rack_visibility='onchange') #Төлбөрийн хүсэлт
    
    request_id=fields.Many2one('request.config',track_visibility='onchange',string='Workflow config',domain="[('department_ids','=',department_id),('process','=','purchase.requisition')]",default = _set_request) #Урсгал тохиргоо
    is_sent_user = fields.Boolean(string='Is sent user', compute= _is_sent_user, default= False)
    is_in_sent = fields.Boolean(string='Is in sent', compute= _is_in_sent, default=False)
    is_in_approve = fields.Boolean(string='Is in sent' ,compute= _is_in_approve, default=False)
    is_in_confirm = fields.Boolean(string='Is in sent', compute= _is_in_confirm, default=False)
    is_in_verify = fields.Boolean(string='Is in sent',compute= _is_in_verify, default=False)
    # is_in_sent_supply = fields.Boolean(string='Is in sent to supply',compute= _is_in_sent_supply, default=False)
    # is_in_fullfil = fields.Boolean(string='Is in fulfill',compute= _is_in_fullfil, default=False)
    is_purchase = fields.Boolean(string='Is in fulfill',default=False)
    # is_in_fullfil = fields.Boolean(string='Is in sent',compute= _is_in_fullfil, default=False)
    is_in_close = fields.Boolean(string='Check groups')
    is_in_group = fields.Boolean(string='Is in groups')
    confirm_user_ids = fields.Many2many(comodel_name='res.users',relation='purhase_requisition_res_users_rel', string='Confirmed user') #Батлах хэрэглэгчид
    change_color = fields.Selection([('red','Red'),('grey','Grey')], string="Change color", default='grey', compute = _color_change)
    # user_id = fields.Many2one('res.users', u'Захиал'),
    auto_change_state = fields.Boolean(string='Is in sent',compute= _auto_change_statee, default=False)
    # amount_total = fields.Float(string='Amount',compute =_requisition_amount, default= 0), 
    amount = fields.Float(string='Confirmed amount',track_visibility='onchange', compute=_requisition_amount, store=True) #Батлагдсан дүн
    allowed_amount = fields.Float('Confirmed total amount', track_visibility='onchange',compute=_requisition_amount, store=True) #Зөвшөөрөгдсөн нийт дүн
    exceed_days = fields.Float('Exceed day',track_visibility='onchange',compute = _color_change)
    exceed_days_1 = fields.Float('Хэтэрсэн хоног',track_visibility='onchange',store=True, compute = _exceed_days_1 )
    ordering_date_new = fields.Date(string='Шаардахын эцсийн хугацаа',track_visibility='onchange',store=True ,compute = _ordering_date_new)
    priority = fields.Selection([('general','General'),('urgent','Urgent')], string='Priority',track_visibility='onchange', default='general')
    priority_id = fields.Many2one('purchase.priority',string='Purchase priority',track_visibility='onchange')
    project_id = fields.Many2one('project.project', string='Project',track_visibility='onchange',)
    helpdesk_id = fields.Many2one('crm.helpdesk', string='Ticket',track_visibility='onchange',) #Тиккет
    tender_id = fields.Many2one('tender.tender', string='Tender',index=True,track_visibility='onchange',) #Тендер
    task_id = fields.Many2one('project.task', string='Task',   index=True,  domain="[('project_id','=',project_id)]",track_visibility='onchange', )
    contract_id = fields.Many2one('contract.management', string="Contract",index=True, domain ="[('state','in',['confirmed','warranty','certified'])]",track_visibility='onchange',)
    control_budget_id = fields.Many2one('control.budget', stirng='Control budget' ,domain="[('project_id','=',project_id),('state','=','done')]",track_visibility='onchange',)
    sector_id = fields.Many2one('hr.department', string='Sector',index=True, domain="[('company_id','=',company_id),('is_sector','!=',False)]" ,track_visibility='onchange',default= _set_sector) #Салбар
    control_selection = fields.Selection([('material','Material expense'),('labor','Labor expense'),('equipment','Equipment expense'), 
        ('carriage','Carriage expense'),('postage','Direct expense'),('other','Other')], string="Expense type",track_visibility='onchange',) 
    #Материалын зардал Ажиллах хүчний зардал Машин механизмын зардал Тээврийн зардал Шууд зардал Бусад Зардлын төрөл

    # partner_id = fields.Many2one('res.partner',string=u'Хүлээн авах байршил',required=False, default= _set_partner),
    location = fields.Char(string='Хүлээн авах байршил',track_visibility='onchange',)
    confirmed_date = fields.Date(string='Confirmed date',track_visibility='onchange',) #Батлагдсан огноо
    confirm_history_lines = fields.One2many('purchase.confirm.history.lines','requisition_id', string='Confirm history lines')
    supply_date = fields.Date(string='Supply date', write=[
        ("nomin_purchase_requisition.group_supply_import_manager"),
        ("nomin_purchase_requisition.group_haaa_head"),
        ("nomin_purchase_requisition.group_haaa_director")])

    state = fields.Selection(STATE_SELECTION,string='Status', track_visibility='onchange', required=True)
    department_id = fields.Many2one('hr.department',string='Department',track_visibility='onchange',default= _set_department)
    active_sequence = fields.Integer(string='Active sequence',default=1)
    comment = fields.Text(string='Бараа материалын зориулалт',track_visibility='onchange')
    warehouse_id = fields.Many2one('stock.warehouse',string='Warehouse', track_visibility='onchange')
    history_lines = fields.One2many('request.history','requisition_id', 'History',  readonly=True)
    state_history_ids = fields.One2many('purchase.requisition.state.history', 'requisition_id', string="History", readonly=True)
    verify_code = fields.Char(string="Verification code") 
    qr_code = fields.Binary("Signature Image", attachment=True) 
    goods_description = fields.Text(string='Бараа материалын тодорхойлолт',track_visibility='onchange')
    source_of_goods = fields.Text(string='Бараа материалыг нийлүүлэх боломжтой суваг',track_visibility='onchange')
    line_ids_1 = fields.One2many('purchase.requisition.line' ,'requisition_id', 'Products to Purchase' )
    product_list_type = fields.Selection([('normalized','Нормчилогдсон бараа'),('new_set','Шинэ дэлгүүрийн багц')], string='Барааны төрөл',track_visibility='onchange') 
    product_list = fields.Many2one('standart.product.list', string='Барааны төрлийн нэр') 
    is_new_requisition = fields.Boolean(string='is old',default =_is_new_requisition)

    @api.onchange('product_list_type')
    def onchange_department_id(self):
        if self.product_list_type:
            self.product_list = None
            if self.product_list_type == 'normalized':
                config_id = self.env['request.config'].search([('process','=','purchase.requisition'),('is_purchase_normalized','=',True)])
                if not config_id:
                    raise osv.except_osv(_('Warning !'), _(u"Нормчилогдсон барааны урсгал хийгдээгүй байна. Систем админтайгаа холбогдоно уу"))
                else:
                    self.request_id = config_id[0]
            else:
                config_id = self.env['request.config'].search([('department_ids','=',self.env.user.department_id.id),('process','=','purchase.requisition')])
                if not config_id:
                    raise osv.except_osv(_('Warning !'), _(u"Хэлтэсийн дээр урсгал %s тохиргоо хийгдээгүй байна. Систем админтайгаа холбогдоно уу")%(self.env.user.department_id.name))
                else:
                    self.request_id = config_id[0]

            return {
                'domain':{
                    'product_list':[('product_type','=',self.product_list_type),('state','=','confirmed')],
                }
            }
        
    @api.onchange('product_list')
    def onchange_product_lits(self):
        self.line_ids = None
        new_lines = []
        if self.product_list_type and self.product_list_type == 'new_set':
            for line in self.product_list.sudo().standart_product_ids:
                if line.sudo().product_product_id.product_tmpl_id.active == False:
                    raise UserError(_(u'"%s" шинэ дэлгүүрийн багц бараанд "%s" бараа архивлагдсан байна.'%(self.product_list.name,line.product_product_id.name)))

                vals = {
                    'product_id': line.product_product_id.id,
                    'product_mark': line.product_product_id.product_mark,
                    'product_price': line.product_product_id.cost_price,
                    'deliver_product_id': line.product_product_id.id,
                    'supplied_price': line.product_product_id.cost_price,
                    'supplied_quantity': 1,
                    'is_new_requisition': True,
                    'product_desc': line.product_product_id.name,
                    'category_id': line.product_product_id.categ_id.id,
                }
                line = self.env['purchase.requisition.line'].create(vals)
                new_lines.append(line.id)
            self.line_ids = [(6,0, new_lines)]


    @api.multi
    def action_get_val(self):
        for obj in self:
            purchase_obj = obj.env['purchase.requisition'].search([('state','=','assigned')])
            for item in purchase_obj:
                item._ordering_date_new()
                item._exceed_days_1()

    @api.multi
    def _set_company(self):
        
        if self.env.user.company_id:           
            return self.env.user.company_id.id
        else:
            raise osv.except_osv(_('Warning!'), _('You don\'t have related employee. Please contact administrator.'))
        return None

    @api.multi
    def _get_picking_in(self):
        picking_obj = self.env['stock.picking.type']
        employee_id = self.env['hr.employee'].search([('user_id','=',self._uid)])[0]
        company_id = False
        company_name = False
        department_id = False
        department_name = False
        if employee_id:
            company_id = employee_id.department_id.company_id.id
            company_name = employee_id.department_id.company_id.name
            department_id = employee_id.department_id.id
         
        # sector_id = self.pool.get('hr.department').get_sector(self,cr,[], department_id)
        sector_id = self.env['hr.department'].get_sector(department_id) 
        dep = self.env['hr.department'].browse(sector_id)
        department_name = dep.name

        picking_ids = picking_obj.sudo().search([('code','=','incoming'),('warehouse_id.department_of_id','=',sector_id)])
        if not picking_ids:
             raise osv.except_osv(_('Warning !'), _(u"%s салбар агуулах үүсгэнэ үү!",)%(department_name))
        return picking_ids[0]
    _defaults = {
    
        'company_id':_set_company,
        'name':'New',
        'picking_type_id': _get_picking_in,
    }
 

    @api.onchange('picking_type_id')
    def onchange_picking_type(self):
        self.warehouse_id = self.picking_type_id.sudo().warehouse_id.id



    @api.multi
    def get_request(self, department_id):
        config_id = False
        config_id = self.env['request.config'].search([('department_ids','=',department_id),('process','=','purchase.requisition')])
        return config_id[0]
 
    @api.model
    def create(self,vals):

        
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order.requisition') or '/'
        return super(purchase_requisition,self).create(vals)
    
    @api.one
    def copy(self, default=None):
        is_true = True
        if not self.is_new_requisition:
            is_true = False
        for line in self.line_ids:
            if not line.is_new_requisition:
                is_true = False
        if not is_true:
            raise UserError(_(u'Хуучин бараатай шаардах тул дахин шинээр худалдан авалтын шаардах үүсгэнэ үү'))
        if default is None:
            default = {}    
    
        default.update({ 'active_sequence':1,
                                        'request_id':False,
                                        'tender_id':False,
                                        'confirm_user_ids':[(5)]})
                    
        return super(purchase_requisition, self).copy(default=default)

    @api.onchange('department_id')
    def onchange_department(self):
        self.employee_id = False
        # self.request_id = self.get_request(self.department_id.id)
        user_id = self.env['res.users'].sudo().search([('id','=',self._uid)])
        self.sector_id = self.env['hr.department'].get_sector(self.env.user.department_id.id)
        self.company_id = self.department_id.company_id
        department_ids = []
        for dep in user_id.purchase_allowed_departments:
            department_ids.extend(self.env['hr.department'].search([('id','child_of',dep.id)]).ids)
            
        return {'domain':{
                          'department_id':[('id','in',department_ids)]                          
                          },
                          }        


    @api.onchange('project_id')
    def onchange_project(self):
        self.task_id = False
        self.control_budget_id = False

    @api.onchange('task_id')
    def onchange_task(self):

        self.control_budget_id = False

    @api.onchange('control_budget_id')
    def onchange_control_budget_id(self):
        for purchase in self:
            purchase.material_amount = purchase.control_budget_id.material_cost
            purchase.equipment_amount = purchase.control_budget_id.equipment_cost
            purchase.carriage_amount = purchase.control_budget_id.carriage_cost
            purchase.postage_amount = purchase.control_budget_id.postage_cost
            purchase.other_amount = purchase.control_budget_id.other_cost


    @api.multi
    def action_purchase_flow(self):
        self.write({'is_purchase':True})
        self.write_state('confirmed')

    @api.multi
    def get_possible_users(self, sel_user_ids):
        department_ids = []
        user_ids = self.env['res.users'].browse(sel_user_ids)
        possible_user_ids = []
        for this in self:
            for user in user_ids:
                department_ids = self.env['hr.department'].search([('id','in',user.purchase_allowed_departments.ids)])
                user_dep_set = set(department_ids.ids)
                if list(user_dep_set.intersection([this.department_id.id])):
                    possible_user_ids.append(user.id)
        return possible_user_ids

    @api.multi
    def get_confirm_users(self,state):

        purchase_line = self.env['request.config.purchase.line']
        line_ids = purchase_line.search([('request_id','=',self.request_id.id),('state','=','confirmed')])
        sel_user_ids = []
        confirm_user_ids = []
        his_user_ids = []
        for line in line_ids:
            # if self.amount <= line.limit or line.limit ==0:
                if line.type == 'group':
                    group = line.group_id
                    # for group in groups.browse(group_id):
                    for user in group.users:
                        sel_user_ids.append( user.id)
                elif line.type == 'fixed':
                    sel_user_ids.append(line.user_id.id)
                elif line.type == 'depart':
                    user_id = self.department_id.user_id.id
                    if user_id :
                        sel_user_ids.append( user_id)
                    else :
                        raise osv.except_osv(_('Warning !'), _(u"Хэлтэсийн менежер дээр холбоотой хэрэглэгч талбар хоосон байна."))
        
        for his in self.confirm_history_lines:
            his_user_ids.append(his.user_id.id)
        
        group_user_ids = self.group_users1()
        user_ids = self.get_possible_users( sel_user_ids)
        if group_user_ids:
            user_ids.extend(group_user_ids)
        for sel in user_ids :                        
            # if self.state in ['','','']
                if sel not in his_user_ids:
                    confirm_user_ids.append(sel)

        return confirm_user_ids

    @api.multi
    def action_send_manager(self):
        is_product_null = False
        for requisition in self:
            for line in requisition.line_ids:
                if not line.product_id:
                        is_product_null = True
            if is_product_null==False:
                self.send_request()  
            else :    
                raise UserError(_(u'Тодорхой бус барааны мэдээллийг оруулж өгнө үү.!'))
    
    @api.multi
    def action_update(self):
        query="select B.id as id,D.assign_categ_id as assign from purchase_requisition A inner join purchase_requisition_line B on A.id =B.requisition_id \
         left join product_product C ON C.id=B.product_id left join product_template D on D.id=C.product_tmpl_id \
         where A.state in ('verified','confirmed','next_confirm_user','sent') and D.assign_categ_id!=B.assign_cat"
        self.env.cr.execute(query)
        dictfetchall = self.env.cr.dictfetchall()        
        for dic in dictfetchall:            
            
            self.env.cr.execute("select B.user_id from assign_category_purchase_category_config_rel A inner join purchase_category_config B \
                on A.purchase_category_config_id=B.id where A.assign_category_id=%s limit 1"%(dic['assign']))
            fetched = self.env.cr.fetchone()
            _logger.info('\n\nFETCH %s FETCH '%(fetched[0]))   
            if fetched:          
                _logger.info('\n\nUPDATE %s, %s , %s UPDATE '%(dic['assign'],fetched[0],dic['id']))      
                if dic['id']==38988:
                    _logger.info('\n\nUPDATE DDDDDDDDDDDDDDDDD  %s, %s , %s UPDATE DDDDDDDDDDD'%(dic['assign'],fetched[0],dic['id']))      
                self.env.cr.execute("update purchase_requisition_line set assign_cat=%s , buyer=%s where id=%s"%(dic['assign'],fetched[0],dic['id']))
                        
        
    #Хангамж руу илгээх
    # @api.multi
    # def action_sent_to_supply(self):
        
    #     # if self.priority =='urgent':
    #     #     days = 5
    #     # else:
    #     #     days = 3
        
    #     if self.state =='confirmed':
    #         self.write({'state': 'sent_to_supply', 'active_sequence':self.active_sequence})
    #         self.line_ids.write({'state':'sent_to_supply'})
    #         notif_groups = self.env['ir.model.data'].get_object_reference( 'nomin_purchase_requisition', 'group_haaa_director')[1]
            
    #         next_user_ids = self.env['res.users'].search([('groups_id','in',[notif_groups])])
    #         if not next_user_ids:
    #               raise osv.except_osv(_(u'Анхааруулга'), _(u'Хангамж аж ахуйн албаны дарга грүпд хэрэглэгч нар алга байна.')) 

    #         self.action_send_email('sent_to_supply',next_user_ids.ids)
    #         history_obj = self.env['request.history']
    #         history_obj.create(
    #                 {'requisition_id': self.id,
    #                 'user_id': self._uid,
    #                 'date': time.strftime('%Y-%m-%d %H:%M:%S'),
    #                 'type': 'sent_to_supply',
    #                 }
    #                 )


    @api.multi
    def action_direct_purchase(self):
        mod_obj = self.env['ir.model.data']
        res = mod_obj.get_object_reference('nomin_purchase_requisition', 'action_create_purchase_order')
        return {
            'name': 'Note',
            'view_type': 'form',
            'view_mode': 'form',
            #'view_id': [res and res[1] or False],
            'res_model': 'create.purchase.order.wizard',
            'context': self._context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            #'res_id': ids[0]  or False,
        }
    #Баталсан төлөвт оруулах
    # @api.multi
    # def action_set_confirm(self):
        
    #     self.check_user_limit()
    #     vals = {
    #             'state':'confirmed',
    #             'active_sequence':99,
    #             }

    #     self.write(vals)
    #     self.action_sent_to_supply()
    @api.multi
    def action_reject(self):
        for purchase in self:
            balance = 0

            if purchase.project_id.budgeted_line_ids:
                for line in purchase.project_id.budgeted_line_ids:
                    balance =  line.total_amount_of_purchase_requisition - purchase.amount
                    line.sudo().write({'total_amount_of_purchase_requisition':balance})

        
        return {
            'name': 'Note',
            'view_type': 'form',
            'view_mode': 'form',
            #'view_id': [res and res[1] or False],
            'res_model': 'purchase.requisition.cancel.note',
            'context': self._context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            #'res_id': ids[0]  or False,
        }
    @api.multi
    def action_cancel(self):
        
        return {
            'name': 'Note',
            'view_type': 'form',
            'view_mode': 'form',
            #'view_id': [res and res[1] or False],
            'res_model': 'purchase.requisition.cancel.note',
            'context': self._context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            #'res_id': ids[0]  or False,
        }
    @api.multi
    def action_set_confirm(self):
        self.write({'state':'confirmed'})

    @api.multi
    def action_return_product(self):
        return {
        'name': u'Тэмдэглэл',
        'view_type': 'form',
        'view_mode': 'form',
        #'view_id': [res and res[1] or False],
        'res_model': 'action.create.tender.request.return',
        'context': self._context,
        'type': 'ir.actions.act_window',
        'nodestroy': True,
        'target': 'new',
        #'res_id': ids[0]  or False,
        }

    @api.multi
    def action_tender_request(self):
        return {
        'type': 'ir.actions.act_window',
        'name': _('Тендер зарлуулах хүсэлт'),
        'res_model': 'action.create.tender.request',
        'view_type' : 'form',
        'view_mode' : 'form',
        'context'   :self._context,      
        'nodestroy': True,
        'target': 'new',           
        }
    @api.multi
    def action_approve_purchase(self):
        
        
        sequence = self.active_sequence+1
        self.write({'state':'approved','active_sequence':sequence})

    @api.multi
    def check_user_limit(self):
        month_obj = self.env['purchase.limit.month']
        employee = self.env['hr.employee']
        job_config_line  = self.env['job.position.limit.line']
        limit_id = month_obj.search([('employee_id.user_id','=',self._uid)])
        employee_id = employee.search([('user_id','=',self._uid)])[0]
        if not limit_id :
            if employee_id.job_id:
                    line_id = job_config_line.search([('job_id','=',employee_id.job_id.id)])[0]
                    if not line_id:
                      raise osv.except_osv(_(u'Анхааруулга'), _(u'Таны албан тушаал дээр худалдан авалтын лимит тохируулдаагүй байна.'))                    
                    data = {
                                'employee_id':employee_id.id,
                                'purchase_month_limit':line_id.purchase_month_limit
                        }

            limit_id = month_obj.create( data)
        external_amount =0
        internal_amount =0
        
        internal_amount = limit_id.purchase_month_limit
        vals = {}
        for req in self:
                vals = {
                        'purchase_month_limit':internal_amount-req.amount,
                        }
        limit_id.write(vals)
    
    @api.multi
    def sap_integration(self):


        
        # self_date = datetime.strptime(self.date, "%Y-%m-%d")
        # today = datetime.today()
        # reserve1 = 'AG%s%s%s%s' % (self_date.year, self_date.strftime('%m'), self_date.strftime('%d'), self.id)
        # url = "http://172.21.32.9:8000/sap/bc/srt/wsdl/flv_10002A111AD1/bndg_url/sap/bc/srt/rfc/sap/znmws001/500/znmws001/znmws001?sap-client=500"
        notification_id = self.env['proactive.notification'].sudo().search([('model','=','sap'),('code','=','sap_pr_create')])
        if not notification_id:
            raise UserError("No integration configured for 'sap_pr_create'")
        # url = "http://172.21.32.9:8000/sap/bc/srt/wsdl/flv_10002A111AD1/bndg_url/sap/bc/srt/rfc/sap/znmmmws_pr_create/600/znmmmws_pr_create/znmmmws_pr_create?sap-client=600"
        url = notification_id.server_ip

        for purchase in self:
            EtOutput = {
            }

            IInfo = {
                    'Source': 'ODOO',
                    'Destination': 'SAP',
                    'Idate': datetime.today().strftime('%Y-%m-%d'),
                    'Itime': datetime.today().strftime('%H:%M:%S'),
		            }
                    

            

            ItAnln1 = {
                    'item':[{
                            'Bednr':purchase.name,
                            'Bnfpo':'10',
                            'Anln1':'11000000000'
                            }]
                        }



            items = []
            category = 0
            for line in purchase.line_ids:
                if line.sap_account_assignment_category == 'asset':
                    category = 'A'
                else:
                    category = 'K'
                print '\n\n\n category:' ,category 
                item = {
                    'Bsart': 'NB',
                    'Banfn': '0010000007',
                    'Loekz': '',
                    'Bnfpo': '60',
                    'Knttp': category,
                    'Matnr': 1000003,
                    'Menge': '90',
                    'Meins': 'PC',
                    'Werks': purchase.department_id.plant_code,
                    'Lfdat': line.product_delivery_date,
                    'Bednr': purchase.name,
                    'Kostl': '3200110001',
                    


                    'Reserve1': '',
                    'Reserve2': '',
                    'Reserve3': '',
                    'Reserve4': '',
                    'Reserve5': '',
                    'Reserve6': '',
                    'Reserve7': '',
                    'Reserve8': '',
                    'Reserve9': '',
                    'Reserve10': '',
                    'Reserve11': '',
                    'Reserve12': '',
                    'Reserve13': '',
                    'Reserve14': '',
                    'Reserve15': '',
                    'Reserve16': '',
                    'Reserve17': '',
                    'Reserve18': '',
                    'Reserve19': '',
                    'Reserve20': '',
                }


            items.append(item)
            ItInput = {
                'item': items
            }
            print 



        
        session = Session()
        session.auth = HTTPBasicAuth("ws_user", "Ws_user123")
        client = Client(url, transport=Transport(session=session))
        response = client.service.ZnmmmfmPrCreate(EtOutput,IInfo,ItAnln1, ItInput)
        print "\n\n",response,"\n\n"




    @api.multi
    def action_send(self):
        #Шаардах хүсэгч бараа сонгоод илгээх
        is_product_null = False
        for requisition in self: 
            requisition.total_amount()
            if requisition.line_ids:
                for line in requisition.line_ids:

                    if not line.product_id:
                        is_product_null = True
                    
                    if line.product_id:
                        if line.product_price ==0:
                            raise osv.except_osv(_(u'Анхааруулга'), _(u'%s барааны үнэ мөр дээр 0 байна.')%line.product_id.name)
                        if line.product_qty ==0:
                            raise osv.except_osv(_(u'Анхааруулга'), _(u'%s барааны тоо хэмжээ 0 байна.')%line.product_id.name)
                        if not self.is_new_requisition:
                            if self.control_budget_id:
                                if line.product_id.assign_categ_id:
                                    if not line.product_id.assign_categ_id==line.assign_cat:
                                        if line.product_id.assign_categ_id:
                                            categ_ids = line.find_buyer(line.product_id.assign_categ_id.id,self.department_id)
                                            if not categ_ids:
                                                raise UserError('"%s"-н "%s" ангилалд харгалзах худалдан авалтын ажилтан тохируулагдаагүй байна. Худалдан авалтын ахлах менежерт хандаж тохиргоогоо хийлгэнэ үү.'%(self.department_id.name, line.product_id.assign_categ_id.name))
                                            line.write({'buyer':categ_ids[0].user_id.id,'assign_cat':line.product_id.assign_categ_id.id}) 
                                        else:
                                            categ_ids = line.find_buyer(line.assign_cat.id,self.department_id)
                                            if not categ_ids:
                                                raise UserError('"%s"-н "%s" ангилалд харгалзах худалдан авалтын ажилтан тохируулагдаагүй байна. Худалдан авалтын ахлах менежерт хандаж тохиргоогоо хийлгэнэ үү.'%(self.department_id.name, line.assign_cat.name))
                                            line.write({'buyer':categ_ids[0].user_id.id})
                            else:
                                categ_ids = line.find_buyer(line.assign_cat.id,self.department_id)
                                if not categ_ids:
                                    raise UserError('"%s"-н "%s" ангилалд харгалзах худалдан авалтын ажилтан тохируулагдаагүй байна. Худалдан авалтын ахлах менежерт хандаж тохиргоогоо хийлгэнэ үү.'%(self.department_id.name, line.assign_cat.name))
                                line.write({'buyer':categ_ids[0].user_id.id})
                        else:
                            if self.control_budget_id:
                                if line.product_id.categ_id:
                                    if not line.product_id.categ_id==line.category_id:
                                        if line.product_id.categ_id:
                                            categ_ids = line.find_buyer(line.product_id.categ_id.id,self.department_id)
                                            if not categ_ids:
                                                raise UserError('"%s"-н "%s" ангилалд харгалзах худалдан авалтын ажилтан тохируулагдаагүй байна. Худалдан авалтын ахлах менежерт хандаж тохиргоогоо хийлгэнэ үү.'%(self.department_id.name, line.product_id.categ_id.name))
                                            line.write({'buyer':categ_ids[0].user_id.id,'category_id':line.product_id.categ_id.id}) 
                                        else:
                                            categ_ids = line.find_buyer(line.category_id.id,self.department_id)
                                            if not categ_ids:
                                                raise UserError('"%s"-н "%s" ангилалд харгалзах худалдан авалтын ажилтан тохируулагдаагүй байна. Худалдан авалтын ахлах менежерт хандаж тохиргоогоо хийлгэнэ үү.'%(self.department_id.name, line.category_id.name))
                                            line.write({'buyer':categ_ids[0].user_id.id})
                            else:
                                categ_ids = line.find_buyer(line.category_id.id,self.department_id)
                                if not categ_ids:
                                    raise UserError('"%s"-н "%s" ангилалд харгалзах худалдан авалтын ажилтан тохируулагдаагүй байна. Худалдан авалтын ахлах менежерт хандаж тохиргоогоо хийлгэнэ үү.'%(self.department_id.name, line.category_id.name))
                                line.write({'buyer':categ_ids[0].user_id.id})
                    comparison_employee = line.find_comparison_employee(line.category_id, line.allowed_amount)
                        
                    if not line.schedule_date:
                       line.write({'schedule_date':requisition.schedule_date})
                if is_product_null==False:
                    self.send_request()
                else:
                    self.write({'state':'sent_to_supply_manager'})
                    self.env['request.history'].create({'requisition_id': requisition.id,
                'user_id': self._uid,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'type': 'sent_to_supply_manager',
                })


                for line in requisition.line_ids:
                    if not line.product_id:
                        line.write({'state':'sent_to_supply_manager'})
                        comparison_employee = line.find_comparison_employee(line.category_id)
                        line.buyer = None
                    else:
                        line.write({'state':'sent'})
            else:
                raise osv.except_osv(_(u'Анхааруулга'), _(u'Та шаардах гэж буй бараагаа сонгoно уу.'))

        if not self.verify_code and not self.qr_code:
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
                self.write({'qr_code':image.encode('base64'),'verify_code':qr_verify})
        
        self._requisition_amount()



    @api.multi
    def action_create_tender(self):
        tender_obj = self.env['tender.tender']
        tender_line_obj = self.env['tender.line']
        vasl={}
        for req in self:
            values = {
            'department_id':req.department_id.id,
            'sector_id':req.sector_id.id,
            'user_id':req.user_id.id,
            'ordering_date':req.ordering_date,
            'requisition_id':req.id,
            'project_id':req.project_id.id if req.project_id else False,
            # 'work_task_id':req.task_id.id if req.task_id else False,
            'control_budget_id': req.control_budget_id.id if req.control_budget_id else False,
            # 'work_graph_id': req.task_id.id if req.task_id else False,
            }
            tender_id = tender_obj.sudo().create(values)
            for line in req.line_ids:
                tender_line_obj.sudo().create( {
                'product_id': line.product_id.id,
                'product_qty': line.product_qty,
                'product_uom_id':line.product_id.uom_id.id,
                'schedule_date': req.schedule_date,
                'tender_id': tender_id.id,
                })
        vals={'state':'tender_created','tender_id':tender_id.id,'active_sequence':99}
        self.write(vals)

    @api.multi
    def action_payment_request (self):
        model_obj = self.env['ir.model.data']
        # res = mod_obj.get_object_reference('nomin_purchase_requisition', 'action_create_purchase_order')
        result = model_obj._get_id('nomin_budget', 'payment_request_form')
        view_id = model_obj.browse(result).res_id

        employee_id = self.env['hr.employee'].sudo().search([('user_id','=',self.user_id.id)])
        vals = {
                'user_id':self.user_id.id,
                'department_id':self.department_id.id,
                'sector_id':self.sector_id.id,
                'receiving_payment_partner_id':employee_id.address_home_id.id,
                'transaction_name': u'Худалдан авалтын шаардахын дугаар:'+ self.name or '?',
                'requisition_id':self.id,
        }
        request_id = self.env['payment.request'].create(vals)
        self.env['payment.request.line'].create({
                                                  'name': u'Худалдан авалтын шаардахын дугаар:'+ self.name or '?',
                                                    'amount': self.allowed_amount,
                                                    # 'amount_currency':amount_currency,
                                                    # 'move_line_id': line.id,
                                                    'parent_id':request_id.id,
                                                    'is_payment': False,
                                                    'sector_id':request_id.sector_id.id,
                                                    # 'account_id':line.account_id.id,
                                                    # 'state':payment.state,
                                                    # 'cashflow_account_id':cashflow_account_id,
                                                    'partner_id':employee_id.partner_id.id,
                                                    
                                                    # 'receiving_payment_account_id':payment.receiving_payment_account_id.id,
                                                    # 'currency_id':payment.currency_id.id,
                                                    # 'transaction_currency_id':payment.transaction_currency_id.id,
                                                    # 'currency_rate':payment.currency_rate,
                                                    # 'is_other_currency':payment.is_other_currency,
                                                     # 'tax_id':payment.tax_id.id if payment.tax_id else False

                                                    }
                                                 )
        self.write({'payment_request_id':request_id.id})
        # self.action_send_email('payment_request', [self.user_id.id])
        return {
                     'type': 'ir.actions.act_window',
                     'name': _('Create payment request'),
                     'res_model': 'payment.request',
                     'view_type' : 'tree',
                     'view_mode' : 'form',
                     'search_view_id' : view_id,
                     'res_id':request_id.id,
                     'target' : 'current',
                     'nodestroy' : True,
                }

    
    @api.multi
    def action_approve(self):
        self.change_state()


    @api.multi
    def action_confirm(self):

        if not self.verify_code and not self.qr_code:
            qr_verify = random_generator()
            path = os.path.abspath("/mnt/data_new/master/empire/odoo_ext/nomin_purchase_requisition/data/")	
            # path = os.path.abspath("/home/erdeneochir.sh/dev/empire/odoo_ext/nomin_purchase_requisition/data/")	
            big_code = pyqrcode.create('http://erp.nomin.mn/verification?search=%s'%(qr_verify))
            big_code.png(path+'/qrcode.png', scale=6, module_color=[0, 0, 0, 128], background=[255, 255, 255])
            img_path=path+"/qrcode.png"
            with open(img_path, 'rb') as f:
                image = f.read()
                self.write({'qr_code':image.encode('base64'),'verify_code':qr_verify})

        self.change_state()
        

    @api.multi
    def action_verify(self):
        self.change_state()
    
    @api.multi
    def find_month_limit(self):
        config_obj = self.env['job.position.limit.config']
        line_obj = self.env['job.position.limit.line']
        limit_obj = self.env['purchase.limit.month']
        today = date.today()
        employee_id = self.env['hr.employee'].sudo().search([('user_id','=',self._uid)])
        fiscalyear_id = self.env['account.fiscalyear'].search([('date_start','<=',today),('date_stop','>=',today)])
        config_id = config_obj.search([('year_id','=',fiscalyear_id.id)])
        limit = 0
        if config_id:
            if config_id.line_id:
                for line in config_id.line_id:
                    if line.job_id.id ==employee_id.job_id.id:
                        limit = line.purchase_limit_month
               
                if limit ==0:
                    raise osv.except_osv(_(u'Анхааруулга!'), _(u"Энэ жилийн албан тушаалын сарын лимит тохиргоо хийгдээгүй байна"))

            else:
                 raise osv.except_osv(_(u'Анхааруулга!'), _(u"Энэ жилийн албан тушаалын сарын лимит тохиргоо хийгдээгүй байна"))

        else:
             raise osv.except_osv(_(u'Анхааруулга!'), _(u"Энэ жилийн албан тушаалын сарын лимит тохиргоо хийгдээгүй байна"))
        return limit

    @api.multi
    def minus_month_limit(self):
        config_obj = self.env['job.position.limit.config']
        line_obj = self.env['job.position.limit.line']
        limit_obj = self.env['purchase.limit.month']
        today= date.today()
        employee_id = self.env['hr.employee'].sudo().search([('user_id','=',self._uid)])
        fiscalyear_id = self.env['account.fiscalyear'].search([('date_start','<=',today),('date_stop','>=',today)])
        config_id = config_obj.search([('year_id','=',fiscalyear_id.id)])
        limit = 0
        if config_id:
            if config_id.line_id:
                for line in config_id.line_id:
                    if line.job_id.id ==employee_id.job_id.id:
                        limit = line.purchase_limit_month
            else:
                 raise osv.except_osv(_(u'Анхааруулга!'), _(u"Энэ жилийн албан тушаалын сарын лимит тохиргоо хийгдээгүй байна"))

        period_id = self.env['account.period'].search([('date_start','<=',today),('date_stop','>=',today)])
        limit_id = self.env['purchase.limit.month'].search([('employee_id','=',employee_id.id),('month_id','=',period_id.id)])
        limit_id.write({'purchase_month_limit':limit_id.purchase_month_limit-self.allowed_amount}) 
    
    @api.multi
    def search_confirm_user_group(self):
        purchase_line = self.env['request.config.purchase.line']
        line_ids = purchase_line.search([('state','=','confirmed'),('request_id','=',self.request_id.id)])
        sequences = []
        for line in line_ids:
            for user in line.group_id.users:
                if self._uid ==user.id:
                    sequences.append(line.sequence)
                
        return sequences
    @api.multi
    def is_in_month_limit(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id','=',self._uid)])
        purchase_line = self.env['request.config.purchase.line']
        today = date.today()
        period_id = self.env['account.period'].search([('date_start','<=',today),('date_stop','>=',today)])
        limit_id = self.env['purchase.limit.month'].search([('employee_id','=',employee_id.id),('month_id','=',period_id.id)])
        limit = self.find_month_limit()
        sequences = []
        if self.is_in_confirm:
            sequences = self.search_confirm_user_group()
            line_ids = purchase_line.search([('sequence','in',sequences),('request_id','=',self.request_id.id)])
        else:
            line_ids = purchase_line.search([('sequence','=',self.active_sequence),('request_id','=',self.request_id.id)])
        if not limit_id:
                if limit!=0 :
                    limit_id = self.env['purchase.limit.month'].create({'employee_id':employee_id.id,'month_id':period_id.id,'purchase_month_limit':limit,'month_limit':limit})
                else:
                    raise osv.except_osv(_(u'Анхааруулга!'), _(u"Энэ жилийн албан тушаалын сарын лимит тохиргоо хийгдээгүй байна"))
        else:
                if limit!=0 :
                    amount =0
                    amount = limit_id.month_limit - limit_id.purchase_month_limit
                    limit_id.write({'purchase_month_limit':limit-amount,'month_limit':limit})
                else:
                    raise osv.except_osv(_(u'Анхааруулга!'), _(u"Энэ жилийн албан тушаалын сарын лимит тохиргоо хийгдээгүй байна"))
        is_true = False
        _logger.info(u'\n\n\n\n\n\n\n\n-------------------------sequences', sequences,'\n\n\n\n')
        for line in line_ids:
            if line.limit ==0.0 or line.limit >=self.allowed_amount:
                is_true = True
        if is_true:        
            if limit_id.purchase_month_limit >=self.allowed_amount:
                return True
            else:
                return False
        else:
            return False

    @api.onchange('schedule_date')
    def onschedule_date(self):
        today = datetime.strptime(time.strftime('%Y-%m-%d'), "%Y-%m-%d")
        if self.schedule_date:
            if datetime.strptime( self.schedule_date,'%Y-%m-%d') < today:
                self.schedule_date = today
#                 raise osv.except_osv(_(u'Анхааруулга'), _(u'Хүсч буй хугацаа өнөөдрөөс өмнө байж болохгүй'))
    
    
        
        
    @api.multi
    def write_state(self,state):
        today = datetime.strptime(time.strftime('%Y-%m-%d'), "%Y-%m-%d")
        
        # if state=='confirmed':
        #     purchase_line = self.env['request.config.purchase.line']
        #     line_ids = purchase_line.search([('state','=','sent_to_supply'),('request_id','=',self.request_id.id)])
        #     if line_ids:
        #         sequence = line_ids[0].sequence                
        #     else:
        #         raise osv.except_osv(_(u'Анхааруулга'), _(u'Урсгал дээр Хангамжийн урсгал хийгдээгүй байна. Системийн админтайгаа холбогдоно уу !!!.'))         
        # else:
        sequence = self.active_sequence+1
        
        if state == 'confirmed':
            self.write({'state':'confirmed'})
            self.line_ids.write({'state':'compare','confirmed_date':today})
            if not self.tender_id:
                self.write({'state':'assigned','active_sequence':sequence,'confirmed_date':today})
                # self.line_ids.write({'state':'assigned','confirmed_date':today,'date_start':time.strftime('%Y-%m-%d')})

                self.create_history('done')
            
            for line in self.line_ids:
                if not line.is_new_requisition:
                    assign_cat = line.assign_cat
                else:
                    assign_cat = line.category_id
                if not assign_cat:
                    assign_cat = line.product_id.assign_categ_id
                if line.find_comparison_employee(assign_cat, line.allowed_amount):
                    line.write({'state':'compare'})
                    line._get_comparison_date()
                else:
                    buyer = line.find_buyer(assign_cat.id, self.department_id)
                    if buyer:
                        line.write({'buyer':buyer[0].user_id.id})
                    else:
                        raise UserError('"%s"-н "%s" ангилалд харгалзах худалдан авалтын ажилтан тохируулагдаагүй байна. Худалдан авалтын ахлах менежерт хандаж тохиргоогоо хийлгэнэ үү.'%(self.department_id.name, assign_cat.name))
                    
        else:
            self.write({'state':state,'active_sequence':sequence,'confirmed_date':today})
            self.line_ids.write({'state':state,'confirmed_date':today})

        notif_groups = self.env['ir.model.data'].get_object_reference( 'nomin_purchase_requisition', 'group_purchase_decide_sent_to_supply')[1]
        
        next_user_ids = self.env['res.users'].search([('groups_id','in',[notif_groups])])
        if not next_user_ids:
              raise osv.except_osv(_(u'Анхааруулга'), _(u'Хангамж руу илгээх эсэх грүпд хэрэглэгч нар алга байна.')) 
        users = []
        for user in self.env['res.users'].search([('partner_id','in', self.message_partner_ids.ids)]):
            users.append(user.id)
#         confirm_user_ids = self.get_possible_users()
        # self.action_send_email(state,users)       
        self.create_history(state)

    @api.multi
    def change_state(self):
        purchase_line = self.env['request.config.purchase.line']
        line_ids = purchase_line.search([('sequence','=',self.active_sequence),('request_id','=',self.request_id.id)])
        total_percent = 0


        if self.is_in_confirm :
            if self.control_budget_id:
                if self.state in['draft','approved','sent_to_supply_manager','sent','verified','next_confirm_user']:
                    self.write_state('confirmed')

            elif self.is_in_month_limit():
                if self.state in['draft','approved','sent_to_supply_manager','sent','verified','next_confirm_user']:
                    self.minus_month_limit()
                    self.write_state('confirmed')
            else:
                self.send_next_request()
        else:
            for line in line_ids:
                if line.limit !=0.0:
                    if line.limit <= self.allowed_amount:
                        self.send_request()                        
                    else:
                        if self.control_budget_id:
                            if self.state in['draft','approved','sent_to_supply_manager','sent','verified','next_confirm_user']:
                                self.write_state('confirmed')
                        elif self.is_in_month_limit():
                            if self.state in['draft','approved','sent_to_supply_manager','sent','verified','next_confirm_user']:
                                self.minus_month_limit()
                                self.write_state('confirmed')
                        else:
                            self.send_request()                            
                else:
                    if self.control_budget_id:
                        if self.state in['draft','approved','sent_to_supply_manager','sent','verified','next_confirm_user']:
                            self.write_state('confirmed')
                    elif self.is_in_month_limit():
                        if self.state in['draft','approved','sent_to_supply_manager','sent','verified','next_confirm_user']:
                            self.minus_month_limit()
                            self.write_state('confirmed')
                    else:
                            self.send_request()

    @api.multi
    def action_to_assign(self):
        for line in self.line_ids:
            if not line.buyer:
                raise osv.except_osv(_('Warning !'), _(u"Шаардахын мөр дээрх Худалдан авалтын ажилтан хоосон байна"))      
        self.write({'state':'assigned'})
        self.line_ids.write({'state':'assigned'})
        next_user_ids = []
        for line in self.line_ids:
            next_user_ids.append(line.buyer.id)
    
        self.message_subscribe_users(next_user_ids)
        # self.action_send_email('assigned',next_user_ids)

    @api.multi
    def send_request(self):
        if self._context is None:
            self._context = {}
        employee_obj = self.env['hr.employee']
        history_obj = self.env['request.history']
        config_obj = self.env['request.config']
        for request in self:
            config_id = request.request_id.id
            vals = {}
            if not config_id:
                raise osv.except_osv(_('Warning !'), _("You don't have purchase requisition request configure !"))
            user = request.user_id
            next_user_ids, next_seq, next_state = config_obj.purchase_forward('purchase.requistion',request.active_sequence, request.user_id.id,config_id,request.department_id.id)
            next_user_ids1, next_seq1, next_state1 = config_obj.purchase_forward('purchase.requistion',request.active_sequence+1, request.user_id.id,config_id,request.department_id.id)
        
        # if self.state=='sent_to_supply' or self.state=='fulfil_request':
        #     next_user_ids1 = next_user_ids1
        # else:
        next_user_ids1 = self.get_possible_users(next_user_ids1)
            
        user_ids = self.group_users(request.active_sequence+1)

        if user_ids:
            next_user_ids1.extend(user_ids)
        if self._uid not in next_user_ids:
            raise osv.except_osv(_('Warning !'), _(u"Таны эрх хүрэхгүй байна."))            
        if not next_user_ids1:
            raise osv.except_osv(_('Warning !'), _(u"Дараагийн батлах хэрэглэгч олдсонгүй Таны батлах дүн хэтэрсэн эсвэл сарын батлах дүнгээс давсан байна."))            
        # if self.state=='sent_to_supply':
        #     vals.update({'state':next_state1,'active_sequence':request.active_sequence+1})
        #     self.write(vals)
        #     self.line_ids.write({'state':next_state1})
        #     self.create_history(next_state1)
        #     self.action_send_email(next_state1,next_user_ids1)

        #     return

        if next_user_ids:
            vals.update({'state':next_state,'active_sequence':request.active_sequence+1})
        else:
            raise osv.except_osv(_('Warning !'), _(u"Дараагийн батлах хэрэглэгч олдсонгүй Таны батлах дүн хэтэрсэн эсвэл сарын батлах дүнгээс давсан байна."))
            
        self.write(vals)
        self.line_ids.write({'state':next_state})
        if next_state != 'done':
            self.create_history(next_state)
        # self.action_send_email(next_state,next_user_ids1)

    @api.multi
    def group_users1 (self):
        sel_user_ids= []
        user_ids = []
        conf_line = self.env['request.config.purchase.line']
        groups = self.env['res.groups']
        config_obj = self.env['request.config']
        group_ids = []
        for request in self:
            config_id = request.request_id.id
            line_ids =conf_line.search([('state','=','confirmed'),('request_id','=',config_id)])
            if line_ids:
                for req in line_ids:
                    # if req.state == state:
                        if req.type == 'group':
                            group = req.group_id
                            group_ids.append(req.group_id.id)
                            # for group in groups.browse(group_id):
                            for user in group.users:
                                sel_user_ids.append( user.id)
                        elif req.type == 'fixed':
                            sel_user_ids.append(req.user_id.id)
                        elif req.type == 'depart':
                            user_id = self.department_id.user_id.id
                            if user_id :
                                sel_user_ids.append( user_id)
                            else :
                                raise osv.except_osv(_('Warning !'), _(u"Хэлтэсийн менежер дээр холбоотой хэрэглэгч талбар хоосон байна."))
        # user_ids = self.get_possible_users( sel_user_ids)
        
        if group_ids :
            group_id= self.env['ir.model.data'].get_object_reference('nomin_base', 'group_financial_business_chief')[1]
            if group_id in group_ids:
                group = groups.search([('id','=',group_id)])
                for user in group.users:
                    user_ids.append(user.id)
            group_id= self.env['ir.model.data'].get_object_reference('nomin_base', 'group_president')[1]
            if group_id in group_ids:        
                group = groups.search([('id','=',group_id)])
                for user in group.users:
                    user_ids.append(user.id)
            group_id= self.env['ir.model.data'].get_object_reference('nomin_base', 'group_holding_ceo')[1]
            if group_id in group_ids:        
                group = groups.search([('id','=',group_id)])
                for user in group.users:
                    user_ids.append(user.id)
        user_ids = list(set(user_ids))

        return user_ids
    @api.multi
    def group_users (self,active_sequence):
        sel_user_ids= []
        user_ids = []
        conf_line = self.env['request.config.purchase.line']
        groups = self.env['res.groups']
        config_obj = self.env['request.config']
        group_ids = []
        for request in self:
            config_id = request.request_id.id
            line_ids =conf_line.search([('sequence','=',active_sequence),('request_id','=',config_id)])
            if line_ids:
                for req in line_ids:
                    # if req.state == state:
                        if req.type == 'group':
                            group = req.group_id
                            group_ids.append(req.group_id.id)
                            # for group in groups.browse(group_id):
                            for user in group.users:
                                sel_user_ids.append( user.id)
                        elif req.type == 'fixed':
                            sel_user_ids.append(req.user_id.id)
                        elif req.type == 'depart':
                            user_id = self.department_id.user_id.id
                            if user_id :
                                sel_user_ids.append( user_id)
                            else :
                                raise osv.except_osv(_('Warning !'), _(u"Хэлтэсийн менежер дээр холбоотой хэрэглэгч талбар хоосон байна."))
        user_ids = self.get_possible_users( sel_user_ids)
        if group_ids :
            group_id= self.env['ir.model.data'].get_object_reference('nomin_base', 'group_financial_business_chief')[1]
            if group_id in group_ids:
                group = groups.search([('id','=',group_id)])
                for user in group.users:
                    user_ids.append(user.id)
            group_id= self.env['ir.model.data'].get_object_reference('nomin_base', 'group_president')[1]
            if group_id in group_ids:        
                group = groups.search([('id','=',group_id)])
                for user in group.users:
                    user_ids.append(user.id)
            group_id= self.env['ir.model.data'].get_object_reference('nomin_base', 'group_holding_ceo')[1]
            if group_id in group_ids:        
                group = groups.search([('id','=',group_id)])
                for user in group.users:
                    user_ids.append(user.id)
           
        user_ids = list(set(user_ids))
        return user_ids
    @api.multi
    def send_next_request(self):
        if self._context is None:
            self._context = {}
        employee_obj = self.env['hr.employee']
        user_ids = []
        config_obj = self.env['request.config']
        sequences = self.search_confirm_user_group()
        active_sequence = 0
        if sequences:
            for seq in sequences:
                if seq > active_sequence:
                    active_sequence =seq

        for request in self:
            config_id = request.request_id.id
            vals = {}
            if active_sequence==0:
                active_sequence = request.active_sequence,
            if not config_id:
                raise osv.except_osv(_('Warning !'), _("You don't have purchase requisition request configure !"))
            user = request.user_id
            next_user_ids, next_seq, next_state = config_obj.purchase_forward('purchase.requisition',request.active_sequence, request.user_id.id,config_id,request.department_id.id)
            next_user_ids1, next_seq1, next_state1 = config_obj.purchase_forward('purchase.requisition',active_sequence+1, request.user_id.id,config_id,request.department_id.id)
            # if not next_user_ids1:
            #     raise osv.except_osv(_('Warning !'), _(u"Дараагийн батлах хэрэглэгч олдсонгүй Таны батлах дүн хэтэрсэн эсвэл сарын батлах дүнгээс давсан байна."))            

        next_user_ids1 = self.get_possible_users(next_user_ids1)
        next_user_ids1 = self.group_users(active_sequence+1)
        if self._uid not in next_user_ids:
            raise osv.except_osv(_('Warning !'), _(u"Таны эрх хүрэхгүй байна."))            
        _logger.info(u'\n\n\n\n\n-------------------------active_sequence ', active_sequence+1,next_user_ids1,'\n\n\n\n\n\n\n\n')

        # if user_ids:
        #     next_user_ids1.extend(user_ids)
        if next_user_ids1:
            vals.update({'state':'next_confirm_user','active_sequence':active_sequence+1})
        else:
            raise osv.except_osv(_('Warning !'), _(u"Дараагийн батлах хэрэглэгч олдсонгүй Таны батлах дүн хэтэрсэн эсвэл сарын батлах дүнгээс давсан байна.!"))
            
        self.write(vals)
        self.line_ids.write({'state':'next_confirm_user'})
        self.create_history('next_confirm_user')
        # self.action_send_email('next_confirm_user',next_user_ids1)

    @api.multi
    def create_history(self,state):
        history_obj = self.env['request.history']
        if state in ['confirmed','next_confirm_user']:
            self.env['purchase.confirm.history.lines'].create({'requisition_id':self.id,'user_id':self._uid})
        history_obj.create(
                {'requisition_id': self.id,
                'user_id': self._uid,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'type': state,
                }
                )


    @api.multi
    def action_send_email(self,state, group_user_ids):
       
        template = self.env.ref('nomin_purchase_requisition.requisition_notif_cron_email_template1')
        

        compose_form = self.env.ref('mail.email_compose_message_wizard_form')
        states={'draft':u'Ноорог',
                       'sent':u'Илгээгдсэн',#Илгээгдсэн
                       'approved':u'Зөвшөөрсөн',#Зөвшөөрсөн
                       'verified':u'Хянасан',#Хянасан
                       'next_confirm_user':u'Дараагийн батлах хэрэглэгчид илгээгдсэн',#Дараагийн батлах хэрэглэгчид илгээгдсэн
                       'confirmed':u'Батласан',#Батласан
                       'tender_created':u'Тендер үүссэн',#Тендер үүссэн
                    #    'sent_to_supply':u'Хангамжид илгээгдсэн',#Хангамжаарх худалдан авалт
                    #    'fulfil_request':u'Биелүүлэх хүсэлт',# Биелүүлэх хүсэлт
                    #    'retrive_request':u'Буцаагдах хүсэлт',# Буцаагдах хүсэлт
                    #    'rfq_created':u'Үнийн санал үүссэн',#Үнийн санал үүссэн
                       'payment_request':u'Төлбөрийн хүсэлт үүссэн',
                    #    'fulfill':u'Биелүүлэх',# Биелүүлэх
                       'assigned':u'Хуваарилагдсан',#Хуваарилагдсан
                       'retrived':u'Буцаагдсан',# Буцаагдсан
                       'rejected':u'Татгалзсан',
                       'canceled':u'Цуцлагдсан',#Цуцлагдсан
                    #    'purchased':u'Худалдан авалт үүссэн',#Худалдан авалт үүссэн
                       'sent_to_supply_manager':u'Бараа тодорхойлох',#Хангамж импортын менежер
                       'done':u'Дууссан',
                                   }


        ctx = dict(
            default_model='purchase.requisition',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
        )
        data = {
                'department': self.department_id.name,
                'name': self.name,
                'base_url': self.env['ir.config_parameter'].get_param('web.base.url'),
    #                 'base_url': domain,
                'action_id': self.env['ir.model.data'].get_object_reference( 'purchase_requisition', 'action_purchase_requisition')[1],
                'id': self.id,
                'db_name': request.session.db,
                'state': states[state],
                'sender': self.env['res.users'].browse(self._uid).name,
            }  
        user_emails = []
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        action_id = self.env['ir.model.data'].get_object_reference('purchase_requisition', 'action_purchase_requisition')[1]
        db_name = request.session.db
        

              
        group_user_ids = list(set(group_user_ids))
        for email in  self.env['res.users'].browse(group_user_ids):
            user_emails.append(email.login)
            subject = u'"Шаардахын дугаар %s".'%(self.name)
            body_html = u'''
                            <h4>Сайн байна уу, \n Таньд энэ өдрийн мэнд хүргье! </h4>
                            <p>
                               ERP системд %s салбарын %s (хэлтэс) дэх %s дугаартай шаардах %s төлөвт орлоо.                               
                            </p>
                            <p><b><li> Шаардахын дугаар: %s</li></b></p>
                            <p><b><li> Салбар: %s</li></b></p>
                            <p><b><li> Хэлтэс: %s</li></b></p>
                            <p><b><li> Хүсч буй хугацаа: %s</li></b></p>
                            <p><li> <b><a href=%s/web?db=%s#id=%s&view_type=form&model=purchase.requisition&action=%s>Шаардахын мэдэгдэл</a></b> цонхоор дамжин харна уу.</li></p>

                            </br>
                            <p>---</p>
                            </br>
                            <p>Энэхүү мэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
                            <p>Баярлалаа.</p>
                        '''%( self.sector_id.name,
                            self.department_id.name,
                            self.name,
                            states[state],
                            self.name,
                             self.sector_id.name,
                            self.department_id.name,
                            self.schedule_date if self.schedule_date else " ......... ",
                            base_url,
                            db_name,
                            self.id,
                            action_id
                            )
     
            if email.login and email.login.strip():
                email_template = self.env['mail.template'].create({
                    'name': _('Followup '),
                    'email_from': self.env.user.company_id.email or '',
                    'model_id': self.env['ir.model'].search([('model', '=', 'purchase.requisition')]).id,
                    'subject': subject,
                    'email_to': email.login,
                    'lang': self.env.user.lang,
                    'auto_delete': True,
                    'body_html':body_html,
                  #  'attachment_ids': [(6, 0, [attachment.id])],
                })
                email_template.send_mail(self.id)
        email = u'' + states[state] +u'\n Дараах хэрэглэгчид рүү имэйл илгээгдэв: ' + ('<b>' + ('</b>, <b>'.join(user_emails)) + '</b>')
        
        self.write( {'confirm_user_ids':[(6,0,group_user_ids)]})
        self.message_subscribe_users(group_user_ids)
        self.message_post(body=email)
        
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def send_notification(self, signal ,group_user_ids):
        model_obj = openerp.pooler.get_pool(cr.dbname).get('ir.model.data')
        
        domain = self.env["ir.config_parameter"].get_param(cr, uid, "mail.catchall.domain", context=None)
   
        
    #     template_id = self.pool.get('ir.model.data').get_object_reference('nomin_purchase_requisition', 'requisition_notif_cron_email_template1')[1]
    #     if group_user_ids:
    #         users = self.env['res.users'].browse( group_user_ids)
    #         user_emails = []
    #         for user in users:
    #             user_emails.append(user.login)
    #             self.pool.get('email.template').send_mail(cr, uid, template_id, user.id, force_send=True, context=data)
    #         # email = u'Төлөв: → ' + states[signal]
    #         email = u'' + states[signal] + u'.\n Дараах хэрэглэгчид рүү имэйл илгээгдэв: ' + ('<b>' + ('</b>, <b>'.join(user_emails)) + '</b>')
            
    #         self.env['purchase.requisition'].write(cr, uid, ids, {'confirm_user_ids':[(6,0,group_user_ids)]}, context=None)
    #         self.env['purchase.requisition'].message_post(cr, uid, ids, body=email, context=None)
    #     else:
    #         raise osv.except_osv(_('Warning!'), _(u'Хүлээн авах хүн олдсонгүй. Систем админтайгаа холбогдоно уу'))
    #     return True
    # # @api.multi
    # def action_fulfil_request(self):
    #     #Шаардах шаардахын мөрийн төлөвийг өөрчлөх
    #     # self.change_state()
    #     day = self.date_by_adding_business_days(time.strftime('%Y-%m-%d'),self.priority_id.priority_day)
    #     if self.state in ['sent_to_supply']:
    #         # purchase_line = self.env['request.config.purchase.line']
    #         # line_ids = purchase_line.search([('sequence','=',self.active_sequence),('request_id','=',self.request_id.id)])
    #         # total_percent = 0
    #         # for line in line_ids:
    #         #         if line.limit ==0.0:
    #         #              self.write_state('assigned')
                          
    #         #         else:
    #         #             if line.limit > self.allowed_amount:
    #         #                self.write_state('assigned')
    #         #             else:
    #         #                 self.send_request() 
    #         for line in self.line_ids:
    #             line.write({'state':'assigned','date_start':time.strftime('%Y-%m-%d')})                    
    #         self.write({'state':'assigned','ordering_date':day})
      
    @api.multi            
    def action_retrive_request(self):
        context = {}
        context.update({'retrive_request':'retrive_request'}) 
        return {
            'name': 'Note',
            'view_type': 'form',
            'view_mode': 'form',
            #'view_id': [res and res[1] or False],
            'res_model': 'purchase.requisition.cancel.note',
            'context': context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            #'res_id': ids[0]  or False,
        }

    @api.multi
    def action_retrived(self):
        context = {}
        notif_groups = self.env['ir.model.data'].get_object_reference( 'nomin_purchase_requisition', 'group_purchase_decide_sent_to_supply')[1]
        
        next_user_ids = self.env['res.users'].search([('groups_id','in',[notif_groups])])
        if not next_user_ids:
              raise osv.except_osv(_(u'Анхааруулга'), _(u'Хангамж руу илгээх эсэх грүпд хэрэглэгч нар алга байна.')) 

        # confirm_user_ids = self.get_possible_users(next_user_ids.ids)
        confirm_user_ids = self.message_partner_ids.ids
        context.update({'retrive':'retrive','confirm_user_ids':confirm_user_ids}) 
        return {
            'name': 'Note',
            'view_type': 'form',
            'view_mode': 'form',
            #'view_id': [res and res[1] or False],
            'res_model': 'purchase.requisition.cancel.note',
            'context': context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            #'res_id': ids[0]  or False,
        }
        
    @api.multi            
    def action_to_reject(self):
        context = {}
        confirm_user_ids = [self.user_id.id]
        context.update({'return':'return','confirm_user_ids':confirm_user_ids}) 
        # self._context.update({'retrive_request':'retrive_request'})
        return {
            'name': 'Note',
            'view_type': 'form',
            'view_mode': 'form',
            #'view_id': [res and res[1] or False],
            'res_model': 'purchase.requisition.cancel.note',
            'context': context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            #'res_id': ids[0]  or False,
        }
    @api.multi        
    def action_fulfill(self):
        today = date.today()
        month_limit = 0
        purchase_line = self.env['request.config.purchase.line']
        line_ids = purchase_line.search([('sequence','=',self.active_sequence),('request_id','=',self.request_id.id)])
        total_percent = 0
        for line in line_ids:
                if line.limit !=0.0:
                    if line.limit < self.allowed_amount:
                        self.send_request()                        
                    else:
                        self.write_state('assigned')
                      
                else:
                    zline = purchase_line.search([('sequence','=',self.active_sequence+1),('request_id','=',self.request_id.id)])
                    if zline:
                        self.send_request()
                    else:
                        self.write_state('assigned')

class purchase_order(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection([
        ('draft', 'Draft PO'), #Ноорог PO
        ('sent', 'Sent'), #Ноорог PO
        ('sent_rfq', 'Get quote'), #Үнийн санал авах
        ('back', 'Quote received'),  #Үнийн санал ирсэн
        ('comparison_created', 'Comparison created'), #Харьцуулалт үүссэн
        ('to approve', 'Approve'), #Зөвшөөрөх
        ('approved', 'Approved'), #Зөвшөөрсөн
        ('purchase', 'Purchase order'), #Худалдан авах захиалга
        ('verified','Checked'), #Хянасан
        ('confirmed','Confirmed'), #Батласан
        ('done', 'Done'), #Дууссан
        ('cancel', 'Canceled') #Цуцлагдсан
        ], string='Status', readonly=True, select=True, copy=False, default='draft', track_visibility='onchange')

    payment_request_id = fields.Many2one('payment.request',string='Payment request') #Төлбөрийн хүсэлт

    @api.multi
    def write(self, vals):
        if vals.get('state'):
            for order in self:
                for line in order.order_line:
                    line.write({'state':vals.get('state')})
        order_id = super(purchase_order,self).write(vals)
        
        line_ids = []
        for order in self:
            if order.state =='purchase':
                if order.order_line:
                    for line in order.order_line:
                        if line.requisition_line_id:
                            line_ids.append(line.requisition_line_id.id)
                if line_ids:
                    order_line_ids = self.env['purchase.order.line'].search([('requisition_line_id','in',line_ids),('order_id','!=',self.id)])
                    if order_line_ids:
                        order_line_ids.write({'state':'cancel'})
                        for order in order_line_ids:
                            order.order_id.write({'state':'cancel'})
        return order_id  

    @api.multi
    def action_payment_request (self):
        model_obj = self.env['ir.model.data']
        # res = mod_obj.get_object_reference('nomin_purchase_requisition', 'action_create_purchase_order')
        result = model_obj._get_id('nomin_budget', 'payment_request_form')
        view_id = model_obj.browse(result).res_id

        employee_id = self.env['hr.employee'].sudo().search([('user_id','=',self._uid)])
        sector_id = self.env['hr.department'].get_sector(employee_id.department_id.id)
        vals = {
                'user_id':self._uid,
                'department_id':employee_id.department_id.id,
                'sector_id':sector_id,
                'receiving_payment_partner_id':employee_id.address_home_id.id,
                'transaction_name': u'Худалдан авалтын захиалгын дугаар:'+ self.name or '?',
                'order_id':self.id,
        }
        request_id = self.env['payment.request'].create(vals)
        self.env['payment.request.line'].create({
                                                  'name': u'Худалдан авалтын захиалгын дугаар:'+ self.name or '?',
                                                    'amount': self.amount_total,
                                                    # 'amount_currency':amount_currency,
                                                    # 'move_line_id': line.id,
                                                    'parent_id':request_id.id,
                                                    'is_payment': False,
                                                    'sector_id':request_id.sector_id.id,
                                                    # 'account_id':line.account_id.id,
                                                    # 'state':payment.state,
                                                    # 'cashflow_account_id':cashflow_account_id,
                                                    'partner_id':employee_id.partner_id.id,
                                                    
                                                    # 'receiving_payment_account_id':payment.receiving_payment_account_id.id,
                                                    # 'currency_id':payment.currency_id.id,
                                                    # 'transaction_currency_id':payment.transaction_currency_id.id,
                                                    # 'currency_rate':payment.currency_rate,
                                                    # 'is_other_currency':payment.is_other_currency,
                                                     # 'tax_id':payment.tax_id.id if payment.tax_id else False

                                                    }
                                                 )
        self.write({'payment_request_id':request_id.id})
        # self.action_send_email('payment_request', [self.user_id.id])
        return {
                     'type': 'ir.actions.act_window',
                     'name': _('Create payment request'),
                     'res_model': 'payment.request',
                     'view_type' : 'tree',
                     'view_mode' : 'form',
                     'search_view_id' : view_id,
                     'res_id':request_id.id,
                     'target' : 'current',
                     'nodestroy' : True,
                }

class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'


    state = fields.Selection([
        ('draft', 'Draft PO'),
        ('sent', 'Sent'),
        ('sent_rfq', 'RFQ Sent'),
        ('back', 'RFQ Back'),
        ('to approve', 'To Approve'),
        ('approved', 'Approved'),
        ('purchase', 'Purchase Order'),
        ('verified','Verified'),
        ('confirmed','Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
        ], string='Status', readonly=True, select=True, copy=False, default='draft', track_visibility='onchange')

    @api.multi
    def write(self, vals):
        if vals.get('state'):
            # if vals.get('state') =='purchase':
            #     if self.requisition_line_id:
            #         if self.requisition_line_id.state not in ['purchased','done']:
            #             self.requisition_line_id.write({'state':'purchased'})
            if vals.get('state') =='done':
                if self.requisition_line_id:
                    if  self.requisition_line_id.state !='done':
                        self.requisition_line_id.write({'state':'done'})
                    
        order_id = super(purchase_order_line,self).write(vals)
        return order_id  
class payment_request(models.Model):
    _inherit ='payment.request'
    
    requisition_id = fields.Many2one('purchase.requisition',string='Requisition number') #Шаардахын дугаар
    order_id = fields.Many2one('purchase.order',string='Order number') #Захиалгын дугаар

class crm_heldesk(models.Model):
    _inherit ='crm.helpdesk'
    
    requisition_ids = fields.One2many('purchase.requisition','helpdesk_id',string='Requisition number') #Шаардахын дугаар
    
class request_history(models.Model):
    """Received Document History"""
    _inherit = "request.history"
    
    requisition_id = fields.Many2one('purchase.requisition', string='Purchase requisition', ondelete="cascade")
class stock_warehouse(models.Model):
    _inherit = 'stock.warehouse'
    
    company_id = fields.Many2one('res.company', string='Company', required=True, select=True)

    
class ir_attachment(models.Model):
    _inherit ='ir.attachment'
    
    requisition_id = fields.Many2one('purchase.requisition',string='Requisition number') #Шаардахын дугаар


class InheritRequisitionProductTemplate(models.Model):
    _inherit = 'product.template'


    product_mark = fields.Char(string=u'Барааны үзүүлэлт')
    assign_categ_id = fields.Many2one('assign.category',string=u'Барааны хувиарлалт ангилал', track_visibility='onchange', required=True, change_default=True)
    product_code = fields.Char(u'Барааны код', required = True,track_visibility='onchange' )


class InheritPurchaseComparison(models.Model):
    _inherit = 'purchase.comparison'

