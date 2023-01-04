# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.web.controllers.main import Database, db_list
import werkzeug.utils

class Database_restrict(Database):
    @http.route('/web/database/create', type='http', auth="none", methods=['POST'], csrf=False)
    def create(self, req, fields):

        # check if it is not first installation - restrict!

        dblist = db_list(req)
        if len(dblist) > 0:
            raise Exception('Not allowed')

        return super(Database_restrict, self).create(req, fields)

    @http.route('/web/database/selector', type='http', auth="none")
    def selector(self, **kw):
        #return self._render_template(manage=False)
        return werkzeug.utils.redirect('/web/login', 303)

    @http.route('/web/database/manager', type='http', auth="none")
    def manager(self, **kw):
        #return self._render_template()
        return werkzeug.utils.redirect('/web/login', 303)


    @http.route('/web/database/duplicate', type='http', auth="none", methods=['POST'], csrf=False)
    def duplicate(self, req, fields):
        #raise Exception('Not allowed')
        return werkzeug.utils.redirect('/web/login', 303)

    @http.route('/web/database/drop', type='http', auth="none", methods=['POST'], csrf=False)
    def drop(self, req, fields):
        #raise Exception('Not allowed')
        return werkzeug.utils.redirect('/web/login', 303)

    @http.route('/web/database/backup', type='http', auth="none", methods=['POST'], csrf=False)
    def backup(self, req, backup_db, backup_pwd, token):
        #raise Exception('Not allowed')
        return werkzeug.utils.redirect('/web/login', 303)

    @http.route('/web/database/restore', type='http', auth="none", methods=['POST'], csrf=False)
    def restore(self, req, db_file, restore_pwd, new_db):
        #raise Exception('Not allowed')
        return werkzeug.utils.redirect('/web/login', 303)

    @http.route('/web/database/change_password', type='http', auth="none", methods=['POST'], csrf=False)
    def change_password(self, req, fields):
        #raise Exception('Not allowed')
        return werkzeug.utils.redirect('/web/login', 303)

