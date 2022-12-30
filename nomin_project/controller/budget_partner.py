# -*- coding: utf-8 -*-

from datetime import datetime
from openerp import api, fields, models, tools
from openerp.exceptions import UserError
from openerp.addons.web import http
from openerp.http import request
import base64
import werkzeug

class BudgetPartner(http.Controller):    

    _results_per_page = 10

    @http.route(['/quotations',
                '/quotations/page/<int:page>'
                ], type='http', auth="public", website=True)
    def quotations(self, page=1, ppg=False, **post):
        vals = {}
        uid = request.uid

        if uid ==3:
            return request.website.render("website.403")
        user_id = request.env['res.users'].browse(uid)

        url = '/quotations'
        obj = request.env['budget.partner.comparison'].sudo()
        domain_requirement_partner = ['&',('invitation_type','=','requirement_partner'),('requirement_partner_ids','in',user_id.partner_id.id)]
        domain_partner_type = ['&',('invitation_type','=','partner_type'),'|',('child_type_id','in',user_id.partner_id.tender_type_ids.ids),('type_id','in',user_id.partner_id.tender_type_ids.ids)]
        domain = [('state','in',['quotation','end_quotation','comparison','management','winner']),'|'] 
        domain.extend(domain_requirement_partner)
        domain.extend(domain_partner_type)

        budget_count = obj.search_count(domain)
        pager = request.website.pager(url=url, total=budget_count, page=page,step=self._results_per_page, scope=3,url_args=post)
        budgets = obj.search(domain, limit=self._results_per_page , offset=pager['offset'], order = 'date_end desc')

        vals ={
            'budgets':budgets,                  
            'pager': pager
            }
        return request.website.render("nomin_project.budget_list", vals)

    @http.route('/quot_detail/<model("budget.partner.comparison"):budget>/', auth='public', website=True)
    def quot_detail(self, budget):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        if uid ==3:
            return request.website.render("website.403")			
        user_id = request.env['res.users'].browse(uid)
        budget_partner_id = request.env['budget.partners'].sudo().search([('partner_id','=',user_id.partner_id.id),('budget_partner_id','=',budget.id)])
        vals ={			
            'budget':budget.sudo(),   
            'budget_partner_id':budget_partner_id.sudo(),               			
            }
        return http.request.render('nomin_project.quot_detail',vals)

    @http.route(['/quotation/create/<model("budget.partner.comparison"):budget>/'], type='http', auth="public", website=True)	
    def quotation_create(self, budget):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry

        if uid ==3:
            return request.website.render("website.403")
        user_id = request.env['res.users'].browse(uid)
        budget_partner_id = request.env['budget.partners'].sudo().search([('partner_id','=',user_id.partner_id.id),('budget_partner_id','=',budget.id)])
        
        return request.website.render("nomin_project.create_my_quotation", {'budget': budget,'budget_partner_id':budget_partner_id,'lines':{}})
    
    @http.route(['/quotation/save'], type='http', auth="public", website=True)
    def quotation_save(self, upload=None, **post):		
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        if uid ==3:
            return request.website.render("website.403")
        total_amount = 0
        budget_partner_id = False
        budget = False
        upload = False
        if 'total_amount' in post and post['total_amount']!=0:
            total_amount = float(post['total_amount'])
        if 'budget_partner_id' in post and post['budget_partner_id']:
            budget_partner_id = int(post['budget_partner_id'])
        if 'budget' in post and post['budget']:
            budget = int(post['budget'])
        if 'cost' in post and post['cost']:
            upload = post['cost']
        
        user_id = request.env['res.users'].browse(uid)
        if not budget_partner_id:
            budget_partner_id = request.env['budget.partners'].sudo().search([('partner_id','=',user_id.partner_id.id),('budget_partner_id','=',budget)])
        if not budget_partner_id:	
            budget_partner_id = request.env['budget.partners'].sudo().create({
                'partner_id':user_id.partner_id.id,
                'price_amount':total_amount,
                'budget_partner_id':budget
            })			
            budget_partner_id = budget_partner_id.sudo()			
            image_data = upload.read()                
            att_cost_id = request.env['ir.attachment'].sudo().create({
            'name': upload.filename,
            'datas': image_data.encode('base64'),
            'datas_fname': upload.filename,
            'res_model': 'budget.partners',
            'res_id':budget_partner_id.id
            })
            budget_partner_id.write({'document_id':att_cost_id.id})
        else:
            budget_partner_id = request.env['budget.partners'].browse(budget_partner_id).sudo()
            if upload:				
                image_data = upload.read()                
                att_cost_id = request.env['ir.attachment'].sudo().create({
                'name': upload.filename,
                'datas': image_data.encode('base64'),
                'datas_fname': upload.filename,
                'res_model': 'budget.partners',
                'res_id':budget_partner_id.id
                })
                budget_partner_id.sudo().write({'document_id':att_cost_id.id})
            if total_amount!=0:				
                budget_partner_id.sudo().write({'price_amount':total_amount})

        return request.website.render("nomin_project.quotation_thanks")

    @http.route('/quotation/<model("ir.attachment"):document>/download', type='http', auth="public", website=True)    
    def quotation_document_download(self, document):
        if document.sudo() and request.session.uid:
            filecontent = base64.b64decode(document.sudo().datas)
            disposition = 'attachment; filename=%s' % werkzeug.urls.url_quote(document.sudo().datas_fname)
            return request.make_response(
                filecontent,
                 [('Content-Type', document.sudo().mimetype),
                  ('Content-Length', len(filecontent)),
                  ('Content-Disposition', disposition)])
        elif not request.session.uid:
            return werkzeug.utils.redirect('/web?redirect=/quotations')
        return request.website.render("website.403")