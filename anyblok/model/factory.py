# This file is a part of the AnyBlok project
#
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from .exceptions import ModelFactoryException
from anyblok.field import Field, FieldException
from sqlalchemy.sql import table
from sqlalchemy.orm import Query, mapper, relationship
from .exceptions import ViewException
from anyblok.common import anyblok_column_prefix
from .view import CreateView, DropView


def has_sql_fields(bases):
    """ Tells whether the model as field or not

    :param bases: list of Model's Class
    :rtype: boolean
    """
    for base in bases:
        for p in base.__dict__.keys():
            try:
                if hasattr(getattr(base, p), '__class__'):
                    if Field in getattr(base, p).__class__.__mro__:
                        return True
            except FieldException:
                # field function case already computed
                return True

    return False


class BaseFactory:

    def __init__(self, registry):
        self.registry = registry

    def insert_core_bases(self, bases, properties):
        raise ModelFactoryException('Must be overwritten')

    def build_model(self, modelname, bases, properties):
        raise ModelFactoryException('Must be overwritten')


class ModelFactory(BaseFactory):

    def insert_core_bases(self, bases, properties):
        if has_sql_fields(bases):
            bases.extend(
                [x for x in self.registry.loaded_cores['SqlBase']])
            bases.append(self.registry.declarativebase)
        else:
            # remove tablename to inherit from a sqlmodel
            del properties['__tablename__']

        bases.extend([x for x in self.registry.loaded_cores['Base']])

    def build_model(self, modelname, bases, properties):
        return type(modelname, tuple(bases), properties)


class ViewFactory(BaseFactory):

    def insert_core_bases(self, bases, properties):
        bases.extend(
            [x for x in self.registry.loaded_cores['SqlViewBase']])
        bases.extend([x for x in self.registry.loaded_cores['Base']])

    def build_model(self, modelname, bases, properties):
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
                continue

            anyblok_field = properties[
                anyblok_column_prefix + field].anyblok_field
            kwargs = anyblok_field.kwargs.copy()
            if 'foreign_keys' in kwargs:
                foreign_keys = kwargs['foreign_keys'][1:][:-1].split(', ')
                foreign_keys = [getattr(view.c, x.split('.')[1])
                                for x in foreign_keys]
                kwargs['foreign_keys'] = foreign_keys

            Model = (
                base
                if anyblok_field.model.model_name == base.__registry_name__
                else self.registry.get(anyblok_field.model.model_name)
            )

            mapper_properties[field] = relationship(Model, **kwargs)

        setattr(base, '__view__', view)
        __mapper__ = mapper(
            base, view, primary_key=pks, properties=mapper_properties)
        setattr(base, '__mapper__', __mapper__)
