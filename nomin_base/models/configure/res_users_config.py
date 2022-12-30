# -*- encoding: utf-8 -*-

from openerp import fields, models, _
from openerp.exceptions import UserError
from openerp import api, fields, models

class ResUsersConfig(models.Model):
	_name = 'res.users.config'
	_description = 'res.users.config'
	_inherit = 'mail.thread'

	job_id = fields.Many2one('hr.job',string="Албан тушаал" , track_visibility='always')
	#group_ids = fields.Many2many(comodel_name='res.groups',string="Грүппүүд")	
	group_ids = fields.Many2many('res.groups','res_groups_res_users_config_rel','res_users_config_id','res_groups_id',string="Грүппүүд" , track_visibility='always')    

	_sql_constraints = [
	('job_id_uniq', 'unique(job_id)', 'Тохируулагдсан албан тушаал байна!')
	]


	line_ids  = fields.One2many('res.users.config.line','config_id', string="Config line")


class ResUsersConfigLine(models.Model):
	_name = 'res.users.config.line'
	_description = "Res users config line"

	config_id = fields.Many2one('res.users.config', string="Res users config" ,ondelete='cascade')
	department_id = fields.Many2one('hr.department' , string='Хэлтэс' , track_visibility='always')
	group_ids = fields.Many2many('res.groups',string="Нэмэлт грүппүүд")
	allowed_resources = fields.Many2many('ir.model.fields',string = 'Хандах нөөц', domain="[('model','=','res.users'),('name','like','allowed')]" ,track_visibility='always' )
	project_allowed_departments = fields.Many2many('hr.department','res_users_project_dep_rel','user_id','dep_id',string='Project Allowed Departments',track_visibility='always')	
	payment_request_departments = fields.Many2many('hr.department','res_users_payment_req_rel','user_id','dep_id',string='Payment_Request Allowed Departments',track_visibility='always')	
	budget_allowed_departments = fields.Many2many('hr.department','res_users_budget_dep_rel','user_id','dep_id',string='Budget Allowed Departments',track_visibility='always')	
	delivery_allowed_departments = fields.Many2many('hr.department','res_users_delivery_dep_rel','user_id','dep_id',string='Delivery Allowed Departments',track_visibility='always')	
	hr_allowed_departments = fields.Many2many('hr.department','res_users_hr_dep_rel','user_id','dep_id',string='Hr Allowed Departments',track_visibility='always')	
	helpdesk_allowed_departments = fields.Many2many('hr.department','res_users_helpdesk_dep_rel','user_id','dep_id',string='Helpdesk Allowed Departments',track_visibility='always')	
	tender_allowed_departments = fields.Many2many('hr.department','res_users_tender_dep_rel','user_id','dep_id',string='Tender Allowed Departments',track_visibility='always')	
	archive_allowed_departments = fields.Many2many('hr.department','res_users_archive_dep_rel','user_id','dep_id',string='Archive Allowed Departments',track_visibility='always')	
	allowed_departments = fields.Many2many('hr.department','res_users_dep_rel','user_id','dep_id',string='Allowed Departments',track_visibility='always')	
	purchase_allowed_departments = fields.Many2many('hr.department','res_users_purchase_dep_rel','user_id','dep_id',string='Purchase Allowed Departments',track_visibility='always')	
	loans_request_allowed_departments = fields.Many2many('hr.department','res_users_loans_req_rel','user_id','dep_id',string='Loans Request Allowed Departments',track_visibility='always')	
	asset_lease_allowed_departments = fields.Many2many('hr.department', 'res_users_asset_lease_dep_rel', 'user_id', 'dep_id', 'Asset Lease Allowed Departments',track_visibility='always')
	logistic_allowed_departments = fields.Many2many('hr.department','res_users_logistic_dep_rel','user_id','dep_id',string='Logistic Allowed Departments',track_visibility='always')		
	salary_see_allowed_departments = fields.Many2many('hr.department','res_users_pay_see_dep_rel','user_id','dep_id','HR-Allowed Departments',track_visibility='always')
	regulation_confirm_allowed_departments = fields.Many2many('hr.department','res_users_hr_regulation_dep_rel','user_id','dep_id','HR-Regulation Departments',track_visibility='always')
	

	@api.multi
	def _check_department_id(self):
		normal = True
		for current_self in self:
			line_ids = current_self.env['res.users.config.line'].search([('config_id','=',current_self.config_id.id),('id','!=',current_self.id)])
			for line in line_ids:			
				if line.department_id == current_self.department_id:
					normal = False
		return normal

	# _constraints = [
    #     (_check_department_id, u'Хэлтэс давхардуулж болохгүй', ['department_id']),
    # ]



	def action_add_department(self,result):
		department_id = result.department_id.id
		sector_id = self.env['hr.department'].get_sector(department_id)
		# remove_resources = []
		# remove_resources_list = []	 

		# config_id = self.env['to.forbid.config'].browse(1)

		remove_resources = []
		# remove_resources_list = []	
		# allow_resources = []

		config_id = self.env['to.forbid.config'].search([(1,'=',1)],limit=1)
		
		# config_id = self.env['to.forbid.config'].browse(1)
		if not result.config_id.group_ids:
			
			result.config_id.write({'group_ids':[(6,0,config_id.group_ids.ids)]})
		
		forbid_config = self.env['to.forbid.config.line'].search([('job_id','=',result.config_id.job_id.id)])
		
		if forbid_config:
			if not result.config_id.job_id.below_than_stockkeeper:				

				for forbid_resource in forbid_config.forbidden_resources:
					if forbid_resource in config_id.sector_allowed_resources:
						remove_resources.append(forbid_resource)
				allow_resources = list(set(config_id.sector_allowed_resources) - set(remove_resources))
				if allow_resources:
					for resource in allow_resources:
						result.write({resource.name:[(4,sector_id)],
									'allowed_resources':[(4,resource.id)]		
									})

				for forbid_resource in forbid_config.forbidden_resources:	
					if forbid_resource in config_id.department_allowed_resources:
						remove_resources.append(forbid_resource)

				allow_resources = list(set(config_id.department_allowed_resources) - set(remove_resources))
				if allow_resources:
					for resource in allow_resources:
						result.write({resource.name:[(4,department_id)],
										'allowed_resources':[(4,resource.id)]										
								})
											
									

			else:

				
				for forbid_resource in forbid_config.forbidden_resources:
					if forbid_resource in config_id.sector_allowed_resources_below:
						remove_resources.append(forbid_resource)
				allow_resources = list(set(config_id.sector_allowed_resources_below) - set(remove_resources))
				if allow_resources:
					for resource in allow_resources:
						result.write({resource.name:[(4,sector_id)],
									'allowed_resources':[(4,resource.id)]		
									})
				for forbid_resource in forbid_config.forbidden_resources:
					if forbid_resource in config_id.department_allowed_resources_below:
						remove_resources.append(forbid_resource)
				allow_resources = list(set(config_id.department_allowed_resources_below) - set(remove_resources))
				if allow_resources:	
					for resource in allow_resources:
						result.write({resource.name:[(4,department_id)],
							'allowed_resources':[(4,resource.id)]										
						})
	
		else:
			raise UserError(_(u'Эрхийн ерөнхий тохиргоо хийгдээгүй байна'))
			

	
	@api.model
	def create(self, vals):	  

		result = super(ResUsersConfigLine, self).create(vals)


		self.action_add_department(result)

		return result

	@api.multi
	def write(self, vals):		

		result = super(ResUsersConfigLine, self).write(vals)

		if vals:
			if vals.get('department_id'): 

				self.action_add_department(self)
	
		return result




class ToForbidConfig(models.Model):
	_name = 'to.forbid.config'
	_description = 'to.forbid.config'
	_inherit = 'mail.thread'

	config_name = fields.Char(string="Ерөнхий тохиргооны нэр" , track_visibility="always")
	line_ids = fields.One2many('to.forbid.config.line', 'forbid_line_id',string='forbid config line' , track_visibility="always")
	
	group_ids = fields.Many2many('res.groups',string='Грүппүүд')
	sector_allowed_resources = fields.Many2many('ir.model.fields','ir_model_sector_resource','res_id','ir_id', string = 'Салбар тохируулах нөөц',  domain="[('model','=','res.users'),('name','like','allowed')]" )
	department_allowed_resources = fields.Many2many('ir.model.fields','ir_model_dep_resource','res_id','ir_id', string = 'Хэлтэс тохируулах нөөц', domain="[('model','=','res.users'),('name','like','allowed')]" )
	sector_allowed_resources_below = fields.Many2many('ir.model.fields','ir_model_sector_res_below','res_id','ir_id', string = 'Салбар тохируулах нөөц', domain="[('model','=','res.users'),('name','like','allowed')]" )
	department_allowed_resources_below = fields.Many2many('ir.model.fields','ir_model_dep_res_below','res_id','ir_id', string = 'Хэлтэс тохируулах нөөц', domain="[('model','=','res.users'),('name','like','allowed')]" )

	@api.model
	def create(self, vals):

		config_id = self.env['to.forbid.config'].search([(1,'=',1)])
		if config_id:
			raise UserError(_(u'2 тохиргоо үүсгэх боломжгүй'))
		return super(ToForbidConfig, self).create(vals)

class ToForbidConfigLine(models.Model):
    _name = 'to.forbid.config.line'
    _description = 'to forbid config line'
    _inherit = 'mail.thread'	
    
	
    forbid_line_id = fields.Many2one('to.forbid.config',string='To forbid config line' , ondelete='cascade')
    job_id = fields.Many2one('hr.job',string="Албан тушаал" , track_visibility="always")
    forbidden_resources = fields.Many2many('ir.model.fields',string = 'Хориг тавих нөөц', domain="[('model','=','res.users'),('name','like','allowed')]" )

    job_id = fields.Many2one('hr.job',string="Албан тушаал" , track_visibility='always')
    
    _sql_constraints = [
		('job_id_line_uniq', 'unique(job_id)', 'Тохируулагдсан албан тушаал байна !')
		]

