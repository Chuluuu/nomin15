# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
import time
from datetime import date, datetime, timedelta
from odoo.tools.translate import _


class LaborCostSettings(models.Model):
    _name ="labor.cost.settings"
    _description = 'labor cost settings'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    engineer_salary= fields.Float(string="Инженер техникийн ажилчдын цалингийн хувь", tracking=True)
    extra_salary = fields.Float(string="Нэмэгдэл цалингийн хувь", tracking=True)
    social_insurance_rate = fields.Float(string="Нийгмийн даатгалын хувь" , tracking=True)
    habe_percent = fields.Float(string="ХАБЭ хувь", tracking=True)

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




    