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
from openerp.tools import exception_to_unicode
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)



class CctSyncUserLine(models.Model):
	_name='cct.sync.user.line'


	check_field = fields.Boolean(string=' ',default = True)
	user_id = fields.Many2one('res.users',string=u"Хэрэглэгч")
	sync_id = fields.Many2one('cct.sync',string="Контакт календар")  
	datetime = fields.Datetime(string='From erp last sync datetime')  
	to_erp_last_sync_datetime = fields.Datetime(string='To erp last sync datetime')  
 	# @api.multi
	def action_sync(self, cr, uid, ids,context=None):
		gCalendar_obj =self.pool.get('google.calendar')
		for sync in self.browse(cr, uid, ids):
			try:
				resp = gCalendar_obj.synchronize_events(cr,sync.user_id.id, False, lastSync=True, context=None)
				if resp.get("status") == "need_reset":
					_logger.info("[%s] Calendar Synchro - Failed - NEED RESET  !" % sync.user_id.id)
				else:
					update = "update calendar_sync_user_line set datetime='%s' where id =%s"%(datetime.now(),sync.id)
					cr.execute(update)
					_logger.info("[\n\n%s] Calendar Synchro - Done with status : %s  !\n\n" % (sync.user_id.id, resp.get("status")))
			except Exception, e:
								_logger.info("\n\n [%s] Calendar Synchro - Exception : %s !" % (sync.user_id.id, exception_to_unicode(e)))


class CctSyncInboundUserLine(models.Model):
	_name='cct.sync.inbound.user.line'

	check_field = fields.Boolean(string=' ',default = True)
	user_id = fields.Many2one('res.users',string=u"Хэрэглэгч")
	sync_id = fields.Many2one('cct.sync',string="Контакт календар")  
	datetime = fields.Datetime(string='From erp last sync datetime')  
	to_erp_last_sync_datetime = fields.Datetime(string='To erp last sync datetime')  
 	# @api.multi
	def inbound_action_sync(self, cr, uid, ids,context=None):
		gCalendar_obj =self.pool.get('google.calendar')
		for sync in self.browse(cr, uid, ids):
			try:
				resp = gCalendar_obj.synchronize_events(cr,sync.user_id.id, False, lastSync=True, context=None)
				if resp.get("status") == "need_reset":
					_logger.info("[%s] Calendar Synchro - Failed - NEED RESET  !" % sync.user_id.id)
				else:
					update = "update calendar_sync_user_line set datetime='%s' where id =%s"%(datetime.now(),sync.id)
					cr.execute(update)
					_logger.info("[\n\n%s] Calendar Synchro - Done with status : %s  !\n\n" % (sync.user_id.id, resp.get("status")))
			except Exception, e:
								_logger.info("\n\n [%s] Calendar Synchro - Exception : %s !" % (sync.user_id.id, exception_to_unicode(e)))



class CctSyncOutboundUserLine(models.Model):
	_name='cct.sync.outbound.user.line'

	user_id = fields.Many2one('res.users',string=u"Хэрэглэгч")
	sync_id = fields.Many2one('cct.sync',string="Контакт календар")  
	datetime = fields.Datetime(string='From erp last sync datetime')  
	to_erp_last_sync_datetime = fields.Datetime(string='To erp last sync datetime')  
 	# @api.multi
	def outbound_action_sync(self, cr, uid, ids,context=None):
		gCalendar_obj =self.pool.get('google.calendar')
		for sync in self.browse(cr, uid, ids):
			try:
				resp = gCalendar_obj.synchronize_events(cr,sync.user_id.id, False, lastSync=True, context=None)
				if resp.get("status") == "need_reset":
					_logger.info("[%s] Calendar Synchro - Failed - NEED RESET  !" % sync.user_id.id)
				else:
					update = "update calendar_sync_user_line set datetime='%s' where id =%s"%(datetime.now(),sync.id)
					cr.execute(update)
					_logger.info("[\n\n%s] Calendar Synchro - Done with status : %s  !\n\n" % (sync.user_id.id, resp.get("status")))
			except Exception, e:
								_logger.info("\n\n [%s] Calendar Synchro - Exception : %s !" % (sync.user_id.id, exception_to_unicode(e)))

class CctSyncEmpLine(models.Model):
	_name= 'cct.sync.emp.line'

	user_id = fields.Many2one('hr.employee',string=u"Ажилчдын нэр")
	job_id = fields.Many2one('hr.job',string="Албан тушаал")  



class CctSync(models.Model):
	_name = 'cct.sync'
	_description = 'Calendar sync Configure'
	_inherit = ['mail.thread', 'ir.needaction_mixin']

	@api.multi
	def _set_name(self):
		for sync in self:
			sync.name="Google calendar sync"
	name = fields.Char(string="Name",required=True)
	line_ids = fields.One2many('cct.sync.user.line','sync_id',string='Calendar sync')
	inbound_line_ids = fields.One2many('cct.sync.inbound.user.line','sync_id',string='Calendar sync')
	user_line_ids =  fields.One2many('cct.sync.emp.line','user_id',string= 'emp')
	outbound_line_ids = fields.One2many('cct.sync.outbound.user.line','sync_id',string='Calendar sync')

 	# def _calendar_sync_cron(self, cr, uid):
	# 	query = "select A.user_id,A.id from calendar_sync_user_line A inner join res_users B on A.user_id=B.id where B.google_calendar_last_sync_date is not null order by B.google_calendar_last_sync_date desc"
	# 	cr.execute(query)
	# 	records = cr.dictfetchall()
	# 	gCalendar_obj =self.pool.get('google.calendar')
	# 	_logger.info("\nCalendar Synchro - Starting synchronization")
	# 	if records:
	# 		for record in records:
	# 			_logger.info("Calendar Synchro - Starting synchronization for a new user [%s] " % record['user_id'])
	# 			try:
	# 				resp = gCalendar_obj.synchronize_events(cr,record['user_id'], False, lastSync=True, context=None)
	# 				if resp.get("status") == "need_reset":
	# 					_logger.info("[%s] Calendar Synchro - Failed - NEED RESET  !" % 	record['user_id'])
	# 				else:
						
	# 					update = "update calendar_sync_user_line set datetime='%s' where id =%s"%(datetime.now(),record['id'])
	# 					cr.execute(update)
	# 					_logger.info("[\n\n%s] Calendar Synchro - Done with status : %s  !\n\n" % (	record['user_id'], resp.get("status")))
	# 			except Exception, e:
	# 				_logger.info("\n\n [%s] Calendar Synchro - Exception : %s !" % (	record['user_id'], exception_to_unicode(e)))
	# 		_logger.info("\n\nCalendar Synchro - Ended by cron")
	# 	_logger.info("\n\nCalendar Synchro - Endining synchronization")

	@api.multi

	def user_action_sync(self):
		employees = self.env['hr.employee'].search([('register_type','=','employee')])
		# print '\n\n\n employee' , employees
		for employee in employees:
			if employee and employee.job_id:
				employee.job_id == "3773"
				print '\n\n\ffffffff' , employee ,employee.job_id
				# qry =('insert into cct_sync_emp_line (user_id,job_id) values(%s,%s)') %(employee.id ,employee.job_id.id)
				# print 'qry',qry
				# self.env.cr.execute(qry)





	@api.multi
	def action_add_users(self):
		
		user_ids = []
		for line in self.line_ids:
				user_ids.append(line.user_id.id)
		self.handle_users(user_ids,'cct_sync_user_line')

		inbound_user_ids = []
		for line in self.inbound_line_ids:
				inbound_user_ids.append(line.user_id.id)
		
		outbound_user_ids = []
		for line in self.outbound_line_ids:
				outbound_user_ids.append(line.user_id.id)
		self.handle_users(outbound_user_ids,'cct_sync_outbound_user_line')
		
		


		# user_ids = []
		# for line in self.line_ids:
		# 		user_ids.append(line.user_id.id)

		# job_ids = self.env['hr.job'].search([('job_level','=','administration')])

		# domain = []
		# if user_ids:
		# 		domain=['&',('user_id','not in',user_ids)]
		# domain = domain + [('job_id','in',job_ids.ids)]



		# employee_ids = self.env['hr.employee'].search(domain)
		# for employee in employee_ids:
			

					
		# 	qry =( 'insert into cct_sync_user_line (user_id,sync_id) values(%s,%s)') %(employee.user_id.id ,self.id)
		# 	print 'qry',qry
		# 	self.env.cr.execute(qry)




		# domain = []
		# if user_ids:
		# 		domain=['&',('user_id','in',user_ids)]
		# domain = domain + ['&',('job_id','in',job_ids.ids),('active','=',False)]

		# employee_ids = self.env['hr.employee'].search(domain)
		# for employee in employee_ids:
				
		# 	qry = ( 'delete from cct_sync_user_line where user_id = %s and sync_id = %s') %(employee.user_id.id ,self.id)
		# 	print 'qry',qry
		# 	self.env.cr.execute(qry)



	def handle_users(self,user_ids,str1):
		

		job_ids = self.env['hr.job'].search([('job_level','=','administration')])

		domain = []
		if user_ids:
				domain=['&',('user_id','not in',user_ids)]
		domain = domain + [('job_id','in',job_ids.ids)]



		employee_ids = self.env['hr.employee'].search(domain)
		for employee in employee_ids:
			

			if employee.user_id:
				qry =( 'insert into '+str1+' (user_id,sync_id) values(%s,%s)') %(employee.user_id.id ,self.id)
				print 'qry',qry
				self.env.cr.execute(qry)



		domain = []
		if user_ids:
				domain=['&',('user_id','in',user_ids)]
		domain = domain + ['&',('job_id','in',job_ids.ids),('active','=',False)]

		employee_ids = self.env['hr.employee'].search(domain)
		for employee in employee_ids:

			if employee.user_id:
				qry = ( 'delete from '+str1+' where user_id = %s and sync_id = %s') %(employee.user_id.id ,self.id)
				print 'qry',qry
				self.env.cr.execute(qry)


				