"""
File: auth.py
Author: Wen Li
Email: wen.li@ucl.ac.uk
Github: http://github.com/spacelis
Description: CDRC auth plugin
"""


from ckan.logic import authz
import ckan.plugins.toolkit as toolkit
from ckan.logic import get_action
from ckan.logic import auth as ckan_auth

@toolkit.auth_allow_anonymous_access
def resource_download(context, data_dict):
    logged_in = True if context.get('auth_user_obj') else False
    is_preview = get_action('resource_show')(context, data_dict)['name'] in ['preview.geojson']
    return {'success': logged_in or is_preview,
            'msg': 'Please login to download the resources.'
            }

def product_create(context, data_dict):
    """ check whether user are allowed to create products.
    """
    return ckan_auth.create.package_create(context, {'owner_org': 'consumer-data-research-centre'})


def resource_clean(context, data_dict):
    # Only sysadmin can do the cleaning
    return {'success': False}

def notice_update(context, data_dict):
    # Only sysadmin can do the cleaning
    return {'success': False}
