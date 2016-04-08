# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from random import random
from anyblok.tests.testcase import DBTestCase
from anyblok.declarations import Declarations, cache, classmethod_cache
from anyblok.bloks.anyblok_core.exceptions import CacheException
from anyblok.column import Integer
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


class TestCache(DBTestCase):

    def add_model_with_method_cached(self):

        @register(Model)
        class Test:

            x = 0

            @cache()
            def method_cached(self):
                self.x += 1
                return self.x

    def test_cache_invalidation(self):
        registry = self.init_registry(self.add_model_with_method_cached)
        Cache = registry.System.Cache
        nb_invalidation = Cache.query().count()
        Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(Cache.query().count(), nb_invalidation + 1)

    def test_invalid_cache_invalidation(self):
        registry = self.init_registry(self.add_model_with_method_cached)
        Cache = registry.System.Cache
        with self.assertRaises(CacheException):
            Cache.invalidate('Model.Test2', 'method_cached')

    def test_detect_cache_invalidation(self):
        registry = self.init_registry(self.add_model_with_method_cached)
        Cache = registry.System.Cache
        self.assertEqual(Cache.detect_invalidation(), False)
        Cache.insert(registry_name="Model.Test", method="method_cached")
        self.assertEqual(Cache.detect_invalidation(), True)

    def test_get_invalidation(self):
        registry = self.init_registry(self.add_model_with_method_cached)
        Cache = registry.System.Cache
        Cache.insert(registry_name="Model.Test", method="method_cached")
        caches = Cache.get_invalidation()
        self.assertEqual(len(caches), 1)
        cache = caches[0]
        self.assertEqual(cache.indentify, ('Model.Test', 'method_cached'))


class TestSimpleCache(DBTestCase):

    def check_method_cached(self, Model, registry_name, value=1):
        m = Model()
        self.assertEqual(m.method_cached(), value)
        self.assertEqual(m.method_cached(), value)
        Model.registry.System.Cache.invalidate(registry_name, 'method_cached')
        self.assertEqual(m.method_cached(), 2 * value)

    def check_method_cached_invalidate_all(self, Model, value=1):
        m = Model()
        self.assertEqual(m.method_cached(), value)
        self.assertEqual(m.method_cached(), value)
        Model.registry.System.Cache.invalidate_all()
        self.assertEqual(m.method_cached(), 2 * value)

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
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 12)

    def test_model_mixin_core_only_core(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withcore=True)
        m = registry.Test()
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 11)
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 17)

    def test_model_mixin_core_only_mixin(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmixin=True)
        m = registry.Test()
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 9)
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 15)

    def test_model_mixin_core_only_model(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmodel=True)
        m = registry.Test()
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 6)
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 12)

    def test_model_mixin_core_only_core_and_mixin(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmixin=True, withcore=True)
        m = registry.Test()
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 9)
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 15)

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
        self.assertEqual(t.method_cached(), 4)
        self.assertEqual(t2.method_cached(), 4)
        self.assertEqual(t.method_cached(), 7)
        self.assertEqual(t2.method_cached(), 7)
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(t.method_cached(), 11)
        self.assertEqual(t2.method_cached(), 10)


class TestClassMethodCache(DBTestCase):

    def check_method_cached(self, Model, registry_name):
        m = Model
        value = m.method_cached()
        self.assertEqual(m.method_cached(), value)
        self.assertEqual(m.method_cached(), value)
        Model.registry.System.Cache.invalidate(registry_name, 'method_cached')
        self.assertNotEqual(m.method_cached(), value)

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
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 12)

    def test_model_mixin_core_only_core(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withcore=True)
        m = registry.Test
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 11)
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 17)

    def test_model_mixin_core_only_mixin(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmixin=True)
        m = registry.Test
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 9)
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 15)

    def test_model_mixin_core_only_model(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmodel=True)
        m = registry.Test
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 6)
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 12)

    def test_model_mixin_core_only_core_and_mixin(self):
        registry = self.init_registry(
            self.add_model_with_method_cached_with_mixin_and_or_core,
            withmixin=True, withcore=True)
        m = registry.Test
        self.assertEqual(m.method_cached(), 6)
        self.assertEqual(m.method_cached(), 9)
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 15)

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
        self.assertEqual(registry.Test.method_cached(), 4)
        self.assertEqual(registry.Test2.method_cached(), 4)
        self.assertEqual(registry.Test.method_cached(), 7)
        self.assertEqual(registry.Test2.method_cached(), 7)
        registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(registry.Test.method_cached(), 11)
        self.assertEqual(registry.Test2.method_cached(), 10)


class TestInheritedCache(DBTestCase):

    def check_method_cached(self, Model):
        m = Model()
        self.assertEqual(m.method_cached(), 3)
        self.assertEqual(m.method_cached(), 5)
        Model.registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 8)

    def check_inherited_method_cached(self, Model):
        m = Model()
        self.assertEqual(m.method_cached(), 3)
        self.assertEqual(m.method_cached(), 3)
        Model.registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(m.method_cached(), 6)

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


class TestInheritedClassMethodCache(DBTestCase):

    def check_method_cached(self, Model):
        self.assertEqual(Model.method_cached(), 3)
        self.assertEqual(Model.method_cached(), 5)
        Model.registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(Model.method_cached(), 8)

    def check_inherited_method_cached(self, Model):
        self.assertEqual(Model.method_cached(), 3)
        self.assertEqual(Model.method_cached(), 3)
        Model.registry.System.Cache.invalidate('Model.Test', 'method_cached')
        self.assertEqual(Model.method_cached(), 6)

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


class TestComparatorInterModel(DBTestCase):

    def check_comparator(self, registry):
        Test = registry.Test
        Test2 = registry.Test2
        self.assertEqual(Test.method_cached(), Test.method_cached())
        self.assertEqual(Test2.method_cached(), Test2.method_cached())
        self.assertNotEqual(Test.method_cached(), Test2.method_cached())

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


class TestSQLModelCache(DBTestCase):

    def add_in_registry(self):

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

    def test_query_and_classmethod_cached(self):
        registry = self.init_registry(self.add_in_registry)
        registry.Test.insert()
        registry.Test.insert()
        self.assertEqual(registry.Test.count(), 2)
        registry.Test.insert()
        self.assertEqual(registry.Test.count(), 2)
        Cache = registry.System.Cache
        Cache.invalidate('Model.Test', 'count')
        self.assertEqual(registry.Test.count(), 3)

    def test_query_and_method_cached(self):
        registry = self.init_registry(self.add_in_registry)
        t = registry.Test.insert(id2=1)
        self.assertEqual(t.get_id2(), 1)
        t.id2 = 2
        self.assertEqual(t.get_id2(), 1)
        Cache = registry.System.Cache
        Cache.invalidate('Model.Test', 'get_id2')
        self.assertEqual(t.get_id2(), 2)
