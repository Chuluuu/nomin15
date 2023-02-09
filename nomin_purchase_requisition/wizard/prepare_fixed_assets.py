# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import date, datetime,timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError, RedirectWarning

import requests
import json
from zeep import Client
import base64


class AssetPreparation(models.TransientModel):
    _name = 'asset.preparation'

    def get_active_object(self):
        context = self._context
        if context.get('active_model') and context.get('active_id'):
            if context['active_model'] == 'fixed.asset.counting' and context['active_id']:
                return self.env['fixed.asset.counting'].browse(context['active_id'])


    def _start_date(self):
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        active_obj = self.get_active_object()


        return date.today()




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
        res = super(AssetPreparation, self).default_get(fields)		
        request_id = self.env['fixed.asset.counting'].browse(self._context.get('active_ids', []))

        default_date = date.today() - timedelta(days=70)
        prev_request_id = self.env['fixed.asset.counting'].search([('start_date','>',default_date),('department_id','=',request_id.department_id.id)],limit=1,order="start_date desc")
        if prev_request_id:
           
            res.update({'start_date':prev_request_id.start_date,
                        })
        return res



    type = fields.Selection([
        ('audit',u'Audit - Хяналтын тооллого'),
        ('basic',u'Basic - Үндсэн тооллого'),
        ('handover',u'Handover - Хүлээлцэх тооллого'),
    ], u'Tооллогын төрөл',required=True)


    filter_options = fields.Selection([
        ('аccount',u'Account - Дансаар шүүх'),
        ('owner',u'Owner - Эд хариуцагчаар шүүх'),
        ('code',u'Code - Хөрөнгийн кодоор шүүх'),
        ('type',u'Type - Данс ба хөрөнгийн бүлгээр шүүх'),
        ('location',u'Location - Байршил ба дансаар шүүх')
    ], u'Хөрөнгө шүүх сонголтууд',  required=True)

    
    is_same_company = fields.Boolean(string="Is same company", compute=_is_same_company, default=False)
    start_date = fields.Date('Тооллого эхэлсэн огноо', required=True, default=_start_date)
    end_date = fields.Date('Тооллого дууссан огноо', required=True)
    department_id = fields.Many2one('hr.department', domain="[('is_sector', '=', True)]",string='Тооллого хийх салбар', required=True)
    account_from = fields.Many2one('account.account', string='Account from', domain="[('department_id', '=', department_id)]")
    employee_id = fields.Many2one('hr.employee', string='Ажилтны нэр' ,domain="[('parent_department', '=', department_id)]")
    location = fields.Char('Байршилын нэр')
    asset_code = fields.Char('Хөрөнгийн код')
    # TODO FIX LATER
    # asset_type = fields.Many2one('fixed.assets.type', string='Хөрөнгийн бүлэг', domain="[('department_id', '=', department_id)]")
    asset_type = fields.Many2one('fixed.assets.type', string='Хөрөнгийн бүлэг')
    description = fields.Char('Description', required=True)




    @api.onchange('filter_options')
    def onchange_filter_options(self):

        if self.filter_options == 'owner':
            self.account_from = False
        else:
            self.employee_id = False
        
        if not self.filter_options == 'location':
            self.location = False
        



    
    def button_accept(self):

        active_obj = self.get_active_object()
        result = []

        if self.start_date:
            active_obj.start_date = self.start_date  

        if self.end_date:
            active_obj.end_date = self.end_date           

        if self.department_id:
            active_obj.department_id = self.department_id

        if self.type:
            active_obj.type = self.type

        if self.account_from:
            active_obj.account_from = self.account_from  

        if self.filter_options:
            active_obj.filter_options = self.filter_options


        if self.location:
            active_obj.location = self.location

        if self.employee_id:
            active_obj.employee_id = self.employee_id

        if self.asset_type:
            active_obj.asset_type = self.asset_type


        if self.description:
            active_obj.description = self.description

        type = self.type[0].upper()
        filter_options = self.filter_options[0].upper()

        active_obj.name = self.department_id.nomin_code + str(self.start_date)[2:4] + type  + str(self.start_date)[5:7] + filter_options




        self.get_assets(active_obj)


        return {'type': 'ir.actions.act_window_close'}



    
    def get_assets(self,active_obj):

        url = self.env['integration.config'].sudo().search([('name','=','handle_asset_transfer')]).server_ip
        client = Client(url)


        account_type ="1"
        account_from =""

        location_type ="1"
        location_string = ""

        asset_type ="1"
        asset_string = ""

        customer_type ="1"
        customer_string = ""


        if self.filter_options == 'owner':
            customer_type = "0"
            customer_string = self.sudo().employee_id.passport_id
        else:
            account_type = "0"
            account_from = str(self.account_from.code)

            
        if self.filter_options == 'type':
            asset_type = "4"
            asset_string = self.asset_type.inf_id

        if self.filter_options == 'location':
            location_type = "3"
            location_string = self.location

        asset_dict = {
            'account_type': account_type,
            'account_from':account_from,
            'location_type':location_type,
            'location_string':location_string,
            'asset_type':asset_type,
            'asset_string':asset_string,
            'customer_type':customer_type,
            'customer_string':customer_string,          
        }

        active_obj.sudo().write(
        {
            'json_data':json.dumps(asset_dict)               
        })

       



        response = client.service.AssetCountGetForSum("1",self.start_date,self.department_id.nomin_code,account_type,account_from,location_type,location_string,"1","",asset_type,asset_string,customer_type,customer_string)

        if response:
            try:
                result_dict = json.loads('['+response+']')
            except ValueError as e:
                raise UserError(_('Мэдээлэл татахад алдаа гарлаа.\n Салбарын код [%s] Дансны дугаар [%s] Алдааны мессеж [%s] response [%s]'%(self.department_id.nomin_code,self.account_from.code,e,response)))
            if result_dict:

                count_of_items = 0
                owner_ids=[]
                count_of_owners = 0
                count_of_rows = 0
                asset_ids=[]
                count_of_assets = 0


                active_obj.sudo().change_line_ids = False

                for dictionary in result_dict:


                    account_id = self.env['account.account'].search([('code','=',dictionary[u'AccountID']),('department_id','=',self.department_id.id)])

                    if not account_id:
                        raise UserError(_(dictionary[u'AccountID'] + ' гэсэн данс erp дээр алга байна!  '))


                    depreciation_account = self.env['account.account'].search([('code','=',dictionary[u'DeprAccountID']),('department_id','=',self.department_id.id)])

                    depreciation_account_id = False
                    if depreciation_account:
                        depreciation_account_id = depreciation_account.id

                    employee_id_id = 215
                    employee_id = self.env['hr.employee'].search([('passport_id','=',dictionary[u'CustomerID'].upper())])

                    asset_name = ''
                    if employee_id:
                        employee_id_id = employee_id.id
                        
                        asset_name =  dictionary[u'AssetDesc']
                    else:
                        asset_name =  dictionary[u'CustomerID'].upper() + ' <=> ' + dictionary[u'AssetDesc']

                    count_of_items += dictionary[u'EndQty']

                    if employee_id_id not in (owner_ids):
                        owner_ids.append(employee_id_id)
                        count_of_owners += 1
                    count_of_rows += 1


                    if dictionary[u'AssetID'] not in (asset_ids):
                        asset_ids.append(dictionary[u'AssetID'])
                        count_of_assets += 1



                    current_line = active_obj.sudo().change_line_ids.create({

                        'request_id':active_obj.id,
                        'amount':dictionary[u'EndAmt'],
                        'asset_id':dictionary[u'AssetID'],
                        'asset_name':asset_name,
                        'qty':dictionary[u'EndQty'],
                        'counted_qty':dictionary[u'EndQty'],
                        'account_id':account_id.id,
                        'depreciation_account':depreciation_account_id,
                        'employee_id':employee_id_id,
                        'department_id':active_obj.department_id.id,
                        'backup_id':active_obj.id,
                        'current_qty':dictionary[u'EndQty'],

                    })


                active_obj.sudo().write({
                    'qty':count_of_items,
                    'count_of_owners':count_of_owners,
                    'count_of_rows':count_of_rows,
                    'count_of_assets':count_of_assets,
                })


class AssetSolution(models.TransientModel):
    _name = 'asset.solution'
 

    @api.model
    def default_get(self, fields):
        res = super(AssetSolution, self).default_get(fields)		
        line_id = self.env['fixed.asset.counting.line'].sudo().browse(self._context.get('active_ids', []))


        detail_ids= []
        if not line_id.sudo().detail_ids:

            url = self.env['integration.config'].sudo().search([('name','=','handle_asset_transfer')]).server_ip
            client = Client(url)

            
            passport_id = line_id.employee_id.sudo().passport_id

            if line_id.employee_id.id == 215:
                passport_id = line_id.asset_name[0:10]


            response = client.service.AssetCountGetDetail("1",line_id.request_id.start_date,line_id.request_id.department_id.nomin_code,"1","","1","","1","","0",line_id.asset_id,"0",passport_id)
            if response:
                try:
                    result_dict = json.loads(response)
                    line_id.diamond_json = response
                except ValueError as e:
                    raise UserError(_('Мэдээлэл татахад алдаа гарлаа.\n Алдааны код [%s] '%(response)))
            


                if result_dict:
                    if "Assets" in result_dict:
                        for dictionary in result_dict[u'Assets']:

                            employee_id_id = 215
                            employee_id = self.env['hr.employee'].sudo().search([('passport_id','=',dictionary[u'CustomerID'].upper())])


                            asset_name = ''
                            if employee_id:
                                employee_id_id = employee_id.id
                                
                                asset_name =  dictionary[u'AssetDesc']
                            else:
                                asset_name =  dictionary[u'CustomerID'].upper() + ' <=> ' + dictionary[u'AssetDesc']
                            
                            start_date = datetime.strptime(str(dictionary[u'BeginUsedDate']), '%Y/%m/%d')
                            

                            struct_value = {

                                'line_id':line_id.id,

                                'accumulated_depreciation':dictionary[u'EndDeprAmt'],
                                'current_value':dictionary[u'CurrentCost'],
                                'amount':dictionary[u'BeginUnitCost'],
                                'capitalized_value': dictionary[u'EndAmt'],
                                'start_date':datetime.strftime(start_date, '%Y-%m-%d'),
                                'registry_number':dictionary[u'RegistryNumberID'],
                                'damage_description':'normal',
                                'damage_desc':'',
                                'asset_state':'used',

                            }

                            detail_ids.append((0,0,struct_value))

                        #     dictionary.update({'SaleQty':"100"})
                        #     # dictionary[u'ToSupplyLocationInfID'] = line_id.id
                        # result_dict.update({'erp_id':line_id.id})
                        # line_id.sudo().write(
                        # {
                        #     'diamond_json':json.dumps(result_dict),                
                        # })


        else:

            for detail in line_id.sudo().detail_ids:	
                start_date = False
                account_move_id = False
                account_move_id_for_accountant = False
                if detail.start_date:
                    start_date = detail.start_date #datetime.strptime(detail.start_date,"%Y/%m/%d")
                if detail.account_move_id:
                    account_move_id = detail.account_move_id.id
                if detail.account_move_id_for_accountant:
                    account_move_id_for_accountant = detail.account_move_id_for_accountant.id

                detail_ids.append((0,0,{
                    'line_id':line_id.id,
                    'accumulated_depreciation':detail.accumulated_depreciation,
                    'current_value':detail.current_value,
                    'amount':detail.amount,
                    'capitalized_value': detail.capitalized_value,
                    'employee_id': detail.employee_id.id,
                    'is_expense':detail.is_expense,
                    'registry_number':detail.registry_number,
                    'start_date':start_date,
                    'damage_description':detail.damage_description,
                    'damage_desc':detail.damage_desc,
                    'asset_state':detail.asset_state,
                    'account_move_id':account_move_id,
                    'account_move_id_for_accountant':account_move_id_for_accountant,
                }))




        account_id = line_id.sudo().account_id
        depreciation_account = line_id.sudo().depreciation_account
        account_receivable_id = line_id.sudo().account_receivable_id
        receivable_income_account_id = line_id.sudo().receivable_income_account_id

        if not depreciation_account:
            prev_line_id = self.env['fixed.asset.counting.line'].sudo().search([('department_id','=',line_id.request_id.department_id.id),('state','in',['count','verify','verified']),('account_id','=',account_id.id),('depreciation_account','!=',False)],limit=1,order="id desc")
            if prev_line_id:

                depreciation_account = prev_line_id.sudo().depreciation_account
                account_receivable_id = prev_line_id.sudo().account_receivable_id
                receivable_income_account_id = prev_line_id.sudo().receivable_income_account_id

        res.update({
            'employee_id':line_id.employee_id.id,
            'department_id':line_id.request_id.department_id.id,
            'counted_qty':line_id.counted_qty,
            'current_qty':line_id.current_qty,
            'qty':line_id.qty,
            'asset_name':line_id.asset_name,
            'current_qty':line_id.current_qty,
            'asset_id':line_id.asset_id,
            'difference':line_id.difference,
            'income_cnt':line_id.income_cnt,
            'receive_cnt':line_id.receive_cnt,
            'expense_cnt':line_id.expense_cnt,
            'transfer_cnt':line_id.transfer_cnt,
            'income':line_id.income,
            'expense':line_id.expense,
            'is_invisible':line_id.is_invisible,
            'account_id':line_id.account_id.id,
            'depreciation_account':depreciation_account.id,
            'account_receivable_id':account_receivable_id.id,
            'receivable_income_account_id':receivable_income_account_id.id,
            'detail_ids':detail_ids,
            })

        return res


    employee_id = fields.Many2one('hr.employee')

    qty = fields.Integer('Эхний үлдэгдэл')
    amount = fields.Float('Amount')
    capitalized_value = fields.Float('Capitalized value')
    accumulated_depreciation = fields.Float('Accumulated depreciation')
    current_value = fields.Float('Current value')
    
    product_id = fields.Many2one('product.template', string='Product')
    asset_id = fields.Char('AssetID')
    
    # registry_number = fields.Char('RegistryNumber')
    asset_name = fields.Char('Asset name')

    counted_qty = fields.Integer('Тоолсон тоо')
    difference = fields.Integer('Зөрүү')
    current_qty = fields.Integer('Эцсийн үлдэгдэл')

    solution = fields.Char('Шийдэл')

    # detail_ids = fields.Many2many(
    #     comodel_name='fixed.asset.details', 
    #     string='Level Matang'
    #     )
    # transfer_ids = fields.Many2many(
    #     comodel_name='asset.transfer', 
    #     string='Level Matang'
    #     )
     
    
    detail_ids = fields.One2many('asset.solution.line', 'wizard_id', string='Details')

    income_cnt = fields.Integer('Орлогодох тоо ширхэг')
    receive_cnt = fields.Integer('Шилжиж ирэх тоо ширхэг')
    expense_cnt = fields.Integer('Зарлагадах тоо ширхэг')
    transfer_cnt = fields.Integer('Шилжүүлэх тоо ширхэг')

    income = fields.Integer('Орлого')
    expense = fields.Integer('Зарлага')

    is_invisible = fields.Integer('Is invisible')

    department_id = fields.Many2one('hr.department', string='Салбар')
    account_id = fields.Many2one('account.account',  string='Хөрөнгийн данс',domain="[('department_id', '=', department_id)]")
    account_receivable_id = fields.Many2one('account.account',  string='Тооллого тооцооны авлага',domain="[('department_id', '=', department_id)]", required=True)
    depreciation_account = fields.Many2one('account.account',  string='Хуримтлагдсан элэгдэл',domain="[('department_id', '=', department_id)]", required=True)
    receivable_income_account_id = fields.Many2one('account.account',  string='Дахин үнэлгээний хойшлогдсон орлого',domain="[('department_id', '=', department_id)]", required=True)
    
    
    def get_active_object(self):
        context = self._context
        if context.get('active_model') and context.get('active_id'):
            if context['active_model'] == 'fixed.asset.counting.line' and context['active_id']:
                return self.env['fixed.asset.counting.line'].browse(context['active_id'])


    
    def button_to_save(self):

        expense_cnt = 0
        transfer_cnt = 0
        active_obj = self.get_active_object()



        detail_ids=[]
        for detail in self.sudo().detail_ids:

            if detail.employee_id and detail.is_expense :
                raise UserError('Зарлагадах эсэх нь чектэй байхад ажилтан сонгож болохгүй!!!')
            elif detail.employee_id and detail.employee_id != self.employee_id: 
                transfer_cnt += 1 
            elif detail.is_expense:
                expense_cnt += 1  


            detail_ids.append((0,0,{
                'accumulated_depreciation':detail.accumulated_depreciation,
                'current_value':detail.current_value,
                'amount':detail.amount,
                'capitalized_value': detail.capitalized_value,
                'employee_id':detail.employee_id.id,
                'is_expense':detail.is_expense,
                'registry_number':detail.registry_number,
                'start_date':detail.start_date,
                'damage_description':detail.damage_description,
                'damage_desc':detail.damage_desc,
                'asset_state':detail.asset_state,
                'account_move_id':detail.account_move_id.id,
                'account_move_id_for_accountant':detail.account_move_id_for_accountant.id,

            }))

        if active_obj.detail_ids:
            active_obj.detail_ids.sudo().unlink()

        if detail_ids:
            active_obj.sudo().write({
                'income_cnt':self.income_cnt,
                'receive_cnt':self.receive_cnt,
                'expense_cnt':expense_cnt,
                'transfer_cnt':transfer_cnt,
                'income':self.income_cnt + self.receive_cnt,
                'expense':expense_cnt + transfer_cnt,
                'is_invisible':self.is_invisible ,
                'account_id':self.account_id.id,
                'depreciation_account':self.depreciation_account.id,
                'account_receivable_id':self.account_receivable_id.id,
                'receivable_income_account_id':self.receivable_income_account_id.id,
                'department_id':self.department_id.id,
                'detail_ids':detail_ids})



            

        return {'type': 'ir.actions.act_window_close'}










    
    def button_to_handle(self):


        line_id = self.get_active_object()
        if line_id:
            line_id.sudo().button_to_handle()

        return {'type': 'ir.actions.act_window_close'}



class AssetSolutionLine(models.TransientModel):
    _name = 'asset.solution.line'
    wizard_id = fields.Many2one('asset.solution',string="Wizard")


    
    amount = fields.Float('Анхны үнэ')
    capitalized_value = fields.Float('Capitalized value')
    accumulated_depreciation = fields.Float('Accumulated depreciation')
    current_value = fields.Float('Одоогийн үнэ цэнэ')
    sale_price = fields.Float('Зарлагадах дүн')
    
    employee_id = fields.Many2one('hr.employee', string='Хүлээлгэн өгөх ажилтан')
    is_expense = fields.Boolean(string='Зарлагадах эсэх')
    registry_number = fields.Char('RegistryNumber')

    start_date = fields.Date('Start Date')

    damage_description = fields.Selection([
        ('normal',u'Хэвийн'),
        ('missing',u'Алга болгосон'),
        ('chipped',u'Эмтэрсэн'),
        ('parts_are_missing',u'Иж бүрдэл дутуу'),
        ('broken',u'Хугарсан'),
        ('bad_appearance',u'Үзэмж муу'),
        ('quality_is_not_enough',u'Чанарын шаардлага хангахаа байсан'),
        ('equipment_malfunction',u'Тоног төхөөрөмжийн хэвийн үйл ажиллагаа алдагдсан'),
        ('cracked',u'Хагарсан'),
        ('manufacturing_defect',u'Үйлдвэрлэлийн гэмтэл'),
        ('mechanical_damage',u'Механик гэмтэл'),
        ('other',u'Бусад'),
    ], u'Гэмтлийн тодорхойлолт',default='normal')

    damage_desc = fields.Char('Гэмтлийг бичих')

    asset_state = fields.Selection([
        ('used',u'Ашиглалттай'),
        ('unused',u'Ашиглахгүй байгаа'),
    ], u'Хөрөнгийн төлөв',default='used')

    amount_ids = fields.One2many('fixed.asset.amounts', 'detail_id', 'Суутгал хуваарьлах')

    account_move_id = fields.Many2one('account.move',string='Тоологчийн ажил гүйлгээ')
    account_move_id_for_accountant = fields.Many2one('account.move',string='Нягтлангийн ажил гүйлгээ')


class AssetDisposal(models.TransientModel):
    _name = 'asset.disposal'
 

    @api.model
    def default_get(self, fields):
        res = super(AssetDisposal, self).default_get(fields)		
        request_id = self.env['fixed.asset.counting.line'].browse(self._context.get('active_ids', []))

        line_ids= []
        total_amt = 0
        if request_id.detail_ids:
            
            for line in request_id.detail_ids:	

                start_date = False
                # if line.start_date:
                #     start_date = datetime.strptime(line.start_date,"%Y-%m-%d")
                amount_ids= []
                if line.is_expense:
                    total_amt += line.sale_price


                    for amount in line.amount_ids:
                        amount_ids.append((0,0,{
                            'partner_id':amount.partner_id.id,
                            'charge_amount':amount.charge_amount,
                        }))



                line_ids.append((0,0,{
                    'accumulated_depreciation':line.accumulated_depreciation,
                    'current_value':line.current_value,
                    'amount':line.amount,
                    'capitalized_value': line.capitalized_value,
                    'employee_id': line.employee_id.id,
                    'is_expense':line.is_expense,
                    'sale_price':line.sale_price,
                    'registry_number':line.registry_number,
                    'start_date':line.start_date,
                    'amount_ids':amount_ids,
                }))


        account_receivable_id = request_id.account_receivable_id
        account_receivable_id_from_employee = request_id.account_receivable_id_from_employee
        vat_account = request_id.vat_account
        profit_account_id = request_id.profit_account_id
        loss_account_id = request_id.loss_account_id
        depreciation_account = request_id.depreciation_account
        receivable_income_account_id = request_id.receivable_income_account_id

        if not vat_account:
            prev_request_id = self.env['fixed.asset.counting.line'].search([('department_id','=',request_id.request_id.department_id.id),('state','in',['verified','verify']),('account_receivable_id_from_employee','!=',False)],limit=1,order="id desc")
            if prev_request_id:

                account_receivable_id_from_employee = prev_request_id.account_receivable_id_from_employee
                vat_account = prev_request_id.vat_account

                profit_account_id = prev_request_id.profit_account_id

                loss_account_id = prev_request_id.loss_account_id


        res.update({
            'employee_id':request_id.employee_id.id,
            'department_id': request_id.department_id.id,
            'counted_qty':request_id.counted_qty,
            'qty':request_id.qty,
            'asset_name':request_id.asset_name,
            'account_id':request_id.account_id.id,
            'account_receivable_id':account_receivable_id.id if account_receivable_id else False,
            'account_receivable_id_from_employee':account_receivable_id_from_employee.id if account_receivable_id_from_employee else False,
            'depreciation_account':depreciation_account.id if depreciation_account else False,
            'vat_account':vat_account.id if vat_account else False,
            'profit_account_id':profit_account_id.id if profit_account_id else False,
            'loss_account_id':loss_account_id.id if loss_account_id else False,
            'profit_or_loss_amount':request_id.profit_or_loss_amount,
            'receivable_income_account_id':receivable_income_account_id.id if receivable_income_account_id else False,
            'current_qty':request_id.current_qty,
            'total_amt':request_id.total_amt,
            'asset_id':request_id.asset_id,
            'difference':request_id.difference,
            'income_cnt':request_id.income_cnt,
            'receive_cnt':request_id.receive_cnt,
            'expense_cnt':request_id.expense_cnt,
            'transfer_cnt':request_id.transfer_cnt,
            'income':request_id.income,
            'expense':request_id.expense,
            'is_invisible':request_id.is_invisible,
            'detail_ids':line_ids,
            })

        return res




    employee_id = fields.Many2one('hr.employee')
    department_id = fields.Many2one('hr.department', string='Салбар')

    qty = fields.Integer('Эхний үлдэгдэл')
    amount = fields.Float('Amount')
    capitalized_value = fields.Float('Capitalized value')
    accumulated_depreciation = fields.Float('Accumulated depreciation')
    current_value = fields.Float('Current value')


    total_amt = fields.Float('Зарлагадах нийт дүн')
    
    product_id = fields.Many2one('product.template', string='Prodreceive_cntuct')
    asset_id = fields.Char('AssetID')
    account_id = fields.Many2one('account.account',  string='Хөрөнгийн данс')
    account_receivable_id = fields.Many2one('account.account',  string='Тооллого тооцооны авлага',domain="[('department_id', '=', department_id)]", readonly=True)
    account_receivable_id_from_employee = fields.Many2one('account.account',  string='ААХА авлага',domain="[('department_id', '=', department_id)]", required=True)
    depreciation_account = fields.Many2one('account.account',  string='Хуримтлагдсан элэгдэл',domain="[('department_id', '=', department_id)]", required=True)
    vat_account = fields.Many2one('account.account',  string='НӨАТ-н данс',domain="[('department_id', '=', department_id)]", required=True)
    profit_or_loss_amount = fields.Float('Зөрүү дүн')
    profit_account_id = fields.Many2one('account.account',  string='Хөрөнгө борлуулсны олз',domain="[('department_id', '=', department_id)]", required=True)
    loss_account_id = fields.Many2one('account.account',  string='Хөрөнгө данснаас хассаны газ',domain="[('department_id', '=', department_id)]", required=True)
    account_receivable_id = fields.Many2one('account.account',  string='Тооллого тооцооны авлага',domain="[('department_id', '=', department_id)]", required=True)
    receivable_income_account_id = fields.Many2one('account.account',  string='Дахин үнэлгээний хойшлогдсон орлого',domain="[('department_id', '=', department_id)]", required=True)

    registry_number = fields.Char('RegistryNumber')
    asset_name = fields.Char('Asset name')

    counted_qty = fields.Integer('Тоолсон тоо')
    difference = fields.Integer('Зөрүү')
    current_qty = fields.Integer('Эцсийн үлдэгдэл')

    solution = fields.Char('Шийдэл')

    detail_ids = fields.One2many('asset.disposal.line', 'wizard_id', 'Employees')
    # detail_ids = fields.One2many('fixed.asset.details', 'line_id', 'Employees')
    income_cnt = fields.Integer('Орлогодох тоо ширхэг')
    receive_cnt = fields.Integer('Шилжиж ирэх тоо ширхэг')
    expense_cnt = fields.Integer('Зарлагадах тоо ширхэг')
    transfer_cnt = fields.Integer('Шилжүүлэх тоо ширхэг')






    def get_active_object(self):
        context = self._context
        if context.get('active_model') and context.get('active_id'):
            if context['active_model'] == 'fixed.asset.counting.line' and context['active_id']:
                return self.env['fixed.asset.counting.line'].browse(context['active_id'])
    


    
    def button_accept(self):

        expense_cnt = 0
        transfer_cnt = 0
        active_obj = self.get_active_object()




        line_ids=[]
        total_amt = 0
        profit_or_loss_amount = 0
        for line in self.detail_ids:
            charge_amount = 0
            amount_ids=[]
            for ln in line.amount_ids:
                charge_amount += ln.charge_amount
                if ln.charge_amount<=0:
                    raise UserError('Дахин үнэлгээ оруулаагүй мөр байна!!!')
                else:
                    amount_ids.append((0,0,{
                        'partner_id':ln.partner_id.id,
                        'charge_amount':ln.charge_amount,
                    })) 


            line_ids.append((0,0,{
                'accumulated_depreciation':line.accumulated_depreciation,
                'current_value':line.current_value,
                'amount':line.amount,
                'capitalized_value': line.capitalized_value,
                'employee_id':line.employee_id.id,
                'is_expense':line.is_expense,
                'sale_price':charge_amount,
                'registry_number':line.registry_number,
                'start_date':line.start_date,
                'amount_ids':amount_ids,
                }))
            total_amt += charge_amount
            profit_or_loss_amount = line.amount - line.sale_price 

        if active_obj.detail_ids:
            active_obj.detail_ids.sudo().unlink()




        if total_amt == 0:
            raise UserError('Дахин үнэлсэн үнэлгээ оруулаaгүй тохиолдолд хадгалах боломжгүй!!!')
        elif line_ids:
            active_obj.write({
                'income_cnt':self.income_cnt,
                'receive_cnt':self.receive_cnt,
                # 'expense_cnt':expense_cnt,
                'transfer_cnt':transfer_cnt,
                # 'income':self.income_cnt + self.receive_cnt,
                # 'expense':expense_cnt + transfer_cnt,
                'total_amt':total_amt,
                'account_receivable_id':self.account_receivable_id.id,
                'account_receivable_id_from_employee':self.account_receivable_id_from_employee.id,
                'depreciation_account':self.depreciation_account.id,
                'vat_account':self.vat_account.id,
                'profit_account_id':self.profit_account_id.id,
                'loss_account_id':self.loss_account_id.id,
                'profit_or_loss_amount':profit_or_loss_amount,
                'account_receivable_id':self.account_receivable_id.id,
                'receivable_income_account_id':self.receivable_income_account_id.id,
                'department_id': self.department_id.id,
                'detail_ids':line_ids})

            # self.create_account_moves()

        return {'type': 'ir.actions.act_window_close'}


    # def create_account_moves(self):

    #     currency_id = 112
    #     journal_id = 33

    #     journal = self.env['account.journal'].search([('company_id','=',self.request_id.department_id.company_id.id)])[0]
    #     if journal:
    #         journal_id = journal.id

    #     line_id = self.get_active_object()

    #     print 'line_id',line_id
        
        
    #     employee_name = self.employee_id.name_related + '.' + self.employee_id.last_name[0]
    #     if self.employee_id.id == 215:
    #         employee_name = self.asset_name


    #     res = []

    #     print 'line_id.detail_ids',line_id.detail_ids
    #     for line in line_id.detail_ids:


    #         if line.is_expense:

    #             ttl_charge_amount = 0
                
    #             for ln in line.amount_ids:


    #                 line_dict = {
    #                     'account_id': line_id.account_receivable_id_from_employee.id, # ААХА авлага   ДТ
    #                     'name':"1 " + ln.partner_id.name ,
    #                     'currency_id':currency_id,
    #                     'company_currency_id':currency_id,
    #                     'partner_id':ln.partner_id.id,
    #                     'debit':ln.charge_amount,
    #                     'credit':0,
    #                     'credit_cash_basis':ln.charge_amount,
    #                     'balance':ln.charge_amount,
    #                     'journal_id':journal_id,       
    #                 }     
    #                 res.append((0,0,line_dict))

    #                 ttl_charge_amount += ln.charge_amount


    #             if line.capitalized_value < ttl_charge_amount:
    #                 raise UserError('Капиталжуулсан үнэнээс үнэтэй зарах боломжгүй')
    #             else:

    #                 line_dict = {
    #                     'account_id': line_id.receivable_income_account_id.id, # Дахин үнэлгээний хойшлогдсон орлого ДТ
    #                     'name':"2 " + employee_name ,
    #                     'currency_id':currency_id,
    #                     'company_currency_id':currency_id,
    #                     'partner_id':False,
    #                     'debit':line.accumulated_depreciation,
    #                     'credit':0,
    #                     'credit_cash_basis':line.accumulated_depreciation,
    #                     'balance':line.accumulated_depreciation,
    #                     'journal_id':journal_id,       
    #                 }     
    #                 res.append((0,0,line_dict))


    #                 line_dict = {
    #                     'account_id': line_id.loss_account_id.id, # Хөрөнгө данснаас хассны гарз ДТ
    #                     'name':"2 " + employee_name ,
    #                     'currency_id':currency_id,
    #                     'company_currency_id':currency_id,
    #                     'partner_id':False,
    #                     'debit':line.current_value,
    #                     'credit':0,
    #                     'credit_cash_basis':line.current_value,
    #                     'balance':line.current_value,
    #                     'journal_id':journal_id,       
    #                 }     
    #                 res.append((0,0,line_dict))


    #                 line_dict = {
    #                     'account_id': line_id.account_receivable_id.id,  #тооллого тооцооны авлага КТ
    #                     'name':"3 "+line_id.asset_name,
    #                     'currency_id':currency_id,
    #                     'company_currency_id':currency_id,
    #                     'partner_id':line_id.department_id.partner_id.id,
    #                     'debit':0,
    #                     'credit':line.capitalized_value, 
    #                     'credit_cash_basis':line.capitalized_value,
    #                     'balance':line.capitalized_value,
    #                     'journal_id':journal_id,    
    #                 }   
    #                 res.append((0,0,line_dict))


    #                 vat = round(ttl_charge_amount/11,2)
    #                 profit = ttl_charge_amount - vat

    #                 line_dict = {
    #                     'account_id': line_id.profit_account_id.id,  # Үндсэн хөрөнгө борлуулсны олз КТ
    #                     'name':"5 " + line_id.asset_name,
    #                     'currency_id':currency_id,
    #                     'company_currency_id':currency_id,
    #                     'partner_id':line_id.department_id.partner_id.id,
    #                     'debit':0,
    #                     'credit':profit, 
    #                     'credit_cash_basis':profit,
    #                     'balance':profit,
    #                     'journal_id':journal_id,    
    #                 }   
    #                 res.append((0,0,line_dict))


    #                 line_dict = {
    #                     'account_id': line_id.vat_account.id,  # НӨАТ тооцоо  КТ
    #                     'name':"6 " + line_id.asset_name,
    #                     'currency_id':currency_id,
    #                     'company_currency_id':currency_id,
    #                     'partner_id':line_id.department_id.partner_id.id,
    #                     'debit':0,
    #                     'credit':vat, 
    #                     'credit_cash_basis':vat,
    #                     'balance':vat,
    #                     'journal_id':journal_id,    
    #                 }   
    #                 res.append((0,0,line_dict))


    #         print 'res',res

    #         move_id = self.env['account.move'].create ({
    #             'department_id':line_id.department_id.id,
    #             'date':date.today(),
    #             'ref':employee_name + '=>' +self.asset_name,
    #             'company_id':line_id.department_id.company_id.id,
    #             'journal_id':journal_id,
    #             'state':'draft',
    #             'line_ids':res,
                
    #             })


    #     print 'line_id',line_id
    #     line_id.sudo().write ({
    #         'account_move_id_for_accountant':move_id.id,
    #         })

    #     print 'move_id.id',line_id.account_move_id_for_accountant

    #     return False
            




class AssetDisposalLine(models.TransientModel):
    _name = 'asset.disposal.line'



    wizard_id = fields.Many2one('asset.disposal',string="Wizard")


    
    amount = fields.Float('Анхны үнэ')
    capitalized_value = fields.Float('Capitalized value')
    accumulated_depreciation = fields.Float('Accumulated depreciation')
    current_value = fields.Float('Одоогийн үнэ цэнэ')
    sale_price = fields.Float('Зарлагадах дүн')
    
    employee_id = fields.Many2one('hr.employee', string='Хүлээлгэн өгөх ажилтан')
    is_expense = fields.Boolean(string='Зарлагадах эсэх')
    registry_number = fields.Char('RegistryNumber')

    start_date = fields.Date('Start Date')

    damage_description = fields.Selection([
        ('normal',u'Хэвийн'),
        ('missing',u'Алга болгосон'),
        ('chipped',u'Эмтэрсэн'),
        ('parts_are_missing',u'Иж бүрдэл дутуу'),
        ('broken',u'Хугарсан'),
        ('bad_appearance',u'Үзэмж муу'),
        ('quality_is_not_enough',u'Чанарын шаардлага хангахаа байсан'),
        ('equipment_malfunction',u'Тоног төхөөрөмжийн хэвийн үйл ажиллагаа алдагдсан'),
        ('cracked',u'Хагарсан'),
        ('manufacturing_defect',u'Үйлдвэрлэлийн гэмтэл'),
        ('mechanical_damage',u'Механик гэмтэл'),
    ], u'Гэмтлийн тодорхойлолт',default='normal')


    damage_desc = fields.Char('Гэмтлийг бичих')

    asset_state = fields.Selection([
        ('used',u'Ашиглалттай'),
        ('unused',u'Ашиглахгүй байгаа'),
    ], u'Хөрөнгийн төлөв',default='used')

    # amount_ids = fields.One2many('fixed.asset.amounts', 'detail_id', 'Суутгал хуваарьлах')
    amount_ids = fields.One2many('asset.disposal.line1', 'line_id', 'Суутгал хуваарьлах')

    # account_move_id = fields.Many2one('account.move',string='Тоологчийн ажил гүйлгээ')
    account_move_id_for_accountant = fields.Many2one('account.move',string='Нягтлангийн ажил гүйлгээ')





class AssetDisposalLine1(models.TransientModel):
    _name = 'asset.disposal.line1'



    line_id = fields.Many2one('asset.disposal.line',string="Wizard")

    partner_id = fields.Many2one('res.partner', string='Мөнгө суутах хүн',required=True)
    charge_amount = fields.Float('Суутгах дүн',required=True)





class AssetTransaction(models.TransientModel):
    _name = 'asset.transaction'
 
    employee_id = fields.Many2one('hr.employee')

    qty = fields.Integer('Эхний үлдэгдэл')
    amount = fields.Float('Amount')
    capitalized_value = fields.Float('Capitalized value')
    accumulated_depreciation = fields.Float('Accumulated depreciation')
    current_value = fields.Float('Current value')
    sale_price = fields.Float('Sale price')
    registry_number = fields.Char('RegistryNumber')
    asset_name = fields.Char('Asset name')

    counted_qty = fields.Integer('Тоолсон тоо')
    difference = fields.Integer('Зөрүү')
    current_qty = fields.Integer('Эцсийн үлдэгдэл')

    solution = fields.Char('Шийдэл')

    # detail_ids = fields.One2many('fixed.asset.details', 'line_id', 'Employees')
    income_cnt = fields.Integer('Орлогодох тоо ширхэг')
    receive_cnt = fields.Integer('Шилжиж ирэх тоо ширхэг')
    expense_cnt = fields.Integer('Зарлагадах тоо ширхэг')
    transfer_cnt = fields.Integer('Шилжүүлэх тоо ширхэг')



    
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




        return {'type': 'ir.actions.act_window_close'}




