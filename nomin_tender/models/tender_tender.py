# -*- coding: utf-8 -*-
##############################################################################
#    Copyright (C) 2014-2020 Asterisk-technologies LLC Developer). All Rights Reserved
#
#    Address : Chingeltei District, Peace Tower, 205, Asterisk-technologies LLC Developer Ganzorig
#    Email : support@asterisk-tech.mn
#    Phone : 976 + 99241623
#
##############################################################################

from datetime import datetime,date, timedelta
import datetime,time
from openerp.osv import fields, osv, expression
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError
from openerp import api, fields, models, SUPERUSER_ID, _
#from _dbus_bindings import String
import openerp.pooler
import logging
_logger = logging.getLogger(__name__)
from openerp.http import request
from dateutil.relativedelta import relativedelta

class tender_work_task(models.Model):
    _name="tender.work.task"
    _description = "Tender Work Task"
    '''
        Тендерийн хавсралтууд: Төслийн ажлын зураг, даалгавар, урилга зэрэг талбаруудаас орж ирнэ
    '''
    tender_id                   = fields.Many2one('tender.tender', string=u"Тендер", index=True)
    tender_work_document_id     = fields.Many2one('ir.attachment', string=u"Батлагдсан хавсралтууд")
    
    
class tender_committee_member(models.Model):
    _name="tender.committee.member"
    _description = "Tender committee members"
    '''
        Тендерийн хорооны гишүүд
    '''
    @api.multi
    def _get_tender_category(self):
        type_id = []
        context= self._context
        if context.get('type_id'):
            type_id=context.get('type_id')
        return type_id
    @api.one
    def _is_user(self):
        for member in self:
            if self._uid ==member.employee_id.user_id.id:
                member.is_user =True

    tender_id = fields.Many2one('tender.tender', string="Current Tender", index=True)
    type_id = fields.Many2one('tender.type', 'Tender type', default=_get_tender_category, index=True)
    employee_id = fields.Many2one("hr.employee", string ="Commission of tender", index=True)
    job_id = fields.Many2one("hr.job", related='employee_id.job_id', string ="Work Position")
    confirmed_date = fields.Datetime(string="Confirm date")
    state = fields.Selection([('draft','Draft'),('complete','complete')],string= "Status", default="draft")
    is_valuation = fields.Boolean(string ="Is Get Valuation", default=False) #Үнэлгээ өгөх ажилтан  эсэх
    is_user = fields.Boolean(string="Is boolean", compute=_is_user,default=False)
    read_state = fields.Selection([('unread','Unread'),('read','read')],string="Read state",default="unread")
        
    @api.onchange('type_id')
    def onchange_type(self):
        '''
            Тендерийн төрөл солиход хорооны гишүүдийг ялгаж харуулна
        '''
        employee_ids = []
        user_obj = self.env['res.users']
        context = self._context
        if self.type_id:
            ir_model_data = self.env['ir.model.data']
            notif_groups=ir_model_data.get_object_reference('nomin_tender', 'group_tender_committee_members')
            sel_user_ids = user_obj.search([('groups_id','in',notif_groups[1])])
            employee_ids = self.env['hr.employee'].search([('user_id','in',sel_user_ids.ids)])
            #return {'domain':{'confirmed_member_ids':[('id','in',employee_ids.ids)]}}
            #dids = [x.id for x in employee_ids]
            return {'domain':{'employee_id':[('id','in',employee_ids.ids)]}}

    @api.multi
    def action_check(self):

        self.write({'read_state':'read'})


class tender_employee_line(models.Model):
    _name="tender.employee.line"
    _description = "Tender employee line"
    '''
        Тендерийн хүсэлт батлах удирдлагууд
    '''
    @api.multi
    def _get_tender_type(self):
        '''
            Хүсэлт батлах удирдлагууд мөр дээр 
            тендерийн төрлийг автоматаар оноож байна
        '''
        type_id = []
        context= self._context
        if context.get('type_id'):
            type_id=context.get('type_id')
        return type_id

    tender_id = fields.Many2one('tender.tender', string="Current Tender", index=True)
    type_id = fields.Many2one('tender.type', 'Tender type', default=_get_tender_type, index=True)
    employee_id = fields.Many2one("hr.employee", string ="Employee of tender", index=True)
    confirmed_date = fields.Datetime(string="Confirm date")
    state = fields.Selection([('draft','Draft'),('approved','Verified'),('cancel','Cancel')],string= "Status")
    _defaults = {
        'state': 'draft',
                }
        
    @api.onchange('type_id')
    def onchange_type(self):
        '''
            Тендерийн хүсэлт батлах удирдлагууд чектэй хүмүүс гарч ирэх
        '''
        employee_ids = []
        user_obj = self.env['res.users']
        context = self._context
        if self.type_id:
            ir_model_data = self.env['ir.model.data']
            notif_groups=ir_model_data.get_object_reference('nomin_tender', 'group_tender_requist_approval_leaders')
            sel_user_ids = user_obj.search([('groups_id','in',notif_groups[1])])
            employee_ids = self.env['hr.employee'].search([('user_id','in',sel_user_ids.ids)])
            #return {'domain':{'confirmed_member_ids':[('id','in',employee_ids.ids)]}}
            #dids = [x.id for x in employee_ids]
            return {'domain':{'employee_id':[('id','in',employee_ids.ids)]}}

class tender_type(models.Model):
    _name = "tender.type"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "tender type"
    '''
        Тендерийн төрөл
    '''
    name = fields.Char(string = 'Type Name', required=True,track_visibility='onchange')
    parent_id = fields.Many2one('tender.type', string='Parent Type', ondelete='restrict',track_visibility='onchange', index=True)
    child_ids = fields.One2many('tender.type', 'parent_id', string='Child Type',track_visibility='onchange')

    @api.multi
    def write(self, vals):
        '''Тендерийн төрөл засах үед өөрөө өөрийгөө 
           эцэг ангиллаар сонгох боломжгүй
        '''
        parent_id=False
        if vals.get('parent_id'):
            parent_id = vals.get('parent_id')
        else:
            parent_id = self.parent_id.id
            
        if parent_id == self.id:
           raise UserError(_(u'Өөрөө өөрийгөө эцэг ангиллаар сонгох боломжгүй !'))
        result = super(tender_type, self).write(vals)
        return result
    
    @api.multi
    def unlink(self):
        '''Дэд төрөлтэй ангиллыг устгах боломжгүй байна'''
        for order in self:
            if order.child_ids:
                raise UserError(_(u'Та дэд төрөлтэй тендерийн ангиллыг устгах боломжгүй.'))
        return super(tender_type, self).unlink()

class tender_tender(models.Model):
    _name = "tender.tender"
    _description = "Tenders"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = "create_date desc"
    
    @api.multi
    def name_get(self):
        '''Тендерийн дугаар, нэр талбаруудыг залгаж харуулна'''
        result = []
        for tender in self:
            name = tender.name
            if tender.desc_name:
                name = u'%s-%s'%(name,tender.desc_name)
            result.append((tender.id, name))
        return result
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        '''Тендерийн дугаар, нэр талбаруудаар хайлт хийхэд ашиглана'''
        args = args or []
        domain = []
        #name - Тендерийн дугаар
        if name:
            domain = ['|',('desc_name', '=ilike', '%' + name+'%'),('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&'] + domain
        categories = self.search(domain + args, limit=limit)
        return categories.name_get()
    
    @api.model
    def _default_company(self):
        '''Тендер үүсгэж байгаа ажилтаны компани'''
        company_id=False
        if not self.env.user.company_id:
            raise osv.except_osv((u'Анхааруулга'), (u"Та ямар нэгэн компанид хамааралгүй байна!"))
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])

        if employee_id:
            return employee_id.department_id.company_id.id
        else:
            return None
        
    @api.model
    def _default_sector(self):
        '''Тендер үүсгэж байгаа ажилтаны салбар'''
        sector_id=False
        if not self.env.user.department_id:
            raise osv.except_osv((u'Анхааруулга'), (u"Та ямар нэгэн хэлтэст хамааралгүй байна!"))
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])

        if employee_id:
            sector_id = self.env['hr.department'].get_sector(employee_id.department_id.id)
            if sector_id:
                return sector_id
            else:
                return None
        
    @api.model
    def _default_department(self):
        '''Тендер үүсгэж байгаа ажилтаны хэлтэс'''
        department_id=False
        if not self.env.user.department_id:
            raise osv.except_osv((u'Анхааруулга'), (u"Та ямар нэгэн хэлтэст хамааралгүй байна!"))
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])

        if employee_id:
            return employee_id.department_id
        else:
            return None
        
    @api.model
    def _default_employee(self):
        '''Тендер үүсгэж байгаа хэрэглэгчийн ажилтан'''
        employee_id=False
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        if employee_id:
            return employee_id
        else:
            raise osv.except_osv((u'Анхааруулга'), (u"Та ямар нэгэн ажилтан хамааралгүй байна!"))
        
    @api.one
    def _partner_count(self):
        '''Тендерт үнийн санал илгээсэн оролцогчдыг тоолно'''
        for tender in self:
            count=self.env['tender.participants.bid'].sudo().search_count([('tender_id','=',tender.id),('state','!=','draft')])
        self.partner_count=count
        
    @api.one
    def _count_rate(self):
        domain = [
            ('state', 'in', ['completed', 'approved']),
        ]
        for tender in self:
            count=self.env['tender.valuation.employee.valuation'].sudo().search_count([('tender_id','=',tender.id)])
        self.count_rated=count
    
    @api.one
    def _is_old(self):
        if self.create_date < '2021-12-09':
            self.is_old = True
        
    name                    = fields.Char(string='Call for Tenders Reference', required=True, copy=False, readonly=True, index=True, default='New')
    color                   = fields.Integer('Color Index')
    desc_name               = fields.Char(string = "Tender name",track_visibility='onchange', required=False, copy=False)
    company_id              = fields.Many2one('res.company', string = "Company", default=_default_company, track_visibility='onchange', ondelete='restrict', index=True)
    sector_id               = fields.Many2one('hr.department', string="Sector department", default=_default_sector, track_visiblity='always', ondelete='restrict', domain=[('is_sector','=',True)], index=True)
    department_id           = fields.Many2one('hr.department', string='Department', default=_default_department, track_visibility='onchange', ondelete='restrict', index=True)
    user_id                 = fields.Many2one('res.users', string ='Respondent',default=lambda self: self.env.user.id,track_visibility='onchange', ondelete='restrict', index=True)
    #employee_id            = fields.Many2one('hr.employee', string='Creater employee',track_visibility='onchange')
    origin                  = fields.Char(string ='Source Document')
    type_id                 = fields.Many2one('tender.type', string='Tender Category',track_visibility='onchange', ondelete='restrict')
    ordering_date           = fields.Date(string ='Scheduled Ordering Date',track_visibility='onchange') #Шаардахаас орж ирж байгаа огноо
    date_end                = fields.Datetime(string ='Tender Closing Deadline',track_visibility='onchange')
    date_open_deadline      = fields.Datetime(string ='Tender Opening Deadline',track_visibility='onchange')
    #meeting_date           = fields.Datetime(string ='Date of tender meeting',track_visibility='onchange') # Хурлын огноо
    active_sequence         = fields.Integer(string='Active sequence', default=1)
    state                   = fields.Selection([('draft', 'Draft'),('reject','Rejected tender requist'),('disabled',u'Хэрэгсэхгүй'),('open_purchase',u'Худалдан авалт'),('allowed', 'Allowed'),('bids', 'Sent'),
                                                ('open', 'Open'),('confirmed', 'Confirmed tender'),('send_to_manager', u'Нийтлэхэд бэлэн'),('published', 'on Web site'),
                                                ('bid_expire', 'Expire BID'),('closed', 'Closed BID'),('in_selection', 'Bid Selection'),('contract_request',u'Гэрээ үүсгэх хүсэлт'),('contract_created',u'Гэрээ'),('finished', 'Finished'),('cancelled', u'Хүчингүй болсон'),('delay',u'Хойшлуулсан')], 
                                               string ='Status', track_visibility='onchange', required=True, copy=False, default='draft')
    multiple_rfq_per_supplier = fields.Boolean(string ='Multiple RFQ per vendor')
    technical_requirement   = fields.Boolean(string ='Technical Requirement', default = False) #Техникийн үзүүлэлтүүд шаардах эсэх
#     work_experience         = fields.Boolean(string ='Work Experience Requirement', default = False)
    work_experience_info    = fields.Integer(string ='Work Experience Requirement', track_visibility='always')
    license                 = fields.Boolean(string = "Required License") #Тусгай зөвшөөрөл шаардах эсэх
    is_alternative          = fields.Boolean(string = "Alternative tender is") #Хувилбарт тендер ирүүлэх эсэх 
    is_domestic             = fields.Boolean(string = "Domestic Preference") #Дотоодын давуу эрх тооцох эсэх
    is_performance          = fields.Boolean(String = "Performance Guarantee") #Гүйцэтгэлийн баталгаа
    is_publish              = fields.Boolean(string ="Publish on Website", default=False) #Вэб сайтад харуулах
    is_extend               = fields.Boolean(string ="Is Extend", default=False) #Хугацаа сунгагдсан эсэх
    is_open_tender          = fields.Boolean(string ="Is Open", default=True) #Нээлттэй тендер эсэх
    is_warranty             = fields.Boolean(string ="Is Waranty", default=False, track_visibility='always') #Баталгаат хугацаа шаардах эсэх
    warranty                = fields.Integer(string="Warranty life", track_visibility='always')#Баталгаат хугацаа сараар
    special_require         = fields.Html(string = "Special Requirement")#Тусгай шаардлагууд
    tender_line_ids         = fields.One2many('tender.line', 'tender_id', string = "Required Products")#Бараа
    tender_labor_ids         = fields.One2many('tender.labor.line', 'tender_id', string = "Required Products")#Бараа
    participants_ids        = fields.One2many('tender.participants.bid', 'tender_id', string = "vendors of Tender", domain=[('state','not in',['draft'])])#оролцогчид
    committee_member_ids    = fields.One2many('tender.committee.member', 'tender_id', string="Committee members")#Хорооны гишүүд
    #member_ids             = fields.Many2many('hr.employee', relation = "tender_committee_member_rel", string='Members of Tender')#
    protocol_ids            = fields.One2many('tender.protocol', 'tender_id', string="Meeting protocol of tender")#хурлын протокол
    close_remaining         = fields.Char(compute='_get_remaining', string = "Remaing For BID Selection")
    count_rated             = fields.Integer(compute='_count_rate', string = "Rated count")#Үнэлгээний тоо
    partner_count           = fields.Integer(compute='_partner_count', string="Partner count")#оролцогчдын тоо
    invitation_id           = fields.Many2one('tender.invitation.guide', string ='Invitation of Tender', ondelete='restrict')#Урилга
    extend_requist_ids      = fields.One2many('tender.date.extend', 'tender_id', string='Extend Date Bid')#хугацаа сунгалт
    is_meeting              = fields.Boolean('Is schedule meeting',default=False)#хурал зарлагдсан эсэх
    meeting_ids             = fields.One2many('tender.meeting', 'tender_id', string='Current meet')#хурал
    published_date          = fields.Datetime(string='Published Date',track_visibility='onchange')#Тендер зарласан огноо
    closed_date             = fields.Date(string='Tender Closed Date',track_visibility='onchange')#Тендер хаасан огноо
    respondent_department_id= fields.Many2one('hr.department', string='Respondent department',track_visibility='onchange', ondelete='restrict')#Тендер зарлуулж байгаа салбар, хэлтэс
    respondent_employee_id  = fields.Many2one('hr.employee', string='Respondent employee',track_visibility='onchange', ondelete='restrict')#Тендер зарлаж байгаа салбарын хариуцсан ажилтан
    confirmed_member_ids    = fields.One2many('tender.employee.line','tender_id', string='Employee of tender', track_visibility='onchange')#Тендерийн хүсэлтийг батлахаар сонгогдсон хэрэглэгчид
    schedule_date           = fields.Date(string ='Scheduled Date', select=True, help="The expected and scheduled delivery date where all the products are received")#
#     sector_id               = fields.Many2one('hr.department','Sector',domain=[('is_sector','=',True)], ondelete='restrict')#салбар
    description             = fields.Html(string ='Description')#Нэмэлт тайлбар
    performance_amount      = fields.Float(string='Amount price', digits=(16, 2), track_visibility='always')#Гүйцэтгэлийн үнийн дүн
    requirement_partner_ids = fields.Many2many('res.partner', relation='tender_require_partner_rel', string='Invitation sent to partner')#Урилга хү.авах харилцагчид
    purchase_order_id       = fields.Many2one('purchase.order', string="Purchase order")#
    rate_partner_ids        = fields.One2many('tender.valuation.partner', 'tender_id', 'Rate of Partner')#
    contract_id             = fields.Many2one('contract.management', 'Contract')#Гэрээ
    child_type_id           = fields.Many2one('tender.type', string=u'Дэд ангилал', track_visibility='always')#Тендерийн төрлийн задаргаа
    sub_user_ids            = fields.Many2many(comodel_name='subscribe.users', string='Subscribe users')#Имэйд бүртгүүлсэн харилцагчид
    is_valuation_created    = fields.Boolean(string ="Is Valuation", default=False) #Үнэлгээ !үүссэн эсэх
    is_valuation_finished   = fields.Boolean(string="Finished Valuation", default=False)
    mail_sent_partner_ids   = fields.One2many('mail.sent.partners','tender_id', string='Mail sent partners')
    is_meet_start_date      = fields.Boolean(string='Is Now Date', default=False)#хурал эхлэсэн эсэх
    work_task_ids           = fields.One2many('tender.work.task', 'tender_id', string=u'Хавсралтууд', default=False)#Батлагдсан ажлын даалгавар
    is_sent_result          = fields.Boolean(u'Мэйл илгээсэн эсэх', default=False)
    is_old                  = fields.Boolean(string='is old',compute=_is_old, default=False)
#     mail_sent_user_ids = fields.One2many('mail.sent.users','tender_id', string='Mail sent users')
#     partner_ids = fields.One2many('tender.participants.bid', 'tender_id', string = "partner of Tender")
#     'is_in_approve' : fields.function(_is_in_approve, method=True, type='boolean', string='Check groups' )
#      request_config_id = fields.Many2one('request.config', string='Request Config',readonly=True)
#      procurement_id = fields.Many2one('procurement.order', string ='Procurement', ondelete='set null', copy=False)
#      task = fields.many2one('project.task', string = "Work Task", domain=[('res_model','=','res.partner')])
#      license_ids = fields.Many2many(comodel_name = 'tender.license', string = "Required License", relation = "tender_license_rel")
#      description = fields.Html('Description')
#     'task_count': fields.function(_task_count, type='integer', string="Tasks",),
    
    @api.one
    def copy(self, default=None):
        """ Need to set origin after copy because original copy clears origin

        """

        if default is None:
            default = {}
        raise UserError(_(u'Хуулбарлаж үүсгэх боломжгүй!'))

        return super(tender_tender, self).copy(default=default)

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
                
    def _add_followers(self,user_ids): 
        '''Тендер дээр дагагч нарыг нэмнэ'''
        self.message_subscribe_users(user_ids=user_ids)
        if self.state in ['draft','bids','open','confirmed']:
            self.project_id.sudo().message_subscribe_users(user_ids=user_ids)
            self.work_graph_id.sudo().message_subscribe_users(user_ids=user_ids)
            self.work_task_id.sudo().message_subscribe_users(user_ids=user_ids)
            
    @api.model
    def create(self, vals):
        '''Тендерийн хүсэлт үүсгэх үед тендерийн 
            огнооны шалгуур ажиллана
        '''
        if vals.get('name','New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('tender.tender') or 'New'
        tender_id = super(tender_tender, self).create(vals)
        if vals.get('date_open_deadline') or vals.get('date_end'):
            if vals.get('date_open_deadline') >= vals.get('date_end'):
                raise ValidationError(_(u'Тендер зарлах огноо хаах огнооноос хэтэрсэн байна!!!'))
        
        if tender_id.state == 'published':
            for partner in tender_id.requirement_partner_ids:
                sent_partner_id = self.env['mail.sent.partners'].create({'tender_id':tender_id.id,'partner_id':partner.id,'is_mail_sent':False})
                #sent_partner_id.sent_tender_invitation()
        
        return tender_id

    @api.multi
    def action_to_delay(self):
        return {
            'type': 'ir.actions.act_window',
            'name': u'Тайлбар',
            'res_model': 'tender.tender.note',
            'view_type': 'form',
            'view_mode': 'form',
            'context':{'delay':'delay'},
            'target' : 'new',
        }
        

    @api.multi
    def action_to_draft(self):

        self.write({'state':'draft'}) 
        if self.invitation_id:
            self.env['tender.invitation.guide'].browse(self.invitation_id.id).write({'state':'draft'})

    @api.multi
    def action_allow_contract(self):
        self.write({'state':'contract_created','date_open_deadline':time.strftime('%Y-%m-%d %H:%M:%S'),'date_end':time.strftime('%Y-%m-%d %H:%M:%S')})
        
        notif_groups = self.env['ir.model.data'].get_object('nomin_tender', 'group_tender_branch_manager')
        sel_user_ids = []
        for user in notif_groups.users:
            if self.sector_id.id in user.tender_allowed_departments.ids:
                sel_user_ids.append(user)

        
        # subject = u'"%s" дугаартай "%s" тендерын гэрээ үүсгэх хүсэлт зөвшөөрөгдлөө.'%( self.name,self.desc_name)
        # db_name = request.session.db
        # base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        # action_id = self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_list')[1]
       
        # sel_user_ids.append(self.user_id)
        # body_html = u'''
        #                 <h4>Сайн байна уу?
        #                     Таньд энэ өдрийн мэнд хүргье! <br/>
        #                     "%s" дугаартай "%s" тендер гэрээ үүсгэх хүсэлт зөвшөөрөгдлөө.</h4>
        #                     <p><li><b>Тендерийн дугаар: </b>%s</li></p>
        #                     <p><li><b>Тендерийн нэр: </b>%s</li></p>
        #                     <p><li><b>Тендерийн ангилал: </b>%s</li></p>
        #                     <p><li><b>Дэд ангилал: </b>%s</li></p>
        #                     <p><li><b>Товлосон захиалгын огноо: </b>%s</li></p>
        #                     <p><li><b>Төлөв: </b>%s</li></p>

                            
        #                     </br>
        #                     <p>"%s" - н мэдээллийг <b><a href=%s/web?db=%s#id=%s&view_type=form&model=tender.tender.bid&action=%s>Тендер/Тендер зарлуулах хүсэлт</a></b> цонхоор дамжин харна уу.</p>
        #                     <p>--</p>
        #                     <p>Энэхүү имэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
        #                     <p>Баярлалаа.</p>
        #             '''%( self.name,self.desc_name, self.name,self.desc_name,self.type_id.name,
        #                     self.child_type_id.name,self.ordering_date,self.state, self.name,
        #                     base_url,
        #                     db_name,
        #                     self.id,
        #                     action_id)
        
        # for user in sel_user_ids:
        #     email = user.login
        #     if email or email.strip():
        #         email_template = self.env['mail.template'].create({
        #                 'name': _('Followup '),
        #                 'email_from': self.env.user.company_id.email or '',
        #                 'model_id': self.env['ir.model'].search([('model', '=', 'tender.tender')]).id,
        #                 'subject': subject,
        #                 'email_to': email,
        #                 'lang': self.env.user.lang,
        #                 'auto_delete': True,
        #                 'body_html':body_html,
        #                 #  'attachment_ids': [(6, 0, [attachment.id])],
        #                 })
        #         email_template.sudo().send_mail(self.id)

    @api.multi
    def action_contract_request(self):
        
        return {
            'type': 'ir.actions.act_window',
            'name': u'Тайлбар',
            'res_model': 'tender.request.note',
            'view_type': 'form',
            'view_mode': 'form',
            'target' : 'new',
        }

        notif_groups = self.env['ir.model.data'].get_object('nomin_base', 'group_holding_ceo')
        sel_user_ids = self.env['res.users'].search([('groups_id','in',groups)])
        subject = u'"%s" дугаартай "%s" тендерт оролцогч нэмэгдлээ.'%( self.tender_id.name,self.tender_id.desc_name)
        db_name = request.session.db
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        action_id = self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_list')[1]
        if sel_user_ids:
            self.write({'state':'contract_request'})
        # else:
        #     raise
        # body_html = u'''
        #                 <h4>Сайн байна уу?
        #                     Таньд энэ өдрийн мэнд хүргье! <br/>
        #                     "%s" дугаартай "%s" тендер гэрээ үүсгэх хүсэлтэй байна.</h4>
        #                     <p><li><b>Тендерийн дугаар: </b>%s</li></p>
        #                     <p><li><b>Тендерийн нэр: </b>%s</li></p>
        #                     <p><li><b>Тендерийн ангилал: </b>%s</li></p>
        #                     <p><li><b>Дэд ангилал: </b>%s</li></p>
        #                     <p><li><b>Товлосон захиалгын огноо: </b>%s</li></p>
        #                     <p><li><b>Төлөв: </b>%s</li></p>

                            
        #                     </br>
        #                     <p>"%s" - н мэдээллийг <b><a href=%s/web?db=%s#id=%s&view_type=form&model=tender.tender.bid&action=%s>Тендер/Тендер зарлуулах хүсэлт</a></b> цонхоор дамжин харна уу.</p>
        #                     <p>--</p>
        #                     <p>Энэхүү мэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
        #                     <p>Баярлалаа.</p>
        #             '''%( self.name,self.desc_name, self.name,self.desc_name,self.type_id.name,
        #                     self.child_type_id.name,self.ordering_date,u'Гэрээ үүсгэх хүсэлт', self.name,
        #                     base_url,
        #                     db_name,
        #                     self.id,
        #                     action_id)
        
        # for user in sel_user_ids:
        #     email = user.login
        #     if email or email.strip():
        #         email_template = self.env['mail.template'].create({
        #                 'name': _('Followup '),
        #                 'email_from': self.env.user.company_id.email or '',
        #                 'model_id': self.env['ir.model'].search([('model', '=', 'tender.tender')]).id,
        #                 'subject': subject,
        #                 'email_to': email,
        #                 'lang': self.env.user.lang,
        #                 'auto_delete': True,
        #                 'body_html':body_html,
        #                 #  'attachment_ids': [(6, 0, [attachment.id])],
        #                 })
        #         email_template.sudo().send_mail(self.id)

    @api.multi
    def write(self,vals):
        '''Тендер мэдээлэл засах үед ажилтаны нэр давхардаж 
           байгааг шалгах, нийтлэгдсэн төлөвтэй байвал харилцагч 
           нарт имэйл илгээх, огнооны шалгуур ажиллуулах гэхмэт
           үйлдлүүд хийнэ
        '''
        tender=self
        members = []
        conf_members = []
        sent_partner_ids = []
        sent_user_ids = []
        sub_users = []
        mail_sent_partner_ids = []

        if vals.get('sub_user_ids'):
            for sub in vals.get('sub_user_ids'):
                sub_users.append(sub)
        
        if tender.state == 'published':
            if sub_users:    
                for sub in self.env['subscribe.users'].browse(sub_users[0][2]):
                    self.env['subscribe.users'].send_tender_invitation_subusers(sub.id, tender.id)
            
                   
        for mail in tender.mail_sent_partner_ids: 
            if mail.partner_id.id:
                sent_partner_ids.append(mail.partner_id.id)
            
        if tender.state == 'published':
            for part in tender.requirement_partner_ids:
                if part.id not in sent_partner_ids:
                    mail_sent_partner_id = self.pool['mail.sent.partners'].create(self.env.cr, 1,{'tender_id':tender.id,'partner_id':part.id,'is_mail_sent':False})
                    mail_sent_partner_obj = self.env['mail.sent.partners'].browse(mail_sent_partner_id)
                    mail_sent_partner_obj.sent_tender_invitation()
                   
        for member in tender.confirmed_member_ids:
            members.append(member.employee_id.id)
        
        # if vals.get('confirmed_member_ids'):
        #     for i in vals.get('confirmed_member_ids'):
        #         if i[2] != False:
        #             conf_members.append(i[2]['employee_id'])
        #             if i[2]['employee_id'] in members:
        #                 raise UserError(_(u'Ажилтны нэр давхацсан байна!'))
        #         if conf_members:
        #             duplicates = [x for x in conf_members if conf_members.count(x) > 1]
        #             if duplicates:
        #                 raise UserError(_(u'Ажилтны нэр давхацсан байна!'))
        #             else:
        #                 emp_ids = self.env['hr.employee'].browse(conf_members)
        #                 for employee in emp_ids:
        #                     tender._add_followers(employee.user_id.id)
            
        # com_members = []
        # committee_members = []
        # for committee in tender.committee_member_ids:
        #     com_members.append(committee.employee_id.id)
        
        # if vals.get('committee_member_ids'):
        #     for i in vals.get('committee_member_ids'):
        #         if i[2] != False:
        #             if i[2].has_key('employee_id'):
        #                 committee_members.append(i[2]['employee_id'])
        #                 if i[2]['employee_id'] in com_members:
        #                    raise UserError(_(u'Ажилтны нэр давхацсан байна!'))
        #         if committee_members:
        #             duplicate = [x for x in committee_members if committee_members.count(x) > 1]
                    
        #             if duplicate:
        #                 raise UserError(_(u'Ажилтны нэр давхацсан байна!'))
        #             else:
        #                 emp_ids = self.env['hr.employee'].browse(committee_members)
        #                 for employee in emp_ids:
        #                     tender._add_followers(employee.user_id.id)
            
        emp_ids = []
        extend_obj = self.env['tender.date.extend']
        for this in tender:
            if vals and vals.get('state') and vals.get('state') == 'confirmed' and not this.invitation_id:
                invitation_values = {}
                invitation_values.update({'tender_id':this.id})
                invitation_values.update({'name':this.desc_name})
                #invitation_values.update({'summary':this.description})
                invitation_values.update({'invitation_detail':this.special_require})
                invitation_id = self.pool['tender.invitation.guide'].create(self.env.cr, 1,invitation_values)
                vals.update({'invitation_id': invitation_id})
                
            if vals.get('respondent_employee_id'):
                emp_ids=self.env['hr.employee'].browse(vals.get('respondent_employee_id'))
                if emp_ids:
                    this._add_followers(emp_ids.user_id.id)
#         if 'member_ids' in values:
#             member_ids = values.get("member_ids")
#             for employee in self.browse(cr, uid, ids).member_ids:
#                 employee_ids = self.pool.get('hr.employee').search(cr,uid,[('id','=',employee.id)])
#                 if employee_ids:
#                     for employee_id in employee_ids:
#                         emp_ids.append(employee_id)
#                         employee=self.pool.get('hr.employee').browse(cr,uid,employee_id)
#                         if employee.user_id:
#                             self.add_follower(cr,employee.user_id.id,ids)
#                         else:
#                             raise osv.except_osv(_('Warning!'), _(u'Ажилтанд холбогдох хэрэглэгч алга байна.'))
#                 else:
#                     raise osv.except_osv(_('Warning!'), _(u'Ажилтанд холбогдох ажилтан алга байна. Систем админтай холбогдоно уу.'))
        
        if vals.get('date_open_deadline'):
            date_open_deadline=False
            date_open_deadline = vals.get('date_open_deadline')
        else:
            date_open_deadline = tender.date_open_deadline
        
        if vals.get('date_end'):
            date_end=False
            date_end = vals.get('date_end')
        else:
            date_end = tender.date_end
        
        if date_open_deadline or date_end:
            if date_open_deadline > date_end:
                raise UserError(_(u'Тендер зарлах огноо хаах огнооноос хэтэрсэн байна.'))
        tender_id = super(tender_tender, self).write(vals)    
                 
        return tender_id
    
    @api.multi
    def send_notification(self,signal):
        '''Тендерийн төлөв солигдох бүрт дагагч нарт имэйл илгээнэ'''
        states = {
                  'draft': u'Ноорог',
                  'allowed': u'Илгээгдсэн',
                  'bids': u'Илгээгдсэн',
                  'open':u'Нээлттэй',
                  'confirmed':u'Батлагдсан',
                  'send_to_manager':u'Нийтлэхэд бэлэн',
                  'published':u'Нийтлэгдсэн',
                  'closed': u'Хаасан',
                  'in_selection':u'Сонгон шалгаруулалт',
                  'finished':u'Дууссан',
                  'open_purchase':u'Цуцлагдсан',
                  }
        user = self.env['res.users'].browse(self.env.user.id)
        mail_obj = self.env['mail.followers']
        template_id = self.env['ir.model.data'].get_object_reference('nomin_tender', 'tender_state_change_followers_email_template')[1]
        
        
        followers = []
        for follower in self.message_follower_ids:
            followers.append(follower.partner_id.id)
        user_ids = []
        if followers:
            user_ids = self.env['res.users'].search([('partner_id','in',followers)])
        
        requist_obj = self
        data = {
                'subject': u'Тендерийн мэдэгдэл',
                'name': requist_obj.name,
                'company': requist_obj.company_id.name,
                'child_type': requist_obj.child_type_id.name,
                'ordering_date':requist_obj.ordering_date,
                'requisition_name': requist_obj.requisition_id.name,
                'type_name': requist_obj.type_id.name,
                'desc_name': requist_obj.desc_name,
                'model': 'tender.tender',
                'base_url': self.env['ir.config_parameter'].get_param('web.base.url'),
                'action_id': self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_list')[1],
                'id': requist_obj[0].id,
                'db_name': request.session.db, 
                'sender': self.env['res.users'].browse(self.env.user.id).name,
                'state': states[signal],
                'menu_path': u'Тендер / Тендер / Тендер жагсаалт',
                }
        for user_id in user_ids:
            if user_id.id != self.env.user.id:
                self.env.context = data
                self.pool['mail.template'].send_mail(self.env.cr, 1, template_id, user_id.id, force_send=True, context=self.env.context)
        return True
    
    
    #Tsutslagdsan tenderees hudaldan avaltiin uniin sanal uusehed hamgamjiin HAAA bolon HIM groupd email ilgeeh heseg
    @api.multi
    def send_mail_purchase_employees(self, l_id):        
        template_id = self.env['ir.model.data'].get_object_reference('nomin_tender', 'send_mail_purchase_employees_email_template')[1]        
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        action_id = self.env['ir.model.data'].get_object_reference('purchase', 'purchase_rfq')[1]
        db_name = request.session.db
        #Hangamj importiin menejeriin group
        group_id = self.env['ir.model.data'].get_object_reference('nomin_purchase_requisition', 'group_supply_import_manager')[1]
        user_obj = self.env['res.users'].search([('groups_id','in',group_id)])
        
        #XAAA darga group
        group_id1 = self.env['ir.model.data'].get_object_reference('nomin_purchase_requisition', 'group_haaa_head')[1]
        user_obj1 = self.env['res.users'].search([('groups_id','in',group_id1)])
        order_name = self.env['purchase.order'].search([('id','=',l_id)])
        
        data = {
            'name': self.name,
            'base_url': base_url,
            'purchase': order_name.name,
            'db_name': db_name,
            'action_id': action_id,
            'id': l_id
            }
        self.env.context = data
        if user_obj:
            for user_id in user_obj:
                self.pool['mail.template'].send_mail(self.env.cr, 1, template_id, user_id.id, force_send=True, context=self.env.context)
        if user_obj1:    
            for user_id in user_obj1:
                self.pool['mail.template'].send_mail(self.env.cr, 1, template_id, user_id.id, force_send=True, context=self.env.context)
        return True
    
    
    @api.multi
    def sent_tender_results(self):
        '''Тендер шалгаруулалтын үр дүн гарахад оролцогч нарт имэйл илгээнэ'''
        participant_ids = self.env['tender.valuation.partner'].search([('tender_id','=',self.id)])
        for participant in participant_ids:
            if participant.is_win == True:
                result = u'шалгарсан'
                template_id = self.env['ir.model.data'].get_object_reference('nomin_tender', 'tender_valuation_result_email_template')[1]
                val_obj = self
                # tender_obj = self.env['tender.tender'].browse(val_obj.tender_id.id)
                
                data = {
                        'subject': u'"Номин Холдинг" ХХК-ийн "%s" тендерийн үр дүн гарлаа.'%(self.desc_name),
                        'company': self.company_id.name,
                        'name': self.name,
                        'desc_name': self.desc_name,
                        'is_win': result,
                        # 'description': val_obj.reason,
                        'model': 'tender.tender',
                        }
                self.env.context = data
                self.pool['mail.template'].send_mail(self.env.cr, 1, template_id, participant.partner_id.id, force_send=True, context=self.env.context)
                # return True

                # participant.send_tender_result(result)
            else:
                result = u'шалгараагүй'
                template_id = self.env['ir.model.data'].get_object_reference('nomin_tender', 'tender_valuation_result_email_template')[1]
                val_obj = self
                # tender_obj = self.env['tender.tender'].browse(val_obj.tender_id.id)
                
                data = {
                        'subject': u'"Номин Холдинг" ХХК-ийн "%s" тендерийн үр дүн гарлаа.'%(self.desc_name),
                        'company': self.company_id.name,
                        'name': self.name,
                        'desc_name': self.desc_name,
                        'is_win': result,
                        # 'description': val_obj.reason,
                        'model': 'tender.tender',
                        }
                self.env.context = data
                self.pool['mail.template'].send_mail(self.env.cr, 1, template_id, participant.partner_id.id, force_send=True, context=self.env.context)

                
                # participant.send_tender_result(result)
            participant.write({'is_sent':True})
        self.write({'is_sent_result': True})
    
    @api.multi
    def action_to_confirm(self):
        '''Тендерийн хүсэлтийг хүсэлт батлах 
           удирдлагаар сонгогдсон ажилчид батална
        '''
        extend_obj = self.env['tender.date.extend']
        tender_obj = self
        #model_obj = openerp.pooler.get_pool(cr.dbname).get('ir.model.data')
        notif_groups = self.env['ir.model.data'].get_object_reference('nomin_tender', 'group_tender_secretary')
        group_user_ids = []
        
        sel_user_ids = self.env['res.users'].search([('groups_id','in',[notif_groups[1]])])
        group_user_ids = self.env['res.users'].search([('id','in',sel_user_ids)])
        if group_user_ids:
            users = self.env['res.users'].browse(group_user_ids)
            for user in users:
                self.add_follower(user.id)
        
        # for tender in tender_obj:
        #     if not tender.extend_requist_ids and tender.date_open_deadline and tender.date_end:
        #         self.write(cr, 1, ids,{'extend_requist_ids': [(0, 0, {'tender_id': tender.id,
        #                                  'name': 1,
        #                                  'extend_date_start': tender.date_open_deadline,
        #                                  'extend_date_end': tender.date_end,
        #                                  'extend_content': u'Анхны үүсгэл',
        #                                  'state':'done'})]},
        #                                  context=context)
        # self.send_notification(cr, uid, ids, 'confirmed')
        self.write({'state':'confirmed'})
    
    @api.multi
    def action_back(self):
        """Тендерийн хүсэлтийг тендерийн нарийн бичиг буцаах"""
        #mod_obj = self.pool.get('ir.model.data')
        res = self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_tender_note')
        
        return {
            'type': 'ir.actions.act_window',
            'name': u'Тайлбар',
            'res_model': 'tender.tender.note',
            'view_type': 'form',
            'view_mode': 'form',
            'target' : 'new',
        }
    
    @api.multi   
    def send_to_manager(self):
        """Тендерийн хорооны даргад илгээх"""
        #model_obj = openerp.pooler.get_pool(cr.dbname).get('ir.model.data')
        notif_groups = self.env['ir.model.data'].get_object_reference('nomin_tender', 'group_tender_manager')
        
        #tender_obj = self.browse(cr, uid, ids)
        for tender in self:
            if not tender.invitation_id:
                raise UserError(_(u'Тендерийн урилга үүсээгүй байна !'))
                
            if not tender.committee_member_ids:
                raise UserError(_(u'Тендерийн комиссын гишүүдийг томилно уу !'))
                
            if not tender.requirement_partner_ids:
                raise UserError(_(u'Урилга хүлээн авах харилцагчид хоосон байна !'))
                
        
            sel_user_ids = []
            group_user_ids = []
            sel_user_obj = self.env['res.users'].search([('groups_id','in',[notif_groups[1]])])
            for sel_user_line in sel_user_obj:
                sel_user_ids.append(sel_user_line.id)
            group_user_obj = self.env['res.users'].search([('id','in',sel_user_ids)])
            for group_user_line in group_user_obj:
                group_user_ids.append(group_user_line.id)
            if group_user_ids:
                users = self.env['res.users'].browse(group_user_ids)
                for user in users:
                    tender._add_followers(user.id)
                    
            if tender.invitation_id:
                self.env['tender.invitation.guide'].browse(tender.invitation_id.id).write({'state':'open'})
        self.write({'state':'send_to_manager'})
        # self.send_notification('send_to_manager')
        
        
#===============================================================================
# if tender_obj.requisition_id.id:
#             purchase_obj = self.pool.get('purchase.requisition')
#             purchase_id=purchase_obj.search(cr, SUPERUSER_ID, [('id','=',tender_obj.requisition_id.id)])
#             if purchase_id: 
#                 pur_obj = self.pool.get('purchase.requisition').browse(cr, uid, purchase_id)
#                 #print 'n\n\n\n\n\n\n\n\nTEST', pur_obj.state
#                 if pur_obj.state == 'confirmed':
#                     #self.send_notif_to_followers(cr, uid, ids, 'send_to_manager')
#                     #self.send_notification(cr, uid, ids, 'send_to_manager')
#                     self.write(cr, uid, ids, {'state':'send_to_manager'},context=context)
#                 else:
#                     raise osv.except_osv(_('Warning !'), _(u"Худалдан авалтын шаардах батлагдаагүй тул тендерийн хорооны даргад илгээх боломжгүй."))
#===============================================================================
    @api.multi
    def action_to_publish(self):
        """Тендерийг веб-д байршуулах"""
        for order in self:
            if order.date_open_deadline < time.strftime('%Y-%m-%d %H:%M:%S'):
                raise UserError(_(u'Тендер зарлах огноо хэтэрсэн байна.'))
            if time.strftime('%Y-%m-%d %H:%M:%S') > order.date_end:
                raise UserError(_(u'Тендер хаах огноо хэтэрсэн байна.'))
             
            if order.invitation_id:
                self.env['tender.invitation.guide'].browse(order.invitation_id.id).write({'state':'done'})
                self.env['tender.work.task'].create({'tender_id': order.id, 
                                                     'tender_work_document_id': order.invitation_id.tender_doc_id.id })

            if order.is_publish == False:
                order.write({'is_publish': True,
                             'published_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                             'state': 'published'
                             })
                if not order.extend_requist_ids and order.date_open_deadline and order.date_end:
                    self.write({'extend_requist_ids': [(0, 0, {'tender_id': order.id,
                                         'name': 1,
                                         'extend_date_start': order.date_open_deadline,
                                         'extend_date_end': order.date_end,
                                         'extend_content': u'Анхны үүсгэл',
                                         'state':'done'})]})
            else:
                raise UserError(_(u'Нийтлэгдсэн тендер байна.'))
            
            for part in order.requirement_partner_ids:
                mail_sent_partner_id = self.env['mail.sent.partners'].create({'tender_id':order.id,'partner_id':part.id,'is_mail_sent':False})
                _logger.info(u'\n\n\n\n\nТендерийн урилга имэйл илгээх харилцагчид байна %s', mail_sent_partner_id)
                mail_sent_partner_id.sent_tender_invitation()
        self.send_notification('published')
        #self.send_invitation_notif(cr, uid, ids, 'published')

    @api.multi            
    def action_to_secretary(self):
        """Тендерийн нарийн бичиг рүү тайлбар 
           бичиж тендерийн хорооны дарга буцаах
        """
        res = self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_tender_note')
        
        return {
            'type': 'ir.actions.act_window',
            'name': u'Тайлбар',
            'res_model': 'tender.tender.note',
            'view_type': 'form',
            'view_mode': 'form',
            'target' : 'new',
        }
        
        self.send_notification('confirmed')
        #self.write(cr, uid, ids, {'state':'confirmed'},context=context)
    
    @api.multi
    def action_to_extend(self):
        """Тендерийн хугацаа сунгах хүсэлт үүсгэх"""
        #mod_obj = self.pool.get('ir.model.data')
        res = self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_extend_menu')
        context = self.env.context.copy()
        context.update({'tender_tender': self.id})
        return {
            'name': u'Тендерийн хугацаа сунгалт',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tender.date.extend',
            'context': context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }
    
    @api.multi
    def action_to_protocol(self):
        """Тендерийн протокол"""
        #mod_obj = self.pool.get('ir.model.data')
        res = self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_protocol_menu')
        context.update({'tender_tender': self.id})
        
        return {
            'name': 'Meeting Protocol',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tender.protocol',
            'context': context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
        }
       
    @api.multi
    def action_closed(self):
        """Тендерийн хаана"""  
        participants = self.env['tender.participants.bid']
        
        for tender in self:
            for partner in tender.participants_ids:
                if partner.state == 'sent':
                    participants.browse(partner.id).write({'state':'open_document'})
                        
        self.write({'state':'closed',
                    'closed_date': time.strftime('%Y-%m-%d')})
        extend_ids = self.env['tender.date.extend'].search([('tender_id','=',self.id),('state','in',['draft','pending'])])
        print'_______TTT______',extend_ids
        if extend_ids:
            for extend in extend_ids:
                extend.write({'state':'cancelled'})
        self.send_notification('closed')

    @api.multi
    def create_valuation(self):
        """Тендер үнэлгээ үүсгэх"""  
        valuation_obj=self.env['tender.valuation'] #Үнэлгээ
        partner_obj=self.env['tender.valuation.partner'] #тендерт оролцогчид
        employee_val_obj=self.env['tender.valuation.employee.valuation'] #Комиссын гишүүдийн өгсөн үнэлгээ
        employee_partner_obj=self.env['tender.valuation.employee.partner'] #Нэг гишүүний нэг оролцогчид өгсөн үнэлгээ
        rate_line_obj=self.env['tender.valuation.rate.line'] #Үзүүлэлт бүрийг үнэлсэн байдал
        rate_obj=self.env['tender.type.rate.max'] #Тохиргоо
        type_obj=self.env['tender.type'] #Тендерийн ангилал
        participants_obj=self.env['tender.participants.bid'] #Тендерт оролцогчид
        rate_id = []
        part_ids = []
        val_partner_ids = []
        partic_ids = []
        partner_count = 0
        employee_count = 1
        emp_part_count = 1
        line_count = 1
        for tender in self:
            self.env.cr.execute("select A.id as type_id,A.max_value as max_value,B.name as rate_name,A.rate_id as rate_id from tender_type_rate_max A inner join tender_rate B on  B.id=A.rate_id\
                where A.tender_type_id=%s"%(tender.type_id.id))
            rate_ids = self.env.cr.dictfetchall()

            if not rate_ids:
                raise UserError(_(u'Тендерийн үзүүлэлтийн оноо тохируулаагүй байна !'))
            if not tender.participants_ids:
                raise UserError(_(u'Тендерт оролцогч хоосон байна !'))
             
            for participants in tender.participants_ids:
                if participants.state in ['sent','open_document','open_cost']:
                    part_ids.append(participants)
                if not part_ids:
                    raise UserError(_(u'Тендерийн оролцогчид хоосон байна !'))
                 
            valuation_vals = {
                              'tender_id': tender.id, 
                              'name': tender.name + u' шалгаруулалт'
                              }
            valuation_id = valuation_obj.create(valuation_vals)
            _logger.info(u'-------------- Тендерийн үнэлгэээ %s', valuation_id)

            for partic in tender.participants_ids:
                if partic.state in ['sent', 'open_document','open_cost']:
                    _logger.info(u'-------------- Тендерийн оролцогчид %s', partic)
                   
                    self.env.cr.execute("insert into tender_valuation_partner (tender_id,participant_id,partner_id,tender_valuation_id) \
                         values (%s,%s,%s,%s) returning id"%(tender.id,partic.id,partic.partner_id.id,valuation_id.id))
                    val_partner_id = self.env.cr.fetchone()
                    val_partner_ids.append((val_partner_id,partic.partner_id.id))
                    partner_count +=1

            self.env.cr.execute("select A.id as Aid,A.partner_id as partner,sum(( C.unit_price *C.qty)+C.costs_of_materials+C.other_costs) as total from tender_valuation_partner A \
                                inner join tender_participants_bid B on A.participant_id=B.id \
                                left join participants_work_task_line C on C.task_id=B.id \
                                where A.tender_id=%s group by Aid,partner order by total asc"%(tender.id))
            val_partners = self.env.cr.dictfetchall()
            _logger.info(u'-------------- Тендерийн үнэлгэээ өгөх харилцагчид %s', val_partners)
            for member in tender.committee_member_ids:
                if member.is_valuation:
                  
                    self.env.cr.execute("insert into tender_valuation_employee_valuation (tender_id,employee_id,tender_valuation_id,create_date) \
                        values (%s,%s,%s,now()-interval '8 hour') returning id"%(tender.id,member.employee_id.id,valuation_id.id))
                    employee_val_id= self.env.cr.fetchone()
                    _logger.info(u'-------------- Тендерийн үнэлгэээ өгөх ажилтан %s', employee_val_id)
                    if employee_val_id:
                        print'_____________employee_val_id_______________',employee_val_id
                        # for partic in val_partner_ids: 
                        value = 0
                        first_value = 0
                        first_total = 0
                        for part in val_partners:
                            print'_____________part_______________',part
                            rate_lines = []
                            
                            self.env.cr.execute("insert into tender_valuation_employee_partner (tender_id,tender_valuation_id,tender_valuation_partner_id,\
                                employee_id, employee_valuation_id,partner_id,create_date) values (%s,%s,%s,%s,%s,%s,now()-interval '8 hour') returning id "%(tender.id,valuation_id.id,part['aid'],member.employee_id.id,employee_val_id[0],part['partner']))
                            emp_partner_id =self.env.cr.fetchone()
                            for line in rate_ids:
                                print'_____________line_______________',line
                                print'_____________line_ssssss______________',line['type_id']
                                _logger.info(u'-------------- Тендерийн үнэлгэээ line %s,', line)
                                # if line['type_id'] in [132,147,158,162,167,168]:
                                if line['type_id'] in [0]:
                                    
                                    if first_value==0:
                                        first_value = line['max_value']
                                        value = first_value
                                        first_total = part['total']
                                    else:
                                        if part['total'] == first_total:
                                            value = first_value
                                        else:
                                            if partner_count==0:
                                                partner_count = 1
                                            first_value =first_value -line['max_value']/partner_count
                                            first_total = part['total']
                                            value = first_value
                                    
                                    # self.env.cr.execute("insert into tender_valuation_rate_line (partner_id,condition,tender_id,tender_valuation_id,tender_valuation_partner_id,\
                                    # rate_id,max_value,rate_name,employee_valuation_id,employee_partner_id,rate_value) \
                                    #  values (%s,'%s',%s,%s,%s,%s,%s,'%s',%s,%s,%s)"%(part['partner'],str(line['max_value'])+" => ",tender.id,valuation_id.id,part['aid'],line['rate_id'],line['max_value'],line['rate_name'],employee_val_id[0],emp_partner_id[0],value))
                                    self.env.cr.execute("insert into tender_valuation_rate_line (partner_id,condition,tender_id,tender_valuation_id,tender_valuation_partner_id,\
                                    rate_id,max_value,rate_name,employee_valuation_id,employee_partner_id,rate_value) \
                                     values (%s,'%s',%s,%s,%s,%s,%s,'%s',%s,%s,%s)"%(part['partner'],str(line['max_value'])+" => ",tender.id,valuation_id.id,part['aid'],line['rate_id'],line['max_value'],line['rate_name'],employee_val_id[0],emp_partner_id[0],line['max_value']))

                 
                                else: 
                                    print'_____________line['']________________',line['type_id'] 
                                    # self.env.cr.execute("insert into tender_valuation_rate_line (partner_id,condition,tender_id,tender_valuation_id,tender_valuation_partner_id,\
                                    # rate_id,max_value,rate_name,employee_valuation_id,employee_partner_id) values (%s,'%s',%s,%s,%s,%s,%s,'%s',%s,%s)"%(part['partner'],str(line['max_value'])+" => ",tender.id,valuation_id.id,part['aid'],line['rate_id'],line['max_value'],line['rate_name'],employee_val_id[0],emp_partner_id[0]))
                                    self.env.cr.execute("insert into tender_valuation_rate_line (partner_id,condition,tender_id,tender_valuation_id,tender_valuation_partner_id,\
                                    rate_id,max_value,rate_name,employee_valuation_id,employee_partner_id,rate_value) values (%s,'%s',%s,%s,%s,%s,%s,'%s',%s,%s,%s)"%(part['partner'],str(line['max_value'])+" => ",tender.id,valuation_id.id,part['aid'],line['rate_id'],line['max_value'],line['rate_name'],employee_val_id[0],emp_partner_id[0],line['max_value']))

                 
            partic_ids = participants_obj.search([('tender_id','=',tender.id),('state','in',['sent','open_document','open_cost'])])
            if partic_ids:
                partic_ids.write({'state':'open_cost'})
        _logger.debug(u'------------------------------- Тендерийн үнэлгээ дууслаа --------------')
        # self.send_notif_partners()
        valuation_id.action_confirm()
        return self.write({'is_valuation_created': True, 'state': 'in_selection'})

    
    @api.multi
    def send_notif_partners(self):
        
         
        subject = u'Таны оролцсон "%s" дугаар "%s" нэртэй тендер дээр сонгон шалгаруулалт хийгдэж эхэллээ.'%( self.name,self.desc_name)
        db_name = request.session.db
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        action_id = self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_list')[1]
       
        
        body_html = u'''
                        <h4>Сайн байна уу?
                            Таньд энэ өдрийн мэнд хүргье! <br/>
                            Таны оролцсон "%s" дугаар "%s" нэртэй тендер дээр сонгон шалгаруулалт хийгдэж эхэллээ.</h4>
                            <p><li><b>Тендерийн дугаар: </b>%s</li></p>
                            <p><li><b>Тендерийн нэр: </b>%s</li></p>
                            <p><li><b>Тендерийн ангилал: </b>%s</li></p>
                            <p><li><b>Дэд ангилал: </b>%s</li></p>
                            <p><li><b>Товлосон захиалгын огноо: </b>%s</li></p>
                            
                            
                            </br>                         
                            <p>Энэхүү имэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
                            <p>Баярлалаа.</p>
                    '''%( self.name,self.desc_name, self.name,self.desc_name,self.type_id.name,
                            self.child_type_id.name,self.ordering_date)
        
        for user in self.participants_ids:
            email = user.partner_id.email
            if email and email.strip():
                email_template = self.env['mail.template'].create({
                        'name': _('Followup '),
                        'email_from': self.env.user.company_id.email or '',
                        'model_id': self.env['ir.model'].search([('model', '=', 'tender.tender')]).id,
                        'subject': subject,
                        'email_to': email,
                        'lang': self.env.user.lang,
                        'auto_delete': True,
                        'body_html':body_html,
                        #  'attachment_ids': [(6, 0, [attachment.id])],
                        })
                email_template.sudo().send_mail(self.id)
    @api.multi
    def send_delay_notif(self):
        
         
        subject = u'Таны оролцсон "%s" дугаар "%s" нэртэй тендер хойшлогдлоо.'%( self.name,self.desc_name)
        db_name = request.session.db
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        action_id = self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_list')[1]
       
        
        body_html = u'''
                        <h4>Сайн байна уу?
                            Таньд энэ өдрийн мэнд хүргье! <br/>
                            Таны оролцсон "%s" дугаар "%s" нэртэй тендер хойшлогдлоо.</h4>
                            <p><li><b>Тендерийн дугаар: </b>%s</li></p>
                            <p><li><b>Тендерийн нэр: </b>%s</li></p>
                            <p><li><b>Тендерийн ангилал: </b>%s</li></p>
                            <p><li><b>Дэд ангилал: </b>%s</li></p>
                            <p><li><b>Товлосон захиалгын огноо: </b>%s</li></p>      


                            </br>                         
                            <p>Энэхүү имэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
                            <p>Баярлалаа.</p>
                    '''%( self.name,self.desc_name, self.name,self.desc_name,self.type_id.name,
                            self.child_type_id.name,self.ordering_date)
        
        for user in self.participants_ids:
            email = user.partner_id.email
            if email or email.strip():
                email_template = self.env['mail.template'].create({
                        'name': _('Followup '),
                        'email_from': self.env.user.company_id.email or '',
                        'model_id': self.env['ir.model'].search([('model', '=', 'tender.tender')]).id,
                        'subject': subject,
                        'email_to': email,
                        'lang': self.env.user.lang,
                        'auto_delete': True,
                        'body_html':body_html,
                        #  'attachment_ids': [(6, 0, [attachment.id])],
                        })
                email_template.sudo().send_mail(self.id)


    @api.multi
    def action_cancelled(self):
        '''Тендерийн цуцлана'''
        return {
            'type': 'ir.actions.act_window',
            'name': u'Тайлбар',
            'res_model': 'tender.cancel.note',
            'view_type': 'form',
            'view_mode': 'form',
            'target' : 'new',
        }
        
    
    #------------------------------------------- def _tender_alarm(self,cr,uid):
        #------------------------------------- '''Тендерийн хаах огноо болох үед
           #------------------------------------- систем автоматаар төлөв солино
        #------------------------------------------------------------------- '''
        # query = "select tender.id as tid, tender.name as tnumber, tender.desc_name tname, type.name as parent_type, child_type.name as child_type, \
                    # tender.ordering_date orderdate, tender.state state, tender.date_end \
                    # from tender_tender as tender, tender_type as type, tender_type as child_type \
                    # where tender.state = 'published' and type.id = tender.type_id and child_type.id = tender.child_type_id"
        #----------------------------------------------------- cr.execute(query)
        #---------------------- print 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAa'
        #------------------------------------------- records = cr.dictfetchall()
        # template_id = self.pool['ir.model.data'].get_object_reference(cr, SUPERUSER_ID,'nomin_tender', 'tender_tender_closed_state_email_template')[1]
        #--------------------------------- tender_obj=self.pool['tender.tender']
#------------------------------------------------------------------------------ 
        #----------------------------------------------------------- if records:
            #-------------------------------------------- for record in records:
                #--------------------------------- date_end = record['date_end']
                #------------------- date_now=time.strftime('%Y-%m-%d %H:%M:%S')
                #-------------------------------------- if date_end <= date_now:
                    # tender_obj.write(cr, SUPERUSER_ID, record['tid'], {'state':'bid_expire'}, context=None)
                    #-------------------------------------------------- data = {
                        #---------------------------- 'name': record['tnumber'],
                        #------------------------- 'desc_name': record['tname'],
                        #------------------- 'type_name': record['parent_type'],
                        #------------------- 'child_type': record['child_type'],
                        #------------------ 'ordering_date':record['orderdate'],
                        #---------- 'state': u'Бичиг баримт хүлээн авч дууссан',
                        # 'base_url': self.pool['ir.config_parameter'].get_param(cr, uid,'web.base.url'),
                        # 'action_id': self.pool['ir.model.data'].get_object_reference(cr, uid,'nomin_tender', 'action_tender_list')[1],
                        #---------------------------------- 'id': record['tid'],
                        #------------------------ 'db_name': request.session.db,
                        #- 'menu_path': u'Тендер / Тендер / Тендерийн жагсаалт',
                        #----------------------------------------------------- }
#------------------------------------------------------------------------------ 
                    #----------------------------------------------- groups = []
                    # notif_groups = self.pool['ir.model.data'].get_object_reference(cr, uid,'nomin_tender', 'group_tender_manager')
                    #---------------------------- groups.append(notif_groups[1])
                    # notif_groups = self.pool['ir.model.data'].get_object_reference(cr, uid,'nomin_tender', 'group_tender_secretary')
                    #---------------------------- groups.append(notif_groups[1])
#------------------------------------------------------------------------------ 
                    #--------------------------------------- group_user_ids = []
#------------------------------------------------------------------------------ 
                    # sel_user_ids = self.pool.get('res.users').search(cr,uid,[('groups_id','in',groups)])
                    # group_user_ids = self.pool.get('res.users').search(cr,uid,[('id','in',sel_user_ids)])
                    #---------------------------------------- if group_user_ids:
                        # users = self.pool.get('res.users').browse(cr,uid,group_user_ids)
                        #------------------------------------ for user in users:
                            # self.pool.get('mail.template').send_mail(cr, uid, template_id, user.id, force_send=True, context=date)

    def _tender_alarm(self, cr, uid):
        print'________________tender_alarm__________'
        _logger.info(u'\n\n\n\n\nТендерийн cron ажиллаж байна')
        '''Тендерийн хаах огноо болох үед 
           систем автоматаар төлөв солино
        '''
        query = "select tender.id as tid, tender.name as tnumber, tender.desc_name tname, type.name as parent_type, child_type.name as child_type, \
                    tender.ordering_date orderdate, tender.state state, tender.date_end \
                    from tender_tender as tender, tender_type as type, tender_type as child_type \
                    where tender.state = 'published' and type.id = tender.type_id and child_type.id = tender.child_type_id"
        cr.execute(query)
        records = cr.dictfetchall()
        template_id = self.pool.get('ir.model.data').get_object_reference(cr, SUPERUSER_ID, 'nomin_tender', 'tender_tender_closed_state_email_template')[1]
        tender_obj=self.pool.get('tender.tender')
        if records:
            for record in records:
                # date_end = record['date_end']
                # ADD time 8 hours
                date_end =datetime.datetime.strptime(record['date_end'], "%Y-%m-%d %H:%M:%S")
                date_now=datetime.datetime.now()
                if date_end <= date_now:
                    tender_obj.write(cr, SUPERUSER_ID, record['tid'], {'state':'bid_expire'}, context=None)
                    cr.commit()
                    # data = {
                    #     'name': record['tnumber'],
                    #     'desc_name': record['tname'],
                    #     'type_name': record['parent_type'],
                    #     'child_type': record['child_type'],
                    #     'ordering_date':record['orderdate'],
                    #     'state': u'Бичиг баримт хүлээн авч дууссан',
                    #     'base_url': self.pool.get('ir.config_parameter').get_param(cr, uid, 'web.base.url'),
                    #     'action_id': self.pool.get('ir.model.data').get_object_reference(cr, uid, 'nomin_tender', 'action_tender_list')[1],
                    #     'id': record['tid'],
                    #     'db_name': cr.dbname, #openerp.http.request.session.db
                    #     'menu_path': u'Тендер / Тендер / Тендерийн жагсаалт',
                    #     }
                    
                    # groups = []
                    # notif_groups = self.pool.get('ir.model.data').get_object_reference(cr, SUPERUSER_ID, 'nomin_tender', 'group_tender_manager')
                    # groups.append(notif_groups[1])
                    # notif_groups = self.pool.get('ir.model.data').get_object_reference(cr, SUPERUSER_ID, 'nomin_tender', 'group_tender_secretary')
                    # groups.append(notif_groups[1])
                    
                    group_user_ids = []
                    
                    # sel_user_ids = self.pool.get('res.users').search(cr,uid,[('groups_id','in',groups)])
                    # group_user_ids = self.pool.get('res.users').search(cr,uid,[('id','in',sel_user_ids)])
                    # if group_user_ids:
                    #     users = self.pool.get('res.users').browse(cr, uid, group_user_ids)
                    #     for user in users:
                    #         self.pool.get('mail.template').send_mail(cr, uid, template_id, user.id, force_send=True, context=data)
                            
    @api.one
    def _get_remaining(self):
        '''Тендерийн хаах хугацааг тооцоолох'''
        if self.date_end:
            temp_date = datetime.datetime.strptime(self.date_end, "%Y-%m-%d %H:%M:%S") - datetime.datetime.now()
            self.close_remaining = str(temp_date)
    
    @api.multi
    def get_publish(self):
        '''Тендер нийтлэх'''
        if self.is_publish:
            return 'published'
        else:
            return 'unpublish'
    
    @api.multi
    def website_publish_button(self):
        '''Тендер нийтлэх'''
        for order in self:
            if order.is_publish == True:
                raise UserError(_(u'.:Нийтлэгдсэн байна:.'))
            
            if order.is_publish == False:
                raise UserError(_(u'.:Нийтлэгдээгүй байна:.'))

    """Тендерийн хүсэгч этгээдийн удирдлага тендер зарлах салбар сонгож баталгаажуулах"""
    
    @api.multi
    def action_allowed(self):
        for order in self:
            if not order.is_old:
                if not order.tender_line_ids and not order.tender_labor_ids:
                    raise UserError(_(u'Шаардлагатай барааг оруулна уу!'))
                else:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': u'Тендер зарлах салбар',
                        'res_model': 'choose.department',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target' : 'new',
                    }
            else:
                if not order.tender_line_ids:
                    raise UserError(_(u'Шаардлагатай барааг оруулна уу!'))
                else:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': u'Тендер зарлах салбар',
                        'res_model': 'choose.department',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target' : 'new',
                    }
            
        
    @api.multi
    def action_reject(self):
        """Тендерийн хүсэгч салбарын эрхлэгчийн удирдлага татгалзах"""
        #mod_obj = self.env['ir.model.data']
        res = self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_tender_note')
        
        for order in self:
            if not order.requirement_partner_ids:
                raise UserError(_(u'Шаардлага хангасан харилцагч сонгоно уу!'))
            if not order.is_old:
                if not order.tender_line_ids and not order.tender_labor_ids:
                    raise UserError(_(u'Шаардлагатай барааг оруулна уу!'))
                else:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': u'Тайлбар',
                        'res_model': 'tender.tender.note',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target' : 'new',
                    }
            else:
                if not order.tender_line_ids:
                    raise UserError(_(u'Шаардлагатай барааг оруулна уу!'))
                else:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': u'Тайлбар',
                        'res_model': 'tender.tender.note',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target' : 'new',
                    }
                
        notif_groups = self.env['ir.model.data'].get_object_reference('nomin_base', 'group_holding_ceo')
        group_user_ids = []
        
        sel_user_ids = self.env['res.users'].search([('groups_id','in',[notif_groups[1]])])
        group_user_ids = self.env['res.users'].search([('id','in',sel_user_ids)])
        if group_user_ids:
            users = self.env['res.users'].browse(group_user_ids)
            for user in users:
                self.add_follower(user.id)
        
        
        
        #self.write(cr, uid, ids, {'state':'reject'},context=context)
    
    @api.multi
    def action_disabled(self):
        """Тендерийн хүсэгч салбарын эрхлэгчийн удирдлага татгалзах"""
        #mod_obj = self.env['ir.model.data']
        res = self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_tender_note')
        
        for order in self:
            if not order.requirement_partner_ids:
                raise UserError(_(u'Шаардлага хангасан харилцагч сонгоно уу!'))
            if not order.is_old:
            
                if not order.tender_line_ids and not order.tender_labor_ids:
                    raise UserError(_(u'Шаардлагатай барааг оруулна уу!'))
                else:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': u'Тайлбар',
                        'res_model': 'tender.disabled',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target' : 'new',
                    }
            else:
                if not order.tender_line_ids:
                    raise UserError(_(u'Шаардлагатай барааг оруулна уу!'))
                else:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': u'Тайлбар',
                        'res_model': 'tender.disabled',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target' : 'new',
                    }


    @api.multi    
    def action_draft_purchase(self):
        """Холдингийн гүйцэтгэх захирал зөвшөөрч худалдан авалтын үнийн санал үүсгэх"""
        purchase_obj = self.env['purchase.order']
        purchase_line_obj = self.env['purchase.order.line']
        tender_obj = self
        values = {}
        for order in self:
            if not order.is_old:
                if not order.tender_line_ids and not order.tender_labor_ids:
                    raise UserError(_(u'Шаардлагатай барааг оруулна уу!'))
            else:
                if not order.tender_line_ids:
                    raise UserError(_(u'Шаардлагатай барааг оруулна уу!'))
            
            if not order.requirement_partner_ids:
                raise UserError(_(u'Урилга хүлээн авах харилцагчид хоосон байна !'))
            
            for line in order.requirement_partner_ids:
                values = {
                          'tender_id':order.id,
#                           'department_id':order.department_id.id,
                          'partner_id':line.id,
                          'date_planned':order.ordering_date,
                          'requisition_id':order.requisition_id.id,
                          'user_id':self.env.user.id
                          }
                order_id = purchase_obj.create(values)
                for product in order.tender_line_ids:
                    vals = {
                            'order_id':order_id.id,
                            'product_id':product.product_id.id,
                            'product_qty':product.product_qty,
                            'name':product.product_id.name,
                            'date_planned':order.ordering_date,
                            'price_unit':0.0,
                            'product_uom':product.product_uom_id.id,
                            } 
                    purchase_line_obj.create(vals)
        self.write({ 'state': 'open_purchase'})
        # self.send_notification('open_purchase')
        self.send_mail_purchase_employees(order_id.id)
    
    @api.multi
    def action_purchase_order(self):
        """Холдингийн гүйцэтгэх захирал зөвшөөрч Худалдан авалт болгох"""
        for order in self:
            if not order.is_old:
                if not order.tender_line_ids and not order.tender_labor_ids:
                    raise UserError(_(u'Шаардлагатай барааг оруулна уу!'))
            else:
                if not order.tender_line_ids:
                    raise UserError(_(u'Шаардлагатай барааг оруулна уу!'))
            if not order.participants_ids:
                return {
                        'type': 'ir.actions.act_window',
                        'name': u'Худалдан авалтын захиалга',
                        'res_model': 'purchase.tender.wizard',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target' : 'new',
                        }
            
            else:
                return {
                        'type': 'ir.actions.act_window',
                        'name': u'Тайлбар',
                        'res_model': 'tender.tender.note',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target' : 'new',
                        }
        
    @api.multi
    def action_to_tender(self):
        """Холдингийн гүйцэтгэх захирал цуцалж Тендер болгох"""
        tender_obj = self
        for order in tender_obj:
            self.write({'state': 'allowed'})
            
    @api.multi
    def action_open(self):
        """Тендерийн зарлах салбарын эрхлэгч тендер хүсэлт 
           батлах ажилчидыг сонгож нээлттэй төлөвт оруулах
        """
        tender_obj = self
        tender_document_obj = self.env['tender.work.task']
        for order in tender_obj:
            if not order.confirmed_member_ids:
                raise UserError(_(u'Тендерийн хүсэлтийг батлах ажилчид сонгогдоогүй байна'))
            if not order.work_task_id:
                raise UserError(_(u'Ажлын даалгавар сонгогдоогүй байна.'))
            else:
                for document in order.work_task_id.work_document:
                    doc_ids = tender_document_obj.search([('tender_id','=', order.id),('tender_work_document_id','=', document.id)])
                    if not doc_ids:
                        tender_document_obj.sudo().create({ 'tender_id' : order.id,
                                                     'tender_work_document_id' : document.id })
                for document1 in order.work_graph_id.work_document:
                    doc_ids1 = tender_document_obj.search([('tender_id','=', order.id),('tender_work_document_id','=', document1.id)])
                    if not doc_ids1:
                        tender_document_obj.sudo().create({ 'tender_id' : order.id,
                                                     'tender_work_document_id' : document1.id })
            
            if order.is_created_from_budget == False and order.control_budget_id:
                order.create_tender_with_control_budget(order.control_budget_id,order.id)
            if order.confirmed_member_ids:
                for line in order.confirmed_member_ids:
                    if line.state != 'draft':
                        raise UserError(_(u'Тендерийн хүсэлт батлах ажилчдыг шинээр тохируулж өгнө үү !'))
                    else:
                        self.write({'state': 'open'})
        self.send_notification('open')
   
    @api.multi
    def action_draft(self):
        """Тендер зарлах салбарын эрхлэгч тендерийн 
            хүсэлтийг буцааж ноорог болгох
        """
        # self.write({'date_open_deadline':time.strftime('%Y-%m-%d %H:%M:%S'),'date_end':time.strftime('%Y-%m-%d %H:%M:%S')})
        #mod_obj = self.pool.get('ir.model.data')
        res = self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_tender_note')
        
        return {
            'type': 'ir.actions.act_window',
            'name': u'Тайлбар',
            'res_model': 'tender.tender.note',
            'view_type': 'form',
            'view_mode': 'form',
            'target' : 'new',
        }
        
    @api.multi
    def action_confirmed(self):
        """Тендерийн хүсэлт батлах удирдлагууд батлах"""
        tender_line_obj = self.env['tender.employee.line']
        emp_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        for tender in self:
            for line_id in tender.confirmed_member_ids:
                if line_id.employee_id.id == emp_id.id:
                    tender_line_obj.browse(line_id.id).write({
                                                                'state': 'approved',
                                                                'confirmed_date': time.strftime('%Y-%m-%d %H:%M:%S')
                                                                })
                    line_res = tender_line_obj.search([('tender_id','=',tender.id),('state','in',['draft','cancel'])])
                    if not line_res:
                        tender.write({'state':'confirmed'})
                        self.send_notification('confirmed')
                        
        #model_obj = openerp.pooler.get_pool(cr.dbname).get('ir.model.data')
        # notif_groups = self.env['ir.model.data'].get_object_reference('nomin_tender', 'group_tender_secretary')
        # group_user_ids = []
        # sel_user_ids = []
        # sel_user_obj = self.env['res.users'].search([('groups_id','in',[notif_groups[1]])])
        # for line in sel_user_obj:
        #     sel_user_ids.append(line.id)
        # if sel_user_ids:
        #     group_user_obj = self.env['res.users'].search([('id','in',sel_user_ids)])
        # for line in group_user_obj:
        #     group_user_ids.append(line.id)
        # if group_user_ids:
        #     users = self.env['res.users'].browse(group_user_ids)
        #     for user in users:
        #         tender._add_followers(user.id)
        
        
    @api.multi
    def action_cancel(self):
        """Тендерийн хүсэлт батлах удирдлагууд цуцлах"""
        #mod_obj = self.pool.get('ir.model.data')
        res = self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_tender_note')
        
        return {
            'type': 'ir.actions.act_window',
            'name': u'Тайлбар',
            'res_model': 'tender.tender.note',
            'view_type': 'form',
            'view_mode': 'form',
            'target' : 'new',
        }
                                
        self.send_notification('bids')
    
    @api.multi
    def action_to_bids(self):
        """Тендерийн зарлах салбарын эрхлэгч тендер 
            хүсэлтийг нээлттэйгээс буцааж өмнөх төлөвт оруулна
        """
        tender_obj = self
        emps=''
        emp_line=[]
        emp_id =self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        for order in tender_obj:
            if not order.respondent_employee_id:
                raise UserError(_('Please is not this tender requist to back employee.'))
            
            if order.confirmed_member_ids:
                for line in order.confirmed_member_ids:
                    if line.state == 'approved':
                        emps=line.employee_id.name
                        emp_line.append(emps)
                        employees = ' ; '.join(emp_line)

                if emp_line:
                    raise UserError(_(u'Тендерийн хүсэлтийг батлах явцад буцаах боломжгүй ! Дараах хүмүүс зөвшөөрсөн байна. %s' %(employees)))
               
                line_id=self.env['tender.employee.line'].search([('tender_id','=',order.id),('state','!=','draft')])    
                if not line_id:
                    if emp_id[0] == order.respondent_employee_id.id:
                        self.write({'state': 'bids'})

    @api.multi
    def create_contract(self):
        '''Шалгаруулалт хийж дууссан тендерээс гэрээ үүсгэх'''
        #history = self.env['tender.partner.history']
        partner_ids = []
        part_child_ids = ''
        values = {}
        if self.rate_partner_ids:
            # raise UserError(_(u'Тендерт оролцогчийн үнэлгээний мэдээлэл хоосон байна !'))
        
            for rate in self.rate_partner_ids:
                self.env['tender.partner.history'].create({
                                         'tender_id':rate.tender_id.id,
                                         'partner_id':rate.partner_id.id,
                                         'is_selected': rate.is_win,
                                         'note':rate.reason,
                                         'date':time.strftime('%Y-%m-%d %H:%M:%S'),
                        })
                  
                if rate.is_win == True:
                    
                    partner_ids.append(rate.partner_id.id)
                    part_child_ids = tuple(partner_ids)
                    length = len(partner_ids)
                                         
            if not part_child_ids:
                raise UserError(_(u'Шалгарсан оролцогч байхгүй байна!'))
            
            if length > 1:
                raise UserError(_(u'Алдаа. Олон харилцагч гэрээ байгуулах боломжгүй!'))
            
            else:
                values.update({
                               'tender_id': self.id,
                               'customer_company':part_child_ids,
                               'agreed_currency':0.0,
                               'description':self.name,
                               'guarantee_period':self.is_warranty,
                               'guarantee_by_month':self.warranty
                               })
            contract_id = self.env['contract.management'].create(values)
            self.write({'contract_id':contract_id.id})
        elif self.requirement_partner_ids:
                partner = False
                for part in self.requirement_partner_ids:
                    partner = part.id
                values.update({
                               'tender_id': self.id,
                               'customer_company':partner,
                               'agreed_currency':0.0,
                               'description':self.name,
                               'guarantee_period':self.is_warranty,
                               'guarantee_by_month':self.warranty
                               })
                
                contract_id = self.env['contract.management'].create(values)
                self.write({'contract_id':contract_id.id})
    
    def create_tender_with_control_budget(self,control_budget_id,tender_id):
        '''Тендер дээр хяналтын төсөв сонгосон үед хяналтын 
            төсвийн зардлуудыг нийтээр тендер зарлана
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
        
        if total_amount > 0:
            m_vals = {
                'budget_id'     :control_budget_id.id,
                'tender'        :tender_id,
                'date'          :time.strftime('%Y-%m-%d %H:%M:%S'),
                'price'         :material_amount,
                'map'           :'tender',
                'state'         :'tender'
                }
            utilization_budget_material = utilization_budget_material.create(m_vals)
        
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
    
    @api.multi
    def unlink(self):
        for main in self:
            if main.state != 'draft':
                raise UserError(_(u'Та зөвхөн ноорог тендерийг устгах боломжтой.'))
            # if main.requisition_id:
            #     raise UserError(_(u'Шаардахаас үүссэн ноорог тендер устгах боломжгүй.'))
            # if main.control_budget_id and is_created_from_budget == True:
            #     raise UserError(_(u'Хяналтын төсвөөс үүссэн тендер устгах боломжгүй.'))
            if main.control_budget_id:
                if main.control_budget_id.utilization_budget_material:
                    is_material = False
                    for mat in main.control_budget_id.utilization_budget_material:
                        if mat.tender.id == main.id:
                            is_material=True
                            mat.unlink()
                    if is_material:
                        for tline in main.tender_line_ids:
                            for mline in main.control_budget_id.material_line_ids:
                                if tline.product_id.id ==mline.product_id.id and tline.product_qty==mline.product_uom_qty:
                                    mline.write({'state':'confirm'})
                    is_service = False
                    for mat in main.control_budget_id.utilization_budget_labor:
                        if mat.tender.id == main.id:
                            is_service=True
                            mat.unlink()
                    if is_service:
                        if main.is_old:
                            for tline in main.tender_line_ids:
                                for mline in main.control_budget_id.labor_line_ids:
                                    if tline.product_id.id ==mline.product_id.id and tline.product_qty==mline.product_uom_qty:
                                        mline.write({'state':'confirm'})
                        else:
                            for tline in main.tender_labor_ids:
                                for mline in main.control_budget_id.labor_line_ids1:
                                    if tline.product_name ==mline.product_name and tline.product_qty==mline.product_uom_qty:
                                        mline.write({'state':'confirm'})

                    query="Delete from utilization_budget_material where budget_id=%s and tender=%s"%(main.control_budget_id.id ,main.id)
                    self.env.cr.execute(query)
                    query="Delete from utilization_budget_labor where budget_id=%s and tender=%s"%(main.control_budget_id.id ,main.id)
                    self.env.cr.execute(query)
                    query="Delete from utilization_budget_equipment where budget_id=%s and tender=%s"%(main.control_budget_id.id ,main.id)
                    self.env.cr.execute(query)
                    query="Delete from utilization_budget_carriage where budget_id=%s and tender=%s"%(main.control_budget_id.id ,main.id)
                    self.env.cr.execute(query)
                    query="Delete from utilization_budget_postage where budget_id=%s and tender=%s"%(main.control_budget_id.id ,main.id)
                    self.env.cr.execute(query)
                    query="Delete from utilization_budget_other where budget_id=%s and tender=%s"%(main.control_budget_id.id ,main.id)
                    self.env.cr.execute(query)



                
        return super(tender_tender, self).unlink()

class contract_management(models.Model):
    ''' Тендерээс үүссэн гэрээ
    '''
    _inherit = 'contract.management'
    
    tender_id               = fields.Many2one('tender.tender', string='Tender')
class mail_sent_partner(models.Model):
    _name = 'mail.sent.partners'
    '''Урилга имэйл хүлээн авсан харилцагчид
    '''
    tender_id = fields.Many2one('tender.tender',string='Tender')
    partner_id = fields.Many2one('res.partner',string='Partner')
    is_mail_sent = fields.Boolean(string='Is mail sent', default=False)
    
    @api.multi
    def sent_tender_invitation(self):
        '''Урилга имэйл сонгогдсон харилцагч нарт илгээнэ
        '''
        
        template_id = self.env['ir.model.data'].get_object_reference('nomin_tender', 'tender_tender_invitation_email_template')[1]        
        invitation_obj = self.env['tender.invitation.guide'].browse(self.tender_id.invitation_id.id)

        published_date = datetime.datetime.strptime(self.tender_id.published_date, '%Y-%m-%d %H:%M:%S')
        date_end = datetime.datetime.strptime(self.tender_id.date_end, '%Y-%m-%d %H:%M:%S')
        
        data = {
            'subject': u'"Номин Холдинг" ХХК-ийн "%s" тендерийн урилга'%(self.tender_id.desc_name),
            'name': self.tender_id.name,
            'company': self.tender_id.company_id.name,
            'desc_name': self.tender_id.desc_name,
            'publish_date': published_date+timedelta(hours=8),
            'end_date': date_end+timedelta(hours=8),
            'invitation_name': invitation_obj.invitation_info,
            'invitation_detail': invitation_obj.invitation_detail,
            'model': 'tender.tender',
            'base_url': self.env['ir.config_parameter'].get_param('web.base.url'),
            'action_id': self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_list')[1],
            'id': self.tender_id.id,
            'db_name': request.session.db, 
            'sender': self.env['res.users'].browse(self._uid).name,
            'state': u'Нийтлэгдсэн',
            }
        
        part_ids_noti = []
        if self.tender_id.mail_sent_partner_ids:
            for mail in self.tender_id.mail_sent_partner_ids:
                if mail.is_mail_sent == False:
#                     part_ids_noti.append(partner.id)
                    self.env.context = data
                    self.pool['mail.template'].send_mail(self.env.cr, 1, template_id, mail.partner_id.id, force_send=True, context=self.env.context)
                    self.write({'is_mail_sent': True})
            
        return True
        
class tender_partner_history(models.Model):
    _name = 'tender.partner.history'
    _description = "Partner history"
    '''Тендер оролцогчдын оролцсон байдал түүх
    '''
    name                    = fields.Char(string='Name')
    tender_id               = fields.Many2one('tender.tender',string='Tender')
    partner_id              = fields.Many2one('res.partner',string='Partner')
    note                    = fields.Text(string='Note')
    state                   = fields.Selection([('draft', 'Draft'),('reject','Rejected tender requist')], string='Status')
    date                    = fields.Date(string = 'Date')
    is_selected             = fields.Boolean(string='Is Win', track_visibility='onchange')
    
    
class tender_line(models.Model):
    _name = "tender.line"
    _description = "Tender Line"
    _rec_name = 'product_id'
    '''Тендер дээр сонгож байгаа бараанууд
    '''
    product_id = fields.Many2one('product.product', 'Product', domain=[('product_tmpl_id.is_new','=',True),('product_tmpl_id.cost_price','>',0)], ondelete='restrict', index=True)
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure', ondelete='restrict')
    product_name = fields.Char(string = 'Барааны нэр' )
    product_qty = fields.Float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'))
    tender_id = fields.Many2one('tender.tender', 'Call for Tenders', ondelete='cascade', index=True)
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account', ondelete='restrict')
    schedule_date = fields.Date('Scheduled Date')

    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        '''Барааг сонгоход тоо хэмжих нэгж, тоо ширхэг шинэчлэх'''
        product_uom_id = ''
        if self.product_id:
            prod = self.env['product.product'].browse(self.product_id.id)
            self.update({'product_uom_id':  prod.uom_id.id, 'product_qty': 1.0})
        
    
class tender_labor_line(models.Model):
    _name = "tender.labor.line"
    _description = "Tender Labor Line"
    _rec_name = 'product_name'
    '''Тендер дээр сонгож байгаа бараанууд
    '''
    # product_id = fields.Many2one('product.product', 'Product', domain=[('purchase_ok', '=', True)], ondelete='restrict', index=True)
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure', ondelete='restrict')
    product_name = fields.Char(string = 'Names' )
    product_qty = fields.Float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'))
    tender_id = fields.Many2one('tender.tender', 'Call for Tenders', ondelete='cascade', index=True)
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account', ondelete='restrict')
    schedule_date = fields.Date('Scheduled Date')

    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        '''Барааг сонгоход тоо хэмжих нэгж, тоо ширхэг шинэчлэх'''
        product_uom_id = ''
        if self.product_id:
            prod = self.env['product.product'].browse(self.product_id.id)
            self.update({'product_uom_id':  prod.uom_id.id, 'product_qty': 1.0})
            
#     def onchange_product_id(self, cr, uid, ids, product_id, product_uom_id, parent_analytic_account, analytic_account, parent_date, date, context=None):
#         """ Changes UoM and name if product_id changes.
#         @param name: Name of the field
#         @param product_id: Changed product_id
#         @return:  Dictionary of changed values
#         """
#         value = {'product_uom_id': ''}
#         if product_id:
#             prod = self.pool.get('product.product').browse(cr, 1, product_id, context=context)
#             value = {'product_uom_id': prod.uom_id.id, 'product_qty': 1.0}
#         if not analytic_account:
#             value.update({'account_analytic_id': parent_analytic_account})
#         if not date:
#             value.update({'schedule_date': parent_date})
#              
#         return {'value': value}

class product_template(models.Model):
    _inherit = 'product.template'
    
    purchase_tender = fields.Selection(
        [('rfq', 'Create a draft purchase order'),
         ('tenders', 'Propose a call for tenders')],
        string='Procurement',
        help="Check this box to generate Call for Tenders instead of generating "
             "requests for quotation from procurement.")
    
    _defaults = {
        'purchase_tender': 'rfq',
    }

class choose_department(models.TransientModel):
    _name = 'choose.department'
    '''Тендер зарлах ажилтан, салбар хэлтэсийг сонгох
    '''
    department_ids = fields.Many2one('hr.department',string='Respondent department', ondelete='restrict', domain=[('is_sector','=',True)])
    employee_id = fields.Many2one('hr.employee',string='Respondent employee', ondelete='restrict')
    
    @api.onchange('department_ids')
    def onchange_department(self):
        '''Тендер зарлах салбар сонгоход тухайн салбарт
           хамааралтай ажилчид гарна
        '''
        acc_ids = []
        user_obj = self.env['res.users']
        context = self._context
        if self.department_ids:
            ir_model_data = self.env['ir.model.data']
            notif_groups=ir_model_data.get_object_reference('nomin_tender', 'group_tender_branch_manager')
            sel_user_ids = user_obj.sudo().search([('groups_id','in',notif_groups[1])])
            employee_ids = self.env['hr.employee'].sudo().search([('user_id','in',sel_user_ids.ids)])
            return {'domain':{'employee_id':[('id','in',employee_ids.ids),
                                             ('department_id','child_of',self.department_ids.id)]}}
    
    @api.multi
    def action_bids_field(self):
        '''Тендерийг хариуцах салбар, 
           ажилтанг томилно
        '''
        active_id = self.env.context.get('active_id', False) 
        tender = self.env['tender.tender']
        tender_id = tender.search([('id','=',active_id)])
        for order in self:
            tender_id.write({'state': 'bids',
                             'respondent_department_id':order.department_ids.id,
                             'respondent_employee_id':order.employee_id.id})
            tender_id.send_notification('bids')
            
            