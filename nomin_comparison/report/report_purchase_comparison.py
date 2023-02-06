# -*- coding: utf-8 -*-
##############################################################################
#
#    odoo, Open Source Management Solution
#    Copyright (C) 2014-Today odoo SA (<http://www.odoo.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import time
import datetime
import odoo
#from odoo.osv import osv
from odoo import api, fields, models, _, modules
from odoo.tools.translate import _
from operator import itemgetter
import logging
_logger = logging.getLogger(__name__)


    
class ReportTenderRequest(models.AbstractModel):
    _name = 'report.nomin_comparison.report_purchase_comparison'

    
    def render_html(self, data):

        comparison_id = self.env['purchase.comparison'].browse(self.id)
        order_ids = self.env['purchase.order'].sudo().search([('comparison_id','=',comparison_id.id)])
        # products= {}
        suppliers = []
        product_prices = {}
        product_qtys = {}
        partner_indicators = {}
        partners = []
        page_counts= []
        # for order in order_ids:
        #     for line in order.order_line:
        #         if line.product_id.name not in products:
        #             products[line.product_id.name]= {
        #             'partners':{},
        #             'product':u'Тодорхойгүй',
        #             }
        #         products[line.product_id.name]['product'] = line.product_id.name
        #         if order.partner_id.name not in products[line.product_id.name]['partners']:
        #             products[line.product_id.name]['partners'][order.partner_id.name]={
        #             'product':u'Тодорхойгүй',
        #             'partner':u'Тодорхойгүй',
        #             'product_qty':0.0,
        #             'price_unit':0.0,
        #             }
                
        #         products[line.product_id.name]['partners'][order.partner_id.name]['partner']=order.partner_id.name
        #         products[line.product_id.name]['partners'][order.partner_id.name]['product_qty']=line.product_qty
        #         products[line.product_id.name]['partners'][order.partner_id.name]['price_unit']=line.price_unit
        products = []
        count =0
        for order in order_ids:
            for line in order.order_line:
                if line.product_id.name not in products:
                    products.append(line.product_id.name)
        orders= []
        m_count =0
        len_orders = len(order_ids)
        indicators = []
        indics =[]
        
        partners = {}
        averages = {}
        for part in comparison_id.partner_ids:
            partner_indicators[part.partner_id.id] = {}
            averages[part.partner_id.id] = part.total_percent
            for indic in part.indicator_ids:
                if indic.indicator_id.name not in indicators:
                    indicators.append(indic.indicator_id.name)
                partner_indicators[part.partner_id.id][indic.indicator_id.name]=indic.total_percent


                
        cat ={}
        for order in order_ids:
            
                
            orders.append(order)

            product_prices [order.partner_id.id] = {}
            product_qtys [order.partner_id.id] = {}
            
            
            suppliers.append(order.partner_id.id)
            for line in order.order_line:
                if line.product_id.name not in products:
                    products.append(line.product_id.name)

                product_prices[order.partner_id.id][line.product_id.name] = line.price_unit if line.price_unit else 0
                product_qtys[order.partner_id.id][line.product_id.name] = line.product_qty if line.product_qty else 0 
            

            
            if order.partner_id.id in partner_indicators:            
                cat[order.partner_id.id] = partner_indicators[order.partner_id.id]
                # for part in partner_indicators[order.partner_id.id]:
           
            
            if count==2 or len_orders-1==m_count:
                page_counts.append(({'product_prices':product_prices,
                    'product_qtys':product_qtys,
                    'products':products,
                    'suppliers':suppliers,
                    'orders':orders,
                    'indicators':indicators,
                    'partner_indicators':cat,
                    'averages':averages,
                    }))
                
                product_prices = {}
                product_qtys = {}                
                suppliers =[]
                count=0
                orders=[]
            else:
                count+=1
            m_count+=1
        employees = []        
        for emp in comparison_id.rate_employee_ids:
            if emp.state=='done':
                employees.append(emp)   
      


      
        docargs = {
            'docs': comparison_id,  
            'order_ids': order_ids,
            'product_prices':product_prices,
            'product_qtys':product_qtys,
            'products':products,
            'suppliers':suppliers,
            'page_counts':page_counts,
            'employees':employees
        }
        return self.env['report'].render('nomin_comparison.report_purchase_comparison', docargs)