# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import time
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.http import request

class TenderParticipantsBid(models.Model):
    _name="tender.participants.bid"
    _description = "Tender participants bid"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    '''Тендерт оролцогчид'''
    
    
    def _partic_name(self):
        for order in self:
            order.name = order.tender_id.name + '/' + order.partner_id.name
    
    
    @api.depends('task_ids.line_total_amount')
    def _compute_amount(self):
        self.amount_total = sum(line.line_total_amount for line in self.task_ids)
        
    name                        = fields.Char('Name', tracking=True, copy=False, compute='_partic_name')
    tender_id                   = fields.Many2one('tender.tender', 'Current tender', ondelete='restrict', tracking=True, index=True)
    partner_id                  = fields.Many2one('res.partner', 'Current partner', ondelete='restrict', tracking=True)
    document_id                 = fields.Many2one('res.partner.documents', 'Partner documents', ondelete='restrict')
    t_partner_cost_id           = fields.Many2one('ir.attachment', domain="[('res_model','=','tender.participants.bid'),('res_id', '=', id)]", string='Partner cost file') #Үнийн санал
    t_partner_schedule_id       = fields.Many2one('ir.attachment', domain="[('res_model','=','tender.participants.bid'),('res_id', '=', id)]", string='Partner schedule file') #Хугацаа, ажлын график
    t_partner_control_budget_id = fields.Many2one('ir.attachment', domain="[('res_model','=','tender.participants.bid'),('res_id', '=', id)]", string='Хяналтын төсөв') #Хугацаа, ажлын график
    t_partner_proxy_id          = fields.Many2one('ir.attachment', string='Partner proxy file') #Харилцагчийн итгэмжлэл
    t_partner_license_id        = fields.Many2one('ir.attachment', string='Partner license file') #Тусгай зөвшөөрөл
    t_partner_require_id        = fields.Many2one('ir.attachment', string='Partner require file') #Тусгай шаардлага
    t_partner_worklist_id       = fields.Many2one('ir.attachment', string='Partner worklist file') #Ажлын туршлага
    t_partner_alternative_id    = fields.Many2one('ir.attachment', string='Partner alternative tender file') #Хувилбарт тендер
    t_partner_technical_id      = fields.Many2one('ir.attachment', string='Partner technical file') #Техникийн боломж
    task_ids                    = fields.One2many('participants.work.task.line', 'task_id', 'Work unit task', ondelete='restrict')
    amount_total                = fields.Float(string='Total', compute='_compute_amount', tracking=True)
    description                 = fields.Text('Description', tracking=True)
    datetime                    = fields.Date('Date', tracking=True)
    execute_time                = fields.Char('Execute Datetime', tracking=True) #гүйцэтгэх хугацаа
    warranty_time               = fields.Char('Warranty Datetime', tracking=True) #Баталгаат хугацаа
    state                       = fields.Selection([('draft', 'Draft'),('sent', u'Илгээсэн'),('open_document', u'Бичиг баримт нээлттэй'),('open_cost', u'Үнийн санал нээлттэй'),('close', u'Хаасан')]
                                                   ,string= "Status",tracking=True)
    
    _defaults = {
                    'state'     : 'draft',
                    'datetime'  : time.strftime('%Y-%m-%d')
                }
    
    @api.onchange('partner_id')
    def onchange_partner(self):
        '''Тендерт оролцогчийг сонгоход тухайн 
           харилцагчийн бичиг баримтыг шинэчилнэ.
        '''
        doc_ids = []
        res_doc = self.env['res.partner.documents']
        context = self._context
        if self.partner_id:
            partner = [self.partner_id.id]
            doc_ids = self.env['res.partner.documents'].search([('partner_id','=',self.partner_id.id)])
            if doc_ids:
                for doc in doc_ids:
                    if doc.state == 'complete':
                        self.update({'document_id':doc.id})
                    else:
                        self.update({'document_id': False})
                        
            return {'domain':{'document_id':[('id','=',doc_ids.ids),
                                         ('state','=','complete')]}}
    
    
    def send_bidding(self):
        '''Тендерт оролцох хүсэлт илгээх'''
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        action_id = self.env['ir.model.data'].get_object_reference('nomin_tender', 'tender_partner_bid_action')[1]
        db_name = request.session.db
        groups = []
        notif_groups = self.env['ir.model.data'].get_object('nomin_tender', 'group_tender_manager')
        groups.append(notif_groups.id)
        notif_groups = self.env['ir.model.data'].get_object('nomin_tender', 'group_tender_secretary')
        groups.append(notif_groups.id)
        
        sel_user_ids = []
        sel_user_ids = self.env['res.users'].search([('groups_id','in',groups)])
        state = u'Тендерийн хүсэлт'
        if self.tender_id.state == 'published':
            state =  u'Нийтлэгдсэн'
        if self.tender_id.state == 'bid_expire':
            state =  u'Бичиг баримт хүлээн авч дууссан'
        if self.tender_id.state == 'closed':
            state =  u'Бичиг баримт хүлээн авч дууссан'
        if self.tender_id.state == 'in_selection':
            state =  u'Сонгон шалгаруулалт'
        if self.tender_id.state == 'finished':
            state =  u'Дууссан'
        if self.tender_id.state == 'cancelled':
            state =  u'Хүчингүй болсон'
        
        subject = u'"%s" дугаартай "%s" тендерт оролцогч нэмэгдлээ.'%( self.tender_id.name,self.tender_id.desc_name)
        body_html = u'''
                        <h4>Сайн байна уу ?, 
                            Таньд энэ өдрийн мэнд хүргье! <br/>
                            "%s" дугаартай "%s" тендерт оролцогч нэмэгдсэн байна.</h4>
                            <p><li><b>Тендерийн дугаар: </b>%s</li></p>
                            <p><li><b>Тендерийн нэр: </b>%s</li></p>
                            <p><li><b>Тендерийн ангилал: </b>%s</li></p>
                            <p><li><b>Дэд ангилал: </b>%s</li></p>
                            <p><li><b>Товлосон захиалгын огноо: </b>%s</li></p>
                            <p><li><b>Төлөв: </b>%s</li></p>
                            <p><li><b>Оролцогч: </b>%s</li></p>
                            </br>
                            <p>"%s" - н мэдээллийг <b><a href=%s/web?db=%s#id=%s&view_type=form&model=tender.participants.bid&action=%s>Тендер/Тендерийн үнэлгээ/Тендерт оролцогчид</a></b> цонхоор дамжин харна уу.</p>
                            <p>--</p>
                            <p>Энэхүү мэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
                            <p>Баярлалаа..</p>
                    '''%( self.tender_id.name,self.tender_id.desc_name, self.tender_id.name,self.tender_id.desc_name,self.tender_id.type_id.name,
                            self.tender_id.child_type_id.name,self.tender_id.ordering_date,state,self.partner_id.name, self.name,
                            base_url,
                            db_name,
                            self.id,
                            action_id)
        
        for user in sel_user_ids:
            email = user.login
            if email or email.strip():
                email_template = self.env['mail.template'].create({
                        'name': _('Followup '),
                        'email_from': self.env.user.company_id.email or '',
                        'model_id': self.env['ir.model'].search([('model', '=', 'tender.participants.bid')]).id,
                        'subject': subject,
                        'email_to': email,
                        'lang': self.env.user.lang,
                        'auto_delete': True,
                        'body_html':body_html,
                        #  'attachment_ids': [(6, 0, [attachment.id])],
                        })
                email_template.sudo().send_mail(self.id)
    
    def action_send(self):
        '''Тендерт оролцогчийн үнийн санал, бичиг баримтыг илгээх.'''
        for order in self:
            if order.tender_id.state != 'published': 
                raise UserError(_(u'Бичиг баримт хүлээн авах боломжгүй байна.'))
            order.write({'state': 'sent'})
            order.send_bidding()
    
    
    def unlink(self):
        '''Нооргоос бусад үед устгах боломжгүй'''
        for bid in self:
            if bid.state != 'draft':
                raise UserError(_(u'Та ноорог үнийн саналыг устгах боломжтой.'))
        return super(TenderParticipantsBid, self).unlink()

    
class ParticipantsWorkTaskLine(models.Model):
    _name = "participants.work.task.line"
    _description = "Tender participants line"
    
    _inherit = ['mail.thread', 'mail.activity.mixin']
    '''Тендерт орлцогчийн үнийн саналын мөр'''
    @api.model
    def _default_tender(self):
        '''Оролцогчийн мөр дээр тендер талбарт тухайн 
           форм дээр сонгогдсон тендерийн мэдээлэл авна
        '''
        tender_id = []
        context = self._context
        if 'tender_id' in context:
            tender_id = context.get('tender_id')
        return tender_id
    
    @api.model
    def _default_partner(self):
        '''Оролцогчийн мөр дээр оролцогч талбарт тухайн 
           форм дээр сонгогдсон харилцагчийн мэдээлэл авна
        '''
        partner_id = []
        context = self._context
        if 'partner_id' in context:
            partner_id = context.get('partner_id')
        return partner_id
    
    
    @api.depends('unit_price', 'qty')
    def _compute_amount(self):
        '''Мөрийн тоо ширхэг, нэгж үнэ 2н үржвэр дүнг гаргана'''
        self.amount = self.unit_price*self.qty
        
    
    def _compute_total_amount(self):
        '''Мөрийн нийт дүнг гаргана'''
        self.line_total_amount = self.amount + self.costs_of_materials + self.other_costs
    
    name                        = fields.Char(string='Work name')
    tender_id                   = fields.Many2one('tender.tender', 'Current tender', default=_default_tender)
    partner_id                  = fields.Many2one('res.partner', 'Current partner', default=_default_partner)
    qty                         = fields.Float(string='Qty', digits=(16, 4), default=1) #Тоо ширхэг
    unit_price                  = fields.Float(string='Unit Price') #Нэгж үнэ
    amount                      = fields.Float(string='Amount', tracking=True,compute='_compute_amount', readonly=True,) #Нийт үнэ
    costs_of_materials          = fields.Float(string="Costs of materials")#МАтериалын үнэ
    other_costs                 = fields.Float(string="Other costs") #Бусад өртөг
    line_total_amount           = fields.Float(string="Total amount", tracking=True, compute="_compute_total_amount", readonly=True) #Тухайн ажлын даалгаврын нийт зардал
    task_id                     = fields.Many2one('tender.participants.bid', 'Participants works', ondelete='cascade')

   
        