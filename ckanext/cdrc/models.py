"""
File: models.py
Author: Wen Li
Email: spacelis@gmail.com
Github: http://github.com/spacelis
Description: DB models used in this plugin.
The view extension to SQLAlchemy is from
https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/Views
"""

from sqlalchemy import select, func
from sqlalchemy.orm import Query
from sqlalchemy.schema import DDLElement
from sqlalchemy.sql import table
from sqlalchemy.ext.compiler import compiles
from ckan import model

metadata = model.repo.metadata

class CreateView(DDLElement):
    def __init__(self, name, selectable):
        self.name = name
        self.selectable = selectable


class DropView(DDLElement):
    def __init__(self, name):
        self.name = name


@compiles(CreateView)
def compile_create_view(element, compiler, **kw):
    return "CREATE VIEW %s AS %s" % (element.name, compiler.sql_compiler.process(element.selectable))


@compiles(DropView)
def compile_drop_view(element, compiler, **kw):
    return "DROP VIEW IF EXISTS %s" % (element.name)


def View(name, metadata, selectable):
    """
        `View` support for SQLAlchemy
        See: http://www.sqlalchemy.org/trac/wiki/UsageRecipes/Views
    """

    t = table(name)

    if isinstance(selectable, Query):
        selectable = selectable.subquery()

    for c in selectable.c:
        c._make_proxy(t)

    CreateView(name, selectable).execute_at('after-create', metadata)
    DropView(name).execute_at('before-drop', metadata)

    return t

group_pkg_counts = View('group_pkg_counts', metadata,
                        select([model.Member.group_id, func.count(model.Member.group_id).label('cnt')])
                        .select_from(model.Member)
                        .where(model.Member.table_name == 'package')
                        .group_by(model.Member.group_id)
                        )
# metadata.create_all(tables=[group_pkg_counts])
