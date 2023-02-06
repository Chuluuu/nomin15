# -*- coding: utf-8 -*-

from odoo.tools.translate import _
from odoo.addons.l10n_mn_report_base.report_helper import verbose_numeric, comma_me, convert_curr
from odoo import api, fields, models, _
from datetime import datetime
from operator import itemgetter
import xlsxwriter
from operator import itemgetter
from io import BytesIO
import base64

class purchase_requisition_performance(models.TransientModel):
	_name = 'purchase.requisition.performance'

	start_date = fields.Date(string=u'Эхлэх огноо' )
	end_date = fields.Date(string=u'Дуусах огноо')
	department_ids = fields.Many2many(comodel_name = 'hr.department',string=u'Хэлтэс')
	user_ids = fields.Many2many(comodel_name='res.users', string=u'Ажилчид')


	
	def export_chart(self,report_code,context=None):
		if context is None:
			context = {}
		datas={}
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)


		header = workbook.add_format({'border':1,'fg_color':'#b0e2ff','align':'justify','valign':'vjustify','text_wrap':100,'pattern':0})

		STATE_SELECTION = {'draft': u'Ноорог',
							'sent': u'Илгээгдсэн',  # Илгээгдсэн
							'approved': u'Зөвшөөрсөн',  # Зөвшөөрсөн
							'verified': u'Хянасан',  # Хянасан
							'confirmed': u'Батласан',  # Батласан
							'canceled': u'Цуцлагдсан',  # Цуцлагдсан
							'purchase': u'Худалдан авалт', #Худалдан авалт
		}

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
		sheet.write(2, 2, u'Худалдан авалтын гүйцэтгэлийн тайлан',title)
		sheet.write(3, 0, u'Эхлэх хугацаа :'+  self.start_date ,)
		sheet.write(4, 0, u'Дуусах хугацаа :'+ self.end_date, )
		concat=""
		if self.start_date and self.end_date:
			concat="and lh.date between '%s 00:00:00' and '%s 15:59:59'"%(self.start_date,self.end_date)
		if self.user_ids:
			if len(self.user_ids.ids)>1:
				concat=concat+"and l.buyer in %s"%(str(tuple(self.user_ids.ids)))
			else:
				
				concat=concat+"and l.buyer = %s"%(str(self.user_ids.ids[0]))
		if self.department_ids:
			if len(self.department_ids.ids)>1:
				concat=concat+"and pr.sector_id in %s"%( str(tuple(self.department_ids.ids)))
			else:
				concat=concat+"and pr.sector_id = %s"%(str(self.department_ids.ids[0]))

		query = "select (rh.create_date+ interval '8 hour') as done_date,(EXTRACT(day from (rh.create_date-l.date_start) )- pp.priority_day ) as used_days, \
			hr.name as sector,l.id as pr_line_id, resp.name as user ,resp1.name as buyer ,pr.name as pr_name ,\
			pr.confirmed_date as confirmed_date ,pr.ordering_date as pr_date,l.date_start as date_start, pt.name as product ,date(l.write_date) as receieved_date ,l.rate_percent as rate ,pp.name as priority,\
			(CASE WHEN l.comparison_id is not null THEN 'Тийм' ELSE 'Үгүй' END) as comparison_id, \
			l.comparison_state as comparison_state, l.comparison_date as comparison_date, l.comparison_date_end as comparison_date_end ,ac.name as assign_cat,l.product_qty as product_qty,\
            l.product_price as product_price, (l.product_qty * l.product_price) as amount , pq.supplied_product_price as supplied_product_price , pq.supplied_product_quantity as supplied_product_quantity ,\
            pq.supplied_amount as supplied_amount , part.name as partner_name ,\
			(case when lh.state = 'sent_nybo' then lh.date end) as date , \
			resp2.name as comparison_user_name, (l.comparison_date - l.comparison_date_end) as excess_day ,l.id as line_id,\
			pr.ordering_date_new as excess_day_new , pt1.name as deliver_product, p.is_purchase_standard as is_purchase_standard , p.is_normalized as is_normalized ,p.is_new_set as is_new_set,\
			p1.is_purchase_standard as delivery_pro_standard , p1.is_normalized as delivery_pro_normalized ,p1.is_new_set as delivery_pro_new_set,\
			pr.exceed_days_1 as exceed_day\
				from purchase_requisition  pr\
					left join hr_department hr\
				on hr.id = pr.sector_id\
					left join res_users res\
				on res.id = pr.user_id\
					left join res_partner resp\
				on resp.id= res.partner_id\
					left join purchase_requisition_line  l\
				on pr.id = l.requisition_id \
					left join res_users res1\
				on res1.id = l.buyer\
					left join res_partner resp1\
				on resp1.id= res1.partner_id\
                    left join res_users res2\
				on res2.id = l.comparison_user_id\
					left join res_partner resp2\
				on resp2.id= res2.partner_id\
					left join product_product  p\
				on l.product_id = p.id \
					left join product_product  p1 \
            	on l.deliver_product_id = p1.id \
					left join product_template pt\
				on p.product_tmpl_id = pt.id\
					left join product_template pt1\
				on l.deliver_product_id = pt1.id\
					left join request_history rh\
				on rh.requisition_id = pr.id\
					left join purchase_priority pp\
				on pp.id = pr.priority_id\
                    left join purchase_requisition_line_state_history lh\
				on lh.requisition_line_id = l.id\
                    left join assign_category ac \
                on ac.id = l.assign_cat\
                    left join purchase_requisition_supplied_quantity pq \
                on pq.line_id = l.id\
					left join res_partner part\
                on pq.partner_id = part.id \
					where lh.state in ('sent_nybo')"

		query=query+concat
		self.env.cr.execute(query)
		dictfetchall = self.env.cr.dictfetchall()
		dictbuyer = {}
		if dictfetchall:
			for dic in dictfetchall:
				group = dic['buyer']
				if group not in dictbuyer:
					dictbuyer[group] = {
					'buyer':u'Тодорхойгүй',
					'sector':{}
					}
				if group:
					dictbuyer[group]['buyer']=group
				group1 = dic ['sector']
				if group1 not in dictbuyer[group]['sector']:
					dictbuyer[group]['sector'][group1] = {
					'sector':u'Тодорхойгүй',
					'employee':{}
					}
				
				dictbuyer[group]['sector'][group1]['sector']=group1
				group2 = dic['user']
				if group2 not in dictbuyer[group]['sector'][group1]['employee']:
					dictbuyer[group]['sector'][group1]['employee'][group2] = {
					'employee':u'Тодорхойгүй',
					'requisition':{}
					}
				dictbuyer[group]['sector'][group1]['employee'][group2]['employee']=group2

				group3 = dic['pr_name']
				if group3 not in dictbuyer[group]['sector'][group1]['employee'][group2]['requisition']:
					dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3] = {
					'requisition':u'Тодорхойгүй',
					'product':{},
					
					}
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['requisition']=group3
				group4 = dic['line_id']
				if group4 not in dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product']:
					dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]={
						'line_id':u'Тодорхойгүй',
						'product':u'Тодорхойгүй',
						'deliver_product':u'Тодорхойгүй',
						'rate':0.0,
						'create_date':u'Тодорхойгүй',
						'received_date':u'Тодорхойгүй',
						'ordering_date':u'Тодорхойгүй',
						'priority':u'Тодорхойгүй',
						'assign_cat':u'Тодорхойгүй',
						'product_qty':u'Тодорхойгүй',
						'product_price':u'Тодорхойгүй',
						'amount':u'Тодорхойгүй',
						'supplied_product_price':u'Тодорхойгүй',
						'supplied_product_quantity':u'Тодорхойгүй',
						'supplied_amount':u'Тодорхойгүй',
						'partner_name':u'Тодорхойгүй',
						'date':u'Тодорхойгүй',
						'comparison_user_name':u'Тодорхойгүй',
						'excess_day':u'Тодорхойгүй',
						'is_purchase_standard':u'Тодорхойгүй',
						'is_normalized':u'Тодорхойгүй',
						'is_new_set':u'Тодорхойгүй',
						'delivery_pro_standard':u'Тодорхойгүй',
						'delivery_pro_normalized':u'Тодорхойгүй',
						'delivery_pro_new_set':u'Тодорхойгүй',
						'used_days':0.0,
					}
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['product']=dic['product']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['deliver_product'] =dic['deliver_product']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['rate'] =dic['rate']
				# move_id = self.env['stock.move'].sudo().search([('requisition_line_id','=',dic['pr_line_id']),('picking_type_id.code','=','incoming')])
				# if len(move_id)>1:
				# 	move_id = move_id[0]
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['rate'] =dic['rate']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['comparison_id'] =dic['comparison_id']
				if dic['comparison_state']:
					dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['comparison_state'] =STATE_SELECTION[dic['comparison_state']]
				else:
					dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['comparison_state'] =dic['comparison_state']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['comparison_date'] =dic['comparison_date']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['comparison_date_end'] =dic['comparison_date_end']
				# dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['create_date'] =move_id.create_date[0:10] if move_id else ''
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['create_date'] = str(dic['done_date'])[0:19]
				# dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['received_date'] = move_id.write_date[0:10] if move_id.picking_id.state=='done' else ''
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['received_date'] = str(dic['confirmed_date'])[0:19]
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['ordering_date'] =dic['excess_day_new']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['exceed_day'] =dic['exceed_day']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['priority'] =dic['priority']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['assign_cat'] =dic['assign_cat']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['product_qty'] =dic['product_qty']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['product_price'] =dic['product_price']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['amount'] =dic['amount']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['supplied_product_price'] =dic['supplied_product_price']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['supplied_product_quantity'] =dic['supplied_product_quantity']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['supplied_amount'] =dic['supplied_amount']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['partner_name'] =dic['partner_name']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['date'] =dic['date']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['comparison_user_name'] =dic['comparison_user_name']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['excess_day'] =dic['excess_day']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['is_purchase_standard'] =dic['is_purchase_standard']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['is_normalized'] =dic['is_normalized']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['is_new_set'] =dic['is_new_set']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['delivery_pro_standard'] =dic['delivery_pro_standard']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['delivery_pro_normalized'] =dic['delivery_pro_normalized']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['delivery_pro_new_set'] =dic['delivery_pro_new_set']
				dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['used_days'] =str(dic['used_days'])
				# dictbuyer[group]['sector'][group1]['employee'][group2]['requisition'][group3]['product'][group4]['used_days'] = (datetime.strptime(move_id.create_date[0:10], "%Y-%m-%d")-datetime.strptime(dic['pr_date'], "%Y-%m-%d")).days if move_id else ''


		if dictbuyer:
			row = 3
			col = 0

			for buyer in sorted(dictbuyer.values(), key=itemgetter('buyer')):
				
				sheet.write(row,  0,buyer['buyer'], header_color)
				sheet.merge_range(row, 6, row, 8, u"Батлагдсан төсөв", header_color)
				sheet.merge_range(row, 9, row, 16, u"Гүйцэтгэл", header_color)
				# sheet.write(row,  13,u'Шалгарсан', header_color)
				sheet.merge_range(row, 17, row, 21, u"Хугацааны мэдээлэл", header_color)
				sheet.merge_range(row, 22, row, 27, u"Харьцуулалтын мэдээлэл", header_color)
				row+=1
				sheet.write(row,  0,u'Захиалсан салбар', header_color)
				sheet.set_column(row,0,20)
				sheet.merge_range(row-1,1,row,1,u'Захиалсан ажилтан', header_color)
				sheet.set_column(row,1,15)
				sheet.merge_range(row-1,2,row,2,u'Шаардах №', header_color)
				sheet.set_column(row,2,15)
				sheet.merge_range(row-1,3,row,3,u'Барааны нэр', header_color)
				sheet.set_column(row,3,15)
				sheet.merge_range(row-1,4,row,4,u'Хувиарлалтын ангилал', header_color)
				sheet.set_column(row,4,15)
				sheet.merge_range(row-1,5,row,5,u'Барааны төрөл', header_color)
				sheet.set_column(row,5,15)
				# Батлагдсан төсөв	
				sheet.write(row,  6,u'Тоо ширхэг', header_color)
				sheet.set_column(row,6,15)
				sheet.write(row,  7,u'Нэгж үнэ', header_color)
				sheet.set_column(row,7,15)
				sheet.write(row,  8,u'Нийт үнэ ', header_color)
				sheet.set_column(row,8,15)
				#Гүйцэтгэл
				sheet.write(row,  9,u'Хүлээлгэн өгсөн барааны нэр', header_color)
				sheet.set_column(row,9,15)
				sheet.write(row,  10,u'Тоо ширхэг', header_color)
				sheet.set_column(row,10,15)
				sheet.write(row,  11,u'Нэгж үнэ', header_color)
				sheet.set_column(row,11,15)
				sheet.write(row,  12,u'Нийт үнэ ', header_color)
				sheet.set_column(row,12,15)
				sheet.write(row,  13,u'Шимтгэл хувь', header_color)
				sheet.set_column(row,13,15)
				sheet.write(row,  14,u'Шимтгэл дүн', header_color)
				sheet.set_column(row,14,15)
				sheet.write(row,  15,u'Хүлээлгэн өгсөн барааны төрөл', header_color)
				sheet.set_column(row,15,15)
				#Шалгарсан
				sheet.write(row,  16,u'Харилцагч', header_color)
				sheet.set_column(row,16,15)
				#Хугацааны мэдээлэл
				sheet.write(row,  17,u'Захиалга биелүүлвэл зохих хугацаа', header_color)
				sheet.set_column(row,17,15)
				sheet.write(row,  18,u'Захиалга хүлээж авсан огноо', header_color)
				sheet.set_column(row,18,15)
				sheet.write(row,  19,u'Нягтланд илгээгдсэн огноо', header_color)
				sheet.set_column(row,19,15)
				sheet.write(row,  20,u'Урьтамж', header_color)
				sheet.set_column(row,20,15)
				sheet.write(row,  21,u'Хэтэрсэн хоног', header_color)
				sheet.set_column(row,21,15)
				#Харьцуулалтын мэдээлэл
				sheet.write(row,  22,u'Харьцуулалт хийгдэх эсэх', header_color)
				sheet.set_column(row,22,15)
				sheet.write(row,  23,u'Харьцуулалтын төлөв', header_color)
				sheet.set_column(row,23,15)
				sheet.write(row,  24,u'Харьцуулалт биелүүлвэл зохих хоног', header_color)
				sheet.set_column(row,24,18)
				sheet.write(row,  25,u'Харьцуулалт дууссан огноо', header_color)
				sheet.set_column(row,25,15)
				sheet.write(row,  26,u'Харьцуулалтын ажилтан', header_color)
				sheet.set_column(row,26,15)
				# sheet.write(row,  11,u'Захиалга хүлээлгэн өгсөн огноо', header_color)
				# sheet.set_column(row,11,15)
				sheet.write(row,  27,u'Хэтэрсэн хоног', header_color)
				sheet.set_column(row,27,15)
				# sheet.write(row,  12,u'Үнэлгээ', header_color)
				# sheet.set_column(row,12,15)
				# sheet.write(row,  13,u'Урьтамж', header_color)
				# sheet.set_column(row,13,15)



				row+=1
				rate = 0
				count = 0
				count_product=0
				requisition = []
				line_count =0
				for sector in sorted(buyer['sector'].values(), key=itemgetter('sector')):
					# sheet.write(row,  0,sector['sector'], cell_float_format_left)
					row2=row
					for emp in sorted(sector['employee'].values(), key=itemgetter('employee')):
						row1=row
						
						for req in sorted(emp['requisition'].values(), key=itemgetter('requisition')):
							row3=row
							# sheet.write(row,  2,req['requisition'], cell_float_format_left)
							for pro in sorted(req['product'].values(), key=itemgetter('product')):
								
								sheet.write(row, 3,pro['product'], cell_float_format_left)
								sheet.write(row, 4,pro['assign_cat'], cell_float_format_left)
								product_type = ''
								if pro['is_purchase_standard']:
									product_type += 'Стандарчилагдсан,'
								if pro['is_normalized']:
									product_type += 'Нормчилогдсон,'
								if pro['is_new_set']:
									product_type += 'Шинэ дэлгүрийн багц бараа,'
								sheet.write(row, 5,product_type, cell_float_format_left)

								sheet.write(row, 6,pro['product_qty'], cell_format_center)
								sheet.write(row, 7,pro['product_price'], cell_format_center)
								sheet.write(row, 8,pro['amount'], cell_format_center)

								sheet.write(row, 9,pro['deliver_product'], cell_format_center)
								sheet.write(row, 10,pro['supplied_product_quantity'], cell_format_center)
								sheet.write(row, 11,pro['supplied_product_price'], cell_format_center)
								sheet.write(row, 12,pro['supplied_amount'], cell_format_center)
								sheet.write(row, 13,'', cell_format_center)
								sheet.write(row, 14,'', cell_format_center)
								product_type = ''
								if pro['delivery_pro_standard']:
									product_type += 'Стандарчилагдсан,'
								if pro['delivery_pro_normalized']:
									product_type += 'Нормчилогдсон,'
								if pro['delivery_pro_new_set']:
									product_type += 'Шинэ дэлгүрийн багц бараа,'
								sheet.write(row, 15,product_type, cell_format_center)
								sheet.write(row, 16,pro['partner_name'], cell_format_center)

								sheet.write(row, 17,pro['ordering_date'], cell_format_center)
								sheet.write(row, 18,pro['received_date'], cell_format_center)
								sheet.write(row, 19,pro['date'], cell_format_center)
								sheet.write(row, 20,pro['priority'], cell_format_center)
								sheet.write(row, 21,pro['exceed_day'], cell_format_center)
								sheet.write(row, 22,pro['comparison_id'], cell_format_center)
								sheet.write(row, 23,pro['comparison_state'], cell_format_center)
								sheet.write(row, 24,pro['comparison_date'], cell_format_center)
								sheet.write(row, 25,pro['comparison_date_end'], cell_format_center)
								sheet.write(row, 26,pro['comparison_user_name'], cell_format_center)
								sheet.write(row, 27,pro['excess_day'], cell_format_center)

								# sheet.write(row, 10,pro['create_date'], cell_float_format_left)
								# sheet.write(row, 11,pro['used_days'], cell_float_format_left)
								# sheet.write(row, 12,pro['rate'], cell_float_format_left)
								row+=1
								line_count+=1
								count_product+=1
								if pro['rate']:
									rate =rate+ pro['rate']
									count+=1

							if req['requisition'] not in requisition:
								requisition.append(req['requisition'])
						# row+=1
							if row!=row3+1:
								sheet.merge_range(row3,2, row-1,  2,req['requisition'], cell_float_format_left)	
							else:
								sheet.write(row3,  2,req['requisition'], cell_float_format_left)
						if row!=row1+1:
							sheet.merge_range(row1,1, row-1,  1,emp['employee'], cell_float_format_left)	
						else:
							sheet.write(row1,  1,emp['employee'], cell_float_format_left)
						line_count=0
					if row!=row2+1:
							sheet.merge_range(row2,0, row-1,  0,sector['sector'], cell_float_format_left)	
					else:
							sheet.write(row1,  0,sector['sector'], cell_float_format_left)
					# sheet.merge_range(row1,0, row1+line_count,  0,sector['sector'], cell_float_format_left)	
					
				if count==0:
					count=1
				sheet.write(row, 2,len(requisition), cell_float_format_left)	
				sheet.write(row, 3,count_product, cell_float_format_left)		
				# sheet.write(row, 12,round(rate/count,2), cell_float_format_left)

				row += 1

				
		workbook.close()

		out = base64.encodestring(output.getvalue())
		file_name = u'Худалдан авалт гүйцэтгэлийн тайлан'
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