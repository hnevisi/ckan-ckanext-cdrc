"""
File: topic.py
Author: Wen Li
Email: spacelis@gmail.com
Github: http://github.com/spacelis
Description:
    This controller is for the index page of lads.
"""

import re
from ckanext.cdrc.controllers.base import DefaultGroupController


class TopicController(DefaultGroupController):
    ''' This controller is for topic groups.
    '''

    group_types = ['topic']

    def __init__(self, *args, **kwargs):
        super(DefaultGroupController, self).__init__(*args, **kwargs)
        self.group_type = 'topic'

    def _guess_group_type(self, expecting_name=False):
        return 'topic'

    def _replace_group_org(self, string):
        ''' substitute organization for group if this is an org'''
        return re.sub('^group', 'topic', string)

    def items_per_page(self):
        """ return items per page
        """
        return 24
