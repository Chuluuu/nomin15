# -*- coding: utf-8 -*-
from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import time

class ProjectBudget(models.Model):
    _name = 'project.budget'

    @api.depends('line_ids','line_ids.material_cost','line_ids.labor_cost','line_ids.equipment_cost','line_ids.carriage_cost','line_ids.postage_cost','line_ids.other_cost')
    def _compute_total(self):
        for budget in self:
            total_material_cost  = 0
            total_labor_cost = 0
            total_equipment_cost = 0
            total_carriage_cost = 0
            total_postage_cost = 0
            total_other_cost =0
            for line in budget.line_ids:
                total_material_cost =total_material_cost+ line.material_cost
                total_labor_cost =total_labor_cost+ line.labor_cost
                total_equipment_cost =total_equipment_cost+ line.equipment_cost
                total_carriage_cost =total_carriage_cost + line.carriage_cost
                total_postage_cost =total_postage_cost + line.postage_cost
                total_other_cost =total_other_cost + line.other_cost
            budget.total_material_cost = total_material_cost
            budget.total_labor_cost = total_labor_cost
            budget.total_equipment_cost = total_equipment_cost
            budget.total_carriage_cost = total_carriage_cost
            budget.total_postage_cost = total_postage_cost
            budget.total_other_cost = total_other_cost
    

    @api.depends('sum_of_budgeted_amount','approximate_amount','sum_of_subproject')
    def _compute_amount(self):
        for budget in self:
            balance  = 0
            if budget.project_id:         
                balance = budget.approximate_amount - budget.sum_of_budgeted_amount           
                budget.possible_amount_create_project = balance
            if budget.project_id.parent_project: 
                parent_project_budget = self.env['project.budget'].search([('parent_project_id','=',budget.project_id.parent_project.id),('department_id','=',budget.project_id.department_id.id)])
                for line in parent_project_budget:
                    if line.investment_pattern in budget.project_id.project_categ.specification_ids:
                        if line.possible_amount_create_project == 0.0:
                            budget.update({'possible_amount_create_project': 0.0})
            else:
                balance = budget.approximate_amount - budget.sum_of_subproject           
                budget.possible_amount_create_project = balance


    @api.depends('sum_of_control_budget','sum_of_purchase_requisition') 
    def _compute_sum_total(self):
        for budget in self:
            total  = 0
            if budget:                
                total = budget.sum_of_control_budget + budget.sum_of_purchase_requisition          
                budget.sum_of_budget_and_purchase = total
                if budget.sum_of_budget_and_purchase == 0.0:
                    budget.possible_budgeting = budget.possible_amount_create_project
                else:
                    budget.possible_budgeting = budget.approximate_amount - total


    @api.depends('budgeted_ids.total_amount_of_control_budget') 
    def _compute_sum_control_budget(self):
        for budget in self:
            total = 0
            budget.sum_of_control_budget = 0
            for line in budget.parent_project_id.parent_budgeted_line_ids:
                if line.investment_pattern == budget.investment_pattern and line.department_id == budget.department_id :
                    total += line.total_amount_of_control_budget
                    budget.sum_of_control_budget = total
    

    @api.depends('budgeted_ids.budgeted_amount') 
    def _compute_sum_of_subproject(self):
        for budget in self:
            budget.sum_of_subproject = 0
            total = 0
            for line in budget.parent_project_id.parent_budgeted_line_ids:
                if line.investment_pattern == budget.investment_pattern and line.department_id == budget.department_id :
                    total += line.budgeted_amount
                    budget.sum_of_subproject = total
    

    @api.depends('budgeted_ids.total_amount_of_purchase_requisition') 
    def _compute_sum_pur_req(self):
        for budget in self:
            total = 0
            budget.sum_of_purchase_requisition= 0
            for line in budget.parent_project_id.parent_budgeted_line_ids:
                if line.investment_pattern == budget.investment_pattern and line.department_id == budget.department_id :
                    total += line.total_amount_of_purchase_requisition
                    budget.sum_of_purchase_requisition = total
    

    @api.depends('budgeted_ids.total_amount_of_contract') 
    def _compute_sum_contract(self):
        for budget in self:
            total = 0
            budget.sum_of_contract = 0
            for line in budget.parent_project_id.parent_budgeted_line_ids:
                if line.investment_pattern == budget.investment_pattern and line.department_id == budget.department_id :
                    total += line.total_amount_of_contract
                    budget.sum_of_contract = total
    


    @api.depends('budgeted_ids.total_amount_of_payment_request') 
    def _compute_sum_payment(self):
        for budget in self:
            total = 0
            budget.sum_of_payment_request = 0
            for line in budget.parent_project_id.parent_budgeted_line_ids:
                if line.investment_pattern == budget.investment_pattern and line.department_id == budget.department_id :
                    total += line.total_amount_of_payment_request
                    budget.sum_of_payment_request = total
    
    @api.depends('sum_of_contract','sum_of_payment_request') 
    def _compute_sum_spent(self):
        for budget in self:
            total  = 0
            if budget:                
                total = budget.sum_of_contract + budget.sum_of_payment_request          
                budget.amount_that_can_be_spent = budget.approximate_amount - total


            
                

    

    def _default_attrs(self):
        context = self._context
        default_attribute = context.get('default_attrs',False)
        return default_attribute
    

    def _default_type(self):
        context = self._context
        default_type_attribute = context.get('default_type',False)
        return default_type_attribute


    specification_id = fields.Many2one('project.specification',string="Specification")
    total_material_cost = fields.Float(string="Total Cost of material",compute="_compute_total",store=True)
    total_labor_cost = fields.Float(string="Total Cost of labor",compute="_compute_total",store=True)
    total_equipment_cost = fields.Float(string="Total Cost of equipments",compute="_compute_total",store=True)
    total_carriage_cost = fields.Float(string="Total Cost of transportations",compute="_compute_total",store=True)
    total_postage_cost = fields.Float(string="Total Postage costs",compute="_compute_total",store=True)
    total_other_cost = fields.Float(string="Total Other costs",compute="_compute_total",store=True)
    project_id = fields.Many2one('project.project',string="Төсөл")
    parent_project_id = fields.Many2one('project.project',string="Parent project")
    line_ids = fields.One2many('project.budget.line','project_budget_id', string="Lines")
    budgeted_ids = fields.One2many('budgeted.line','budgeted_id', string="Budgeted")

    #add new field
    investment_pattern = fields.Many2one('project.specification',string="Investment pattern")
    department_id = fields.Many2one('hr.department',string="Department")
    approximate_amount = fields.Float(string="Approximate amount") 
    budget_amount = fields.Float(string="Budget amount")
    possible_balance = fields.Float(string="Possible balance",compute="_compute_possible_balance",store=True)
    possible_amount_create_project = fields.Float(string="Батлагдсан дүнгийн үлдэгдэл" , compute="_compute_amount")
    surplus_amount = fields.Float(string="Тодотгол")
    sum_of_subproject = fields.Float(string="Дэд төслүүдийн нийлбэр дүн" , compute='_compute_sum_of_subproject')
    sum_of_control_budget = fields.Float(string="Хяналтын төсвийн нийлбэр" , compute='_compute_sum_control_budget')
    sum_of_purchase_requisition = fields.Float(string="Худалдан авалтын нийлбэр" , compute='_compute_sum_pur_req')
    sum_of_budget_and_purchase = fields.Float(string="Нийт" , compute="_compute_sum_total")
    possible_budgeting =  fields.Float(string="Төсөв үүсгэх боломжит дүн" , compute="_compute_sum_total")
    sum_of_contract = fields.Float(string="Гэрээний нийт дүн" , compute="_compute_sum_contract")
    sum_of_payment_request = fields.Float(string="Төлбөрийн хүсэлтийн нийт дүн" , compute="_compute_sum_payment")
    amount_that_can_be_spent = fields.Float(string="Зарцуулах боломжтой дүн" , compute='_compute_sum_spent')
    state =  fields.Selection(selection=[('draft',u'Ноорог'), 
                                ('sent',u'Илгээгдсэн'), 
                                ('approved',u'Зөвшөөрсөн'),
                                ('confirmed',u'Баталсан'),
                                ('modified',u'Тодотгосон'),
                                ('rejected',u'Татгалзсан'),
                                ('closed',u'Хаагдсан'),
                                ],
                                string = 'State',  copy=False, default='draft', tracking=True)

    default_attrs = fields.Boolean(string="Is parent project", default=_default_attrs)
    default_type = fields.Boolean(string="Is sub project", default=_default_type)
    invisible_button = fields.Boolean(string="Invisible button" , default=False)
    sum_of_budgeted_amount = fields.Float(string="Sum of budgeted amount" ,readonly=True)

    


    @api.model
    def create(self,vals):


        result = super(ProjectBudget, self).create(vals)
        total = 0
        if result.parent_project_id:
            for line in result.parent_project_id.parent_budget_line_ids:
                if line.approximate_amount:
                    total += line.approximate_amount 
            result.parent_project_id.update({'total_limit':total})
        





        return result



    
    def write(self,vals):
        result = super(ProjectBudget, self).write(vals)
        # total = 0
        # if vals.get('approximate_amount'):            
        #     for line in self.parent_project_id.parent_budget_line_ids:
        #         total += line.approximate_amount             
        #     self.parent_project_id.update({'total_limit': total})



            # query = """UPDATE 
            #     project_budget pb
            # SET 
            #     approximate_amount = %s
            # FROM 
            #     project_project pp
            # WHERE 
            #     pb.project_id = pp.id and pp.parent_project=%s"""%(vals.get('approximate_amount'),self.parent_project_id.id)
            
            # if self.parent_project_id:

            #     self.env.cr.execute(query)

            
        return result
    


class ProjectBudgetLine(models.Model):
    _name ='project.budget.line'



    
    def _line_limit(self):
        '''Хөрөнгө оруулалтын батлагдсан хяналтын төсвүүдийн ажиллах хүчний зардлын нийт дүНгээр үлдэгдэл тооцох
        '''
        for line in self:
            labor_total = 0.0
            material_total = 0.0
            equipment_total = 0.0
            postage_total = 0.0
            other_total = 0.0
            carriage_total = 0.0
            if line.material_cost:
                material_total += line.material_cost
            if line.labor_cost:
                labor_total += line.labor_cost
            if line.equipment_cost:
                equipment_total += line.equipment_cost
            if line.carriage_cost:
                carriage_total += line.carriage_cost
            if line.postage_cost:
                postage_total += line.postage_cost
            if line.other_cost:
                other_total += line.other_cost

            line.labor_line_limit_new = labor_total
            line.material_line_limit_new = material_total
            line.equipment_line_limit_new = equipment_total
            line.postage_line_limit_new = postage_total
            line.other_line_limit_new = other_total
            line.carriage_limit_new = carriage_total

    
    def _material_line_total_new(self):
        '''Хөрөнгө оруулалтын батлагдахаар хүлээж буй хяналтын төсвүүдийн материалын зардлын нийт дүн
        '''

        for line in self:
            if line.project_budget_id.project_id.id:
                self.env.cr.execute("select sum(product_uom_qty*price_unit) from material_budget_line where parent_id in (select id from control_budget where project_id= %s)"%(line.project_budget_id.project_id.id))
                res = self.env.cr.fetchone()[0] or 0.0
                line.material_line_total_new =  line.material_line_limit_new - res


    
    
    def _equipment_line_total_new(self):
        '''Хөрөнгө оруулалтын батлагдахаар хүлээж буй хяналтын төсвүүдийн машин механизм зардлын нийт дүн
        '''
        for line in self:
            if line.project_budget_id.project_id.id:
                self.env.cr.execute("select sum(product_uom_qty*price_unit) from equipment_budget_line where parent_id in (select id from control_budget where project_id= %s )"%(line.project_budget_id.project_id.id))
                res = self.env.cr.fetchone()[0] or 0.0
                line.equipment_line_total_new = line.equipment_line_limit_new - res
    

    
    def _labor_line_total_new(self):
        '''Хөрөнгө оруулалтын батлагдахаар хүлээж буй хяналтын төсвүүдийн ажиллах хүчний зардлын нийт дүн
        '''

        for line in self:
            if line.project_budget_id.project_id.id:
                self.env.cr.execute("select sum(product_uom_qty*price_unit + \
                                                product_uom_qty*price_unit *engineer_salary_percent /100 + \
                                                product_uom_qty*price_unit*extra_salary_percent/100 + \
                                                product_uom_qty*price_unit*habe_percent/100 + \
                                                product_uom_qty*price_unit*social_insurance_rate/100) \
                                                    from labor_budget_line where parent_id in \
                                                        (select id from control_budget where project_id= %s )"%(line.project_budget_id.project_id.id))
                res = self.env.cr.fetchone()[0] or 0.0
                line.labor_line_total_new = line.labor_line_limit_new - res
    
    
    def _carriage_cost_total_new(self):
        '''Хөрөнгө оруулалтын батлагдахаар хүлээж буй хяналтын төсвүүдийн тээврийн зардлын нийт дүн
        '''
        for line in self:
            # line.carriage_cost = 0
            line.carriage_cost_new = 0
            if line.project_budget_id.project_id.id:
                self.env.cr.execute("select sum(price) from carriage_budget_line where parent_id in (select id from control_budget where project_id= %s )"%(line.project_budget_id.project_id.id))
                res = self.env.cr.fetchone()[0] or 0.0
                line.carriage_cost = line.carriage_limit_new - res
                line.carriage_cost_new = line.carriage_limit_new - res

    

    
    def _postage_line_total_new(self):
        '''Хөрөнгө оруулалтын батлагдахаар хүлээж буй хяналтын төсвүүдийн шууд зардлын нийт дүн
        '''
        for line in self:
            if line.project_budget_id.project_id.id:
                self.env.cr.execute("select sum(price) from postage_budget_line where parent_id in (select id from control_budget where project_id= %s )"%(line.project_budget_id.project_id.id))
                res = self.env.cr.fetchone()[0] or 0.0
                line.postage_line_total_new = line.postage_line_limit_new - res
    

    
    def _other_line_total_new(self):
        '''Хөрөнгө оруулалтын батлагдахаар хүлээж буй хяналтын төсвүүдийн бусад зардлын нийт дүн
        '''
        for line in self:
            if line.project_budget_id.project_id.id:
                self.env.cr.execute("select sum(price) from other_cost_budget_line where parent_id in (select id from control_budget where project_id= %s )"%(line.project_budget_id.project_id.id))
                res = self.env.cr.fetchone()[0] or 0.0
                line.other_line_total_new = line.other_line_limit_new - res



    STATE_SELECTION = [('new',u'Шинэ'), 
                        ('sent',u'Илгээгдсэн'), 
                        ('approved',u'Зөвшөөрсөн'),
                        ('confirmed',u'Баталсан'),
                        ('modified',u'Тодотгосон'),
                        ('rejected',u'Татгалзсан'),
                        ('closed',u'Хаагдсан'),
                        ]

    project_budget_id = fields.Many2one('project.budget', string="Lines")
    department_id = fields.Many2one('hr.department',tring="Department")
    material_cost = fields.Float(string="Cost of material")
    labor_cost = fields.Float(string="Cost of labor")
    equipment_cost = fields.Float(string="Cost of equipments")
    carriage_cost = fields.Float(string="Cost of transportations")
    postage_cost = fields.Float(string="Postage costs")
    other_cost = fields.Float(string="Other costs")
    description = fields.Text(string="Description")
    total_cost = fields.Float(string = 'Total cost')
    state  = fields.Selection(selection=STATE_SELECTION,string = 'Төлөв' , default = 'new', tracking=True , readonly=True)

    labor_line_limit_new  = fields.Float(u'Ажиллах хүчний зардлын төсөвлөсөн дүн',    compute = _line_limit)
    material_line_limit_new     = fields.Float(u'Материалын зардлын төсөвлөсөн дүн',        compute = _line_limit)
    equipment_line_limit_new    = fields.Float(u'Машин механизмын зардлын төсөвлөсөн дүн',  compute = _line_limit)
    postage_line_limit_new      = fields.Float(u'Шууд зардлын төсөвлөсөн дүн',              compute = _line_limit)
    other_line_limit_new        = fields.Float(u'Бусад зардлын төсөвлөсөн дүн',             compute = _line_limit)
    carriage_limit_new          = fields.Float(u'Тээврийн зардлын төсөвлөсөн дүн',          compute = _line_limit)

    material_line_total_new     = fields.Float(u'Боломжит үлдэгдэл',compute=_material_line_total_new)
    labor_line_total_new        = fields.Float(u'Боломжит үлдэгдэл',compute=_labor_line_total_new)
    equipment_line_total_new    = fields.Float(u'Боломжит үлдэгдэл',compute=_equipment_line_total_new)
    postage_line_total_new      = fields.Float(u'Боломжит үлдэгдэл',compute=_postage_line_total_new)
    other_line_total_new        = fields.Float(u'Боломжит үлдэгдэл',compute=_other_line_total_new)
    carriage_cost_new           = fields.Float(u'Боломжит үлдэгдэл',compute=_carriage_cost_total_new)

    
    


    @api.model
    def create(self,vals):
        '''
           6 зардлаар төлөвлөх
        '''

        total = 0 
        balance = 0
        # actual_balance = 0
        result = super(ProjectBudgetLine, self).create(vals)
        if result.project_budget_id.approximate_amount == 0.0:
            raise ValidationError(_(u'Дэд төсөл бол Эцэг төслийн төлөвлөлтөөс үүснэ'))
        if result:
            total = result.material_cost + result.labor_cost + result.equipment_cost + result.carriage_cost + result.postage_cost + result.other_cost
        result.total_cost = total
        if result.state == 'new':
            budget = result.project_budget_id
            for line in budget:
                line.project_id.total_limit = total
                line.sum_of_budgeted_amount = total
            
        # if budget.surplus_amount == 0:
        #     budget.possible_amount_create_project = budget.approximate_amount - total
        # else:
        #     budget.possible_amount_create_project = budget.surplus_amount - total
            # if line.possible_amount_create_project < result.total_cost:
            #     print '\n\n\n hahaha ' , line.possible_amount_create_project , result.total_cost
            #     raise ValidationError(_(u'Төлөвлөсөн дүн батлагдсан дүнгийн үлдэгдлээс хэтэрсэн байна'))
            line.possible_amount_create_project = line.approximate_amount - total
        budget = result.project_budget_id
        budgeted = self.env['budgeted.line'].sudo().search([('project_id','=',budget.project_id.id)],limit =1)
        if not budgeted:
            
            budget_line_id = budgeted.create({'investment_pattern':result.project_budget_id.investment_pattern.id,
                                                'department_id':result.project_budget_id.department_id.id,
                                                'project_id':result.project_budget_id.project_id.id,
                                                'budgeted_amount':result.total_cost,
                                                })   
   
        return result
    
    
    def write(self,vals):
        '''
           6 зардлаар төлөвлөх
        '''         
        total = 0 
        balance = 0
        # actual_balance = 0
        result = super(ProjectBudgetLine, self).write(vals)
        if vals.get('material_cost') or vals.get('labor_cost') or vals.get('equipment_cost') or vals.get('carriage_cost') or vals.get('postage_cost') or vals.get('other_cost') :
            
            if self:
                total = self.material_cost + self.labor_cost + self.equipment_cost + self.carriage_cost + self.postage_cost + self.other_cost
                
            self.total_cost = total
            budget = self.project_budget_id
            budget.project_id.total_limit = total
            budget.sum_of_budgeted_amount = total
            budget.possible_amount_create_project = budget.approximate_amount - budget.sum_of_budgeted_amount
            # if budget.surplus_amount == 0:
            #     budget.possible_amount_create_project = budget.approximate_amount - total
            # else:
            #     budget.possible_amount_create_project = budget.surplus_amount - total
            if self.total_cost>0 and budget.approximate_amount < self.total_cost:
                raise ValidationError(_(u'Төлөвлөсөн дүнгийн утга батлагдсан дүнгээс хэтэрсэн байна'))

            for line in budget.project_id.budgeted_line_ids:
                line.update({'investment_pattern':budget.investment_pattern.id,
                            'department_id':budget.department_id.id,
                            'budgeted_amount':self.total_cost,
                            })

                # if line.budgeted_amount:
                #     balance =   line.budgeted_amount - line.total_amount_of_control_budget - line.total_amount_of_purchase_requisition   
                #     actual_balance =   line.budgeted_amount - line.total_amount_of_contract - line.total_amount_of_payment_request 
                #     line.write({'total_possible_balance':balance,
                #                 'actual_balance':actual_balance
                #                 }) 
            # budget.possible_amount_create_project = budget.approximate_amount - total


        return result
    
    


class SubProjectPerformanceLine(models.Model):
    _name ='subproject.performance.line'

    budget_line_id = fields.Many2one('project.budget.line', string="Project budget line")
    project_id = fields.Many2one('project.project',string="Төсөл")
    type =  fields.Char(string="Type")
    source =  fields.Many2one('ir.attachment',string='Эх баримт')
    amount = fields.Float(string="Amount")
    create_date  = fields.Date(string="Create date")

class SurplusBudgetLine(models.Model):

    _name ='surplus.budget'

    project_id = fields.Many2one('project.project',string="Төсөл")
    budgeted_amount = fields.Float(string="Төлөвлөсөн дүн" , readonly=True)
    surplus_amount = fields.Float(string="Тодотгосон дүн" , tracking=True)
    parent_project_id = fields.Many2one('project.project',string="Parent project")
    surplus_date = fields.Datetime(string='Surplus Date', required=True)
    state =  fields.Selection(selection=[('draft',u'Ноорог'), 
                                ('sent',u'Илгээгдсэн'), 
                                ('approved',u'Зөвшөөрсөн'),
                                ('confirmed',u'Баталсан'),
                                ('modified',u'Тодотгосон'),
                                ('rejected',u'Татгалзсан'),
                                ('closed',u'Хаагдсан'),
                                ],
                                string='State',  copy=False, default='draft', tracking=True , readonly=True)   

class ProjectSpecification(models.Model):
    _name ="project.specification"
    _inherit = ['mail.thread']

    name  = fields.Char(string="Name")


class ProjectEmployeeDuty(models.Model):
    _name ="project.employee.duty"
    _inherit = ['mail.thread']

    name  = fields.Char(string="Name")

class BudgetedLine(models.Model):
    _name = "budgeted.line"



    @api.depends('budgeted_amount','total_amount_of_contract','total_amount_of_payment_request')
    def _compute_actual_balance(self):
        for line in self:
            actual_balance = 0

            if line:
                actual_balance = line.budgeted_amount - line.total_amount_of_contract - line.total_amount_of_payment_request           
                line.actual_balance = actual_balance
                
    
    @api.depends('budgeted_amount','total_amount_of_purchase_requisition','total_amount_of_control_budget')
    def _compute_total_possible_balance(self):
        for line in self:
            balance = 0
            if line:
                balance = line.budgeted_amount - line.total_amount_of_control_budget - line.total_amount_of_purchase_requisition
                line.total_possible_balance = balance
                
         

    
    def write(self,vals):
        # amount = 0
        # balance = 0
        # if vals.get('budgeted_amount'):
        #     amount = vals.get('budgeted_amount')
        # project_budget = self.env['project.budget'].search([('department_id','=',self.department_id.id),('investment_pattern','=',self.investment_pattern.id),('project_id','=',self.project_id.id)])
        # balance = project_budget.approximate_amount - amount
        # vals.update({'total_possible_balance':balance})

        result = super(BudgetedLine, self).write(vals)
        return result


    budgeted_id = fields.Many2one('project.budget', string="Lines")
    project_id = fields.Many2one('project.project',string="Төсөл")
    investment_pattern = fields.Many2one('project.specification',string="Investment pattern")
    department_id = fields.Many2one('hr.department',string="Department")
    budgeted_amount = fields.Float(string="Төлөвлөсөн дүн" , readonly=True) 
    surplus_amount = fields.Float(string="Төлөвлөсөн дүн" , readonly=True) 
    total_amount_of_control_budget = fields.Float(string="Total amount of control budget" , readonly=True)
    total_amount_of_purchase_requisition = fields.Float(string="Total amount of purchase requisition", readonly=True)
    total_possible_balance = fields.Float(string="Total possible balance", readonly=True, compute="_compute_total_possible_balance")
    parent_project_id = fields.Many2one('project.project',string="Parent project")
    total_amount_of_contract = fields.Float(string="Total amount of contract", readonly=True)
    total_amount_of_payment_request = fields.Float(string="Total amount of payment request", readonly=True)
    actual_balance = fields.Float(string="Actual balance", readonly=True ,  compute="_compute_actual_balance")
    surplus_number = fields.Integer(string="Surplus number", readonly=True , default=0)
    
    state =  fields.Selection(selection=[('draft',u'Ноорог'), 
                                ('sent',u'Илгээгдсэн'), 
                                ('modified',u'Тодотгосон'),
                                ('rejected',u'Татгалзсан'),
                                ('surplus_request',u'Тодотгох хүсэлт '),
                                ],
                                string='Тодотгол төлөв',  copy=False, default='draft', tracking=True)

    
    def confirm_surplus(self):
        '''Тодотгол батлах
        '''
        
        for line in self:
            project_budget = self.env['project.budget'].search([('project_id','=',line.project_id.id),('department_id','=',line.department_id.id),('investment_pattern','=',line.investment_pattern.id)])
            parent_project_budget = self.env['project.budget'].search([('parent_project_id','=',line.parent_project_id.id),('department_id','=',line.department_id.id),('investment_pattern','=',line.investment_pattern.id)]) 
        
            project_budgeted_line = self.env['project.budget.line'].sudo().search([('project_budget_id.project_id','=',line.project_id.id),('state','=','sent')])
            surplus_line = self.env['surplus.budget'].search([('project_id','=',line.project_id.id),('state','=','draft')])
           
            balance = 0
            if line.state == 'surplus_request':
                balance = line.surplus_amount - line.budgeted_amount
            
            project_budget.update({                               
                                'sum_of_budgeted_amount':project_budgeted_line.total_cost,
                                })
            if project_budgeted_line:
                project_budgeted_line.update({'state':'modified'}) 
            if surplus_line:
                surplus_line.update({'state':'modified'})     


            if parent_project_budget.possible_amount_create_project >= balance:               
                parent_project_budget.update({'sum_of_subproject':parent_project_budget.sum_of_subproject + balance})
                
    
        
                
            else:
                variance = 0
                variance = balance - parent_project_budget.possible_amount_create_project  
                parent_project_budget.approximate_amount +=  variance

                sub_variance = 0 
                sub_variance = project_budget.sum_of_budgeted_amount - project_budget.approximate_amount        
                project_budget.approximate_amount += sub_variance
                
                
                
                parent_project_budget.update({'sum_of_subproject':parent_project_budget.sum_of_subproject + variance})
                
            query = """UPDATE 
                            budgeted_line bl
                        SET 
                            budgeted_amount = %s , surplus_amount = %s
                        FROM 
                            project_project pp
                        WHERE 
                            bl.project_id = pp.id and pp.id=%s"""%(line.surplus_amount,0.0,line.project_id.id)
                            

            self.env.cr.execute(query)

            query1 = """UPDATE 
                            project_budget pb
                        SET 
                            surplus_amount = %s
                        FROM 
                            project_project pp
                        WHERE 
                            pb.parent_project_id = pp.id and pb.department_id=%s"""%(parent_project_budget.approximate_amount,line.department_id.id)
                        
            if self.parent_project_id:

                self.env.cr.execute(query1)


            
            count = line.surplus_number
            
            line.write({'state':'modified',
                        'surplus_number':count+1
                        })
            line.project_id.write({'state_new':'comfirm'})
    

    
    def sub_project_surplus(self):
        '''Тодотгол батлах
        '''
        
        for line in self:
            project_budget = self.env['project.budget'].search([('project_id','=',line.project_id.id),('department_id','=',line.department_id.id),('investment_pattern','=',line.investment_pattern.id)])
            parent_project_budget = self.env['project.budget'].search([('parent_project_id','=',line.parent_project_id.id),('department_id','=',line.department_id.id),('investment_pattern','=',line.investment_pattern.id)]) 
        
            project_budgeted_line = self.env['project.budget.line'].sudo().search([('project_budget_id.project_id','=',line.project_id.id),('state','=','sent')])
            surplus_line = self.env['surplus.budget'].search([('project_id','=',line.project_id.id),('state','=','draft')])
           
            balance = 0
            if line.state == 'surplus_request':
                balance = project_budget.approximate_amount - project_budget.sum_of_budgeted_amount
            
            project_budget.update({                               
                                'sum_of_budgeted_amount':project_budgeted_line.total_cost,
                                })
            if project_budgeted_line:
                project_budgeted_line.update({'state':'modified'}) 
            if surplus_line:
                surplus_line.update({'state':'modified'})     


            if parent_project_budget.possible_amount_create_project >= balance:               
                parent_project_budget.update({'sum_of_subproject':parent_project_budget.sum_of_subproject + balance})
                
    
                
            query = """UPDATE 
                            budgeted_line bl
                        SET 
                            budgeted_amount = %s 
                        FROM 
                            project_project pp
                        WHERE 
                            bl.project_id = pp.id and pp.id=%s"""%(project_budget.sum_of_budgeted_amount,line.project_id.id)
                            

            self.env.cr.execute(query)

            # query1 = """UPDATE 
            #                 project_budget pb
            #             SET 
            #                 surplus_amount = %s
            #             FROM 
            #                 project_project pp
            #             WHERE 
            #                 pb.parent_project_id = pp.id and pb.department_id=%s"""%(parent_project_budget.approximate_amount,line.department_id.id)
                        
            # if self.parent_project_id:

            #     self.env.cr.execute(query1)


            
            count = line.surplus_number
            
            line.write({'state':'modified',
                        'surplus_number':count+1
                        })
            line.project_id.write({'state_new':'comfirm'})
        
    
    
    def reject_surplus(self):
        '''Тодотгол татгалзах
        '''

        for line in self:
            surplus_line = self.env['surplus.budget'].sudo().search([('parent_project_id','=',line.parent_project_id.id),('state','=','draft')])
            project_budgeted_line = self.env['project.budget.line'].sudo().search([('project_budget_id.project_id','=',line.project_id.id),('state','=','sent')])
            project_budgeted_line.update({'state':'rejected'
                                         })
            if line.state == 'surplus_request':
                line.update({   'project_id':line.project_id.id,
                                'parent_project_id':line.project_id.parent_project.id,
                                'state':'rejected',
                                'budgeted_amount':surplus_line.budgeted_amount,
                            })  
                surplus_line.update({'state':'rejected',
                                    'project_id':line.project_id.id,
                                    })
                line.project_id.write({'state_new':'comfirm'})



        
       
                            
class PerformanceLine(models.Model):
    _name = 'performance.line'
     

    project_id = fields.Many2one('project.project',string="Төсөл")
    investment_pattern = fields.Many2one('project.specification',string="Investment pattern")
    department_id = fields.Many2one('hr.department',string="Department")
    # approximate_amount = fields.Float(string="Approximate amount") 
    budgeted_amount = fields.Float(string="Төлөвлөсөн дүн" , readonly=True)
    total_amount_of_contract = fields.Float(string="Total amount of contract", readonly=True)
    total_amount_of_payment_request = fields.Float(string="Total amount of payment request", readonly=True)
    actual_balance = fields.Float(string="Actual balance", readonly=True)
class SubProjectLine(models.Model):
    _name = 'subproject.line'

    project_id = fields.Many2one('project.project',string="Төсөл")
    investment_pattern = fields.Many2one('project.specification',string="Investment pattern")
    department_id = fields.Many2one('hr.department',string="Department")
    approximate_amount = fields.Float(string="Approximate amount") 
    subproject_amount = fields.Float(string="Subproject amount")
    subproject_possible_amount = fields.Float(string="Subproject possible amount")


    


