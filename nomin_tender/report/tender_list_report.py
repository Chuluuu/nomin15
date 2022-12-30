# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
import openerp.tools
from openerp.tools.translate import _
from openerp.http import request
from openerp import SUPERUSER_ID
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp import api, fields, models, _
import xlwt
from xlwt import *
from StringIO import StringIO
from io import BytesIO
import base64
import xlsxwriter
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter

from openerp.addons.l10n_mn_report_base.report_helper import verbose_numeric, comma_me, convert_curr
from openerp.addons.nomin_base.report.nomin_report_style import styles

class bidding_list_report(models.TransientModel):
    _name = 'bidding.list.report'
    _inherit = 'abstract.report.model'
    
    @api.model
    def _get_start_date(self):
        return datetime.strptime(fields.Datetime.now(), '%Y-%m-%d %H:%M:%S')

    @api.model
    def _get_end_date(self):
        return datetime.strptime(fields.Datetime.now(), '%Y-%m-%d %H:%M:%S')
    
    def weeks_between(self, start_date, end_date):
        weeks = rrule.rrule(rrule.WEEKLY, dtstart=start_date, until=end_date)
        return weeks.count()
    
    start_date              = fields.Date(string=u'Эхлэх огноо', default=_get_start_date)
    end_date                = fields.Date(string=u'Дуусах огноо', default=_get_end_date)
    type_ids                = fields.Many2many(comodel_name='tender.type', string = u'Тендерийн төрөл')
    sector_ids              = fields.Many2many(comodel_name='hr.department', string = u'Гэрээт ажлын захиалагч', domain=[('is_sector','=',True)])
    respondent_sector_ids   = fields.Many2many(comodel_name='hr.department', string = u'Тендер санхүүжүүлэгч')
    #participant_ids        = fields.Many2many(comodel_name='tender.participants.bid',string = u'Гэрээт ажлын гүйцэтгэгч /Шалгарсан оролцогч/')
    partner_ids             = fields.Many2many(comodel_name='res.partner',string = u'Гэрээт ажлын гүйцэтгэгч')
    tender_amount_min       = fields.Float(string = u'Гэрээт ажлын төсөв')
    tender_amount_max       = fields.Float(string = u'Гэрээт ажлын төсөв')
    contract_date_start     = fields.Date(string = u'Гэрээ эхлэх огноо')
    contract_date_end       = fields.Date(string = u'Гэрээ дуусах огноо')
    
    
    @api.multi
    def export_tender_report(self,report_code,context=None):
        active_ids = self.env.context.get('active_ids', [])
        if context is None:
            context = {}

        domain = [('date_open_deadline','>=',self.start_date),('date_end','<=',self.end_date),('state','not in',['draft', 'reject'])]
        domain_value = []
        if self.type_ids:
             domain = domain + [('type_id','=',self.type_ids.ids)]
        if self.sector_ids:
             domain =  domain + [('department_id','=',self.sector_ids.ids)]
        if self.respondent_sector_ids:
            domain =  domain + [('respondent_department_id','=',self.respondent_sector_ids.ids)]
        if self.partner_ids:
            domain =  domain + [('participants_ids.partner_id','=',self.partner_ids.ids)]
        if self.tender_amount_min:
            domain =  domain + [('total_budget_amount','>=',self.tender_amount_min)]
        if self.tender_amount_max:
            domain =  domain + [('total_budget_amount','<=',self.tender_amount_max)]
        if self.contract_date_start:
            domain = domain + [('contract_id.date_start','>=',self.contract_date_start)]
        if self.contract_date_end:
            domain = domain + [('contract_id.date_end','<=',self.contract_date_end)]
        
        tenders = self.env['tender.tender'].search(domain)
        tender_ids = []
        for tender in tenders:
            tender_ids.append(tender.id)

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        
        header = workbook.add_format({
                'border': 1,
                'bold': 1,
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': 'on',
                'font_size':10,
                'font_name': 'Arial',
                'fg_color': '#8cece2',
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
                'bold': 0,
                'align': 'left',
                'valign': 'vcenter',
                'text_wrap': 'on',
                'font_size':10,
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
        
        cell_float_format_left = workbook.add_format({
                'border': 1,
                'bold': 0,
                'align': 'left',
                'valign': 'vcenter',
                'text_wrap': 'on',
                'font_size':10,
                'font_name': 'Arial',
                'num_format': '#,##0'
                })
        
        cell_float_format_right = workbook.add_format({
                'border': 1,
                'bold': 0,
                'align': 'right',
                'valign': 'vcenter',
                'text_wrap': 'on',
                'font_size':10,
                'font_name': 'Arial',
                'num_format': '#,##0'
                })

        cell_float_format_left_bold = workbook.add_format({
                'border': 1,
                'bold': 1,
                'align': 'left',
                'valign': 'vcenter',
                'text_wrap': 'on',
                'font_size':10,
                'font_name': 'Arial',
                'num_format': '#,##0'
                })

        cell_float_format_right_bold = workbook.add_format({
                'border': 1,
                'bold': 1,
                'align': 'right',
                'valign': 'vcenter',
                'text_wrap': 'on',
                'font_size':10,
                'font_name': 'Arial',
                'num_format': '#,##0'
                })

        cell_percent_format_right_bold = workbook.add_format({
            'border': 1,
            'align': 'center',
            'bold': 1,
            'valign': 'top',
            'font_size':10,
            'font_name': 'Arial',
            #'fg_color': '#87ceeb',
            #'num_format':'0.0%'
            })

        cell_percent_format_right = workbook.add_format({
            'border': 1,
            'align': 'center',
            'bold': 0,
            'valign': 'top',
            'font_size':10,
            'font_name': 'Arial',
            #'fg_color': '#87ceeb',
            #'num_format':'0,0.0%'
            })
                
        
#         worksheet = workbook.add_worksheet()
        worksheet = workbook.add_worksheet(u'Tender')
        file_name = 'Tender.xlsx'
        worksheet.set_column('A:A', 10)
        worksheet.set_row(1, 40)
#         worksheet.set_row(2, 40)
        worksheet.set_column('B:B', 50)
        worksheet.set_column('C:C', 10)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 8)
        worksheet.set_column('H:H', 8)
        worksheet.set_column('I:I', 8)
        worksheet.set_column('J:J', 8)
        worksheet.set_column('K:K', 10)
        worksheet.set_column('L:L', 8)
        worksheet.set_column('M:M', 8)
        worksheet.set_column('N:N', 8)
        worksheet.set_column('O:O', 8)
        worksheet.set_column('P:P', 8)
        worksheet.set_column('Q:Q', 8)
        worksheet.set_column('R:R', 8)
        worksheet.set_column('S:S', 8)
        worksheet.set_column('T:T', 8)
        worksheet.set_column('U:U', 8)
        worksheet.set_column('V:V', 8)
        worksheet.set_column('W:W', 15)
        worksheet.set_column('X:X', 10)
        worksheet.set_column('Y:Y', 8)
        worksheet.set_column('Z:Z', 8)
        worksheet.set_column('AA:AA', 10)
        worksheet.set_column('AB:AB', 10)
        worksheet.set_column('AC:AC', 10)
        worksheet.set_column('AD:AD', 10)
        worksheet.set_column('AE:AE', 10)
        worksheet.set_column('AF:AF', 10)
        worksheet.set_column('AG:AG', 15)
        worksheet.set_column('AH:AH', 8)
        worksheet.set_column('AI:AI', 8)
        worksheet.set_column('AJ:AJ', 8)
        worksheet.set_column('AK:AK', 10)
 
        row = 0
        col = 0
        
        tender_dict = {}
        tenders = self.env['tender.tender'].sudo().search([('id','in', tender_ids)])
        for tender in tenders:
            meetings = self.env['tender.meeting'].sudo().search([('tender_id','=',tender.id),('state','=','confirmed')])
            members = self.env['tender.committee.member'].sudo().search([('tender_id','=', tender.id),('is_valuation','=', False)])
            participant_ids = self.env['tender.participants.bid'].sudo().search([('tender_id','=', tender.id),('state','!=','draft')])
            
            if tender.id:
                group = tender.name
            
            if group not in tender_dict:
                tender_dict [group] = {
                    'name':u'Тодорхойгүй',
                    'desc_name':u'Тодорхойгүй',
                    'type_id':u'Тодорхойгүй',
                    'child_type_id':u'Тодорхойгүй',
                    'sector_id':u'Тодорхойгүй',
                    'respondent_sector_id':u'Тодорхойгүй',
                    'date_open_deadline':u'Тодорхойгүй',
                    'published_date':u'Тодорхойгүй',
                    'date_end':u'Тодорхойгүй',
                    'closed_date':u'Тодорхойгүй',
                    'total_budget_amount':u'Тодорхойгүй',
                    'control_budget_verifier':u'Тодорхойгүй',
                    'work_graph_verifier':u'Тодорхойгүй',
                    'work_task_verifier':u'Тодорхойгүй',
                    'meet_name':u'Тодорхойгүй',
                    'meeting_from_date':u'Тодорхойгүй',
                    'is_valuation_members1': u'',
                    'is_valuation_members2': u'',
                    'is_valuation_members3': u'',
                    'is_valuation_members4': u'',
                    'is_valuation_members5': u'',
                    'is_valuation_members': {},
                    'is_members': '',
                    'participants':{}
                    }
                
            
            tender_dict [group]['name']= tender.name if tender.name else  u'-'
            tender_dict [group]['desc_name']= tender.desc_name if tender.desc_name else  u'-'
            tender_dict [group]['type_id']= tender.type_id.name if tender.type_id.name else 0.0
            tender_dict [group]['child_type_id']= tender.child_type_id.name if tender.child_type_id.name else  u'Тодорхойгүй'
            tender_dict [group]['sector_id']= tender.sector_id.name if tender.sector_id.name else u''
            tender_dict [group]['respondent_sector_id']= tender.respondent_department_id.name if tender.respondent_department_id.name else u''
            date_open_deadline = u''
            if tender.date_open_deadline:
                date_open_deadline = datetime.strptime(tender.date_open_deadline, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
            published_date = u''
            if tender.published_date:
                published_date = datetime.strptime(tender.published_date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
            date_end = u''
            if tender.date_end:
                date_end = datetime.strptime(tender.date_end, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')

            tender_dict [group]['date_open_deadline']= date_open_deadline if date_open_deadline else u''
            tender_dict [group]['published_date']= published_date if published_date else  u''
            tender_dict [group]['date_end']= date_end if date_end else  u''
            tender_dict [group]['closed_date']= tender.closed_date if tender.closed_date else u''
            tender_dict [group]['total_budget_amount']= tender.total_budget_amount if tender.total_budget_amount else 0.0
            tender_dict [group]['control_budget_verifier']= tender.control_budget_verifier if tender.control_budget_verifier else  u''
            tender_dict [group]['work_graph_verifier']= tender.work_task_verifier if tender.work_task_verifier else  u''
            tender_dict [group]['work_task_verifier']= tender.work_task_verifier if tender.work_task_verifier else  u''
            
            for meet in meetings:
                meeting_date = u''
                if meet.meeting_from_date:
                    meeting_date = datetime.strptime(meet.meeting_from_date, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
                tender_dict [group]['meet_name'] = meet.name
                tender_dict [group]['meeting_from_date'] = meeting_date
            
            advisor = ''
            count=1
            for member in tender.committee_member_ids:
                if member.is_valuation == True:
                    tender_dict [group]['is_valuation_members'+str(count)]= member.employee_id.name if member.employee_id.name else  u''
                    count+=1
                    
                else:
                    employeename = member.employee_id.name
                    advisor= advisor + employeename + ", "
                    
            tender_dict [group]['is_members']= advisor if advisor else  u''
            for p in participant_ids:
                group1 = p.partner_id.name
                if group1 not in tender_dict[group]['participants']:
                    tender_dict[group]['participants'][group1] = {
                        'partic_name':u'',
                        'partic_cost':0.0,
                        'parcic_schedule':u'',
                        'rate_value':0.0,
                        'description':u'',
                        'contract_start_date': u'',
                        'contract_end_date': u'',
                        'contract_started_date': u'',
                        'contract_ended_date': u'',
                        'contract_create_date': u'',
                        'contract_create_date': u'',
                        'contract_is_date': u'',
                        'cont_description': u'',
                        'add_expense': 0.0,
                        'min_expense': 0.0,
                        'real_total_amount': 0.0,
                        'cont_rate' : 0,
                        }
                
                rate_partner_id = self.env['tender.valuation.partner'].search([('tender_id','=',tender.id),('partner_id','=',p.partner_id.id)])
                tender_dict [group]['participants'][group1]['partic_name']= p.partner_id.name if p.partner_id else  u''
                tender_dict [group]['participants'][group1]['partic_cost']= p.amount_total if p.amount_total else  0.0
                tender_dict [group]['participants'][group1]['parcic_schedule']= p.execute_time if p.execute_time else u''
                
                for rate in rate_partner_id:
                    tender_dict [group]['participants'][group1]['rate_value']= rate.total_value if rate.total_value else  0.0
                    tender_dict [group]['participants'][group1]['description']= u'шалгарсан' if rate.is_win else u'-'
                
                contract_partner_id = self.env['contract.management'].sudo().search([('tender_id','=',tender.id),('customer_company','=',p.partner_id.id)])
                
                tender_dict [group]['participants'][group1]['contract_start_date']= contract_partner_id.date_start if contract_partner_id.date_start else  u''
                tender_dict [group]['participants'][group1]['contract_end_date']= contract_partner_id.date_end if contract_partner_id.date_end else  u''
                
                perform_contract_id = self.env['contract.performance'].sudo().search([('contract_id','=', contract_partner_id.id),('partner_id','=', p.partner_id.id)])
                        
                for per in perform_contract_id:
                    tender_dict [group]['participants'][group1]['contract_started_date']= per.start_date if per.start_date else u''
                    tender_dict [group]['participants'][group1]['contract_ended_date']= per.confirmed_date if per.confirmed_date else u''
                    tender_dict [group]['participants'][group1]['contract_is_date']= u'үгүй' if per.confirmed_date > per.end_date else u'тийм'
                    tender_dict [group]['participants'][group1]['cont_description']= per.description if per.description else u''
                    tender_dict [group]['participants'][group1]['add_expense']= per.additional_expense if per.additional_expense else 0.0
                    tender_dict [group]['participants'][group1]['min_expense']= per.minus_expense if per.minus_expense else 0.0
                    tender_dict [group]['participants'][group1]['real_total_amount']= per.minus_expense if per.minus_expense else 0.0
                    tender_dict [group]['participants'][group1]['cont_rate']= per.total_percent if per.total_percent else 0.0
            
                
        if tender_dict:
            row += 1
            worksheet.write(row, 0, u'Т.№', header)
            worksheet.write(row, 1, u'Т.Нэр', header)
            worksheet.write(row, 2, u'Т.Ангилал', header)
            worksheet.write(row, 3, u'Т.Дэд ангилал', header)
            worksheet.write(row, 4, u'Т.Захиалагч', header)
            worksheet.write(row, 5, u'Т.Санхүүжүүлэгч', header)
            worksheet.write(row, 6, u'Т.Хүсэлт огноо', header)
            worksheet.write(row, 7, u'Т.Зарласан огноо', header)
            worksheet.write(row, 8, u'Т.Хаах огноо', header)
            worksheet.write(row, 9, u'Т.Хаасан огноо', header)
            worksheet.write(row, 10, u'Т.Хяналтын төсөв үнэ', header)
            worksheet.write(row, 11, u'Т.Хяналтын төсөв баталсан', header)
            worksheet.write(row, 12, u'Т.Зураг баталсан', header)
            worksheet.write(row, 13, u'Т.Ажлын даалгавар баталсан', header)
            worksheet.write(row, 14, u'Х.№', header)
            worksheet.write(row, 15, u'Х.Огноо', header)
            worksheet.write(row, 16, u'Х.Комисс 1', header)
            worksheet.write(row, 17, u'Х.Комисс 2', header)
            worksheet.write(row, 18, u'Х.Комисс 3', header)
            worksheet.write(row, 19, u'Х.Комисс 4', header)
            worksheet.write(row, 20, u'Х.Комисс 5', header)
            worksheet.write(row, 21, u'Х.Инженер', header)
            worksheet.write(row, 22, u'Ш.Оролцогч', header)
            worksheet.write(row, 23, u'Ш.Үнэ', header)
            worksheet.write(row, 24, u'Ш.Хугацаа хоногоор', header)
            worksheet.write(row, 25, u'Ш.Оноо', header)
            worksheet.write(row, 26, u'Ш.Тайлбар', header)
            worksheet.write(row, 27, u'А.Гэрээгээр эхлэх огноо', header)
            worksheet.write(row, 28, u'А.Гэрээгээр дуусах огноо', header)
            worksheet.write(row, 29, u'А.Гэрээгээр эхэлсэн огноо', header)
            worksheet.write(row, 30, u'А.Гэрээгээр дууссан огноо', header)
            worksheet.write(row, 31, u'А.Гэрээт хугацаандаа дууссан эсэх', header)
            worksheet.write(row, 32, u'А.Тайлбар', header)
            worksheet.write(row, 33, u'А.Нэмэгдэх зардал', header)
            worksheet.write(row, 34, u'А.Хасагдах зардал', header)
            worksheet.write(row, 35, u'А.Нийт үнийн дүн', header)
            worksheet.write(row, 36, u'А.Гүйцэтгэлийн үнэлгээ', header)
            row += 1
            for tender in sorted(tender_dict.values(), key=itemgetter('name')):
                for partic in sorted(tender['participants'].values(), key=itemgetter('partic_name')):
                    total_amount = 0
                    worksheet.write(row, 0, tender['name'], cell_format_right)
                    worksheet.write(row, 1, tender['desc_name'], cell_format_left)
                    worksheet.write(row, 2, tender['type_id'], cell_format_left)
                    worksheet.write(row, 3, tender['child_type_id'], cell_format_left)
                    worksheet.write(row, 4, tender['sector_id'], cell_format_left)
                    worksheet.write(row, 5, tender['respondent_sector_id'], cell_format_left)
                    worksheet.write(row, 6, tender['date_open_deadline'], cell_format_right)
                    worksheet.write(row, 7, tender['published_date'], cell_format_right)
                    worksheet.write(row, 8, tender['date_end'], cell_format_right)
                    worksheet.write(row, 9, tender['closed_date'], cell_format_right)
                    total_budget_amount = comma_me(abs(tender['total_budget_amount']))
                    worksheet.write(row, 10, u''+str(total_budget_amount), cell_float_format_right)
                    worksheet.write(row, 11, tender['control_budget_verifier'], cell_format_left)
                    worksheet.write(row, 12, tender['work_graph_verifier'], cell_format_left)
                    worksheet.write(row, 13, tender['work_task_verifier'], cell_format_left)
                    worksheet.write(row, 14, tender['meet_name'], cell_format_right)
                    worksheet.write(row, 15, tender['meeting_from_date'], cell_format_right)
                    worksheet.write(row, 16, tender['is_valuation_members1'], cell_format_right)
                    worksheet.write(row, 17, tender['is_valuation_members2'], cell_format_right)
                    worksheet.write(row, 18, tender['is_valuation_members3'], cell_format_right)
                    worksheet.write(row, 19, tender['is_valuation_members4'], cell_format_right)
                    worksheet.write(row, 20, tender['is_valuation_members5'], cell_format_right)
                    worksheet.write(row, 21, tender['is_members'], cell_format_right)
                    worksheet.write(row, 22, partic['partic_name'], cell_format_left)
                    total_cost = comma_me(abs(partic['partic_cost']))
                    worksheet.write(row, 23, u''+str(total_cost), cell_float_format_right)
                    worksheet.write(row, 24, partic['parcic_schedule'], cell_format_right)
                    worksheet.write(row, 25, partic['rate_value'], cell_format_right)
                    worksheet.write(row, 26, partic['description'], cell_format_left)
                    worksheet.write(row, 27, partic['contract_start_date'], cell_format_right)
                    worksheet.write(row, 28, partic['contract_end_date'], cell_format_right)
                    worksheet.write(row, 29, partic['contract_started_date'], cell_format_right)
                    worksheet.write(row, 30, partic['contract_ended_date'], cell_format_right)
                    worksheet.write(row, 31, partic['contract_is_date'], cell_format_left)
                    worksheet.write(row, 32, partic['cont_description'], cell_format_left)
                    add_expense = comma_me(abs(partic['add_expense']))
                    min_expense = comma_me(abs(partic['min_expense']))
                    worksheet.write(row, 33, add_expense, cell_float_format_right)
                    worksheet.write(row, 34, min_expense, cell_float_format_right)
                    min_expense = 0.0
                    add_expense = 0.0
                    amount = 0.0
                    if partic['partic_cost']:
                        amount = partic['partic_cost']
                    
                    if partic['add_expense']:
                        add_expense = partic['add_expense']
                    
                    if partic['min_expense']:
                        min_expense = partic['min_expense'] 
                    
                    total_amount = amount + add_expense - min_expense
                    total_amount = comma_me(abs(total_amount))
                    worksheet.write(row, 35, u''+str(total_amount) if partic['description'] ==u'шалгарсан' else 0.0, cell_float_format_right)
                    worksheet.write(row, 36, partic['cont_rate'], cell_percent_format_right)
                    
                    row += 1
        
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
            
        

