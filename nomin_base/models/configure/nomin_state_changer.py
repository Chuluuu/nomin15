# -*- encoding: utf-8 -*-


from openerp import api, fields, models
from openerp.exceptions import UserError

class NominStateChanger(models.TransientModel):
	_name ='nomin.state.changer'


	#('cost_share_out','Зардал хувиарлалт орлогогүй'),('cost_share_in','Зардал хувиарлалт орлоготой'),
	select_model = fields.Selection([('business_plan','Бизнес төлөвлөгөө'),('other_budget','Мөнгөн урсгалын төсөв'),
		('payment_request','Төлбөрийн хүсэлт'),('incash','Инкасс')],string="Модел")

	number = fields.Integer(string="Бүртгэлийн ID")
	active_sequence = fields.Integer(string="Дарааллын дугаар")
	sequence = fields.Integer(string="Дараалал")
	is_account_move_delete = fields.Boolean(string='Ажил гүйлгээ устгах')

	STATE_SELECTION_BUDGET = [
	('draft','Ноорог'),
	('confirm_branch','Салбарын эдийн засагч хянах'),
	('confirm_ceo','Гүйцэтгэх захирал батлах'),
	('confirm_bc','Бизнес эрхэлсэн захирал батлах'),
	('confirm_bde','БХГ-ийн эдийн засагч хянах'),
	('confirm_bdc','БХГ-ийн захирал хянах'),
	('confirm_group_ceo','Гүйцэтгэх захирал батлах'),
	('done','Батлагдсан'),
	('closed','Хаагдсан'),
	('cancelled','Цуцлагдсан')
	]

	business_plan_state = fields.Selection(STATE_SELECTION_BUDGET,string="Бизнес төлөвлөгөө")

	STATE_SELECTION_OTHER = [
	('draft','Ноорог'),
	('confirm_ceo','Салбарын захирал батлах'),
	('business_chief_verify','Бизнес эрхэлсэн захирал хянах'),
	('confirm_group_ceo','Гүйцэтгэх захирал батлах'),
	('done','Батлагдсан'),
	('closed','Хаагдсан'),
	('cancelled','Цуцлагдсан')
	]

	nomin_other_state = fields.Selection(STATE_SELECTION_OTHER,string="Мөнгөн урсгалын төсөв")


	STATE_SELECTION_PAYMENT = [
	('draft','Ноорог'),
	('dep_account_verify','Салбарын нягтлан хянах'),
	('dep_chiep_verify','Салбарын захирал хянах'),
	('business_chief_verify','Бизнес эрхэлсэн захирал хянах'),
	('holding_ceo_verify','Холдингийн гүйцэтгэх захирал хянах'),
	('done','Батлагдсан'),
	('transfers','Шилжүүлсэн'),
	('cancel','Цуцлагдсан')
	]

	payment_request_state = fields.Selection(STATE_SELECTION_PAYMENT,string="Төлбөрийн хүсэлт")

	STATE_SELECTION_INCASH = [
	('draft','Ноорог'),
	('send','илгээдсэн'),
	('received','Хүлээн авсан'),
	('send1','Салбарын захиралд илгээгдсэн'),
	('send2','Салбарын нягтланд илгээгдсэн'),
	('confirmed','Батлагдсан'),
	('paid','Төлөгдсөн'),
	('refused','Буцаагдсан')
	]


	cost_share_line_state = fields.Selection(STATE_SELECTION_INCASH,string="Инкасс")


	@api.multi
	def check_sequence(self):
		values= {}
		if self.select_model=="business_plan":
			if self.number==0:
				raise UserError((u'%s id тай Бизнес төлөвлөгөө олдсонгүй !')%self.number)
			budget_id = self.env['nomin.budget'].search([('id','=',self.number)])
			if budget_id:
				self.write({'sequence':budget_id.active_sequence})
			else:
				raise UserError((u'%s id тай Бизнес төлөвлөгөө олдсонгүй !')%self.number)
		elif self.select_model=="other_budget":
			if self.number==0:
				raise UserError((u'%s id тай Мөнгөн урсгалын төсөв олдсонгүй !'))
			budget_id = self.env['nomin.other.budget'].search([('id','=',self.number)])
			if budget_id:
				self.write({'sequence':budget_id.active_sequence})
			else:
				raise UserError((u'%s id тай Мөнгөн урсгалын төсөв олдсонгүй !'))
		elif self.select_model=="payment_request":
			if self.number==0:
				raise UserError((u'%s id тай Төлбөрийн хүсэлт олдсонгүй !')%self.number)
			budget_id = self.env['payment.request'].search([('id','=',self.number)])
			if budget_id:
				self.write({'sequence':budget_id.active_sequence})
			else:
				raise UserError((u'%s id тай Төлбөрийн хүсэлт олдсонгүй !'))
		elif self.select_model=="incash":
			if self.number==0:
				raise UserError((u'%s id тай Инкасс олдсонгүй !'))
			budget_id = self.env['account.cost.sharing.line'].search([('id','=',self.number)])
			if budget_id:
				self.write({'sequence':budget_id.active_sequence})
			else:
				raise UserError((u'%s id тай Инкасс олдсонгүй !'))
		return {
		"type": "set_scrollTop",
		}
	@api.multi
	def action_set(self):
		values= {}
		move_ids = []
		if self.select_model=="business_plan":
			if self.number==0:
				raise UserError((u'%s id тай Бизнес төлөвлөгөө олдсонгүй !')%self.number)
			budget_id = self.env['nomin.budget'].search([('id','=',self.number)])
			if budget_id:
				if self.active_sequence>0:
					values.update({'active_sequence':self.active_sequence})
				if self.business_plan_state:
					values.update({'state':self.business_plan_state})
				budget_id.write(values)

			else:
				raise UserError((u'%s id тай Бизнес төлөвлөгөө олдсонгүй !')%self.number)
		elif self.select_model=="other_budget":
			if self.number==0:
				raise UserError((u'%s id тай Мөнгөн урсгалын төсөв олдсонгүй !'))
			budget_id = self.env['nomin.other.budget'].search([('id','=',self.number)])
			if budget_id:
				if self.active_sequence>0:
					values.update({'active_sequence':self.active_sequence})
				if self.nomin_other_state:
					values.update({'state':self.nomin_other_state})
				budget_id.write(values)
			else:
				raise UserError((u'%s id тай Мөнгөн урсгалын төсөв олдсонгүй !'))
		elif self.select_model=="payment_request":
			if self.number==0:
				raise UserError((u'%s id тай Төлбөрийн хүсэлт олдсонгүй !')%self.number)
			budget_id = self.env['payment.request'].search([('id','=',self.number)])
			if budget_id:
				if self.active_sequence>0:
					values.update({'active_sequence':self.active_sequence})
				if self.payment_request_state:
					values.update({'state':self.payment_request_state})
				budget_id.write(values)
				if self.is_account_move_delete:

					for move_line in budget_id.account_move_line_ids:
						move_ids.extend([move_line.move_id])
					move_ids = list(set(move_ids))
					if move_ids:
						for move in move_ids:
							move.button_cancel_call()
							move.unlink()
			else:
				raise UserError((u'%s id тай Төлбөрийн хүсэлт олдсонгүй !'))
		elif self.select_model=="incash":
			if self.number==0:
				raise UserError((u'%s id тай Инкасс олдсонгүй !'))
			budget_id = self.env['account.cost.sharing.line'].search([('id','=',self.number)])
			if budget_id:
				if self.active_sequence>0:
					values.update({'active_sequence':self.active_sequence})
				if self.cost_share_line_state:
					values.update({'state':self.cost_share_line_state})
				budget_id.write(values)
				if self.is_account_move_delete:
					budget_id.incash_button_cancel()

					for move_line in budget_id.account_move_line_incash_ids:
						move_ids.append(move_line.move_id)
					move_ids = list(set(move_ids))
					if move_ids:
						for move in move_ids:
							move.button_cancel_call()
							move.unlink()
			else:
				raise UserError((u'%s id тай Инкасс олдсонгүй !'))