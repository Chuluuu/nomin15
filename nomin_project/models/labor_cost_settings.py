# -*- coding: utf-8 -*-
from openerp import api, fields, models
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
import time
from datetime import date, datetime, timedelta
from openerp.tools.translate import _


class LaborCostSettings(models.Model):
    _name ="labor.cost.settings"
    _description = 'labor cost settings'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    engineer_salary= fields.Float(string="Инженер техникийн ажилчдын цалингийн хувь", track_visibility='onchange')
    extra_salary = fields.Float(string="Нэмэгдэл цалингийн хувь", track_visibility='onchange')
    social_insurance_rate = fields.Float(string="Нийгмийн даатгалын хувь" , track_visibility='onchange')
    habe_percent = fields.Float(string="ХАБЭ хувь", track_visibility='onchange')

    @api.model
    def create(self,vals):
        result = super(LaborCostSettings, self).create(vals)
        settings_obj = self.env['labor.cost.settings'].search([(1,'=',1)]).ids
        count = 0
        for item in settings_obj:
            count+=1
            if count > 1:
                raise ValidationError(_(u'Өмнө нь үүсгэсэн байна. 1 удаа үүсгэх боломжтой.'))
        return result




    