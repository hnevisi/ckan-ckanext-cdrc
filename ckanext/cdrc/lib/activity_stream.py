"""
File: activity_stream.py
Author: Wen Li
Email: spacelis@gmail.com
Github: http://github.com/spacelis
Description: Patching functions in the CKAN to allow recording approving process

"""

from ckan.logic.schema import default_create_activity_schema
from ckan.logic import get_action
from ckan.lib.activity_streams import activity_stream_string_functions
from ckan.lib.activity_streams import activity_stream_string_icons
from ckan.logic.validators import object_id_validators, package_id_exists
from ckan.common import _


# patching the dicts from the ckan to add new activity types

def activity_stream_string_approved_package(context, activity):
    return _("{actor} approved the dataset {dataset}")

def activity_stream_string_rejected_package(context, activity):
    return _("{actor} rejected the dataset {dataset}")

def activity_stream_string_raised_package(context, activity):
    return _("{actor} raised the dataset {dataset} to disclosure control")

activity_stream_string_functions.update({
    'approved package': activity_stream_string_approved_package,
    'rejected package': activity_stream_string_rejected_package,
    'raised package': activity_stream_string_raised_package
})

activity_stream_string_icons.update({
    'approved package': 'thumbs-up',
    'rejected package': 'ban-circle',
    'raised package': 'flag',
    'new package': 'plus',
    'changed package': 'pencil'
})

object_id_validators.update({
    'approved package' : package_id_exists,
    'rejected package' : package_id_exists,
    'raised package' : package_id_exists,
})


def record_pkg_activity(context, pkg, activity_type):
    """ record the activity in the database """

    activity_dict = {
        'user_id': context['model'].User.by_name(context['user'].decode('utf8')).id,
        'object_id': pkg['id'],
        'activity_type': activity_type
    }
    activity_dict['data'] = {
        'package': pkg
    }
    activity_create_context = {
        'model': context['model'],
        'user': context['user'],
        'defer_commit': False,
        'ignore_auth': True,
        'session': context['session']
    }
    get_action('activity_create')(activity_create_context, activity_dict)
