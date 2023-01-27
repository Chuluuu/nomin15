# -*- coding: utf-8 -*-

import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


def create_purchase_with_control_budget(self, control_budget_id, requisition_id, equipment_amount, carriage_amount, postage_amount, other_amount,line_ids):
    '''
        Хяналтын төсөв сонгож Худалдан авалтын шаардах үүсгэхэд хяналтын төсөврүү гүйцэтгэл хотлох
        :param control_budget_id: Хяналтын төсөв
        :param requisition_id: Худалдан авалтын шаардах
        :param equipment_amount: Машин механизмын зардалын дүн
        :param carriage_amount: Тээврийн зардлын дүн
        :param postage_amount: Шууд зардлын дүн
        :param other_amount: Бусад зардлын дүн
        :param line_ids: шаардахын мөрүүд
    '''
    utilization_budget_material     = self.env['utilization.budget.material']
    utilization_budget_labor        = self.env['utilization.budget.labor']
    utilization_budget_equipment    = self.env['utilization.budget.equipment']
    utilization_budget_carriage     = self.env['utilization.budget.carriage']
    utilization_budget_postage      = self.env['utilization.budget.postage']
    utilization_budget_other        = self.env['utilization.budget.other']
    
    m_total_amount = 0.0
    l_total_amount = 0.0
    
    if line_ids:
        for line in line_ids:
            if line.c_budget_type == 'material':
                m_total_amount += line.amount
            else:
                l_total_amount += line.amount
                
    if m_total_amount > 0:
        if control_budget_id.material_utilization_limit >= m_total_amount:
            m_vals = {
                        'budget_id'     : control_budget_id.id,
                        'purchase'      : requisition_id,
                        'price'         : m_total_amount,
                        'date'          : time.strftime('%Y-%m-%d %H:%M:%S'),
                        'map'           : 'purchase',
                        'state'         : 'purchase'
                        }
            utilization_budget_material     = utilization_budget_material.create(m_vals)
        else:
            raise UserError(_(u'Хяналтын төсвийн Материалын зардлын боломжит үлдэгдэлээс их байна'))
    if l_total_amount > 0:
        if control_budget_id.labor_utilization_limit >= l_total_amount:
            l_vals = {
                        'budget_id'     : control_budget_id.id,
                        'purchase'      : requisition_id,
                        'price'         : l_total_amount,
                        'date'          : time.strftime('%Y-%m-%d %H:%M:%S'),
                        'map'           : 'purchase',
                        'state'         : 'purchase'
                        }
            utilization_budget_labor        = utilization_budget_labor.create(l_vals)
        else:
            raise UserError(_(u'Хяналтын төсвийн Ажиллах хүчний зардлын боломжит үлдэгдэлээс их байна'))
        
    if equipment_amount > 0:
        if control_budget_id.equipment_utilization_limit >= equipment_amount:
            e_vals = {
                        'budget_id'     : control_budget_id.id,
                        'purchase'      : requisition_id,
                        'price'         : equipment_amount,
                        'date'          : time.strftime('%Y-%m-%d %H:%M:%S'),
                        'map'           : 'purchase',
                        'state'         : 'purchase'
                        }
            utilization_budget_equipment    = utilization_budget_equipment.create(e_vals)
        else:
            raise UserError(_(u'Хяналтын төсвийн Машин механизмын зардлын боломжит үлдэгдэлээс их байна'))
        
    if carriage_amount > 0:
        if control_budget_id.carriage_utilization_limit >= carriage_amount:
            c_vals = {
                        'budget_id'     : control_budget_id.id,
                        'purchase'      : requisition_id,
                        'price'         : carriage_amount,
                        'date'          : time.strftime('%Y-%m-%d %H:%M:%S'),
                        'map'           : 'purchase',
                        'state'         : 'purchase'
                        }
            utilization_budget_carriage     = utilization_budget_carriage.create(c_vals)
        else:
            raise UserError(_(u'Хяналтын төсвийн Тээврийн зардлын боломжит үлдэгдэлээс их байна'))
    if postage_amount > 0:
        if control_budget_id.postage_utilization_limit >= postage_amount:
            p_vals = {
                        'budget_id'     : control_budget_id.id,
                        'purchase'      : requisition_id,
                        'price'         : postage_amount,
                        'date'          : time.strftime('%Y-%m-%d %H:%M:%S'),
                        'map'           : 'purchase',
                        'state'         : 'purchase'
                        }
            utilization_budget_postage      = utilization_budget_postage.create(p_vals)
        else:
            raise UserError(_(u'Хяналтын төсвийн Шууд зардлын боломжит үлдэгдэлээс их байна'))
    if other_amount > 0:
        if control_budget_id.other_utilization_limit >= other_amount:
            o_vals = {
                        'budget_id'     : control_budget_id.id,
                        'purchase'      : requisition_id,
                        'price'         : other_amount,
                        'date'          : time.strftime('%Y-%m-%d %H:%M:%S'),
                        'map'           : 'purchase',
                        'state'         : 'purchase'
                        }
            utilization_budget_other        = utilization_budget_other.create(o_vals)
        else:
            raise UserError(_(u'Хяналтын төсвийн Бусад зардлын боломжит үлдэгдэлээс их байна'))
        
def create_tender_with_control_budget(self,control_budget_id,tender_id):
    '''
        Хяналтын төсөв сонгож тендер үүсгэхэд хяналтын төсөврүү гүйцэтгэл хотлох
        :param cr: Cr заалт. Өгөгдлийн сантай ажиллах
        :param uid: Системд нэвтэрсэн хэрэглэгчийн ID
        :param control_budget_id: Хяналтын төсөв
        :param tender_id: Худалдан авалтын шаардах
        :param context: Нэмэлт мэдээлэл агуулсан Dict байна
    '''
    utilization_budget_material     = self.env['utilization.budget.material']
    utilization_budget_labor        = self.env['utilization.budget.labor']
    utilization_budget_equipment    = self.env['utilization.budget.equipment']
    utilization_budget_carriage     = self.env['utilization.budget.carriage']
    utilization_budget_postage      = self.env['utilization.budget.postage']
    utilization_budget_other        = self.env['utilization.budget.other']
    
    total_amount = 0.0
    material_amount = 0.0
    material_amount += control_budget_id.material_utilization_limit
    labor_amount = 0.0
    labor_amount += control_budget_id.labor_utilization_limit
    equipment_amount = 0.0
    equipment_amount += control_budget_id.equipment_utilization_limit
    carriage_amount = 0.0
    carriage_amount += control_budget_id.carriage_utilization_limit
    postage_amount = 0.0
    postage_amount += control_budget_id.postage_utilization_limit
    other_amount = 0.0
    other_amount += control_budget_id.other_utilization_limit
    total_amount = material_amount + labor_amount + equipment_amount + carriage_amount + postage_amount + other_amount
    
    if material_amount > 0:
        m_vals = {
            'budget_id'     :control_budget_id.id,
            'tender'        :tender_id,
            'date'          :time.strftime('%Y-%m-%d %H:%M:%S'),
            'price'         :material_amount,
            'map'           :'tender',
            'state'         :'tender'
            }
        utilization_budget_material = utilization_budget_material.create( m_vals)
    
    if labor_amount > 0:
        l_vals = {
            'budget_id'     :control_budget_id.id,
            'tender'        :tender_id,
            'date'          :time.strftime('%Y-%m-%d %H:%M:%S'),
            'price'         :labor_amount,
            'map'           :'tender',
            'state'         :'tender'
            }
        utilization_budget_labor = utilization_budget_labor.create(l_vals)
    
    if equipment_amount > 0:
        e_vals = {
            'budget_id'     :control_budget_id.id,
            'tender'        :tender_id,
            'date'          :time.strftime('%Y-%m-%d %H:%M:%S'),
            'price'         :equipment_amount,
            'map'           :'tender',
            'state'         :'tender'
            }
        utilization_budget_equipment = utilization_budget_equipment.create(e_vals)
    
    if carriage_amount > 0:
        c_vals = {
            'budget_id'     :control_budget_id.id,
            'tender'        :tender_id,
            'date'          :time.strftime('%Y-%m-%d %H:%M:%S'),
            'price'         :carriage_amount,
            'map'           :'tender',
            'state'         :'tender'
            }
        utilization_budget_carriage = utilization_budget_carriage.create(c_vals)
    
    if postage_amount > 0:
        p_vals = {
            'budget_id'     :control_budget_id.id,
            'tender'        :tender_id,
            'date'          :time.strftime('%Y-%m-%d %H:%M:%S'),
            'price'         :postage_amount,
            'map'           :'tender',
            'state'         :'tender'
            }
        utilization_budget_postage = utilization_budget_postage.create(p_vals)
    
    if other_amount > 0:
        o_vals = {
            'budget_id'     :control_budget_id.id,
            'tender'        :tender_id,
            'date'          :time.strftime('%Y-%m-%d %H:%M:%S'),
            'price'         :other_amount,
            'map'           :'tender',
            'state'         :'tender'
            }
        utilization_budget_other = utilization_budget_other.create(o_vals)
        
class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'


    def write(self, vals):
        if 'state' in vals:
            if vals.get('state')=='confirmed':
                if 'control_budget_id' in vals :
                    create_purchase_with_control_budget(self, vals.get('control_budget_id'), self.id, self.equipment_amount,self.carriage_amount,self.postage_amount,self.other_amount,self.line_ids)
                elif  self.control_budget_id and self.is_in_control_budget == False:
                        create_purchase_with_control_budget(self, self.control_budget_id, self.id, self.equipment_amount,self.carriage_amount,self.postage_amount,self.other_amount,self.line_ids)
        return super(PurchaseRequisition ,self).write(vals)

class ControlBudget(models.Model):
    _inherit = 'control.budget'
    _order = "create_date desc"
    
    '''
        Хяналтын төсөв
    '''
    
    def _get_all(self):
        '''
            Зардлуудын боломжит үлдэгдэл , жинхэнэ үлдэгдэл төсөвлөсөн дүн тооцоолох
        '''
        for budget in self:
            if budget.project_id:
                if budget.project_id.project_flag:
                    lines = self.env['project.budget.line'].sudo().search([('project_budget_id.project_id','=',budget.project_id.id)])
                    a = []
                    for line in lines:
                        a.append(line.total_cost)
                        maxx = max(a)
                        if line.total_cost == maxx:
                            budget.update({
                                        # 'project_budget_material'         :line.material_line_limit_new,
                                        # 'project_budget_carriage'         :line.carriage_limit_new,
                                        # 'project_budget_labor'            :line.labor_line_limit_new,
                                        # 'project_budget_equipment'        :line.equipment_line_limit_new,
                                        # 'project_budget_postage'          :line.postage_line_limit_new,
                                        # 'project_budget_other'            :line.other_line_limit_new,
                                        'project_budget_material_limit'   :line.material_line_limit_new,
                                        'project_budget_carriage_limit'   :line.carriage_limit_new,
                                        'project_budget_labor_limit'      :line.labor_line_limit_new,
                                        'project_budget_equipment_limit'  :line.equipment_line_limit_new,
                                        'project_budget_postage_limit'    :line.postage_line_limit_new,
                                        'project_budget_other_limit'      :line.other_line_limit_new,
                                        'project_budget_material_real'    :line.material_line_total_new,
                                        'project_budget_carriage_real'    :line.carriage_cost_new,
                                        'project_budget_labor_real'       :line.labor_line_total_new,
                                        'project_budget_equipment_real'   :line.equipment_line_total_new,
                                        'project_budget_postage_real'     :line.postage_line_total_new,
                                        'project_budget_other_real'       :line.other_line_total_new
                                        })
                else:
                    line = self.env['main.specification'].sudo().search([('parent_project_id','=',budget.project_id.id),('confirm','=',True)])
                    if line:
                        budget.update({
                                    'project_budget_material'         :line.material_line_real,
                                    'project_budget_carriage'         :line.carriage_real,
                                    'project_budget_labor'            :line.labor_line_real,
                                    'project_budget_equipment'        :line.equipment_line_real,
                                    'project_budget_postage'          :line.postage_line_real,
                                    'project_budget_other'            :line.other_line_real,
                                    'project_budget_material_limit'   :line.material_line_limit,
                                    'project_budget_carriage_limit'   :line.carriage_limit,
                                    'project_budget_labor_limit'      :line.labor_line_limit,
                                    'project_budget_equipment_limit'  :line.equipment_line_limit,
                                    'project_budget_postage_limit'    :line.postage_line_limit,
                                    'project_budget_other_limit'      :line.other_line_limit,
                                    'project_budget_material_real'    :line.material_line_total,
                                    'project_budget_carriage_real'    :line.carriage_cost,
                                    'project_budget_labor_real'       :line.labor_line_total,
                                    'project_budget_equipment_real'   :line.equipment_line_total,
                                    'project_budget_postage_real'     :line.postage_line_total,
                                    'project_budget_other_real'       :line.other_line_total
                                    })
                    
    def _get_limit(self):
        '''
            Зардлуудын гүйцэтгэл тооцолох
        '''
        for budget in self:
            total_price = 0.0
            for material_line in budget.utilization_budget_material:
                total_price += material_line.price
            budget.material_utilization_limit = budget.material_cost - total_price
            total_price = 0.0
            for labor_line in budget.utilization_budget_labor:
                total_price += labor_line.price
            budget.labor_utilization_limit = budget.labor_cost - total_price
            total_price = 0.0
            for equipment_line in budget.utilization_budget_equipment:
                total_price += equipment_line.price
            budget.equipment_utilization_limit = budget.equipment_cost - total_price
            total_price = 0.0
            for carriage_line in budget.utilization_budget_carriage:
                total_price += carriage_line.price
            budget.carriage_utilization_limit = budget.carriage_cost - total_price
            total_price = 0.0
            for postage_line in budget.utilization_budget_postage:
                total_price += postage_line.price
            budget.postage_utilization_limit = budget.postage_cost - total_price
            total_price = 0.0
            for other_line in budget.utilization_budget_other:
                total_price += other_line.price
            budget.other_utilization_limit = budget.other_cost - total_price
            
    def _total_limit(self):
        '''
            Нийт төсвийн үлдэгдэл тооцоолох
        '''
        total = 0.0
        for budget in self:
            total += budget.material_utilization_limit + budget.labor_utilization_limit + budget.equipment_utilization_limit + budget.carriage_utilization_limit + budget.postage_utilization_limit + budget.other_utilization_limit
            budget.total_utilization_limit = total
            
    def _budgets_utilization_total(self):
        '''
            Бодит гүйцэтгэлийн нийт дүн талбар тооцоолох
        '''
        total = 0.0
        for budget in self:
            for util_line in budget.budgets_utilization:
                total += util_line.price
            budget.budgets_utilization_total = total
            
    def _budgets_utilization_util(self):
        '''
            Бодит гүйцэтгэлийн гүйцэтгэл талбар тооцоолох
        '''
        total = 0.0
        for budget in self:
            for util_line in budget.budgets_utilization:
                total += util_line.utilization
            budget.budgets_utilization_util = total
    
    def _budgets_utilization_balance(self):
        '''
            Бодит гүйцэтгэлийн Үлдэгдэл талбар тооцоолох
        '''
        total = 0.0
        for budget in self:
            for util_line in budget.budgets_utilization:
                total += util_line.balance
            budget.budgets_utilization_balance = total
    
    def _invisible_to_confirm(self):
        '''
            Нэвтэрсэн хэрэглэгчийг Төсөвчин мөн эсэхийг тооцоолох
        '''
        for budget in self:
            budget.invisible_to_confirm = False
            if budget.user_id.id == budget._uid:
                budget.invisible_to_confirm = True
            
    def _add_followers(self,user_ids):
        '''Add followers
        '''
        partner_ids = [user.partner_id.id for user in self.env['res.users'].browse(user_ids) if user.partner_id]
        self.message_subscribe(partner_ids=partner_ids)
    
    
    def _is_old(self):
        for record in self:
            record.is_old= False
            if record.create_date < datetime.strptime('2021-12-09 00:00:00', '%Y-%m-%d %H:%M:%S'):
                record.is_old = True

    
    def _is_old2(self):
        for record in self:
            record.is_old2=False
            if record.create_date < datetime.strptime('2022-12-28 00:00:00', '%Y-%m-%d %H:%M:%S'):
                record.is_old2 = True

    project_budget_material         = fields.Float(u'Жинхэнэ үлдэгдэл', compute=_get_all)
    project_budget_carriage         = fields.Float(u'Жинхэнэ үлдэгдэл', compute=_get_all)
    project_budget_labor            = fields.Float(u'Жинхэнэ үлдэгдэл', compute=_get_all)
    project_budget_equipment        = fields.Float(u'Жинхэнэ үлдэгдэл', compute=_get_all)
    project_budget_postage          = fields.Float(u'Жинхэнэ үлдэгдэл', compute=_get_all)
    project_budget_other            = fields.Float(u'Жинхэнэ үлдэгдэл', compute=_get_all)
    project_budget_material_limit   = fields.Float(u'Төсөвлөсөн дүн', compute=_get_all)
    project_budget_carriage_limit   = fields.Float(u'Төсөвлөсөн дүн', compute=_get_all)
    project_budget_labor_limit      = fields.Float(u'Төсөвлөсөн дүн', compute=_get_all)
    project_budget_equipment_limit  = fields.Float(u'Төсөвлөсөн дүн', compute=_get_all)
    project_budget_postage_limit    = fields.Float(u'Төсөвлөсөн дүн', compute=_get_all)
    project_budget_other_limit      = fields.Float(u'Төсөвлөсөн дүн', compute=_get_all)
    project_budget_material_real    = fields.Float(u'Боломжит үлдэгдэл', compute=_get_all)
    project_budget_carriage_real    = fields.Float(u'Боломжит үлдэгдэл', compute=_get_all)
    project_budget_labor_real       = fields.Float(u'Боломжит үлдэгдэл', compute=_get_all)
    project_budget_equipment_real   = fields.Float(u'Боломжит үлдэгдэл', compute=_get_all)
    project_budget_postage_real     = fields.Float(u'Боломжит үлдэгдэл', compute=_get_all)
    project_budget_other_real       = fields.Float(u'Боломжит үлдэгдэл', compute=_get_all)
    
    material_utilization_limit      = fields.Float(u'Үлдэгдэл', compute=_get_limit)
    labor_utilization_limit         = fields.Float(u'Үлдэгдэл', compute=_get_limit)
    equipment_utilization_limit     = fields.Float(u'Үлдэгдэл', compute=_get_limit)
    carriage_utilization_limit      = fields.Float(u'Үлдэгдэл', compute=_get_limit)
    postage_utilization_limit       = fields.Float(u'Үлдэгдэл', compute=_get_limit)
    other_utilization_limit         = fields.Float(u'Үлдэгдэл', compute=_get_limit)
    total_utilization_limit         = fields.Float(u'Үлдэгдэл', compute=_total_limit)
    budgets_utilization             = fields.One2many('utilization.on.budget','control_budget_id',string= u'Гүйцэтгэл')
    
    invisible_to_confirm            = fields.Boolean('Invisible botton',compute=_invisible_to_confirm)
    
    budgets_utilization_total       = fields.Float(u'Нийт дүн',compute=_budgets_utilization_total)
    budgets_utilization_util        = fields.Float(u'Гүйцэтгэл',compute=_budgets_utilization_util)
    budgets_utilization_balance       = fields.Float(u'Үлдэгдэл',compute=_budgets_utilization_balance)
    work_graph_id                   = fields.Many2one('project.task', string='Work Graph', tracking=True)
    
    back_state                  = fields.Char('back_stage')
    evaluate_budget             = fields.One2many('evaluate.tasks','budget_id','Budget evaluate')
    budget_users                = fields.One2many('main.specification.confirmers','budget_id','Project users')
    m_department_id             = fields.Many2one('hr.department', string=u'Зардал гарах салбар',domain=[('is_sector', '=',True)])
    is_old                      = fields.Boolean(string='is old' , compute=_is_old, default=False)
    is_old2                      = fields.Boolean(string='is old material' , compute=_is_old2, default=False)

    _sql_constraints = [
        ('unique_budget_code', 'unique(budget_code)',
         ("There is already a rule defined on this model\n"
          "You cannot define another: please edit the existing one."))
    ]
     
    def test_action(self):
        budgets = self.env['control.budget'].search([('user_id','!=',False)])
        for budget in budgets:
            if budget.task_id:
                for emp in budget.budget_confirmer:
                    budget.task_id._add_followers(emp.user_id.id)
                    budget.task_id.project_id._add_followers(emp.user_id.id)
                    
            if budget.work_graph_id:
                for emp in budget.budget_confirmer:
                    budget.work_graph_id._add_followers(emp.user_id.id)
    
    @api.model
    def create(self, vals):
        '''
            Үүсгэх
            Төсөвчин болон батлах хэрэглэгчидийг дагагчаар нэмнэ
        '''
        if vals.get('budget_code','New') == 'New':
            vals['budget_code'] = self.env['ir.sequence'].next_by_code('control.budget') or 'New'
        result = super(ControlBudget, self).create(vals)
        if vals.get('budget_confirmer'):
            for user in result.budget_confirmer:
                result._add_followers(user.user_id.id)
                result.project_id.sudo().add_raci_users('C',user.user_id.id)
        if vals.get('user_id'):
            result._add_followers(result.user_id.id)
            result.project_id.sudo().add_raci_users('C',result.user_id.id)
        return result

    def handle_budget_consumption(self):


        overrun_counts=0
        expenditure_ratio=0
        overrun_ratio=0


        project_budget_material_limit = 0.0
        project_budget_labor_limit = 0.0
        project_budget_equipment_limit = 0.0
        project_budget_carriage_limit = 0.0
        project_budget_postage_limit = 0.0
        project_budget_other_limit = 0.0

        material_cost = 0.0
        labor_cost = 0.0
        carriage_cost = 0.0
        equipment_cost = 0.0
        postage_cost = 0.0
        other_cost = 0.0

        project_budget_material = 0.0
        project_budget_labor = 0.0
        project_budget_equipment = 0.0
        project_budget_carriage = 0.0
        project_budget_postage = 0.0
        project_budget_other = 0.0

        project_budget_limit = 0.0
        total_expenditure = 0.0
        project_budget = 0.0


        main_specification_id = self.env['main.specification'].sudo().search([('parent_project_id','=',self.id),('state','=','confirm')],limit =1)
        overrun_counts = len(self.env['main.specification'].sudo().search([('parent_project_id','=',self.id)]))

        if self.project_id:

            task_counts = len(self.env['project.task'].sudo().search([('project_id','=',self.project_id.id)]))
            if task_counts>0:
                self.project_id.task_counts = task_counts


            issue_counts = len(self.env['project.issue'].sudo().search([('project_id','=',self.project_id.id)]))
            if issue_counts>0:
                self.project_id.issue_counts = issue_counts



            control_budget = self.env['control.budget'].sudo().search([('project_id','=',self.project_id.id),('state','=','done')])
            if control_budget:
                for i in control_budget:



                    material_cost += i.material_cost 
                    labor_cost += i.labor_cost 
                    carriage_cost += i.carriage_cost 
                    equipment_cost += i.equipment_cost 
                    postage_cost += i.postage_cost
                    other_cost += i.other_cost 

                    total_expenditure += i.material_cost + i.labor_cost 
                    total_expenditure += i.carriage_cost + i.equipment_cost 
                    total_expenditure += i.postage_cost + i.other_cost 

                project_budget_material_limit += i.project_budget_material_limit 
                project_budget_labor_limit += i.project_budget_labor_limit
                project_budget_equipment_limit += i.project_budget_equipment_limit 
                project_budget_carriage_limit += i.project_budget_carriage_limit 
                project_budget_postage_limit += i.project_budget_postage_limit
                project_budget_other_limit += i.project_budget_other_limit 

                project_budget_limit += i.project_budget_material_limit + i.project_budget_labor_limit 
                project_budget_limit += i.project_budget_equipment_limit + i.project_budget_carriage_limit 
                project_budget_limit += i.project_budget_postage_limit + i.project_budget_other_limit 

                project_budget_material += i.project_budget_material
                project_budget_labor += i.project_budget_labor
                project_budget_equipment += i.project_budget_equipment 
                project_budget_carriage += i.project_budget_carriage 
                project_budget_postage += i.project_budget_postage
                project_budget_other += i.project_budget_other 

                project_budget += i.project_budget_material + i.project_budget_labor
                project_budget += i.project_budget_equipment + i.project_budget_carriage 
                project_budget += i.project_budget_postage + i.project_budget_other 


                project = self.env['project.project'].sudo().search([('id','=',self.project_id.id)])

                expenditure_ratio = 0
                overrun_ratio = 0
                if main_specification_id.total_investment>0:
                    expenditure_ratio = int(total_expenditure*100/main_specification_id.total_investment)
                    overrun_ratio = int(project_budget_limit*100/main_specification_id.total_investment)

                if project.project_flag:
                    project.update({
                                    'material_budget_new':project_budget_material_limit,
                                    'labour_budget_new':project_budget_labor_limit,
                                    'equipment_budget_new':project_budget_equipment_limit,
                                    'transport_budget_new':project_budget_carriage_limit,
                                    'direct_budget_new':project_budget_postage_limit,
                                    'other_budget_new':project_budget_other_limit,

                                    'material_expenditure_new':material_cost,
                                    'labour_expenditure_new':labor_cost,
                                    'equipment_expenditure_new':equipment_cost,
                                    'transport_expenditure_new':carriage_cost,
                                    'direct_expenditure_new':postage_cost,
                                    'other_expenditure_new':other_cost,

                                    'material_remaining_amount_new':project_budget_material,
                                    'labour_remaining_amount_new':project_budget_labor,
                                    'equipment_remaining_amount_new':project_budget_equipment,
                                    'transport_remaining_amount_new':project_budget_carriage,
                                    'direct_remaining_amount_new':project_budget_postage,
                                    'other_remaining_amount_new':project_budget_other,

                                    'project_budget' : project_budget_limit,
                                    'total_expenditure' : total_expenditure,
                                    'total_remaining_amount' : project_budget,
                                    'task_counts' : task_counts,
                                    'issue_counts' : issue_counts,


                                    'overrun_counts':overrun_counts,
                                    'expenditure_ratio':expenditure_ratio,
                                    'overrun_ratio':overrun_ratio,


                                    })

                else:

                    project.update({


                        'material_budget':project_budget_material_limit,
                        'labour_budget':project_budget_labor_limit,
                        'equipment_budget':project_budget_equipment_limit,
                        'transport_budget':project_budget_carriage_limit,
                        'direct_budget':project_budget_postage_limit,
                        'other_budget':project_budget_other_limit,

                        'material_expenditure':material_cost,
                        'labour_expenditure':labor_cost,
                        'equipment_expenditure':equipment_cost,
                        'transport_expenditure':carriage_cost,
                        'direct_expenditure':postage_cost,
                        'other_expenditure':other_cost,

                        'material_remaining_amount':project_budget_material,
                        'labour_remaining_amount':project_budget_labor,
                        'equipment_remaining_amount':project_budget_equipment,
                        'transport_remaining_amount':project_budget_carriage,
                        'direct_remaining_amount':project_budget_postage,
                        'other_remaining_amount':project_budget_other,

                        'project_budget' : project_budget_limit,
                        'total_expenditure' : total_expenditure,
                        'total_remaining_amount' : project_budget,
                        'task_counts' : task_counts,
                        'issue_counts' : issue_counts,


                        'overrun_counts':overrun_counts,
                        'expenditure_ratio':expenditure_ratio,
                        'overrun_ratio':overrun_ratio,
                        'estimated_budget' : main_specification_id.total_investment


                    })

    def write(self, vals):
        '''
            Төсөвчин болон батлах хэрэглэгчидийг дагагчаар нэмнэ
        '''
        
        result = super(ControlBudget, self).write(vals)
        if vals and 'user_id' in vals:
            self._add_followers(vals['user_id'])
            if vals['user_id'] not in self.project_id.sudo().c_user_ids.ids:
                self.project_id.sudo().add_raci_users('C',vals['user_id'])
        if vals and 'budget_confirmer' in vals:
            for users in vals['budget_confirmer']:
                for user in users[-1]:
                    emp = self.env['hr.employee'].sudo().browse(user)
                    if emp.user_id and emp.user_id.id not in self.project_id.sudo().c_user_ids.ids:
                        self.project_id.sudo().add_raci_users('C',emp.user_id.id)
                    self._add_followers(emp.user_id.id)
        return result
    
    def unlink(self):
        '''
            Устгах Ноорог төлөвтөй Хяналтын төсвийг
        '''
        for budget in self:
            if budget.state != 'draft':
                raise UserError(_(u'Та зөвхөн ноорог төлөвтөй хяналтын төсөв устгах боломжтой'))
        return super(ControlBudget, self).unlink()
    
    
    def copy(self, default=None):
        if default is None:
            default = {}
        
        if not default.get('budget_code'):
            code = self.env['ir.sequence'].next_by_code('control.budget')
            default.update({'budget_code':code})
        
        return super(ControlBudget, self).copy(default=default)

    def action_select(self):
        '''
            Материалын зардлын батлагдаагүй мөрүүдийг нийтээр нь сонгох
        '''
        for budget in self:
            for line in budget.material_line_ids:
                if line.state == 'confirm':
                    line.cost_choose = True
    
    def action_deselect(self):
        '''
            Материалын зардлын батлагдаагүй мөрүүдийг нийтээр нь сонгохыг болиулах
        '''
        for budget in self:
            for line in budget.material_line_ids:
                if line.state == 'confirm':
                    line.cost_choose = False
                    
    
    def action_select_labor(self):
        '''
            Ажиллах хүчний зардлын батлагдаагүй мөрүүдийг нийтээр нь сонгох
        '''
        for budget in self:
            for line in budget.labor_line_ids:
                if line.state == 'confirm':
                    line.cost_choose = True
    
    def action_deselect_labor(self):
        '''
            Ажиллах хүчний зардлын батлагдаагүй мөрүүдийг нийтээр нь сонгохыг болиулах
        '''
        for budget in self:
            for line in budget.labor_line_ids:
                if line.state == 'confirm':
                    line.cost_choose = False
                        
    @api.onchange('project_id')
    def onchange_evaluator(self):
        '''
            Төсөл талбар солигдоход Батлах ажилчид , Ажлын даалгавар , ажлын зураг талбаруудад domain дамжуулна
        '''
        group_id        = self.env['ir.model.data']._xmlid_to_res_id('nomin_project.group_project_confirmer')
        sel_user_ids    = self.env['res.users'].sudo().search([('groups_id','in',group_id)])
        emp_ids         = self.env['hr.employee'].sudo().search([('user_id','in',sel_user_ids.ids)])
        budgets         = self.env['control.budget'].sudo().search([('project_id','=',self.project_id.id)])
        tasks           = self.env['project.task'].sudo().search([('project_id','=',self.project_id.id),('task_state','in',('t_done','t_evaluate')),('task_type','=','work_task')]) 
        graphs          = self.env['project.task'].sudo().search([('project_id','=',self.project_id.id),('task_state','in',('t_done','t_evaluate')),('task_type','=','work_graph')])
        return {'domain':{
                          'budget_confirmer':[('id','in',emp_ids.ids)],
                          'task_id':[('id','in',tasks.ids)],
                          'work_graph_id':[('id','in',graphs.ids)],
                          }
                }
    
    def check_budget_limit(self):
        '''
            Боломжит үлдэгдэл шалгах
        '''
        if self.project_budget_material_real < self.material_cost:        
            raise ValidationError(_(u'Материалын зардлын дүн боломжит үлдэгдэлээс хэтэрсэн байна'))
        if self.project_budget_carriage_real < self.carriage_cost:
            raise ValidationError(_(u'Тээврийн зардлын дүн боломжит үлдэгдэлээс хэтэрсэн байна'))
        if self.project_budget_labor_real < self.labor_cost:
            raise ValidationError(_(u'Ажиллах хүчний зардлын дүн боломжит үлдэгдэлээс хэтэрсэн байна'))
        if self.project_budget_equipment_real < self.equipment_cost:
            raise ValidationError(_(u'Машин механизмын зардлын дүн боломжит үлдэгдэлээс хэтэрсэн байна'))
        if self.project_budget_postage_real < self.postage_cost:
            raise ValidationError(_(u'Шууд зардлын дүн боломжит үлдэгдэлээс хэтэрсэн байна'))
        if self.project_budget_other_real < self.other_cost:
            raise ValidationError(_(u'Бусад зардлын дүн боломжит үлдэгдэлээс хэтэрсэн байна'))
    

    def check_control_budget_limit(self):
        '''
            Боломжит үлдэгдэл шалгах
        '''
        
        for budget in self:
            if budget.project_id:
                
                if budget.project_id.budgeted_line_ids:
                    total = 0
                    for line in budget.project_id.budgeted_line_ids:
                        
                        if line.total_possible_balance:
                            if line.total_possible_balance  < budget.sub_total:
                                raise ValidationError(_(u'Хяналтын төсвийн дүн төслийн боломжит үлдэгдэлээс хэтэрсэн байна'))

                        if line.total_amount_of_control_budget == 0:
                            total = budget.sub_total
                        else:
                            total = line.total_amount_of_control_budget + budget.sub_total

                        line.write({'total_amount_of_control_budget':total})
                        
    def action_to_user(self):
        # self.check_budget_limit()
        self.write({'state':'user'})
    
    def action_start(self):
        '''
            Эхлэх товч
        '''
        for budget in self:
            if budget.project_id.project_flag:
                self.check_control_budget_limit()
            else:
                self.check_budget_limit()
            budget.write({'state':'start'})
        
    def action_close(self):
        '''
            Бодит гүйцэтгэл гарж дууссан эсэхийг шалгаад хаах
        '''
        if self.budgets_utilization_balance == 0:
            self.write({'state':'close'})
            for line in self.budgets_utilization:
                line.write({
                            'state':'close'
                            })
        else:
            raise ValidationError(_(u'Бодит гүйцэтгэл гарж дуусаагүй байна'))
    
    def action_new(self):
        history_confirm = self.env['main.specification.confirmers'].search([('budget_id', '=',self.id)])
        if history_confirm:
            history_confirm.unlink()
        
        for line in self.material_line_ids:
                line.write({
                            'state':'draft'
                            })
        for line in self.labor_line_ids:
            line.write({
                        'state':'draft'
                        })
        for line in self.equipment_line_ids:
            line.write({
                        'state':'draft'
                        })
        for line in self.carriage_line_ids:
            line.write({
                        'state':'draft'
                        })
        for line in self.postage_line_ids:
            line.write({
                        'state':'draft'
                        })
        for line in self.other_cost_line_ids:
            line.write({
                        'state':'draft'
                        })
        self.reject_control_budget()
        self.write({'state':'draft'})
        
    def action_to_confirm(self):
        '''
            Батлах төлөвт оруулах, зардлын мөрүүдийн төлвийг мөн өөрчлөх
        '''
       
        for budget in self:
            if not budget.project_id.project_flag:
                budget.check_budget_limit()
        self.write({'state':'confirm'})
        if self.task_id:
            for emp in self.budget_confirmer:
                self.task_id._add_followers(emp.user_id.id)
                self.task_id.project_id._add_followers(emp.user_id.id)
                
        if self.work_graph_id:
            for emp in self.budget_confirmer:
                self.work_graph_id._add_followers(emp.user_id.id)
                
        for line in self.material_line_ids:
                line.write({
                            'state':'request'
                            })
        for line in self.labor_line_ids:
            line.write({
                        'state':'request'
                        })
        for line in self.equipment_line_ids:
            line.write({
                        'state':'request'
                        })
        for line in self.carriage_line_ids:
            line.write({
                        'state':'request'
                        })
        for line in self.postage_line_ids:
            line.write({
                        'state':'request'
                        })
        for line in self.other_cost_line_ids:
            line.write({
                        'state':'request'
                        })
    def action_after(self):
        '''
            Шалтгаан бичээд хойшлуулах товч
        '''
        return {
            'name': 'Хяналтын төсөв хойшлуулах',
            'view_mode': 'form',
            'res_model': 'back.control.budget',
            'context': self._context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }
    
    def action_back(self):
        '''
            Хойшлогдсон төлвөөс буцааж хуучин төлөвт оруулах
        '''
        self.write({'state':self.back_state})
    
    def action_draft_back(self):
        '''
            Эхэлсэн төлөврүү буцаах
        '''
        self.write({'state':'start'})
    
    def action_confirmed(self):
        '''
            Батлах товч 
                Баталсан түүх бичнэ
                Хэрэв сүүлийн батлах хүн батлах товч дарахад батлагдсан төлөврүү орно
        '''
        ids = []
        main_specification_confirmers = self.env['main.specification.confirmers']
        employee = self.env['hr.employee']
        budgets_utilization = self.env['utilization.on.budget']
        employee_id = employee.sudo().search([('user_id','=',self._uid)])
        vals = {
                'budget_id' : self.id,
                'confirmer' : employee_id.id,
                'date'      : time.strftime('%Y-%m-%d %H:%M:%S'),
                'role'      : 'budget_confirmer',
                'state'     : 'confirmed',
                }
        main_specification_confirmers = main_specification_confirmers.create(vals)
        
        for budget in self:
            
            

                if self.is_show_confirmed == True:
                    if not budget.project_id.project_flag:
                        line = self.env['main.specification'].search([('parent_project_id', '=', self.project_id.id), ('confirm', '=', True)])
                        for budget in line.control_budget_ids:
                            ids.append(budget.id)
                        ids.append(self.id)
                        line.update({
                                    'control_budget_ids': [(6, 0, ids)]
                                    })
        #             МАТЕРИАЛ
                    departments = []
                    for material_line in self.material_line_ids:
                        if not material_line.department_id in departments:
                            departments.append(material_line.department_id)
                    for department in departments:
                        m_total = 0.0
                        for material_line in self.material_line_ids:
                            if department in material_line.department_id:
                                m_total += material_line.material_total
                        m_vals = {
                                'control_budget_id':self.id,
                                'budget_type':'material',
                                'department_id':department.id,
                                'value':u'Материалын зардал',
                                'price':m_total,
                                }
                        budgets_utilization = budgets_utilization.create(m_vals)
        #             Ажиллах хүч
                    for labor_line in self.labor_line_ids:
                        l_vals = {
                                'control_budget_id':self.id,
                                'budget_type':'labor',
                                'department_id':labor_line.department_id.id,
                                'value':labor_line.name,
                                'price':labor_line.labor_cost_basic,
                                }
                        budgets_utilization = budgets_utilization.create(l_vals)
        #             Машин механизм
                    for equipment_line in self.equipment_line_ids:
                        e_vals = {
                                'control_budget_id':self.id,
                                'budget_type':'equipment',
                                'department_id':equipment_line.department_id.id,
                                'value':equipment_line.name,
                                'price':equipment_line.equipment_total,
                                }
                        budgets_utilization = budgets_utilization.create(e_vals)
        #             Тээвэр
                    for carriage_line in self.carriage_line_ids:
                        c_vals = {
                                'control_budget_id':self.id,
                                'budget_type':'carriage',
                                'department_id':carriage_line.department_id.id,
                                'value':carriage_line.name,
                                'price':carriage_line.price,
                                }
                        budgets_utilization = budgets_utilization.create(c_vals)
        #             Шууд
                    for postage_line in self.postage_line_ids:
                        p_vals = {
                                'control_budget_id':self.id,
                                'budget_type':'postage',
                                'department_id':postage_line.department_id.id,
                                'value':postage_line.name,
                                'price':postage_line.price,
                                }
                        budgets_utilization = budgets_utilization.create(p_vals)
        #             Бусад
                    for other_line in self.other_cost_line_ids:
                        o_vals = {
                                'control_budget_id':self.id,
                                'budget_type':'other',
                                'department_id':other_line.department_id.id,
                                'value':other_line.name,
                                'price':other_line.price,
                                }
                        budgets_utilization = budgets_utilization.create(o_vals)
                                                                        
                    self.write({'state':'done',
                                'confirm_date':time.strftime('%Y-%m-%d %H:%M:%S'),})
                    
                    for line in self.material_line_ids:
                        line.write({
                                    'state':'confirm'
                                    })
                    for line in self.labor_line_ids:
                        line.write({
                                    'state':'confirm'
                                    })
                    for line in self.equipment_line_ids:
                        line.write({
                                    'state':'confirm'
                                    })
                    for line in self.carriage_line_ids:
                        line.write({
                                    'state':'confirm'
                                    })
                    for line in self.postage_line_ids:
                        line.write({
                                    'state':'confirm'
                                    })
                    for line in self.other_cost_line_ids:
                        line.write({
                                    'state':'confirm'
                                    })
                    
                self.handle_budget_consumption()
            # else:
            #     self.write({'state':'done',
            #                 'confirm_date':time.strftime('%Y-%m-%d %H:%M:%S'),})


    def action_evaluate(self):
        return {
            'name': 'Note',
            'view_mode': 'form',
            'res_model': 'rate.control.budget',
            'context': self._context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }
        
   
    def action_create_tender(self):
        '''
            Тендер үүсгэх товч
            Тендер үүсгэх цонх дуудах
        '''
        return {
            'name': 'Note',
            'view_mode': 'form',
            'res_model': 'create.project.tender',
            'context': self._context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }
    
    def action_budget_partner_comparison(self):
        '''
            Үнийн харьцуулалт үүсгэх товч
            Үнийн харьцуулалт үүсгэх цонх дуудах
        '''
        return {
            'name': 'Note',
            'view_mode': 'form',
            'res_model': 'create.partner.comparison.wizard',
            'context': self._context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }
   
    @api.onchange('project_id')
    def onchange_project_id(self):
        '''
            Төсөл солигдоход хөрөнгө оруулалтын төсөвлөсөн дүн , боломжит үлдэгдэл, үлдэгдэл талбаруудыг зардлуудаар харуулна
        '''
        for budget in self:
            if budget.project_id:
                for line in budget.project_id.main_line_ids:
                    if line.confirm == True:
                        budget.project_budget_material = line.material_line_real
                        budget.project_budget_carriage = line.carriage_real
                        budget.project_budget_labor = line.labor_line_real
                        budget.project_budget_equipment = line.equipment_line_real
                        budget.project_budget_postage = line.postage_line_real
                        budget.project_budget_other = line.other_line_real
                        
                        budget.project_budget_material_limit = line.material_line_limit
                        budget.project_budget_carriage_limit = line.carriage_limit
                        budget.project_budget_labor_limit = line.labor_line_limit
                        budget.project_budget_equipment_limit = line.equipment_line_limit
                        budget.project_budget_postage_limit = line.postage_line_limit
                        budget.project_budget_other_limit = line.other_line_limit
                        
                        budget.project_budget_material_real = line.material_line_total
                        budget.project_budget_carriage_real = line.carriage_cost
                        budget.project_budget_labor_real = line.labor_line_total
                        budget.project_budget_equipment_real = line.equipment_line_total
                        budget.project_budget_postage_real = line.postage_line_total
                        budget.project_budget_other_real = line.other_line_total
    
    
    def reject_control_budget(self):
        '''
            Холбоотой төслийн хяналтын төсвийг хасах 
        '''

        for budget in self:
            if budget.project_id.project_flag:                
                if budget.project_id.budgeted_line_ids:
                    for line in budget.project_id.budgeted_line_ids:
                        if line.total_amount_of_control_budget:
                            balance = line.total_amount_of_control_budget - budget.sub_total
                            line.write({'total_amount_of_control_budget':balance })

    
    def action_draft(self):
        '''
            Шинэ төлөврүү оруулах
        '''
        for budget in self:
            budget.reject_control_budget()    

    
        history_confirm = self.env['main.specification.confirmers'].search([('budget_id', '=',self.id)])
        if history_confirm:
            history_confirm.unlink()
        
        for line in self.material_line_ids:
                line.write({
                            'state':'draft'
                            })
        for line in self.labor_line_ids:
            line.write({
                        'state':'draft'
                        })
        for line in self.equipment_line_ids:
            line.write({
                        'state':'draft'
                        })
        for line in self.carriage_line_ids:
            line.write({
                        'state':'draft'
                        })
        for line in self.postage_line_ids:
            line.write({
                        'state':'draft'
                        })
        for line in self.other_cost_line_ids:
            line.write({
                        'state':'draft'
                        })
        
        self.write({'state':'draft'})
    
    
    def action_cancel(self):
        '''
            Төсөл Цуцлах цонх дуудна
        '''
        return {
            'name': 'Хяналтын төсөв цуцлах',
            'view_mode': 'form',
            'res_model': 'cancel.control.budget',
            'context': self._context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }

    
    
    def create_purchase_request(self):
        '''
            Худалдан авалтын шаардах үүсгэх цонх дуудах
        '''
        for task in self:
            return {
                    'name': 'Note',
                    'view_mode': 'form',
                    'res_model': 'create.purchase.requisition',
                    'context': task._context,
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                    }
    
    def action_import(self):
        '''
            Хяналтын төсвийн ажиллах хүчний зардал болон материалын зардал импортлох цонх дуудна
        '''

        return {
            'name': 'Импорт хийх',
            'view_mode': 'form',
            'res_model': 'import.control.budget',
            'context': self._context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }

class CancelControlBudget(models.Model):
    _name = 'cancel.control.budget'
    
    '''
        Хяналтын төсөв цуцлагдсан талаар тайлбар лог болон бичигдэнэ
    '''
    
    budget_id = fields.Many2one('control.budget')
    description = fields.Text(u'Тайлбар')
    
    def default_get(self):
        result = []
        if context is None:
            context = {}
        res = super(CancelControlBudget, self).default_get()    
        active_id = self.env.context and self.env.context.get('active_id', False) or False
        perform_obj = self.env['control.budget']
        perform = perform_obj.browse(active_id)
        res.update({
                    'budget_id' : perform.id,
                    })
        return res
    
    
    def action_cancel(self):
        self.budget_id.message_post(subject=_('Хяналтын төсөв цуцлагдлаа'), body="Цуцлагдсан шалтгаан : %s"%(self.description))
        self.budget_id.write({
                              'state':'cancel'
                              })
        self.budget_id.reject_control_budget()

class BackControlBudget(models.Model):
    _name = 'back.control.budget'
    '''
        Хяналтын Хойшлуулах төсөл хойшлогдсон талаар тайлбар лог болон бичигдэнэ
    '''
    
    budget_id = fields.Many2one('control.budget')
    description = fields.Text(u'Тайлбар')
    
    def default_get(self,fields):
        result = []
        if context is None:
            context = {}
        res = super(BackControlBudget, self).default_get( fields)    
        active_id = self.env.context and self.env.context.get('active_id', False) or False
        perform_obj = self.env['control.budget']
        perform = perform_obj.browse(active_id)
        res.update({
                    'budget_id' : perform.id,
                    })
        return res
    
    
    def action_cancel(self):
        self.budget_id.message_post(subject=_('Хяналтын төсөв хойшлогдлоо'), body="Хойшилсон шалтгаан : %s"%(self.description))
        state = self.budget_id.state
        self.budget_id.write({
                              'back_state':state,
                              'state':'after'
                              })
        self.budget_id.reject_control_budget()
#TODO FIX LATER controll.budget.line
# class ControllBudgetLine(models.Model):
#     _inherit = 'controll.budget.line'
#     budget_line_id = fields.Many2one('utilization.on.budget', string='Budget')
#     control_budget_id = fields.Many2one('control.budget', string='Control Budget',required=True)
     
#     @api.constrains('budget_line_id')
#     def _check_budget_line_id(self):
#         if self.budget_line_id:
#             self._cr.execute("select count(id) from controll_budget_line where budget_line_id = %s and parent_id = %s "
#                        "and id <> %s",(self.budget_line_id.id,self.parent_id.id, self.id))
#             fetched = self._cr.fetchone()
#             if fetched and fetched[0] and fetched[0] > 0:
#                 raise UserError((u'Төлбөрийн хүсэлтийн мөр дээр хяналтын төсвийн мөр давхар үүсэх боломжгүй!'))
            
class account_analytic_line(models.Model):
    _inherit = 'account.analytic.line'
    controll_budget_id = fields.Many2one('utilization.on.budget', string='Controll budget',readonly=True, ondelete="restrict")
#TODO FIX LATER 
# class BudgetBalanceCheckPayment(models.TransientModel):
#     _inherit = 'budget.balance.check.payment'
     
#     @api.model
#     def default_get(self, fields):
#         rec = super(BudgetBalanceCheckPayment, self).default_get(fields)
#         context = dict(self._context or {})
#         active_model = context.get('active_model')
#         active_ids = context.get('active_ids')
 
#         # Checks on context parameters
#         if not active_model or not active_ids:
#             raise UserError(_("Programmation error: wizard action executed without active_model or active_ids in context."))
#         payments = self.env[active_model].browse(active_ids)
         
#         is_hoat=False
#         if payments.tax_id and payments.tax_id.is_hoat:
#             is_hoat=True
         
         
#         untax_amount = payments.subtotal
#         amount = payments.amount
             
#         amount_currency=payments.amount_currency
#         department_id = payments.sector_id.id
#         cashflow_type = payments.ask_budget_type
         
#         partner_id=False
#         if payments.partner_id:
#             partner_id=payments.partner_id.id
#         result1=[]
#         result2=[]
#         result3=[]
#         control_budget_id=False
#         for line in payments:
#             for budget in line.nomin_budget_line_ids:
#                 result1.append((0, 0, {'account_id': payments.account_id.id, 
#                                           'internal_type': payments.account_id.internal_type, 
#                                           'department_id':department_id,
#                                           'cashflow_type':cashflow_type,
#                                           'accept_amount':budget.accept_amount,
#                                           'analytic_account_id':budget.analytic_account_id.id,
#                                           'budget_post_ids':[(6,0,budget.budget_post_ids.ids)],
#                                           'current_budget_month_id':budget.current_budget_month_id.id,
#                                           'budget_month_ids':[(6,0,budget.budget_month_ids.ids)],
#                                           'is_null_budget':False}))
         
#             for other_budget in line.other_budget_line_ids:
#                 result2.append((0,0,{'date':other_budget.date,
#                                      'analytic_account_id':other_budget.analytic_account_id.id,
#                                      'partner_id':partner_id,
#                                      'budget_id':other_budget.budget_line_id.parent_id.id,
#                                      'budget_line_id':other_budget.budget_line_id.id,
#                                      'accept_amount':other_budget.accept_amount,
#                                      }))
             
#             for control_budget in line.controll_budget_line_ids:
#                 control_budget_id=control_budget.control_budget_id.id if control_budget.control_budget_id else False
#                 result3.append((0,0,{'date':control_budget.date,
#                                      'analytic_account_id':control_budget.analytic_account_id.id,
#                                      'controll_budget_id':control_budget.budget_line_id.id,
#                                      'accept_amount':control_budget.accept_amount,
#                                      'budget_type':control_budget.budget_type
#                                      }))
                 
#         if 'nomin_budget_line_ids' in fields:
#             if rec['nomin_budget_line_ids'] == []:
#                 rec.update({'nomin_budget_line_ids': result1})
         
#         if 'other_budget_line_ids' in fields:
#             rec.update({'other_budget_line_ids': result2})
             
#         if 'controll_budget_line_ids' in fields:
#             rec.update({'controll_budget_line_ids': result3})
             
#         rec.update({
#             'date':payments.parent_id.date,
#             'budget_id':payments.other_budget_id.id if payments.other_budget_id else False,
#             'is_hoat':is_hoat,
#             'amount':amount,
#             'untax_amount':untax_amount,
#             'currency_id':payments.transaction_currency_id.id,
#             'is_other_currency':payments.is_other_currency,
#             'amount_currency':amount_currency,
#             'department_id':department_id,
#             'account_id':payments.account_id.id,
#             'cashflow_type':cashflow_type,
#             'is_controll_budget':payments.cashflow_account_id.is_controll_budget,
#             'partner_id':partner_id,
#             'control_budget_id':control_budget_id
#         })
#         return rec
     
#     control_budget_id = fields.Many2one('control.budget', string='Control Budget')
     
    
#     def ok_new(self):
#         month_budget_obj = self.env['nomin.budget.month.expense']
#         context = self._context
#         analytic_account_id=False
#         if self.nomin_budget_line_ids: 
#             budget_ids = []
#             sum_season = 0.0
#             line_amount = 0.0
    
#             if self.not_found_budget:
#                 name = ''
#                 check = False
#                 for line in self.nomin_budget_line_ids:
#                     for aa in self.not_found_budget:
#                         if aa.id == line.analytic_account_id.id:
#                             check = True
#                             break
    
#                 if check == True:
#                     for aa in self.not_found_budget:
#                         name += ' ' + aa.code+'-'+aa.name + ','
#                     raise UserError(u'Дараах шинжилгээний данснууд бизнес төлөвлөгөөнд тусгагдаагүй байна!!! %s'%(name))        
            
#             if self.nomin_budget_line_ids:
#                 for line in self.nomin_budget_line_ids:
#                     line_amount += line.accept_amount
        
#                 tt100 = round(float(self.untax_amount),2)
#                 tt00 = round(float(line_amount),2)
#                 if tt00 != tt100:
#                     raise UserError(u'Мөрүүд дээр хувиарласан дүнгүүдийн нийлбэр зардлын дүнтэй тэнцүү байх ёстой!!!')
    
#             self.env.cr.execute("select budget_id from account_budget_rel where account_id=%s order by budget_id"%(self.account_id.id))
#             fetched = self.env.cr.fetchall()
#             if fetched:
#                 budget_post = self.env['account.budget.post'].browse(fetched[0])
#                 if budget_post.not_ask_budget == False:
#                     account_period = self.env['account.period'].search([('date_start','<=',self.date),('date_stop','>=',self.date)])[0]
#                     account_season = self.env['account.period'].search([('fiscalyear_id','=',account_period.fiscalyear_id.id),('account_season','=',account_period.account_season),('date_stop','<=',account_period.date_stop)], order="id desc")
#                     for period in account_season.ids:
#                         budget_ids.extend(month_budget_obj.search([('general_budget_id','=', budget_post.id),
#                                                         ('month_id','=',period),                                                    
#                                                         ('state','=','done')], order='id desc'))
#                     if budget_ids != []:
#                         for budget in budget_ids:
#                             sum_season += budget.balance_resource_subtotal
    
#                     if sum_season != 0.0 and sum_season > self.amount:
#                         pass
#                     else:
#                         raise UserError(u'Төсвийн үлдэгдэл хүрэлцэхгүй байна!!! Төсвийн боломжит үлдэгдэл %s'%(sum_season))
    
#         if self.cashflow_type == 'other_budget_ask':
#             if not self.budget_id and not self.controll_budget_line_ids:
#                 raise UserError((u'Бусад төсөв эсвэл Хяналтын төсвээс заавал шалгах ёстой!'))
         
#         other_budget_id=False
#         if self.budget_id:
#             other_budget_id = self.budget_id.id
         
#         current_budget_month_id=False
#         if self.current_budget_month_id:
#             current_budget_month_id = self.current_budget_month_id.id
             
#         total = 0.0
#         amount_currency = self.amount_currency
#         is_bp=False
#         is_ob=False
#         is_cb=False
#         if context.get('active_model') and context.get('active_id'):
#             if context['active_model'] == 'payment.request.line' and context['active_id']:
#                 active_obj = self.env['payment.request.line'].browse(context['active_id'])
         
#                 remove_analytic_lines = self.env['budget.analytic.line'].search([('payment_request_line_id','=',active_obj.id)])
#                 if remove_analytic_lines:
#                     for ral in remove_analytic_lines:
#                         ral.unlink()
                 
#                 remove_other_budget_lines = self.env['other.budget.line'].search([('parent_id','=',active_obj.id)])
#                 if remove_other_budget_lines:
#                     for reob in remove_other_budget_lines:
#                         reob.unlink()
                         
#                 if self.cashflow_type == 'bp_ask' or self.internal_type == 'expense':
#                     if not self.nomin_budget_line_ids:
#                         raise UserError((u'Бизнес төлөвлөгөөнөөс заавал шалгах ёстой!'))                     
                             
#                     for budget_line in self.nomin_budget_line_ids:
#                             total += budget_line.accept_amount
#                             budget_month_ids=[]
#                             if budget_line.budget_month_ids:
#                                 budget_month_ids = budget_line.budget_month_ids.ids
                             
#                             current_budget_month_id=False
#                             if budget_line.current_budget_month_id:
#                                 current_budget_month_id = budget_line.current_budget_month_id.id
                             
#                             budget_post_ids=[]
#                             if budget_line.budget_post_ids:
#                                 budget_post_ids = budget_line.budget_post_ids.ids
                                 
#                             self.env['budget.analytic.line'].create({'payment_request_line_id':active_obj.id,
#                                                                   'analytic_account_id':budget_line.analytic_account_id.id,
#                                                                   'budget_post_ids':[(6,0,budget_post_ids)],
#                                                                   'current_budget_month_id':current_budget_month_id,
#                                                                   'budget_month_ids':[(6,0,budget_month_ids)],
#                                                                   'accept_amount':budget_line.accept_amount
#                                                                   })
#                             is_bp=True
#                     if not self.is_hoat:
#                         if total == self.untax_amount:
#                             total = self.amount
#                         else:
#                             if active_obj.tax_id:
#                                 total = total*1.1
                                 
#                 if other_budget_id:
#                     if self.controll_budget_line_ids:
#                         raise UserError((u'Мөнгөн урсгалын төсөв сонгосон учир Хяналтын төсөв давхар сонгох боломжгүй. Хяналтын төсвөө устгана уу!'))
                     
#                     total = 0.0
#                     is_budget_other_curr = False
#                     for other_budget_line in self.other_budget_line_ids:
#                             if other_budget_line.budget_line_id.is_other_currency:
#                                 is_budget_other_curr=True
                                 
#                             total += other_budget_line.accept_amount
#                             self.env['other.budget.line'].create({'parent_id':active_obj.id,
#                                                                   'analytic_account_id':other_budget_line.analytic_account_id.id,
#                                                                   'budget_line_id':other_budget_line.budget_line_id.id,
#                                                                   'accept_amount':other_budget_line.accept_amount,
#                                                                   'date':other_budget_line.date
#                                                                   })
#                             is_ob=True
#                     if is_budget_other_curr:
#                         if self.is_other_currency:
#                             rate = active_obj.currency_rate
#                             amount_currency = total
#                             total = total*rate
#                     else:
#                         if self.is_other_currency and active_obj.currency_rate > 0.0:
#                             amount_currency = total/active_obj.currency_rate
                 
                 
#                 if self.controll_budget_line_ids:
#                     if other_budget_id:
#                          raise UserError((u'Хяналтын төсөв сонгосон учир Мөнгөн урсгалын төсөв давхар сонгох боломжгүй. Мөнгөн урсгалын төсвөө устгана уу!'))
                     
#                     total = 0.0
#                     remove_controll_budget_line = self.env['controll.budget.line'].search([('parent_id','=',active_obj.id)])
#                     if remove_controll_budget_line:
#                         for ro in remove_controll_budget_line:
#                             ro.unlink()
#                     for controll_budget_line in self.controll_budget_line_ids:
#                         total += controll_budget_line.accept_amount
#                         cb_line = self.env['controll.budget.line'].create({'parent_id':active_obj.id,
#                                                                   'analytic_account_id':controll_budget_line.analytic_account_id.id,
#                                                                   'control_budget_id':self.control_budget_id.id,
#                                                                   'budget_line_id':controll_budget_line.controll_budget_id.id,
#                                                                   'accept_amount':controll_budget_line.accept_amount,
#                                                                   'date':controll_budget_line.date,
#                                                                   'budget_type':controll_budget_line.budget_type
#                                                                   })
#                         is_cb=True
                         
#                 account_id=False
#                 if self.account_id:
#                     account_id = self.account_id.id
                     
#                 if total == 0.0 and self.amount > 0.0:
#                     total = self.amount
                 
#                 active_obj.write({'account_id':account_id,
#                                   'other_budget_id':other_budget_id,
#                                   'amount':total,
#                                   'amount_currency':amount_currency})
                 
#         return {'type': 'ir.actions.act_window_close'}

# class ControllBudgetCheckLine(models.TransientModel):
#     _inherit = 'controll.budget.check.line'
     
#     controll_budget_id = fields.Many2one('utilization.on.budget', string='Control Budget line',required=True)
     
    
#     @api.onchange('controll_budget_id','accept_amount')
#     def onchange_budget(self):
#         res = {}
#         if self.controll_budget_id and self.accept_amount:
#             if self.controll_budget_id.balance < self.accept_amount:
#                 self.update({'accept_amount':self.controll_budget_id.balance})
#                 res = {
#                     'warning': {
#                         'title': u'Анхааруулга',
#                         'message': u'Зөвшөөрсөн дүн төсвийн үлдэгдэлээс их байна!'
#                             }
#                     }
#         return res
    
            