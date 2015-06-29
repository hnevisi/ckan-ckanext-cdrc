"""
File: auth.py
Author: Wen Li
Email: wen.li@ucl.ac.uk
Github: http://github.com/spacelis
Description: CDRC auth plugin
"""


from ckan.logic import authz
import ckan.plugins.toolkit as toolkit

def resource_download(context, data_dict):
    try:
        context_user = toolkit.c.user
    except TypeError:
        context_user = None
    assert False
    return toolkit.asbool(context_user)
