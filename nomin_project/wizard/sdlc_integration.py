# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
import requests
import json
from odoo.addons.l10n_mn_report_base.report_helper import verbose_numeric, comma_me, convert_curr
import xlsxwriter
from io import BytesIO
import base64
from operator import itemgetter
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta
class SdlcIntegration(models.TransientModel):
    _name = 'sdlc.integration'
    _description = 'OPEN project integration'
    
    def _get_is_unauthorized(self):
        if not self.env.user.sdlc_config:
            return False
        return True

    def _get_token(self):
        if self.env.user.sdlc_config:
            return self.env.user.sdlc_config

    date_from = fields.Date(string='Эхлэх огноо', required=True)
    date_to = fields.Date(string='Дуусах огноо', required=True, default=fields.Date.context_today)
    is_unauthorized = fields.Boolean(string='Is unauthorized', default=lambda self: self._get_is_unauthorized())
    is_unauthorized_error = fields.Boolean(string='Is unauthorized error', default=False)
    access_token = fields.Char(string='SDLC access token', default=lambda self: self._get_token())
    
    
    type = fields.Selection([('update','OdooID шинэчлэх'),('detail','Дэлгэрэнгүй'),('summary','Хураангуй')],string="Төрөл",default="update")

    def set_access_token(self):
        if not self.is_unauthorized:
            self.env.user.write({'sdlc_config':self.access_token})

    def is_authorized(self, request):
        if request.status_code == 401:
            self.is_unauthorized = False
            self.is_unauthorized_error = True
            self.access_token = ''
            return False 
        return True

    @api.multi
    def action_update_sdlc(self):
        self.set_access_token()
        headers = {
            # 'Authorization': 'Basic %s' % (self.access_token)
        }

        headers2 = {
            'Content-Type': 'application/json',	
            # 'Authorization': 'Basic %s' % (self.access_token)
        }    
        
        date_from = str(self.date_from)+'T00:00:00Z'
        date_to = str(self.date_to)+'T00:00:00Z'        
        offset=1
        check_repeats=[]
        while True:
            url='http://sdlc.nomin.net/api/v3/work_packages?pageSize=1000&&offset=%s&filters=[{"createdAt": { "operator": "<>d", "values": ["%s","%s"] }}]'%(offset,date_from,date_to)
            r = requests.get(url, headers = headers2, auth=('apikey', self.access_token))
            if not self.is_authorized(r):
                return { 'type' : 'ir.actions.do_nothing'} 
            stories = r.json()['_embedded']['elements']
            if len(stories) == 0: break
            offset = offset + 1
            for story in stories:   
                if 'customField1' in story:
                    id = story['id']
                    if id not in check_repeats:
                        check_repeats.append(id)
                        custom_field_1 = story['customField1']
                        _story = requests.get(url='http://sdlc.nomin.net/api/v3/work_packages/' + str(id), headers = headers, auth=('apikey', self.access_token))
                        _story_json = _story.json()
                        if '_links' not in _story_json: continue
                        if 'children' not in _story_json['_links']: continue
                        children = _story_json['_links']['children']
                        for child_url in children:                    
                            child_id = child_url['href'].split('/')[-1]
                            _child = requests.get(url='http://sdlc.nomin.net/api/v3/work_packages/' + str(child_id) + '', headers = headers, auth=('apikey', self.access_token))
                            lock_version = _child.json()['lockVersion']
                            body = {
                            "lockVersion": lock_version,
                            "customField1": custom_field_1
                            }
                            if not _child.json()['startDate'] and story['startDate']:
                                body.update({'startDate':story['startDate']})
                            if not _child.json()['dueDate'] and story['dueDate']:
                                body.update({'dueDate':story['dueDate']})
                            
                            _child2 = requests.patch(url='http://sdlc.nomin.net/api/v3/work_packages/' + str(child_id) + '', headers = headers2, data = json.dumps(body))
        return {'type': 'ir.actions.act_window_close'}
    
    @api.multi
    def export_report(self):
        self.set_access_token()
        headers = {
            # 'Authorization': 'Basic %s' % (self.access_token)
        }

        headers2 = {
            'Content-Type': 'application/json',	
            # 'Authorization': 'Basic %s' % (self.access_token)
        }    
        date_from = datetime.strptime(self.date_from,'%Y-%m-%d')
        date_to = datetime.strptime(self.date_to,'%Y-%m-%d')
        account_seasons={}
        while date_from <= date_to:
            date = date_from.strftime('%Y-%m-%d')
            
            year = date.split('-')[0]
            month = year+'/'+date.split('-')[1]
                        
            if month not in account_seasons:
                account_seasons[month]={
                    'year':'',
                    'month':''
                }
            account_seasons[month]['year']=year
            account_seasons[month]['month']=month
            date_from = date_from +relativedelta(months=1)


        date_from = str(self.date_from)+'T00:00:00Z'
        date_to = str(self.date_to)+'T00:00:00Z'        
        offset=1
        
        dict_stories={}
        dict_performances={}
        dic_logs = []
        check_repeated_log = {}
        while True:
            if self.type=='detail':
                url='http://sdlc.nomin.net/api/v3/work_packages?pageSize=1000&offset=%s&filters=[{"startDate": { "operator": "<>d", "values": ["%s","%s"] },"endDate": { "operator": "<>d", "values": ["%s","%s"] }}]'%(offset,date_from,date_to,date_from,date_to)
                r = requests.get(url, headers = headers2, auth=('apikey', self.access_token))
                if not self.is_authorized(r):
                    return { 'type' : 'ir.actions.do_nothing'}   
                stories = r.json()['_embedded']['elements']
                if len(stories) == 0: break
                offset = offset + 1
                for story in stories:                       
                    group = story['_links']['project']['title']
                    if 'SAP Project Team'!=group:
                        if group not in dict_stories:
                            dict_stories[group] = {
                                'team':'Тодорхойгүй',
                                'user_stories':{},
                            }
                        dict_stories[group]['team']=group
                        group1 = story['_links']['parent']['href']
                        if group1 not in dict_stories[group]['user_stories']:
                            dict_stories[group]['user_stories'][group1]={
                                'parent':'Тодорхойгүй',
                                'title':'Тодорхойгүй',
                                'users':{},
                            }
                        dict_stories[group]['user_stories'][group1]['title'] = story['_links']['parent']['title']
                        dict_stories[group]['user_stories'][group1]['parent'] = group1
                        
                        if story['_links']['parent']['href']:
                            package_url='http://sdlc.nomin.net/'+story['_links']['parent']['href']
                            r = requests.get(package_url, headers = headers2, auth=('apikey', self.access_token))
                            
                            group2 = r.json()['_links']['assignee']['title'] if 'title' in r.json()['_links']['assignee'] else 'Тодорхойгүй'
                        elif 'title' in story['_links']['assignee']:
                            group2 = story['_links']['assignee']['title'] if 'title' in story['_links']['assignee'] else 'Тодорхойгүй'
                        else:
                            group2 = 'Тодорхойгүй'
                        if group2 not in dict_stories[group]['user_stories'][group1]['users']:
                            dict_stories[group]['user_stories'][group1]['users'][group2]={
                                'assignee':'Тодорхойгүй',
                                'work_packages':{}
                            }
                        
                        dict_stories[group]['user_stories'][group1]['users'][group2]['assignee'] = group2
                        group3 = story['id']
                        
                        if group3 not in dict_stories[group]['user_stories'][group1]['users'][group2]['work_packages']:
                            dict_stories[group]['user_stories'][group1]['users'][group2]['work_packages'][group3]={
                                'title':'Тодорхойгүй',
                                'estimate_time':0,            
                                'odoo_id':'',
                                'package_id':'',
                                'users':{},
                                'assignee': 'Тодорхойгүй',
                            }
                        spent_time = 0
                        log_offset = 1
                        customField1 = story['customField1'] if 'customField1' in story else 'Тодорхойгүй'
                        while True:
                            if self.type=='detail':
                                url='http://sdlc.nomin.net/api/v3/time_entries?pageSize=1000&&offset=%s&filters=[{"workPackage":{"operator": "=", "values":["%s"]}},{"spentOn": { "operator": "<>d", "values": ["%s","%s"] }}]'%(log_offset,group3,date_from,date_to)
                            else:
                                if story['_links']['parent']['href']:
                                    package_url='http://sdlc.nomin.net/'+story['_links']['parent']['href']
                                    r = requests.get(package_url, headers = headers2, auth=('apikey', self.access_token))
                                    if 'children' in r.json()['_links']:
                                        value= ""
                                        for child in r.json()['_links']['children']:
                                            value=value+child['href'].split('/')[-1]+","
                                        value=value[:-1]
                                        url='http://sdlc.nomin.net/api/v3/time_entries?pageSize=1000&&offset=%s&filters=[{"workPackage":{"operator": "=", "values":['%(log_offset)+value+']}},{"spentOn": { "operator": "<>d", "values": ["%s","%s"] }}]'%('2019-01-01T00:00:00Z',date_to)
                                    else:
                                        url='http://sdlc.nomin.net/api/v3/time_entries?pageSize=1000&&offset=%s&filters=[{"workPackage":{"operator": "=", "values":["%s"]}},{"spentOn": { "operator": "<>d", "values": ["%s","%s"] }}]'%(log_offset,group3,'2019-01-01T00:00:00Z',date_to)
                                else:
                                    url='http://sdlc.nomin.net/api/v3/time_entries?pageSize=1000&&offset=%s&filters=[{"workPackage":{"operator": "=", "values":["%s"]}},{"spentOn": { "operator": "<>d", "values": ["%s","%s"] }}]'%(log_offset,group3,'2019-01-01T00:00:00Z',date_to)
                            
                            r = requests.get(url, headers = headers2, auth=('apikey', self.access_token))             
                            logtimes = r.json()['_embedded']['elements']
                            if len(logtimes) == 0: break
                            log_offset +=1
                            
                            if customField1 not in dict_performances:
                                dict_performances[customField1]={
                                    'users':{},
                                    'odoo_id':customField1,
                                }
                            
                            for log in logtimes:
                                group5= log['_links']['workPackage']['href'] 
                                if group5 not in check_repeated_log:
                                    check_repeated_log[group5]={
                                        'users':{},
                                    }
                                group6 =log['_links']['user']['title']
                                if group6 not in check_repeated_log[group5]['users']:
                                    check_repeated_log[group5]['users'][group6]={
                                        'user':'',
                                        'create_dates':[]
                                    }
                                check_repeated_log[group5]['users'][group6]['user']=group6
                                group7 = log['createdAt']
                                if group7 not in check_repeated_log[group5]['users'][group6]['create_dates']:
                                    check_repeated_log[group5]['users'][group6]['create_dates'].append(group7)
                                    if group6 not in dict_stories[group]['user_stories'][group1]['users'][group2]['work_packages'][group3]['users']:
                                        dict_stories[group]['user_stories'][group1]['users'][group2]['work_packages'][group3]['users'][group6]={
                                            'user':'Тодорхойгүй',
                                            'spent_time':0,
                                        }
                                    dict_stories[group]['user_stories'][group1]['users'][group2]['work_packages'][group3]['users'][group6]['user'] = group6
                                    spent_time=self.time_convert(log['hours'])
                                    dict_stories[group]['user_stories'][group1]['users'][group2]['work_packages'][group3]['users'][group6]['spent_time'] += spent_time
                                    if group6 not in dict_performances[customField1]['users']:
                                        dict_performances[customField1]['users'][group6]={
                                            'user':'',
                                            'months':{},
                                        }
                                    dict_performances[customField1]['users'][group6]['user']=group6
                                    month = log['spentOn'].split('-')[0]+'/'+log['spentOn'].split('-')[1]
                                    if month not in account_seasons:
                                        month = 'Өмнөх',
                                    if month not in dict_performances[customField1]['users'][group6]['months']:
                                        dict_performances[customField1]['users'][group6]['months'][month]={
                                            'month':'',
                                            'total_spent':0,
                                        }
                                    dict_performances[customField1]['users'][group6]['months'][month]['month']=month 
                                    dict_performances[customField1]['users'][group6]['months'][month]['total_spent']+=spent_time 
                        estimate_time = self.time_convert(story['estimatedTime'])
                        dict_stories[group]['user_stories'][group1]['users'][group2]['work_packages'][group3]['title'] = story['subject']
                        dict_stories[group]['user_stories'][group1]['users'][group2]['work_packages'][group3]['package_id'] = group3            
                        dict_stories[group]['user_stories'][group1]['users'][group2]['work_packages'][group3]['estimate_time'] = estimate_time
                        dict_stories[group]['user_stories'][group1]['users'][group2]['work_packages'][group3]['odoo_id'] = customField1
                        if story['_links']['assignee']['href']:
                            dict_stories[group]['user_stories'][group1]['users'][group2]['work_packages'][group3]['assignee'] = story['_links']['assignee']['title']
            elif self.type=='summary':
                    
                url='http://sdlc.nomin.net/api/v3/time_entries?pageSize=1000&&offset=%s&filters=[{"spentOn": { "operator": "<>d", "values": ["%s","%s"] }}]'%(offset,date_from,date_to)
                r = requests.get(url, headers = headers2, auth=('apikey', self.access_token))
                if not self.is_authorized(r):
                    return { 'type' : 'ir.actions.do_nothing'}     
                stories = r.json()['_embedded']['elements']
                if len(stories) == 0: break
                offset = offset + 1
                for story in stories:      
                    spent_time = 0
                    customField1 = 'Тодорхойгүй'
                    group= story['_links']['workPackage']['href'] 
                    if group not in check_repeated_log:
                        check_repeated_log[group]={
                            'users':{},
                        }
                        if story['_links']['workPackage']['href']:
                            package_url='http://sdlc.nomin.net/'+story['_links']['workPackage']['href']                            
                            r = requests.get(package_url, headers = headers2, auth=('apikey', self.access_token))
                            package = r.json()
                            customField1 =package['customField1'] if 'customField1' in package else 'Тодорхойгүй'
                            group3 = package["id"]
                            log_offset=1
                            while True:
                                if package['_links']['parent']['href'] and package['_links']['parent']['href'] not in check_repeated_log:
                                    package_url='http://sdlc.nomin.net/'+package['_links']['parent']['href']
                                    if package['_links']['parent']['href'] not in check_repeated_log:
                                        check_repeated_log[package['_links']['parent']['href']]={
                                        'users':{},
                                    }
                                    r = requests.get(package_url, headers = headers2, auth=('apikey', self.access_token))
                                    value= package['_links']['parent']['href'].split('/')[-1]
                                    if 'children' in r.json()['_links']:
                                        for child in r.json()['_links']['children']:
                                            if child['href'] not in check_repeated_log:
                                                check_repeated_log[child['href']]={
                                                'users':{},
                                            }
                                            value=value+","+child['href'].split('/')[-1]
                                        # value=value[:-1]
                                    url='http://sdlc.nomin.net/api/v3/time_entries?pageSize=1000&&offset=%s&filters=[{"workPackage":{"operator": "=", "values":['%(log_offset)+value+']}},{"spentOn": { "operator": "<>d", "values": ["%s","%s"] }}]'%('2019-01-01T00:00:00Z',date_to)
                                    # else:
                                    #     url='http://sdlc.nomin.net/api/v3/time_entries?pageSize=1000&&offset=%s&filters=[{"workPackage":{"operator": "=", "values":["%s"]}},{"spentOn": { "operator": "<>d", "values": ["%s","%s"] }}]'%(log_offset,group3,'2019-01-01T00:00:00Z',date_to)
                                else:
                                    url='http://sdlc.nomin.net/api/v3/time_entries?pageSize=1000&&offset=%s&filters=[{"workPackage":{"operator": "=", "values":["%s"]}},{"spentOn": { "operator": "<>d", "values": ["%s","%s"] }}]'%(log_offset,group3,'2019-01-01T00:00:00Z',date_to)
                                
                                r = requests.get(url, headers = headers2, auth=('apikey', self.access_token))                
                                pageSize = r.json()['pageSize']
                                pageCount = r.json()['count']
                                logtimes = r.json()['_embedded']['elements']
                                if len(logtimes) == 0: break
                                log_offset +=1
                                if customField1 not in dict_performances:
                                    dict_performances[customField1]={
                                        'users':{},
                                        'odoo_id':customField1,
                                    }
                                for log in logtimes:
                                    
                                    group5= log['_links']['workPackage']['href'] 
                                    if group5 not in check_repeated_log:
                                                check_repeated_log[group5]={
                                                    'users':{},
                                                }
                                    group6 =log['_links']['user']['title']
                                    if group6 not in check_repeated_log[group5]['users']:
                                                check_repeated_log[group5]['users'][group6]={
                                                    'user':'',
                                                    'create_dates':[]
                                                }
                                    check_repeated_log[group5]['users'][group6]['user']=group6
                                    group7 = log['createdAt']
                                    if group7 not in check_repeated_log[group5]['users'][group6]['create_dates']:
                                                check_repeated_log[group5]['users'][group6]['create_dates'].append(group7)
                                                
                                    if group6 not in dict_performances[customField1]['users']:
                                        dict_performances[customField1]['users'][group6]={
                                                        'user':'',
                                                        'months':{},
                                                    }
                                    dict_performances[customField1]['users'][group6]['user']=group6
                                    month = log['spentOn'].split('-')[0]+'/'+log['spentOn'].split('-')[1]
                                    if month not in account_seasons:
                                        month = 'Өмнөх',
                                    if month not in dict_performances[customField1]['users'][group6]['months']:
                                        dict_performances[customField1]['users'][group6]['months'][month]={
                                            'month':'',
                                            'total_spent':0,
                                        }
                                    spent_time=self.time_convert(log['hours'])
                                    dict_performances[customField1]['users'][group6]['months'][month]['month']=month 
                                    dict_performances[customField1]['users'][group6]['months'][month]['total_spent']+=spent_time 
                                if pageCount!= pageSize: break

                        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        if self.type=='detail':
            file_name = 'Төлөвлөгөө гүйцэтгэлийн тайлан'
        else:
            file_name = 'Хүн цагийн гүйцэтгэл'
        header = workbook.add_format({'border':1,'fg_color':'#b0e2ff','align':'justify','valign':'vjustify','text_wrap':100,'pattern':0})

        title = workbook.add_format({
		'border': 0,
		'bold': 0,
		'align': 'center',
		'valign': 'vcenter',
		'text_wrap': 'on',
		'font_size':10,
		'font_name': 'Arial',
		})


        header_color = workbook.add_format({
        'border': 1,
        'bold': 0,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 'on',
        'font_size':8,
        'bg_color':'#bdd7ee',
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
        # 'num_format': '#,##0.00'
        })
        cell_float_format_left1 = workbook.add_format({
        'border': 0,
        'bold': 0,
        'align': 'left',
        'valign': 'vcenter',
        'text_wrap': 'on',
        'font_size':10,
        # 'bg_color':'#40E0D0',
        'font_name': 'Arial',
        # 'num_format': '#,##0.00'
        })
        cell_float_format_right = workbook.add_format({
        'border': 1,
        'bold': 0,
        'align': 'right',
        'valign': 'vcenter',
        'text_wrap': 'on',
        'font_size':10,
        'font_name': 'Arial',
        # 'bg_color':'#40E0D0',
        'num_format': '#,##0.00'
        })
        cell_float_format_right1 = workbook.add_format({
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
        'bold': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 'on',
        'font_size':10,
        #'bg_color':'#ADBFF7',
        'font_name': 'Arial',
        'num_format': '#,##0.00'
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
        row = 3
        # sheet.fit_to_pages(1, 1)
        sheet.merge_range(2,2,2,6, u'Шүүлтүүр:'+self.date_from+' '+self.date_to,cell_float_format_left )  
        if self.type=='detail':
            sheet.write(row,0, u'№',header_color )   
            sheet.write(row,1, u'Төслийн менежер',header_color )   
            sheet.write(row,2, u'Ажилтан',header_color )   
            sheet.write(row,3, u'Төсөл',header_color )   
            sheet.write(row,4, u'Odoo ID',header_color )   
            sheet.write(row,5, u'Хэрэглэгчийн түүх',header_color )   
            sheet.write(row,6, u'Package ID',header_color )   
            sheet.write(row,7, u'Work Packаge',header_color )   
            sheet.write(row,8, u'Төлөвлөсөн цаг/Estimated time',header_color )   
            sheet.write(row,9, u'Гүйцэтгэсэн цаг/Spent time',header_color )  
            
            sheet.set_row(row, 30)
            sheet.set_column(0,0,5)
            sheet.set_column(1,10,15)
            sheet.set_column(3,3,50)
            sheet.set_column(7,7,50)
            if dict_stories:
                count =1
                row+=1
                for team in sorted(dict_stories.values(), key=itemgetter('team')):
                    for story in sorted(team['user_stories'].values(), key=itemgetter('parent')):
                        for assignee in sorted(story['users'].values(), key=itemgetter('assignee')):
                            for work in sorted(assignee['work_packages'].values(), key=itemgetter('title')):
                                if len(work['users'])  == 0:
                                    sheet.write(row, 0 , count, cell_float_format_left)
                                    sheet.write(row, 1 , assignee['assignee'], cell_float_format_right)
                                    sheet.write(row, 2 , work['assignee'], cell_float_format_right)
                                    sheet.write(row, 3 , team['team'], cell_float_format_right)
                                    sheet.write(row, 4 , work['odoo_id'], cell_float_format_right)
                                    sheet.write(row, 5 , story['title'], cell_float_format_right)
                                    sheet.write(row, 6 , work['package_id'], cell_float_format_left)
                                    sheet.write(row, 7 , work['title'], cell_float_format_right)
                                    sheet.write(row, 8 , work['estimate_time'], cell_float_format_right)
                                    sheet.write(row, 9 , 0, cell_float_format_right)
                                    count+=1
                                    row+=1

                                for user in sorted(work['users'].values(), key=itemgetter('user')):
                                    sheet.write(row, 0 , count, cell_float_format_left)
                                    sheet.write(row, 1 , assignee['assignee'], cell_float_format_right)
                                    sheet.write(row, 2 , user['user'], cell_float_format_right)
                                    sheet.write(row, 3 , team['team'], cell_float_format_right)
                                    sheet.write(row, 4 , work['odoo_id'], cell_float_format_right)
                                    sheet.write(row, 5 , story['title'], cell_float_format_right)
                                    sheet.write(row, 6 , work['package_id'], cell_float_format_left)
                                    sheet.write(row, 7 , work['title'], cell_float_format_right)
                                    sheet.write(row, 8 , work['estimate_time'], cell_float_format_right)
                                    sheet.write(row, 9 , user['spent_time'], cell_float_format_right)
                                    count+=1
                                    row+=1
        else:
            col=3
            sheet.set_row(row, 30)
            sheet.set_column(0,0,5)
            sheet.set_column(1,10,15)
            dict_columns = {}
            sheet.write(row,0, u'№',header_color )   
            sheet.write(row,1, u'Ажилтан',header_color )   
            sheet.write(row,2, u'Өмнөх',header_color )  
            
            for season in sorted(account_seasons.values(), key=itemgetter('month')):
                sheet.write(row,col, season['month'],header_color ) 
                if season['month'] not in dict_columns:
                    dict_columns.update({season['month']:col})
                col+=1 
            row+=1
            last_col = col -1              
            if dict_performances:
                count=1
                for custom in sorted(dict_performances.values(), key=itemgetter('odoo_id')):
                    sheet.write(row, 0 , count, cell_float_format_left)
                    
                    page=self.env['order.page'].sudo().search([('name','=',custom['odoo_id'])],limit =1)
                    if page and page.cost_info:
                        odoo_desc =""
                        for cost in page.cost_info:
                            odoo_desc =odoo_desc+ cost.position_name.name+" "+ str(cost.time_info)+" "
                        odoo_desc= "Захиалгын дугаар:"+custom['odoo_id']+" - "+page.order_name+" "+odoo_desc
                        sheet.merge_range(row, 1 ,row,last_col, odoo_desc, cell_float_format_left)
                    else:
                        sheet.merge_range(row, 1 ,row,last_col, custom['odoo_id'], cell_float_format_left)
                    sheet.set_row(row, 30)
                    
                    row+=1
                    for user in sorted(custom['users'].values(), key=itemgetter('user')):
                        sheet.write(row, 1 , user['user'], cell_float_format_left1)
                        for month in sorted(user['months'].values(), key=itemgetter('month')):
                            if month['month'] not in account_seasons:
                                sheet.write(row, 2 , month['total_spent'], cell_float_format_right1)
                            else:
                                if month['month'] in dict_columns:
                                    sheet.write(row, dict_columns[month['month']] , month['total_spent'], cell_float_format_right1)
                        row+=1
                    count+=1
        workbook.close()
        out = base64.encodestring(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data':out,'name':file_name + '.xlsx'})

        return {
		'name': 'Export Report',
		'view_type':'form',
		'view_mode':'form',
		'res_model':'report.excel.output',
		'res_id':excel_id.id,
		'view_id':False,
		#'context':self._context,
		'type': 'ir.actions.act_window',
		'target':'new',
		'nodestroy': True,
		}


    def time_convert(self, spent_time):
        spent_day = 0
        spent_hour =0
        spent_minute = 0
        spent_second = 0        
        if spent_time:            
            spent_duration = re.findall(r'\d+',spent_time)
            spent_times = re.findall(r'\D+',spent_time)
            index = 0
            if 'D' in spent_times or 'DT' in spent_times:
                spent_day = float(spent_duration[index])*24                
                index+=1
            if 'H' in spent_times:
                spent_hour = float(spent_duration[index])
                index+=1
            if 'M' in spent_times:                
                spent_minute = round(float(spent_duration[index])/60,2)
                index+=1
                
            if 'S' in spent_times:
                spent_second = round(float(spent_duration[index])/60,2)
                index+=1
        return spent_day+spent_hour+spent_minute+spent_second