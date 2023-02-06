# -*- coding: utf-8 -*-

import time
from odoo.tools.translate import _
from odoo import models,  api, _,fields
from datetime import timedelta
from datetime import datetime, date
from odoo.http import request


class PurchaseRequisitionSetDone(models.TransientModel):
	_name = 'purchase.requisition.set.done'

	note =  fields.Text(string=u'Тайлбар' ,required=True)

	
	def purchase_set_done(self):
		active_ids = self.env.context.get('active_ids', [])
		notif_groups_ids = self.env['ir.model.data'].get_object_reference( 'nomin_purchase_requisition', 'group_haaa_head')[1]
		group_ids = self.env['res.groups'].browse(notif_groups_ids)
		users = []
		for group in group_ids:
			if group.users:
				users.extend(group.users)
		requistition_id = False
		for line in self.env['purchase.requisition.line'].browse(active_ids):
			line.requisition_id.write({'state':'assigned'})
			line.requisition_id.message_post(body=self.note)
			users.append(line.buyer)
			requisition_id =line.requisition_id
			line.write({'state':'assigned'})
		# if requisition_id:
		# 	self.action_send_email(requisition_id,users)
		return {
		'type': 'ir.actions.client',
		'tag': 'reload',
		}



	
	def action_send_email(self,requisition_id, group_user_ids):
		
		user_emails = []
		base_url = self.env['ir.config_parameter'].get_param('web.base.url')
		action_id = self.env['ir.model.data'].get_object_reference('purchase_requisition', 'action_purchase_requisition')[1]
		db_name = request.session.db        


		group_user_ids = list(set(group_user_ids))
		for email in  group_user_ids:
			user_emails.append(email.login)
			subject = u'"Шаардахын дугаар %s".'%(requisition_id.name)
			body_html = u'''
                            <h4>Сайн байна уу, \n Таньд энэ өдрийн мэнд хүргье! </h4>
                            <p>
                               ERP системд %s салбарын %s (хэлтэс) дэх %s дугаартай шаардах Дууссан төлвөөс Хувиарлагдсан төлөвт орлоо.                               
                            </p>
                            <p><b><li> Шаардахын дугаар: %s</li></b></p>
                            <p><b><li> Салбар: %s</li></b></p>
                            <p><b><li> Хэлтэс: %s</li></b></p>
                            <p><b><li> Шалтгаан: %s</li></b></p>
                            <p><li> <b><a href=%s/web?db=%s#id=%s&view_type=form&model=purchase.requisition&action=%s>Шаардахын мэдэгдэл</a></b> цонхоор дамжин харна уу.</li></p>

                            </br>
                            <p>---</p>
                            </br>
                            <p>Энэхүү мэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
                            <p>Баярлалаа.</p>
                        '''%( requisition_id.sector_id.name,
                            requisition_id.department_id.name,
                            requisition_id.name,                            
                            requisition_id.name,
                             requisition_id.sector_id.name,
                            requisition_id.department_id.name,
                            self.note if self.note else " ......... ",
                            base_url,
                            db_name,
                            requisition_id.id,
                            action_id
                            )
     
			if email.login and email.login.strip():
				email_template = self.env['mail.template'].create({
                    'name': _('Followup '),
                    'email_from': self.env.user.company_id.email or '',
                    'model_id': self.env['ir.model'].search([('model', '=', 'purchase.requisition')]).id,
                    'subject': subject,
                    'email_to': email.login,
                    'lang': self.env.user.lang,
                    'auto_delete': True,
                    'body_html':body_html,
                  #  'attachment_ids': [(6, 0, [attachment.id])],
                })
				email_template.send_mail(requisition_id.id)
			email = u'' +u'\n Дараах хэрэглэгчид рүү имэйл илгээгдэв: ' + ('<b>' + ('</b>, <b>'.join(user_emails)) + '</b>')
        
#		requisition_id.write( {'confirm_user_ids':[(6,0,group_user_ids.ids)]})
#		requisition_id.message_subscribe_users(group_user_ids.ids)
		requisition_id.message_post(body=email)

		# return {
  #           'name': _('Compose Email'),
  #           'type': 'ir.actions.act_window',
  #           'view_type': 'form',
  #           'view_mode': 'form',
  #           'res_model': 'mail.compose.message',
  #           'views': [(compose_form.id, 'form')],
  #           'view_id': compose_form.id,
  #           'target': 'new',
  #           'context': ctx,
  #       }

