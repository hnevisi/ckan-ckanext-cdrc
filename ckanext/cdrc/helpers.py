#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Helper functions for CDRC Data.

File: helpers.py
Author: Wen Li
Email: spacelis@gmail.com
GitHub: http://github.com/spacelis
Description:


"""
# TODO: write code...
from pylons import config
import ckan.model as model
from ckan.common import (
    _, ungettext, g, c, request, session, json, OrderedDict
)
def is_admin_in_org_or_group(group_id=None, group_name=None):
    ''' Check if user is in a group or organization '''
    # we need a user
    if not c.userobj:
        return False
    # sysadmins can do anything
    if c.userobj.sysadmin:
        return True
    if not group_id:
        group_id = model.Group.get(group_name).id
    query = model.Session.query(model.Member) \
        .filter(model.Member.state == 'active') \
        .filter(model.Member.table_name == 'user') \
        .filter(model.Member.capacity == 'admin') \
        .filter(model.Member.group_id == group_id) \
        .filter(model.Member.table_id == c.userobj.id)
    return len(query.all()) != 0


def is_cdrc_admin():
    return is_admin_in_org_or_group('consumer-data-research-centre')


def get_ga_account_ids():
    """ Return the code for google analytic account.
    """
    if config.get('debug'):
        return []
    return [('tracking_{0}'.format(i), gaid) for i, gaid in enumerate(aslist(config.get('cdrc.google_analytics.id', [])))]


