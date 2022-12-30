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


class DamageAssetDescription(models.TransientModel):
    _name = 'damage.asset.description'
 

    @api.model
    def default_get(self, fields):
        res = super(DamageAssetDescription, self).default_get(fields)		
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

        # if not depreciation_account:
        #     prev_line_id = self.env['fixed.asset.counting.line'].sudo().search([('department_id','=',line_id.request_id.department_id.id),('state','in',['count','verify','verified']),('account_id','=',account_id.id),('depreciation_account','!=',False)],limit=1,order="id desc")
        #     if prev_line_id:

        #         depreciation_account = prev_line_id.sudo().depreciation_account
        #         account_receivable_id = prev_line_id.sudo().account_receivable_id
        #         receivable_income_account_id = prev_line_id.sudo().receivable_income_account_id

        res.update({
            'employee_id':line_id.employee_id.id,
            'department_id':line_id.request_id.department_id.id,
            'counted_qty':line_id.counted_qty,
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
            # 'depreciation_account':depreciation_account.id,
            # 'account_receivable_id':account_receivable_id.id,
            # 'receivable_income_account_id':receivable_income_account_id.id,
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
     
    
    detail_ids = fields.One2many('damage.asset.description.line', 'damage_asset_id', string='Details')

    income_cnt = fields.Integer('Орлогодох тоо ширхэг')
    receive_cnt = fields.Integer('Шилжиж ирэх тоо ширхэг')
    expense_cnt = fields.Integer('Зарлагадах тоо ширхэг')
    transfer_cnt = fields.Integer('Шилжүүлэх тоо ширхэг')

    income = fields.Integer('Орлого')
    expense = fields.Integer('Зарлага')

    is_damage_asset = fields.Boolean(string='is damage asset',default=False)
    is_invisible = fields.Integer('Is invisible')

    department_id = fields.Many2one('hr.department', string='Салбар')
    account_id = fields.Many2one('account.account',  string='Хөрөнгийн данс',domain="[('department_id', '=', department_id)]")
    account_receivable_id = fields.Many2one('account.account',  string='Тооллого тооцооны авлага',domain="[('department_id', '=', department_id)]")
    depreciation_account = fields.Many2one('account.account',  string='Хуримтлагдсан элэгдэл',domain="[('department_id', '=', department_id)]")
    receivable_income_account_id = fields.Many2one('account.account',  string='Дахин үнэлгээний хойшлогдсон орлого',domain="[('department_id', '=', department_id)]")
    
    
    def get_active_object(self):
        context = self._context
        if context.get('active_model') and context.get('active_id'):
            if context['active_model'] == 'fixed.asset.counting.line' and context['active_id']:
                return self.env['fixed.asset.counting.line'].browse(context['active_id'])


    @api.multi
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
            if detail.asset_state not in ('normal'):
                self.is_damage_asset = True

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
                # 'depreciation_account':self.depreciation_account.id,
                # 'account_receivable_id':self.account_receivable_id.id,
                # 'receivable_income_account_id':self.receivable_income_account_id.id,
                'department_id':self.department_id.id,
                'is_damage_asset':self.is_damage_asset,
                'detail_ids':detail_ids})


        return {'type': 'ir.actions.act_window_close'}




    @api.multi
    def button_to_handle(self):


        line_id = self.get_active_object()
        if line_id:
            line_id.sudo().button_to_handle()

        return {'type': 'ir.actions.act_window_close'}



class DamageAssetDescriptionLine(models.TransientModel):
    _name = 'damage.asset.description.line'
    damage_asset_id = fields.Many2one('damage.asset.description',string="damage asset description")


    
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

    # amount_ids = fields.One2many('fixed.asset.amounts', 'detail_id', 'Суутгал хуваарьлах')

    account_move_id = fields.Many2one('account.move',string='Тоологчийн ажил гүйлгээ')
    account_move_id_for_accountant = fields.Many2one('account.move',string='Нягтлангийн ажил гүйлгээ')
