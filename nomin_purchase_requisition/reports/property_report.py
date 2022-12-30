
# -*- coding: utf-8 -*-

from openerp.tools.translate import _
from openerp import api, fields, models, _,modules
from datetime import datetime,timedelta,date
from operator import itemgetter
from openerp.exceptions import UserError, ValidationError, RedirectWarning
import xlsxwriter
from io import BytesIO
import base64
import requests
from zeep import Client
import json
import pdfkit
# from openerp.addons.nomin_payroll.report.nomin_payroll_salary_report import encode_for_xml ,_xmlcharref_encode
from openerp.addons.l10n_mn_report_base.report_helper import verbose_numeric, comma_me, convert_curr
import logging
_logger = logging.getLogger(__name__)

class PropertyReport(models.TransientModel):
	_name = 'property.report'
	
	def get_active_object(self):
		context = self._context
		if context.get('active_model') and context.get('active_id'):
			if context['active_model'] == 'fixed.asset.counting' and context['active_id']:
				return self.env['fixed.asset.counting'].browse(context['active_id'])


	def _start_date(self):
		employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
		active_obj = self.get_active_object()

		if employee_id.parent_department:

			if employee_id.parent_department.nomin_code == "024" and date.today()<datetime.strptime('2021-04-01', '%Y-%m-%d').date() :
				return  datetime.strptime('2021-01-01', '%Y-%m-%d').date() 
			else:
				return date.today()
		else:
			return date.today()


	def _account_from(self):
		active_obj = self.get_active_object()
		if not active_obj:
			return False
		if active_obj.account_from:
			return active_obj.account_from
		else:
			return False



	def _type(self):
		active_obj = self.get_active_object()
		if active_obj:
			return active_obj.type
		else:
			return False

	def _is_same_company(self):
		return False

	@api.model
	def default_get(self, fields):
		res = super(PropertyReport, self).default_get(fields)		
		request_id = self.env['fixed.asset.counting'].browse(self._context.get('active_ids', []))

		default_date = date.today() - timedelta(days=70)
		prev_request_id = self.env['fixed.asset.counting'].search([('start_date','>',default_date),('department_id','=',request_id.department_id.id)],limit=1,order="start_date desc")
		if prev_request_id:
			res.update({'start_date':prev_request_id.start_date,
                        })
		return res




	filter_options = fields.Selection([
        ('аccount',u'Account - Дансаар шүүх'),
        ('owner',u'Owner - Эд хариуцагчаар шүүх'),
        ('code',u'Code - Хөрөнгийн кодоор шүүх'),
        ('type',u'Type - Данс ба хөрөнгийн бүлгээр шүүх'),
        ('location',u'Location - Байршил ба дансаар шүүх')
    ], u'Хөрөнгө шүүх сонголтууд',  required=True)

    
	is_same_company = fields.Boolean(string="Is same company", compute=_is_same_company, default=False)
	start_date = fields.Date('Огноо', required=True, default=_start_date)
	department_id = fields.Many2one('hr.department', domain="[('is_sector', '=', True)]",string=' Салбар', required=True)
	account_from = fields.Many2one('account.account', string='Account from', default = _account_from)
	employee_id = fields.Many2one('hr.employee', string='Ажилтны нэр')
	location = fields.Char('Байршилын нэр')
	asset_code = fields.Char('Хөрөнгийн код')
	asset_type = fields.Many2one('fixed.assets.type', string='Хөрөнгийн бүлэг', domain="[('department_id', '=', department_id)]")

	# description = fields.Text('Description')




	@api.onchange('filter_options')
	def onchange_filter_options(self):

		if self.filter_options == 'owner':
			self.account_from = False
		else:
			self.employee_id = False
        
		if not self.filter_options == 'location':
			self.location = False
        



	@api.multi
	def button_accept(self):

		active_obj = self.get_active_object()
		result = []

		if self.start_date:
			active_obj.start_date = self.start_date            

		if self.department_id:
			active_obj.department_id = self.department_id

		if self.account_from:
			active_obj.account_from = self.account_from  

		if self.filter_options:
			active_obj.filter_options = self.filter_options


		if self.location:
			active_obj.location = self.location

		if self.employee_id:
			active_obj.employee_id = self.employee_id

		if self.asset_type:
			active_obj.asset_type = self.asset_type


		# if self.description:
		# 	active_obj.description = self.description

		filter_options = self.filter_options[0].upper()

		active_obj.name = self.department_id.nomin_code + str(self.start_date)[2:4] + type  + str(self.start_date)[5:7] + filter_options




		self.get_assets(active_obj)


		return {'type': 'ir.actions.act_window_close'}



	@api.multi
	def export_chart(self,active_obj):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)				
		header = workbook.add_format({'border':1,'fg_color':'#b0e2ff','align':'justify','valign':'vjustify','text_wrap':100,'pattern':0})

		title = workbook.add_format({
		'border': 0,
		'bold': 1,
		'align': 'center',
		'valign': 'vcenter',
		# 'text_wrap': 'on',
		'font_size':12,
		'font_name': 'Arial',
		})


		header_color = workbook.add_format({
		'border': 1,
		'bold': 1,
		'align': 'center',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		'bg_color':'#BDFDFF',
		'font_name': 'Arial',
		})

		header_left = workbook.add_format({
		'border': 1,
		'bold': 1,
		'align': 'left',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		# 'bg_color':'#BDFDFF',
		'font_name': 'Arial',
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
		'num_format': '#,0.'
		})
		
		cell_float_format_right = workbook.add_format({
		'border': 0,
		'bold': 0,
		'align': 'right',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		'font_name': 'Arial',
		# 'bg_color':'#40E0D0',
		'num_format': '#,##0.00'
		})

		cell_format_center = workbook.add_format({
		'border': 1,
		'bold': 0,
		'align': 'center',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		#'bg_color':'#ADBFF7',
		'font_name': 'Arial',
		# 'num_format': '#,##0.00'
		})

		sum_format_center = workbook.add_format({
		'top': 1,
		'bold': 0,
		'align': 'center',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':12,
		#'bg_color':'#ADBFF7',
		'font_name': 'Arial',
		'num_format': '#,##0.00'
		})

		footer_color = workbook.add_format({
		'border': 0,
		'bold': 1,
		'align': 'center',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':8,
		'bg_color':'#E0E0E0',
		'font_name': 'Arial',
		'num_format': '#,##0.00'
		})
		sheet = workbook.add_worksheet()
		
		sheet.portrait=True
		row = 5
		col = 5


		sheet.merge_range(1,0,1,3,u'Хөрөнгийн тайлан', title)
		sheet.merge_range(2,0,2,2,u'Хөрөнгийн тайлан', title)
		sheet.write(row,  0,u'№', header_color)
		sheet.set_column(0,0,5)
		sheet.write(row,  1,u'Хөрөнгийн код', header_color)
		sheet.set_column(1,1,15)
		sheet.write(row,  2,u'Хөрөнгийн данс', header_color)
		sheet.set_column(2,2,10)
		sheet.write(row,  3,u'Хөрөнгийн нэр', header_color)
		sheet.set_column(3,3,40)    
		sheet.write(row,  4,u'Тоо хэмжээ', header_color)
		sheet.set_column(4,4,15) 
		sheet.write(row,  5,u'Анхны өртөг', header_color)
		sheet.set_column(5,5,15)
		sheet.write(row,  6,u'Нийт элэгдэл', header_color)
		sheet.set_column(6,6,30) 
		sheet.write(row,  7,u'Одоогийн үнэ цэнэ', header_color)
		sheet.set_column(7,7,30) 
		sheet.write(row,  8,u'CustomerID', header_color)
		sheet.set_column(8,8,10)
		# sheet.write(row,  9,u'AssetInfID', header_color)
		# sheet.set_column(9,9,30) 
		# sheet.write(row,  10,u'LocationInfID', header_color)
		# sheet.set_column(10,10,30) 
		# sheet.write(row,  11,u'CustomerID', header_color)
		# sheet.set_column(11,11,15)
		# sheet.write(row,  12,u'AccountID', header_color)
		# sheet.set_column(12,12,20) 
		
		url = self.env['integration.config'].sudo().search([('name','=','handle_asset_transfer')]).server_ip
		client = Client(url)


		account_type ="1"
		account_from =""

		location_type ="1"
		location_string = ""

		asset_type ="1"
		asset_string = ""

		customer_type ="1"
		customer_string = ""


		if self.filter_options == 'owner':
			customer_type = "0"
			customer_string = self.sudo().employee_id.passport_id
		else:
			account_type = "0"
			account_from = str(self.account_from.code)

            
		if self.filter_options == 'type':
			asset_type = "4"
			asset_string = self.asset_type.inf_id

		if self.filter_options == 'location':
			location_type = "3"
			location_string = self.location

		asset_dict = {
            'account_type': account_type,
            'account_from':account_from,
            'location_type':location_type,
            'location_string':location_string,
            'asset_type':asset_type,
            'asset_string':asset_string,
            'customer_type':customer_type,
            'customer_string':customer_string,          
        }

		# active_obj.sudo().write(
        # {
        #     'json_data':json.dumps(asset_dict)               
        # })

       

		
		response = client.service.AssetCountGetForSum("1",self.start_date,self.department_id.nomin_code,account_type,account_from,location_type,location_string,"1","",asset_type,asset_string,customer_type,customer_string)




		if response:
			try:
				result_dict = json.loads('['+response+']')
			except ValueError as e:
				raise UserError(_('Мэдээлэл татахад алдаа гарлаа.\n Салбарын код [%s] Дансны дугаар [%s] Алдааны мессеж [%s] response [%s]'%(self.department_id.nomin_code,self.account_from.code,e,response)))
			if result_dict:
				
				count_of_items = 0
				owner_ids=[]
				count_of_owners = 0
				asset_ids=[]
				count_of_assets = 0
				results = {}
				for dic in result_dict:
					group =  dic['AssetID']
					if group not in results:
						results[group] ={
							'EndDeprAmt' :u'Тодорхойгүй',
							'EndAmt' :u'Тодорхойгүй',
							'AssetDesc' :u'Тодорхойгүй',
							'BeginUnitCost' :u'Тодорхойгүй',
							'AssetID' :u'Тодорхойгүй',
							'DeprAccountID' :u'Тодорхойгүй',
							'AccountantInfID' :u'Тодорхойгүй',
							'EndQty' :u'Тодорхойгүй',
							'AssetInfID' :u'Тодорхойгүй',
							'LocationInfID' :u'Тодорхойгүй',
							'CustomerID' :u'Тодорхойгүй',
							'AccountID' :u'Тодорхойгүй'
						}
					results[group]['AssetID'] = group
					results[group]['EndDeprAmt'] = dic['EndDeprAmt']
					results[group]['EndAmt'] = dic['EndAmt']
					results[group]['AssetDesc'] = dic['AssetDesc']
					results[group]['BeginUnitCost'] = dic['BeginUnitCost']
					results[group]['DeprAccountID'] = dic['DeprAccountID']
					results[group]['AccountantInfID'] = dic['AccountantInfID']
					results[group]['EndQty'] = dic['EndQty']
					results[group]['AssetInfID'] = dic['AssetInfID']
					results[group]['LocationInfID'] = dic['LocationInfID']
					results[group]['CustomerID'] = dic['CustomerID']
					results[group]['AccountID'] = dic['AccountID']
				row+=1
				count = 1
				for item in sorted(results.values() , key = itemgetter('AssetID')):
					sheet.write(row,  0,count, cell_format_center)
					sheet.write(row,  1,item['AssetID'], cell_float_format_left)
					sheet.write(row,  2,item['AccountID'], cell_format_center)
					sheet.write(row,  3,item['AssetDesc'], cell_float_format_left)
					sheet.write(row,  4,item['EndQty'], cell_float_format_left)
					sheet.write(row,  5,item['BeginUnitCost'], cell_float_format_left)
					sheet.write(row,  6,item['EndDeprAmt'], cell_float_format_left)
					sheet.write(row,  7,item['EndAmt'], cell_float_format_left)
					sheet.write(row,  8,item['CustomerID'], cell_float_format_left)
					# sheet.write(row,  9,item['AssetInfID'], cell_float_format_left)
					# sheet.write(row,  10,item['LocationInfID'], cell_float_format_left)
					# sheet.write(row,  11,item['CustomerID'], cell_float_format_left)
					# sheet.write(row,  12,item['AccountID'], cell_float_format_left)
					count = 1
					row+=1
		workbook.close()
		out = base64.encodestring(output.getvalue())
		file_name = u'Хөрөнгийн тайлан'
		excel_id = self.env['report.excel.output'].create({'data':out,'name':file_name + '.xlsx'})

		return {
        'name': _('Download contract'),
        'context': self._context,
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'report.excel.output',
        'res_id': excel_id.id,
        'type': 'ir.actions.act_window',
        'target': 'new',
        }
