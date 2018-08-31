# This file is a part of the AnyBlok project
#
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from .plugins import ModelPluginBase
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import DDLElement
from sqlalchemy.sql import table
from sqlalchemy.orm import Query, mapper, relationship
from .exceptions import ViewException
from .common import VIEW, MODEL
from anyblok.common import anyblok_column_prefix


class CreateView(DDLElement):
    def __init__(self, name, selectable):
        self.name = name
        self.selectable = selectable


class DropView(DDLElement):
    def __init__(self, name):
        self.name = name


@compiles(CreateView)
def compile_create_view(element, compiler, **kw):
    return "CREATE VIEW %s AS %s" % (
        element.name, compiler.sql_compiler.process(element.selectable))


@compiles(DropView)
def compile_drop_view(element, compiler, **kw):
    return "DROP VIEW IF EXISTS %s" % (element.name)


class ViewPlugin(ModelPluginBase):

    def insert_core_bases(self, bases, properties):
        if properties.get('type', MODEL) == VIEW:
            bases.extend(
                [x for x in self.registry.loaded_cores['SqlViewBase']])
            bases.extend([x for x in self.registry.loaded_cores['Base']])

    def build_base(self, modelname, bases, properties):
        if properties.get('type', MODEL) == VIEW:
            Model = type(modelname, tuple(bases), properties)
            self.apply_view(Model, properties)
            return Model

    def apply_view(self, base, properties):
        """ Transform the sqlmodel to view model

        :param base: Model cls
        :param properties: properties of the model
        :exception: MigrationException
        :exception: ViewException
        """
        tablename = base.__tablename__
        if hasattr(base, '__view__'):
            view = base.__view__
        elif tablename in self.registry.loaded_views:
            view = self.registry.loaded_views[tablename]
        else:
            if not hasattr(base, 'sqlalchemy_view_declaration'):
                raise ViewException(
                    "%r.'sqlalchemy_view_declaration' is required to "
                    "define the query to apply of the view" % base)

            view = table(tablename)
            self.registry.loaded_views[tablename] = view
            selectable = getattr(base, 'sqlalchemy_view_declaration')()

            if isinstance(selectable, Query):
                selectable = selectable.subquery()

            for c in selectable.c:
                c._make_proxy(view)

            DropView(tablename).execute_at(
                'before-create', self.registry.declarativebase.metadata)
            CreateView(tablename, selectable).execute_at(
                'after-create', self.registry.declarativebase.metadata)
            DropView(tablename).execute_at(
                'before-drop', self.registry.declarativebase.metadata)

        pks = [col for col in properties['loaded_columns']
               if getattr(getattr(base, anyblok_column_prefix + col),
                          'primary_key', False)]

        if not pks:
            raise ViewException(
                "%r have any primary key defined" % base)

        pks = [getattr(view.c, x) for x in pks]

        mapper_properties = {}
        for field in properties['loaded_columns']:
            if not hasattr(properties[anyblok_column_prefix + field],
                           'anyblok_field'):
                mapper_properties[field] = getattr(view.c, field)
            else:
                anyblok_field = properties[
                    anyblok_column_prefix + field].anyblok_field
                kwargs = anyblok_field.kwargs.copy()
                if 'foreign_keys' in kwargs:
                    foreign_keys = kwargs['foreign_keys'][1:][:-1].split(', ')
                    foreign_keys = [getattr(view.c, x.split('.')[1])
                                    for x in foreign_keys]
                    kwargs['foreign_keys'] = foreign_keys

                mapper_properties[field] = relationship(
                    self.registry.get(anyblok_field.model.model_name), **kwargs)

        setattr(base, '__view__', view)
        __mapper__ = mapper(
            base, view, primary_key=pks, properties=mapper_properties)
        setattr(base, '__mapper__', __mapper__)
