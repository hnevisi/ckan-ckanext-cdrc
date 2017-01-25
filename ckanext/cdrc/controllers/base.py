"""
File: base.py
Author: Wen Li
Email: spacelis@gmail.com
Github: http://github.com/spacelis
Description:
"""

from ckan.common import OrderedDict, c, g, request, _
import ckan.lib.helpers as h
import ckan.model as model
import ckan.controllers.group as group
import ckan.plugins as plugins
from ckan.logic import NotAuthorized
from ckan.lib.base import abort, render


class DefaultGroupController(group.GroupController):

    """ Default index page """

    def index(self):
        group_type = self._guess_group_type()

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'with_private': False}

        q = c.q = request.params.get('q', '')
        data_dict = {'all_fields': True, 'q': q, 'type': group_type or 'group', 'hide_empty': True}
        sort_by = c.sort_by_selected = request.params.get('sort')
        if sort_by:
            data_dict['sort'] = sort_by
        try:
            self._check_access('site_read', context)
        except NotAuthorized:
            abort(401, _('Not authorized to see this page'))

        # pass user info to context as needed to view private datasets of
        # orgs correctly
        if c.userobj:
            context['user_id'] = c.userobj.id
            context['user_is_admin'] = c.userobj.sysadmin

        results = self._action('group_list')(context, data_dict)

        c.page = h.Page(
            collection=results,
            page = self._get_page_number(request.params),
            url=h.pager_url,
            items_per_page=self.items_per_page()
        )
        return render(self._index_template(group_type),
                      extra_vars={'group_type': group_type})

