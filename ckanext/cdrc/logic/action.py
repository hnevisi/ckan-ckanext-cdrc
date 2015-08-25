"""
File: action.py
Author: Wen Li
Email: spacelis@gmail.com
Github: http://github.com/spacelis
Description: Extending the set of actions to facilitate this plugin.
"""

import os
import sqlalchemy
from sqlalchemy import func
from sqlalchemy import or_
from paste.deploy.converters import asbool, aslist

from ckan.logic import check_access
from ckan.logic.action.get import _unpick_search
from ckan.logic.action.patch import group_patch as ckan_group_patch
from ckan.logic import get_action
from ckan.lib.uploader import get_storage_path
from ckan.common import c

from pylons import cache
from pylons import config
from subprocess import check_output, CalledProcessError


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


FILESIZE_UNITS = {
    'name': ['B', 'KB', 'MB', 'GB', 'TB', 'PB'],
    'base': 1024,
    'upper_bound': 99
}

SI_NUMBER_UNITS = {
    'name': ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'],
    'base': 1000,
    'upper_bound': 99
}


def unitify(number, unit_frame):
    ''' Returns a localised unicode representation of a number in bytes, MiB
    etc '''

    number = float(number)
    unit_idx = 0
    while number > unit_frame['upper_bound']:
        number = number / unit_frame['base']
        unit_idx += 1

    return number, unit_frame['name'][unit_idx]


def storage_use():
    """ Return the number of bytes used for storing resource.
    :returns: TODO

    """
    try:
        return int(check_output(['du', config['ckan.storage_path'] + '/resources', '-bs']).split('\t')[0])
    except CalledProcessError:
        return 0


def number_of_downloads(session):
    """ Return the total number of downloads from this service.
    """
    return list(session.execute(
        "select sum(running_total ) from tracking_summary where tracking_type='resource' and tracking_date = (select max(tracking_date) from tracking_summary)"))[0][0]


def get_site_statistics(context, data_dict):
    """ return package statistics, deprecated as get_action in helpers is deprecated. """

    mappings = [
        ('topic_count', len(group_list(context, {'type': 'topic'})), SI_NUMBER_UNITS),
        ('product_count', len(group_list(context, {'type': 'product'})), SI_NUMBER_UNITS),
        ('lad_count', len(group_list(context, {'type': 'lad'})), SI_NUMBER_UNITS),
        ('dataset_count', get_action('package_search')({}, {"rows": 1})['count'], SI_NUMBER_UNITS),
        ('resource_size', storage_use(), FILESIZE_UNITS),
        ('downloads', number_of_downloads(context['session']), SI_NUMBER_UNITS)
    ]

    stats = {}

    for name, number, unit_frame in mappings:
        short, unit = unitify(number, unit_frame)
        short_text = '{:.1f}'.format(short)
        if short_text.endswith('.0'):
            short_text = short_text[:-2]
        stats[name] = {
            'number': number,
            'text': '{0}{1}'.format(short_text, unit),
            'html': '{0}<span class="unit">{1}</span>'.format(short_text, unit)
        }

    return stats


def get_ga_account_ids(context, data_dict):
    """ Return the code for google analytic account.
    """
    return [('tracking_{0}'.format(i), gaid) for i, gaid in enumerate(aslist(config.get('cdrc.google_analytics.id', [])))]


def group_patch(context, data_dict):
    """ A patched version for group_patch
    """
    context['allow_partial_update'] = True
    return ckan_group_patch(context, data_dict)


def resource_clean(context, data_dict):
    """ Remove resource that is not referred by a package.

    :context: TODO
    :data_dict: TODO
    :returns: TODO

    """
    check_access('resource_clean', context, data_dict)
    model = context['model']
    confirmed = data_dict.get('confirmed', False)
    res_indb = set([r[0] for r in sqlalchemy.sql.select([model.resource_table.c.id]).execute()])
    storage_path = os.path.join(get_storage_path(), 'resources')

    dangling = []
    for l in check_output(['find', storage_path, '-type', 'f']).split('\n'):
        if l:
            rid = ''.join(l.split('/')[-3:])
            if rid not in res_indb:
                dangling.append(l)

    deleted = []
    if confirmed:
        for f in dangling:
            os.remove(f)
            deleted.append(f)

    return {'deleted': deleted,
            'deleted_count': len(deleted),
            'dangling': dangling,
            'dangling_count': len(dangling)}
