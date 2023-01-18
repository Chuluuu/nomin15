# -*- coding: utf-8 -*-
import base64
import logging
import werkzeug
import werkzeug.utils
import werkzeug.wrappers
import time
import xml.etree.ElementTree as ET
from odoo import SUPERUSER_ID
from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import Website
from odoo import _, http

_logger = logging.getLogger(__name__)

try:
    from odoo.addons.crm.validate_email import validate_email
except ImportError:
    _logger.debug("Cannot import `validate_email`.")
from io import StringIO
PPG = 6
PPR = 10


class NominTender(http.Controller):
    _results_per_page = 10
    _max_text_content_len=500
    _text_segment_back=100
    _text_segment_forward=300
    _min_search_len=3
    _search_on_pages=True
    _case_sensitive=False
    _search_advanced=False
    variables=None
    bidid=None
    partner_id=0
    
    @http.route('''/tender_detail/<model("tender.work.task"):document>/download''', type='http', auth="public", website=True)
    def tender_works_download(self, document):
        if document.tender_work_document_id and request.session.uid:
            filecontent = base64.b64decode(document.tender_work_document_id.sudo().datas)
            disposition = 'attachment; filename=%s.pdf' % werkzeug.urls.url_quote(document.tender_work_document_id.sudo().name)
            return request.make_response(
                filecontent,
                [('Content-Type', 'application/pdf'),
                 ('Content-Length', len(filecontent)),
                 ('Content-Disposition', disposition)])
        elif not request.session.uid:
            return werkzeug.utils.redirect('/web?redirect=/tender_details/%s' % (document.tender_id.id))
        return request.website.render("website.403")
 
    @http.route([
        '/document_download',
    ], type='http', auth='public')
    def download_attachment(self, attachment_id):
        # Check if this is a valid attachment id
        attachment = request.env['ir.attachment'].sudo().search_read(
            [('id', '=', int(attachment_id))],
            ["name", "datas", "file_type", "res_model", "res_id", "type", "url"]
        )
        if attachment:
            attachment = attachment[0]
        else:
            return http.local_redirect(self.orders_page)
 
        if attachment["type"] == "url":
            if attachment["url"]:
                return http.local_redirect(attachment["url"])
            else:
                return request.not_found()
        elif attachment["datas"]:
            data = StringIO(base64.standard_b64decode(attachment["datas"]))
            return http.send_file(data, filename=attachment['name'], as_attachment=True)
        else:
            return request.not_found()

    @http.route([
        '/page/contactus',
        ], type='http', auth="public", website=True)
    def contactus(self, page=1, **post):
        suggestion=request.env['tender.suggestion']
        values = {}
        sugges= ''
        sugges = suggestion.sudo().search([('is_publish','=',True)], order="published_date desc", limit=2)
        
        tender_types = request.env['tender.type'].sudo().search([])
        
        surveys=request.env['question.survey']
        s_ids = []
        survey_question= ''
        survey_question = surveys.sudo().search([('is_publish','=',True)], order="published_date desc")
        
        
        query = "select question.id as qid, question.question as question, answer_id, label.label_name, count(answer.answer_id) \
                from answer_label as answer, question_label as label, question_survey as question \
                where label.id=answer.answer_id group by answer_id, label.label_name, question.id"
        
        request.env.cr.execute(query)
        records = request.env.cr.dictfetchall()
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
        request.env.cr.execute(sumquery)
        sumrecords = request.env.cr.dictfetchall()
        for sum in sumrecords:
            if sum['qid'] not in sum_dict:
                sum_dict[sum['qid']] = {
                                        'answered' : sum['total']
                                        }
                
        values ={
                  'suggestions': sugges,
                  'tender_types':tender_types,
                  'survey_question': survey_question or '',
                  'question_dict': question_dict,
                  'answer_dict': answer_dict,
                  'sum_dict': sum_dict,
                }
        return request.website.render("nomin_web.nomin_contactus_form", values)
     
    @http.route([
        '/new_tenders/',
        '/new_tenders/page/<int:page>', 
        ], type='http', auth="public", website=True)
    def new_tenders(self, page=1, ppg=False, **post):
        user_id = user = request.env['res.users'].sudo().browse(request.uid)
        
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG
        
        suggestion=request.env['tender.suggestion']
        tender_obj=request.env['tender.tender']
        values = {}
        sugges= ''
        domain = [('is_publish','=',True),('state','in',['published','bid_expire'])]
        domainok = [('is_publish','=',True),('is_open_tender','=',True),('state','in',['published','bid_expire'])]
        sugges = suggestion.sudo().search([('is_publish','=',True)], order="published_date desc", limit=2)
        url = "/new_tenders"
        tender_types = request.env['tender.type'].sudo().search([])
#         product_count = product_obj.search_count(cr, uid, domain, context=context)
        if (request.uid!=3):
            tender_count = tender_obj.sudo().search_count(domain)
        else:
            tender_count = tender_obj.sudo().search_count(domainok)
        
        pager = request.website.pager(url=url, total=tender_count, page=page, step=ppg, scope=7, url_args=post)
        if (request.uid!=3):
            tenders = tender_obj.sudo().search([('is_publish','=',True),('state','in',['published', 'bid_expire'])], limit=ppg, offset=pager['offset'], order='published_date desc',)
        else:
            tenders = tender_obj.sudo().search([('is_publish','=',True),('is_open_tender','=',True),('state','in',['published', 'bid_expire'])], limit=ppg, offset=pager['offset'], order='published_date desc')
#         tender_ids = tender_obj.search(cr, uid, domain, limit=ppg, offset=pager['offset'], order='published_date desc', context=context)
        # tenders = tender_obj.browse(cr, SUPERUSER_ID, tender_ids, context=context)
        
        tender_tender_ids = []
        for tender in tenders:
            if user_id.partner_id.id in tender.requirement_partner_ids.ids and tender.is_open_tender == False:
                tender_tender_ids.append(tender)
            if tender.is_open_tender == True:
                tender_tender_ids.append(tender)
        
        surveys=request.env['question.survey']
        s_ids = []
        survey_question= ''
        survey_question = surveys.sudo().search( [('is_publish','=',True)], order="published_date desc")
        
        
        query = "select question.id as qid, question.question as question, answer_id, label.label_name, count(answer.answer_id) \
                from answer_label as answer, question_label as label, question_survey as question \
                where label.id=answer.answer_id group by answer_id, label.label_name, question.id"
        
        request.env.cr.execute(query)
        records = request.env.cr.dictfetchall()
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

        request.env.cr.execute(sumquery)
        sumrecords = request.env.cr.dictfetchall()
        for sum in sumrecords:
            if sum['qid'] not in sum_dict:
                sum_dict[sum['qid']] = {
                                        'answered' : sum['total']
                                        }

        values ={
                  'suggestions': sugges,
                  'survey_question': survey_question or '',
                  'question_dict': question_dict,
                  'answer_dict': answer_dict,
                  'sum_dict': sum_dict,
                  'new_tenders':tender_tender_ids,
                  'tender_types':tender_types,
                  'pager': pager
                  
                }

        return request.website.render("nomin_web.new_tender_list", values)
    
    @http.route([
        '/subscribe/',
        ], type='http', auth="public", website=True)
    def subscribe_users(self, ppg=False, page=1, **post):
        user_id = user = request.env['res.users'].sudo().browse(request.uid)

        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG
        
        values = {}
        
        suggestion=request.env['tender.suggestion']
        sugges = suggestion.sudo().search([('is_publish','=',True)], order="published_date desc", limit=2)
        
        surveys=request.env['question.survey']
        s_ids = []
        survey_question = surveys.sudo().search([('is_publish','=',True)], order="published_date desc")
        
        
        query = "select question.id as qid, question.question as question, answer_id, label.label_name, count(answer.answer_id) \
                from answer_label as answer, question_label as label, question_survey as question \
                where label.id=answer.answer_id group by answer_id, label.label_name, question.id"
        
        request.env.cr.execute(query)
        records = request.env.cr.dictfetchall()
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

        request.env.cr.execute(sumquery)
        sumrecords = request.cr.dictfetchall()
        for sum in sumrecords:
            if sum['qid'] not in sum_dict:
                sum_dict[sum['qid']] = {
                                        'answered' : sum['total']
                                        }
        
        tender_obj = request.env['tender.tender']
        subscribe = request.env['subscribe.users']
        
        number1 = 1
        number2 = 2
        number3 = 3
        number4 = 4
        number5 = 5
        fix=True
        type_ids = []
 
        if 'type_id-%d'%number1 in post:
            type_ids.append(int(post['type_id-%d'%number1]))
        if 'type_id-%d'%number2 in post:
            type_ids.append(int(post['type_id-%d'%number2]))
        if 'type_id-%d'%number3 in post:
            type_ids.append(int(post['type_id-%d'%number3]))
        if 'type_id-%d'%number4 in post:
            type_ids.append(int(post['type_id-%d'%number4]))
        if 'type_id-%d'%number5 in post:
            type_ids.append(int(post['type_id-%d'%number5]))
                
        if not type_ids:
            return http.local_redirect('/new_tenders')
        elif type_ids and post['email'] == '':
            return http.local_redirect('/new_tenders')
        else:
            sub_user = subscribe.sudo().search([('email', '=', post['email'])])
            if sub_user:
                sub_user.sudo().write({'tender_type_ids': [(6, 0, [type_ids])]
                                                    })
                return http.local_redirect('/new_tenders')
            else:
                subscribe.sudo().create({'tender_type_ids': [(6, 0, [type_ids])],'email': post['email']})
                return http.local_redirect('/new_tenders')
    
    def _get_search_domain(self, category):
        domain = [('is_publish','=',True)]
                    
        if (request.uid==3):
            domain += [
                        ('is_open_tender','=',True)
                        ]
        if category:
            domain += [('type_id', '=', int(category))]
            
        return domain


    @http.route([
        '/tender_list',
        '/tender_list/page/<int:page>',
        '/tender_list/category_id/link_<model("tender.type"):category>', 
        '/tender_list/category_id/link_<model("tender.type"):category>/page/<int:page>', 
        ], type='http', auth="public", website=True)
    def tenders(self, page=1, category=None, ppg=False, **post):
        user_id = user = request.env['res.users'].sudo().browse(request.uid)
        
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG
        
        domain = self._get_search_domain(category)
        
        self.partner_id=user_id.partner_id[0].id#partner_id of online user

        tender_obj = request.env['tender.tender']
        tender_type_obj = request.env['tender.type']
        tender_documents=request.env['res.partner.documents']
        url = "/tender_list"
        values = {}
        tender_count = tender_obj.search_count(domain)
        pager = request.website.pager(url=url, total=tender_count, page=page, step=ppg, scope=7, url_args=post)
        tenders = tender_obj.search( domain, limit=ppg, offset=pager['offset'], order='name desc')
        
#         print '\n\n\n\n\\n\n\ntender_count', tender_count
        if category:
            url = "/tender_list/category_id/link_%s" %int(category)
            tender_count = tender_obj.search_count(domain)
            pager = request.website.pager(url=url, total=tender_count, page=page, step=ppg, scope=7, url_args=post)
            tenders = tender_obj.search(domain, limit=ppg, offset=pager['offset'], order='name desc')
                
        tender_types = tender_type_obj.search([])
        dt = time.strftime('%Y-%m-%d')
        tender_tender_ids = []
        
        for tender in tenders:
            if user_id.partner_id.id in tender.requirement_partner_ids.ids and tender.is_open_tender == False:
                tender_tender_ids.append(tender)
            if tender.is_open_tender == True:
                tender_tender_ids.append(tender)
        
        values ={
                  'tenders':tender_tender_ids,
                  'tender_types':tender_types,
                  'user_type':request.uid, 
                  'start_date': dt,
                  'end_date': dt,
                  'pager': pager
                }
        #return self.page(page)
        return request.website.render("nomin_web.tender_list", values)        
    
        
    @http.route([
        '/tender_list/published',
        '/tender_list/published/page/<int:page>',
        ], type='http', auth="public", website=True)
    def publish_tenders(self, page=1, ppg=False, **post):
        user_id = user = request.env['res.users'].sudo().browse(request.uid)
        
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG
        
        tender_obj = request.env['tender.tender']
        tender_type_obj = request.env['tender.type']
        
        values = {}
        url = "/tender_list/published"
        tender_count = tender_obj.sudo().search_count([('is_publish','=',True), ('state','=','published')])
        pager = request.website.pager(url=url, total=tender_count, page=page, step=ppg, scope=7, url_args=post)
        if (request.uid!=3):
            tenders = tender_obj.sudo().search([('is_publish','=',True), ('state','=','published')], limit=ppg, offset=pager['offset'], order='name desc')
        else:
            tenders = tender_obj.sudo().search([('is_publish','=',True), ('is_open_tender','=',True), ('state','=','published')], limit=ppg, offset=pager['offset'], order='name desc')
        tender_tender_ids = []
        
        for tender in tenders:
            if user_id.partner_id.id in tender.requirement_partner_ids.ids and tender.is_open_tender == False:
                tender_tender_ids.append(tender)
            if tender.is_open_tender == True:
                tender_tender_ids.append(tender)
                
        tender_type_ids = tender_type_obj.sudo().search([])
        dt = time.strftime('%Y-%m-%d')
        
        values ={
                  'tenders':tender_tender_ids,
                  'tender_types':tender_type_ids,
                  'pager': pager, 
                  'start_date': dt,
                  'end_date': dt,
                }
        #return self.page(page)
        return request.website.render("nomin_web.tender_list", values)    
        
    @http.route([
        '/tender_list/unpublished',
        '/tender_list/unpublished/page/<int:page>',
        ], type='http', auth="public", website=True)
    def unpublish_tenders(self, page=1, ppg=False, **post):
        user_id = user = request.env['res.users'].sudo().browse(request.uid)
        
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG
            
        tender_obj = request.env('tender.tender')
        tender_type_obj = request.env('tender.type')
        
        values = {}
        url = "/tender_list/unpublished"
        tender_count = tender_obj.sudo().search_count([('is_publish','=',True), ('state','!=','published')])
        pager = request.website.pager(url=url, total=tender_count, page=page, step=ppg, scope=7, url_args=post)
        if (request.uid!=3):
            tenders = tender_obj.sudo().search([('is_publish','=',True), ('state','!=','published')], limit=ppg, offset=pager['offset'], order='name desc')
        else:
            tenders = tender_obj.sudo().search([('is_publish','=',True), ('is_open_tender','=',True), ('state','!=','published')], limit=ppg, offset=pager['offset'], order='name desc')
        tender_tender_ids = []
        
        #урилга авсан харилцагчдыг шалгаж байна
        for tender in tenders:
            if user_id.partner_id.id in tender.requirement_partner_ids.ids and tender.is_open_tender == False:
                tender_tender_ids.append(tender)
            if tender.is_open_tender == True:
                tender_tender_ids.append(tender)
        
        tender_types = tender_type_obj.sudo().search([])
        dt = time.strftime('%Y-%m-%d')
        
        values ={
                  'tenders':tender_tender_ids,
                  'tender_types':tender_types,
                  'pager':pager, 
                  'start_date': dt,
                  'end_date': dt,
                }
        #return self.page(page)
        return request.website.render("nomin_web.tender_list", values)

    @http.route('/tender_detail/<model("tender.tender"):tender>/', auth='public', website=True)
    def news_detail(self, tender):
        user_id = user = request.env['res.users'].sudo().browse(request.uid)
        
        part_ids = []
        user_ids = []
        defeated_partners = []
        winning_partners = []
        valuations = ''
        partner_docs = ''
        

        tender_obj = request.env['tender.tender']
        type_obj = request.env['tender.type']
        tender_types = request.env['tender.type'].sudo().search([])
        
        valuations=request.env['tender.valuation'].sudo().search([('tender_id','=',tender.id)])
        
        val_partner=request.env['tender.valuation.partner']
        partner_valuation = val_partner.sudo().search([('tender_id','=',tender.id)])
        if partner_valuation:
            for order in partner_valuation:
                part_ids.append(order.partner_id.id)
                if order.is_win == True:
                    winning_partners.append(order)
                if order.is_win == False:
                    defeated_partners.append(order)
            
            if part_ids:
                user_ids = request.env['res.users'].sudo().search([('partner_id','in',part_ids)])
                _logger.info(u'\n\n\n\n\n Тендерт оролцсон хэрэглэгчид %s', user_ids)
        
        partner_bid = ''
        query = "select * from tender_require_partner_rel where res_partner_id = %s and tender_tender_id = %s"%(user_id.partner_id.id, tender.id)
        request.env.cr.execute(query)
        attend_tenders = request.env.cr.dictfetchall()
                
        partner_doc=request.env['res.partner.documents']
        doc_id=partner_doc.sudo().search([('partner_id','=',user_id.partner_id.id)])
        if doc_id:
            partner_docs = doc_id
        
        participants=request.env['tender.participants.bid']
        participant_ids=participants.sudo().search([('partner_id','=',user_id.partner_id.id),('tender_id','=',tender.id)])
        if participant_ids:
            partner_bid =  participant_ids[0]
        
        same_tender_ids = []
        type_ids = tender_obj.sudo().search([('is_publish','=',True),('type_id','=',tender.type_id.id),('id', '!=', tender.id)], limit=6, order='name desc')
        if type_ids:
            for sametender in type_ids:
                if user_id.partner_id.id in sametender.requirement_partner_ids.ids:
                    same_tender_ids.append(sametender)
                if sametender.is_open_tender:
                    same_tender_ids.append(sametender)
        
        return http.request.render('nomin_web.tender_detail', {'tender':tender,'same_tenders':same_tender_ids,'user_ids':user_ids,'partner_bid': partner_bid, 'inv_tenders': attend_tenders, 'partner_docs': partner_docs, 'tender_types':tender_types, 'valuations':valuations, 'winning_partners':winning_partners, 'defeated_partners':defeated_partners, 'user_type':request.uid})
    
    
    @http.route([
                 '/result_list/',
                 '/result_list/page/<int:page>', 
        ], type='http', auth="public", website=True)
    def tender_results(self, page=1, category=False, ppr=False, **post):
        user_id = user = request.env['res.users'].sudo().browse(request.uid)
        
        if ppr:
            try:
                ppr = int(ppr)
            except ValueError:
                ppr = PPR
            post["ppr"] = ppr
        else:
            ppg = PPR
        
        domain = self._get_search_domain(category)
        self.partner_id=user_id.partner_id[0].id#partner_id of online user
        
        tender_obj = request.env['tender.tender']
        tender_type_obj = request.env['tender.type']
        
        values = {}
        url = "/result_list"
        tender_count = tender_obj.sudo().search_count(domain)
        pager = request.website.pager(url=url, total=tender_count, page=page, step=ppg, scope=7, url_args=post)
        
        tenders = tender_obj.sudo().search( domain, limit=ppg, offset=pager['offset'], order='name desc')
        
        tender_tender_ids = []
        for tender in tenders:
            if user_id.partner_id.id in tender.requirement_partner_ids.ids and tender.is_open_tender == False:
                tender_tender_ids.append(tender)
            if tender.is_open_tender == True:
                tender_tender_ids.append(tender)
        
        tender_types = tender_type_obj.sudo().search([])
        dt = time.strftime('%Y-%m-%d')
        
        values ={
                  'tender_results':tender_tender_ids,
                  'tender_types':tender_types,
                  'user_type':request.uid,
                  'start_date': dt,
                  'end_date': dt,
                  'pager': pager
                }
        
        return request.website.render("nomin_web.tender_result_list", values)

    
    @http.route('/result_details/<model("tender.tender"):tender>/', type='http', auth="public", website=True)
    def results_details(self, tender):
        user_id = user = request.env['res.users'].sudo().browse(request.uid)

        part_ids = []
        user_ids = []
        defeated_partners = []
        winning_partners = []
        valuations = ()
        
        
        tender_obj = request.env['tender.tender']
        tender_types = request.env['tender.type'].sudo().search([])

        valuations=request.env['tender.valuation'].sudo().search([('tender_id','=',tender.id)])
                 
        val_partner=request.env['tender.valuation.partner']
        participants = val_partner.sudo().search([('tender_id','=', tender.id)])
        if participants:
            for order in participants:
                part_ids.append(order.partner_id.id)
                if order.is_win == True:
                    winning_partners.append(order)
                if order.is_win == False:
                    defeated_partners.append(order)
            
            if part_ids:
                user_ids = request.registry('res.users').search(request.cr, SUPERUSER_ID, [('partner_id','in',part_ids)])
                _logger.info(u'\n\n\n\n\n Тендерт оролцсон хэрэглэгчид %s', user_ids)
        same_tender_ids = []
        tender_type_ids = tender_obj.sudo().search([('is_publish','=',True),('type_id','=',tender.type_id.id),('id', '!=', tender.id)])
        if tender_type_ids:
            for sametender in tender_type_ids:
                if user_id.partner_id.id in sametender.requirement_partner_ids.ids:
                    same_tender_ids.append(sametender)
                if sametender.is_open_tender:
                    same_tender_ids.append(sametender)
        
        values ={
                    'tender': tender,
                    'tender_types': tender_types,
                    'user_type': request.uid,
                    'valuations': valuations,
                    'defeated_partners': defeated_partners,
                    'winning_partners': winning_partners,
                    'same_tenders': same_tender_ids,
                    'user_ids' : user_ids,
                }
        
        return request.website.render("nomin_web.tender_result_detail", values)
    
    @http.route('/tender/create/documents/<model("tender.tender"):tender>/', type='http', auth="public", website=True)
    def my_tender_bid(self, tender):
        user_id = user = request.env['res.users'].sudo().browse(request.uid)
        tender = request.env['tender.tender'].sudo().browse(tender.id)

        vals = {
                'tender': tender,
                }
        
        return request.website.render("nomin_web.create_documents_tender", vals)
    
    
    
    
    
    @http.route([
    '/create/tender/documents/',
    ], type='http', auth="public", methods=['GET', 'POST'], website=True)
    def tender_document_save(self, upload=None, **kw):
        user_id = user = request.env['res.users'].sudo().browse(request.uid)
        
        Attachments = request.env['ir.attachment']
        tenders = request.env['tender.tender']
        res_partner_documents = request.env['res.partner.documents']
        participants = request.env['tender.participants.bid']
        participants_lines = request.env['participants.work.task.line']
        
        partner_doc = res_partner_documents.sudo().search([('partner_id', '=', user_id.partner_id.id)])

        if kw.get('tender'):
            
            tender = tenders.sudo().browse(int(kw.get('tender')))
            
            att_proxy_id = []
            att_technical_id = []
            att_worklist_id = []
            att_requirement_id = []
            att_license_id = []
            att_alternative_id = []
            att_cost_id = []
            att_schedule_id = []
            
            if kw.get('proxy', False):
                upload = kw.get('proxy')
                image_data = upload.read()                
                att_proxy_id = Attachments.create( {
                        'name': upload.filename,
                        'datas': image_data.encode('base64'),
                        'datas_fname': upload.filename,
                        'res_model': 'tender.participants.bid',
                    })
                
            if kw.get('technical', False):
                upload = kw.get('technical')
                image_data = upload.read()                
                att_technical_id = Attachments.create({
                        'name': upload.filename,
                        'datas': image_data.encode('base64'),
                        'datas_fname': upload.filename,
                        'res_model': 'tender.participants.bid',
                    })

                
            if kw.get('work_list', False):
                upload = kw.get('work_list')
                image_data = upload.read()                
                att_worklist_id = Attachments.create({
                        'name': upload.filename,
                        'datas': image_data.encode('base64'),
                        'datas_fname': upload.filename,
                        'res_model': 'tender.participants.bid',
                    })
                
            if kw.get('requirement', False):
                upload = kw.get('requirement')
                image_data = upload.read()                
                att_requirement_id = Attachments.create( {
                        'name': upload.filename,
                        'datas': image_data.encode('base64'),
                        'datas_fname': upload.filename,
                        'res_model': 'tender.participants.bid',
                    })
            
            if kw.get('license', False):
                upload = kw.get('license')
                image_data = upload.read()                
                att_license_id = Attachments.create({
                        'name': upload.filename,
                        'datas': image_data.encode('base64'),
                        'datas_fname': upload.filename,
                        'res_model': 'tender.participants.bid',
                    })
                     
            if kw.get('alternative', False):
                upload = kw.get('alternative')
                image_data = upload.read()                
                att_alternative_id = Attachments.create({
                        'name': upload.filename,
                        'datas': image_data.encode('base64'),
                        'datas_fname': upload.filename,
                        'res_model': 'tender.participants.bid',
                    })
            
            if kw.get('cost', False):
                upload = kw.get('cost')
                image_data = upload.read()                
                att_cost_id = Attachments.create({
                        'name': upload.filename,
                        'datas': image_data.encode('base64'),
                        'datas_fname': upload.filename,
                        'res_model': 'tender.participants.bid',
                    })
                
            if kw.get('schedule', False):
                upload = kw.get('schedule')
                image_data = upload.read()                
                att_schedule_id = Attachments.create({
                        'name': upload.filename,
                        'datas': image_data.encode('base64'),
                        'datas_fname': upload.filename,
                        'res_model': 'tender.participants.bid',
                    })
            if kw.get('control_budget', False):
                upload = kw.get('control_budget')
                image_data = upload.read()                
                control_budget_id = Attachments.create({
                        'name': upload.filename,
                        'datas': image_data.encode('base64'),
                        'datas_fname': upload.filename,
                        'res_model': 'tender.participants.bid',
                    })

            part_id = participants.create(
                                        {
                                            'name': tender.desc_name + ' - ' + user_id.partner_id.name,
                                            'tender_id': tender.id,
                                            'partner_id': user_id.partner_id.id,
                                            'document_id': partner_doc.id,
                                            't_partner_proxy_id': att_proxy_id,
                                            't_partner_technical_id': att_technical_id,
                                            't_partner_worklist_id': att_worklist_id,
                                            't_partner_require_id': att_requirement_id,
                                            't_partner_license_id': att_license_id,
                                            't_partner_alternative_id': att_alternative_id,
                                            't_partner_cost_id': att_cost_id,
                                            't_partner_schedule_id': att_schedule_id,
                                            't_partner_control_budget_id': control_budget_id,
                                            'execute_time': kw.get('execute_time'),
                                            'warranty_time': kw.get('warranty_time'),
                                        })
            count = 1
            booleann=True
            while (booleann):
                if 'work%d'%count in kw:                   
                    participants_lines.create(
                                                        {
                                                            'name':kw["work%d"%count],
                                                            'tender_id': tender.id,
                                                            'task_id': part_id,
                                                            'partner_id': user_id.partner_id.id,
                                                            'qty': float(kw["hemjee%d"%count]),
                                                            'unit_price': float(kw["negjune%d"%count]),
#                                                             'amount': float(kw["hemjee%d"%count])*float(kw["negjune%d"%count]),
                                                            'costs_of_materials': float(kw["material%d"%count] or 0),
                                                            'other_costs': float(kw["busadzardal%d"%count] or 0),
#                                                             'line_total_amount': float(kw["hemjee%d"%count])*float(kw["negjune%d"%count])+float(kw["material%d"%count])+float(kw["busadzardal%d"%count])
                                                         })
                    
                else:
                    booleann=False
                    count=0
                    
                count = count + 1
        
        part_tenders = participants.sudo().search([('partner_id','=', user_id.partner_id.id),('tender_id','=',tender.id)])
        
        lines = participants_lines.sudo().search([('partner_id','=', user_id.partner_id.id),('tender_id','=',tender.id),('task_id','=',part_tenders[0].id)])
        return request.website.render("nomin_web.my_tenders_documents_details", {
            'tender': tender,
            'part_tenders': part_tenders,
            'lines': lines,
        })

    @http.route(['/search_results/',
                 '/search_results/page/<int:page>'], 
                type='http', auth="public", website=True)
    def search_results(self, page=1, ppg=False, sorting='date_end', startdate='', enddate='', category='', tendername='', category_id='', child_cate_id='', status='', **post):
        user_id = user = request.env['res.users'].sudo().browse(request.uid)
        
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG
            
        tender_obj = request.env['tender.tender']
        tender_type_obj = request.env['tender.type']
        
        tender_types = tender_type_obj.sudo().search([])
        
        # Define search scope
        search_on_pages=self._search_on_pages
        case_sensitive=self._case_sensitive
        
        url = "/search_results/"
        sql_query=""
        
        
        if sorting=='date_end':
            sql_order_by='date_end desc'

        sql_query = "select id, date_end from tender_tender where is_publish=true and is_open_tender = true and state in ('published','bid_expire','closed','in_selection','finished','cancelled')"
        if search_on_pages:

            if startdate and enddate:
                sql_query+=" and date_end between '%s 00:00:00' and '%s 23:59:59'"  % (startdate, enddate)
            if category:
                sql_query+=" and lower(name) like lower('%%%s%%')"  % (category)
            if tendername:
                sql_query+=" and lower(desc_name) like lower('%%%s%%')"  % (tendername)
            if category_id:
                sql_query+=" and type_id = %s" % (category_id)
            if child_cate_id:
                sql_query+=" and child_type_id = %s" % (child_cate_id)
            if status:
                if status == 'closed':
                    sql_query+=" and ( state != 'published')"
                else:
                    sql_query+=" and ( state = 'published')"
            
        if sql_query:
            sql_query_count="""SELECT count(*) FROM ( %s ) as subquery""" % (sql_query)
            
        # Build query for results ordered
        if sql_query:
            limit=self._results_per_page
            offset=(page-1)*self._results_per_page
            sql_query_ordered="""SELECT *
                                 FROM ( %s ) as subquery
                                 ORDER BY %s
                                 LIMIT %s
                                 OFFSET %s
                                 """ % (sql_query, sql_order_by, limit, offset)
        
        request.env.cr.execute(sql_query)
        records = request.env.cr.dictfetchall()
        tender_ids = []
        t_ids = []
        for record in records:
            tender_ids.append(record ['id'])
        # Get results count for pager
        if sql_query_count:
            request.env.cr.execute(sql_query_count)
            results_count=request.env.cr.fetchone()[0] or 0
            
        url_args = {}
        if startdate:
            url_args['startdate'] = startdate
            
        if enddate:
            url_args['enddate'] = enddate
            
        if category:
            url_args['category'] = category
            
        if tendername:
            url_args['tendername'] = tendername
            
        if category_id:
            url_args['category_id'] = category_id
            
        if child_cate_id:
            url_args['child_cate_id'] = child_cate_id
            
        if status:
            url_args['status'] = status
            
        if sorting:
            url_args['sorting'] = sorting
            pager = request.website.pager(url=url, total=results_count, page=page, step=ppg, scope=7, url_args=url_args)
            tenders = tender_obj.sudo().search([('id','in',tender_ids)], limit=ppg, offset=pager['offset'], order='name desc')
        if not tenders:
            tenders = tender_obj.sudo().search([], limit=ppg, offset=pager['offset'], order='name desc')     
        values = {
                  'user': user_id,
                  'pager': pager,
                  'sorting': sorting,
                  'startdate': startdate,
                  'enddate': enddate,
                  'category': category,
                  'tendername': tendername,
                  'category_id': category_id,
                  'child_cate_id': child_cate_id,
                  'status': status,
                  'tenders':tenders,
                  'tender_types':tender_types,
                  }
        
        return request.website.render("nomin_web.search_results", values)
    
    
    @http.route(['/result/search_results/',
                 '/result/search_results/page/<int:page>'], 
                type='http', auth="public", website=True)
    def tenderresult_search_results(self, page=1, ppg=False, sorting='date_end', startdate='', enddate='', category='', tendername='',category_id='',child_cate_id='', state='', **post):
        user_id = user = request.env['res.users'].sudo().browse(request.uid)
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG
            
        tender_obj = request.env['tender.tender']
        tender_type_obj = request.env['tender.type']
        
        tender_types = tender_type_obj.search(SUPERUSER_ID, [])
        
        # Define search scope
        search_on_pages=self._search_on_pages
        case_sensitive=self._case_sensitive
        
        url = "/result/search_results/"
        sql_query=""
        
        
        if sorting=='date_end':
            sql_order_by='date_end desc'

        sql_query = "select id, date_end from tender_tender where is_publish=true and is_open_tender=true and state in ('published','bid_expire','closed','in_selection','finished','cancelled')"
        if search_on_pages:

            if startdate and enddate:
                sql_query+=" and date_end between '%s 00:00:00' and '%s 23:59:59'"  % (startdate, enddate)
            if category:
                sql_query+=" and lower(name) like lower('%%%s%%')"  % (category)
            if tendername:
                sql_query+=" and lower(desc_name) like lower('%%%s%%')"  % (tendername)
            if category_id:
                sql_query+=" and type_id = %s" % (category_id)
            if child_cate_id:
                sql_query+=" and child_type_id = %s" % (child_cate_id)
            if state:
                if state == 'closed':
                    sql_query+=" and ( state != 'published')"
                else:
                    sql_query+=" and ( state = 'published')"
            
        if sql_query:
            sql_query_count="""SELECT count(*) FROM ( %s ) as subquery""" % (sql_query)
        
        # Build query for results ordered
        if sql_query:
            limit=self._results_per_page
            offset=(page-1)*self._results_per_page
            sql_query_ordered="""SELECT *
                                 FROM ( %s ) as subquery
                                 ORDER BY %s
                                 LIMIT %s
                                 OFFSET %s
                                 """ % (sql_query, sql_order_by, limit, offset)
            
        
        request.env.cr.execute(sql_query)
        records = request.env.cr.dictfetchall()
        tender_ids = []
        t_ids = []

        for record in records:
            tender_ids.append(record ['id'])
        # Get results count for pager
        if sql_query_count:
            request.env.cr.execute(sql_query_count)
            results_count=request.env.cr.fetchone()[0] or 0
            
        url_args = {}
        if startdate:
            url_args['startdate'] = startdate
            
        if enddate:
            url_args['enddate'] = enddate
            
        if category:
            url_args['category'] = category
            
        if tendername:
            url_args['tendername'] = tendername
            
        if category_id:
            url_args['category_id'] = category_id
             
        if child_cate_id:
            url_args['child_cate_id'] = child_cate_id
             
        if state:
            url_args['state'] = state
            
        if sorting:
            url_args['sorting'] = sorting
            pager = request.website.pager(url=url, total=results_count, page=page, step=ppg, scope=7, url_args=url_args)
            tenders = tender_obj.sudo().search([('id','in',tender_ids)], limit=ppg, offset=pager['offset'], order='name desc')           

        if not tenders:
            tenders = tender_obj.sudo().search([], limit=ppg, offset=pager['offset'], order='name desc')     
        values = {'user': user_id,
                  'is_public_user': user_id.id == request.website.user_id.id,
                  'header': post.get('header', dict()),
                  'searches': post.get('searches', dict()),
                  'results_per_page': self._results_per_page,
                  'last_result_showing': min(results_count, page*self._results_per_page),
                  'results_count': results_count,
                  'results': [],
                  'pager': pager,
                  'search_on_pages': search_on_pages,
                  'sorting': sorting,
                  'startdate': startdate,
                  'enddate': enddate,
                  'category': category,
                  'tendername': tendername,
                  'state': state,
                  'category_id': category_id,
                  'child_cate_id': child_cate_id,
                  'tender_results':tenders,
                  'tender_types':tender_types,
                  }
        
        return request.website.render("nomin_web.tender_result_search_results", values)
    
    @http.route(['/allresults/',
                 '/allresults/page/<int:page>'], 
                type='http', auth="public", website=True)
    def all_search(self, page=1, ppg=False, sorting='create_date', search='', **post):
        user_id = user = request.env['res.users'].sudo().browse(request.uid)
        
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG
            
        tender_obj = request.env['tender.tender']
        tender_type_obj = request.env['tender.type']
        tender_inv = request.env['tender.invitation.guide']
        
        tender_types = tender_type_obj.sudo().search( [])
        
        # Define search scope
        search_on_pages=self._search_on_pages
        case_sensitive=self._case_sensitive
            
        url = "/allresults/"
        sql_query=""
        
        if sorting=='create_date':
            sql_order_by='create_date desc'

        sql_query = "select tenderinv.name, tenderinv.inv_id, tenderinv.tender_id from \
                            (select inv.id as inv_id, inv.invitation_detail as invitation_detail, \
                            tender.id as tender_id, tender.name as name, tender.desc_name as desc_name \
                            from tender_tender as tender, tender_invitation_guide as inv \
                            where tender.is_publish = true and tender.is_open_tender = true and tender.invitation_id = inv.id) \
                    tenderinv"
        
        if search_on_pages:

            if search:
                sql_query+=" where lower(tenderinv.name) like lower('%%%s%%') \
                            or lower(tenderinv.desc_name) like lower('%%%s%%')\
                            or lower(tenderinv.invitation_detail) like lower('%%%s%%')\
                            group by tenderinv.inv_id, tenderinv.name, tenderinv.tender_id \
                            order by tenderinv.name desc"  % (search, search, search)

        if sql_query:
            sql_query_count="""SELECT count(*) FROM ( %s ) as subquery""" % (sql_query)
        
        
        if sql_query:
            limit=self._results_per_page
            offset=(page-1)*self._results_per_page
            sql_query_ordered="""SELECT *
                                 FROM ( %s ) as subquery
                                 ORDER BY %s
                                 LIMIT %s
                                 OFFSET %s
                                 """ % (sql_query, sql_order_by, limit, offset)
            
        
        request.env.cr.execute(sql_query)
        records = request.env.cr.dictfetchall()
        tender_ids = []

        for record in records:
            tender_ids.append(record['tender_id'])
        # Get results count for pager
        if sql_query_count:
            request.env.cr.execute(sql_query_count)
            results_count=request.env.cr.fetchone()[0] or 0
            
        url_args = {}
        if search:
            url_args['search'] = search
#        if search_on:
#            url_args['search_on'] = search_on
        if sorting:
            url_args['sorting'] = sorting
            pager = request.website.pager(url=url, total=results_count, page=page, step=ppg, scope=7, url_args=url_args)
            t_ids = tender_obj.sudo().search([('id','in',tender_ids)], limit=ppg, offset=pager['offset'], order='name desc') 

        if not tenders:
            tenders = tender_obj.sudo().search([], limit=ppg, offset=pager['offset'], order='name desc')     

        values = {
                    'user': user_id,
                    'is_public_user': user_id.id == request.website.user_id.id,
                    'header': post.get('header', dict()),
                    'searches': post.get('searches', dict()),
                    'results_per_page': self._results_per_page,
                    'last_result_showing': min(results_count, page*self._results_per_page),
                    'results_count': results_count,
                    'results': [],
                    'pager': pager,
                    'search_on_pages': search_on_pages,
                    'sorting': sorting,
                    'search': search,
                    'tenders':tenders,
                    'tender_types':tender_types,
#                   'invitation':invitation,
                  }

        return request.website.render("nomin_web.allsearch_results", values)
    
    