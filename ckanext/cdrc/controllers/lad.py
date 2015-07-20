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


class LadController(DefaultGroupController):
    ''' This controller is for lad groups.
    '''

    group_types = ['lad']

    def __init__(self, *args, **kwargs):
        super(DefaultGroupController, self).__init__(*args, **kwargs)
        self.group_type = 'lad'

    def _guess_group_type(self, expecting_name=False):
        return 'lad'

    def _replace_group_org(self, string):
        ''' substitute organization for group if this is an org'''
        return re.sub('^group', 'lad', string)

    def items_per_page(self):
        """ return items per page
        """
        return 20
