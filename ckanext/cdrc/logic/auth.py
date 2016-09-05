"""
File: auth.py
Author: Wen Li
Email: wen.li@ucl.ac.uk
Github: http://github.com/spacelis
Description: CDRC auth plugin
"""


from ckan.logic import authz
import ckan.logic as logic
import ckan.logic.auth as logic_auth
import ckan.plugins.toolkit as toolkit
from ckan.logic import get_action, check_access
from ckan.logic import auth as ckan_auth
from ckan.logic import action as ckan_action
from ckanext.cdrc import helpers

@toolkit.auth_allow_anonymous_access
def resource_download(context, data_dict):
    logged_in = True if context.get('auth_user_obj') else False
    is_preview = get_action('resource_show')(context, data_dict)['name'] in ['preview.geojson']
    return {'success': logged_in or is_preview,
            'msg': 'Please login to download the resources.'
            }

def group_edit(context, data_dict):
    """ check whether user are allowed to create products.
    """
    return ckan_auth.create.package_create(context, {'owner_org': 'consumer-data-research-centre'})


def group_create(context, data_dict):
    user = authz.get_user_id_for_username(context['user'], allow_none=True)
    group_type = data_dict.get('type', 'group')

    if not group_type == 'group':
        return {'success': check_access(group_type + '_create', context, data_dict)}

    else:
        return ckan_auth.create.group_create(context, data_dict)


def resource_clean(context, data_dict):
    # Only sysadmin can do the cleaning
    return {'success': False}

def user_list(context, data_dict):
    # Only sysadmin can do the cleaning
    return {'success': False}

def notice_update(context, data_dict):
    # Only sysadmin can do the cleaning
    return {'success': False}


def member_edit(context, data_dict):
    return ckan_auth.create.package_create(context, {'owner_org': 'consumer-data-research-centre'})


def package_create(context, data_dict):
    if data_dict and (data_dict.get('private', '') == u'False' and not helpers.is_cdrc_admin()):
        return {'success': False,
                'msg': 'You do not have the permission of publishing datasets or editing published dataset.'}
    return ckan_auth.create.package_create(context, data_dict)


def package_update(context, data_dict):
    if data_dict and (data_dict.get('private', '') == u'False' and not helpers.is_cdrc_admin()):
        return {'success': False,
                'msg': 'You do not have the permission of publishing datasets or editing published dataset.'}
    return ckan_auth.update.package_update(context, data_dict)

def bulk_pass(context, data_dict):
    """TODO: Docstring for package_admin.

    :context: TODO
    :data_dict: TODO
    :returns: TODO

    """
    return {'success': helpers.is_cdrc_admin()}

def config_option_update(context, data_dict):
    return {'success': helpers.is_cdrc_admin()}


def bulk_reject(context, data_dict):
    """TODO: Docstring for package_admin.

    :context: TODO
    :data_dict: TODO
    :returns: TODO

    """
    return {'success': helpers.is_cdrc_admin()}



def bulk_approve(context, data_dict):
    """TODO: Docstring for package_admin.

    :context: TODO
    :data_dict: TODO
    :returns: TODO

    """
    return {'success': helpers.is_cdrc_admin()}


def user_show(context, data_dict):
    """ Make sure only users themselves can view their own infomation.
    """
    user = context['user']

    try:
        user_obj = logic_auth.get_user_object(context, data_dict)
    except NotFound:
        return {'success': False, 'msg': _('User not found')}

    if not user:
        return {'success': False,
                'msg': _('Have to be logged in to edit user')}

    if user == user_obj.name:
        # Allow users to update their own user accounts.
        return {'success': True}
    else:
        # Don't allow users to update other users' accounts.
        return {'success': False,
                'msg': _('User %s not authorized to edit user %s') %
                        (user, user_obj.id)}
