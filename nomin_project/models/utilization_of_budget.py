# -*- coding: utf-8 -*-

import datetime
import time
from datetime import date, datetime, timedelta
from odoo import api, fields, models, _

class utilization_on_budget(models.Model):
    _name = 'utilization.on.budget'
    '''
       Хяналтын төсвийн бодит гүйцэтгэл
    '''
    @api.multi
    def name_get(self):
        result = []
        for budget in self:
            name = u'%s-%s-[%s]'%(budget.control_budget_id.name,
                                    budget.budget_type, 
                                    budget.balance
                                    )
            result.append((budget.id, name))
        return result
    
    @api.one
    @api.depends('price', 'utilization')
    def _balance_subtotal(self):
        self.balance = self.price-self.utilization
    
    @api.one
    def _prac_amt(self):
        '''
           Хяналтын төсвийн бодит гүйцэтгэл бодох
        '''
        res = 0.0
        result = 0.0
        for line in self.browse(self.id):
            self.env.cr.execute("SELECT SUM(amount) FROM account_analytic_line WHERE controll_budget_id=%s"%(line.id))
            result = self.env.cr.fetchone()[0]
            if result:
                if int(result) < 0:
                    result = int(result)*(-1)
            if result is None:
                result = 0.00
            res = result
        return res


    @api.one
    def _practical_subtotal(self):
        res = 0.0
        if self.id:
            res = self._prac_amt()[0]
            if res is None:
                res=0.0
        self.utilization = res
        
    control_budget_id = fields.Many2one('control.budget', index=True,string = 'Budget')
    budget_type     = fields.Selection([
                                        ('material',u'Материалын зардал'),
                                        ('labor', u'Ажиллах хүчний зардал'),
                                        ('equipment',u'Машин механизмын зардал'),
                                        ('carriage',u'Тээврийн зардал'),
                                        ('postage',u'Шууд зардал'),
                                        ('other',u'Бусад зардал')
                                        ],string = u'Зардлын төрөл')
    department_id   = fields.Many2one('hr.department', index=True,string=u'Хэлтэс')
    value           = fields.Char(string = u'Утга')
    price           = fields.Float(string = u'Дүн') #ТӨЛӨВЛӨСӨН ДҮН
    balance         = fields.Float(compute='_balance_subtotal', string=u'Үлдэгдэл', digits=(16, 2), readonly=True) #Үлдэгдэл
    utilization     = fields.Float(compute='_practical_subtotal', string=u'Гүйцэтгэл', digits=(16, 2), readonly=True) #Гүйцэтгэл
#    utilization     = fields.Float(string = u'Гүйцэтгэл') # БОТИД ГҮЙЦЭТГЭЛ ФУНКЦ ТАЛБАР БОЛГОНО
    state           = fields.Selection([
                                    ('confirm',u'Батлагдсан'),
                                    ('close', u'Хаагдсан'),
                                    ],string = u'Төлөв',default ='confirm')
    
    
class utilization_budget_material(models.Model):
    _name = 'utilization.budget.material'
    
    '''
       Хяналтын төсвийн материалын зардлын гүйцэтгэл
    '''
    budget_id   = fields.Many2one('control.budget', index=True, string='Budget')
    purchase    = fields.Many2one('purchase.requisition', string=u'Худалдан авалтын шаардах')
    budget_comparison = fields.Many2one('budget.partner.comparison', string='Үнийн харьцуулалт')
    tender      = fields.Many2one('tender.tender', index=True, string=u'Тендер')
    date        = fields.Date(string = u'Огноо')
    map         = fields.Selection([
                                    ('budget', u'Хяналтын төсвөөс'),
                                    ('purchase', u'Худалдан авалтын шаардахаас'),
                                    ('tender',u'Тендерээс'),
                                    ('order',u'Худалдан авалтын захиалгаас')
                                    ],string = u'Үүсвэр')
    state       = fields.Selection([
                                    ('purchase',u'Худалдан авалтын шаардах үүссэн'),
                                    ('tender', u'Тендер үүссэн'),
                                    ('comparison', u'Үнийн харьцуулалт үүссэн'),
                                    ('order',u'Худалдан авалтын захиалга үүссэн'),
                                    ('ordered',u'Худалдан авалтын захиалга хийгдсэн'),
                                    ],string = u'Төлөв')
    price       = fields.Float(u'Үнэ')

class utilization_budget_labor(models.Model):
    _name = 'utilization.budget.labor'
    '''
       Хяналтын төсвийн Ажиллах хүчний зардлын гүйцэтгэл
    '''
    budget_id   = fields.Many2one('control.budget', index=True, string='Budget')
    purchase    = fields.Many2one('purchase.requisition', string=u'Худалдан авалтын шаардах')
    budget_comparison = fields.Many2one('budget.partner.comparison', string='Үнийн харьцуулалт')
    tender      = fields.Many2one('tender.tender', index=True, string=u'Тендер')
    date        = fields.Date(string = u'Огноо')
    map         = fields.Selection([
                                    ('budget', u'Хяналтын төсвөөс'),
                                    ('purchase', u'Худалдан авалтын шаардахаас'),
                                    ('tender',u'Тендерээс'),
                                    ('order',u'Худалдан авалтын захиалгаас')
                                    ],string = u'Үүсвэр')
    state       = fields.Selection([
                                    ('purchase',u'Худалдан авалтын шаардах үүссэн'),
                                    ('tender', u'Тендер үүссэн'),
                                    ('comparison', u'Үнийн харьцуулалт үүссэн'),
                                    ('order',u'Худалдан авалтын захиалга үүссэн'),
                                    ('ordered',u'Худалдан авалтын захиалга хийгдсэн'),
                                    ],string = u'Төлөв')
    price       = fields.Float(u'Үнэ')

class utilization_budget_equipment(models.Model):
    _name = 'utilization.budget.equipment'
    '''
       Хяналтын төсвийн Машин механизмын зардлын гүйцэтгэл
    '''
    budget_id   = fields.Many2one('control.budget', index=True, string='Budget')
    purchase    = fields.Many2one('purchase.requisition', string=u'Худалдан авалтын шаардах')
    tender      = fields.Many2one('tender.tender', index=True, string=u'Тендер')
    budget_comparison = fields.Many2one('budget.partner.comparison', string='Үнийн харьцуулалт')
    date        = fields.Date(string = u'Огноо')
    map         = fields.Selection([
                                    ('budget', u'Хяналтын төсвөөс'),
                                    ('purchase', u'Худалдан авалтын шаардахаас'),
                                    ('tender',u'Тендерээс'),
                                    ('order',u'Худалдан авалтын захиалгаас')
                                    ],string = u'Үүсвэр')
    state       = fields.Selection([
                                    ('purchase',u'Худалдан авалтын шаардах үүссэн'),
                                    ('tender', u'Тендер үүссэн'),
                                    ('comparison', u'Үнийн харьцуулалт үүссэн'),
                                    ('order',u'Худалдан авалтын захиалга үүссэн'),
                                    ('ordered',u'Худалдан авалтын захиалга хийгдсэн'),
                                    ],string = u'Төлөв')
    price       = fields.Float(u'Үнэ')
    
class utilization_budget_carriage(models.Model):
    _name = 'utilization.budget.carriage'
    '''
       Хяналтын төсвийн тээврийн зардлын гүйцэтгэл
    '''
    budget_id   = fields.Many2one('control.budget', index=True, string='Budget')
    purchase    = fields.Many2one('purchase.requisition', string=u'Худалдан авалтын шаардах')
    tender      = fields.Many2one('tender.tender', index=True, string=u'Тендер')
    budget_comparison = fields.Many2one('budget.partner.comparison', string='Үнийн харьцуулалт')
    date        = fields.Date(string = u'Огноо')
    map         = fields.Selection([
                                    ('budget', u'Хяналтын төсвөөс'),
                                    ('purchase', u'Худалдан авалтын шаардахаас'),
                                    ('tender',u'Тендерээс'),
                                    ('order',u'Худалдан авалтын захиалгаас')
                                    ],string = u'Үүсвэр')
    state       = fields.Selection([
                                    ('purchase',u'Худалдан авалтын шаардах үүссэн'),
                                    ('tender', u'Тендер үүссэн'),
                                    ('comparison', u'Үнийн харьцуулалт үүссэн'),
                                    ('order',u'Худалдан авалтын захиалга үүссэн'),
                                    ('ordered',u'Худалдан авалтын захиалга хийгдсэн'),
                                    ],string = u'Төлөв')
    price       = fields.Float(u'Үнэ')
    
class utilization_budget_other(models.Model):
    _name = 'utilization.budget.other'
    '''
       Хяналтын төсвийн бусад зардлын гүйцэтгэл
    '''
    budget_id   = fields.Many2one('control.budget', index=True, string='Budget')
    purchase    = fields.Many2one('purchase.requisition', string=u'Худалдан авалтын шаардах')
    tender      = fields.Many2one('tender.tender', index=True, string=u'Тендер')
    budget_comparison = fields.Many2one('budget.partner.comparison', string='Үнийн харьцуулалт')
    date        = fields.Date(string = u'Огноо')
    map         = fields.Selection([
                                    ('budget', u'Хяналтын төсвөөс'),
                                    ('purchase', u'Худалдан авалтын шаардахаас'),
                                    ('tender',u'Тендерээс'),
                                    ('order',u'Худалдан авалтын захиалгаас')
                                    ],string = u'Үүсвэр')
    state       = fields.Selection([
                                    ('purchase',u'Худалдан авалтын шаардах үүссэн'),
                                    ('tender', u'Тендер үүссэн'),
                                    ('comparison', u'Үнийн харьцуулалт үүссэн'),
                                    ('order',u'Худалдан авалтын захиалга үүссэн'),
                                    ('ordered',u'Худалдан авалтын захиалга хийгдсэн'),
                                    ],string = u'Төлөв')
    price       = fields.Float(u'Үнэ')
    
class utilization_budget_postage(models.Model):
    _name = 'utilization.budget.postage'
    '''
       Хяналтын төсвийн Шууд зардлын гүйцэтгэл
    '''
    budget_id   = fields.Many2one('control.budget', index=True, string='Budget')
    purchase    = fields.Many2one('purchase.requisition', string=u'Худалдан авалтын шаардах')
    tender      = fields.Many2one('tender.tender', index=True, string=u'Тендер')
    budget_comparison = fields.Many2one('budget.partner.comparison', string='Үнийн харьцуулалт')
    date        = fields.Date(string = u'Огноо')
    map         = fields.Selection([
                                    ('budget', u'Хяналтын төсвөөс'),
                                    ('purchase', u'Худалдан авалтын шаардахаас'),
                                    ('tender',u'Тендерээс'),
                                    ('order',u'Худалдан авалтын захиалгаас')
                                    ],string = u'Үүсвэр')
    state       = fields.Selection([
                                    ('purchase',u'Худалдан авалтын шаардах үүссэн'),
                                    ('tender', u'Тендер үүссэн'),
                                    ('comparison', u'Үнийн харьцуулалт үүссэн'),
                                    ('order',u'Худалдан авалтын захиалга үүссэн'),
                                    ('ordered',u'Худалдан авалтын захиалга хийгдсэн'),
                                    ],string = u'Төлөв')
    price       = fields.Float(u'Үнэ')