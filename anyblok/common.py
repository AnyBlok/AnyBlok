# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2021 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import sys
from functools import lru_cache
from sqlalchemy.schema import ForeignKeyConstraint
from sqlalchemy.sql.naming import ConventionDict
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy import text


"""Define the prefix for the mapper attribute of the column"""
anyblok_column_prefix = '__anyblok_field_'


def all_column_name(constraint, table):
    """Define the convention to merge the column keys

    :param constraint:
    :return:
    """
    if isinstance(constraint, ForeignKeyConstraint):
        return '_'.join(constraint.column_keys)
    else:
        return '_'.join(constraint.columns.keys())


def model_name(constraint, table):
    """Return a shortest table name

    :param table:
    :return:
    """
    name = table.name.split('_')
    if len(name) == 1:
        return name[0]

    return ''.join(x[0] for x in name[:-1]) + '_' + name[-1]


def constraint_name(constraint, table):
    """return a shortest table name"""
    conv = ConventionDict(constraint, table, naming_convention)
    try:
        return conv._key_constraint_name()
    except InvalidRequestError:  # pragma: no cover
        if constraint._pending_colargs:
            return '_'.join([x.name for x in constraint._pending_colargs])

        raise


"""table convention for constraint"""
naming_convention = {
    "all_column_name": all_column_name,
    "model_name": model_name,
    "constraint_name": constraint_name,
    "ix": "anyblok_ix_%(model_name)s__%(all_column_name)s",
    "uq": "anyblok_uq_%(model_name)s__%(all_column_name)s",
    "ck": "anyblok_ck_%(model_name)s__%(constraint_name)s",
    "fk": "anyblok_fk_%(model_name)s__%(all_column_name)s",
    "pk": "anyblok_pk_%(table_name)s",
}


def add_autodocs(meth, autodoc):
    """Add autodocs entries

    :param meth:
    :param autodoc:
    """
    if not hasattr(meth, 'autodocs'):
        meth.autodocs = []

    meth.autodocs.append(autodoc)


def function_name(function_):
    """Return the name of the function

    :param function_:
    :return:
    """
    return function_.__qualname__


def python_version():  # pragma: no cover
    """Return Python version tuple

    :return:
    """
    vi = sys.version_info
    return (vi.major, vi.minor)


class TypeList(list):

    def __init__(self, Model, registry, namespace,
                 transformation_properties=None):
        super(TypeList, self).__init__()
        self.Model = Model
        self.registry = registry
        self.namespace = namespace
        self.transformation_properties = transformation_properties

    def transform_base(self, base, namespace=None):
        """Detect specific declaration which must define by registry

        :param namespace: the namespace of the model
        :param base: One of the base of the model
        :rtype: new base
        """
        if base in self.registry.removed:
            return None

        if namespace is None:
            namespace = self.namespace

        newbase = self.Model.transform_base(
            self.registry, namespace, base, self.transformation_properties)
        return newbase

    def append(self, base, **kwargs):
        """Add base

        :param base:
        :param kwargs:
        """
        bases = self.transform_base(base, **kwargs) or []
        for newbase in bases:
            super(TypeList, self).append(newbase)

    def extend(self, bases, **kwargs):
        """Extend bases

        :param bases:
        :param kwargs:
        """
        newbases = []
        for base in bases:
            _bases = self.transform_base(base, **kwargs)
            if _bases:
                newbases.extend(_bases)

        if newbases:
            super(TypeList, self).extend(newbases)


def apply_cache(attr, method, registry, namespace, base, properties):
    """Find the cached methods in the base to apply the real cache decorator.

    :param attr: name of the attribute
    :param method: method pointer
    :param registry: the current registry
    :param namespace: the namespace of the model
    :rtype: new base
    """
    if hasattr(method, 'is_cache_method') and method.is_cache_method is True:
        if namespace not in registry.caches:
            registry.caches[namespace] = {attr: []}
        elif attr not in registry.caches[namespace]:
            registry.caches[namespace][attr] = []

        @lru_cache(maxsize=method.size)
        def wrapper(*args, **kwargs):
            return method(*args, **kwargs)

        wrapper.indentify = (namespace, attr)
        registry.caches[namespace][attr].append(wrapper)
        if method.is_cache_classmethod:
            return {attr: classmethod(wrapper)}
        else:
            return {attr: wrapper}

    return {}


DATABASES_CACHED = {}


def sgdb_in(engine, databases):
    for database in databases:
        if database not in DATABASES_CACHED:
            DATABASES_CACHED[database] = False
            if engine.url.drivername.startswith('mysql'):
                if database == 'MySQL':
                    DATABASES_CACHED['MySQL'] = True

                with engine.connect() as conn:
                    res = conn.execute(
                        text("show variables like 'version'")
                    ).fetchone()
                    if res and database in res[1]:
                        # MariaDB
                        DATABASES_CACHED[database] = True  # pragma: no cover

            if (
                engine.url.drivername.startswith('postgres') and
                database == 'PostgreSQL'
            ):
                DATABASES_CACHED['PostgreSQL'] = True
            if (
                engine.url.drivername.startswith('mssql') and
                database == 'MsSQL'
            ):
                DATABASES_CACHED['MsSQL'] = True

        if DATABASES_CACHED[database]:
            return True

    return False


def return_list(entry):
    if entry is None:
        return []

    elif not isinstance(entry, (list, tuple)):
        entry = [entry]

    return entry
