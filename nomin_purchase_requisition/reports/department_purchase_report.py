# -*- coding: utf-8 -*-
from openerp import api, fields, models
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import xlsxwriter
from io import BytesIO
import base64

class DepartmentPurchaseReport(models.TransientModel):
	''' Салбаруудын худалдан авалтын нэгтгэл тайлан '''
	_name = 'department.purchase.report'

	start_date = fields.Date(string=u'Эхлэх огноо' )
	end_date = fields.Date(string=u'Дуусах огноо')
	department_ids = fields.Many2many(comodel_name = 'hr.department',string=u'Хэлтэс')


	@api.multi
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

		where = " WHERE A.create_date BETWEEN '%s' AND '%s'"%(self.start_date, self.end_date)

		if self.department_ids:
			if len(self.department_ids.ids)>1:
				where = where+"and C.id in %s"%( str(tuple(self.department_ids.ids)))
			else:
				where = where+"and C.id = %s"%(str(self.department_ids.ids[0]))

		query = "SELECT C.id as department_id, C.name as department_name, D.id as user_id, F.id as employee_id, F.name_related as employee_name, \
            A.name as requisition_number, A.id as requisition_id, B.id as requisition_line_id, G.name_template as product_name,\
            J.name_related as buyer_name, B.product_qty, B.product_price as product_price, B.comparison_date as comparison_date,\
            K.name as comparison_number, L.name as priority, L.priority_day as priority_day, B.date_start as assigned_date, B.date_end as date_end,\
            M.supplied_product_quantity as supplied_qty, M.supplied_product_price as supplied_product_price,\
            (CASE WHEN K.name is not null THEN 'Тийм' ELSE 'Үгүй' END) as comparison, P.name_related as comparison_employee, B.comparison_date_end as comparison_date_end\
            FROM purchase_requisition A\
            LEFT JOIN purchase_requisition_line B ON B.requisition_id = A.id\
            INNER JOIN hr_department C ON C.id = A.department_id\
            INNER JOIN res_users D ON D.id = A.user_id\
            INNER JOIN resource_resource E ON E.user_id = D.id\
            INNER JOIN hr_employee F ON F.resource_id = E.id\
            LEFT JOIN product_product G ON G.id = B.product_id\
            LEFT JOIN res_users H ON B.buyer = H.id\
            LEFT JOIN resource_resource I ON I.user_id = H.id\
            LEFT JOIN hr_employee J ON J.resource_id = I.id\
            LEFT JOIN purchase_comparison K ON B.comparison_id = K.id\
            LEFT JOIN purchase_priority L ON A.priority_id = L.id\
            LEFT JOIN purchase_requisition_supplied_quantity M ON M.line_id = B.id\
            LEFT JOIN res_users N ON B.comparison_user_id = N.id\
            LEFT JOIN resource_resource O ON O.user_id = N.id\
            LEFT JOIN hr_employee P ON P.resource_id = o.id\
		"
		
		where += " AND A.state = 'done' "

		query = query + where
		self.env.cr.execute(query)
		dictfetchall = self.env.cr.dictfetchall()
		if dictfetchall:
			departments = {}
			for fetch in dictfetchall:
				group = fetch['department_id']
				if group not in departments:
					departments[group] = {
						'department_name':u'Тодорхойгүй',
						'department_id':u'Тодорхойгүй',
						'employees':{}
					}

				departments[group]['department_id']     = group
				departments[group]['department_name']   = fetch['department_name']

				group1 = fetch['employee_id']
				if group1 not in departments[group]['employees']:
					departments[group]['employees'][group1] = {
						'employee_name':u'Тодорхойгүй',
						'user_id':u'Тодорхойгүй',
						'requisitions':{}
					}
                
				departments[group]['employees'][group1]['employee_id'] 	    = group1
				departments[group]['employees'][group1]['employee_name'] 	= fetch['employee_name']
				
				group2 = fetch['requisition_id']
				if group2 not in departments[group]['employees'][group1]['requisitions']:
					departments[group]['employees'][group1]['requisitions'][group2] = {
						'requisition_id':u'Тодорхойгүй',
						'requisition_number':u'Тодорхойгүй',
						'requisition_lines':{}
					}

				departments[group]['employees'][group1]['requisitions'][group2]['requisition_id']	    = group2
				departments[group]['employees'][group1]['requisitions'][group2]['requisition_number']   = fetch['requisition_number']

				group3 = fetch['requisition_line_id']
				if group3 not in departments[group]['employees'][group1]['requisitions'][group2]['requisition_lines']:
					departments[group]['employees'][group1]['requisitions'][group2]['requisition_lines'][group3] = {
						'requisition_line_id':u'Тодорхойгүй',
						'product_name':u'Тодорхойгүй',
						'buyer_name':u'Тодорхойгүй',
						'assigned_date':u'Тодорхойгүй',
						'date_end':u'Тодорхойгүй',
						'comparison_number':u'Тодорхойгүй',
						'comparison_date':u'Тодорхойгүй',
						'supplied_qty':u'Тодорхойгүй',
						'supplied_product_price':u'Тодорхойгүй',
						'product_price':u'Тодорхойгүй',
						'product_qty':u'Тодорхойгүй',
						'comparison_date':u'Тодорхойгүй',
						'priority':u'Тодорхойгүй',
						'comparison':u'Тодорхойгүй',
						'comparison_employee':u'Тодорхойгүй',
						'priority_day':0,
					}

				departments[group]['employees'][group1]['requisitions'][group2]['requisition_lines'][group3]['requisition_line_id'] = group3
				departments[group]['employees'][group1]['requisitions'][group2]['requisition_lines'][group3]['product_name'] 		= fetch['product_name']
				departments[group]['employees'][group1]['requisitions'][group2]['requisition_lines'][group3]['buyer_name'] 			= fetch['buyer_name']
				departments[group]['employees'][group1]['requisitions'][group2]['requisition_lines'][group3]['assigned_date'] 		= fetch['assigned_date']
				departments[group]['employees'][group1]['requisitions'][group2]['requisition_lines'][group3]['date_end'] 			= fetch['date_end']
				departments[group]['employees'][group1]['requisitions'][group2]['requisition_lines'][group3]['comparison_number'] 	= fetch['comparison_number']
				departments[group]['employees'][group1]['requisitions'][group2]['requisition_lines'][group3]['comparison_date'] 	= fetch['comparison_date']
				departments[group]['employees'][group1]['requisitions'][group2]['requisition_lines'][group3]['priority'] 			= fetch['priority']
				departments[group]['employees'][group1]['requisitions'][group2]['requisition_lines'][group3]['priority_day'] 		= fetch['priority_day']
				departments[group]['employees'][group1]['requisitions'][group2]['requisition_lines'][group3]['supplied_qty'] 		= fetch['supplied_qty']
				departments[group]['employees'][group1]['requisitions'][group2]['requisition_lines'][group3]['supplied_product_price'] 		= fetch['supplied_product_price']
				departments[group]['employees'][group1]['requisitions'][group2]['requisition_lines'][group3]['product_price'] 		= fetch['product_price']
				departments[group]['employees'][group1]['requisitions'][group2]['requisition_lines'][group3]['product_qty'] 		= fetch['product_qty']
				departments[group]['employees'][group1]['requisitions'][group2]['requisition_lines'][group3]['comparison'] 			= fetch['comparison']
				departments[group]['employees'][group1]['requisitions'][group2]['requisition_lines'][group3]['comparison_employee'] = fetch['comparison_employee']
				departments[group]['employees'][group1]['requisitions'][group2]['requisition_lines'][group3]['comparison_date_end'] = fetch['comparison_date_end']



			sheet = workbook.add_worksheet(u'Худалдан авалтын нэгтгэл тайлан')
		
			sheet.portrait=True
			sheet.set_column('A:A',20)
			sheet.set_column('B:B',15)
			sheet.set_column('C:C',10)
			sheet.set_column('D:D',20)
			sheet.set_column('E:K',15)
			sheet.set_column('L:T',10)
			sheet.set_row(4,50)

			date_from = datetime.strptime(self.start_date, "%Y-%m-%d").strftime('%Y.%m.%d')
			date_to = datetime.strptime(self.end_date, "%Y-%m-%d").strftime('%Y.%m.%d')
			
			sheet.merge_range(1, 0, 1, 18, u'Салбаруудын худалдан авалтын нэгтгэл тайлан', header)
			sheet.merge_range(3, 0, 3, 2, u'Тайлангийн огноо: ' + date_from + '-' + date_to, title)
			
			row = 4

			sheet.write(row, 0, 'Захиалсан салбар', table_header)
			sheet.write(row, 1, 'Захиалсан ажилтан', table_header)
			sheet.write(row, 2, 'Шаардах №', table_header)
			sheet.write(row, 3, 'Материалын нэр', table_header)
			sheet.write(row, 4, 'Худалдан авалтын ажилтан', table_header)
			sheet.write(row, 5, 'Шаардах дээр байгаа тоо ширхэг', table_header)
			sheet.write(row, 6, 'Шаардах дээр байгаа нэгж үнэ', table_header)
			sheet.write(row, 7, 'Гүйцэтгэлээрх нийлүүлсэн тоо хэмжээ', table_header)
			sheet.write(row, 8, 'Гүйцэтгэлээрх нэгж үнэ', table_header)
			sheet.write(row, 9, 'Гүйцэтгэлээрх нийт үнэ', table_header)
			sheet.write(row, 10, 'Захиалга хүлээж авсан огноо', table_header)
			sheet.write(row, 11, 'Захиалга биелүүлвэл зохих огноо', table_header)
			sheet.write(row, 12, 'Харьцуулалттай эсэх', table_header)
			sheet.write(row, 13, 'Харьцуулалтын дугаар', table_header)
			sheet.write(row, 14, 'Харьцуулалтын ажилтан', table_header)
			sheet.write(row, 15, 'Харьцуулалт биелүүлвэл зохих огноо', table_header)
			sheet.write(row, 16, 'Захиалга хүлээлгэн өгсөн огноо', table_header)
			sheet.write(row, 17, 'Хэтэрсэн хоног', table_header)
			sheet.write(row, 18, 'Хэтэрсэн хоног Харьцуулалт', table_header)
			sheet.write(row, 19, 'Урьтамж', table_header)

			row += 1

			for department in sorted(departments.values(), key=itemgetter('department_id')):
				rowdep = row

				for employee in sorted(department['employees'].values(), key=itemgetter('employee_id')):
					rowemp = row

					for requisition in sorted(employee['requisitions'].values(), key=itemgetter('requisition_id')):
						rowreq = row

						for line in sorted(requisition['requisition_lines'].values(), key=itemgetter('requisition_line_id')):
							
							planned_date = None
							if line['assigned_date']:
								assigned_date = datetime.strptime(line['assigned_date'], "%Y-%m-%d")
								planned_date = (assigned_date + relativedelta(days=line['priority_day'])).strftime('%Y-%m-%d')

							date_diff = 0
							if line['date_end']:
								date_end = datetime.strptime(line['date_end'], "%Y-%m-%d")
								if planned_date:
									plan = datetime.strptime(planned_date, "%Y-%m-%d")
									date_diff = (date_end - plan).days

									
							comparison_date_diff = 0
							if line['comparison_date_end']:
								comparison_date_end = datetime.strptime(line['comparison_date_end'], "%Y-%m-%d")
								if line['comparison_date']:
									comparison_date = datetime.strptime(line['comparison_date'], "%Y-%m-%d")
									comparison_date_diff = (comparison_date_end - comparison_date).days

							supplied_price = 0
							if line['supplied_qty'] and line['supplied_product_price']:
								supplied_price = line['supplied_qty'] * line['supplied_product_price']


							sheet.write(row, 3, line['product_name'], cell_format_left)
							sheet.write(row, 4, line['buyer_name'], cell_format_left)
							sheet.write(row, 5, line['product_qty'], cell_format_right_float)
							sheet.write(row, 6, line['product_price'], cell_format_right_float)
							sheet.write(row, 7, line['supplied_qty'], cell_format_right_float)
							sheet.write(row, 8, line['supplied_product_price'], cell_format_right_float)
							sheet.write(row, 9, supplied_price, cell_format_right_float)
							sheet.write(row, 10, line['assigned_date'], cell_format_left)
							sheet.write(row, 11, planned_date, cell_format_left)
							sheet.write(row, 12, line['comparison'], cell_format_left)
							sheet.write(row, 13, line['comparison_number'], cell_format_left)
							sheet.write(row, 14, line['comparison_employee'], cell_format_left)
							sheet.write(row, 15, line['comparison_date'], cell_format_left)
							sheet.write(row, 16, line['date_end'], cell_format_left)
							sheet.write(row, 17, date_diff, cell_format_left)
							sheet.write(row, 18, comparison_date_diff, cell_format_left)
							sheet.write(row, 19, line['priority'], cell_format_left)

							row += 1

						if row - 1 == rowreq:
							sheet.write(rowreq, 2, requisition['requisition_number'], cell_format_left)
						else:
							sheet.merge_range(rowreq, 2, row-1, 2, requisition['requisition_number'], cell_format_left)
						
					if row - 1 == rowemp:
						sheet.write(rowemp, 1, employee['employee_name'], cell_format_left)
					else:
						sheet.merge_range(rowemp, 1, row-1, 1, employee['employee_name'], cell_format_left)

				if row - 1 == rowdep:
					sheet.write(rowdep, 0, department['department_name'], cell_format_left)
				else:
					sheet.merge_range(rowdep, 0, row-1, 0, department['department_name'], cell_format_left)
                        
		workbook.close()

		out = base64.encodestring(output.getvalue())
		file_name = u'Худалдан авалтын нэгтгэл тайлан'
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