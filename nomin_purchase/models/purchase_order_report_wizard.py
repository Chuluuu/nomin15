# -*- coding: utf-8 -*-

from datetime import datetime,timedelta,date
from dateutil import parser
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.translate import _
from odoo.tools.float_utils import float_is_zero, float_compare
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, AccessError
import time
from odoo.osv import osv
from odoo.http import request    
import xlwt
from xlwt import *
from odoo.exceptions import UserError, ValidationError


class purchase_order_report_wizard(models.TransientModel):
    _name = 'purchase.order.report.wizard'
    # TODO FIX LATER
    # _inherit = 'abstract.report.model'
    _description = 'Purchase order report wizard'

    @api.model
    def _get_start_date(self):
        return datetime.strptime(fields.Datetime.now(), '%Y-%m-%d %H:%M:%S')

    @api.model
    def _get_end_date(self):
        return datetime.strptime(fields.Datetime.now(), '%Y-%m-%d %H:%M:%S')
    
    def weeks_between(self, start_date, end_date):
        weeks = rrule.rrule(rrule.WEEKLY, dtstart=start_date, until=end_date)
        return weeks.count()
    
    department_ids = fields.Many2many(comodel_name='hr.department', string='Department') #Хэлтэс
    start_date = fields.Date(string="Date start" , default=_get_start_date) #Эхлэх огноо
    end_date = fields.Date(string='Date end', default=_get_end_date) #Дуусах огноо
    category_ids = fields.Many2many(comodel_name='product.category', string='Product category') #Барааны ангилал
    product_ids = fields.Many2many(comodel_name='product.product', string='Products') #Бараанууд
    year_id     = fields.Selection([(num, str(num)) for num in range(2010, (datetime.now().year)+1 )], 'Choose year') #Сонгож харуулах жил
    
    
    
    def get_export_data(self,report_code,context=None):
        if context is None:
            context = {}
        datas={}
        datas['model'] = 'purchase.requisition.line'
        datas['form'] = self.read(['start_date','end_date','category_ids','department_ids','product_ids','year_id'])[0] 

        data = datas['form']
        
        ezxf = xlwt.easyxf
        style1 = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
        style2 = ezxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin; pattern: pattern solid, fore_color  light_turquoise')
        style3 = ezxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
        style4 = ezxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin; pattern: pattern solid, fore_color  blue')
        style2_1 = ezxf('font: bold off; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
        style2_5 = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
        body_style2 = ezxf('font: bold off; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
        body_style_right = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')

        book = xlwt.Workbook(encoding='utf8')
        sheet = book.add_sheet('Худалдан авалт')
        sheet.portrait=True
        ezxf = xlwt.easyxf

        sheet.write(2, 5, u'Салбараарх худалдан авалтын дүн ба давтамжийн тайлан,/дэлгэрэнгүй/ ', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(3, 0, u'Эхлэх хугацаа :'+  data['start_date'] , ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(4, 0, u'Дуусах хугацаа :'+ data['end_date'], ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        row = 4
        col = 0
#         search_value = [('requisition_id.confirmed_date','>=',data['start_date']),('requisition_id.confirmed_date','<=',data['end_date'])]
#         search_value.append(('state','=','done'))
#         lines = self.env['purchase.requisition.line'].sudo().search(search_value)
#         for line in lines:
#             print 'line       eee' ,line
        # sheet.write_merge(row,row, 1, 21,u'Төсвийн задаргаанууд', style2)
        # sheet.write(row, 0,u'Төслийн нэр', style2)
        row += 1
        sheet.col(0).width = 8000
        project_name_row = row
        sheet.write_merge(row, row+2, col,col, u'Захиалагч', style2)
        sheet.write_merge(row, row+2, col+1, col+1,u'Материалын код', style2)
        sheet.col(col+1).width = 5000
        sheet.write_merge(row, row+2, col+2,col+2,u'Материалын нэр', style2)
        sheet.col(col+2).width = 6000
        sheet.write_merge(row, row+2, col+3, col+3,u'Ангилал', style2)
        sheet.col(col+3).width = 6000
        sheet.write_merge(row, row+2, col+4, col+4,u'Загвар', style2)
        sheet.col(col+4).width = 6000
        sheet.write_merge(row, row+2, col+5, col+5,u'Хэмжих нэгж', style2)
        sheet.write_merge(row, row+2, col+6, col+6,u'Нэгж үнэ', style2)
        start_d = datetime.strptime(self.start_date, '%Y-%m-%d')
        end_d = datetime.strptime(self.end_date, '%Y-%m-%d')
        
        year_ids = self.env['account.fiscalyear'].search([('code','>=',start_d.year),('code','<=',end_d.year)])
        period_ids = self.env['account.period'].search([('date_start','>=',data['start_date']),('date_stop','<=',data['end_date']),('special','=',False)])
        if not period_ids:
            raise ValidationError(_(u'Сонгосон хугацаанд мөчлөг олдохгүй байна!!!'))
#         purchases = self.env['purchase.requisition'].search([('confirmed_date','>=',period_ids[0].date_start),('confirmed_date','<=',period_ids[-1].date_stop),('state','in',('confirmed','sent_to_supply','fulfil_request','fulfill','purchased','done'))])
        purchase_dict = {}
        result_dict = {}
        
        purchase_dict2 = {}
        result_dict2 = {}
        
        year_ids2 = self.env['account.fiscalyear'].search([('code','=',data['year_id'])])
        
        if data['department_ids']:
            departments = self.env['hr.department'].search([('id', 'in',data['department_ids'])])
            req_search_query = "SELECT id FROM purchase_requisition WHERE id IN (SELECT id FROM purchase_requisition WHERE confirmed_date BETWEEN '%s' AND '%s' AND state in ('confirmed','sent_to_supply','fulfil_request','fulfill','purchased','done') AND sector_id in %s) OR id IN (SELECT id FROM purchase_requisition WHERE confirmed_date BETWEEN '%s' AND '%s' AND state in ('confirmed','sent_to_supply','fulfil_request','fulfill','purchased','done') AND sector_id in %s) "%(period_ids[0].date_start,period_ids[-1].date_stop,"("+ ','.join(map(str, departments.ids)) +")",year_ids2.date_start,year_ids2.date_stop,"("+ ','.join(map(str, departments.ids)) +")")
        else:
            req_search_query = "SELECT id FROM purchase_requisition WHERE id IN (SELECT id FROM purchase_requisition WHERE confirmed_date BETWEEN '%s' AND '%s' AND state in ('confirmed','sent_to_supply','fulfil_request','fulfill','purchased','done')) OR id IN (SELECT id FROM purchase_requisition WHERE confirmed_date BETWEEN '%s' AND '%s' AND state in ('confirmed','sent_to_supply','fulfil_request','fulfill','purchased','done')) "%(period_ids[0].date_start,period_ids[-1].date_stop,year_ids2.date_start,year_ids2.date_stop)
        self.env.cr.execute(req_search_query)
        
        req_ids = self.env.cr.fetchall()
        requisitions = self.env['purchase.requisition'].search([('id', 'in',req_ids)])
        

        
        search_value = [('requisition_id','in',requisitions.ids)]
        if data['product_ids']:
            products = self.env['product.product'].search([('id', 'in',data['product_ids'])])
            search_value.append(('product_id','in',products.ids))
        if data['category_ids']:
            catergorys = self.env['product.category'].search([('id', 'in',data['category_ids'])])
            search_value.append(('product_id.categ_id','in',catergorys.ids))
        
        purchase_lines = self.env['purchase.requisition.line'].search(search_value,order='product_id DESC')
        
      
        
        for line in purchase_lines:
            if line.product_id:
                if (line.requisition_id.sector_id ,line.product_id, line.product_price) not in purchase_dict:
                    p_lines = self.env['purchase.requisition.line'].search([('requisition_id.sector_id','=',line.requisition_id.sector_id.id),('product_id','=',line.product_id.id),
                                                                  ('product_price','=',line.product_price)])
                    purchase_dict[line.requisition_id.sector_id,line.product_id,line.product_price]={'department':line.requisition_id.sector_id,
                                                                                                         'product':line.product_id,
                                                                                                         'price':line.product_price,
                                                                                                         'purchase_lines':p_lines}
        result_dict[0] = {'purchase_dict':purchase_dict}
        col= coll=7
        if data['year_id']:
            sheet.write_merge(row, row, coll, col+1, data['year_id'], style2)
            sheet.write_merge(row+1, row+1, col, col+1,data['year_id'], style2)
            sheet.write( row+2,  col, u'Тоо', style2)
            col+=1
            sheet.write( row+2,  col, u'Дүн', style2)
            col+=1
            coll=col
        for year in year_ids:    
            for period in period_ids:
                if period.fiscalyear_id.id ==year.id:
                    sheet.write_merge(row+1, row+1, col, col+1,period.name, style2)
                    sheet.write( row+2,  col, u'Тоо', style2)
                    col+=1
                    sheet.write( row+2,  col, u'Дүн', style2)
                    col+=1
            sheet.write_merge(row, row, coll, col-1, year.name, style2)
            coll=col
        sheet.write_merge(row, row+1, col, col+1,u'Нийт', style2)
        sheet.write( row+2,  col, u'Тоо', style2)
        sheet.write( row+2,  col+1, u'Дүн', style2)
        sheet.write_merge(row, row+2, col+2, col+2,u'Нийт дүнд эзлэх хувь', style2)
        row += 3
        col = 7
#         for line in purchase_lines:
        total_amount = 0.0
        for dict in purchase_dict:
            total_count = 0.0
            for year in year_ids:    
                for period in period_ids:
                    if period.fiscalyear_id.id ==year.id:
                        count = 0.0
                        for p_line in purchase_dict[dict]['purchase_lines']:
                            if p_line.requisition_id.confirmed_date >= period.date_start and p_line.requisition_id.confirmed_date <= period.date_stop:
                                count += p_line.product_qty
                                total_count += p_line.product_qty
                        total_amount += count*purchase_dict[dict]['price']
        last_column = 0
        total_percent = 0.0
        for dict in purchase_dict:
            last_column = 0
            total_count = 0.0
#             if line.product_id:
            column = col
            sheet.write( row,  0, '%s - %s'%(purchase_dict[dict]['department'].nomin_code,purchase_dict[dict]['department'].name), style2_5)
            sheet.write( row,  1, purchase_dict[dict]['product'].product_code, style2_1)
            sheet.write( row,  2, purchase_dict[dict]['product'].name, style2_1)
            sheet.write( row,  3, purchase_dict[dict]['product'].categ_id.name, style2_1)
            sheet.write( row,  4, purchase_dict[dict]['product'].name, style2_1)
            sheet.write( row,  5, purchase_dict[dict]['product'].uom_id.name, style2_1)
            sheet.write( row,  6, purchase_dict[dict]['price'], style2_1)
            count = 0
            for p_line in purchase_dict[dict]['purchase_lines']:
                if p_line.requisition_id.confirmed_date >= year_ids2.date_start and p_line.requisition_id.confirmed_date <= year_ids2.date_stop:
                    count += p_line.product_qty
                    
            sheet.write( row,  column, count, style2_1)
            sheet.write( row,  column+1, count*purchase_dict[dict]['price'], style2_1)
            column +=2
            
            for year in year_ids:    
                for period in period_ids:
                    if period.fiscalyear_id.id ==year.id:
                        count = 0.0
                        for p_line in purchase_dict[dict]['purchase_lines']:
                            if p_line.requisition_id.confirmed_date >= period.date_start and p_line.requisition_id.confirmed_date <= period.date_stop:
                                count += p_line.product_qty
                                total_count += p_line.product_qty
#                             if p_line.requisition_id.confirmed_date >= year_ids2.date_start and p_line.requisition_id.confirmed_date <= year_ids2.date_stop:
#                                 total_count += p_line.product_qty
                        sheet.write( row,  column, count, style2_1)
                        column+=1
                        sheet.write( row,  column, count*purchase_dict[dict]['price'], style2_1)
                        column+=1
            last_column += column 
            sheet.write( row,  last_column, total_count, style2)
            sheet.write( row,  last_column+1, total_count*purchase_dict[dict]['price'], style2)
            s_price = (total_count*purchase_dict[dict]['price'])*100
            total_percent += s_price/total_amount
            sheet.write( row,  last_column+2, round(((total_count*purchase_dict[dict]['price']*100.0)/total_amount),2), style2)
            row+=1
        sheet.write( row,  last_column+1, total_amount, style2)
        sheet.write( row,  last_column+2, total_percent, style2)
        return {'data':book}




