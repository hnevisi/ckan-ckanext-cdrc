import logging
from textwrap import dedent
import sqlalchemy
from sqlalchemy import func
from sqlalchemy import or_
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.logic import auth as ckan_auth
from ckan.logic import action as ckan_action
from ckan.logic import get_action as get_action
from ckan.logic import check_access
from ckan.logic.action.get import _unpick_search
from ckan.common import c
from ckan.lib.base import BaseController
from ckan.lib.plugins import DefaultGroupForm
from routes.mapper import SubMapper
from ckanext.cdrc.logic import auth

from paste.deploy.converters import asbool

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


    # IConfigurer

    def update_config(self, config_):

        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic/css', 'css')
        toolkit.add_resource('fanstatic', 'cdrc')
        config_['ckan.site_logo'] = '/images/CDRC Col.jpg'
        config_['ckan.site_description'] = dedent(
            ''' CDRC Data Cloud is a platform for data discovering, data analytics, data comprehension.
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
        config_['ckan.site_title'] = 'CDRC Data Cloud'
        config_['ckan.main_css'] = '/base/cdrc/css/main.css'


    def get_auth_functions(self):
        return {
            'resource_download': auth.resource_download,
        }

    def after_map(self, map):
        return map

    def before_map(self, map):
        map.connect('/testing/assertfalse', controller='ckanext.cdrc.plugin:CDRCExtController', action='assertfalse')
        return map


def mapper_mixin(map, group_type, controller):
    """ Mixin for group types

    :map: TODO
    :group_type: TODO
    :returns: TODO

    """
    GET = dict(method=['GET'])
    PUT = dict(method=['PUT'])
    POST = dict(method=['POST'])
    DELETE = dict(method=['DELETE'])
    GET_POST = dict(method=['GET', 'POST'])
    PUT_POST = dict(method=['PUT', 'POST'])
    PUT_POST_DELETE = dict(method=['PUT', 'POST', 'DELETE'])
    OPTIONS = dict(method=['OPTIONS'])
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


def group_list(context, data_dict):
    """ A fix for the efficiency of group_list"""
    is_org = False

    check_access('group_list', context, data_dict)

    model = context['model']
    api = context.get('api_version')
    groups = data_dict.get('groups')
    group_type = data_dict.get('type', 'group')
    ref_group_by = 'id' if api == 2 else 'name'
    lite_list = data_dict.get('lite_list', False)

    sort = data_dict.get('sort', 'name')
    q = data_dict.get('q')

    # order_by deprecated in ckan 1.8
    # if it is supplied and sort isn't use order_by and raise a warning
    order_by = data_dict.get('order_by', '')
    if order_by:
        log.warn('`order_by` deprecated please use `sort`')
        if not data_dict.get('sort'):
            sort = order_by

    # if the sort is packages and no sort direction is supplied we want to do a
    # reverse sort to maintain compatibility.
    if sort.strip() in ('packages', 'package_count'):
        sort = 'package_count desc'

    sort_info = _unpick_search(sort,
                               allowed_fields=['name', 'packages',
                                               'package_count', 'title'],
                               total=1)

    all_fields = data_dict.get('all_fields', None)
    include_extras = all_fields and \
                     asbool(data_dict.get('include_extras', False))

    query = model.Session.query(model.Group)
    if include_extras:
        # this does an eager load of the extras, avoiding an sql query every
        # time group_list_dictize accesses a group's extra.
        query = query.options(sqlalchemy.orm.joinedload(model.Group._extras))

    query = query.filter(model.Group.state == 'active')
    if groups:
        query = query.filter(model.Group.name.in_(groups))
    if q:
        q = u'%{0}%'.format(q)
        query = query.filter(sqlalchemy.or_(
            model.Group.name.ilike(q),
            model.Group.title.ilike(q),
            model.Group.description.ilike(q),
        ))

    query = query.filter(model.Group.is_organization == is_org)
    if not is_org:
        query = query.filter(model.Group.type == group_type)

    if lite_list:
        package_member = model.Session.query(model.Member.group_id).filter(model.Member.table_name == 'package').subquery()
        query = query.add_column(func.count(package_member.c.group_id))\
            .outerjoin(package_member, model.Group.id == package_member.c.group_id)\
            .group_by(model.Group.id)
        groups = query.all()
        g_list = [{'id': g[0].id,
                       'name': g[0].name,
                       'display_name': g[0].title or g[0].name,
                       'type': g[0].type,
                       'description': g[0].description,
                       'image_display_url': g[0].image_url,
                       'package_count': g[1]}
                      for g in groups]

    else:
        groups = query.all()

        action = 'organization_show' if is_org else 'group_show'

        g_list = []
        for group in groups:
            data_dict['id'] = group.id
            g_list.append(get_action(action)(context, data_dict))

    g_list = sorted(g_list, key=lambda x: x[sort_info[0][0]],
        reverse=sort_info[0][1] == 'desc')

    if not all_fields:
        g_list = [group[ref_group_by] for group in g_list]

    return g_list


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


