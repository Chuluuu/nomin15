# -*- coding: utf-8 -*-
##############################################################################
#
#    Asterisk Technologies LLC, Enterprise Management Solution    
#    Copyright (C) 2013-2014 Asterisk Technologies LLC Co.,ltd (<http://www.erp.mn>). All Rights Reserved
#
#    Email : unuruu25@gmail.com
#    Phone : 976 + 88005462
#
##############################################################################

from openerp import api, fields, models, SUPERUSER_ID, _
from openerp.tools.translate import _
from openerp.osv.orm import setup_modifiers
from lxml import etree
import time
from openerp.exceptions import UserError, ValidationError

class tender_invitation_guide(models.Model):
    _name = "tender.invitation.guide"
    _description = "Tender Invitation Guide"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    '''Тендерийн урилга
    '''
    name                = fields.Char(string='Tender Invitation Name', track_visibility='onchange')
    tender_id           = fields.Many2one('tender.tender', string='Call for Tender', track_visibility='onchange', ondelete='restrict', index=True)
    summary             = fields.Text('Summary', track_visibility='onchange')
    invitation_info     = fields.Html(u'Тендерийн урилга', track_visibility='onchange')
    invitation_detail   = fields.Html('Invitation Summary')
    tender_doc_id       = fields.Many2one('ir.attachment', 'Tender Document', track_visibility='onchange')
#     invitation_pdf      = fields.Binary('Invitation File')
    #order_date          = fields.Date('Ordering Date')
    #close_date          = fields.Datetime('Close Date')
    state               = fields.Selection(
                            [('draft', 'New'),
                             ('open', 'Open'),
                             ('done', 'Done')], string='Status', readonly=True, track_visibility='onchange',
                                            copy=False, index=True, default='draft', required=True)
    
    def _add_followers(self,user_ids): 
        '''Дагагч нэмнэ'''
        self.message_subscribe_users(user_ids=user_ids)
        
    @api.model
    def create(self, vals):
        '''Тендерийн урилга үүсэх үед нэг тендерт олон урилга үүсгэхгүй'''
        if vals.get('tender_id'):
            tender = self.env['tender.tender'].sudo().search([('id','=',vals.get('tender_id'))])
            if tender.invitation_id:
                raise UserError(_(u'Сонгосон тендерт урилга үүссэн байна. Дахин үүсгэх боломжгүй.'))
        result = super(tender_invitation_guide, self).create(vals)
        if result.tender_id:
            users = self.env['res.users'].sudo().search([('partner_id','in',result.tender_id.message_partner_ids.ids)])
            if users:
                for user in users:
                    result._add_followers(user.id)
        return result
    
    @api.multi
    def write(self, vals):
        '''Тендерийн урилга засах үед нэг тендерт олон урилга үүсгэхгүй'''
        tender_id=False
        tender=False
        if vals.get('tender_id'):
            tender_id = vals.get('tender_id')
        else:
            tender = self.tender_id.id
        if tender_id:
            tenders=self.env['tender.tender'].sudo().search([('id','=',tender_id)])
            if tenders.invitation_id:
                raise UserError(_(u'Сонгосон тендерт урилга үүссэн байна. Дахин үүсгэх боломжгүй.'))
            users = self.env['res.users'].sudo().search([('partner_id','in',tenders.message_partner_ids.ids)])
            if users:
                for user in users:
                    tenders._add_followers(user.id)
            
        result = super(tender_invitation_guide, self).write(vals)
        return result

    @api.multi
    def unlink(self):
        '''Тендерийн урилга нооргоос бусад үед устгах боломжгүй'''
        for order in self:
            if order.tender_id.invitation_id.id == order.id:
                if order.state != 'draft':
                    raise UserError(_(u'Устгах үйлдэл хий боломжгүй!'))
            else:
                return super(tender_invitation_guide, self).unlink()
            