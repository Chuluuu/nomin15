# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.translate import _
from datetime import date ,datetime
import time
from odoo.exceptions import UserError
class purchase_requisition_cancel_note(models.TransientModel):
    _name = "purchase.requisition.cancel.note"
    _description = "Purchase Requisition cancel Note"
    
    note = fields.Text('Note', required=True)
    
    
    def req_cancel(self):
        active_ids = self._context and self._context.get('active_ids', [])
        requisition = self.pool.get('purchase.requisition')    
        subtype = u"Цуцалсан шалтгаан: "
        body = "<b>" + (u"" + self.note) + "</b>"
        requistions = self.env['purchase.requisition'].browse(active_ids)
        requistions.write( {'state':'draft','active_sequence':1})
        requistions.message_post(body=body)
    
    
    def req_reject(self):
        active_ids = self._context and self._context.get('active_ids', [])

        if not active_ids:
            raise UserError(_(u'Анхааруулга'), _(u'ACTIVE id хоосон байна.')) 
        today = date.today()
        period_id = self.env['account.period'].search([('date_start','<=',today),('date_stop','>=',today)])
        reason=self.note
        state ='draft'
        month_limit = 0
        user_emails = []
        active_sequence = 1
        email = ''
        group_user_ids = []
        requisition = self.env['purchase.requisition'].browse(active_ids)
        subtype = u"Татгалзсан шалтгаан: "
        body = u"<b>" + (u"" + reason) + "</b>"
        if 'retrive_request' in self._context:
            state = 'retrive_request'
            active_sequence = requisition[0].active_sequence -1
            notif_groups = self.env['ir.model.data']._xmlid_to_res_id('nomin_purchase_requisition.group_haaa_director')
            group_user_ids = self.env['res.users'].search([('groups_id','in',[notif_groups])])
            if not group_user_ids:
                  raise UserError(_(u'Анхааруулга'), _(u'Хангамж аж ахуйн албаны захирал грүпд хэрэглэгч нар алга байна.')) 
            if group_user_ids:
                for user in group_user_ids:          
                    user_emails.append(user.login)
            user_emails.append(requisition[0].user_id.login)
            email = u'Буцаах хүсэлт Дараах хэрэглэгчид рүү имэйл илгээгдэв: ' + ('<b>' + ('</b>, <b>'.join(user_emails)) + '</b>')
                # self.action_send_email('fulfil_request',next_user_ids.ids)
        if 'retrive' in self._context:

            state = 'confirmed'
            active_sequence = requisition[0].active_sequence -1
            for user in requisition.history_lines:
                group_user_ids.append(user.user_id)
            if not group_user_ids:
                  raise UserError(_(u'Анхааруулга'), _(u'Хангамж аж ахуйн албаны захирал грүпд хэрэглэгч нар алга байна.')) 
            if group_user_ids:
                for user in group_user_ids:
                        user_emails.append(user.login)
            user_emails.append(requisition.user_id.login)
            email = u'Буцаах хүсэлт Дараах хэрэглэгчид рүү имэйл илгээгдэв: ' + ('<b>' + ('</b>, <b>'.join(user_emails)) + '</b>')
        if 'return' in self._context:
            for user in requisition.history_lines:
                group_user_ids.append(user.user_id)
            state = 'draft'
            active_sequence = 1
            if not group_user_ids:
                  raise UserError(_(u'Анхааруулга'), _(u'Хангамж аж ахуйн албаны захирал грүпд хэрэглэгч нар алга байна.')) 
            for user in group_user_ids:          
                    if user:
                        user_emails.append(user.login)
                        

            email = u'Буцаах хүсэлт Дараах хэрэглэгчид рүү имэйл илгээгдэв: ' + ('<b>' + ('</b>, <b>'.join(user_emails)) + '</b>')
            history_ids = self.env['request.history'].search([('requisition_id','in',active_ids),('type','=','confirmed')], order="date desc")

            for request in history_ids[0]:
                confirmed_period_id = self.env['account.period'].search([('date_start','<=',request.date),('date_stop','>=',request.date)])
                if confirmed_period_id ==period_id:
                    user_month_id = self.env['purchase.limit.month'].search([('employee_id.user_id','=',request.user_id.id),('month_id','=',period_id.id)], order="create_date desc")
                    if user_month_id:    
                        for limit in user_month_id:
                            month_limit = limit.purchase_month_limit
                        month_limit = month_limit+requisition.amount
                        user_month_id.write({'purchase_month_limit':month_limit})
                    else:
                         raise UserError(_(u'Анхааруулга'), _(u'Өмнөх сарын лимит алга')) 
                         
        requisition.write({'state':state,'active_sequence':active_sequence})

        for line in requisition.line_ids:
            line.write({'state':state})
        requisition.message_post(body=subtype + body)
        if state =='draft':
            lines = self.env['purchase.confirm.history.lines'].sudo().search([('requisition_id','in',active_ids)])
            lines.unlink()
        if email:
            requisition.message_post(body= user_emails)
        history_obj = self.env['request.history']
        history_obj.create({'requisition_id': active_ids[0],
                'user_id': self._uid,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'type': state,
                }
                )
        return {'type': 'ir.actions.act_window_close'}
