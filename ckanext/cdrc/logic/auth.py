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

@toolkit.auth_allow_anonymous_access
def resource_download(context, data_dict):
    logged_in = True if context.get('auth_user_obj') else False
    is_preview = get_action('resource_show')(context, data_dict)['name'] in ['preview.geojson']
    return {'success': logged_in or is_preview,
            'msg': 'Please login to download the resources.'
            }
