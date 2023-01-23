# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError
import xlrd, base64, os
from tempfile import NamedTemporaryFile

class ImportOperationTask(models.TransientModel):
	_name = 'import.operation.task'
	_description = 'Import operation task'

	data = fields.Binary(string='File', required=True)


	
	def import_data(self):	       
		form = self
		fileobj = NamedTemporaryFile('w+')
		fileobj.write(base64.decodestring(form.data))
		fileobj.seek(0)

		if not os.path.isfile(fileobj.name):
			raise UserError(_(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!'))
        
		book = xlrd.open_workbook(fileobj.name)
		sheet = book.sheet_by_index(0)
		nrows = sheet.nrows
		
		if self._context['active_id']:
			active_id = self._context['active_id']

		if not active_id:
			raise UserError(_(u'Алдаа',u'Та F5 дараад дахин үргэжлүүлнэ үү!'))	
		rowi = 1
		count = 0
		sp_dict = {}
		while rowi < nrows:
			try:
				row = sheet.row(rowi)
				name = row[1].value
				quantity = row[2].value
				uom = row[3].value
				claim = row[4].value
				description = row[5].value
				
				
				if uom:
					uom_id = self.env['product.uom'].search([('name','=',str(uom))])
				if not uom_id:
					raise UserError(_(u'%s мөр дээр алдаа гарав. %s хэмжих нэгж системд бүртгэлгүй байна эсвэл хэмжих нэгжийг буруу бичсэн байна.' % (rowi,uom)))	
				is_type = False
				if type(quantity)==int or type(quantity)==float:
					is_type= True
				if not is_type:
					raise UserError(_('%s мөр дээр алдаа гарав. Та тоо хэмжээ багана дээр тоо оруулах боломжтой.' % rowi))

				sp_dict[count] = {
						'name': str(name),	
						'quantity':float(quantity),
						'uom_id':uom_id.id,
						'material_claim':str(claim),
						'description':str(description),
						'task_id':active_id,
					}		
			
				count+=1
				rowi += 1
			except IndexError :
				raise UserError(_('error on row: %s ' % rowi))


		if sp_dict:			
			for row in range(count):
				self.env['task.operation'].create(sp_dict[row])
		
		return {'type': 'ir.actions.act_window_close'}