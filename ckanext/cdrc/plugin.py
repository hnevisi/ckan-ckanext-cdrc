from textwrap import dedent
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.cdrc.logic import auth


class CdrcPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IAuthFunctions)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic/css', 'css')
        toolkit.add_resource('fanstatic', 'cdrc')
        config_['ckan.site_logo'] = '/images/CDRC Col.jpg'
        config_['ckan.site_description'] = dedent(
            ''' CDRC Data Cloud is a platform for data discovering, data analytics, data comprehension.
            ''')
        config_['ckan.favicon'] = '/images/CDRC_fav.png'
        config_['ckan.site_about'] = dedent(
            '''
            <h1>
            Welcome to the Consumer Data Research Centre (CDRC).
            </h1>
            <p>
            We are an academic led, multi-institution laboratory which discovers, mines, analyses and synthesises consumer-related datasets from around the UK. The CDRC is an ESRC Data Investment.
            </p>
            '''
        )
        config_['ckan.site_title'] = 'CDRC Data Cloud'
        config_['ckan.main_css'] = '/base/cdrc/css/main.css'


    def get_auth_functions(self):
        return {'resource_download': auth.resource_download}
