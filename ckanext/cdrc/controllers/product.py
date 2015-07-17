"""
File: product.py
Author: Wen Li
Email: spacelis@gmail.com
Github: http://github.com/spacelis
Description:
    This controller is used for improve index page loading time.
"""

import re
from ckanext.cdrc.controllers.base import DefaultGroupController


class ProductController(DefaultGroupController):
    ''' This controller is for product groups.
    '''

    group_types = ['product']

    def __init__(self, *args, **kwargs):
        super(DefaultGroupController, self).__init__(*args, **kwargs)
        self.group_type = 'product'

    def _guess_group_type(self, expecting_name=False):
        return 'product'

    def _replace_group_org(self, string):
        ''' substitute organization for group if this is an org'''
        return re.sub('^group', 'product', string)
