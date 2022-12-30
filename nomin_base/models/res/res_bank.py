# -*- coding: utf-8 -*-

import re

from openerp import api, fields, models, _
from openerp.osv import expression
from openerp.exceptions import UserError
from lxml import etree

class Bank(models.Model):
    _inherit = 'res.bank'
    
    is_nes_sync = fields.Boolean(string='Is NES Sync',track_visibility='always')
#     
#     name = fields.Char(required=True, track_visibility='always')
#     street = fields.Char(track_visibility='always')
#     street2 = fields.Char(track_visibility='always')
#     zip = fields.Char(track_visibility='always')
#     city = fields.Char(track_visibility='always')
#     state = fields.Many2one('res.country.state', 'Fed. State', domain="[('country_id', '=', country)]",track_visibility='always')
#     country = fields.Many2one('res.country',track_visibility='always')
#     email = fields.Char(track_visibility='always')
#     phone = fields.Char(track_visibility='always')
#     fax = fields.Char(track_visibility='always')
#     active = fields.Boolean(default=True,track_visibility='always')
#     bic = fields.Char('Bank Identifier Code', select=True, help="Sometimes called BIC or Swift.",track_visibility='always')

class ResPartnerBank(models.Model):
    _name='res.partner.bank'
    _inherit = ['res.partner.bank', 'mail.thread', 'mail.activity.mixin']
    
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for acc in self:
            name = acc.acc_number
            if acc.currency_id:
                name += ' [%s]'%(acc.currency_id.name)
            if acc.bank_id:
                name += ' - ' + acc.bank_id.name
            result.append((acc.id, name))
        return result
    
    active = fields.Boolean(string='Active', default=True, help="If the active field is set to False, it will allow you to hide the account without removing it.")
    acc_number = fields.Char('Account Number', required=True,track_visibility='always')
    bank_id = fields.Many2one('res.bank', string='Bank',track_visibility='always')
    department_id = fields.Many2one('hr.department', 'Department', domain=[('is_sector', '=', True)],track_visibility='always')
    rule_department_id = fields.Many2one('hr.department', 'Rule Department', domain=[('is_sector', '=', True)],track_visibility='always')
    account_id = fields.Many2one('account.account', string='Account', domain=[('type', '=', 'MNYPAY')],track_visibility='always')
    is_nes_sync = fields.Boolean(string='Is NES Sync',track_visibility='always')
    swift_code = fields.Char(string='Swift Code' , size=128,track_visibility='always')
    bank_account_name = fields.Char(string='Bank Account Name' , size=128,track_visibility='always')
    partner_id = fields.Many2one('res.partner', u'Данс эзэмшигч', ondelete='cascade', track_visibility='always', select=True)
    currency_id = fields.Many2one('res.currency', required=True, string='Currency',track_visibility='always')
    
    iban_number = fields.Char(string='Iban number')
    correspondent_bank = fields.Char(string='Correspondent bank')
    
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ResPartnerBank, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        allowed_deps = self.env.user.budget_allowed_departments.ids
        child_deps=[]
        if allowed_deps:
            child_deps = self.env['hr.department'].get_child_deparments(allowed_deps, only_sector=True)
        doc = etree.XML(res['arch'])
        for node in doc.xpath("//field[@name='department_id']"):
            user_filter =  "[('id', 'in',"+str(child_deps)+")]"
            node.set('domain',user_filter)
        res['arch'] = etree.tostring(doc)
        return res