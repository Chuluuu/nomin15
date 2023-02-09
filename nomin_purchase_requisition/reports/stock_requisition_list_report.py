# -*- coding: utf-8 -*-

from odoo.tools.translate import _
from odoo import api, fields, models, _
from datetime import datetime,timedelta
from operator import itemgetter
import xlsxwriter
from io import BytesIO
import base64

class StockRequisitionListReport(models.TransientModel):
	_name = 'stock.requisition.list.report'

	start_date = fields.Date(string="Start date", required=True)
	end_date = fields.Date(string="End date", required=True)
	department_ids = fields.Many2many(comodel_name='hr.department',relation='stock_requisition_list_report_department_rel', string='Хүлээлгэн өгсөн хэлтэсүүд')
	receive_department_ids = fields.Many2many(comodel_name='hr.department',relation='stock_requisition_list_report_received_department_rel', string='Хүлээн авсан хэлтэсүүд')


	
	def export_chart(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)

		header = workbook.add_format({'border':1,'fg_color':'#b0e2ff','align':'justify','valign':'vjustify','text_wrap':100,'pattern':0})

		title = workbook.add_format({
		'border': 0,
		'bold': 1,
		'align': 'center',
		'valign': 'vcenter',
		'text_wrap': 'off',
		'font_size':12,
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
		cell_format_center = workbook.add_format({
		'border': 1,
		'bold': 1,
		'align': 'center',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		'font_name': 'Arial',
		})
		cell_float_format_left_bold = workbook.add_format({
		'border': 1,
		'bold': 1,
		'align': 'right',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		# 'bg_color':'#40E0D0',
		'font_name': 'Arial',
		'num_format': '#,##0.00'
		})
		cell_float_format_left = workbook.add_format({
		'border': 1,
		'bold': 0,
		'align': 'right',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		# 'bg_color':'#40E0D0',
		'font_name': 'Arial',
		'num_format': '#,##0.00'
		})
		cell_float_format_left1 = workbook.add_format({
		'border': 1,
		'bold': 0,
		'align': 'right',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		# 'bg_color':'#40E0D0',
		'font_name': 'Arial',
		# 'num_format': '#,##0.00'
		})
		sheet = workbook.add_worksheet()
	
		sheet.portrait=True

		states = {'draft':'Ноорог',
		'sent_to_supply':'Бараа Тодорхойлох',
		'verify':'Хянах',
		'confirmed':'Зөвшөөрөх',
		'receive':'Хүлээн авах',
		'done':'Дууссан',
		'cancelled':'Цуцлагдсан'}
		# sheet.write(1, 3, u'Тендер хүсэлтийн тайлан', title)
		# sheet.write(2, 0, u'Эхлэх хугацаа :'+  self.start_date , title)
		# sheet.write(2, 1, u'Дуусах хугацаа :'+ self.end_date, title)
#		sheet.write(3, 0, u'Хэлтэс :'+ self.department_id.name, title)
		query="select A.name as name,(A.create_date+interval '8 hour') as create_date,D.name as product,B.product_qty as product_qty, \
				B.unit_price as unit_price, (B.unit_price*B.product_qty) as total, T.name as supply_manager,	\
				H.name as user, F.name as sector, E.name as department,N.name as assign, \
				H1.name as receive_user, F1.name as receive_sector, E1.name as receive_department, B.state as state, A.description as description\
			from stock_requisition A inner join stock_requisition_line B ON A.id=B.requisition_id \
				left join product_product C on C.id=B.product_id inner join product_template D ON C.product_tmpl_id=D.id \
				left join res_users P ON P.id=B.supply_user_id \
				left join res_partner T ON T.id=P.partner_id \
				left join hr_department E ON E.id = A.department_id \
				left join hr_department F ON F.id = A.sector_id \
				left join res_users G ON G.id = A.user_id \
				left join res_partner H ON H.id = G.partner_id \
				left join hr_department E1 ON E1.id = A.receiver_department_id \
				left join hr_department F1 ON F1.id = A.receiver_sector_id \
				left join res_users G1 ON G1.id = A.receiver_user_id \
				left join res_partner H1 ON H1.id = G1.partner_id \
				left join assign_category N ON N.id=D.assign_categ_id \
		"	
		where =""
		if self.department_ids:
			if len(self.department_ids.ids)>1:
				where=where+" and A.department_id in %s"%( str(tuple(self.department_ids.ids)))
			else:
				where=where+" and A.department_id = %s"%(str(self.department_ids.ids[0]))
		if self.receive_department_ids:
			if len(self.receive_department_ids.ids)>1:
				where=where+" and A.receiver_sector_id in %s"%( str(tuple(self.receive_department_ids.ids)))
			else:
				where=where+" and A.receiver_sector_id = %s"%(str(self.receive_department_ids.ids[0]))

		query=query+where +" order by A.create_date asc"


		self.env.cr.execute(query)
		dictfetchall = self.env.cr.dictfetchall()

		sheet.write(0,0,'№',header)
		sheet.set_column(0,0,5)
		sheet.write(0,1,u'Хөдөлгөөний шаардахын дугаар' ,header)
		sheet.set_column(0,1,7)
		sheet.write(0,2,u'Шаардахын огноо' ,header)
		sheet.set_column(0,2,15)
		sheet.write(0,3,u'Ангилал' ,header)
		sheet.set_column(0,3,7)

		sheet.write(0,4,u'Бараа' ,header)
		sheet.set_column(0,4,15)

		sheet.write(0,5,u'Тоо ширхэг' ,header)
		sheet.set_column(0,5,15)
		sheet.write(0,6,u'Нэгж үнэ' ,header)
		sheet.set_column(0,6,15)
		sheet.write(0,7,u'Нийт дүн' ,header)
		sheet.set_column(0,7,15)
		sheet.write(0,8,u'Хариуцсан хангамжийн ажилтан' ,header)
		sheet.set_column(0,8,15)
		sheet.write(0,9,u'Хөрөнгө эзэмшигч' ,header)
		sheet.set_column(0,9,15)
		sheet.write(0,10,u'Хөрөнгө эзэмшигч хэлтэс' ,header)
		sheet.set_column(0,10,15)
		sheet.write(0,11,u'Хөрөнгө эзэмшигч салбар' ,header)
		sheet.set_column(0,11,15)
		sheet.write(0,12,u'Хүлээн авагч ажилтан' ,header)
		sheet.set_column(0,12,15)
		sheet.write(0,13,u'Хүлээн авагч хэлтэс' ,header)
		sheet.set_column(0,13,15)
		sheet.write(0,14,u'Хүлээн авагч салбар' ,header)
		sheet.set_column(0,14,15)
		sheet.write(0,15,u'Төлөв' ,header)
		sheet.set_column(0,15,15)
		sheet.write(0,16,u'Тайлбар / Зориулалт' ,header)
		sheet.set_column(0,16,15)
		
		# sheet.write(0,11,u'Үүссэн огноо' ,header)
		# sheet.set_column(0,11,15)
		# sheet.write(0,12,u'Үүссэн огноо' ,header)
		# sheet.set_column(0,12,15)


		if dictfetchall:
			count =1
			row=1
			for dic in dictfetchall:
				sheet.write(row,0,count ,cell_float_format_left1)
				sheet.write(row,1, dic['name'],cell_float_format_left)
				sheet.write(row,2, dic['create_date'],cell_float_format_left)
				sheet.write(row,3, dic['assign'],cell_float_format_left)
				sheet.write(row,4, dic['product'],cell_float_format_left)
				sheet.write(row,5, dic['product_qty'],cell_float_format_left)
				sheet.write(row,6, dic['unit_price'],cell_float_format_left)
				sheet.write(row,7, dic['total'],cell_float_format_left)
				sheet.write(row,8, dic['supply_manager'],cell_float_format_left)
				sheet.write(row,9, dic['user'],cell_float_format_left)
				sheet.write(row,10, dic['department'],cell_float_format_left)
				sheet.write(row,11, dic['sector'],cell_float_format_left)
				sheet.write(row,12, dic['receive_user'],cell_float_format_left)
				sheet.write(row,13, dic['receive_department'],cell_float_format_left)
				sheet.write(row,14, dic['receive_sector'],cell_float_format_left)
				sheet.write(row,15, states[dic['state']],cell_float_format_left)
				sheet.write(row,16, dic['description'],cell_float_format_left)
				row+=1
				count+=1


		workbook.close()
		out = base64.encodestring(output.getvalue())
		file_name = u'Хөдөлгөөний шаардахын тайлан'
		excel_id = self.env['report.excel.output'].sudo().create({'data':out,'name':file_name + '.xlsx'})

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

	