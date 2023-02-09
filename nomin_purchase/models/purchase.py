# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models,SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.translate import _
from odoo.tools.float_utils import  float_compare
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, AccessError
import time
from odoo.osv import osv
from odoo.http import request    



class PurchaseOrderEvaluationIndicators(models.Model):
    _name = 'purchase.order.evaluation.indicators'

    name= fields.Char(related='indicator_id.name', string=u'Нэр')
    indicator_id = fields.Many2one('evaluation.indicators',string=u"Үзүүлэлт")
    description = fields.Char(string=u"Үзүүлэлт")
    order_id = fields.Many2one('purchase.order', string=u'Захиалга')

    @api.model
    def create(self, vals):

        if vals.get('order_id'):
            order_id = self.env['purchase.order'].browse(vals.get('order_id'))
            if order_id.state!='draft':
                raise UserError( _('Ноорог төлөв дээр үзүүлэлт нэмэх боломжтой.'))

        return super(PurchaseOrderEvaluationIndicators, self).create(vals)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    
    def _add_followers(self,user_ids): 
        '''Дагагч нэмнэ'''
        partner_ids = [user.partner_id.id for user in self.env['res.users'].browse(user_ids) if user.partner_id]
        self.message_subscribe(partner_ids=partner_ids)

    def _set_sector(self):
            department_ids = self.env['hr.department'].get_sector(self.env.user.department_id.id)
            if department_ids :
                return department_ids
            else :      
              return self.env.user.department_id.id
            return None
    
    def set_request(self):
        config_obj = self.env['request.config']
        config_id = config_obj.sudo().search([('department_ids','=',self.department_id.id),('process','=','purchase.comparison')],limit = 1)
        if config_id:
            return config_id
        else:
            return False
    
    
    def _set_department(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id','=',self._uid)])
        if employee_id and employee_id.department_id:
            return employee_id.department_id.id
        return None

    
    def _check_user_in_request(self, state):
        sel_user_ids= []
        user_ids = []
        conf_line = self.env['request.config.purchase.line']
        groups = self.env['res.groups']
        config_obj = self.env['request.config']
        for request in self:
            config_id = request.request_id.id
            line_ids =conf_line.sudo().search([('sequence','=',request.active_sequence),('request_id','=',config_id)])
            if line_ids:
                for req in line_ids:
                    if req.state == state or state == 'back':
                        if req.type == 'group':
                            group = req.group_id
                            # for group in groups.browse(group_id):
                            for user in group.users:
                                sel_user_ids.append( user.id)
                        elif req.type == 'fixed':
                            sel_user_ids.append(req.user_id.id)
                        elif req.type == 'depart':
                            user_id = self.department_id.manager_id.user_id.id
                            if user_id :
                                sel_user_ids.append( user_id)
                            else :
                                raise UserError( _(u"Хэлтэсийн менежер дээр холбоотой хэрэглэгч талбар хоосон байна."))
        user_ids = self.get_possible_users( sel_user_ids)
        return user_ids

    
    def _is_in_sent(self):
        for record in self:
            record.is_in_sent=False
            if record.state=='draft':
                sel_user_ids = self._check_user_in_request('sent')
                if self._uid in sel_user_ids:
                    if self.user_id.id ==self._uid:
                        record.is_in_sent = True
                    else:
                        record.is_in_sent = False
        
    def _is_in_approve(self):
        sel_user_ids = []
        sel_user_ids = self._check_user_in_request('approved')
        for record in self:
            if self._uid in sel_user_ids:
                record.is_in_approve = True
            else:
                record.is_in_approve = False  
    
    
    def _is_in_verify(self):

        sel_user_ids = []
        sel_user_ids = self._check_user_in_request('verified')
        for record in self:
            if self._uid in sel_user_ids:
                record.is_in_verify = True
            else:
                record.is_in_verify = False   

    
    def _is_in_confirm(self):
        sel_user_ids = []
        sel_user_ids = self._check_user_in_request('confirmed')
        for record in self:
            if self._uid in sel_user_ids:
                record.is_in_confirm= True
            else:
                record.is_in_confirm = False  

    
    def _set_request(self):
        config_id = False
        employee_id = self.env['hr.employee'].sudo().search([('user_id','=',self._uid)])
        sector_id = self.env['hr.department'].get_sector(self.env.user.department_id.id)
        sector_obj = self.env['hr.department'].browse(sector_id)
        config_id = self.env['request.config'].search([('department_ids','=',sector_id),('process','=','purchase.order')],limit = 1)   
        if not config_id:
            return False
                # raise UserError( _(u"Таны %s хэлтэс дээр урсгал тохиргоо хийгдээгүй байна." % sector_obj.name))
        return config_id

    @api.model
    def _is_portal_user(self):
        for line in self:
            if not line.env.user.has_group('purchase.group_purchase_user'):
                line.is_portal_user = True
            else:
                line.is_portal_user = False

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }
    request_id = fields.Many2one('request.config',string='Workflow config' ,domain="[('department_ids','=',sector_id),('process','=','purchase.order')]", tracking=True, default=_set_request) #Урсгал тохиргоо    

    payment_request_id = fields.Many2one('payment.request', string='Payment request',index=True,tracking=True) #Төлбөрийн хүсэлт
    indicator_lines = fields.One2many('purchase.order.evaluation.indicators','order_id', string='Rates',tracking=True) #Үзүүлэлтүүд
    active_sequence = fields.Integer(string="Active sequence", default=1)
    user_id = fields.Many2one('res.users', string="User", index=True,default=lambda self: self.env.user.id,tracking=True) #Хэрэглэгч
    sector_id = fields.Many2one('hr.department', 'Performer sector',index=True,domain="[('is_sector','=',True)]", default=_set_sector,tracking=True) #Гүйцэтгэгч салбар 
    department_id = fields.Many2one('hr.department', 'Performer department',index=True,default=_set_department, tracking=True) #Гүйцэтгэгч хэлтэс
    rfq_department_id = fields.Many2one('hr.department', 'Order department', index=True,default=_set_department, tracking=True) #Захиалагч хэлтэс
    confirmed_date  = fields.Date(string='Confirmed date',tracking=True) #Батлагдсан огноо
    rfq_date_term  = fields.Date(string='The Quotation valid date',tracking=True) #Үнийн саналын хүчинтэй хугацаа
    is_rfq_closed = fields.Boolean(string='Is RFQ Closed',tracking=True) #RFQ хаалттай авах эсэх
    is_open_date = fields.Boolean(string='Is RFQ opening day', default=True) #RFQ нээх өдөр мөн эсэх
    rfq_close_date = fields.Datetime(string='RFQ deadline') #Үнийн санал авах сүүлийн хугацаа
    rfq_open_date = fields.Datetime(string='RFQ opening date') #Үнийн санал нээх хугацаа
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, states=READONLY_STATES,\
        default=lambda self: self.env.user.company_id.currency_id.id, tracking=True)
    related_currency_id = fields.Many2one('res.currency', 'Currency', related='currency_id')
#     tender_id = fields.Many2one('tender.tender', string=u"Тендер")

    partner_ref = fields.Char('Vendor Reference', copy=False,\
        help="Reference of the sales order or bid sent by the vendor. "
             "It's used to do the matching when you receive the "
             "products as this reference is usually written on the "
             "delivery order sent by your vendor.")

    date_order = fields.Datetime('Order Date', required=True, states=READONLY_STATES, select=True, copy=False, default=fields.Datetime.now,\
        help="Depicts the date where the Quotation should be validated and converted into a purchase order.",tracking=True)
    state = fields.Selection([
        ('draft', 'Draft PO'), #Ноорог PO
        ('sent', 'Sent'), #Илгээгдсэн
        ('sent_rfq', 'Get quote'), #Үнийн санал авах
        ('back', 'Quote received'), #Үнийн санал ирсэн
        ('to approve', 'Approve'), #Зөвшөөрөх
        ('approved', 'Approved'), #Зөвшөөрсөн
        ('purchase', 'Purchase order'), #Худалдан авах захиалга
        ('verified', 'Checked'), #Хянасан
        ('confirmed','Confirmed'), #Батласан
        ('done', 'Done'), #Дууссан
        ('cancel', 'Canceled') #Цуцлагдсан
        ], string='Status', readonly=True, select=True, copy=False, default='draft', tracking=True)
    

    is_in_sent = fields.Boolean(string='Is in sent', compute= _is_in_sent, default=False)
    is_in_approve = fields.Boolean(string='Is in approve' ,compute= _is_in_approve, default=False)
    is_in_confirm = fields.Boolean(string='Is in confirm', compute= _is_in_confirm, default=False)
    is_in_verify = fields.Boolean(string='Is in verify',compute= _is_in_verify, default=False)

    length_of_warranty = fields.Integer(string='Length of warranty', default = 0,tracking=True) #Баталгаат хугацаатай эсэх (сараар)
    is_carriage = fields.Selection([('yes', u"Yes"),('no', u"No"),], string='Carriage',tracking=True) #Тээврийн зардал багтсан эсэх
    is_VAT = fields.Selection(
        [('has_VAT', u"Тийм"),
        ('hasnt_VAT', u"Үгүй"),
        ('has_ebarimt', u"ebarimt-тай хувь хүн"),
        ('hasnt_ebarimt', u"ebarimt-гүй хувь хүн")
        ], string=u'НӨАТ төлөгч эсэх',tracking=True)
    cost_of_assembling = fields.Integer(string='Cost of assembling', default = 0,tracking=True )#Угсралтын зардалтай эсэх
    time_of_delivery = fields.Integer(string='Time of delivery', default = 0,tracking=True) #Нийлүүлэх хугацаа (хоногоор)

    equipment_amount    = fields.Float('Machine expense',tracking=True) #Машин механизмын зардал
    carriage_amount     = fields.Float('Transportation expense',tracking=True) #Тээврийн зардал
    postage_amount      = fields.Float('Direct expense',tracking=True) #Шууд зардал
    other_amount        = fields.Float('Other expense',tracking=True) #Бусад зардал

    rfq_equipment_amount    = fields.Float('RFQ machine expense',tracking=True) #Үнийн санал машин механизмын зардал
    rfq_carriage_amount     = fields.Float('RFQ transportation expense',tracking=True) #Үнийн санал тээврийн зардал
    rfq_postage_amount      = fields.Float('RFQ direct expense',tracking=True) #Үнийн санал шууд зардал
    rfq_other_amount        = fields.Float('RFQ other expense',tracking=True) #Үнийн санал бусад зардал
    history_emp   = fields.Many2one('hr.employee', string = 'History employee')

    delivery_condition      = fields.Selection([('required', u"Required"),('not_required', u"Not required")], string='Delivery condition', tracking=True) # Хүргэлтийн нөхцөл
    rfq_delivery_condition  = fields.Selection([('free', u"Free"),('paid', u"Paid"),('no_delivery',u'No delivery')], string='RFQ delivery condition', tracking=True) # Үнийн санал хүргэлтийн  нөхцөл
    delivery_cost           = fields.Integer('Delivery cost', tracking=True) # Хүргэлтийн үнэ
    installation_condition   = fields.Selection([('required', u"Required"),('not_required', u"Not required")], string='Installation condition', tracking=True) # Угсралт, суурилуулалтын нөхцөл
    rfq_installation_condition = fields.Selection([('free', u"Free"),('paid', u"Paid")], string='RFQ installation condition', tracking=True) # Үнийн санал угсралт, суурилуулалтын нөхцөл
    installation_cost       = fields.Integer('Installation cost', tracking=True) # Угсралтын үнэ

    delivery_term       = fields.Char('Delivery term /day/', tracking=True) # Нийлүүлэх хугацаа /хоног/
    rfq_delivery_term   = fields.Char('RFQ delivery term /day/', tracking=True)# Үнийн санал нийлүүлэх хугацаа /хоног/
    warranty_period     = fields.Char('Warranty period /day/', tracking=True) # Баталгаат хугацаа /хоног/
    rfq_warranty_period = fields.Char('RFQ warranty period /day/', tracking=True) # Үнийн санал баталгаат хугацаа /хоног/
    return_condition    = fields.Char('Return condition', tracking=True) # Буцаалтын нөхцөл
    rfq_return_condition = fields.Char('RFQ return condition', tracking=True) # Үнийн санал буцаалтын нөхцөл

    loan_term           = fields.Char('Loan term', tracking=True) # Зээлийн хугацаа
    rfq_loan_term       = fields.Char('RFQ loan term', tracking=True) # Үнийн санал зээлийн хугацаа
    barter_percentage   = fields.Char('Barter percentage', tracking=True) # Бартерийн хувь
    rfq_barter_percentage = fields.Char('RFQ barter percentage', tracking=True) # Үнийн санал бартерийн хувь

    vat_condition       = fields.Selection([('required', u"Required"),('not_required', u"Not required")], string='VAT condition', tracking=True) # НӨАТ төлөгч байхыг шаардах эсэх
    vat_amount          = fields.Integer('VAT value') #НӨАТатвар

    is_portal_user = fields.Boolean('Portal User', compute='_is_portal_user', default = False)
    is_created_in_sent = fields.Boolean('Created in sent', default = False)
    
    
    def get_request(self, department_id):
        config_id = False
        config_id = self.env['request.config'].search([('department_ids','=',department_id),('process','=','purchase.order')])
        return config_id

    
    def get_possible_users(self, sel_user_ids):
        department_ids = []
        user_ids = self.env['res.users'].sudo().browse(sel_user_ids)
        possible_user_ids = []
        for this in self:
            for user in user_ids:
                department_ids = self.env['hr.department'].sudo().search([('id','in',user.purchase_allowed_departments.ids)])
                user_dep_set = set(department_ids.ids)
                if list(user_dep_set.intersection([this.department_id.id])):
                    possible_user_ids.append(user.id)
        return possible_user_ids
    
    @api.onchange('department_id')
    def onchange_department(self):
        self.request_id = self.get_request(self.sector_id.id)

    
    def action_send(self):
        self.send_request()

    
    def action_verify(self):
        self.change_state()
    
    def action_approve(self):
        self.change_state()

    
    def action_confirm(self):
        self.change_state()
        history_obj = self.env['request.history'].search([('order_id','=',self.id)])
        count = 0;
        for qqq in history_obj:
            if count == 0:
                employee_id = self.env['hr.employee'].sudo().search([('user_id','=',qqq.user_id.id)])
                self.update({
                                'history_emp': employee_id.id,                  
                                })
            count+=1
        

    
    def action_rfq_back(self):
        for order in self.order_line:
            if not order.price_unit > 0:
                raise UserError(u'Барааны нэгж үнийг оруулна уу')
        self.write({'state':'back','active_sequence':2,'is_open_date':False})
        if self.is_rfq_closed:
            self.order_line.write({'is_rfq_closed':True})

    @api.model
    def create(self, vals):

        

        return super(PurchaseOrder, self).create(vals)
    
    
    def action_cancel(self):
        
        # self.write(cr, uid, ids, {'state':'draft','active_sequence':0},context=context)
#         self.send_notification(cr, uid, ids,'rejected',context=context)
        return {
            'name': 'Note',
            'view_mode': 'form',
            #'view_id': [res and res[1] or False],
            'res_model': 'purchase.order.cancel',
            'context': self._context,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            #'res_id': ids[0]  or False,
        }
    
    def change_state(self):
        purchase_line = self.env['request.config.purchase.line']
        line_ids = purchase_line.search([('sequence','=',self.active_sequence),('request_id','=',self.request_id.id)])
        total_percent = 0
        amount = 0.0
        for line in line_ids:
            if line.limit !=0.0:
                
                if line.limit >= self.amount_total:
                    self.send_request()
                else:
                    self._add_supplier_to_product()
                    self.write({'state':'purchase','active_sequence':99,'confirmed_date':datetime.strptime(time.strftime('%Y-%m-%d'), "%Y-%m-%d")})
                    # self.send_notification('purchase')
                    self.create_history('purchase')
                    self._create_picking()
            else:
                self.sudo()._add_supplier_to_product()
                self.write({'state':'purchase','active_sequence':99,'confirmed_date': datetime.strptime(time.strftime('%Y-%m-%d'), "%Y-%m-%d")})
                # self.send_notification('purchase')
                self.create_history('purchase')
                self._create_picking()

    
    def send_request(self):
        if self._context is None:
            self._context = {}
        employee_obj = self.env['hr.employee']
        history_obj = self.env['request.history']
        config_obj = self.env['request.config']
        for request in self:
            config_id = request.request_id.id
            vals = {}
            if not config_id:
                raise UserError( _("You don't have purchase requisition request configure !"))
            user = request.user_id
            next_user_ids, next_seq, next_state = config_obj.purchase_forward('purchase.order',request.active_sequence, request.user_id.id,config_id,request.department_id.id)
            next_user_ids1, next_seq1, next_state1 = config_obj.purchase_forward('purchase.requistion',request.active_sequence+1, request.user_id.id,config_id,request.department_id.id)
        next_user_ids1 = self.get_possible_users(next_user_ids1)

        if not next_user_ids1:
            raise UserError( _(u"Дараагийн батлах хэрэглэгч олдсонгүй Таны батлах дүн хэтэрсэн эсвэл сарын батлах дүнгээс давсан байна."))           
        if next_user_ids:
                vals.update({'state':next_state,'active_sequence':request.active_sequence+1})
        
        # self.send_notification(next_state)
        self.create_history(next_state)        
        self.write(vals)

    @api.model
    def _purchase_alarm(self):
        today = datetime.strptime(time.strftime('%Y-%m-%d %H:%M:%S'), "%Y-%m-%d %H:%M:%S")
        self.env.cr.execute("select id from purchase_order where is_rfq_closed =True and is_open_date= False and rfq_open_date <'%s'" %today)
        fetched =self.env.cr.fetchone()
        if fetched:
            for fetch in fetched:
                self.env.cr.execute("update purchase_order set is_open_date =True ,state='back' where id =%s" %fetch)
                self.env.cr.execute("update purchase_order_line set is_rfq_closed = False where order_id =%s" %fetch)

    
    def print_quotation(self):
        
        return self.env['report'].get_action(self, 'purchase.report_purchasequotation')

    
    def action_processed(self):
        pass
        return {}
    
    
    def action_back_supply(self):
        for order in self:
            order.write({'state': 'back'})
        return {}

    @api.onchange('partner_id')
    def onchange_partner(self):
        self.partner_ref = self.partner_id.nomin_code
        if not self.partner_id:
            self.fiscal_position_id = False
            self.payment_term_id = False
            self.currency_id = False
        else:
            self.fiscal_position_id = self.env['account.fiscal.position'].with_context(company_id=self.company_id.id).get_fiscal_position(self.partner_id.id)
            self.payment_term_id = self.partner_id.property_supplier_payment_term_id.id
            self.currency_id = self.partner_id.property_purchase_currency_id.id or self.env.user.company_id.currency_id.id
        return {}


    

    @api.model
    def _prepare_picking(self):
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
            })
        return {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            # 'rfq_department_id':self.rfq_department_id.id,
            'department_id':self.department_id.id,
            # 'order_department_id':self.department_id.id,
            'sector_id':self.sector_id.id,
            'order_type':'from_warehouse',
            'date': self.date_order,
            'origin': self.name,
            'location_dest_id': self._get_destination_location(),
            'location_id': self.partner_id.property_stock_supplier.id
        }

    
    
    def _create_picking(self):
        for order in self:
            if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
                res = order._prepare_picking()
                picking = self.env['stock.picking'].create(res)
                moves = order.order_line.filtered(lambda r: r.product_id.type in ['product', 'consu'])._create_stock_moves(picking)
                move_ids = moves.action_confirm()
                moves = self.env['stock.move'].browse(move_ids)
                moves.force_assign()
        # print '\n\n\n\nCREATE INVOICE'
        # invoice_id = self.env['account.invoice'].create({
        #     'partner_id':self.partner_id.id,
        #     'department_id':self.sector_id.id,
        #     'reference':self.name,
        #     'currency_id':self.currency_id.id,
        #     })
        # # print '\n\n\n\n\nINVOICE ID', invoice_id
        # invoice_id.invoice_line_ids.mapped('purchase_line_id')
        # invoice_id.invoice_line_ids.mapped('purchase_id').filtered(lambda r: r.order_line <= purchase_line_ids)

        return True
    
    
    def create_history(self,state):
        history_obj = self.env['request.history']
        history_obj.create(
                {'order_id': self.id,
                'user_id': self._uid,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'type': state,
                })

    
    def unlink(self):
        for order in self:
           
            if order.state != 'draft':
                raise UserError(_(u'Ноорог төлөвтэй захиалга устгаж болно.'))
        return super(PurchaseOrder, self).unlink()
    
    def action_rfq_send_partner(self):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            if self.env.context.get('send_rfq', False):
                template_id = ir_model_data._xmlid_to_res_id('purchase.email_template_edi_purchase')
            else:
                template_id = ir_model_data._xmlid_to_res_id('purchase.email_template_edi_purchase_done')
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data._xmlid_to_res_id('mail.bemail_compose_message_wizard_form')
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
        


    
    def _check_user(self, state):
        sel_user_ids= []
        user_ids = []
        conf_line = self.env['request.config.purchase.line']
        groups = self.env['res.groups']
        config_obj = self.env['request.config']
        for request in self:
            config_id = request.request_id.id
            line_ids =conf_line.search([('sequence','=',request.active_sequence+1),('request_id','=',config_id)])
            if line_ids:
                for req in line_ids:
                    if req.state == state or state == 'back':
                        if req.type == 'group':
                            group = req.group_id
                            # for group in groups.browse(group_id):
                            for user in group.users:
                                sel_user_ids.append( user.id)
                        elif req.type == 'fixed':
                            sel_user_ids.append(req.user_id.id)
                        elif req.type == 'depart':
                            user_id = self.department_id.manager_id.user_id.id
                            if user_id :
                                sel_user_ids.append( user_id)
                            else :
                                raise UserError( _(u"Хэлтэсийн менежер дээр холбоотой хэрэглэгч талбар хоосон байна."))
        user_ids = self.get_possible_users( sel_user_ids)
        return user_ids
    def send_notification(self,state):
#         model_obj = odoo.pooler.get_pool(cr.dbname).get('ir.model.data')
        sel_user_ids = []
        conf_line = self.env['request.config.purchase.line']
        groups = self.env['res.groups']
        config_obj = self.env['request.config']

        sel_user_ids = []
        # for contract in self:
        #     config_id = contract.request_id.id
        #     line_id =conf_line.search([('sequence','=',contract.active_sequence+1),('request_id','=',config_id)])
        if state not in ['purchase','done','draft','sent_rfq','back']:
                sel_user_ids= self._check_user(state)
       
        sel_user_ids.append(self.user_id.id)
                
        states = {
                    'draft':u'Ноорог',
                   'sent':u'Илгээгдсэн',
                   'sent_rfq':u'Үнийн санал илгээгдсэн',
                   'back':u'Үнийн санал хүлээн авсан',
                   'approved':u'Зөвшөөрсөн',
                   'confirmed':u'Баталсан',
                   'verified':u'Хянасан',
                   'rejected':u'Буцаагдсан',
                   'warranty':u'Баталгаат хугацаа',
                   'purchase':u'Худалдан авах захиалга',
                   'certified':u'Баталгаажсан',
                   'canceled':u'Цуцлагдсан',
                   'closed':u'Хаагдсан',
                   'done':u'Дууссан',
            }
            
      
        user_emails = []
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        action_id = self.env['ir.model.data']._xmlid_to_res_id('nomin_purchase.purchase_mail_template')
        db_name = request.session.db
        

              
        sel_user_ids = list(set(sel_user_ids))
        
        for email in  self.env['res.users'].browse(sel_user_ids):
            user_emails.append(email.login)
            subject = u'"Захиалгын дугаар %s".'%(self.name)
            body_html = u'''
                            <h4>Сайн байна уу,\n Таньд энэ өдрийн мэнд хүргье! </h4>
                            <p>
                               ERP системд %s салбарын %s хэлтэсийн %s дугаартай худалдан авалтын захиалгын дугаар %s төлөвт орлоо.
                               
                            </p>
                            <p><b><li> Захиалгын дугаар: %s</li></b></p>
                            <p><b><li> Салбар: %s</li></b></p>
                            <p><b><li> Хэлтэс: %s</li></b></p>
                            <p><b><li> Хүсч буй хугацаа: %s</li></b></p>
                            <p><li> <b><a href=%s/web?db=%s#id=%s&model=purchase.order&action=%s>Захиалгын мэдэгдэл</a></b> цонхоор дамжин харна уу.</li></p>

                            </br>
                            <p>---</p>
                            </br>
                            <p>Энэхүү мэйл нь ERP системээс автоматаар илгээгдэж буй тул хариу илгээх шаардлагагүй.</p>
                            <p>Баярлалаа.</p>
                        '''%( self.sector_id.name,
                            self.department_id.name,
                            self.name,
                            states[state],
                            self.name,
                             self.sector_id.name,
                            self.department_id.name,
                            self.date_order if self.date_order else " ......... ",
                            base_url,
                            db_name,
                            self.id,
                            action_id
                            )
     
            if email.login and email.login.strip():
                email_template = self.env['mail.template'].create({
                    'name': _('Followup '),
                    'email_from': self.env.user.company_id.email or '',
                    'model_id': self.env['ir.model'].search([('model', '=', 'purchase.order')]).id,
                    'subject': subject,
                    'email_to': email.login,
                    'lang': self.env.user.lang,
                    'auto_delete': True,
                    'body_html':body_html,
                  #  'attachment_ids': [(6, 0, [attachment.id])],
                })
                email_template.send_mail(self.id)
        email = u'' + states[state] +u'\n Дараах хэрэглэгчид рүү имэйл илгээгдэв: ' + ('<b>' + ('</b>, <b>'.join(user_emails)) + '</b>')
             
        
        self.message_subscribe_users(sel_user_ids)
        self.message_post(body=email)


         
class request_history(models.Model):
    """Received Document History"""
    _inherit = "request.history"
    
    order_id =  fields.Many2one('purchase.order', 'Purchase order', ondelete="cascade")
class purchase_order_inherit(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line.market_price_total')
    
    def _market_price_total(self):
        total = 0.0
        for order in self:
            for line in order.order_line:
                total =total+ line.market_price_total
            order.market_price_total = total

    
    def _expense_total(self):
        total = 0.0
        for order in self:
            order.partner_expense_total = order.amount_total +order.rfq_other_amount+ order.rfq_postage_amount+ order.rfq_equipment_amount+order.rfq_carriage_amount
            order.expense_total = order.amount_total + order.other_amount+ order.postage_amount+ order.equipment_amount+order.carriage_amount

    @api.depends('order_line.price_total')
    def _get_amount(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
            order.update({
                'untax_amount': amount_untaxed,
                'total_amount': amount_untaxed + order.vat_amount
            })

    @api.depends('vat_amount')
    def _get_tax_amount(self):
        for order in self:
            order.update({
                'tax_amount': order.vat_amount,
                'total_amount': order.amount_untaxed + order.vat_amount
            })

    partner_expense_total = fields.Float(string='Partner total expense', compute = _expense_total) #Харилцагч зардал орсон нийт дүн
    expense_total = fields.Float(string='Expense total', compute = _expense_total) #Зардал орсон нийт дүн
    
    tax_amount = fields.Float(string='Tax amount', compute = _get_tax_amount) # НӨАТатвар
    untax_amount = fields.Float(string='Untax amount', compute = _get_amount) # Татваргүй дүн
    total_amount = fields.Float(string='Total amount', compute = _get_amount) # Үнийн санал /Нийт/

    market_price_total = fields.Float(string='Market total price', compute = _market_price_total) #Зах зээлийн нийт дүн
    history_lines = fields.One2many('request.history','order_id', string='State history',  readonly=True) #Төлөвийн түүх


    
    def copy(self, default=None):
        """ Need to set origin after copy because original copy clears origin
        """
        if default is None:
            default = {}
        
        default.update({'active_sequence':1})
        newpo = super(purchase_order_inherit, self).copy(default=default)

        return newpo
    @api.model
    def _purchase_order_alarm(self):
        today = datetime.strptime(time.strftime('%Y-%m-%d %H:%M:%S'), "%Y-%m-%d %H:%M:%S")
    
class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    
    def send_mail(self, auto_commit=False):
        if self._context.get('default_model') == 'purchase.order' and self._context.get('default_res_id'):
            order = self.env['purchase.order'].browse([self._context['default_res_id']])
            # if order.state == 'draft':
            order.state = 'sent_rfq'
        return super(MailComposeMessage, self.with_context(mail_post_autofollow=True)).send_mail(auto_commit=auto_commit)

class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'



    
    def _market_price_total(self):
        
        for line in self:
            line.market_price_total = line.market_price * line.product_qty
    
    def _is_portal_user(self):
        user_id = self.env['res.users'].browse(self._uid)
        for line in self:
            # if line.order_id.partner_id.id ==user_id.partner_id.id:
            if line.order_id.state =='sent_rfq':
                line.is_portal = True
            else:
                line.is_portal = False

    product_id = fields.Many2one('product.product', string='Product', domain=[('product_tmpl_id.is_new','=',True),('product_tmpl_id.cost_price','>',0)], change_default=True, required=True)        
    warranty = fields.Char(string='Warranty date') #Баталгаат хугацаа 
    market_price = fields.Float(string='Market price') #Зах зээлийн үнэ
    market_price_total = fields.Float(string='Market subtotal', compute = _market_price_total)#Зах зээлийн дэд дүн
    purchase_line_order_ids = fields.One2many('purchase.requisition.line.order.line','order_line_id',string='Purchase order request summary') #Худалдан авалт шаардахын нэгтгэл
    is_rfq_closed = fields.Boolean(string='Is RFQ close') #RFQ хаалттай авах эсэх
    is_portal = fields.Boolean(string='Is portal', compute=_is_portal_user)
    purchase_date_planned = fields.Date(string='Planned date') #Товлогдсон огноо
    state = fields.Selection(related='order_id.state', string="State",store=True)
    sector_id = fields.Many2one('hr.department', related='order_id.sector_id',store=True, string="Sector")
    additional_desc = fields.Char('Additional description') # Нэмэлт тодорхойлолт

    @api.onchange('product_id')
    def onchange_product(self):
        self.market_price = self.product_id.sudo().cost_price
        self.price_unit = self.product_id.sudo().cost_price
        

    
    def unlink(self):
        for order in self:
           
            if order.order_id.state != 'draft':
                raise UserError(_(u'Ноорог төлөвтэй захиалга устгаж болно.'))

    @api.model
    def create(self, vals):

        
        requisition_line_id = vals.get('requisition_line_id')
        if vals.get('date_planned'):
            vals.update({'purchase_date_planned':vals.get('date_planned')[0:10]})
        if requisition_line_id and 'requisition_line_id' in vals:
            vals.update({'requisition_line_id':False})

        return super(purchase_order_line, self).create(vals)

    
    def copy(self, default=None):
        """ Need to set origin after copy because original copy clears origin

        """

        if default is None:
            default = {}

        requisition_line_id = default.get('requisition_line_id')

        if requisition_line_id and 'requisition_line_id' in default:
            default.update({'requisition_line_id':False})
        if 'active_sequence' in default:
            default.update({'active_sequence':1})
        newpo = super(purchase_order_line, self).copy(default=default)

        return newpo


    
    def _create_stock_moves(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            # price_unit = line._get_stock_move_price_unit()

            template = {
                'name': line.name or '',
                # 'requisition_line_id':line.requisition_line_id.id or False,
                'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                'date': line.order_id.date_order,
                'date_expected': line.date_planned,
                'location_id': line.order_id.partner_id.property_stock_supplier.id,
                'location_dest_id': line.order_id._get_destination_location(),
                'picking_id': picking.id,
                'partner_id': line.order_id.dest_address_id.id,
                'move_dest_id': False,
                'state': 'draft',
                'purchase_line_id': line.id,
                'company_id': line.order_id.company_id.id,
                'price_unit': 1,
                'picking_type_id': line.order_id.picking_type_id.id,
                'group_id': line.order_id.group_id.id,
                'procurement_id': False,
                'origin': line.order_id.name,
                'route_ids': line.order_id.picking_type_id.warehouse_id and [(6, 0, [x.id for x in line.order_id.picking_type_id.warehouse_id.route_ids])] or [],
                'warehouse_id':line.order_id.picking_type_id.warehouse_id.id,
            }

            # Fullfill all related procurements with this po line
            diff_quantity = line.product_qty
            for procurement in line.procurement_ids:
                procurement_qty = procurement.product_uom._compute_qty_obj(procurement.product_uom, procurement.product_qty, line.product_uom)
                tmp = template.copy()
                tmp.update({
                    'product_uom_qty': min(procurement_qty, diff_quantity),
                    'move_dest_id': procurement.move_dest_id.id,  #move destination is same as procurement destination
                    'procurement_id': procurement.id,
                    'propagate': procurement.rule_id.propagate,
                })
                done += moves.create(tmp)
                diff_quantity -= min(procurement_qty, diff_quantity)
            if float_compare(diff_quantity, 0.0, precision_rounding=line.product_uom.rounding) > 0:
                template['product_uom_qty'] = diff_quantity
                done += moves.create(template)
        return done
