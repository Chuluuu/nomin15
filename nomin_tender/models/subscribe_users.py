# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime,date, timedelta
import datetime, time
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.translate import _
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError, AccessError

from odoo.http import request
import logging
_logger = logging.getLogger(__name__)
    
class subscribe_users(models.Model):
    _name='subscribe.users'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    tender_type_ids = fields.Many2many('tender.type', domain=[('parent_id','=',False)],string = "Tender Type", ondelete='restrict')
    email           = fields.Char(string = "Tender Received Email", copy=False)
    
    
    def send_tender_invitation_subusers(self,ids,tender):
        '''Урилга авах бүртгэл рүү имэйл илгээнэ'''
        template_id = self.env['ir.model.data'].get_object_reference('nomin_tender', 'tender_invitation_sub_users_email_template')[1]
        tender_obj = self.env['tender.tender'].browse(tender)
        invitation_obj = self.env['tender.invitation.guide'].browse(tender_obj.invitation_id.id)
        published_date = datetime.datetime.strptime(tender_obj.published_date, '%Y-%m-%d %H:%M:%S')
        date_end = datetime.datetime.strptime(tender_obj.date_end, '%Y-%m-%d %H:%M:%S')
        
        data = {
            'subject': u'"Номин Холдинг" ХХК-ийн "%s" тендерийн урилга'%(tender_obj.desc_name),
            'name': tender_obj.name,
            'company': tender_obj.company_id.name,
            'desc_name': tender_obj.desc_name,
            'publish_date': published_date+timedelta(hours=8),
            'end_date': date_end+timedelta(hours=8),
            'invitation_name': invitation_obj.invitation_info,
            'invitation_detail': invitation_obj.invitation_detail,
            'model': 'tender.tender',
            'base_url': self.env['ir.config_parameter'].get_param('web.base.url'),
            'action_id': self.env['ir.model.data'].get_object_reference('nomin_tender', 'action_tender_list')[1],
            'id': tender_obj[0].id,
            'db_name': request.session.db, 
            'sender': self.env['res.users'].browse(self.env.user.id).name,
            'state': u'Нийтлэгдсэн',
            }
        
        self.env.context = data
        self.pool['mail.template'].send_mail(self.env.cr, 1, template_id, ids, force_send=True, context=self.env.context)
        return True
    