# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.declarations import Declarations
from anyblok.column import String, Integer
from ..exceptions import CacheException


register = Declarations.register
System = Declarations.Model.System


@register(System)
class Cache:

    last_cache_id = None
    lrus = {}

    id = Integer(primary_key=True)
    registry_name = String(nullable=False)
    method = String(nullable=False)

    @classmethod
    def get_last_id(cls):
        """ Return the last primary key ``id`` value
        """
        res = cls.query('id').order_by(cls.id.desc()).limit(1).first()
        if res:
            return res[0]

        return 0

    @classmethod
    def initialize_model(cls):
        """ Initialize the last_cache_id known
        """
        super(Cache, cls).initialize_model()
        cls.last_cache_id = cls.get_last_id()

    @classmethod
    def invalidate_all(cls):
        res = []
        for registry_name, methods in cls.anyblok.caches.items():
            for method in methods.keys():
                res.append(dict(registry_name=registry_name, method=method))

        if res:
            cls.multi_insert(*res)

        cls.clear_invalidate_cache()

    @classmethod
    def invalidate(cls, registry_name, method):
        """ Call the invalidation for a specific method cached on a model

        :param registry_name: namespace of the model
        :param method: name of the method on the model
        :exception: CacheException
        """
        caches = cls.anyblok.caches

        def insert(registry_name=None, method=None):
            if registry_name in caches:
                if method in caches[registry_name]:
                    cls.insert(registry_name=registry_name, method=method)
                else:
                    raise CacheException(  # pragma: no cover
                        "Unknown cached method %r" % method)
            else:
                raise CacheException(
                    "Unknown cached model %r" % registry_name)

        if isinstance(registry_name, str):
            insert(registry_name=registry_name, method=method)
        elif hasattr(registry_name, '__registry_name__'):
            insert(registry_name=registry_name.__registry_name__,
                   method=method)

        cls.clear_invalidate_cache()

    @classmethod
    def detect_invalidation(cls):
        """ Return True if a new invalidation is found in the table

        :rtype: Boolean
        """
        if cls.last_cache_id is None:
            cls.last_cache_id = 0
        return cls.last_cache_id < cls.get_last_id()

    @classmethod
    def get_invalidation(cls):
        """ Return the pointer of the method to invalidate
        """
        res = []
        if cls.detect_invalidation():
            caches = cls.anyblok.caches
            for i in cls.query().filter(cls.id > cls.last_cache_id).all():
                res.extend(caches[i.registry_name][i.method])

            cls.last_cache_id = cls.get_last_id()

        return res

    @classmethod
    def clear_invalidate_cache(cls):
        """ Invalidate the cache that needs to be invalidated
        """
        for cache in cls.get_invalidation():
            cache.cache_clear()
