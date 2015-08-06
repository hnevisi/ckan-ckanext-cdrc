"""
File: helpers.py
Author: Wen Li
Email: spacelis@gmail.com
Github: http://github.com/spacelis
Description: The helper functions for CDRC plugin
"""

import sqlalchemy
from sqlalchemy import func
from sqlalchemy import or_
from paste.deploy.converters import asbool, aslist

from ckan.logic import check_access
from ckan.logic.action.get import _unpick_search
from ckan.logic.action.patch import group_patch as ckan_group_patch
from ckan.logic import get_action
from ckan.common import c

from pylons import cache
from pylons import config


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

    groups = query.all()

    action = 'organization_show' if is_org else 'group_show'

    g_list = []


    # The cache may leak private group information?
    @cache.region('short_term')
    def group_show_cached(action, group_id):
        data_dict['id'] = group_id
        return get_action(action)(context, data_dict)

    for group in groups:
        g_list.append(group_show_cached(action, group.id))


    g_list = sorted(g_list, key=lambda x: x[sort_info[0][0]],
        reverse=sort_info[0][1] == 'desc')

    if not all_fields:
        g_list = [group[ref_group_by] for group in g_list]

    return g_list


def get_site_statistics(context, data_dict):
    """ return package statistics, deprecated as get_action in helpers is deprecated. """

    return {
        'topic_count': len(group_list(context, {'type': 'topic'})),
        'product_count': len(group_list(context, {'type': 'product'})),
        'lad_count': len(group_list(context, {'type': 'lad'})),
        'dataset_count': get_action('package_search')({}, {"rows": 1})['count']
    }


def get_ga_account_ids(context, data_dict):
    """ Return the code for google analytic account.
    """
    return [('tracking_{0}'.format(i), gaid) for i, gaid in enumerate(aslist(config.get('cdrc.google_analytics.id', [])))]


def group_patch(context, data_dict):
    """ A patched version for group_patch
    """
    context['allow_partial_update'] = True
    return ckan_group_patch(context, data_dict)
