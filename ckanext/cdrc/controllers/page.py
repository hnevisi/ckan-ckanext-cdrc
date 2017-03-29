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
from ckan import logic
from ckan.logic import NotAuthorized
from ckan.lib.base import abort, render
from ckan.lib.base import BaseController

class CDRCBlogController(BaseController):
    def blog_proxy(self):
        return render("page/blog.html", extra_vars={'src_url': h.url('/', locale='default', qualified=False) + '_blog/'})


class CDRCPageController(BaseController):

    def _get_pkg(self, pkg_id, pkg_tag='Practical'):
        """ Return the pkg dict if it has the given tag"""
        context = {'model': model, 'session': model.Session,
                   'user': c.user}
        pkg = logic.get_action('package_show')(context, {'id': pkg_id})
        if pkg_tag.lower() in (t['name'].lower() for t in pkg['tags']):
            return pkg
        else:
            return None

    def _get_pkg_list(self, pkg_tag='Practical'):
        """ Return the pkg dict if it has the given tag"""
        context = {'model': model, 'session': model.Session,
                   'user': c.user}
        pkgs = logic.get_action('package_search')(context, {'fq': 'tags:' + pkg_tag})
        return pkgs

    def page_list(self, pkg_id, pkg_tag='Practical'):
        pkg = self._get_pkg(pkg_id)
        assert pkg is not None
        page_list = [{
            'title': r['name'],
            'description': r['description'],
            'id': r['id'],
            'package_id': pkg['name']
        } for r in pkg['resources']]
        return render("page/page_list.html", extra_vars={'page_list': page_list, 'subtitle': pkg['title'], 'pkg_id': pkg['name']})

    def index(self, pkg_tag='Practical'):
        found = self._get_pkg_list()
        assert found['count'] > 0

        pkg_list = [{
            'title': p['title'],
            'description': p['notes'],
            'pkg_id': p['name'],
        } for p in found['results']]
        return render("page/index.html", extra_vars={'pkg_list': pkg_list, 'subtitle': pkg_tag})

    def page_show(self, pkg_id, page_id):
        pkg = self._get_pkg(pkg_id)
        assert pkg is not None
        resource = [r for r in pkg['resources'] if r['id'] == page_id]
        assert len(resource) > 0
        res = resource[0]
        return render("page/page.html", extra_vars={
            'src_url': '//' + res['url'].split('://', 1)[1],
            'pkg_id': pkg['name'],
            'page_id': res['id'],
            'subtitle': res['name'],
                'pkg_name': pkg['title']
        })
