# -*- coding: utf-8 -*-
##############################################################################
#
#    Asterisk Technologies LLC, Enterprise Management Solution    
#    Copyright (C) 2013-2013 Asterisk Technologies LLC (<http://www.erp.mn>). All Rights Reserved
#
#    Email : unuruu25@gmail.com
#    Phone : 976 + 88005462
#
##############################################################################

from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import api, fields, models, _
from openerp.tools.translate import _
import time
from openerp.osv import osv
from openerp.http import request    
import xlwt
from xlwt import *
from StringIO import StringIO
from io import BytesIO
import base64
import xlsxwriter

def get_sector(self,department_id):
    if department_id:
        self.env.cr.execute("select is_sector from hr_department where id=%s"%(department_id))
        fetched = self.env.cr.fetchone()
        if fetched:
            if fetched[0] == True:
                return department_id
            else:
                self.env.cr.execute("select parent_id from hr_department where id=%s"%(department_id))
                pfetched = self.env.cr.fetchone()
                if pfetched:
                    return get_sector(self,pfetched[0])


class purchase_order_report_wizard(models.TransientModel):
	_name = 'purchase.comparison.report.wizard'
	_inherit = 'abstract.report.model'
	_description = 'Purchase comparison report wizard'

	comparison_id = fields.Many2one('purchase.comparison',string=u'Худалдан авалт харьцуулалт')
	



	@api.model
	def default_get(self, fields):
		"""
		To get default values for the object.
		@param self: The object pointer.
		@param cr: A database cursor
		@param uid: ID of the user currently logged in
		@param fields: List of fields for which we want default values
		@param context: A standard dictionary
		@return: A dictionary with default values for all field in ``fields``
		"""
		result1 = []
		result2 = []

		if self._context is None:
			self._context = {}

		res = super(purchase_order_report_wizard, self).default_get(fields)



		record_id = self._context and self._context.get('active_id', False) or False
		if record_id:
			res.update({'comparison_id': record_id})
	
		return res

	@api.multi
	def export_comparison(self,report_code,context=None):
		if context is None:
			context = {}
		datas={}
		datas['model'] = 'purchase.comparison'
		datas['form'] = self.read(['comparison_id',])[0] 
		state_translation = {'cancel':'Шалгараагүй',
                                                'draft':'Ноорог PO',
                                                'comparison_created':'Харьцуулалт үүссэн',
                                                'approved':'Зөвшөөрсөн',
                                                'confirmed':'Баталсан',
                                                'purchase':'Шалгарсан',
                                                'done':'Дууссан',
                            }
		data = datas['form']

		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)


		title = workbook.add_format({
		'border': 0,
		'bold': 1,
		'align': 'center',
		'valign': 'vcenter',
		# 'text_wrap': 'on',
		'font_size':10,
		'font_name': 'Arial',
		})

		header = workbook.add_format({
		'border': 1,
		'bold': 1,
		'align': 'center',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		'bg_color':'#40E0D0',
		'font_name': 'Arial',
		})

		header_left = workbook.add_format({
		'border': 1,
		'bold': 1,
		'align': 'left',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		'font_name': 'Arial',
		})

		cell_format_left = workbook.add_format({
		'border': 1,
		'bold': 0,
		'align': 'left',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		'font_name': 'Arial',
		})

		cell_format_right = workbook.add_format({
		'border': 1,
		'bold': 0,
		'align': 'right',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		'font_name': 'Arial',
		})

		cell_format_center_1 = workbook.add_format({
		'border': 1,
		'bold': 0,
		'align': 'center',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		'bg_color':'#33ff80',
		'font_name': 'Arial',
		})

		cell_format_center = workbook.add_format({
		'border': 1,
		'bold': 0,
		'align': 'center',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		'font_name': 'Arial',
		})

		cell_format_center_2 = workbook.add_format({
		'border': 1,
		'bold': 0,
		'align': 'center',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		'font_name': 'Arial',
		'bg_color':'#40E0D0',
		})
		cell_float_format_left = workbook.add_format({
		'border': 1,
		'bold': 0,
		'align': 'left',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		# 'bg_color':'#40E0D0',
		'font_name': 'Arial',
		# 'num_format': '000,000.0'
		})
		cell_float_format_left_left = workbook.add_format({
		'border': 0,
		'bold': 1,
		'align': 'left',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		# 'bg_color':'#40E0D0',
		'font_name': 'Arial',
		# 'num_format': '000,000.0'
		})


		cell_float_format_right = workbook.add_format({
		'border': 1,
		'bold': 0,
		'align': 'right',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		'font_name': 'Arial',
		'bg_color':'#40E0D0',
		# 'num_format': '000,000.0'
		})

		cell_float_format_left_bold = workbook.add_format({
		'border': 1,
		'bold': 1,
		'align': 'left',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		'font_name': 'Arial',
		'num_format': '000,000.0'
		})

		cell_float_format_left_left_bold = workbook.add_format({
		'border': 0,
		'bold': 1,
		# 'align': 'left',
		# 'valign': 'vcenter',
		# 'text_wrap': 'on',
		'font_size':10,
		'font_name': 'Arial',
		'num_format': '000,000.0'
		})

		cell_float_format_right_bold = workbook.add_format({
		'border': 1,
		'bold': 1,
		'align': 'right',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		'font_name': 'Arial',
		'bg_color':'#40E0D0',
		'num_format': '000,000.0'
		})

		footer_format_left = workbook.add_format({
		'border': 0,
		'bold': 0,
		# 'align': 'left',
		# 'valign': 'vcenter',
		# 'text_wrap': 'on',
		'font_size':10,
		'font_name': 'Arial',
		})

		footer_format_right = workbook.add_format({
		'border': 0,
		'bold': 0,
		'align': 'right',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		'font_name': 'Arial',
		})

		footer_format_center = workbook.add_format({
		'border': 0,
		'bold': 0,
		'align': 'center',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		'font_name': 'Arial',
		})




		sheet = workbook.add_worksheet()
		sheet.portrait=True
		comparison_id = self.env['purchase.comparison'].sudo().browse(data['comparison_id'])[0]
		sheet.set_column(0,0, 30)
		sheet.write(2, 3, u'Худалдан авалт харьцуулалт:'+comparison_id.name,cell_float_format_left_left_bold )
		sheet.write(3, 0, u'Салбар :'+ comparison_id.sector_id.name  , cell_float_format_left_left_bold )
		sheet.write(4, 0, u'Хэлтэс :'+ comparison_id.department_id.name  ,cell_float_format_left_left_bold )
		sheet.write(5, 0, u' Хариуцагч :'+ comparison_id.user_id.name  ,cell_float_format_left_left_bold)

		row =row1= 6
		col =0
		col1= 1

		sheet.write(row, col, u'', header)
		order_ids = self.env['purchase.order'].search([('comparison_id','=',comparison_id.id)])
		for order in order_ids:
			sheet.merge_range(row,  col+1,row1,col1+1, u'%s' %order.partner_id.name, header)
			sheet.set_column(row,col, 17.5)
			col1=col1+2
			col=col+2
		row =row1= 7
		col =0
		col1= 1
		sheet.write(row,  0, u'Үнийн саналын дугаар', header)
		for order in order_ids:
			sheet.merge_range(row,  col+1,row1, col1+1, u'%s' %order.name, cell_format_center)
			col1=col1+2
			col=col+2
		row =row1= 8
		col =0
		col1= 1
		sheet.write(row,  0, u'Үнийн саналын төлөв', header)
		for order in order_ids:
			sheet.merge_range(row,  col+1,row1,col1+1, u'%s' %state_translation[order.state] , cell_format_center_1 if order.state in ['purchase','done'] else cell_format_center)
			col1=col1+2
			col=col+2
		row =row1= 9
		col =0
		col1= 1
		sheet.write(row, 0, u'Үнийн саналын дүн', header)
		for order in order_ids:
			sheet.merge_range(row, col+1,row1, col1+1, u'%s' %order.amount_total, cell_format_center)
			col1=col1+2
			col=col+2
		row =row1= 10
		col =0
		col1= 1	
		sheet.write(row,  0, u'Бараа', cell_format_center)
		for order in order_ids:
			sheet.write(row,  col+1, u'%s' %'Нэгж үнэ', cell_format_center)
			sheet.write(row,  col1+1, u'%s' %'Тоо хэмжээ', cell_format_center)
			col1=col1+2
			col=col+2

		row =row1= 11
		col =0
		col1= 1	
		products= []
		suppliers = []
		product_prices = {}
		product_qtys = {}

		
		for order in order_ids:
			product_prices [order.partner_id.id] = {}
 			product_qtys [order.partner_id.id] = {}
 			suppliers.append(order.partner_id.id)
			for line in order.order_line:
				if line.product_id.name not in products:
					products.append(line.product_id.name)
				product_prices[order.partner_id.id][line.product_id.name] = line.price_unit if line.price_unit else 0
				product_qtys[order.partner_id.id][line.product_id.name] = line.product_qty if line.product_qty else 0
		col =0
		col1= 2	
		for prod in products:
			sheet.write(row, col, u'%s' %prod, cell_format_center)
			for price in suppliers:
					
				if prod in product_prices[price]:
						
					sheet.write(row,  col+1, u'%s' %product_prices[price][prod], cell_format_center)
				else:
					sheet.write(row, col+1, 0.0, cell_format_center)
				col=col+2

			for qty in suppliers:
				if prod in product_qtys[qty]:
					sheet.write(row,  col1, u'%s' %product_qtys[qty][prod], cell_format_center)
				else:
					sheet.write(row, col1, 0.0, cell_format_center)
				col1=col1+2
			row = row+1
			row1= row1+1
			col =0
			col1= 2
		row+=2
		row1= row	
		col= 1
		indict_rows = {}
		sheet.write(row, 0, u'Үнэлгээ', cell_float_format_left_bold)
		purchase_indicator_ids = self.env['purchase.indicators'].search([('comparison_id','=',comparison_id.id)])
		for indic in purchase_indicator_ids:
			row+=1
			sheet.write(row, 0, u''+indic.indicator_id.name, cell_float_format_left)
			indict_rows.update({indic.indicator_id.name:row})
		partner_ids  = self.env['purchase.partner.comparison'].search([('comparison_id','=',comparison_id.id)])
		for partner_id in partner_ids:
			# sheet.merge_range(row1,  col,row1,col+1, partner_id.total_percent, cell_format_center)
			for indic in partner_id.indicator_ids:
				sheet.merge_range(indict_rows.get(indic.indicator_id.name),  col,indict_rows.get(indic.indicator_id.name),col+1, round(indic.total_percent,2) , cell_format_center)
			col+=2
		row+=1
		col= 1
		sheet.write(row, 0, u'Дундаж', cell_float_format_right_bold)	
		for partner_id in partner_ids:
				sheet.merge_range(row,  col,row,col+1, round(partner_id.total_percent,2), cell_format_center_2)
				col+=2
		row+=2	
		sheet.write(row,  0, u'Нийлүүлэгч сонгосон:' ,cell_float_format_left_left)
		employee_ids = self.env['purchase.indicator.rate.employee'].search([('comparison_id','=',comparison_id.id)])
		for emp in employee_ids:
			row+=1
			sheet.write(row, 0, u''+emp.employee_id.job_id.name+'............../ '+emp.employee_id.name ,footer_format_left )
		
		workbook.close()
		out = base64.encodestring(output.getvalue())
		file_name = u'Худалдан авалт харьцуулалт'
		excel_id = self.env['report.excel.output'].create({'data':out,'name':file_name + '.xlsx'})

		return {
		'name': 'Export Report',
		'view_type':'form',
		'view_mode':'form',
		'res_model':'report.excel.output',
		'res_id':excel_id.id,
		'view_id':False,
		#'context':self._context,
		'type': 'ir.actions.act_window',
		'target':'new',
		'nodestroy': True,
		}
