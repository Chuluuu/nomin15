# -*- coding: utf-8 -*-
from odoo import api, fields, models
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
import time
from datetime import date, datetime, timedelta
from odoo.tools.translate import _


class BudgetPartnerComparison(models.Model):
    _name = 'budget.partner.comparison'
    _description = "Budget partner comparison"
    _inherit = ['mail.thread', 'mail.activity.mixin']


    def _add_followers(self,user_ids):
         '''Add followers
         '''
         self.message_subscribe_users(user_ids=user_ids)

    def _is_voter(self):
        if self.department_id:
            if self.department_id.is_sector and self.department_id.manager_id.user_id.id == self.env.user.id:
                self.is_voter = True
            elif self.department_id.is_sector == False and self.department_id.parent_id.manager_id.user_id.id == self.env.user.id:
                self.is_voter = True
   
    def _is_employee(self):
        if self.employee_id and self.employee_id.user_id.id == self.env.user.id:
            self.is_employee =True

    def _is_old(self):
        if self.sudo().control_budget_id.is_old:
            self.is_old = True
            
    name = fields.Char(string='Дугаар' ,tracking=True ,default='New')
    desc_name = fields.Char(string = "Тодорхойлох нэр",tracking=True)
    control_budget_id = fields.Many2one('control.budget', string = 'Хяналтын төсөв')
    project_id = fields.Many2one('project.project', string = 'Төсөл')
    task_id = fields.Many2one('project.task', string = u'Ажлын даалгавар')   
    task_graph_id = fields.Many2one('project.task', string = u'Ажлын зураг')
    employee_id = fields.Many2one('hr.employee',string = u'Хариуцагч' ,tracking=True)
    type_id = fields.Many2one('tender.type',  string = u'Ангилал' ,tracking=True)
    child_type_id = fields.Many2one('tender.type', string = u'Дэд ангилал')
    is_verify = fields.Boolean(string = "Баталгаат хугацаатай эсэх", default=False)
    confirmed_time = fields.Integer(string ='Баталгаат хугацаа(сараар)')
    date_start = fields.Date(string ='Зарлах огноо' , tracking=True)
    date_end = fields.Date(string ='Хаах огноо', tracking=True)
    # is_performance_percent = fields.Boolean(string = "Гүйцэтгэлийн баталгаа", default=False)
    # performance_percent = fields.Integer(string ='Гүйцэтгэлийн хувь')
    description = fields.Text(string ='Тодорхойлолт')
    committee_member_ids = fields.One2many('partners.comparison.committee.member', 'budget_partner_comparison_id', string="Committee members")#Хорооны гишүүд
    participants_ids = fields.One2many('budget.partners', 'budget_partner_id', string = "budget partner")
    # Tolov deer bagana nuuhiin tuld nemev
    participants_ids2 = fields.One2many('budget.partners', 'budget_partner_id', string = "budget partner")
    document_ids= fields.One2many(related='task_id.work_document', string=u'Хавсралтууд')
    task_graph_document= fields.One2many(related='task_graph_id.work_document', string=u'Хавсралтууд')
    requirement_partner_ids = fields.Many2many(comodel_name='res.partner', string='Урилга явуулах харилцагчид')#Урилга явуулах харилцагчид
    invitation_type =fields.Selection([
                            ('requirement_partner' ,u'Сонгосон харилцагч'),
                            ('partner_type',u'Ангиллын дагуу')
                        ], string="Урилга илгээх төрөл")
    invitation_template = fields.Html(string ='Урилга илгээх загвар')
    state = fields.Selection([
                                    ('draft',u'Ноорог'),
                                    ('quotation',u'Үнийн санал авах'),
                                    ('end_quotation',u'Үнийн санал авч дууссан'),
                                    ('comparison',u'Үнийн харьцуулалт хийх'),
                                    ('management',u'Удирдлагад илгээгдсэн'),
                                    ('winner',u'Шалгарсан'),
                                    ('cancelled',u'Цуцлагдсан'),                            
                                    ], u'Төлөв',  default = 'draft' ,tracking=True)

    new_material_cost_ids = fields.One2many('comparison.material.line','partner_comparison_id',string = u'Материалын зардал')
    material_cost_ids = fields.One2many('comparison.material.line','partner_comparison_id',string = u'Материалын зардал')
    labor_cost_ids = fields.One2many('comparison.labor.line','partner_comparison_id',string = u'Ажиллах хүчний зардал')
    labor_cost_ids1 = fields.One2many('comparison.labor.line','partner_comparison_id',string = u'Ажиллах хүчний зардал')
    equipment_cost = fields.Float(string="Машин механизмын зардал")
    carriage_cost = fields.Float(string="Тээврийн зардал")
    postage_cost = fields.Float(string="Шууд зардал")
    other_cost = fields.Float(string="Бусад зардал")
    department_id = fields.Many2one('hr.department', string=u'Хэлтэс')
    contract_id = fields.Many2one('contract.management', string=u'Гэрээ')
    is_voter = fields.Boolean(string="Is Voter", compute=_is_voter, default=False)
    is_employee = fields.Boolean(string="Is Employee", compute=_is_employee, default=False)
    date_win = fields.Date(string = 'Date win')
    total_amount = fields.Float(string=u'Нийт дүн')
    rejection_reason = fields.Text( string='Цуцалсан шалтгаан')
    is_old = fields.Boolean(string='is old' , compute=_is_old, default=False)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('budget.partner.comparison') or '/' 
        result = super(BudgetPartnerComparison, self).create(vals)
        if vals.get('employee_id'):
            result.sudo()._add_followers([result.employee_id.user_id.id])
        if vals.get('committee_member_ids'):
            for line in result.committee_member_ids:
                result.sudo()._add_followers([line.employee_id.user_id.id])
        if vals.get('department_id'):
            if result.department_id.is_sector and result.department_id.manager_id:
                result.sudo()._add_followers([result.department_id.manager_id.user_id.id])
            elif result.department_id.parent_id.manager_id:
                result.sudo()._add_followers([result.department_id.parent_id.manager_id.user_id.id])
        return result

    def write(self, vals):
        old_date_end = False
        if vals.get('date_end'):
            old_date_end = self.date_end
        result = super(BudgetPartnerComparison, self).write(vals)
        if old_date_end and self.state == 'end_quotation':
            if old_date_end < self.date_end:
                self.write({'state':'quotation'})
            else:
                raise UserError((u'Хаагдах огнооноос өмнөх өдрийг оруулж болохгүй.'))
        if vals.get('committee_member_ids'):
            for line in self.committee_member_ids:
                self.sudo()._add_followers([line.employee_id.user_id.id])
        return result
   
    def action_start(self):
        if not self.committee_member_ids:
            raise UserError((u'Комиссийн гишүүдийг сонгоогүй байна.'))
        subject = "%s-с үнийн санал ирүүлэх урилга"%(self.department_id.name)
        if self.invitation_type == 'requirement_partner':
            for user in self.requirement_partner_ids:
                email_template = self.env['mail.mail'].sudo().create({
                        'name': ('Followup '),
                        'email_from': self.env.user.email or '',
                        'model_id': self.env['ir.model'].search([('model', '=', 'budget.partner.comparison')]).id,
                        'subject': subject,
                        'model':'budget.partner.comparison',
                        'lang': self.env.user.lang,
                        'auto_delete': True,
                        'body_html':self.invitation_template,
                    })
                if user.email:
                    email_template.write({'email_to':user.email})
                    email_template.send()
      
        elif self.invitation_type == 'partner_type':
            partner_ids = self.env['res.partner'].search(['|',('tender_type_ids','child_of',self.type_id.id),('tender_type_ids','in',[self.child_type_id.id])]) 
            if partner_ids:
                for user in partner_ids:
                    if user.email:
                        email_template = self.env['mail.mail'].sudo().create({
                            'name': ('Followup '),
                            'email_from': self.env.user.email or '',
                            'model_id': self.env['ir.model'].search([('model', '=', 'budget.partner.comparison')]).id,
                            'subject': subject,
                            'model':'project.task',
                            'lang': self.env.user.lang,
                            'auto_delete': True,
                            'body_html':self.invitation_template,
                        })
                        email_template.write({'email_to':user.email})
                        email_template.send()
        self.write({'state':'quotation'}) 

        utilization_budget_material     = self.env['utilization.budget.material']
        utilization_budget_labor        = self.env['utilization.budget.labor']
        utilization_budget_equipment    = self.env['utilization.budget.equipment']
        utilization_budget_carriage     = self.env['utilization.budget.carriage']
        utilization_budget_postage      = self.env['utilization.budget.postage']
        utilization_budget_other        = self.env['utilization.budget.other']

        m_total_amount = 0.0
        l_total_amount = 0.0

        if self.material_cost_ids:
            for line in self.material_cost_ids:
                m_total_amount += line.material_total
            if m_total_amount > 0:
                m_vals = {
                            'budget_id'     : self.sudo().control_budget_id.id,
                            'price'         : m_total_amount,
                            'date'          : time.strftime('%Y-%m-%d %H:%M:%S'),
                            'map'           : 'budget',
                            'state'         : 'comparison',
                            'budget_comparison' : self.id,
                                }
                utilization_budget_material     = utilization_budget_material.create(m_vals)
        
        if self.labor_cost_ids:
            for line in self.labor_cost_ids:
                l_total_amount += line.labor_cost_basic
            if l_total_amount > 0:
                l_vals = {
                    'budget_id'     : self.control_budget_id.id,
                    'price'         : l_total_amount,
                    'date'          : time.strftime('%Y-%m-%d %H:%M:%S'),
                    'map'           : 'budget',
                    'state'         : 'comparison',
                    'budget_comparison' : self.id,
                        }
                utilization_budget_labor = utilization_budget_labor.create(l_vals)
            
        if  self.equipment_cost > 0:
            e_vals = {
                    'budget_id'     : self.sudo().control_budget_id.id,
                    'price'         : self.equipment_cost,
                    'date'          : time.strftime('%Y-%m-%d %H:%M:%S'),
                    'map'           : 'budget',
                    'state'         : 'comparison',
                    'budget_comparison' : self.id,
                        }
            utilization_budget_equipment    = utilization_budget_equipment.create(e_vals)
            
        if self.carriage_cost > 0:
            c_vals = {
                'budget_id'     : self.sudo().control_budget_id.id,
                'price'         : self.carriage_cost,
                'date'          : time.strftime('%Y-%m-%d %H:%M:%S'),
                'map'           : 'budget',
                'state'         : 'comparison',
                'budget_comparison' : self.id
                    }
            utilization_budget_carriage     = utilization_budget_carriage.create(c_vals)
        if self.postage_cost > 0:
            p_vals = {
                'budget_id'     : self.sudo().control_budget_id.id,
                'price'         : self.postage_cost,
                'date'          : time.strftime('%Y-%m-%d %H:%M:%S'),
                'map'           : 'budget',
                'state'         : 'comparison',
                'budget_comparison' : self.id
                    }
            utilization_budget_postage      = utilization_budget_postage.create(p_vals)
        if self.other_cost > 0:
            o_vals = {
                'budget_id'     : self.sudo().control_budget_id.id,
                'price'         : self.other_cost,
                'date'          : time.strftime('%Y-%m-%d %H:%M:%S'),
                'map'           : 'budget',
                'state'         : 'comparison',
                'budget_comparison' : self.id
                    }
            utilization_budget_other        = utilization_budget_other.create(o_vals)
            
   
    def action_quotation(self):
        self.write({'state':'comparison'})
    
    def action_cancel(self):
        mod_obj = self.env['ir.model.data']

        res = mod_obj.get_object_reference('nomin_project', 'action_cancel_partner_comparison')
        return {
            'name': 'Цуцлах шалтгаан',
            'view_mode': 'form',
            'res_model': 'cancel.partner.comparison.wizard',
            'context': self._context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }
        
    def action_vote(self):
        '''
            Салбарын захирал санал өгөх 
        '''
        partners = {}
        result =  []
        for partner in self.committee_member_ids:
            group1 = partner.partner_id
            if group1 not in partners:
                partners[group1] = {
                        'partner' : '',
                        'members' :[],
                     }
            partners[group1]['partner'] = group1
            partners[group1]['members'].append(partner.employee_id.id)
        for line in self.participants_ids:
            if line.partner_id in partners:
                result.append((0,0,{'is_winner':False,'partner_id':line.partner_id.id,'price_amount':line.price_amount,'employee_ids':[(6,0,partners[line.partner_id]['members'])]}))
         
        vals = {
            'comparison_id' : self.id,
            'participants_ids' : result
         }
        template_id = self.env['action.vote.wizard'].create(vals)
        return {
            'name': 'Note',
            'view_mode': 'form',
            'res_model': 'action.vote.wizard',
            'type': 'ir.actions.act_window',         
            'res_id':template_id.id,        
            'target': 'new',
            'nodestroy': True,
            #  'views': [(templat/e_id.id, 'form')],
        }

    @api.onchange('date_start')
    def onchange_date_start(self):
        if self.date_start:
            self.date_end = (datetime.strptime(self.date_start,'%Y-%m-%d') + relativedelta(days=3)).strftime('%Y-%m-%d')
         
    @api.onchange('type_id')
    def onchange_type(self):
        '''Тендерийн ангиллыг сонгоход түүнд 
           хамаарах дэд ангиллууд гарна
        '''
        self.update({'child_type_id':False})
        child_ids = []
        if self.type_id:
            type_ids = self.env['tender.type'].sudo().search([('parent_id','=',self.type_id.id)])
            child_ids.extend(type_ids.ids)
        return {'domain':{'child_type_id': [('id','=', child_ids)]}}

    @api.onchange('invitation_type','date_end')
    def onchange_template(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        text = """<p><b>“%s”<b> нь “%s” ажилд гүйцэтгэгчийг сонгон шалгаруулах тул сонирхсон этгээдийг үнийн саналаа ирүүлэхийг урьж байна.</p>
                  <p>%s-аас өмнө <a>%s</a> сайтаар хандаж үнийн санал болон баримт бичгийг цахимаар ирүүлнэ үү.</p>
                  <p>Ажлын даалгавартай холбогдолтой нэмэлт мэдээллийг %s лавлаж болно.</p>       
                  <p>Утас: %s</p>
                  <p>И-мэйл: %s</p>
            """%(self.department_id.name,self.desc_name,self.date_end,base_url,self.employee_id.name,self.employee_id.mobile_phone,self.employee_id.work_email)
        self.update({"invitation_template": text})

    @api.model
    def _vote_end_cron(self):
        query = """ select id from budget_partner_comparison where state = 'quotation' and date_end <= DATE(now())
                """
        self.env.cr.execute(query)
        budget_partner_comparison_ids =  self.env.cr.fetchall()
        if budget_partner_comparison_ids:
            for comparison_id in budget_partner_comparison_ids:
                comparison = self.env['budget.partner.comparison'].browse(comparison_id)
                comparison.write({'state':'end_quotation'})

    def create_contract(self):
        '''
            Гэрээ үүсгэх
        '''
        contract_id = self.env['contract.management']
        customer_company = False
        contract_amount = False

        if self.participants_ids:
            for line in self.participants_ids:
                if line.is_winner:
                    customer_company = line.partner_id
                    contract_amount = line.price_amount

        vals = {
            'contract_type' : 'work_perform_contract',
            'categ_id' : 133,
            'part_type' : 19,
            'user_id' : self.env.user.id,
            'department_id' : self.department_id.id,
            'sector_id' : self.department_id.parent_id.id,
            'company_id' : self.department_id.company_id.id,
            'customer_company' : customer_company.id,
            'contract_content' : self.desc_name,
            'register' : customer_company.registry_number,
            'project_id' : self.project_id.id,
            'perform_user_id' : self.employee_id.id,
            'guarantee_period' : self.is_verify,
            'guarantee_by_month' : self.confirmed_time,
            'contract_amount' : contract_amount,
            'agreed_currency' : contract_amount,
        }

        contract_id = contract_id.sudo().create(vals)
        if contract_id:
            contract_id.sudo().message_subscribe_users([self.employee_id.user_id.id])
            if not self.contract_id:
                self.write({'contract_id':contract_id.id})
        return {
            'view_mode': 'form',
            'res_model': 'contract.management',
            'type': 'ir.actions.act_window',         
            'res_id':contract_id.id,                    
            'nodestroy': True,
        }
   
    def unlink(self):
        for main in self:
            if main.state != 'draft':
                raise UserError((u'Ноорог төлөв дээр устгах боломжтой.'))
            else :
                #Ажиллах хүчний зардлын гүйцэтгэл цуцлах
                if self.sudo().control_budget_id and self.sudo().control_budget_id.labor_line_ids:
                    for line in self.sudo().control_budget_id.labor_line_ids:
                        for labor in self.labor_cost_ids:
                            if line.state == 'comparison' and line.product_name == labor.product_name:
                                line.write({'state' : 'confirm','cost_choose' : False})
                        for utilization in self.sudo().control_budget_id.utilization_budget_labor:
                            if self == utilization.budget_comparison:
                                utilization.unlink()
                #Материалын зардлын гүйцэтгэл цуцлах
                if self.sudo().control_budget_id and self.sudo().control_budget_id.material_line_ids:
                    for line in self.sudo().control_budget_id.material_line_ids:
                        for material in self.material_cost_ids:
                            if line.state == 'comparison' and line.product_id.id == material.product_id.id:
                                line.write({'state' : 'confirm','cost_choose' : False})
                        for utilization in self.sudo().control_budget_id.utilization_budget_material:
                            if self == utilization.budget_comparison:
                                utilization.unlink()
                #Машин механизмын зардлын гүйцэтгэл цуцлах
                if self.sudo().control_budget_id and self.equipment_cost > 0:
                    for line in self.sudo().control_budget_id.utilization_budget_equipment:
                        if line.state == 'comparison' and self.equipment_cost == line.price:
                            line.unlink()
                #Тээврийн зардлын гүйцэтгэл цуцлах
                if self.sudo().control_budget_id and self.carriage_cost > 0:
                    for line in self.sudo().control_budget_id.utilization_budget_carriage:
                        if line.state == 'comparison' and self.carriage_cost == line.price:
                            line.unlink()
                #Шууд зардлын гүйцэтгэл цуцлах
                if self.sudo().control_budget_id and self.postage_cost > 0:
                    for line in self.sudo().control_budget_id.utilization_budget_postage:
                        if line.state == 'comparison' and self.postage_cost == line.price:
                            line.unlink()
                #Бусад зардлын гүйцэтгэл цуцлах
                if self.sudo().control_budget_id and self.other_cost > 0:
                    for line in self.sudo().control_budget_id.utilization_budget_other:
                        if line.state == 'comparison' and self.other_cost == line.price:
                            line.unlink()
        return super(BudgetPartnerComparison, self).unlink()

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        raise UserError((u"Хуулбарлан үүсгэх боломжгүй!"))
        return super(BudgetPartnerComparison, self).copy()

# class BudgetPartnerComparisonDocument(models.Model):
#     _name = 'budget.partner.comparison.document'
#     _description = "Budget partner comparison document"

#     '''
# 		Үнийн харьцуулалтын хавсралтууд
# 	'''
    

#     budget_partner_comparison_id = fields.Many2one('budget.partner.comparison', string=u"Үнийн санал", index=True)
#     document_id = fields.Many2one('ir.attachment', string=u"Батлагдсан хавсралтууд")
    # datas_fname =  fields.Char( string='File name')
    # datas =  fields.Binary(string='Download')
    # name = fields.Char(string = 'name')
   

class BudgetPartners(models.Model):
    _name="budget.partners"
    _description = "Budget Partners"

    '''Төсвийн түншүүд
    '''
   

    def _is_voter(self):
        for partner in self:
            if partner.budget_partner_id.committee_member_ids:
                for line in partner.budget_partner_id.committee_member_ids:
                    if self._uid == line.employee_id.user_id.id and not line.vote_date and partner.budget_partner_id.state == 'comparison':
                        partner.is_voter = True
            # if partner.budget_partner_id.state == 'management' and self._uid == partner.budget_partner_id.department_id.manager_id.user_id.id:
            #    partner.is_voter = True
    
    def _get_price_percent(self):
        for partner in self:
            if partner.price_amount and partner.budget_partner_id.total_amount:
                total_amount = partner.budget_partner_id.total_amount
                partner.price_percent = (partner.price_amount - total_amount)*100/ total_amount

    budget_partner_id = fields.Many2one('budget.partner.comparison', string = 'Budget partner comparison')
    partner_id = fields.Many2one('res.partner' , string = 'Харилцагчийн нэр')
    price_amount = fields.Float(string = 'Үнийн санал')
    document_id = fields.Many2one('ir.attachment', string = 'Ирүүлсэн материал')
    is_voter = fields.Boolean(string = 'is voter', default=False ,compute =_is_voter)
    is_winner = fields.Boolean(string = 'is winner', default=False )
    price_percent = fields.Float(string = 'Үнийн саналын хувь (%)', compute = _get_price_percent)
   
    def action_vote(self):
        members = {}
        partners = {}
        is_done = True
        for partner in self:         
            if partner.budget_partner_id:
                for line in partner.budget_partner_id.committee_member_ids:
                    if line.employee_id.user_id:
                        group = line.employee_id.user_id.id
                        if group not in members:
                            members[group]={
                                'budget' : '',
                                'line':'',
                                'employee':'',
                                'partner_id':'',
                            }
                        members[group]['budget'] = partner.budget_partner_id
                        members[group]['line'] = line
                        members[group]['employee'] = group
                        members[group]['partner_id'] = line.partner_id
                if self._uid in members:
                    lines = members[self._uid]['line']
                    lines.write({
                            'vote_date' : time.strftime('%Y-%m-%d %H:%M:%S'),
                            'partner_id': partner.partner_id.id})
                    for line in partner.budget_partner_id.committee_member_ids:
                        group1 = line.partner_id
                        if group1 not in partners:
                            partners[group1] = {
                                'partner' : '',
                                'count' : 0,
                            }
                        partners[group1]['partner'] = group1
                        partners[group1]['count'] += 1
                        
                        if not line.vote_date:
                            is_done = False
                    if is_done:
                        counter = 1
                        winner = False
                        not_win = False
                        for line in partner.budget_partner_id.participants_ids:
                            if line.partner_id in partners and counter < partners[line.partner_id]['count']:
                                counter = partners[line.partner_id]['count']
                                winner = line
                        if winner:
                            winner.budget_partner_id.write({'state' : 'winner','date_win': datetime.today().strftime("%Y-%m-%d")})
                            winner.write({ 'is_winner' : True})
                        else:
                            partner.budget_partner_id.write({'state' : 'management'})
        file_id = self.document_id
        return {'name': _('Download contract'),
                'type': 'ir.actions.client', 
                'tag': 'reload',
                'res_id': file_id.id, } 
         

class PartnersComparisonCommitteeMember(models.Model):
    _name="partners.comparison.committee.member"
    _description = "Partners comparison committee members"
    '''
        Комиссийн гишүүд
    '''

    budget_partner_comparison_id = fields.Many2one('budget.partner.comparison' , string=u"Үнийн санал")
    employee_id = fields.Many2one("hr.employee", string ="Санал өгөх хэрэглэгч", index=True)
    vote_date = fields.Datetime(string="Санал өгсөн өдөр")
    partner_id = fields.Many2one('res.partner' , string = 'Санал өгсөн харилцагч')

class ComparisonMaterialLine(models.Model):
    _name = 'comparison.material.line'
    _description = 'comparison material line'

    @api.model
    def _amount(self):
        for obj in self:
            obj.material_total = obj.product_uom_qty * obj.price_unit


    partner_comparison_id = fields.Many2one('budget.partner.comparison',string="wizard")
    product_id=fields.Many2one('product.product', string='Product',required = False, domain=[('product_tmpl_id.is_new','=',True),('product_tmpl_id.cost_price','>',0)])
    product_uom=fields.Many2one('product.uom',string='Unit of Measure',required = False)
    product_uom_qty=fields.Float(string = 'Estimated Quantity',required = False,default=1)
    price_unit=fields.Float(string = 'Estimated price',required = False)
    material_total=fields.Float(compute=_amount, digits_compute=dp.get_precision('Account'), string='Total', type='float', help="The material amount.")
    name = fields.Char(string = 'name')
    product_name=fields.Char(string ='Product name')


class ComparisonLaborLine(models.Model):
    _name = 'comparison.labor.line'
    _description = 'comparison labor line'

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

    partner_comparison_id = fields.Many2one('budget.partner.comparison',string="wizard")        
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