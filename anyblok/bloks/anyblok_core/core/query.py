# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2021 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from logging import getLogger

from sqlalchemy import func, select
from sqlalchemy.orm.exc import NoResultFound

from anyblok import Declarations
from anyblok.common import anyblok_column_prefix

logger = getLogger(__name__)


@Declarations.register(Declarations.Core)
class Query:
    """Overload the SqlAlchemy Query"""

    def __init__(self, Model, *elements, sql_statement=None):
        self.Model = Model
        self.elements = elements
        self.sql_statement = sql_statement
        if sql_statement is None:
            self.sql_statement = Model.select_sql_statement(*elements)

    def __getattr__(self, key, default=None):
        sqla_function = getattr(self.sql_statement, key)

        def wrapper(*args, **kwargs):
            statement = sqla_function(*args, **kwargs)
            return self.anyblok.Query(
                self.Model, *self.elements, sql_statement=statement
            )

        return wrapper

    def __iter__(self):
        for res in self._execute():
            yield res

    def __str__(self):
        return str(self.sql_statement)

    def __repr__(self):
        return str(self.sql_statement)

    def _execute(self):
        res = self.Model.execute(self.sql_statement)
        if self.elements:
            return res

        return res.scalars()

    @property
    def column_descriptions(self):
        return self.sql_statement.column_descriptions

    def count(self):
        stmt = select(func.count())
        stmt = stmt.select_from(self.sql_statement.subquery())
        return self.Model.execute(stmt).scalars().first()

    def delete(self, *args, **kwargs):
        raise NotImplementedError(  # pragma: no cover
            "You have to use Model.delete_sql_statement()"
        )

    def update(self, *args, **kwargs):
        raise NotImplementedError(  # pragma: no cover
            "You have to use Model.update_sql_statement()"
        )

    def first(self):
        try:
            return self._execute().first()
        except NoResultFound as exc:  # pragma: no cover
            logger.debug(
                "On Model %r: exc %s: query %s",
                self.Model.__registry_name__,
                str(exc),
                str(self),
            )
            raise exc.__class__(
                "On Model %r: %s" % (self.Model.__registry_name__, str(exc))
            )

    def one(self):
        """Overwrite sqlalchemy one() method to improve exception message

        Add model name to query exception message
        """
        try:
            return self._execute().one()
        except NoResultFound as exc:
            logger.debug(
                "On Model %r: exc %s: query %s",
                self.Model.__registry_name__,
                str(exc),
                str(self),
            )
            raise exc.__class__(  # pragma: no cover
                "On Model %r: %s" % (self.Model.__registry_name__, str(exc))
            )

    def one_or_none(self):
        return self._execute().one_or_none()

    def all(self):
        """Return an instrumented list of the result of the query"""
        res = self._execute().all()
        return self.anyblok.InstrumentedList(res)

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
        return self.anyblok.wrap_query_permission(self, principals, permission)

    def get_field_names_in_column_description(self):
        field2get = [
            x["name"]
            for x in self.column_descriptions
            if not hasattr(x["type"], "__table__")
        ]
        field2get = [
            (
                x[len(anyblok_column_prefix) :]
                if x.startswith(anyblok_column_prefix)
                else x,
                x,
            )
            for x in field2get
        ]
        return field2get

    def dictone(self):
        try:
            val = self.one()
        except NoResultFound as exc:
            msg = str(exc).replace("one()", "dictone()")
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
            primary_keys = {
                (
                    anyblok_column_prefix + k
                    if k in self.Model.hybrid_property_columns
                    else k
                ): v
                for k, v in primary_keys.items()
            }

        return self.anyblok.session.get(self.Model, primary_keys)

    def subquery(self, *args, **kwargs):
        return self.sql_statement.subquery(*args, **kwargs)
