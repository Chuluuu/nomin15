# -*- coding: utf-8 -*-

import time
import datetime
import odoo
from odoo import api, fields, models, _, modules
from odoo.tools.translate import _
from operator import itemgetter
import logging
_logger = logging.getLogger(__name__)


    
class ReportTenderRequest(models.AbstractModel):
    '''Тендерийн хүсэлт
    '''
    _name = 'report.nomin_tender.tender_request_report'
    
    
    def render_html(self, data=None):
        #if context is None:
        #    context = {}
        report_obj = self.env['report']
        tender_obj = self.env['tender.tender']
        report = report_obj._get_report_from_name('nomin_tender.tender_request_report')
        #if data and not ids:
        #    ids = data['ids']
        tenders = tender_obj.browse(self._ids)
        lines = []
        employees = []
        confirmed_date = False
        tender_ceo = False
        tender_secretary = False
        document_name = u"Тендер зарлуулах хүсэлт"
        index = 1 
        for tender in tenders:
            document_name = " %s"%(tender.desc_name)
            lines.append({'index':1.1, 'value':u'<b>Захиалагч нь: </b>%s'%(tender.sector_id.name if tender.sector_id else '')})
            lines.append({'index':1.2, 'value':u'<b>Ажлын буюу гэрээний товч нэр, тодорхойлолт:</b> \n %s'%(tender.desc_name if tender.desc_name else '')})
            lines.append({'index':1.3, 'value':u'<b>Энэхүү тендер шалгаруулалт нь дараах нэр, дугаар бүхий багцуудаас бүрдэнэ:</b> %s'%(tender.description)})
            lines.append({'index':2.1, 'value':u'<b>Ажлын даалгавар:</b> %s; %s'%(tender.work_task_state if tender.work_task_state else u'', tender.work_task_verifier if tender.work_task_verifier else u'')})
            lines.append({'index':2.2, 'value':u'<b>Хяналтын төсөв:</b> %s; %s'%(tender.control_budget_state if tender.control_budget_state else u'', tender.control_budget_verifier if tender.control_budget_verifier else u'')})
            lines.append({'index':2.3, 'value':u'<b>Ажлын зураг:</b> %s; %s'%(tender.work_graph_state if tender.work_graph_state else u'', tender.work_graph_verifier if tender.work_graph_verifier else u'')})
            lines.append({'index':3.1, 'value':u'<b>Уг ажлыг гүйцэтгэхэд тусгай зөвшөөрөл зайлшгүй шаардлагатай эсэх:</b> %s'%(u'Тийм' if tender.license else u'Үгүй')})
            warranty=''
            is_warranty=u'Үгүй'
            if tender.is_warranty:
                is_warranty=u'Тийм'
                warranty=u', Баталгаат хугацаа: %s сар'%(tender.warranty)
            lines.append({'index':3.2, 'value':u'<b>Уг ажлыг гүйцэтгэхэд баталгаат хугацаа шаардлагатай эсэх:</b> %s %s'%(is_warranty, warranty)})
            lines.append({'index':3.3, 'value':u'<b>Тоног төхөөрөмж, машин механизмын нэр төрөл, хүчин чадлын жагсаалт шаардлагатай эсэх:</b> %s'%(u'Тийм' if tender.technical_requirement else u'Үгүй')})
            lines.append({'index':3.4, 'value':u'<b>Ижил төстэй ажил гэрээгээр гүйцэтгэсэн туршлагын талаарх мэдээлэл ирүүлэх жилийн тоо:</b> %s жил'%(tender.work_experience_info)})
            lines.append({'index':3.5, 'value':u'<b>Хувилбарт тендер ирүүлэхийг</b> %s'%(u'Зөвшөөрнө' if tender.is_alternative else u'Зөвшөөрөхгүй')})
            
            is_performance=u'Гүйцэтгэлийн баталгаа шаардлагагүй;'
            performance_amount=u''
            if tender.is_performance:
                is_performance=u'Гүйцэтгэлийн баталгаа шаардлагатай;'
                performance_amount=u'Гүйцэтгэлийн  баталгааны хэмжээ буюу мөнгө дүн нь: [Үнийн дүнгийн %s хувь] '%(tender.performance_amount)
            lines.append({'index':4.1, 'value':u'<b>%s</b> \n %s'%(is_performance, performance_amount)})
            date_open_deadline = u''
            date_end = u''
            if tender.date_open_deadline:
                date_open_deadline = datetime.datetime.strptime(tender.date_open_deadline, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
            if tender.date_end:
                date_end = datetime.datetime.strptime(tender.date_end, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
            lines.append({'index':4.2, 'value':u'<b>Тендер зарлах эцсийн хугацаа нь:</b> %s'%(date_open_deadline)})
            lines.append({'index':4.3, 'value':u'<b>Тендер хүлээн авах эцсийн хугацаа нь:</b> %s'%(date_end)})
            lines.append({'index':4.4, 'value':u'<b>Ажил хүлээлгэн өгөх хугацаа нь:</b> %s'%(tender.ordering_date)})
            lines.append({'index':4.5, 'value':u'<b>Дотоодын давуу эрх тооцох, эсэх:</b> %s'%(u'Тийм' if tender.is_domestic else u'Үгүй')})
            lines.append({'index':4.6, 'value':u'<b>Тусгай шаардлага:</b> \n %s'%(tender.special_require)})
            
            for emp in tender.confirmed_member_ids:    
                if emp.confirmed_date>confirmed_date:
                    confdate = emp.confirmed_date
                    confirmed_date = datetime.datetime.strptime(confdate, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
                employees.append(emp.employee_id)
            
        
        manager_group_id = self.env['ir.model.data']._xmlid_to_res_id('nomin_tender.group_tender_manager')
        _logger.info(u'Тендерийн хорооны дарга групп =  %s', manager_group_id)
        if manager_group_id:
            #user_ids=self.pool['res.users'].search(cr, 1, [('groups_id','=',manager_group_id[1])])
            user_ids = self.env['res.users'].sudo().search([('groups_id','in',manager_group_id)])
            _logger.info(u'Тендерийн хорооны дарга хэрэглэгч   %s', user_ids)
            if user_ids:
                #manager_empl = self.pool['hr.employee'].browse(cr, uid, self.pool['hr.employee'].search(cr, uid, [('user_id','=',user_ids[0])]))
                manager_empl = self.env['hr.employee'].search([('user_id','=',user_ids.ids)])
                _logger.info(u'Тендерийн хорооны дарга ажилтан %s', manager_empl)
                if manager_empl:
                    tender_ceo = manager_empl[0]
                    _logger.info(u'Тендерийн хорооны дарга %s', tender_ceo)
        
        sec_group_id = self.env['ir.model.data']._xmlid_to_res_id('nomin_tender.group_tender_secretary')
        _logger.info(u'Тендерийн нарийн бичиг групп =  %s', sec_group_id)
        if sec_group_id:
            #user_ids=self.pool['res.users'].search(cr, 1, [('groups_id','=',sec_group_id[1])])
            user_ids = self.env['res.users'].sudo().search([('groups_id','in',sec_group_id)])
            _logger.info(u'Тендерийн нарийн бичиг хэрэглэгч  %s', user_ids) 
            if user_ids:
                #sec_empl = self.pool['hr.employee'].browse(cr, uid, self.pool['hr.employee'].search(cr, uid, [('user_id','=',user_ids[0])]))
                sec_empl = self.env['hr.employee'].search([('user_id','=',user_ids.ids)])
                _logger.info(u'Тендерийн нарийн бичиг ажилтан  %s', sec_empl)
                if sec_empl:
                    tender_secretary = sec_empl[0]
                    _logger.info(u'Тендерийн нарийн бичиг  %s', tender_secretary)
                    
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': tenders,
            'lines': lines,
            'type': 'out',
            'document_name': document_name,
            'employees':employees,
            'confirmed_date':confirmed_date,
            'tender_ceo':tender_ceo,
            'tender_secretary':tender_secretary
        }
        return report_obj.render('nomin_tender.tender_request_report', docargs)
