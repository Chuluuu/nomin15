# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools.translate import _
import time
import xlwt
from xlwt import *
from operator import itemgetter
import logging
_logger = logging.getLogger(__name__)
class distributed_purchase_requisition(models.TransientModel):
    _name = 'distributed.purchase.requisition'
    # TODO FIX LATER inherited from l10_mn_report_base
    # _inherit = 'abstract.report.model'
    
    
    def get_export_data(self,report_code,context=None):
        active_ids = self.env.context.get('active_ids', [])
        
        datas={}
        datas['model'] = 'purchase.requisition.line'
        datas['form'] = self.read() 

        data = datas['form']
        
        ezxf = xlwt.easyxf
        style1 = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
        style2 = ezxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin; pattern: pattern solid, fore_color  light_turquoise')
        style3 = ezxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
        style4 = ezxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin; pattern: pattern solid, fore_color  blue')
        style2_1 = ezxf('font: bold off; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
        body_style2 = ezxf('font: bold off; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
        body_style_right = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
        
        book = xlwt.Workbook(encoding='utf8')
        sheet = book.add_sheet('Миний захиалгууд')
         
        sheet.portrait=True
        ezxf = xlwt.easyxf
 
        sheet.write(2, 4, u'Салбаруудын бараа захиалгын нэгтгэл ', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        row = 3
        col = 1
        
        sheet.col(0).width = 8000
        sheet.col(1).width = 5000
        sheet.col(2).width = 8000
        sheet.col(3).width = 1000
        sheet.col(4).width = 3500
        sheet.col(5).width = 5000
        sheet.col(6).width = 2000
        sheet.col(7).width = 2000
        sheet.col(8).width = 3000
        sheet.col(9).width = 3000
        sheet.col(10).width = 4000
        sheet.col(11).width = 6000
        sheet.col(12).width = 6000
        sheet.col(13).width = 6000
        
        requisition_lines = self.env['purchase.requisition.line'].search([('id','in', active_ids)])
        
        
        purchase_dict = {}
        count = 1
        for reqline in requisition_lines:
            requisition_id = reqline.requisition_id.id
            histories = self.env['request.history'].search([('requisition_id','=', requisition_id),('type','=', 'confirmed')])
#             histories[-1]
            if reqline.requisition_id.department_id:
                group = reqline.requisition_id.department_id.name
                
            if group not in purchase_dict:
                purchase_dict [group] = {
                    'department':u'Тодорхойгүй',
                    'requisitions':{}
                    }
            
            purchase_dict [group]['department']= group
            group1 = reqline.requisition_id.name
        
            if group1 not in purchase_dict[group]['requisitions']:
                purchase_dict[group]['requisitions'][group1] = {
                    'requisition':u'Тодорхойгүй',
                    'comment':u'Тодорхойгүй',
                    'confirmed_date':u'Тодорхойгүй',
                    'confirmed_user':u'Тодорхойгүй',
                    'products':{},
                    }
    
            purchase_dict[group]['requisitions'][group1]['requisition']= group1
            purchase_dict [group]['requisitions'][group1]['comment'] = reqline.requisition_id.comment
            date = ''
            for history in histories:
                if history.date > date:
                    date = history.date 
                    purchase_dict [group]['requisitions'][group1]['confirmed_date'] = history.date
                    purchase_dict [group]['requisitions'][group1]['confirmed_user'] = history.user_id.name
            group2 =reqline.id
            if group2 not in purchase_dict[group]['requisitions'][group1]['products']:
                purchase_dict [group]['requisitions'][group1]['products'][group2]= {
                                                        'product_code':u'Тодорхойгүй',
                                                        'product_name':u'Тодорхойгүй',
                                                        'product_qty':0.0,
                                                        'product_mark':u'Тодорхойгүй',
                                                        'price_unit':0.0,
                                                        'uom':u'Тодорхойгүй',
                                                        'total':0.0,
                                                        }
            count+=1
            purchase_dict [group]['requisitions'][group1]['products'][group2]['product_code']= reqline.product_id.product_code if reqline.product_id.product_code else  u'Тодорхойгүй'
            purchase_dict [group]['requisitions'][group1]['products'][group2]['product_qty']= float(reqline.product_qty) if reqline.product_qty else 0.0
            purchase_dict [group]['requisitions'][group1]['products'][group2]['product_mark']= reqline.product_id.product_mark if reqline.product_id.product_mark else  u'Тодорхойгүй'
            purchase_dict [group]['requisitions'][group1]['products'][group2]['product_price']= float(reqline.product_price) if reqline.product_price else 0.0
            purchase_dict [group]['requisitions'][group1]['products'][group2]['total']= reqline.amount if reqline.amount else  0.0
            purchase_dict [group]['requisitions'][group1]['products'][group2]['product_name']= reqline.product_id.name if reqline.product_id.name  else u'Тодорхойгүй'        
            purchase_dict [group]['requisitions'][group1]['products'][group2]['schedule_date']= reqline.schedule_date if reqline.schedule_date  else u'Тодорхойгүй'        
            purchase_dict [group]['requisitions'][group1]['products'][group2]['product_desc']= reqline.product_desc if reqline.product_desc  else u'Тодорхойгүй'        
            purchase_dict [group]['requisitions'][group1]['products'][group2]['qty']= float(reqline.allowed_qty) if reqline.allowed_qty  else u'Тодорхойгүй'
            purchase_dict [group]['requisitions'][group1]['products'][group2]['uom']= reqline.product_uom_id.name if reqline.product_uom_id.name  else u'Тодорхойгүй'
        
        total_amount = 0
        if purchase_dict:
            row += 2
            col = 7
            for line in sorted(purchase_dict.values(), key=itemgetter('department')):
                deptotal = 0
                sheet.write(row, 0, u'Салбарын нэр', style2)
                sheet.write(row, 1, u'Шаардахын дугаар', style2)
                sheet.write(row, 2, u'Зориулалт', style2)
                sheet.write(row, 3, u'', style2)
                sheet.write(row, 4, u'', style2)
                sheet.write(row, 5, u'', style2)
                sheet.write(row, 6, u'', style2)
                sheet.write(row, 7, u'', style2)
                sheet.write(row, 8, u'', style2)
                sheet.write(row, 9, u'', style2)
                sheet.write(row, 10, u'', style2)
                sheet.write(row, 11, u'', style2)
                sheet.write(row, 12, u'Баталсан хэрэглэгч', style2)
                sheet.write(row, 13, u'Баталсан огноо', style2)
                row += 1
                sheet.write(row, 0, line['department'], style2_1)
                
                for requisition in sorted(line['requisitions'].values(), key=itemgetter('requisition')):
                    reqtotal = 0
                    sheet.write(row, 1, requisition['requisition'], style3)
                    sheet.write(row, 2, requisition['comment'], style3)
                    sheet.write(row, 3, u'№', style3)
                    sheet.write(row, 4, u'Барааны код', style3)
                    sheet.write(row, 5, u'Барааны нэр', style3)
                    sheet.write(row, 6, u'Хэмжих нэгж', style3)
                    sheet.write(row, 7, u'Тоо ширхэг', style3)
                    sheet.write(row, 8, u'Нэгж үнэ', style3)
                    
                    sheet.write(row, 9, u'Нийт дүн', style3)
                    sheet.write(row, 10, u'Хүсч буй огноо', style3)
                    sheet.write(row, 11, u'Зориулалт', style3)
                    sheet.write(row, 12, requisition['confirmed_user'], style3)
                    sheet.write(row, 13, requisition['confirmed_date'], style3)
                    count=1
                    row += 1
                    for product in sorted(requisition['products'].values(), key=itemgetter('product_code')):
                        sheet.write(row, 0, u'', style2_1)
                        sheet.write(row, 1, u'', style2_1)
                        sheet.write(row, 2, u'', style2_1)
                        sheet.write(row, 3, u'%s'%(count), style2_1)
                        sheet.write(row, 4, product['product_code'], style2_1)
                        sheet.write(row, 5, product['product_name'], style2_1)
                        sheet.write(row, 6, product['uom'], style2_1)
                        sheet.write(row, 7, product['qty'], style2_1)
                        sheet.write(row, 8, product['product_price'], style2_1)
                        _logger.info(u'\n\n\n\n\n\n\n\n-------------------------product_code', product['product_code'],'\n\n\n\n')
                        if product['qty']:
                            
                            if isinstance(product['qty'],float):
                                qty = product['qty']
                            elif isinstance(product['qty'],int):
                                qty=product['qty']
                            elif isinstance(product['qty'],list):
                                
                                qty=product['qty'][0]
                            else:
                                qty=product['qty']
                            
                        
                        else:
                            qty =0
                        if product['product_price']:
                            
                            if isinstance(product['product_price'],float):
                                price = product['product_price']
                            elif isinstance(product['product_price'],int):
                                price = product['product_price']
                            elif isinstance(product['product_price'],list):
                                price = product['product_price'][0]
                            else:
                                price = product['product_price']
                            
                        else:
                            price = 0
                        sheet.write(row, 9,qty * price , style2_1)
                        reqtotal+= product['qty']*product['product_price']
                        sheet.write(row, 10, product['schedule_date'], style2_1)
                        sheet.write(row, 11, product['product_desc'], style2_1)
                        sheet.write(row, 12, u'', style2_1)
                        sheet.write(row, 13, u'', style2_1)
                        row += 1
                        count += 1
                    sheet.write(row, 0, u'', style2_1)
                    sheet.write(row, 1, u'',style2_1)
                    sheet.write(row, 2, u'', style2_1)
                    sheet.write(row, 3, u'',style2_1)
                    sheet.write(row, 4, u'', style2_1)
                    sheet.write(row, 5, u'',style2_1)
                    sheet.write(row, 6, u'', style2_1)
                    sheet.write(row, 7, u'',style2_1)
                    sheet.write(row, 8, u'Нийт дүн', style2_1)
                    sheet.write(row, 9, u''+str(reqtotal),style2_1)
                    sheet.write(row, 10, u'', style2_1)
                    sheet.write(row, 11, u'',style2_1)
                    sheet.write(row, 12, u'', style2_1)
                    sheet.write(row, 13, u'',style2_1)
                    deptotal += reqtotal
                    row += 1
                    
                sheet.write(row, 0, u'', style2_1)
                sheet.write(row, 1, u'',style2_1)
                sheet.write(row, 2, u'', style2_1)
                sheet.write(row, 3, u'',style2_1)
                sheet.write(row, 4, u'', style2_1)
                sheet.write(row, 5, u'',style2_1)
                sheet.write(row, 6, u'', style2_1)
                sheet.write(row, 7, u'',style2_1)
                sheet.write(row, 8, u'НИЙТ', style3)
                sheet.write(row, 9, u''+str(deptotal), style3)
                sheet.write(row, 10, u'', style2_1)
                sheet.write(row, 11, u'',style2_1)
                sheet.write(row, 12, u'', style2_1)
                sheet.write(row, 13, u'',style2_1)
                total_amount += deptotal
                row += 1
                
        
        row += 3
        sheet.write(row, 7, u'Нийт', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(row, 8, u''+str(total_amount), ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        
        return {'data':book}
        

