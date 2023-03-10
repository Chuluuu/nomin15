
# -*- coding: utf-8 -*-

import operator
import json
import urllib2

import openerp
from openerp import tools
from openerp import SUPERUSER_ID
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, exception_to_unicode
from openerp.tools.translate import _
from openerp.http import request
from datetime import datetime, timedelta
from dateutil import parser
import pytz
from openerp.osv import fields, osv
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)
from openerp.addons.google_calendar.google_calendar import SyncEvent,NothingToDo,Create,Update,Exclude,Delete
def status_response(status):
    return int(str(status)[0]) == 2


class google_calendar(osv.AbstractModel):
    STR_SERVICE = 'calendar'
    _inherit = 'google.%s' % STR_SERVICE

    def generate_data(self, cr, uid, event, isCreating=False, context=None):
        if not context:
            context = {}
        if event.allday:
            start_date = event.start_date
            final_date = (datetime.strptime(event.stop_date, tools.DEFAULT_SERVER_DATE_FORMAT) + timedelta(days=1)).strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
            type = 'date'
            vstype = 'dateTime'
        else:
            start_date = fields.datetime.context_timestamp(cr, uid, datetime.strptime(event.start, tools.DEFAULT_SERVER_DATETIME_FORMAT), context=context).isoformat('T')
            if event.start<event.stop:
                even_stop = event.stop
            else:
                
                even_stop = (datetime.strptime(event.start, tools.DEFAULT_SERVER_DATE_FORMAT) + timedelta(hours=event.duration)).strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
                if even_stop<event.start:
                    even_stop = (datetime.strptime(event.start, tools.DEFAULT_SERVER_DATE_FORMAT) + timedelta(hours=1)).strftime(tools.DEFAULT_SERVER_DATE_FORMAT)
            final_date = fields.datetime.context_timestamp(cr, uid, datetime.strptime(even_stop, tools.DEFAULT_SERVER_DATETIME_FORMAT), context=context).isoformat('T')
            type = 'dateTime'
            vstype = 'date'
        attendee_list = []
        for attendee in event.attendee_ids:
            email = tools.email_split(attendee.email)
            email = email[0] if email else 'NoEmail@mail.com'
            attendee_list.append({
                'email': email,
                'displayName': attendee.partner_id.name,
                'responseStatus': attendee.state or 'needsAction',
            })

        reminders = []
        if len(event.alarm_ids)==1:
            for alarm in event.alarm_ids:
                reminders.append({
                    "method": "email" if alarm.type == "email" else "popup",
                    "minutes": alarm.duration_minutes
                })
        # attendee_list = []
        data = {
            "summary": event.name or '',
            "description": event.description or '',
            "start": {
                type: start_date,
                vstype: None,
                'timeZone': context.get('tz') or 'UTC',
            },
            "end": {
                type: final_date,
                vstype: None,
                'timeZone': context.get('tz') or 'UTC',
            },
            "attendees": attendee_list,
            "reminders": {
                "overrides": reminders,
                "useDefault": "false"
            },
            "location": event.location or '',
            "visibility": event['class'] or 'public',
        }
        if event.recurrency and event.rrule:
            data["recurrence"] = ["RRULE:" + event.rrule]

        if not event.active:
            data["state"] = "cancelled"

        if not self.get_need_synchro_attendee(cr, uid, context=context):
            data.pop("attendees")
        if isCreating:
            other_google_ids = [other_att.google_internal_event_id for other_att in event.attendee_ids if other_att.google_internal_event_id]
            if other_google_ids:
                data["id"] = other_google_ids[0]
        return data


    def get_minTime(self, cr, uid, context=None):
        number_of_week = int(self.pool['ir.config_parameter'].get_param(cr, uid, 'calendar.week_synchro', default=0))
        
        return datetime.now() - timedelta(weeks=number_of_week)

    def update_from_google(self, cr, uid, event, single_event_dict, type, context):
        if context is None:
            context = []
        
        calendar_event = self.pool['calendar.event']
        res_partner_obj = self.pool['res.partner']
        calendar_attendee_obj = self.pool['calendar.attendee']
        calendar_alarm_obj = self.pool['calendar.alarm']
        user_obj = self.pool['res.users']
        myPartnerID = user_obj.browse(cr, uid, uid, context).partner_id.id
        attendee_record = []
        alarm_record = set()
        partner_record = [(4, myPartnerID)]
        result = {}

        if self.get_need_synchro_attendee(cr, uid, context=context):
            for google_attendee in single_event_dict.get('attendees', []):
                partner_email = google_attendee.get('email', False)
                if type == "write":
                    for oe_attendee in event['attendee_ids']:
                        if oe_attendee.email == partner_email:
                            calendar_attendee_obj.write(cr, oe_attendee.event_id.user_id.id, [oe_attendee.id], {'state': google_attendee['responseStatus']}, context=context)
                            google_attendee['found'] = True
                            continue

                if google_attendee.get('found'):
                    continue

                attendee_id = res_partner_obj.search(cr, uid, [('email', '=', partner_email)], context=context)
                if attendee_id:                   
                	attendee = res_partner_obj.read(cr, uid, attendee_id[0], ['email'], context=context)
                	partner_record.append((4, attendee.get('id')))
                	attendee['partner_id'] = attendee.pop('id')
                	attendee['state'] = google_attendee['responseStatus']
                	attendee_record.append((0, 0, attendee))
        for google_alarm in single_event_dict.get('reminders', {}).get('overrides', []):
            alarm_id = calendar_alarm_obj.search(
                cr,
                uid,
                [
                    ('type', '=', google_alarm['method'] if google_alarm['method'] == 'email' else 'notification'),
                    ('duration_minutes', '=', google_alarm['minutes'])
                ],
                context=context
            )
            # if not alarm_id:
            #     data = {
            #         'type': google_alarm['method'] if google_alarm['method'] == 'email' else 'notification',
            #         'duration': google_alarm['minutes'],
            #         'interval': 'minutes',
            #         'name': "%s minutes - %s" % (google_alarm['minutes'], google_alarm['method'])
            #     }
            #     alarm_id = [calendar_alarm_obj.create(cr, uid, data, context=context)]
            
            # alarm_record.add(alarm_id[0])

        UTC = pytz.timezone('UTC')
        if single_event_dict.get('start') and single_event_dict.get('end'):  # If not cancelled

            if single_event_dict['start'].get('dateTime', False) and single_event_dict['end'].get('dateTime', False):
                date = parser.parse(single_event_dict['start']['dateTime'])
                stop = parser.parse(single_event_dict['end']['dateTime'])
                date = str(date.astimezone(UTC))[:-6]
                stop = str(stop.astimezone(UTC))[:-6]
                allday = False
            else:
                date = (single_event_dict['start']['date'])
                stop = (single_event_dict['end']['date'])
                d_end = datetime.strptime(stop, DEFAULT_SERVER_DATE_FORMAT)
                allday = True
                d_end = d_end + timedelta(days=-1)
                stop = d_end.strftime(DEFAULT_SERVER_DATE_FORMAT)

            update_date = datetime.strptime(single_event_dict['updated'], "%Y-%m-%dT%H:%M:%S.%fz")
            result.update({
                'start': date,
                'stop': stop,
                'allday': allday
            })
        result.update({
            'attendee_ids': attendee_record,
            'partner_ids': list(set(partner_record)),
            'alarm_ids': [(6, 0, list(alarm_record))],

            'name': single_event_dict.get('summary', 'Event'),
            'description': single_event_dict.get('description', False),
            'location': single_event_dict.get('location', False),
            'class': single_event_dict.get('visibility', 'public'),
            'oe_update_date': update_date,
        })

        if single_event_dict.get("recurrence", False):
            rrule = [rule for rule in single_event_dict["recurrence"] if rule.startswith("RRULE:")][0][6:]
            result['rrule'] = rrule

        context = dict(context or {}, no_mail_to_attendees=True)
        res = False
        if type == "write":            
            event_obj = calendar_event.browse(cr, uid, event['id'], result)
            if event_obj.user_id.id == uid:                
                res = calendar_event.write(cr, uid, event['id'], result, context=context)

        elif type == "copy":
            result['recurrence'] = True            
            # res = calendar_event.write(cr, uid, [event['id']], result, context=context)
        elif type == "create":            
            
            events=calendar_event.search(cr,uid,[('name','=',result['name']),('start','=',result['start'])])
            if not events:
                res = calendar_event.create(cr, uid, result, context=context)
        if context['curr_attendee']:
            
            self.pool['calendar.attendee'].write(cr, 1, [context['curr_attendee']], {'oe_synchro_date': update_date, 'google_internal_event_id': single_event_dict.get('id', False)}, context)
        
        return res

    def get_event_synchro_dict(self, cr, uid, lastSync=False, token=False, nextPageToken=False, context=None):
        if not token:
            token = self.get_token(cr, uid, context)

        params = {
            'fields': 'items,nextPageToken',
            'access_token': token,
            'maxResults': 1,
        }
        

        if lastSync:
            params['updatedMin'] = lastSync.strftime("%Y-%m-%dT%H:%M:%S.%fz")
            # params['updatedMin'] = lastSync.strftime("%Y-%m-%dT%H:%M:%S.%fz")
            params['showDeleted'] = True
        else:
            params['timeMin'] = self.get_minTime(cr, uid, context=context).strftime("%Y-%m-%dT%H:%M:%S.%fz")

        
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        url = "/calendar/v3/calendars/%s/events" % 'primary'
        if nextPageToken:
            params['pageToken'] = nextPageToken

        status, content, ask_time = self.pool['google.service']._do_request(cr, uid, url, params, headers, type='GET', context=context)

        google_events_dict = {}
        for google_event in content['items']:
            google_events_dict[google_event['id']] = google_event

        if content.get('nextPageToken'):
            google_events_dict.update(
                self.get_event_synchro_dict(cr, uid, lastSync=lastSync, token=token, nextPageToken=content['nextPageToken'], context=context)
            )

        return google_events_dict

    def get_one_event_synchro(self, cr, uid, google_id, context=None):
        token = self.get_token(cr, uid, context)

        params = {
            'access_token': token,
            'maxResults': 1,
            'showDeleted': True,
        }
        
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        url = "/calendar/v3/calendars/%s/events/%s" % ('primary', google_id)
        
        try:
            status, content, ask_time = self.pool['google.service']._do_request(cr, uid, url, params, headers, type='GET', context=context)
        except Exception, e:
            _logger.info("Calendar Synchro - In except of get_one_event_synchro")
            _logger.info(exception_to_unicode(e))
            return False

        return status_response(status) and content or False
    def create_new_events(self, cr, uid, context=None):
        if context is None:
            context = {}

        new_ids = []
        ev_obj = self.pool['calendar.event']
        att_obj = self.pool['calendar.attendee']
        user_obj = self.pool['res.users']
        myPartnerID = user_obj.browse(cr, uid, uid, context=context).partner_id.id

        context_norecurrent = context.copy()
        context_norecurrent['virtual_id'] = False
        my_att_ids = att_obj.search(cr, uid, [('partner_id', '=', myPartnerID),
                                    ('google_internal_event_id', '=', False),
                                    '|',
                                    ('event_id.stop', '>', self.get_minTime(cr, uid, context=context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                    ('event_id.final_date', '>', self.get_minTime(cr, uid, context=context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                    ], context=context_norecurrent)
        for att in att_obj.browse(cr, uid, my_att_ids, context=context):
            other_google_ids = [other_att.google_internal_event_id for other_att in att.event_id.attendee_ids if other_att.google_internal_event_id and other_att.id != att.id]
            for other_google_id in other_google_ids:
                if self.get_one_event_synchro(cr, uid, other_google_id, context=context):
                    att_obj.write(cr, att.event_id.create_uid.id, [att.id], {'google_internal_event_id': other_google_id})
                    # query = "update calendar_attendee set google_internal_event_id=%s where id=%s"%(other_google_id,att.id)
                    # cr.execute(query)
                    break
            else:
                if not att.event_id.recurrent_id or att.event_id.recurrent_id == 0:
                    st, response, ask_time = self.create_an_event(cr, uid, att.event_id, context=context)
                    if status_response(st):
                        update_date = datetime.strptime(response['updated'], "%Y-%m-%dT%H:%M:%S.%fz")
                        ev_obj.write(cr, att.event_id.create_uid.id, att.event_id.id, {'oe_update_date': update_date})
                        # query = "update calendar_event set oe_update_date='%s' where id=%s"%(update_date,att.event_id.id)
                        # cr.execute(query)
                        new_ids.append(response['id'])
                        att_obj.write(cr, att.event_id.create_uid.id, [att.id], {'google_internal_event_id': response['id'], 'oe_synchro_date': update_date})
                        # query = "update calendar_attendee set google_internal_event_id='%s' , oe_synchro_date ='%s' where id=%s"%(response['id'],update_date,att.id)
                        # cr.execute(query)
                        cr.commit()
                    else:
                        _logger.warning("Impossible to create event %s. [%s] Enable DEBUG for response detail.", att.event_id.id, st)
                        _logger.debug("Response : %s" % response)
        return new_ids

    def update_to_google(self, cr, uid, oe_event, google_event, context):
        calendar_event = self.pool['calendar.event']

        url = "/calendar/v3/calendars/%s/events/%s?fields=%s&access_token=%s" % ('primary', google_event['id'], 'id,updated', self.get_token(cr, uid, context))
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        data = self.generate_data(cr, uid, oe_event, context=context)
        data['sequence'] = google_event.get('sequence', 0)
        data_json = json.dumps(data)
        
        status, content, ask_time = self.pool['google.service']._do_request(cr, uid, url, data_json, headers, type='PATCH', context=context)
        
        update_date = datetime.strptime(content['updated'], "%Y-%m-%dT%H:%M:%S.%fz")    
        calendar_event.write(cr, oe_event.create_uid.id, [oe_event.id], {'oe_update_date': update_date})

        if context['curr_attendee']:
            self.pool['calendar.attendee'].write(cr, oe_event.user_id.id, [context['curr_attendee']], {'oe_synchro_date': update_date}, context)


    def bind_recurring_events_to_google(self, cr, uid, context=None):
        if context is None:
            context = {}

        new_ids = []
        ev_obj = self.pool['calendar.event']
        att_obj = self.pool['calendar.attendee']
        user_obj = self.pool['res.users']
        myPartnerID = user_obj.browse(cr, uid, uid, context=context).partner_id.id

        context_norecurrent = self.get_context_no_virtual(context)
        my_att_ids = att_obj.search(cr, uid, [('partner_id', '=', myPartnerID), ('google_internal_event_id', '=', False)], context=context_norecurrent)

        for att in att_obj.browse(cr, uid, my_att_ids, context=context):
            if att.event_id.recurrent_id and att.event_id.recurrent_id > 0:
                new_google_internal_event_id = False
                source_event_record = ev_obj.browse(cr, uid, att.event_id.recurrent_id, context)
                source_attendee_record_id = att_obj.search(cr, uid, [('partner_id', '=', myPartnerID), ('event_id', '=', source_event_record.id)], context=context)
                if not source_attendee_record_id:
                    continue
                source_attendee_record = att_obj.browse(cr, uid, source_attendee_record_id, context)[0]

                if att.event_id.recurrent_id_date and source_event_record.allday and source_attendee_record.google_internal_event_id:
                    new_google_internal_event_id = source_attendee_record.google_internal_event_id + '_' + att.event_id.recurrent_id_date.split(' ')[0].replace('-', '')
                elif att.event_id.recurrent_id_date and source_attendee_record.google_internal_event_id:
                    new_google_internal_event_id = source_attendee_record.google_internal_event_id + '_' + att.event_id.recurrent_id_date.replace('-', '').replace(' ', 'T').replace(':', '') + 'Z'

                if new_google_internal_event_id:
                    #TODO WARNING, NEED TO CHECK THAT EVENT and ALL instance NOT DELETE IN GMAIL BEFORE !
                    try:
                        st, response, ask_time = self.update_recurrent_event_exclu(cr, uid, new_google_internal_event_id, source_attendee_record.google_internal_event_id, att.event_id, context=context)
                        if status_response(st):
                            att_obj.write(cr, att.event_id.create_uid.id, [att.id], {'google_internal_event_id': new_google_internal_event_id}, context=context)
                            new_ids.append(new_google_internal_event_id)
                            cr.commit()
                        else:
                            _logger.warning("Impossible to create event %s. [%s]" % (att.event_id.id, st))
                            _logger.debug("Response : %s" % response)
                    except:
                        pass
        return new_ids

    def synchronize_events(self, cr, uid, ids, lastSync=True, context=None):
        if context is None:
            context = {}

        user_to_sync = ids and ids[0] or uid
        current_user = self.pool['res.users'].browse(cr, SUPERUSER_ID, user_to_sync, context=context)

        st, current_google, ask_time = self.get_calendar_primary_id(cr, user_to_sync, context=context)

        if current_user.google_calendar_cal_id:
            if current_google != current_user.google_calendar_cal_id:
                return {
                    "status": "need_reset",
                    "info": {
                        "old_name": current_user.google_calendar_cal_id,
                        "new_name": current_google
                    },
                    "url": ''
                }

            if lastSync and self.get_last_sync_date(cr, user_to_sync, context=context) and not self.get_disable_since_synchro(cr, user_to_sync, context=context):
                # lastSync = self.get_last_sync_date(cr, user_to_sync, context)
                lastSync = datetime.today()
                _logger.info("[%s] Calendar Synchro - MODE SINCE_MODIFIED : %s !" % (user_to_sync, lastSync.strftime(DEFAULT_SERVER_DATETIME_FORMAT)))
            else:
                lastSync = False
                _logger.info("[%s] Calendar Synchro - MODE FULL SYNCHRO FORCED" % user_to_sync)
        else:
            current_user.write({'google_calendar_cal_id': current_google})
            lastSync = False
            _logger.info("[%s] Calendar Synchro - MODE FULL SYNCHRO - NEW CAL ID" % user_to_sync)

        new_ids = []
        new_ids += self.create_new_events(cr, user_to_sync, context=context)
        new_ids += self.bind_recurring_events_to_google(cr, user_to_sync, context)
        res = self.update_events(cr, user_to_sync, lastSync, context)
        

        current_user.write({'google_calendar_last_sync_date': ask_time})
        return {
            "status": res and "need_refresh" or "no_new_event_from_google",
            "url": ''
        }
    def update_events(self, cr, uid, lastSync=False, context=None):
        context = dict(context or {})

        calendar_event = self.pool['calendar.event']
        user_obj = self.pool['res.users']
        att_obj = self.pool['calendar.attendee']
        myPartnerID = user_obj.browse(cr, uid, uid, context=context).partner_id.id
        context_novirtual = self.get_context_no_virtual(context)

        if lastSync:
            lastSync_date = lastSync and lastSync.strftime(DEFAULT_SERVER_DATETIME_FORMAT) or self.get_minTime(cr, uid, context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            lastSync_date = datetime.strptime(lastSync_date, '%Y-%m-%d %H:%M:%S')-relativedelta(days=5)
            
            try:
                all_event_from_google = self.get_event_synchro_dict(cr, uid, lastSync=lastSync_date, context=context)
            except urllib2.HTTPError, e:
                if e.code == 410:  # GONE, Google is lost.
                    # we need to force the rollback from this cursor, because it locks my res_users but I need to write in this tuple before to raise.
                    cr.rollback()
                    registry = openerp.modules.registry.RegistryManager.get(request.session.db)
                    with registry.cursor() as cur:
                        self.pool['res.users'].write(cur, SUPERUSER_ID, [uid], {'google_calendar_last_sync_date': False}, context=context)
                error_key = json.loads(str(e))
                error_key = error_key.get('error', {}).get('message', 'nc')
                error_msg = _("Google is lost... the next synchro will be a full synchro. \n\n %s") % error_key
                raise self.pool.get('res.config.settings').get_config_warning(cr, error_msg, context=context)

            my_google_att_ids = att_obj.search(cr, uid, [
                ('partner_id', '=', myPartnerID),
                ('google_internal_event_id', 'in', all_event_from_google.keys())
            ], context=context_novirtual)
            
            my_openerp_att_ids = att_obj.search(cr, uid, [
                ('partner_id', '=', myPartnerID),
                ('event_id.oe_update_date', '>', lastSync_date and lastSync_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT) or self.get_minTime(cr, uid, context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                ('google_internal_event_id', '!=', False),
            ], context=context_novirtual)
            

            my_openerp_googleinternal_ids = att_obj.read(cr, SUPERUSER_ID, my_openerp_att_ids, ['google_internal_event_id', 'event_id'], context=context_novirtual)

            if self.get_print_log(cr, uid, context=context):
                _logger.info("Calendar Synchro -  \n\nUPDATE IN GOOGLE\n%s\n\nRETRIEVE FROM OE\n%s\n\nUPDATE IN OE\n%s\n\nRETRIEVE FROM GG\n%s\n\n" % (all_event_from_google, my_google_att_ids, my_openerp_att_ids, my_openerp_googleinternal_ids))

            for giid in my_openerp_googleinternal_ids:
                active = True  # if not sure, we request google
                if giid.get('event_id'):
                    active = calendar_event.browse(cr, uid, int(giid.get('event_id')[0]), context=context_novirtual).active

                if giid.get('google_internal_event_id') and not all_event_from_google.get(giid.get('google_internal_event_id')) and active:
                    one_event = self.get_one_event_synchro(cr, uid, giid.get('google_internal_event_id'), context=context)
                    if one_event:
                        all_event_from_google[one_event['id']] = one_event

            my_att_ids = list(set(my_google_att_ids + my_openerp_att_ids))

        else:
            domain = [
                ('partner_id', '=', myPartnerID),
                ('google_internal_event_id', '!=', False),
                '|',
                ('event_id.stop', '>', self.get_minTime(cr, uid, context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                ('event_id.final_date', '>', self.get_minTime(cr, uid, context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
            ]

            # Select all events from OpenERP which have been already synchronized in gmail
            my_att_ids = att_obj.search(cr, uid, domain, context=context_novirtual)
            all_event_from_google = self.get_event_synchro_dict(cr, uid, lastSync=False, context=context)

        event_to_synchronize = {}
        
        for att in att_obj.browse(cr, uid, my_att_ids, context=context):
            event = att.sudo().event_id
            base_event_id = att.google_internal_event_id.rsplit('_', 1)[0]

            if base_event_id not in event_to_synchronize:
                event_to_synchronize[base_event_id] = {}

            if att.google_internal_event_id not in event_to_synchronize[base_event_id]:
                event_to_synchronize[base_event_id][att.google_internal_event_id] = SyncEvent()

            ev_to_sync = event_to_synchronize[base_event_id][att.google_internal_event_id]


            ev_to_sync.OE.attendee_id = att.id
            ev_to_sync.OE.event = event
            ev_to_sync.OE.found = True
            ev_to_sync.OE.event_id = event.id

            ev_to_sync.OE.isRecurrence = event.recurrency

            ev_to_sync.OE.isInstance = bool(event.recurrent_id and event.recurrent_id > 0)
            ev_to_sync.OE.update = event.oe_update_date
            ev_to_sync.OE.status = event.active
            ev_to_sync.OE.synchro = att.oe_synchro_date

        
        for event in all_event_from_google.values():
            event_id = event.get('id')
            base_event_id = event_id.rsplit('_', 1)[0]

            if base_event_id not in event_to_synchronize:
                event_to_synchronize[base_event_id] = {}

            if event_id not in event_to_synchronize[base_event_id]:
                event_to_synchronize[base_event_id][event_id] = SyncEvent()

            ev_to_sync = event_to_synchronize[base_event_id][event_id]

            ev_to_sync.GG.event = event
            ev_to_sync.GG.found = True
            ev_to_sync.GG.isRecurrence = bool(event.get('recurrence', ''))
            ev_to_sync.GG.isInstance = bool(event.get('recurringEventId', 0))
            ev_to_sync.GG.update = event.get('updated', None)  # if deleted, no date without browse event
            if ev_to_sync.GG.update:
                ev_to_sync.GG.update = ev_to_sync.GG.update.replace('T', ' ').replace('Z', '')
            ev_to_sync.GG.status = (event.get('status') != 'cancelled')
        
        ######################
        #   PRE-PROCESSING   #
        ######################
        
        for base_event in event_to_synchronize:
            for current_event in event_to_synchronize[base_event]:
                if event_to_synchronize[base_event][current_event].OE.event:
                    user_id =  event_to_synchronize[base_event][current_event].OE.event.user_id
                    event_to_synchronize[base_event][current_event].OE.event.user_id = event_to_synchronize[base_event][current_event].OE.event.env.user
                event_to_synchronize[base_event][current_event].compute_OP(modeFull=not lastSync)
                if event_to_synchronize[base_event][current_event].OE.event:
                    event_to_synchronize[base_event][current_event].OE.event.user_id = user_id
            if self.get_print_log(cr, uid, context=context):
                if not isinstance(event_to_synchronize[base_event][current_event].OP, NothingToDo):
                    _logger.info(event_to_synchronize[base_event])

        ######################
        #      DO ACTION     #
        ######################
        
        for base_event in event_to_synchronize:
            event_to_synchronize[base_event] = sorted(event_to_synchronize[base_event].iteritems(), key=operator.itemgetter(0))
            for current_event in event_to_synchronize[base_event]:
                cr.commit()
                event = current_event[1]  # event is an Sync Event !
                actToDo = event.OP
                actSrc = event.OP.src

                context['curr_attendee'] = event.OE.attendee_id

                if isinstance(actToDo, NothingToDo):
                    continue
                elif isinstance(actToDo, Create):
                    if actSrc == 'GG':
                        self.create_from_google(cr, uid, event, myPartnerID, context=context)
                    elif actSrc == 'OE':
                        raise "Should be never here, creation for OE is done before update !"
                    #TODO Add to batch
                elif isinstance(actToDo, Update):
                    if actSrc == 'GG':
                        self.update_from_google(cr, uid, event.OE.event, event.GG.event, 'write', context)
                    elif actSrc == 'OE':
                        self.update_to_google(cr, uid, event.OE.event, event.GG.event, context)
                elif isinstance(actToDo, Exclude):
                    if actSrc == 'OE':
                        self.delete_an_event(cr, uid, current_event[0], context=context)
                    elif actSrc == 'GG':
                        new_google_event_id = event.GG.event['id'].rsplit('_', 1)[1]
                        if 'T' in new_google_event_id:
                            new_google_event_id = new_google_event_id.replace('T', '')[:-1]
                        else:
                            new_google_event_id = new_google_event_id + "000000"

                        if event.GG.status:
                            parent_event = {}
                            if not event_to_synchronize[base_event][0][1].OE.event_id:
                                main_ev = att_obj.search_read(cr, uid, [('google_internal_event_id', '=', event.GG.event['id'].rsplit('_', 1)[0])], fields=['event_id'], context=context_novirtual)
                                event_to_synchronize[base_event][0][1].OE.event_id = main_ev[0].get('event_id')[0] if main_ev else None
                            if event_to_synchronize[base_event][0][1].OE.event_id:
                                parent_event['id'] = "%s-%s" % (event_to_synchronize[base_event][0][1].OE.event_id, new_google_event_id)
                                res = self.update_from_google(cr, uid, parent_event, event.GG.event, "copy", context)
                            else:
                                self.create_from_google(cr, uid, event, myPartnerID, context=context)
                        else:
                            parent_oe_id = event_to_synchronize[base_event][0][1].OE.event_id
                            if parent_oe_id:
                                try:
                                    calendar_event.unlink(cr, uid, "%s-%s" % (parent_oe_id, new_google_event_id), context=context)
                                except Exception, e:
                                    pass
                elif isinstance(actToDo, Delete):
                    if actSrc == 'GG':
                        try:
                            self.delete_an_event(cr, uid, current_event[0], context=context)
                        except urllib2.HTTPError, e:
                            # if already deleted from gmail or never created
                            if e.code in (404, 410,):
                                pass
                            else:
                                raise e
                    elif actSrc == 'OE':
                        try:
                            calendar_event.unlink(cr, uid, event.OE.event_id,  context=context)
                        except Exception, e:
                                    pass
        return True



class calendar_event(osv.Model):
    _inherit = "calendar.event"
    

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        
        sync_fields = set(self.get_fields_need_update_google(cr, uid, context))
        if (set(vals.keys()) & sync_fields) and 'oe_update_date' not in vals.keys() and 'NewMeeting' not in context:
            vals['oe_update_date'] = datetime.now()

        return super(calendar_event, self).write(cr, uid, ids, vals, context=context)
class calendar_attendee(osv.Model):
    _inherit = 'calendar.attendee'

    _columns = {
        'google_internal_event_id': fields.char('Google Calendar Event Id'),
        'oe_synchro_date': fields.datetime('Odoo Synchro Date'),
    }
    _sql_constraints = [('google_id_uniq', 'unique(google_internal_event_id,partner_id,event_id)', 'Google ID should be unique!')]

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}

        for id in ids:
            ref = vals.get('event_id', self.browse(cr, uid, id, context=context).event_id.id)

            # If attendees are updated, we need to specify that next synchro need an action
            # Except if it come from an update_from_google
            if not context.get('curr_attendee', False) and not context.get('NewMeeting', False):
                
                self.pool['calendar.event'].write(cr, uid, ref, {'oe_update_date': datetime.now()}, context)
        return super(calendar_attendee, self).write(cr, uid, ids, vals, context=context)