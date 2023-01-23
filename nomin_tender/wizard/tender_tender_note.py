# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools.translate import _
import time
import logging
_logger = logging.getLogger(__name__)
from odoo.http import request
from odoo.exceptions import UserError
class tender_cancel_note(models.Model):
    _name = "tender.cancel.note"
    _description = "Tender Cancel Note"
    '''Тендер цуцлах
    '''
    tender_id       = fields.Many2one('tender.tender', 'Tender')
    description     = fields.Text('Note', require=True)
    
    
    def save_cancel_note(self):
        '''Тендерийг цуцлах тайлбарыг бичиж хадгална'''
        context = self._context
        active_id = context and context.get('active_ids', [])
        self.write({'tender_id': active_id[0]})
        for cancel in self:
            tender = self.env['tender.tender'].browse(active_id)
            if tender.state not in ('closed','in_selection'):
                raise UserError(_(u'Алдаа!'))
            else:
                tender.write({'state':'cancelled'})
        for line in self.tender_id.confirmed_member_ids:
                line.write({'state':'draft', 'confirmed_date': time.strftime('%Y-%m-%d %H:%M:%S')})
        valuation_ids = self.env['tender.valuation'].sudo().search([('state','in',['draft','open']),('tender_id','=',self.tender_id.id)])
        for val in valuation_ids:
                    val.write({'state':'draft'})
                    val.unlink()
        # if self.tender_id.participants_ids:
        #     self.send_notif_parners()
        return tender.message_post(body=cancel.description)


class DisabledTender(models.Model):
    _name = "tender.disabled"
    _description = "Tender Disabled"
    '''Тендер хэрэгсэхгүй болгох
    '''
    tender_id       = fields.Many2one('tender.tender', 'Tender')
    description     = fields.Text('Note', require=True)
    
    
    def confirm(self):
        '''Тендерийг хэрэгсэхгүй болгох тайлбарыг бичиж хадгална'''
        context = self._context
        active_id = context and context.get('active_ids', [])
        self.write({'tender_id': active_id[0]})
        for cancel in self:
            tender = self.env['tender.tender'].browse(active_id)
            tender.write({'state':'disabled'})
            tender.message_post(body=cancel.description)
        return True


    
    def send_notif_parners(self):
        
         
        subject = u'Таны оролцсон "%s" дугаар "%s" нэртэй тендер хүчингүй боллоо.'%( self.tender_id.name,self.tender_id.desc_name)
        
        
        body_html = u'''
                        <h4>Сайн байна уу ?, 
                            Таньд энэ өдрийн мэнд хүргье! <br/>
                            Таны оролцсон "%s" дугаар "%s" нэртэй тендер хүчингүй боллоо.</h4>
                            <p><li><b>Тендерийн дугаар: </b>%s</li></p>
                            <p><li><b>Тендерийн нэр: </b>%s</li></p>
                            <p><li><b>Тендерийн ангилал: </b>%s</li></p>
                            <p><li><b>Дэд ангилал: </b>%s</li></p>
                            <p><li><b>Товлосон захиалгын огноо: </b>%s</li></p>
                           
                            </br>                         
                            <p>Энэхүү имэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
                            <p>Баярлалаа..</p>
                    '''%( self.tender_id.name,self.tender_id.desc_name, self.tender_id.name,self.tender_id.desc_name,self.tender_id.type_id.name,
                            self.tender_id.child_type_id.name,self.tender_id.ordering_date)
        
        for user in self.tender_id.participants_ids:
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
                email_template.sudo().send_mail(self.tender_id.id)

class tender_meeting_note(models.Model):
    _name = "tender.meet.note"
    _description = "Tender Meet Note"
    '''Тендерийн хурлыг цуцлах
    '''
    meet_id     = fields.Many2one('tender.meet', 'Tender Meet')
    note        = fields.Text('Note', require=True)
    
    
    def save_note(self):
        '''Тендерийн хурлыг цуцлах тайлбарыг бичиж хадгална'''
        meet_obj = self.env['tender.meeting']
        context = self._context
        active_id = context and context.get('active_ids', [])
        self.write({'meet_id': active_id[0]})
        for order in self:
            meet = meet_obj.browse(active_id)
            
            if meet.state == 'confirmed':
                meet_obj.browse(meet.id).write({'state':'cancel'})
#                 self.send_notif_to_followers(cr, uid, ids, 'reject')
        return meet_obj.message_post(body=order.note)

class tender_tender_note(models.Model):
    _name = "tender.tender.note"
    _description = "Tender Note"
    
    tender_id   = fields.Many2one('tender.tender', 'Tender')
    note        = fields.Text('Note', require=True)
    
    
    def send_notif_to_followers(self,signal):
        '''Имэйл илгээнэ'''
        states = {
                  'draft': u'ноорог',
                  'reject': u'цуцлагдсан',
                  'bids': u'илгээгдсэн',
                  'open':u'нээлттэй',
                  'confirmed': u'батлагдсан',
                  'open_purchase': u'худалдан авалт'
                  }

        mail_obj = self.env['mail.followers']
        template_id = self.env['ir.model.data'].get_object_reference('nomin_tender', 'tender_state_change_followers_email_template')[1]
        active_id = self
        requist_obj = self.env['tender.tender'].browse(active_id.tender_id.id)
        
        follower_ids = mail_obj.search([('res_model','=','tender.tender'),('res_id','=',requist_obj.id)])
        if follower_ids:
            user_ids = []
            followers = []
            for followers_line in follower_ids:
                followers.append(followers_line.id)
            if followers:
                user_ids = self.env['res.users'].search([('partner_id','in',followers)])
            
            data = {
                    'subject': u'"%s" дугаартай "%s" тендер “%s” төлөвт орлоо.'%(requist_obj.name, requist_obj.desc_name, states[signal]),
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
            self.env.context = data
            for user_id in user_ids:
                if user_id != uid:
                    self.pool['mail.template'].send_mail(self.env.cr, 1, template_id, user_id.id, force_send=True, context=self.env.context)
        return True
    
    
    def save(self):
        '''Тендерийг буцаах бүрт тайлбар бичиж хадгална'''
        tender_obj = self.env['tender.tender']
        context = self._context
        delay = context.get('delay',False)
      
        active_id = context and context.get('active_ids', [])
        self.write({'tender_id': active_id[0]})
        for order in self:
            tender = tender_obj.browse(active_id)
            if delay:
                for line in tender.confirmed_member_ids:
                    self.env['tender.employee.line'].browse(line.id).write({'state':'draft', 'confirmed_date': time.strftime('%Y-%m-%d %H:%M:%S')})
                valuation_ids = self.env['tender.valuation'].search([('state','in',['draft','open']),('tender_id','=',tender.id)])
                if valuation_ids:
                    valuation_ids.write({'state':'draft'})
                    valuation_ids.unlink()
                # for val in self.env['tender.valuation'].browse(valuation_ids):
                #     val.write({'state':'draft'})
                # for val in self.env['tender.valuation'].browse(valuation_ids):
                #     val.unlink()
                # tender.send_delay_notif()

                tender_obj.browse(tender.id).write({'state':'delay','is_valuation_created': False,'is_publish':False})
            else:
                if tender.state == 'draft':
                    tender_obj.browse(tender.id).write({'state':'reject'})
                    self.send_notif_to_followers('reject')
                     
                if tender.state == 'bids':
                    tender_obj.browse(tender.id).write({'state':'draft'})
                    self.send_notif_to_followers('draft')
                if tender.state == 'contract_request':
                    tender_obj.browse(tender.id).write({'state':'draft'})
                    self.send_notif_to_followers('draft')
                    
                if tender.state == 'open':
                    for row in tender.confirmed_member_ids:
                        self.env['tender.employee.line'].browse(row.id).write({'state':'draft', 'confirmed_date': time.strftime('%Y-%m-%d %H:%M:%S')})
                    tender_obj.browse(tender.id).write({'state':'bids'})
                    self.send_notif_to_followers('bids')

                if tender.state == 'confirmed':
                    for line in tender.confirmed_member_ids:
                        self.env['tender.employee.line'].browse(line.id).write({'state':'draft', 'confirmed_date': time.strftime('%Y-%m-%d %H:%M:%S')})
                    tender_obj.browse(tender.id).write({'state':'bids'})
                    self.send_notif_to_followers('bids')
                     
                if tender.state == 'send_to_manager':
                    tender_obj.browse(tender.id).write({'state':'confirmed'})
                    self.send_notif_to_followers('confirmed')
                    
                if tender.state == 'closed':
                    
                    purchase_obj = self.env['purchase.order']
                    purchase_line_obj = self.env['purchase.order.line']
                    values = {}
                    for main in tender:
                        for partic in main.participants_ids:
                            values = {
                                      'tender_id':main.id,
                                      'department_id':main.department_id.id,
                                      'partner_id':partic.partner_id.id,
                                      'date_planned':main.ordering_date,
                                      'requisition_id':main.requisition_id.id,
                                      'user_id':uid
                                      }
                            order_id = purchase_obj.create(values)
                            for product in main.tender_line_ids:
                                vals = {
                                        'order_id': order_id,
                                        'product_id': product.product_id.id,
                                        'product_qty': product.product_qty,
                                        'name': product.product_id.name,
                                        'date_planned': main.ordering_date,
                                        'price_unit': 0.0,
                                        'product_uom': product.product_uom_id.id,
                                        } 
                                purchase_line_obj.create(vals)
                    tender_obj.browse(tender.id).write({'state': 'open_purchase'})
                    self.send_notif_to_followers('open_purchase')
                
                    
        return tender_obj.message_post(body=order.note)
class tender_request_note(models.TransientModel):
    _name = "tender.request.note"
    _description = "Tender Note"

    tender_id   = fields.Many2one('tender.tender', 'Tender')
    note        = fields.Text('Note', require=True)


    
    def action_contract_request(self):
        active_id = self._context and self._context.get('active_ids', [])
        
        if active_id:
            self.write({'tender_id':active_id[0]})
            self.tender_id.write({'state':'contract_request'})
            self.tender_id.message_post(body=self.note)
        notif_groups = self.env['ir.model.data'].get_object('nomin_base', 'group_holding_ceo')
        if not self.tender_id.requirement_partner_ids:
            raise UserError(_(u'Шаардлага хангасан харилцагч сонгоно уу!'))
        if len(self.tender_id.requirement_partner_ids)>1 :
            raise UserError(_(u'Шаардлага хангасан 1 харилцагч сонгоно уу!'))
        sel_user_ids = notif_groups.users
        
        # subject = u'"%s" дугаартай "%s" тендер гэрээ үүсгэх хүсэлт илгээсэн байна.'%( self.tender_id.name,self.tender_id.desc_name)
        # db_name = request.session.db
        # base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        # action_id = self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_list')[1]
        # if sel_user_ids:
        #     self.write({'state':'contract_request'})
        # else:
        #     raise
        # body_html = u'''
        #                 <h4>Сайн байна уу ?, 
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
        #                     <p>Баярлалаа..</p>
        #             '''%( self.tender_id.name,self.tender_id.desc_name, self.tender_id.name,self.tender_id.desc_name,self.tender_id.type_id.name,
        #                     self.tender_id.child_type_id.name,self.tender_id.ordering_date,self.tender_id.state, self.tender_id.name,
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
        #         email_template.sudo().send_mail(self.tender_id.id)