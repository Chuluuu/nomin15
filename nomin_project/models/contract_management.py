# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
class contract_management(models.Model):	
	_inherit = 'contract.management'
	'''
        Гэрээн дээр гэрээ зөрчсөн асуудал бүртгэх
    '''
	issue_ids = fields.One2many('project.issue','contract_id', string="Contract Issues")
	# TODO FIX LATER REmove project_id 
	project_id = fields.Many2one('project.project', stirng="Project")
class ContractPerformance(models.Model):
	# TODO FIX LATER
	# _inherit = 'contract.performance'
	_name ='contract.performance'
	contract_id = fields.Many2one('contract.management',string="Contract")
	state =  fields.Selection(selection=[('draft',u'Ноорог'), 
                                ('sent',u'Илгээгдсэн'), 
                                ('approved',u'Зөвшөөрсөн'),
                                ('confirmed',u'Баталсан'),
                                ('modified',u'Тодотгосон'),
                                ('rejected',u'Татгалзсан'),
                                ('closed',u'Хаагдсан'),
                                ],
                                string = 'State',  copy=False, default='draft', tracking=True)
class PaymentRequest(models.Model):
	# TODO FIX LATER
	_name = 'payment.request'

class project_ticket(models.Model):
	_name = "crm.helpdesk"
	# TODO FIX LATER
	# _inherit = 'crm.helpdesk'
	'''
        Тусламжийн төв дээр Холбоотой ажлууд харуулах
    '''
	 
	task_ids =  fields.One2many('project.task','ticket_id', string=u"Даалгавар")
