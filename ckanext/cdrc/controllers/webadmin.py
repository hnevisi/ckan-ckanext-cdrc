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


c = base.c
request = base.request
_ = base._


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

    def downloads_per_month(self):
        #now pass the list of sysadmins
        downloads_per_month_sql = '''
            select to_char(access_timestamp, 'YYYY-MM') as yearmonth, count(*) as downloads from tracking_raw where tracking_type = 'download' group by yearmonth order by yearmonth desc
        '''
        model = context['model']
        result = model.Session.execute(downloads_per_month_sql)
        assert False


