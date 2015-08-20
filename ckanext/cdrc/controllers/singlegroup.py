"""
File: catelog.py
Author: Wen Li
Email: spacelis@gmail.com
Github: http://github.com/spacelis
Description:
    This controller is for the catelog groups.
"""

import re
from ckanext.cdrc.controllers.base import DefaultGroupController


class SingleGroupController(DefaultGroupController):
    ''' This controller is for topic groups.
    '''

    def read_national(self, limit=20):
        return self.read('national', limit)

    def read_regional(self, limit=20):
        return self.read('regional', limit)
