# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from random import random
from anyblok.declarations import Declarations, cache, classmethod_cache
from anyblok.bloks.anyblok_core.exceptions import CacheException
from anyblok.column import Integer
import pytest
from .conftest import init_registry, reset_db

register = Declarations.register
Model = Declarations.Model
Mixin = Declarations.Mixin
Core = Declarations.Core


def wrap_cache(condition):

    def wrapper(function):
        return function

    if condition:
        return cache()

    return wrapper


def wrap_cls_cache(condition):
    if condition:
        return classmethod_cache()

    return classmethod


def add_model_with_method_cached():

    @register(Model)
    class Test:

        x = 0

        @cache()
        def method_cached(self):
            self.x += 1
            return self.x


@pytest.fixture(scope="class")
def registry_method_cached(request, bloks_loaded):
    reset_db()
    registry = init_registry(add_model_with_method_cached)
    request.addfinalizer(registry.close)
    return registry


class TestCache:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_method_cached):
        transaction = registry_method_cached.begin_nested()
        request.addfinalizer(transaction.rollback)

    def test_cache_invalidation(self, registry_method_cached):
        registry = registry_method_cached
        Cache = registry.System.Cache
        nb_invalidation = Cache.query().count()
        Cache.invalidate('Model.Test', 'method_cached')
        assert Cache.query().count() == nb_invalidation + 1

    def test_invalid_cache_invalidation(self, registry_method_cached):
        registry = registry_method_cached
        Cache = registry.System.Cache
        with pytest.raises(CacheException):
            Cache.invalidate('Model.Test2', 'method_cached')

    def test_detect_cache_invalidation(self, registry_method_cached):
        registry = registry_method_cached
        Cache = registry.System.Cache
        assert not Cache.detect_invalidation()
        Cache.insert(registry_name="Model.Test", method="method_cached")
        assert Cache.detect_invalidation()

    def test_detect_cache_invalidation_first_call(self, registry_method_cached):
        registry = registry_method_cached
        Cache = registry.System.Cache
        Cache.last_cache_id = None
        assert Cache.detect_invalidation()

    def test_get_invalidation(self, registry_method_cached):
        registry = registry_method_cached
        Cache = registry.System.Cache
        # call it before to clear cache and to be predictible
        Cache.get_invalidation()
        Cache.insert(registry_name="Model.Test", method="method_cached")
        caches = Cache.get_invalidation()
        assert len(caches) == 1
        cache = caches[0]
        assert cache.indentify == ('Model.Test', 'method_cached')


class TestSimpleCache:

    @pytest.fixture(autouse=True)
    def close_registry(self, request, bloks_loaded):

        def close():
            self.registry.close()

        request.addfinalizer(close)

    def init_registry(self, *args, **kwargs):
        self.registry = init_registry(*args, **kwargs)
        return self.registry

    def check_method_cached(self, Model, registry_name, value=1):
        m = Model()
        assert m.method_cached() == value
        assert m.method_cached() == value
        Model.anyblok.System.Cache.invalidate(registry_name, 'method_cached')
        assert m.method_cached() == 2 * value

    def check_method_cached_invalidate_all(self, Model, value=1):
        m = Model()
        assert m.method_cached() == value
        assert m.method_cached() == value
        Model.anyblok.System.Cache.invalidate_all()
        assert m.method_cached() == 2 * value

    def add_model_with_method_cached(self):

        @register(Model)
        class Test:

            x = 0

            @cache()
            def method_cached(self):
                self.x += 1
                return self.x

    def add_model_with_method_cached_by_core(self):

        @register(Core)
        class Base:

            x = 0

            @cache()
            def method_cached(self):
                self.x += 1
                return self.x

        @register(Model)
        class Test:
            pass

    def add_model_with_method_cached_by_mixin(self):

        @register(Mixin)
        class MTest:

            x = 0

            @cache()
            def method_cached(self):
                self.x += 1
                return self.x

        @register(Model)
        class Test(Mixin.MTest):
            pass

    def add_model_with_method_cached_by_mixin_chain(self):

        @register(Mixin)
        class MTest:

            x = 0

            @cache()
            def method_cached(self):
                self.x += 1
                return self.x

        @register(Mixin)
        class MTest2(Mixin.MTest):
            pass

        @register(Model)
        class Test(Mixin.MTest2):
            pass

    def add_model_with_method_cached_with_mixin_and_or_core(self,
                                                            withmodel=False,
                                                            withmixin=False,
                                                            withcore=False):

        @register(Core)
        class Base:

            x = 0

            @wrap_cache(withcore)
            def method_cached(self):
                self.x += 1
                return self.x

        @register(Mixin)
        class MTest:

            y = 0

            @wrap_cache(withmixin)
            def method_cached(self):
                self.y += 2
                return self.y + super(MTest, self).method_cached()

        @register(Model)
        class Test(Mixin.MTest):

            z = 0

            @wrap_cache(withmodel)
            def method_cached(self):
                self.z += 3
                return self.z + super(Test, self).method_cached()

    def test_model(self):
        registry = self.init_registry(self.add_model_with_method_cached)
        self.check_method_cached(registry.Test, 'Model.Test')

    def test_model2(self):
        registry = self.init_registry(self.add_model_with_method_cached)
        from anyblok import Declarations
        self.check_method_cached(registry.Test, Declarations.Model.Test)

    def test_core(self):
        registry = self.init_registry(self.add_model_with_method_cached_by_core)
        self.check_method_cached(registry.Test, 'Model.Test')

    def test_core2(self):
        registry = self.init_registry(self.add_model_with_method_cached_by_core)
        from anyblok import Declarations
        self.check_method_cached(registry.Test, Declarations.Model.Test)

    def test_mixin(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_mixin)
        self.check_method_cached(registry.Test, 'Model.Test')

    def test_mixin2(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_mixin)
        from anyblok import Declarations
        self.check_method_cached(registry.Test, Declarations.Model.Test)

    def test_mixin_chain(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_mixin_chain)
        self.check_method_cached(registry.Test, 'Model.Test')

    def test_mixin_chain2(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_mixin_chain)
        from anyblok import Declarations
        self.check_method_cached(registry.Test, Declarations.Model.Test)

    def test_model_mixin_core_not_cache(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core)
        m = registry.Test()
        assert m.method_cached() == 6
        assert m.method_cached() == 12

    def test_model_mixin_core_only_core(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withcore=True)
        m = registry.Test()
        assert m.method_cached() == 6
        assert m.method_cached() == 11
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        assert m.method_cached() == 17

    def test_model_mixin_core_only_mixin(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmixin=True)
        m = registry.Test()
        assert m.method_cached() == 6
        assert m.method_cached() == 9
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        assert m.method_cached() == 15

    def test_model_mixin_core_only_model(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmodel=True)
        m = registry.Test()
        assert m.method_cached() == 6
        assert m.method_cached() == 6
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        assert m.method_cached() == 12

    def test_model_mixin_core_only_core_and_mixin(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmixin=True, withcore=True)
        m = registry.Test()
        assert m.method_cached() == 6
        assert m.method_cached() == 9
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        assert m.method_cached() == 15

    def test_invalidate_all_check_model(self):
        registry = self.init_registry(self.add_model_with_method_cached)
        self.check_method_cached_invalidate_all(registry.Test)

    def test_invalidate_all_check_core(self):
        registry = self.init_registry(self.add_model_with_method_cached_by_core)
        self.check_method_cached_invalidate_all(registry.Test)

    def test_invalidate_all_check_mixin(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_mixin)
        self.check_method_cached_invalidate_all(registry.Test)

    def add_model_with_method_core_cached_with_two_model(self):

        @register(Core)
        class Base:

            def __init__(self):
                super(Base, self).__init__()
                self.x = 0
                self.z = 0

            @cache()
            def method_cached(self):
                self.x += 1
                return self.x

        @register(Model)
        class Test:

            def method_cached(self):
                self.z += 3
                return self.z + super(Test, self).method_cached()

        @register(Model)
        class Test2:

            def method_cached(self):
                self.z += 3
                return self.z + super(Test2, self).method_cached()

    def test_2_model_with_core_catched(self):
        registry = self.init_registry(
            self.add_model_with_method_core_cached_with_two_model)
        t = registry.Test()
        t2 = registry.Test2()
        assert t.method_cached() == 4
        assert t2.method_cached() == 4
        assert t.method_cached() == 7
        assert t2.method_cached() == 7
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        assert t.method_cached() == 11
        assert t2.method_cached() == 10


class TestClassMethodCache:

    @pytest.fixture(autouse=True)
    def close_registry(self, request, bloks_loaded):

        def close():
            self.registry.close()

        request.addfinalizer(close)

    def init_registry(self, *args, **kwargs):
        self.registry = init_registry(*args, **kwargs)
        return self.registry

    def check_method_cached(self, Model, registry_name):
        m = Model
        value = m.method_cached()
        assert m.method_cached() == value
        assert m.method_cached() == value
        Model.anyblok.System.Cache.invalidate(registry_name, 'method_cached')
        assert m.method_cached() != value

    def add_model_with_method_cached(self):

        @register(Model)
        class Test:

            x = 0

            @classmethod_cache()
            def method_cached(cls):
                cls.x += 1
                return cls.x

    def add_model_with_method_cached_by_core(self):

        @register(Core)
        class Base:

            x = 0

            @classmethod_cache()
            def method_cached(cls):
                cls.x += 1
                return cls.x

        @register(Model)
        class Test:
            pass

    def add_model_with_method_cached_by_mixin(self):

        @register(Mixin)
        class MTest:

            x = 0

            @classmethod_cache()
            def method_cached(cls):
                cls.x += 1
                return cls.x

        @register(Model)
        class Test(Mixin.MTest):
            pass

    def add_model_with_method_cached_by_mixin_chain(self):

        @register(Mixin)
        class MTest:

            x = 0

            @classmethod_cache()
            def method_cached(cls):
                cls.x += 1
                return cls.x

        @register(Mixin)
        class MTest2(Mixin.MTest):
            pass

        @register(Model)
        class Test(Mixin.MTest2):
            pass

    def add_model_with_method_cached_with_mixin_and_or_core(self,
                                                            withmodel=False,
                                                            withmixin=False,
                                                            withcore=False):

        @register(Core)
        class Base:

            x = 0

            @wrap_cls_cache(withcore)
            def method_cached(cls):
                cls.x += 1
                return cls.x

        @register(Mixin)
        class MTest:

            y = 0

            @wrap_cls_cache(withmixin)
            def method_cached(cls):
                cls.y += 2
                return cls.y + super(MTest, cls).method_cached()

        @register(Model)
        class Test(Mixin.MTest):

            z = 0

            @wrap_cls_cache(withmodel)
            def method_cached(cls):
                cls.z += 3
                return cls.z + super(Test, cls).method_cached()

    def test_model(self):
        registry = self.init_registry(self.add_model_with_method_cached)
        self.check_method_cached(registry.Test, 'Model.Test')

    def test_model2(self):
        registry = self.init_registry(self.add_model_with_method_cached)
        from anyblok import Declarations
        self.check_method_cached(registry.Test, Declarations.Model.Test)

    def test_core(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_core)
        self.check_method_cached(registry.Test, 'Model.Test')

    def test_core2(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_core)
        from anyblok import Declarations
        self.check_method_cached(registry.Test, Declarations.Model.Test)

    def test_mixin(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_mixin)
        self.check_method_cached(registry.Test, 'Model.Test')

    def test_mixin2(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_mixin)
        from anyblok import Declarations
        self.check_method_cached(registry.Test, Declarations.Model.Test)

    def test_mixin_chain(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_mixin_chain)
        self.check_method_cached(registry.Test, 'Model.Test')

    def test_mixin_chain2(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_mixin_chain)
        from anyblok import Declarations
        self.check_method_cached(registry.Test, Declarations.Model.Test)

    def test_model_mixin_core_not_cache(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core)
        m = registry.Test
        assert m.method_cached() == 6
        assert m.method_cached() == 12

    def test_model_mixin_core_only_core(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withcore=True)
        m = registry.Test
        assert m.method_cached() == 6
        assert m.method_cached() == 11
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        assert m.method_cached() == 17

    def test_model_mixin_core_only_mixin(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmixin=True)
        m = registry.Test
        assert m.method_cached() == 6
        assert m.method_cached() == 9
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        assert m.method_cached() == 15

    def test_model_mixin_core_only_model(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmodel=True)
        m = registry.Test
        assert m.method_cached() == 6
        assert m.method_cached() == 6
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        assert m.method_cached() == 12

    def test_model_mixin_core_only_core_and_mixin(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmixin=True, withcore=True)
        m = registry.Test
        assert m.method_cached() == 6
        assert m.method_cached() == 9
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        assert m.method_cached() == 15

    def add_model_with_method_core_cached_with_two_model(self):

        @register(Core)
        class Base:

            x = 0

            @classmethod_cache()
            def method_cached(cls):
                cls.x += 1
                return cls.x

        @register(Model)
        class Test:

            z = 0

            @classmethod
            def method_cached(cls):
                cls.z += 3
                return cls.z + super(Test, cls).method_cached()

        @register(Model)
        class Test2:

            z = 0

            @classmethod
            def method_cached(cls):
                cls.z += 3
                return cls.z + super(Test2, cls).method_cached()

    def test_2_model_with_core_catched(self):
        registry = self.init_registry(
            self.add_model_with_method_core_cached_with_two_model)
        assert registry.Test.method_cached() == 4
        assert registry.Test2.method_cached() == 4
        assert registry.Test.method_cached() == 7
        assert registry.Test2.method_cached() == 7
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        assert registry.Test.method_cached() == 11
        assert registry.Test2.method_cached() == 10


class TestInheritedCache:

    @pytest.fixture(autouse=True)
    def close_registry(self, request, bloks_loaded):

        def close():
            self.registry.close()

        request.addfinalizer(close)

    def init_registry(self, *args, **kwargs):
        self.registry = init_registry(*args, **kwargs)
        return self.registry

    def check_method_cached(self, Model):
        m = Model()
        assert m.method_cached() == 3
        assert m.method_cached() == 5
        Model.anyblok.System.Cache.invalidate('Model.Test', 'method_cached')
        assert m.method_cached() == 8

    def check_inherited_method_cached(self, Model):
        m = Model()
        assert m.method_cached() == 3
        assert m.method_cached() == 3
        Model.anyblok.System.Cache.invalidate('Model.Test', 'method_cached')
        assert m.method_cached() == 6

    def add_model_with_method_cached(self, inheritcache=False):

        @register(Model)
        class Test:

            x = 0

            @cache()
            def method_cached(self):
                self.x += 1
                return self.x

        @register(Model)  # noqa
        class Test:

            y = 0

            if inheritcache:
                @cache()
                def method_cached(self):
                    self.y += 2
                    return self.y + super(Test, self).method_cached()
            else:
                def method_cached(self):
                    self.y += 2
                    return self.y + super(Test, self).method_cached()

    def add_model_with_method_cached_by_core(self, inheritcache=False):

        @register(Core)
        class Base:

            x = 0

            @cache()
            def method_cached(self):
                self.x += 1
                return self.x

        @register(Core)  # noqa
        class Base:

            y = 0

            if inheritcache:
                @cache()
                def method_cached(self):
                    self.y += 2
                    return self.y + super(Base, self).method_cached()
            else:
                def method_cached(self):
                    self.y += 2
                    return self.y + super(Base, self).method_cached()

        @register(Model)
        class Test:
            pass

    def add_model_with_method_cached_by_mixin(self, inheritcache=False):

        @register(Mixin)
        class MTest:

            x = 0

            @cache()
            def method_cached(self):
                self.x += 1
                return self.x

        @register(Mixin)  # noqa
        class MTest:

            y = 0

            if inheritcache:
                @cache()
                def method_cached(self):
                    self.y += 2
                    return self.y + super(MTest, self).method_cached()
            else:
                def method_cached(self):
                    self.y += 2
                    return self.y + super(MTest, self).method_cached()

        @register(Model)
        class Test(Mixin.MTest):
            pass

    def test_model(self):
        registry = self.init_registry(self.add_model_with_method_cached)
        self.check_method_cached(registry.Test)

    def test_model2(self):
        registry = self.init_registry(self.add_model_with_method_cached,
                                      inheritcache=True)
        self.check_inherited_method_cached(registry.Test)

    def test_core(self):
        registry = self.init_registry(self.add_model_with_method_cached_by_core)
        self.check_method_cached(registry.Test)

    def test_core2(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_core, inheritcache=True)
        self.check_inherited_method_cached(registry.Test)

    def test_mixin(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_mixin)
        self.check_method_cached(registry.Test)

    def test_mixin2(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_mixin, inheritcache=True)
        self.check_inherited_method_cached(registry.Test)


class TestInheritedClassMethodCache:

    @pytest.fixture(autouse=True)
    def close_registry(self, request, bloks_loaded):

        def close():
            self.registry.close()

        request.addfinalizer(close)

    def init_registry(self, *args, **kwargs):
        self.registry = init_registry(*args, **kwargs)
        return self.registry

    def check_method_cached(self, Model):
        assert Model.method_cached() == 3
        assert Model.method_cached() == 5
        Model.anyblok.System.Cache.invalidate('Model.Test', 'method_cached')
        assert Model.method_cached() == 8

    def check_inherited_method_cached(self, Model):
        assert Model.method_cached() == 3
        assert Model.method_cached() == 3
        Model.anyblok.System.Cache.invalidate('Model.Test', 'method_cached')
        assert Model.method_cached() == 6

    def add_model_with_method_cached(self, inheritcache=False):

        @register(Model)
        class Test:

            x = 0

            @classmethod_cache()
            def method_cached(cls):
                cls.x += 1
                return cls.x

        @register(Model)  # noqa
        class Test:

            y = 0

            if inheritcache:
                @classmethod_cache()
                def method_cached(cls):
                    cls.y += 2
                    return cls.y + super(Test, cls).method_cached()
            else:
                @classmethod
                def method_cached(cls):
                    cls.y += 2
                    return cls.y + super(Test, cls).method_cached()

    def add_model_with_method_cached_by_core(self, inheritcache=False):

        @register(Core)
        class Base:

            x = 0

            @classmethod_cache()
            def method_cached(cls):
                cls.x += 1
                return cls.x

        @register(Core)  # noqa
        class Base:

            y = 0

            if inheritcache:
                @classmethod_cache()
                def method_cached(cls):
                    cls.y += 2
                    return cls.y + super(Base, cls).method_cached()
            else:
                @classmethod
                def method_cached(cls):
                    cls.y += 2
                    return cls.y + super(Base, cls).method_cached()

        @register(Model)
        class Test:
            pass

    def add_model_with_method_cached_by_mixin(self, inheritcache=False):

        @register(Mixin)
        class MTest:

            x = 0

            @classmethod_cache()
            def method_cached(cls):
                cls.x += 1
                return cls.x

        @register(Mixin)  # noqa
        class MTest:

            y = 0

            if inheritcache:
                @classmethod_cache()
                def method_cached(cls):
                    cls.y += 2
                    return cls.y + super(MTest, cls).method_cached()
            else:
                @classmethod
                def method_cached(cls):
                    cls.y += 2
                    return cls.y + super(MTest, cls).method_cached()

        @register(Model)
        class Test(Mixin.MTest):
            pass

    def test_model(self):
        registry = self.init_registry(self.add_model_with_method_cached)
        self.check_method_cached(registry.Test)

    def test_model2(self):
        registry = self.init_registry(self.add_model_with_method_cached,
                                      inheritcache=True)
        self.check_inherited_method_cached(registry.Test)

    def test_core(self):
        registry = self.init_registry(self.add_model_with_method_cached_by_core)
        self.check_method_cached(registry.Test)

    def test_core2(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_core, inheritcache=True)
        self.check_inherited_method_cached(registry.Test)

    def test_mixin(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_mixin)
        self.check_method_cached(registry.Test)

    def test_mixin2(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_by_mixin, inheritcache=True)
        self.check_inherited_method_cached(registry.Test)


class TestComparatorInterModel:

    @pytest.fixture(autouse=True)
    def close_registry(self, request, bloks_loaded):

        def close():
            self.registry.close()

        request.addfinalizer(close)

    def init_registry(self, *args, **kwargs):
        self.registry = init_registry(*args, **kwargs)
        return self.registry

    def check_comparator(self, registry):
        Test = registry.Test
        Test2 = registry.Test2
        assert Test.method_cached() == Test.method_cached()
        assert Test2.method_cached() == Test2.method_cached()
        assert Test.method_cached() != Test2.method_cached()

    def test_model(self):

        def add_in_registry():

            @register(Model)
            class Test:

                @classmethod_cache()
                def method_cached(cls):
                    return random()

            @register(Model)
            class Test2:

                @classmethod_cache()
                def method_cached(cls):
                    return random()

        registry = self.init_registry(add_in_registry)
        self.check_comparator(registry)

    def test_mixin(self):

        def add_in_registry():

            @register(Mixin)
            class MTest:

                @classmethod_cache()
                def method_cached(cls):
                    return random()

            @register(Model)
            class Test(Mixin.MTest):
                pass

            @register(Model)
            class Test2(Mixin.MTest):

                pass

        registry = self.init_registry(add_in_registry)
        self.check_comparator(registry)

    def test_core(self):

        def add_in_registry():

            @register(Core)
            class Base:

                @classmethod_cache()
                def method_cached(cls):
                    return random()

            @register(Model)
            class Test:
                pass

            @register(Model)
            class Test2:

                pass

        registry = self.init_registry(add_in_registry)
        self.check_comparator(registry)


def add_sql_model_cache():

    @register(Model)
    class Test:

        id = Integer(primary_key=True)
        id2 = Integer()

        @cache()
        def get_id2(self):
            return self.id2

        @classmethod_cache()
        def count(cls):
            return cls.query().count()


@pytest.fixture(scope="class")
def registry_sql_model_cached(request, bloks_loaded):
    registry = init_registry(add_sql_model_cache)
    request.addfinalizer(registry.close)
    return registry


class TestSQLModelCache:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_sql_model_cached):
        transaction = registry_sql_model_cached.begin_nested()
        request.addfinalizer(transaction.rollback)

    def test_query_and_classmethod_cached(self, registry_sql_model_cached):
        registry = registry_sql_model_cached
        registry.Test.insert()
        registry.Test.insert()
        assert registry.Test.count() == 2
        registry.Test.insert()
        assert registry.Test.count() == 2
        Cache = registry.System.Cache
        Cache.invalidate('Model.Test', 'count')
        assert registry.Test.count() == 3

    def test_query_and_method_cached(self, registry_sql_model_cached):
        registry = registry_sql_model_cached
        t = registry.Test.insert(id2=1)
        assert t.get_id2() == 1
        t.id2 = 2
        assert t.get_id2() == 1
        Cache = registry.System.Cache
        Cache.invalidate('Model.Test', 'get_id2')
        assert t.get_id2() == 2
