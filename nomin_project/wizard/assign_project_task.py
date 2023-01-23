# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

class AssignProjectTask(models.TransientModel):
    _name = 'assign.project.task'
    _description = 'Assign project task'
    
    user_id = fields.Many2one('res.users', string="User")
    
    def action_assign(self):
        context = self._context
        active_ids =  self._context.get('active_ids', [])
        tasks = {
                                   't_new' :u'Шинэ',
                                   't_cheapen':u'Үнэ тохирох',
                                   't_cheapened':u'Үнэ тохирсон',
                                   't_user':u'Хариуцагчтай',
                                   't_start':u'Хийгдэж буй',
                                   't_control':u'Хянах',
                                   't_confirm':u'Батлах',
                                   't_evaluate':u'Үнэлэх',
                                   't_done':u'Дууссан',
                                   't_cancel':u'Цуцалсан',
                                   't_back':u'Хойшлуулсан'
        }
        if context['active_model'] == 'project.task':
                task_obj = self.env['project.task'].browse(active_ids)
                for task in task_obj:
                    if task.task_state in ['t_new','t_cheapen','t_cheapened','t_user']:
                        task.write({'user_id':self.user_id.id})
                    else:

                        raise UserError(_(u'Алдаа: [%s  даалгавар- %s]  төлөвтэй  даалгавар хувиарлах боломжгүй.\n Та Ноорог, Үнэ тохирох, Үнэ тохирсон, Хариуцагчтай төлөв дээр даалгавар хувиарлах боломжтой'%(task.name,tasks[task.task_state])))
        
                 
        return {'type': 'ir.actions.act_window_close'}