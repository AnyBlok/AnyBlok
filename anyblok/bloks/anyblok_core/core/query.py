# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from ..exceptions import QueryException
from sqlalchemy.orm import query
from inspect import ismethod


@Declarations.register(Declarations.Core)
class Query(query.Query):
    """ Overload the SqlAlchemy Query
    """

    def all(self):
        """ Return an instrumented list of the result of the query
        """
        return self.registry.InstrumentedList(super(Query, self).all())

    def sqlalchemy_query_method(self, method, *args, **kwargs):
        """ Wrapper to call a specific method by getattr
        """
        return getattr(query.Query, method)(self, *args, **kwargs)

    @classmethod
    def get_on_model_methods(cls):
        """ Return  the list of the method which can be wrapped by
        ``sqlalchemy_query_method`` method

        :rtype: list of the method name
        """
        return ['update', 'delete']

    def with_perm(self, principals, permission):
        """Add authorization pre- and post-filtering to query.

        This must be last in the construction chain of the query.
        Queries too complicated for the authorization system to infer
        safely will be refused.

        :param principals: list, set or tuple of strings
        :param str permission: the permission to filter for
        :returns: a query-like object, with only the returning methods, such
                  as ``all()``, ``count()`` etc. available.
        """
        return self.registry.wrap_query_permission(
            self, principals, permission)

    def __getattribute__(self, name):
        validate = False
        model_function = "sqlalchemy_query_" + name

        if name in Query.get_on_model_methods():
            try:
                entity = self._primary_entity.mapper.entity
            except:
                pass
            else:
                if name in entity.get_on_model_methods():
                    if hasattr(entity, model_function):
                        validate = True

        if validate:

            def wrapper(*args, **kwargs):
                if ismethod(getattr(entity, model_function)):
                    return getattr(entity, model_function)(
                        self, *args, **kwargs)
                else:
                    raise QueryException("%s.%s must be a classmethod" % (
                        entity, name))

            return wrapper
        else:
            return super(Query, self).__getattribute__(name)

    def dictone(self):
        val = self.one()
        field2get = [x['name'] for x in self.column_descriptions
                     if not hasattr(x['type'], '__table__')]
        if field2get:
            return {x: getattr(val, x) for x in field2get}
        else:
            return val.to_dict()

    def dictfirst(self):
        val = self.first()
        field2get = [x['name'] for x in self.column_descriptions
                     if not hasattr(x['type'], '__table__')]
        if field2get:
            return {x: getattr(val, x) for x in field2get}
        else:
            return val.to_dict()

    def dictall(self):
        vals = self.all()
        if not vals:
            return []

        field2get = [x['name'] for x in self.column_descriptions
                     if not hasattr(x['type'], '__table__')]
        if field2get:
            return [{x: getattr(y, x) for x in field2get} for y in vals]
        else:
            return vals.to_dict()
