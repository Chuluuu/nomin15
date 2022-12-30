# -*- coding: utf-8 -*-
##############################################################################
#
#    Asterisk Technologies LLC, Enterprise Management Solution    
#    Copyright (C) 2007-2013 Asterisk Technologies LLC Co.,ltd (<http://www.erp.mn>). All Rights Reserved
#
#    Email : unuruu25@gmail.com
#    Phone : 976 + 88005462
#
##############################################################################
from openerp.tools.translate import _
from openerp import api, fields, models, _
import time
import xlrd
import openerp.netsvc, decimal, base64, os, time, xlrd
from tempfile import NamedTemporaryFile
import logging
_logger = logging.getLogger(__name__)
from openerp.exceptions import UserError, ValidationError
# from datetime import datetime
# from openerp.osv import osv,fields,orm

class import_control_budget(models.Model):
    _name = 'import.control.budget'
    _description = 'Import control budget'
    
    '''
        Хяналтын төсөв импортлох
    '''
    
    # _columns = {
    #     'data': fields.binary('Excel File', required=True),
    #     'control_budget':fields.many2one('control.budget', index=True)
    # }
    data=fields.Binary(string='Excel File', required=True)
    control_budget=fields.Many2one('control.budget', index=True)

    # def default_get(self, cr, uid, fields, context=None):
    #     result = []
    #     if context is None:
    #         context = {}
    #     res = super(import_control_budget, self).default_get(cr, uid, fields, context=context)    
    #     active_id = context and context.get('active_id', False) or False
    #     perform_obj = self.pool.get('control.budget')
    #     perform = perform_obj.browse(cr, uid, active_id)
    #     res.update({
    #                 'control_budget' : perform.id,
    #                 })
    #     return res

    # @api.model
    # def default_get(self, fields):
    #     res = super(import_control_budget, self).default_get(fields)   
    #     context = dict(self._context or {})   
    #     active_id = context and context.get('active_id', False) or False
    #     perform_obj = self.env['control.budget']
    #     perform = perform_obj.browse(active_id)
    #     res.update({
    #                 'control_budget' : perform.id,
    #                 })
        # return res
    
#     def import_data(self, cr, uid, ids, context={}):
#         labor_line_obj = self.pool.get('labor.budget.line')
#         material_line_obj = self.pool.get('material.budget.line')
#         for obj in self.browse(cr, uid, ids, context=context):
#             budget  =self.pool.get('control.budget').browse(cr,uid,obj.control_budget.id)
#             form = self.browse(cr, uid, ids[0])
            
#             fileobj = NamedTemporaryFile('w+')
#             fileobj.write(base64.decodestring(form.data))
#             fileobj.seek(0)
            
#             if not os.path.isfile(fileobj.name):
#                 raise osv.except_osv(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
#             book = xlrd.open_workbook(fileobj.name)
            
#             sheet = book.sheet_by_index(0)
            
#             nrows = sheet.nrows
            
#             rowi = 1
#             data = {}
#             tasks_ids = []
#             while rowi < nrows :
#                 try :
#                     row = sheet.row(rowi)
#                     type = row[0].value
#                     nomin_code        = row[1].value
#                     department_id = self.pool.get('hr.department').search(cr,uid,[('nomin_code', '=', str(nomin_code).split('.')[0])])
#                     department = self.pool.get('hr.department').browse(cr,uid,department_id[0])
                    
#                     if not department:
#                         raise osv.except_osv(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\n "%s" мөр дээр зардал гаргах салбар баганад алдаа гарсан байна шалгаад дахин оролдоно уу!'%str(rowi))
                    
#                     product_code  = row[2].value
#                     product_id = self.pool.get('product.product').search(cr,uid,[('product_code', '=', product_code)])
#                     product = self.pool.get('product.product').browse(cr,uid,product_id[0])
                    
#                     if not department:
#                         raise osv.except_osv(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\n "%s" мөр дээр бараа баганад алдаа гарсан байна шалгаад дахин оролдоно уу!'%str(rowi))
                    
#                     uom_name     = row[3].value
#                     uom_id = self.pool.get('product.uom').search(cr,uid,[('name', '=', uom_name)])
#                     uom = self.pool.get('product.uom').browse(cr,uid,uom_id[0])
#                     if not department:
#                         raise osv.except_osv(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\n "%s" мөр дээр хэмжих нэгж баганад алдаа гарсан байна шалгаад дахин оролдоно уу!'%str(rowi))
                    
#                     qty = row[4].value
#                     price = row[5].value
#                     description = row[6].value
#                     print 'ssss\n\n\n\n\n',department.name,product.name,uom.name,qty,price,description
#                     vals = {
#                             'department_id': department.id,
#                             'product_id': product.id,
#                             'product_uom':uom.id,
#                             'product_uom_qty':qty,
#                             'price_unit':price,
#                             'name':description,
#                             'parent_id':budget.id
#                             }
#                     if str(type).split('.')[0] == '1':
#                         material_line_obj.create(cr, uid, vals, context=context)
#                     else:
#                         if str(type).split('.')[0] == '2':
#                             labor_line_obj.create(cr, uid, vals, context=context)
#                         else:
#                              raise osv.except_osv(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\n "%s" мөр дээр Зардлын төрөл багана дээр алдаа гарсан байна шалгаад дахин оролдоно уу!'%str(rowi))
                        
#                     _logger.warning(u'%s Даалгавар үүслээ'%(description))
#                     rowi += 1
#                 except IndexError :
#                     raise osv.except_osv('Алдаа', 'Индексийн алдаа %s -р мөр дээр ' % rowi)
#             return True    
# import_control_budget()
    @api.multi
    def import_data(self):
        labor_line_obj = self.env['labor.budget.line']
        material_line_obj = self.env['material.budget.line']
        for obj in self:
            
            budget  =self.env['control.budget'].browse((self._context.get('active_ids', [])))
            form = self
            
            fileobj = NamedTemporaryFile('w+')
            fileobj.write(base64.decodestring(form.data))
            fileobj.seek(0)
            
            if not os.path.isfile(fileobj.name):
                raise UserError(_('Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!'))
                
            book = xlrd.open_workbook(fileobj.name)
            
            sheet = book.sheet_by_index(0)
            # print '\n\n\n sheet' , sheet 
            nrows = sheet.nrows
            print '\n\n\n nrows' , nrows
            rowi = 1
            data = {}
            tasks_ids = []
            
            if sheet.name == 'Материалын зардал':
                while rowi < nrows :
                    try :
                        row = sheet.row(rowi)
                        type = row[0].value
                        nomin_code = row[1].value
                        department_id = self.env['hr.department'].search([('nomin_code', '=', str(nomin_code).split('.')[0])])
                        
                        
                        if not department_id:
                            raise UserError(_('Мэдээллийн файлыг уншихад алдаа гарлаа.\n "%s" мөр дээр зардал гаргах салбар баганад алдаа гарсан байна шалгаад дахин оролдоно уу!'%str(rowi)))
                        
                        product_name = row[2].value
                        # product_code  = row[2].value
                        # product_id = self.env['product.product'].search([('product_code', '=', product_code)])
                        # if not product_id:
                        #     raise UserError(_('Мэдээллийн файлыг уншихад алдаа гарлаа.\n "%s" бараа дээр алдаа гарлаа шалгаад дахин оролдоно уу!'%str(product_code)))
                        # if not department_id:
                        #     raise UserError(_('Мэдээллийн файлыг уншихад алдаа гарлаа.\n "%s" мөр дээр хэмжих нэгж баганад алдаа гарсан байна шалгаад дахин оролдоно уу!'%str(rowi)))
                        
                        uom_name = row[3].value
                        uom_id = self.env['product.uom'].search([('name', '=', uom_name)])
                        # if not uom_id:
                        #     raise UserError(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\n "%s" бараа дээр алдаа гарлаа шалгаад дахин оролдоно уу!'%str(uom_name))
                        if not uom_id:
                            raise UserError(_('Мэдээллийн файлыг уншихад алдаа гарлаа.\n "%s" мөр дээр хэмжих нэгж баганад алдаа гарсан байна шалгаад дахин оролдоно уу!'%str(rowi)))
                        
                        qty = row[4].value
                        price = row[5].value
                        # description = row[6].value
                        vals = {
                                'department_id': department_id.id,
                                'product_name': product_name,
                                'product_uom':uom_id.id,
                                'product_uom_qty':qty,
                                'price_unit':price,
                                # 'name':description,
                                'parent_id':budget.id
                                }
                        material_line_obj.create(vals)
                        # if str(type).split('.')[0] == '1':
                            # material_line_obj.create(vals)
                        # else:
                        #     if str(type).split('.')[0] == '2':
                        #         labor_line_obj.create(vals)
                        # else:
                        #     raise UserError((u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\n "%s" мөр дээр Зардлын төрөл багана дээр алдаа гарсан байна шалгаад дахин оролдоно уу!'%str(rowi)))
                            
                        # _logger.warning(u'%s Даалгавар үүслээ'%(description))
                        rowi += 1
                    except IndexError :
                        raise UserError(_('Индексийн алдаа %s -р мөр дээр ' % rowi))
            elif sheet.name == 'Ажиллах хүчний зардал':
                while rowi < nrows :
                    try :
                        row = sheet.row(rowi)
                        nomin_code = row[1].value
                        department_id = self.env['hr.department'].search([('nomin_code', '=', str(nomin_code).split('.')[0])])
                        
                        if not department_id:
                            raise UserError(_('Мэдээллийн файлыг уншихад алдаа гарлаа.\n "%s" мөр дээр зардал гаргах салбар баганад алдаа гарсан байна шалгаад дахин оролдоно уу!'%str(rowi)))
                        uom_name = row[3].value
                        uom_id = self.env['product.uom'].search([('name', '=', uom_name)])[0]
                        if not uom_id:
                            raise UserError(_('Мэдээллийн файлыг уншихад алдаа гарлаа.\n "%s" мөр дээр хэмжих нэгж баганад алдаа гарсан байна шалгаад дахин оролдоно уу!'%str(rowi)))
                        product_name = row[2].value
                        qty = row[4].value
                        price = row[5].value
                        
                        vals = {
                                'department_id': department_id.id,
                                'product_name': product_name,
                                'product_uom':uom_id.id,
                                'product_uom_qty':qty,
                                'price_unit':price,
                                # 'name':description,
                                'parent_id':budget.id
                                }
                        
                        labor_line_obj.create(vals)
                        
                        _logger.warning(u' Даалгавар үүслээ')
                        rowi += 1
                    except IndexError :
                        raise UserError(_('Индексийн алдаа %s -р мөр дээр ' % rowi))
                        
            return True    