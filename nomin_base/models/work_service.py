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

class WorkServiceTime(models.Model):
    """ Тарифт ажлын хугацаа"""
    _name = 'work.service.time'
    _description = 'Time Range'
    
    name = fields.Char(string='Name', size=64, required=True)
    worktime = fields.Integer(string='Work Time', required=True, default=1)
    
class WorkServiceMeasurement(models.Model):
    """ Хэмжих нэгж бүртгэх"""
    _name = 'work.service.measurement'
    _description = 'Measurement'
    
    name = fields.Char(string='Name', size=64, required=True , track_visibility='onchange')
    measurement = fields.Integer(string='Measurement',track_visibility='onchange')
    
class WorkService(models.Model):
    """ Тарифт ажил """
    
    _name = 'work.service'
    _description = "Work Service"
    _order = "id desc"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    name = fields.Char(string='Name', required=True, size=128,track_visibility='onchange')
    department_id = fields.Many2one('hr.department', string='Department',track_visibility='onchange')
    amount = fields.Float(string='Regular Internal Amount', default=0.0, required=True,track_visibility='onchange')
    time_id = fields.Many2one('work.service.time', string='Time Range', required=True,track_visibility='onchange')
    active = fields.Boolean('Active', default=1,track_visibility='onchange')
    measurement = fields.Many2one('work.service.measurement',string='Measurement',track_visibility='always')
    active = fields.Boolean('Active', default=True, track_visibility='onchange')
    
    @api.constrains('name')
    def _check_name(self):
        if self.name:
            self._cr.execute("select count(id) from helpdesk_default where name = %s "
                       "and id <> %s",(self.name,self.id))
            fetched = self._cr.fetchone()
            if fetched and fetched[0] and fetched[0] > 0:
                raise UserError(_('The name already exists'))
    