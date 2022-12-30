# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from fnmatch import translate
from odoo.osv import osv
from lxml import etree
import time
from datetime import datetime, timedelta


# class partner_transport_category(models.Model):
#     _name = 'partner.transport.category'
# 
#     name = fields.Char(string=u'Тээвэрлэлтийн төрөл')

class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Partner'
    
# 
#     @api.model
#     def name_search(self, name, args=None, operator='ilike', limit=100):
#         args = args or []
#         domain = []
#         if name:
#             # domain = [ ('code', '=ilike', name + '%')]
#             domain = ['|', ('code', '=ilike', name + '%'),'|',('mobile', '=ilike', name + '%'),'|',('phone', '=ilike', name + '%'),'|',('email', '=ilike', name + '%'),'|',('nomin_code', '=ilike', '%' + name),('name', operator, name)]
#             
#             if operator in expression.NEGATIVE_TERM_OPERATORS:
#                 domain = [('name', operator, name)]
#         partners = self.search(domain + args, limit=limit)
#         return partners.name_get()
    
#     def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
#         if not args:
#             args = []
#         if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
#  
#             self.check_access_rights(cr, uid, 'read')
#             where_query = self._where_calc(cr, uid, args, context=context)
#             self._apply_ir_rules(cr, uid, where_query, 'read', context=context)
#             from_clause, where_clause, where_clause_params = where_query.get_sql()
#             where_str = where_clause and (" WHERE %s AND " % where_clause) or ' WHERE '
#  
#             # search on the name of the contacts and of its company
#             search_name = name
#             if operator in ('ilike', 'like'):
#                 search_name = '%%%s%%' % name
#             if operator in ('=ilike', '=like'):
#                 operator = operator[1:]
#  
#             unaccent = get_unaccent_wrapper(cr)
#             query = """SELECT id
#                          FROM res_partner
#                       {where} ({email} {operator} {percent}
#                            OR {display_name} {operator} {percent}
#                            OR {reference} {operator} {percent})
#                            -- don't panic, trust postgres bitmap
#                      ORDER BY {display_name} {operator} {percent} desc,
#                               {display_name}
#                     """.format(where=where_str,
#                                operator=operator,
#                                email=unaccent('email'),
#                                display_name=unaccent('display_name'),
#                                reference=unaccent('ref'),
#                                percent=unaccent('%s'))
#  
#             where_clause_params += [search_name]*4
#             if limit:
#                 query += ' limit %s'
#                 where_clause_params.append(limit)
#             cr.execute(query, where_clause_params)
#             ids = map(lambda x: x[0], cr.fetchall())
#  
#             if ids:
#                 return self.name_get(cr, uid, ids, context)
#             else:
#                 return []
#         return super(ResPartner,self).name_search(cr, uid, name, args, operator=operator, context=context, limit=limit)
    
#     def name_get(self, cr, uid, ids, context=None):
#       
#         if context is None:
#             context = {}
#         if isinstance(ids, (int, long)):
#             ids = [ids]
#         res = []
#         types_dict = dict(self.fields_get(cr, uid, context=context)['type']['selection'])
#         for record in self.browse(cr, uid, ids, context=context):
#             name = record.name or ''
#             
#             if record.parent_id and not record.is_company:
#                 if not name and record.type in ['invoice', 'delivery', 'other']:
#                     name = types_dict[record.type]
#                 last_name = record.last_name if record.last_name else ''
#                 name = "%s %s, %s" % (name, last_name, record.parent_name)
#             
#             if not record.parent_id and not record.is_company:
#                 last_name = record.last_name if record.last_name else ''
#                 name = "%s %s" % (name,last_name)
#             
# #             if record.nomin_code:
# #                 name = "%s %s" % (record.nomin_code, name)
#             
#             if context.get('show_address_only'):
#                 name = self._display_address(cr, uid, record, without_company=True, context=context)
#             
#             if context.get('show_address'):
#                 name = name + "\n" + self._display_address(cr, uid, record, without_company=True, context=context)
#             
#             name = name.replace('\n\n','\n')
#             name = name.replace('\n\n','\n')
#             
#             if context.get('show_email') and record.email:
#                 name = "%s <%s>" % (name, record.email)
#             if context.get('html_format'):
#                 name = name.replace('\n', '<br/>')
#             res.append((record.id, name))
#         return res
#     
#     name = fields.Char(string='Name', select=True, track_visibility='always', reuuired=True)
    department_id = fields.Many2one('hr.department', string='Department')
#     property_account_payable_id = fields.Many2one('account.account', company_dependent=True,
#         string="Account Payable", oldname="property_account_payable",
#         domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False)]",
#         help="This account will be used instead of the default one as the payable account for the current partner")
#     property_account_receivable_id = fields.Many2one('account.account', company_dependent=True,
#         string="Account Receivable", oldname="property_account_receivable",
#         domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False)]",
#         help="This account will be used instead of the default one as the receivable account for the current partner")
    nomin_code = fields.Char(string='Nomin code',size=256, track_visibility='always', index=True, compute='_compute_code', store=True)
    last_name = fields.Char(string='Last name' ,size=128,track_visibility='always')
    code = fields.Char(string='Partner Code' ,size=128,track_visibility='always', index=True)
    registry_number = fields.Char(string='Registry Number' ,size=128,track_visibility='always')
    vat_date = fields.Date(string=u'НӨАТ төлөгч болсон огноо',track_visibility='always')
    is_vat = fields.Boolean(string='Is VAT',track_visibility='always')
    certification_number = fields.Char(string='Certification number' ,size=128,track_visibility='always')
    tax_number = fields.Char(string=u'Татвар төлөгчийн дугаар', size=256,track_visibility='always')

    @api.depends('vat','nomin_code','name',)
    def _compute_code(self):
        for item in self:
            if item.vat:
                item.nomin_code = item.vat
            else: 
                item.nomin_code = '1'
    
#     transport_id = fields.Many2many(comodel_name='partner.transport.category',relation='partner_partner_transport_category_relation',string=u'Тээвэрлэлтийн төрөл')
#     country_id = fields.Many2one('res.country', string='Country', ondelete='restrict',track_visibility='always')
#     email = fields.Char(string='Email',track_visibility='always', index=True)
#     phone = fields.Char(string='Phone',track_visibility='always', index=True)
#     fax = fields.Char(string='Fax',track_visibility='always')
#     mobile = fields.Char(string='Mobile',track_visibility='always', index=True)
#     supplier = fields.Boolean(string='Is a Vendor', help="Check this box if this contact is a vendor. If it's not checked, purchase people will not see it when encoding a purchase order.", default=True)
#     is_orignal = fields.Boolean(string='Is Original', default=False)
#     mapped_value = fields.Char(string='Map Nomin', size=128)
#     exempt_proj_for_vat= fields.Boolean(string='НӨАТ-с чөлөөлөгдөх төсөл болон ОУБ эсэх', default=False)
#     
#     
#     is_group_partner = fields.Boolean(string='Is Group Res Partner',compute= "_is_group_partner", default=False)
#     is_company_type = fields.Boolean(string='Is Group Company Partner',compute= "_is_company_type", default=False)
#     odoo15_sync = fields.Boolean(string="Odoo 15 sync",default=False)
#     #is_not_sync = fields.Boolean('Is not sync', readonly=True)
#     partner_id = fields.Many2one('draft.partner', string="Partner_id")
#     @api.constrains('code','nomin_code')
#     def _check_code(self):
#         if self.code:
#             self._cr.execute("select count(id) from res_partner where code = %s "
#                        "and id <> %s",(self.code,self.id))
#             fetched = self._cr.fetchone()
#             if fetched and fetched[0] and fetched[0] > 0:
#                 raise UserError(_('The code already exists'))
#         if self.nomin_code:
#             self._cr.execute("select count(id) from res_partner where nomin_code = %s "
#                        "and id <> %s",(self.nomin_code,self.id))
#             fetched = self._cr.fetchone()
#             if fetched and fetched[0] and fetched[0] > 0:
#                 raise UserError((u'%s номин кодтой харилцагч үүссэн байна!'%(self.code)))
#     
#     def _set_calendar_last_notif_ack(self, cr, uid, context=None):
#         partner = self.pool['res.users'].browse(cr, uid, uid, context=context).partner_id
#         self.write(cr, 1, partner.id, {'calendar_last_notif_ack': datetime.now()}, context=context)
#         return
# 
#     
# 
#     def _is_group_partner(self):
#         for partner in self:
# 
#             if self.env.user.has_group('nomin_base.group_partner_nomin_admin') or self.env.user.has_group('nomin_base.group_res_partner') :
#                 # self.update({'is_group_partner': True})
#                 partner.is_group_partner = True
# 
#     def _is_company_type(self):
#         for partner in self:
#             if partner.company_type == 'person':
#                 partner.is_company_type =True





