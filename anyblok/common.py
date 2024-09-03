# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2021 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import sys

from sqlalchemy import text
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.schema import ForeignKeyConstraint
from sqlalchemy.sql.naming import ConventionDict

"""Define the prefix for the mapper attribute of the column"""
anyblok_column_prefix = "ANYBLOK_FIELD_"


def all_column_name(constraint, table):
    """Define the convention to merge the column keys

    :param constraint:
    :return:
    """
    if isinstance(constraint, ForeignKeyConstraint):
        return "_".join(constraint.column_keys)
    else:
        return "_".join(constraint.columns.keys())


def model_name(constraint, table):
    """Return a shortest table name

    :param table:
    :return:
    """
    name = table.name.split("_")
    if len(name) == 1:
        return name[0]

    return "".join(x[0] for x in name[:-1]) + "_" + name[-1]


def constraint_name(constraint, table):
    """return a shortest table name"""
    conv = ConventionDict(constraint, table, naming_convention)
    try:
        return conv._key_constraint_name()
    except InvalidRequestError:  # pragma: no cover
        if constraint._pending_colargs:
            return "_".join([x.name for x in constraint._pending_colargs])

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
    if not hasattr(meth, "autodocs"):
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


class BaseModelSecondStepList(list):
    def __init__(
        self, Model, registry, namespace, transformation_properties=None
    ):
        super().__init__()
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

        self.Model.transform_base(
            self.registry, namespace, base, self.transformation_properties
        )
        return True

    def append(self, base):
        """Add base

        :param base:
        :param kwargs:
        """
        if self.transform_base(base):
            super().append(base)

    def extend(self, bases):
        """Extend bases

        :param bases:
        :param kwargs:
        """
        realbases = []
        for base in bases:
            if self.transform_base(base):
                realbases.append(base)

        super().extend(realbases)

    def insert(self, index, base, **kwargs):
        if self.transform_base(base, **kwargs):
            super().insert(index, base)


class BaseModelFirstStepList(list):
    def __init__(self, Model, registry, properties):
        super(BaseModelFirstStepList, self).__init__()
        self.Model = Model
        self.properties = properties
        self.registry = registry
        registry.call_plugins("initialize_properties", properties)

    def merge_properties(self, base):
        self.registry.call_plugins("merge_properties", self.properties, base)

    def insert(self, index, base):
        """Add base

        :param base:
        :param kwargs:
        """
        if base in self:  # Reload bloks overload bases
            return

        if isinstance(base, str):
            self.merge_properties(
                self.Model.load_namespace_first_step(self.registry, base)
            )
        else:
            self.merge_properties(base.__dict__)

        super(BaseModelFirstStepList, self).insert(index, base)


DATABASES_CACHED = {}


def sgdb_in(engine, databases):
    for database in databases:
        if database not in DATABASES_CACHED:
            DATABASES_CACHED[database] = False
            if engine.url.drivername.startswith("mysql"):
                if database == "MySQL":
                    DATABASES_CACHED["MySQL"] = True

                with engine.connect() as conn:
                    res = conn.execute(
                        text("show variables like 'version'")
                    ).fetchone()
                    if res and database in res[1]:
                        # MariaDB
                        DATABASES_CACHED[database] = True  # pragma: no cover

            if (
                engine.url.drivername.startswith("postgres")
                and database == "PostgreSQL"
            ):
                DATABASES_CACHED["PostgreSQL"] = True
            if (
                engine.url.drivername.startswith("mssql")
                and database == "MsSQL"
            ):
                DATABASES_CACHED["MsSQL"] = True  # pragma: no cover

        if DATABASES_CACHED[database]:
            return True

    return False


def return_list(entry):
    if entry is None:
        return []

    elif not isinstance(entry, (list, tuple)):
        entry = [entry]

    return entry
