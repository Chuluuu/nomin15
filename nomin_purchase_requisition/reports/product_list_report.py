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
from openerp.addons.l10n_mn_report_base.report_helper import verbose_numeric, comma_me, convert_curr
from openerp import api, fields, models, _
from datetime import datetime,date
from dateutil import parser
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import xlsxwriter
from operator import itemgetter
from io import BytesIO
import base64
from xlwt import *


class ProductRegistrationReport(models.TransientModel):
    _name = 'product.registration.report'

    start_date = fields.Date(string='date start')
    end_date = fields.Date(string='date end')
    state= fields.Selection([('done','Done',),('assigned','Assigned')],string="State")
    categ_ids = fields.Many2many(comodel_name = 'assign.category',string=u'Assign categorys')
    # department_ids = fields.Many2many(comodel_name = 'hr.department',string=u'Departments')
    # state= fields.Selection([('done','Done',),('assigned','Assigned')],string="State")

    @api.multi
    def export_report(self,report_code,context=None):
        if context is None:
            context = {}
        datas={}
        datas['form'] = self.read(['department_ids','job_ids'])[0] 
        data = datas['form']
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        # department = self.department_ids.name
        # header = workbook.add_format({'border':1,'align':'justify','valign':'vjustify','text_wrap':'on','pattern':0})

        title = workbook.add_format({
        'border': 1,
        'bold': 1,
        'bg_color':'fce77a',
        'align': 'wrap on',
        'valign': 'vcenter',
        'text_wrap': 'on',
        'font_size':10,
        'font_name': 'Arial',
        })

        title1 = workbook.add_format({
        'border': 1,
        'bold': 1,
        'bg_color':'f9b165',
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 'on',
        'font_size':10,
        'font_name': 'Arial',
        })


        header = workbook.add_format({
        'border': 1,
        'bold': 1,
        'bg_color':'#f8f0f0',
        'align': 'wrap on',
        'valign': 'vcenter',
        'text_wrap': 'on',
        'font_size':10,
        'font_name': 'Arial',
        })

        header1 = workbook.add_format({
        'border': 0,
        'bold': 1,
        'align': 'wrap on',
        'valign': 'vcenter',
        'text_wrap': 'on',
        'font_size':10,
        # 'bg_color':'#f2f2f2',
        'font_name': 'Arial',
        })
        style1 = workbook.add_format({
        'border': 1,
        'bold': 1,
        'align': 'wrap on',
        'valign': 'vcenter',
        'text_wrap': 'on',
        'font_size':10,
        'bg_color':'#c9c8c8',
        'font_name': 'Arial',
        })
        style2 = workbook.add_format({
        'border': 1,
        'bold': 1,
        'align': 'wrap on',
        'valign': 'vcenter',
        'text_wrap': 'on',
        'font_size':10,
        'bg_color':'#f6eaac',
        'font_name': 'Arial',
        })

        group = "group by assign_name,A.product_type,req_state,D.id,D.name,A.state,C.name,A.product_id,A.product_desc,A.requisition_id,A.date_end,E.ordering_date,H.name,J.name,H.id,E.name,K.name_template,A.date_end,E.ordering_date "
        where = ""

        if self.categ_ids:
            where = "and C.id in %s"%(str(tuple(self.categ_ids.ids)))

        select_state = ''
        if self.state == 'done':
            select_state = 'done','th'
        if self.state == 'assigned':
            select_state = 'assigned','th'
        if self.state == False:
            select_state = 'done','assigned'

        query = "select C.name as assign_name,A.product_type,E.state as req_state,A.date_end,E.ordering_date,K.name_template,E.name as requisition_code,H.id as team_id,H.name as team_name,J.name,DATE_PART('day', A.date_end::timestamp- E.ordering_date::timestamp) as daydiff,D.id ,D.name,A.state,count(A.id),sum(A.product_qty) as qty_sum,sum(A.product_qty * A.product_price) as amount, \
        (select count(id) from purchase_requisition_line where state = 'done') as done_state, \
        (select count(id) from purchase_requisition_line where state = 'assigned') as assigned_state, \
        C.name  as assign from purchase_requisition_line A \
                    inner join res_users B ON B.id=A.user_id \
                    left join hr_department hd on A.department_id = hd.id \
                    left join assign_category C ON C.id=A.assign_cat \
                    left join purchase_category_config J ON J.user_id=B.id \
                    left join team_registration H ON H.id=J.team_id \
                    left join purchase_requisition E on A.requisition_id = E.id \
                    left join product_product K on A.product_id = K.id\
                    inner join res_partner D ON D.id=B.partner_id \
                    where A.state in %s and A.create_date >= '%s' and A.create_date <= '%s' \
                    " %(select_state,self.start_date,self.end_date)  + where + group 
        category_query = "select D.name,B.id,C.purchase_category_config_id,C.assign_category_id from purchase_category_config A \
                    inner join res_users B ON B.id=A.user_id \
                    left join assign_category_purchase_category_config_rel C on C.purchase_category_config_id = A.id  \
                    left join purchase_category_config J ON J.user_id=B.id \
                    inner join res_partner D ON D.id=B.partner_id " 



        sheet = workbook.add_worksheet()
        sheet.portrait=True
        sheet.merge_range(0,3,0,6,u'Барааны бүлэг гүйцэтгэлийн тайлан', title1)
        sheet.merge_range(3,0,3,1,u"Огноо :%s - %s"%(self.start_date,self.end_date), header1)
        
        sheet.merge_range(4,0,6,0,u'Ангилал', title1)
        sheet.set_column(0,0,20)

        sheet.merge_range(4,1,6,1,u'Төрөл', title1)
        sheet.set_column(1,1,50)

        sheet.merge_range(4,2,6,2,u'Төлөв', title1)
        sheet.set_column(2,2,10)

        sheet.merge_range(4,3,6,3,u'Хэмжээ', title1)
        sheet.set_column(3,3,10)

        sheet.merge_range(4,4,6,4,u'Үнийн дүн', title1)
        sheet.set_column(4,4,10)

        sheet.merge_range(4,5,6,5,u'Хэвийн', title1)
        sheet.set_column(5,5,10)

        sheet.merge_range(4,6,6,6,u'Хугацаа хэтэрсэн', title1)
        sheet.set_column(6,6,10)

        sheet.merge_range(4,7,6,7,u'Нийт', title1)
        sheet.set_column(7,7,10)

        sheet.merge_range(4,8,6,8,u'Биелсэн дундаж хоног', title1)
        sheet.set_column(8,8,10)

        row = 7
        self.env.cr.execute(query)
        dictfetchall = self.env.cr.dictfetchall()
        self.env.cr.execute(category_query)
        categ_dictfetchall = self.env.cr.dictfetchall()

        category_fetchedAll = {}
        for dic in categ_dictfetchall:
            user = dic['name']
            if dic['name'] not in category_fetchedAll:
                category_fetchedAll[user]= {
                    'name':u'',
                    'count':0,
                }
            category_fetchedAll[user]['name']=dic['name']
            category_fetchedAll[user]['count']+=1

        fetchedAll = {}
        for dic in dictfetchall:
            parent = dic['assign_name']
            if dic['assign_name'] not in fetchedAll:
                fetchedAll[parent]= {
                    'assign_name':u'',
                    'products':{},
                }
            fetchedAll[parent]['assign_name'] = dic['assign_name']

            product = dic['name_template']
            if product not in fetchedAll[parent]['products']:
                fetchedAll[parent]['products'][product]={
                    'name_template':u'',
                    'states':{},
                }

            fetchedAll[parent]['products'][product]['name_template']=dic['name_template']

            state = dic['state']
            if state not in fetchedAll[parent]['products'][product]['states']:
                fetchedAll[parent]['products'][product]['states'][state]={
                    'qty':0,
                    'amount':0, 
                    'done_normal_requisition_line':0,
                    'done_overdue_requisition_line':0,
                    'normal_average':0,  
                    'state':u'',                    

                }
            fetchedAll[parent]['products'][product]['states'][state]['state']= state
            fetchedAll[parent]['products'][product]['states'][state]['qty']+=dic['qty_sum']
            fetchedAll[parent]['products'][product]['states'][state]['amount']+=dic['amount']

            if dic['state'] == 'assigned':
                if (datetime.strptime(dic['ordering_date'], "%Y-%m-%d")-datetime.today()).days>0:
                    fetchedAll[parent]['products'][product]['states'][state]['done_normal_requisition_line']+=1
                    fetchedAll[parent]['products'][product]['states'][state]['normal_average']+=(datetime.strptime(dic['ordering_date'], "%Y-%m-%d")-datetime.today()).days
                else:
                    fetchedAll[parent]['products'][product]['states'][state]['done_overdue_requisition_line'] += 1
                    fetchedAll[parent]['products'][product]['states'][state]['normal_average']+=(datetime.strptime(dic['ordering_date'], "%Y-%m-%d")-datetime.today()).days
            else:
                if dic['date_end'] and dic['ordering_date']:
                    if (datetime.strptime(dic['ordering_date'], "%Y-%m-%d")-datetime.strptime(dic['date_end'], "%Y-%m-%d")).days>0:
                        fetchedAll[parent]['products'][product]['states'][state]['done_normal_requisition_line']+=1
                        fetchedAll[parent]['products'][product]['states'][state]['normal_average']+=(datetime.strptime(dic['ordering_date'], "%Y-%m-%d")-datetime.today()).days
                    else:
                        fetchedAll[parent]['products'][product]['states'][state]['done_overdue_requisition_line'] += 1
                        fetchedAll[parent]['products'][product]['states'][state]['normal_average']+=(datetime.strptime(dic['ordering_date'], "%Y-%m-%d")-datetime.today()).days


        for parent in sorted(fetchedAll.values(), key=itemgetter('assign_name')):
            row_count=row
            sheet.write(row,0,parent['assign_name'],header)
            for product in sorted(parent['products'].values(), key=itemgetter('name_template')):
                row_dep = row
                sheet.write(row,1,product['name_template'],header)
                for state in sorted(product['states'].values(), key=itemgetter('state')):
                    if state['state'] == 'done':
                        st = u'Дууссан'
                    elif state['state'] == 'assigned':
                        st = u'Хувиарласан'
                    sheet.write(row,1,product['name_template'],header)
                    sheet.write(row,2,st,header)
                    sheet.write(row,3,state['qty'],header)
                    sheet.write(row,4,state['amount'],header)
                    
                    sheet.write(row,5,state['done_normal_requisition_line'],header)
                    sheet.write(row,6,state['done_overdue_requisition_line'],header)
                    sheet.write(row,7,state['done_overdue_requisition_line']+state['done_normal_requisition_line'],header)
                    if (state['done_overdue_requisition_line']+state['done_normal_requisition_line']) > 0:
                        sheet.write(row,8,state['normal_average']/(state['done_overdue_requisition_line']+state['done_normal_requisition_line']),header)
                    row += 1
            if row-1 == row_count:
                sheet.write(row_count,0,parent['assign_name'],header)
            else:
                sheet.merge_range(row_count,0, row-1, 0,parent['assign_name'], header)



        workbook.close()
        out = base64.encodestring(output.getvalue())
        file_name = u'Барааны бүлэг гүйцэтгэлийн тайлан'
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