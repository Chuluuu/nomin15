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

from openerp import models, fields, api, _
from dateutil.relativedelta import relativedelta
from lxml import etree
from openerp.exceptions import UserError
import xlwt
from xlwt import *
from StringIO import StringIO
from datetime import date, datetime, timedelta
import time
from dateutil import rrule

class project_issue_status_report(models.TransientModel):
    _name = 'project.issue.status.report'
    _inherit = 'abstract.report.model'
    _description = 'Project Issue Status Report'
    
    project_id = fields.Many2many(comodel_name='project.project',string=u'Төсөл')
    user_id = fields.Many2many(comodel_name='res.users', string=u'Хариуцагч')
    reason_id = fields.Many2many(comodel_name='task.deadline.reason', string=u'Шалтгаан')
    tag_ids = fields.Many2many(comodel_name='project.tags', string=u'Пайз')
    
    @api.multi
    def get_export_data(self,report_code,context=None):
        if context is None:
            context = {}
        datas={}
        datas['model'] = 'project.issue'
        datas['form'] = self.read(['project_id','user_id','reason_id','tag_ids'])[0] 
        data = datas['form']
        
        employee                        = self.env['hr.employee']
        employee_id                     = employee.sudo().search([('user_id','=',self._uid)])
        
        ezxf = xlwt.easyxf
        style1 = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
        style2 = ezxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin; pattern: pattern solid, fore_color light_turquoise')
        style2_1 = ezxf('font: bold off; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
        style2_12 = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
        body_style2 = ezxf('font: bold off; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
        body_style_right = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
            
        book = xlwt.Workbook(encoding='utf8')
        sheet = book.add_sheet('Work Report')
        sheet.portrait=True
        ezxf = xlwt.easyxf
        
        sheet.write(1, 1, u'АСУУДЛЫН ЭМХЭТГЭЛ ТАЙЛАН ', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(3, 1, u'Төсөл : ', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(4, 1, u'Хариуцагч : ', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(5, 1, u'Шалтгаан : ', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(6, 1, u'Пайз : ', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        user_search_value = []
        search_value = []
        if data['project_id']:
            projects = self.env['project.project'].search([('id', 'in',data['project_id'])])
            col = 2
            for i in projects:
                sheet.write(3, col, u'%s'%i.name, ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
                col += 1
            search_value.append(('project_id','in',projects.ids))
            
        if data['user_id']:
            users = self.env['res.users'].search([('id', 'in',data['user_id'])])
            col = 2
            for i in users:
                sheet.write(4, col, u'%s'%i.name, ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
                col += 1
            search_value.append(('user_id','in',users.ids))
            user_search_value.append(('id','in',users.ids))
        else :
            sheet.write(4, 2, u'Бүгд', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        
        if data['reason_id']:
            reasons = self.env['task.deadline.reason'].search([('id', 'in',data['reason_id'])])
            col = 2
            for i in reasons:
                sheet.write(5, col, u'%s'%i.name, ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
                col += 1
            search_value.append(('reason_id','in',reasons.ids))
        else :
            sheet.write(5, 2, u'Бүгд', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        
        if data['tag_ids']:
            tags = self.env['project.tags'].search([('id', 'in',data['tag_ids'])])
            col = 2
            for i in tags:
                sheet.write(6, col, u'%s'%i.name, ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
                col += 1
            search_value.append(('tag_ids','in',tags.ids))
        else :
            sheet.write(6, 2, u'Бүгд', ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        
        row = 10
        sheet.write_merge(row,row, 0, 1,u'Асуудал', style2)
        sheet.row(row).height = 500
        sheet.col(0).width = 4000
        sheet.col(1).width = 30000
        sheet.write(row, 2,u'Төсөл', style2)
        sheet.col(2).width = 3000
        sheet.write(row, 3,u'Гэрээ', style2)
        sheet.col(3).width = 3000
        sheet.write(row, 4,u'Дуусах хугацаа', style2)
        sheet.col(4).width = 3000
        sheet.write(row, 5,u'Харилцагч', style2)
        sheet.col(5).width = 4000
        sheet.write(row, 6,u'Пайзууд', style2)
        sheet.col(6).width = 4000
        sheet.write(row, 7,u'Шалтгаан', style2)
        sheet.col(7).width = 3000
        
        result = self.env['project.issue'].sudo().search(search_value, order='id')
        
        user_list = []
        for rs in result:
            if rs.user_id.id not in user_list:
                user_list.append(rs.user_id.id)
        if not data['user_id']:
            user_search_value.append(('id','in',user_list))
        users = self.env['res.users'].sudo().search(user_search_value, order='id')
        row += 1
        col += 1
        if result:
            for user in users:
                sheet.write(row, 0,u'Хариуцагч', style2)
                sheet.write(row, 1,user.name, style2)
                row += 1
                count = 1
                for data in result:
                    space = ', '
                    names = []
                    if data.user_id.id == user.id:
                        sheet.write(row,0,str(count), style2_1)
                        sheet.write(row,1,data.name, style2_12)
                        sheet.write(row,2,data.project_id.name, style2_1)
                        if data.contract_id:
                            sheet.write(row,3,data.contract_id.name, style2_1)
                        else:
                            sheet.write(row,3,'', style2_1)
                        if data.date_deadline:
                            sheet.write(row,4,data.date_deadline, style2_1)
                        else:
                            sheet.write(row,4,'', style2_1)
                        if data.partner_id:
                            sheet.write(row,5,data.partner_id.name, style2_1)
                        else:
                            sheet.write(row,5,'', style2_1)
                        if data.tag_ids:
                            for tag in data.tag_ids:
                                names.append(tag.name)
                            sheet.write(row,6,space.join(names), style2_1)
                        else:
                            sheet.write(row,6,'', style2_1)
                        if data.reason_id:
                            sheet.write(row,7,data.reason_id.name, style2_1)
                        else: 
                            sheet.write(row,7,'', style2_1)
                        count += 1
                        row += 1
        row +=3
        sheet.write_merge(row,row, 1, 4,u'Тайлан хэвлэсэн: ................... /%s/'%(employee_id.name), ezxf('font: bold on;align:wrap off,vert centre,horiz left;'))
        return {'data':book}