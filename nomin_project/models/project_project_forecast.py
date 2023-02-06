# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError
from odoo.osv import expression
from operator import itemgetter

class ProjectProjectForecast(models.TransientModel):
	_name = 'project.project.forecast'	
	_order = "create_date desc"

	name = fields.Char(string="Name",related="project_id.name")
	project_id = fields.Many2one('project.project', string="Project")
	task_ids = fields.One2many('project.forecast.task', 'forecast_id',string="Project tasks")
	date_from = fields.Date(string="Task Date from")
	date_to = fields.Date(string="Task Date to")
	task_state = fields.Selection([
                                   ('t_new' ,u'Шинэ'),
                                   ('t_cheapen',u'Үнэ тохирох'),
                                   ('t_cheapened',u'Үнэ тохирсон'),
                                   ('t_user',u'Хариуцагчтай'),
                                   ('t_start',u'Хийгдэж буй'),
                                   ('t_control',u'Хянах'),
                                   ('t_confirm',u'Батлах'),
                                   ('t_evaluate',u'Үнэлэх'),
                                   ('t_done',u'Дууссан'),
                                   ('t_cancel',u'Цуцалсан'),
                                   ('t_back',u'Хойшлуулсан')],string='State')
	user_id = fields.Many2one('res.users',string="Responsible")

	@api.model
	def default_get(self, fields):
		res = super(ProjectProjectForecast, self).default_get(fields) 
		context = dict(self._context or {})   
		active_id = context and context.get('active_id', False) or False        
		
		if active_id:
			res.update({
						'project_id' : active_id
						})
		return res



	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = ['|', ('code', '=ilike', name + '%'),('name', operator, name)]
			if operator in expression.NEGATIVE_TERM_OPERATORS:
				domain = ['&'] + domain
		ProjectProjectForecast = self.search(domain + args, limit=limit)
		return ProjectProjectForecast.name_get()

	@api.onchange('project_id','task_state','date_from','date_to')
	def onchange_project(self):		
		if self.project_id:			
			domain = [('project_id','=',self.project_id.id)]
			if self.task_state:
				domain =domain +[('task_state','=',self.task_state)]
			if self.date_from:
				domain =domain +[('task_date_start','<=',self.date_from)]
			if self.date_to:
				domain =domain +[('date_deadline','>=',self.date_to)]
			
			if self.user_id:
				domain =domain +[('user_id','=',self.user_id)]
			
			task_ids = self.env['project.task'].sudo().search(domain)
			tasks = []
			if task_ids:
				for task in task_ids:
					tasks.append((0,0,{'task_id':task.id,'project_id':task.project_id.id}))
				# if tasks:				
				
				self.update({'task_ids':tasks})
			else:
				raise ValidationError(_(u'Даалгаврууд олдсонгүй'))


class ProjectForecastTask(models.TransientModel):
	_name = 'project.forecast.task'

	task_id = fields.Many2one('project.task', string="")
	project_id = fields.Many2one('project.project', string="Project")
	forecast_id = fields.Many2one('project.project.forecast', string="Project forecast")


	@api.model
	def get_line_values(self, line_ids):
		lines = []
		roots ={}
		# where =""
		
		# if len(line_ids)>1:
		# 	where=where+"where id in %s"%(str(tuple(line_ids)))
		# else:				
		# 	where=where+"where id = %s"%(str(line_ids[0]))            		
		# query ="WITH RECURSIVE child_projects (id,parent_project) AS ( SELECT id,parent_project	FROM project_project WHERE parent_project = (select project_id from project_task  %s group by project_id) \
		# 		UNION SELECT A.*, B.parent_project,D.name as user_name FROM project_project A INNER JOIN child_projects B ON B.parent_project = A.id ) select A.*,B.parent_project from project_task A \
		# 		LEFT join res_users C ON C.id=A.user_id INNER join child_projects as B ON B.id=A.project_id order by B.parent_project desc, A.parent_task desc"%where
            
		# self.env.cr.execute(query)
		# dictfetchall = self.env.cr.dictfetchall()
		if line_ids and type(line_ids)==list and type(line_ids[0])==int:
			
			line_objs = self.env['project.task'].search([('id','in',line_ids)],order ='parent_task desc')
			group_colors = ['ggroupblack','gmilestone','gtaskblue','gtaskred','gtaskyellow','gtaskpurple','gtaskpink']
			if line_objs:
				count=1
				for line in line_objs:
					
					if line not in roots:
						roots[line]= {
							'root':str(count),
							'user':line.user_id.name,						
							'root_length':1,
							'department':line.department_id.name,
							'project':line.project_id.name,
							'task':line.name,
							'planned_date_start':line.task_date_start,
							'planned_date_end':line.date_deadline,
							'done_date':line.done_date,
							'complete_percent':line.flow,
							'description':line.description or '',
							'group_color':'gtaskblue',
							'expand':0,
							'parent_task':0,
						}
						root = str(count)
						if line.parent_task:
							if line.parent_task not in roots:
								roots[line.parent_task]= {
									'root':str(count),
									'root_length':1,
									'user':line.parent_task.user_id.name,
									'department':line.parent_task.department_id.name,
									'project':line.parent_task.project_id.name,
									'task':line.parent_task.name,
									'planned_date_start':'',
									'planned_date_end':'',
									'done_date':'',
									'expand':1,
									'parent_task':0,
									'complete_percent':0,
									'description':line.parent_task.description or '',
									'group_color':'ggroupblack',
								}
								if count==9:
									count=1000
								else:
									count=count+1
							roots[line.parent_task]['planned_date_start']= ''
							roots[line.parent_task]['planned_date_end']= ''
							roots[line.parent_task]['done_date']= ''
							roots[line.parent_task]['complete_percent']= 0
							roots[line.parent_task]['group_color']= 'ggroupblack'
							root = roots[line.parent_task]['root']+str(roots[line.parent_task]['root_length'])						
							roots[line.parent_task]['root_length']= roots[line.parent_task]['root_length']+1					
							roots[line]['parent_task'] = roots[line.parent_task]['root']
						else:
							if count==9:
								count=1000
							else:
								count=count+1
						if line.done_date and line.done_date> line.date_deadline:
							roots[line]['group_color'] = "gtaskred"
						roots[line]['root']=root					
				for root in sorted(roots.values(), key=itemgetter('root')):				
					# vals = {
					# 	'user':root['user'],		
					# 	'roots':root['root'],
					# 	'parent_task':root['parent_task'],
					# 	'department':root['department'],
					# 	'project':root['project'],
					# 	'task':root['task'],
					# 	'expand':root['expand'],
					# 	'planned_date_start':root['planned_date_start'],
					# 	'planned_date_end':root['planned_date_end'],
					# 	'done_date':root['done_date'],
					# 	'complete_percent':root['complete_percent'],
					# 	'description':root['description'],
					# 	'group_color':root['group_color'],						
					# }
					vals = {
						'pID':root['root'],
						'pName':root['task'],
						'pStart':root['planned_date_start'],
						'pEnd':root['planned_date_end'],
						'pClass':root['group_color'],					
						'pLink':root['task'],
						'pMile':0,
						'pRes':root['user'],
						'pComp':root['complete_percent'],
						'pGroup':0,
						'pParent':root['parent_task'],
						'pOpen': 1,
						'pDepend': 0,
						'pCaption': 0,					
						'pNotes': root['description'],					
											
					}

					lines.append(vals)
	
		return lines

