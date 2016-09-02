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


class CDRCAdminController(base.BaseController):
    def __before__(self, action, **params):
        super(CDRCAdminController, self).__before__(action, **params)
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

    def reset_config(self):
        '''FIXME: This method is probably not doing what people would expect.
           It will reset the configuration to values cached when CKAN started.
           If these were coming from the database during startup, that's the
           ones that will get applied on reset, not the ones in the ini file.
           Only after restarting the server and having CKAN reset the values
           from the ini file (as the db ones are not there anymore) will these
           be used.
        '''

        if 'cancel' in request.params:
            h.redirect_to(controller='ckanext.cdrc.controllers.cdrc_admin:CDRCAdminController', action='config')

        if request.method == 'POST':
            # remove sys info items
            for item in self._get_config_form_items():
                name = item['name']
                model.delete_system_info(name)
            # reset to values in config
            app_globals.reset()
            h.redirect_to(controller='ckanext.cdrc.controllers.cdrc_admin:CDRCAdminController', action='config')

        return base.render('admin/confirm_reset.html')

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
                return base.render('cdrcadmin/config.html', extra_vars=vars)

            h.redirect_to(controller='ckanext.cdrc.controllers.cdrc_admin:CDRCAdminController', action='config')

        schema = logic.schema.update_configuration_schema()
        data = {}
        for key in schema:
            data[key] = config.get(key)

        vars = {'data': data, 'errors': {}, 'form_items': items}
        return base.render('cdrcadmin/config.html',
                           extra_vars=vars)

    def user_emails(self):
        #now pass the list of sysadmins
        pass

