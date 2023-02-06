# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning
from datetime import timedelta
from datetime import datetime

from dateutil.relativedelta import relativedelta

import json
from zeep import Client, Plugin
from odoo.exceptions import UserError #
import base64

import logging
_logger = logging.getLogger(__name__)
class MyLoggingPlugin(Plugin):

    def ingress(self, envelope, http_headers, operation):
        # print(etree.tostring(envelope, pretty_print=True))
        return envelope, http_headers

    def egress(self, envelope, http_headers, operation, binding_options):
        # print(etree.tostring(envelope, pretty_print=True))
        http_headers['Content-Type'] = 'text/json; charset=utf-8;'
        return envelope, http_headers

class AssetTransferLine(models.Model):

    _name = 'asset.transfer.line'
    _description = 'Asset transfer line'
    _order = "employee_id,asset_name"


    # 
    # def _check_employee(self):
    #     for line in self:
    #         if line.employee_id and line.request_id and line.registry_number:
    #             for change_line in line.request_id.change_line_ids:
    #                 if change_line.id != line.id and change_line.employee_id.id == line.employee_id.id and change_line.registry_number == line.registry_number:
    #                     return False
    #     return True

    # _constraints = [
    #     (_check_employee, u'Нэг хөрөнгийг 2 удаа харуулах боломжгүй!', []),
    # ]

    
    def compute_time_plan(self):
        for line in self:
            line.warning_type = "normal"


    def _set_employee(self): 
        employee_ids = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        if employee_ids:
            return employee_ids.id
        else:
            raise UserError(_('You don\'t have related company. Please contact administrator.'))
        return None



    def _show_accept_button(self):

        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
       
        for line in self:
            if line.employee_id != line.receiver_employee_id and line.receiver_employee_id == employee_id \
                and line.state == 'accept':
                line.show_accept_button = True 
            else:
                line.show_accept_button = False


    show_accept_button = fields.Boolean(u'Towq haruulah', compute=_show_accept_button, default=False)




    state = fields.Selection([
        ('draft',u'Ноорог'),
        ('returned',u'Буцаагдсан'),
        ('verify',u'Хянах'),
        ('accept',u'Зөвшөөрөх'),
        ('approve',u'Батлах'),
        ('approved',u'Батлагдсан'),

    ], u'State', default='draft', tracking=True)



    employee_id = fields.Many2one('hr.employee', required=True, string='Employee', default = _set_employee)
    job_id = fields.Many2one('hr.job', string='Job')
    
    # Form haragdats ashiglaj ehelvel is_from_unused_assets ene talbariig xml haragdats deer n read only bolgoh
    is_from_unused_assets = fields.Boolean(string="Is from unused assets", default=False)
    warning_type = fields.Char(u'Warning type', compute="compute_time_plan", store=True)

    request_id = fields.Many2one('asset.transfer.request', string='Request', ondelete='cascade')
    account_id = fields.Many2one('account.account',  string='Sender asset account')
    receiver_asset_account_id = fields.Many2one('account.account',  string='Receiver asset account')
    receiver_depreciation_account_id = fields.Many2one('account.account',  string='Receiver depreciation account')
    receiver_stockkeeper = fields.Char(string='Receiver stockkeeper')
    receiver_employee_id = fields.Many2one('hr.employee', required=True, string='Receiver employee',domain="[('parent_department','=',parent.receiver_department_id)]")
    receiver_job_id = fields.Many2one('hr.job', string='Receiver job')
    
    qty = fields.Integer('Quantity')
    amount = fields.Float('Amount')
    capitalized_value = fields.Float('Capitalized value')
    accumulated_depreciation = fields.Float('Accumulated depreciation')
    current_value = fields.Float('Current value')
    sale_price = fields.Float('Sale price')
    
    product_id = fields.Many2one('product.template', string='Product')
    asset_id = fields.Char('AssetID')
    registry_number = fields.Char('RegistryNumber')
    asset_name = fields.Char('Asset name')
    start_date = fields.Date('Start Date')
    

    @api.onchange('employee_id')
    def onchange_employee(self):
        if self.employee_id:
            self.set_employee_information(self)


    @api.onchange('receiver_employee_id')
    def onchange_receiver_employee(self):
        if self.receiver_employee_id:
            self.set_receiver_employee_information(self)

    @api.model
    def create(self, vals):
        result = super(AssetTransferLine, self).create(vals)
        self.set_employee_information(result)

        return result

    
    def write(self, vals):
        result = super(AssetTransferLine, self).write(vals)
        if vals.get('employee_id'):
            self.sudo().set_employee_information(self)
        if vals.get('receiver_employee_id'):
            self.sudo().set_receiver_employee_information(self)
        if vals.get('receiver_employee_id') and not vals.get('is_from_unused_assets'):
            self.is_from_unused_assets = False
        return result

    def set_employee_information(self, result):
        result.job_id = result.employee_id.job_id or None
        # result.department_id = result.employee_id.parent_department or None

    def set_receiver_employee_information(self, result):
        result.job_id = result.employee_id.job_id or None
        # result.receiver_department_id = result.receiver_employee_id.parent_department or None


    
    def action_accept(self):

        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        if employee_id and self.receiver_employee_id == employee_id :
            self.write({'state': 'approved'})

        if self.request_id.is_all_approved():
            self.request_id.sudo().action_accept_all()



    
    def action_get_details(self):


        # client = Client('http://10.0.10.117/Nomin.WS/Odoo/Asset.svc?wsdl')
        url = self.env['integration.config'].sudo().search([('name','=','handle_asset_transfer')]).server_ip
        client = Client(url)
        response = client.service.AssetGet("1","2021-01-14","50","1","","1","","1","","1","","0","200310010124800000")
        # if response.status_code == 200:	
        result_dict = json.loads(response)
        if result_dict:
            # print '\n dddddddddd ',response


            if not self.request_id.change_line_ids:
                for dictionary in result_dict[u'Assets']:
                    # print '\nffffffffff ',dictionary
                    account_id = self.env['account.account'].search([('code','=',dictionary[u'AccountID'])])
                    self.request_id.change_line_ids.create({
                        'request_id':self.id,
                        'asset_id':dictionary[u'AssetID'],
                        'registry_number':dictionary[u'FromRegistryNumberInfID'],
                        'asset_name':dictionary[u'AssetDesc'],
                        'qty':dictionary[u'EndQty'],
                        'amount':dictionary[u'BeginUnitCost'],
                        'start_date':dictionary[u'BeginUsedDate'],
                        'account_id':account_id.id,
                        'employee_id':6813,
                        'receiver_employee_id':6813,
                        })



class AssetTransferRequest(models.Model):

    _name = 'asset.transfer.request'
    _description = 'Asset transfer request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "create_date desc"

    def _set_requested_employee(self): 
        employee_ids = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        if employee_ids:
            return employee_ids.id
        else:
            raise UserError(_('You don\'t have related company. Please contact administrator.'))
        return None


    def _set_requested_employee_department(self): 
        employee_ids = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        if employee_ids:
            return employee_ids.parent_department.id
        else:
            raise UserError(_('You don\'t have related company. Please contact administrator.'))
        return None


    
    @api.depends('change_line_ids.sale_price')
    def _total_sale_price(self):


        coefficient = 0.0
        if not self.is_same_company:
            coefficient = 0.1

        for obj in self:
            try:
                obj.total_sale_price = sum([line.sale_price + line.sale_price * coefficient if line.receiver_employee_id.id <> 215 else 0.0 for line in obj.change_line_ids])
            except Exception as e:
                obj.total_sale_price = 0


    
    @api.depends('change_line_ids.sale_price','change_line_ids.current_value')
    def _total_profit_n_loss_amount(self):

        for obj in self:
            try:
                obj.total_profit_n_loss_amount = sum([line.sale_price-line.current_value for line in obj.change_line_ids])
            except Exception as e:
                obj.total_profit_n_loss_amount = 0




    
    @api.depends('change_line_ids.sale_price')
    def _total_vat_amount(self):

        for obj in self:
            try:
                obj.total_vat_amount = sum([line.sale_price * 0.1  if line.receiver_employee_id.id <> 215 else 0.0 for line in obj.change_line_ids])
            except Exception as e:
                obj.total_vat_amount = 0







    
    state = fields.Selection([
        ('draft',u'Ноорог'),
        ('returned',u'Буцаагдсан'),
        ('verify',u'Хянах'),
        ('approve',u'Батлах'),        
        ('accept',u'Зөвшөөрөх'),
        ('approved',u'Батлагдсан'),
    ], u'State', default='draft', tracking=True)


    type = fields.Selection([
        ('asset',u'Хөрөнгө'),
        ('supply',u'Эд материал'),
    ], u'Tөрөл',   tracking=True)



    def _is_same_company(self):
        
        if self.department_id.company_id ==  self.receiver_department_id.company_id:
            self.is_same_company = True
        else:
            self.is_same_company = False 


    
    def _compute_button_clickers(self):
        if self.state == 'verify':
            group_id = self.env['ir.model.data'].sudo().get_object_reference('nomin_base', 'group_financial_account_user')[1]
            user_ids = self.env['res.groups'].browse(group_id).users
            users = []
            for user in user_ids:
                if self.department_id.id in user.purchase_allowed_departments.ids:
                    users.append(user.id)
            self.button_clickers = users
        elif self.state == 'approve':
            group_id = self.env['ir.model.data'].sudo().get_object_reference('nomin_base', 'group_financial_account_user')[1]
            user_ids = self.env['res.groups'].browse(group_id).users
            users = []
            for user in user_ids:
                if self.receiver_department_id.id in user.purchase_allowed_departments.ids and self.state in ['approve','accept','approved']:
                    users.append(user.id)
            self.button_clickers = users
            

    def _role(self):
        for line in self:
            role = 'employee'
            try:
                if self.env.user.has_group('nomin_base.group_financial_account_user') or self.env.user.has_group('nomin_base.group_branch_account_user'):

                    if line.department_id.id  in self.env.user.purchase_allowed_departments.ids:
                        role = 'verifier'
                        
                    if line.receiver_department_id.id  in self.env.user.purchase_allowed_departments.ids and line.state in ['approve','accept','approved']:
                        role = 'approver'
            except Exception as e:
                role = 'employee'

            line.role = role


    role = fields.Selection([
        ('employee',u'Ажилтан'),
        ('verifier',u'Хянагч'),
        ('approver',u'Батлагч'),
    ], u'Дүр', compute=_role)

    is_same_company = fields.Boolean(string="Is same company", compute=_is_same_company, default=False)

    all_line_employees_are_same = fields.Boolean(string="All line employees are same", default=False)
    is_from_unused_assets = fields.Boolean(string="Is from unused assets", default=False)
    requested_employee_id = fields.Many2one('hr.employee', 'Requested employee', index=True, readonly=True, \
         default=lambda self: self._set_requested_employee())
    transfer_date = fields.Date('Transfer date', readonly=True)
    requested_date = fields.Datetime('Requested date', default=fields.Date.today)
    department_id = fields.Many2one('hr.department', domain="[('is_sector', '=', True)]",string='Department', default=_set_requested_employee_department)
    account_from = fields.Many2one('account.account', string='Account from')

    sender_vat_account_id = fields.Many2one('account.account',  string='Sender vat account', domain="[('department_id', '=', department_id)]")
    sender_account_receivable_id = fields.Many2one('account.account',  string='Sender account receivable',domain="[('department_id', '=', department_id)]")
    sender_profit_account_id = fields.Many2one('account.account',  string='Илгээгчийн олзын данс')
    sender_loss_account_id = fields.Many2one('account.account',  string='Илгээгчийн гарзын данс')

    receiver_department_id = fields.Many2one('hr.department', string='Receiver department')
    receiver_vat_account_id = fields.Many2one('account.account',  string='Receiver vat account')
    receiver_account_payable_id = fields.Many2one('account.account',  string='Receiver account payable')
    approved_employee_id = fields.Many2one('hr.employee', 'Approved employee', tracking=True, readonly=True)
    change_line_ids = fields.One2many('asset.transfer.line', 'request_id', 'Employees')
    change_line_ids_for_sender = fields.One2many('asset.transfer.line', 'request_id', 'Employees')
    change_line_ids_for_receiver = fields.One2many('asset.transfer.line', 'request_id', 'Employees')

    returned_reason = fields.Text('Returned reason', tracking=True, readonly=True)
    returned_description = fields.Text('Returned description', tracking=True, readonly=True)

    description = fields.Text('Description')

    diamond_json = fields.Text(string=u'Диамондоос ирж бгаа утга агуулсан json')
    transaction_id = fields.Char('Transaction ID')
    total_sale_price = fields.Float(compute='_total_sale_price',string='НӨАТ-тэй нийт дүн')
    total_vat_amount = fields.Float(compute='_total_vat_amount',string='НӨАТ')
    total_profit_n_loss_amount = fields.Float(compute='_total_profit_n_loss_amount',string='Гарз олзын дүн')
    diamond_binary = fields.Binary(string="Diamond binary")
    button_clickers = fields.Many2many('res.users',string='Товч дарах хэрэглэгчид', compute=_compute_button_clickers)
    

       
    
    @api.model
    def create(self, vals):
        result = super(AssetTransferRequest, self).create(vals)
        result.department_id = result.requested_employee_id.parent_department
        self.check_description_length(result)
        return result



    
    def write(self, vals):
        result = super(AssetTransferRequest, self).write(vals)
        if vals.get('employee_id'):
            if self.department_id != self.receiver_department_id:
                self.department_id = self.requested_employee_id.parent_department
        if vals.get('description'):
            self.check_description_length(self)
            
        return result

    def check_description_length(self, result):
        if result.description and len(result.description) > 150:
            raise UserError(_('Тодорхойлолтын үсгийн тоо 150 аас хэтэрч болохгүй!'))

    def get_current_employee_id(self): 
        employee_ids = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        if employee_ids:
            return employee_ids.id
        else:
            raise UserError(_('You don\'t have related user. Please contact administrator.'))



    
    def action_delete_waiting_ones(self):

        if self.type == 'asset':

            url = self.env['integration.config'].sudo().search([('name','=','handle_asset_transfer')]).server_ip
            client = Client(url)

            response = client.service.AssetWaitingDel(self.department_id.nomin_code,str(self.account_from.code))
            raise UserError(str(response) + ' бичлэг устгалаа!')

        else:

            url = self.env['integration.config'].sudo().search([('name','=','handle_supply_transfer')]).server_ip
            client = Client(url)

            response = client.service.SupplyWaitingDel(self.department_id.nomin_code,str(self.account_from.code))
            raise UserError(_(str(response) + ' бичлэг устгалаа!'))



    
    def send_received_confirmation(self):
        if self.diamond_json:
            result_dict = json.loads(self.diamond_json) if self.diamond_json else {}
        else:
            result_dict = json.loads(base64.decodestring(self.diamond_binary)) if self.diamond_binary else {}

        if self.type == 'asset':

            for dictionary in result_dict[u'Assets']:
                dictionary[u'ToAccountantInfID'] = ''
            url = self.env['integration.config'].sudo().search([('name','=','handle_asset_transfer')]).server_ip
            client = Client(url)
            # response = client.service.AssetAccept("1",json.dumps(result_dict))
            response=""
        #     is_done = False
        #     c=50
        #     d=0
        #     while not is_done:
        #         result_send={}
        #         [result_send.update({k:v}) for k,v in result_dict.iteritems() if k !="Assets"]
        #         if result_dict['Assets'][d:c]:                    
        #             result_send.update({'Assets':result_dict['Assets'][d:c]})
        #             response = client.service.AssetAccept("1",json.dumps(result_send))
        #             d=c
        #             c=c+50
        #         else:
        #             is_done =True

        # else:

        #     for dictionary in result_dict[u'Supply']:
        #         dictionary[u'ToSupplyLocationInfID'] = ''
        #     url = self.env['integration.config'].sudo().search([('name','=','handle_supply_transfer')]).server_ip
        #     client = Client(url)
        #     response = client.service.SupplyAccept("1",json.dumps(result_dict))


        # # print '\n\n\n\n\n\n\n\nresponses',response[:7]
        # # print '\n\n\n\n\n\n\n\nresponses7',response



        # if response[:7] == 'Success':
        #     return True
        # else:
        #     return False
        

        return True



        


    
    def action_request(self):

        
        if self.send_received_confirmation():

            if self.department_id == self.receiver_department_id and self.type == 'asset':
                self.change_line_ids.sudo().write({'state': 'accept'})
                self.sudo().write({'state': 'accept'})
                self.auto_accept_all_from_unused_assets()
                follower_ids = []
                for line in self.change_line_ids:
                    if line.employee_id != line.receiver_employee_id:
                        follower_ids.append(line.receiver_employee_id.user_id.id)

                    if follower_ids != []:
                        self.sudo().message_subscribe_users(follower_ids) 


            elif self.sender_account_receivable_id and self.sender_profit_account_id and self.sender_loss_account_id:
                self.change_line_ids.sudo().write({'state': 'approve'})
                self.sudo().write({'state': 'approve'})

            else:
                self.sudo().write({'state': 'verify'})

        else:
            raise UserError('Хүлээн авлаа гэсэн баталгаажуулалтанд диамонд хариу өгсөнгүй')

        


    
    def action_verify(self): 
        if not self.sender_account_receivable_id:
            raise UserError('Илгээгчийн авлагын дансыг бөглөнө үү!')
        if not self.sender_profit_account_id:
            raise UserError('Илгээгчийн олзын дансыг бөглөнө үү!')
        if not self.sender_loss_account_id:
            raise UserError('Илгээгчийн гарзын дансыг бөглөнө үү!')
        if not self.is_same_company and not self.sender_account_receivable_id:
            raise UserError('Илгээгчийн НӨАТ-н дансыг бөглөнө үү!')

        self.change_line_ids.sudo().write({'state': 'approve'})
        self.sudo().write({'state': 'approve'})

    def is_all_approved(self):
        for line in self.change_line_ids:
            if line.state != 'approved' and line.employee_id != line.receiver_employee_id:
                return False
        return True
       
    
    def action_accept_all(self): 
        
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        if not employee_id:
            raise UserError('Холбоотой ажилтан олдсонгүй!')

        receiver_employee_ids = []
        receiver_employee_names = ''
        is_receiver = False
        is_approved = False
        for line in self.change_line_ids:
            if line.employee_id == line.receiver_employee_id:
                continue
            if line.receiver_employee_id == employee_id:
                if not is_approved and line.state != 'approved':
                    is_approved = True
                line.write({'state': 'approved'})
                is_receiver = True
            elif line.state != 'approved' and line.receiver_employee_id:
                if line.receiver_employee_id not in receiver_employee_ids:
                    receiver_employee_ids.append(line.receiver_employee_id)
        
        # for receiver_employee_id in receiver_employee_ids:
        #     receiver_employee_names += receiver_employee_id.name + ' ' + receiver_employee_id.last_name + ", "

        # is_all_approved = self.is_all_approved()
        # if is_approved and not is_all_approved:
        #     return

        # if is_receiver and not is_all_approved:
        #     raise UserError('Та аль хэдийн зөвшөөрсөн байна!\nДараах ажилчид зөвшөөрөөгүй байна: [ %s]' % (receiver_employee_names))
        # elif not is_all_approved:
        #     raise UserError('Та зөвшөөрөх ажилтан биш байна!\nДараах ажилчид зөвшөөрөөгүй байна. [ %s]' % (receiver_employee_names))

        if self.type == 'asset':
            if self.transaction_id and self.transaction_id <> '':
                # print '\n\n\n\n\n\nself.transaction_id',self.transaction_id
                self.cancel_assets()
            self.send_all_changes_to_diamond()
        else:
            self.send_all_supplies_to_diamond()
            
    
    def auto_accept_all_from_unused_assets(self):
        for line in self.change_line_ids:
            if line.is_from_unused_assets:
                line.write({'state': 'approved'})
        if self.is_all_approved():
            self.action_accept_all()



    
    def action_approve(self):


        if self.department_id == self.receiver_department_id:
            raise UserError('Хэрэв хөрөнгийг салбар дотороо шилжүүлэх гэж байгаа бол хариуцсан нягтлангаараа хийлгэ!')

        zzzz = datetime.strptime(self.requested_date, '%Y-%m-%d %H:%M:%S') + timedelta(minutes = 1) 
        if zzzz < datetime.now():

            follower_ids = []
            all_filled_out = True
            for line in self.change_line_ids:
                if line.receiver_asset_account_id and line.receiver_depreciation_account_id:
                    print ''
                else:
                    all_filled_out = False

            if not all_filled_out:
                raise UserError('Хүлээн авах дансууд бүгд бөглөгдсөн байх ёстой!')


            is_same_employee = True
            for line in self.change_line_ids:
                if line.employee_id != line.receiver_employee_id:
                    is_same_employee = False

                    follower_ids.append(line.receiver_employee_id.user_id.id)

            if follower_ids != []:
                self.sudo().message_subscribe_users(follower_ids) 


            if is_same_employee:

                if self.type == 'asset':
                    if self.transaction_id and self.transaction_id <> '':
                        # print '\n\n\n\n\n\nself.transaction_id',self.transaction_id
                        self.cancel_assets()
                    self.send_all_changes_to_diamond()
                else:
                    self.send_all_supplies_to_diamond()

            else:
                self.change_line_ids.write({'state': 'accept'})
                self.write({'state': 'accept'})
                self.auto_accept_all_from_unused_assets()

        self.requested_date = datetime.now()
        






    
    def cancel(self):


        if self.type == 'asset':
            self.cancel_assets()
        else:
            self.cancel_supplies()

    
    def get_json(self):
        
        # print 'dddd'
        # if self.diamond_json:
        #     raise UserError(self.diamond_json)
        # else:
        print 'aaaa',self.diamond_binary
        raise UserError(base64.decodestring(self.diamond_binary))

    
    def cancel_assets(self):
        
        url = self.env['integration.config'].sudo().search([('name','=','handle_asset_transfer')]).server_ip
        client = Client(url)
        # tst ---------------------------------------------------------------------------------
        # response = client.service.AssetDel("0U1","0U2", self.transaction_id)

        response = ''
        if self.transaction_id:

            for trans in self.transaction_id.split(','):
                if trans:
                    if self.department_id == self.receiver_department_id:
                        # print 'ddd','['+str(trans) + ']'
                        # return
                        response = client.service.AssetMovHolderDel(self.department_id.nomin_code, '['+str(trans) + ']')
                    else:
                        response = client.service.AssetDel(self.department_id.nomin_code,self.receiver_department_id.nomin_code, trans)
        

        # print '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nfdddd ',response
        if response[:7] == 'Success':
            if self.department_id == self.receiver_department_id:
                self.sudo().write({'state': 'returned',
                'transaction_id':''})
            else:
                self.sudo().write({'state': 'approve',
                    'transaction_id':''})
        else:
            raise UserError('Diamond-с ирсэн мэдээлэл cas - ' + response )


        # --------------------
        if self.diamond_json:
            result_dict = json.loads(self.diamond_json) if self.diamond_json else {}
        else:
            result_dict = json.loads(base64.decodestring(self.diamond_binary)) if self.diamond_binary else {}

        for dictionary in result_dict[u'Assets']:
            dictionary[u'ToAccountantInfID'] = ''
        url = self.env['integration.config'].sudo().search([('name','=','handle_asset_transfer')]).server_ip
        client = Client(url)
        # response = client.service.AssetAccept("1",json.dumps(result_dict))
        response=""
        is_done = False
        c=30
        d=0
        while not is_done:
            result_send={}
            [result_send.update({k:v}) for k,v in result_dict.iteritems() if k !="Assets"]
            if result_dict['Assets'][d:c]:                    
                result_send.update({'Assets':result_dict['Assets'][d:c]})
                response = client.service.AssetAccept("1",json.dumps(result_send))
                d=c
                c=c+30
            else:
                is_done =True



    
    def cancel_supplies(self):
        
        url = self.env['integration.config'].sudo().search([('name','=','handle_supply_transfer')]).server_ip
        client = Client(url)
        # splts ---------------------------------------------------------------------------------
        # response = client.service.SupplyDel("0U1","0U2", self.transaction_id)
        response = client.service.SupplyDel(self.department_id.nomin_code,self.receiver_department_id.nomin_code, self.transaction_id)
        
        # print '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nfdddd ',response
        if response[:7] == 'Success':
            self.write({'state': 'approve'})
        else:
            raise UserError('Diamond-с ирсэн мэдээлэл css - ' + response )



        if self.diamond_json:
            result_dict = json.loads(self.diamond_json) if self.diamond_json else {}
        else:
            result_dict = json.loads(base64.decodestring(self.diamond_binary)) if self.diamond_binary else {}

        response = client.service.SupplyAccept("1",json.dumps(result_dict))

        # print '\n\n\n\n\n\n\n\nresponses',response[:7]
        # print '\n\n\n\n\n\n\n\nresponses7',response



        if response[:7] == 'Success':
            return True
        else:
            return False
        




    
    def reverse(self):

        if self.diamond_json:
            result_dict = json.loads(self.diamond_json) if self.diamond_json else {}
        else:
            result_dict = json.loads(base64.decodestring(self.diamond_binary)) if self.diamond_binary else {}


        if self.type == 'asset':

            for dictionary in result_dict[u'Assets']:
                dictionary[u'ToAccountantInfID'] = ''
            url = self.env['integration.config'].sudo().search([('name','=','handle_asset_transfer')]).server_ip
            client = Client(url)
            # response = client.service.AssetCancel("1",json.dumps(result_dict))
            response=""
            is_done = False
            c=30
            d=0
            while not is_done:
                result_send={}
                [result_send.update({k:v}) for k,v in result_dict.iteritems() if k !="Assets"]
                if result_dict['Assets'][d:c]:
                    result_send.update({'Assets':result_dict['Assets'][d:c]})
                    response = client.service.AssetCancel("1",json.dumps(result_send))
                    d=c
                    c=c+30
                    
                else:
                    is_done =True

        else:

            for dictionary in result_dict[u'Supply']:
                dictionary[u'ToSupplyLocationInfID'] = ''
            url = self.env['integration.config'].sudo().search([('name','=','handle_supply_transfer')]).server_ip
            client = Client(url)
            # print '\n\n\n\n\n\nnnnnnnnnnnnnn',json.dumps(result_dict)
            response = client.service.SupplyCancel("1",json.dumps(result_dict))


        # print '\n\n\n\n\n\n\n\nresponses',response[:7]
        # print '\n\n\n\n\n\n\n\nresponses7',response


        if response[:7] == 'Success':
            return True
        else:
            return False
        

 
    
    def action_resend_(self):
        self.reverse()
        self.send_received_confirmation()

    
    
    def action_reconfirm(self):
        self.cancel_assets()
        self.send_all_changes_to_diamond()



    
    def unlink(self):

        for line in self:
            if line.state not in ('draft','returned'):
                raise UserError(u'Зөвхөн ноорог болон буцаагдсан төлвөөс устгах боломжтой!')
        return super(AssetTransferRequest, self).unlink()




    
    def send_all_changes_to_diamond(self):

        
        url = self.env['integration.config'].sudo().search([('name','=','handle_asset_transfer')]).server_ip
        client = Client(url)

        # tst ---------------------------------------------------------------------------------
        # response = client.service.AssetInfo("1","0U2")
        response = client.service.AssetInfo("1",self.receiver_department_id.nomin_code)
        

        # print '\n\n\n\n\n\n\n\nresponsesa',response

        result_dict = json.loads(response)
        accountant_pkey = ''
        location_pkey = ''       
        if result_dict:

            if "LocationJson" in result_dict[0]:

                for dictionary in json.loads(result_dict[0][u'LocationJson']):
                    if dictionary['LocationID'] == self.receiver_department_id.nomin_code:
                        location_pkey = dictionary[u'PKey']
            else:
                raise UserError('Хүлээн авч байгаа диамонд дээр Байршил тохируулаагүй байна!' )
            if location_pkey == '':
                raise UserError('Хүлээн авч байгаа диамонд дээр [%s] дугаартай байршил тохируулаагүй байна!' % (self.receiver_department_id.nomin_code))


            if "FaAssetAccountantJson" in result_dict[0]:
                for dictionary in json.loads(result_dict[0][u'FaAssetAccountantJson']):
                    accountant_pkey = dictionary[u'PKey']
            else:
                raise UserError('Хүлээн авч байгаа диамонд дээр Нярав тохируулаагүй байна!' )

        if self.diamond_json:
            result_dict = json.loads(self.diamond_json) if self.diamond_json else {}
        else:
            result_dict = json.loads(base64.decodestring(self.diamond_binary)) if self.diamond_binary else {}
        for dictionary in result_dict[u'Assets']:
            query = """
                select id from asset_transfer_line where request_id = %s and registry_number = '%s'
            """ % (self.id, str(dictionary[u'RegistryNumberID']))
            self.env.cr.execute(query)
            result = self.env.cr.fetchall()
            dictionary.update({
                u'IsDeleted': False,
            })  

            if result:
                line_id = self.env['asset.transfer.line'].browse(result[0])
                
                if line_id.receiver_employee_id.id == 215 or \
                    self.department_id == self.receiver_department_id and line_id.employee_id == line_id.receiver_employee_id:

                    dictionary.update({
                        u'ToCustomerID': dictionary[u'FromCustomerID'] ,
                        # u'ToAccountID':  line_id.receiver_asset_account_id.code,
                        # u'ToDeprAccountID':  line_id.receiver_depreciation_account_id.code,

                        # u'ToAccountID':  dictionary[u'ToAccountID'],
                        # u'ToDeprAccountID':  dictionary[u'ToDeprAccountID'],
                        u'ToAccountantInfID': accountant_pkey, # dictionary[u'FromAccountantInfID'],
                        u'ToLocationInfID': location_pkey,      
                        u'IsDeleted': True ,        
                    }) 

                elif self.department_id == self.receiver_department_id:

                    dictionary.update({
                        u'ToCustomerID': line_id.receiver_employee_id.sudo().passport_id ,
                        u'ToAccountID':  dictionary[u'FromAccountID'],
                        u'ToDeprAccountID':  dictionary[u'FromDeprAccountID'],
                        u'ToAccountantInfID': accountant_pkey,
                        u'ToLocationInfID': location_pkey,              
                    })    

                else:
                    dictionary.update({
                        u'ToCustomerID': line_id.receiver_employee_id.sudo().passport_id ,
                        u'ToAccountID':  line_id.receiver_asset_account_id.code,
                        u'ToDeprAccountID':  line_id.receiver_depreciation_account_id.code,
                        u'ToAccountantInfID': accountant_pkey, 
                        u'ToLocationInfID': location_pkey,              
                    })    

            elif dictionary[u'ToAccountantInfID'] == 999999999999:
                dictionary.update({
                    u'ToCustomerID': dictionary[u'FromCustomerID'] ,
                    u'ToAccountantInfID': accountant_pkey, 
                    u'ToLocationInfID': location_pkey,      
                    u'IsDeleted': True ,        
                }) 

            else:
                dictionary.update({
                    u'IsDeleted': True ,
                })                 


        result_dict.update({
            u'FromVatAccountId':  self.sudo().sender_vat_account_id.code if self.sudo().sender_vat_account_id else '',
            u'FromRcvAccountId':  self.sudo().sender_account_receivable_id.code if self.sudo().sender_account_receivable_id else '',
            u'ToVatAccountId':  self.sudo().receiver_vat_account_id.code if self.sudo().receiver_vat_account_id else '',
            u'ToPblAccountId':  self.sudo().receiver_account_payable_id.code if self.sudo().receiver_account_payable_id else '',
            u'InvDate':  self.transfer_date,
            u'InvDescription':  self.description,
            u'FromGarzAccountId':  self.sudo().sender_loss_account_id.code if self.sudo().sender_loss_account_id else '',
            u'FromSaleAccountId':  self.sudo().sender_profit_account_id.code if self.sudo().sender_profit_account_id else '',



            # tst ---------------------------------------------------------------------------------
            u'ToDivisionId':  self.receiver_department_id.nomin_code,
            # u'ToDivisionId':  '0U2',
            


        })

# =======================================================================
# json haruulahyin tuld nemew

        # print 'result_dict',json.dumps(result_dict)
        # if self.diamond_json:
            
        #     # result_dict = json.loads(self.diamond_json) if self.diamond_json else {}
        #     self.diamond_json = json.dumps(result_dict)
        # else:
        #     # result_dict = json.loads(base64.decodestring(self.diamond_binary)) if self.diamond_binary else {}
        


#===========================================================================
        try:

            new_list = []
            for dictionary in result_dict[u'Assets']:
                if not dictionary[u'IsDeleted']:
                    new_list.append(dictionary)
            result_dict[u'Assets'] = new_list

            # print '\n\n\n\n\n\n\n\ndddddddddddddddsssssss3 ',json.dumps(result_dict)
            # return
            # response = client.service.AssetMod("1",json.dumps(result_dict))
            response=""
            is_done = False
            c=30
            d=0
            transaction_id=""
            while not is_done:
                result_send={}
                [result_send.update({k:v}) for k,v in result_dict.iteritems() if k !="Assets"]
                if result_dict['Assets'][d:c]:
                    result_send.update({'Assets':result_dict['Assets'][d:c]})
                    
                    if self.department_id == self.receiver_department_id:
                        response = client.service.AssetMovHolderMod("1",json.dumps(result_send))
                    else:
                        response = client.service.AssetMod("1",json.dumps(result_send))

                    d=c
                    c=c+30           
                    response1 = response
                    if response[:7] == 'Success':
                        transaction_id=transaction_id+response[7:]+","
                        self.sudo().write({
                            'transaction_id':transaction_id,
                            'state': 'approved'
                            })

                    else:
                        if self.transaction_id and self.transaction_id <> '':
                            self.cancel_assets()
                        raise UserError('Diamond-с ирсэн мэдээлэл1 - ' + response1 )

                else:
                    is_done =True

            # print '\n\n\n\n\n\n\n\nresponses',response[:7]
            # print '\n\n\n\n\n\n\n\nresponses7',response

            employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])

            if response[:7] == 'Success':
                # print 'd55555555555555555555555555555555'
                self.write({'state': 'approved',
                    'transaction_id':transaction_id,
                    'approved_employee_id':employee_id.id,
                    })
            else:
                raise UserError('Diamond-с ирсэн мэдээлэл - ' + response )

        except Exception as e:	
            # _logger.info(u'Connection Error [%s]'%(e))
            # return None
            raise UserError('Diamond-с ирсэн мэдээлэл - ' + response)
        finally:
            self.diamond_binary = base64.encodestring(json.dumps(result_dict))





    
    def send_all_supplies_to_diamond(self):


        url = self.env['integration.config'].sudo().search([('name','=','handle_supply_transfer')]).server_ip
        client = Client(url)

        self.write({'state': 'approved'})

        # splts ---------------------------------------------------------------------------------
        # response = client.service.SupplyInfo("1","0U2")
        response = client.service.SupplyInfo("1",self.receiver_department_id.nomin_code)
        
        
        result_dict = json.loads(response)
        item_location_pkey = ''
        supply_location_pkey = ''  
  
        if result_dict:

            if "ItemLocationJson" in result_dict[0]:

                for dictionary in json.loads(result_dict[0][u'ItemLocationJson']):
                    item_location_pkey = dictionary[u'PKey']
                for dictionary in json.loads(result_dict[0][u'SupplyLocationJson']):
                    supply_location_pkey = dictionary[u'PKey']


            # print '\n\n\n\n\n\n\nsupply_location_pkey',supply_location_pkey
            # print '\n\n\n\n\n\n\nitem_location_pkey',item_location_pkey

        if self.diamond_json:
            result_dict = json.loads(self.diamond_json) if self.diamond_json else {}
        else:
            result_dict = json.loads(base64.decodestring(self.diamond_binary)) if self.diamond_binary else {}
        
        for dictionary in result_dict[u'Supply']:
            query = 'select id from asset_transfer_line where id=' + str(dictionary[u'ToSupplyLocationInfID'])
            self.env.cr.execute(query)
            result = self.env.cr.fetchall()
            if result:

                line_id = self.env['asset.transfer.line'].browse(dictionary[u'ToSupplyLocationInfID'])
                if line_id.receiver_employee_id.id == 215:

                    dictionary.update({
                        u'ToCustomerID': dictionary[u'FromCustomerID'] ,
                        # u'ToAccountID':  line_id.receiver_asset_account_id.code,
                        # u'ToDeprAccountID':  line_id.receiver_depreciation_account_id.code,
                        u'ToSupplyLocationInfID': supply_location_pkey,
                        u'ToItemLocationInfID': item_location_pkey,      
                        u'IsDeleted': True,        
                    }) 
                else:
                    
                    dictionary.update({
                        u'ToCustomerID': line_id.receiver_employee_id.sudo().passport_id ,
                        u'ToAccountID':  line_id.receiver_asset_account_id.code,
                        # u'ToDeprAccountID':  line_id.receiver_depreciation_account_id.code,
                        u'ToSupplyLocationInfID': supply_location_pkey,
                        u'ToItemLocationInfID': item_location_pkey,               
                    })    

            elif dictionary[u'ToSupplyLocationInfID'] == 999999999999:
                dictionary.update({
                    u'ToCustomerID': dictionary[u'FromCustomerID'] ,
                    # u'ToAccountID':  line_id.receiver_asset_account_id.code,
                    # u'ToDeprAccountID':  line_id.receiver_depreciation_account_id.code,
                    u'ToSupplyLocationInfID': supply_location_pkey,
                    u'ToItemLocationInfID': item_location_pkey,      
                    u'IsDeleted': True,        
                }) 

            else:
                dictionary.update({
                    u'ToSupplyLocationInfID': supply_location_pkey,
                    u'ToItemLocationInfID': item_location_pkey,                       
                    u'IsDeleted': True ,
                })                 


        result_dict.update({
            u'FromVatAccountId':  self.sudo().sender_vat_account_id.code if self.sudo().sender_vat_account_id else '',
            u'FromRcvAccountId':  self.sudo().sender_account_receivable_id.code if self.sudo().sender_account_receivable_id else '',
            u'ToVatAccountId':  self.sudo().receiver_vat_account_id.code if self.sudo().receiver_vat_account_id else '',
            u'ToPblAccountId':  self.sudo().receiver_account_payable_id.code if self.sudo().receiver_account_payable_id else '',
            u'InvDate':  self.transfer_date,
            u'InvDescription':  self.description,
            u'FromGoodsAccountId':  self.sudo().sender_loss_account_id.code if self.sudo().sender_loss_account_id else '',
            u'FromSaleAccountId':  self.sudo().sender_profit_account_id.code if self.sudo().sender_profit_account_id else '',
            
        
            # splts ---------------------------------------------------------------------------------
            u'ToDivisionId':  self.receiver_department_id.nomin_code,
            # u'ToDivisionId':  '0U2',



        })
        # print '\n\n\n\n\n\n\n\ndddddddddddddddsssssss3 ',json.dumps(result_dict)


        response = client.service.SupplyMod("1",json.dumps(result_dict))


        # print '\n\n\n\n\n\n\n\nresponses',response[:7]
        # print '\n\n\n\n\n\n\n\nresponses7',response

        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)])

        if response[:7] == 'Success':
            # print 'd55555555555555555555555555555555'
            self.write({'state': 'approved',
                'transaction_id':response[7:],
                'approved_employee_id':employee_id.id,
                })
        else:
            raise UserError('Diamond-с ирсэн мэдээлэл - ' + response )

    def create_asset_transfer_request(self, vals):
        transfer_date = vals['transfer_date']
        department_id = vals['department_id']
        type = vals['type']
        receiver_department_id = vals['receiver_department_id']
        receiver_employee_id = vals['receiver_employee_id']
        result_dict = vals['result_dict']
        is_from_unused_assets = vals['is_from_unused_assets'] if vals.has_key('is_from_unused_assets') else False

        asset_transfer_request_id = self.env['asset.transfer.request'].create({
            'transfer_date': transfer_date,
            'department_id': department_id,
            'type': type,
            'receiver_department_id': receiver_department_id,
            'is_from_unused_assets': is_from_unused_assets,
        })

        if department_id != receiver_department_id:
            for dictionary in result_dict[u'Assets']:
                account_id = self.env['account.account'].search([('code','=',dictionary[u'FromAccountID']),('department_id','=',asset_transfer_request_id.department_id.id)])
                # product_id = self.env['product.template'].search([('code','=',dictionary[u'AssetID'])])
                employee_id = self.env['hr.employee'].search([('passport_id','=',dictionary[u'FromCustomerID'].upper())])
                # employee_id = self.env['hr.employee'].search([('passport_id','=','ЧЙ77040671')])
                if employee_id:
                    current_line = asset_transfer_request_id.change_line_ids.sudo().create({
                        'request_id':asset_transfer_request_id.id,
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
                        'receiver_employee_id':receiver_employee_id,
                        'is_from_unused_assets': is_from_unused_assets,
                    })
                    dictionary[u'ToAccountantInfID'] = current_line.id
                else:
                    dictionary[u'ToAccountantInfID'] = 999999999999

            asset_transfer_request_id.sudo().write(
            {
                'diamond_binary':base64.encodestring(json.dumps(result_dict)),                       
            })

        elif department_id and department_id == receiver_department_id:
            asset_transfer_request_id.sudo().write(
            {
                'diamond_binary':base64.encodestring(json.dumps(result_dict)),                       
            })

            asset_registry_numbers = []
            asset_code = ''

            for dictionary in result_dict[u'Assets']:
                asset_registry_numbers.append(dictionary[u'RegistryNumberID'])
                asset_code += dictionary[u'AssetID'] + ','

            prepare_transfer_request_id = self.env['prepare.transfer.request'].create({
                'transfer_date': transfer_date,
                'no_customer_selection': True,
                'employee_id': receiver_employee_id,
                'request_id': asset_transfer_request_id.id,
                'type': 'asset',
                'search_type': 'by_code_multiple',
                'search_string': asset_code,
                'receiver_employee_id': receiver_employee_id,
            })
            prepare_transfer_request_id.button_accept()
            request_result_dict = json.loads(base64.decodestring(asset_transfer_request_id.diamond_binary)) if asset_transfer_request_id.diamond_binary else {}
            new_assets = []
            for dictionary in request_result_dict[u'Assets']:
                if dictionary['RegistryNumberID'] in asset_registry_numbers:
                    new_assets.append(dictionary)
            request_result_dict['Assets'] = new_assets
            for line in asset_transfer_request_id.change_line_ids:
                if line.registry_number not in asset_registry_numbers:
                    line.sudo().unlink()
                else:
                    line.is_from_unused_assets = True
            
            asset_transfer_request_id.sudo().write(
            {
                'diamond_binary':base64.encodestring(json.dumps(request_result_dict)),                
            })
                
        return asset_transfer_request_id



