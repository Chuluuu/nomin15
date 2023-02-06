# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime,timedelta
from operator import itemgetter
import xlsxwriter
from io import BytesIO
import base64

class PurchaseComparisonParticipationReport(models.TransientModel):
    ''' Худалдан авалтын үнийн харьцуулалтанд оролцсон түүх '''
    _name = 'purchase.comparison.participation.report'

    date_from = fields.Date(string=u'Эхлэх огноо', required=True)
    date_to = fields.Date(string=u'Дуусах огноо', required=True, default=fields.Date.context_today)
    partner_ids = fields.Many2many('res.partner',string=u'Нийлүүлэгч')
    product_ids = fields.Many2many('product.product',string=u'Бараа' )

    
    def export(self):
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
        
        where = " WHERE A.date BETWEEN '%s' AND '%s'"%(self.date_from, self.date_to)

        if self.product_ids:
            if len(self.product_ids) > 1:
                where = where + " AND D.id in %s"%str(tuple(self.product_ids.ids))
            else:
                where = where + " AND D.id = %s"%(self.product_ids.id)

        if self.partner_ids:
            if len(self.partner_ids) > 1:
                where = where + " AND F.id in %s"%str(tuple(self.partner_ids.ids))
            else:
                where = where + " AND F.id = %s"%(self.partner_ids.id)

        query = "select A.name as comparison_name, A.id as comparison_id, B.name as order_name, A.date as date, I.name_related as created_user, F.id as partner_id, F.name as partner_name, \
                D.name_template as product_name, C.price_unit as price_unit, C.product_qty as product_qty, D.id as product_id, (C.price_unit * C.product_qty) as subtotal, \
                (CASE WHEN A.state in ('confirmed', 'purchase') THEN (CASE WHEN E.is_winner THEN 'Шалгарсан' ELSE 'Шалгараагүй' END) ELSE 'Харьцуулалт хийгдэж буй' END) as is_winner \
                from purchase_comparison A \
                inner join purchase_order B ON B.comparison_id = A.id \
                inner join purchase_order_line C ON C.order_id = B.id \
                inner join product_product D ON C.product_id = D.id \
                inner join purchase_partner_comparison E ON E.comparison_id = A.id AND B.id = E.order_id \
                inner join res_partner F ON F.id = B.partner_id \
                inner join res_users G ON G.id = A.user_id \
                inner join resource_resource H ON H.user_id = G.id \
                inner join hr_employee I ON I.resource_id = H.id \
        " + where

        self.env.cr.execute(query)
        fetchall =  self.env.cr.dictfetchall()

        file_name = u'Худалдан авалтын үнийн харьцуулалтанд оролцсон түүх.xlsx'

        if fetchall:
            products = {}
            for fetch in fetchall:
                group = fetch['product_id']
                if group not in products:
                    products[group] = {
                        'product_name': u'Тодорхойгүй',
                        'comparisons': {},
                    }
                
                products[group]['product_id']   = group
                products[group]['product_name'] = fetch['product_name']

                group1 = fetch['comparison_id']
                if group1 not in products[group]['comparisons']:
                    products[group]['comparisons'][group1] = {
                        'comparison_name': u'Тодорхойгүй',
                        'created_user': u'Тодоройгүй',
                        'date': u'Тодорхойгүй',
                        'partners': {},
                    }

                products[group]['comparisons'][group1]['comparison_id']     = group1
                products[group]['comparisons'][group1]['date']              = fetch['date']
                products[group]['comparisons'][group1]['comparison_name']   = fetch['comparison_name']
                products[group]['comparisons'][group1]['created_user']      = fetch['created_user']

                group2 = fetch['partner_id']
                if group2 not in products[group]['comparisons'][group1]['partners']:
                    products[group]['comparisons'][group1]['partners'][group2] = {
                        'order_name': u'Тодорхойгүй',
                        'partner_name': u'Тодоройгүй',
                        'price_unit': u'Тодоройгүй',
                        'product_qty': u'Тодоройгүй',
                        'is_winner': u'Тодорхойгүй',
                        'subtotal': u'Тодоройгүй',
                    }

                products[group]['comparisons'][group1]['partners'][group2]['partner_id']    = group2
                products[group]['comparisons'][group1]['partners'][group2]['partner_name']  = fetch['partner_name']
                products[group]['comparisons'][group1]['partners'][group2]['price_unit']    = fetch['price_unit']
                products[group]['comparisons'][group1]['partners'][group2]['product_qty']   = fetch['product_qty']
                products[group]['comparisons'][group1]['partners'][group2]['subtotal']      = fetch['subtotal']
                products[group]['comparisons'][group1]['partners'][group2]['is_winner']      = fetch['is_winner']
                products[group]['comparisons'][group1]['partners'][group2]['order_name']      = fetch['order_name']

            worksheet = workbook.add_worksheet(u'Үнийн харьцуулалт')
            worksheet.set_column('A:E',15)
            worksheet.set_column('F:F',30)
            worksheet.set_column('G:I',10)
            date_from = datetime.strptime(self.date_from, "%Y-%m-%d").strftime('%Y.%m.%d')
            date_to = datetime.strptime(self.date_to, "%Y-%m-%d").strftime('%Y.%m.%d')

            worksheet.merge_range(1, 0, 1, 9, u'Худалдан авалтын үнийн харьцуулалтанд оролцсон түүх', header)
            worksheet.merge_range(3, 6, 3, 9, u'Огноо: ' + date_from + '-' + date_to, title)
            
            row = 5

            for product in sorted(products.values(),key=itemgetter('product_name')):
                worksheet.merge_range(row, 0, row, 2,product['product_name'], partner_name)
                row += 1

                worksheet.write(row, 0, 'Харьцуулалтын №',table_header)
                worksheet.write(row, 1, 'Үнийн саналын №',table_header)
                worksheet.write(row, 2, 'Харьцуулалтын огноо',table_header)
                worksheet.write(row, 3, 'Үүсгэсэн хэрэглэгч',table_header)
                worksheet.write(row, 4, 'Нийлүүлэгч',table_header)
                worksheet.write(row, 5, 'Шалгарсан эсэх',table_header)
                worksheet.write(row, 6, 'Нэгжийн үнэ',table_header)
                worksheet.write(row, 7, 'Тоо хэмжээ',table_header)
                worksheet.write(row, 8, 'Нийт дүн',table_header)
                row += 1

                for comparison in sorted(product['comparisons'].values(),key=itemgetter('comparison_name')):
                    rowx = row

                    for partner in sorted(comparison['partners'].values(),key=itemgetter('partner_name')):
                        worksheet.write(row, 1, partner['order_name'],cell_format_left)
                        worksheet.write(row, 4, partner['partner_name'],cell_format_left)
                        worksheet.write(row, 5, partner['is_winner'],cell_format_center)
                        worksheet.write(row, 6, partner['price_unit'],cell_format_right_float)
                        worksheet.write(row, 7, partner['product_qty'],cell_format_center)
                        worksheet.write(row, 8, partner['subtotal'],cell_format_right_float)
                        row += 1

                    if row - 1 == rowx:
                        worksheet.write(rowx, 0, comparison['comparison_name'],cell_format_left)
                        worksheet.write(rowx, 2, comparison['date'],cell_format_center)
                        worksheet.write(rowx, 3, comparison['created_user'],cell_format_center)
                    else:
                        worksheet.merge_range(rowx, 0, row-1, 0, comparison['comparison_name'],cell_format_left)
                        worksheet.merge_range(rowx, 2, row-1, 2, comparison['date'],cell_format_center)
                        worksheet.merge_range(rowx, 3, row-1, 3, comparison['created_user'],cell_format_center)

                row += 3

        
        workbook.close()
        out = base64.encodestring(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

        return {
            'name': 'Export Result',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'report.excel.output',
            'res_id': excel_id.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'nodestroy': True,
        }
