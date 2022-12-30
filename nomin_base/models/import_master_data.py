# -*- coding: utf-8 -*-
##############################################################################
#
#    Asterisk Technologies LLC, Enterprise Management Solution    
#    Copyright (C) 2007-2012 Asterisk Technologies LLC (<http://www.erp.mn>). All Rights Reserved
#
#    Email : unurjargal@asterisk-tech.mn
#    Phone : 976 + 88005462
#
##############################################################################
from openerp import models, fields, api 
from openerp.tools.translate import _
from openerp.exceptions import UserError
from datetime import date, datetime
import time
import xlrd, base64, os
from tempfile import NamedTemporaryFile
import logging
_logger = logging.getLogger(__name__)
from openerp.osv import  osv

class import_account_tax(models.TransientModel):
    '''НӨТ Үзүүлэлт
    '''
    _name = 'import.account.tax'
    _description = 'Import TAX'
    
    data = fields.Binary(string='File', required=True)
    sector_id = fields.Many2one('hr.department','Sector',domain=[('is_sector','=',True)])
    
#     _columns = {
#         'data': fields.binary('File', required=True),
#         'sector_id': fields.many2one('hr.department','Sector',domain=[('is_sector','=',True)]),
#     }
    
    @api.multi
    def update_data(self):
        account_tax = self.env['account.tax']
        form = self
        
        fileobj = NamedTemporaryFile('w+')
        fileobj.write(base64.decodestring(form.data))
        fileobj.seek(0)
        if not os.path.isfile(fileobj.name):
            UserError (u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
        
        book = xlrd.open_workbook(fileobj.name)
        sheet = book.sheet_by_index(0)
        nrows = sheet.nrows
        rowi = 1
        while rowi < nrows :
            try:
                row = sheet.row(rowi)
                
                code = row[0].value
                if type(code) is float:
                    code = str(code).split(".")[0]
                    
                name = row[1].value
                
                if code and name:
                    tax = account_tax.search(cr, uid, [('name','=',name)])
                    if tax:
                        for f in tax:
                            account_tax.write(cr, uid, [f], {'code':code})
                rowi += 1
                print rowi
            except IndexError :
                raise osv.except_osv('Error', 'Excel sheet must be 10 columned : error on row %s ' % rowi)
        return True
    
    @api.multi
    def import_data(self):
        account_tax = self.env['account.tax']        
        sector_id=self.sector_id.id
        
        fileobj = NamedTemporaryFile('w+')
        fileobj.write(base64.decodestring(self.data))
        fileobj.seek(0)
        if not os.path.isfile(fileobj.name):
            raise osv.except_osv(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
        
        book = xlrd.open_workbook(fileobj.name)
        sheet = book.sheet_by_index(0)
        nrows = sheet.nrows
        rowi = 1
        while rowi < nrows :
            try:
                row = sheet.row(rowi)
                
                code = row[0].value
                if type(code) is float:
                    code = str(code).split(".")[0]
                    
                name = row[1].value
                # Түр файл импортлов
                # bank_partner_id = self.env['res.partner.bank'].sudo(6721).browse(int(code))
                # print 'bank_partner_id',bank_partner_id
                # # if bank_partner_id.active:
                # bank_partner_id.write({'active':False})
                # bank_partner_id.message_post(body=u"Буруу бүртгэгдсэн данс болон харилцагчгүй, банк сонгоогүй данс архивлав.")
                ex_type = row[2].value
                type1 = 'purchase'
                if ex_type == u'Борлуулалт':
                    type1 = 'sale'
                    
                if sector_id and code and name and type1:
                      account_tax_id = account_tax.create({'code':code,
                                                   'name':name,
                                                   'department_id':sector_id,
                                                   'type_tax_use':type1,
                                                   'amount':10,
                                                   'price_include':True
                                                   })
                rowi += 1
                print rowi
            except IndexError :
                raise UserError('Error', 'Excel sheet must be 10 columned : error on row %s ' % rowi)
        return True


class import_account_analytic_account(models.TransientModel):
    '''Шинжилгээний данс импортлох
    '''
    _name = 'import.account.analytic.account'
    _description = 'Import Analytic Account'
    

    data = fields.Binary('File', required=True)
    sector_id = fields.Many2one('hr.department','Sector',domain=[('is_sector','=',True)])
    
    @api.multi
    def import_cashflow(self):
        
        
        return True
    @api.multi
    def import_data(self):
        account_analytic = self.env['account.analytic.account']
        fileobj = NamedTemporaryFile('w+')
        fileobj.write(base64.decodestring(self.data))
        fileobj.seek(0)
        if not os.path.isfile(fileobj.name):
            raise UserError(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
        book = xlrd.open_workbook(fileobj.name)
        sheet = book.sheet_by_index(0)
        nrows = sheet.nrows
        rowi = 2
        while rowi < nrows :
            try:
                row = sheet.row(rowi)
                
                code = row[0].value
                if type(code) is float:
                    code = str(code).split(".")[0]
                name = row[1].value
                
                parent_code = row[2].value
                if type(parent_code) is float:
                    parent_code = str(parent_code).split(".")[0]
                parent_name = row[3].value
                
                dep_nomin_code = row[4].value
                if type(dep_nomin_code) is float:
                    dep_nomin_code = str(dep_nomin_code).split(".")[0]
                department_id=False
                if dep_nomin_code:
                    cr.execute("select id from hr_department where nomin_code='%s' order by id desc limit 1"%(dep_nomin_code))
                    fetched = cr.fetchone()
                    if fetched:
                        department_id=fetched[0]
                
                parent_id=False
                if parent_code:
                    cr.execute("select id from account_analytic_account where code='%s' and name = '%s' order by id desc limit 1"%(parent_code,parent_name))
                    fetched = cr.fetchone()
                    if fetched:
                        parent_id=fetched[0]
                      #  code = '%s-%s'%(fetched[1], code)
                    else:
                        "parent_code : " , parent_code
                
                
              #  level = row[5].value
        #        cparent_id=False
                if code and name:
                      account_analytic_id = account_analytic.create({'code':code,
                                                   'name':name,
                                                   'type':'budget',
                                                   'parent_id':parent_id,
                                                   'department_id':department_id
                                                   })
                print rowi
                rowi += 1
            except IndexError :
                raise UserError('Error', 'Excel sheet must be 10 columned : error on row %s ' % rowi)
        return True
    

    
class import_res_partner(models.TransientModel):
    _name = 'import.res.partner'
    _description = 'Import Res Partner'
    

    data= fields.Binary('File')

    @api.multi
    def dans_update(self):
        account_obj = self.env['account.account']
        account_type_obj = self.env['account.account.type']
        department_obj = self.env['hr.department']
        currency_obj = self.env['res.currency']
        account_id=False
           
        _logger.info(u'Данс үүсгэх функц уншиж эхэллээ!')
           
        self.env.cr.execute("select user_type_id, id from account_account where department_id=206")
        fetched = self.env.cr.fetchall()
        if fetched:
            count = 1
            for f in fetched:
                user_type = f[0]
                acc_id = f[1]
                account_id = account_obj.browse(acc_id)
                account_id.write({'user_type_id':user_type})
                # account_obj.write([acc_id],{})
                count += 1
                _logger.warning(u'Дугаар : %s, Данс ID: %s!'%(count, acc_id))
    @api.multi
    def import_partner(self):
        '''ХАРИЛЦАГЧ ИМПОРТ ХИЙХ
        '''
        
        form = self
        fileobj = NamedTemporaryFile('w+')
        fileobj.write(base64.decodestring(form.data))
        fileobj.seek(0)
        if not os.path.isfile(fileobj.name):
            raise osv.except_osv(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
          
        book = xlrd.open_workbook(fileobj.name)
        sheet = book.sheet_by_index(0)
        nrows = sheet.nrows
        rowi = 2
        while rowi < nrows :
            try:
                row = sheet.row(rowi)
                  
                nomin_code = row[0].value
                if type(nomin_code) is float:
                    nomin_code = str(nomin_code).split(".")[0]
                try:
                    lastname = row[1].value 
                except:
                    lastname = ''

                name = row[2].value
                code = row[3].value
                if type(code) is float:
                    code = str(code).split(".")[0]
                try:
                    address = row[4].value
                except:
                    address=''
                try:
                    website = row[5].value
                except:
                    website=''
                
                try:
                    mobile =  str(row[6].value).split(".")[0]
                except:
                    mobile=''
                try:
                    email = row[7].value
                except:
                    email =''
                try:
                    is_vat = row[8].value
                except:
                    is_vat=''
                vat = False
                if is_vat == 'Y':
                    vat=True
                try:
                    register = row[9].value
                except:
                    register =''

                if type(register) is float:
                    register = str(register).split('.')[0]
                try:
                    type1 = row[10].value
                except:
                    type1 = ''

                customer=False
                supplier=False
                customer=True
                supplier = True
                if type1 == '[CUS]':
                    customer=True
                else:
                    supplier = True
                try:
                    is_person = row[11].value 
                except:
                    is_person =''
                company_type='company'
                
                if is_person == 'Y':
                    company_type = 'person'
                try:    
                    comment = row[17].value
                except:
                    comment=''
                # if nomin_code or code:
                #     self.env.cr.execute("select id from res_partner where nomin_code='%s'"%(nomin_code))
                #     fetched = self.env.cr.fetchall()
                #     if not fetched:
                #         partner = self.env['res.partner']
                #         partner.create({'name':name,
                #                             'code':code, 
                #                         'street':address, 
                #                         'is_vat':vat,
                #                         'registry_number':register,
                #                         'customer':customer,
                #                         'supplier':supplier,
                #                         'company_type':company_type,
                #                         'nomin_code':nomin_code,
                #                         'last_name':lastname,
                #                         'comment':comment,
                #                         'mobile':mobile,
                #                         'email':email,
                #                         'website':website
                #                         })
                #     else:
                #         if code :
                #             self.env.cr.execute("select id from res_partner where code='%s'"%(code))
                #             fetched = self.env.cr.fetchall()
                #             if not fetched:
                #                 partner = self.env['res.partner']
                #                 partner.create({'name':name,
                #                             'code':code, 
                #                         'street':address, 
                #                         'is_vat':vat,
                #                         'registry_number':register,
                #                         'customer':customer,
                #                         'supplier':supplier,
                #                         'company_type':company_type,
                #                         'nomin_code':nomin_code,
                #                         'last_name':lastname,
                #                         'comment':comment,
                #                         'mobile':mobile,
                #                         'email':email,
                #                         'website':website
                #                         })            

                if code and name:
                    self.env.cr.execute("select id from res_partner where code='%s'"%(code))
                    fetched = self.env.cr.fetchall()
                    if fetched:
                        for part in fetched:
                            partner = self.env['res.partner'].browse(part[0])
                            partner.write(
                                                        {'name':name,
                                                         'code':code, 
                                                        'street':address, 
                                                        'is_vat':vat,
                                                        'registry_number':register,
                                                        'customer':customer,
                                                        'supplier':supplier,
                                                        'company_type':company_type,
                                                        'nomin_code':nomin_code,
                                                        'comment':comment,
                                                        'last_name':lastname,
                                                        'mobile':mobile,
                                                        'email':email,
                                                        'website':website
                                                            })
                    else:
                        if nomin_code:
                            self.env.cr.execute("select id from res_partner where nomin_code='%s'"%(nomin_code))
                            fetched = self.env.cr.fetchall()
                            if fetched:
                                for part in fetched:
                                    partner = self.env['res.partner'].browse(part[0])
                                    partner.write(
                                                                {'name':name,
                                                                 'code':code, 
                                                                'street':address, 
                                                                'is_vat':vat,
                                                                'registry_number':register,
                                                                'customer':customer,
                                                                'supplier':supplier,
                                                                'company_type':company_type,
                                                                'nomin_code':nomin_code,
                                                                'last_name':lastname,
                                                                'comment':comment,
                                                                'mobile':mobile,
                                                                'email':email,
                                                                'website':website
                                                                    })
                            else:
                                partner = self.env['res.partner']
                                partner.create({'name':name,
                                                     'code':code, 
                                                    'street':address, 
                                                    'is_vat':vat,
                                                    'registry_number':register,
                                                    'customer':customer,
                                                    'supplier':supplier,
                                                    'company_type':company_type,
                                                    'nomin_code':nomin_code,
                                                    'last_name':lastname,
                                                    'comment':comment,
                                                    'mobile':mobile,
                                                    'email':email,
                                                    'website':website
                                                    })
                        else:
                            partner = self.env['res.partner']
                            partner.create({'name':name,
                                                     'code':code, 
                                                    'street':address, 
                                                    'is_vat':vat,
                                                    'registry_number':register,
                                                    'customer':customer,
                                                    'supplier':supplier,
                                                    'company_type':company_type,
                                                    'last_name':lastname,
                                                    'nomin_code':nomin_code,
                                                    'comment':comment,
                                                    'mobile':mobile,
                                                    'email':email,
                                                    'website':website
                                                    })
                  
                print rowi
                rowi += 1
            except IndexError :
                raise osv.except_osv('Error', 'Excel sheet must be 10 columned : error on row %s ' % rowi)
        return True

    @api.multi    
    def import_partner1(self):
          partner_ids = []

          #ГЭРЭЭ
          self.env.cr.execute("select customer_company from contract_management")
          fetched = self.env.cr.fetchall()
          if fetched:
              print "GEREEE" , len(fetched)
              for f in fetched:
                  partner_ids.append(f[0])
                  
          #ИЛГЭЭСЭН БИЧИГ
          self.env.cr.execute("select receiver from send_document")
          fetched1 = self.env.cr.fetchall()
          if fetched1:
              print "SEND DOC" , len(fetched1)
              for f1 in fetched1:
                  partner_ids.append(f1[0])
                  
          #ХҮЛЭЭН АВСАН БИЧИГ
          self.env.cr.execute("select where_from from received_document")
          fetched2 = self.env.cr.fetchall()
          if fetched2:
              print "REC DOC", len(fetched2)
              for f2 in fetched2:
                  partner_ids.append(f2[0])          
          #КОМ
          self.env.cr.execute("select partner_id from res_company")
          fetched3 = self.env.cr.fetchall()
          if fetched3:
              print "COMPANY", len(fetched3)
              for f3 in fetched3:
                  partner_ids.append(f3[0])          
                            
          #КАЛ
          self.env.cr.execute("select res_partner_id from calendar_event_res_partner_rel")
          fetched4 = self.env.cr.fetchall()
          if fetched4:
              print "CALENDAR", len(fetched4)
              for f4 in fetched4:
                  partner_ids.append(f4[0])
          
          #ХЭРЭГЛЭГЧ
          self.env.cr.execute("select partner_id from res_users")
          fetched5 = self.env.cr.fetchall()
          if fetched5:
              print "USER", len(fetched5)
              for f5 in fetched5:
                  partner_ids.append(f5[0])
          
          #АЖИЛТАН
          self.env.cr.execute("select address_home_id from hr_employee")
          fetched6 = self.env.cr.fetchall()
          if fetched6:
              print "EMPLO", len(fetched6)
              for f6 in fetched6:
                  partner_ids.append(f6[0])
                  
          #ХАРИЛЦАГЧ
          self.env.cr.execute("select id from res_partner where employee=True")
          fetched7 = self.env.cr.fetchall()
          if fetched7:
              print "PART IN EMP", len(fetched7)
              for f7 in fetched7:
                  partner_ids.append(f7[0])
          
          #ТУСЛАМЖ
          self.env.cr.execute("select partner_id from crm_helpdesk where partner_id is not null")
          fetched8 = self.env.cr.fetchall()
          if fetched8:
              print "HELPDESK", len(fetched8)
              for f8 in fetched8:
                  partner_ids.append(f8[0])
                  
          #САЛБАР
          self.env.cr.execute("select partner_id from hr_department where partner_id is not null")
          fetched9 = self.env.cr.fetchall()
          if fetched9:
              print "DEPART", len(fetched9)
              for f9 in fetched9:
                  partner_ids.append(f9[0])
          print "LEN1 : " , len(partner_ids)
          partner_ids = list(set(partner_ids))
          print "LEN2 : ", len(partner_ids)
          partner_ids.remove(None)
          print "LEN2 : ", len(partner_ids)
          self.env.cr.execute("delete from res_partner where id not in %s"%(str(tuple(partner_ids))))
          self.env.cr.commit()
          
          return {}
      
   
  
        


