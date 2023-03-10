# -*- coding: utf-8 -*-
##############################################################################
#    Copyright (C) 2014-2020 Asterisk-technologies LLC Developer). All Rights Reserved
#
#    Address : Chingeltei District, Peace Tower, 205, Asterisk-technologies LLC Developer Ganzorig
#    Email : support@asterisk-tech.mn
#    Phone : 976 + 99241623
#
##############################################################################

import datetime,time
from datetime import timedelta
import io
import json
from PIL import Image
import re
from urllib import urlencode
import urllib2
from urlparse import urlparse

from openerp import api, fields, models, SUPERUSER_ID, _
from openerp.tools import image
from openerp.exceptions import Warning
from openerp.addons.website.models.website import slug
import base64
import logging
import werkzeug
import requests
from openerp.addons.web import http
from openerp.exceptions import AccessError, UserError
from openerp.http import request
from openerp.tools.translate import _
from cStringIO import StringIO
import cStringIO
from openerp import tools, api
import openerp
import openerp.tools
import uuid
PPG = 10
PPR = 10
_logger = logging.getLogger(__name__)

class answer_label(models.Model):
    _name='answer.label'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    question_id         = fields.Many2one('question.survey', string = "Question", ondelete="cascade")
    date_create         = fields.Date('Date Create', readonly=1, copy=False)
    token               = fields.Char('Identification token', readonly=1, required=1, copy=False, )
    answer_id           = fields.Many2one('question.label', string="Answer", copy=False, ondelete="restrict")
    ans_name            = fields.Char(related="answer_id.label_name", string = "Answer Name", copy=False)
    label_score         = fields.Float(string = "Answer Value", copy=False)
    
    _defaults = {
                    'token' : lambda s, cr, uid, c: uuid.uuid4().__str__(),
                    'date_create' : datetime.datetime.now()
                }
    
class question_label(models.Model):
    _name='question.label'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    question_id         = fields.Many2one('question.survey',string = "Question", ondelete="cascade")
    label_name          = fields.Char(string = "Answer Name", required=1, copy=False)
    label_score         = fields.Float(string = "Answer Value", copy=False)
    sequence            = fields.Integer(string="Label Sequence order")
    
class question_survey(models.Model):
    _name='question.survey'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    question            = fields.Char(string = "Question Name", required=1, copy=False)
    published_date      = fields.Date("Published Date")
    is_publish          = fields.Boolean(string = "Is Publish", default=False)
    label_ids           = fields.One2many('question.label', 'question_id', string="Types of answers", copy=True)
    answer_ids          = fields.One2many('answer.label', 'question_id', string="Answers", copy=True)
    
    
    @api.multi
    def website_publish_button(self):
        for main in self:
            if main.is_publish != True:
                self.write({'is_publish': True,'published_date': time.strftime('%Y-%m-%d %H:%M:%S')})
            else:
                self.write({'is_publish': False})
    
    @api.multi
    def unlink(self):
        for main in self:
            if main.is_publish != False:
                raise UserError(_(u'?????????????????????? ???????????????????? ???????????? ?????????????????? !'))
            else:
                return super(question_survey, self).unlink()
    
class survey_nomin(http.Controller):
         
    # AJAX submission of a page
#     @http.route('/save_partner/', type='http', auth='public', methods=['GET', 'POST'], website=True)
    @http.route(['/question/submit/<model("question.survey"):question>'],
                type='http', methods=['GET','POST'], auth='public', website=True)
    def submit(self, question, **post):
        _logger.debug('Incoming data: %s', post)
        cr, uid, context = request.cr, request.uid, request.context
#         print 'n\n\n\n\post', post
        survey_obj = request.registry['question.survey']
        answer_obj = request.registry['answer.label']
        user_input_id = answer_obj.create(cr, 1, {'question_id': question.id, 'ans_name':question.question}, context=context)
        
        vals = {}
        if user_input_id:
            vals.update({
                        'label_score': 1,
                        'answer_id': int(post['label_answer']),
                        })
        answer_obj.write(cr, 1, user_input_id, vals, context=context)
#         # Answer validation
        errors = {}
#         for question in questions:
#             answer_tag = "%s_%s_%s" % (survey.id, page_id, question.id)
#             errors.update(questions_obj.validate_question(cr, uid, question, post, answer_tag, context=context))
# 
        ret = {}
        if (len(errors) != 0):
            # Return errors messages to webpage
            ret['errors'] = errors
        else:
            # Store answers into database
#             user_input_obj = request.registry['survey.user_input']
#  
#             user_input_line_obj = request.registry['survey.user_input_line']
#             try:
#                 user_input_id = user_input_obj.search(cr, SUPERUSER_ID, [('token', '=', post['token'])], context=context)[0]
#             except KeyError:  # Invalid token
#                 return request.website.render("website.403")
#             user_input = user_input_obj.browse(cr, SUPERUSER_ID, user_input_id, context=context)
#             user_id = uid if user_input.type != 'link' else SUPERUSER_ID
#             for question in questions:
#                 answer_tag = "%s_%s_%s" % (survey.id, page_id, question.id)
#                 user_input_line_obj.save_lines(cr, user_id, user_input_id, question, post, answer_tag, context=context)
#  
#             go_back = post['button_submit'] == 'previous'
#             next_page, _, last = survey_obj.next_page(cr, uid, user_input, page_id, go_back=go_back, context=context)
#             vals = {'last_displayed_page_id': page_id}
#             if next_page is None and not go_back:
#                 vals.update({'state': 'done'})
#             else:
#                 vals.update({'state': 'skip'})
#             user_input_obj.write(cr, user_id, user_input_id, vals, context=context)
            ret['redirect'] = '/new_tenders'
#             if go_back:
#                 ret['redirect'] += '/prev'
        return json.dumps(ret)
    
    @http.route(['/question/results/<model("survey.survey"):survey>'],
                type='http', auth='user', website=True)
    def survey_reporting(self, survey, token=None, **post):
        '''Display survey Results & Statistics for given survey.'''
        result_template ='survey.result'
        current_filters = []
        filter_display_data = []
        filter_finish = False

        survey_obj = request.registry['survey.survey']
        if not survey.user_input_ids or not [input_id.id for input_id in survey.user_input_ids if input_id.state != 'new']:
            result_template = 'survey.no_result'
        if 'finished' in post:
            post.pop('finished')
            filter_finish = True
        if post or filter_finish:
            filter_data = self.get_filter_data(post)
            current_filters = survey_obj.filter_input_ids(request.cr, request.uid, survey, filter_data, filter_finish, context=request.context)
            filter_display_data = survey_obj.get_filter_display_data(request.cr, request.uid, filter_data, context=request.context)
        return request.website.render(result_template,
                                      {'survey': survey,
                                       'survey_dict': self.prepare_result_dict(survey, current_filters),
                                       'page_range': self.page_range,
                                       'current_filters': current_filters,
                                       'filter_display_data': filter_display_data,
                                       'filter_finish': filter_finish
                                       })
        
class tender_suggestion(models.Model):
    _name='tender.suggestion'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.depends('suggestion_image')
    def _compute_sugges_images(self):
        for rec in self:
            rec.suggestion_image_medium = tools.image_resize_image_medium(rec.suggestion_image)
            rec.suggestion_image_small = tools.image_resize_image_small(rec.suggestion_image)

    def _inverse_sugges_image_medium(self):
        for rec in self:
            rec.suggestion_image = tools.image_resize_image_big(rec.suggestion_image_medium)

    def _inverse_sugges_image_small(self):
        for rec in self:
            rec.suggestion_image = tools.image_resize_image_big(rec.suggestion_image_small)
    
    name            = fields.Char(string = "Suggestion Name", copy=False)
#     image           = fields.Binary("Image", attachment=True)
    is_publish      = fields.Boolean(string = "Is Publish", default=False)
    published_date  = fields.Date("Published Date")
    description     = fields.Html("Description")
    
    # image: all image fields are base64 encoded and PIL-supported
    suggestion_image = openerp.fields.Binary("Suggestion Image", attachment=True,
        help="This field holds the image used as avatar for this contact, limited to 1024x1024px")
    suggestion_image_medium = openerp.fields.Binary("Suggestion Medium-sized image",
        compute='_compute_sugges_images', inverse='_inverse_sugges_image_medium', store=True, attachment=True,
        help="Medium-sized image of this contact. It is automatically "\
             "resized as a 128x128px image, with aspect ratio preserved. "\
             "Use this field in form views or some kanban views.")
    suggestion_image_small = openerp.fields.Binary("Suggestion Small-sized image",
        compute='_compute_sugges_images', inverse='_inverse_sugges_image_small', store=True, attachment=True,
        help="Small-sized image of this contact. It is automatically "\
             "resized as a 64x64px image, with aspect ratio preserved. "\
             "Use this field anywhere a small image is required.")
    
    @api.multi
    def website_publish_button(self):
        for order in self:
            if order.is_publish != True:
                self.write({'is_publish': True,'published_date': time.strftime('%Y-%m-%d %H:%M:%S')})
            else:
                self.write({'is_publish': False})
    
    @api.multi
    def unlink(self):
        for main in self:
            if main.is_publish != False:
                raise UserError(_(u'?????????????????????? ???????????????????? ???????????? ?????????????????? !'))
            else:
                return super(tender_suggestion, self).unlink()
    
class portal_user_file(models.Model):
    _name='portal.user.file'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    name            = fields.Char(string = "Name", copy=False)
    is_publish      = fields.Boolean(string = "Is Publish", default=False)
    file_id         = fields.Many2one('ir.attachment', string="File Name", )
    published_date  = fields.Date("Published Date")
    description     = fields.Text("Description")

    @api.multi
    def website_publish_button(self):
        for order in self:
            if order.is_publish != True:
                self.write({'is_publish': True,'published_date': time.strftime('%Y-%m-%d %H:%M:%S')})
            else:
                self.write({'is_publish': False})
    
    @api.multi
    def unlink(self):
        for main in self:
            if main.is_publish != False:
                raise UserError(_(u'?????????????????????? ???????????????????? ???????????? ?????????????????? !'))
            else:
                return super(portal_user_file, self).unlink()
    
    
class ResPartnerRequest(http.Controller):


    # @http.route('/partner_request/<model("res.partner.request"):partner>/', type='http', auth='public', website=True)
    @http.route('/web/partner/register_request/', type='http', auth="public", methods=['GET', 'POST'],website=True)
    def res_partner_request(self, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        
        activities =request.httprequest.form.getlist('area_activity')
        
        new_list = [int(i) for i in activities]

        partner_search=request.env['res.partner.request'].sudo().search([('register_number','=',post['register_number']),('state','=','draft')])
        if partner_search:
            create_date = datetime.datetime.strptime(partner_search.create_date, '%Y-%m-%d %H:%M:%S')  + timedelta(hours=8)

            values={
            'create_date':create_date

            }
            return request.website.render("nomin_web.partner_register_request_exist",values)
        parent = False
        if post['partner_type']=='insurance_broker':
            partner_search=request.env['res.partner'].sudo().search(['|','|',('nomin_code','=',post['parent_register_number']),('registry_number','=',post['parent_register_number']),('code','=',post['parent_register_number'])],limit=1)
            if partner_search:
                parent = partner_search.id
            else:
                return request.website.render("nomin_web.partner_not_found")
        request.env['res.partner.request'].sudo().create({'name':post['company_name'],
            'register_number':post['register_number'],
            'tax_number':post['register_number'],
            'type':'create',
            'phone':post['phone'],
            'street':post['street'],
            'website':post['website'],
            'email':post['email'],
            'parent_id':parent,
            'partner_type':post['partner_type'],
            'description':post['description'],
            'area_ids':[(6,0,new_list)]
            })

        return request.website.render("nomin_web.partner_register_thanks")

    @http.route('/web/register/checkpartner', type='http', auth='public', website=True)
    def checkpartner(self, tax_number):
        partner_id = request.env['res.partner'].sudo().search([('registry_number','=',tax_number)])
        # if partner_id:
        #     return request.website.render("nomin_web.return_partner_data", {'login':partner_id.email,'email':partner_id.email})
        #     portal_user_id = request.env['res.users'].sudo().search([('partner_id','=',partner_id.id)])
        #     if portal_user_id:

        #         return request.website.render("nomin_web.return_partner_data", {'login':portal_user_id.login,'email':partner_id.email})

        get_request=requests.get("http://info.ebarimt.mn/rest/merchant/info?regno=%s"%(tax_number))
        data=''
        
        if get_request.status_code==200:
            data = get_request.json()['name']
        
        return data

      
    @http.route('/web/partner/search', type='http', auth="public", website=True)
    def webPartnerSearch(self, **kw):

        return request.website.render("nomin_web.partner_search")

    @http.route('/web/partner/check', type='http', auth="public",methods=['GET', 'POST'], website=True)
    def webcheckpartner(self, **post):
        values = {}
        portal_user_id= False

        partner_id = request.env['res.partner'].sudo().search([('registry_number','=',post['partner_search'])])
        
        if not partner_id:
            partner_id = request.env['res.partner'].sudo().search([('nomin_code','=',post['partner_search'])])

        if not partner_id:
            partner_id = request.env['res.partner'].sudo().search([('code','=',post['partner_search'])])

        if partner_id:
            if len(partner_id)>1:
                partner_id=partner_id[0]
            portal_user_id = request.env['res.users'].sudo().search([('partner_id','=',partner_id.id)])
            if len(portal_user_id)>1:
                portal_user_id = portal_user_id[0]
            # return request.website.render("nomin_web.return_partner_data", {'login':portal_user_id.login,'email':partner_id.email})
            if not portal_user_id:
                portal_user_id= False

        
            values = {
            'partner':partner_id,
            'partner_search':post['partner_search'],
            'portal':portal_user_id,
            }
            
                
            return request.website.render("nomin_web.return_check_partner",values)
           
        return request.website.render("nomin_web.partner_not_found")


    @http.route('/web/partner/editrequest', type='http', auth="public", methods=['GET','POST'], website=True)
    def partner_update_request(self, **post):
        
        
        if post['change_request']=='change_request':
            partner_id = request.env['res.partner'].sudo().search([('registry_number','=',post['partner_search'])])
            if not partner_id:
                partner_id = request.env['res.partner'].sudo().search([('nomin_code','=',post['partner_search'])])

            if not partner_id:
                partner_id = request.env['res.partner'].sudo().search([('code','=',post['partner_search'])])

            if len(partner_id)>1:
                partner_id = partner_id[0]
            if 'email' in post:
                
                    email=post['email']
            else:
                    email=partner_id.email
            if 'phonenumber' in post:
                
                    phonenumber = post['phonenumber']
            else:
                phonenumber = partner_id.phone


            vals = {
                    'partner': partner_id,     
                    'phonenumber':phonenumber,
                    'email':email
                    }
            
            return request.website.render("nomin_web.partner_edit_request", vals)
        if post['login_request']=='login_request':

            partner_search=request.env['res.partner.request'].sudo().search([('register_number','=',post['partner_search']),('state','=','draft')])
            if len(partner_search)>1:
                partner_search = partner_search[0]
           
            if partner_search:

                create_date = datetime.datetime.strptime(partner_search.create_date, '%Y-%m-%d %H:%M:%S')  + timedelta(hours=8)
                values={
                'create_date':create_date,
                }
                return request.website.render("nomin_web.partner_register_request_exist",values)

            partner_id = request.env['res.partner'].sudo().search([('registry_number','=',post['partner_search'])])
            if not partner_id:
                partner_id = request.env['res.partner'].sudo().search([('nomin_code','=',post['partner_search'])])

            if not partner_id:
                partner_id = request.env['res.partner'].sudo().search([('code','=',post['partner_search'])])

            
            if len(partner_id)>1:
                partner_id = partner_id[0]
            
            email=""
            phone =""
            if 'email' in post:
                email =post['email']
            else:
                email = partner_id.email
            if 'phonenumber' in post:
                phone =post['phonenumber']
            else:
                phone= partner_id.phone
            
            request_partner_id = request.env['res.partner.request'].sudo().search([('partner_id','=',partner_id.id),('state','=','confirmed')],limit = 1)
            partner_type = 'tender'
            if 'partner_type' in post and post['partner_type']:
                 partner_type = post['partner_type']
           
            if request_partner_id:
                partner_type = request_partner_id.partner_type
            partner_request=request.env['res.partner.request']
            partner_request.sudo().create({
            'name':partner_id.name,
            'register_number':partner_id.registry_number,
            'tax_number':partner_id.registry_number,
            'type':'portal',
            'partner_type':partner_type,
            'partner_id':partner_id.id,
            'phone':phone,
            'street':partner_id.street,
            'website':partner_id.website,
             'description':'?????????????? ?????? ???????????? ???????????? ?????????????? ??????????????',
            'email':email
            })

            return request.website.render("nomin_web.partner_register_thanks")


    @http.route('/web/partner/sendrequest', type='http', auth="public", methods=['GET','POST'], website=True)
    def partner_request_send(self, **post):
        # partner_id = request.env['res.partner'].sudo().search([('registry_number','=',post['registery_number'])])
        partner_id = request.env['res.partner'].sudo().search([('registry_number','=',post['certificate_no'])])[0]
        request_partner_id = request.env['res.partner.request'].sudo().search([('partner_id','=',partner_id.id),('state','=','confirmed')],limit = 1)
        partner_type = 'tender'
        if request_partner_id:
            partner_type = request_partner_id.partner_type
        partner_request=request.env['res.partner.request']
        partner_request.sudo().create({'name':post['company_name'],
            'register_number':post['certificate_no'],
            'tax_number':post['certificate_no'],
            'partner_id':partner_id.id,
            'phone':post['phonenumber'],
            'nomin_code':partner_id.nomin_code,
            'partner_type':partner_type,
            'type':'edit',
            'street':post['address'],
            # 'website':post['website'],
            'email':post['email'],
            'description':post['description']
            })


        return request.website.render("nomin_web.partner_register_thanks")

class dowload_file(http.Controller):
                    
    @http.route('/web/partner/register/', type='http', auth="public", website=True)
    def register_file(self, **kw):
        # cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        # portal_file=request.registry('portal.user.file')
        # file_ids = []
        # files= ''
        # file_ids = portal_file.search(request.cr, SUPERUSER_ID, file_ids)
        # portal_files = portal_file.browse(request.cr, SUPERUSER_ID, file_ids)
        
        # if portal_files:
        #     files = portal_files[0]
        # # partner = request.env['res.partner'].sudo().search([('registry_number','=',2708892)])
        # # values = {
        # #           'portal_files': files,
        # #           'partner':partner,
        # #           }
        activities = request.env['area.activity'].sudo().search([('id','!=',0)])
        values  ={
        'activities':activities,
        # 'partner_type':'insurance_broker',
        }
        return request.website.render("nomin_web.nomin_partner_register",values)
        # return request.website.render("nomin_web.portal_register_file", values)


        


    @http.route('''/register/file/<model("portal.user.file"):portal>/download''', type='http', auth="public", website=True)
    def register_file_download(self, portal):
        if portal.file_id.sudo():
            filecontent = base64.b64decode(portal.file_id.sudo().datas)
            disposition = 'attachment; filename=%s.doc' % werkzeug.urls.url_quote(portal.file_id.sudo().name)
            return request.make_response(
                filecontent,
                [('Content-Type', 'application/pdf'),
                 ('Content-Length', len(filecontent)),
                 ('Content-Disposition', disposition)])
        elif request.session.uid:
            return werkzeug.utils.redirect('/web?redirect=/web')
        return request.website.render("website.403")
 
    @http.route([
        '/portal/download',
    ], type='http', auth='public')
    def download_file(self, attachment_id):
        # Check if this is a valid attachment id
        attachment = request.env['ir.attachment'].sudo().search_read(
            [('id', '=', int(attachment_id))],
            ["name", "datas", "file_type", "res_model", "res_id", "type", "url"]
        )
        if attachment:
            attachment = attachment[0]
        else:
            return redirect(self.orders_page)


        # Check if the user has bought the associated product
#         res_model = attachment['res_model']
#         res_id = attachment['res_id']
#         purchased_products = request.env['account.invoice.line'].get_digital_purchases(request.uid)
# 
#         if res_model == 'product.product':
#             if res_id not in purchased_products:
#                 return redirect(self.orders_page)
# 
#         # Also check for attachments in the product templates
#         elif res_model == 'product.template':
#             P = request.env['product.product']
#             template_ids = map(lambda x: P.browse(x).product_tmpl_id.id, purchased_products)
#             if res_id not in template_ids:
#                 return redirect(self.orders_page)
# 
#         else:
#             return redirect(self.orders_page)

        # The client has bought the product, otherwise it would have been blocked by now
        if attachment["type"] == "url":
            if attachment["url"]:
                return redirect(attachment["url"])
            else:
                return request.not_found()
        elif attachment["datas"]:
            data = StringIO(base64.standard_b64decode(attachment["datas"]))
            return http.send_file(data, filename=attachment['name'], as_attachment=True)
        else:
            return request.not_found()
  
class suggestion_list(http.Controller):
    
    @http.route(['/suggestion/',
                 '/suggestion/page/<int:page>'], 
                type='http', auth="public", website=True)
    def suggestion_list(self, page=1, ppg=False, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG
            
        suggestion=request.registry('tender.suggestion')
        nominsuggestion= ''
        
        tender_type_ids = request.registry('tender.type').search(cr, SUPERUSER_ID, [], context=context)
        tender_types = request.registry('tender.type').browse(cr, SUPERUSER_ID, tender_type_ids, context) 
        
        sugges= ''
        sugges_ids = suggestion.search(request.cr, SUPERUSER_ID, [('is_publish','=',True)], limit=2, order="published_date desc")
        sugges = suggestion.browse(request.cr, SUPERUSER_ID, sugges_ids)
        
        surveys=request.registry('question.survey')
        s_ids = []
        survey_question= ''
        survey_ids = surveys.search(request.cr, SUPERUSER_ID, [('is_publish','=',True)], order="published_date desc")
        if survey_ids:
            survey_question = surveys.browse(request.cr, SUPERUSER_ID, survey_ids[0])
        
        
        query = "select question.id as qid, question.question as question, answer_id, label.label_name, count(answer.answer_id) \
                from answer_label as answer, question_label as label, question_survey as question \
                where label.id=answer.answer_id group by answer_id, label.label_name, question.id"
        
        cr.execute(query)
        records = cr.dictfetchall()
        question_dict = {}
        answer_dict = {}
        sum_dict = {}
        results = {}
        for question in records:
            if question['qid'] not in question_dict:
                question_dict[question['qid']] = {'question' : question['question']}
                
            if question['qid'] not in answer_dict:
                answer_dict[question['qid']] = {'answers' : [question['label_name']],
                                                'count' : [question['count']]}
            else:
                answer_dict[question['qid']]['answers'].append(question['label_name'])
                answer_dict[question['qid']]['count'].append(question['count'])
            
            
            
        sumquery = "select question.id as qid, question.question as question, count(answer.answer_id) total \
                from question_survey as question, answer_label as answer \
                where question.is_publish = true and question.id = answer.question_id group by question.id"
#         print 'n\n\n\n\\n\nsumquery', sumquery
        cr.execute(sumquery)
        sumrecords = cr.dictfetchall()
        for sum in sumrecords:
            if sum['qid'] not in sum_dict:
                sum_dict[sum['qid']] = {
                                        'answered' : sum['total']
                                        }
        
        url = "/suggestion"
        suggestion_count = suggestion.search_count(cr, SUPERUSER_ID, [('is_publish','=',True)], context=context)
        pager = request.website.pager(url=url, total=suggestion_count, page=page, step=ppg, scope=7, url_args=post)
        nominsugges_ids = suggestion.search(request.cr, SUPERUSER_ID, [('is_publish','=',True)], limit=ppg, offset=pager['offset'], order="published_date desc")
        nominsuggestion = suggestion.browse(request.cr, SUPERUSER_ID, nominsugges_ids)
        
        values = {
                  'tender_types': tender_types,
                  'nominsuggestion': nominsuggestion,
                  'suggestions': sugges,
                  'survey_question': survey_question or '',
                  'question_dict': question_dict,
                  'answer_dict': answer_dict,
                  'sum_dict': sum_dict,
                  'pager': pager,
                  }
        return request.website.render("nomin_web.tender_suggestion_document", values)
        
    @http.route([
        '/suggestion/<model("tender.suggestion"):currsuggest>', 
        ], type='http', auth="public", website=True)
    def suggestion_details(self, currsuggest=None, **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        suggestion=request.registry('tender.suggestion')
        values = {}
        sugges= ''
        sugges_ids = suggestion.search(request.cr, SUPERUSER_ID, [('is_publish','=',True)], order="published_date desc", limit=2)
        sugges = suggestion.browse(request.cr, SUPERUSER_ID, sugges_ids)
        
        tender_type_ids = request.registry('tender.type').search(cr, SUPERUSER_ID, [], context=context)
        tender_types = request.registry('tender.type').browse(cr, SUPERUSER_ID, tender_type_ids, context) 
        
        if currsuggest:
            curr_suggest = currsuggest[0]
        
        surveys=request.registry('question.survey')
        s_ids = []
        survey_question= ''
        survey_ids = surveys.search(request.cr, SUPERUSER_ID, [('is_publish','=',True)], order="published_date desc")
        if survey_ids:
            survey_question = surveys.browse(request.cr, SUPERUSER_ID, survey_ids[0])
        
        
        query = "select question.id as qid, question.question as question, answer_id, label.label_name, count(answer.answer_id) \
                from answer_label as answer, question_label as label, question_survey as question \
                where label.id=answer.answer_id group by answer_id, label.label_name, question.id"
        
        cr.execute(query)
        records = cr.dictfetchall()
        question_dict = {}
        answer_dict = {}
        sum_dict = {}
        results = {}
        for question in records:
            if question['qid'] not in question_dict:
                question_dict[question['qid']] = {'question' : question['question']}
                
            if question['qid'] not in answer_dict:
                answer_dict[question['qid']] = {'answers' : [question['label_name']],
                                                'count' : [question['count']]}
            else:
                answer_dict[question['qid']]['answers'].append(question['label_name'])
                answer_dict[question['qid']]['count'].append(question['count'])
            
            
            
        sumquery = "select question.id as qid, question.question as question, count(answer.answer_id) total \
                from question_survey as question, answer_label as answer \
                where question.is_publish = true and question.id = answer.question_id group by question.id"
#         print 'n\n\n\n\\n\nsumquery', sumquery
        cr.execute(sumquery)
        sumrecords = cr.dictfetchall()
        for sum in sumrecords:
            if sum['qid'] not in sum_dict:
                sum_dict[sum['qid']] = {
                                        'answered' : sum['total']
                                        }
        
        values = {
                  'currsuggest': curr_suggest,
                  'suggestions': sugges,
                  'tender_types':tender_types,
                  'survey_question': survey_question or '',
                  'question_dict': question_dict,
                  'answer_dict': answer_dict,
                  'sum_dict': sum_dict,
                  }
        
        return request.website.render("nomin_web.tender_current_suggestion", values)
    
class partner_file(models.Model):
    _name = "res.partner.file"
    _description = "Partner FIle Type"
    
    partner_id = fields.Many2one('res.partner', string = "Partner")
    attachment_id = fields.Many2one('ir.attachment', string = "Attachment")
    type_id = fields.Many2one('res.partner.file.type', string = 'File Type')
    
    
class partner_file_type(models.Model):
    _name = "res.partner.file.type"
    
    name = fields.Char(string = 'File Type')
    
    
    
class res_partner_extra(models.Model):
    _name="res.partner"
    _inherit = 'res.partner'
    _description = 'Basic registration'
    
    @api.model
    def _count_document(self):
        return 1
    
    register_number = fields.Char('Register Number', translate=False, required=False, help="")
    company_number = fields.Char('Company Number', translate=False, required=False, help="company")

    tender_type_ids = fields.Many2many('tender.type', 'purchase_tender_type_res_partner_rel', 'partner_id', 'type_id', string = "Tender Bid Type")
    describtion = fields.Text(string = "Partner Describtion")
    document_count = fields.Integer(string='Document Count', default=_count_document)


    

