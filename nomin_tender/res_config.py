# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID
from odoo.osv import osv, orm, fields
from openerp.addons.web.http import request
from openerp.tools.translate import _

from datetime import datetime, timedelta
import odoo
from urlparse import urljoin
import werkzeug
from openerp.addons.decimal_precision import decimal_precision as dp

from openerp.addons.base.ir.ir_mail_server import MailDeliveryException
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, ustr
from ast import literal_eval
 
class WebsiteConfigSettings(models.Model):
    _inherit = 'website.config.settings'
    '''Тендер зарлах үнийн дүн 
    '''
    _columns = {
         'purchase_tender_limit': fields.related('website_id', 'purchase_tender_limit', type="char", string='Tender minimum amount'),
     }

class website(orm.Model):
    _inherit = 'website'

    _columns = {
         'purchase_tender_limit': fields.float('Tender minimum amount'),
     }