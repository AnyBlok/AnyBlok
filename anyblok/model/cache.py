# This file is a part of the AnyBlok project
#
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.common import apply_cache

from .plugins import ModelPluginBase


class CachePlugin(ModelPluginBase):
    def __init__(self, registry):
        if not hasattr(registry, "caches"):
            registry.caches = {}

        super(CachePlugin, self).__init__(registry)

    def insert_in_bases(
        self, new_base, namespace, properties, transformation_properties
    ):
        """Create overload to define the cache from __depends__.

        Because the cache is defined on the depend models and this namespace
        does not exist in caches dict

        :param new_base: the base to be put on front of all bases
        :param namespace: the namespace of the model
        :param properties: the properties declared in the model
        :param transformation_properties: the properties of the model
        """
        for dep in properties["__depends__"]:
            if dep in self.registry.caches:
                cache = self.registry.caches.setdefault(namespace, {})
                for method_name, methods in self.registry.caches[dep].items():
                    entry = cache.setdefault(method_name, [])
                    entry.extend(methods)

        return {}

    def transform_base_attribute(
        self,
        attr,
        method,
        namespace,
        base,
        transformation_properties,
        new_type_properties,
    ):
        """Find the sqlalchemy hybrid methods in the base to save the
        namespace and the method in the registry

        :param attr: attribute name
        :param method: method pointer of the attribute
        :param namespace: the namespace of the model
        :param base: One of the base of the model
        :param transformation_properties: the properties of the model
        :param new_type_properties: param to add in a new base if need
        """
        new_type_properties.update(
            apply_cache(
                attr,
                method,
                self.registry,
                namespace,
                base,
                transformation_properties,
            )
        )
