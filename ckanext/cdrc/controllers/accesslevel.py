"""
File: accesslevel.py
Author: Wen Li
Email: spacelis@gmail.com
Github: http://github.com/spacelis
Description:
    This controller is for the index page of lads.
"""

import re
from ckanext.cdrc.controllers.base import DefaultGroupController


class AccessLevelController(DefaultGroupController):
    ''' This controller is for accesslevel groups.
    '''

    group_types = ['accesslevel']

    def __init__(self, *args, **kwargs):
        super(DefaultGroupController, self).__init__(*args, **kwargs)
        self.group_type = 'accesslevel'

    def _guess_group_type(self, expecting_name=False):
        return 'accesslevel'

    def _replace_group_org(self, string):
        ''' substitute organization for group if this is an org'''
        return re.sub('^group', 'accesslevel', string)

    def items_per_page(self):
        """ return items per page
        """
        return 24
