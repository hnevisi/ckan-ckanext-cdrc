import re
import json
import logging
from textwrap import dedent
from collections import defaultdict
from routes.mapper import SubMapper

from zope.interface import implements as zimpl
from repoze.who.interfaces import IAuthenticator
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.logic import auth as ckan_auth
from ckan.logic import action as ckan_action
from ckan.lib.base import BaseController
from ckan.lib.plugins import DefaultGroupForm
import ckan.model as model
import ckan.lib.fanstatic_resources as fanstatic_resources
from ckanext.cdrc.logic import auth
from ckanext.cdrc.logic import action
from ckanext.cdrc import helpers
from ckan.logic import get_action as ckan_get_action
from ckan.lib.app_globals import set_app_global
from ckanext.cdrc.controllers.lad import LadController

from ckan.common import _, g, c
from ckan.lib.navl.validators import (ignore_missing, not_missing, ignore_empty)

log = logging.getLogger('ckanext.cdrc')


class CDRCExtController(BaseController):
    def assertfalse(self):
        assert False

    def __before__(self, action=None, **params):
        super(CDRCExtController, self)


class CdrcPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    zimpl(IAuthenticator)


    # IConfigurer
    def update_config(self, config_):

        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'cdrc')

        # Patching the ckan group needs to remove default mason-grid.js
        ckan_group = getattr(fanstatic_resources, 'base/ckan')
        ckan_group.depends = set([r for r in ckan_group.depends if not r.relpath.endswith('media-grid.js')])
        ckan_group.resources = set([r for r in ckan_group.resources if not r.relpath.endswith('media-grid.js')])

        config_['ckan.site_logo'] = '/images/CDRC Col.jpg'
        config_['ckan.site_description'] = dedent(
            ''' CDRC Data is a platform for data discovering, data analytics, data comprehension.
            ''')
        config_['ckan.favicon'] = '/images/CDRC_fav.png'
        config_['ckan.site_about'] = dedent(
            '''
            <h1>
            Welcome to the Consumer Data Research Centre (CDRC).
            </h1>
            <p>
            We are an academic led, multi-institution laboratory which discovers, mines, analyses and synthesises consumer-related datasets from around the UK. The CDRC is an ESRC Data Investment.
            </p>
            '''
        )
        config_['ckan.site_title'] = 'CDRC Data'
        config_['ckan.main_css'] = '/base/cdrc/css/main.css'
        config_['ckan.site_intro_text'] = dedent('''
            ## Welcome to CDRC Data

            CDRC's mission is to make consumer data available to an ever broader
            constituency of users in the research, business and local government
            communities. We do this by creating data packs that are readily
            available for analysis and intelligible to a broad constituency of
            users. We are also committed to extend the collection available here
            with new, novel and policy-relevant datasets as our work programme
            develops.
        ''')
        config_['cdrc.site_notice.text'] = ''
        config_['cdrc.site_notice.type'] = ''

    def authenticate(self, environ, identity):
        if not ('login' in identity and 'password' in identity):
            return None

        login = identity['login']
        try:
            user = model.user.User.by_email(login)[0]
        except (TypeError, IndexError):
            user = model.user.User.by_name(login)

        if user is None:
            log.debug('Login failed - user %r not found', login)
        elif not user.is_active():
            log.debug('Login as %r failed - user isn\'t active', login)
        elif not user.validate_password(identity['password']):
            log.debug('Login as %r failed - password not valid', login)
        else:
            return user.name

        return None

    def get_helpers(self):
        return {
            'is_cdrc_admin': helpers.is_cdrc_admin,
            'get_ga_account_ids': helpers.get_ga_account_ids,
            'get_user_count': helpers.get_user_count,
            'get_group_type_name': helpers.get_group_type_name
        }

    def update_config_schema(self, schema):
        cdrc_schema = {
            'cdrc.mom.tile_url': [unicode],
            'cdrc.mom.title': [unicode],
            'cdrc.mom.description': [unicode],
            'cdrc.mom.map_link': [unicode],
            'cdrc.site_notice.text':  [ignore_missing, unicode],
            'cdrc.site_notice.type':  [ignore_missing, unicode]
        }
        return dict(schema, **cdrc_schema)

    def get_actions(self):
        return {
            'get_site_statistics': action.get_site_statistics,
            'refresh_site_statistics': action.refresh_site_statistics,
            'resource_clean': action.resource_clean,
            'notice_show': action.notice_show,
            'notice_update': action.notice_update,
            'group_list_authz': action.group_list_authz,
            'package_create': action.package_create,
            'package_update': action.package_update,
            'package_group_removeall': action.package_group_removeall,
            'bulk_reject': action.bulk_reject,
            'bulk_pass': action.bulk_pass,
            'bulk_approve': action.bulk_approve,
            'momconfig_show': action.momconfig_show
        }

    def get_auth_functions(self):
        return {
            'resource_download': auth.resource_download,
            'resource_clean': auth.resource_clean,
            'notice_update': auth.notice_update,
            'group_create': auth.group_create,
            'member_create': auth.member_edit,
            'member_delete': auth.member_edit,
            'user_list': auth.user_list,
            'package_update': auth.package_update,
            'package_create': auth.package_create,
            'bulk_pass': auth.bulk_pass,
            'bulk_approve': auth.bulk_approve,
            'bulk_reject': auth.bulk_reject,
            'config_option_update': auth.config_option_update,
            'user_show': auth.user_show
        }

    def after_map(self, map):
        return map

    def before_map(self, map):
        map.connect('/testing/assertfalse', controller='ckanext.cdrc.plugin:CDRCExtController', action='assertfalse')
        map.connect('blog', '/blog', controller='ckanext.cdrc.controllers.page:CDRCBlogController', action='blog_proxy')
        map.connect('practical', '/practical', controller='ckanext.cdrc.controllers.page:CDRCPageController', action='index')
        map.connect('national', '/national', controller='ckanext.cdrc.controllers.singlegroup:SingleGroupController', action='read_national')
        map.connect('regional', '/regional', controller='ckanext.cdrc.controllers.singlegroup:SingleGroupController', action='read_regional')
        with SubMapper(map, controller='ckanext.cdrc.controllers.page:CDRCPageController') as m:
            m.connect('/practical/{pkg_id}/{page_id}', action='page_show')
            m.connect('/practical/{pkg_id}', action='page_list')
        with SubMapper(map, controller='ckanext.cdrc.controllers.organization_admin:CDRCOrgAdminController') as m:
            m.connect('organization_format_review',
                      '/organization/format_review/{id}',
                      action='format_review', ckan_icon='check')
            m.connect('organization_disclosure_review',
                      '/organization/disclosure_review/{id}',
                      action='disclosure_review', ckan_icon='legal')
            m.connect('organization_admin',
                      '/cdrc_admin',
                      action='cdrc_admin')
        with SubMapper(map, controller='ckanext.cdrc.controllers.webadmin:WebAdminController') as m:
            m.connect('webadmin_config', '/webadmin/config', action='config', ckan_icon='check')
            m.connect('/webadmin/stat_csv/{code}', action='stat_csv')
            m.connect('webadmin_stat', '/webadmin/stat_csv_view', action='stat_csv_view', ckan_icon='table')
        map.redirect('/user/me', '/cdrc_admin')
        return map

    def before_search(self, data_dict):
        return data_dict

    def after_search(self, result, params):
        return result

    def before_index(self, pkg_dict):
        groups = json.loads(pkg_dict['data_dict'])['groups']
        customized_groups = defaultdict(list)
        for g in groups:
            if g['type'] in ['accesslevel', 'lad', 'topic', 'product']:
                customized_groups[g['type']].append(g['name'])
        pkg_dict.update(customized_groups)
        return pkg_dict

    def dataset_facets(self, facets_dict, package_type):
        del facets_dict['organization']
        del facets_dict['license_id']
        facets_dict['topic'] = toolkit._('Topics')
        facets_dict['product'] = toolkit._('Products')
        facets_dict['lad'] = toolkit._('LADs')
        facets_dict['accesslevel'] = toolkit._('Access Levels')
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        del facets_dict['organization']
        del facets_dict['license_id']
        if group_type != 'topic':
            facets_dict['topic'] = toolkit._('Topics')
        if group_type != 'product':
            facets_dict['product'] = toolkit._('Products')
        if group_type != 'lad':
            facets_dict['lad'] = toolkit._('LADs')
        if group_type != 'accesslevel':
            facets_dict['accesslevel'] = toolkit._('Access Levels')
        return facets_dict

    def before_view(self, pkg_dict):
        user_dict = ckan_get_action('user_show')({'model': model}, {'id': pkg_dict['creator_user_id']})
        pkg_dict['creator_name'] = user_dict['fullname']
        pkg_dict['creator_id'] = user_dict['name']
        return pkg_dict


def mapper_mixin(map, group_type, controller=None):
    """ Mixin for group types

    :map: TODO
    :group_type: TODO
    :returns: TODO

    """
    GET = dict(method=['GET'])
    with SubMapper(map, controller='api', path_prefix='/api{ver:/1|/2|}',
                ver='/1') as m:
        m.connect('/util/%s/autocomplete' % (group_type,), action='%s_autocomplete' % (group_type,),
                conditions=GET)

    with SubMapper(map, controller=controller) as m:
        m.connect('%s_about' % (group_type,), '/%s/about/{id}' % (group_type,),
                  action='about', ckan_icon='info-sign')
        m.connect('%s_bulk_process' % (group_type,),
                  '/%s/bulk_process/{id}' % (group_type,),
                  action='bulk_process', ckan_icon='sitemap')
    return map


class CdrcTopicPlugin(plugins.SingletonPlugin, DefaultGroupForm):
    plugins.implements(plugins.IGroupForm)
    plugins.implements(plugins.IRoutes)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)

    def is_fallback(self):
        return False

    def group_types(self):
        return ['topic']

    def after_map(self, map):
        mapper_mixin(map, 'topic', 'ckanext.cdrc.controllers.topic:TopicController')
        return map

    def before_map(self, map):
        return map

    def get_auth_functions(self):
        return {
            'topic_create': ckan_auth.create.group_create,
            'topic_update': ckan_auth.update.group_update,
            'topic_delete': ckan_auth.delete.group_delete,
        }

    def get_actions(self):
        return {
            'topic_list': action.group_list,
            'topic_show': ckan_action.get.group_show,
            'topic_activity_list_html': ckan_action.get.group_activity_list_html,
            'topic_create': ckan_action.create.group_create,
            'topic_update': ckan_action.update.group_update,
            'topic_patch': action.group_patch,
            'topic_delete': ckan_action.delete.group_delete,
        }

    def group_controller(self):
        """TODO: Docstring for group_controller.
        :returns: TODO

        """
        return 'ckanext.cdrc.controllers.topic:TopicController'

    def group_form(self):
        return 'topic/new_customized_group_form.html'

    def setup_template_variables(self, context, data_dict):
        pass

    def new_template(self):
        return 'topic/new.html'

    def about_template(self):
        return 'topic/about.html'

    def index_template(self):
        return 'topic/index.html'

    def admins_template(self):
        return 'topic/admins.html'

    def bulk_process_template(self):
        return 'topic/bulk_process.html'

    def read_template(self):
        return 'topic/read.html'

    # don't override history_template - use group template for history

    def edit_template(self):
        return 'topic/edit.html'

    def activity_template(self):
        return 'topic/activity_stream.html'


class CdrcProductPlugin(plugins.SingletonPlugin, DefaultGroupForm):
    plugins.implements(plugins.IGroupForm)
    plugins.implements(plugins.IRoutes)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)

    def is_fallback(self):
        return False

    def group_types(self):
        return ['product']

    def after_map(self, map):
        mapper_mixin(map, 'product', 'ckanext.cdrc.controllers.product:ProductController')
        return map

    def before_map(self, map):
        return map

    def get_auth_functions(self):
        return {
            'product_create': auth.group_edit,
            'product_update': auth.group_edit,
            'product_delete': ckan_auth.delete.group_delete,
        }

    def get_actions(self):
        return {
            'product_list': action.group_list,
            'product_show': ckan_action.get.group_show,
            'product_activity_list_html': ckan_action.get.group_activity_list_html,
            'product_create': ckan_action.create.group_create,
            'product_update': ckan_action.update.group_update,
            'product_patch': action.group_patch,
            'product_delete': ckan_action.delete.group_delete,
        }

    def group_controller(self):
        """TODO: Docstring for group_controller.
        :returns: TODO

        """
        return 'ckanext.cdrc.controllers.product:ProductController'

    def group_form(self):
        return 'product/new_customized_group_form.html'

    def setup_template_variables(self, context, data_dict):
        pass

    def new_template(self):
        return 'product/new.html'

    def about_template(self):
        return 'product/about.html'

    def index_template(self):
        return 'product/index.html'

    def admins_template(self):
        return 'product/admins.html'

    def bulk_process_template(self):
        return 'product/bulk_process.html'

    def read_template(self):
        return 'product/read.html'

    # don't override history_template - use group template for history

    def edit_template(self):
        return 'product/edit.html'

    def activity_template(self):
        return 'product/activity_stream.html'


class CdrcLadPlugin(plugins.SingletonPlugin, DefaultGroupForm):
    plugins.implements(plugins.IGroupForm)
    plugins.implements(plugins.IRoutes)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)

    def is_fallback(self):
        return False

    def group_types(self):
        return LadController.group_types

    def after_map(self, map):
        for gt in self.group_types():
            mapper_mixin(map, gt, 'ckanext.cdrc.controllers.lad:LadController')
        import sys, pprint; print >>sys.stderr, map.__class__
        return map

    def before_map(self, map):
        return map

    def get_auth_functions(self):
        auth_tmpl = {
            'lad_create': lambda c, d: ckan_auth.create.group_create(c, dict(d, type='group')),
            'lad_update': auth.group_edit,
            'lad_delete': ckan_auth.delete.group_delete,
        }
        auths = {}
        for gt in self.group_types():
            auths.update(
                {re.sub('^lad', gt, k): v for k, v in auth_tmpl.items()}
            )
        return auths

    def get_actions(self):
        action_tmpl = {
            'lad_list': action.group_list,
            'lad_show': ckan_action.get.group_show,
            'lad_activity_list_html': ckan_action.get.group_activity_list_html,
            'lad_create': ckan_action.create.group_create,
            'lad_update': ckan_action.update.group_update,
            'lad_patch': action.group_patch,
            'lad_delete': ckan_action.delete.group_delete,
        }
        actions = {}
        for gt in self.group_types():
            actions.update(
                {re.sub('^lad', gt, k): v for k, v in action_tmpl.items()}
            )
        return actions

    def group_controller(self):
        """TODO: Docstring for group_controller.
        :returns: TODO

        """
        return 'ckanext.cdrc.controllers.lad:LadController'

    def group_form(self):
        return 'lad/new_customized_group_form.html'

    def setup_template_variables(self, context, data_dict):
        pass

    def new_template(self):
        return 'lad/new.html'

    def about_template(self):
        return 'lad/about.html'

    def index_template(self):
        return 'lad/index.html'

    def admins_template(self):
        return 'lad/admins.html'

    def bulk_process_template(self):
        return 'lad/bulk_process.html'

    def read_template(self):
        return 'lad/read.html'

    # don't override history_template - use group template for history

    def edit_template(self):
        return 'lad/edit.html'

    def activity_template(self):
        return 'lad/activity_stream.html'


class CdrcAcclvlPlugin(plugins.SingletonPlugin, DefaultGroupForm):
    plugins.implements(plugins.IGroupForm)
    plugins.implements(plugins.IRoutes)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)

    def is_fallback(self):
        return False

    def group_types(self):
        return ['accesslevel']

    def after_map(self, map):
        mapper_mixin(map, 'accesslevel', 'ckanext.cdrc.controllers.accesslevel:AccessLevelController')
        return map

    def before_map(self, map):
        return map

    def get_auth_functions(self):
        return {
            'accesslevel_create': lambda c, d: ckan_auth.create.group_create(c, dict(d, type='group')),
            'accesslevel_update': auth.group_edit,
            'accesslevel_delete': ckan_auth.delete.group_delete,
        }

    def get_actions(self):
        return {
            'accesslevel_list': action.group_list,
            'accesslevel_show': ckan_action.get.group_show,
            'accesslevel_activity_list_html': ckan_action.get.group_activity_list_html,
            'accesslevel_create': ckan_action.create.group_create,
            'accesslevel_update': ckan_action.update.group_update,
            'accesslevel_patch': action.group_patch,
            'accesslevel_delete': ckan_action.delete.group_delete,
        }

    def group_controller(self):
        """TODO: Docstring for group_controller.
        :returns: TODO

        """
        return 'ckanext.cdrc.controllers.accesslevel:AccessLevelController'

    def group_form(self):
        return 'accesslevel/new_customized_group_form.html'

    def setup_template_variables(self, context, data_dict):
        pass

    def new_template(self):
        return 'accesslevel/new.html'

    def about_template(self):
        return 'accesslevel/about.html'

    def index_template(self):
        return 'accesslevel/index.html'

    def admins_template(self):
        return 'accesslevel/admins.html'

    def bulk_process_template(self):
        return 'accesslevel/bulk_process.html'

    def read_template(self):
        return 'accesslevel/read.html'

    # don't override history_template - use group template for history

    def edit_template(self):
        return 'accesslevel/edit.html'

    def activity_template(self):
        return 'accesslevel/activity_stream.html'

