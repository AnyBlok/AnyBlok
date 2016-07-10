# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase, DBTestCase
from anyblok.registry import RegistryManager
from anyblok.config import Configuration
from anyblok.blok import BlokManager, Blok
from anyblok.column import Integer
from threading import Thread


class Test:
    pass


class TestTest:
    pass


class TestTestTest:
    pass


class TestRegistry(DBTestCase):

    def tearDown(self):
        super(TestRegistry, self).tearDown()
        for cls in (Test, TestTest):
            if hasattr(cls, 'Test'):
                delattr(cls, 'Test')

    def test_get_model(self):
        registry = self.init_registry(None)
        System = registry.get('Model.System')
        self.assertEqual(registry.System, System)

    def test_get_the_same_registry(self):
        registry = self.init_registry(None)
        registry2 = self.getRegistry()
        self.assertEqual(registry, registry2)

    def test_reload(self):
        registry = self.init_registry(None)
        bloks_before_reload = registry.System.Blok.query('name').filter(
            registry.System.Blok.state == 'installed').all()
        registry.reload()
        bloks_after_reload = registry.System.Blok.query('name').filter(
            registry.System.Blok.state == 'installed').all()
        self.assertEqual(bloks_before_reload, bloks_after_reload)

    def test_get_bloks_to_load(self):
        registry = self.init_registry(None)
        bloks = registry.get_bloks_to_load()
        self.assertIn('anyblok-core', bloks)

    def test_load_entry(self):
        registry = self.init_registry(None)
        registry.loaded_registries['entry_names'] = []
        RegistryManager.loaded_bloks['blok'] = {
            'entry': {
                'registry_names': ['key'],
                'key': {'properties': {'property': True},
                        'bases': [TestCase]},
            },
        }
        registry.load_entry('blok', 'entry')
        self.assertEqual(registry.loaded_registries['key'],
                         {'properties': {'property': True},
                          'bases': [TestCase]})

    def test_load_core(self):
        RegistryManager.loaded_bloks['blok'] = {
            'Core': {'Session': [TestCase]},
        }
        registry = self.init_registry(None)
        registry.load_core('blok', 'Session')
        self.assertIn(TestCase, registry.loaded_cores['Session'])

    def test_load_blok(self):

        class BlokTest(Blok):
            pass

        registry = self.init_registry(None)
        BlokManager.bloks['blok'] = BlokTest
        RegistryManager.loaded_bloks['blok'] = {
            'Core': {'Session': [TestCase],
                     'Base': [],
                     'SqlBase': [],
                     'SqlViewBase': [],
                     'Query': [],
                     'InstrumentedList': []},
            'removed': [],
            'properties': {},
        }
        for entry in RegistryManager.declared_entries:
            RegistryManager.loaded_bloks['blok'][entry] = {
                'registry_names': []}

        registry.load_blok('blok', False, [])
        self.assertIn(TestCase, registry.loaded_cores['Session'])

    def check_added_in_regisry(self, registry):
        self.assertEqual(registry.Test, Test)
        self.assertEqual(registry.Test.Test, TestTest)
        self.assertEqual(registry.Test.Test.Test, TestTestTest)

    def test_add_in_registry_1(self):
        registry = self.init_registry(None)
        registry.add_in_registry('Declarations.Test', Test)
        registry.add_in_registry('Declarations.Test.Test', TestTest)
        registry.add_in_registry('Declarations.Test.Test.Test', TestTestTest)
        self.check_added_in_regisry(registry)

    def test_add_in_registry_2(self):
        registry = self.init_registry(None)
        registry.add_in_registry('Declarations.Test', Test)
        registry.add_in_registry('Declarations.Test.Test.Test', TestTestTest)
        registry.add_in_registry('Declarations.Test.Test', TestTest)
        self.check_added_in_regisry(registry)

    def test_add_in_registry_3(self):
        registry = self.init_registry(None)
        registry.add_in_registry('Declarations.Test.Test', TestTest)
        registry.add_in_registry('Declarations.Test', Test)
        registry.add_in_registry('Declarations.Test.Test.Test', TestTestTest)
        self.check_added_in_regisry(registry)

    def test_add_in_registry_4(self):
        registry = self.init_registry(None)
        registry.add_in_registry('Declarations.Test.Test', TestTest)
        registry.add_in_registry('Declarations.Test.Test.Test', TestTestTest)
        registry.add_in_registry('Declarations.Test', Test)
        self.check_added_in_regisry(registry)

    def test_add_in_registry_5(self):
        registry = self.init_registry(None)
        registry.add_in_registry('Declarations.Test.Test.Test', TestTestTest)
        registry.add_in_registry('Declarations.Test', Test)
        registry.add_in_registry('Declarations.Test.Test', TestTest)
        self.check_added_in_regisry(registry)

    def test_add_in_registry_6(self):
        registry = self.init_registry(None)
        registry.add_in_registry('Declarations.Test.Test.Test', TestTestTest)
        registry.add_in_registry('Declarations.Test.Test', TestTest)
        registry.add_in_registry('Declarations.Test', Test)
        self.check_added_in_regisry(registry)

    def test_registry_db_exist(self):
        self.assertTrue(Configuration.get('Registry').db_exists(
            db_name=Configuration.get('db_name')))

    def test_registry_db_unexist(self):
        self.assertFalse(Configuration.get('Registry').db_exists(
            db_name='wrong_db_name'))


class TestRegistry2(DBTestCase):

    def add_model(self):

        from anyblok import Declarations

        register = Declarations.register
        Model = Declarations.Model

        @register(Model)
        class Test:

            id = Integer(primary_key=True)
            val = Integer(default=0)

            @classmethod
            def _precommit_hook(cls):
                for t in cls.query().all():
                    t.val += t.id

            def add_precommit_hook(self):
                self.precommit_hook('_precommit_hook')

            @classmethod
            def add_cl_precommit_hook(cls):
                cls.precommit_hook('_precommit_hook')

    def test_precommit_hook(self):
        registry = self.init_registry(self.add_model)
        t1 = registry.Test.insert()
        t1.add_precommit_hook()
        t2 = registry.Test.insert()
        t2.add_precommit_hook()
        self.assertEqual(t1.val, 0)
        self.assertEqual(t2.val, 0)
        registry.commit()
        self.assertEqual(t1.val, t1.id)
        self.assertEqual(t2.val, t2.id)
        registry.commit()
        self.assertEqual(t1.val, t1.id)
        self.assertEqual(t2.val, t2.id)
        registry.Test.add_cl_precommit_hook()
        self.assertEqual(t1.val, t1.id)
        self.assertEqual(t2.val, t2.id)
        registry.commit()
        self.assertEqual(t1.val, 2 * t1.id)
        self.assertEqual(t2.val, 2 * t2.id)
        registry.commit()
        self.assertEqual(t1.val, 2 * t1.id)
        self.assertEqual(t2.val, 2 * t2.id)
        t1.add_precommit_hook()
        self.assertEqual(t1.val, 2 * t1.id)
        self.assertEqual(t2.val, 2 * t2.id)
        registry.commit()
        self.assertEqual(t1.val, 3 * t1.id)
        self.assertEqual(t2.val, 3 * t2.id)

    def test_precommit_hook_in_thread(self):
        registry = self.init_registry(self.add_model)
        t1 = registry.Test.insert()
        t1.add_precommit_hook()
        t2 = registry.Test.insert()
        t2.add_precommit_hook()
        self.assertEqual(t1.val, 0)
        self.assertEqual(t2.val, 0)

        def target():
            registry.commit()

        t = Thread(target=target)
        t.start()
        t.join()

        self.assertEqual(t1.val, 0)
        self.assertEqual(t2.val, 0)
        registry.commit()
        self.assertEqual(t1.val, t1.id)
        self.assertEqual(t2.val, t2.id)

    def define_cls(self, typename='Model', name='Test', val=1, usesuper=False,
                   inherit=None):

        from anyblok import Declarations

        register = Declarations.register
        Type = getattr(Declarations, typename)
        if inherit is None:
            inherit = object
        else:
            inherit = getattr(Declarations.Mixin, inherit)

        @register(Type, name_=name)
        class Test(inherit):

            @classmethod
            def foo(cls):
                if usesuper:
                    return val * super(Test, cls).foo()

                return val

        return Test

    def test_check_define_cls(self):

        def add_in_registry():
            self.define_cls()

        registry = self.init_registry(add_in_registry)
        self.assertEqual(registry.Test.foo(), 1)

    def test_check_define_cls_with_inherit(self):

        def add_in_registry():
            self.define_cls()
            self.define_cls(val=2, usesuper=True)

        registry = self.init_registry(add_in_registry)
        self.assertEqual(registry.Test.foo(), 2)

    def test_check_define_cls_with_inherit_core(self):

        def add_in_registry():
            self.define_cls(typename='Core', name='Base', val=2)
            self.define_cls(val=2, usesuper=True)

        registry = self.init_registry(add_in_registry)
        self.assertEqual(registry.Test.foo(), 4)

    def test_check_define_cls_with_inherit_mixin(self):

        def add_in_registry():
            self.define_cls(typename='Mixin', name='MTest', val=3)
            self.define_cls(val=3, usesuper=True, inherit='MTest')

        registry = self.init_registry(add_in_registry)
        self.assertEqual(registry.Test.foo(), 9)

    def test_check_define_cls_with_inherit2(self):

        def add_in_registry():
            self.define_cls()
            self.define_cls(val=2, usesuper=True)
            self.define_cls(val=2, usesuper=True)

        registry = self.init_registry(add_in_registry)
        self.assertEqual(registry.Test.foo(), 4)

    def test_check_define_cls_with_inherit_core2(self):

        def add_in_registry():
            self.define_cls(typename='Core', name='Base', val=2)
            self.define_cls(typename='Core', name='Base', val=2, usesuper=True)
            self.define_cls(val=2, usesuper=True)

        registry = self.init_registry(add_in_registry)
        self.assertEqual(registry.Test.foo(), 8)

    def test_check_define_cls_with_inherit_mixin2(self):

        def add_in_registry():
            self.define_cls(typename='Mixin', name='MTest', val=3)
            self.define_cls(typename='Mixin', name='MTest', val=3,
                            usesuper=True)
            self.define_cls(val=3, usesuper=True, inherit='MTest')

        registry = self.init_registry(add_in_registry)
        self.assertEqual(registry.Test.foo(), 27)

    def test_remove(self):

        def add_in_registry():
            self.define_cls()
            cls_ = self.define_cls(val=2, usesuper=True)
            self.define_cls(val=2, usesuper=True)
            from anyblok import Declarations
            Declarations.unregister(Declarations.Model.Test, cls_)

        registry = self.init_registry(add_in_registry)
        self.assertEqual(registry.Test.foo(), 2)

    def test_remove_core(self):

        def add_in_registry():
            self.define_cls(typename='Core', name='Base', val=2)
            cls_ = self.define_cls(typename='Core', name='Base', val=2,
                                   usesuper=True)
            self.define_cls(val=2, usesuper=True)
            from anyblok import Declarations
            Declarations.unregister(Declarations.Core.Base, cls_)

        registry = self.init_registry(add_in_registry)
        self.assertEqual(registry.Test.foo(), 4)

    def test_remove_mixin(self):

        def add_in_registry():
            self.define_cls(typename='Mixin', name='MTest', val=3)
            cls_ = self.define_cls(typename='Mixin', name='MTest', val=3,
                                   usesuper=True)
            self.define_cls(val=3, usesuper=True, inherit='MTest')
            from anyblok import Declarations
            Declarations.unregister(Declarations.Mixin.MTest, cls_)

        registry = self.init_registry(add_in_registry)
        self.assertEqual(registry.Test.foo(), 9)
