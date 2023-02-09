# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime,timedelta
from operator import itemgetter
import xlsxwriter
from io import BytesIO
import base64

class PurchaseComparisonPerformanceReport(models.TransientModel):
	''' Худалдан авалтын харьцуулалтын гүйцэтгэлийн тайлан '''
	_name = 'purchase.comparison.performance'

	start_date = fields.Date(string=u'Эхлэх огноо' )
	end_date = fields.Date(string=u'Дуусах огноо')
	department_ids = fields.Many2many(comodel_name = 'hr.department',string=u'Хэлтэс')
	user_ids = fields.Many2many(comodel_name='res.users', string=u'Ажилчид')


	
	def export_chart(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)

		title = workbook.add_format({
			'border': 0,
			'bold': 0,
			# 'align': 'center',
			'valign': 'vcenter',
			'text_wrap': 'on',
			'font_size':11,
			'font_name': 'Arial'
		})
				
		header = workbook.add_format({
			'border': 0,
			'bold': 1,
			'align': 'center',
			'valign': 'vcenter',
			'text_wrap': 'on',
			'font_size':11,
			'font_name': 'Arial',
		})

		table_header = workbook.add_format({
			'border': 1,
			'bold': 1,
			'align': 'center',
			'valign': 'vcenter',
			'text_wrap': 'on',
			'font_size':10,
			'bg_color': '#e0e0e0',
			'font_name': 'Arial'
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

		cell_format_right_float = workbook.add_format({
			'border': 1,
			'bold': 0,
			'align': 'right',
			'valign': 'vcenter',
			'text_wrap': 'on',
			'font_size':10,
			'font_name': 'Arial',
			'num_format': '#,##0.00',
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

		partner_name = workbook.add_format({
			'border': 0,
			'bold': 1,
			'align': 'center',
			'valign': 'vcenter',
			'text_wrap': 'on',
			'font_size':10,
			'font_name': 'Arial',
			'bg_color': '#e0e0e0'
		})

		where = " WHERE B.comparison_date_end BETWEEN '%s' AND '%s'"%(self.start_date, self.end_date)

		if self.user_ids:
			if len(self.user_ids.ids)>1:
				where = where+"and K.user_id in %s"%(str(tuple(self.user_ids.ids)))
			else:
				where = where+"and K.user_id = %s"%(str(self.user_ids.ids[0]))

		if self.department_ids:
			if len(self.department_ids.ids)>1:
				where = where+"and N.id in %s"%( str(tuple(self.department_ids.ids)))
			else:
				where = where+"and N.id = %s"%(str(self.department_ids.ids[0]))

		query = "SELECT C.id as department_id, C.name as department_name, D.id as user_id, F.name_related as employee_name, \
			A.name as requisition_number, B.id as requisition_line_id, G.name_template as product_name, A.id as requisition_id,\
			B.comparison_date as comparison_date, J.name_related as comparison_employee, B.date_start as assigned_date,\
			B.comparison_sent_date as comparison_sent_date, B.comparison_confirmed_date as comparison_confirmed_date,\
			K.name as comparison_number, M.price_unit as price_unit, M.product_qty as product_qty, B.allowed_qty as allowed_qty, B.product_price as product_price\
			FROM purchase_requisition A\
			LEFT JOIN purchase_requisition_line B ON B.requisition_id = A.id\
			INNER JOIN hr_department C ON C.id = A.department_id\
			INNER JOIN res_users D ON D.id = A.user_id\
			INNER JOIN resource_resource E ON E.user_id = D.id\
			INNER JOIN hr_employee F ON F.resource_id = E.id\
			LEFT JOIN product_product G ON G.id = B.product_id\
			LEFT JOIN res_users H ON B.comparison_user_id = H.id\
			LEFT JOIN resource_resource I ON I.user_id = H.id\
			LEFT JOIN hr_employee J ON J.resource_id = I.id\
			INNER JOIN purchase_comparison K ON B.comparison_id = K.id\
			INNER JOIN purchase_order L ON L.comparison_id = K.id AND L.state = 'purchase'\
			INNER JOIN purchase_order_line M ON M.order_id = L.id AND M.product_id = G.id\
			LEFT JOIN hr_department N ON K.department_id = N.id\
		"

		query = query + where
		self.env.cr.execute(query)
		dictfetchall = self.env.cr.dictfetchall()
		if dictfetchall:
			requisitions = {}
			for fetch in dictfetchall:
				group = fetch['requisition_id']
				if group not in requisitions:
					requisitions[group] = {
						'requisition_number':u'Тодорхойгүй',
						'requisition_id':u'Тодорхойгүй',
						'employee_name':u'Тодорхойгүй',
						'department_name':u'Тодорхойгүй',
						'products':{}
					}

				requisitions[group]['requisition_id'] = group
				requisitions[group]['requisition_number'] = fetch['requisition_number']
				requisitions[group]['employee_name'] = fetch['employee_name']
				requisitions[group]['department_name'] = fetch['department_name']

				group1 = fetch['requisition_line_id']
				if group1 not in requisitions[group]['products']:
					requisitions[group]['products'][group1] = {
						'requisition_line_id':u'Тодорхойгүй',
						'product_name':u'Тодорхойгүй',
						'allowed_qty':0,
						'product_price':0,
						'comparison_date':u'Тодорхойгүй',
						'comparison_employee':u'Тодорхойгүй',
						'assigned_date':u'Тодорхойгүй',
						'comparison_sent_date':u'Тодорхойгүй',
						'comparison_confirmed_date':u'Тодорхойгүй',
						'comparison_number':u'Тодорхойгүй',
						'price_unit':0,
						'product_qty':0,
					}
				
				requisitions[group]['products'][group1]['requisition_line_id'] 		= group1
				requisitions[group]['products'][group1]['product_name'] 			= fetch['product_name']
				requisitions[group]['products'][group1]['allowed_qty'] 				= fetch['allowed_qty']
				requisitions[group]['products'][group1]['product_price'] 			= fetch['product_price']
				requisitions[group]['products'][group1]['comparison_date'] 			= fetch['comparison_date']
				requisitions[group]['products'][group1]['comparison_employee'] 		= fetch['comparison_employee']
				requisitions[group]['products'][group1]['assigned_date'] 			= fetch['assigned_date']
				requisitions[group]['products'][group1]['comparison_sent_date'] 	= fetch['comparison_sent_date']
				requisitions[group]['products'][group1]['comparison_confirmed_date'] = fetch['comparison_confirmed_date']
				requisitions[group]['products'][group1]['comparison_number'] 		= fetch['comparison_number']
				requisitions[group]['products'][group1]['price_unit'] 				= fetch['price_unit']
				requisitions[group]['products'][group1]['product_qty'] 				= fetch['product_qty']


			sheet = workbook.add_worksheet(u'Харьцуулалтын гүйцэтгэл')
		
			sheet.portrait=True
			sheet.set_column('A:A',20)
			sheet.set_column('B:B',15)
			sheet.set_column('C:C',10)
			sheet.set_column('D:D',20)
			sheet.set_column('E:K',15)
			sheet.set_column('L:P',10)
			sheet.set_row(4,50)

			date_from = datetime.strptime(self.start_date, "%Y-%m-%d").strftime('%Y.%m.%d')
			date_to = datetime.strptime(self.end_date, "%Y-%m-%d").strftime('%Y.%m.%d')
			
			sheet.merge_range(1, 0, 1, 15, u'Худалдан авалтын харьцуулалтын гүйцэтгэлийн тайлан', header)
			sheet.merge_range(3, 0, 3, 2, u'Тайлангийн огноо: ' + date_from + '-' + date_to, title)
			
			row = 4

			sheet.write(row, 0, 'Захиалсан салбар', table_header)
			sheet.write(row, 1, 'Захиалсан ажилтан', table_header)
			sheet.write(row, 2, 'Шаардах №', table_header)
			sheet.write(row, 3, 'Материалын нэр', table_header)
			sheet.write(row, 4, 'Шаардахын үнийн дүн', table_header)
			sheet.write(row, 5, 'Захиалга биелүүлвэл зохих хугацаа', table_header)
			sheet.write(row, 6, 'Харьцуулалтын ажилтан', table_header)
			sheet.write(row, 7, 'Харьцуулалт хүлээж авсан огноо', table_header)
			sheet.write(row, 8, 'Харьцуулалт биелүүлсэн огноо', table_header)
			sheet.write(row, 9, 'Харьцуулалт дууссан огноо', table_header)
			sheet.write(row, 10, 'Харьцуулалтын дугаар', table_header)
			sheet.write(row, 11, 'Харьцуулалтын үнийн дүн /шалгарсан/', table_header)
			sheet.write(row, 12, 'Харьцуулалтын хэтэрсэн хоног', table_header)
			sheet.write(row, 13, 'Нийлүүлсэн тоо', table_header)
			sheet.write(row, 14, 'Захилга хүлээлгэж өгсөн үнийн дүн', table_header)
			sheet.write(row, 15, 'Төсвийн хэмнэлт/хэтрэлт', table_header)

			row += 1

			for requisition in sorted(requisitions.values(), key=itemgetter('requisition_id')):
				rowx = row

				for product in sorted(requisition['products'].values(), key=itemgetter('requisition_line_id')):

					alllowed_qty = product['allowed_qty'] or 0
					product_price = product['product_price'] or 0
					price_unit = product['price_unit'] or 0
					product_qty = product['product_qty'] or 0
					
					date_diff = 0
					if product['comparison_date']:
						comparison_date = datetime.strptime(product['comparison_date'], "%Y-%m-%d")
						if product['comparison_sent_date']:
							comparison_sent_date = datetime.strptime(product['comparison_sent_date'], "%Y-%m-%d %H:%M:%S")
							date_diff = (comparison_sent_date - comparison_date).days
						else:
							date_diff = (datetime.today() - comparison_date).days
					
					comparison_sent_date = ''
					if product['comparison_sent_date']:
						comparison_sent_date = datetime.strptime(product['comparison_sent_date'], "%Y-%m-%d %H:%M:%S")
						comparison_sent_date = comparison_sent_date.strftime("%Y-%m-%d %H:%M")

					comparison_confirmed_date = ''
					if product['comparison_confirmed_date']:
						comparison_confirmed_date = datetime.strptime(product['comparison_confirmed_date'], "%Y-%m-%d %H:%M:%S")
						comparison_confirmed_date = comparison_confirmed_date.strftime("%Y-%m-%d %H:%M")

					sheet.write(row, 3, product['product_name'], cell_format_left)
					sheet.write(row, 4, alllowed_qty * product_price, cell_format_right_float)
					sheet.write(row, 5, product['comparison_date'], cell_format_left)
					sheet.write(row, 6, product['comparison_employee'], cell_format_left)
					sheet.write(row, 7, product['assigned_date'], cell_format_left)
					sheet.write(row, 8, comparison_sent_date, cell_format_left)
					sheet.write(row, 9, comparison_confirmed_date, cell_format_left)
					sheet.write(row, 10, product['comparison_number'], cell_format_left)
					sheet.write(row, 11, price_unit, cell_format_right_float)
					sheet.write(row, 12, date_diff, cell_format_right_float)
					sheet.write(row, 13, product_qty, cell_format_right_float)
					sheet.write(row, 14, price_unit * product_qty, cell_format_right_float)
					sheet.write(row, 15, (alllowed_qty * product_price) - (price_unit * product_qty), cell_format_right_float)
					row += 1

				if row - 1 == rowx:
					sheet.write(rowx, 0, requisition['department_name'], cell_format_left)
					sheet.write(rowx, 1, requisition['employee_name'], cell_format_left)
					sheet.write(rowx, 2, requisition['requisition_number'], cell_format_left)
				else:
					sheet.merge_range(rowx, 0, row-1, 0, requisition['department_name'], cell_format_left)
					sheet.merge_range(rowx, 1, row-1, 1, requisition['employee_name'], cell_format_left)
					sheet.merge_range(rowx, 2, row-1, 2, requisition['requisition_number'], cell_format_left)


				
		workbook.close()

		out = base64.encodestring(output.getvalue())
		file_name = u'Харьцуулалтын гүйцэтгэлийн тайлан'
		excel_id = self.env['report.excel.output'].create({'data':out,'name':file_name + '.xlsx'})

		return {
		'name': 'Export Report',
		'view_mode':'form',
		'res_model':'report.excel.output',
		'res_id':excel_id.id,
		'view_id':False,
		'type': 'ir.actions.act_window',
		'target':'new',
		'nodestroy': True,
		}