
# -*- coding: utf-8 -*-
from odoo import api, fields, models

class purchase_requisition_line_state_history(models.Model):
    _name = "purchase.requisition.line.state.history"


    order_id = fields.Many2one('purchase.order',string=u'Захиалгын дугаар')
    user_id = fields.Many2one('res.users', 'User')
    date = fields.Date(string='Date')
    requisition_line_id = fields.Many2one('purchase.requisition.line',string='Purchase Requisition Line', ondelete='cascade')
    state = fields.Selection([('draft',u'Ноорог'),
     ('sent','Илгээгдсэн'),#Илгээгдсэн
     ('approved','Зөвшөөрсөн'),#Зөвшөөрсөн
     ('verified','Хянасан'),#Хянасан
     ('next_confirm_user','Дараагийн батлах хэрэглэгчид илгээгдсэн'),#Дараагийн батлах хэрэглэгчид илгээгдсэн
     ('confirmed','Батласан'),#Батласан
     ('tender_created','Тендер үүссэн'),#Тендер үүссэн
     ('sent_to_supply','Хангамжаарх худалдан авалт'),#Хангамжаарх худалдан авалт
     ('fulfil_request','Биелүүлэх хүсэлт'),# Биелүүлэх хүсэлт
     ('rfq_created','Үнийн санал үүссэн'),#Үнийн санал үүссэн
     ('fulfill','Биелүүлэх'),# Биелүүлэх
     ('assigned','Assigned'),#Хуваарилагдсан
     ('retrived','Буцаагдсан'),# Буцаагдсан
     ('retrive_request','Буцаагдах хүсэлт'),# Буцаагдах хүсэлт
     ('rejected','Татгалзсан'),
     ('canceled','Цуцлагдсан'),#Цуцлагдсан
     ('ready','Хүлээлгэж өгөхөд бэлэн'),
     ('purchased','Худалдан авалт үүссэн'),#Худалдан авалт үүссэн
     ('sent_to_supply_manager','Бараа тодорхойлох'),#Хангамж импортын менежер
     ('sent_nybo','Нягтлан бодогчид илгээгдсэн'),#Хангамж импортын менежер
     ('compare','Харьцуулалт хийх'),# Харьцуулалт хийх
     ('compared','Харьцуулалт үүссэн'),# Харьцуулалт хийх
     ('done',u'Дууссан')], string='State')

class purchase_requisition_state_history(models.Model):
    _name = "purchase.requisition.state.history"
    
    STATE_SELECTION=[('draft',u'Ноорог'),
                       ('sent','Илгээгдсэн'),#Илгээгдсэн
                       ('approved','Зөвшөөрсөн'),#Зөвшөөрсөн
                       ('verified','Хянасан'),#Хянасан
                       ('next_confirm_user','Дараагийн батлах хэрэглэгчид илгээгдсэн'),#Дараагийн батлах хэрэглэгчид илгээгдсэн
                       ('confirmed','Батласан'),#Батласан
                       ('tender_created','Тендер үүссэн'),#Тендер үүссэн
                       ('sent_to_supply','Хангамжаарх худалдан авалт'),#Хангамжаарх худалдан авалт
                       ('fulfil_request','Биелүүлэх хүсэлт'),# Биелүүлэх хүсэлт
                       ('rfq_created','Үнийн санал үүссэн'),#Үнийн санал үүссэн
                       ('fulfill','Биелүүлэх'),# Биелүүлэх
                       ('assigned','Assigned'),#Хуваарилагдсан
                       ('retrived','Буцаагдсан'),# Буцаагдсан
                       ('retrive_request','Буцаагдах хүсэлт'),# Буцаагдах хүсэлт
                       ('rejected','Татгалзсан'),
                       ('canceled','Цуцлагдсан'),#Цуцлагдсан
                       ('ready','Хүлээлгэж өгөхөд бэлэн'),
                       ('purchased','Худалдан авалт үүссэн'),#Худалдан авалт үүссэн
                       ('sent_to_supply_manager','Бараа тодорхойлох'),#Хангамж импортын менежер
                       ('done',u'Дууссан')
                                   ]
    requisition_id = fields.Many2one('purchase.requisition', 'Reference', ondelete='cascade')
    user_id = fields.Many2one('res.users', 'User Name', select=True)
    sequence = fields.Char('Sequence')
    name =  fields.Char('Name')
    type =  fields.Char('Type')
    group_id= fields.Char('Group')
    state = fields.Selection(STATE_SELECTION,'State', readonly=True, select=True, tracking=True)
        
