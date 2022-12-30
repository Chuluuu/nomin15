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
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _
from openerp.tools.float_utils import float_is_zero, float_compare
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError, AccessError
import time
from openerp.osv import osv
from openerp.http import request    
import xlwt
from xlwt import *
from StringIO import StringIO
import xlsxwriter
from operator import itemgetter
from io import BytesIO
import base64

class purchase_order_supplier_report_wizard(models.TransientModel):
	_name = 'purchase.receive.report.wizard'
	_inherit = 'abstract.report.model'
	_description = 'Purchase order report wizard'

	start_date = fields.Date(string=u"Эхлэх огноо" , required=True)
	end_date = fields.Date(string=u'Дуусах огноо',required=True)
	department_ids = fields.Many2many(comodel_name='hr.department', string=u'Хэлтэс')
	

	@api.multi
	def export_report(self,report_code,context=None):
		if context is None:
			context = {}
		datas={}
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)

		header = workbook.add_format({'border':1,'fg_color':'#b0e2ff','align':'justify','valign':'vjustify','text_wrap':100,'pattern':0})

		style2 = workbook.add_format({'border':True,'align':'justify','valign':'vjustify','text_wrap':100,'pattern':0})
		style3 = workbook.add_format({'border':True,'align':'justify','num_format': '0.00%','valign':'vjustify','text_wrap':100,'pattern':0})

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
		'font_size':8,
		'bg_color':'#b0e2ff',
		'font_name': 'Arial',
		})

		header_color = workbook.add_format({
		'border': 1,
		'bold': 1,
		'align': 'center',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':8,
		'bg_color':'#E0E0E0',
		'font_name': 'Arial',
		})

		header_font_color = workbook.add_format({
		'border': 1,
		'bold': 1,
		'align': 'center',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':8,
		'bg_color':'#b0e2ff',
		'font_color':'red',
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
		'bold': 1,
		'align': 'left',
		'valign': 'vcenter',
		'bg_color':'#b0e2ff',
		'text_wrap': 'on',
		'font_size':8,
		'font_name': 'Arial',
		})

		cell_format_left_color = workbook.add_format({
		'border': 1,
		'bold': 1,
		'align': 'left',
		'valign': 'vcenter',
		'bg_color':'#E0E0E0',
		'text_wrap': 'on',
		'font_size':8,
		'font_name': 'Arial',
		})

		cell_format_left_font_color = workbook.add_format({
		'border': 1,
		'bold': 1,
		'align': 'left',
		'valign': 'vcenter',
		'bg_color':'#b0e2ff',
		'text_wrap': 'on',
		'font_size':8,
		'font_color':'red',
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

		report_type = {
			'detailed':'Дэлгэрэнгүй',
			'summary':'Хураангуй',
		}
		

		sheet = workbook.add_worksheet()
	
		sheet.portrait=True
		sheet.write(2, 2, u'Бараа хүлээн авалтын тайлан',title)
		sheet.write(3, 0, u'Эхлэх хугацаа :'+ self.start_date ,)
		sheet.write(4, 0, u'Дуусах хугацаа :'+ self.end_date, )
		row = 4
		col = 0
		
	
		query = "select sector.name as sector , sp.name as pick_name, sm.name as move_name ,pt.name as product,pt.product_code,uom.name as uom_name ,sm.product_qty as move_qty,sm.price_unit as price_unit, pr.name,prl.allowed_qty as allowed_qty\
					from stock_picking sp\
						left join stock_picking_type spt\
							on spt.id=sp.picking_type_id\
						left join stock_move sm\
							on sm.picking_id = sp.id\
						join  product_product pp\
							on pp.id=sm.product_id\
						join product_template pt\
							on pt.id=pp.product_tmpl_id\
						join product_uom uom\
							on uom.id=pt.uom_id\
						join purchase_requisition pr\
							on pr.id=sp.requisition_id\
						join purchase_requisition_line prl\
							on (prl.requisition_id = pr.id and prl.id=sm.requisition_line_id)\
						join hr_department sector\
							on sector.id=pr.sector_id\
						where spt.code='outgoing' and sp.state ='done'"
		domain = "and sp.create_date between '%s' and '%s' "%(self.start_date,self.end_date)
		if self.department_ids:
			domain = domain + "and pr.sector_id in (%s)"%(self.department_ids.id)
		query = query+domain
		self.env.cr.execute(query)
		dictfetchall = self.env.cr.dictfetchall()
		
		product_dict = {}
		count=1
		if dictfetchall:
			# sheet.write(row, col, u'№',header)
			
			# sheet.merge_range(row, col+1, row, col+3,u'Бараа бүтээгдэхүүн', header)
			# sheet.write(row, col+4,u'Барааны код', header)
			# sheet.set_column(row,col+4,10)
			# sheet.write(row, col+5, u'Барааны Нэр', header)
			# sheet.set_column(row,col+5, 25)
			# sheet.write(row, col+6, u'Баталгаат хугацаа', header)
			# sheet.set_column(row,col+6, 20)
			# sheet.write(row,  col+7,u'Хэмжих нэгж', header)
			# sheet.set_column(row,col+7, 15)
			# sheet.write(row, col+8,u'Тоо', header)
			# sheet.set_column(row,col+8, 10)
			# sheet.write(row, col+9,u'Нэгж үнэ', header)
			# sheet.set_column(row,col+9, 15)
			# sheet.write(row,col+10,u'НӨАТ-гүй дүн', header)
			# sheet.set_column(row,col+10, 15)
			# sheet.write(row,  col+11,u'НӨАТ', header)
			# sheet.set_column(row,col+11, 15)
			# sheet.write(row,  col+12,u'НИЙТ', header)
			# sheet.set_column(row,col+12, 15)
			for line in dictfetchall:
				group = False
				group1 = False
				group2 = False
				group3 = False

				if line['sector']:
					group = line['sector']
					
				if group not in product_dict:
					product_dict [group]= {
					'sector':u'Тодорхойгүй',
					'products':{},					
					}


				product_dict [group]['sector']= group
				

				group1 =line['product']

				if group1 not in product_dict[group]['products']:
					product_dict[group]['products'][group1] = {
					'product':u'Тодорхойгүй',
					'product_code':u'Тодорхойгүй',
					'product_uom':u'Тодорхойгүй',
					'price_units':{},
					}
		
					product_dict[group]['products'][group1]['product']= group1
					product_dict[group]['products'][group1]['product_code']= line['product_code']
					product_dict[group]['products'][group1]['product_uom']= line['uom_name']
					
					group2  = line['price_unit']

					if group2 not in product_dict[group]['products'][group1]['price_units']:
						product_dict [group]['products'][group1]['price_units'][group2]= {
						'price_unit':0.0,
						'allowed_qty':0.0,
						'move_qty':0.0,
						
						}

					product_dict [group]['products'][group1]['price_units'][group2]['price_unit']= group2
					product_dict [group]['products'][group1]['price_units'][group2]['allowed_qty']+= line['allowed_qty']
					product_dict [group]['products'][group1]['price_units'][group2]['move_qty']+= line['move_qty']

					# if group3 not in product_dict[group]['tablets'][group1]['partners'][group2]['products']:
					# 	product_dict [group]['tablets'][group1]['partners'][group2]['products'][group3]= {
					# 						'product_name':u'Тодорхойгүй',
					# 						'product_code':u'Тодорхойгүй',
					# 						'product_qty':0.0,
					# 						'product_mark':u'Тодорхойгүй',
					# 						'warranty':u'Тодорхойгүй',
					# 						'price_unit':0.0,
					# 						'uom':u'Тодорхойгүй',
					# 						'total':0.0,
					# 	}

					
					
			if product_dict:

				row += 1
				count=1
				for cat in sorted(product_dict.values(), key=itemgetter('sector')):
					sheet.write(row,0,u'%s'%cat['sector'], header_color)
					row+=1					
					
					sheet.write(row, 0,u'Барааны код', header)
					sheet.set_column(row,0,25)
					sheet.write(row, 1, u'Барааны Нэр', header)
					sheet.set_column(row,1, 25)
					sheet.write(row,  2,u'Хэмжих нэгж', header)
					sheet.set_column(row,2, 15)
					sheet.write(row, 3,u'Нэгж үнэ', header)
					sheet.set_column(row,3, 10)
					sheet.write(row, 4,u'Захиалсан тоо', header)
					sheet.set_column(row,4, 10)
					sheet.write(row,5,u'Хүлээлгэн өгсөн тоо', header)
					sheet.set_column(row,5, 15)
					row+=1
					# sheet.write(row,  col+11,u'НӨАТ', header)
					# sheet.set_column(row,col+11, 15)
					# sheet.write(row,  col+12,u'НИЙТ', header)
					# sheet.set_column(row,col+12, 15)
					for tab in sorted(cat['products'].values(), key=itemgetter('product')):
						
						sheet.write(row,0,u'%s'%tab['product_code'], header)
						sheet.write(row,1 ,u'%s'%tab['product'], header)
						sheet.write(row,2,u'%s'%tab['product_uom'], header)

						for part in sorted(tab['price_units'].values(), key=itemgetter('price_unit')):
							sheet.write(row,  3,part['price_unit'],header )
							sheet.write(row,  4,part['allowed_qty'],header )
							sheet.write(row,  5,part['move_qty'],header )
							row+=1
		
		workbook.close()

		out = base64.encodestring(output.getvalue())
		file_name = u'Бараа хүлээн авалтын тайлан'
		excel_id = self.env['report.excel.output'].create({'data':out,'name':file_name + '.xlsx'})

		return {
		'name': 'Export Report',
		'view_type':'form',
		'view_mode':'form',
		'res_model':'report.excel.output',
		'res_id':excel_id.id,
		'view_id':False,
		'type': 'ir.actions.act_window',
		'target':'new',
		'nodestroy': True,
		}

	def concat_alphabet(numbers):
		concat = ''
		alphabet =['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

		if numbers >len(alphabet):
			concat= aplhabet[numbers/len(alphabet)]
		else:
			concat = alphabet[numbers]
		concat
		return concat