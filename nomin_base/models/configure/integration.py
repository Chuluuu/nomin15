# # -*- encoding: utf-8 -*-




# from ssl import SSLSocket
# from tokenize import group
# from unittest.result import failfast
# from xmlrpc.client import DateTime

# from defusedxml import DTDForbidden
# from openerp import api, fields, models, _
# from openerp.exceptions import UserError
# from fnmatch import translate
# from openerp.osv import osv
# from pychart.color import steelblue
# from openerp.tools import exception_to_unicode
# # from datetime import datetime, timedelta
# import time
# from datetime import date, datetime, timedelta
# from datetime import timedelta
# from datetime import datetime
# from dateutil.relativedelta import relativedelta



# import logging
# _logger = logging.getLogger(__name__)
# import requests 
# import json

# import socket
# import re
# from lxml import etree
# from requests.auth import HTTPBasicAuth
# import xmlrpclib


# from hashlib import sha1
# import hmac
# import base64
# from datetime import datetime, timedelta

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import socket
import re
from lxml import etree
from requests.auth import HTTPBasicAuth
from odoo import SUPERUSER_ID, models
# from . import openerp.exceptions
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import float_is_zero
from odoo.tools import float_compare, float_round
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, ValidationError


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


class IntegrationConfig(models.Model):
    _name = 'integration.config'
    _description = 'Integration Configure'
    _table = "integration_config"
    #_inherit = ['mail.thread', 'ir.needaction_mixin']
   
    
    name = fields.Char(string='Name', required=True, size=40)
    server_ip = fields.Char(string='Устгах',  size=128)
    from_server_ips = fields.Char(string='Аль серверүүдээс хандах',required=True)
    category = fields.Char(string='Категори', required=True, size=30)
    token_url = fields.Char(string='Token Url', track_visibility='always') 
    url_ids = fields.One2many('proactive.notification', 'config_id',string='Url')
    a1 = fields.Char(string='A1',track_visibility='onchange')
    a2 = fields.Char(string='A2',track_visibility='onchange')
    a3 = fields.Char(string='A3',track_visibility='onchange')
    a4 = fields.Char(string='A4',track_visibility='onchange')
    active = fields.Boolean(string='Идэвхтэй', default=True)
    connection_type = fields.Selection([
            ('basic_post',u'Бейсик одинтикэшнтэй пост'),
            ('bearer_token',u'Bearer token'),
            ('token_post',u'Токентэй пост'),
            ('non_token_post',u'Токенгүй пост'),
            ('non_token_post_without_header',u'non_token_post_without_header'),
            ('manually_created_token_post',u'Гар аргаар үүсгэсэн токентэй пост'),
            ('xml_rpc',u'Xml rpc'),
            ('bunch_connections_for_soap',u'Олон холболттой soap'),
            ('just_url',u'Зүгээр л Url')
        ], 'Холболтын төрөл', required=True,track_visibility='onchange')

    integration_type = fields.Selection([
            ('reply_based', u'Илгээгээд амжилттай хариулт авсан бол дахин дуудахгүй'),
            ('repeat_based',u'Илгээгээд амжилттай хариулт авсан хэдий ч дахин дуудна'),
        ], 'Интеграцын төрөл', required=True,track_visibility='onchange')   
    update_record_count = fields.Integer(string='Update хийх бичлэгийн тоо',default = 4)

   
    def integration_handler(self,object_id): # it's for insertion and update
            
        notification_ids = self.env['proactive.notification'].sudo().search([('model','=',type(object_id).__name__),('integration_data_type','not in',['sync_flag_is_on_object','integration_for_deletion','inbound_integration'])])
        for notification_id in notification_ids:

            if notification_id.python:
                exec(notification_id.python)


    def outbound_integration(self,object_id,records): 
        #_logger.info('Action sync ДАРАГДЛААААААААААА!!!!!!!!!!!%s!!!!     %s'%(type(object_id).__name__,records))
        notification_ids = False
        result_txt = ''
        if type(object_id).__name__ == 'str':
            notification_ids = self.env['proactive.notification'].sudo().search([('code','=',object_id),('integration_data_type','in',['sync_flag_is_on_object'])])
        else:
            notification_ids = self.env['proactive.notification'].sudo().search([('model','=',type(object_id).__name__),('integration_data_type','in',['sync_flag_is_on_object'])])
        
        for notification_id in notification_ids:

            result_txt = notification_id.sync_object_based_items(False,records)
        return result_txt 
            

    def integration_for_deletion(self,object_id):
        #print '=============integration_for_deletion===========self, object_id============', self, object_id 
        notification_ids = self.env['proactive.notification'].sudo().search([('model','=',type(object_id).__name__),('integration_data_type','=','integration_for_deletion')])
        
        result=''
        for notification_id in notification_ids:
            if notification_id.python:
                exec(notification_id.python)
                return result



#     def zangia_ref_tables_for_cvs(self,notification_id):

#             # print '====================ref cvs ==================================   '

#             sApiCode = notification_id.config_id.a2
#             sApiSecret =  notification_id.config_id.a1


#             sUserAgent ='BiznetworkAuth [https://www.biznetwork.mn]'
#             iStamp = (datetime.now() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')

#             sHashStr = sApiCode + ':' + sApiSecret
#             sHashKey = sUserAgent + '|' + iStamp


#             hashed = hmac.new(sHashKey, bytes(sHashStr), sha1).digest()

#             Token = base64.b64encode(hashed)

#             headers = {
#                 'Content-Type': 'application/x-www-form-urlencoded',
#                 }

# # ========================================= ref for school country/location==============================================================
#             body = {'optioncode':'cntr',
#                 'api_code': sApiCode,
#                 'token':Token,
#                 'stamp': iStamp,
#                 }
#             notification_id.inbound_integration('hr.profession',body)
#             state,msg = notification_id.connect(json.dumps(body),False)
#             print  '+++++++ref for school country/location+++++++',state,msg

#             main_dictionary = json.loads(msg)
#             for item in main_dictionary:
#                 # print '===', item,main_dictionary[item].upper()
#                 query="""select id from res_country 
#                     where upper(name) = '%s'"""%(main_dictionary[item].upper())
                    
#                 # print ' qqqqquery ++++++++++++=========================', query
#                 self.env.cr.execute(query)
#                 records = self.env.cr.dictfetchall()
#                 # print 'records---------++++++++++++++++++',records
#                 if records:
#                     # print '===', item,main_dictionary[item].upper()
#                     print ' ++++++++++exist++++++++exist++++++++++__',records[0]['id'],item

#                     query="""update res_country set zangia_id= %s 
#                     where id = '%s'"""%(item,records[0]['id'])
#                     print ' update query =================+++++++++++++++', query
#                     self.env.cr.execute(query)              

#                 else:
#                     print '===empty===========empty===========',item,main_dictionary[item].upper()
#                     query=""" insert into res_country(name , zangia_id)
#                     values ('%s', %s)
#                     """%(main_dictionary[item], item)
#                     print '===insert===========insert===========',query
#                     self.env.cr.execute(query)

# # ==========================school ref for cvs==============================================================================
#             body = {'optioncode':'schl',
#                 'api_code': sApiCode,
#                 'token':Token,
#                 'stamp': iStamp,
#                 }

#             notification_id.inbound_integration('hr.profession',body)
#             state,msg = notification_id.connect(json.dumps(body),False)

#             print  '+++++school ref+++++++++',state,msg
        
#             main_dictionary = json.loads(msg)
#             for item in main_dictionary:
#                 print '===', item,main_dictionary[item].upper()
            
#                 query="""select id from hr_school 
#                     where upper(name) = '%s'"""%(main_dictionary[item].upper())
                    
#                 # print ' qqqqquery ++++++++++++=========================', query
#                 self.env.cr.execute(query)
#                 records = self.env.cr.dictfetchall()
#                 # print 'records---------++++++++++++++++++',records
#                 if records:
#                     print ' ++++++++++exist++++++++exist++++++++++__',records[0]['id'],item

#                     query="""update hr_school set zangia_id= '%s' 
#                     where id = '%s'"""%(item,records[0]['id'])
#                     # print ' update query =================+++++++++++++++', query
#                     self.env.cr.execute(query)              

#                 else:

#                     print '===empty===========empty===========',item,main_dictionary[item].upper()
#                     query=""" insert into hr_school(name , zangia_id)
#                     values ('%s', '%s')
#                     """%(main_dictionary[item],item)
#                     # print '===insert===========insert===========',query
#                     self.env.cr.execute(query)
                        
# # ================================================= ref for language, software and soft skills=======================================================================
#             stype=('tk01', 'tk02', 'tk03')
#             for st in stype:
#                 print 'st +++++++++++++++++', st, 
#                 body = {'optioncode':st,
#                     'api_code': sApiCode,
#                     'token':Token,
#                     'stamp': iStamp,
#                     }
                
#                 stype_id= '3'
#                 if st =='tk01':
#                     stype_id= '1'
#                 elif st== 'tk02':
#                     stype_id = '2'
#                 # print 'body===========================body===========', body
#                 notification_id.inbound_integration('hr.profession',body)
#                 state,msg = notification_id.connect(json.dumps(body),False)

#                 print  '++++++ref for language, software and soft skills++++++++',state,msg
#                 main_dictionary = json.loads(msg)
#                 for item in main_dictionary:
#                     print '===', item,main_dictionary[item].upper()
#                     query="""select id from hr_info_skill 
#                         where upper(name) = '%s'"""%(main_dictionary[item].upper())
                        
#                     # print ' qqqqquery ++++++++++++=========================', query
#                     self.env.cr.execute(query)
#                     records = self.env.cr.dictfetchall()
#                     # print 'records---------++++++++++++++++++',records
#                     if records:

#                         # print '===', item,main_dictionary[item].upper()
#                         print ' ++++++++++exist++++++++exist++++++++++__',records[0]['id'],item

#                         query="""update hr_info_skill set zangia_id= %s, group_zangia_id='%s'
#                         where id = '%s'"""%(item ,stype_id ,records[0]['id'])
#                         print ' update query =================+++++++++++++++', query ,st
#                         self.env.cr.execute(query)              

#                     else:
#                         print '===empty===========empty===========',item,main_dictionary[item].upper()
#                         query=""" insert into hr_info_skill(name , zangia_id, group_zangia_id)
#                         values ('%s', %s, '%s')
#                         """%(main_dictionary[item], item, stype_id)
#                         print '===insert===========insert===========',query, st
#                         self.env.cr.execute(query)

# # ================================================= evaluation for language and software skill /rf02/,/rf03/=======================================================================
#             body = {'optioncode':'rf02',
#                 'api_code': sApiCode,
#                 'token':Token,
#                 'stamp': iStamp,
#                 }
#             notification_id.inbound_integration('hr.profession',body)
#             state,msg = notification_id.connect(json.dumps(body),False)

#             print  '++++++evaluation for language and software skill++++++++',state,msg
# =============================================================zangia_ref_tables_for_notice++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # def zangia_ref_tables_for_notice(self,notification_id):

    #         print '====================++++++++++++++++++++ ==================================   '
    #         sApiCode = notification_id.config_id.a2
    #         sApiSecret =  notification_id.config_id.a1


    #         sUserAgent ='BiznetworkAuth [https://www.biznetwork.mn]'
    #         iStamp = (datetime.now() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')

    #         sHashStr = sApiCode + ':' + sApiSecret
    #         sHashKey = sUserAgent + '|' + iStamp


    #         hashed = hmac.new(sHashKey, bytes(sHashStr), sha1).digest()

    #         Token = base64.b64encode(hashed) 



    #         headers = {
    #             'Content-Type': 'application/x-www-form-urlencoded',
    #             }
    #         #=======================================location==================================================

    #         body = {'optioncode':'lcnm',
    #             'api_code': sApiCode,
    #             'token':Token,
    #             'stamp': iStamp,
    #             }


    #         state,msg = notification_id.connect(json.dumps(body),False)

    #         print  '++++++++++++++',state,msg
        
    #         main_dictionary = json.loads(msg)
    #         for item in main_dictionary:

    #             print '===',item,main_dictionary[item].upper()
    #             query="""select id from hr_employee_location 
    #                     where upper(name) = '%s'"""%(main_dictionary[item].upper())
    #             # body = []

    #             if '&nbs' in main_dictionary[item] and len(main_dictionary[item])>37:

    #                 query = """select id from hr_employee_location 
    #                         where upper(name) = '%s'"""%(main_dictionary[item][37:].upper())
                
    #             self.env.cr.execute(query)
    #             records = self.env.cr.dictfetchall()
    #             # print 'records',records
    #             if records:
    #                 print '===_____________',records[0]['id'],item

    #                 query="""update hr_employee_location set zangia_id=%s 
    #                 where id = %s"""%(item,records[0]['id'])

    #                 self.env.cr.execute(query)


    #         # ==========================================branch=======================================================

    #         body = {'optioncode':'prbr',
    #             'api_code': sApiCode,
    #             'token':Token,
    #             'stamp': iStamp,
    #         }
                
    #         state,msg = notification_id.connect(json.dumps(body),False)

    #         print  '+++++============================bumbayar',state,msg
        
    #         main_dictionary = json.loads(msg)
    #         for item in main_dictionary:
    #             # print '===',item,main_dictionary[item].upper()

    #             if '&nbs' not in main_dictionary[item]:

    #                 query="""insert into hr_types_of_careers (name, zangia_id) values('%s','%s') on conflict (zangia_id)
    #                         do update set name='%s' where hr_types_of_careers.zangia_id='%s' and hr_types_of_careers.name!='%s'"""%(main_dictionary[item],item, main_dictionary[item],item, main_dictionary[item])

    #                 # print '----------------query',query,
    #                 self.env.cr.execute(query)

    #                 # print '///////////////////////////////////////////////////////////////////item-', item

    #                 # ====================================profession=======================================

    #                 body = {'optioncode':'pfs1',
    #                     'branch':item,
    #                     'api_code': sApiCode,
    #                     'token':Token,
    #                     'stamp': iStamp,
    #                     }

    #                 state,msge = notification_id.connect(json.dumps(body),False)
    #                 # print  '+++++++++++++profession++++++++++++++', main_dictionary[item] ,state,msge

    #                 main_dic = json.loads(msge)

    #                 for elem in main_dic:
    #                             # print '===',elem,main_dic[elem].upper()
    #                             # type_id="""select id from hr_types_of_careers where zangia_id='%s'"""%(item)
    #                             # self.env.cr.execute(type_id)
    #                             # result = self.env.cr.dictfetchall()
    #                             # print '===result===',result
                                
    #                             query_for_profession="""insert into hr_profession (name, zangia_id, type_id) select '%s','%s',(select id from hr_types_of_careers where zangia_id='%s') on conflict (zangia_id)
    #                         do update set name='%s' where hr_profession.zangia_id='%s' and hr_profession.name!='%s'"""%(main_dic[elem], elem, item, main_dic[elem],elem, main_dic[elem])

    #                             print '<<<<<<<<<<<<<!=>>>>>>>>>>>',main_dictionary[item], query_for_profession

    #                             self.env.cr.execute(query_for_profession)

# =================================================================================================

    # def zangia_cv_download(self,notification_id):


    #     sApiCode = notification_id.config_id.a2
    #     sApiSecret =  notification_id.config_id.a1


    #     sUserAgent ='BiznetworkAuth [https://www.biznetwork.mn]'
    #     iStamp = (datetime.now() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')

    #     sHashStr = sApiCode + ':' + sApiSecret
    #     sHashKey = sUserAgent + '|' + iStamp


    #     hashed = hmac.new(sHashKey, bytes(sHashStr), sha1).digest()

    #     Token = base64.b64encode(hashed)


    #     headers = {
    #         'Content-Type': 'application/x-www-form-urlencoded',
    #         }

    #     notification_id = self.env['proactive.notification'].sudo().search([('model','=','new.employee.order'),('code','=','zangia_vacancy_notice_sync')])[0]
    #     #print '<<<<<<<<<<<<<<<notification_id_for_ads??????????>>>>>>>', notification_id
    #     for ad in notification_id.line_ids:
    #         print '======================= ad,notification_id.line_ids============', ad, notification_id.line_ids
    #         if not ad.msg:
    #             continue

    #         if 'success' not in json.loads(ad.msg):
    #             continue

    #         body = {'adcode':json.loads(ad.msg)['ad_code'],
    #             'api_code': sApiCode,
    #             'token':Token,
    #             'stamp': iStamp,
    #             }
            
    #         notification_id_for_ads = self.env['proactive.notification'].sudo().search([('model','=','hr.applicant'),('code','=','zangia_cv_sync')])[0]
    #         # print '====================notification_id_for_ads====================', notification_id_for_ads
    #         state,msg = notification_id_for_ads.connect(json.dumps(body),False)

    #         if msg and not msg=='[]':

    #             cvs = json.loads(msg)
    #             print '<<<<<<<<<<<<<<< cv from zangia >>>>>>>', state, msg
    #         else:
    #             continue
            
    #         for item in cvs:
                    
    #             #  ############################## EDUCATION GROUP ############################=================================================== ---->

    #             key_list = cvs[item].keys()
    #             print '\n\n\n\n\n\n ======keys in dict=====',key_list
    #             complete_array=[]
    #             edus= ('level5', 'level5', 'level5', 'special', 'level4', 'level3', 'level1')
    #             edulvl = 'level1'
    #             buff = 7
    #             if 'educations' in key_list:
    #                 edu = cvs[item]['educations']

    #                 for edu_item in edu:
    #                     print ' ============== edu item ===========-------',edu_item
    #                     educs = []
    #                     intg= int(edu_item['degree'])
    #                     if intg < buff:
    #                         edulvl = edus[intg-1]
    #                         print '---------------------------------edulvl-----------------',edulvl, intg
    #                         buff = intg

    #                     degree = ''
    #                     if intg == 1:
    #                         degree = 'bachelor'
    #                     elif intg == 2:
    #                         degree = 'master'
    #                     elif intg == 3:
    #                         degree = 'doctor' 
    #                     is_there_zangia_id = """select id from res_country where zangia_id= %s"""%(edu_item['country'])

    #                     self.env.cr.execute(is_there_zangia_id)
    #                     records = self.env.cr.dictfetchall()
    #                     # print 'records---------++++++++++++++++++',records[0]['id']
                
    #                     print 'start =============end============' ,edu_item['start'], str(edu_item['end'])+'-01-01'
    #                     dictionary={}
    #                     dictionary['school_from_zangia'] = edu_item['school']
    #                     if is_there_zangia_id:
    #                         dictionary['country_id'] = records[0]['id']
    #                     else:
    #                         self.env['integration.config'].sudo().inbound_integration('zangia_ref_tables_for_cvs')
    #                     dictionary['education_level'] = edus[intg-1]
    #                     dictionary['education_degree'] = degree
    #                     dictionary['profession_name']= edu_item['pro']
    #                     if edu_item['start'] != '0000': 
    #                         dictionary['entered_date'] = str(edu_item['start'])+'-01-01'
    #                     else:
    #                         dictionary['entered_date'] = False
    #                     if edu_item ['end'] !='0000':
    #                         dictionary['finished_date'] = str(edu_item['end'])+'-01-01'
    #                     else: 
    #                         dictionary['finished_date'] = False
    #                     dictionary['gpa'] = edu_item['rate']

    #                     dictionary['gpa'] = edu_item['rate']

    #                     educs.append(0)
    #                     educs.append(False) 
    #                     educs.append(dictionary)
    #                     complete_array.append(educs)

    #                 # print ' dictionary and array===================== ' , educs
    #             # print ' complete===================== ' , complete_array

    #             ############################## TRAINING GROUP ############################==================================================== ---->


    #             training_arr=[]
    #             if 'trainings' in key_list:
    #                 trainings = cvs[item]['trainings']
    #                 print 'trainings==============================================', trainings
    #                 for tr_item in trainings:
    #                     trngs=[]
    #                     tr_dict={}
    #                     tr_dict['where_school'] = tr_item['tcname']
    #                     tr_dict['chiglel'] = tr_item['title']
    #                     tr_dict['entered_date'] = tr_item['start']
    #                     tr_dict['resigned_date'] = tr_item['end']
                        
    #                     trngs.append(0)
    #                     trngs.append(False)
    #                     trngs.append(tr_dict)
    #                     training_arr.append(trngs)

    #             #  ############################## EXPERIENCE GROUP ############################================================================== ---->
                


    #             experiences_arr=[]
    #             check=True
    #             if 'experiences' in key_list:
    #                 experiences = cvs[item]['experiences']
    #                 # print 'experiences==============================================', experiences
    #                 for exper_item in experiences:
    #                     exper=[]
    #                     exp_dict={}
                            
    #                     exp_dict['organization'] =exper_item['cname']
    #                     exp_dict['job_title'] = exper_item['pos']

    #                     print '==========start, end on===============',exper_item['starton'],exper_item['endon']
    #                     if (exper_item['endon'])!= None:
    #                         if(int(exper_item['starton'][0:4])<int(exper_item['endon'][0:4])):

    #                             if len(str(exper_item['starton']))>7:
    #                                 # print 'if_starton ====================endon st444r', exper_item['starton'][0:7]+"-01"
    #                                 exp_dict['entered_date'] = exper_item['starton'][0:7]+"-01"
    #                             else:
    #                                 exp_dict['entered_date'] = exper_item['starton'][0:4]+"-01-01"
    #                             if len(str(exper_item['endon'])) > 7:
    #                                 # print 'if_starton ====================endon s111tr', exper_item['endon'][0:7]+"-01"
    #                                 exp_dict['resigned_date'] = exper_item['endon'][0:7]+"-01"
    #                             else:
    #                                 exp_dict['resigned_date'] = exper_item['endon'][0:4]+"-01-01"
    #                         else:
    #                             check=False
    #                     else:
    #                         if len(str(exper_item['starton']))>7:
    #                             # print 'else_starton ====================endon st444r', exper_item['starton'][0:7]+"-01"
    #                             exp_dict['entered_date'] = exper_item['starton'][0:7]+"-01"
    #                             exp_dict['resigned_date'] = None
    #                         else:
    #                             exp_dict['entered_date'] = exper_item['starton'][0:4]+"-01-01"
    #                             exp_dict['resigned_date'] = None
    #                     #print '==========entered, resigned date===============',exp_dict['entered_date'],exp_dict['resigned_date']
    #                     exper.append(0)
    #                     exper.append(False)
    #                     exper.append(exp_dict)
    #                     experiences_arr.append(exper)

    #             #  ############################## TECHNICAL AND LANGUAGE SKILL GROUP ############################=================================================== ---->


    #             tech_complete_array=[]
    #             lange_complete_array=[]
    #             if 'skills' in key_list:
    #                 skills = cvs[item]['skills']
    #                 print '------------------skills------------------', skills
    #                 for skl_item in skills:
    #                     arr = []
    #                     l_arr = []
    #                     if int(skl_item['group'])==3:
    #                         is_there_skill = """select id from hr_info_skill where zangia_id= %s and group_zangia_id='%s'"""%(skl_item['skillid'], skl_item['group'])
                                
    #                         self.env.cr.execute(is_there_skill)
    #                         records = self.env.cr.dictfetchall()
    #                         print 'records---------++++++++++++++++++',records
    #                         tech_dictionary={}
    #                         if records:
    #                             tech_dictionary['skill_id'] = records[0]['id']
    #                         else:
    #                             self.env['integration.config'].sudo().inbound_integration('zangia_ref_tables_for_cvs')
    #                         print '=============rate===============', skl_item['rate']
    #                         tech_dictionary['software_level'] = 'middle'
    #                         if int(skl_item['rate'])>6 and skl_item['rate']<=9:
    #                             tech_dictionary['software_level'] = 'good'
    #                         elif int(skl_item['rate'])>9:
    #                             tech_dictionary['software_level'] = 'excellent'
    #                         arr.append(0)
    #                         arr.append(False) 
    #                         arr.append(tech_dictionary)
    #                         tech_complete_array.append(arr)

    #                         # print '================tech_complete_array===============', tech_complete_array
    #                     elif int(skl_item['group'])==2:
    #                         is_zangia_id = """select id from hr_info_skill where zangia_id= %s and group_zangia_id='%s'"""%(skl_item['skillid'], skl_item['group'])
    #                         self.env.cr.execute(is_zangia_id)
    #                         record = self.env.cr.dictfetchall()
    #                         lange_dict={}
    #                         if record:
    #                             lange_dict['skill_id'] = record[0]['id']
    #                         else:
    #                             self.env['integration.config'].sudo().inbound_integration('zangia_ref_tables_for_cvs')
    #                         l_arr.append(0)
    #                         l_arr.append(False) 
    #                         l_arr.append(lange_dict)
    #                         lange_complete_array.append(l_arr)

    #                         # print ' dictionary and array===================== ' , educs
    #                     print 'complete tech===================== ' , tech_complete_array
    #                     print 'complete lang===================== ',lange_complete_array

    #             # ---------------------------------------------------------------------------------------------------
    #             application_id = self.env['hr.applicant']
    #             print '\n\n\n\n\n\n===applicant id=======',item ,cvs[item]['reg'], application_id
    #             if cvs[item]['reg']:
    #                 application_id = application_id.sudo().search([('register_no','=',cvs[item]['reg'])])
    #             else:
    #                 application_id = application_id.sudo().search([('zangia_anket_id','=',item)])
                
    #             # print '<<<<<<<<<<<<<<< application_id??????????>>>>>>>', application_id
    #             res= []
    #             if cvs[item]['loc']:
    #                 query = """select id from hr_employee_location where zangia_id = '%s'"""%(cvs[item]['loc'])
    #                 self.env.cr.execute(query)
    #                 res = self.env.cr.dictfetchall() 

    #             cv = {
    #                     'zangia_anket_id':item,
    #                     # 'job_id':ad.res_id,
    #                     'location_id': res[0]['id'] if res else None,
    #                     'email_from':cvs[item]['email'],
    #                     'partner_name':cvs[item]['fname'],
    #                     'name':cvs[item]['lname'],
    #                     'gender':'male' if cvs[item]['sex'] == 'm' else 'female',
    #                     'register_no':cvs[item]['reg'],
    #                     'marital_status':'single' if cvs[item]['marstat']== '2' else 'married',
    #                     'birth_date':cvs[item]['bday'] if cvs[item]['bday']!='' else False,
    #                     'expected_salary_from_zangia':cvs[item]['salary'],
    #                     'partner_phone':cvs[item]['phone1'],
    #                     'availability':str(cvs[item]['availdt']) if len(str(cvs[item]['availdt'])) > 9 else False,
    #                     'education_level':edulvl if complete_array else None,
    #                     'education_ids': complete_array,
    #                     'training_ids': training_arr,
    #                     'employment_ids':experiences_arr if check else False,
    #                     'software_skill_ids': tech_complete_array,
    #                     'language_ids':lange_complete_array
    #                 }
    #             print '=================rendered cv ============================', cv

    #             # create or update an applicant
    #             if application_id:

    #                 application_id.zangia_anket_id = item 
    #                 for applies_item in cvs[item]['applies']: 
    #                     print '\n\n\n\n\n\n\n-----------applies-----------', cvs[item]['applies'], applies_item   
    #                     if not application_id.zangia_id or application_id.zangia_id == applies_item['jobid']:
    #                         application_id.zangia_id = applies_item['jobid']
    #                     elif not application_id.zangia_id2 or application_id.zangia_id2 == applies_item['jobid']:
    #                         application_id.zangia_id2 = applies_item['jobid']
    #                     elif not application_id.zangia_id3 or application_id.zangia_id3 == applies_item['jobid']:
    #                         application_id.zagia_id3 = applies_item ['jobid']
    #                 if not application_id.job_id.id or application_id.job_id.id==ad.res_id:
    #                     application_id.job_id=ad.res_id

    #                 elif not application_id.position_name2.id or application_id.position_name2.id == ad.res_id:
    #                     application_id.position_name2 = ad.res_id

    #                 elif not application_id.position_name3.id or application_id.position_name3.id == ad.res_id:
    #                         application_id.position_name3 = ad.res_id
                    
    #                 else:
    #                     is_there = self.env['interested.in.job.line'].search([('job_position','=',self.name_job), ('applicant_id','=',application_id.id)])
    #                     print '============is there in the line===========', is_there, self.name_job
    #                     if not is_there:
    #                         line={
    #                             'job_position':self.name_job,
    #                             'applicant_id':application_id.id,
    #                         }
    #                         self.env['interested.in.job.line'].sudo().create(line)

    #                 self.env.cr.execute('delete from hr_education where applicant_id=%s'%(application_id.id))
    #                 self.env.cr.execute('delete from hr_training where applicant_id=%s'%(application_id.id))
    #                 self.env.cr.execute('delete from hr_employment where applicant_id=%s'%(application_id.id))
    #                 self.env.cr.execute('delete from hr_software_skill where applicant_id=%s'%(application_id.id))
    #                 self.env.cr.execute('delete from hr_language where applicant_id=%s'%(application_id.id))
    #                 print '==================update the applicant ============================'
                    
    #                 application_id.write(cv)
    #             else:

    #                 print'===========create a applicant========================'

    #                 application_id = self.env['hr.applicant'].sudo().create(cv)
    #                 application_id.job_id = ad.res_id
    #                 application_id.zangia_id = cvs[item]['applies'][0]['jobid']

    #             order_ids = self.env['new.employee.order'].sudo().search([('name_job','=',ad.res_id),('job_description_id','=',int(ad.res_id3)), ('state','not in',['draft','cancelled','done'])])
    #             print '=======ad.res_id+++++ ad.res_id3==============',ad.res_id, ad.res_id3
    #             print 'order_ids-----------------------------------------------------------------',order_ids
    #             for order in order_ids:

    #                 print '\n\n\n\n\n order -------------------------------', order,order.depart_id.location_id.id,ad.res_id2
    #                 print '\n\n\n\n\n order -------------------------------', order, ad.res_id3, order.job_description_id.id
    #                 if order.depart_id.location_id.id == ad.res_id2 and str(order.job_description_id.id) == ad.res_id3:
    #                     in_line = self.env['employee.announcement.line'].search([('order_id','=',order.id), ('applicant_id','=',application_id.id)])
    #                     if not in_line:
    #                         an_ln = {
    #                             'order_id':order.id,
    #                             'applicant_id':application_id.id,
    #                         }
    #                         # print '+++++++++++++++++++++++', an_ln
    #                         self.env['employee.announcement.line'].sudo().create(an_ln)

    def inbound_integration(self,code):
        
        notification_ids = self.env['proactive.notification'].sudo().search([('code','=',code),('integration_data_type','=','inbound_integration')])

        for notification_id in notification_ids:

            if notification_id.python:
                #print '========in inbound integration===============', notification_id, notification_ids
                exec(notification_id.python)

            # self.zangia_ref_tables_for_notice(notification_id)    
            # self.zangia_ref_tables_for_cvs(notification_id)
            # self.zangia_cv_download(notification_id)


class ProactiveNotification(models.Model):

    _name = 'proactive.notification'
    _description = 'Proactive notification'
    _table = "proactive_notification"
    _order = "name"
    #_inherit = ['mail.thread', 'ir.needaction_mixin']
   
    config_id = fields.Many2one('integration.config', string='Config')
    code = fields.Char(string='Code', required=True, size=40)
    server_ip = fields.Char(string='Server IP', required=True, size=128)

    name = fields.Char(string='Name')
    model = fields.Char('Model name', index=True)

    user_id = fields.Many2one('res.users', string='User ID')
    active = fields.Boolean(string="Active", default=True)
    line_ids = fields.One2many('proactive.line','notification_id', string='Line IDs')
    state = fields.Selection([
            ('need_a_solution',u'Шийдэл хэрэгтэй'),
            ('completed',u'Шийдэгдсэн'),
        ], 'State', track_visibility='onchange', default = 'need_a_solution')

    domain = fields.Text(string='Domain/query',default="[('create_date', '>', '3022-01-30')]",track_visibility='onchange')
    delete_query = fields.Text(string='Delete query',track_visibility='onchange')
    python = fields.Text(string='Python',track_visibility='onchange')
    python_with_sql = fields.Text(string='Python',track_visibility='onchange')
    python_for_resend_button = fields.Text(string='Python for RB',track_visibility='onchange')
    python_for_after_resend_button = fields.Text(string='Python for ARB',track_visibility='onchange')

    total_count = fields.Integer(string='Шийдэх шаардлагатай')
    need_a_solution_count = fields.Integer(string='Шийдэгдээгүй')
    completed_count = fields.Integer(string='Шийдэгдсэн')
    no_need_count = fields.Integer(string='Шийдэх шаардлагагүй')
    cron_trial_period = fields.Integer(string='Cron job оролдлого хийх хоногийн тоо', default=2)
    allow_to_show_json = fields.Boolean(string="Шийдэгдсэн төлөвт Json харуулдаг байх эсэх", default=True)

    integration_data_type = fields.Selection([
            ('workflow_notification',u'Урсгалын нотификешн'),
            ('reference_based_integration',u'Reference дээр үндэслэсэн интеграц'),
            ('reference_based_integration_on_many_objects',u'Олон объектын reference дээр үндэслэсэн интеграц'),
            ('object_based_integration',u'Объект дээр үндэслэсэн интеграц'),
            ('sync_flag_is_on_object',u'Синклэсэн эсэхийг объект дээрээ хөтлөх'),
            ('inbound_integration',u'Хүлээн авах интеграц'),
            ('inbound_integration_without_cron',u'Кронгүй хүлээн авах интеграц'),
            ('integration_for_deletion',u'Устгах интеграц'),
            
        ], 'Интеграцын төрөл', track_visibility='onchange', default = 'reference_based_integration',required=True)

    button_pressed_date = fields.Datetime(string='Товч дарсан огноо')
    sync_field_name = fields.Char('Sync field-н нэр')

    @api.model
    def create(self, vals):

        res = super(ProactiveNotification, self).create(vals)
        res.name = res.model + ' => ' + res.code


        if vals.get('model') or vals.get('code') or vals.get('integration_data_type'):
            
            if res.integration_data_type == 'reference_based_integration':
                res.name = '1r. ' + res.model + ' => ' + res.code
            elif self.integration_data_type == 'object_based_integration':
                res.name = '2o. ' + res.model + ' => ' + res.code
            elif self.integration_data_type == 'reference_based_integration_on_many_objects':
                res.name = '3m. ' + res.model + ' => ' + res.code
            elif self.integration_data_type == 'inbound_integration':
                res.name = '4i. ' + res.model + ' => ' + res.code
            else:
                res.name = '5d. ' + res.model + ' => ' + res.code


        return res

    #@api.multi
    def write(self, vals):


        res = super(ProactiveNotification, self).write(vals)

        if vals.get('model') or vals.get('code') or vals.get('integration_data_type'):
            
            if self.integration_data_type == 'reference_based_integration':
                self.name = '1r. ' + self.model + ' => ' + self.code
            elif self.integration_data_type in ('object_based_integration','sync_flag_is_on_object'):
                self.name = '2o. ' + self.model + ' => ' + self.code
            elif self.integration_data_type == 'reference_based_integration_on_many_objects':
                self.name = '3m. ' + self.model + ' => ' + self.code
            elif self.integration_data_type == 'inbound_integration':
                self.name = '4i. ' + self.model + ' => ' + self.code
            else:
                self.name = '5d. ' + self.model + ' => ' + self.code
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='',
                        toolbar=False, submenu=False):
        result = super(ProactiveNotification, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)

        if view_type =='tree':
            doc = etree.XML(result['arch'])

            for node in doc.xpath("//tree"):
                node.set('create', 'false')
            result['arch'] = etree.tostring(doc)
        elif view_type == 'form':
            doc = etree.XML(result['arch'])

            for node in doc.xpath("//form"):
                node.set('create', 'false')
            result['arch'] = etree.tostring(doc)

        return result   



			
    def config(self,ba1, ba2):

        return ''.join([chr(ord(a)^ord(b)) for a, b in zip(ba1, ba2)])

    def get_url(self,from_cron):

        error_msg = ''
        if not self.config_id.active:

            return False    
        elif not self.server_ip:
            error_msg = 'Интеграци тохиргоо хийгдээгүй байна.'
        elif not self.config_id.from_server_ips:
            error_msg = 'Илгээгч серверийг тохируулах талбар хоосон байна.'
        elif get_ip_address() not in (self.config_id.from_server_ips):
            error_msg = 'Энэ серверийн ip-с илгээж болно гэсэн тохиргоо алга байна.'
        elif not self.server_ip:
            error_msg = 'Url тохируулагдаагүй байна'
        else:
            # print 'ds',self.config_id
            return self.server_ip
        


        if from_cron:
            return False
        else:
            raise UserError(_(error_msg))

            
    def handle_active_directory_users(bearer_token):
        print ('sss')


    def get_bearer_token(self):

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',  
            }
        xxx = self.config(self.config_id.a1,self.config_id.a3)
        zzz = self.config(self.config_id.a2,self.config_id.a4)
        body = {'loginName':xxx,'password':zzz,'domainName':'nm','PRODUCT_NAME':'ERP'}

        r=requests.post(self.config_id.token_url,headers=headers,data=body)
        dict_txt = json.loads(r.text)
        
        if r.status_code == 200:
            if dict_txt['LoginStatusMessage'] == 'Success':			
                return str(json.loads(r.text)['AuthTicket'])
        else:
            return ''



    def connect(self,body,from_cron):

        result = 'tried'
        msg = ''
        
        url = self.get_url(from_cron) 
        #print '=======================url=======================',url
        if not url:
            return False,False

        # print '-------',self.config_id.connection_type
        # if self.config_id.connection_type == 'xml_rpc':
        #     username = 'admin' # The Odoo user
        #     pwd = '123'# The password of the Odoo user
        #     dbname = 'nomin0302' # The Odoo database``
            
        #     sock_common = xmlrpclib.ServerProxy (url + '/common')
        #     uid = sock_common.login(dbname, username, pwd)
        #     sock = xmlrpclib.ServerProxy(url+'/object')

        #     resp = sock.execute_kw(dbname, uid, pwd, 'partner.inbound.integration', 'create_partners_from_employees', ['self',{'user_id':'20031', 'line_ids':json.loads(body)}])
            
        
        if self.config_id.connection_type == 'xml_rpc':
            username = self.config_id.a1 # The Odoo user
            pwd = self.config_id.a2 # The password of the Odoo user
            dbname = self.config_id.a3 # The Odoo database``
            
            sock_common = xmlrpclib.ServerProxy (url + '/common')


            uid = sock_common.login(dbname, username, pwd)
            sock = xmlrpclib.ServerProxy(url+'/object')

            result_msg = []

            #
            for item in body:             
                r_msg = sock.execute_kw(dbname, uid, pwd, 'inbound.integration', 'create_n_update', ['self',item])  
                
                if self.sync_field_name and r_msg[0]['msg'] in ('created','updated'):
                    query = "update %s set %s=True where id = %s"%(item['odoo9_table_name'],self.sync_field_name,item['id'])

                    self.env.cr.execute(query)

                result_msg += r_msg

            msg = json.dumps(result_msg,ensure_ascii=False)
            result = 'completed'

            table_name = item['table_name']
            if item.get('odoo9_table_name', False):
                table_name =item['odoo9_table_name']

            query = """create temp table lines2(total_count int,need_a_solution_count int,completed_count int ,no_need_count int,notification_id int);
                insert into lines2 select count(*),0,count(*),0,%s from %s a;"""%(self.id,table_name)

            if self.sync_field_name:
                query = """create temp table lines2(total_count int,need_a_solution_count int,completed_count int ,no_need_count int,notification_id int);
                    insert into lines2 select count(*),
                    sum(case when a.%s=False then 1 else 0 end),
                    sum(case when a.%s=True then 1 else 0 end),
                    sum(case when a.%s is null  then 1 else 0 end),%s 
                    from %s a;"""%(self.sync_field_name,self.sync_field_name,self.sync_field_name,self.id,table_name)



            query += """
                UPDATE 
                    proactive_notification pn
                SET 
                    total_count = pl.need_a_solution_count+pl.completed_count,
                    need_a_solution_count = pl.need_a_solution_count,
                    completed_count = pl.completed_count,
                    no_need_count = pl.no_need_count,
                    state = case when pl.need_a_solution_count = 0 then 'completed' else 'need_a_solution' end
                FROM 
                    lines2 pl
                WHERE 
                    pn.id = %s;"""%(self.id)


            #print 'query',query

#

            self.env.cr.execute(query)    


#

        if self.config_id.connection_type == 'xml_rpc1':
            username = self.config_id.a1 # The Odoo user
            pwd = self.config_id.a2 # The password of the Odoo user
            dbname = self.config_id.a3 # The Odoo database``
            
            sock_common = xmlrpclib.ServerProxy (url + '/common')
            #print 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',dbname, username, pwd
            username = 'admin' # The Odoo user
            pwd = '123'# The password of the Odoo user
            dbname = 'mw' # The Odoo database
            uid = sock_common.login(dbname, username, pwd)
            sock = xmlrpclib.ServerProxy(url+'/object')

            result_msg = []
            # print "\n\nResult msg start"
            # try:
            #     result_msg = sock.execute_kw(dbname, uid, pwd, 'inbound.integration', 'create_n_update_hr_employee', ['self',body])
            # except Exception as e:
            #     print "Result msg exception", body, "\n\nException", e
            #     result_msg = {'msg': str(e)}
#

            # print "\n\nResult msg end\n\n"

            result_msg = sock.execute_kw(dbname, uid, pwd, 'inbound.integration', 'create_n_update_hr_employee', ['self',body])
 #
            msg = json.dumps(result_msg,ensure_ascii=False)
            result = 'completed'


            
            



        elif self.config_id.connection_type == 'bunch_connections_for_soap':
            proxy = xmlrpclib.ServerProxy(url)
            result_msg = []
            # print '\n\n\n\n\n\n body',json.loads(body)
            for item in json.loads(body):
                res_msg = ''
                #print 'item \n\n\n\n\n\n\n\n\n\n',item

                res ={'value':True,'Msg':"TEST"}
                try:
                    #socket.setdefaulttimeout(20)        #set the timeout to 20 seconds
                    res = proxy.partner.create(item)
                except:
                    res = False
                 




                #_logger.info(u'::: ИНТЕГРАЦИ ::: ----------------------- Харилцагч үүсгэх: %s'%(res))
                if res['error_code'] == 2601:
                    res_msg = u"Энэ харилцагч Номин програм дээр бүртгэгдсэн байна! Өгөгдөл: %s"%(params)
                if res['error_code'] == 101:
                    res_msg = u"Харилцагч үүсгэх интеграци хийх ажил амжилтгүй боллоо. Алдаа: %s"%(res['Msg'])
                
                if res['value'] == True:
                    res_msg = 'completed'
                    #_logger.info(u'::: ИНТЕГРАЦИ ::: Диамондруу харилцагч амжилттай бүртгэгдлээ!')
                else:
                    res_msg = u"Харилцагч үүсгэх интеграци хийх ажил амжилтгүй боллоо. Алдаа2: %s"%(res['Msg'])

                result_msg.append({'SyncOdooID':item['SyncOdooID'],'msg':res_msg})
			
            msg = json.dumps(result_msg,ensure_ascii=False)
            result = 'completed'
            

                

      
        elif self.config_id.connection_type == 'bearer_token':
            if self.config_id.a1 and self.config_id.a2 and self.config_id.a3 and self.config_id.a4 and self.config_id.token_url:

                bearer_token = self.get_bearer_token()

                #print 'bearer_token',bearer_token

                headers = {
                        'Content-Type':'application/json',
                        }

                self.handle_active_directory_users(bearer_token)

            
             
        elif self.config_id.connection_type == 'just_url':
            if self.config_id.a1 and self.config_id.a2 and self.config_id.a3 and self.config_id.a4:


                xxx = self.config(self.config_id.a1,self.config_id.a3)
                zzz = self.config(self.config_id.a2,self.config_id.a4)

                #print '\n\n 77777777777 ',xxx,zzz,body

                r=requests.post(url,auth=(xxx, zzz),data=str(body))

                #print 'jjjjjjjjjjjjjjjjjjjjjj\n\n',r,r.text
    
                if r.status_code == 200:				
                    result = 'completed'
                    msg = r.text
                else:
                    if r.text:
                        msg = r.text
                    else:
                        #print 'r\n\n',r
                        msg = r
            else:
                raise UserError(_('А1,A2,A3,A4 талбаруудын аль нэгийг бөглөөгүй байна!'))




        elif self.config_id.connection_type == 'basic_post':
            if self.config_id.a1 and self.config_id.a2 and self.config_id.a3 and self.config_id.a4:


                xxx = self.config(self.config_id.a1,self.config_id.a3)
                zzz = self.config(self.config_id.a2,self.config_id.a4)

                #print '\n\n 77777777777 ',url,xxx,zzz,body
                header = {'Content-Type':'application/json'}
                r=requests.post(url,auth=(xxx, zzz),headers=header,data=str(body))

                #print 'jjjjjjjjjjjjjjjjjjjjjj\n\n',r,r.text
    
                if r.status_code == 200:				
                    result = 'completed'
                    msg = r.text
                else:
                    if r.text:
                        msg = r.text
                    else:
                        #print 'r\n\n',r
                        msg = r
            else:
                raise UserError(_('А1,A2,A3,A4 талбаруудын аль нэгийг бөглөөгүй байна!'))

            # 

        elif self.config_id.connection_type == 'non_token_post':

            headers = {
                   'Content-Type':'application/json',
                   }

            r = requests.post(url,data=str(body), headers=headers)
            #print 'rrrrrr44\n\n\n\n\n\n\n\n\n\n',r
            if r.status_code == 200:
                msg = r.text				
                result = 'completed'
            elif r.status_code == 500:
                msg = 'Хариу алга'
            else:
                msg = r.text



        elif self.config_id.connection_type == 'non_token_post_without_header':

            r = requests.post(url,data=body)
            #print 'rrrrrrmmmmmmmmmmmmmm\n\n\n\n\n\n\n\n\n\n',r
            if r.status_code == 200:				
                result = 'completed'


                if r.json()["resultData"]:
                    msg = r.json()["resultData"]

            else:
                msg = r.text


        elif self.config_id.connection_type == 'manually_created_token_post':


            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                }

            r=requests.post(url,data=json.loads(body))



            msg = r.text
            #print 'msg',r,r.status_code
            if "success" in json.loads(msg):
                if json.loads(msg)['success']:
                    result = 'completed'
                else:
                    result = 'fail'

            elif r.status_code == 200: 
                result = 'completed'
                

        return result,msg

    def validate_sync(self,res_id):

        

        domain=[('id','=',res_id)]

        if self.domain:
            domain=['&',]+domain+eval(self.domain)
        return self.env[self.model].sudo().search(domain)


    def reference_based_integration(self,res_id,body): 
        
        return self.integration_with_checkflag(res_id,0,'0',body,False,False)


    def reference_based_integration_on_many_objects(self,res_id,res_id2,res_id3,body):

        return self.integration_with_checkflag(res_id,res_id2,res_id3,body,False,False)



    def inbound_integration(self,res_id3,body): 

        #print 'dddfwee sdprof',res_id3
        
        return self.integration_with_checkflag(0,0,res_id3,body,False,False)


    def integration_with_checkflag(self,res_id,res_id2,res_id3,body,check_flag,from_cron):

        #print 'dddfwee sd',res_id,res_id2,res_id3,body,check_flag,from_cron

        state = 'completed' 
        msg = ''
        json_txt = json.dumps(body,ensure_ascii=False)
        # if self.validate_sync(res_id) or 1==1:
        if 1==1:
            if check_flag:
                state,msg = self.connect(json_txt,from_cron)
                if state != 'completed':
                    raise UserError(_(msg))
            else:


                
                domain = [('notification_id','=',self.id),('res_id','=',res_id),('res_id2','=',res_id2),('res_id3','=',res_id3)]

                if res_id == 0:
                    domain = [('notification_id','=',self.id),('res_id3','=',res_id3)]
                elif res_id2 == 0:
                    domain = [('notification_id','=',self.id),('res_id','=',res_id)]
                elif res_id3 == '0':
                    domain = [('notification_id','=',self.id),('res_id','=',res_id),('res_id2','=',res_id2)]
                
                #print 'domain',domain



                line_id = self.env['proactive.line'].sudo().search(domain)
                #print '7777777',line_id
                if not line_id:
                    line_id = self.env['proactive.line'].sudo().create({
                        'notification_id':self.id,
                        'res_id':res_id,
                        'res_id2':res_id2,
                        'res_id3':res_id3,
                        'state':'need_a_solution',
                        'msg':msg
                    })

                #print '=========send json============',json_txt,from_cron,line_id


                if res_id != 0:
                    return self.update_line_item(line_id,json_txt,from_cron)
                
            
        else:
            return 'wont_sync'

#


    def delete_items_in_integrated_system(self,res_id,res_id2,res_id3,body):

        
        domain = [('res_id','=',res_id),('res_id2','=',res_id2),('res_id3','=',res_id3)]
        
        if res_id2 == 0:
            domain = [('res_id','=',res_id)]
        elif res_id3 == '0':
            domain = [('res_id','=',res_id),('res_id2','=',res_id2)]

        line_id = self.env['proactive.line'].sudo().search(domain)

        #print 'line_id',line_id

        if line_id:

            state,msg = self.connect(json.dumps(body),False) 
            #print '\n\n\n\n\n\n\n\n ================state and msg for deletion ====',state,msg,line_id
            if state == 'completed':

                query="""delete from proactive_line where  id = %s"""%(line_id.id)
                self.env.cr.execute(query)
                return state        
        else:
            return 'none'

        # if line_id:

        #     state,msg = self.connect(json.dumps(body),False) 
        #     print '\n\n\n\n\n\n\n\n ================state and msg for deletion ====',state,msg,line_id
        #     if state == 'completed':

        #         query="""delete from proactive_line where  id = %s"""%(line_id.id)
        #         self.env.cr.execute(query)
        #         return state
        
        # else:
        #     return 'none'


        # print '==+++1111',json_txt,from_cron,line_id


    def update_line_item(self,line_id,json_txt,from_cron):

        if line_id.state in ('need_a_solution','tried') or self.config_id.integration_type == 'repeat_based':

            
            
            state,msg = self.connect(json_txt,from_cron) 
            #print '\n\n\n======recieve json===========',msg ,state ,line_id
            if state == 'completed' and not self.allow_to_show_json:
                json_txt = ''
            line_id.sudo().write({'state':state,'msg':msg,'json':json_txt})

            return state,line_id
        else:
            return 'completed',line_id

    @api.model
    def _cron_job_for_transactional_data_integration(self):

        self.sync_object_based_items(True,False)



    @api.model
    def _cron_job_for_proactive_notifications(self):

        self.sync_500_items(True)



#



    #@api.multi
    def cron_job_for_proactive_notifications(self):


        self.sync_items(True)


    #@api.multi
    def sync_prepared_items(self):

        return self.sync_items(False)

    #@api.multi
    def sync_items(self,is_cron_job):

        self.button_pressed_date = datetime.now()
        if self.code == 'notification':

            field_ids = []
            line_ids = self.env['proactive.line'].search([('notification_id','=',self.id)])
            for line in line_ids:
                field_ids.append(line['res_id'])
            domain = [('id','in',field_ids)]
            view_id_tree = self.env['ir.ui.view'].search([('model','=',self.model),('type','=','tree')])
            #print 'ddd\n\n\n\n\n\n\n\n\n\nkkk',view_id_tree
            if view_id_tree:
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': self.model,
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'views': [(view_id_tree[0].id, 'tree'),(False,'form')],
                    'view_id': False,
                    'target': 'main',
                    'domain': domain,
                }

        elif self.integration_data_type == 'reference_based_integration':

            self.sync_500_items(is_cron_job)

        elif self.integration_data_type in ('object_based_integration','sync_flag_is_on_object'):

            return self.sync_object_based_items(is_cron_job,False)

        elif self.integration_data_type == 'inbound_integration':
            print ('')
        elif self.integration_data_type == 'inbound_integration_without_cron':
            print ('')


    #@api.multi
    def sync_500_items(self,is_cron_job):

        # model_name = self.model
        # filter_value = self.domain
        records = False
        
        # model_name = 'proactive.line'
        if is_cron_job:
            notification_ids = self.env['proactive.notification'].sudo().search([('code','!=','notification')])
            records = self.env['proactive.line'].sudo().search([('state','in',['need_a_solution','tried']),('notification_id','in', notification_ids.ids)] ,limit=50 ,order='state,write_date')
        else:
            records = self.env['proactive.line'].sudo().search([('state','in',['need_a_solution','tried']),('notification_id','=', self.id)],limit=50 ,order='state,write_date')

        if records:
            #print 'not_synced_records---------',records


            for not_synced_record in records:
                not_synced_record.sudo().update_one_record(is_cron_job)
            self.env.cr.commit()


        query = """create temp table lines2(total_count int,need_a_solution_count int,completed_count int ,no_need_count int,notification_id int);
            insert into lines2 select count(*),
            sum(case when state in ('need_a_solution','tried') then 1 else 0 end),
            sum(case when state='completed' then 1 else 0 end),
            sum(case when state='no_need' then 1 else 0 end),
            notification_id from proactive_line
            group by notification_id;
            UPDATE 
                proactive_notification pn
            SET 
                total_count = pl.total_count,
                need_a_solution_count = pl.need_a_solution_count,
                completed_count = pl.completed_count,
                no_need_count = pl.no_need_count,
                state = case when pl.need_a_solution_count = 0 then 'completed' else 'need_a_solution' end
            FROM 
                lines2 pl
            WHERE 
                pn.id = pl.notification_id and pn.integration_data_type != 'object_based_integration';"""

        self.env.cr.execute(query)

    #@api.multi
    def object_based_integration(self,res_id,body):
        # if self.python:
        #     exec(self.python)

        json_txt = json.dumps(body,ensure_ascii=False)
        #print 'json_txt111','['+json_txt+']'
        if json_txt:
            self.resend('['+json_txt+']',False)


 



    #@api.multi
    def sync_object_based_items(self,is_cron_job,records):

        if is_cron_job:

            records = self.env['proactive.notification'].sudo().search([('integration_data_type','=','object_based_integration')], limit=50, order='write_date') 
            for record in records:
                if record.python_with_sql:
                    exec(record.python_with_sql)

#


        else:

            field_ids = []
            if self.integration_data_type == 'object_based_integration':

                
                body = []
                #
                if self.python_with_sql:
                    exec(self.python_with_sql)
                #43                
                json_txt = json.dumps(body,ensure_ascii=False)



    
                if json_txt:
                    #print 'd4'
                    self.resend(json_txt,False)
                records = False
                if self.python_for_after_resend_button:
                    exec(self.python_for_after_resend_button)



                if records:
                    for record in records:
                        field_ids.append(record['id'])

            else:

                body = []

                if not records:
                    self.env.cr.execute(self.domain)
                    records = self.env.cr.dictfetchall()

                #print 'records',records
                if records:

                    items =[]
                    for record in records:
                        object_id = self.env[self.model].browse(record['id'])

                        if object_id:

                            if self.python:
                                exec(self.python)

                        items.append(body)
                    # print '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n items - ',items
                    json_txt = json.dumps(items,ensure_ascii=False)
                    state = 'need_a_solution'
                    msg = ''
                    # print '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n json_txt-----------67777777777777777-',json_txt
                    if self.config_id.connection_type == 'xml_rpc':
                        state,msg = self.connect(items,False)  
                    else:      
                        state,msg = self.connect(json_txt,False)
                    # print '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n state,msg-------',state,msg      

                        
                    failed = False
                    # print 'g============================'

                    #

                    line_id = self.env['proactive.line'].sudo().search([('notification_id','=',self.id)])
                    #print 'line_id',line_id

                    #
                    #
                    if line_id:
                        line_id.sudo().write({
                            'state':state,
                            'res_id':0,
                            'msg':msg,
                            'json':json_txt
                        })
                    else:
                        line_id = self.env['proactive.line'].sudo().create({
                            'notification_id':self.id,
                            'state':state,
                            'res_id':0,
                            'msg':msg,
                            'json':json_txt
                        })
                        

                return msg




                    # update_query ="update res_partner set is_synced =%s where id=%s"%(is_synced,item['SyncOdooID'])
                    # print 'update_query',update_query

                    # self.env.cr.execute(update_query)
                    # self.env.cr.commit()  



                
            # domain = [('id','in',field_ids)]
            # print 'domain',domain
            # view_id_tree = self.env['ir.ui.view'].search([('model','=',self.model),('type','=','tree')])
            # print '\n\n\n\n\n\n\n\n\n\nview_id_tree',view_id_tree
            # if view_id_tree:
            #     return {
            #         'type': 'ir.actions.act_window',
            #         'res_model': self.model,
            #         'view_type': 'form',
            #         'view_mode': 'tree,form',
            #         'views': [(view_id_tree[0].id, 'tree'),(False,'form')],
            #         'view_id': False,
            #         'target': 'main',
            #         'domain': domain,
            #     }




    #@api.multi
    def resend(self,json_txt,from_cron):
        # exec(record.python_of_resend_button)
        state = 'need_a_solution'
        #print '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n json_txt-----------67777777777777777-',json_txt
        state,msg = self.connect(json_txt,from_cron)        
        #print '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n state,msg-------',state,msg      
        if self.integration_data_type == 'object_based_integration':
            #
            failed = False

            if self.python_for_resend_button:
                exec(self.python_for_resend_button)
            

            line_id = self.env['proactive.line'].sudo().search([('notification_id','=',self.id)])
            #print 'line_id',line_id

            
            if not failed:
                state = 'completed'
                msg = ''
                json_txt = ''

            # 
            if line_id:
                line_id.sudo().write({
                    'state':state,
                    'res_id':0,
                    'msg':msg,
                    'json':json_txt
                })
            else:
                line_id = self.env['proactive.line'].sudo().create({
                    'notification_id':self.id,
                    'state':state,
                    'res_id':0,
                    'msg':msg,
                    'json':json_txt
                })
                


            # else:
            #     if line_id:
            #         line_id.sudo().write({
            #             'state':'completed',
            #             'res_id':0,
            #             'msg':'',
            #             'json':''
            #         })

            

        return state,msg     








    #@api.multi
    def prepare_sync_items(self):
    
        self.env.cr.execute("select res_id from proactive_line where res_id is not null and notification_id=%s"%(self.id))
        fetched = self.env.cr.fetchall()
        existing_items = []
        for fetch in fetched:
            existing_items.append(fetch[0])

        domain = []
        
        if self.domain:
            domain= eval(self.domain)

        if existing_items:
            domain=[('id','not in',existing_items)]

        if existing_items and self.domain:
            domain=['&',]+domain+eval(self.domain)
        #print 'domain',domain,self.model
        line_ids=self.env[self.model].sudo().search(domain)
        #print 'line_ids',line_ids
        for line in line_ids:
            self.env.cr.execute("insert into proactive_line (res_id,notification_id,state) values(%s,%s,'need_a_solution')"%(line.id,self.id))

        if self.delete_query:
            self.env.cr.execute(self.delete_query%(self.id))



class ProactiveLine(models.Model):
    _name = 'proactive.line'
    _description = 'Proactive line'
    _table = "proactive_line"
    _order = "state desc,write_date desc"
    #_inherit = ['mail.thread', 'ir.needaction_mixin']
    

    notification_id = fields.Many2one('proactive.notification', string='Notification ID')
    handler_id = fields.Many2one('proactive.handler', string='Handler ID')
    res_id = fields.Integer('Res ID', index=True)
    res_id2 = fields.Integer('Res ID2')
    res_id3 = fields.Char('Res ID3')
    state = fields.Selection([
            ('need_a_solution',u'Шийдэл хэрэгтэй'),
            ('tried',u'Шийдэх оролдлого хийгдсэн'),
            ('completed',u'Шийдэгдсэн'),
            ('no_need',u'Шийдэх шаардлагагүй'),
        ], 'State', track_visibility='onchange', default = 'need_a_solution')
    msg = fields.Char(string='Message')
    json = fields.Text(string='Json')


    @api.model
    def fields_view_get(self, view_id=None, view_type='',
                        toolbar=False, submenu=False):
        result = super(ProactiveLine, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)

        if view_type =='tree':
            doc = etree.XML(result['arch'])

            for node in doc.xpath("//tree"):
                node.set('create', 'false')
            result['arch'] = etree.tostring(doc)
        elif view_type == 'form':
            doc = etree.XML(result['arch'])

            for node in doc.xpath("//form"):
                node.set('create', 'false')
            result['arch'] = etree.tostring(doc)

        return result   

#
    def update_one_record(self,from_cron):


        if self.notification_id.python_with_sql:
            exec(self.notification_id.python_with_sql)


            
    #


    #@api.multi
    def resend_button(self):
        #
        state = 'completed'  

        if self.state == 'need_a_solution':
            
            # state,msg = self.notification_id.connect(self.json) 

            #
            #print 'd68',self.json
            state,msg = self.notification_id.resend(self.json,False) 
            #print '---------',state,msg 
            self.sudo().update({'state':state,'msg':msg})


#
class CalendarSyncUserLine(models.Model):
 	_name='calendar.sync.user.line'

#	
class CalendarSyncUserLine(models.Model):
    _name = 'calendar.sync.user.line'
    
	
	
    user_id = fields.Many2one('res.users',string=u"Хэрэглэгч")
    sync_id = fields.Many2one('calendar.sync.user',string="Sync")  
    datetime = fields.Datetime(string='Last auto sync date')  
    


 	# @api.multi
    def action_sync(self, cr, uid, ids,context=None):

        gCalendar_obj =self.pool.get('google.calendar')
        for sync in self.browse(cr, uid, ids):
            try:
                resp = gCalendar_obj.synchronize_events(cr,sync.user_id.id, False, lastSync=True, context=None)
                if resp.get("status") == "need_reset":
                    #_logger.info("[%s] Calendar Synchro - Failed - NEED RESET  !" % sync.user_id.id)
                    print ('')
                else:
                    update = "update calendar_sync_user_line set datetime='%s' where id =%s"%(datetime.now(),sync.id)
                    cr.execute(update)
                    #_logger.info("[\n\n%s] Calendar Synchro - Done with status : %s  !\n\n" % (sync.user_id.id, resp.get("status")))
            except Exception as e:
                #_logger.info("\n\n [%s] Calendar Synchro - Exception : %s !" % (sync.user_id.id, exception_to_unicode(e)))
                print ('')


class CalendarSyncUser(models.Model):
    _name = 'calendar.sync.user'
    _description = 'Calendar sync Configure'
    #_inherit = ['mail.thread', 'ir.needaction_mixin']

    #@api.multi
    def _set_name(self):
        for sync in self:
            sync.name="Google calendar sync"
	
    name = fields.Char(string="Name",required=True)
    line_ids = fields.One2many('calendar.sync.user.line','sync_id',string='Calendar sync')


    def _google_calendar_sync_cron(self, cr, uid):

        query = "select A.user_id,A.id from calendar_sync_user_line A inner join res_users B on A.user_id=B.id where B.google_calendar_last_sync_date is not null order by B.google_calendar_last_sync_date desc"
        cr.execute(query)
        records = cr.dictfetchall()
        gCalendar_obj =self.pool.get('google.calendar')
        #_logger.info("\nCalendar Synchro - Starting synchronization")
        if records:
            for record in records:
                print ('')
                #_logger.info("Calendar Synchro - Starting synchronization for a new user [%s] " % record['user_id'])
            
            try:

                resp = gCalendar_obj.synchronize_events(cr,record['user_id'], False, lastSync=True, context=None)
                if resp.get("status") == "need_reset":
                    print ('')
                    #_logger.info("[%s] Calendar Synchro - Failed - NEED RESET  !" % 	record['user_id'])
                else:
                    update = "update calendar_sync_user_line set datetime='%s' where id =%s"%(datetime.now(),record['id'])
                    cr.execute(update)
                    #_logger.info("[\n\n%s] Calendar Synchro - Done with status : %s  !\n\n" % (	record['user_id'], resp.get("status")))
                
            except Exception:
                print ('')
                    
                    # _logger.info("\n\n [%s] Calendar Synchro - Exception : %s !" % (record['user_id'], exception_to_unicode(e)))
                    # _logger.info("\n\nCalendar Synchro - Ended by cron")
                    # _logger.info("\n\nCalendar Synchro - Endining synchronization")
