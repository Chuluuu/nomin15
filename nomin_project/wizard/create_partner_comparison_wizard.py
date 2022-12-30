# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.tools.translate import _
from openerp.exceptions import UserError, ValidationError
import openerp.addons.decimal_precision as dp
import time
from datetime import datetime, timedelta
from openerp.http import request

class CreatePartnerComparisonWizard(models.TransientModel):
    _name = 'create.partner.comparison.wizard'
    _description = 'create partner comparison wizard'
    

    result = []

    @api.model
    def default_get(self, fields):
        res = super(CreatePartnerComparisonWizard, self).default_get(fields) 
        context = dict(self._context or {})   
        active_id = context and context.get('active_id', False) or False
        perform_obj = self.env['control.budget']
        perform = perform_obj.browse(active_id)
        material_result = []
        new_material_result = []
        labor_result1= []
        labor_result2= []
        if perform.is_old2:
            for line in perform.material_line_ids:
                if line.cost_choose == True and line.state == 'confirm':
                    material_result.append((0,0,{'product_id': line.product_id.id,
                                                'product_uom':line.product_uom.id,
                                                'product_uom_qty':line.product_uom_qty,
                                                'price_unit':line.price_unit,
                                                'material_total':line.material_total,
                                                'name':line.name}))
            res.update({'material_line': material_result,})
        else:
            for line in perform.new_material_line_ids:
                if line.cost_choose == True and line.state == 'confirm':
                    new_material_result.append((0,0,{'product_name': line.product_name,
                                                    'product_uom':line.product_uom.id,
                                                    'product_uom_qty':line.product_uom_qty,
                                                    'price_unit':line.price_unit,
                                                    'material_total':line.material_total,
                                                    'name':line.name}))
            res.update({'new_material_line': new_material_result,})

        if perform.is_old:   
            for line in perform.labor_line_ids:
                if line.cost_choose == True and line.state == 'confirm':
                    labor_result1.append((0,0,{'product_id': line.product_id.id,
                                            'product_uom':line.product_uom.id,
                                            'product_uom_qty':line.product_uom_qty,
                                            'price_unit':line.price_unit,
                                            'labor_total':line.labor_total,
                                            'engineer_salary':line.engineer_salary,
                                            'extra_salary':line.extra_salary,
                                            'social_insurance':line.social_insurance,
                                            'habe':line.habe,
                                            'total_salary':line.total_salary,
                                            'labor_cost_basic':line.labor_cost_basic,
                                            'engineer_salary_percent':line.engineer_salary_percent,
                                            'extra_salary_percent':line.extra_salary_percent,
                                            'social_insurance_rate':line.social_insurance_rate,
                                            'habe_percent':line.habe_percent,
                                            'name':line.name}))
            res.update({'labor_line': labor_result1,})
            
        else:
            for line in perform.labor_line_ids1:
                if line.cost_choose == True and line.state == 'confirm':
                    labor_result2.append((0,0,{'product_name': line.product_name,
                                            'product_uom':line.product_uom.id,
                                            'product_uom_qty':line.product_uom_qty,
                                            'price_unit':line.price_unit,
                                            'labor_total':line.labor_total,
                                            'engineer_salary':line.engineer_salary,
                                            'extra_salary':line.extra_salary,
                                            'social_insurance':line.social_insurance,
                                            'habe':line.habe,
                                            'total_salary':line.total_salary,
                                            'labor_cost_basic':line.labor_cost_basic,
                                            'engineer_salary_percent':line.engineer_salary_percent,
                                            'extra_salary_percent':line.extra_salary_percent,
                                            'social_insurance_rate':line.social_insurance_rate,
                                            'habe_percent':line.habe_percent,
                                            'name':line.name}))
            res.update({'labor_line1': labor_result2,})
        res.update({
                    'control_budget_id' : perform.id,
                    'material_limit' : perform.material_utilization_limit,
                    'labor_limit' : perform.labor_utilization_limit,
                    'equipment_limit' : perform.equipment_utilization_limit,
                    'carriage_limit' : perform.carriage_utilization_limit,
                    'postage_limit' : perform.postage_utilization_limit,
                    'other_limit' : perform.other_utilization_limit,
                    # 'material_line': material_result,
                    'is_old': perform.is_old,
                    'is_old2': perform.is_old2,
                    'task_id' : perform.task_id.id,
                    'task_graph_id' : perform.work_graph_id.id,
                    })
        
        return res

    @api.multi
    def _total_amount(self):
        total = 0.0
        for budget in  self:
            for line in budget.control_budget_id.material_line_ids:
                if line.cost_choose == True and line.state == 'confirm':
                    total += line.material_total
            if budget.is_old:
                for line in budget.labor_line:
                    total += line.labor_cost_basic
            else:
                for line in budget.labor_line1:
                    total += line.labor_cost_basic
            total += budget.equipment_create
            total += budget.carriage_create
            total += budget.postage_create
            total += budget.other_create
            budget.total_amount = total

    control_budget_id   = fields.Many2one('control.budget', string = 'Budget')
    employee_id         = fields.Many2one('hr.employee',string = u'Хариуцагч')
    labor_create        = fields.Float(u'Ажиллах хүчний зардал',default=0.0)
    equipment_create    = fields.Float(u'Машин механизм зардал',default=0.0)
    carriage_create     = fields.Float(u'Тээврийн зардал',default=0.0)
    postage_create      = fields.Float(u'Шууд зардал',default=0.0)
    other_create        = fields.Float(u'Бусад зардал',default=0.0)
    
    labor_limit         = fields.Float(u'Ажиллах хүчний зардлын үлдэгдэл')
    equipment_limit     = fields.Float(u'Машин механизмын зардлын үлдэгдэл')
    carriage_limit      = fields.Float(u'Тээврийн зардлын үлдэгдэл')
    postage_limit       = fields.Float(u'Шууд зардлын үлдэгдэл')
    other_limit         = fields.Float(u'Бусад зардлын үлдэгдэл')
    
    material_line       = fields.One2many('partner.comparison.material.line','partner_comparison_id',string = u'Материалын зардал')
    new_material_line       = fields.One2many('partner.comparison.material.line','partner_comparison_id',string = u'Материалын зардал')
    labor_line          = fields.One2many('partner.comparison.labor.line','partner_comparison_id',string = u'Ажиллах хүчний зардал')
    labor_line1         = fields.One2many('partner.comparison.labor.line','partner_comparison_id',string = u'Ажиллах хүчний зардал')
    type_id             = fields.Many2one('tender.type', index=True, string=u'Ангилал',required=True)
    child_type_id       = fields.Many2one('tender.type', string=u'Дэд ангилал',required=True)
    desc_name           = fields.Char(u'Тодорхойлох нэр',required=True)
    control_budget_id   = fields.Many2one('control.budget', string = 'Budget')
    task_id             = fields.Many2one('project.task', index=True,string = u'Ажлын даалгавар',required=True, domain=[('task_type', '=','work_task'),('task_state','in',('t_confirm','t_evaluate','t_done'))])
    task_graph_id       = fields.Many2one('project.task', index=True,string = u'Ажлын зураг', domain=[('task_type', '=','work_graph'),('task_state','in',('t_confirm','t_evaluate','t_done'))])
    
    total_amount        = fields.Float(string=u'Нийт дүн',compute=_total_amount)
    is_old              = fields.Boolean(string="is old")
    is_old2              = fields.Boolean(string="is old2")
    
    @api.onchange('material_create','labor_create','equipment_create','carriage_create','postage_create','other_create')
    def onchange_types(self):
        '''
           хяналтын төсвийн боломжит үлдэгдэлээс хэтэрсэн эсэх шалгах
        '''
  
        total = 0.0
        for budget in  self:

            if budget.is_old2:
                for line in budget.control_budget_id.material_line_ids:
                    if line.cost_choose == True and line.state == 'confirm':
                        total += line.material_total
            else:
                for line in budget.control_budget_id.new_material_line_ids:
                    if line.cost_choose == True and line.state == 'confirm':
                        total += line.material_total

            if budget.is_old:
                for line in budget.labor_line:
                    total += line.labor_cost_basic
            else:
                for line in budget.labor_line1:
                    total += line.labor_cost_basic
            if budget.equipment_create <= budget.equipment_limit:
                total += budget.equipment_create
            else :
                raise ValidationError(_(u'Машин механизмын зардлын дүн хэтэрсэн байна'))
            if budget.carriage_create <= budget.carriage_limit:
                total += budget.carriage_create
            else :
                raise ValidationError(_(u'Тээврийн зардлын дүн хэтэрсэн байна'))
            if budget.postage_create <= budget.postage_limit:
                total += budget.postage_create
            else :  
                raise ValidationError(_(u'Шууд зардлын дүн хэтэрсэн байна'))
            if budget.other_create <= budget.other_limit:
                total += budget.other_create
            else :
                raise ValidationError(_(u'Бусад зардлын дүн хэтэрсэн байна'))
            
            budget.total_amount = total
    @api.onchange('type_id')
    def onchange_type(self):
        '''Aнгиллыг сонгоход түүнд 
           хамаарах дэд ангиллууд гарна
        '''
        self.update({'child_type_id':False})
        child_ids = []
        if self.type_id:
            type_ids = self.env['tender.type'].sudo().search([('parent_id','=',self.type_id.id)])
            child_ids.extend(type_ids.ids)
        return {'domain':{'child_type_id': [('id','=', child_ids)]}}

    @api.multi
    def action_create(self):
        budget = self.control_budget_id
        budget_partner_comparison = self.env['budget.partner.comparison']
        model_obj =self.env['ir.model.data']
        result = model_obj._get_id('nomin_project', 'view_budget_partner_comparison_form')
        view_id = model_obj.browse(result).res_id
        material_result = []
        new_material_result = []
        labor_result= []
        labor_result1= []

        if self.total_amount >= 36000000.0:
            raise ValidationError(_(u'Үнийн санал үүсгэх дүнгээс их байна. Тендер үүсгэнэ үү!!'))
        if self.total_amount <= 0.0:
            raise ValidationError(_(u'Үнийн санал үүсгэх дүнгээс бага байна.'))

        if self.is_old2 and self.material_line:

            for line in budget.material_line_ids:
                if line.cost_choose == True and line.state == 'confirm':
                    material_result.append((0,0,{'product_id': line.product_id.id,
                                        'product_uom':line.product_uom.id,
                                        'product_uom_qty':line.product_uom_qty,
                                        'price_unit':line.price_unit,
                                        'material_total':line.material_total,
                                        'partner_comparison_id' : line.id,
                                        'name':line.name}))
                    line.write({'state' : 'comparison'})

        elif not self.is_old2 and self.new_material_line:
            for line in budget.new_material_line_ids:
                if line.cost_choose == True and line.state == 'confirm':
                    new_material_result.append((0,0,{'product_name': line.product_name,
                                        'product_uom':line.product_uom.id,
                                        'product_uom_qty':line.product_uom_qty,
                                        'price_unit':line.price_unit,
                                        'material_total':line.material_total,
                                        'partner_comparison_id' : line.id,
                                        'name':line.name}))
                    line.write({'state' : 'comparison'})

        
        
        if self.is_old and self.labor_line:   
            for line in budget.labor_line_ids:
                if line.cost_choose == True and line.state == 'confirm':
                    labor_result.append((0,0,{'product_id': line.product_id.id,
                                            'product_uom':line.product_uom.id,
                                            'product_uom_qty':line.product_uom_qty,
                                            'price_unit':line.price_unit,
                                            'labor_total':line.labor_total,
                                            'engineer_salary':line.engineer_salary,
                                            'extra_salary':line.extra_salary,
                                            'social_insurance':line.social_insurance,
                                            'habe':line.habe,
                                            'total_salary':line.total_salary,
                                            'labor_cost_basic':line.labor_cost_basic,
                                            'engineer_salary_percent':line.engineer_salary_percent,
                                            'extra_salary_percent':line.extra_salary_percent,
                                            'social_insurance_rate':line.social_insurance_rate,
                                            'habe_percent':line.habe_percent,
                                            'name':line.name}))
                    line.write({'state' : 'comparison'})
        elif not self.is_old and self.labor_line1:
            for line in budget.labor_line_ids1:
                if line.cost_choose == True and line.state == 'confirm':
                    labor_result1.append((0,0,{'product_name': line.product_name,
                                            'product_uom':line.product_uom.id,
                                            'product_uom_qty':line.product_uom_qty,
                                            'price_unit':line.price_unit,
                                            'labor_total':line.labor_total,
                                            'engineer_salary':line.engineer_salary,
                                            'extra_salary':line.extra_salary,
                                            'social_insurance':line.social_insurance,
                                            'habe':line.habe,
                                            'total_salary':line.total_salary,
                                            'labor_cost_basic':line.labor_cost_basic,
                                            'engineer_salary_percent':line.engineer_salary_percent,
                                            'extra_salary_percent':line.extra_salary_percent,
                                            'social_insurance_rate':line.social_insurance_rate,
                                            'habe_percent':line.habe_percent,
                                            'name':line.name}))
                    line.write({'state' : 'comparison'})
                    
                
        if budget:
            if budget.task_id:
                for line in budget.task_id.work_document:
                    line.write({'public' : True})
            if budget.work_graph_id:
                for line in budget.work_graph_id.work_document:
                    line.write({'public' : True})
            vals = {
                'control_budget_id' : budget.id,
                'project_id'        : budget.project_id.id,
                'employee_id'       : self.employee_id.id,
                'task_id'           : self.task_id.id,
                'task_graph_id'     : self.task_graph_id.id,
                'material_cost_ids' : material_result,
                'new_material_cost_ids' : new_material_result,
                'labor_cost_ids'    : labor_result,
                'labor_cost_ids1'    : labor_result1,
                'equipment_cost'    : self.equipment_create,
                'carriage_cost'     : self.carriage_create,
                'postage_cost'      : self.postage_create,
                'other_cost'        : self.other_create,
                'department_id'     : self.employee_id.department_id.id,
                'desc_name'         : self.desc_name,
                'type_id'           : self.type_id.id,
                'child_type_id'     : self.child_type_id.id,
                'total_amount'      : self.total_amount
            }
        budget_partner_comparison = budget_partner_comparison.create(vals)
        
        if self.employee_id:
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            action_id = self.env['ir.model.data'].get_object_reference('nomin_project', 'action_budget_partner_comparison')[1]
            db_name = request.session.db
            body_html = """ <p>Сайн байна уу ?</p>
                            <p>Таньд "%s" үнийн харьцуулалтыг гүйцэтгэх захиалга ирлээ.</p>
                            <p><b>Төсөл:</b> %s</p>
                            <p><b>Хяналтын төсөв:</b> %s</p>       
                            <p><b>Үнийн харьцуулалт:</b></p>
                            <p>"%s" -н мэдээллийг <b><a href=%s/web?db=%s#id=%s&view_type=form&model=budget.partner.comparison&action=%s>%s</a></b> линкээр дамжин харна уу.</p>
                            <br/>                    
                            <p>Энэхүү мэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
                            <p>Баярлалаа.</p>
                        """%(self.desc_name,
                            budget.project_id.name,
                            budget.name,
                            self.desc_name,
                            base_url,
                            db_name,
                            budget_partner_comparison.id,
                            action_id,
                            self.desc_name,)
            subject = 'Таньд "%s" үнийн харьцуулалтыг гүйцэтгэх захиалга ирлээ.'%self.desc_name
            email_template = self.env['mail.mail'].sudo().create({
                        'name': ('Followup '),
                        'email_from': self.env.user.email or '',
                        'model_id': self.env['ir.model'].sudo().search([('model', '=', 'budget.partner.comparison')]).id,
                        'subject': subject,
                        'model':'budget.partner.comparison',
                        'email_to':self.employee_id.name,
                        'lang': self.env.user.lang,
                        'auto_delete': True,
                        'body_html':body_html,
                    })
            email_template.send()

        return {
                     'type': 'ir.actions.act_window',
                     'name': _('Register Call'),
                     'res_model': 'budget.partner.comparison',
                     'view_type' : 'tree',
                     'view_mode' : 'form',
                     'search_view_id' : view_id,
                     'res_id':budget_partner_comparison.id,
                     'target' : 'current',
                     'nodestroy' : True,
                 }
class PartnerComparisonMaterialLine(models.TransientModel):
    _name = 'partner.comparison.material.line'
    _description = 'partner comparison material line'

    @api.model
    def _amount(self):
        for obj in self:
            obj.material_total = obj.product_uom_qty * obj.price_unit


    partner_comparison_id = fields.Many2one('create.partner.comparison.wizard',string="wizard")
    product_id=fields.Many2one('product.product', string='Product',required = False, domain=[('product_tmpl_id.is_new','=',True),('product_tmpl_id.cost_price','>',0)])
    product_uom=fields.Many2one('product.uom',string='Unit of Measure',required = False)
    product_uom_qty=fields.Float(string = 'Estimated Quantity',required = False,default=1)
    price_unit=fields.Float(string = 'Estimated price',required = False)
    material_total=fields.Float(compute=_amount, digits_compute=dp.get_precision('Account'), string='Total', type='float', help="The material amount.")
    name = fields.Char(string = 'name')
    product_name=fields.Char(string ='Product name')


class PartnerComparisonLaborLine(models.TransientModel):
    _name = 'partner.comparison.labor.line'
    _description = 'partner comparison labor line'

    @api.model
    def _amount(self):
        for obj in self:
            obj.labor_total = obj.product_uom_qty * obj.price_unit

    @api.model
    @api.depends('product_name','price_unit','product_uom_qty')
    def _set_engineer_salary(self):
        for obj in self:
            if not obj.engineer_salary_percent:
                settings = self.env['labor.cost.settings'].search([(1,'=',1)])
                obj.engineer_salary_percent = settings.engineer_salary

    @api.model
    def _engineer_salary(self):
        for obj in self:            
            obj.engineer_salary = obj.labor_total * obj.engineer_salary_percent / 100
    
    @api.model
    @api.depends('product_name','price_unit','product_uom_qty')
    def _set_extra_salary(self):
        for obj in self:
            if not obj.extra_salary:
                settings = self.env['labor.cost.settings'].search([(1,'=',1)])
                obj.extra_salary_percent = settings.extra_salary

    @api.model
    def _extra_salary(self):
        for obj in self:
            obj.extra_salary = obj.labor_total * obj.extra_salary_percent / 100

    @api.model
    def _total_salary(self):
        for obj in self:
            obj.total_salary = obj.labor_total + obj.engineer_salary + obj.extra_salary
            
    @api.model
    @api.depends('product_name','price_unit','product_uom_qty')
    def _set_social_insurance_rate(self):
        for obj in self:
            if not obj.social_insurance_rate:
                settings = self.env['labor.cost.settings'].search([(1,'=',1)])
                obj.social_insurance_rate = settings.social_insurance_rate

    @api.model
    def _social_insurance(self):
        for obj in self:
            obj.social_insurance = obj.total_salary * obj.social_insurance_rate / 100
    
    
    @api.model
    @api.depends('product_name','price_unit','product_uom_qty')
    def _set_HABE(self):
        for obj in self:
            if not obj.habe_percent:
                settings = self.env['labor.cost.settings'].search([(1,'=',1)])
                obj.habe_percent = settings.habe_percent

    @api.model
    def _HABE(self):
        for obj in self:
            obj.habe = obj.total_salary * obj.habe_percent / 100

    @api.model
    def _labor_cost_basic(self):
        for obj in self:
            obj.labor_cost_basic = obj.total_salary + obj.social_insurance + obj.habe


    partner_comparison_id = fields.Many2one('create.partner.comparison.wizard',string="wizard")        
    product_id=fields.Many2one('product.product', string='Product', domain=[('product_tmpl_id.is_new','=',True),('product_tmpl_id.cost_price','>',0)])
    product_uom=fields.Many2one('product.uom',string='Unit of Measure')
    product_name=fields.Char(string = 'Names' )
    product_uom_qty=fields.Float(string = 'Estimated Quantity',default=1)
    price_unit=fields.Float(string = 'Estimated price')
    labor_total=fields.Float(compute=_amount, digits_compute=dp.get_precision('Account'), string='Total', type='float', help="The material amount.")
    engineer_salary= fields.Float(compute=_engineer_salary, string="Инженер техникийн ажилчдын цалин")
    extra_salary = fields.Float(compute=_extra_salary, string="Нэмэгдэл цалин")
    social_insurance = fields.Float(compute=_social_insurance, string="Нийгмийн даатгал")
    habe = fields.Float(compute=_HABE, string="ХАБЭ")
    total_salary = fields.Float(compute=_total_salary, string="Нийт цалин")
    labor_cost_basic = fields.Float(compute=_labor_cost_basic, string="Ажиллах хүчний зардал /Үндсэн/")
    name = fields.Char(string = 'name')
    engineer_salary_percent = fields.Float(string="Инженер техникийн ажилчдын цалингийн хувь", compute=_set_engineer_salary ,store=True)
    extra_salary_percent = fields.Float(string="Нэмэгдэл цалингийн хувь" , compute=_set_extra_salary ,store=True)
    social_insurance_rate = fields.Float(string="Нийгмийн даатгалын хувь", compute=_set_social_insurance_rate ,store=True)
    habe_percent = fields.Float(string="ХАБЭ хувь", compute=_set_HABE ,store=True)