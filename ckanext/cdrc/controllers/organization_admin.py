"""
File: blog.py
Author: Wen Li
Email: spacelis@gmail.com
Github: http://github.com/spacelis
Description:
    A blog controller that wrapping a wp in a page.
"""


from ckan.common import OrderedDict, c, g, request, _
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.model as model
import ckan.plugins as plugins
from ckan.logic import NotAuthorized, NotFound, get_action
import ckan.lib.maintain as maintain
import ckan.lib.search as search
from ckan.lib.base import abort, render
from ckan.lib.base import BaseController
from ckan.controllers.group import GroupController
from ckan import authz
import ckan.lib.search as search
from ckanext.cdrc.helpers import is_cdrc_admin


class CDRCOrgAdminController(GroupController):

    def _read(self, id, limit, group_type, q=None):
        ''' This is common code used by both read and bulk_process'''
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'schema': self._db_to_form_schema(group_type=group_type),
                   'for_view': True, 'extras_as_string': True}

        c.q = q
        # Search within group
        if c.group_dict.get('is_organization'):
            q += ' owner_org:"%s"' % c.group_dict.get('id')
        else:
            q += ' groups:"%s"' % c.group_dict.get('name')

        c.description_formatted = \
            h.render_markdown(c.group_dict.get('description'))

        context['return_query'] = True

        # c.group_admins is used by CKAN's legacy (Genshi) templates only,
        # if we drop support for those then we can delete this line.
        c.group_admins = authz.get_group_or_org_admin_ids(c.group.id)

        page = self._get_page_number(request.params)

        # most search operations should reset the page counter:
        params_nopage = [(k, v) for k, v in request.params.items()
                         if k != 'page']
        sort_by = request.params.get('sort', None)

        def search_url(params):
            controller = lookup_group_controller(group_type)
            action = 'bulk_process' if c.action == 'bulk_process' else 'read'
            url = h.url_for(controller=controller, action=action, id=id)
            params = [(k, v.encode('utf-8') if isinstance(v, basestring)
                       else str(v)) for k, v in params]
            return url + u'?' + urlencode(params)

        def drill_down_url(**by):
            return h.add_url_param(alternative_url=None,
                                   controller='group', action='read',
                                   extras=dict(id=c.group_dict.get('name')),
                                   new_params=by)

        c.drill_down_url = drill_down_url

        def remove_field(key, value=None, replace=None):
            return h.remove_url_param(key, value=value, replace=replace,
                                      controller='group', action='read',
                                      extras=dict(id=c.group_dict.get('name')))

        c.remove_field = remove_field

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            return search_url(params)

        try:
            c.fields = []
            search_extras = {}
            for (param, value) in request.params.items():
                if not param in ['q', 'page', 'sort'] \
                        and len(value) and not param.startswith('_'):
                    if not param.startswith('ext_'):
                        c.fields.append((param, value))
                        q += ' %s: "%s"' % (param, value)
                    else:
                        search_extras[param] = value

            fq = 'capacity:"public"'
            user_member_of_orgs = [org['id'] for org
                                   in h.organizations_available('read')]

            if (c.group and c.group.id in user_member_of_orgs):
                fq = ''
                context['ignore_capacity_check'] = True

            facets = OrderedDict()

            default_facet_titles = {'organization': _('Organizations'),
                                    'groups': _('Groups'),
                                    'tags': _('Tags'),
                                    'res_format': _('Formats'),
                                    'license_id': _('Licenses')}

            for facet in g.facets:
                if facet in default_facet_titles:
                    facets[facet] = default_facet_titles[facet]
                else:
                    facets[facet] = facet

            # Facet titles
            self._update_facet_titles(facets, group_type)

            if 'capacity' in facets and (group_type != 'organization' or
                                         not user_member_of_orgs):
                del facets['capacity']

            c.facet_titles = facets

            data_dict = {
                'q': q,
                'fq': fq,
                'facet.field': facets.keys(),
                'rows': limit,
                'sort': sort_by,
                'start': (page - 1) * limit,
                'extras': search_extras
            }

            context_ = dict((k, v) for (k, v) in context.items()
                            if k != 'schema')
            query = get_action('package_search')(context_, data_dict)

            c.page = h.Page(
                collection=query['results'],
                page=page,
                url=pager_url,
                item_count=query['count'],
                items_per_page=limit
            )

            c.group_dict['package_count'] = query['count']
            c.facets = query['facets']
            maintain.deprecate_context_item('facets',
                                            'Use `c.search_facets` instead.')

            c.search_facets = query['search_facets']
            c.search_facets_limits = {}
            for facet in c.facets.keys():
                limit = int(request.params.get('_%s_limit' % facet,
                                               g.facets_default_number))
                c.search_facets_limits[facet] = limit
            c.page.items = query['results']

            c.sort_by_selected = sort_by

        except search.SearchError, se:
            log.error('Group search error: %r', se.args)
            c.query_error = True
            c.facets = {}
            c.page = h.Page(collection=[])

        self._setup_template_variables(context, {'id': id},
                                       group_type=group_type)
    def format_review(self, id):
        ''' Allow bulk processing of datasets for an organization.  Make
        private/public or delete. For organization admins.'''

        # group_type = self._ensure_controller_matches_group_type(
        #     id.split('@')[0])
        #
        #
        # if group_type != 'organization':
        #     # FIXME: better error
        #     raise Exception('Must be an organization')
        group_type = 'organization'

        # check we are org admin

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'schema': self._db_to_form_schema(group_type=group_type),
                   'for_view': True, 'extras_as_string': True}
        data_dict = {'id': id}

        try:
            # Do not query for the group datasets when dictizing, as they will
            # be ignored and get requested on the controller anyway
            data_dict['include_datasets'] = False
            c.group_dict = self._action('organization_show')(context, data_dict)
            c.group = context['group']
        except NotFound:
            abort(404, _('Group not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read group %s') % id)

        #use different form names so that ie7 can be detected
        form_names = set(["bulk_action.approve", "bulk_action.delete",
                          "bulk_action.pass", "bulk_action.reject"])
        actions_in_form = set(request.params.keys())
        actions = form_names.intersection(actions_in_form)
        # If no action then just show the datasets
        if not actions:
            # unicode format (decoded from utf8)
            limit = 500
            self._read(id, limit, group_type, 'capacity:private AND -groups:disclosure-control AND -groups:rejected')
            c.packages = c.page.items
            return render('organization/dataset_review.html',
                          extra_vars={'group_type': group_type, 'review': 'format'})

        #ie7 puts all buttons in form params but puts submitted one twice
        for key, value in dict(request.params.dict_of_lists()).items():
            if len(value) == 2:
                action = key.split('.')[-1]
                break
        else:
            #normal good browser form submission
            action = actions.pop().split('.')[-1]

        # process the action first find the datasets to perform the action on.
        # they are prefixed by dataset_ in the form data
        datasets = []
        for param in request.params:
            if param.startswith('dataset_'):
                datasets.append(param[8:])

        action_functions = {
            'approve': 'bulk_approve',
            'delete': 'bulk_update_delete',
            'reject': 'bulk_reject',
            'pass': 'bulk_pass',
        }

        data_dict = {'datasets': datasets, 'org_id': c.group_dict['id']}

        try:
            get_action(action_functions[action])(context, data_dict)
        except NotAuthorized:
            abort(401, _('Not authorized to perform bulk update'))
        base.redirect(h.url_for(controller='ckanext.cdrc.controllers.organization_admin:CDRCOrgAdminController',
                                action='format_review',
                                id=id))


    def disclosure_review(self, id):
        ''' Allow bulk processing of datasets for an organization.  Make
        private/public or delete. For organization admins.'''

        # group_type = self._ensure_controller_matches_group_type(
        #     id.split('@')[0])
        #
        #
        # if group_type != 'organization':
        #     # FIXME: better error
        #     raise Exception('Must be an organization')
        group_type = 'organization'

        # check we are org admin

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'schema': self._db_to_form_schema(group_type=group_type),
                   'for_view': True, 'extras_as_string': True}
        data_dict = {'id': id}

        try:
            # Do not query for the group datasets when dictizing, as they will
            # be ignored and get requested on the controller anyway
            data_dict['include_datasets'] = False
            c.group_dict = self._action('organization_show')(context, data_dict)
            c.group = context['group']
        except NotFound:
            abort(404, _('Group not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read group %s') % id)

        #use different form names so that ie7 can be detected
        form_names = set(["bulk_action.approve", "bulk_action.delete",
                          "bulk_action.reject"])
        actions_in_form = set(request.params.keys())
        actions = form_names.intersection(actions_in_form)
        # If no action then just show the datasets
        if not actions:
            # unicode format (decoded from utf8)
            limit = 500
            self._read(id, limit, group_type, 'capacity:private AND groups:disclosure-control AND -groups:rejected')
            c.packages = c.page.items
            return render('organization/dataset_review.html',
                          extra_vars={'group_type': group_type, 'review': 'disclosure'})

        #ie7 puts all buttons in form params but puts submitted one twice
        for key, value in dict(request.params.dict_of_lists()).items():
            if len(value) == 2:
                action = key.split('.')[-1]
                break
        else:
            #normal good browser form submission
            action = actions.pop().split('.')[-1]

        # process the action first find the datasets to perform the action on.
        # they are prefixed by dataset_ in the form data
        datasets = []
        for param in request.params:
            if param.startswith('dataset_'):
                datasets.append(param[8:])

        action_functions = {
            'approve': 'bulk_approve',
            'reject': 'bulk_reject',
            'delete': 'bulk_update_delete',
        }

        data_dict = {'datasets': datasets, 'org_id': c.group_dict['id']}

        try:
            get_action(action_functions[action])(context, data_dict)
        except NotAuthorized:
            abort(401, _('Not authorized to perform bulk update'))
        base.redirect(h.url_for(controller='ckanext.cdrc.controllers.organization_admin:CDRCOrgAdminController',
                                action='disclosure_review',
                                id=id))
    def cdrc_admin(self):
        """TODO: Docstring for org_admin.
        :returns: TODO

        """
        if not c.user:
            h.redirect_to(locale=locale, controller='user', action='login',
                          id=None)
        if is_cdrc_admin():
            h.redirect_to('/organization/format_review/consumer-data-research-centre')
        else:
            h.redirect_to('/dashboard')
