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
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.translate import _
import time
from odoo.osv import osv
from odoo.http import request    
from xlwt import *
from operator import itemgetter
import xlsxwriter
from io import BytesIO
import base64



class PurchasePerformanceReport(models.TransientModel):
    _name = 'purchase.performance.report.wizard'
    # TODO FIX LATER
    # _inherit = 'abstract.report.model'
    _description = 'Purchase performance report'


    start_date = fields.Date(string="Performance date start") #Эхлэх огноо
    end_date = fields.Date(string='Performance date end') #Дуусах огноо
    department_ids = fields.Many2many(comodel_name='hr.department', string='Departments')
    buyer_ids = fields.Many2many(comodel_name='hr.employee', string='Buyers')
    state= fields.Selection([('done','Done',),('assigned','Assigned')],string="State")


    
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
        select_state = ''
        if self.state == 'done':
            select_state = 'done','th'
        if self.state == 'assigned':
            select_state = 'assigned','th'
        if self.state == False:
            select_state = 'done','assigned'

        query = "select E.state as req_state,A.date_end,E.ordering_date,K.name_template,E.name as requisition_code,H.id as team_id,H.name as team_name,J.name,DATE_PART('day', A.date_end::timestamp- E.ordering_date::timestamp) as daydiff,D.id ,D.name,A.state,count(A.id),sum(A.product_qty) as qty_sum,sum(A.product_qty * A.product_price) as amount, \
        (select count(id) from purchase_requisition_line where state = 'done') as done_state, \
        (select count(id) from purchase_requisition_line where state = 'assigned') as assigned_state, \
        C.name  as assign from purchase_requisition_line A \
                    inner join res_users B ON B.id=A.buyer \
                    left join assign_category C ON C.id=A.assign_cat \
                    left join purchase_category_config J ON J.user_id=B.id \
                    left join team_registration H ON H.id=J.team_id \
                    left join purchase_requisition E on A.requisition_id = E.id \
                    left join product_product K on A.product_id = K.id\
                    inner join res_partner D ON D.id=B.partner_id \
                    where A.state in %s and A.create_date >= '%s' and A.create_date <= '%s' \
                    group by req_state,D.id,D.name,A.state,C.name,A.product_id,A.product_desc,A.requisition_id,A.date_end,E.ordering_date,H.name,J.name,H.id,E.name,K.name_template,A.date_end,E.ordering_date \
                    order by D.name; \
                    " %(select_state,self.start_date,self.end_date)
        category_query = "select D.name,B.id,C.purchase_category_config_id,C.assign_category_id from purchase_category_config A \
                    inner join res_users B ON B.id=A.user_id \
                    left join assign_category_purchase_category_config_rel C on C.purchase_category_config_id = A.id  \
                    left join purchase_category_config J ON J.user_id=B.id \
                    inner join res_partner D ON D.id=B.partner_id " 

        sheet = workbook.add_worksheet()
        sheet.portrait=True
        sheet.merge_range(0,3,0,6,u'Худалдан авалтын гүйцэтгэлийн тайлан', title1)
        sheet.merge_range(3,0,3,1,u"Огноо :%s - %s"%(self.start_date,self.end_date), header1)
        
        sheet.merge_range(4,0,6,0,u'Баг', title1)
        sheet.set_column(0,0,10)

        sheet.merge_range(4,1,6,1,u'Худалдан авалтын мэргэжилтэн', title1)
        sheet.set_column(1,1,25)

        sheet.merge_range(4,2,6,2,u'Төлөв', title1)
        sheet.set_column(2,2,12)

        sheet.merge_range(4,3,4,4,u'Хэвийн', title1)
        sheet.set_column(3,3,12)

        sheet.merge_range(5,3,6,3,u'Шаардах', title1)
        sheet.set_column(2,2,12)

        sheet.merge_range(5,4,6,4,u'Шаардах мөр', title1)
        sheet.set_column(2,2,12)

        sheet.merge_range(4,5,4,6,u'Хугацаа хэтэрсэн', title1)
        sheet.set_column(2,2,12)

        sheet.merge_range(5,5,6,5,u'Шаардах', title1)
        sheet.set_column(2,2,12)

        sheet.merge_range(5,6,6,6,u'Шаардах мөр', title1)
        sheet.set_column(2,2,12)

        sheet.merge_range(4,7,4,8,u'Нийт', title1)
        sheet.set_column(2,2,12)

        sheet.merge_range(5,7,6,7,u'Шаардах', title1)
        sheet.set_column(2,2,12)

        sheet.merge_range(5,8,6,8,u'Шаардах мөр', title1)
        sheet.set_column(2,2,12)

        sheet.merge_range(4,9,4,10,u'Хувиарлалтын Ангилал', title1)
        sheet.set_column(2,2,12)

        sheet.merge_range(5,9,6,9,u'Гүйцэтгэл', title1)
        sheet.set_column(2,2,12)

        sheet.merge_range(5,10,6,10,u'Төлөвлөлт', title1)
        sheet.set_column(2,2,12)

        sheet.merge_range(4,11,6,11,u'Барааны нэрийн тоо', title1)
        sheet.set_column(11,11,12)

        sheet.merge_range(4,12,6,12,u'Хэмжээ тоо хэмжээ', title1)
        sheet.set_column(12,12,12)

        sheet.merge_range(4,13,6,13,u'Үнийн дүн', title1)
        sheet.set_column(13,13,12)

        sheet.merge_range(4,14,6,14,u'Үнийн дүн', title1)
        sheet.set_column(14,14,12)


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
        stateDict = {}
        for dic in dictfetchall:
            buyer = dic['team_id']
            if dic['team_id'] not in fetchedAll:
                fetchedAll[buyer]= {
                    'team_id':u'',
                    'name':u'',
                    'id':u'',
                    'partners':{},
                    'count':0,
                    'assigned_cats':{},
                    'percent':{},
                }

            fetchedAll[buyer]['name']=dic['team_name']
            fetchedAll[buyer]['id']=dic['team_id']
            partner = dic['id']
            if partner not in fetchedAll[buyer]['partners']:
                fetchedAll[buyer]['partners'][partner]={
                    'name':u'',                    
                    'states':{},
                    'req_states':{},

                }

            fetchedAll[buyer]['partners'][partner]['name']=dic['name']
            # BEGIN
            req_state = dic['req_state']
            if req_state not in fetchedAll[buyer]['partners'][partner]['req_states']:
                fetchedAll[buyer]['partners'][partner]['req_states'][req_state]={
                'name':u'',
                'normal':0,
                'normal_average':0,
                'overdue':0,
                'daydiff':0

                }
            fetchedAll[buyer]['partners'][partner]['req_states'][req_state]['name'] = req_state
             
            if dic['state'] == 'assigned':
                if (datetime.strptime(dic['ordering_date'], "%Y-%m-%d")-datetime.today()).days>0:
                    fetchedAll[buyer]['partners'][partner]['req_states'][req_state]['normal']+=1
                    fetchedAll[buyer]['partners'][partner]['req_states'][req_state]['normal_average']+=(datetime.strptime(dic['ordering_date'], "%Y-%m-%d")-datetime.today()).days
                else:
                    fetchedAll[buyer]['partners'][partner]['req_states'][req_state]['overdue']+=1
                    fetchedAll[buyer]['partners'][partner]['req_states'][req_state]['normal_average']+=(datetime.strptime(dic['ordering_date'], "%Y-%m-%d")-datetime.today()).days
            else:
                if (datetime.strptime(dic['ordering_date'], "%Y-%m-%d")-datetime.strptime(dic['date_end'], "%Y-%m-%d")).days>0:
                    fetchedAll[buyer]['partners'][partner]['req_states'][req_state]['normal']+=1
                    fetchedAll[buyer]['partners'][partner]['req_states'][req_state]['normal_average']+=(datetime.strptime(dic['ordering_date'], "%Y-%m-%d")-datetime.today()).days
                else:
                    fetchedAll[buyer]['partners'][partner]['req_states'][req_state]['overdue']+=1
                    fetchedAll[buyer]['partners'][partner]['req_states'][req_state]['normal_average']+=(datetime.strptime(dic['ordering_date'], "%Y-%m-%d")-datetime.today()).days

            # if dic['ordering_date']:
            #     if dic['daydiff']<=0:
            #         if dic['state'] == 'done'

            #         fetchedAll[buyer]['partners'][partner]['req_states'][req_state]['normal']+=1
            #     else:
            #         fetchedAll[buyer]['partners'][partner]['req_states'][req_state]['overdue']+=1

            # TSOOJ
            state = dic['state']
            if state not in fetchedAll[buyer]['partners'][partner]['states']:
                fetchedAll[buyer]['partners'][partner]['states'][state]={
                    'state':u'',
                    'count':0,
                    'name':0,
                    'qty':0,
                    'amount':0,
                    'done_normal_requisition_line':0,
                    'done_overdue_requisition_line':0,
                    'assigned_normal_requisition_line':0,
                    'assigned_overdue_requisition_line':0,
                    'assigned_state':0,
                    'assigned_cats':{},
                    'requisitions':{},
                    'requisition_lines':{},
                    'products':{},
                    'assigned_cats':{},
                    'normal_daydiff':0,
                    'overdue_daydiff':0,
                    'normal_count':0,
                    'overdue_count':0,
                }

            fetchedAll[buyer]['partners'][partner]['states'][state]['name']= dic['name']
            fetchedAll[buyer]['partners'][partner]['states'][state]['state']= state
            fetchedAll[buyer]['partners'][partner]['states'][state]['count'] += dic['count']
            fetchedAll[buyer]['partners'][partner]['states'][state]['qty']+=dic['qty_sum']
            fetchedAll[buyer]['partners'][partner]['states'][state]['amount']+=dic['amount']

            if dic['state'] == 'assigned':
                if (datetime.strptime(dic['ordering_date'], "%Y-%m-%d")-datetime.today()).days>0:
                    fetchedAll[buyer]['partners'][partner]['states'][state]['done_normal_requisition_line']+=1
                else:
                    fetchedAll[buyer]['partners'][partner]['states'][state]['done_overdue_requisition_line'] += 1
            else:
                if (datetime.strptime(dic['ordering_date'], "%Y-%m-%d")-datetime.strptime(dic['date_end'], "%Y-%m-%d")).days>0:
                    fetchedAll[buyer]['partners'][partner]['states'][state]['done_normal_requisition_line']+=1
                else:
                    fetchedAll[buyer]['partners'][partner]['states'][state]['done_overdue_requisition_line'] += 1

            assign = dic['assign']
            if assign not in fetchedAll[buyer]['partners'][partner]['states'][dic['state']]['assigned_cats']:
                fetchedAll[buyer]['partners'][partner]['states'][dic['state']]['assigned_cats'][assign] = {
                                'name':u'',
                            }
            fetchedAll[buyer]['partners'][partner]['states'][dic['state']]['assigned_cats'][assign]['name']= assign
 
            requisition = dic['requisition_code']
            if requisition not in fetchedAll[buyer]['partners'][partner]['states'][state]['requisitions']:
                fetchedAll[buyer]['partners'][partner]['states'][state]['requisitions'][requisition] = {
                    'name':u'',
                    'normal':u'',                    
                    'overdue':u'',                    
                }
            
            fetchedAll[buyer]['partners'][partner]['states'][state]['requisitions'][requisition]['name']=requisition

            

                        

            product = dic['name_template']
            if product not in fetchedAll[buyer]['partners'][partner]['states'][state]['products']:
                fetchedAll[buyer]['partners'][partner]['states'][state]['products'][product] = {
                    'name':u'',
                }
            fetchedAll[buyer]['partners'][partner]['states'][state]['products'][product]['name']=product

        for emp in sorted(fetchedAll.values(), key=itemgetter('id')):
            row_count=row
            for partner in sorted(emp['partners'].values(), key=itemgetter('name')):
                # print'________LP________',partner['name']
                sheet.write(row,1,partner['name'],header)
                # sheet.write(row,2,partner['state'],header)
                row+=1
                normal_done_assigned = 0
                overdue_done_assigned = 0
                sum_normal_requisition = 0
                sum_normal_requisition_line = 0
                sum_overdue_requisition = 0
                sum_normal_requisition_line = 0
                overdue_done_assigned = 0
                overdue_done_assigned = 0
                overdue_done_assigned = 0
                overdue_done_assigned = 0
                for state in sorted(partner['states'].values(), key=itemgetter('state')):
                    if state['state'] == 'done':
                        st = u'Дууссан'
                        # normal_done_assigned = state['done_normal_requisition_line']
                        # overdue_done_assigned = state['done_overdue_requisition_line']
                    elif state['state'] == 'assigned':
                        st = u'Хувиарласан'
                        # normal_done_assigned = state['assigned_normal_requisition_line']
                        # overdue_done_assigned = state['assigned_overdue_requisition_line']
                    sheet.write(row-1,2,st,header)
                    sheet.write(row-1,3,partner['req_states'][state['state']]['normal'],header)
                    sheet.write(row-1,4,partner['states'][state['state']]['done_normal_requisition_line'],header)
                    sheet.write(row-1,5,partner['req_states'][state['state']]['overdue'],header)
                    sheet.write(row-1,6,partner['states'][state['state']]['done_overdue_requisition_line'],header)
                    sheet.write(row-1,7,partner['req_states'][state['state']]['overdue']+partner['req_states'][state['state']]['normal'],header)
                    sheet.write(row-1,8,partner['states'][state['state']]['done_normal_requisition_line']+partner['states'][state['state']]['done_overdue_requisition_line'],header)
                    if state['assigned_cats']:
                        sheet.write(row-1,9,len(state['assigned_cats']),header)
                    else:
                        sheet.write(row-1,9,' ',header)
                    if state['name'] in category_fetchedAll:
                        sheet.write(row-1,10,category_fetchedAll[state['name']]['count'],header)
                    else:
                        sheet.write(row-1,10,' ',header)
                        
                    if state['products']:
                        sheet.write(row-1,11,len(state['products']),header)
                    else:
                        sheet.write(row-1,11,' ',header)
                    sheet.write(row-1,12,state['qty'],header)
                    sheet.write(row-1,13,state['amount'],header)
                    sheet.write(row-1,14,partner['req_states'][state['state']]['normal_average']/partner['req_states'][state['state']]['overdue']+partner['req_states'][state['state']]['normal'],header)

                    row+=1

            sheet.merge_range(row,1, row, 2,u'Нийт дүн', title)
            # sheet.write(row,3,total_count,style1)
            # sheet.write(row-1,4,round(total_qty_in,3),style1)
            # sheet.write(row-1,5,total_qty,style1)
            # sheet.write(row-1,6,total_assigned_cats,style1)
            # sheet.write(row-1,7,total_amount,style1)
            # sheet.write(row-1,8,round(total_price,3),style1)
            # sheet.write(row-1,9,normal_daydiff,style1)
            # sheet.write(row-1,10,overdue_daydiff,style1)

            # if row-1 == row_count:
            #     sheet.write(row_count,0,emp['name'],header)
            # else:
            #     print'____LOL____',row_count,row-1,row
            #     sheet.write(row,1,emp['name'],header)
            #     sheet.merge_range(row_count,0, row-1, 0,emp['name'], header)

            sheet.write(row,1,emp['name'],header)
            sheet.merge_range(row_count,0, row-1, 0,emp['name'], header)


        #     state = dic['state']
        #     if dic['state'] not in stateDict:
        #         stateDict[state]= {
        #             'name':u'',
        #             'count':0,
        #             'price':0,
        #         }
        #     stateDict[dic['state']]['name'] = dic['state']
        #     stateDict[dic['state']]['count'] += dic['count']
        #     stateDict[dic['state']]['price'] += dic['amount']
            
        #     if dic['state'] not in fetchedAll[buyer]['states']:
        #         fetchedAll[buyer]['states'][dic['state']]={
        #             'state':u'',
        #             'count':0,
        #             'qty':0,
        #             'amount':0,
        #             'done_state':0,
        #             'assigned_state':0,
        #             'assigned_cats':{},
        #             'normal_daydiff':0,
        #             'overdue_daydiff':0,
        #             'normal_count':0,
        #             'overdue_count':0,
        #         }
        #     if dic['state'] == 'done':
        #         fetchedAll[buyer]['states'][dic['state']]['done_state']=dic['done_state']
        #     elif dic['state'] == 'assigned':
        #         fetchedAll[buyer]['states'][dic['state']]['assigned_state']=dic['assigned_state']
        #     fetchedAll[buyer]['states'][dic['state']]['state']=dic['state']
        #     fetchedAll[buyer]['states'][dic['state']]['count']+=dic['count']
        #     fetchedAll[buyer]['states'][dic['state']]['qty']+=dic['qty_sum']
        #     fetchedAll[buyer]['states'][dic['state']]['amount']+=dic['amount']
        #     if dic['daydiff'] > 0:
        #         fetchedAll[buyer]['states'][dic['state']]['overdue_daydiff']+=dic['daydiff']
        #         fetchedAll[buyer]['states'][dic['state']]['overdue_count'] += 1
        #     else:
        #         fetchedAll[buyer]['states'][dic['state']]['overdue_count'] = 1
        #     if dic['daydiff'] < 0:
        #         fetchedAll[buyer]['states'][dic['state']]['normal_daydiff']+=dic['daydiff']
        #         fetchedAll[buyer]['states'][dic['state']]['normal_count'] += 1
        #     else:
        #         fetchedAll[buyer]['states'][dic['state']]['normal_count'] = 1
        #     if dic['assign'] not in fetchedAll[buyer]['states'][dic['state']]['assigned_cats']:
        #                     fetchedAll[buyer]['states'][dic['state']]['assigned_cats'][dic['assign']] = {
        #                         'name':u'',
        #                     }
        #     fetchedAll[buyer]['states'][dic['state']]['assigned_cats'][dic['assign']]['name']=dic['assign']            

        #     fetchedAll[buyer]['count']+=dic['count']
        #     if dic['assign'] not in fetchedAll[buyer]['assigned_cats']:
        #         fetchedAll[buyer]['assigned_cats'][dic['assign']] = {
        #             'name':u'',
        #         }
        #     fetchedAll[buyer]['assigned_cats'][dic['assign']]['name']=dic['assign']            
            
        # count=1
        # all_count = 0
        # all_qty_in = 0
        # all_total_qty = 0
        # all_assigned_cats = 0
        # all_amount = 0
        # all_price = 0
        # all_daydiff = 0
        # all_normal_daydiff = 0
        # all_overdue_daydiff = 0
        # emp_average = 0.0
        # for emp in sorted(fetchedAll.values(), key=itemgetter('name')):
        #     sheet.write(row,0,count,header)
        #     sheet.write(row,1,emp['name'],header)
        #     sheet.write(row,2,' ',header)
        #     sheet.write(row,3,' ',header)
        #     sheet.write(row,4,' ',header)
        #     sheet.write(row,5,' ',header)
        #     sheet.write(row,6,' ',header)
        #     sheet.write(row,7,' ',header)
        #     sheet.write(row,8,' ',header)
        #     sheet.write(row,9,' ',header)
        #     emp_average += 1
        #     row+=1
        #     qty_in = 0.0
        #     price_in = 0.0
        #     total_count = 0
        #     total_qty_in = 0 
        #     total_price = 0 
        #     total_qty = 0 
        #     total_assigned_cats = 0 
        #     total_amount = 0 
        #     total_daydiff = 0
        #     normal_daydiff = 0.0
        #     overdue_daydiff = 0.0
        #     for state in sorted(emp['states'].values(), key=itemgetter('state')):
        #         total_count += state['count']
        #         total_qty += state['qty']
        #         total_amount += state['amount']
        #         normal_daydiff += state['normal_daydiff']/state['normal_count']
        #         overdue_daydiff += state['overdue_daydiff']/state['overdue_count']
        #         if state['state'] == 'done':
        #             st = u'Дууссан'
        #             qty_in = (float(state['count']) * 100) / float(stateDict['done']['count'])
        #             price_in = (float(state['amount']) * 100) / float(stateDict['done']['price'])
        #             total_qty_in += (float(state['count']) * 100) / float(stateDict['done']['count'])
        #             total_price += (float(state['amount']) * 100) / float(stateDict['done']['price'])
        #         elif state['state'] == 'assigned':
        #             st = u'Хувиарласан'
        #             qty_in = (float(state['count']) * 100) / float(stateDict['assigned']['count'])
        #             price_in = (float(state['amount']) * 100) / float(stateDict['assigned']['price'])
        #             total_qty_in += (float(state['count']) * 100) / float(stateDict['assigned']['count'])
        #             total_price += (float(state['amount']) * 100) / float(stateDict['assigned']['price'])
        #         sheet.write(row,0,' ',header)
        #         sheet.write(row,1,' ',header)
        #         sheet.write(row,2,st,header)
        #         sheet.write(row,3,state['count'],header)
        #         sheet.write(row,4,round(qty_in,3),header)
        #         sheet.write(row,5,state['qty'],header)
        #         if state['assigned_cats']:
        #             sheet.write(row,6,len(state['assigned_cats']),header)
        #             total_assigned_cats += len(state['assigned_cats'])
        #         else:
        #             sheet.write(row,6,' ',header)
        #         sheet.write(row,7,state['amount'],header)
        #         sheet.write(row,8,round(price_in,3),header)
        #         sheet.write(row,9,state['normal_daydiff']/state['normal_count'],header)
        #         sheet.write(row,10,state['overdue_daydiff']/state['overdue_count'],header)
                
        #         row+=1
        #     if total_count:
        #         all_count += total_count
        #     all_qty_in += total_qty_in
        #     all_total_qty += total_qty
        #     all_assigned_cats += total_assigned_cats
        #     all_amount += total_amount
        #     all_price += total_price
        #     all_normal_daydiff += normal_daydiff
        #     all_overdue_daydiff += overdue_daydiff
        #     sheet.write(row,0,' ',style1)
        #     sheet.write(row,1,' ',style1)
        #     sheet.write(row,2,u'Нийт',style1)
        #     sheet.write(row,3,total_count,style1)
        #     sheet.write(row,4,round(total_qty_in,3),style1)
        #     sheet.write(row,5,total_qty,style1)
        #     sheet.write(row,6,total_assigned_cats,style1)
        #     sheet.write(row,7,total_amount,style1)
        #     sheet.write(row,8,round(total_price,3),style1)
        #     sheet.write(row,9,normal_daydiff,style1)
        #     sheet.write(row,10,overdue_daydiff,style1)
        #     count+=1
        #     row+=1
        # if emp_average:
        #     sheet.merge_range(row,0, row, 2,u'Нийт дундаж', title)
        #     sheet.write(row,3,round(all_count/emp_average,1),title)
        #     sheet.write(row,4,round(round(all_qty_in,3)/emp_average,1),title) 
        #     sheet.write(row,5,round(all_total_qty/emp_average,1),title) 
        #     sheet.write(row,6,round(all_assigned_cats/emp_average,1),title) 
        #     sheet.write(row,7,round(all_amount/emp_average,1),title) 
        #     sheet.write(row,8,round(round(all_price,3)/emp_average,1),title) 
        #     sheet.write(row,9,round(all_normal_daydiff/emp_average,1),title)
        #     sheet.write(row,10,round(all_overdue_daydiff/emp_average,1),title)

        # sheet.merge_range(row+1,0, row+1, 2,u'Нийт дүн', title)
        # sheet.write(row+1,3,all_count,title)
        # sheet.write(row+1,4,round(all_qty_in,3),title) 
        # sheet.write(row+1,5,all_total_qty,title) 
        # sheet.write(row+1,6,all_assigned_cats,title) 
        # sheet.write(row+1,7,all_amount,title) 
        # sheet.write(row+1,8,round(all_price,3),title) 
        # sheet.write(row+1,9,all_normal_daydiff,title)
        # sheet.write(row+1,10,round(all_overdue_daydiff,1),title)  
        # sheet.merge_range(row+4,0, row+4, 3,u'Тайлан хэвлэсэн: ................... /%s/'%(self.env.user.name), title)
        workbook.close()

        out = base64.encodestring(output.getvalue())
        file_name = u'Худалдан авалтын хураангуй тайлан/Худалдан авалтын ажилтан/'
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
