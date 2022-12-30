# -*- coding: utf-8 -*-
##############################################################################
#
#    Asterisk Technologies LLC, Enterprise Management Solution    
#    Copyright (C) 2013-2014 Asterisk Technologies LLC Co.,ltd (<http://www.erp.mn>). All Rights Reserved
#    Email : unuruu25@gmail.com
#    Phone : 976 + 88005462
#
##############################################################################

from openerp import api, fields, models, SUPERUSER_ID, _
from openerp.tools.translate import _
from openerp.osv.orm import setup_modifiers
from lxml import etree
import time
import openerp.pooler
from openerp.exceptions import UserError, ValidationError
import datetime, time
from datetime import date, datetime, timedelta
from openerp.http import request
    
class tender_protocol(models.Model):
    _name="tender.protocol"
    _description = "Tender meeting protocol"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    '''Тендерийн протокол
    '''
    name                = fields.Char('Tender Protocol',track_visibility='onchange')
    tender_id           = fields.Many2one('tender.tender', string="Current Tender", track_visibility='onchange',ondelete='restrict', index=True)
    meeting_id          = fields.Many2one('tender.meeting', string ="Meeting of tender", track_visibility='onchange', ondelete='restrict')
    member_ids          = fields.Many2many("hr.employee", string ="Member", store=True, track_visibility='onchange')
    committee_member_ids= fields.One2many(related="tender_id.committee_member_ids", string='Committee Members', track_visibility='always')
#     comment             = fields.Text(string= "Comment",track_visibility='onchange')
    meet_protocol       = fields.Html(string= "Comment",track_visibility='onchange')
    user_id             = fields.Many2one('res.users', string ='User',default=lambda self: self.env.user, readonly=True,track_visibility='onchange')
    state               = fields.Selection([('draft', 'Draft'), ('open', 'Open'), ('sent',u'Илгээгдсэн'),('done', 'Done')], string ='Status', track_visibility='onchange', default="draft")
    employee_comments   = fields.Text(string ="Members Comments")
    employee_html_comments       = fields.Html(string= "Members Comments",track_visibility='onchange')
        
    @api.onchange('meeting_id')
    def onchange_type(self):
        '''Тендерийн хурал сонгоход тендерийн тендер талбарыг шинэчилнэ'''
        self.update({'tender_id':False})
        child_ids = []
        if self.meeting_id:
            meet_ids = self.env['tender.meeting'].sudo().search([('id','=',self.meeting_id.id)])
            if meet_ids:
#                 child_ids.append(meet_ids.tender_id.id)
                self.update({'tender_id':meet_ids.tender_id.id})
#         return {'domain':{'tender_id': [('id','=', child_ids)]}}
        
    @api.multi
    def save(self):
        '''Протоколыг нээлттэй төлөвт оруулна'''
        context = self._context
        active_id = context and context.get('active_id', False) or False
        self.write({
                    'state': 'open',
                   'tender_id': active_id,
                   })
    
    @api.multi
    def action_to_open(self):
        '''Протоколыг нээлттэй төлөвт оруулна'''
        for order in self:
            protocol = self.env['tender.protocol'].search([('meeting_id','=',order.meeting_id.id)])
            for line in protocol:
                if line.state != 'draft':
                    raise UserError(_(u'Дахин батлах боломжгүй.'))
            order.write({'state': 'open'})

    def _add_followers(self,user_ids):
        '''Дагагч нэмнэ'''
        self.message_subscribe_users(user_ids=user_ids)
        

    #---------------------------------------------------------------- @api.multi
    #------------------------------------------------- def protocol_notif(self):
        #------- self.env.cr.execute("select A.id as id from tender_protocol A \
        # inner join tender_meeting B ON A.meeting_id=B.id where A.state='sent' and B.state='done'")
        #---------------------------------------------------- #cr.execute(query)
        #---------------------------------- records = self.env.cr.dictfetchall()
        #----------------------------------------------------------- if records:
            #-------------------------------------------- for record in records:
                # self.env['tender.protocol'].browse([record['id']]).send_protocol_notif()
       
    def protocol_notif(self,cr,uid):
        query = "select A.id as id from tender_protocol A \
        inner join tender_meeting B ON A.meeting_id=B.id where A.state='sent' and B.state='done'"
        cr.execute(query)
        
        records = cr.dictfetchall()
        if records:
            for record in records:
                self.pool.get('tender.protocol').browse(cr,1,[record['id']]).send_protocol_notif()


    @api.multi
    def send_protocol_notif(self):
        '''Имэйл илгээнэ'''
        states = {
                  'done': u'Дууссан',
                  }
        
        emp = ''
        emp_name=[]
        members=''
        protocol_obj=self
        read_states={'unread':u'Танилцаагүй','read':u'Танилцсан'}
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        action_id = self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_protocol_menu')[1],
        body=""
        for employee in protocol_obj.committee_member_ids:
            body=body+"""<tr class="">
                        <td style="width:150px" class="oe_list_field_cell oe_list_field_many2one">%s</td>
                        <td style="width:150px"   class="oe_list_field_cell oe_list_field_float  oe_readonly ">%s</td>
                        <td class="oe_list_field_cell oe_list_field_float   oe_readonly ">%s</td>
                        </tr>"""%(employee.employee_id.last_name +' '+ employee.employee_id.name, employee.employee_id.job_id.name, str(read_states[employee.read_state]))
        html_text="""<table class="oe_list_content table table-bordered">
                    <thead>
                    <tr class="oe_list_header_columns">
                        <th style="width:150px" class="oe_list_header_many2one oe_sortable">
                            <div>Комиссын гишүүн<span>&nbsp;</span></div>
                        </th>
                        <th style="width:150px" class="oe_list_header_float oe_sortable">
                            <div>Албан тушаал<span>&nbsp;</span></div>
                        </th>
                        <th style="width:70px"class="oe_list_header_float oe_sortable">
                            <div>Төлөв<span>&nbsp;</span></div>
                        </th>
                    </tr>
                    </thead>
                    <tbody>%s</tbody>
                    </table>"""%body
        body_html="""
        <p>
            Сайн байна уу? </br>
            </p>
            <p>
            Таньд <b>%s</b> -н хурлын протоколыг илгээж байна. Тендерийн журмын дагуу хурлын протоколтой танилцана уу.
            </p>
            <ul>
                <li>Хурлын нэр: %s <b></b></li>
                <li>Тендерийн нэр: %s <b></b></li>
                <li>Комиссын гишүүд: 
                    <b>%s</b>
                </li>

            </ul>
            <p>
                Та системийн дараах цэснээс энэхүү баримтыг олох боломжтой.
               
            </p>
            <ul>
                <li><b>%s</b></li>
            </ul>

            <p>
                Та <a href="%s/web?db=%s#id=%s&view_type=form&model=tender.protocol&action=%s"><b>%s</b>
                </a> линкээр дамжин орж дэлгэрэнгүй танилцах боломжтой.
            </p>
            <p>
                Баярлалаа,
            </p>

            <pre>
            -- 
            Odoo ERP Автомат Имэйл

            </pre>
        """%(protocol_obj.tender_id.name,
            protocol_obj.meeting_id.name,
            protocol_obj.tender_id.desc_name,
            html_text,
            u'Тендер / Тендер / Тендерийн протокол',
            base_url,
            self.env.cr.dbname,
            self.id,
            action_id[0],
            protocol_obj.meeting_id.name)
        
            
        user_ids= []
        for member in protocol_obj.committee_member_ids:
            if member.read_state!='read':
                user_ids.append(member.employee_id.user_id)
        # template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'nomin_tender', 'tender_meeting_protocol_email_template')[1]
        
        # model_obj = openerp.pooler.get_pool(cr.dbname).get('ir.model.data')
        # data = {
        #         'subject': u'Хурлын протокол',
        #         'tender': protocol_obj.tender_id.name,
        #         'meet_name': protocol_obj.meeting_id.name,
        #         'tender_name': protocol_obj.tender_id.desc_name,
        #         # 'comment': protocol_obj.meet_protocol,
        #         'state': protocol_obj.state,
        #         'member_ids': html_text,
        #         'model': 'tender.protocol',
        #         'base_url': self.pool.get('ir.config_parameter').get_param(cr, uid, 'web.base.url'),
        #         'action_id': self.pool.get('ir.model.data').get_object_reference(cr, uid, 'nomin_tender', 'action_tender_protocol_menu')[1],
        #         'id': protocol_obj[0].id,
        #         'db_name': cr.dbname, 
        #         'sender': self.pool.get('res.users').browse(cr, 1, uid).name,
        #         'state': states['done'],
        #         'menu_path': 
        #         }
        
        for user in user_ids:
            email = user.login
            if email or email.strip():
                email_template = self.env['mail.template'].create({
                        'name': _('Followup '),
                        'email_from': self.env.user.company_id.email or '',
                        'model_id': self.env['ir.model'].search([('model', '=', 'tender.protocol')]).id,
                        'subject': u'Хурлын протоколтой танилцана уу',
                        'email_to': email,
                        'lang': self.env.user.lang,
                        'auto_delete': True,
                        'body_html':body_html,
                        #  'attachment_ids': [(6, 0, [attachment.id])],
                        })
                email_template.sudo().send_mail(self.id)
        return True

    @api.multi
    def send_notification(self,signal):
        '''Имэйл илгээнэ'''
        states = {
                  'done': u'Дууссан',
                  }
        
        emp = ''
        emp_name=[]
        protocol_obj=self
        for employee in protocol_obj.member_ids:
            emp=employee.name
            emp_name.append(emp)
            members = ';'.join(emp_name)
        
        
        mail_obj = self.env['mail.followers']
        template_id = self.env['ir.model.data'].get_object_reference('nomin_tender', 'tender_meeting_protocol_email_template')[1]
        
        model_obj = self.env['ir.model.data']
        follower_ids = mail_obj.search([('res_model','=','tender.protocol'),('res_id','in',self._ids)])
        
        if follower_ids:
            followers = self.env['mail.followers'].browse(follower_ids)
            user_ids = []
            if followers:
                user_ids = self.env['res.users'].search([('partner_id','in',[follower.partner_id.id for follower in followers])])
        
        
        data = {
                'subject': u'Хурлын протокол',
                'tender': protocol_obj.tender_id.name,
                'meet_name': protocol_obj.meeting_id.name,
                'tender_name': protocol_obj.tender_id.desc_name,
                # 'comment': protocol_obj.meet_protocol,
                'state': protocol_obj.state,
                'member_ids': members,
                'model': 'tender.protocol',
                'base_url': self.env['ir.config_parameter'].get_param('web.base.url'),
                'action_id': self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_protocol_menu')[1],
                'id': protocol_obj[0].id,
                'db_name': request.session.db, 
                'sender': self.env['res.users'].browse(self.env.user.id).name,
                'state': states[signal],
                'menu_path': u'Тендер / Тендер / Тендерийн протокол',
                }
        self.env.context = data
        for user_id in user_ids:
            if user_id != uid:
                self.pool['mail.template'].send_mail(self.env.cr, 1, template_id, user_id.id, force_send=True, context=self.env.context)
      
        return True
    
    '''Устгах'''
    @api.multi
    def unlink(self):
        '''Ноорог тендерийн протоколыг устгах боломжтой'''
        for protocol in self:
            if protocol.state!='draft':
                raise UserError(_(u'Ноорог төлөвөөс бусад үед устгах боломжгүй.'))
        return super(tender_protocol, self).unlink()
    
    @api.multi
    def action_to_sent(self):

        self.write({'state':'sent'})

    @api.multi
    def action_to_done(self):
        '''Тендерийн протоколыг дуусгах'''
        users = []

        for protocol in self:
            for commit in protocol.committee_member_ids:
                if commit.read_state =='unread':
                    raise UserError(_(u'%s гишүүн танилцаагүй байна.')%(commit.employee_id.name))
            if protocol.member_ids:
                for employee in protocol.member_ids:
                    user_ids = self.env['res.users'].search([('id','=',employee.user_id.id)])
                    if user_ids:
                        users.append(user_ids.id)
                        self._add_followers(users)
        
        #self.send_notification('done')
        self.write({'state':'done'})

