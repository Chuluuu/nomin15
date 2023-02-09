from odoo import api, fields, models

# TODO FIX LATER
# REMOVE OR COMMENT BELOW class when upgrading nomin_account module
class AccountAccount(models.Model):
    _inherit = 'account.account'

    department_id = fields.Many2one('hr.department', 'Department', index=True)
class AccountTax(models.Model):
    _inherit = 'account.tax'
    
    department_id = fields.Many2one('hr.department', 'Department', index=True)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    parent_department = fields.Many2one('hr.department' ,string='Parent department',readonly=True,track_visibility='onchange')