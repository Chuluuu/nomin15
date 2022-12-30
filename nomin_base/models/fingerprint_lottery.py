# -*- encoding: utf-8 -*-
from openerp import api, fields, models, _
from openerp.exceptions import UserError

class FingerprintLottery(models.Model):
    _name ='fingerprint.lottery'
    _order="create_date desc"
    finger_code = fields.Char(string="Хурууны код")
    employee_id = fields.Many2one('hr.employee',string="Ажилтан")
    lastname = fields.Char(string="Хурууны код", )
    department_id = fields.Many2one('hr.department',string="Хэлтэс")
    sector_id = fields.Many2one('hr.department',string="Салбар")
    job_id = fields.Many2one('hr.job', string="Албан тушаал")
    phone = fields.Text(string="Ажилтаны утас")
    lottery_number = fields.Text(string="Сугалааны дугаар")
    purpose = fields.Text(string="Ирсэн Зорилго")
    issue = fields.Text(string="Асуудлын дэлгэрэнгүй")
    desc = fields.Text(string="Шийдвэрлэсэн тодорхойлолт")
    
    