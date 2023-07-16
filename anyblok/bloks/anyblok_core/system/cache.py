# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy import func

from anyblok.column import Integer, ModelSelection, String
from anyblok.declarations import Declarations

from ..exceptions import CacheException

register = Declarations.register
System = Declarations.Model.System


@register(System)
class Cache:
    last_cache_id = None

    id = Integer(primary_key=True)
    registry_name = ModelSelection(nullable=False)
    method = String(nullable=False)

    @classmethod
    def get_last_id(cls):
        """Return the last primary key ``id`` value"""
        res = cls.query("id").order_by(cls.id.desc()).limit(1).first()
        if res:
            return res[0]

        return 0  # pragma: no cover

    @classmethod
    def initialize_model(cls):
        """Initialize the last_cache_id known"""
        super(Cache, cls).initialize_model()
        cls.last_cache_id = cls.get_last_id()

    @classmethod
    def invalidate_all(cls):
        res = []
        for registry_name, methods in cls.anyblok.caches.items():
            for method, caches in methods.items():
                res.append(dict(registry_name=registry_name, method=method))
                for cache in caches:
                    cache.cache_clear()

        if res:
            instances = cls.multi_insert(*res)
            cls.last_cache_id = max(i.id for i in instances)

    @classmethod
    def invalidate(cls, registry_name, method):
        """Call the invalidation for a specific method cached on a model

        :param registry_name: namespace of the model
        :param method: name of the method on the model
        :exception: CacheException
        """
        caches = cls.anyblok.caches

        if hasattr(registry_name, "__registry_name__"):
            registry_name = registry_name.__registry_name__

        if registry_name in caches:
            if method in caches[registry_name]:
                cls.last_cache_id = cls.insert(
                    registry_name=registry_name, method=method
                ).id
                for cache in caches[registry_name][method]:
                    cache.cache_clear()
            else:
                raise CacheException(  # pragma: no cover
                    "Unknown cached method %r" % method
                )
        else:
            raise CacheException("Unknown cached model %r" % registry_name)

    @classmethod
    def get_invalidation(cls):
        """Return the pointer of the method to invalidate"""
        res = []
        query = cls.select_sql_statement(
            func.max(cls.id).label("id"),
            cls.registry_name,
            cls.method,
        )
        query = query.group_by(cls.registry_name, cls.method)
        query = query.where(cls.id > cls.last_cache_id)
        query_res = cls.execute_sql_statement(query)
        caches = cls.anyblok.caches
        for id_, registry_name, method in query_res:
            res.extend(caches[registry_name][method])
            cls.last_cache_id = max(cls.last_cache_id, id_)

        return res

    @classmethod
    def clear_invalidate_cache(cls):
        """Invalidate the cache that needs to be invalidated"""
        for cache in cls.get_invalidation():
            cache.cache_clear()
