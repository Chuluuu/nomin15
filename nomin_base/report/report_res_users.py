# -*- coding: utf-8 -*-
from openerp import api, fields, models, _
from datetime import datetime,timedelta
from operator import itemgetter
import xlsxwriter
from io import BytesIO
import base64

class RepotResUsers(models.TransientModel):
    _name ='report.res.users'
    job_ids = fields.Many2many(comodel_name='hr.job', string='Албан тушаал')
    group_ids = fields.Many2many(comodel_name='res.groups', string='Грүпп')
    report_type = fields.Selection([('group','Грүпп'),('department','Салбар/Хэлтэс')],string="Төрөл",default='group')


    @api.multi
    def export_chart(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        header = workbook.add_format({'border':1,'fg_color':'#b0e2ff','align':'justify','valign':'vjustify','text_wrap':100,'pattern':0})

        title = workbook.add_format({
        'border': 0,
        'bold': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 'off',
        'font_size':12,
        'font_name': 'Arial',
        })

        header = workbook.add_format({
        'border': 1,
        'bold': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': 'on',
        'font_size':8,
        'bg_color':'#b0e2ff',
        'font_name': 'Arial',
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
        cell_float_format_left_bold = workbook.add_format({
        'border': 1,
        'bold': 1,
        'align': 'right',
        'valign': 'vcenter',
        'text_wrap': 'on',
        'font_size':10,
        # 'bg_color':'#40E0D0',
        'font_name': 'Arial',
        'num_format': '#,##0.00'
        })
        cell_float_format_left = workbook.add_format({
        'border': 1,
        'bold': 0,
        'align': 'right',
        'valign': 'vcenter',
        'text_wrap': 'on',
        'font_size':10,
        # 'bg_color':'#40E0D0',
        'font_name': 'Arial',
        'num_format': '#,##0.00'
        })
        cell_float_format_left1 = workbook.add_format({
        'border': 1,
        'bold': 0,
        'align': 'right',
        'valign': 'vcenter',
        'text_wrap': 'on',
        'font_size':10,
        # 'bg_color':'#40E0D0',
        'font_name': 'Arial',
        # 'num_format': '#,##0.00'
        })
        sheet = workbook.add_worksheet()
        sheet.portrait=True

        if self.report_type=='group':
            where="where A.id!=0 "
            query_where=""
            if self.job_ids:
                if len(self.job_ids)>1:
                    query_where=query_where+" and A.job_id in %s"%( str(tuple(self.job_ids.ids)))
                else:
                    query_where=query_where+" and A.job_id = %s"%(str(self.job_ids.ids[0]))
            if self.group_ids:
                if len(self.group_ids)>1:
                    query_where=query_where+" and G.res_groups_id in %s"%( str(tuple(self.group_ids.ids)))
                else:                   
                    query_where=query_where+" and G.res_groups_id = %s"%(str(self.group_ids.ids[0]))
            

            query_group="select A.login, A.id as user_id,B.name as user,C.name as job,concat(K.name,' / ',E.name) as group,E.id as group_id, D.name as department from res_users A \
                            left join res_partner B ON B.id=A.partner_id \
                            left join hr_job C ON C.id=A.job_id \
                            left join hr_department D ON D.id=A.department_id \
                            left join res_groups_users_rel F ON F.uid=A.id \
                            left join res_groups E ON E.ID = F.gid  \
                            left join ir_module_category K ON K.ID = E.category_id  \
                            left join res_users_config H on H.job_id=A.job_id  \
                            left join res_groups_res_users_config_rel G ON G.res_users_config_id=H.id \
                            where A.active=True %s \
                            group by A.login,A.id,B.name,C.name,K.name,E.name,E.id,D.name \
except \
select A.login, A.id as user_id,B.name as user,C.name as job,concat(K.name,' / ',E.name) as group,E.id as group_id, D.name as department from res_users A \
                            left join res_partner B ON B.id=A.partner_id \
                            left join hr_job C ON C.id=A.job_id \
                            left join hr_department D ON D.id=A.department_id \
                            left join res_groups_users_rel F ON F.uid=A.id \
                            left join res_groups E ON E.ID = F.gid  \
                            left join ir_module_category K ON K.ID = E.category_id  \
                            left join res_users_config H on H.job_id=A.job_id  \
                            left join res_groups_res_users_config_rel G ON G.res_users_config_id=H.id \
                            where A.active=True and E.id=G.res_groups_id %s \
                            group by A.login,A.id,B.name,C.name,K.name,E.name,E.id,D.name"%(query_where,query_where)
            
            self.env.cr.execute(query_group)
            fetchall = self.env.cr.dictfetchall()
            count =0
            users_dic={}
            groups = {}
            for fetch in fetchall:
                group1 = fetch['user_id']
                if group1 not in users_dic:
                    users_dic [group1] = {
                    'login':u'Тодорхойгүй',
                    'user':u'Тодорхойгүй',
                    'job':u'Тодорхойгүй',
                    'department':u'Тодорхойгүй',
                    'groups':{}
                    }
                users_dic[group1]['login']=fetch['login']
                users_dic[group1]['user']=fetch['user']
                users_dic[group1]['job']=fetch['job']
                users_dic[group1]['department']=fetch['department']
                group2=fetch['group']
                if group2 not in users_dic[group1]['groups']:
                    users_dic[group1]['groups'][group2]={
                    'group':u'Тодорхойгүй',
                    'group_id':0,
                    }
                users_dic[group1]['groups'][group2]['group']=fetch['group']
                users_dic[group1]['groups'][group2]['group_id']=fetch['group_id']
                groupid= fetch['group_id']
                if groupid not in groups: 
                    groups[groupid]={
                    'group':u'Тодорхойгүй',
                    }
                groups[groupid]['group'] = fetch['group']
            row=2
            col=4
            get_group_columns = {}
            sheet.write(row, 0,'Нэвтрэх нэр' , header)                
            sheet.write(row, 1,'Нэр', header)                
            sheet.write(row, 2,u'Албан тушаал' , header)                
            sheet.write(row, 3,u'Хэлтэс' , header)

            for group in sorted(groups.values(),key=itemgetter('group')):
                sheet.set_column(2,col,20)
                sheet.write(row,col,group['group'],header)
                get_group_columns.update({group['group']:col})
                col+=1
            
            #sheet.merge_range(row,4,row,col-1,'Грүпп',cell_format_center)
            row+=1
            for user in sorted(users_dic.values(),key=itemgetter('user')):
                sheet.set_column(2,2,20)
                sheet.write(row, 0,user['login'] , cell_format_center)                
                sheet.write(row, 1,user['user'] , cell_format_center)                
                sheet.write(row, 2,user['job'] , cell_format_center)                
                sheet.write(row, 3,user['department'] , cell_format_center)
                for group in  sorted(user['groups'].values(),key=itemgetter('group')):
                    sheet.write(row, get_group_columns.get(group['group']),u'ERP эрх тохируулагдсан', cell_format_center)
                row+=1
        else:
            where = "where A.active=True"
            if self.job_ids:
                if len(self.job_ids)>1:
                    where=where+" and A.job_id in %s"%( str(tuple(self.job_ids.ids)))
                else:
                    where=where+" and A.job_id = %s"%(str(self.job_ids.ids[0]))
            if self.group_ids:
                if len(self.group_ids)>1:
                    where=where+" and E.id in %s"%( str(tuple(self.group_ids.ids)))
                else:
                    where=where+" and E.id = %s"%(str(self.group_ids.ids[0]))
           
            row=1
            sheet.write(row, 0,'Нэвтрэх нэр' , header)
            sheet.write(row, 1, 'Нэр' , header)
            sheet.write(row, 2,'Албан тушаал' , header)
            sheet.write(row, 3,'Салбар', header)
            sheet.write(row, 4,'Хэлтэс', header)
            sheet.write(row, 5,'Төсөл', header)
            sheet.write(row, 6,'Төсөв', header)
            sheet.write(row, 7,'Төлбөрийн хүсэлт', header)
            sheet.write(row, 8,'Хүргэлт', header)
            sheet.write(row, 9,'Хүний нөөц', header)
            sheet.write(row, 10,'Тусламжийн төв', header)
            sheet.write(row, 11,'Тендер', header)
            sheet.write(row, 12,'Архив', header)
            sheet.write(row, 13,'Гэрээ', header)
            sheet.write(row, 14,'Худалдан авалт', header)
            sheet.write(row, 15,'Тодорхойлолт хүсэлт', header)
            row=2

            query="select A.id as user_id,  A.login,B.name as user,C.name as job, D.name as department from res_users A \
                    left join res_partner B ON B.id=A.partner_id \
                    left join hr_job C ON C.id=A.job_id \
                    left join hr_department D ON D.id=A.department_id  "+where
                    
            self.env.cr.execute(query)
            dictfetchall=self.env.cr.dictfetchall()
            departments={}
            users= {}
            rowx=2
            for fetch in dictfetchall:
                self.env.cr.execute("select B.name,B.code from res_users A left join res_users_project_department_rel E ON E.uid=A.id \
                     left join hr_department B ON E.depid=B.id where B.active=True and A.id=%s"%fetch['user_id'])
                depfetchall=self.env.cr.dictfetchall()        
                row=rowx
                sheet.write(row, 0,fetch['login'] , cell_format_center)
                sheet.write(row, 1,fetch['user'] , cell_format_center)
                sheet.write(row, 2,fetch['job'] , cell_format_center)
                sheet.write(row, 3,fetch['department'] , cell_format_center)
                sheet.write(row, 4,fetch['department'] , cell_format_center)
                row1=row
                for dep in depfetchall:            
                    # sheet.write(row1, 5,dep['code'] , cell_format_center)
                    sheet.write(row1, 5,dep['name'] , cell_format_center)
                    row1+=1
                if row1==rowx:
                    rowx+=1
                else:
                    rowx=row1
                self.env.cr.execute("select B.name,B.code from res_users A left join res_users_budget_department_rel E ON E.uid=A.id \
                     left join hr_department B ON E.depid=B.id where B.active=True and  A.id=%s"%fetch['user_id'])
                depfetchall=self.env.cr.dictfetchall()                          
                row1=row
                for dep in depfetchall:            
                    # sheet.write(row1, 7,dep['code'] , cell_format_center)
                    sheet.write(row1, 6,dep['name'] , cell_format_center)
                    row1+=1
                if rowx<row1:
                    rowx=row1
                self.env.cr.execute("select B.name,B.code from res_users A left join res_users_payment_request_rel  E ON E.uid=A.id \
                     left join hr_department B ON E.depid=B.id where B.active=True and  A.id=%s"%fetch['user_id'])
                depfetchall=self.env.cr.dictfetchall()                          
                row1=row
                for dep in depfetchall:            
                    # sheet.write(row1, 7,dep['code'] , cell_format_center)
                    sheet.write(row1, 7,dep['name'] , cell_format_center)
                    row1+=1
                if rowx<row1:
                    rowx=row1

                self.env.cr.execute("select B.name,B.code from res_users A left join res_users_delivery_department_rel  E ON E.uid=A.id \
                     left join hr_department B ON E.depid=B.id where B.active=True and  A.id=%s"%fetch['user_id'])
                depfetchall=self.env.cr.dictfetchall()                          
                row1=row
                for dep in depfetchall:            
                    # sheet.write(row1, 7,dep['code'] , cell_format_center)
                    sheet.write(row1, 8,dep['name'] , cell_format_center)
                    row1+=1
                if rowx<row1:
                    rowx=row1


                self.env.cr.execute("select B.name,B.code from res_users A left join res_users_hr_department_rel  E ON E.uid=A.id \
                     left join hr_department B ON E.depid=B.id where B.active=True and  A.id=%s"%fetch['user_id'])
                depfetchall=self.env.cr.dictfetchall()                          
                row1=row
                for dep in depfetchall:            
                    # sheet.write(row1, 7,dep['code'] , cell_format_center)
                    sheet.write(row1, 9,dep['name'] , cell_format_center)
                    row1+=1
                if rowx<row1:
                    rowx=row1


                self.env.cr.execute("select B.name,B.code from res_users A left join res_users_helpdesk_department_rel  E ON E.uid=A.id \
                     left join hr_department B ON E.depid=B.id where B.active=True and  A.id=%s"%fetch['user_id'])
                depfetchall=self.env.cr.dictfetchall()                          
                row1=row
                for dep in depfetchall:            
                    # sheet.write(row1, 7,dep['code'] , cell_format_center)
                    sheet.write(row1, 10,dep['name'] , cell_format_center)
                    row1+=1
                if rowx<row1:
                    rowx=row1

                self.env.cr.execute("select B.name,B.code from res_users A left join res_users_tender_department_rel  E ON E.uid=A.id \
                     left join hr_department B ON E.depid=B.id where B.active=True and  A.id=%s"%fetch['user_id'])
                depfetchall=self.env.cr.dictfetchall()                          
                row1=row
                for dep in depfetchall:            
                    # sheet.write(row1, 7,dep['code'] , cell_format_center)
                    sheet.write(row1, 11,dep['name'] , cell_format_center)
                    row1+=1
                if rowx<row1:
                    rowx=row1

                self.env.cr.execute("select B.name,B.code from res_users A left join res_users_archive_department_rel  E ON E.uid=A.id \
                     left join hr_department B ON E.depid=B.id where B.active=True and  A.id=%s"%fetch['user_id'])
                depfetchall=self.env.cr.dictfetchall()                          
                row1=row
                for dep in depfetchall:            
                    # sheet.write(row1, 7,dep['code'] , cell_format_center)
                    sheet.write(row1, 12,dep['name'] , cell_format_center)
                    row1+=1
                if rowx<row1:
                    rowx=row1

                self.env.cr.execute("select B.name,B.code from res_users A left join res_users_department_rel  E ON E.uid=A.id \
                     left join hr_department B ON E.depid=B.id where B.active=True and  A.id=%s"%fetch['user_id'])
                depfetchall=self.env.cr.dictfetchall()                          
                row1=row
                for dep in depfetchall:            
                    # sheet.write(row1, 7,dep['code'] , cell_format_center)
                    sheet.write(row1, 13,dep['name'] , cell_format_center)
                    row1+=1
                if rowx<row1:
                    rowx=row1

                self.env.cr.execute("select B.name,B.code from res_users A left join  res_users_purchase_department_rel E ON E.uid=A.id \
                     left join hr_department B ON E.depid=B.id where B.active=True and  A.id=%s"%fetch['user_id'])
                depfetchall=self.env.cr.dictfetchall()                          
                row1=row
                for dep in depfetchall:            
                    # sheet.write(row1, 7,dep['code'] , cell_format_center)
                    sheet.write(row1, 14,dep['name'] , cell_format_center)
                    row1+=1
                if rowx<row1:
                    rowx=row1

                self.env.cr.execute("select B.name,B.code from res_users A left join res_users_loans_request_rel E ON E.uid=A.id \
                     left join hr_department B ON E.depid=B.id where B.active=True and  A.id=%s"%fetch['user_id'])
                depfetchall=self.env.cr.dictfetchall()                          
                row1=row
                for dep in depfetchall:            
                    # sheet.write(row1, 7,dep['code'] , cell_format_center)
                    sheet.write(row1, 15,dep['name'] , cell_format_center)
                    row1+=1
                if rowx<row1:
                    rowx=row1


        workbook.close()
        out = base64.encodestring(output.getvalue())
        file_name = u'Эрхийн тохиргооны тайлан'
        excel_id = self.env['report.excel.output'].sudo().create({'data':out,'name':file_name + '.xlsx'})

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
