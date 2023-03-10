# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-Today OpenERP SA (<http://www.openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.tools.translate import _
# from openerp.addons.l10n_mn_report_base.report_helper import verbose_numeric, comma_me, convert_curr
from openerp import api, fields, models, _
from datetime import datetime,timedelta
from operator import itemgetter
import xlsxwriter
from io import BytesIO
import base64

class TenderRequestReport(models.TransientModel):
	_name = 'tender.request.report'

	start_date = fields.Date(string="Start date", required=True)
	end_date = fields.Date(string="End date", required=True)

	@api.multi
	def export_report(self):
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

		sheet = workbook.add_worksheet()
	
		sheet.portrait=True


		# sheet.write(1, 3, u'???????????? ?????????????????? ????????????', title)
		# sheet.write(2, 0, u'?????????? ?????????????? :'+  self.start_date , title)
		# sheet.write(2, 1, u'???????????? ?????????????? :'+ self.end_date, title)
#		sheet.write(3, 0, u'???????????? :'+ self.department_id.name, title)
		query="select A.name as name, A.desc_name as desc, B.name as categ,C.name as child_categ,D.name as sector, E.name as department,G.name as user, \
				H.name as res_department , T.name_related as res_employee,A.create_date as create_date, A.state as state, A.description as description \
				from tender_tender A inner join tender_type B ON A.type_id=B.id \
				inner join tender_type C ON C.id=A.child_type_id inner join hr_department D ON D.id=A.sector_id inner join hr_department E \
				ON E.id =A.department_id inner join res_users F ON F.id = A.user_id inner join res_partner G ON G.id= F.partner_id \
				left join hr_department H ON H.id=A.respondent_department_id left join hr_employee T on T.id= A.respondent_employee_id \
				\
		"
		where=" where A.create_date between '%s' and '%s' and A.state in ('sent','confirmed','contract_request','contract_created','open','reject','delay')"%(self.start_date,self.end_date)
		


		query=query+where +" order by A.create_date asc"


		self.env.cr.execute(query)
		dictfetchall = self.env.cr.dictfetchall()

		sheet.write(0,0,'???',header)
		sheet.set_column(0,0,5)
		sheet.write(0,1,u'?????????????????? ???????????? ????????????' ,header)
		sheet.set_column(0,1,7)
		sheet.write(0,2,u'?????????????????? ??????' ,header)
		sheet.set_column(0,2,15)
		sheet.write(0,3,u'?????????????????? ??????????????' ,header)
		sheet.set_column(0,3,15)
		sheet.write(0,4,u'?????? ??????????????' ,header)
		sheet.set_column(0,4,15)
		sheet.write(0,5,u'?????????????????? ????????????' ,header)
		sheet.set_column(0,5,15)
		sheet.write(0,6,u'?????????????????? ????????????' ,header)
		sheet.set_column(0,6,15)
		sheet.write(0,7,u'???????????? ??????????????' ,header)
		sheet.set_column(0,7,15)
		sheet.write(0,8,u'?????????????????? ??????????????' ,header)
		sheet.set_column(0,8,15)
		sheet.write(0,9,u'???????????? ??????????' ,header)
		sheet.set_column(0,9,15)
		sheet.write(0,10,u'??????????' ,header)
		sheet.set_column(0,10,15)
		# sheet.write(0,11,u'???????????? ??????????' ,header)
		# sheet.set_column(0,11,15)
		# sheet.write(0,12,u'???????????? ??????????' ,header)
		# sheet.set_column(0,12,15)


		if dictfetchall:
			count =1
			row=1
			for dic in dictfetchall:
				sheet.write(row,0,count ,cell_float_format_left)
				sheet.write(row,1, dic['name'],cell_float_format_left)
				sheet.write(row,2, dic['desc'],cell_float_format_left)
				sheet.write(row,3, dic['categ'],cell_float_format_left)
				sheet.write(row,4, dic['child_categ'],cell_float_format_left)
				sheet.write(row,5, dic['sector'],cell_float_format_left)
				sheet.write(row,6, dic['department'],cell_float_format_left)
				sheet.write(row,7, dic['user'],cell_float_format_left)
				#sheet.write(0,8, dic['res_department'],cell_float_format_left)
				sheet.write(row,8, dic['res_employee'],cell_float_format_left)
				sheet.write(row,9, dic['create_date'],cell_float_format_left)
				sheet.write(row,10, dic['state'],cell_float_format_left)
				row+=1
				count+=1


		workbook.close()
		out = base64.encodestring(output.getvalue())
		file_name = u'???????????? ?????????????????? ????????????'
		excel_id = self.env['report.excel.output'].create({'data':out,'name':file_name + '.xlsx'})

		return {
		'name': 'Export Report',
		'view_type':'form',
		'view_mode':'form',
		'res_model':'report.excel.output',
		'res_id':excel_id.id,
		'view_id':False,
#		'context':self._context,
		'type': 'ir.actions.act_window',
		'target':'new',
		'nodestroy': True,
		}

	