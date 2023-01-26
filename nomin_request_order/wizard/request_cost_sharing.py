# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, modules
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging , time
from odoo.exceptions import UserError
from operator import itemgetter
class RequestCostSharing(models.TransientModel):
    _name = 'request.cost.sharing'
    _description = 'request account cost sharing'

    @api.model
    def default_get(self, fields):
        res = super(RequestCostSharing, self).default_get(fields)	
        order_ids = self.env['request.order'].browse(self._context.get('active_ids', []))
        sector_id = False
        sector_ids = []
        sectors = {}
        lines = []
        if order_ids:
            
            for order in order_ids:
                if order.cost_share_id:
                    raise UserError(_(u'Алдаа: %s захиалгын хүсэлтээс зардал хувиарлалт үүссэн байна.'%order.name))
                config_id = self.env['request.order.config'].search([('sequence','=',order.active_sequence+1),('department_ids','=',order.perform_department_id.id),('is_fold','=',False)])
                if config_id:
                    raise UserError(_(u'Алдаа: Дуусаагүй төлөв дээрээс зардал хувиарлах боломжгүй'))
                sector_id = self.env['hr.department'].get_sector(order.perform_department_id.id)
                if sector_id not in sector_ids:
                    sector_ids.append(sector_id)
                if len(sector_ids)>1:
                    raise UserError(_(u'Алдаа: 2 өөр гүйцэтгэгч салбарын зардал хувиарлах боломжгүй'))
                if sector_id not in sectors:
                    sectors [sector_id] = {
                        'sector_id':'' ,
                        'departments':{    
                            
                        }
                    }
                if order.cost_sector_id.id not in sectors[sector_id]['departments']:
                    sectors[sector_id]['departments'][order.cost_sector_id.id]= {
                            'department_id':'',
                            'is_vat_partner':'',
                            'is_same_sector':'',
                            'amount_total':0,
                            'amount_tax':0,
                            'amount_untaxed':0,

                    }
                unit_price = order.total_amount
                is_same_sector = False
                is_vat_partner = False
                
                if order.cost_sector_id.company_id.id== order.perform_department_id.company_id.id:
                    is_same_sector = True
                    unit_price = unit_price/1.1

                sectors[sector_id]['departments'][order.cost_sector_id.id]['amount_total'] += unit_price

                if order.cost_sector_id.partner_id and order.cost_sector_id.partner_id.is_vat:
                    is_vat_partner=True

                sectors[sector_id]['departments'][order.cost_sector_id.id]['is_vat_partner'] = is_vat_partner
                sectors[sector_id]['departments'][order.cost_sector_id.id]['is_same_sector'] = is_same_sector
                sectors[sector_id]['departments'][order.cost_sector_id.id]['department_id'] = order.cost_sector_id.id
            if sectors:                
                for sector in sorted(sectors.values(), key=itemgetter('sector_id')):
                    for dep in sorted(sector['departments'].values(), key=itemgetter('department_id')):
                        lines.append((0,0,{'is_true':True,'department_id':dep['department_id'],'amount_total':dep['amount_total'],'is_same_sector':dep['is_same_sector'],'is_vat_partner':dep['is_vat_partner']}))
            if lines:
                res.update({'line_ids':lines})
            res.update({'sector_id':sector_id})
        return res
    @api.model
    def _default_currency(self):
        
        return 112

    date = fields.Datetime(string='Гүйлгээний огноо', default=fields.Date.context_today)
    paid_due_date = fields.Datetime(string='Төлбөр төлөх огноо', default=fields.Date.context_today)
    sector_id = fields.Many2one('hr.department', string="Салбар")
    is_tax = fields.Boolean(string="НӨАТ-тэй эсэх?", default=True)
    desc = fields.Char(string="Гүйлгээний утга")
    currency_id = fields.Many2one('res.currency', string="Гүйлгээний валют", default=_default_currency)
    line_ids = fields.One2many('request.cost.sharing.line','request_cost_id', string="Lines")

    # TODO FIX LATER
    # journal_id = fields.Many2one('account.journal', string="Журнал", domain="[('department_id','=',sector_id),('type','not in',['bank','cash'])]")
    # credit_account_id = fields.Many2one('account.account', string="Авлага данс",domain="[('department_id','=',sector_id),('internal_type','=','receivable'),('type','=','account')]")
    # debit_account_id = fields.Many2one('account.account', string="Орлого данс",domain="[('department_id','=',sector_id),('type','=','account')]")
    # vat_account_id = fields.Many2one('account.account', string="НӨАТ-ын данс",domain="[('department_id','=',sector_id),('type','=','account'),('internal_type','=','payable')]")
    # tax_id = fields.Many2one('account.tax', string="Татвар",domain="[('department_id','=',sector_id),('type_tax_use','=','sale')]")
    credit_account_id = fields.Many2one('account.account', string="Авлага данс")
    debit_account_id = fields.Many2one('account.account', string="Орлого данс")
    vat_account_id = fields.Many2one('account.account', string="НӨАТ-ын данс")
    journal_id = fields.Many2one('account.journal', string="Журнал")
    tax_id = fields.Many2one('account.tax', string="Татвар")


    
    def action_create(self):

        cost_obj=self.env['account.cost.sharing']
        cost_line_obj=self.env['account.cost.sharing.line']
        cost_sharing_id=cost_obj.create({
		'company_id':self.sector_id.company_id.id,
		'from_partner_id':self.sector_id.id,
		'from_partner_id1':self.sector_id.partner_id.id,
		'description':self.desc,
		'is_vat':True,
		'type':'income',
		'date':time.strftime('%Y%m%d'),
		'send_date':time.strftime('%Y%m%d'),
		'paid_due_date':time.strftime('%Y%m%d'),
		'partner_id':self.sector_id.partner_id.id,
		'currency_id':self.currency_id.id,
		'transaction_currency_id':self.currency_id.id,
		'receivable_account_id':self.credit_account_id.id,
		'tax_id':self.tax_id.id,
		'vat_account_id':self.vat_account_id.id,
		'journal_id':self.journal_id.id,
		})
        for line in self.line_ids:
            cost_line_obj.create({
				'parent_id':cost_sharing_id.id,
				'name':line.desc,
				'type':'income',
				'is_vat_from_partner':line.is_vat_partner,
				'from_partner_id':self.sector_id.id,
				'from_partner_id1':self.sector_id.partner_id.id,
				'to_partner_id':line.department_id.id,
				'partner_id':self.sector_id.partner_id.id,
				'is_vat_partner':line.is_vat_partner,
				'sale_income_account_id':self.debit_account_id.id,
				'qty':1,
				'price_unit':line.amount_total,
				'send_date':time.strftime('%Y%m%d'),
				'paid_due_date':time.strftime('%Y%m%d'),
				'date':time.strftime('%Y%m%d'),
				'tax_id':self.tax_id.id,
				'currency_id':self.currency_id.id,
				'transaction_currency_id':self.currency_id.id,
				'send_user_id':self._uid,
				'is_same_sector':line.is_same_sector,
				})
        order_ids = self.env['request.order'].browse(self._context.get('active_ids', []))
        for order in order_ids:
            order_ids.write({'cost_share_id':cost_sharing_id.id})
        return {
            'name': _('Budget filter'),
            'view_mode': 'form',
            'res_model': 'account.cost.sharing',		
            'res_id':cost_sharing_id.id,
            'target':'current',
            'type': 'ir.actions.act_window'
            }
class RequestCostSharingLine(models.TransientModel):
    _name = 'request.cost.sharing.line'

    request_cost_id = fields.Many2one('request.cost.sharing',string="Request")
    desc = fields.Char(string="Гүйлгээний утга")
    department_id = fields.Many2one('hr.department', string="Салбар")
    amount_untaxed = fields.Float(string="Татваргүй дүн")
    amount_tax = fields.Float(string="Татвар")
    amount_total = fields.Float(string="Дүн")
    is_true = fields.Boolean(string="НӨАТ-тэй эсэх?", default=True)
    is_same_sector = fields.Boolean(string="НӨАТ-тэй эсэх?", default=False)
    is_vat_partner = fields.Boolean(string="НӨАТ-тэй эсэх?", default=False)
