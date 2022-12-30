# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from openerp import api, fields, models, _
from openerp.exceptions import UserError
from fnmatch import translate
from openerp.osv import osv
from pychart.color import steelblue

integraition_user_id=462

class RequestConfig(models.Model):
    """ Ажлын урсгалын тохиргоо """
    
    _name = 'request.config'
    _description = "All Request Configure"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = "id desc"
    
    TYPE_SELECTION =[('payment.request','Төлбөрийн хүсэлт'),
                      ('purchase.requisition',u'Худалдан авалт шаардах'),
                      ('contract',u'Гэрээ'),
                      ('nomin.budget','Budget'),
                      ('nomin.other.budget','Other Budget'),
                      ('purchase.tender','Tender Reguest'),
                      ('account.cost.sharing.line','Account Cost Share'),
                      ('purchase.comparison',u'Худалдан авалт харьцуулалт'),
                      ('purchase.order',u'Худалдан авалт захиалга'),
                      ('insurance',U'Даатгал'),
                      ('salary.performance', 'Salary performance'),
                      ('assignment.order', 'Томилолтын захиалга'),
                      ('loans.list', 'Тодорхойлолтын хүсэлт'),
                      ('hr.disciplinary.punishment', 'Сахилгын хариуцлага'),
                      ('hr.job.position.move', 'Job Position Move'),
                      ('hr.award.proposal', 'Шагналын хүсэлт'),
                      ('hr.leave.flow', 'Чөлөөний урсгал'),
                      ('program.order.flow', 'Захиалгын урсгал'),
                      ('employment.termination.checkout.flow', 'Тойрох хуудасны урсгал'),
                      ('stock.requisition', 'Хөрөнгийн хөдөлгөөний шаардах'),
                      ('nomin.payroll', 'Цалин бодолтын урсгал'),
                      ('nomin.payroll.vacation', 'Цалин ээлжийн амралт'),
                      ('nomin.payroll.employee.gap', 'Цалин зөрүү бодох'),
                      ('nomin.payroll.performance.plan', 'Цалин гүйцэтгэл өөрчлөх'),
                      ('loan.request.for.department', 'Зээлийн хүсэлт(Салбар)'),
                      ('archive.flow', 'Тушаалын урсгал'),
                    ]



    active = fields.Boolean(string='Active', default=True)
    name = fields.Char(string='Name', required=True, size=128)
    process = fields.Selection(TYPE_SELECTION, string='Process', required=True, default='payment.request')
    template_id = fields.Many2one('mail.template', string='Mail Template')
    lines = fields.One2many('request.config.line', 'request_id', 'Config Line')
    department_id = fields.Many2one('hr.department', string='Department')
    department_ids = fields.Many2many('hr.department', 'hr_department_request_config_ref', 'config_id', 'dep_id', string=u'Хэлтэсүүд')
    object_id = fields.Many2one('ir.model', string='Обьект')
    sequence = fields.Integer(string='Sequence',default=0)
    payment_lines = fields.One2many('request.config.payment.line', 'request_id', 'Config Line')
    other_budget_lines = fields.One2many('request.config.other.budget.line', 'request_id', 'Config Line')
    purchase_lines = fields.One2many('request.config.purchase.line', 'request_id', 'Config Line')
    assignment_lines = fields.One2many('request.config.assignment.order.line', 'request_id', string="Assignment order config line", ondelete="cascade")
    loans_lines = fields.One2many('request.config.loans.request.line', 'reg_id', string="Loan request line", ondelete="cascade")
    award_proposal_lines = fields.One2many('request.config.award.proposal.line', 'request_id', string="Award proposal config line", ondelete="cascade")
    assignment_type_id = fields.Selection([('internal','Internal'),('external','External')], string="Request Type")
    is_show_parent = fields.Boolean(string="Is show parent")
    leave_flow_lines = fields.One2many('request.config.leave.flow', 'request_id', string="Leave Flow Config", ondelete="cascade")
    loans_type_id = fields.Selection([('a','Normal'),('b','Union')], string="Loans request Type")
    program_order_flow_lines = fields.One2many('request.config.ordering.flow', 'request_id', string="Order Flow Config", ondelete="cascade")
    ordering_type_id = fields.Selection([('training','Сургалтын хүсэлт'),('system','Систем админ'),('system_senior','Системийн ахлах'),('program','ПХУА')], string="Request Type")
    turn_around_page_flow_lines = fields.One2many('request.config.employment.termination.checkout.flow', 'request_id', string="Termiantion Checkout Flow Config", ondelete="cascade")
    turn_around_page_type_id = fields.Selection([('up','Няраваас дээш албан тушаалтан'),('down','Няраваас дooш албан тушаалтан'),('move_down','Салбар шилжих няраваас доош'),('move_up','Салбар шилжих няраваас дээш')], string="Turn Around Page Type")
    loans_request_department_id = fields.One2many('loans.request.config.department', 'reg_id', string="Loan request config department", ondelete="cascade")
    max_limit = fields.Integer(string = 'Max limit')
    min_limit = fields.Integer(string = 'Min limit')
    archive_flow_lines = fields.One2many('request.config.archive.flow', 'request_id', string="Archive Flow Config", ondelete="cascade")
    loan_request_type_id = fields.Selection([('impecs','Impecs')], string="Loan request type")
    
    
    @api.multi
    @api.onchange('process','department_id')
    def onchange_process(self):
        values = {}
        if self.process:
            object = self.env['ir.model'].search([('model','=',self.process)])
            self.update({'object_id':object.id})
            module = u''
            if self.process == 'nomin.budget':
                module = u'Бизнес төлөвлөгөө'
            elif self.process == 'purchase.requisition':
                module = u'Худалдан авалт'
            elif self.process == 'payment.request':
                module = u'Төлбөрийн хүсэлт'
            elif self.process == 'purchase.tender':
                module = u'Тендер зарлуулах хүсэлт'
            elif self.process == 'account.cost.sharing.line':
                module = u'ИнКасс хүлээн авах'
            elif self.process == 'nomin.other.budget':
                module = u'Бусад төсөв'
            if self.department_id:
                if self.process != 'contract':
                    name = u'%s салбарын %s-ны хянах, батлах урсгалын тохиргоо'%(self.department_id.name,module)
                    self.update({'name':name})  
        
            
    
    @api.model
    def get_new_group_users(self, groups):
        user_ids = []
        partner_ids = []
        if groups and groups.users:
            for u in groups.users:
                if u.id != integraition_user_id:
                    user_ids.append(u.id)
                    partner_ids.append(u.partner_id.id)
        return user_ids, partner_ids
    
    @api.model
    def get_new_department_manager(self,user_id):
        emp_id = self.env['hr.employee'].search([('user_id','=',user_id)])
        if emp_id:
            emp = self.env['hr.employee'].browse(emp_id[0].id)
            if emp and emp.department_id and emp.department_id.manager_id and emp.department_id.manager_id.user_id:
                return emp.department_id.manager_id.user_id.id, emp.department_id.manager_id.user_id.partner_id.id
            else:
                return False
        else:
            return False
        
    @api.model
    def get_new_config(self, model, user_id, process, department_id):
        context = self._context
        search_val = [('object_id.model','=',model)]+[('process','=',process)]+[('department_ids','in',department_id)]
        config_id = self.env['request.config'].search(search_val)
        if config_id:
            return config_id[0].id
        else:
            return False
        
    @api.model
    def get_department_user(self, user_ids, department_id):
        res_user_ids = []
        res_partner_ids = []
        if user_ids:
            for user in user_ids:
                self.env.cr.execute("select uid from res_users_budget_department_rel where depid=%s and uid=%s"%(department_id, user))
                fetched = self.env.cr.fetchone()
                if fetched:
                    part_id = self.env['res.users'].browse(user).partner_id.id
                    res_user_ids.append(user)
                    res_partner_ids.append(part_id)
        return res_user_ids, res_partner_ids
    
    @api.model
    def new_backward(self, model, active_seq, requester_id, depart_id=False):
        return self.new_forward(model, active_seq, requester_id, config_id, depart_id=depart_id, back=True)
   


    @api.model
    def budget_forward(self, active_seq, requester_id, config_id, state, department=False,back=False):
        ''' Ажлын урсгалын дараагийн алхамыг тодорхойлж ажилбар
            гүйцэтгэх хэрэглэгчийн id жагсаалтыг гаргаж авна.
        '''
        config_line_obj = self.env['request.config.other.budget.line']
        config_obj = self.env['request.config']
        state = ''
        signature_sequence = 0
        if not config_id:
            UserError(_('There is no request workflow transaction defined on your department! Please contact System Team!'))
        search_args = [('request_id','=',config_id),('sequence','=',active_seq)]
        transitions = config_line_obj.search(search_args, order='sequence', limit=1)
        if transitions:
            transition = config_line_obj.browse(transitions.id)
            # ижил дараалал бүхий ажилбар бий эсэхийг шалгана.
            transitions = config_line_obj.search([('request_id','=',config_id),
                                                  ('sequence','=',active_seq)])
            if len(transitions) == 1:
                transitions = [transition]
            user_ids = []
            partner_ids = []
            sequence = active_seq
            group_name=""
            for transition in transitions:
                sequence = transition.sequence
                signature_sequence= transition.signature_sequence
                state = transition.state
                if transition.type == 'fixed':
                    user_ids.append(transition.user_id.id)
                    partner_ids.append(transition.user_id.partner_id.id)
                elif transition.type == 'group':
                    group_name = transition.group_id.name
                    group_user_ids , group_partner_ids = self.get_new_group_users(transition.group_id)
                    if group_user_ids and group_partner_ids:
                        user_ids.extend(group_user_ids)
                        partner_ids.extend(group_partner_ids)
                        if department:
                            user_ids, partner_ids = self.get_department_user(user_ids,department.id)
                    else:
                        UserError(_('There is no activity group defined for next workflow step! Please contact System Team! [%s]'%(transition.group_id.name)))
                elif transition.type == 'depart':
                    dep_id, partner_id = self.get_new_department_manager(requester_id)
                    if dep_id and partner_id:
                        user_ids.append(dep_id)
                        partner_ids.append(partner_id)
                    else:
                        UserError(_('There is no activity manager defined for next workflow step! Please contact System Team!'))
                        
            if requester_id in user_ids and len(user_ids) == 1 and active_seq == 0:
                return self.payment_forward(sequence, requester_id)
            
            if user_ids == [] or partner_ids == []:
                raise UserError(_('There is no activity group defined for next workflow step! Please contact System Team! [%s]'%(group_name)))
            
            return user_ids, partner_ids, sequence ,state,signature_sequence
        elif active_seq == 0 :
            UserError(_('There is no activity defined for next workflow step! Please contact System Team!'))
        return [], [], active_seq,'done',signature_sequence

    @api.model
    def payment_forward(self, active_seq, requester_id, config_id, state, department=False,back=False):
        ''' Ажлын урсгалын дараагийн алхамыг тодорхойлж ажилбар
            гүйцэтгэх хэрэглэгчийн id жагсаалтыг гаргаж авна.
        '''
        config_line_obj = self.env['request.config.payment.line']
        config_obj = self.env['request.config']
        state = ''
        signature_sequence = 0
        if not config_id:
            UserError(_('There is no request workflow transaction defined on your department! Please contact System Team!'))
        search_args = [('request_id','=',config_id),('sequence','=',active_seq)]
        transitions = config_line_obj.search(search_args, order='sequence', limit=1)
        if transitions:
            transition = config_line_obj.browse(transitions.id)
            # ижил дараалал бүхий ажилбар бий эсэхийг шалгана.
            transitions = config_line_obj.search([('request_id','=',config_id),
                                                  ('sequence','=',active_seq)])
            if len(transitions) == 1:
                transitions = [transition]
            user_ids = []
            partner_ids = []
            sequence = active_seq
            group_name=""
            for transition in transitions:
                sequence = transition.sequence
                signature_sequence= transition.signature_sequence
                state = transition.state
                if transition.type == 'fixed':
                    user_ids.append(transition.user_id.id)
                    partner_ids.append(transition.user_id.partner_id.id)
                elif transition.type == 'group':
                    group_name = transition.group_id.name
                    group_user_ids , group_partner_ids = self.get_new_group_users(transition.group_id)
                    if group_user_ids and group_partner_ids:
                        user_ids.extend(group_user_ids)
                        partner_ids.extend(group_partner_ids)
                        if department:
                            user_ids, partner_ids = self.get_department_user(user_ids,department.id)
                    else:
                        UserError(_('There is no activity group defined for next workflow step! Please contact System Team! [%s]'%(transition.group_id.name)))
                elif transition.type == 'depart':
                    dep_id, partner_id = self.get_new_department_manager(requester_id)
                    if dep_id and partner_id:
                        user_ids.append(dep_id)
                        partner_ids.append(partner_id)
                    else:
                        UserError(_('There is no activity manager defined for next workflow step! Please contact System Team!'))
                        
            if requester_id in user_ids and len(user_ids) == 1 and active_seq == 0:
                return self.payment_forward(sequence, requester_id)
            
            if user_ids == [] or partner_ids == []:
                raise UserError(_('There is no activity group defined for next workflow step! Please contact System Team! [%s]'%(group_name)))
            
            return user_ids, partner_ids, sequence ,state,signature_sequence
        elif active_seq == 0 :
            UserError(_('There is no activity defined for next workflow step! Please contact System Team!'))
        return [], [], active_seq,'done',signature_sequence

    @api.model
    def new_forward(self, active_seq, requester_id, config_id, department=False,back=False):
        ''' Ажлын урсгалын дараагийн алхамыг тодорхойлж ажилбар
            гүйцэтгэх хэрэглэгчийн id жагсаалтыг гаргаж авна.
        '''
        config_line_obj = self.env['request.config.line']
        config_obj = self.env['request.config']
        
        if not config_id:
            UserError(_('There is no request workflow transaction defined on your department! Please contact System Team!'))
        search_args = [('request_id','=',config_id),('sequence','=',active_seq)]
        transitions = config_line_obj.search(search_args, order='sequence', limit=1)
        if transitions:
            transition = config_line_obj.browse(transitions.id)
            # ижил дараалал бүхий ажилбар бий эсэхийг шалгана.
            transitions = config_line_obj.search([('request_id','=',config_id),
                                                  ('sequence','=',active_seq)])
            if len(transitions) == 1:
                transitions = [transition]
            user_ids = []
            partner_ids = []
            sequence = active_seq
            group_name=""
            for transition in transitions:
                sequence = transition.sequence
                if transition.type == 'fixed':
                    user_ids.append(transition.user_id.id)
                    partner_ids.append(transition.user_id.partner_id.id)
                elif transition.type == 'group':
                    group_name = transition.group_id.name
                    group_user_ids , group_partner_ids = self.get_new_group_users(transition.group_id)
                    if group_user_ids and group_partner_ids:
                        user_ids.extend(group_user_ids)
                        partner_ids.extend(group_partner_ids)
                        if department:
                            user_ids, partner_ids = self.get_department_user(user_ids,department.id)
                    else:
                        UserError(_('There is no activity group defined for next workflow step! Please contact System Team! [%s]'%(transition.group_id.name)))
                elif transition.type == 'depart':
                    dep_id, partner_id = self.get_new_department_manager(requester_id)
                    if dep_id and partner_id:
                        user_ids.append(dep_id)
                        partner_ids.append(partner_id)
                    else:
                        UserError(_('There is no activity manager defined for next workflow step! Please contact System Team!'))
                        
            if requester_id in user_ids and len(user_ids) == 1 and active_seq == 0:
                return self.new_forward(sequence, requester_id)
            
            if user_ids == [] or partner_ids == []:
                raise UserError(_('There is no activity group defined for next workflow step! Please contact System Team! [%s]'%(group_name)))
            
            return user_ids, partner_ids, sequence
        elif active_seq == 0 :
            UserError(_('There is no activity defined for next workflow step! Please contact System Team!'))
        return [], [], active_seq
        
    #===========================================================================
    # END
    #===========================================================================
    
    
    @api.model
    def get_department_manager(self,user_id):
        emp_id = self.env['hr.employee'].search([('user_id','=',user_id)])
        if emp_id:
            emp = self.env['hr.employee'].browse(emp_id[0].id)
            if emp and emp.department_id and emp.department_id.manager_id and emp.department_id.manager_id.user_id:
                return emp.department_id.manager_id.user_id.id
            else:
                return False
                #raise osv.except_osv(_('Error!'), _('There is no activity defined for next workflow step! Please contact System Team!'))
        else:
            return False
    
    @api.model
    def get_group_users(self,groups):
        user_ids = []
        if groups and groups.users:
            for u in groups.users:
                user_ids.append(u.id)
        return user_ids
    
    @api.model
    def get_depart(self,user_id):
        emp_id = self.env['hr.employee'].search([('user_id','=',user_id)])
        if emp_id:
            emp = self.env['hr.employee'].browse(emp_id[0].id)
            if emp and emp.department_id:
                return emp.department_id.id
            else:
                return False
                #raise osv.except_osv(_('Error!'), _('There is no activity defined for next workflow step! Please contact System Team!'))
        else:
            return False
    
   
    @api.model
    def get_config(self, model, user_id, process, sequence):
        res = False
        context = self._context
        search_val = [('object_id.model','=',model)]+[('process','=',process)]+[('sequence','=',sequence)]
        depart_id = self.get_depart(user_id)
        if depart_id:
            config_id = self.env['request.config'].search(search_val+[('department_id','=',depart_id)])
            if config_id:
                return config_id[0].id
#             else:
#                 config_id = self.env['request.config'].search(search_val)
#                 if config_id:
#                     return config_id[0].id
        else:
            config_id = self.env['request.config'].search(search_val)
            if config_id:
                return config_id[0].id
        return res
    
    
    @api.model
    def backward(self, model, active_seq, requester_id, depart_id=False):
        return self.forward(model, active_seq, requester_id, depart_id=depart_id, back=True)
    


    @api.model
    def forward(self, model, active_seq, requester_id, config_ids, depart_id=False, back=False):
        ''' Ажлын урсгалын дараагийн алхамыг тодорхойлж ажилбар
            гүйцэтгэх хэрэглэгчийн id жагсаалтыг гаргаж авна.
        '''
        config_line_obj = self.env['request.config.line']
        config_obj = self.env['request.config']
        domain = [('object_id.model','=',model)]
#         if depart_id:
#             domain = ['|',('object_id.model','=',model),('department_id','=',depart_id)]
#         config_ids = config_obj.search(domain)
        # if depart_id:
        #     domain = [('object_id.model','=',model),('department_id','=',depart_id),('sequence','=',sequence),('process','=',process)]
        #     config_ids = config_obj.search(domain)
        #     if not config_ids:
        #         config_ids = config_obj.search(domain)
        # else:
        #     config_ids = config_obj.search(domain)

        if not config_ids:
            raise osv.except_osv(_('Error!'), _('There is no request workflow transaction defined on your department! Please contact System Team!'))
        search_args = [('request_id','=',config_ids)]
        if not back:
            search_args = search_args+[('sequence','=',active_seq)]
        else :
            search_args = search_args+[('sequence','=',active_seq)]
        transitions = config_line_obj.search(search_args, order='sequence', limit=1)
        if transitions:
            transition = config_line_obj.browse(transitions.id)
            # ижил дараалал бүхий ажилбар бий эсэхийг шалгана.
            transitions = config_line_obj.search([('request_id','=',config_ids),
                                ('sequence','=',transition.sequence)])
            if len(transitions) == 1:
                transitions = [transition]
            user_ids = []
            sequence = active_seq
            for transition in transitions:
                sequence = transition.sequence
                state = transition.state
                if transition.type == 'fixed':
                    user_ids.append(transition.user_id.id)
                elif transition.type == 'group':
                    group_user_ids = self.get_group_users(transition.group_id)
                    if group_user_ids:
                        user_ids.extend(group_user_ids)
                    else:
                        raise osv.except_osv(_('Error!'), _('There is no activity group defined for next workflow step! Please contact System Team!'))
                elif transition.type == 'depart':
                    dep_id = self.get_department_manager(requester_id)
                    if dep_id:
                        user_ids.append(dep_id)
                    else:
                        raise osv.except_osv(_('Error!'), _('There is no activity manager defined for next workflow step! Please contact System Team!'))
            if requester_id in user_ids and len(user_ids) == 1 and active_seq == 0:
                return self.forward(model, sequence, requester_id, depart_id=depart_id, back=back)
            return user_ids, sequence ,state
        elif active_seq == 0 :
            raise osv.except_osv(_('Error!'), _('There is no activity defined for next workflow step! Please contact System Team!'))
        return [], active_seq ,'draft'
    

    @api.model
    def purchase_forward(self, model, active_seq, requester_id, config_ids, depart_id=False, back=False):
        ''' Ажлын урсгалын дараагийн алхамыг тодорхойлж ажилбар
            гүйцэтгэх хэрэглэгчийн id жагсаалтыг гаргаж авна.
        '''
        config_line_obj = self.env['request.config.purchase.line']
        config_obj = self.env['request.config']
        domain = [('object_id.model','=',model)]
#         if depart_id:
#             domain = ['|',('object_id.model','=',model),('department_id','=',depart_id)]
#         config_ids = config_obj.search(domain)
        # if depart_id:
        #     domain = [('object_id.model','=',model),('department_id','=',depart_id),('sequence','=',sequence),('process','=',process)]
        #     config_ids = config_obj.search(domain)
        #     if not config_ids:
        #         config_ids = config_obj.search(domain)
        # else:
        #     config_ids = config_obj.search(domain)

        if not config_ids:
            raise osv.except_osv(_('Error!'), _('There is no request workflow transaction defined on your department! Please contact System Team!'))
        search_args = [('request_id','=',config_ids)]
        if not back:
            search_args = search_args+[('sequence','=',active_seq)]
        else :
            search_args = search_args+[('sequence','=',active_seq)]
        transitions = config_line_obj.search(search_args, order='sequence', limit=1)
        if transitions:
            transition = config_line_obj.browse(transitions.id)
            # ижил дараалал бүхий ажилбар бий эсэхийг шалгана.
            transitions = config_line_obj.search([('request_id','=',config_ids),
                                ('sequence','=',transition.sequence)])
            if len(transitions) == 1:
                transitions = [transition]
            user_ids = []
            sequence = active_seq
            for transition in transitions:
                sequence = transition.sequence
                state = transition.state
                if transition.type == 'fixed':
                    user_ids.append(transition.user_id.id)
                elif transition.type == 'group':
                    group_user_ids = self.get_group_users(transition.group_id)
                    if group_user_ids:
                        user_ids.extend(group_user_ids)
                    else:
                        raise osv.except_osv(_('Error!'), _('There is no activity group defined for next workflow step! Please contact System Team!'))
                elif transition.type == 'depart':
                    dep_id = self.get_department_manager(requester_id)
                    if dep_id:
                        user_ids.append(dep_id)
                    else:
                        raise osv.except_osv(_('Error!'), _('There is no activity manager defined for next workflow step! Please contact System Team!'))
            if requester_id in user_ids and len(user_ids) == 1 and active_seq == 0:
                return self.forward(model, sequence, requester_id, depart_id=depart_id, back=back)
            return user_ids, sequence ,state
        elif active_seq == 0 :
            raise osv.except_osv(_('Error!'), _('There is no activity defined for next workflow step! Please contact System Team!'))
        return [], active_seq ,'draft'
    
class RequestConfigLine(models.Model):
    """ Ажлын урсгалын тохиргооны жагсаалт """
    
    _name = 'request.config.line'
    _description = 'All request Config Line'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'sequence'
    STATE_SELECTION = [
                       #('draft','Draft'),
                       ('other','Other'),
                       ('sent','Sent'),
                       ('approved','Approved'),
                       ('verified','Verified'),
                       ('confirmed','Confirmed'),
                       ('rejected','Rejected'),
                       #('cancelled','Cancelled'),
                       ]
  
    name = fields.Char(string='Name', size=128, required=True)
    request_id = fields.Many2one('request.config', string='Request Config', required=True)
    sequence = fields.Integer(string='Sequence', required=True, default=1)
    type = fields.Selection([('fixed','Fixed'),('depart','Department'),('group','Group')], string='Type', required=True, default='group')
    user_id = fields.Many2one('res.users', string='User')
    group_id = fields.Many2one('res.groups', string='Group')
    state = fields.Selection(STATE_SELECTION, string='State', required=True, defualt='sent')

    @api.onchange('type')
    def onchange_type(self):
            self.update({'user_id': False,
                         'group_id':  False,
                        'state':False,
                         })
    @api.multi
    def write(self, vals):
        if vals.get('type') =='fixed':
            vals.update({
                     'group_id':  False,                        
                     })
        if vals.get('type') =='group':
            vals.update({
                     'user_id':  False,                        
                     })
        if vals.get('type') =='depart':
            vals.update({
                    'user_id':  False,    
                     'group_id':  False,                        
                     })
                        
        return super(RequestConfigLine, self).write(vals)

class RequestConfigPaymentLine(models.Model):
    """ Ажлын урсгалын тохиргооны жагсаалт """
    
    _name = 'request.config.payment.line'
    _description = 'All request Config Line'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'sequence'
    # STATE_SELECTION = [
    #                    #('draft','Draft'),
    #                    ('other','Other'),
    #                    ('sent','Sent'),
    #                    ('approved','Approved'),
    #                    ('verified','Verified'),
    #                    ('confirmed','Confirmed'),
    #                    ('rejected','Rejected'),
    #                    #('cancelled','Cancelled'),
    #                    ]
    PAYMENT_SELECTION=  [
        ('dep_account_verify','Department Account Verify'),
        ('dep_chiep_verify','Department chief  Verify'),
        ('business_chief_verify','Business Chief Verify'),
        ('holding_ceo_verify','Holding CEO verify'),
    ]
    name = fields.Char(string='Name', size=128, required=True)
    request_id = fields.Many2one('request.config', string='Request Config', required=True)
    sequence = fields.Integer(string='Sequence', required=True, default=1)
    type = fields.Selection([('fixed','Fixed'),('depart','Department'),('group','Group')], string='Type', required=True, default='group')
    user_id = fields.Many2one('res.users', string='User')
    group_id = fields.Many2one('res.groups', string='Group')
    limit = fields.Float(string = 'Limit')
    # state = fields.Selection(STATE_SELECTION, string='State', required=True, defualt='sent')
    state = fields.Selection(PAYMENT_SELECTION, string="Payment selection", required = True)
    signature_sequence = fields.Integer(string='Signature sequence')
    @api.onchange('type')
    def onchange_type(self):
            self.update({'user_id': False,
                         'group_id':  False,
                        'state':False,
                         })
    @api.multi
    def write(self, vals):
        if vals.get('type') =='fixed':
            vals.update({
                     'group_id':  False,                        
                     })
        if vals.get('type') =='group':
            vals.update({
                     'user_id':  False,                        
                     })
        if vals.get('type') =='depart':
            vals.update({
                    'user_id':  False,    
                     'group_id':  False,                        
                     })
                        
        return super(RequestConfigPaymentLine, self).write(vals)

class RequestConfigOtherBudgetLine(models.Model):
    """ Ажлын урсгалын тохиргооны жагсаалт """
    
    _name = 'request.config.other.budget.line'
    _description = 'All request Config Line'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'sequence'
    # STATE_SELECTION = [
    #                    #('draft','Draft'),
    #                    ('other','Other'),
    #                    ('sent','Sent'),
    #                    ('approved','Approved'),
    #                    ('verified','Verified'),
    #                    ('confirmed','Confirmed'),
    #                    ('rejected','Rejected'),
    #                    #('cancelled','Cancelled'),
    #                    ]
    STATE_SELECTION = [
        ('draft','Draft'),
        ('verify1','Verify 1'),
        ('confirm_ceo','Branch CEO Approval'),
        ('verify2','Verify 2'),
        ('business_chief_verify','Business Chief Verify'),
        ('verify3','Verify 3'),
        ('confirm_group_ceo','Holding CEO Approval'),
        ('done','Done'),
        ('closed','Closed'),
        ('cancelled','Cancelled')
    ]
    name = fields.Char(string='Name', size=128, required=True)
    request_id = fields.Many2one('request.config', string='Request Config', required=True)
    sequence = fields.Integer(string='Sequence', required=True, default=1)
    type = fields.Selection([('fixed','Fixed'),('depart','Department'),('group','Group')], string='Type', required=True, default='group')
    user_id = fields.Many2one('res.users', string='User')
    group_id = fields.Many2one('res.groups', string='Group')
    limit = fields.Float(string = 'Limit')
    # state = fields.Selection(STATE_SELECTION, string='State', required=True, defualt='sent')
    state = fields.Selection(STATE_SELECTION, string="Other budget state selection", required = True)
    signature_sequence = fields.Integer(string='Signature sequence')

    @api.onchange('type')
    def onchange_type(self):
            self.update({'user_id': False,
                         'group_id':  False,
                        'state':False,
                         })
    @api.multi
    def write(self, vals):
        if vals.get('type') =='fixed':
            vals.update({
                     'group_id':  False,                        
                     })
        if vals.get('type') =='group':
            vals.update({
                     'user_id':  False,                        
                     })
        if vals.get('type') =='depart':
            vals.update({
                    'user_id':  False,    
                     'group_id':  False,                        
                     })
                        
        return super(RequestConfigOtherBudgetLine, self).write(vals)
class RequestConfigPurchasetLine(models.Model):
    """ Ажлын урсгалын тохиргооны жагсаалт """
    
    _name = 'request.config.purchase.line'
    _description = 'All request Config Line'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'sequence'
    # STATE_SELECTION = [
    #                    #('draft','Draft'),
    #                    ('other','Other'),
    #                    ('sent','Sent'),
    #                    ('approved','Approved'),
    #                    ('verified','Verified'),
    #                    ('confirmed','Confirmed'),
    #                    ('rejected','Rejected'),
    #                    #('cancelled','Cancelled'),
    #                    ]
    STATE_SELECTION=[('draft','Draft'),
    ('sent','Sent'),#Илгээгдсэн
    ('approved','Approved'),#Зөвшөөрсөн
    ('verified','Verified'),#Хянасан
    ('confirmed','Confirmed'),#Батласан
    ('sent_to_supply',u'Хангамжид илгээгдсэн'),#Хангамжаарх худалдан авалт
    ('fulfil_request',u'Биелүүлэх хүсэлт'),# Биелүүлэх хүсэлт
    # ('fulfill',u'Биелүүлэх'),# Биелүүлэх
    ('receive','Хүлээн авах'),
    ('assigned',u'Хувиарласан'),
    ('canceled','Canceled'),#Цуцлагдсан
    ('sent_nybo',u'Нягтлан бодогчид илгээгдсэн')
    ]
    name = fields.Char(string='Name', size=128, required=True)
    request_id = fields.Many2one('request.config', string='Request Config', required=True)
    sequence = fields.Integer(string='Sequence', required=True, default=1)
    type = fields.Selection([('fixed','Fixed'),('depart','Department'),('group','Group')], string='Type', required=True, default='group')
    user_id = fields.Many2one('res.users', string='User')
    group_id = fields.Many2one('res.groups', string='Group')
    limit = fields.Float(string = 'Limit')
    # state = fields.Selection(STATE_SELECTION, string='State', required=True, defualt='sent')
    state = fields.Selection(STATE_SELECTION, string="STATE", required = True)
    signature_sequence = fields.Integer(string=u'Гарын үсгийн дараалал')

    @api.onchange('type')
    def onchange_type(self):
            self.update({'user_id': False,
                         'group_id':  False,
                        'state':False,
                         })
    @api.multi
    def write(self, vals):
        if vals.get('type') =='fixed':
            vals.update({
                     'group_id':  False,                        
                     })
        if vals.get('type') =='group':
            vals.update({
                     'user_id':  False,                        
                     })
        if vals.get('type') =='depart':
            vals.update({
                    'user_id':  False,    
                     'group_id':  False,                        
                     })
                        
        return super(RequestConfigPurchasetLine, self).write(vals)


class RequestHistory(models.Model):
    """ Ажлын урсгалын түүх """
    
    _name = 'request.history'
    _description = 'Request History'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'id desc'
    STATE_SELECTION = [('draft','Draft'),
                       ('sent','Sent'),#Илгээгдсэн
                       ('approved',u'Зөвшөөрсөн'),#Зөвшөөрсөн
                       ('verified',u'Хянасан'),#Хянасан
                       ('next_confirm_user',u'Зөвшөөрсөн'),#Дараагийн батлах хэрэглэгчид илгээгдсэн
                       ('confirmed',u'Баталсан'),#Батласан
                       ('tender_created',u'Тендер үүссэн'),#Тендер үүссэн
                       ('sent_to_supply',u'Хангамжид илгээгдсэн'),#Хангамжаарх худалдан авалт
                       ('fulfil_request',u'Биелүүлэх хүсэлт'),# Биелүүлэх хүсэлт
                       ('fulfill',u'Биелүүлэх'),# Биелүүлэх
                       ('retrived',u'Буцаагдсан'),# Буцаагдсан
                       ('retrive_request',u'Буцаагдах хүсэлт'),# Буцаагдах хүсэлт
                       ('rejected',u'Rejected'),
                       ('assigned',u'Хувиарласан'),
                       ('canceled',u'Цуцлагдсан'),#Цуцлагдсан
                       ('purchased',u'Худалдан авалт үүссэн'),#Худалдан авалт үүссэн
                       ('purchase',U'Худалдан авах захиалга'),#Худалдан авалт үүссэн
                       ('sent_to_supply_manager',u'Бараа тодорхойлох'),#Хангамж импортын менежер
                       ('closed',u'Хаагдсан'),
                       ('done',u'Дууссан'),
                       ('anket', 'Анкет'),
                        ('exam', 'Шалгалт'),
                        ('interview', 'Ярилцлага'),
                        ('professional', 'Мэргэжлийн шалгалт'),	
                        ('interview2', 'Ярилцлага2'),	
                        ('task', 'Даалгавар'),	
                        ('interview3', 'Ярилцлага3'),	
                       ('receive',u'Хүлээн авах'),
                       ('completed','Completed'),
                                   ]
    user_id = fields.Many2one('res.users', string='User', required=True)
    date = fields.Datetime(string='Action Date', required=True)
    type = fields.Selection(STATE_SELECTION, string='Type', required=True, default='draft')
    comment = fields.Text(string='Comment')
    sequence = fields.Integer(string='Sequence', default=1)
    awards_id = fields.Many2one('hr.award.proposal', 'Award Proposal', ondelete="cascade")

    

class RequestNewHistory(models.Model):
    """ Ажлын урсгалын түүх """
    
    _name = 'request.new.history'
    _description = 'Request History'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'id asc'
    
    STATE_SELECTION = [('verify','Verify'),
                       ('approved','Approved'),
                       ('rejected','Rejected'),
                       ('cancelled','Cancelled'),
                       ]
    
    user_ids = fields.Many2many('res.users', 'request_history_res_users_ref', 'history_id', 'user_id', string='User', required=True)
    date = fields.Datetime(string='Action Date', required=True)
    type = fields.Selection(STATE_SELECTION, string='Type', required=True, default='draft')
    comment = fields.Text(string='Comment')
    sequence = fields.Integer(string='Sequence', default=1)

    
class RequestAssignmentOrder(models.Model):
    """ Ажлын урсгалын тохиргооны жагсаалт """
    
    _name = 'request.config.assignment.order.line'
    _description = 'Assignment order Config Line'   
    _order = 'sequence'
    
    STATE_SELECTION = [
        ('draft','Draft'),
        ('sent_travel_manager','Sent travel manager'),
        ('sent_department_director', 'Sent department director'),
        ('sent_hr_manager', 'Sent HR manager'),
        ('sent_ceo', 'Sent CEO'),
        ('sent_business_director','Sent business director'),
        ('sent_postpone_request', 'Sent postpone request'),
        ('confirmed','Confirmed'),
        ('sent_report_accountants', 'Sent report accountants'),
        ('sent_report_director', 'Sent report director'),
    ]
    name = fields.Char(string='Name', size=128, required=True)
    request_id = fields.Many2one('request.config', string='Request Config', required=True)
    sequence = fields.Integer(string='Sequence', required=True, default=1)    
    group_id = fields.Many2one('res.groups', string='Group', required=True)        
    state = fields.Selection(STATE_SELECTION, string="State", required = True)



class RequestLoans(models.Model):
    """ Ажлын урсгалын тохиргооны жагсаалт """
    
    _name = 'request.config.loans.request.line'
    _description = 'Loans request Config Line'  
    _order = 'sequence'
    
    STATE_SELECTION = [
                                ('draft', 'Draft'),
                                ('accountants', 'Sent Accountants'),                                
                                ('sent_hr_manager', 'Sent HR manager'),
                                ('sent_director', 'Sent Director'),
                                ('sent_union', 'Sent Union manager'),
                                ('sent_hr_director', 'Sent HR Director'),
                                ('done', 'Done'),
                                ('reject', 'Reject'),
                    ]
    name = fields.Char(string='Name', size=128, required=True)
    reg_id = fields.Many2one('request.config', string='Request Config', required=True)
    sequence = fields.Integer(string='Sequence', required=True, default=1)    
    group_id = fields.Many2one('res.groups', string='Group', required=True)        
    state = fields.Selection(STATE_SELECTION, string="State", required = True)

        
class RequestHrAwardProposal(models.Model):
    """ Ажлын урсгалын тохиргооны жагсаалт 
    """
    _name = 'request.config.award.proposal.line'
    _description = 'HR Award Config Line'   
    _order = 'sequence'
    _inherit = 'mail.thread'
    
    STATE_SELECTION = [
        ('draft',u'Шагналын санал'),
        ('sent',u'Санал илгээгдсэн'),
        ('rejected',u'Татгалзагдсан'),
        ('verified',u'Хянасан'),
        ('confirmed',u'Батлагдсан'),
        ('completed',u'Шалгаруулалт дууссан'),
    ]

    name = fields.Char(string='Name', size=128, required=True)
    sequence = fields.Integer(string='Sequence', required=True, default=1)    
    group_id = fields.Many2one('res.groups', string='Group', required=True)        
    state = fields.Selection(STATE_SELECTION, string="State", required = True)
    request_id = fields.Many2one('request.config',track_visibility='onchange',string='Request config')

    

class RequestHrLeaveFlow(models.Model):
    """ Ажлын урсгалын тохиргооны жагсаалт 
    """
    _name = 'request.config.leave.flow'
    _description = 'Hr Leave Flow Config'   
    _order = 'sequence'
    _inherit = 'mail.thread'
    
    STATE_SELECTION = [
        ('draft',u'Ноорог'),
        ('requested',u'Удирдлагад илгээгдсэн'),
        ('sent_to_hr',u'Хүний нөөцөд илгээгдсэн'),
        ('sent_to_hr_director',u'Хүний нөөцийн захиралд илгээгдсэн'),
        ('rejected',u'Татгалзсан'),
        ('approved',u'Зөвшөөрсөн'),
    ]

    name = fields.Char(string='Name', size=128, required=True)
    sequence = fields.Integer(string='Sequence', required=True, default=1)    
    group_id = fields.Many2one('res.groups', string='Group', required=True)        
    state = fields.Selection(STATE_SELECTION, string="State", required = True)
    request_id = fields.Many2one('request.config',track_visibility='onchange',string='Request config')
    approvable_days = fields.Integer('Approvable days')



class ProgramOrderFlow(models.Model):
    """ Ажлын урсгалын тохиргооны жагсаалт 
    """
    _name = 'request.config.ordering.flow'
    _description = 'Program Order Flow Config'   
    _order = 'sequence'
    _inherit = 'mail.thread'
    
    STATE_SELECTION = [
        ('draft',u'Ноорог'),
        ('send',u'Илгээсэн'),
        ('done',u'Дууссан'),
        ('canceled',u'Цуцлагдсан'),
        ('confirmed',u'Зөвшөөрсөн'),
        ('allocated',u'Хувиарласан'),
        ('estimated',u'Хянуулах'),
        ('approved',u'Хянасан'),
        ('approved1',u'Батлагдсан'),                         
    ]


    name = fields.Char(string='Name', size=128, required=True)
    sequence = fields.Integer(string='Sequence', required=True, default=1)    
    group_id = fields.Many2one('res.groups', string='Group', required=True)        
    state = fields.Selection(STATE_SELECTION, string="State", required = True)
    request_id = fields.Many2one('request.config',track_visibility='onchange',string='Request config')




class TurnAroundPageFlow(models.Model):
    """ Ажлын урсгалын тохиргооны жагсаалт 
    """
    _name = 'request.config.employment.termination.checkout.flow'
    _description = u'Тойрох хуудас'
    _order = 'sequence'
    _inherit = 'mail.thread'
    
    STATE_SELECTION = [
        ('property', u'Эд зүйлсийн буцаалт'),
        ('financial', u'Санхүүгийн тооцоо'),
        ('legal', u'Эрхзүй ба Удирдлага'),
        ('hr_director',u'Хүний нөөцийн захирал'),
                           
    ]

    name = fields.Char(string='Name', size=128, required=True)
    sequence = fields.Integer(string='Sequence', required=True, default=1)    
    group_id = fields.Many2one('res.groups', string='Group', required=True)        
    state = fields.Selection(STATE_SELECTION, string="State", required = True)
    request_id = fields.Many2one('request.config',track_visibility='onchange',string='Request config')
    department_id = fields.Many2one('hr.department', string='Баталж байгаа хүний хэлтэс')
    job_id = fields.Many2one('hr.job', string='Боловсруулсан хүний албан тушаал')

class LoanRequestDepartment(models.Model):
    """ Ажлын урсгалын тохиргооны жагсаалт """
    
    _name = 'loans.request.config.department'
    _description = 'Loan Request Config department'  
    _order = 'sequence'
    
    STATE_SELECTION = [
                                ('draft', 'Draft'),
                                ('department_chief', 'Department chief'),
                                ('union_chief', 'Union chief'),
                                ('business_chief', 'Business chief'),
                                ('financial_business_chief', 'Financial business chief'),
                                ('business_development_chief', 'Business development chief'),
                                ('holding_ceo', 'Holding ceo'),                                   
                    ]
    name = fields.Char(string='Name', size=128, required=True)
    reg_id = fields.Many2one('request.config', string='Request Config', required=True)
    sequence = fields.Integer(string='Sequence', required=True, default=1)
    group_id = fields.Many2one('res.groups', string='Group', required=True)        
    state = fields.Selection(STATE_SELECTION, string="State", required = True)






class ArchiveFlow(models.Model):
    """ Ажлын урсгалын тохиргооны жагсаалт 
    """
    _name = 'request.config.archive.flow'
    _description = 'Archive Flow Config'   
    _order = 'sequence'
    _inherit = 'mail.thread'
    
    STATE_SELECTION = [

        ('notify',u'Мэдэгдэх ажилчид'),
        ('requested',u'Илгээгдсэн'),
        ('control',u'Хянасан'),
        ('confirmed',u'Баталсан'),
        ('verify',u'Илгээгдсэн1'),
        ('approve',u'Хянасан1'),
        ('approved',u'Баталсан1'),


    ]

    name = fields.Char(string='Name', size=128, required=True)
    sequence = fields.Integer(string='Sequence', required=True, default=1)    
    group_id = fields.Many2one('res.groups', string='Group', required=True)        
    state = fields.Selection(STATE_SELECTION, string="State", required = True)
    request_id = fields.Many2one('request.config',track_visibility='onchange',string='Request config')
    job_id = fields.Many2one('hr.job', string='HR Job')
