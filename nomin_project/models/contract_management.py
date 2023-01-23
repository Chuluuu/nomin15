# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
class contract_management(models.Model):
	_name = 'contract.management'
	# TODO FIX LATER
	# _inherit = 'contract.management'
	'''
        Гэрээн дээр гэрээ зөрчсөн асуудал бүртгэх
    '''
	
	issue_ids = fields.One2many('project.issue','contract_id', string="Contract Issues")
# TODO FIX LATER
class ContractPerformance(models.Model):
	_name ='contract.performance'
# TODO FIX LATER
class PaymentRequest(models.Model):
	_name ='payment.request'

class project_ticket(models.Model):
	_name = "crm.helpdesk"
	# TODO FIX LATER
	# _inherit = 'crm.helpdesk'
	'''
        Тусламжийн төв дээр Холбоотой ажлууд харуулах
    '''
	 
	task_ids =  fields.One2many('project.task','ticket_id', string=u"Даалгавар")
