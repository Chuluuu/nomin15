# import string
# from openerp import api, fields, models

from odoo import SUPERUSER_ID, models
# from . import openerp.exceptions
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import float_is_zero
from odoo.tools import float_compare, float_round
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, ValidationError


# class hr_employee_team(models.Model):
#     _inherit = "hr.employee"

#     team_id = fields.Many2one('hr.team',
#         ondelete='set null', string="Team name", index=True,  tracking=True)

    # @api.one
    # @api.depends('department_id')
    # def department_id(self):
    #     self.= len(self.work_sub)
  
class hr_team(models.Model):
    _name = "hr.team"
    _description = "Team name"

    name = fields.Char("Name", required = True, tracking=True)
    department_id = fields.Many2one('hr.department',string="Category", index=True, required = True, tracking=True)
    user_ids = fields.One2many('res.users','team_id',string = 'ddd')


# class hr_allowed_teams(models.Model):
#     _inherit = "res.users"
#     hr_allowed_team = fields.Many2many('hr.team',string="Allowed teams", index=True, required = True, tracking=True)





# access_res_users_config_user,res users config user,model_res_users_config,base.group_user,1,0,0,0
# access_res_users_config_manager,res users config manager,model_res_users_config,nomin_base.group_config_manager,1,1,1,1
# access_res_users_config_support,res users config support,model_res_users_config,nomin_base.group_support_assistant,1,1,1,1

# access_res_users_config_line_user,res users config line user,model_res_users_config_line,base.group_user,1,0,0,0
# access_res_users_config_line_manager,res users config line manager,model_res_users_config_line,nomin_base.group_config_manager,1,1,1,1
# access_res_users_config_line_support,res users config line support,model_res_users_config_line,nomin_base.group_support_assistant,1,1,1,1

# access_res_users_to_forbid_config_user,res users to forbid config  user,model_to_forbid_config,base.group_user,1,0,0,0
# access_res_users_to_forbid_config_manager,res users to forbid config  manager,model_to_forbid_config,nomin_base.group_config_manager,1,1,1,0
# access_res_users_to_forbid_config_support,res users to forbid config  support,model_to_forbid_config,nomin_base.group_support_assistant,1,1,1,0

# access_res_users_forbid_config_line_user,res users forbid config line user,model_to_forbid_config_line,base.group_user,1,0,0,0
# access_res_users_forbid_config_line_manage,res users forbid config line manage,model_to_forbid_config_line,nomin_base.group_config_manager,1,1,1,1
# access_res_users_forbid_config_line_support,res users forbid config line support,model_to_forbid_config_line,nomin_base.group_support_assistant,1,1,1,1

# access_request_config_user,request.config.user,model_request_config,base.group_user,1,0,0,0
# access_request_config_manage,request.config.manage,model_request_config,nomin_base.group_config_manager,1,1,1,1
# access_request_config_line_user,request.config.line.user,model_request_config_line,base.group_user,1,0,0,0
# access_request_config_line_manage,request.config.line.manage,model_request_config_line,nomin_base.group_config_manager,1,1,1,1
# access_request_config_payment_line_user,request.config.line.user,model_request_config_payment_line,base.group_user,1,0,0,0
# access_request_config_payment_line_manager,request.config.line.manage,model_request_config_payment_line,nomin_base.group_config_manager,1,1,1,1
# access_request_history,request.history.user,model_request_history,base.group_user,1,1,1,1
# access_work_service_time,work.service.time.user,model_work_service_time,base.group_user,1,1,1,1
# access_work_service,work.service.user,model_work_service,base.group_user,1,0,0,0
# access_evaluation_indicators_users,evalution.indicators,model_evaluation_indicators,base.group_user,1,0,0,0
# access_res_partner_nomin_manager,res.partner,model_res_partner,nomin_base.group_partner_nomin_admin,1,1,1,1
# access_res_partner_group_manager,res.partner,model_res_partner,nomin_base.group_res_partner,1,0,0,0
# access_request_new_history_users,request.new.history,model_request_new_history,base.group_user,1,1,1,0
# access_request_config_other_budget_user,request.config.line.user,model_request_config_other_budget_line,base.group_user,1,0,0,0
# access_request_config_other_budget_line_manager,request.config.line.manage,model_request_config_other_budget_line,nomin_base.group_config_manager,1,1,1,1
# access_request_config_purchase_user,request.config.line.user,model_request_config_purchase_line,base.group_user,1,0,0,0
# access_request_config_purchase_line_manager,request.config.line.manager,model_request_config_purchase_line,nomin_base.group_config_manager,1,1,1,1
# access_add_user_followers_manager,add.user.followers.manager,model_add_user_followers,base.group_configuration,1,1,1,1
# access_partner_transport_category_admin,add.transport categor,model_partner_transport_category,group_partner_nomin_admin,1,1,1,1
# access_partner_transport_category_user,add.transport categor,model_partner_transport_category,base.group_user,1,0,0,0

# access_request_config_award_proposal_line_hr_user,request.config.award.proposal.line,model_request_config_award_proposal_line,base.group_hr_manager,1,1,1,1
# access_request_config_award_proposal_line_hr_employee,request.config.award.proposal.line,model_request_config_award_proposal_line,base.group_user,1,1,1,1
# access_hr_user_request_leave_flow,request.config.leave.flow,model_request_config_leave_flow,base.group_user,1,1,1,0
# access_hr_user_request_turn_around_page_flow,request.request.config.employment.termination.checkout.flow,model_request_config_employment_termination_checkout_flow,base.group_user,1,1,1,0
# access_business_direction_user,business.direction,model_business_direction,base.group_user,1,0,0,0
# access_nomin_report_footer_config_user,nomin.footer.report.config,model_nomin_report_footer_config,base.group_user,1,0,0,0
# access_business_type_user,business.type,model_business_type,base.group_user,1,0,0,0


# access_hr_user_loans_request_config_department,loans.request.config.department,model_loans_request_config_department,base.group_user,1,1,1,0
# access_hr_user_request_config_archive_flow,request.config.archive.flow,model_request_config_archive_flow,base.group_user,1,1,1,0
# access_fingerprint_lottery,fingerprint.lottery,model_fingerprint_lottery,base.group_user,1,1,1,1
# access_res_users_permission_log_user,res.users.permission.log,model_res_users_permission_log,base.group_user,0,1,1,0
# access_res_users_permission_log_manager,res.users.permission.log,model_res_users_permission_log,base.group_configuration,1,1,1,1

# access_hr_user_sod_designer,sod.designer,model_sod_designer,base.group_user,1,1,1,0
# access_hr_user_sod_field,sod.field,model_sod_field,base.group_user,1,1,1,0
# access_hr_user_sod_state,sod.state,model_sod_state,base.group_user,1,1,1,0
# access_hr_user_sod_workflow,sod.workflow,model_sod_workflow,base.group_user,1,1,1,0

# access_hr_user_sod_workflow_name,sod.workflow.name,model_sod_workflow_name,base.group_user,1,1,1,0
# access_hr_user_sod_workflow_line,sod.workflow.line,model_sod_workflow_line,base.group_user,1,1,1,0
# access_hr_user_sod_workflow_group_line,sod.workflow.group.line,model_sod_workflow_group_line,base.group_user,1,1,1,0


# access_hr_user_proactive_notification,proactive.notification,model_proactive_notification,base.group_user,1,1,1,0
# access_hr_user_proactive_line,proactive.line,model_proactive_line,base.group_user,1,1,1,0

# access_contract_department_history,contract.department.history,model_contract_department_history,base.group_user,1,1,1,1
# access_contract_company_history,contract.company.history,model_contract_company_history,base.group_user,1,1,1,1


# access_hr_employee_location_manager,hr.employee.location,model_hr_employee_location,nomin_base.group_config_manager,1,1,1,1
# access_hr_employee_location_hr_user,hr.employee.location,model_hr_employee_location,base.group_hr_manager,1,0,0,0
# access_hr_employee_location_user,hr.employee.location,model_hr_employee_location,base.group_user,1,0,0,0
# access_hr_employee_location_line_manager,hr.employee.location.line,model_hr_employee_location_line,nomin_base.group_config_manager,1,1,1,1
# access_hr_employee_location_line_hr_user,hr.employee.location.line,model_hr_employee_location_line,base.group_hr_manager,1,0,0,0
# access_hr_employee_location_line_user,hr.employee.location.line,model_hr_employee_location_line,base.group_user,1,0,0,0
