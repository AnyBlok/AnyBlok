# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import sys
from functools import lru_cache
from sqlalchemy.schema import ForeignKeyConstraint


"""Define the prefixe for the mapper attribute for the column"""
anyblok_column_prefix = '__anyblok_field_'


def all_column_name(constraint, table):
    """Define the convention for merge the column"""
    if isinstance(constraint, ForeignKeyConstraint):
        return '_'.join(constraint.column_keys)
    else:
        return '_'.join(constraint.columns.keys())


def model_name(constraint, table):
    """return a shortest table name"""
    name = table.name.split('_')
    if len(name) == 1:
        return name[0]

    return ''.join(x[0] for x in name[:-1]) + '_' + name[-1]


"""table convention for constraint"""
naming_convention = {
    "all_column_name": all_column_name,
    "model_name": model_name,
    "ix": "anyblok_ix_%(model_name)s__%(all_column_name)s",
    "uq": "anyblok_uq_%(model_name)s__%(all_column_name)s",
    "ck": "anyblok_ck_%(model_name)s__%(constraint_name)s",
    "fk": "anyblok_fk_%(model_name)s__%(all_column_name)s",
    "pk": "anyblok_pk_%(table_name)s",
}


def add_autodocs(meth, autodoc):
    if not hasattr(meth, 'autodocs'):
        meth.autodocs = []

    meth.autodocs.append(autodoc)


def function_name(function):
    if sys.version_info < (3, 3):
        return function.__name__
    else:
        return function.__qualname__


def python_version():
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
        if base in self.registry.removed:
            return None

        if namespace is None:
            namespace = self.namespace

        newbase = self.Model.transform_base(
            self.registry, namespace, base, self.transformation_properties)
        return newbase

    def append(self, base, **kwargs):
        bases = self.transform_base(base, **kwargs) or []
        for newbase in bases:
            super(TypeList, self).append(newbase)

    def extend(self, bases, **kwargs):
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
    :param registry: the current  registry
    :param namespace: the namespace of the model
    :param base: One of the base of the model
    :param properties: the properties of the model
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
