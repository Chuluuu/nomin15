# -*- coding: utf-8 -*-
from openerp import api, fields, models, _
from datetime import date, datetime,timedelta
from dateutil.relativedelta import relativedelta
from openerp.exceptions import UserError, ValidationError, RedirectWarning

import requests
import json
import xmlrpclib
from zeep import Client
import base64


class SenderPreparation(models.TransientModel):
    _name = 'sender.preparation'

    def get_active_object(self):
        context = self._context
        if context.get('active_model') and context.get('active_id'):
            if context['active_model'] == 'asset.transfer.request' and context['active_id']:
                return self.env['asset.transfer.request'].browse(context['active_id'])


    def _transfer_date(self):
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        active_obj = self.get_active_object()
        if active_obj.transfer_date:
            return active_obj.transfer_date
        elif employee_id.parent_department:


            # return  datetime.strptime('2021-01-01', '%Y-%m-%d').date() 

            #  Tvr commentlow
            if employee_id.parent_department.nomin_code == "024" and date.today()<datetime.strptime('2021-04-01', '%Y-%m-%d').date() :
                return  datetime.strptime('2021-01-01', '%Y-%m-%d').date() 
            else:
                return date.today()
        else:            
            return date.today()


    def _account_from(self):
        active_obj = self.get_active_object()
        if active_obj.account_from:
            return active_obj.account_from
        else:
            return False

    def _department_id(self):

        # return 

        active_obj = self.get_active_object()
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        if active_obj.department_id:
            return active_obj.department_id
        elif employee_id.parent_department:
           
            return employee_id.parent_department

    def _type(self):
        active_obj = self.get_active_object()
        if active_obj:
            return active_obj.type
        else:
            return False

    def _is_same_company(self):
        return False

    @api.model
    def default_get(self, fields):
        res = super(SenderPreparation, self).default_get(fields)		
        transfer_request_id = self.env['asset.transfer.request'].browse(self._context.get('active_ids', []))
        prev_transfer_request_id = self.env['asset.transfer.request'].search([('department_id','=',transfer_request_id.department_id.id)],limit=1,order="create_date asc")
        if prev_transfer_request_id:
            res.update({'sender_account_receivable_id':prev_transfer_request_id.sender_account_receivable_id.id,
                        'sender_profit_account_id':prev_transfer_request_id.sender_profit_account_id.id,
                        'sender_vat_account_id':prev_transfer_request_id.sender_vat_account_id.id,
                        'sender_loss_account_id':prev_transfer_request_id.sender_loss_account_id.id,
                        })
        return res


    type = fields.Selection([
        ('asset',u'Хөрөнгө'),
        ('supply',u'Эд материал'),
    ], u'Tөрөл', required=True,  track_visibility='onchange', default = _type)

    is_same_company = fields.Boolean(string="Is same company", compute=_is_same_company, default=False)
    transfer_date = fields.Date('Гүйлгээний огноо', required=True, default=_transfer_date)
    department_id = fields.Many2one('hr.department', domain="[('is_sector', '=', True)]",string='Илгээгч салбар', required=True, default = _department_id)
    account_from = fields.Many2one('account.account', string='Account from', required=True, default = _account_from)

    receiver_department_id = fields.Many2one('hr.department', domain="[('is_sector', '=', True)]", string='Хүлээн авах салбар', required=True)#, default=_receiver_department_id)
    sender_vat_account_id = fields.Many2one('account.account',  string='Илгээгчийн НӨАТ-н данс',domain="[('department_id', '=', department_id)]")#, default = _sender_vat_account_id)
    sender_account_receivable_id = fields.Many2one('account.account',  string='Илгээгчийн авлагын данс', required=True)

    sender_profit_account_id = fields.Many2one('account.account',  string='Илгээгчийн олзын данс', required=True)
    sender_loss_account_id = fields.Many2one('account.account',  string='Илгээгчийн гарзын данс', required=True)


    description = fields.Text('Description')
    employee_ids = fields.Many2many('hr.employee','rel_hr_employee_timesheet_change_request',\
                                        'employee_id','timesheet_change_request_add_multiple_id', string='Employees', required=True)

    @api.multi
    def button_accept(self):

        active_obj = self.get_active_object()
        result = []

        if self.transfer_date:
            active_obj.transfer_date = self.transfer_date            

        if self.department_id:
            active_obj.department_id = self.department_id

        if self.type:
            active_obj.type = self.type

        if self.account_from:
            active_obj.account_from = self.account_from  

        if self.receiver_department_id:
            active_obj.receiver_department_id = self.receiver_department_id

        if self.sender_vat_account_id:
            active_obj.sender_vat_account_id = self.sender_vat_account_id


        if self.sender_account_receivable_id:
            active_obj.sender_account_receivable_id = self.sender_account_receivable_id

        if self.sender_profit_account_id:
            active_obj.sender_profit_account_id = self.sender_profit_account_id

        if self.sender_loss_account_id:
            active_obj.sender_loss_account_id = self.sender_loss_account_id


        if self.description:
            active_obj.description = self.description


        if self.type == 'asset':
            self.get_assets(active_obj)
        else:
            self.get_supplies(active_obj)

        return {'type': 'ir.actions.act_window_close'}


    @api.multi
    def get_assets(self,active_obj):

        url = self.env['integration.config'].sudo().search([('name','=','handle_asset_transfer')]).server_ip
        client = Client(url)

        # tst ---------------------------------------------------------------------------------
        # response = client.service.AssetGet("1",self.transfer_date,self.department_id.nomin_code,"0",str(self.account_from.code),"1","","1","","1","","1","")
        response = client.service.AssetGetNoLimit("1",self.transfer_date,self.department_id.nomin_code,"0",str(self.account_from.code),"1","","1","","1","","1","")
        # response = client.service.AssetGet("1",self.transfer_date,"0U1","0","200301000000000000000000","1","","1","","1","","1","")
        
        
        # if response.status_code == 200:	
        print '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n response',response
        if response:
            try:
                result_dict = json.loads(response)
            except ValueError as e:
                raise UserError(_('Мэдээлэл татахад алдаа гарлаа.\n Салбарын код [%s] Дансны дугаар [%s] Алдааны мессеж [%s] response [%s]'%(self.department_id.nomin_code,self.account_from.code,e,response)))
        
            if result_dict:
                if not active_obj.change_line_ids and "Assets" in result_dict:
                    if result_dict[u'InvDescription'] == "Failed":
                        raise UserError(_('Бэлтгэх гэж буй хөрөнгүүд дээр хөдөлгөөн хийгдсэн байна.'))
                    else:
                
                        for dictionary in result_dict[u'Assets']:
                            account_id = self.env['account.account'].search([('code','=',dictionary[u'FromAccountID']),('department_id','=',self.department_id.id)])

                            if not account_id:
                                raise UserError(_(dictionary[u'FromAccountID'] + ' гэсэн данс erp дээр алга байна!  '))
                            # product_id = self.env['product.template'].search([('code','=',dictionary[u'AssetID'])])
                            employee_id_id = 215
                            # tst ---------------------------------------------------------------------------------
                            employee_id = self.env['hr.employee'].search([('passport_id','=',dictionary[u'FromCustomerID'].upper())])
                            # employee_id = self.env['hr.employee'].search([('passport_id','=','ЧЙ77040671')])

                            asset_name = ''
                            if employee_id:
                                employee_id_id = employee_id.id
                                
                                asset_name =  dictionary[u'AssetDesc']
                            else:
                                asset_name =  dictionary[u'FromCustomerID'].upper() + ' <=> ' + dictionary[u'AssetDesc']


                            current_line = active_obj.sudo().change_line_ids.create({

                                'request_id':active_obj.id,
                                # 'product_id': product_id.id or False,
                                'asset_id':dictionary[u'AssetID'],
                                'registry_number':dictionary[u'RegistryNumberID'],
                                'asset_name':asset_name,
                                'receiver_stockkeeper':dictionary[u'FromAccountantInfID'],
                                'qty':dictionary[u'EndQty'],
                                'accumulated_depreciation':dictionary[u'EndDeprAmt'],
                                'current_value':dictionary[u'CurrentCost'],
                                'sale_price':dictionary[u'SaleAmt'],
                                'amount':dictionary[u'BeginUnitCost'],
                                'capitalized_value': dictionary[u'EndAmt'],
                                'start_date':dictionary[u'BeginUsedDate'],
                                'account_id':account_id.id,
                                'employee_id':employee_id_id,
                                'receiver_employee_id':employee_id_id,
                            })


                            dictionary[u'ToAccountantInfID'] = current_line.id

                            # if employee_id:
                            #     dictionary[u'ToAccountantInfID'] = current_line.id
                            # else:
                            #     dictionary[u'ToAccountantInfID'] = 999999999999



                            # if employee_id:
                            #     result.append((0,0,
                            #     {
                            #         'request_id':active_obj.id,
                            #         # 'product_id': product_id.id or False,
                            #         'asset_id':dictionary[u'AssetID'],
                            #         'registry_number':dictionary[u'RegistryNumberID'],
                            #         'asset_name':dictionary[u'AssetDesc'],
                            #         'receiver_stockkeeper':dictionary[u'FromAccountantID'],
                            #         'qty':dictionary[u'EndQty'],
                            #         'accumulated_depreciation':dictionary[u'EndDeprAmt'],
                            #         'current_value':dictionary[u'CurrentCost'],
                            #         'amount':dictionary[u'BeginUnitCost'],
                            #         'capitalized_value': dictionary[u'EndAmt'],
                            #         'start_date':dictionary[u'BeginUsedDate'],
                            #         'account_id':account_id.id,
                            #         'employee_id':employee_id.id,
                            #         'receiver_employee_id':employee_id.id,
                            #     }))
                            # else:
                            #     print 'employee_id ' ,dictionary[u'FromCustomerID'] 
                        # print 'ddddddddddddddddddddddddddddddd_     ',result

                    # json.dumps(result_dict)

                        active_obj.sudo().write(
                        {
                            # 'change_line_ids':result,
                            # 'diamond_json':json.dumps(result_dict),
                            'diamond_binary':base64.encodestring(json.dumps(result_dict)),                       
                        })


    @api.multi
    def get_supplies(self,active_obj):


        url = self.env['integration.config'].sudo().search([('name','=','handle_supply_transfer')]).server_ip
        client = Client(url)

        # splts ---------------------------------------------------------------------------------
        response = client.service.SupplyGet("1",self.transfer_date,self.department_id.nomin_code,"0",str(self.account_from.code),"1","","1","")
        # response = client.service.SupplyGet("1",self.transfer_date,"0U1","0","160701000000010000000001","1","","1","")
        
        # if response.status_code == 200:	
        print '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n response',response        
        if response:
            try:
                result_dict = json.loads(response)
            except ValueError as e:
                raise UserError(_('Мэдээлэл татахад алдаа гарлаа.\n Салбарын код [%s] Дансны дугаар [%s] Алдааны мессеж [%s] response [%s]'%(self.department_id.nomin_code,self.account_from.code,e,response)))
            if result_dict:

                if not active_obj.change_line_ids and "Supply" in result_dict:
                    for dictionary in result_dict[u'Supply']:
                        account_id = self.env['account.account'].search([('code','=',dictionary[u'FromAccountID']),('department_id','=',self.department_id.id)])[0]
                        # product_id = self.env['product.template'].search([('code','=',dictionary[u'AssetID'])])
                        employee_id_id = 215
                        # splts ---------------------------------------------------------------------------------
                        employee_id = self.env['hr.employee'].search([('passport_id','=',dictionary[u'FromCustomerID'].upper())])
                        # employee_id = self.env['hr.employee'].search([('passport_id','=','ЧЙ77040671')])
                        print '\n\n\n\n\n\n\n\n\n\n\n\n\nzzzzz ',dictionary[u'ItemID']
                        
                        supply_name = dictionary[u'ItemDesc']
                        if employee_id:
                            employee_id_id = employee_id.id
                        else:
                            supply_name =  dictionary[u'FromCustomerID'].upper() + ' <=> ' + dictionary[u'ItemDesc']

                        current_line = active_obj.sudo().change_line_ids.create({

                            'request_id':active_obj.id,
                            # 'product_id': product_id.id or False,
                            'asset_id':dictionary[u'ItemID'],
                            # 'registry_number':dictionary[u'RegistryNumberID'],
                            'asset_name':supply_name,
                            # 'receiver_stockkeeper':dictionary[u'FromAccountantInfID'],
                            'qty':dictionary[u'EndQty'],
                            # 'accumulated_depreciation':dictionary[u'EndDeprAmt'],
                            # 'current_value':dictionary[u'CurrentCost'],
                            'sale_price':dictionary[u'SaleAmt'],
                            'amount':dictionary[u'BeginUnitCost'],
                            'capitalized_value': dictionary[u'EndAmt'],
                            'start_date':dictionary[u'BeginUsedDate'],
                            'account_id':account_id.id,
                            'employee_id':employee_id_id,
                            'receiver_employee_id':employee_id_id,
                        })


                        dictionary[u'ToSupplyLocationInfID'] = current_line.id
                        # if employee_id:
                        #     dictionary[u'ToSupplyLocationInfID'] = current_line.id
                        # else:
                        #     dictionary[u'ToSupplyLocationInfID'] = 999999999999



                        # if employee_id:
                        #     result.append((0,0,
                        #     {
                        #         'request_id':active_obj.id,
                        #         # 'product_id': product_id.id or False,
                        #         'asset_id':dictionary[u'AssetID'],
                        #         'registry_number':dictionary[u'RegistryNumberID'],
                        #         'asset_name':dictionary[u'AssetDesc'],
                        #         'receiver_stockkeeper':dictionary[u'FromAccountantID'],
                        #         'qty':dictionary[u'EndQty'],
                        #         'accumulated_depreciation':dictionary[u'EndDeprAmt'],
                        #         'current_value':dictionary[u'CurrentCost'],
                        #         'amount':dictionary[u'BeginUnitCost'],
                        #         'capitalized_value': dictionary[u'EndAmt'],
                        #         'start_date':dictionary[u'BeginUsedDate'],
                        #         'account_id':account_id.id,
                        #         'employee_id':employee_id.id,
                        #         'receiver_employee_id':employee_id.id,
                        #     }))
                        # else:
                        #     print 'employee_id ' ,dictionary[u'FromCustomerID'] 
                    # print 'ddddddddddddddddddddddddddddddd_     ',result

                    # json.dumps(result_dict)

                    active_obj.sudo().write(
                    {
                        # 'change_line_ids':result,
                        # 'diamond_json':json.dumps(result_dict),
                        'diamond_binary':base64.encodestring(json.dumps(result_dict)),                
                    })




    @api.onchange('receiver_department_id')
    def onchange_receiver_department_id(self):


        if self.department_id.company_id ==  self.receiver_department_id.company_id:
            self.is_same_company = True
        else:
            self.is_same_company = False



    @api.onchange('type')
    def onchange_type(self):

        if self.type == 'asset':
            return {'domain':
                            {'account_from':[('department_id', '=', self.department_id.id),('user_type_id', 'in', [198,228] )]}}
        elif self.type == 'supply':
            return {'domain':
                            {'account_from':[('department_id', '=', self.department_id.id),('user_type_id', '=',[254,255,257] )]}}

        




class ReceiverPreparation(models.TransientModel):
    _name = 'receiver.preparation'


    def _receiver_vat_account_id(self):
        context = self._context
        if context.get('active_model') and context.get('active_id'):
            if context['active_model'] == 'asset.transfer.request' and context['active_id']:
                active_obj = self.env['asset.transfer.request'].browse(context['active_id'])
                result = []	
                if active_obj:
                    return active_obj.receiver_vat_account_id
                else:
                    return False


    def _receiver_account_payable_id(self):
        context = self._context
        if context.get('active_model') and context.get('active_id'):
            if context['active_model'] == 'asset.transfer.request' and context['active_id']:
                active_obj = self.env['asset.transfer.request'].browse(context['active_id'])
                result = []	
                if active_obj:
                    return active_obj.receiver_account_payable_id
                else:
                    return False

    def _department_id(self):
        context = self._context
        if context.get('active_model') and context.get('active_id'):
            if context['active_model'] == 'asset.transfer.request' and context['active_id']:
                active_obj = self.env['asset.transfer.request'].browse(context['active_id'])
                result = []	
                if active_obj:
                    return active_obj.department_id
                else:
                    return False



    def _receiver_department_id(self):
        context = self._context
        if context.get('active_model') and context.get('active_id'):
            if context['active_model'] == 'asset.transfer.request' and context['active_id']:
                active_obj = self.env['asset.transfer.request'].browse(context['active_id'])
                result = []	
                if active_obj:
                    if active_obj.receiver_department_id:
                        return active_obj.receiver_department_id
                    else:
                        active_obj.department_id
                else:
                    return False

                    
    def _is_same_company(self):

        if self.department_id.company_id ==  self.receiver_department_id.company_id:
            self.is_same_company = True
        else:
            self.is_same_company = False



    def _type(self):
        context = self._context
        if context.get('active_model') and context.get('active_id'):
            if context['active_model'] == 'asset.transfer.request' and context['active_id']:
                active_obj = self.env['asset.transfer.request'].browse(context['active_id'])
                result = []	
                if active_obj:
                    return active_obj.type
                else:
                    return False


    type = fields.Selection([
        ('asset',u'Хөрөнгө'),
        ('supply',u'Эд материал'),
    ], u'Tөрөл', required=True,  track_visibility='onchange', default = _type)


    is_same_company = fields.Boolean(string="Is same company", compute=_is_same_company, default=False)
    transfer_date = fields.Date('Transfer date', readonly=True)
    department_id = fields.Many2one('hr.department', domain="[('is_sector', '=', True)]",string='Илгээгч салбар', required=True, default = _department_id)
    
    receiver_department_id = fields.Many2one('hr.department', domain="[('is_sector', '=', True)]", string='Хүлээн авагч салбар', readonly=True, default = _receiver_department_id)
    account_to = fields.Many2one('account.account', string='Хүлээн авагчийн хөрөнгийн данс', required=True)
    receiver_depreciation_account_id = fields.Many2one('account.account', string='Хүлээн авагчийн элэгдлийн данс',domain="[('department_id', '=', receiver_department_id)]", required=True)

    receiver_vat_account_id = fields.Many2one('account.account',  string='Хүлээн авагчийн НӨАТ данс')#, default= _receiver_vat_account_id)
    receiver_account_payable_id = fields.Many2one('account.account',  string='Хүлээн авагчийн өглөгийн данс',required=True)#,default= _receiver_account_payable_id)

    description = fields.Text('Тайлбар')
    # employee_ids = fields.Many2many('hr.employee','rel_hr_employee_timesheet_change_request',\
    #                                     'employee_id','timesheet_change_request_add_multiple_id', string='Employees', required=True)
    
    employee_id = fields.Many2one('hr.employee', string='Employee')
    receiver_employee_id = fields.Many2one('hr.employee',  string='Receiver employee')
    


    @api.multi
    def button_accept(self):
        context = self._context

        context = self._context
        if context.get('active_model') and context.get('active_id'):
            if context['active_model'] == 'asset.transfer.request' and context['active_id']:
                active_obj = self.env['asset.transfer.request'].browse(context['active_id'])
                result = []	

                if self.description:
                    if active_obj.description:
                        active_obj.description = active_obj.description + self.description
                    else:
                        active_obj.description = self.description


                if self.receiver_vat_account_id:
                    active_obj.receiver_vat_account_id = self.receiver_vat_account_id

                if self.receiver_account_payable_id:
                    active_obj.receiver_account_payable_id = self.receiver_account_payable_id


                for line in active_obj.change_line_ids:

                    if self.account_to:
                        line.receiver_asset_account_id = self.account_to

                    if self.receiver_depreciation_account_id:
                        line.receiver_depreciation_account_id = self.receiver_depreciation_account_id

                    if self.employee_id and self.receiver_employee_id:
                        if line.employee_id == self.employee_id:
                            line.receiver_employee_id = self.receiver_employee_id


                return 

        return {'type': 'ir.actions.act_window_close'}




class PrepareTransferRequest(models.TransientModel):
    _name = 'prepare.transfer.request'


    def _transfer_date(self):

        return date.today()


    def get_active_object(self):
        context = self._context
        if context.get('active_model') and context.get('active_id'):
            if context['active_model'] == 'asset.transfer.request' and context['active_id']:
                return self.env['asset.transfer.request'].browse(context['active_id'])


    def _set_employee(self): 
        employee_ids = self.env['hr.employee'].search([('user_id','=',self.env.user.id)], limit=1)
        if employee_ids:
            return employee_ids.id
        else:
            raise UserError(_('You don\'t have related company. Please contact administrator.'))
        return None


    def _set_department(self): 

        employee_ids = self.env['hr.employee'].search([('user_id','=',self.env.user.id)], limit=1)
        if employee_ids:
            return employee_ids.parent_department
        else:
            raise UserError(_('You don\'t have related company. Please contact administrator.'))
        return None


    @api.multi
    def compute_asset_request(self):
        for line in self:

            line.warning_type = "normal"


    type = fields.Selection([
        ('asset',u'Хөрөнгө'),
        ('supply',u'Эд материал'),
    ], u'Tөрөл', required=True,  track_visibility='onchange')

    transfer_date = fields.Date('Transfer date', required=True, default=_transfer_date)

    employee_id = fields.Many2one('hr.employee', required=True, string='Employee', default = _set_employee)
    job_id = fields.Many2one('hr.job', string='Job')
    department_id = fields.Many2one('hr.department', string='Department', required=True, default = _set_department)
    
    warning_type = fields.Char(u'Warning type', compute="compute_asset_request", store=True)
    request_id = fields.Many2one('asset.transfer.request', string='Request', ondelete='cascade')
    search_type = fields.Selection([
        ('all',u'Бүх төрлөөр хайх'),
        ('by_name',u'Хөрөнгийн нэрээр'),
        ('by_code',u'Хөрөнгийн кодоор'),
        ('by_code_multiple',U'Хөрөнгийн код /олноор/'),
        ('by_account',u'Дансаар'),
        ], 'Хайх төрөл', default = 'all')

    search_string = fields.Char(string='Хайх үг')

    receiver_employee_id = fields.Many2one('hr.employee', required=True, string='Хүлээн авах ажилтан')
    receiver_job_id = fields.Many2one('hr.job', string='Receiver job')
    receiver_department_id = fields.Many2one('hr.department', string='Receiver department')
    account_from = fields.Many2one('account.account', string='Account from')
    no_customer_selection = fields.Boolean(string='No customer selection')


    @api.onchange('employee_id')
    def onchange_employee(self):
        if self.employee_id:
            self.set_employee_information(self)

    @api.onchange('receiver_employee_id')
    def onchange_receiver_employee(self):
        if self.receiver_employee_id:
            self.set_employee_information(self)

    @api.model
    def create(self, vals):

        result = super(PrepareTransferRequest, self).create(vals)
        self.set_employee_information(result)
        return result

    @api.multi
    def write(self, vals):
        result = super(PrepareTransferRequest, self).write(vals)
        if vals.get('employee_id'):
            self.set_employee_information(self)
        return result

    def set_employee_information(self, result):
        result.job_id = result.employee_id.job_id or None
        # result.department_id = result.employee_id.parent_department or None
        result.receiver_job_id = result.receiver_employee_id.job_id or None
        result.receiver_department_id = result.receiver_employee_id.parent_department or None
            
    @api.multi
    def button_accept(self):

        # 
        active_obj = self.request_id if self.request_id else self.get_active_object()
        result = []

        if self.transfer_date:
            active_obj.transfer_date = self.transfer_date            

        if self.department_id:
            active_obj.department_id = self.department_id

        if self.type:
            active_obj.type = self.type

        if self.receiver_department_id:
            active_obj.receiver_department_id = self.receiver_department_id

        if self.type == 'asset':
            self.get_assets(active_obj)
        else:
            self.get_supplies(active_obj)


        return {'type': 'ir.actions.act_window_close'}



    @api.multi
    def get_assets(self,active_obj):

        # if self.department_id == self.receiver_department_id:
        #     raise UserError('Хэрэв хөрөнгийг салбар дотороо шилжүүлэх гэж байгаа бол хариуцсан нягтлангаараа хийлгэ!')


        url = self.env['integration.config'].sudo().search([('name','=','handle_asset_transfer')]).server_ip
        client = Client(url)
        if self.sudo().employee_id.passport_id:

            print 'ddddddddddddddddddddddddddd+++++++++++++++++='

            if not self.search_string:
                self.search_string = ""
            asset_type ="1"
            search_string = self.search_string
            account_type ="1"
            account_from = ""
            
            if self.search_type == 'by_name':
                asset_type = "3"
            elif self.search_type == 'by_code_multiple':
                asset_type = "2"
            elif self.search_type == 'by_code':
                asset_type = "5"
            elif self.search_type == 'by_account':
                search_string = ""
                account_type = "0"
                account_from = str(self.account_from.code)

            customer_selection_type  = "0" if not self.no_customer_selection else "1"
            customer_selection = self.sudo().employee_id.passport_id if not self.no_customer_selection else ""
            

            response = client.service.AssetGetWithCheck("1",self.transfer_date,self.sudo().department_id.nomin_code,account_type,account_from,"1","","1","",asset_type,search_string,customer_selection_type,customer_selection)
            try:
                result_dict = json.loads(response)
            except ValueError as e:
                raise UserError(_('Мэдээлэл татахад алдаа гарлаа.\n Салбарын код [%s] Алдааны мессеж [%s] response [%s]'%(self.department_id.nomin_code,e,response)))
            if result_dict:
                print '\n dddddddddd ',response


                if "Assets" in result_dict:

                    if active_obj.change_line_ids and active_obj.state == 'draft':
                        active_obj.sudo().write({'change_line_ids': [(6,0,[])]})

                    if not active_obj.change_line_ids:
                        for dictionary in result_dict[u'Assets']:
                            account_id = self.env['account.account'].search([('code','=',dictionary[u'FromAccountID']),('department_id','=',self.department_id.id)])
                            # product_id = self.env['product.template'].search([('code','=',dictionary[u'AssetID'])])

                            employee_id = self.env['hr.employee'].search([('passport_id','=',dictionary[u'FromCustomerID'].upper())])
                            # employee_id = self.env['hr.employee'].search([('passport_id','=','ЧЙ77040671')])


                            if employee_id:
                            
                                current_line = active_obj.change_line_ids.sudo().create({
                                    'request_id':active_obj.id,
                                    # 'product_id': product_id.id or False,
                                    'asset_id':dictionary[u'AssetID'],
                                    'registry_number':dictionary[u'RegistryNumberID'],
                                    'asset_name':dictionary[u'AssetDesc'],
                                    'receiver_stockkeeper':dictionary[u'FromAccountantInfID'],
                                    'qty':dictionary[u'EndQty'],
                                    'accumulated_depreciation':dictionary[u'EndDeprAmt'],
                                    'current_value':dictionary[u'CurrentCost'],
                                    'sale_price':dictionary[u'SaleAmt'],
                                    'amount':dictionary[u'BeginUnitCost'],
                                    'capitalized_value': dictionary[u'EndAmt'],
                                    'start_date':dictionary[u'BeginUsedDate'],
                                    'account_id':account_id.id,
                                    'employee_id':employee_id.id,
                                    'receiver_employee_id':self.receiver_employee_id.id,
                                })

                                dictionary[u'ToAccountantInfID'] = current_line.id
                            else:
                                dictionary[u'ToAccountantInfID'] = 999999999999
                

                        active_obj.sudo().write(
                        {
                            # 'change_line_ids':result,
                            # 'diamond_json':json.dumps(result_dict),
                            'diamond_binary':base64.encodestring(json.dumps(result_dict)),                
                        
                        })




    @api.multi
    def get_supplies(self,active_obj):

        url = self.env['integration.config'].sudo().search([('name','=','handle_supply_transfer')]).server_ip
        client = Client(url)
        if self.sudo().employee_id.passport_id:
            
            # splts ---------------------------------------------------------------------------------
            response = client.service.SupplyGet("1",self.transfer_date,self.sudo().department_id.nomin_code,"1","","1","","0",self.sudo().employee_id.passport_id)
            # response = client.service.SupplyGet("1",self.transfer_date,"0U1","1","","1","","0","СВ97022708")
            # ЕЮ95113006
            # if response.status_code == 200:	
            try:
                result_dict = json.loads(response)
            except ValueError as e:
                raise UserError(_('Мэдээлэл татахад алдаа гарлаа.\n Салбарын код [%s] Дансны дугаар [%s] Алдааны мессеж [%s] response [%s]'%(self.department_id.nomin_code,self.account_from.code,e,response)))
            if result_dict:
                print '\n dddddddddd ',response

                if not active_obj.change_line_ids and "Supply" in result_dict:
                    for dictionary in result_dict[u'Supply']:
                        # print '\nffffffffff ',dictionary
                        account_id = self.env['account.account'].search([('code','=',dictionary[u'FromAccountID']),('department_id','=',self.department_id.id)])
                        # product_id = self.env['product.template'].search([('code','=',dictionary[u'AssetID'])])

                        # splts ---------------------------------------------------------------------------------
                        employee_id = self.env['hr.employee'].search([('passport_id','=',dictionary[u'FromCustomerID'].upper())])
                        # employee_id = self.env['hr.employee'].search([('passport_id','=','ЧЙ77040671')])


                        if employee_id:
                        
                            current_line = active_obj.change_line_ids.sudo().create({
                                'request_id':active_obj.id,
                                # 'product_id': product_id.id or False,
                                'asset_id':dictionary[u'ItemID'],
                                # 'registry_number':dictionary[u'RegistryNumberID'],
                                'asset_name':dictionary[u'ItemDesc'],
                                # 'receiver_stockkeeper':dictionary[u'FromAccountantInfID'],
                                'qty':dictionary[u'EndQty'],
                                # 'accumulated_depreciation':dictionary[u'EndDeprAmt'],
                                # 'current_value':dictionary[u'CurrentCost'],
                                'sale_price':dictionary[u'SaleAmt'],
                                'amount':dictionary[u'BeginUnitCost'],
                                'capitalized_value': dictionary[u'EndAmt'],
                                'start_date':dictionary[u'BeginUsedDate'],
                                'account_id':account_id.id,
                                'employee_id':employee_id.id,
                                'receiver_employee_id':self.receiver_employee_id.id,
                            })

                            dictionary[u'ToSupplyLocationInfID'] = current_line.id
                        else:
                            dictionary[u'ToSupplyLocationInfID'] = 999999999999

                    # print 'ddddddddddddddddddddddddddddddd_     ',result
                    active_obj.sudo().write(
                    {
                        # 'change_line_ids':result,
                        # 'diamond_json':json.dumps(result_dict),
                        'diamond_binary':base64.encodestring(json.dumps(result_dict)),                
                    
                    })


                if not active_obj.change_line_ids and "Assets" in result_dict:
                    for dictionary in result_dict[u'Assets']:
                        # print '\nffffffffff ',dictionary
                        account_id = self.env['account.account'].search([('code','=',dictionary[u'FromAccountID']),('department_id','=',self.department_id.id)])
                        # product_id = self.env['product.template'].search([('code','=',dictionary[u'AssetID'])])

                        employee_id = self.env['hr.employee'].search([('passport_id','=',dictionary[u'FromCustomerID'].upper())])
                        # employee_id = self.env['hr.employee'].search([('passport_id','=','ЧЙ77040671')])


                        if employee_id:
                        
                            current_line = active_obj.change_line_ids.sudo().create({
                                'request_id':active_obj.id,
                                # 'product_id': product_id.id or False,
                                'asset_id':dictionary[u'AssetID'],
                                'registry_number':dictionary[u'RegistryNumberID'],
                                'asset_name':dictionary[u'AssetDesc'],
                                'receiver_stockkeeper':dictionary[u'FromAccountantInfID'],
                                'qty':dictionary[u'EndQty'],
                                'accumulated_depreciation':dictionary[u'EndDeprAmt'],
                                'current_value':dictionary[u'CurrentCost'],
                                'sale_price':dictionary[u'SaleAmt'],
                                'amount':dictionary[u'BeginUnitCost'],
                                'capitalized_value': dictionary[u'EndAmt'],
                                'start_date':dictionary[u'BeginUsedDate'],
                                'account_id':account_id.id,
                                'employee_id':employee_id.id,
                                'receiver_employee_id':self.receiver_employee_id.id,
                            })

                            dictionary[u'ToSupplyLocationInfID'] = current_line.id
                        else:
                            dictionary[u'ToSupplyLocationInfID'] = 999999999999

                    # print 'ddddddddddddddddddddddddddddddd_     ',result
                    active_obj.sudo().write(
                    {
                        # 'change_line_ids':result,
                        # 'diamond_json':json.dumps(result_dict),
                        'diamond_binary':base64.encodestring(json.dumps(result_dict)),                
                    
                    })

