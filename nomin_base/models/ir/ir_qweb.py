#-*- coding:utf-8 -*-
# Author: Baskhuu.L

from dateutil.relativedelta import relativedelta as rdelta
from datetime import date, datetime
from openerp import tools, SUPERUSER_ID
from openerp.addons.base.ir.ir_qweb import AssetsBundle
from openerp.exceptions import QWebException
from openerp.osv import osv, orm, fields
import logging
_logger = logging.getLogger('nomin_base')

class AssetsBundle2(AssetsBundle):
    
    def clean_attachments(self, type):
        """ Takes care of deleting any outdated ir.attachment records associated to a bundle before
        saving a fresh one.

        When `type` is css we need to check that we are deleting a different version (and not *any*
        version) because css may be paginated and, therefore, may produce multiple attachments for
        the same bundle's version.

        When `type` is js we need to check that we are deleting a different version (and not *any*
        version) because, as one of the creates in `save_attachment` can trigger a rollback, the
        call to `clean_attachments ` is made at the end of the method in order to avoid the rollback
        of an ir.attachment unlink (because we cannot rollback a removal on the filestore), thus we
        must exclude the current bundle.
        """
        ira = self.registry['ir.attachment']
        dnow = datetime.now() - rdelta(days=7)
        _logger.info('cleaning attachment with modified before %s' % dnow.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT))
        domain = [
            ('create_date','<',dnow.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)),
            ('url', '=like', '/web/content/%-%/{0}%.{1}'.format(self.xmlid, type)),  # The wilcards are id, version and pagination number (if any)
            '!', ('url', '=like', '/web/content/%-{}/%'.format(self.version))
        ]

        attachment_ids = ira.search(self.cr, SUPERUSER_ID, domain, context=self.context)

        return ira.unlink(self.cr, SUPERUSER_ID, attachment_ids, context=self.context)

class IrQWeb(orm.AbstractModel):
    _inherit = 'ir.qweb'

    def render_tag_call_assets(self, element, template_attributes, generated_attributes, qwebcontext):
        """ This special 't-call' tag can be used in order to aggregate/minify javascript and css assets"""
        if len(element):
            # An asset bundle is rendered in two differents contexts (when genereting html and
            # when generating the bundle itself) so they must be qwebcontext free
            # even '0' variable is forbidden
            template = qwebcontext.get('__template__')
            raise QWebException("t-call-assets cannot contain children nodes", template=template)
        xmlid = template_attributes['call-assets']
        cr, uid, context = [getattr(qwebcontext, attr) for attr in ('cr', 'uid', 'context')]
        bundle = AssetsBundle2(xmlid, cr=cr, uid=uid, context=context, registry=self.pool)
        css = self.get_attr_bool(template_attributes.get('css'), default=True)
        js = self.get_attr_bool(template_attributes.get('js'), default=True)
        async = self.get_attr_bool(template_attributes.get('async'), default=False)
        return bundle.to_html(css=css, js=js, debug=bool(qwebcontext.get('debug')), async=async, qwebcontext=qwebcontext)
