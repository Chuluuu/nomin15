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
	_name = 'purchase.order.supplier.report.wizard'
	_inherit = 'abstract.report.model'
	_description = 'Purchase order report wizard'

	start_date = fields.Date(string="Date start" , required=True) #Эхлэх огноо
	end_date = fields.Date(string='Date end',required=True) #Дуусах огноо
	partner_ids = fields.Many2many(comodel_name='res.partner', string='Supplier') #Нийлүүлэгч
	category_ids = fields.Many2many(comodel_name='product.category', string='Product category') #Барааны ангилал
	product_ids = fields.Many2many(comodel_name='product.product', string='Products') #Бараанууд
	partner_categ_ids = fields.Many2many(comodel_name='res.partner.category', string='Supplier category') #Нийлүүлэгч ангилал
	report_type = fields.Selection([('detailed','Detailed'),('summary','Summary')],required=True, default='detailed',string='Type') #Дэлгэрэнгүй, Хураангуй* Төрөл
	summary_type = fields.Selection([('year','Year'),('month','Month'),('season','Season')], string='Interval type', default='month') #Жил Сар Улирал Интервал төрөл
	export_type = fields.Selection([('product','Product'),('partner','Partner'),('partner_categ','Partner category')], string='Export type',default='partner_categ') #Бараа Харилцагч Харилцагч ангилал Гаргах бүлэг

	@api.multi
	def export_chart(self,report_code,context=None):
		if context is None:
			context = {}
		datas={}
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)

		datas['model'] = 'purchase.order'
		datas['form'] = self.read(['start_date','end_date','report_type','category_ids','partner_categ_ids','partner_ids','product_ids'])[0] 

		data = datas['form']

		# header = workbook.add_format({'border':1,'fg_color':'#b0e2ff','align':'justify','valign':'vjustify','text_wrap':100,'pattern':0})

		style2 = workbook.add_format({'border':True,'align':'right','num_format': '#,##0.00','valign':'vcenter','text_wrap':100,'pattern':0})
		style3 = workbook.add_format({'border':True,'align':'right','num_format': '0.00%','valign':'vcenter','text_wrap':100,'pattern':0})

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
		'num_format': '#,##0.00'
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
		sheet.write(2, 2, u'Худалдан авалтын %s тайлан'%report_type[data['report_type']],title)
		sheet.write(3, 0, u'Эхлэх хугацаа :'+  data['start_date'] ,)
		sheet.write(4, 0, u'Дуусах хугацаа :'+ data['end_date'], )
		row = 4
		col = 0
		row += 1
	
		query = "select part.name as partner_name , categ.name as categ_name,  part_cat.name as part_cat, temp.name as product_name ,temp.code as product_code,\
								temp.product_mark as product_mark,line.warranty as warranty, uom.name as uom, line.product_qty as product_qty,line.price_unit as price_unit,\
					(line.product_qty *line.price_unit ) as total\
			from 				purchase_order as ord ,\
			res_partner as part ,\
				 purchase_order_line as line ,\
				 product_product as prod,\
				 product_template as temp,\
				 product_category as categ,\
				 product_uom as uom,\
				 res_partner_res_partner_category_rel as rel,\
				 res_partner_category as part_cat\
				  where line.order_id= ord.id \
				  and rel.partner_id = part.id\
					and rel.category_id = part_cat.id\
				  and ord.partner_id = part.id\
					and prod.id= line.product_id \
					and prod.product_tmpl_id = temp.id\
					and temp.categ_id = categ.id\
					and temp.uom_id = uom.id\
						and ord.confirmed_date between '%s' and '%s'" %(str(data["start_date"]), str(data["end_date"]))
						

		self.env.cr.execute(query)
		dictfetchall = self.env.cr.dictfetchall()
		categories = {}
		order_lines = []
		domain = [('state','in',['done','purchase','']),('confirmed_date','>=',data['start_date']),('confirmed_date','<=',data['end_date'])]
		if data['partner_ids']:
			domain = domain + [('partner_id','in', data['partner_ids'])]
		if data['partner_categ_ids']:
				domain = domain + [('partner_id.category_id','in', data['partner_categ_ids'])]
		
		order_ids =self.env['purchase.order'].search(domain, order='confirmed_date')

		if order_ids:
			prod_domain= [('order_id','in',order_ids.ids)]
			if data['category_ids']:
				prod_domain = prod_domain + [('product_id.categ_id','in', data['category_ids'])]
			if data['product_ids']:
				prod_domain = prod_domain + [('product_id','in', data['product_ids'])]
			
			order_lines = self.env['purchase.order.line'].search(prod_domain ,order='create_date')
		
		product_dict = {}
		count=1
		if data['report_type'] =='detailed':
			sheet.write(row, col, u'№',header)
			# sheet.set_column(row,col, 10)
			sheet.merge_range(row, col+1, row, col+3,u'Бараа бүтээгдэхүүн', header)
			sheet.write(row, col+4,u'Барааны код', header)
			sheet.set_column(row,col+4,10)
			sheet.write(row, col+5, u'Барааны Нэр', header)
			sheet.set_column(row,col+5, 25)
			sheet.write(row, col+6, u'Баталгаат хугацаа', header)
			sheet.set_column(row,col+6, 20)
			sheet.write(row,  col+7,u'Хэмжих нэгж', header)
			sheet.set_column(row,col+7, 15)
			sheet.write(row, col+8,u'Тоо', header)
			sheet.set_column(row,col+8, 10)
			sheet.write(row, col+9,u'Нэгж үнэ', header)
			sheet.set_column(row,col+9, 15)
			sheet.write(row,col+10,u'НӨАТ-гүй дүн', header)
			sheet.set_column(row,col+10, 15)
			sheet.write(row,  col+11,u'НӨАТ', header)
			sheet.set_column(row,col+11, 15)
			sheet.write(row,  col+12,u'НИЙТ', header)
			sheet.set_column(row,col+12, 15)
			for line in order_lines:
				group = False
				group1 = False
				group2 = False
				group3 = False


				if line.product_id.categ_id:
					group = line.product_id.categ_id.name
					
				if group not in product_dict:
					product_dict [group]= {
					'category':u'Тодорхойгүй',
					'tablets':{}
					}


				product_dict [group]['category']= group
				if not line.partner_id.category_id:

					group1 = u'Тодорхойгүй'

					if group1 not in product_dict[group]['tablets']:
						product_dict[group]['tablets'][group1] = {
						'tablet':u'Тодорхойгүй',
						'partners':{}
						}
			
					product_dict[group]['tablets'][group1]['tablet']= group1
					
					if line.partner_id.name :
						group2  = line.partner_id.name 

					if group2 not in product_dict[group]['tablets'][group1]['partners']:
						product_dict [group]['tablets'][group1]['partners'][group2]= {
						'partner':u'Тодорхойгүй',
						'products':{}
						}

					product_dict [group]['tablets'][group1]['partners'][group2]['partner']= group2
					
					if group3 not in product_dict[group]['tablets'][group1]['partners'][group2]['products']:
						product_dict [group]['tablets'][group1]['partners'][group2]['products'][group3]= {
											'product_name':u'Тодорхойгүй',
											'product_code':u'Тодорхойгүй',
											'product_qty':0.0,
											'product_mark':u'Тодорхойгүй',
											'warranty':u'Тодорхойгүй',
											'price_unit':0.0,
											'uom':u'Тодорхойгүй',
											'total':0.0,
						}

					count+=1
					product_dict [group]['tablets'][group1]['partners'][group2]['products'][group3]['product_code']= line.product_id.product_code if line.product_id.product_code else  u'Тодорхойгүй'
					product_dict [group]['tablets'][group1]['partners'][group2]['products'][group3]['product_qty']= line.product_qty if line.product_qty else 0.0
					product_dict [group]['tablets'][group1]['partners'][group2]['products'][group3]['product_mark']= line.product_id.product_mark if line.product_id.product_mark else  u'Тодорхойгүй'
					product_dict [group]['tablets'][group1]['partners'][group2]['products'][group3]['warranty']= line.warranty if line.warranty else  u'Тодорхойгүй'
					product_dict [group]['tablets'][group1]['partners'][group2]['products'][group3]['price_unit']= line.price_unit if line.price_unit else 0.0
					product_dict [group]['tablets'][group1]['partners'][group2]['products'][group3]['total']= line.price_subtotal if line.price_subtotal else  0.0
					product_dict [group]['tablets'][group1]['partners'][group2]['products'][group3]['product_name']= line.product_id.name if line.product_id.name  else u'Тодорхойгүй'		
					product_dict [group]['tablets'][group1]['partners'][group2]['products'][group3]['uom']= line.product_uom.name if line.product_uom.name  else u'Тодорхойгүй'		
				for cat in line.partner_id.category_id:
					if cat:
						group1 = cat.name

					if group1 not in product_dict[group]['tablets']:
						product_dict[group]['tablets'][group1] = {
						'tablet':u'Тодорхойгүй',
						'partners':{}
						}
			
					product_dict[group]['tablets'][group1]['tablet']= group1
					
					if line.partner_id.name :
						group2  = line.partner_id.name 

					if group2 not in product_dict[group]['tablets'][group1]['partners']:
						product_dict [group]['tablets'][group1]['partners'][group2]= {
						'partner':u'Тодорхойгүй',
						'products':{}
						}

					product_dict [group]['tablets'][group1]['partners'][group2]['partner']= group2
					
					if group3 not in product_dict[group]['tablets'][group1]['partners'][group2]['products']:
						product_dict [group]['tablets'][group1]['partners'][group2]['products'][group3]= {
											'product_name':u'Тодорхойгүй',
											'product_code':u'Тодорхойгүй',
											'product_qty':0.0,
											'product_mark':u'Тодорхойгүй',
											'warranty':u'Тодорхойгүй',
											'price_unit':0.0,
											'uom':u'Тодорхойгүй',
											'total':0.0,
						}
					
					count+=1
					product_dict [group]['tablets'][group1]['partners'][group2]['products'][group3]['product_code']= line.product_id.code if line.product_id.code else  u'Тодорхойгүй'
					product_dict [group]['tablets'][group1]['partners'][group2]['products'][group3]['product_qty']= line.product_qty if line.product_qty else 0.0
					product_dict [group]['tablets'][group1]['partners'][group2]['products'][group3]['product_mark']= line.product_id.product_mark if line.product_id.product_mark else  u'Тодорхойгүй'
					product_dict [group]['tablets'][group1]['partners'][group2]['products'][group3]['warranty']= line.warranty if line.warranty else  u'Тодорхойгүй'
					product_dict [group]['tablets'][group1]['partners'][group2]['products'][group3]['price_unit']= line.price_unit if line.price_unit else 0.0
					product_dict [group]['tablets'][group1]['partners'][group2]['products'][group3]['total']= line.taxes_id if line.taxes_id else  0.0
					product_dict [group]['tablets'][group1]['partners'][group2]['products'][group3]['product_name']= line.product_id.name if line.product_id.name  else u'Тодорхойгүй'		
					product_dict [group]['tablets'][group1]['partners'][group2]['products'][group3]['uom']= line.product_uom.name if line.product_uom.name  else u'Тодорхойгүй'				
			if product_dict:

				row += 1
				count=1
				for cat in sorted(product_dict.values(), key=itemgetter('category')):
					sheet.write(row,  col,u'%s'%count, header_color)
					col+=1
					sheet.merge_range(row,col, row,  col+11,u'%s'%cat['category'], cell_format_left_color)
					row += 1
					count1=1
					
					for tab in sorted(cat['tablets'].values(), key=itemgetter('tablet')):
						sheet.write(row,  0,'', header)
						sheet.write(row,  col,u'%s.%s'%(count,count1), header_font_color)
						col+=1
						sheet.merge_range(row,col, row,  col+10,u'%s'%tab['tablet'], cell_format_left_font_color)
						row += 1
						count2=1
						col1 = col
						for part in sorted(tab['partners'].values(), key=itemgetter('partner')):
							sheet.write(row,  0,'',header )
							sheet.write(row,  1,'',header )
							sheet.write(row,  col,u'%s.%s.%s'%(count,count1,count2), header)
							col+=1
							sheet.merge_range(row,col, row,  col+9,u'%s'%part['partner'], cell_format_left)
							row += 1
							col2 = col
							for product in sorted(part['products'].values(), key=itemgetter('product_name')):
								sheet.write(row,  0,'',header )
								sheet.write(row,  1,'',header )
								sheet.write(row,  2,'',header )
								sheet.write(row,  3,'',header )
								col+=1
								sheet.write(row,  col,u'%s'%product['product_code'],style2 )
								col+=1
								sheet.write(row,  col,u'%s'%product['product_name'],style2 )
								col+=1
								sheet.write(row,  col,u'%s'%product['warranty'],style2 )
								col+=1
								sheet.write(row, col,u'%s'%product['uom'],style2 )
								col+=1
								sheet.write(row,  col,u'%s'%product['product_qty'], style2)
								col+=1
								sheet.write(row,  col,product['price_unit'],style2 )
								col+=1
								sheet.write(row,  col, round((product['price_unit']/1.1)*product['product_qty'] if product['total']==0.0 else product['product_qty']*product['price_unit'] ,2),style2 )
								col+=1
								sheet.write(row,  col, round(((product['price_unit']/1.1)*product['product_qty'])*0.1 if product['total']==0.0 else 0.0,2 ),style2 )
								col+=1
								sheet.write(row,  col, product['product_qty']*product['price_unit'] ,style2 )
								row += 1
								col= col2
							
							col = col1
							count2+=1

						count1+=1
						col=1
					col=0
					count+=1

		else:			
			categories = {}
			months = {}
			for order in order_lines:
				group = False
				group1 = False
				group2 = False
				group3 = False
				month_id = self.env['account.period'].sudo().search([('date_start','<=',order.order_id.confirmed_date),('date_stop','>=',order.order_id.confirmed_date)])
				
				if self.export_type =='partner_categ' and self.summary_type =='season':
					if month_id.account_season+'/'+month_id.fiscalyear_id.name not in months:
						months[month_id.account_season+'/'+month_id.fiscalyear_id.name]= {
								'month_name':u'Тодорхойгүй',
								'month':0.0
							}
					months[month_id.account_season+'/'+month_id.fiscalyear_id.name]['month_name'] = month_id.account_season+'/'+month_id.fiscalyear_id.name
					
					if not order.partner_id.category_id:
						group = u'Тодорхойгүй'

						if group not in categories:
							categories[group]  = {
							'category':u'Тодорхойгүй',
							'months':{}
							}
						categories[group]['category'] = group

						if month_id:
							group1 = month_id.account_season+'/'+month_id.fiscalyear_id.name
						if group1 not in categories[group]['months']:
							categories[group]['months'][group1] = {
							'month_name':u'Тодорхойгүй',
							'month':0.0,

							}
						# categories[group]['months'][group1] = group1	
						categories[group]['months'][group1]['month'] += order.price_total
						categories[group]['months'][group1]['month_name'] = group1

					for cat in order.partner_id.category_id:
						if cat.name :
							group = cat.name

						if group not in categories:
							categories[group]  = {
							'category':u'Тодорхойгүй',
							'months':{}
							}
						categories[group]['category'] = group

						if month_id:
							group1 = month_id.account_season+'/'+month_id.fiscalyear_id.name
						if group1 not in categories[group]['months']:
							categories[group]['months'][group1] = {
							'month_name':u'Тодорхойгүй',
							'month':0.0,

							}
						# categories[group]['months'][group1] = group1	
						categories[group]['months'][group1]['month'] += order.price_total
						categories[group]['months'][group1]['month_name'] = group1

				elif self.export_type =='partner_categ' and self.summary_type =='month':
					if month_id.name not in months:
						months[month_id.name]= {
								'month_name':u'Тодорхойгүй',
								'month':0.0
							}
					months[month_id.name]['month_name'] = month_id.name
					
					if not order.partner_id.category_id:
						group = u'Тодорхойгүй'

						if group not in categories:
							categories[group]  = {
							'category':u'Тодорхойгүй',
							'months':{}
							}
						categories[group]['category'] = group

						if month_id:
							group1 = month_id.name
						if group1 not in categories[group]['months']:
							categories[group]['months'][group1] = {
							'month_name':u'Тодорхойгүй',
							'month':0.0,

							}
						# categories[group]['months'][group1] = group1	
						categories[group]['months'][group1]['month'] += order.price_total
						categories[group]['months'][group1]['month_name'] = group1

					for cat in order.partner_id.category_id:
						if cat.name :
							group = cat.name

						if group not in categories:
							categories[group]  = {
							'category':u'Тодорхойгүй',
							'months':{}
							}
						categories[group]['category'] = group

						if month_id:
							group1 = month_id.name
						if group1 not in categories[group]['months']:
							categories[group]['months'][group1] = {
							'month_name':u'Тодорхойгүй',
							'month':0.0,

							}
						# categories[group]['months'][group1] = group1	
						categories[group]['months'][group1]['month'] += order.price_total
						categories[group]['months'][group1]['month_name'] = group1
				elif self.export_type =='partner_categ' and self.summary_type =='year':
					if month_id.fiscalyear_id.name not in months:
						months[month_id.fiscalyear_id.name]= {
								'month_name':u'Тодорхойгүй',
								'month':0.0
							}
					months[month_id.fiscalyear_id.name]['month_name'] = month_id.fiscalyear_id.name
					
					if not order.partner_id.category_id:
						group = u'Тодорхойгүй'

						if group not in categories:
							categories[group]  = {
							'category':u'Тодорхойгүй',
							'months':{}
							}
						categories[group]['category'] = group

						if month_id:
							group1 = month_id.fiscalyear_id.name
						if group1 not in categories[group]['months']:
							categories[group]['months'][group1] = {
							'month_name':u'Тодорхойгүй',
							'month':0.0,

							}
						# categories[group]['months'][group1] = group1	
						categories[group]['months'][group1]['month'] += order.price_total
						categories[group]['months'][group1]['month_name'] = group1

					for cat in order.partner_id.category_id:
						if cat.name :
							group = cat.name

						if group not in categories:
							categories[group]  = {
							'category':u'Тодорхойгүй',
							'months':{}
							}
						categories[group]['category'] = group

						if month_id:
							group1 = month_id.fiscalyear_id.name
						if group1 not in categories[group]['months']:
							categories[group]['months'][group1] = {
							'month_name':u'Тодорхойгүй',
							'month':0.0,

							}
						# categories[group]['months'][group1] = group1	
						categories[group]['months'][group1]['month'] += order.price_total
						categories[group]['months'][group1]['month_name'] = group1
				elif self.export_type =='partner' and self.summary_type =='year':
					if month_id.fiscalyear_id.name not in months:
						months[month_id.fiscalyear_id.name]= {
								'month_name':u'Тодорхойгүй',
								'month':0.0
							}
					months[month_id.fiscalyear_id.name]['month_name'] = month_id.fiscalyear_id.name
					
					if not order.partner_id.name:
						group = u'Тодорхойгүй'

						if group not in categories:
							categories[group]  = {
							'category':u'Тодорхойгүй',
							'months':{}
							}
						categories[group]['category'] = group

						if month_id:
							group1 = month_id.fiscalyear_id.name
						if group1 not in categories[group]['months']:
							categories[group]['months'][group1] = {
							'month_name':u'Тодорхойгүй',
							'month':0.0,

							}
						# categories[group]['months'][group1] = group1	
						categories[group]['months'][group1]['month'] += order.price_total
						categories[group]['months'][group1]['month_name'] = group1

					for cat in order.partner_id:
						if cat.name :
							group = cat.name

						if group not in categories:
							categories[group]  = {
							'category':u'Тодорхойгүй',
							'months':{}
							}
						categories[group]['category'] = group

						if month_id:
							group1 = month_id.fiscalyear_id.name
						if group1 not in categories[group]['months']:
							categories[group]['months'][group1] = {
							'month_name':u'Тодорхойгүй',
							'month':0.0,

							}
						# categories[group]['months'][group1] = group1	
						categories[group]['months'][group1]['month'] += order.price_total
						categories[group]['months'][group1]['month_name'] = group1

				elif self.export_type =='partner' and self.summary_type =='month':
					if month_id.name not in months:
						months[month_id.name]= {
								'month_name':u'Тодорхойгүй',
								'month':0.0
							}
					months[month_id.name]['month_name'] = month_id.name
					
					if not order.partner_id.name:
						group = u'Тодорхойгүй'

						if group not in categories:
							categories[group]  = {
							'category':u'Тодорхойгүй',
							'months':{}
							}
						categories[group]['category'] = group

						if month_id:
							group1 = month_id.name
						if group1 not in categories[group]['months']:
							categories[group]['months'][group1] = {
							'month_name':u'Тодорхойгүй',
							'month':0.0,

							}
						# categories[group]['months'][group1] = group1	
						categories[group]['months'][group1]['month'] += order.price_total
						categories[group]['months'][group1]['month_name'] = group1

					for cat in order.partner_id:
						if cat.name :
							group = cat.name

						if group not in categories:
							categories[group]  = {
							'category':u'Тодорхойгүй',
							'months':{}
							}
						categories[group]['category'] = group

						if month_id:
							group1 = month_id.name
						if group1 not in categories[group]['months']:
							categories[group]['months'][group1] = {
							'month_name':u'Тодорхойгүй',
							'month':0.0,

							}
						# categories[group]['months'][group1] = group1	
						categories[group]['months'][group1]['month'] += order.price_total
						categories[group]['months'][group1]['month_name'] = group1
				elif self.export_type =='partner' and self.summary_type =='season':
					if month_id.account_season+'/'+month_id.fiscalyear_id.name not in months:
						months[month_id.account_season+'/'+month_id.fiscalyear_id.name]= {
								'month_name':u'Тодорхойгүй',
								'month':0.0
							}
					months[month_id.account_season+'/'+month_id.fiscalyear_id.name]['month_name'] = month_id.account_season+'/'+month_id.fiscalyear_id.name
					
					if not order.partner_id.name:
						group = u'Тодорхойгүй'

						if group not in categories:
							categories[group]  = {
							'category':u'Тодорхойгүй',
							'months':{}
							}
						categories[group]['category'] = group

						if month_id:
							group1 = month_id.account_season+'/'+month_id.fiscalyear_id.name
						if group1 not in categories[group]['months']:
							categories[group]['months'][group1] = {
							'month_name':u'Тодорхойгүй',
							'month':0.0,

							}
						# categories[group]['months'][group1] = group1	
						categories[group]['months'][group1]['month'] += order.price_total
						categories[group]['months'][group1]['month_name'] = group1

					for cat in order.partner_id:
						if cat.name :
							group = cat.name

						if group not in categories:
							categories[group]  = {
							'category':u'Тодорхойгүй',
							'months':{}
							}
						categories[group]['category'] = group

						if month_id:
							group1 = month_id.account_season+'/'+month_id.fiscalyear_id.name
						if group1 not in categories[group]['months']:
							categories[group]['months'][group1] = {
							'month_name':u'Тодорхойгүй',
							'month':0.0,

							}
						# categories[group]['months'][group1] = group1	
						categories[group]['months'][group1]['month'] += order.price_total
						categories[group]['months'][group1]['month_name'] = group1

				elif self.export_type =='product' and self.summary_type =='year':
					if month_id.fiscalyear_id.name not in months:
						months[month_id.fiscalyear_id.name]= {
								'month_name':u'Тодорхойгүй',
								'month':0.0
							}
					months[month_id.fiscalyear_id.name]['month_name'] = month_id.fiscalyear_id.name
					
					if not order.product_id.name:
						group = u'Тодорхойгүй'

						if group not in categories:
							categories[group]  = {
							'category':u'Тодорхойгүй',
							'months':{}
							}
						categories[group]['category'] = group

						if month_id:
							group1 = month_id.fiscalyear_id.name
						if group1 not in categories[group]['months']:
							categories[group]['months'][group1] = {
							'month_name':u'Тодорхойгүй',
							'month':0.0,

							}
						# categories[group]['months'][group1] = group1	
						categories[group]['months'][group1]['month'] += order.price_total
						categories[group]['months'][group1]['month_name'] = group1

					for cat in order.product_id:
						if cat.name :
							group = cat.name

						if group not in categories:
							categories[group]  = {
							'category':u'Тодорхойгүй',
							'months':{}
							}
						categories[group]['category'] = group

						if month_id:
							group1 = month_id.fiscalyear_id.name
						if group1 not in categories[group]['months']:
							categories[group]['months'][group1] = {
							'month_name':u'Тодорхойгүй',
							'month':0.0,

							}
						# categories[group]['months'][group1] = group1	
						categories[group]['months'][group1]['month'] += order.price_total
						categories[group]['months'][group1]['month_name'] = group1

				elif self.export_type =='product' and self.summary_type =='month':
					if month_id.name not in months:
						months[month_id.name]= {
								'month_name':u'Тодорхойгүй',
								'month':0.0
							}
					months[month_id.name]['month_name'] = month_id.name
					
					if not order.product_id.name:
						group = u'Тодорхойгүй'

						if group not in categories:
							categories[group]  = {
							'category':u'Тодорхойгүй',
							'months':{}
							}
						categories[group]['category'] = group

						if month_id:
							group1 = month_id.name
						if group1 not in categories[group]['months']:
							categories[group]['months'][group1] = {
							'month_name':u'Тодорхойгүй',
							'month':0.0,

							}
						# categories[group]['months'][group1] = group1	
						categories[group]['months'][group1]['month'] += order.price_total
						categories[group]['months'][group1]['month_name'] = group1

					for cat in order.product_id:
						if cat.name :
							group = cat.name

						if group not in categories:
							categories[group]  = {
							'category':u'Тодорхойгүй',
							'months':{}
							}
						categories[group]['category'] = group

						if month_id:
							group1 = month_id.name
						if group1 not in categories[group]['months']:
							categories[group]['months'][group1] = {
							'month_name':u'Тодорхойгүй',
							'month':0.0,

							}
						# categories[group]['months'][group1] = group1	
						categories[group]['months'][group1]['month'] += order.price_total
						categories[group]['months'][group1]['month_name'] = group1
				elif self.export_type =='product' and self.summary_type =='season':
					if month_id.account_season+'/'+month_id.fiscalyear_id.name not in months:
						months[month_id.account_season+'/'+month_id.fiscalyear_id.name]= {
								'month_name':u'Тодорхойгүй',
								'month':0.0
							}
					months[month_id.account_season+'/'+month_id.fiscalyear_id.name]['month_name'] = month_id.account_season+'/'+month_id.fiscalyear_id.name
					
					if not order.product_id.name:
						group = u'Тодорхойгүй'

						if group not in categories:
							categories[group]  = {
							'category':u'Тодорхойгүй',
							'months':{}
							}
						categories[group]['category'] = group

						if month_id:
							group1 = month_id.account_season+'/'+month_id.fiscalyear_id.name
						if group1 not in categories[group]['months']:
							categories[group]['months'][group1] = {
							'month_name':u'Тодорхойгүй',
							'month':0.0,

							}
						# categories[group]['months'][group1] = group1	
						categories[group]['months'][group1]['month'] += order.price_total
						categories[group]['months'][group1]['month_name'] = group1

					for cat in order.product_id:
						if cat.name :
							group = cat.name

						if group not in categories:
							categories[group]  = {
							'category':u'Тодорхойгүй',
							'months':{}
							}
						categories[group]['category'] = group

						if month_id:
							group1 = month_id.account_season+'/'+month_id.fiscalyear_id.name
						if group1 not in categories[group]['months']:
							categories[group]['months'][group1] = {
							'month_name':u'Тодорхойгүй',
							'month':0.0,

							}
						# categories[group]['months'][group1] = group1	
						categories[group]['months'][group1]['month'] += order.price_total
						categories[group]['months'][group1]['month_name'] = group1
			row= 5
			col=0
			colums = {}
			rows = {}
			for cat in months.values():
				col+=1
				sheet.write(row, col,u'%s'%cat['month_name'], header)
				if cat['month_name'] not in colums:
					colums [cat['month_name']]= {
					cat['month_name']:col
					}
			col=0
			row= 6
			total = 0
			month_sub_total = {}
			cat_sub_total = {}	
			col_range = 0	
			for cat in sorted(categories.values(), key=itemgetter('category')):
					col=0
					sheet.write(row,  col,u'%s'%cat['category'], header)
					sheet.set_column(row,col,15)
					if cat['category'] not in rows:
						rows[cat['category']]= {
						cat['category']:row
						}
					for mon in sorted(cat['months'].values(), key=itemgetter('month')):
						col+=1
						if col > col_range:
							col_range=col
						collum = colums.get(mon['month_name'])
						get_col = collum.get(mon['month_name'])
						sheet.write(row,  get_col,mon['month'],style2)
						sheet.set_column(row,get_col,7)
						if cat['category'] not in cat_sub_total:
							cat_sub_total[cat['category']] = {
							'category':u'Тодорхойгүй',
							'sub_total':0.0,
							}
						if mon['month_name'] not in month_sub_total:
							month_sub_total[ mon['month_name']]=	 {
							'month_name':u'Тодорхойгүй',
							'sub_total':0.0}
						cat_sub_total[ cat['category']]['sub_total'] += mon['month']
						cat_sub_total[ cat['category']]['category'] =  cat['category']
						month_sub_total[ mon['month_name']]['sub_total'] += mon['month']
						month_sub_total[ mon['month_name']]['month_name'] = mon['month_name']
					row+=1

			sheet.write(row,  0,u'Нийт',header)
			total=0
			for cat in sorted(month_sub_total.values(), key=itemgetter('month_name')):
				collum = colums.get(cat['month_name'])
				get_col = collum.get(cat['month_name'])
				sheet.write(row,  get_col,cat['sub_total'],header)

				sheet.set_column(row,get_col,7)
				total += cat['sub_total']
			col_range+=1
			sheet.write(5,  col_range,u'Дундаж хувийн жин',header)
			# sheet.set_column(5,get_col,7)
			for cat in sorted(cat_sub_total.values(), key=itemgetter('category')):
				rowum = rows.get(cat['category'])
				get_row = rowum.get(cat['category'])
				# u'%s'%(cat['sub_total']/total)+'%'
				sheet.write(get_row,col_range, (cat['sub_total']/total),style3)
			sheet.write(row,col_range, '100%',style3)
		# sheet.set_column(4,0,row,col_range,10)
			# categ_chart = workbook.add_chart({'type': 'column'})
   #          # categ_chart.set_title({ 'name': u'Асуудлын явц'})
   #          # categ_chart.set_x_axis({'name': u'Шат'})
   #          # categ_chart.set_y_axis({'name': u'Тоо'})
   #          categ_chart.add_series({
   #                                  'name':u'Асуудал',
   #                                  'categories': '=Sheet1!$B$6:$%s$%s'%()),
   #                                  'values': '=Sheet2!$V$10:$V$%s'%(str(10 + len(issue_category))),
   #                                  'width': 100
   #                                  })
   #          categ_chart.set_chartarea({'fill': {'color': 'white', 'transparency': 100}})
   #          worksheet.insert_chart('I23', categ_chart)		
		# return {'data':workbook}
		workbook.close()

		out = base64.encodestring(output.getvalue())
		file_name = u'Худалдан авалт тайлан'
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