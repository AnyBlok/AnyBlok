# This file is a part of the AnyBlok project
#
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from functools import lru_cache

from .plugins import ModelPluginBase


class CachePlugin(ModelPluginBase):
    def __init__(self, registry):
        if not hasattr(registry, "caches"):
            registry.caches = {}

        super(CachePlugin, self).__init__(registry)

    def initialisation_tranformation_properties(
        self, properties, transformation_properties
    ):
        if "caches" not in transformation_properties:
            transformation_properties.update({"caches": {}})

    def transform_base(self, namespace, base, transformation_properties):
        if hasattr(base, "__declared_caches__"):
            transformation_properties["caches"].update(base.__declared_caches__)

    def before_model_construction(
        self, namespace, first_step, properties, transformation_properties
    ):
        for name, cache in transformation_properties["caches"].items():
            properties[name] = self.add_cache_method(namespace, name, cache)

    def add_cache_method(self, namespace, name, cache):
        cache_ = self.registry.caches.setdefault(namespace, {})
        entry = cache_.setdefault(name, [])

        @lru_cache(maxsize=cache.size)
        def __func__(cls_or_self, *a, **kw):
            Model = self.registry.get(namespace)
            return getattr(super(Model, cls_or_self), name)(*a, **kw)

        entry.append(__func__)

        if cache.is_clasmethod:
            return classmethod(__func__)

        return __func__
