# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
class contract_management(models.Model):
	_inherit = 'contract.management'
	'''
        Гэрээн дээр гэрээ зөрчсөн асуудал бүртгэх
    '''
	
	issue_ids = fields.One2many('project.issue','contract_id', string="Contract Issues")
class project_ticket(models.Model):
	_inherit = 'crm.helpdesk'
	'''
        Тусламжийн төв дээр Холбоотой ажлууд харуулах
    '''
	 
	task_ids =  fields.One2many('project.task','ticket_id', string=u"Даалгавар")
