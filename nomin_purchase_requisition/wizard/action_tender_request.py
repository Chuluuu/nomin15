# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import time
from openerp import models,  api, _,fields
from datetime import timedelta
from datetime import datetime, date
from openerp.http import request

class CreateTenderRequest(models.TransientModel):
    _name = "action.create.tender.request"
    _description = "Create tender request"

    description = fields.Text(string='Тодорхойлолт')


    @api.multi
    def action_tender_request(self):

    	active_id = self.env.context.get('active_id')
    	if active_id:
    		requisition_id = self.env['purchase.requisition'].browse(active_id)

		requisition_id.write({'state':'tender_request'})
		requisition_id.line_ids.write({'state':'tender_request'})
		requisition_id.message_post(body=self.description)
		groups = self.env['res.groups']
		group_id= self.env['ir.model.data'].get_object_reference('nomin_base', 'group_holding_ceo')[1]
		group = groups.search([('id','=',group_id)])
		user_ids = []
		user_emails=[]
		base_url = self.env['ir.config_parameter'].get_param('web.base.url')
		action_id = self.env['ir.model.data'].get_object_reference('purchase_requisition', 'action_purchase_requisition')[1]
		db_name = request.session.db
		user_ids.append(requisition_id.user_id.id)
		for user in group.users:
				user_ids.append(user.id)
		for email in  self.env['res.users'].browse(user_ids):
			user_emails.append(email.login)
			subject = u'"Шаардахын дугаар %s".'%(requisition_id.name)
			body_html = u'''
                            <h4>Сайн байна уу, \n Таньд энэ өдрийн мэнд хүргье! </h4>
                            <p>
                               ERP системд %s салбарын %s (хэлтэс) дэх %s дугаартай шаардах %s төлөвт орлоо.                               
                            </p>
                            <p><b><li> Шаардахын дугаар: %s</li></b></p>
                            <p><b><li> Салбар: %s</li></b></p>
                            <p><b><li> Хэлтэс: %s</li></b></p>
                            <p><b><li> Хүсч буй хугацаа: %s</li></b></p>
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
                            'Тендер зарлуулах хүсэлт',
                            requisition_id.name,
                             requisition_id.sector_id.name,
                            requisition_id.department_id.name,
                            requisition_id.schedule_date if requisition_id.schedule_date else " ......... ",
                            self.description,
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
		email = u'' + 'Тендер зарлуулах хүсэлт' +u'\n Дараах хэрэглэгчид рүү имэйл илгээгдэв: ' + ('<b>' + ('</b>, <b>'.join(user_emails)) + '</b>')
		requisition_id.message_post(body=email)        

class CreateTenderRequestReturn(models.TransientModel):
    _name = "action.create.tender.request.return"
    _description = "Create tender request"

    description = fields.Text(string='Тодорхойлолт')


    @api.multi
    def action_tender_return(self):

    	active_id = self.env.context.get('active_id')
    	if active_id:
    		requisition_id = self.env['purchase.requisition'].browse(active_id)

		requisition_id.write({'state':'sent_to_supply'})
		requisition_id.line_ids.write({'state':'sent_to_supply'})
		requisition_id.message_post(body=self.description)
