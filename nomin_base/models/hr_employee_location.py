#-*- coding:utf-8 -*-
from odoo import api, fields, models, _

class HrEmployeeLocation(models.Model):
    _name = 'hr.employee.location'
    _description = 'Employee Location'

    name = fields.Char(string="Employee Location", required=True)
    line_ids = fields.One2many('hr.employee.location.line', 'emp_loc_id', string='Sub Location Name')
    country_state_code = fields.Char(string="Country state code",track_visibility='onchange')
    parent_location =  fields.Many2one('hr.employee.location', string='Parent Location')
    zangia_id = fields.Char(string="Zangia id", required=True)
    
    

    @api.onchange('name')
    def onchange_location_name(self):
        self.update({
            'name': str(self.name).decode('utf-8').title() if self.name  else  ''
            }) 

    _sql_constraints = [
            ('name_uniq', 'unique (name)', "Name already exists !"),
    ]

class HrEmployeeLocationLine(models.Model):
    _name = 'hr.employee.location.line'
        
    emp_loc_id = fields.Many2one('hr.employee.location', string='Employee Location')
    name = fields.Char(string="Sub location", required=True)
    state_loc_code = fields.Char(string="state location code",track_visibility='onchange')
    
    @api.onchange('name')
    def onchange_location_sub_name(self):
        self.update({
            'name': str(self.name).decode('utf-8').title() if self.name  else  ''
            }) 
    
    _sql_constraints = [
            ('sub_name_uniq', 'unique (emp_loc_id, name)', "Sub name already exists !"),
    ]

 
