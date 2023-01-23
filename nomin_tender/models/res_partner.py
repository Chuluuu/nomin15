# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.translate import _
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError, AccessError
import logging
_logger = logging.getLogger(__name__)

class res_partner(models.Model):
    _inherit='res.partner'
    
     
    
    def _tender_count(self):
        '''Харилцагчийн тендерт оролцсон тоо'''
        for partner in self:
            count=self.env['tender.participants.bid'].sudo().search_count([('partner_id','=',partner.id)])
        self.tender_management_counts=count
         
    
    def _tender_history(self):
        '''Харилцагчийн тендерт оролцсон үр дүнгийн тоо'''
        for partner in self:
            p_count = self.env['tender.partner.history'].sudo().search_count([('partner_id', '=', partner.id)])
        self.tender_history_counts = p_count
    
    
    #===========================================================================
    # 
    # def _tender_count(self):
    #     '''Харилцагчийн тендерт оролцсон тоо'''
    #     
    #     if self.ids:
    #         self._cr.execute("select count(id) from tender_participants_bid "
    #                         "WHERE partner_id = ANY(%s)", (self.ids,))
    #         data_dict = dict(self._cr.fetchall())
    #         for obj in self:
    #             obj.tender_management_counts = data_dict.get(obj.id,0)        
    #     
    #     
    #                 
    # 
    # def _tender_history(self):
    #     '''Харилцагчийн тендерт оролцсон үр дүнгийн тоо'''
    #     if self.ids:
    #         self._cr.execute("select count(id) "
    #                         "from tender_partner_history "
    #                         "WHERE partner_id = ANY(%s)", (self.ids,))
    #         data_dict = dict(self._cr.fetchall())
    #         for obj in self:
    #             obj.tender_history_counts = data_dict.get(obj.id,0)
    #===========================================================================
                
    tender_management_counts = fields.Integer(compute='_tender_count', string="Tender count")
    tender_history_counts = fields.Integer(compute='_tender_history', string="Tender history")
    area_ids    = fields.Many2many(comodel_name='area.activity',string="Үйл ажиллагааны чиглэл")