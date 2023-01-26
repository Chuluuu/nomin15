# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class RequestOrderConfig(models.Model):
    """ Ажлын урсгалын тохиргоо """
    
    _name = 'request.order.config'
    _description = "All Request Configure"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "sequence asc"



    name = fields.Char(string='Name', required=True, size=128 ,tracking=True)    
    department_ids = fields.Many2many('hr.department', 'hr_department_request_order_config_ref', 'config_id', 'dep_id', string=u'Хэлтэсүүд' , required="1")
    sequence = fields.Integer(string='Sequence',default=1,tracking=True)
    group_ids = fields.Many2many('res.groups', 'res_groups_request_order_config_ref', 'config_id', 'group_id', string=u'Грүппүүд',tracking=True)
    select_dep = fields.Selection([('perform','Perform'),('customer','Customer')], string='Selection department',tracking=True, default='perform')
    python_code = fields.Text(string="Python code" ,tracking=True)   

    type = fields.Selection([('fixed','Fixed'),('department','Department'),('group','Group'),('distribute','Distribute')], string='Type', required=True, default='group')
    user_ids = fields.Many2many('res.users', string='Users')
    user_id = fields.Many2one('res.users', string='User')
    is_fold =fields.Boolean(string="Is fold",default=False)
    field_invisible =fields.Boolean(string="Дизайны захиалга",default=False)
    field_doctor =fields.Boolean(string="Эмчийн тохиргоо",default=False)

    @api.onchange('type')
    def onchange_type(self):
            self.update({'user_id': False,
                         'group_ids':  False,
                         })
    
    def write(self, vals):
        if vals.get('type') =='fixed':
            vals.update({
                     'group_ids':  False,                        
                     })
        if vals.get('type') =='distribute':
            vals.update({
                     'group_ids':  False,                        
                     })
        if vals.get('type') =='group':
            vals.update({
                     'user_id':  False,                        
                     })
        if vals.get('type') =='department':
            vals.update({
                    'user_id':  False,    
                     'group_ids':  False,                        
                     })
                        
        return super(RequestOrderConfig, self).write(vals)