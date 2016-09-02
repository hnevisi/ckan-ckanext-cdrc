from pylons import config

import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.app_globals as app_globals
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.model as model
import ckan.logic as logic
import ckan.plugins as plugins
from ckan.controllers.home import CACHE_PARAMETERS
from ckanext.cdrc import helpers
from ckan.common import response


c = base.c
request = base.request
_ = base._



def sql_to_csv_response(sql, headers=None, name=None):
    response.headers['Content-Type'] = 'text/csv'
    response.status = 200
    if name:
        response.headers['Content-Disposition'] = 'attachment;filename={}'.format(name)

    res = model.Session.execute(sql)
    def csv_iter():
        yield ','.join(['"{}"'.format(i) for i in headers]) + '\n'
        for r in res:
            yield ','.join([str(i) for i in r]) + '\n'
    return csv_iter()


class WebAdminController(base.BaseController):
    def __before__(self, action, **params):
        super(WebAdminController, self).__before__(action, **params)
        context = {'model': model,
                   'user': c.user, 'auth_user_obj': c.userobj}
        try:
            if not helpers.is_cdrc_admin():
                raise logic.NotAuthorized()
        except logic.NotAuthorized:
            base.abort(401, _('Need to be CDRC website administrator to administer'))
        c.revision_change_state_allowed = True

    def _get_config_form_items(self):
        # Styles for use in the form.select() macro.
        notice_types = [
            {'text': 'Warning', 'value': 'alert-error'},
            {'text': 'Information', 'value': 'alert-info'},
            {'text': 'Other', 'value': 'alert-success'},
        ]
        items = [
            {'name': 'cdrc.mom.title', 'control': 'input', 'label': _('MoM Title'), 'placeholder': ''},
            {'name': 'cdrc.mom.description', 'control': 'markdown', 'label': _('MoM Description'), 'placeholder': ''},
            {'name': 'cdrc.mom.tile_url', 'control': 'input', 'label': _('MoM Tile URL'), 'placeholder': ''},
            {'name': 'cdrc.mom.map_link', 'control': 'input', 'label': _('CDRC Maps Link'), 'placeholder': ''},
            {'name': 'cdrc.site_notice.text', 'control': 'input', 'label': _('Website Notice'), 'placeholder': ''},
            {'name': 'cdrc.site_notice.type', 'control': 'select', 'options': notice_types, 'label': _('Notice Type'), 'placeholder': ''},
        ]
        return items

    def config(self):

        items = self._get_config_form_items()
        data = request.POST
        if 'save' in data:
            try:
                # really?
                data_dict = logic.clean_dict(
                    dict_fns.unflatten(
                        logic.tuplize_dict(
                            logic.parse_params(
                                request.POST, ignore_keys=CACHE_PARAMETERS))))

                del data_dict['save']

                data = logic.get_action('config_option_update')(
                    {'user': c.user}, data_dict)
            except logic.ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
                vars = {'data': data, 'errors': errors,
                        'error_summary': error_summary, 'form_items': items}
                return base.render('webadmin/config.html', extra_vars=vars)

            h.redirect_to(controller='ckanext.cdrc.controllers.webadmin:WebAdminController', action='config')

        schema = logic.schema.update_configuration_schema()
        data = {}
        for key in schema:
            data[key] = config.get(key)

        vars = {'data': data, 'errors': {}, 'form_items': items}
        return base.render('webadmin/config.html',
                           extra_vars=vars)

    def stat_csv(self, name):
        ''' Downloads per Month
        '''
        downloads_per_month_sql = '''
            select to_char(access_timestamp, 'YYYY-MM') as yearmonth, count(*) as downloads from tracking_raw where tracking_type = 'download' group by yearmonth order by yearmonth desc
        '''
        user_reg_per_month_sql = '''
            select to_char(created, 'YYYY-MM') as yearmonth, count(id) as reg_users from "user" group by yearmonth order by yearmonth desc
        '''
        user_allowing_email_dataset_update = '''
            select fullname, email from "user" as u right join user_extra as m on u.id = m.user_id where m.key = 'extra_dataset_update'
        '''
        user_allowing_email_event_update = '''
            select fullname, email from "user" as u right join user_extra as m on u.id = m.user_id where m.key = 'extra_event_update'
        '''
        user_per_private_secotor = '''
            select "value" as "sector", count(id) from user_extra where "key"='extra_private_sector' group by "sector"
        '''
        total_user = '''
            select count(id) - 4 as reg_users from "user"
        '''
        if name == 'dpm':
            return sql_to_csv_response(downloads_per_month_sql, ['yearmonth', 'downloads'], 'downloads_per_month.csv')
        elif name == 'urpm':
            return sql_to_csv_response(user_reg_per_month_sql, ['yearmonth', 'user_reg_number'], 'user_reg_per_month.csv')
        elif name == 'uaedu':
            return sql_to_csv_response(user_allowing_email_dataset_update, ['fullname', 'email'], 'user_allowing_email_dataset_update.csv')
        elif name == 'uaeeu':
            return sql_to_csv_response(user_allowing_email_event_update, ['fullname', 'email'], 'user_allowing_email_event_update.csv')
        elif name == 'ups':
            return sql_to_csv_response(user_per_private_secotor, ['private_sector', 'user_number'], 'user_per_private_secotor.csv')
        elif name == 'tun':
            return sql_to_csv_response(total_user, ['total_user'], 'total_user.csv')

