from textwrap import dedent
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


class CdrcPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'cdrc')
        config_['ckan.site_logo'] = '/images/CDRC_logo_white.png'
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
