# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from openerp import api, fields, models, _
from openerp.exceptions import UserError

class ir_attachment(models.Model):
    _inherit = 'ir.attachment'
    
    def check_budget_attach(self, model, id):
        self.env.cr.execute("select state from %s where id=%s"%(model,id))
        fetched = self.env.cr.fetchone()
        if fetched:
            return  fetched[0]
    
    @api.multi
    def unlink(self):
        self.check('unlink')

        # First delete in the database, *then* in the filesystem if the
        # database allowed it. Helps avoid errors when concurrent transactions
        # are deleting the same file, and some of the transactions are
        # rolled back by PostgreSQL (due to concurrent updates detection).
        for a in self:
            if a.res_model == 'payment.request' and a.res_id:
              #  payment = self.pool.get('payment.request').browse(cr, uid, a.res_id)
                state = self.check_budget_attach('payment_request', a.res_id)
                if state != 'draft':
                    raise UserError((u"Ноорог төлөвтэй баримтын хавсралтыг устгах боломжтой!"))
                
            if a.res_model == 'payment.request.transaction' and a.res_id:
                state = self.check_budget_attach('payment_request_transaction', a.res_id)
                if state != 'done':
                    raise UserError((u"Батлагдсан төлөвтэй баримтын хавсралтыг устгах боломжтой! %s"%(str(state))))
            
            if a.res_model == 'nomin.budget' and a.res_id:
                state = self.check_budget_attach('nomin_budget', a.res_id)
                if state != 'draft':
                    raise UserError((u"Ноорог төлөвтэй баримтын хавсралтыг устгах боломжтой!"))
            
            if a.res_model == 'account.cost.sharing' and a.res_id:
                state = self.check_budget_attach('account_cost_sharing', a.res_id)
                if state != 'draft':
                    raise UserError((u"Ноорог төлөвтэй баримтын хавсралтыг устгах боломжтой!"))
            
            if a.res_model == 'account.cost.sharing.ni' and a.res_id:
                state = self.check_budget_attach('account_cost_sharing_ni', a.res_id)
                if state != 'draft':
                    raise UserError((u"Ноорог төлөвтэй баримтын хавсралтыг устгах боломжтой!"))
                
            if a.res_model == 'nomin.other.budget' and a.res_id:
                state = self.check_budget_attach('nomin_other_budget', a.res_id)
                if state != 'draft':
                    raise UserError((u"Ноорог төлөвтэй баримтын хавсралтыг устгах боломжтой!"))
                
            if a.res_model == 'received.document' and a.res_id:
                state = self.check_budget_attach('received_document', a.res_id)
                if state != 'draft':
                    raise UserError((u"Ноорог төлөвтэй баримтын хавсралтыг устгах боломжтой!"))
                
            if a.res_model == 'send.document' and a.res_id:
                state = self.check_budget_attach('send_document', a.res_id)
                if state != 'draft':
                    raise UserError((u"Ноорог төлөвтэй баримтын хавсралтыг устгах боломжтой!"))
            if a.res_model == 'purchase.requisition' and a.res_id:
                state = self.check_budget_attach('purchase_requisition', a.res_id)
                if state != 'draft':
                    raise UserError((u"Ноорог төлөвтэй баримтын хавсралтыг устгах боломжтой!"))    
                
        to_delete = set(attach.store_fname for attach in self if attach.store_fname)
        res = super(ir_attachment, self).unlink()
        for file_path in to_delete:
            self._file_delete(file_path)

        return res
