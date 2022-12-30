# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from unittest import result
from lxml import etree
import math
import pytz
import threading
import urlparse
import openerp
from openerp import tools, api
from openerp.osv import osv, fields
from openerp.osv.expression import get_unaccent_wrapper
from openerp.tools.translate import _
from openerp.exceptions import UserError
from urlparse import urljoin
import werkzeug
from datetime import datetime



class ResCompany(osv.Model):
    _inherit = 'res.company'
    _description = 'Company'
    
    @api.depends('blank_header_image')
    def _compute_images(self):
        for rec in self:
            rec.blank_header_image_medium = tools.image_resize_image_medium(rec.blank_header_image)
            rec.blank_header_image_small = tools.image_resize_image_small(rec.blank_header_image)

    def _inverse_image_medium(self):
        for rec in self:
            rec.blank_header_image = tools.image_resize_image_big(rec.blank_header_image_medium)

    def _inverse_image_small(self):
        for rec in self:
            rec.blank_header_image = tools.image_resize_image_big(rec.blank_header_image_small)
    
    # image: all image fields are base64 encoded and PIL-supported
    blank_header_image = openerp.fields.Binary("Blank Header Image", attachment=True,
        help="This field holds the image used as avatar for this contact, limited to 1024x1024px")
    blank_header_image_medium = openerp.fields.Binary("Medium-sized image",
        compute='_compute_images', inverse='_inverse_image_medium', store=True, attachment=True,
        help="Medium-sized image of this contact. It is automatically "\
             "resized as a 128x128px image, with aspect ratio preserved. "\
             "Use this field in form views or some kanban views.")
    blank_header_image_small = openerp.fields.Binary("Small-sized image",
        compute='_compute_images', inverse='_inverse_image_small', store=True, attachment=True,
        help="Small-sized image of this contact. It is automatically "\
             "resized as a 64x64px image, with aspect ratio preserved. "\
             "Use this field anywhere a small image is required.")
    
    @api.depends('blank_header_en_image')
    def _compute_en_images(self):
        for rec in self:
            rec.blank_header_en_image_medium = tools.image_resize_image_medium(rec.blank_header_en_image)
            rec.blank_header_en_image_small = tools.image_resize_image_small(rec.blank_header_en_image)

    def _inverse_image_en_medium(self):
        for rec in self:
            rec.blank_header_en_image = tools.image_resize_image_big(rec.blank_header_en_image_medium)

    def _inverse_image_en_small(self):
        for rec in self:
            rec.blank_header_en_image = tools.image_resize_image_big(rec.blank_header_en_image_small)
            
        # image: all image fields are base64 encoded and PIL-supported
    blank_header_en_image = openerp.fields.Binary("Blank Header English Image", attachment=True,
        help="This field holds the image used as avatar for this contact, limited to 1024x1024px")
    blank_header_en_image_medium = openerp.fields.Binary("Medium-sized image",
        compute='_compute_en_images', inverse='_inverse_image_en_medium', store=True, attachment=True,
        help="Medium-sized image of this contact. It is automatically "\
             "resized as a 128x128px image, with aspect ratio preserved. "\
             "Use this field in form views or some kanban views.")
    blank_header_en_image_small = openerp.fields.Binary("Small-sized image",
        compute='_compute_en_images', inverse='_inverse_image_en_small', store=True, attachment=True,
        help="Small-sized image of this contact. It is automatically "\
             "resized as a 64x64px image, with aspect ratio preserved. "\
             "Use this field anywhere a small image is required.")
    
    
    ticket_email = openerp.fields.Char(string='Ticket Email Incoming/Outgoing', size=64)
    partner_code =openerp.fields.Char(string="Partner code",required=True)
    domain_name =openerp.fields.Char(string="Domain name",required=True)
    company_history_ids = openerp.fields.One2many('contract.company.history','company_id', string='company history')
    location_id = openerp.fields.Many2one('hr.employee.location', string='Компанийн байрших хот')

    def create(self, cr, uid, vals, context=None):
        
        if not vals.get('name', False) or vals.get('partner_id', False):
            self.cache_restart(cr)
            result =  super(ResCompany, self).create(cr, uid, vals, context=context)
            company_obj = self.pool.get('res.company').browse(cr, uid,result)
            for his in company_obj.company_history_ids:
                if not his.end_date:
                    his.write({'end_date':datetime.now()})
            history_new = self.pool.get('contract.company.history')
            print '\n\n aaaaaaaaaa ' , history_new
            history_new.create(cr, uid,{
                        'company_id': company_obj.id,
                        'start_date': datetime.now(),
                        'name'  : company_obj.name ,
            })
            return result
        if not vals.get('partner_id'):
            obj_partner = self.pool.get('res.partner')
            partner_id = obj_partner.create(cr, uid, {
                'name': vals['name'],
                'is_company': True,
                'image': vals.get('logo', False),
                'customer': False,
                'email': vals.get('email'),
                'nomin_code':vals.get('partner_code'),
                'code':vals.get('partner_code'),
                'phone': vals.get('phone'),
                'website': vals.get('website'),
                'vat': vals.get('vat'),
            }, context=context)
            vals.update({'partner_id': partner_id})
        self.cache_restart(cr)
        company_id = super(ResCompany, self).create(cr, uid, vals, context=context)
        obj_partner.write(cr, uid, [partner_id], {'company_id': company_id}, context=context)
        return company_id
    
    @api.multi
    def write(self, vals):
        if vals.get('name'):
            history_obj = self.env['contract.company.history'].search([('start_date','=',openerp.fields.Date.context_today(self)),('company_id','=',self.id)])
            for history in history_obj:
                history.write({
                                'name' : vals.get('name') ,
                            })
            if not history_obj:
                for his in self.company_history_ids:
                    if not his.end_date:
                        his.write({'end_date':openerp.fields.Date.context_today(self)})
                history_new = self.env['contract.company.history']
                history_new.create({
                            'company_id' : self.id,
                            'start_date' : openerp.fields.Date.context_today(self),
                            'name'      : vals.get('name'),
                })
        return super(ResCompany, self).write(vals)
        

class ContractCompanyHistory(osv.Model):
    _name = 'contract.company.history'
    _descpription = 'Contract company history'
    _order = 'start_date desc'

    name = openerp.fields.Text(string="Company name")
    company_id = openerp.fields.Many2one('res.company',string="Department" )
    start_date = openerp.fields.Date(string="Start date")
    end_date = openerp.fields.Date(string="End date")


class wizard(osv.osv_memory):
    """
        A wizard to manage the creation/removal of portal users.
    """
    _inherit = 'portal.wizard'
    _description = 'Portal Access Management'

    def onchange_portal_id(self, cr, uid, ids, portal_id, context=None):
        # for each partner, determine corresponding portal.wizard.user records
        res_partner = self.pool.get('res.partner')
        partner_ids = context and context.get('active_ids') or []
        contact_ids = set()
        user_changes = []
        for partner in res_partner.browse(cr, 1, partner_ids, context):
            for contact in partner.child_ids:
                # make sure that each contact appears at most once in the list
                if contact.id not in contact_ids:
                    contact_ids.add(contact.id)
                    in_portal = False
                    if contact.user_ids:
                        in_portal = portal_id in [g.id for g in contact.user_ids[0].groups_id]
                    user_changes.append((0, 0, {
                        'partner_id': contact.id,
                        'email': contact.email,
                        'in_portal': in_portal,
                    }))
            for contact in partner:
                # make sure that each contact appears at most once in the list
                if contact.id not in contact_ids:
                    contact_ids.add(contact.id)
                    in_portal = False
                    if contact.user_ids:
                        in_portal = portal_id in [g.id for g in contact.user_ids[0].groups_id]
                    user_changes.append((0, 0, {
                        'partner_id': contact.id,
                        'email': contact.email,
                        'in_portal': in_portal,
                    }))
        return {'value': {'user_ids': user_changes}}


class portal_user_wizard(osv.osv_memory):
    _inherit = 'portal.wizard.user'


    def onchange_portal_id(self, cr, uid, ids, portal_id, context=None):
        # for each partner, determine corresponding portal.wizard.user records
        res_partner = self.pool.get('res.partner')
        partner_ids = context and context.get('active_ids') or []
        contact_ids = set()
        user_changes = []
        for partner in res_partner.browse(cr, SUPERUSER_ID, partner_ids, context):
            for contact in partner.child_ids:
                # make sure that each contact appears at most once in the list
                if contact.id not in contact_ids:
                    contact_ids.add(contact.id)
                    in_portal = False
                    if contact.user_ids:
                        in_portal = portal_id in [g.id for g in contact.user_ids[0].groups_id]
                    user_changes.append((0, 0, {
                        'partner_id': contact.id,
                        'email': contact.email,
                        'in_portal': in_portal,
                    }))
            for contact in partner:
                # make sure that each contact appears at most once in the list
                if contact.id not in contact_ids:
                    contact_ids.add(contact.id)
                    in_portal = False
                    if contact.user_ids:
                        in_portal = portal_id in [g.id for g in contact.user_ids[0].groups_id]
                    user_changes.append((0, 0, {
                        'partner_id': contact.id,
                        'email': contact.email,
                        'in_portal': in_portal,
                    }))
        return {'value': {'user_ids': user_changes}}


    def _send_email(self, cr, uid, ids, context=None):
        """ send notification email to a new portal user
            @param wizard_user: browse record of model portal.wizard.user
            @return: the id of the created mail.mail record
        """
        wizard_user = self.browse(cr, uid, ids, context=context)
        res_partner = self.pool['res.partner']
        this_user = self.pool.get('res.users').browse(cr, 1, uid, context)
        if not this_user.email:
            raise UserError(_('You must have an email address in your User Preferences to send emails.'))

        # determine subject and body in the portal user's language
        user = wizard_user.user_id
        context = dict(context or {}, lang=user.lang)
        ctx_portal_url = dict(context, signup_force_type_in_url='')
        portal_url = res_partner._get_signup_url_for_action_partner(cr, uid,
                                                            [user.partner_id.id],
                                                            context=ctx_portal_url)[user.partner_id.id]
        res_partner.signup_prepare(cr, uid, [user.partner_id.id], context=context)

        context.update({'dbname': cr.dbname, 'portal_url': portal_url})
        template_id = self.pool['ir.model.data'].xmlid_to_res_id(cr, uid, 'portal.mail_template_data_portal_welcome')
        if template_id:
            self.pool['mail.template'].send_mail(cr, uid, template_id, wizard_user.id, force_send=True, context=context)
        else:
            _logger.warning("No email template found for sending email to the portal user")
        return True
class res_partner_osv(osv.osv):
    _inherit = 'res.partner'

    def _get_signup_url_for_action_partner(self, cr, uid, ids, action=None, view_type=None, menu_id=None, res_id=None, model=None, context=None):
        """ generate a signup url for the given partner ids and action, possibly overriding
            the url state components (menu_id, id, view_type) """
        if context is None:
            context= {}
        res = dict.fromkeys(ids, False)
        base_url = self.pool.get('ir.config_parameter').get_param(cr, uid, 'procurement.base.url')
        for partner in self.browse(cr, uid, ids, context):
            # when required, make sure the partner has a valid signup token
            if context.get('signup_valid') and not partner.user_ids:
                self.signup_prepare(cr, uid, [partner.id], context=context)

            route = 'login'
            # the parameters to encode for the query
            query = dict(db=cr.dbname)
            signup_type = context.get('signup_force_type_in_url', partner.signup_type or '')
            if signup_type:
                route = 'reset_password' if signup_type == 'reset' else signup_type

            if partner.signup_token and signup_type:
                query['token'] = partner.signup_token
            elif partner.user_ids:
                query['login'] = partner.user_ids[0].login
            else:
                continue        # no signup token, no user, thus no signup url!

            fragment = dict()
            base = '/web#'
            if action == '/mail/view':
                base = '/mail/view?'
            elif action:
                fragment['action'] = action
            if view_type:
                fragment['view_type'] = view_type
            if menu_id:
                fragment['menu_id'] = menu_id
            if model:
                fragment['model'] = model
            if res_id:
                fragment['res_id'] = res_id

            if fragment:
                query['redirect'] = base + werkzeug.url_encode(fragment)

            res[partner.id] = urljoin(base_url, "/web/%s?%s" % (route, werkzeug.url_encode(query)))
        return res
    def _get_procurement_signup_url(self, cr, uid, ids, name, arg, context=None):
        """ proxy for function field towards actual implementation """
        return self._get_signup_url_for_action_partner(cr, uid, ids, context=context)

    _columns ={
        'procurement_signup_url':fields.function(_get_procurement_signup_url, type='char', string='Signup URL'),
    }