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
from openerp.osv import expression
from datetime import datetime,date
import logging
_logger = logging.getLogger(__name__)
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from datetime import datetime 
import datetime 
import time 
import dateutil
from datetime import date
from openerp.osv import osv
from openerp.http import request

class tender_date_extend(models.Model):
    _name = "tender.date.extend"
    _description = "Tender extend date"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    '''Тендерийн хугацаа сунгалт
    '''
    tender_id               = fields.Many2one('tender.tender','Current tender',ondelete='restrict', track_visibility='always', index=True, domain=[('state','in',['bid_expire'])])
    name                    = fields.Char('Name', track_visibility='always')
    extend_date_start       = fields.Date('Extend Start Date', track_visibility='always')
    extend_date_end         = fields.Datetime('Extend Close Date', track_visibility='always')
    extend_content          = fields.Text('Extend Content', track_visibility='always')
    user_id                 = fields.Many2one('res.users', string='User', required=True, default=lambda self: self.env.user, readonly=True,ondelete='restrict', track_visibility='always')
    state                   = fields.Selection([('draft', 'Draft'),('pending','Pending'),
                                                ('done','Done'),('cancelled','Cancel')], 
                              string ='Status', track_visibility='onchange', copy=False, default='draft')
    
    def _add_followers(self,user_ids): 
        '''Дагагч нэмнэ'''
        self.message_subscribe_users(user_ids=user_ids)
        
    @api.model
    def create(self, vals):
        '''Хугацаа сунгалт үүсгэх үед 
           огнооны шалгуур ажиллаж байна
        '''
        if vals.get('extend_date_start') or vals.get('extend_date_end'):
            if vals.get('extend_date_start') < time.strftime('%Y-%m-%d'):
                raise UserError(_(u'Эхлэх огноо одоогийн цагаас бага байна.'))
            
            if vals.get('extend_date_start') >= vals.get('extend_date_end'):
                raise UserError(_(u'Эхлэх огноо дуусах огнооноос их байна.'))
            
        result = super(tender_date_extend, self).create(vals)
        if result.tender_id:
            users = self.env['res.users'].sudo().search([('partner_id','in',result.tender_id.message_partner_ids.ids)])
            if users:
                for user in users:
                    result._add_followers(user.id)
        return result
    
    @api.multi
    def write(self, vals):
        '''Хугацаас сунгалт засах үед огнооны 
           шалгуур ажиллана, дагагч нэмнэ
        '''
        if vals.get('extend_date_start'):
            extend_date_start=False
            extend_date_start = vals.get('extend_date_start')
        else:
            extend_date_start = self.extend_date_start
        
        if vals.get('extend_date_end'):
            extend_date_end=False
            extend_date_end = vals.get('extend_date_end')
        else:
            extend_date_end = self.extend_date_end
            
        if extend_date_start < time.strftime('%Y-%m-%d'):
            raise UserError(_(u'Эхлэх огноо одоогийн цагаас бага байна.'))
        
        if extend_date_start or extend_date_end:
            if extend_date_start > extend_date_end:
                raise UserError(_(u'Эхлэх огноо дуусах огнооноос их байна.'))
        
        if vals.get('tender_id'):
            tender_id=False
            tender_id = vals.get('tender_id')
        else:
            tender_id = self.tender_id.id
            
        if tender_id:
            tender = self.env['tender.tender'].browse(tender_id)
            users = self.env['res.users'].sudo().search([('partner_id','in', tender.message_partner_ids.ids)])
            if users:
                for user in users:
                    tender._add_followers(user.id)
        result = super(tender_date_extend, self).write(vals)
        
        
        return result
    
    @api.multi
    def send_notification(self,signal):
        '''Тендерийн хугацааг сунгаж, батлагдах үед имэйл илгээнэ'''
        states = {
                  'pending': u'илгээсэн',
                  'done': u'батлагдсан',
                  }
        extend_obj=self
        template_id = self.env['ir.model.data'].get_object_reference('nomin_tender', 'tender_tender_date_extend_email_template2')[1]
        #model_obj = openerp.pooler.get_pool(cr.dbname).get('ir.model.data')
        date = datetime.datetime.strptime(extend_obj.extend_date_end, '%Y-%m-%d %H:%M:%S')
        
        data = {
                'subject': u'"%s" дугаартай "%s" тендерийн хугацаа cунгах хүсэлт "%s" байна.'%(extend_obj.tender_id.name,extend_obj.tender_id.desc_name,states[signal]),
                'name': extend_obj.tender_id.name,
                'desc_name': extend_obj.tender_id.desc_name,
                'tender_type': extend_obj.tender_id.type_id.name,
                'child_type': extend_obj.tender_id.child_type_id.name,
                'ordering_date': extend_obj.tender_id.ordering_date,
                'state': u'Веб байршуулсан' if extend_obj.tender_id.state == 'published' else u'Бичиг баримт хүлээн авч дууссан',
                'extend_name': extend_obj.name,
                'content': extend_obj.extend_content,
                'extend_date_start':extend_obj.extend_date_start,
                'extend_date_end':date+timedelta(hours=8),
                'model': 'tender.date.extend',
                'base_url': self.env['ir.config_parameter'].get_param('web.base.url'),
                'action_id': self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_extend_menu')[1],
                'id': extend_obj[0].id,
                'db_name': request.session.db, 
                'extend_state': states[signal],
                'menu_path': u'Тендер / Тендер / Тендерийн хугацаа сунгалт',
                }
        
        if states[signal] == u'илгээсэн':
            notif_groups = self.env['ir.model.data'].get_object_reference('nomin_tender', 'group_tender_manager')
            
        if states[signal] == u'батлагдсан':
            notif_groups = self.env['ir.model.data'].get_object_reference('nomin_tender', 'group_tender_secretary')
        
        if notif_groups:   
            group_user_ids = []
            sel_user_ids = []
            sel_user_obj = self.env['res.users'].search([('groups_id','in',[notif_groups[1]])])
                
            for sel_user_line in sel_user_obj:
                sel_user_ids.append(sel_user_line.id)
            group_user_obj = self.env['res.users'].search([('id','in',sel_user_ids)])
            
            if group_user_obj:
                for group_user_line in group_user_obj:
                    group_user_ids.append(group_user_line.id)
                users = self.env['res.users'].browse(group_user_ids)
                #user_emails = []
                self.env.context = data
                for user in users:
                    #user_emails.append(user.login)
                    self.pool['mail.template'].send_mail(self.env.cr, 1, template_id, user.id, force_send=True, context=self.env.context)
            
        return True
    @api.multi
    def send_notification_followers(self, signal):
        '''Имэйл илгээнэ'''
        states = {
                  'published': u'Нээлттэй тендер',
                  'expire_bid': u'Тендерийн материал хүлээн авч дууссан',
                  }
        extend_obj=self
        tender_obj = self.env['tender.tender'].browse(extend_obj.tender_id.id)
#         print "________________ETSTSEESSV__________",extend_obj
        template_id = self.env['ir.model.data'].get_object_reference('nomin_tender', 'tender_extend_followers_email_template')[1]
        template_id1 = self.env['ir.model.data'].get_object_reference('nomin_tender', 'invitation_receiver_email_template1')[1]
        published_date = datetime.datetime.strptime(tender_obj.published_date, '%Y-%m-%d %H:%M:%S')
        date_end = datetime.datetime.strptime(tender_obj.date_end, '%Y-%m-%d %H:%M:%S')
        #model_obj = openerp.pooler.get_pool(cr.dbname).get('ir.model.data')
        data = {
                'subject': u'Тендерийн хугацаа сунгалт',
                'name': tender_obj.name,
                'company': tender_obj.company_id.name,
                'department': tender_obj.respondent_department_id.name,
                'ordering_date':tender_obj.ordering_date,
                'type_name': tender_obj.type_id.name,
                'desc_name': tender_obj.desc_name,
                'publish_date':published_date+timedelta(hours=8),
                'end_date': date_end+timedelta(hours=8),
                'model': 'tender.tender',
                'base_url': self.env['ir.config_parameter'].get_param('web.base.url'),
                'action_id': self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_list')[1],
                'id': tender_obj[0].id,
                'db_name': request.session.db,
                'extend_from_date':extend_obj.extend_date_start,
                'extend_to_date':extend_obj.extend_date_end,
                'sender': self.env['res.users'].browse(self.env.user.id).name,
                'state': states[signal],
                'menu_path': u'Тендер / Тендер / Тендерийн жагсаалт',
                }
        
        self.env.context = data
        if tender_obj.message_partner_ids:
            user_emails = []
            for user in tender_obj.message_partner_ids:
                user_emails.append(user.email)
                self.env['mail.template'].send_mail(self.env.cr, 1, template_id, user.id, force_send=True, context=self.env.context)
                
        part_ids_noti = []
        if tender_obj.requirement_partner_ids:
            for partner in tender_obj.requirement_partner_ids:
                part_ids_noti.append(partner.id)
                
                
        for p_id in part_ids_noti:
            self.env['mail.template'].send_mail(self.env.cr, 1, template_id1, p_id, force_send=True, context=self.env.context)
        return True
    
    @api.multi
    def extend_save(self):
        '''Хугацаа сунгалт үүсгэх'''
        #data =  self.browse(cr, uid, ids, context=context)[0]
        active_id = self.env.context and self.env.context.get('active_id', False) or False
        _logger.info(u'\n\n\n\n\n Хугацаа сунгалт: Тендерийн id= %s', active_id)
        self.write({'state': 'pending',
                    'tender_id': active_id,})
        # self.send_notification('pending')
        
    @api.multi
    def action_to_confirmed(self):
        '''Хугацаа сунгалт батлах'''
        date_obj=self
        if date_obj.tender_id:
            self.env['tender.tender'].browse(date_obj.tender_id.id).write({ 'state':'published',
                                                                                'is_extend': False,
                                                                                'date_end':date_obj.extend_date_end })
            self.write({'state':'done'})
            # self.send_notification('done')
    
    @api.multi    
    def action_to_cancel(self):
        '''Хугацаа сунгалт цуцлах'''
        self.write({'state':'cancelled'})
    
    @api.multi
    def action_to_pending(self):
        '''Хугацаа сунгалт илгээх'''
        # self.send_notification('pending')
        self.write({'state':'pending'})

    @api.multi
    def action_to_approved_date(self):
        '''Хугацаа сунгалт батлах'''
        if self.env.context.get('reg_id') != False:
            tender_obj=self.env['tender.tender'].browse(self.env.context.get('reg_id'))
            extend_obj=self
            for extend in extend_obj:
                if tender_obj.state == 'bid_expire':
                    if tender_obj.is_extend==False:
                        self.env['tender.tender'].browse(tender_obj.id).write({'state': 'published',
                                                                               'is_extend': True,
                                                                               'date_end': extend.extend_date_end,})
                        self.send_notification('done')
                        self.env['tender.date.extend'].browse(extend.id).write({'state':'done'})
                    else:
                        raise UserError(_(u'Тендерийн сунгалт хийгдэж батлагдсан байна'))
                else:
                    raise UserError(_(u'Тендерийн сунгалт хийгдэж батлагдсан байна'))
        
    @api.multi
    def unlink(self):
        '''Ноорог болон цуцалсан төлөвтэй хугацаа сунгалтыг устгах боломжтой'''
        for order in self:
            if order.state not in ['draft','cancelled']:
                raise UserError(_(u'Та батлагдсан хугацаа сунгах хүсэлтийг устгах боломжгүй !'))
        return super(tender_date_extend, self).unlink()
        
class tender_meeting(models.Model):
    _name = 'tender.meeting'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.multi
    def name_get(self):
        '''Тендерийн хурлын дугаар тендерийн нэр 
            талбаруудыг залгаж харуулна
        '''
        result = []
        for meet in self:
            name = meet.name
            if meet.tender_id.desc_name:
                name = u'%s-%s'%(name,meet.tender_id.desc_name)
            result.append((meet.id, name))
        return result
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        '''Тендерийн хурлын дугаар, тендерийн 
            нэр талбаруудаар хайлт хийнэ
        '''
        args = args or []
        domain = []
        if name:
            domain = ['|',('tender_id.desc_name', '=ilike', '%' + name+'%'),('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&'] + domain
        categories = self.search(domain + args, limit=limit)
        return categories.name_get()
    
    
    name                = fields.Char('Meeting Name', track_visibility='always')
    tender_id           = fields.Many2one('tender.tender', string='Tender', track_visibility='onchange',ondelete='restrict', index=True)
    meeting_from_date   = fields.Datetime(string ="Meeting of tender date start",track_visibility='onchange')
    meeting_to_date     = fields.Datetime(string ="Meeting of tender date end",track_visibility='onchange')
    comment             = fields.Text(string= "Comment")
    user_id             = fields.Many2one('res.users', string='User', required=True, default=lambda self: self.env.user, readonly=True,ondelete='restrict')
    state               = fields.Selection([('draft', 'Draft'),('confirmed','Confirmed'),('done','Done'),('cancel','Cancel')],
                                                 string='State', readonly=True, default='draft', track_visibility='always')
    
    def _add_followers(self,user_ids): 
        '''Дагагч нэмнэ'''
        self.message_subscribe_users(user_ids=user_ids)
        
#     Түр коммент болгов
    @api.model
    def create(self,vals):
        '''Тендерийн хурлыг үүсгэхэд огнооны шалгуур ажиллаж байна'''
        meet_id = super(tender_meeting, self).create(vals)
        meet = self.browse(meet_id.id)
        # if meet.meeting_from_date < time.strftime('%Y-%m-%d %H:%M:%S'):
        #         raise UserError(_(u'Хурал эхлэх огноо хэтэрсэн байна.'))
          
        if meet.meeting_from_date and meet.meeting_to_date:
            if meet.meeting_from_date >= meet.meeting_to_date:
                raise UserError(_(u'Хурлын эхлэх огноо дуусах огнооноос хэтэрсэн байна.'))
             
        if meet.tender_id:
            users = self.env['res.users'].search([('partner_id', 'in', meet.tender_id.message_partner_ids.ids)])
            if users:
                user = []
                for line in users:
                    user.append(line.id)
                meet_id.message_subscribe_users(user_ids=user)
        return meet_id
    
    @api.multi 
    def write(self, values):
        '''Тендерийн хурлыг засахад огнооны шалгуур ажиллаж байна'''
        obj=self
        if values.get('meeting_from_date'):
            meeting_from_date=False
            meeting_from_date = values.get('meeting_from_date')
        else:
            meeting_from_date = obj.meeting_from_date
          
        if values.get('meeting_to_date'):
            meeting_to_date=False
            meeting_to_date = values.get('meeting_to_date')
        else:
            meeting_to_date = obj.meeting_to_date
          
        if values.get('meeting_from_date') or values.get('meeting_to_date'):
            # if meeting_from_date < time.strftime('%Y-%m-%d %H:%M:%S'):
            #     raise UserError(_(u'Хурал эхлэх огноо хэтэрсэн байна.'))
              
            if meeting_from_date > meeting_to_date:
                raise UserError(_(u'Хурлын эхлэх огноо дуусах огнооноос хэтэрсэн байна.'))
         
        if values.get('tender_id'):
            tender_id=False
            tender_id = values.get('tender_id')
        else:
            tender_id = obj.tender_id.id
        if tender_id:
            tenders = self.env['tender.tender'].browse(tender_id)
            users = self.env['res.users'].search([('partner_id','in', tenders.message_partner_ids.ids)])
 
        values.update({'message_partner_ids': tenders.message_partner_ids.ids})
        meet_id = super(tender_meeting, self).write(values)
                 
        return meet_id
    
    @api.multi         
    def send_notif_meeting(self,signal):
        '''Хурал батлагдах имэйл илгээнэ'''
        states = {
                  'confirmed': u'батлагдсан',
                  'done': u'дууссан',
                  'cancel': u'цуцлагдсан',
                  }
        mail_obj = self.env['mail.followers']
        template_id = self.env['ir.model.data'].get_object_reference('nomin_tender', 'tender_meeting_email_template1')[1]
        meet_obj = self
        tender_obj=self.env['tender.tender'].browse(meet_obj.tender_id.id)
#         print time.strftime('We are the %d, %b %Y')
        date_from = datetime.datetime.strptime(meet_obj.meeting_from_date, '%Y-%m-%d %H:%M:%S')
        date_to = datetime.datetime.strptime(meet_obj.meeting_to_date, '%Y-%m-%d %H:%M:%S')
        data = {
                'subject': u'"%s" дугаартай "%s" тендерийн хурал "%s" цагт товлогдсон байна.'%(meet_obj.tender_id.name,meet_obj.tender_id.desc_name,date_from+timedelta(hours=8)),
                'name': meet_obj.tender_id.name,
                'desc_name': meet_obj.tender_id.desc_name,
                'tender_type': meet_obj.tender_id.type_id.name,
                'child_type': meet_obj.tender_id.child_type_id.name,
                'ordering_date': meet_obj.tender_id.ordering_date,
                'state': meet_obj.tender_id.state,
                'meet_from_date': date_from+timedelta(hours=8),
                'meet_to_date':date_to+timedelta(hours=8),
                'meetname': meet_obj.name,
                'comment': meet_obj.comment,
                'model': 'tender.meeting',
                'base_url': self.env['ir.config_parameter'].get_param('web.base.url'),
                'action_id': self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_schedule_meeting')[1],
                'id': meet_obj[0].id,
                'db_name': request.session.db, 
                'sender': self.env['res.users'].browse(self.env.user.id).name,
                'state': states[signal],
                'menu_path': u'Тендер / Тендер / Тендерийн хурал товлолт',
                }
        user_emails = []
        self.env.context = data
        if tender_obj.message_partner_ids:
            for user in tender_obj.message_partner_ids:
                user_emails.append(user.email)
                self.pool['mail.template'].send_mail(self.env.cr, 1, template_id, user.id, force_send=True, context=self.env.context)
        return True   

    
    @api.multi
    def action_confirm(self):
        tender_obj = self.env['tender.tender']
        date_now = datetime.datetime.strptime(time.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
        
        for order in self:
            from_date = datetime.datetime.strptime(order.meeting_from_date, '%Y-%m-%d %H:%M:%S')
            meet_id=self.env['tender.meeting'].search([('tender_id','=',order.tender_id.id),('state','=','confirmed')])
            if meet_id:
                raise UserError(_(u'Тухайн тендерийн хурал товлогдож батлагдсан байна !'))
            else:
                tender_obj.browse(order.tender_id.id).write({'is_meeting': True})
            
            if date_now>from_date:
                raise UserError(_(u'Хурлын огноо одоогийн цагаас их байх ёстой.'))
            else:
                name = self.env['ir.sequence'].get('tender.meeting')
        self.write({'state': 'confirmed',
                    'name': name})
        # self.send_notif_meeting('confirmed')
       
    @api.multi
    def action_done(self):
        '''Товлогдсон хурлыг дууссан төлөвт оруулах'''
        self.write({'state': 'done'})
    
    @api.multi
    def action_cancel(self):
        """Товлогдсон хурал цуцлах"""
        mod_obj = self.env['ir.model.data']
        res = mod_obj.get_object_reference('nomin_tender', 'action_tender_meet_note')
        
        return {
            'type': 'ir.actions.act_window',
            'name': u'Тайлбар',
            'res_model': 'tender.meet.note',
            'view_type': 'form',
            'view_mode': 'form',
            'target' : 'new',
        }
        
    #---------------------------------------------------------------- @api.multi
    #-------------------------------------------------- def meeting_notif(self):
        # self.env.cr.execute("select id from tender_meeting where state='confirmed' and \
         # now() between (meeting_from_date - interval '16 hour') and (meeting_from_date - interval '15 hour')")
        #---------------------------------- records = self.env.cr.dictfetchall()
        #----------------------------------------------------------- if records:
            #-------------------------------------------- for record in records:
                #----------------------- self.send_meeting_notif([record['id']])
        # self.env.cr.execute("select id from tender_meeting where state='confirmed' and \
         # now() between (meeting_from_date + interval '5 hour') and (meeting_from_date + interval '6 hour')")
#------------------------------------------------------------------------------ 
        #---------------------------------- records = self.env.cr.dictfetchall()
        #----------------------------------------------------------- if records:
            #-------------------------------------------- for record in records:
                #----------------------- self.send_meeting_notif([record['id']])
                
#   Cron job ni huuchin @api deer suurilsan uchir hurvuuleh bolomjgui
#    shine api_aar bichegdsen base deer hurvunu
    def meeting_notif(self,cr,uid):
        query = "select id from tender_meeting where state='confirmed' and \
         now() between (meeting_from_date - interval '16 hour') and (meeting_from_date - interval '15 hour')"
        cr.execute(query)

        records = cr.dictfetchall()
        if records:
            for record in records:
                self.send_meeting_notif( cr, 1, [record['id']])
        query = "select id from tender_meeting where state='confirmed' and \
         now() between (meeting_from_date + interval '5 hour') and (meeting_from_date + interval '6 hour')"
        cr.execute(query)

        records = cr.dictfetchall()
        if records:
            for record in records:
                self.send_meeting_notif(cr, 1, [record['id']])
                     
    def send_meeting_notif(self):
        states = {
                  'confirmed': u'батлагдсан',
                  'done': u'дууссан',
                  'cancel': u'цуцлагдсан',
                  }
        mail_obj = self.env['mail.followers']
        template_id = self.env['ir.model.data'].get_object_reference('nomin_tender', 'tender_meeting_email_template1')[1]
        meet_obj = self
        tender_obj=self.env['tender.tender'].browse(meet_obj.tender_id.id)
#         print time.strftime('We are the %d, %b %Y')
        date_from = datetime.datetime.strptime(meet_obj.meeting_from_date, '%Y-%m-%d %H:%M:%S')
        date_to = datetime.datetime.strptime(meet_obj.meeting_to_date, '%Y-%m-%d %H:%M:%S')
        data = {
                'subject': u'"%s" дугаартай "%s" тендерийн хурал "%s" цагт товлогдсон байна.'%(meet_obj.tender_id.name,meet_obj.tender_id.desc_name,date_from+timedelta(hours=8)),
                'name': meet_obj.tender_id.name,
                'desc_name': meet_obj.tender_id.desc_name,
                'tender_type': meet_obj.tender_id.type_id.name,
                'child_type': meet_obj.tender_id.child_type_id.name,
                'ordering_date': meet_obj.tender_id.ordering_date,
                'state': meet_obj.tender_id.state,
                'meet_from_date': date_from+timedelta(hours=8),
                'meet_to_date':date_to+timedelta(hours=8),
                'meetname': meet_obj.name,
                'comment': meet_obj.comment,
                'model': 'tender.meeting',
                'base_url': self.env['ir.config_parameter'].get_param('web.base.url'),
                'action_id': self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_schedule_meeting')[1],
                'id': meet_obj[0].id,
                'db_name': request.session.db, 
                'sender': self.env['res.users'].browse(self.env.user.id).name,
                'state': states['confirmed'],
                'menu_path': u'Тендер / Тендер / Тендерийн хурал товлолт',
                }
        user_emails = []
        self.env.context = data
        if tender_obj.message_partner_ids:
            for user in tender_obj.message_partner_ids:
                user_emails.append(user.email)
                self.env['mail.template'].send_mail(self.env.cr, 1, template_id, user.id, force_send=True, context=self.env.context)
        return True
       
    #---------------------------------------------------------------- @api.multi
    #----------------------------------------- def running_meet(self, cr , uid):
        #----------- '''Товлогдсон хурлын хугацаа болсон эсэхийг шалгаж байна'''
        # self.env.cr.execute("select tender.id, tender.is_meet_start_date, meeting.* \
                #----- from tender_meeting as meeting, tender_tender as tender \
                # where tender.id = meeting.tender_id and meeting.meeting_to_date is not null \
                # and meeting.state = 'confirmed' and tender.is_meet_start_date = false \
                #----------- group by tender.id, meeting.id, meeting.tender_id")
        # _logger.info(u'----------------Батлагдсан хурал-- %s', self.env.cr.execute)
        #---------------------------------------------------- #cr.execute(query)
#------------------------------------------------------------------------------ 
        #---------------------------------- records = self.env.cr.dictfetchall()
        #----------------------------------------------------------- if records:
            #-------------------------------------------- for record in records:
# #                 bid_ids=self.pool.get('tender.participants.bid').search(cr, 1, [('tender_id','=',record['tender_id'])])
                #---------------------- date_start = record['meeting_from_date']
                #-------------------------- date_end = record['meeting_to_date']
                #------------------- date_now=time.strftime('%Y-%m-%d %H:%M:%S')
                #------------------------------------ if date_start <= date_now:
                    # self.env['tender.tender'].browse(record['tender_id']).write({'is_meet_start_date': True})
#------------------------------------------------------------------------------ 
        # self.env.cr.execute("select A.id as id,B.state from tender_date_extend A inner join tender_tender B ON A.tender_id =B.id where A.state in ('draft','pending') and \
        # B.state in ('closed','finished','cancelled','delay','in_selection','contract_request') and A.extend_date_start >=now()")
        #---------------------------------------------------- #cr.execute(query)
        #---------------------------------- records = self.env.cr.dictfetchall()
        #------------------------------------------------------------ states = {
        # 'closed':u'Хаагдсан','finished':u'Дууссан','cancelled':u'Цуцлагдсан','delay':u'Хойцлуулсан','in_selection':u'Сонгон шалгаруулалт',
        #--------------------------------- 'contract_request':u'Гэрээний хүсэлт'
#------------------------------------------------------------------------------ 
        #--------------------------------------------------------------------- }
        #----------------------------------------------------------- if records:
            #-------------------------------------------- for record in records:
                # self.env['tender.date.extend'].browse(record['id']).write({'state':'cancelled'})
                # self.env['tender.date.extend'].message_post(body=u'Үндсэн тендер бичиг баримт хүлээн авч буйгаас %s төлөвт шилжив '%(states[record['state']]))


    def running_meet(self, cr, uid):
        '''Товлогдсон хурлын хугацаа болсон эсэхийг шалгаж байна'''
        query= "select tender.id, tender.is_meet_start_date, meeting.* \
                from tender_meeting as meeting, tender_tender as tender \
                where tender.id = meeting.tender_id and meeting.meeting_to_date is not null \
                and meeting.state = 'confirmed' and tender.is_meet_start_date = false \
                group by tender.id, meeting.id, meeting.tender_id";
        _logger.info(u'----------------Батлагдсан хурал-- %s', query)
        cr.execute(query)

        records = cr.dictfetchall()
        if records:
            for record in records:
#                 bid_ids=self.pool.get('tender.participants.bid').search(cr, 1, [('tender_id','=',record['tender_id'])])
                date_start = record['meeting_from_date']
                date_end = record['meeting_to_date']
                date_now=time.strftime('%Y-%m-%d %H:%M:%S')
                if date_start <= date_now:
                    self.pool.get('tender.tender').write(cr, uid, record['tender_id'], {'is_meet_start_date': True}, context=None)

        query="select A.id as id,B.state from tender_date_extend A inner join tender_tender B ON A.tender_id =B.id where A.state in ('draft','pending') and \
        B.state in ('closed','finished','cancelled','delay','in_selection','contract_request') and A.extend_date_start >=now()"
        cr.execute(query)
        records = cr.dictfetchall()
        states = {
        'closed':u'Хаагдсан','finished':u'Дууссан','cancelled':u'Цуцлагдсан','delay':u'Хойцлуулсан','in_selection':u'Сонгон шалгаруулалт',
        'contract_request':u'Гэрээний хүсэлт'

        }
        if records:
            for record in records:
                self.pool.get('tender.date.extend').write(cr,1,record['id'],{'state':'cancelled'},context=None)
                self.pool.get('tender.date.extend').message_post(cr, 1, record['id'], body=u'Үндсэн тендер бичиг баримт хүлээн авч буйгаас %s төлөвт шилжив '%(states[record['state']]), context=None)


    @api.multi
    def unlink(self):
        '''Хурлыг ноорог төлөвтэй үед устгана'''
        for order in self:
            if order.state not in ['draft']:
                raise UserError(_(u'Та товлогдсон хурлыг зөвхөн ноорог төлөвтэй үед устгах боломжтой !'))
        return super(tender_meeting, self).unlink()
    
    