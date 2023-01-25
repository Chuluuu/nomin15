# -*- coding: utf-8 -*-

from openerp import api, fields, models, _
from openerp.exceptions import UserError

class RequestOrderConfig(models.Model):
    """ Ажлын урсгалын тохиргоо """
    
    _name = 'request.order.config'
    _description = "All Request Configure"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = "sequence asc"



    name = fields.Char(string='Name', required=True, size=128 ,track_visibility='onchange')    
    department_ids = fields.Many2many('hr.department', 'hr_department_request_config_ref', 'config_id', 'dep_id', string=u'Хэлтэсүүд' , required="1")
    sequence = fields.Integer(string='Sequence',default=1,track_visibility='onchange')
    group_ids = fields.Many2many('res.groups', 'res_groups_request_config_ref', 'config_id', 'group_id', string=u'Грүппүүд',track_visibility='onchange')
    select_dep = fields.Selection([('perform','Perform'),('customer','Customer')], string='Selection department',track_visibility='onchange', default='perform')
    python_code = fields.Text(string="Python code" ,track_visibility='onchange')   

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
    @api.multi
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