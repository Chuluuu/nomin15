# -*- coding: utf-8 -*-
##############################################################################
#
#    Asterisk Technologies LLC, Enterprise Management Solution    
#    Copyright (C) 2013-2013 Asterisk Technologies LLC (<http://www.erp.mn>). All Rights Reserved
#
#    Email : unuruu25@gmail.com
#    Phone : 976 + 88005462
#
##############################################################################

from datetime import datetime,timedelta,date
from dateutil import parser
from dateutil.relativedelta import relativedelta
from openerp import api, fields, models, _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _
from openerp.tools.float_utils import float_is_zero, float_compare
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError, AccessError
import time
from openerp.osv import osv
from openerp.http import request    
import xlwt
from xlwt import *
from StringIO import StringIO
from openerp.exceptions import UserError, ValidationError
from operator import itemgetter
import xlsxwriter
from io import BytesIO
import base64


class PurchaseRequisitionOrderReport(models.TransientModel):
    _name = 'purchase.requisition.order.report'
    _inherit = 'abstract.report.model'
    _description = 'Purchase requisition order report'


    start_date = fields.Date(string="Performance date start") #Эхлэх огноо
    end_date = fields.Date(string='Performance date end') #Дуусах огноо
    department_ids = fields.Many2many(comodel_name='hr.department', string='Departments')
    user_ids = fields.Many2many(comodel_name='res.users', string='User ids')
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

        group = "group by parent_department_name,td.parent_id,hd.id,req_state,department_name,D.id,D.name,A.state,C.name,A.product_id,A.product_desc,A.requisition_id,A.date_end,E.ordering_date,H.name,J.name,H.id,E.name,K.name_template,A.date_end,E.ordering_date "
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

        query = "select hd1.name as parent_department_name,td.parent_id,hd.id as department_id,hd.name as department_name,E.state as req_state,A.date_end,E.ordering_date,K.name_template,E.name as requisition_code,H.id as team_id,H.name as team_name,J.name,DATE_PART('day', A.date_end::timestamp- E.ordering_date::timestamp) as daydiff,D.id ,D.name,A.state,count(A.id),sum(A.product_qty) as qty_sum,sum(A.product_qty * A.product_price) as amount, \
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
                    left join temp_department td on td.department_id=hd.id\
                    left join hr_department hd1 on td.parent_id = hd1.id\
                    inner join res_partner D ON D.id=B.partner_id \
                    where A.state in %s and A.create_date >= '%s' and A.create_date <= '%s' \
                    " %(select_state,self.start_date,self.end_date) + where + group + order
        category_query = "select D.name,B.id,C.purchase_category_config_id,C.assign_category_id from purchase_category_config A \
                    inner join res_users B ON B.id=A.user_id \
                    left join assign_category_purchase_category_config_rel C on C.purchase_category_config_id = A.id  \
                    left join purchase_category_config J ON J.user_id=B.id \
                    inner join res_partner D ON D.id=B.partner_id " 

        sheet = workbook.add_worksheet()
        sheet.portrait=True
        sheet.merge_range(0,3,0,6,u'Худалдан авалтын гүйцэтгэлийн тайлан', title1)
        sheet.merge_range(3,0,3,1,u"Огноо :%s - %s"%(self.start_date,self.end_date), header1)
        
        sheet.merge_range(4,0,6,0,u'Салбар', title1)
        sheet.set_column(0,0,10)

        sheet.merge_range(4,1,6,1,u'Хэлтэс', title1)
        sheet.set_column(1,1,25)

        sheet.merge_range(4,2,6,2,u'Захиалагч', title1)
        sheet.set_column(2,2,12)

        sheet.merge_range(4,3,6,3,u'Төлөв', title1)
        sheet.set_column(3,3,12)

        sheet.merge_range(4,4,4,5,u'Хэвийн', title1)
        sheet.set_column(4,4,12)

        sheet.merge_range(5,4,6,4,u'Шаардах', title1)
        sheet.set_column(2,2,12)

        sheet.merge_range(5,5,6,5,u'Шаардах мөр', title1)
        sheet.set_column(2,2,12)

        sheet.merge_range(4,6,4,7,u'Хугацаа хэтэрсэн', title1)
        sheet.set_column(2,2,12)

        sheet.merge_range(5,6,6,6,u'Шаардах', title1)
        sheet.set_column(2,2,12)

        sheet.merge_range(5,7,6,7,u'Шаардах мөр', title1)
        sheet.set_column(2,2,12)



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

            state = dic['state']
            if state not in fetchedAll[parent]['departments'][department]['partners'][partner]['states']:
                fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]={
                    'state':u'',
                    'count':0,
                    'name':0,
                    'qty':0,
                    'amount':0,
                    'done_normal_requisition_line':0,
                    'done_overdue_requisition_line':0,
                    'requisitions':{},
                    'assigned_cats':{},
                    'products':{},
                }
            fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['name']= dic['name']
            fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['state']= state
            fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['count'] += dic['count']
            fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['qty']+=dic['qty_sum']
            fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['amount']+=dic['amount']

            if dic['ordering_date']:
                if dic['daydiff']<0:
                    fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['done_normal_requisition_line']+=1
                else:
                    fetchedAll[parent]['departments'][department]['partners'][partner]['states'][state]['done_overdue_requisition_line'] += 1

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
            print'_________qqq________',fetchedAll[parent]['departments'][department]['partners'][partner]['req_states']
            if dic['ordering_date']:
                if dic['daydiff']<=0:
                    fetchedAll[parent]['departments'][department]['partners'][partner]['req_states'][req_state]['normal']+=1
                else:

                    fetchedAll[parent]['departments'][department]['partners'][partner]['req_states'][req_state]['overdue']+=1

        for parent in sorted(fetchedAll.values(), key=itemgetter('parent_department_name')):
            row_count=row
            for department in sorted(parent['departments'].values(), key=itemgetter('name')):
                row_dep = row
                for partner in sorted(department['partners'].values(), key=itemgetter('name')):
                    row_partner = row
                    for state in sorted(partner['states'].values(), key=itemgetter('state')):
                        if state['state'] == 'done':
                            st = u'Дууссан'
                        elif state['state'] == 'assigned':
                            st = u'Хувиарласан'
                        sheet.write(row,3,st,header)
                        sheet.write(row,4,partner['req_states'][state['state']]['normal'],header)
                        sheet.write(row,5,partner['states'][state['state']]['done_normal_requisition_line'],header)
                        sheet.write(row,6,partner['req_states'][state['state']]['overdue'],header)
                        sheet.write(row,7,partner['states'][state['state']]['done_overdue_requisition_line'],header)
                        row+=1
                    if row-1 == row_partner:
                        sheet.write(row_partner,2,partner['name'],header)
                    else:
                        sheet.merge_range(row_partner,2, row-1, 2,partner['name'], header)
                if row-1 == row_dep:
                    sheet.write(row_dep,1,department['name'],header)
                else:
                    sheet.merge_range(row_dep,1, row-1, 1,department['name'], header)
            if row-1 == row_count:
                sheet.write(row_count,0,parent['parent_department_name'],header)
            else:
                sheet.merge_range(row_count,0, row-1, 0,parent['parent_department_name'], header)


        workbook.close()
        self.env.cr.execute('drop table temp_department;')
        out = base64.encodestring(output.getvalue())
        file_name = u'Худалдан авалтын хураангуй тайлан/Захиалагч ажилтан/'
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