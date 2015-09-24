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
from anyblok.blok import BlokManager, Blok
from anyblok.column import Integer
from threading import Thread


class Test:
    pass


class TestTest:
    pass


class TestTestTest:
    pass


class TestRegistry(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestRegistry, cls).setUpClass()
        cls.init_configuration_manager()
        cls.createdb()
        BlokManager.load()

    def setUp(self):
        super(TestRegistry, self).setUp()
        self.registry = self.getRegistry()

    @classmethod
    def tearDownClass(cls):
        super(TestRegistry, cls).tearDownClass()
        BlokManager.unload()
        cls.dropdb()

    def tearDown(self):
        super(TestRegistry, self).tearDown()
        RegistryManager.clear()
        for cls in (Test, TestTest):
            if hasattr(cls, 'Test'):
                delattr(cls, 'Test')

    def test_get(self):
        self.registry.close()
        self.registry = self.getRegistry()

    def test_get_model(self):
        System = self.registry.get('Model.System')
        self.assertEqual(self.registry.System, System)

    def test_get_the_same_registry(self):
        registry = self.getRegistry()
        self.assertEqual(self.registry, registry)

    def test_reload(self):
        bloks_before_reload = self.registry.System.Blok.query('name').filter(
            self.registry.System.Blok.state == 'installed').all()
        self.registry.reload()
        bloks_after_reload = self.registry.System.Blok.query('name').filter(
            self.registry.System.Blok.state == 'installed').all()
        self.assertEqual(bloks_before_reload, bloks_after_reload)

    def test_get_bloks_to_load(self):
        bloks = self.registry.get_bloks_to_load()
        have_anyblokcore = 'anyblok-core' in bloks
        self.assertEqual(have_anyblokcore, True)

    def test_load_entry(self):
        self.registry.loaded_registries['entry_names'] = []
        RegistryManager.loaded_bloks['blok'] = {
            'entry': {
                'registry_names': ['key'],
                'key': {'properties': {'property': True}, 'bases': [TestCase]},
            },
        }
        self.registry.load_entry('blok', 'entry')
        self.assertEqual(self.registry.loaded_registries['key'],
                         {'properties': {'property': True},
                          'bases': [TestCase]})

    def test_load_core(self):
        RegistryManager.loaded_bloks['blok'] = {
            'Core': {'Session': [TestCase]},
        }
        self.registry.load_core('blok', 'Session')
        have_session = TestCase in self.registry.loaded_cores['Session']
        self.assertEqual(have_session, True)

    def test_load_blok(self):

        class BlokTest(Blok):
            pass

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

        self.registry.load_blok('blok', False, [])
        have_session = TestCase in self.registry.loaded_cores['Session']
        self.assertEqual(have_session, True)

    def check_added_in_regisry(self):
        self.assertEqual(self.registry.Test, Test)
        self.assertEqual(self.registry.Test.Test, TestTest)
        self.assertEqual(self.registry.Test.Test.Test, TestTestTest)

    def test_add_in_registry_1(self):
        self.registry.add_in_registry('Declarations.Test', Test)
        self.registry.add_in_registry('Declarations.Test.Test', TestTest)
        self.registry.add_in_registry('Declarations.Test.Test.Test',
                                      TestTestTest)
        self.check_added_in_regisry()

    def test_add_in_registry_2(self):
        self.registry.add_in_registry('Declarations.Test', Test)
        self.registry.add_in_registry('Declarations.Test.Test.Test',
                                      TestTestTest)
        self.registry.add_in_registry('Declarations.Test.Test', TestTest)
        self.check_added_in_regisry()

    def test_add_in_registry_3(self):
        self.registry.add_in_registry('Declarations.Test.Test', TestTest)
        self.registry.add_in_registry('Declarations.Test', Test)
        self.registry.add_in_registry('Declarations.Test.Test.Test',
                                      TestTestTest)
        self.check_added_in_regisry()

    def test_add_in_registry_4(self):
        self.registry.add_in_registry('Declarations.Test.Test', TestTest)
        self.registry.add_in_registry('Declarations.Test.Test.Test',
                                      TestTestTest)
        self.registry.add_in_registry('Declarations.Test', Test)
        self.check_added_in_regisry()

    def test_add_in_registry_5(self):
        self.registry.add_in_registry('Declarations.Test.Test.Test',
                                      TestTestTest)
        self.registry.add_in_registry('Declarations.Test', Test)
        self.registry.add_in_registry('Declarations.Test.Test', TestTest)
        self.check_added_in_regisry()

    def test_add_in_registry_6(self):
        self.registry.add_in_registry('Declarations.Test.Test.Test',
                                      TestTestTest)
        self.registry.add_in_registry('Declarations.Test.Test', TestTest)
        self.registry.add_in_registry('Declarations.Test', Test)
        self.check_added_in_regisry()


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

    def test_check_dbtestcase_desable_ci(self):
        registry = self.init_registry(self.add_model)
        registry.begin_nested()  # add SAVEPOINT
        registry.Test.insert()
        registry.commit()
        self.assertEqual(registry.Test.query().count(), 1)
        registry.rollback()  # rollback() to SAVEPOINT
        self.assertEqual(registry.Test.query().count(), 0)

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
