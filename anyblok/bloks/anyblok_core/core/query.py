# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from sqlalchemy.orm import query


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

    def update(self, values, lowlevel=False, **kwargs):
        if lowlevel:
            return super(Query, self).update(values, **kwargs)
        else:
            all = self.all()
            if all:
                all.update(values, flush=False)

            self.registry.flush()
            return len(all)

    def delete(self, lowlevel=False, **kwargs):
        if lowlevel:
            return super(Query, self).delete(**kwargs)
        else:
            all = self.all()
            if all:
                all.delete()

            self.registry.flush()
            return len(all)
