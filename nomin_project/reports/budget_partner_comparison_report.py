# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-Today OpenERP SA (<http://www.openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.addons.l10n_mn_report_base.report_helper import verbose_numeric, comma_me, convert_curr
from operator import itemgetter
from openerp.exceptions import UserError, ValidationError
# import logging
# _logger = logging.getLogger(__name__)
# from operator import itemgetter
# from openerp.osv import osv

class PrintOrderRequest(models.AbstractModel):
    """
          Захиалгын баримт
    """
    _name = 'report.nomin_project.budget_partner_comparison_report'


    @api.multi
    def render_html(self, data):
        report = self.env['report']._get_report_from_name('nomin_project.budget_partner_comparison_report')

        budget_partner_obj = self.env['budget.partner.comparison']
        budget_partners = budget_partner_obj.sudo().browse(self.id)
        members = {}
        partners = {}
        winners = {}
        partner_comparison_name = u"СОНГОН ШАЛГАРУУЛАЛТЫН ТАЙЛАН" 

        for budget_partner in budget_partners:
            line = {}
            committee_members = {}
            if budget_partner.state in ('draft','quotation','end_quotation'):
                raise UserError(_('Үнийн харьцуулалт хийх төлвөөс хойш ажлын гүйцэтгэгч сонгох тайлан татах боломжтой.'))

            for participant in budget_partner.participants_ids:
                if participant.id not in line:
                    line[participant.id] = {'partner_id': participant.partner_id.name or '',
                                'price': participant.price_amount or '',
                                'price_percent': participant.price_percent or '',
                                'document':participant.document_id or '',
                                'is_winner':participant.is_winner or False,
                                'total_votes':0,
                                }
                # CHULUU
                if participant.partner_id not in winners and participant.is_winner:
                    winners[participant.partner_id] = {'partner_id': participant.partner_id.name or '',
                                'price': participant.price_amount or '',
                                'price_percent': participant.price_percent or '',
                                'document':participant.document_id or '',
                                'is_winner':participant.is_winner or '',
                                'total_votes':0,
                                }
                members[budget_partner.id] = sorted(line.values(), key=itemgetter('partner_id'))
                
            for committee_member in budget_partner.committee_member_ids:
                if committee_member.id not in committee_members:
                    committee_members[committee_member.id] = {'name': committee_member.employee_id.name or '',
                                'employee_id': committee_member.employee_id or '',
                                'vote_date': committee_member.vote_date or '',
                                'partner':committee_member.partner_id.name or '',
                                'job':committee_member.employee_id.job_id.name or '',
                                }
                if committee_member.partner_id in winners and winners[committee_member.partner_id]['is_winner']:
                    winners[committee_member.partner_id]['total_votes']+=1
                partners[budget_partner.id] = sorted(committee_members.values(), key = itemgetter('name'))
        docargs = {
                   'lines': members,
                   'winners': winners,
                   'partners': partners,
                   'budget_partners': budget_partners,
                   'partner_comparison_name': partner_comparison_name,
        }
        return self.env['report'].render('nomin_project.budget_partner_comparison_report', docargs)
