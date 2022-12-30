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


class WorkImplementationReport(models.TransientModel):
    _name = 'work.implementation.report'

    start_date = fields.Date(string='date start')
    end_date = fields.Date(string='date end')
    department_ids = fields.Many2many(comodel_name = 'hr.department',string=u'Departments')
    state= fields.Selection([('done','Done',),('assigned','Assigned')],string="State")

    @api.multi
    def export_report(self,report_code,context=None):
        if context is None:
            context = {}
        datas={}
        datas['form'] = self.read(['department_ids','job_ids'])[0] 
        data = datas['form']
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

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

        group = "group by buyer_name,assign_name,A.product_type,parent_department_name,td.parent_id,hd.id,req_state,department_name,D.id,D.name,A.state,C.name,A.product_id,A.product_desc,A.requisition_id,A.date_end,E.ordering_date,H.name,J.name,H.id,E.name,K.name_template,A.date_end,E.ordering_date "
        order = "order by D.name;"
        where = ""
            
        if self.department_ids:
            self.env.cr.execute('create table temp_department(parent_id int,department_id int) ')
            parent_ids = []
            for line in self.department_ids:
                parent_id = self.env['hr.department'].search([('parent_id','=',line.id)])
                parent_ids.append(line.id)
                self.env.cr.execute('insert into temp_department(parent_id,department_id) values (%s,%s)'%(line.id,line.id))
                if parent_id:
                    for parent_department in parent_id:
                        self.env.cr.execute('insert into temp_department(parent_id,department_id) values (%s,%s)'%(line.id,parent_department.id))
                        parent_ids.append(parent_department.id)
                        parent_parent_id = self.env['hr.department'].search([('parent_id','=',parent_department.id)])
                        if parent_parent_id:
                            for parent_parent_department in parent_parent_id:
                                self.env.cr.execute('insert into temp_department(parent_id,department_id) values (%s,%s)'%(line.id,parent_parent_department.id))
                                parent_ids.append(parent_parent_department.id)
                                parent_parent_parent_id = self.env['hr.department'].search([('parent_id','=',parent_parent_department.id)])
                                if parent_parent_parent_id:
                                    for parent_parent_parent_department in parent_parent_parent_id:
                                        self.env.cr.execute('insert into temp_department(parent_id,department_id) values (%s,%s)'%(line.id,parent_parent_parent_department.id))
                                        parent_ids.append(parent_parent_parent_department.id)
                else:
                    parent_ids.append(line.id)
                    self.env.cr.execute('insert into temp_department(parent_id,department_id) values (%s,%s)'%(line.id,line.id))

            where=where+"and A.department_id in %s"%(str(tuple(parent_ids)))


        select_state = ''
        if self.state == 'done':
            select_state = 'done','th'
        if self.state == 'assigned':
            select_state = 'assigned','th'
        if self.state == False:
            select_state = 'done','assigned'

        query = "select P.name as buyer_name,C.name as assign_name,A.product_type,hd1.name as parent_department_name,td.parent_id,hd.id as department_id,hd.name as department_name,E.state as req_state,A.date_end,E.ordering_date,K.name_template,E.name as requisition_code,H.id as team_id,H.name as team_name,J.name,DATE_PART('day', A.date_end::timestamp- E.ordering_date::timestamp) as daydiff,D.id ,D.name,A.state,count(A.id),sum(A.product_qty) as qty_sum,sum(A.product_qty * A.product_price) as amount, \
        (select count(id) from purchase_requisition_line where state = 'done') as done_state, \
        (select count(id) from purchase_requisition_line where state = 'assigned') as assigned_state, \
        C.name  as assign from purchase_requisition_line A \
                    inner join res_users L ON L.id=A.buyer \
                    inner join res_users B ON B.id=A.user_id \
                    left join hr_department hd on A.department_id = hd.id \
                    left join assign_category C ON C.id=A.assign_cat \
                    left join purchase_category_config J ON J.user_id=L.id \
                    left join team_registration H ON H.id=J.team_id \
                    left join purchase_requisition E on A.requisition_id = E.id \
                    left join product_product K on A.product_id = K.id\
                    left join temp_department td on td.department_id=hd.id\
                    left join hr_department hd1 on td.parent_id = hd1.id\
                    inner join res_partner D ON D.id=B.partner_id \
                    inner join res_partner P ON P.id=L.partner_id \
                    where A.state in %s and A.create_date >= '%s' and A.create_date <= '%s' \
                    " %(select_state,self.start_date,self.end_date) + where + group + order
        category_query = "select D.name,B.id,C.purchase_category_config_id,C.assign_category_id from purchase_category_config A \
                    inner join res_users B ON B.id=A.user_id \
                    left join assign_category_purchase_category_config_rel C on C.purchase_category_config_id = A.id  \
                    left join purchase_category_config J ON J.user_id=B.id \
                    inner join res_partner D ON D.id=B.partner_id " 

        sheet = workbook.add_worksheet()
        sheet.portrait=True
        sheet.merge_range(0,3,0,6,u'Худалдан авалтын дэлгэрэнгүй тайлан', title1)
        sheet.merge_range(2,0,2,1,u"Огноо :%s - %s"%(self.start_date,self.end_date), header1)
        
        sheet.merge_range(3,0,3,2,u'Захиалагчийн мэдээлэл', title1)
        sheet.merge_range(4,0,6,0,u'Салбар', title1)
        sheet.set_column(0,0,20)

        sheet.merge_range(4,1,6,1,u'Хэлтэс', title1)
        sheet.set_column(1,1,20)

        sheet.merge_range(4,2,6,2,u'Захиалагч', title1)
        sheet.set_column(2,2,12)

        sheet.merge_range(3,3,3,6,u'Захиалгын мэдээлэл', title1)
        sheet.merge_range(4,3,6,3,u'Шаардахын дугаар', title1)
        sheet.set_column(3,3,7)

        sheet.merge_range(4,4,6,4,u'Төлөв', title1)
        sheet.set_column(4,4,12)

        sheet.merge_range(4,5,6,5,u'Нөхцөл', title1)
        sheet.set_column(5,5,12)

        sheet.merge_range(4,6,6,6,u'Биелсэн хоног', title1)
        sheet.set_column(6,6,7)

        sheet.merge_range(3,7,3,10,u'Бараа материалын мэдээлэл', title1)
        sheet.merge_range(4,7,6,7,u'Ангилал', title1)
        sheet.set_column(7,7,25)

        sheet.merge_range(4,8,6,8,u'Төрөл', title1)
        sheet.set_column(8,8,25)

        sheet.merge_range(4,9,6,9,u'Ширхэг', title1)
        sheet.set_column(9,9,10)

        sheet.merge_range(4,10,6,10,u'Үнийн дүн', title1)
        sheet.set_column(10,10,10)

        sheet.merge_range(3,11,3,12,u'Гүйцэтгэгчийн мэдээлэл', title1)
        sheet.merge_range(4,11,6,11,u'Баг', title1)
        sheet.set_column(11,11,10)

        sheet.merge_range(4,12,6,12,u'Ажилтан', title1)
        sheet.set_column(12,12,10)


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
            parent = dic['parent_id']
            if dic['parent_id'] not in fetchedAll:
                fetchedAll[parent]= {
                    'parent_id':u'',
                    'parent_department_name':u'',
                    'departments':{},
                }
            fetchedAll[parent]['parent_department_name'] = dic['parent_department_name']

            department = dic['department_id']
            if department not in fetchedAll[parent]['departments']:
                fetchedAll[parent]['departments'][department]={
                    'name':u'',                    
                    'partners':{},
                }

            fetchedAll[parent]['departments'][department]['name']=dic['department_name']

            partner = dic['id']
            if partner not in fetchedAll[parent]['departments'][department]['partners']:
                fetchedAll[parent]['departments'][department]['partners'][partner]={
                    'name':u'',                    
                    'states':{},
                    'req_states':{},

                }

            fetchedAll[parent]['departments'][department]['partners'][partner]['name']= dic['name']

            state = dic['name_template']
            if state not in fetchedAll[parent]['departments'][department]['partners'][partner]['states']:
                fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]={
                    'state':u'',
                    'count':0,
                    'name':0,
                    'qty':0,
                    'amount':0,
                    'requisition_code':u'',
                    'product_type':u'',
                    'assign_name':u'',
                    'name_template':u'',
                    'team_name':u'',
                    'buyer_name':u'',
                    'day':0,
                    'done_normal_requisition_line':u'',
                    'done_overdue_requisition_line':u'',
                    'requisitions':{},
                    'assigned_cats':{},
                    'products':{},
                }
            fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['name']= dic['name']
            fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['state']= dic['state']
            fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['count'] += dic['count']
            fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['qty']+=dic['qty_sum']
            fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['amount']+=dic['amount']
            fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['requisition_code']=dic['requisition_code']
            fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['product_type']=dic['product_type']
            fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['assign_name']=dic['assign_name']
            fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['name_template']=dic['name_template']
            fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['team_name']=dic['team_name']
            fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['buyer_name']=dic['buyer_name']

            if dic['state'] == 'done':
                if dic['daydiff']<0:
                    fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['done_normal_requisition_line']=u'Энгийн'
                    fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['day']=dic['daydiff']
                else:
                    fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['done_normal_requisition_line']=u'Хугацаа хэтэрсэн'
                    fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['day']=dic['daydiff']
            else:
                if parser.parse(dic['ordering_date']).day-date.today().day<0:
                    fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['done_normal_requisition_line']=u'Энгийн'
                    fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['day']=dic['daydiff']
                else:
                    fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['done_normal_requisition_line']=u'Хугацаа хэтэрсэн'
                    fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['day']=dic['daydiff']

            assign = dic['assign']
            if assign not in fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['assigned_cats']:
                fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['assigned_cats'][assign] = {
                                'name':u'',
                            }
            fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['assigned_cats'][assign]['name']= assign


            product = dic['name_template']
            if product not in fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['products']:
                fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['products'][product] = {
                    'name':u'',
                }
            fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['products'][product]['name']=product


            requisition = dic['requisition_code']
            if requisition not in fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['requisitions']:
                fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['requisitions'][requisition] = {
                    'name':u'',
                    'normal':u'',                    
                    'overdue':u'',                    
                }
            
            fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['requisitions'][requisition]['name']=requisition


            req_state = dic['req_state']
            if req_state not in fetchedAll[parent]['departments'][department]['partners'][partner]['req_states']:
                fetchedAll[parent]['departments'][department]['partners'][partner]['req_states'][req_state]={
                'name':u'',
                'normal':0,
                'overdue':0

                }
            fetchedAll[parent]['departments'][department]['partners'][partner]['req_states'][req_state]['name'] = req_state
            if dic['ordering_date']:
                if dic['daydiff']<=0:
                    fetchedAll[parent]['departments'][department]['partners'][partner]['req_states'][req_state]['normal']+=1
                else:

                    fetchedAll[parent]['departments'][department]['partners'][partner]['req_states'][req_state]['overdue']+=1

        for parent in sorted(fetchedAll.values(), key=itemgetter('parent_department_name')):
            sheet.write(row,0,parent['parent_department_name'],header)
            for department in sorted(parent['departments'].values(), key=itemgetter('name')):
                sheet.write(row,1,department['name'],header)
                for partner in sorted(department['partners'].values(), key=itemgetter('name')):
                    sheet.write(row,2,partner['name'],header)
                    for state in sorted(partner['states'].values(), key=itemgetter('state')):
                        if state['state'] == 'done':
                            st = u'Дууссан'
                        elif state['state'] == 'assigned':
                            st = u'Хувиарласан'
                        sheet.write(row,0,parent['parent_department_name'],header)
                        sheet.write(row,1,department['name'],header)
                        sheet.write(row,2,partner['name'],header)
                        sheet.write(row,3,state['requisition_code'],header)
                        sheet.write(row,4,st,header)
                        sheet.write(row,5,partner['states'][state['name_template']]['done_normal_requisition_line'],header)
                        sheet.write(row,6,partner['states'][state['name_template']]['day'],header)
                        sheet.write(row,7,state['assign_name'],header)
                        sheet.write(row,8,state['name_template'],header)
                        sheet.write(row,9,state['qty'],header)
                        sheet.write(row,10,state['amount'],header)
                        sheet.write(row,11,state['team_name'],header)
                        sheet.write(row,12,state['buyer_name'],header)
                        row+=1


        workbook.close()
        self.env.cr.execute('drop table temp_department;')
        out = base64.encodestring(output.getvalue())
        file_name = u'Худалдан авалтын дэлгэрэнгүй тайлан'
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