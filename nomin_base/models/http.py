from openerp import http


def ignored_session_gc(session_store):
    ''' ignore this action for performance'''
    if random.random() < 0.001:
       # we keep session one week
       last_week = time.time() - 60*60*24*7
       for fname in os.listdir(session_store.path):
           path = os.path.join(session_store.path, fname)
           try:
               if os.path.getmtime(path) < last_week:
                   os.unlink(path)
           except OSError:
               pass
    pass


http.session_gc = ignored_session_gc