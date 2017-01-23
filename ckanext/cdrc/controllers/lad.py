"""
File: lad.py
Author: Wen Li
Email: spacelis@gmail.com
Github: http://github.com/spacelis
Description:
    This controller is used for improve index page loading time.
"""

import re
from ckanext.cdrc.controllers.base import DefaultGroupController
from ckan.common import request


class LadController(DefaultGroupController):
    ''' This controller is for lad groups.
    '''

    group_types = ['combauth', 'lad', 'lep', 'np']

    type_names = {
        'lad': {'short': 'LAD', 'long': 'Local Authority District'},
        'lep': {'short': 'LEP', 'long': 'Local Enterprise Partnership'},
        'combauth': {'short': 'CA', 'long': 'Combined Authority'},
        'np': {'short': 'NP', 'long': 'Northern Powerhouse Region'}
    }

    def __init__(self, *args, **kwargs):
        super(DefaultGroupController, self).__init__(*args, **kwargs)
        self.group_type = self._guess_group_type()

    def _guess_group_type(self, expecting_name=False):
        for g in LadController.group_types:
            if '/'+ g + '/' in request.path or request.path.endswith('/' + g):
                return g

    def _replace_group_org(self, string):
        ''' substitute organization for group if this is an org'''
        return re.sub('^group', 'lad', string)


    def items_per_page(self):
        """ return items per page
        """
        return 20
