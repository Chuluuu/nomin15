# -*- coding: utf-8 -*-

# sarn8851code4212ai
# from email.policy import default
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning
from datetime import timedelta
# from datetime import datetime
from datetime import date, datetime,timedelta
from dateutil.relativedelta import relativedelta

import requests
import json
import xmlrpclib
from zeep import Client, Settings
from odoo.exceptions import UserError #
import base64
from zeep import Plugin
class MyLoggingPlugin(Plugin):

    def ingress(self, envelope, http_headers, operation):
        # print(etree.tostring(envelope, pretty_print=True))
        return envelope, http_headers

    def egress(self, envelope, http_headers, operation, binding_options):
        # print(etree.tostring(envelope, pretty_print=True))
        http_headers['Content-Type'] = 'text/json; charset=utf-8;'
        return envelope, http_headers




class FixedAssetAmounts(models.Model):

    _name = 'fixed.asset.amounts'
    _description = 'Fixed asset amounts'

    detail_id = fields.Many2one('fixed.asset.details', string='Line', ondelete='cascade')
    
    partner_id = fields.Many2one('res.partner', string='Мөнгө суутах хүн',required=True)
    charge_amount = fields.Float('Суутгах дүн',required=True)





class FixedAssetDetails(models.Model):

    _name = 'fixed.asset.details'
    _description = 'Fixed asset details'
    _order = "start_date"



    line_id = fields.Many2one('fixed.asset.counting.line', string='Line', ondelete='cascade')
    
    amount = fields.Float('Анхны үнэ')
    capitalized_value = fields.Float('Capitalized value')
    accumulated_depreciation = fields.Float('Accumulated depreciation')
    current_value = fields.Float('Одоогийн үнэ цэнэ')
    sale_price = fields.Float('Зарлагадах дүн')
    
    employee_id = fields.Many2one('hr.employee', string='Хүлээлгэн өгөх ажилтан')
    is_expense = fields.Boolean(string='Зарлагадах эсэх')
    registry_number = fields.Char('RegistryNumber')
    # asset_name = fields.Char('Asset name')

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



# class AssetTransfer(models.Model):

#     _name = 'asset.transfer'
#     _description = 'Asset transfer list'

#     line_id = fields.Many2one('fixed.asset.counting.line', string='Request', ondelete='cascade')
#     department_id = fields.Many2one('hr.department', string='Department')
#     receiver_department_id = fields.Many2one('hr.department', string='Receiver department')
#     request_id = fields.Many2one('asset.transfer.request', string='Request', ondelete='cascade')
    
class FixedAssetTransfer(models.Model):

    _name = 'fixed.asset.transfer'
    _description = 'Fixed asset transfer list'

    counting_id = fields.Many2one('fixed.asset.counting', string='Request', ondelete='cascade')
    department_id = fields.Many2one('hr.department', string='Department')
    receiver_department_id = fields.Many2one('hr.department', string='Receiver department')
    request_id = fields.Many2one('asset.transfer.request', string='Request', ondelete='cascade')

class FixedAssetLine(models.Model):

    _name = 'fixed.asset.counting.line'
    _description = 'Fixed asset line'
    _order = "is_damage_asset desc,has_difference,difference  desc, employee_id"


    def _show_accept_button(self):
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])

    
                
    show_accept_button = fields.Boolean(u'Towq haruulah', compute=_show_accept_button, default=False)
    state = fields.Selection([
        ('draft',u'Ноорог'),
        ('returned',u'Буцаагдсан'),
        ('count',u'Тоолох'),
        ('verify',u'Тоолсон'),       
        ('verified',u'Дууссан'),
        ('cancelled',u'Цуцлагдсан'),
    ], u'State', default='draft', tracking=True)

    connection_state = fields.Selection([
                            ('unknown',u'Тодорхойгүй'),
                            ('doubtful',u'Эргэлзээтэй'),
                            ('confirmed',u'Баталгаажсан'),
                            ('connected_for_cycle_counter',u'Тоологчийн гүйлгээ холбогдсон'),
                            ('connected_for_accountant',u'Нягтлангийн гүйлгээ холбогдсон'),
                            ], u'Холболтын төлөв', tracking=True, default = 'unknown')

    employee_id = fields.Many2one('hr.employee', required=True, string='Employee')
    department_id = fields.Many2one('hr.department', string='Department')
    job_id = fields.Many2one('hr.job', string='Job')
    request_id = fields.Many2one('fixed.asset.counting', string='Request', ondelete='cascade')
    account_id = fields.Many2one('account.account',  string='Asset account')
    depreciation_account = fields.Many2one('account.account',  string='Хуримтлагдсан элэгдэл')
    account_receivable_id = fields.Many2one('account.account',  string='Тооллого тооцооны авлга')
    account_receivable_id_from_employee = fields.Many2one('account.account',  string='ААХА авлага')
    vat_account = fields.Many2one('account.account',  string='НӨАТ-н данс')
    profit_or_loss_amount = fields.Float('Зөрүү дүн')
    profit_account_id = fields.Many2one('account.account',  string='Хөрөнгө борлуулсны олз')
    loss_account_id = fields.Many2one('account.account',  string='Хөрөнгө данснаас хассаны газ')
    receivable_income_account_id = fields.Many2one('account.account',  string='Дахин үнэлгээний хойшлогдсон орлого')

    qty = fields.Integer('Эхний үлдэгдэл')
    amount = fields.Float('Үнэ')

    total_amt = fields.Float('Зарлaгадах дүн')
    
    product_id = fields.Many2one('product.template', string='Product')
    asset_id = fields.Char('AssetID')
    asset_name = fields.Char('Asset name')

    counted_qty = fields.Integer('Тоолсон тоо')
    difference = fields.Integer('Зөрүү')
    has_difference = fields.Integer('has_difference')
    current_qty = fields.Integer('Эцсийн үлдэгдэл')

    solution = fields.Char('Шийдэл')
    income = fields.Integer('Орлого')
    expense = fields.Integer('Зарлага')

    detail_ids = fields.One2many('fixed.asset.details', 'line_id', 'Datails')
    # transfer_ids = fields.One2many('asset.transfer', 'line_id', 'Transfers')
    income_cnt = fields.Integer('Орлогодох тоо ширхэг')
    expense_cnt = fields.Integer('Зарлагадах тоо ширхэг')
    receive_cnt = fields.Integer('Шилжиж ирэх тоо ширхэг')
    transfer_cnt = fields.Integer('Шилжүүлэх тоо ширхэг')

    is_invisible = fields.Integer('Is invisible')
    backup_id = fields.Integer('Backup ID')

    account_move_id = fields.Many2one('account.move',string='Тоологчийн ажил гүйлгээ')
    account_move_id_for_accountant = fields.Many2one('account.move',string='Нягтлангийн ажил гүйлгээ')

    filter_by30s = fields.Boolean(string="Filter By 30s", default=False)
    diamond_json = fields.Text(string=u'Диамонд json')
    transaction_id = fields.Char('Transaction ID')

    is_damage_asset = fields.Boolean(string='is damage asset',default=False)

    @api.onchange('employee_id')
    def onchange_employee(self):
        if self.employee_id:
            self.set_employee_information(self)


    @api.onchange('counted_qty')
    def onchange_counted_qty(self):
        self.difference = self.counted_qty
        if self.counted_qty != 0:
            self.has_difference = 1



    @api.model
    def create(self, vals):
        result = super(FixedAssetLine, self).create(vals)
        self.set_employee_information(result)

        return result

    
    def write(self, vals):

        has_defference = 0
        if vals.get('counted_qty') or vals.get('counted_qty') == 0:
            defference = vals.get('counted_qty') - self.qty
            if defference !=0:
                has_defference = 1
            vals.update({
                'difference':defference,
                'has_difference':has_defference,
                'current_qty': vals.get('counted_qty'),
                })
        # else:
            # vals.update({'current_qty':self.qty})
            # print '\n\n\ qty',vals.get('qty'),self.qty
        if vals.get('transaction_id') and self.transaction_id:
            if(self.transaction_id != vals.get('transaction_id')):
                message = str(self.transaction_id) + " - г " + str(vals.get('transaction_id')) + " болгож өөрчлөв."
                self.request_id.message_post(message) 

        # print '\n\n counted_qty',self.counted_qty
        result = super(FixedAssetLine, self).write(vals)
        return result

    def set_employee_information(self, result):
        result.job_id = result.employee_id.job_id or None
        result.department_id = result.employee_id.parent_department or None


    
    def get_solution(self):

        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])

        # if employee_id:

        #     if self.receiver_employee_id == employee_id :
        #         # if self.employee_id.parent_department == self.receiver_employee_id.parent_department and \
        #         #     self.request_id.department_id == self.request_id.receiver_department_id :
        #         #     self.write({'state': 'approved'})
        #         # else:
        #         self.write({'state': 'approved'})
            
        #     self.request_id.sudo().action_accept_all()




    
    def handle_journal_entries_for_cycle_counter(self):
        current_qty = 0


        url = self.env['integration.config'].sudo().search([('name','=','handle_asset_transfer')]).server_ip
        client = Client(url)

        response = client.service.AssetCountGetForSum("1",datetime.today(),self.request_id.department_id.nomin_code,"1","","1","","1","","0",self.asset_id,"0",self.employee_id.sudo().passport_id)

        if response:
            try:
                result_dict = json.loads('['+response+']')
            except ValueError as e:
                raise UserError(_('Мэдээлэл татахад алдаа гарлаа.\n Алдааны код [%s] '%(response)))
        
            if result_dict:
                for dictionary in result_dict:
                    current_qty = int(dictionary[u'EndQty'])

        if self.qty + self.income - self.expense == self.current_qty: 
            partner_id = self.employee_id.address_home_id
            if self.employee_id.id == 215:
                partner_id = self.env['res.partner'].sudo().search([('code','=',self.asset_name[:12])])

            if partner_id:

                for detail_id in self.detail_ids:
                    zzz = detail_id.amount_ids.sudo().create({
                        'detail_id':detail_id.id,
                        'partner_id':partner_id.id,
                        'charge_amount':0,
                    })

            self.sudo().diamond_integration_for_cycle_counter(client)
            self.sudo().write({'is_invisible':1})
        else:
            raise UserError(str(self.id) + '-р мөр дээрх зөрүүг яаж шийдэж байгааг зөв бөглөж хадгална уу!!!')

        if self.current_qty != current_qty and self.transfer_cnt != 0:
            raise UserError(_('Тоологчийн прогнозоор байх ёстой үлдэгдэл нь : %s \nГэтэл диамонд дээрх одоогийн үлдэгдэл нь : %s \nбайна. Иймд ажилтнуудын "Хөрөнгө шилжүүлэх хүсэлт"-ийг яаравчлуулах хэрэгтэй'%(self.current_qty,current_qty)))




    def connect_account_moves_for_cycle_counter(self):

        self.account_move_id
         


    def disconnect_account_moves_for_cycle_counter(self):

        if self.transaction_id:     


            url = self.env['integration.config'].sudo().search([('name','=','handle_asset_transfer')]).server_ip
            client = Client(url)
            response = client.service.AssetDel(self.request_id.department_id.nomin_code,"",self.transaction_id)
            if response[:7] == 'Success':
                    self.sudo().write({ 
                            'connection_state': 'doubtful' ,
                            'transaction_id':''
                            }) 
            else:
                raise UserError('Diamond-с ирсэн мэдээлэл cas - ' + response )



    def connect_account_moves_for_accountant(self):

        self.account_move_id_for_accountant
           


    def disconnect_account_moves_for_accountant(self):

        if self.account_move_id_for_accountant:      
            self.sudo().write({ 
                'connection_state': 'doubtful' 
                }) 


    def diamond_integration_for_cycle_counter(self,client):

        diamond_json = json.loads(self.diamond_json)
        if self.account_receivable_id and self.receivable_income_account_id:
            if self.account_receivable_id.code and self.receivable_income_account_id.code:

                diamond_json.update({'RcvAccountID':self.account_receivable_id.code,
                    'SaleAccountId':self.receivable_income_account_id.code})
                if self.employee_id.id != 215:
                    diamond_json.update({'CustomerId':self.employee_id.passport_id,'SaleAccountCustomerID':self.employee_id.passport_id})

                new_list = []
                for detail in self.sudo().detail_ids:
                    if detail.is_expense:
                        if "Assets" in diamond_json:
                            # print 'diamond_json[uAssets]', diamond_json[u'Assets']
                            for dictionary in diamond_json[u'Assets']:
                                if dictionary[u'RegistryNumberID'] == detail.registry_number:
                                    dictionary.update({'SaleQty':"1"})
                                    new_list.append(dictionary)
                diamond_json[u'Assets'] = new_list

                self.sudo().write(
                {
                    'diamond_json':json.dumps(diamond_json),                
                })

                response = client.service.AssetExpMod("1",self.diamond_json)

                if response[:7] == 'Success':
                    self.sudo().write({'connection_state': 'confirmed' ,
                        'transaction_id':response[7:],
                        })
                else:
                    # raise UserError(response)
                    self.sudo().write({'transaction_id':response[7:],
                        })
# ++++++++++++++++++++++++++++++++++++++++==

        #     detail_ids.append((0,0,struct_value))
        #     print "\nIF\n",line_id.id,detail_ids,"\n\n"

        #     dictionary.update({'SaleQty':"100"})
        #     # dictionary[u'ToSupplyLocationInfID'] = line_id.id
        # result_dict.update({'erp_id':line_id.id})
        # line_id.sudo().write(
        # {
        #     'diamond_json':json.dumps(result_dict),                
        # })



    def handle_account_moves_for_cycle_counter(self):

        currency_id = 112
        journal_id = 33

        journal = self.env['account.journal'].search([('company_id','=',self.request_id.department_id.company_id.id),('type','=','general')])
        if journal:
            journal_id = journal[0].id


        employee_name = self.employee_id.name_related + '.' + self.employee_id.last_name[0]
        if self.employee_id.id == 215:
            employee_name = self.asset_name

        res = []
        for line in self.detail_ids:
            
            if line.is_expense:

                line_dict = {
                    'account_id': self.depreciation_account.id, # хуримтлагдсан элэгдэл ДТ
                    'name':employee_name ,
                    'currency_id':currency_id,
                    'company_currency_id':currency_id,
                    'partner_id':False,
                    'debit':line.accumulated_depreciation,
                    'credit':0,
                    'credit_cash_basis':line.accumulated_depreciation,
                    'balance':line.accumulated_depreciation,
                    'journal_id':journal_id,       
                }     
                res.append((0,0,line_dict))

                if line.current_value != 0:
                    
                    line_dict = {
                        'account_id': self.receivable_income_account_id.id, # Дахин үнэлгээний хойшлогдсон орлого ДТ
                        'name':employee_name ,
                        'currency_id':currency_id,
                        'company_currency_id':currency_id,
                        'partner_id':False,
                        'debit':line.current_value,
                        'credit':0,
                        'credit_cash_basis':line.current_value,
                        'balance':line.current_value,
                        'journal_id':journal_id,       
                    }     
                    res.append((0,0,line_dict))


                line_dict = {
                    'account_id': self.account_id.id,  # hɵrɵngɵ   КТ
                    'name':self.asset_name,
                    'currency_id':currency_id,
                    'company_currency_id':currency_id,
                    'partner_id':self.department_id.partner_id.id,
                    'debit':0,
                    'credit':line.capitalized_value, 
                    'credit_cash_basis':line.capitalized_value,
                    'balance':line.capitalized_value,
                    'journal_id':journal_id,    
                }   
                res.append((0,0,line_dict))

                line_dict = {
                    'account_id': self.account_receivable_id.id, #тооллого тооцооны авлага ДТ
                    'name':employee_name ,
                    'currency_id':currency_id,
                    'company_currency_id':currency_id,
                    'partner_id':False,
                    'debit':line.capitalized_value,
                    'credit':0,
                    'credit_cash_basis':line.capitalized_value,
                    'balance':line.capitalized_value,
                    'journal_id':journal_id,       
                }     
                res.append((0,0,line_dict))

                line_dict = {
                    'account_id': self.receivable_income_account_id.id,  # Дахин үнэлгээний хойшлогдсон орлого КТ
                    'name':self.asset_name,
                    'currency_id':currency_id,
                    'company_currency_id':currency_id,
                    'partner_id':self.department_id.partner_id.id,
                    'debit':0,
                    'credit':line.capitalized_value, 
                    'credit_cash_basis':line.capitalized_value,
                    'balance':line.capitalized_value,
                    'journal_id':journal_id,    
                }   
                res.append((0,0,line_dict))

        if self.account_move_id:

            self.account_move_id.sudo().write({
                'department_id':self.department_id.id,
                'date':self.request_id.start_date,
                'ref':employee_name + '=>' +self.asset_name,
                'company_id':self.department_id.company_id.id,
                'partner_id':self.department_id.partner_id.id,
                'journal_id':journal_id,
                'state':'draft',
                'line_ids':False,   
                })


            self.account_move_id.sudo().write({
                'line_ids':res,   
                })

        else:

            move_id = self.env['account.move'].create ({
                'department_id':self.department_id.id,
                'date':self.request_id.start_date,
                'ref':employee_name + '=>' +self.asset_name,
                'company_id':self.department_id.company_id.id,
                'partner_id':self.department_id.partner_id.id,
                'journal_id':journal_id,
                'state':'draft',
                'line_ids':res,
                    
                })

            self.account_move_id = move_id

        self.sudo().write({ 
            'connection_state': 'confirmed' 
            })

        return False
            
        


    def handle_account_moves_for_accountant(self):

        currency_id = 112
        journal_id = 33

        journal = self.env['account.journal'].search([('company_id','=',self.request_id.department_id.company_id.id),('type','=','general')])[0]
        if journal:
            journal_id = journal.id

        # line_id = self.get_active_object()

        # print 'line_id',line_id
        
        
        employee_name = self.employee_id.name_related + '.' + self.employee_id.last_name[0]
        if self.employee_id.id == 215:
            employee_name = self.asset_name


        res = []

        for line in self.detail_ids:
            if line.is_expense:
                ttl_charge_amount = 0
                for ln in line.amount_ids:
                    line_dict = {
                        'account_id': self.account_receivable_id_from_employee.id, # ААХА авлага   ДТ
                        'name':"1 " + ln.partner_id.name ,
                        'currency_id':currency_id,
                        'company_currency_id':currency_id,
                        'partner_id':ln.partner_id.id,
                        'debit':ln.charge_amount,
                        'credit':0,
                        'credit_cash_basis':ln.charge_amount,
                        'balance':ln.charge_amount,
                        'journal_id':journal_id,    
                        'company_id':self.department_id.company_id.id,   
                    }     
                    res.append((0,0,line_dict))

                    ttl_charge_amount += ln.charge_amount


                if line.capitalized_value >= ttl_charge_amount or ttl_charge_amount==1 and line.capitalized_value == 0:
                    
                

                    line_dict = {
                        'account_id': self.receivable_income_account_id.id, # Дахин үнэлгээний хойшлогдсон орлого ДТ
                        'name':"2 " + employee_name ,
                        'currency_id':currency_id,
                        'company_currency_id':currency_id,
                        'partner_id':False,
                        'debit':line.accumulated_depreciation,
                        'credit':0,
                        'credit_cash_basis':line.accumulated_depreciation,
                        'balance':line.accumulated_depreciation,
                        'journal_id':journal_id,  
                        'company_id':self.department_id.company_id.id,     
                    }     
                    res.append((0,0,line_dict))


                    line_dict = {
                        'account_id': self.loss_account_id.id, # Хөрөнгө данснаас хассны гарз ДТ
                        'name':"2 " + employee_name ,
                        'currency_id':currency_id,
                        'company_currency_id':currency_id,
                        'partner_id':False,
                        'debit':line.current_value,
                        'credit':0,
                        'credit_cash_basis':line.current_value,
                        'balance':line.current_value,
                        'journal_id':journal_id,       
                        'company_id':self.department_id.company_id.id,
                    }     
                    res.append((0,0,line_dict))


                    line_dict = {
                        'account_id': self.account_receivable_id.id,  #тооллого тооцооны авлага КТ
                        'name':"3 "+self.asset_name,
                        'currency_id':currency_id,
                        'company_currency_id':currency_id,
                        'partner_id':ln.partner_id.id,
                        'debit':0,
                        'credit':line.capitalized_value, 
                        'credit_cash_basis':line.capitalized_value,
                        'balance':line.capitalized_value,
                        'journal_id':journal_id,    
                        'company_id':self.department_id.company_id.id,
                    }   
                    res.append((0,0,line_dict))


                    vat = round(ttl_charge_amount/11,2)
                    profit = ttl_charge_amount - vat

                    if profit>0:

                        line_dict = {
                            'account_id': self.profit_account_id.id,  # Үндсэн хөрөнгө борлуулсны олз КТ
                            'name':"5 " + self.asset_name,
                            'currency_id':currency_id,
                            'company_currency_id':currency_id,
                            'partner_id':ln.partner_id.id,
                            'debit':0,
                            'credit':profit, 
                            'credit_cash_basis':profit,
                            'balance':profit,
                            'journal_id':journal_id,    
                            'company_id':self.department_id.company_id.id,
                        }   
                        res.append((0,0,line_dict))


                    line_dict = {
                        'account_id': self.vat_account.id,  # НӨАТ тооцоо  КТ
                        'name':"6 " + self.asset_name,
                        'currency_id':currency_id,
                        'company_currency_id':currency_id,
                        'partner_id':ln.partner_id.id,
                        'debit':0,
                        'credit':vat, 
                        'credit_cash_basis':vat,
                        'balance':vat,
                        'journal_id':journal_id, 
                        'company_id':self.department_id.company_id.id,   
                    }   
                    res.append((0,0,line_dict))
                else:
                    raise UserError('Капиталжуулсан үнэнээс үнэтэй зарах боломжгүй')

        if self.account_move_id_for_accountant:
            self.account_move_id_for_accountant.sudo().write({
                'department_id':self.department_id.id,
                'date':self.request_id.start_date,
                'ref':employee_name + '=>' +self.asset_name,
                'company_id':self.department_id.company_id.id,
                'journal_id':journal_id,
                'state':'draft',
                'line_ids':False,   
                })

            self.account_move_id_for_accountant.sudo().write({
                'line_ids':res,   
                })
        else:
            move_id = self.env['account.move'].sudo().create ({
                'department_id':self.department_id.id,
                'date':self.request_id.start_date,
                'ref':employee_name + '=>' +self.asset_name,
                'company_id':self.department_id.company_id.id,
                'journal_id':journal_id,
                'state':'draft',
                'line_ids':res,
                
                })


            # line.connection_state = 'confirmed'
            self.sudo().write ({
                'account_move_id_for_accountant':move_id.id,
                })

        return False
            



    
    def action_connect_transactions(self):

        confirmed_transactions = self.env['fixed.asset.counting.line'].search([('connection_state','=','confirmed')])
        
            # if confirmed_transaction.account_move_id.state == 'draft':

            #     confirmed_transaction.account_move_id.sudo().self_post()
            #     self.env.cr.commit()
            # if confirmed_transaction.account_move_id.state == 'posted':
            #     confirmed_transaction.update({'connection_state':'connected_for_cycle_counter'})

            # if confirmed_transaction.account_move_id_for_accountant.state == 'draft':
            #     confirmed_transaction.account_move_id_for_accountant.sudo().self_post()
            #     self.env.cr.commit()
            # if confirmed_transaction.account_move_id_for_accountant.state == 'posted' and \
            #     confirmed_transaction.connection_state == 'connected_for_cycle_counter':
            #     confirmed_transaction.update({'connection_state':'connected_for_accountant'})


class FixedAssetCounting(models.Model):

    _name = 'fixed.asset.counting'
    _description = 'Fixed asset counting'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "create_date desc"
    
    def _set_requested_employee(self): 
        employee_ids = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        if employee_ids:
            return employee_ids.id
        else:
            raise UserError(_('You don\'t have related company. Please contact administrator.'))
        return None


    # def _set_requested_employee_department(self): 
    #     employee_ids = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
    #     if employee_ids:
    #         return employee_ids.parent_department.id
    #     else:
    #         raise UserError(_('You don\'t have related company. Please contact administrator.'))
    #     return None



    
    state = fields.Selection([
        ('draft',u'Ноорог'),
        ('returned',u'Буцаагдсан'),
        ('count',u'Тоолох'),
        ('verify',u'Тоолсон'),       
        ('verified',u'Дууссан'),
        ('cancelled',u'Цуцлагдсан'),
    ], u'State', default='draft', tracking=True)


    type = fields.Selection([
        ('audit',u'Audit - Хяналтын тооллого'),
        ('basic',u'Basic - Үндсэн тооллого'),
        ('handover',u'Handover - Хүлээлцэх тооллого'),
    ], u'Tооллогын төрөл')




    def _role(self):
        for line in self:
            role = 'employee'
            try:
                if self.env.user.has_group('nomin_base.group_financial_account_user') or self.env.user.has_group('nomin_base.group_branch_account_user'):

                    if line.department_id.id  in self.env.user.purchase_allowed_departments.ids:
                        role = 'verifier'

            except Exception as e:
                role = 'employee'

            line.role = role

    role = fields.Selection([
        ('employee',u'Ажилтан'),
        ('verifier',u'Хянагч'),
    ], u'Дүр', compute=_role)

    name = fields.Char('Нэр',tracking=True)
    # is_same_company = fields.Boolean(string="Is same company", compute=_is_same_company, default=False)

    all_line_employees_are_same = fields.Boolean(string="All line employees are same", default=False)
    requested_employee_id = fields.Many2one('hr.employee', 'Үүсгэсэн ажилтан', index=True, readonly=True, \
         default=lambda self: self._set_requested_employee())
    start_date = fields.Date('Start date', readonly=True)
    end_date = fields.Date('End date', readonly=True)
    requested_date = fields.Datetime('Requested date', default=fields.Date.today)
    department_id = fields.Many2one('hr.department', domain="[('is_sector', '=', True)]",string='Салбар')
    account_from = fields.Many2one('account.account', string='Account from')
    approved_employee_id = fields.Many2one('hr.employee', 'Approved employee', tracking=True, readonly=True)
    change_line_ids = fields.One2many('fixed.asset.counting.line', 'request_id', 'Lines')
    change_line_ids_for_counting = fields.One2many('fixed.asset.counting.line', 'request_id', 'Lines_for_emp' )

    returned_reason = fields.Text('Returned reason', tracking=True, readonly=True)
    returned_description = fields.Text('Returned description', tracking=True, readonly=True)

    description = fields.Text('Тайлбар')

    # diamond_json = fields.Text(string=u'Диамондоос ирж бгаа утга агуулсан json')
    # transaction_id = fields.Char('Transaction ID')
    total_sale_price = fields.Float(compute='_total_sale_price',string='НӨАТ-тэй нийт дүн')
    total_vat_amount = fields.Float(compute='_total_vat_amount',string='НӨАТ')
    total_profit_n_loss_amount = fields.Float(compute='_total_profit_n_loss_amount',string='Гарз олзын дүн')
    diamond_binary = fields.Binary(string="Diamond binary")

    count_of_owners = fields.Integer('Эд хариуцагчийн тоо')
    count_of_rows = fields.Integer('Бэлтгэсэн мөрийн тоо')
    count_of_prepared_rows = fields.Integer('Тоолох мөрийн тоо')
    count_of_assets = fields.Integer('Хөрөнгийн нэр төрөл')
    qty = fields.Integer('Тоо ширхэг')
    difference = fields.Integer('Зөрчилтэй хөрөнгийн тоо')
    counted = fields.Integer('Тоолсон')
    completed = fields.Integer('Хянагдсан')

    filter_options = fields.Selection([
        ('аccount',u'Account - Дансаар шүүх'),
        ('owner',u'Owner - Эд хариуцагчаар шүүх'),
        ('type',u'Type - Данс ба хөрөнгийн бүлгээр шүүх'),
        ('code',u'Code - Данс ба хөрөнгийн кодоор шүүх'),
        ('location',u'Location - Байршил ба дансаар шүүх')
    ], u'Хөрөнгө шүүх сонголтууд')



    employee_id = fields.Many2one('hr.employee', string='Ажилтны нэр')
    location = fields.Char('Байршилын нэр')
    asset_type = fields.Char('Бүлгийн нэр')
    json_data = fields.Char('Json Data')
       
    asset_code = fields.Char('Шүүлтүүрдэх хөрөнгийн код')
    employee_ids = fields.Many2many('hr.employee', string='Шүүлтүүрдэх ажилтнууд',domain="[('parent_department','=',department_id)]")
    transfers = fields.One2many('fixed.asset.transfer', 'counting_id', 'Transfers')
    

    # @api.model
    # def create(self, vals):
    #     result = super(FixedAssetCounting, self).create(vals)
    #     return result



    
    def write(self, vals):
        result = super(FixedAssetCounting, self).write(vals)
        # if vals.get('employee_id'):
        #     self.department_id = self.requested_employee_id.parent_department

        if vals.get('start_date') and self.name:
            self.name = self.name[0:3] + str(self.start_date)[2:4] + self.name[5:6] + str(self.start_date)[5:7] + self.name[8:9]
            
        return result



    
    def unfilter_assets(self):
        # zzzz = self.env['fixed.asset.counting.line'].search([('backup_id','=',self.id)])
        # print 'zzzz',zzzz
        # self.change_line_ids_for_counting = zzzz

        string1 = "update fixed_asset_counting_line set request_id=backup_id where backup_id=%s "%(str(self.id))
        self.env.cr.execute(string1)

        self.asset_code = ''


    
    def filter_assets(self):
        # self.change_line_ids_for_counting = self.env['fixed.asset.counting.line'].search([('backup_id','=',self.id)])

        string1 = "update fixed_asset_counting_line set request_id=backup_id where backup_id=%s "%(str(self.id))
        self.env.cr.execute(string1)

        extra_str = ')'
        if self.asset_code:
            extra_str = " asset_id not like \'" + "%" + self.asset_code + "%\')"

        emp_str = ''
        if self.employee_ids :
            employee_ids = str(tuple(self.employee_ids.ids))
            if len(self.employee_ids.ids)==1:
                employee_ids = '(' + str(tuple(self.employee_ids.ids)[0]) + ')'
            emp_str = 'employee_id not in ' + employee_ids 


        or_sign = ''
        if self.employee_ids and self.asset_code: 
            or_sign = ' or'   

        if self.employee_ids or self.asset_code:
            string1 = "update fixed_asset_counting_line set request_id=null where request_id=%s and ("%(str(self.id)) + emp_str + or_sign + extra_str
            self.env.cr.execute(string1)


    
    def filter_few_assets(self):

        string1 = "update fixed_asset_counting_line set request_id=null where request_id=%s"%(str(self.id))
        self.env.cr.execute(string1)

        string1 = "select count(id) id from fixed_asset_counting_line where backup_id=%s and filter_by30s=False and counted_qty = qty"%(str(self.id))
        self.env.cr.execute(string1)
        zzz = self.env.cr.fetchone()

        if zzz[0] == 0:
            string1 = "update fixed_asset_counting_line set filter_by30s=False where backup_id=%s"%(str(self.id))
            self.env.cr.execute(string1)


        string1 = """update fixed_asset_counting_line set request_id=%s,filter_by30s=True where id in (
            select id from fixed_asset_counting_line where backup_id=%s and counted_qty = qty and filter_by30s=False limit 30)"""%(str(self.id),str(self.id))
        # print 'string1',string1
        self.env.cr.execute(string1)



    
    def filter_while_complete_counting(self):

        string1 = "update fixed_asset_counting_line set request_id=null where request_id=%s"%(str(self.id))
        self.env.cr.execute(string1)
        string1 = "update fixed_asset_counting_line set request_id=%s where difference < 0 and expense_cnt<>0 and backup_id=%s"%(str(self.id),str(self.id))
        self.env.cr.execute(string1)


    def get_current_employee_id(self): 
        employee_ids = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        if employee_ids:
            return employee_ids.id
        else:
            raise UserError(_('You don\'t have related user. Please contact administrator.'))



    
    def button_to_handle(self):

        for line in self.change_line_ids_for_counting:
            if line.qty + line.income - line.expense == line.counted_qty: 
                if line.is_invisible == 0 and line.difference != 0 and line.state == 'count' and line.expense!=0:
                    line.sudo().handle_journal_entries_for_cycle_counter()
                    line.sudo().connect_account_moves_for_cycle_counter()
                elif line.account_move_id:
                    string1 = "delete from account_move_line where move_id=%s"%(str(line.account_move_id.id))
                    self.env.cr.execute(string1)
                    string1 = "delete from account_move where id=%s"%(str(line.account_move_id.id))
                    self.env.cr.execute(string1)
            else:
                raise UserError(_('%s-р мөр дээр орлогодсон болон зарлагадсан хөрөнгийн тоо нь баланслахгүй байна'%(str(line.id))))
        

    
    def action_get_asset_type(self):
        self.env['fixed.assets.type'].sudo().get_type(self.department_id.nomin_code, True)

    
    def action_request(self):
        count = 0
        for line in self.change_line_ids:
            count+=1
        self.change_line_ids.sudo().write({'state': 'count'})
        self.sudo().write({'state': 'count','count_of_assets':count})


    
    def action_complete_counting(self): 
        jump = True
        self.unfilter_assets()
        count_of_prepared_rows = 0
        difference = 0
        for line in self.change_line_ids_for_counting:
            if line.difference != 0:
                difference += 1
                jump = False
            count_of_prepared_rows =+ 1
            


            
            # print 'line.difference',line.difference,line.is_invisible
            # if line.counted_qty < 0:
            #     line.sudo().write({'state': 'count'})
            #     raise UserError('Зарим мөр дээрх тоолсон тоог 0-с бага тоо оруулсан байна!')
            # elif line.difference != 0 and line.is_invisible == 0 :
            #     line.sudo().write({'state': 'count'})
            #     raise UserError('Зарим мөр дээрх зөрүүнүүдийг зохицуулалт хийгээгүй байна!')
            # else:
            #     line.sudo().write({'state': 'verify'})
                

        if jump:
            self.sudo().write({
                'state': 'verified',
                'counted':1,
                'completed':1,
                'count_of_prepared_rows':count_of_prepared_rows,
                })

        else:
            self.sudo().button_to_handle()
            str1 = ''
            go_to_next_state = True
            count_of_prepared_rows = 0
            for line in self.change_line_ids_for_counting:
                if line.counted_qty < 0:
                    go_to_next_state = False
                    # line.sudo().write({'state': 'count'})
                    str1 = 'Зарим мөр дээрх тоолсон тоог 0-с бага тоо оруулсан байна!'
                elif line.difference != 0 and line.is_invisible == 0 and (line.income == 0 and line.expense == 0 ):
                    go_to_next_state = False
                    str1 = str(line.id) + ' дугаартай мөр дээрх зөрүүнүүдийг зохицуулалт хийгээгүй байна! "Зөрүү шийдэх" товч харагдахгүй бол "Шүүлтүүрийг болих" товчийг дарж дараа нь зохицуулалтыг хийнэ үү! '
                elif line.difference != 0 and line.is_invisible != 0 and (line.income == 0 and line.expense == 0 ):
                    go_to_next_state = False
                    str1 = str(line.id) + 'Зарим мөр дээрх зөрүүнүүдийг зохицуулалт хийгээгүй 888888888888888888888888888888888888888'
                count_of_prepared_rows =+ 1        

            if go_to_next_state==False:
                raise UserError(str1)
                
            if go_to_next_state:
                self.sudo().write({
                    'state': 'verify',
                    'counted':1,
                    'difference':difference,
                    'count_of_prepared_rows':count_of_prepared_rows,
                    })
                self.sudo().change_line_ids_for_counting.write({'state': 'verify'})
                
            self.filter_while_complete_counting()
            return {'type': 'ir.actions.act_window_close'}
        
 
    
    def action_verify(self): 

        self.unfilter_assets()

        # for line in self.change_line_ids_for_counting:
        #     print 'expense_cnt',line.expense_cnt
        #     if line.expense_cnt > 0:
        #         line.sudo().write({'state': 'verify'})
        #         raise UserError('Бүх зарлагадах товчуудыг алга болгох хэрэгтэй!')
        #     else:
        #         line.sudo().write({'state': 'verified'})



        for line in self.change_line_ids_for_counting:

            # if line.expense_cnt != 0:

            didnt_fill_out = False
            for detail in line.sudo().detail_ids:
                for amount in detail.amount_ids:
                    if amount.charge_amount == 0:
                        didnt_fill_out = True

                # if detail.sale_price == 0:
                #     print 'didnt_fill_out5555555555555',didnt_fill_out
                #     didnt_fill_out = True
                    

            if didnt_fill_out:
                raise UserError(str(line.id)+'-р мөрөнд байгаа хөрөнгүүдэд дахин үнэлгээ хийгээгүй байна.')

            elif line.qty + line.income - line.expense != line.counted_qty:
                raise UserError(str(line.id)+'-р мөрөнд орлогодох болон зарлагадахыг буруу бөглөсөн байна. \n'+ \
                    '\"Тоолсон тоо = Эцсийн үлдэгдэл = Эхний үлдэгдэл + Орлого - Зарлага\" гэсэн томъёог баримтал!')
            else:
                if line.is_invisible != 0:
                    line.sudo().handle_account_moves_for_accountant()
                    line.sudo().connect_account_moves_for_accountant()
                line.sudo().write({#'expense_cnt':0,
                    'state': 'verified'
                    })
                

        self.sudo().write({
            'state': 'verified',
            'completed':1})




    # 
    # def cancel(self):
    #     print 'self.state',self.state
    #     if self.state == 'verified':

    #         self.sudo().write({
    #             'state': 'cancelled',
    #             'completed':0})
    #         self.change_line_ids.sudo().write({'state': 'cancelled'})


    
    def reverse(self):

        self.unfilter_assets()


        if self.state in ('verify','verified'):


            for line in self.change_line_ids_for_counting:
                line.sudo().write({
                    'state': 'count',
                    'is_invisible' : 0,
                    # 'difference' : 0,
                    
                    # 'income' : 0,
                    # 'expense' : 0,
                    'income_cnt' : 0,
                    # 'expense_cnt' : 0,
                    'receive_cnt' : 0,
                    'transfer_cnt' : 0,
                    'connection_state' : 'doubtful',

                })


                if line.account_move_id:
                    line.account_move_id.sudo().line_ids = False
 
                line.sudo().disconnect_account_moves_for_cycle_counter()

                if self.state in ('verified'):
                    if line.account_move_id_for_accountant:
                        line.account_move_id_for_accountant.sudo().line_ids = False
                        line.sudo().disconnect_account_moves_for_accountant()
                
                for detail in line.detail_ids:
                    detail.sudo().amount_ids = False



            self.sudo().write({
                'state': 'count',
                'completed':0,
                'counted':0,
                'count_of_prepared_rows':0})





        elif self.state == 'count':

            for line_id in self.change_line_ids:

                line_id.sudo().write({
                    'state': 'draft',
                    'difference' : 0,
                    'current_qty' : 0,
                    'income' : 0,
                    'expense' : 0,
                    'income_cnt' : 0,
                    'expense_cnt' : 1,
                    'receive_cnt' : 0,
                    'transfer_cnt' : 0,
                })

            self.sudo().write({'state': 'draft'})
            # self.change_line_ids.sudo().write({'state': 'draft'})
        return {'type': 'ir.actions.act_window_close'}



    
    def unlink(self):

        for line in self:
            if line.state not in ('count','draft'):
                raise UserError(u'Зөвхөн ноорог болон тоолох төлвөөс устгах боломжтой!')
        return super(FixedAssetCounting, self).unlink()

    
    def action_expense(self):
        vals = {'report_type' : 'expense',
                'start_date' : self.start_date,
                'end_date' : self.end_date,
                'asset_counting_id' : self.id,
                }
                
        expense_id = self.env['asset.counting.report'].create(vals)
        return expense_id.export_chart()

    
    def action_income(self):
        vals = {'report_type' : 'income',
                'start_date' : self.start_date,
                'end_date' : self.end_date,
                'asset_counting_id' : self.id,
                }
                
        expense_id = self.env['asset.counting.report'].create(vals)
        return expense_id.export_chart()
 
    
    def action_transfer(self):
        vals = {'report_type' : 'transfer',
                'start_date' : self.start_date,
                'end_date' : self.end_date,
                'asset_counting_id' : self.id,
                }
                
        expense_id = self.env['asset.counting.report'].create(vals)
        return expense_id.export_chart()

    
    def action_damage_asset(self):
        vals = {'report_type' : 'damage_asset',
                'start_date' : self.start_date,
                'end_date' : self.end_date,
                'asset_counting_id' : self.id,
                }
                
        expense_id = self.env['asset.counting.report'].create(vals)
        return expense_id.export_chart()


class FixedAssetType(models.Model):

    _name = 'fixed.asset.type'
    _description = 'Fixed asset type'
    _order = "inf_id"

    inf_id = fields.Char('Inf ID')
    parent_inf_id = fields.Char('Parent inf ID')
    name = fields.Char('Name')
    department_id = fields.Many2one('hr.department', string='Department')
    
