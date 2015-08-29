"""
File: blog.py
Author: Wen Li
Email: spacelis@gmail.com
Github: http://github.com/spacelis
Description:
    A blog controller that wrapping a wp in a page.
"""


from ckan.common import OrderedDict, c, g, request, _
import ckan.lib.helpers as h
import ckan.model as model
import ckan.plugins as plugins
from ckan.logic import NotAuthorized
from ckan.lib.base import abort, render
from ckan.lib.base import BaseController

class CDRCBlogController(BaseController):
    def blog_proxy(self):
        return render("blog.html")
