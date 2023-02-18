# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2021 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import warnings
from anyblok import Declarations
from anyblok.common import anyblok_column_prefix
from sqlalchemy.orm import query
from sqlalchemy.orm.exc import NoResultFound
from logging import getLogger


logger = getLogger(__name__)


@Declarations.register(Declarations.Core)
class Query(query.Query):
    """ Overload the SqlAlchemy Query
    """
    def set_Model(self, Model):
        self.Model = Model.__registry_name__

    def one(self):
        """Overwrite sqlalchemy one() method to improve exception message

        Add model name to query exception message
        """
        try:
            return super(Query, self).one()
        except NoResultFound as exc:
            logger.debug('On Model %r: exc %s: query %s', self.Model, str(exc),
                         str(self))
            if self.Model:
                raise exc.__class__(
                    'On Model %r: %s' % (self.Model, str(exc)))

            raise  # pragma: no cover

    def all(self):
        """ Return an instrumented list of the result of the query
        """
        return self.anyblok.InstrumentedList(super(Query, self).all())

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
        return self.anyblok.wrap_query_permission(
            self, principals, permission)

    def get_field_names_in_column_description(self):
        field2get = [x['name'] for x in self.column_descriptions
                     if not hasattr(x['type'], '__table__')]
        field2get = [(x[len(anyblok_column_prefix):]
                      if x.startswith(anyblok_column_prefix)
                      else x, x)
                     for x in field2get]
        return field2get

    def dictone(self):
        try:
            val = self.one()
        except NoResultFound as exc:
            msg = str(exc).replace('one()', 'dictone()')
            raise exc.__class__(msg)

        field2get = self.get_field_names_in_column_description()
        if field2get:
            return {x: getattr(val, y) for x, y in field2get}
        else:
            return val.to_dict()

    def dictfirst(self):
        val = self.first()
        field2get = self.get_field_names_in_column_description()
        if field2get:
            return {x: getattr(val, y) for x, y in field2get}
        else:
            return val.to_dict()

    def dictall(self):
        vals = self.all()
        if not vals:
            return []  # pragma: no cover

        field2get = self.get_field_names_in_column_description()
        if field2get:
            return [{x: getattr(y, z) for x, z in field2get} for y in vals]
        else:
            return vals.to_dict()

    def get(self, primary_keys=None, **kwargs):
        """Return instance of the Model

        ::
            instance = Model.query().get(the primary key value)

        or

        ::
            instance Model.query().get(pk1 name=pk1 value, ...)
        """

        if primary_keys is None:
            primary_keys = kwargs

        if isinstance(primary_keys, dict):
            Model = self.anyblok.get(self.Model)
            primary_keys = {
                (anyblok_column_prefix + k
                 if k in Model.hybrid_property_columns else k): v
                for k, v in primary_keys.items()
            }

        return super(Query, self).get(primary_keys)

    def update(self, *args, **kwargs):  # pragma: no cover
        """Overwrite Query.update of sqlalchemy to depreciate this it"""
        warnings.warn(
            "This method is deprecated and will be removed in the next version"
            "of AnyBlok, you should use update_sql_statement classmethod",
            DeprecationWarning, stacklevel=2)

        return super(Query, self).update(*args, **kwargs)

    def delete(self, *args, **kwargs):  # pragma: no cover
        """Overwrite Query.delete of sqlalchemy to depreciate this it"""
        warnings.warn(
            "This method is deprecated and will be removed in the next version"
            "of AnyBlok, you should use delete_sql_statement classmethod",
            DeprecationWarning, stacklevel=2)

        return super(Query, self).delete(*args, **kwargs)
