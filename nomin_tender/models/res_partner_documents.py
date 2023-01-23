# -*- coding: utf-8 -*-

import re
from odoo.exceptions import Warning
from odoo.tools.translate import _
import datetime, time
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


from odoo import api, fields, models, tools
class ir_attachment(models.Model):
    _inherit = 'ir.attachment'
    '''Хавсралт файлууд'''

    p_tax_id = fields.Many2one('res.partner.documents', string ='Tax pdf')
    p_certificate_id = fields.Many2one('res.partner.documents','Certificate pdf')
    p_spec_license_id = fields.Many2one('res.partner.documents','Special license')
    p_vat_file_id = fields.Many2one('res.partner.documents','VAT PDF')
    p_org_define_id = fields.Many2one('res.partner.documents','Organization define')
    p_judgement_define_id = fields.Many2one('res.partner.documents','Judgement define pdf')
    p_bank_define_id = fields.Many2one('res.partner.documents','Bank define pdf')
    p_insurance_define_id = fields.Many2one('res.partner.documents','Insurance define pdf')
    p_technical_define_id = fields.Many2one('res.partner.documents','Technical define pdf')
    p_work_list_id = fields.Many2one('res.partner.documents','Work history pdf')
    p_insurance_report_id = fields.Many2one('res.partner.documents','Insurance report pdf')
    p_finance_report_id = fields.Many2one('res.partner.documents','Finance report pdf')
    p_audit_report_id = fields.Many2one('res.partner.documents','Audit report pdf')
    date_end = fields.Date(string="Date end")

class res_partner_documents(models.Model):
    _name="res.partner.documents"
    _description = 'Basic registration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    '''Харилцагчийн бичиг баримт
    '''
    
    name                    = fields.Char('Tender info')
    partner_id              = fields.Many2one('res.partner', 'Current partner', ondelete='CASCADE')
    company_info            = fields.Many2one('ir.attachment','Partner Document')
    tax_ids                 = fields.One2many('ir.attachment','p_tax_id', 'Tax pdf', required = False) #Татварын албаны тодорхойлолт
    certificate_ids         = fields.One2many('ir.attachment','p_certificate_id', 'Certificate pdf', required = False) #Гэрчилгээ
    spec_license_ids        = fields.One2many('ir.attachment','p_spec_license_id', 'Special license pdf', required = False) #Тусгай зөвшөөрөл
    vat_file_ids            = fields.One2many('ir.attachment','p_vat_file_id','VAT PDF', required = False) #НӨАТ
    org_define_ids          = fields.One2many('ir.attachment','p_org_define_id','Organization define pdf', required = False) #Байгууллагын тодорхойлолт
    judgement_define_ids    = fields.One2many('ir.attachment','p_judgement_define_id','Judgement define pdf', required = False) #Шүүхийн тодорхойлолт
    bank_define_ids         = fields.One2many('ir.attachment','p_bank_define_id','Bank define pdf', required = False) #Банкны тодорхойлолт
    insurance_define_ids    = fields.One2many('ir.attachment','p_insurance_define_id','Insurance define pdf', required = False) #НД газрын тодорхойлолт
    technical_define_ids    = fields.One2many('ir.attachment','p_technical_define_id','Technical define pdf', required = False) #Техникийн тодорхойлолт
    work_list_ids           = fields.One2many('ir.attachment','p_work_list_id','Work history pdf', required = False) #Гүйцэтгэсэн ажлын жагсаалт
    insurance_report_ids    = fields.One2many('ir.attachment','p_insurance_report_id','Insurance report pdf', required = False) #НДаатгалын тайлан
    finance_report_ids      = fields.One2many('ir.attachment','p_finance_report_id','Finance report pdf', required = False) #Санхүүгийн тодорхойлолт
    audit_report_ids        = fields.One2many('ir.attachment','p_audit_report_id','Audit report pdf') #Аудитын тайлан
    state                   = fields.Selection([('complete','Complete Document'),('expired',u'Хүчинтэй хугацаа дууссан'),('incomplete','Incomplete Document')], string='Status', tracking=True,copy=False, default='incomplete')
    
    
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        '''Харилцагч сонгоход харилцагчийн нэрний урд бичиг баримт нэмж харуулах'''
        if self.partner_id:
            self.name = u'Бичиг баримт' + self.partner_id.name
        return 

    
    def write(self, vals):
        '''Харилцагчийг бичиг баримтанд давхар сонгосон эсэхийг шалгаж байна'''
        if vals.get('partner_id'):
            for document in self:
                if document.partner_id.id != vals.get('partner_id'):
                    raise UserError(_(u'Харилцагчийн бичиг баримт давхар үүсэх тул анх үүсгэсэн харилцагчийн оруулж өгнө үү.!!!'))
        return super(res_partner_documents, self).write(vals)
    
    
    def action_confirm(self):
        '''Харилцагчийн бичиг баримтын төлвийг бичиг баримт бүрдсэн болгоно'''
        self.state = 'complete'
        for doc in self:
            doc.partner_id.document_id = doc.id

    
    def check_document_expiredates(self):
        self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_tax_id and B.date_end is not null order by B.date_end desc limit 1 ")
        records = self.env.cr.dictfetchall()
        for record in records:
            self.env.cr.execute("update res_partner_documents set state='expired' where id=%s"%record['id'])
        
        self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_certificate_id and B.date_end is not null order by B.date_end desc limit 1 ;")
        records = self.env.cr.dictfetchall()
        for record in records:
            self.env.cr.execute("update res_partner_documents set state='expired' where id=%s"%record['id'])

        self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_audit_report_id and B.date_end is not null order by B.date_end desc limit 1 ;")
        records = self.env.cr.dictfetchall()
        for record in records:
            self.env.cr.execute("update res_partner_documents set state='expired' where id=%s"%record['id'])

        self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_finance_report_id and B.date_end is not null order by B.date_end desc limit 1 ;")
        records = self.env.cr.dictfetchall()
        for record in records:
            self.env.cr.execute("update res_partner_documents set state='expired' where id=%s"%record['id'])

        self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_vat_file_id and B.date_end is not null order by B.date_end desc limit 1 ;")
        records = self.env.cr.dictfetchall()
        for record in records:
            self.env.cr.execute("update res_partner_documents set state='expired' where id=%s"%record['id'])

        self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_spec_license_id and B.date_end is not null order by B.date_end desc limit 1 ;")
        records = self.env.cr.dictfetchall()
        for record in records:
            self.env.cr.execute("update res_partner_documents set state='expired' where id=%s"%record['id'])

        self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_org_define_id and B.date_end is not null order by B.date_end desc limit 1 ;")
        records = self.env.cr.dictfetchall()
        for record in records:
            self.env.cr.execute("update res_partner_documents set state='expired' where id=%s"%record['id'])

        self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_judgement_define_id and B.date_end is not null order by B.date_end desc limit 1 ;")
        records = self.env.cr.dictfetchall()
        for record in records:
            self.env.cr.execute("update res_partner_documents set state='expired' where id=%s"%record['id'])

        self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_bank_define_id and B.date_end is not null order by B.date_end desc limit 1 ;")
        records = self.env.cr.dictfetchall()
        for record in records:
            self.env.cr.execute("update res_partner_documents set state='expired' where id=%s"%record['id'])
        self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_insurance_define_id and B.date_end is not null order by B.date_end desc limit 1 ;")
        records = self.env.cr.dictfetchall()
        for record in records:
            self.env.cr.execute("update res_partner_documents set state='expired' where id=%s"%record['id'])
        self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_technical_define_id and B.date_end is not null order by B.date_end desc limit 1 ;")
        records = self.env.cr.dictfetchall()
        for record in records:
            self.env.cr.execute("update res_partner_documents set state='expired' where id=%s"%record['id'])

    
    
    def partner_document_running(self):
        '''Харилцагчийн бичиг баримтын хугацаа шалгана'''
        file_duration =self.env['partner.file.duration']
        file_type =self.env['partner.file.type']
        duration_id = file_duration.search([('is_active','=',True)])
        if duration_id :
            cer_type_id = file_type.search([('file_id','=',duration_id[0]),('name','=','certificate')])
            if cer_type_id :
                cer_type = file_type.browse(cer_type_id[0])
                cer_day = cer_type.duration_day
            else:
                cer_day = 10000
            
            lic_type_id = file_type.search([('file_id','=',duration_id[0]),('name','=','spec_license')])
            if lic_type_id :
                license_type = file_type.browse(lic_type_id[0])
                license_day = license_type.duration_day
            else:
                license_day = 10000
            
            vat_type_id = file_type.search([('file_id','=',duration_id[0]),('name','=','vat_file')])
            if vat_type_id :
                vat_type = file_type.browse(vat_type_id[0])
                vat_day = vat_type.duration_day
            else:
                vat_day = 10000
                    
            org_type_id = file_type.search([('file_id','=',duration_id[0]),('name','=','org_define')])
            if org_type_id :
                org_type = file_type.browse(org_type_id[0])
                org_day = org_type.duration_day
            else:
                org_day = 10000
                    
            judgement_type_id = file_type.search([('file_id','=',duration_id[0]),('name','=','judgement')])
            if judgement_type_id :
                judgement_type = file_type.browse(judgement_type_id[0])
                judgement_day = judgement_type.duration_day
            else:
                judgement_day = 10000
                    
            bank_type_id = file_type.search([('file_id','=',duration_id[0]),('name','=','bank')])
            if bank_type_id :
                bank_type = file_type.browse(bank_type_id[0])
                bank_day = bank_type.duration_day
            else:
                bank_day = 10000
                
            insur_type_id = file_type.search([('file_id','=',duration_id[0]),('name','=','insurance_def')])
            if insur_type_id :
                insur_type = file_type.browse(insur_type_id[0])
                insur_day = insur_type.duration_day
            else:
                insur_day = 10000
                    
            tech_type_id = file_type.search([('file_id','=',duration_id[0]),('name','=','technical_def')])
            if tech_type_id :
                tech_type = file_type.browse(tech_type_id[0])
                tech_day = tech_type.duration_day
            else:
                tech_day = 10000
                    
            work_type_id = file_type.search([('file_id','=',duration_id[0]),('name','=','work')])
            if work_type_id :
                work_type = file_type.browse(work_type_id[0])
                work_day = work_type.duration_day
            else:
                work_day = 10000
                    
            ins_rep_type_id = file_type.search([('file_id','=',duration_id[0]),('name','=','insurance_rep')])
            if ins_rep_type_id :
                ins_rep_type = file_type.browse(ins_rep_type_id[0])
                ins_rep_day = ins_rep_type.duration_day
            else:
                ins_rep_day = 10000
                    
            finance_type_id = file_type.search([('file_id','=',duration_id[0]),('name','=','finance')])
            if  finance_type_id :
                finance_type = file_type.browse(finance_type_id[0])
                finance_day = finance_type.duration_day
            else:
                finance_day = 10000
                        
            audit_type_id = file_type.search([('file_id','=',duration_id[0]),('name','=','audit')])
            if  audit_type_id:
                audit_type = file_type.browse(audit_type_id[0])
                audit_day = audit_type.duration_day
            else:
                audit_day = 10000
        
        DATE_FORMAT = '%Y-%m-%d'
        date_now=  datetime.now()
        date_now = date_now.strftime(DATE_FORMAT)
        date = False
        

#         query = "select doc.id as document_id, ir.id as attachment_id, ir.create_date as ir_create_date, doc.state as state \
#                 from res_partner_documents as doc, ir_attachment as ir where ir.p_certificate_id=doc.id and ir.create_date < now();"
                
                
        self.env.cr.execute = "select doc.id document_id, Max(ir.create_date) as ir_create_date from res_partner_documents as doc, ir_attachment as ir \
                where doc.state='complete' and ir.p_certificate_id=doc.id and ir.create_date < now() group by document_id order by document_id;"
        #cr.execute(query)
        cer_obj = self.env.cr.dictfetchall()
        is_in_cer = False
        for cer_document in cer_obj:
            date = cer_document['ir_create_date']
            date_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
            end_date = date_time + timedelta(days=cer_day)
            end_date = end_date.strftime(DATE_FORMAT)
            if end_date <= date_now:
                is_in_cer = True
                #self.pool.get('ir.attachment').write(cr, uid, cer_document['attachment_id'],{'status': False}, context=None)
             
                 
                if is_in_cer == True:
                    self.env['res.partner.documents'].browse(cer_document['document_id']).write({'state': 'incomplete'})
                    
                    
                    
        self.env.cr.execute   = "select doc.id as document_id, Max(ir.create_date) as ir_create_date from res_partner_documents as doc, ir_attachment as ir \
                        where ir.p_spec_license_id=doc.id and doc.state = 'complete' and ir.create_date < now() group by document_id order by document_id;"
         
        #cr.execute(license_query)
        lic_obj = self.env.cr.dictfetchall()
         
        is_in_lic = False
        for lic_document in lic_obj:
            date = lic_document['ir_create_date']
            date_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
            end_date = date_time + timedelta(days=license_day)
            end_date = end_date.strftime(DATE_FORMAT)
            
              
            if end_date <= date_now:
                is_in_lic = True
                   
                if is_in_lic == True:
                    self.env['res.partner.documents'].browse(lic_document['document_id']).write({'state': 'incomplete'})
#                 
                
        
        is_in_vat = False
        self.env.cr.execute       = "select doc.id as document_id, Max(ir.create_date) as ir_create_date from res_partner_documents as doc, ir_attachment as ir \
                        where ir.p_vat_file_id=doc.id and doc.state = 'complete' and ir.create_date < now() group by document_id order by document_id;"
        #cr.execute(vat_query)
        vat_document_obj = self.env.cr.dictfetchall()
          
        for vat_document in vat_document_obj:
            date = vat_document['ir_create_date']
            date_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
            end_date = date_time + timedelta(days=vat_day)
            end_date = end_date.strftime(DATE_FORMAT)
            if end_date <= date_now:
                is_in_vat = True
                  
                if is_in_vat == True:
                    self.env['res.partner.documents'].browse(vat_document['document_id']).write({'state': 'incomplete'})
                    
                    
        

        is_in_org = False
        self.env.cr.execute       = "select doc.id as document_id, Max(ir.create_date) as ir_create_date from res_partner_documents as doc, ir_attachment as ir \
                        where ir.p_org_define_id=doc.id and doc.state = 'complete' and ir.create_date < now() group by document_id order by document_id;"
        #cr.execute(org_query)
        org_def_obj = self.env.cr.dictfetchall()
          
        for org_document in org_def_obj:
            date = org_document['ir_create_date']
            date_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
            end_date = date_time + timedelta(days=org_day)
            end_date = end_date.strftime(DATE_FORMAT)
            if end_date <= date_now:
                is_in_org = True
                  
                if is_in_org == True:
                    self.env['res.partner.documents'].browse(org_document['document_id']).write({'state': 'incomplete'})
                    
                    
                    
                    
        is_in_judge = False
        self.env.cr.execute     = "select doc.id as document_id, Max(ir.create_date) as ir_create_date from res_partner_documents as doc, ir_attachment as ir \
                            where ir.p_judgement_define_id=doc.id and doc.state = 'complete' and ir.create_date < now() group by document_id order by document_id;"
        #cr.execute(judgement_query)
        judgement_obj = self.env.cr.dictfetchall()
          
        for judge_document in judgement_obj:
            date = judge_document['ir_create_date']
            date_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
            end_date = date_time + timedelta(days=judgement_day)
            end_date = end_date.strftime(DATE_FORMAT)
            if end_date <= date_now:
                is_in_judge = True
                  
                if is_in_judge == True:
                    self.env['res.partner.documents'].browse(judge_document['document_id']).write({'state': 'incomplete'})
                    
                                
        is_in_bank = False
        self.env.cr.execute       = "select doc.id as document_id, Max(ir.create_date) as ir_create_date from res_partner_documents as doc, ir_attachment as ir \
                        where ir.p_bank_define_id=doc.id and doc.state = 'complete' and ir.create_date < now() group by document_id order by document_id;"
        #cr.execute(bank_query)
        bank_obj = self.env.cr.dictfetchall()
          
        for bank_document in bank_obj:
            date = bank_document['ir_create_date']
            date_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
            end_date = date_time + timedelta(days=bank_day)
            end_date = end_date.strftime(DATE_FORMAT)
            if end_date <= date_now:
                is_in_bank = True
                  
                if is_in_bank == True:
                    self.env['res.partner.documents'].browse(bank_document['document_id']).write({'state': 'incomplete'})
                                                    
        
        is_in_insur = False
        self.env.cr.execute    = "select doc.id as document_id, Max(ir.create_date) as ir_create_date from res_partner_documents as doc, ir_attachment as ir \
                        where ir.p_insurance_define_id=doc.id and doc.state = 'complete' and ir.create_date < now() group by document_id order by document_id;"
        #cr.execute(ins_def_query)
        ins_def_obj = self.env.cr.dictfetchall()
          
        for ins_def_doc in ins_def_obj:
            date = ins_def_doc['ir_create_date']
            date_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
            end_date = date_time + timedelta(days=insur_day)
            end_date = end_date.strftime(DATE_FORMAT)
            if end_date <= date_now:
                is_in_insur = True
                  
                if is_in_insur == True:
                    self.env['res.partner.documents'].browse(ins_def_doc['document_id']).write({'state': 'incomplete'})
                    
        is_in_tech = False
        self.env.cr.execute    = "select doc.id as document_id, Max(ir.create_date) as ir_create_date from res_partner_documents as doc, ir_attachment as ir \
                        where ir.p_technical_define_id=doc.id and doc.state = 'complete' and ir.create_date < now() group by document_id order by document_id;"
        #cr.execute(tech_query)
        tech_obj = self.env.cr.dictfetchall()
          
        for tech_document in tech_obj:
            date = tech_document['ir_create_date']
            date_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
            end_date = date_time + timedelta(days=tech_day)
            end_date = end_date.strftime(DATE_FORMAT)
            if end_date <= date_now:
                is_in_tech = True
                  
                if is_in_tech == True:
                    self.env['res.partner.documents'].browse(tech_document['document_id']).write({'state': 'incomplete'})
                    
                                                                            
        is_in_work = False
        self.env.cr.execute    = "select doc.id as document_id, Max(ir.create_date) as ir_create_date from res_partner_documents as doc, ir_attachment as ir \
                        where ir.p_work_list_id=doc.id and doc.state = 'complete' and ir.create_date < now() group by document_id order by document_id;"
        #cr.execute(work_query)
        work_obj = self.env.cr.dictfetchall()
          
        for work_document in work_obj:
            date = work_document['ir_create_date']
            date_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
            end_date = date_time + timedelta(days=work_day)
            end_date = end_date.strftime(DATE_FORMAT)
            if end_date <= date_now:
                is_in_work = True
                  
                if is_in_work == True:
                    self.env['res.partner.documents'].browse(work_document['document_id']).write({'state': 'incomplete'})
                    
                    
        is_in_ins_rep = False
        self.env.cr.execute    = "select doc.id as document_id, Max(ir.create_date) as ir_create_date from res_partner_documents as doc, ir_attachment as ir \
                        where ir.p_insurance_report_id=doc.id and doc.state = 'complete' and ir.create_date < now() group by document_id order by document_id;"
        #cr.execute(ins_rep_query)
        ins_rep_obj = self.env.cr.dictfetchall()
          
        for ins_rep_document in ins_rep_obj:
            date = ins_rep_document['ir_create_date']
            date_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
            end_date = date_time + timedelta(days=ins_rep_day)
            end_date = end_date.strftime(DATE_FORMAT)
            if end_date <= date_now:
                is_in_ins_rep = True
                  
                if is_in_ins_rep == True:
                    self.env['res.partner.documents'].browse(ins_rep_document['document_id']).write({'state': 'incomplete'})
                                                        
        is_in_finance = False
        self.env.cr.execute    = "select doc.id as document_id, Max(ir.create_date) as ir_create_date from res_partner_documents as doc, ir_attachment as ir \
                        where ir.p_finance_report_id=doc.id and doc.state = 'complete' and ir.create_date < now() group by document_id order by document_id;"
        #cr.execute(finance_query)
        finance_obj = self.env.cr.dictfetchall()
          
        for finance_document in finance_obj:
            date = finance_document['ir_create_date']
            date_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
            end_date = date_time + timedelta(days=finance_day)
            end_date = end_date.strftime(DATE_FORMAT)
            if end_date <= date_now:
                is_in_finance = True
                  
                if is_in_finance == True:
                    self.env['res.partner.documents'].browse(finance_document['document_id']).write({'state': 'incomplete'})
                    
                                                                        
        is_in_audit = False
        self.env.cr.execute    = "select doc.id as document_id, Max(ir.create_date) as ir_create_date from res_partner_documents as doc, ir_attachment as ir \
                        where ir.p_audit_report_id=doc.id and doc.state = 'complete' and ir.create_date < now() group by document_id order by document_id;"
        #cr.execute(audit_query)
        audit_obj = self.env.cr.dictfetchall()
        for audit_document in audit_obj:
            date = audit_document['ir_create_date']
            date_time = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
            end_date = date_time + timedelta(days=audit_day)
            end_date = end_date.strftime(DATE_FORMAT)
            if end_date <= date_now:
                is_in_audit = True
                  
                if is_in_audit == True:
                    self.env['res.partner.documents'].browse(audit_document['document_id']).write({'state': 'incomplete'})

    
    def unlink(self):
        '''Нооргоос бусад үед устгах боломжгүй'''
        for document in self:
            if document.state == 'complete':
                raise UserError(_(u'Та бичиг баримтыг бүрдээгүй төлөвт устгах боломжтой.'))
        return super(res_partner_documents, self).unlink()  


class res_partner(models.Model):
    _name="res.partner"
    _inherit = 'res.partner'
    _description = 'Basic registration'
    '''Харилцагч'''
    tender_type_ids = fields.Many2many('tender.type', 'tender_type_res_partner_rel', 'partner_id', 'type_id', string = "Tender Bid Type")
    document_id = fields.Many2one('res.partner.documents','Partner Document')
    
    
    
class partner_file_type(models.Model):
    _name="partner.file.type"
    _description = "Partner File Type"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    '''Харилцагчийн бичиг баримтын хугацаа тохируулах'''
    
    name = fields.Selection([('tax','Tax'),
                                            ('certificate','Certificate'),('spec_license','Special license'),('vat_file','VAT'),
                                            ('org_define','Organization define'),('judgement','Judgement define'),('bank','Bank define'),
                                            ('insurance_def','Insurance define'),('work','Work history'),
                                            ('insurance_rep','Insurance report'),('finance','Finance report'),('audit','Audit report'),
                                            ], string='Document type', tracking=True,copy=False)
    duration_day = fields.Integer('Duration days',tracking=True)
    is_required = fields.Boolean('Is required',default=False,tracking=True)
    file_id = fields.Many2one('partner.file.duration', 'Partner file', ondelete='restrict',tracking=True)
    
                    
class partner_file_duration(models.Model):
    _name = "partner.file.duration"
    _description = "File duration"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    '''Бичиг баримтын төрөл'''

    name = fields.Char('Name',tracking=True)
    duration_ids = fields.One2many('partner.file.type', 'file_id', string='Document duration',tracking=True)
    is_active = fields.Boolean('Is Active', default=False,tracking=True)

class PartnerDocuments(models.Model):
    _inherit = 'res.partner.documents'


    
    def check_dates(self):
        
        self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_tax_id and B.date_end is not null and B.date_end >now() and a.id=%s order by b.date_end desc limit 1 ;"%self.id)
        records = self.env.cr.dictfetchall()
        tax_false =False
        if records:
            tax_false=True


        self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_certificate_id and B.date_end is not null and B.date_end >now() and a.id=%s order by b.date_end desc limit 1 ;"%self.id)
        records = self.env.cr.dictfetchall()
        cert_false=False
        if records:
            cert_false =True

        self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_audit_report_id and B.date_end is not null and B.date_end >now() and a.id=%s order by b.date_end desc limit 1 ;"%self.id)
        records = self.env.cr.dictfetchall()
        
        audit_false= False
        if records:
            audit_false=True

        self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_finance_report_id and B.date_end is not null and B.date_end >now() and a.id=%s order by b.date_end desc limit 1 ;"%self.id)
        records = self.env.cr.dictfetchall()
        fin_false = False
        if records:
            fin_false=True
        self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_vat_file_id and B.date_end is not null and B.date_end >now() and a.id=%s order by b.date_end desc limit 1 ;"%self.id)
        records = self.env.cr.dictfetchall()
        vat_false =False
        if records:
            vat_false=True

        self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_spec_license_id and B.date_end is not null and B.date_end >now() and a.id=%s order by b.date_end desc limit 1 ;"%self.id)
        records = self.env.cr.dictfetchall()
        lic_false=False
        if records:
            lic_false=True


        self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_org_define_id and B.date_end is not null and B.date_end >now() and a.id=%s order by b.date_end desc limit 1 ;"%self.id)
        records = self.env.cr.dictfetchall()
        org_false = False
        if records:
            org_false =True

        self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_judgement_define_id and B.date_end is not null and B.date_end >now() and a.id=%s order by b.date_end desc limit 1 ;"%self.id)
        records = self.env.cr.dictfetchall()
        jud_false =False
        if records:        
            jud_false=True

        self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_bank_define_id and B.date_end is not null and B.date_end >now() and a.id=%s order by b.date_end desc limit 1 ;"%self.id)
        records = self.env.cr.dictfetchall()
        bank_false = False
        if records:
            bank_false = True

        self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_insurance_define_id and B.date_end is not null and B.date_end >now() and a.id=%s order by b.date_end desc limit 1 ;"%self.id)
        records = self.env.cr.dictfetchall()
        insu_false = False
        if records:
            insu_false =True

        # self.env.cr.execute("select A.id from res_partner_documents A inner join ir_attachment B ON A.id =B.p_technical_define_id and B.date_end is not null and B.date_end >now() and a.id=%s order by b.date_end desc limit 1 ;"%self.id)
        # records = self.env.cr.dictfetchall()
        # tech_false = False
        if records:
            tech_false =True
                
        if insu_false and bank_false and org_false and lic_false and vat_false and fin_false and audit_false and cert_false and tax_false:
            self.env.cr.execute("update res_partner_documents set state='complete' where id=%s"%self.id)