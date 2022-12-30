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
from operator import itemgetter
from io import BytesIO
import base64, os
import xlrd
from openerp.osv import  osv
from tempfile import NamedTemporaryFile
from xlrd import sheet
import xlsxwriter
from openerp.exceptions import UserError

class ProductImportExport(models.TransientModel):
	_name ='product.import.export'

	data =  fields.Binary(string='File')
	is_passed = fields.Boolean(string="Is passed",default=False)
	is_import = fields.Boolean(string="Бараа оруулах",default=False)


	@api.multi
	def action_check(self):
		fileobj = NamedTemporaryFile('w+')
		
		fileobj.write(base64.decodestring(self.data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			raise osv.except_osv(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
		
		book = xlrd.open_workbook(fileobj.name)
		sheet = book.sheet_by_index(0)

		nrows = sheet.nrows
		rowi = 1
		while rowi < nrows :
			row = sheet.row(rowi)
			name= row[0].value
			product_code = row[1].value
			assign_category = row[2].value
			self.env.cr.execute("select id from product_template where product_code='%s' "%(str(product_code)))
			fetched = self.env.cr.fetchone()
			if not fetched:
				raise UserError(_(u'%s кодтой %s бараа системд бүртгэлгүй байна.\n \
					Хэрэв тухайн бараа системд бүртгэлгүй байгаа бол системд эхлээд бүртгэлнэ үү.\n \
					 Бүртгэлтэй орохгүй байгаа бол барааны код нэр шалгана уу'%(name,product_code)))

			self.env.cr.execute("select id from assign_category where name like '%s'"%(assign_category))
			fetched = self.env.cr.fetchone()
			if not fetched:
				raise UserError(_(u'%s ангилал системд бүртгэлгүй байна.'%(assign_category)))
			rowi+=1
		self.write({'is_passed':True})
		return {
		"type": "set_scrollTop",
		}

	@api.multi
	def action_update(self):
		fileobj = NamedTemporaryFile('w+')
		fileobj.write(base64.decodestring(self.data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			raise osv.except_osv(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
		book = xlrd.open_workbook(fileobj.name)
		sheet = book.sheet_by_index(0)

		nrows = sheet.nrows
		rowi = 1
		while rowi < nrows :
			row = sheet.row(rowi)
			name= row[0].value
			product_code = row[1].value
			assign_category = row[2].value

			self.env.cr.execute("select id from assign_category where name like '%s'"%(assign_category))
			fetched = self.env.cr.fetchone()

			self.env.cr.execute("update product_template set assign_categ_id=%s where product_code='%s' "%(fetched[0],product_code))
			rowi+=1
			
			
	@api.multi
	def action_export(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
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
		query="select name,product_code from product_template where assign_categ_id is null"

		self.env.cr.execute(query)
		dictfetchall = self.env.cr.dictfetchall()
		sheet = workbook.add_worksheet()
	
		sheet.portrait=True
		sheet.write(0,0,'Бараа',header)
		sheet.set_column(0,0,7)
		sheet.write(0,1,u'Барааны код' ,header)
		sheet.set_column(0,1,7)
		sheet.write(0,2,u'Ангилал' ,header)
		sheet.set_column(0,1,7)
		if dictfetchall:
			row=1
			for dic in dictfetchall:
					sheet.write(row,0,dic['name'] ,cell_float_format_left)
					sheet.write(row,1, dic['product_code'],cell_float_format_left)
					sheet.write(row,2, '',cell_float_format_left)
					row+=1
					
		workbook.close()
		out = base64.encodestring(output.getvalue())
		file_name = u'Барааны мэдээлэл'
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
	