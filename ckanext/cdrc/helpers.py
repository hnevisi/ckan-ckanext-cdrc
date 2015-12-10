
import ckan.model as model
from ckan.common import (
    _, ungettext, g, c, request, session, json, OrderedDict
)
def is_admin_in_org_or_group(group_id):
    ''' Check if user is in a group or organization '''
    # we need a user
    if not c.userobj:
        return False
    # sysadmins can do anything
    if c.userobj.sysadmin:
        return True
    query = model.Session.query(model.Member) \
        .filter(model.Member.state == 'active') \
        .filter(model.Member.table_name == 'user') \
        .filter(model.Member.capacity == 'admin') \
        .filter(model.Member.group_id == group_id) \
        .filter(model.Member.table_id == c.userobj.id)
    return len(query.all()) != 0


def is_cdrc_admin():
    return is_admin_in_org_or_group('consumer-data-research-centre')
