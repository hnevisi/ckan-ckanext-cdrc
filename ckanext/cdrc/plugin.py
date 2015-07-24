import logging
from textwrap import dedent
from routes.mapper import SubMapper

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.logic import auth as ckan_auth
from ckan.logic import action as ckan_action
from ckan.lib.base import BaseController
from ckan.lib.plugins import DefaultGroupForm
import ckan.lib.fanstatic_resources as fanstatic_resources
from ckanext.cdrc.logic import auth
from ckanext.cdrc.helpers import get_site_statistics, group_list


log = logging.getLogger('ckanext.cdrc')


class CDRCExtController(BaseController):
    def assertfalse(self):
        assert False

    def __before__(self, action=None, **params):
        super(CDRCExtController, self)


class CdrcPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IRoutes)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IFacets)

    # IConfigurer
    def update_config(self, config_):

        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'cdrc')

        # # Patching the ckan group needs to remove default mason-grid.js
        # ckan_group = getattr(fanstatic_resources, 'base/ckan')
        # ckan_group.depends = set([r for r in ckan_group.depends if not r.relpath.endswith('media-grid.js')])
        # ckan_group.resources = set([r for r in ckan_group.depends if not r.relpath.endswith('media-grid.js')])

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


    def get_actions(self):
        return {
           'get_site_statistics': get_site_statistics,
        }

    def get_auth_functions(self):
        return {
            'resource_download': auth.resource_download,
        }

    def after_map(self, map):
        return map

    def before_map(self, map):
        map.connect('/testing/assertfalse', controller='ckanext.cdrc.plugin:CDRCExtController', action='assertfalse')
        return map

    def dataset_facets(self, facets_dict, package_type):
        del facets_dict['organization']
        del facets_dict['license_id']
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        del facets_dict['organization']
        del facets_dict['license_id']
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):
        del facets_dict['organization']
        del facets_dict['license_id']
        return facets_dict

def mapper_mixin(map, group_type, controller):
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
        m.connect('%ss_index' % (group_type,), '/%s' % (group_type), action='index')
        m.connect('/%s/list' % (group_type,), action='list')
        m.connect('/%s/new' % (group_type,), action='new')
        m.connect('/%s/{action}/{id}' % (group_type,),
                  requirements=dict(action='|'.join([
                    'delete',
                    'admins',
                    'member_new',
                    'member_delete',
                    'history'
                    ])))
        m.connect('%s_activity' % (group_type,), '/%s/activity/{id}' % (group_type,),
                  action='activity', ckan_icon='time')
        m.connect('%s_read' % (group_type,), '/%s/{id}' % (group_type,), action='read')
        m.connect('%s_about' % (group_type,), '/%s/about/{id}' % (group_type,),
                  action='about', ckan_icon='info-sign')
        m.connect('%s_read' % (group_type,), '/%s/{id}' % (group_type,), action='read',
                  ckan_icon='sitemap')
        m.connect('%s_edit' % (group_type,), '/%s/edit/{id}' % (group_type,),
                  action='edit', ckan_icon='edit')
        m.connect('%s_members' % (group_type,), '/%s/members/{id}' % (group_type,),
                  action='members', ckan_icon='group')
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
           'topic_list': group_list,
           'topic_show': ckan_action.get.group_show,
           'topic_activity_list_html': ckan_action.get.group_activity_list_html,
           'topic_create': ckan_action.create.group_create,
           'topic_update': ckan_action.update.group_update,
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
           'product_create': ckan_auth.create.group_create,
           'product_update': ckan_auth.update.group_update,
           'product_delete': ckan_auth.delete.group_delete,
        }

    def get_actions(self):
        return {
           'product_list': group_list,
           'product_show': ckan_action.get.group_show,
           'product_activity_list_html': ckan_action.get.group_activity_list_html,
           'product_create': ckan_action.create.group_create,
           'product_update': ckan_action.update.group_update,
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
        return ['lad']

    def after_map(self, map):
        mapper_mixin(map, 'lad', 'ckanext.cdrc.controllers.lad:LadController')
        return map

    def before_map(self, map):
        return map

    def get_auth_functions(self):
        return {
           'lad_create': ckan_auth.create.group_create,
           'lad_update': ckan_auth.update.group_update,
           'lad_delete': ckan_auth.delete.group_delete,
        }

    def get_actions(self):
        return {
           'lad_list': group_list,
           'lad_show': ckan_action.get.group_show,
           'lad_activity_list_html': ckan_action.get.group_activity_list_html,
           'lad_create': ckan_action.create.group_create,
           'lad_update': ckan_action.update.group_update,
           'lad_delete': ckan_action.delete.group_delete,
        }

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
