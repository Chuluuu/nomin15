# -*- coding: utf-8 -*-

from odoo.tools.translate import _
from odoo import api, fields, models, _
import time
import xlrd
import odoo.netsvc, decimal, base64, os, time, xlrd
from tempfile import NamedTemporaryFile
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, ValidationError

class import_control_budget(models.Model):
    _name = 'import.control.budget'
    _description = 'Import control budget'
    
    '''
        Хяналтын төсөв импортлох
    '''
    
    data=fields.Binary(string='Excel File', required=True)
    control_budget=fields.Many2one('control.budget', index=True)

    
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
            nrows = sheet.nrows
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
                        uom_id = self.env['uom.uom'].search([('name', '=', uom_name)])
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
                        uom_id = self.env['uom.uom'].search([('name', '=', uom_name)])[0]
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