# -*- coding: utf-8 -*-
import base64
import json
from odoo import SUPERUSER_ID
from odoo import http
from odoo.tools.translate import _
from odoo.http import request
from PIL import Image
from posix import unlink
from psycopg2 import IntegrityError
from odoo.tools.translate import _
from odoo.exceptions import ValidationError
from odoo.addons.base.models.ir_qweb_fields import nl2br


import logging
_logger = logging.getLogger(__name__)

class PartnerDocuments(http.Controller):
    
    @http.route('/my/tender', type='http', auth="public", website=True)
    def my_tender_account(self, **kw):
        user = request.env['res.users'].sudo().browse(request.uid)
        tender_obj = request.env['tender.tender']
        tender_ids = []
        inv_tenders = ()
        query = "select * from tender_require_partner_rel where res_partner_id = %s"%(user.partner_id.id)
        request.env.cr.execute(query)
        attend_tenders = request.env.cr.dictfetchall()
        if attend_tenders:
            for attend in attend_tenders:
                tender_id = attend['tender_tender_id']
                tender_ids.append(tender_id)
                
        if tender_ids:
            inv_tenders = tender_obj.sudo().browse(tender_ids)
        
        vals = {
                'inv_tenders': inv_tenders, 
                }
        
        return request.render("nomin_web.my_tender_account", vals)
        
    @http.route('/my/account', type='http', methods=['GET','POST'], auth='public', website=True)
    def my_account(self):
        user = request.env['res.users'].sudo().browse(request.uid)
        categories = request.env['res.partner.category'].sudo().search([])
        types = request.env['tender.type'].sudo().search([])
        cate_ids = user.partner_id.category_id.ids
        tendertype_ids = user.partner_id.tender_type_ids.ids
        vals = {
                'partner': user.partner_id,
                'categories': categories,
                'types': types,
                'category_ids': cate_ids,
                'type_ids': tendertype_ids,
                }
        return request.render("nomin_web.my_general_account", vals)
    
    
    @http.route('/my/account/update', type='http', auth="public", methods=['GET','POST'], website=True)
    def account_update(self, **kwargs):
        user = request.env['res.users'].sudo().browse(request.uid)
        categories = request.env['res.partner.category'].sudo().search([])
        types = request.env['tender.type'].sudo().search([])
        cate_ids = user.partner_id.category_id.ids
        tendertype_ids = user.partner_id.tender_type_ids.ids
        
        vals = {
                'partner': user.partner_id,
                'categories': categories,
                'types': types,
                'category_ids': cate_ids,
                'type_ids': tendertype_ids,
                }
        
        return request.render("nomin_web.my_account_edit", vals)
    
    
    @http.route('/save_partner/', type='http', auth='public', methods=['GET', 'POST'], website=True)
    def save_partners(self, **post):
        user = request.env['res.users'].sudo().browse(request.uid)
        res_partner = request.env['res.partner']
        categories = request.env('res.partner.category').sudo().search([])
        types = request.env['tender.type'].sudo().search([])
        vals = {}
        category_ids = []
        tendertype_ids = []
        
        if "cate1" in post:
            category_ids.append(int(post["cate1"]))
        if "cate2" in post:
            category_ids.append(int(post["cate2"]))
        if "cate3" in post:
            category_ids.append(int(post["cate3"]))
        if "cate4" in post:
            category_ids.append(int(post["cate4"]))
        if "cate5" in post:
            category_ids.append(int(post["cate5"]))
        if "cate6" in post:
            category_ids.append(int(post["cate6"]))
        if "cate7" in post:
            category_ids.append(int(post["cate7"]))
        if "cate8" in post:
            category_ids.append(int(post["cate8"]))
        if "cate9" in post:
            category_ids.append(int(post["cate9"]))
        if "cate10" in post:
            category_ids.append(int(post["cate10"]))
        if "cate11" in post:
            category_ids.append(int(post["cate11"]))
        if "cate12" in post:
            category_ids.append(int(post["cate12"]))
        if "type1" in post:
            tendertype_ids.append(int(post["type1"]))
        if "type2" in post:
            tendertype_ids.append(int(post["type2"]))
        if "type3" in post:
            tendertype_ids.append(int(post["type3"]))
        if "type4" in post:
            tendertype_ids.append(int(post["type4"]))
        if "type5" in post:
            tendertype_ids.append(int(post["type5"]))
            
        if post["company_image"]:
            vals.update({'image': base64.encodestring(post['company_image'].read())})
            user.partner_id.sudo().write(vals)
        user.partner_id.write(
               {
                    'name': post["company_name"],
                    'category_id': [(6, 0, category_ids)],
                    'street': post["address"],
                    'registry_number': post["certificate_no"],
                    'mobile': post["phonenumber"],
                    'code': post["registration_number"],
                    'comment': post["description"],
                    'email': post["email"],
                    'tender_type_ids': [(6, 0, tendertype_ids)],
                })

        vals = {
                'partner': user.partner_id,
                'pcate_ids': user.partner_id.category_id,
                'category_ids': category_ids,
                'categories': categories,
                'types': types,
                'type_ids': tendertype_ids,
                }
        
        return request.render("nomin_web.my_general_account", vals)

    @http.route([
        '/my/documents/create',
    ], type='http', auth="public", website=True)
    def documents_create(self, **kwargs):
        user = request.env['res.users'].sudo().browse(request.uid)
        required_tax = True    #Татварын албаны тодорхойлолт
        required_cer = True    #Гэрчилгээ
        required_lice = True   #Тусгай зөвшөөрөл
        required_vat = True    #Нөат
        required_org = True    #ААН тодорхойлолт
        required_jud = True    #Шүүхийн тодорхойлолт
        required_bank = True   #Банкны тодорхойлолт
        required_ins = True    #НДГ тодорхойлолт
        required_work = True   #Ажлын туршлага
        required_irep = True   #Даатгалын тайлан
        required_fin = True    #Санхүүгийн тайлан
        required_aud = True    #Аудитын тайлан
        document = ''
        line_ids = []
        documents=request.env['res.partner.documents']
        document = documents.sudo().search([('partner_id', '=', user.partner_id.id)])
        if document:
            return request.render("nomin_web.my_documents")
        else:
            return request.render("nomin_web.create_my_document", {
                'partner': user.partner_id,
                'document': document,
#                 'file': conf_line,
                'required_tax':required_tax,
                'required_cer':required_cer,
                'required_lice':required_lice,
                'required_vat':required_vat,
                'required_org':required_org,
                'required_jud':required_jud,
                'required_bank':required_bank,
                'required_ins':required_ins,
                'required_work':required_work,
                'required_irep':required_irep,
                'required_fin':required_fin,
                'required_aud':required_aud,
            })

    
    # Check and insert values from the form on the model <model>
    @http.route('/create_document/<string:model_name>', type='http', auth="public", methods=['POST'], website=True)
    def create_partner_document(self, model_name, **kwargs):
        model_record = request.env['ir.model'].sudo().search([('model', '=', model_name), ('website_form_access', '=', True)])        
        if not model_record:
            return json.dumps(False)
        try:

            data = self.extract_data(model_record, ** kwargs)
        # If we encounter an issue while extracting data
        except ValidationError as e:
            # I couldn't find a cleaner way to pass data to an exception
            return json.dumps({'error_fields' : e.args[0]})
        try:
            id_record = self.insert_record(request, model_record, data['record'], data['custom'], data.get('meta'))
            if id_record:
                self.insert_attachment(model_record, id_record, data['attachments'])
        # Some fields have additionnal SQL constraints that we can't check generically
        # Ex: crm.lead.probability which is a float between 0 and 1
        # TODO: How to get the name of the erroneous field ?
        except IntegrityError:
            return json.dumps(False)

        request.session['form_builder_model'] = model_record.name
        request.session['form_builder_id']    = id_record
        return json.dumps({'id': id_record})

    # Constants string to make custom info and metadata readable on a text field

    _custom_label = "%s\n___________\n\n" % _("Custom infos")  # Title for custom fields
    _meta_label = "%s\n________\n\n" % _("Metadata")  # Title for meta data

    # Dict of dynamically called filters following type of field to be fault tolerent
    def identity(self, field_label, field_input):
        return field_input

    def integer(self, field_label, field_input):
        return int(field_input)

    def floating(self, field_label, field_input):
        return float(field_input)

    def boolean(self, field_label, field_input):
        return bool(field_input)

    def binary(self, field_label, field_input):
        return base64.b64encode(field_input.read())

    def one2many(self, field_label, field_input):
        return [int(i) for i in field_input.split(',')]

    def many2many(self, field_label, field_input, *args):
        return [(args[0] if args else (6,0)) + (self.one2many(field_label, field_input),)]

    _input_filters = {
        'char': identity,
        'text': identity,
        'html': identity,
        'datetime': identity,
        'many2one': integer,
        'one2many': one2many,
        'many2many':many2many,
        'selection': identity,
        'boolean': boolean,
        'integer': integer,
        'float': floating,
        'binary': binary,
    }

    # Extract all data sent by the form and sort its on several properties
    def extract_data(self, model, **kwargs):
        data = {
            'record': {},        # Values to create record
            'attachments': [],  # Attached files
            'custom': '',        # Custom fields values
        }
        authorized_fields = model.sudo()._get_form_writable_fields()
        error_fields = []
        for field_name, field_value in kwargs.items():
            # If the value of the field if a file
            if hasattr(field_value, 'filename'):
                # Undo file upload field name indexing
                field_name = field_name.rsplit('[', 1)[0]
                # If it's an actual binary field, convert the input file
                # If it's not, we'll use attachments instead
                if field_name in authorized_fields and authorized_fields[field_name]['type'] == 'binary':
                    data['record'][field_name] = base64.b64encode(field_value.read())
                else:
                    data['attachments'].append(field_value)
                    field_value.field_name = field_name
                    if model.model =='res.partner.documents':
                        if field_name=='tax':
                                data['record']['tax_id']=field_value
                        if field_name=='certificate':
                                data['record']['certificate_id']=field_value
                        if field_name =='organization':
                                data['record']['organization_id']=field_value
                        if field_name=='work_list':
                                data['record']['work_id']=field_value
                        if field_name =='judgement':
                                data['record']['judgement_id']=field_value
                        if field_name=='license':
                                data['record']['license_id']=field_value
                        if field_name =='bank':
                                data['record']['bank_id']=field_value
                        if field_name=='vat':
                                data['record']['vat_id']=field_value
                        if field_name =='insurance':
                                data['record']['insurance_id']=field_value
                        if field_name=='ins_report':
                                data['record']['ins_report_id']=field_value
                        if field_name =='finance_report':
                                data['record']['finance_id']=field_value
                        if field_name =='audit_report':
                                data['record']['audit_id']=field_value
            # If it's a known field
            elif field_name in authorized_fields:
                # field_value.field_name = field_name
                try:
                    input_filter = self._input_filters[authorized_fields[field_name]['type']]
                    data['record'][field_name] = input_filter(self, field_name, field_value)
                except ValueError:
                    error_fields.append(field_name)
            # If it's a custom field
            elif field_name != 'context':
                if field_name =='audit_date_end':
                        data['record']['audit_date_end']=field_value
                if field_name=='fin_date_end':
                        data['record']['fin_date_end']=field_value
                if field_name=='insurep_date_end':
                        data['record']['insurep_date_end']=field_value
                if field_name=='insu_date_end':
                        data['record']['insu_date_end']=field_value
                if field_name=='vat_date_end':
                        data['record']['vat_date_end']=field_value
                if field_name =='bank_date_end':
                        data['record']['bank_date_end']=field_value
                if field_name=='spec_date_end':
                        data['record']['spec_date_end']=field_value
                if field_name=='judge_date_end':
                        data['record']['judge_date_end']=field_value
                if field_name=='work_date_end':
                        data['record']['work_date_end']=field_value
                if field_name=='tax_date_end':
                        data['record']['tax_date_end']=field_value
                if field_name=='certif_date_end':
                        data['record']['certif_date_end']=field_value
                if field_name=='org_date_end':
                        data['record']['org_date_end']=field_value
                data['custom'] += "%s : %s\n" % (field_name.decode('utf-8'), field_value)

        # Add metadata if enabled
        environ = request.httprequest.headers.environ
        if(request.website.website_form_enable_metadata):
            data['meta'] += "%s : %s\n%s : %s\n%s : %s\n%s : %s\n" % (
                "IP"                , environ.get("REMOTE_ADDR"),
                "USER_AGENT"        , environ.get("HTTP_USER_AGENT"),
                "ACCEPT_LANGUAGE"   , environ.get("HTTP_ACCEPT_LANGUAGE"),
                "REFERER"           , environ.get("HTTP_REFERER")
            )
        dest_model = request.env[model.model]
        if hasattr(dest_model, "website_form_input_filter"):
            data['record'] = dest_model.website_form_input_filter(request, data['record'])

        missing_required_fields = [label for label, field in authorized_fields.iteritems() if field['required'] and not label in data['record']]
        if any(error_fields):
            raise ValidationError(error_fields + missing_required_fields)
        
        return data

    def insert_record(self, request, model, values, custom, meta=None):
        record=request.env[model.model].sudo().search([('partner_id','=',values['partner_id'])])
        if not record:
            record = request.env[model.model].sudo().create(values)
        for doc in record:

            if not doc.partner_id.document_id:
                doc.partner_id.write({'document_id':doc.id})
        if 'tax_id' in values:
            request.env['ir.attachment'].sudo().create({'p_tax_id':record.id,
                                                        'name': values['tax_id'].filename,
                                                        'datas': base64.encodestring(values['tax_id'].read()),
                                                        'datas_fname': values['tax_id'].filename,
                                                        'date_end':values['tax_date_end'],
                                                        })


        if 'certificate_id' in values or 'certif_date_end' in values:            
            request.env['ir.attachment'].sudo().create({'p_certificate_id':record.id,
                                                        'name': values['certificate_id'].filename,
                                                        'datas': base64.encodestring(values['certificate_id'].read()),
                                                        'datas_fname': values['certificate_id'].filename,
                                                        'date_end':values['certif_date_end'],
                                                        })
        if 'organization_id' in values:
            request.env['ir.attachment'].sudo().create({
                                                        'p_org_define_id':record.id,
                                                        'name': values['organization_id'].filename,
                                                        'datas': base64.encodestring(values['organization_id'].read()),
                                                        'datas_fname': values['organization_id'].filename,
                                                        'date_end':values['org_date_end'],
                                                        })
        if 'work_id' in values:
            request.env['ir.attachment'].sudo().create({
                                                        'p_work_list_id':record.id,
                                                        'name': values['work_id'].filename,
                                                        'datas': base64.encodestring(values['work_id'].read()),
                                                        'datas_fname': values['work_id'].filename,
                                                        'date_end':values['work_date_end'],
                                                        })
        if 'judgement_id' in values:
            request.env['ir.attachment'].sudo().create({
                                                        'p_judgement_define_id':record.id,
                                                        'name': values['judgement_id'].filename,
                                                        'datas': base64.encodestring(values['judgement_id'].read()),
                                                        'datas_fname': values['judgement_id'].filename,
                                                        'date_end':values['judge_date_end'],
                                                        })
        if 'license_id' in values:
            request.env['ir.attachment'].sudo().create({
                                                        'p_spec_license_id':record.id,
                                                        'name': values['license_id'].filename,
                                                        'datas': base64.encodestring(values['license_id'].read()),
                                                        'datas_fname': values['license_id'].filename,
                                                        'date_end':values['spec_date_end'],
                                                        })
        if 'bank_id' in values:
            request.env['ir.attachment'].sudo().create({
                                                        'p_bank_define_id':record.id,
                                                        'name': values['bank_id'].filename,
                                                        'datas': base64.encodestring(values['bank_id'].read()),
                                                        'datas_fname': values['bank_id'].filename,
                                                        'date_end':values['bank_date_end'],
                                                        })
        if 'vat_id' in values:
            request.env['ir.attachment'].sudo().create({
                                                        'p_vat_file_id':record.id,
                                                        'name': values['vat_id'].filename,
                                                        'datas': base64.encodestring(values['vat_id'].read()),
                                                        'datas_fname': values['vat_id'].filename,
                                                        'date_end':values['vat_date_end'],
                                                        })
        if 'insurance_id' in values:
            request.env['ir.attachment'].sudo().create({
                                                        'p_insurance_define_id':record.id,
                                                        'name': values['insurance_id'].filename,
                                                        'datas': base64.encodestring(values['insurance_id'].read()),
                                                        'datas_fname': values['insurance_id'].filename,
                                                        'date_end':values['insu_date_end'],
                                                        })
        if 'ins_report_id' in values:
            request.env['ir.attachment'].sudo().create({
                                                        'p_insurance_report_id':record.id,
                                                        'name': values['ins_report_id'].filename,
                                                        'datas': base64.encodestring(values['ins_report_id'].read()),
                                                        'datas_fname': values['ins_report_id'].filename,
                                                        'date_end':values['insurep_date_end'],
                                                        })
        if 'finance_id' in values:
            request.env['ir.attachment'].sudo().create({
                                                        'p_finance_report_id':record.id,
                                                        'name': values['finance_id'].filename,
                                                        'datas': base64.encodestring(values['finance_id'].read()),
                                                        'datas_fname': values['finance_id'].filename,
                                                        'date_end':values['fin_date_end'],
                                                        })
        if 'audit_id' in values:
            request.env['ir.attachment'].sudo().create({
                                                        'p_audit_report_id':record.id,
                                                        'name': values['audit_id'].filename,
                                                        'datas': base64.encodestring(values['audit_id'].read()),
                                                        'datas_fname': values['audit_id'].filename,
                                                        'date_end':values['audit_date_end'],
                                                        })
        
        if custom or meta:
            default_field = model.website_form_default_field_id
            default_field_data = values.get(default_field.name, '')
            custom_content = (default_field_data + "\n\n" if default_field_data else '') \
                           + (self._custom_label + custom + "\n\n" if custom else '') \
                           + (self._meta_label + meta if meta else '')

            # If there is a default field configured for this model, use it.
            # If there isn't, put the custom data in a message instead
            if default_field.name:
                if default_field.ttype == 'html' or model.model == 'mail.mail':
                    custom_content = nl2br(custom_content)
                record.update({default_field.name: custom_content})
            else:
                values = {
                    'body': nl2br(custom_content),
                    'model': model.model,
                    'message_type': 'comment',
                    'no_auto_thread': False,
                    'res_id': record.id,
                }
                mail_id = request.env['mail.message'].sudo().create(values)
        record.check_dates()
        return record.id

    # Link all files attached on the form
    def insert_attachment(self, model, id_record, files):
        orphan_attachment_ids = []
        record = model.env[model.model].browse(id_record)
        authorized_fields = model.sudo()._get_form_writable_fields()
        for file in files:
            custom_field = file.field_name not in authorized_fields
            attachment_value = {
                'name': file.field_name if custom_field else file.filename,
                'datas': base64.encodestring(file.read()),
                'datas_fname': file.filename,
                'res_model': model.model,
                'res_id': record.id,
            }
            attachment_id = request.env['ir.attachment'].sudo().create(attachment_value)
            if attachment_id and not custom_field:
                record.sudo()[file.field_name] = [(4, attachment_id.id)]
            else:
                orphan_attachment_ids.append(attachment_id.id)

    @http.route([
        '/my/documents',
    ], type='http', auth="public", website=True)
    def documents(self, **kwargs):
        user = request.env['res.users'].sudo().browse(request.uid)
        documents=request.env['res.partner.documents']
        document = documents.sudo().search([('partner_id', '=', user.partner_id.id)])
        return request.render("nomin_web.my_documents", {
            'document': document,
        })
        
    @http.route([
        '/my/documents/update',
    ], type='http', auth="public", website=True)
    def documents_update(self, **kwargs):
        user = request.env['res.users'].sudo().browse(request.uid)
        documents=request.env['res.partner.documents']
        document = documents.sudo().search([('partner_id', '=', user.partner_id.id)])
        return request.render("nomin_web.my_documents_edit", {
            'document': document,
            'partner': user.partner_id,
        })
        
        
    @http.route([
        '/mydoc/download',
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
            # return redirect(self.orders_page)

        if attachment["type"] == "url":
            if attachment["url"]:
                return http.local_redirect(attachment["url"])
                # return redirect(attachment["url"])
            else:
                return request.not_found()
        elif attachment["datas"]:
            data = StringIO(base64.standard_b64decode(attachment["datas"]))
            return http.send_file(data, filename=attachment['name'], as_attachment=True)
        else:
            return request.not_found()

    @http.route([
    '/save_partner_documents/',
    ], type='http', auth="public", methods=['GET', 'POST'], website=True)
    def save_partner_documents(self, upload=None, **kw):
        user = user = request.env['res.users'].sudo().browse(request.uid)
        partner_id = user.partner_id
        res_partner_documents = request.env['res.partner.documents']
        partner_doc_id = res_partner_documents.sudo().search([('partner_id', '=', partner_id.id)])
        if partner_doc_id:
            for partner in partner_doc_id:
                doc_id = partner
        if not partner_doc_id:
            doc_id = res_partner_documents.create({
                    'partner_id': user.partner_id.id,
                    'name': user.partner_id.name + u' бичиг баримт',
                    'state': 'complete'
                })
            if doc_id and doc_id.partner_id.document_id:
                    doc_id.partner_id.write({'document_id':doc_id.id})
        if doc_id:
            if kw.get('tax', False):
                upload = kw.get('tax')
                attachment_id = self.attachment_create(field_name='p_tax_id',doc_id=doc_id.id,upload=upload) 
            if kw.get('certificate', False):
                upload = kw.get('certificate')
                attachment_id = self.attachment_create(field_name='p_certificate_id',doc_id=doc_id.id,upload=upload) 
            if kw.get('organization', False):
                upload = kw.get('organization')
                attachment_id = self.attachment_create(field_name='p_org_define_id',doc_id=doc_id.id,upload=upload) 
            if kw.get('work_list', False):
                upload = kw.get('work_list')
                attachment_id = self.attachment_create(field_name='p_work_list_id',doc_id=doc_id.id,upload=upload)   
            if kw.get('judgement', False):
                upload = kw.get('judgement')
                attachment_id = self.attachment_create(field_name='p_judgement_define_id',doc_id=doc_id.id,upload=upload)            
            if kw.get('license', False):
                upload = kw.get('license')
                attachment_id = self.attachment_create(field_name='p_spec_license_id',doc_id=doc_id.id,upload=upload)            
            if kw.get('bank', False):
                upload = kw.get('bank')
                attachment_id = self.attachment_create(field_name='p_bank_define_id',doc_id=doc_id.id,upload=upload)            
            if kw.get('vat', False):
                upload = kw.get('vat')
                attachment_id = self.attachment_create(field_name='p_vat_file_id',doc_id=doc_id.id,upload=upload)
            if kw.get('insurance', False):
                upload = kw.get('insurance')
                attachment_id = self.attachment_create(field_name='p_insurance_define_id',doc_id=doc_id.id,upload=upload)
            if kw.get('ins_report', False):
                upload = kw.get('ins_report')
                attachment_id = self.attachment_create(field_name='p_insurance_report_id',doc_id=doc_id.id,upload=upload)
            if kw.get('finance_report', False):
                upload = kw.get('finance_report')
                attachment_id = self.attachment_create(field_name='p_finance_report_id',doc_id=doc_id.id,upload=upload)
            if kw.get('audit_report', False):
                upload = kw.get('audit_report')
                attachment_id = self.attachment_create(field_name='p_audit_report_id',doc_id=doc_id.id,upload=upload)
        
        document = res_partner_documents.sudo().search([('partner_id', '=', user.partner_id.id)])
        return request.render("nomin_web.my_documents", {
            'document': document,
        })

    def attachment_create(self, field_name, doc_id, upload):
        image_data = upload.read()   
        Attachments = request.env['ir.attachment']
        attachment_id = Attachments.create({
                        'name': upload.filename,
                        'datas': image_data.encode('base64'),
                        'datas_fname': upload.filename,
                        'res_model': 'res.partner.documents',
                        field_name: doc_id,
                    })
        return attachment_id

    @http.route('/my/tenders_documents', type='http', auth="public", website=True)
    def my_tenders_documents(self, **kw):
        user = user = request.env['res.users'].sudo().browse(request.uid)
        participants = request.env['tender.participants.bid']
        participant_ids = participants.sudo().search([('partner_id', '=', user.partner_id.id)])
        vals = {
                'part_tenders': participant_ids,                
                }
        
        return request.render("nomin_web.my_tenders_documents", vals)
    
    @http.route('/my/tender_documents/<model("tender.tender"):tender>/', type='http', auth="public", website=True)
    def my_tender_documents_detail(self, tender):
        user = user = request.env['res.users'].sudo().browse(request.uid)
        tenders = request.env['tender.tender']
        participants = request.env['tender.participants.bid']
        participants_lines = request.env['participants.work.task.line']
        
        tender_id = tenders.sudo().search([('id','=',tender.id)])
        participant_id = participants.sudo().search([('partner_id','=', user.partner_id.id),('tender_id','=',tender.id)],limit =1)
        lines = participants_lines.search([('partner_id','=', user.partner_id.id),('tender_id','=',tender.id),('task_id','=',participant_id.id)])
        vals = {
                'tender': tender_id,
                'part_tenders': participant_id, 
                'lines': lines
                }
        return request.render("nomin_web.my_tenders_documents_details", vals)
    
    @http.route('/my/tender_documents/update/<model("tender.tender"):tender>/', type='http', auth="public", website=True)
    def my_tender_documents_detail_update(self, tender):
        user = user = request.env['res.users'].sudo().browse(request.uid)
        tenders = request.env['tender.tender']
        participants = request.env['tender.participants.bid']
        participants_lines = request.env['participants.work.task.line']
        tender = tenders.sudo().search([('id','=',tender.id)])
        participant_id = participants.sudo().search([('partner_id','=', user.partner_id.id),('tender_id','=',tender.id)],limit=1)
        participant_line_ids = participants_lines.search([('partner_id','=', user.partner_id.id),('tender_id','=',tender.id),('task_id','=',participant_id.id)])
        vals = {
                'tender': tender,
                'participant': participant_id.id,
                'part_tenders': participant_id, 
                'lines': participant_line_ids
                }
        return request.render("nomin_web.my_tenders_documents_details_edit", vals)
        

    @http.route([
    '/save_tender/documents/',
    ], type='http', auth="public", methods=['GET', 'POST'], website=True)
    def save_tender_documents(self, upload=None, **kw):
        user = user = request.env['res.users'].sudo().browse(request.uid)
        partner_id = user.partner_id
        
        Attachments = request.env['ir.attachment']
        participants = request.env['tender.participants.bid']
        participants_lines = request.env['participants.work.task.line']
        part_lines = []
        if kw.get('participant'):
            participant = participants.sudo().browse(int(kw.get('participant')))
            tender = participant.tender_id
            partlines = participants_lines.sudo().search([('partner_id','=', user.partner_id.id),('tender_id','=',participant.tender_id.id),('task_id','=',participant.id)])
            
            att_proxy_id = []
            att_technical_id = []
            att_worklist_id = []
            att_requirement_id = []
            att_license_id = []
            att_alternative_id = []
            att_cost_id = []
            att_schedule_id = []
            
            if not participant.t_partner_proxy_id:
                if kw.get('proxy', False):
                    upload = kw.get('proxy')
                    image_data = upload.read()                
                    att_proxy_id = Attachments.create( {
                            'name': upload.filename,
                            'datas': image_data.encode('base64'),
                            'datas_fname': upload.filename,
                            'res_model': 'tender.participants.bid',
                        })
            else:
                if kw.get('proxy', False):
                    upload = kw.get('proxy')
                    image_data = upload.read()                
                    att_proxy_id = Attachments.create({
                            'name': upload.filename,
                            'datas': image_data.encode('base64'),
                            'datas_fname': upload.filename,
                            'res_model': 'tender.participants.bid',
                        })
                    participant.t_partner_proxy_id.unlink()
                else:
                    att_proxy_id = participant.t_partner_proxy_id.id
                
            if not participant.t_partner_technical_id:
                if kw.get('technical', False):
                    upload = kw.get('technical')
                    image_data = upload.read()                
                    att_technical_id = Attachments.create( {
                            'name': upload.filename,
                            'datas': image_data.encode('base64'),
                            'datas_fname': upload.filename,
                            'res_model': 'tender.participants.bid',
                        })
            else:
                if kw.get('technical', False):
                    upload = kw.get('technical')
                    image_data = upload.read()                
                    att_technical_id = Attachments.create( {
                            'name': upload.filename,
                            'datas': image_data.encode('base64'),
                            'datas_fname': upload.filename,
                            'res_model': 'tender.participants.bid',
                        })
                    participant.t_partner_technical_id.unlink()
                else:
                    att_technical_id = participant.t_partner_technical_id.id
                
            if not participant.t_partner_worklist_id:
                if kw.get('work_list', False):
                    upload = kw.get('work_list')
                    image_data = upload.read()                
                    att_worklist_id = Attachments.create({
                            'name': upload.filename,
                            'datas': image_data.encode('base64'),
                            'datas_fname': upload.filename,
                            'res_model': 'tender.participants.bid',
                        })
            else:
                if kw.get('work_list', False):
                    upload = kw.get('work_list')
                    image_data = upload.read()                
                    att_worklist_id = Attachments.create({
                            'name': upload.filename,
                            'datas': image_data.encode('base64'),
                            'datas_fname': upload.filename,
                            'res_model': 'tender.participants.bid',
                        })
                    participant.t_partner_worklist_id.unlink()
                else:
                    att_worklist_id = participant.t_partner_worklist_id.id
                
            if not participant.t_partner_require_id:  
                if kw.get('requirement', False):
                    upload = kw.get('requirement')
                    image_data = upload.read()                
                    att_requirement_id = Attachments.create({
                            'name': upload.filename,
                            'datas': image_data.encode('base64'),
                            'datas_fname': upload.filename,
                            'res_model': 'tender.participants.bid',
                        })
            else:
                if kw.get('requirement', False):
                    upload = kw.get('requirement')
                    image_data = upload.read()                
                    att_requirement_id = Attachments.create({
                            'name': upload.filename,
                            'datas': image_data.encode('base64'),
                            'datas_fname': upload.filename,
                            'res_model': 'tender.participants.bid',
                        })
                    participant.t_partner_require_id.unlink()
                else:
                    att_requirement_id = participant.t_partner_require_id.id
            
            if not participant.t_partner_license_id:
                if kw.get('license', False):
                    upload = kw.get('license')
                    image_data = upload.read()                
                    att_license_id = Attachments.create({
                            'name': upload.filename,
                            'datas': image_data.encode('base64'),
                            'datas_fname': upload.filename,
                            'res_model': 'tender.participants.bid',
                        })
            else:
                if kw.get('license', False):
                    upload = kw.get('license')
                    image_data = upload.read()                
                    att_license_id = Attachments.create( {
                            'name': upload.filename,
                            'datas': image_data.encode('base64'),
                            'datas_fname': upload.filename,
                            'res_model': 'tender.participants.bid',
                        })
                    participant.t_partner_license_id.unlink()
                else:
                    att_license_id = participant.t_partner_license_id.id
                     
            if not participant.t_partner_alternative_id:
                if kw.get('alternative', False):
                    upload = kw.get('alternative')
                    image_data = upload.read()                
                    att_alternative_id = Attachments.create({
                            'name': upload.filename,
                            'datas': image_data.encode('base64'),
                            'datas_fname': upload.filename,
                            'res_model': 'tender.participants.bid',
                        })
            else:
                if kw.get('alternative', False):
                    upload = kw.get('alternative')
                    image_data = upload.read()                
                    att_alternative_id = Attachments.create({
                            'name': upload.filename,
                            'datas': image_data.encode('base64'),
                            'datas_fname': upload.filename,
                            'res_model': 'tender.participants.bid',
                        })
                    participant.t_partner_alternative_id.unlink()
                else:
                    att_alternative_id = participant.t_partner_alternative_id.id
            
            if not participant.t_partner_cost_id:
                if kw.get('cost', False):
                    upload = kw.get('cost')
                    image_data = upload.read()                
                    att_cost_id = Attachments.create({
                            'name': upload.filename,
                            'datas': image_data.encode('base64'),
                            'datas_fname': upload.filename,
                            'res_model': 'tender.participants.bid',
                        })
            else:
                if kw.get('cost', False):
                    upload = kw.get('cost')
                    image_data = upload.read()                
                    att_cost_id = Attachments.create({
                            'name': upload.filename,
                            'datas': image_data.encode('base64'),
                            'datas_fname': upload.filename,
                            'res_model': 'tender.participants.bid',
                        })
                    participant.t_partner_cost_id.unlink()
                else:
                    att_cost_id = participant.t_partner_cost_id.id
                
            if not participant.t_partner_schedule_id:     
                if kw.get('schedule', False):
                    upload = kw.get('schedule')
                    image_data = upload.read()                
                    att_schedule_id = Attachments.create( {
                            'name': upload.filename,
                            'datas': image_data.encode('base64'),
                            'datas_fname': upload.filename,
                            'res_model': 'tender.participants.bid',
                        })
            else:
                if kw.get('schedule', False):
                    upload = kw.get('schedule')
                    image_data = upload.read()                
                    att_schedule_id = Attachments.create({
                            'name': upload.filename,
                            'datas': image_data.encode('base64'),
                            'datas_fname': upload.filename,
                            'res_model': 'tender.participants.bid',
                        })
                    participant.t_partner_schedule_id.unlink()
                else:
                    att_schedule_id = participant.t_partner_schedule_id.id
            
            count = 1
            line_id = []
            checklines = []
            del_ids = []
            booleann=True
            old_work = len(part_lines)
            while (booleann):
                if 'hiddn%d'%count in kw:                                        
                    part_line=participants_lines.sudo().search([('id', '=', kw["hiddn%d"%count])])
                    part_line.write(
                                                        {
                                                            'name':kw["work%d"%count],
                                                            'tender_id': participant.tender_id.id,
                                                            'task_id': participant.id,
                                                            'partner_id': partner_id.id,
                                                            'qty': float(kw["hemjee%d"%count]),
                                                            'unit_price': float(kw["negjune%d"%count]),
#                                                             'amount': float(kw["hemjee%d"%count])*float(kw["negjune%d"%count]),
                                                            'costs_of_materials': float(kw["material%d"%count] or 0),
                                                            'other_costs': float(kw["busadzardal%d"%count] or 0),
#                                                             'line_total_costs': float(kw["hemjee%d"%count])*float(kw["negjune%d"%count])+float(kw["material%d"%count])+float(kw["busadzardal%d"%count])
                                                         })
                    checklines.append(int(kw['hiddn%d'%count]))
                    
                if 'workx%d'%count in kw:                    
                    line = participants_lines.create(
                                                        {
                                                            'name': kw["workx%d"%count],
                                                            'tender_id': participant.tender_id.id,
                                                            'task_id': participant.id,
                                                            'partner_id': partner_id.id,
                                                            'qty': float(kw["hemjeex%d"%count]),
                                                            'unit_price': float(kw["negjunex%d"%count]),
#                                                             'amount': float(kw["hemjeex%d"%count])*float(kw["negjunex%d"%count]),
                                                            'costs_of_materials': float(kw["materialx%d"%count] or 0),
                                                            'other_costs': float(kw["busadzardalx%d"%count] or 0),
#                                                             'line_total_costs': float(kw["hemjeex%d"%count])*float(kw["negjunex%d"%count])+float(kw["materialx%d"%count])+float(kw["busadzardalx%d"%count])
                                                         })                    
                elif count < old_work:
                    _logger.info(u'Үнийн саналын мөр устгалаа, Дугаар: %s',  count)
                else:
                    booleann=False
                    count=0
                count = count + 1
            diffs = list(set(part_lines) - set(checklines))
            for diff in diffs:
                participants_lines.unlink(request.cr, request.uid, diff)
        participant.write(
                                        {
                                            't_partner_proxy_id': att_proxy_id,
                                            't_partner_technical_id': att_technical_id,
                                            't_partner_worklist_id': att_worklist_id,
                                            't_partner_require_id': att_requirement_id,
                                            't_partner_license_id': att_license_id,
                                            't_partner_alternative_id': att_alternative_id,
                                            't_partner_cost_id': att_cost_id,
                                            't_partner_schedule_id': att_schedule_id,
                                            'execute_time': kw.get('execute_time'),
                                            'warranty_time': kw.get('warranty_time'),
                                        })
        
        part_tender = participants.sudo().search([('partner_id','=', user.partner_id.id),('tender_id','=',participant.tender_id.id)],limit=1)
        
        lines = participants_lines.sudo().search([('partner_id','=', user.partner_id.id),('tender_id','=',participant.tender_id.id),('task_id','=',part_tender.id)])
        return request.render("nomin_web.my_tenders_documents_details", {
            'tender': tender,
            'part_tenders': part_tender,
            'lines': lines,
        })     
    
    @http.route('/send/tender/document/<model("tender.tender"):tender>/', type='http', auth="public", website=True)
    def send_tender_documents(self, tender):
        user_id = user = request.env['res.users'].sudo().browse(request.uid)
        
        participants = request.env['tender.participants.bid']
        participants_lines = request.env['participants.work.task.line']
        
        participant_id = participants.sudo().search([('partner_id','=', user_id.partner_id.id),('tender_id','=',tender.id)],limit =1)        
        
        if participant_id:
            lines = participants_lines.sudo().search([('partner_id','=', user_id.partner_id.id),('tender_id','=',tender.id),('task_id','=',participant_id.id)])
            if participant_id.state != 'draft':
                return request.render("nomin_web.thanks", {'tender': tender})
            else:
                participant_id.write({'state': 'sent'})
        return request.render("nomin_web.thanks", {'tender': tender,})
    
    
    @http.route('/my/tenders/history', type='http', auth="public", website=True)
    def my_tender_history(self, **kw):
        user_id = user = request.env['res.users'].sudo().browse(request.uid)
        history_obj = request.env['tender.partner.history']
        
        tender_history = history_obj.sudo().search([('partner_id','=',user_id.partner_id.id)])
        
        vals = {
                'tender_history': tender_history, 
                }
        
        return request.render("nomin_web.my_tender_history", vals)