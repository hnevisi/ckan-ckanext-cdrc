"""
File: blog.py
Author: Wen Li
Email: spacelis@gmail.com
Github: http://github.com/spacelis
Description:
    A blog controller that wrapping a wp in a page.
    A page controller to show HTML resources in datasets with a special tag as a sub-website.
"""

import yaml
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


def link_attachment(res, attachments):
    try:
        links = yaml.load(res['description'])
        res['attachments'] = [
            {'anchor': k,
            'resource': None if v not in attachments else attachments[v]}
            for k, v in links.items()
        ]
    except:
        pass
    return res


def get_extra_items(pkg):
    try:
        extra_res = yaml.load(pkg['notes'].split('\r\n\r\n++\r\n\r\n')[1])
        return extra_res
    except:
        return []


def make_page_items(resources):
    resources = [r for r in resources if r['name'] != 'Logo']
    attachments = {r['name']: r for r in resources}
    for r in resources:
        link_attachment(r, attachments)
    for r in resources:
        if 'attachments' in r:
            for d in r['attachments']:
                d['resource']['is_attachment'] = True
    return [r for r in resources if not r.get('is_attachment', False)]



class CDRCPageController(BaseController):

    logos = {
        'tutorial': '/images/tutorial-logo.png'
    }

    def _get_pkg(self, pkg_id, pkg_tag='Tutorial'):
        """ Return the pkg dict if it has the given tag"""
        context = {'model': model, 'session': model.Session,
                   'user': c.user}
        pkg = logic.get_action('package_show')(context, {'id': pkg_id})
        if pkg_tag.lower() in (t['name'].lower() for t in pkg['tags']):
            return pkg
        else:
            return None

    def _get_pkg_list(self, pkg_tag='Tutorial'):
        """ Return the pkg dict if it has the given tag"""
        context = {'model': model, 'session': model.Session,
                   'user': c.user}
        pkgs = logic.get_action('package_search')(context, {'fq': 'tags:' + pkg_tag})
        return pkgs

    def page_list(self, pkg_id, pkg_tag='Tutorial', content='HTML'):
        try:
            context = {'model': model, 'session': model.Session,
                    'user': c.user}
            logic.check_access('package_show', context, {'id': pkg_id})
            pkg = self._get_pkg(pkg_id)
            assert pkg is not None
        except:
            abort(404)
        extra_items = get_extra_items(pkg)
        page_list = make_page_items(pkg['resources']) + extra_items
        return render("page/page_list.html", extra_vars={
            'page_list': page_list,
            'subtitle': pkg['title'],
            'pkg_id': pkg['name'],
            'pkg_tag': pkg_tag,
            'description': pkg['notes'].split('\r\n\r\n++\r\n\r\n')[0],
        })

    def index(self, pkg_tag='Tutorial'):
        found = self._get_pkg_list()
        if not (found['count'] > 0):
            abort(404)

        pkg_list = [{
            'title': p['title'],
            'description': p['notes'],
            'pkg_id': p['name'],
            'image_url': ([r['url'] for r in p['resources'] if r['name'] == 'Logo'] + [None])[0]
        } for p in found['results']]
        return render("page/index.html", extra_vars={
            'pkg_list': pkg_list,
            'subtitle': pkg_tag,
            'pkg_tag': pkg_tag,
        })

    def page_show(self, pkg_id, page_id, pkg_tag='Tutorial'):
        pkg = self._get_pkg(pkg_id)
        if pkg is None:
            abort(404)
        resource = [r for r in pkg['resources'] if r['id'] == page_id]
        if not len(resource) > 0:
            abort(404)
        res = resource[0]
        context = {'model': model, 'session': model.Session,
                   'user': c.user}
        try:
            logic.check_access('resource_download', context, {'id': page_id})
        except:
            h.flash_error('Please login to continue...')
            h.redirect_to(
                controller='user', action='login',
                id=None,
                came_from=h.url_for(
                    controller='ckanext.cdrc.controllers.page:CDRCPageController',
                    action='page_show',
                    pkg_id=pkg_id,
                    page_id=page_id,
                    pkg_tag=pkg_tag))
        return render("page/page.html", extra_vars={
            'src_url': '//' + res['url'].split('://', 1)[1],
            'pkg_id': pkg['name'],
            'page_id': res['id'],
            'subtitle': res['name'],
            'pkg_name': pkg['title'],
            'notes': pkg['notes'],
            'pkg_tag': pkg_tag
        })
