# -*- coding: utf-8 -*-

from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError
from odoo import api, fields, models, SUPERUSER_ID, _

class purchase_tender_config(models.Model):
    _name = 'purchase.tender.config'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name        = fields.Char(u'Үнийн дүн')
    amount      = fields.Float('Amount', digits=(16, 2), tracking=True)
    type = fields.Selection([('purchase','Шаардах'),('control_budget','Хяналтын төсөв')],string="Төрөл")
    is_active   = fields.Boolean('Is Active', default=True, tracking=True)
    
purchase_tender_config()

class purchase_requisition_line(models.Model):
    _inherit = 'purchase.requisition.line'
    '''Шаардахын мөр'''
    
    def write(self,vals):
        for line in self:
          if line.requisition_id.state=='tender_created':
              vals.update({'state':'tender_created'})
                  # vals.update({''})
                  # for line in self.line_ids:  
                  #     line.write( {'state':'tender_created'})
        return super(purchase_requisition_line, self).write(vals)    

class purchase_requisition(models.Model):
    _inherit = 'purchase.requisition'
    '''Худалдан авалтын шаардахын мөр'''
    # def create(self, cr, uid, vals, context=None):
        
    #     result = super(purchase_requisition, self).create(cr, uid,  vals, context=context)
    #     if 'state' in vals:
    #       if vals ['state'] == 'confirmed':
    #         pri
    #         is_tender_created = self.check_tender_amount(cr, 1, result, context=context)
    #         if is_tender_created:
    #           vals.update({'state':'tender_created'})
    #     return result
    
    
    def write(self,vals):
        '''Батлагдсан шаардахын үнийн дүн тендер зарлах 
           үнийн дүнгээс хэтэрсэн бол тендер үүснэ
        '''
        if 'state' in vals:
          if vals ['state'] == 'confirmed':
            if not self.tender_id :
                if not self.is_purchase:
                    is_tender_created , tender_id = self.check_tender_amount()
                    if is_tender_created:
                      vals.update({'state':'tender_created','tender_id':tender_id.id,'active_sequence':99})
                  # vals.update({''})
                  # for line in self.line_ids:  
                  #     line.write( {'state':'tender_created'})
        return super(purchase_requisition, self).write(vals)


    
    def check_tender_amount(self):
        '''Шаардахын үнийн тендер зарлах 
           үнийн дүнгээс хэтэрсэн эсэхийг шалгана
        '''
        sum = 0.0
        is_true = False
        config = self.env['purchase.tender.config']
        tender_obj = self.env['tender.tender']
        tender_line_obj = self.env['tender.line']
        # if self.control_budget_id:
        #   config_id = config.search([('type','=','control_budget'),('is_active','=',True)])
        # else:
        config_id = config.search([('type','=','purchase'),('is_active','=',True)])
        values = {}
        tender_id = False
        for req in self:
            for line in req.line_ids:
                 sum+=  line.product_qty * line.product_price

            if config_id:    
                for conf in config_id[0]:
                    if conf.amount:
                        if sum >= conf.amount:
                            is_true = True
                            values = {
                                      'department_id':req.department_id.id,
                                      'sector_id':req.sector_id.id,
                                      'user_id':req.user_id.id,
                                      'ordering_date':req.ordering_date,
                                      'requisition_id':req.id,
                                      'project_id':req.project_id.id if req.project_id else False,
                                      # 'work_task_id':req.task_id.id if req.task_id else False,
                                      'control_budget_id': req.control_budget_id.id if req.control_budget_id else False,
                                      # 'work_graph_id': req.task_id.id if req.task_id else False,
                                      }
                            tender_id = tender_obj.sudo().create(values)
                            for line in req.line_ids:
                                tender_line_obj.sudo().create( {
                                                                 'product_id': line.product_id.id,
                                                                 'product_qty': line.product_qty,
                                                                 'product_uom_id':line.product_id.uom_id.id,
                                                                 'schedule_date': req.schedule_date,
                                                                 'tender_id': tender_id.id,
                                                                 })
                    else:
                        raise UserError(_('Warning!'),_(u'Тендер авах хязгаар дүн оруулж өгнө үү. Админтай холбогдоно уу.'))
            else :
                raise UserError(_('Warning!'),_(u'Тендер үнийн дүн оруулж өгнө үү.'))
        return is_true,tender_id
purchase_requisition()

class tender_tender(models.Model):
    _inherit = 'tender.tender'
    '''Тендер'''
    requisition_id = fields.Many2one('purchase.requisition','Purchase requisition', ondelete="restrict")
    
tender_tender()
    
class purchase_order(models.Model):
    _inherit = 'purchase.order'
    '''Худалдан авалтын захиалга'''
    tender_id = fields.Many2one('tender.tender', 'Current Tender')
    
    