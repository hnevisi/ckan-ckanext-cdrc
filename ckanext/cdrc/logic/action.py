"""
File: action.py
Author: Wen Li
Email: spacelis@gmail.com
Github: http://github.com/spacelis
Description: Extending the set of actions to facilitate this plugin.
"""

import os
import re
import json
import sqlalchemy
from sqlalchemy import func
from sqlalchemy import or_
from paste.deploy.converters import asbool, aslist

from mock import patch
from ckan.logic import action as ckan_action
from ckan.logic import side_effect_free
from ckan.logic import check_access
from ckan.logic.action.get import _unpick_search
from ckan.logic.action.patch import group_patch as ckan_group_patch
from ckan.logic import get_action
from ckan.lib.uploader import get_storage_path
from ckan.common import c
from ckan.lib import helpers as h
import ckan.lib.dictization.model_dictize as model_dictize

from pylons import cache
from pylons import config
from subprocess import check_output, CalledProcessError
from ckan.lib.app_globals import app_globals, set_app_global

NONALPHANUMERIC = re.compile(r'[^a-z0-9_-]')
DASHES = re.compile(r'[-_]+')
DASHATEND = re.compile(r'^[-_]+|[-_]+$')

def namify(title):
    """ Generate a name from a title """
    name = NONALPHANUMERIC.subn('-', title.lower())[0]
    name = DASHES.subn('-', name)[0]
    return DASHATEND.subn('', name)[0][:95]


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
    if not is_org and group_type != 'group':
        query = query.filter(model.Group.type == group_type)

    groups = query.all()

    action = 'organization_show' if is_org else 'group_show'


    # The cache may leak private group information?
    @cache.region('short_term', 'action_group_show')
    def group_show_cached(action, group_id):
        data_dict['id'] = group_id
        return get_action(action)(context, data_dict)

    @cache.region('short_term', 'action_group_show_list')
    def group_show_list_cached(action, group_ids):
        g_list = []
        for group in group_ids:
            g_list.append(group_show_cached(action, group))
        return g_list

    g_list = group_show_list_cached(action, [g.id for g in groups])


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
        "select sum(count) from tracking_summary where tracking_type='download'"))[0][0] or 0


def get_site_statistics(context, data_dict):
    """ return package statistics, deprecated as get_action in helpers is deprecated. """
    try:
        stats = cache.get_cache_region('cdrc_data', 'long_term').get('ckan_stats')
    except:
        stats = refresh_site_statistics(context, data_dict)
    return stats

def refresh_site_statistics(context, data_dict):
    """ refresh package statistics, deprecated as get_action in helpers is deprecated. """

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
    cache.get_cache_region('cdrc_data', 'long_term').put('ckan_stats', stats)

    return stats


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


def notice_show(context, data_dict):
    """ return the stored notice
    """
    try:
        model = context['model']
        notice = model.get_system_info('cdrc.site_notice.text')
        notice_type = model.get_system_info('cdrc.site_notice.type')
        if len(notice) > 0 and len(notice_type) > 0:
            h.flash(notice, notice_type)
    except:
        pass
    return ''


def notice_update(context, data_dict):
    """ return the stored notice
    """
    check_access('notice_update', context, data_dict)
    model = context['model']
    notice = data_dict.get('text', '')
    notice_type = data_dict.get('type', 'alert-error')
    model.set_system_info('cdrc.site_notice.text', notice)
    model.set_system_info('cdrc.site_notice.type', notice_type)
    return notice

def group_list_authz(context, data_dict):
    try:
        check_access('member_create', context, data_dict)
    except:
        return []
    available_only = data_dict.get('available_only', False)
    glist = set([(g['id'], g['display_name']) for g in ckan_action.get.group_list_authz(context, data_dict)])
    for t in ['topic', 'product', 'lad', 'accesslevel']:
        glist |= set([(g['id'], g['display_name']) for g in group_list(context, {'type': t, 'all_fields': True})])

    if available_only:
        package = context.get('package')
        if package:
            glist -= set([(g['id'], g['display_name']) for g in model_dictize.group_list_dictize(package.get_groups(), context)])

    return [{'id': g[0], 'display_name': g[1]} for g in sorted(list(glist), key=lambda g: g[1].lower())]


def always_true(*arg, **kwargs):
    return True


# patching the function as the original package_create auth logic will need the
# user to have permission on all the groups which will be headache for
# managing. Now only user will be promoted to have permission when creating
# packages.
@patch('ckan.authz.has_user_permission_for_group_or_org', new=always_true)
def package_create(context, data_dict):
    """ Wrapping around the original package create and add parsers for product/topic/geography info.
    :returns: TODO

    """
    check_access('package_create', context, data_dict)
    data_dict['private'] = u'True'
    group_names = []
    if data_dict.get('tags'):
        group_names += [t['name'].lower() for t in data_dict['tags']]
    elif data_dict.get('tag_string'):
        group_names += [namify(t) for t in data_dict['tag_string'].split(',')]

    if data_dict.get('product_info'):
        product_title = data_dict['product_info']
        product_name = namify(product_title)
        product = group_list(context, {'type': 'product', 'groups': [product_name]})
        if len(product) == 0:
            ckan_action.create.group_create(context, {
                'name': product_name,
                'title': product_title,
                'type': 'product'
            })
        group_names += [product_name]

    if group_names:
        group_names = list(set([g['name'] for g in data_dict.get('groups', [])] + group_names))
        groups = [{'name': g} for g in group_list(context, {'groups': group_names})]
        data_dict['groups'] = groups
    pkg_dict = ckan_action.create.package_create(context, data_dict)
    return pkg_dict

@patch('ckan.authz.has_user_permission_for_group_or_org', new=always_true)
def package_update(context, data_dict):
    """ Wrapping around the original package create and add parsers for product/topic/geography info.
    :returns: TODO

    """
    check_access('package_create', context, data_dict)
    data_dict['private'] = u'True'
    pkg = get_action('package_show')(context, {'id': data_dict['id']})

    group_names = [g['name'] for g in pkg['groups'] if g['name'] != pkg['product_info']]
    if data_dict.get('tags'):
        group_names += [t['name'].lower() for t in data_dict['tags']]
    elif data_dict.get('tag_string'):
        group_names += [namify(t) for t in data_dict['tag_string'].split(',')]

    if data_dict.get('product_info'):
        product_title = data_dict['product_info']
        product_name = namify(product_title)
        product = group_list(context, {'type': 'product', 'groups': [product_name]})
        if len(product) == 0:
            ckan_action.create.group_create(context, {
                'name': product_name,
                'title': product_title,
                'type': 'product'
            })
        group_names += [product_name]

    if group_names:
        group_names = list(set([g['name'] for g in data_dict.get('groups', [])] + group_names))
        groups = [{'name': g} for g in group_list(context, {'groups': group_names})]
        data_dict['groups'] = groups
    pkg_dict = ckan_action.update.package_update(context, data_dict)
    return pkg_dict


def bulk_approve(context, data_dict):
    """TODO: Docstring for bulk_update_reject.
    :returns: TODO

    """
    check_access('bulk_approve', context, data_dict)
    dataset_ids = data_dict['datasets']
    for did in dataset_ids:
        get_action('member_delete')(context,{
            'id': 'disclosure-control',
            'object': did,
            'object_type': 'package',
        })
        get_action('member_delete')(context,{
            'id': 'rejected',
            'object': did,
            'object_type': 'package',
        })
    get_action('bulk_update_public')(context, data_dict)


def bulk_reject(context, data_dict):
    """TODO: Docstring for bulk_update_reject.
    :returns: TODO

    """
    check_access('bulk_reject', context, data_dict)
    dataset_ids = data_dict['datasets']
    for did in dataset_ids:
        get_action('member_create')(context,{
            'id': 'rejected',
            'object': did,
            'object_type': 'package',
            'capacity': 'public'
        })
        get_action('member_delete')(context,{
            'id': 'disclosure-control',
            'object': did,
            'object_type': 'package',
        })


def bulk_pass(context, data_dict):
    """TODO: Docstring for bulk_update_reject.
    :returns: TODO

    """
    check_access('bulk_pass', context, data_dict)
    dataset_ids = data_dict['datasets']
    for did in dataset_ids:
        get_action('member_create')(context,{
            'id': 'disclosure-control',
            'object': did,
            'object_type': 'package',
            'capacity': 'public'
        })
        get_action('member_delete')(context,{
            'id': 'rejected',
            'object': did,
            'object_type': 'package',
        })


def package_group_removeall(context, data_dict):
    check_access('package_create', context, data_dict)
    pkg = get_action('package_show')(context, {'id': data_dict['id']})
    for grp in pkg['groups']:
        get_action('member_delete')(context,{
            'id': grp['id'],
            'object': pkg['id'],
            'object_type': 'package',
        })


P_TAG = re.compile('<p>')
P_ENDTAG = re.compile('</p>')

@side_effect_free
def momconfig_show(context, data_dict):
    momconfig_key = ['title', 'tile_url', 'description', 'map_link']
    momconfig = {k: config.get('cdrc.mom.' + k) for k in momconfig_key}
    momconfig['description'] = [l.strip() for l in P_ENDTAG.sub('', P_TAG.sub('', h.render_markdown(momconfig['description']))).split('\n') if l]
    return momconfig
