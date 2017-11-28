# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase, DBTestCase, LogCapture
from anyblok.registry import RegistryManager
from anyblok.config import Configuration
from anyblok.blok import BlokManager, Blok
from anyblok.column import Integer
from threading import Thread
from logging import ERROR


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

    def test_precommit_hook_in_thread_2(self):
        do_somthing = 0

        def add_in_registry():

            from anyblok import Declarations

            @Declarations.register(Declarations.Model)
            class Test:

                @classmethod
                def _precommit_hook(cls):
                    nonlocal do_somthing
                    do_somthing += 1

        registry = self.init_registry(add_in_registry)
        self.assertEqual(do_somthing, 0)

        def target():
            registry.Test.precommit_hook('_precommit_hook')
            registry.commit()

        t = Thread(target=target)
        t.start()
        t.join()

        registry.commit()
        self.assertEqual(do_somthing, 1)

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

    def test_postcommit_hook(self):
        do_somthing = 0

        def add_in_registry():

            from anyblok import Declarations

            @Declarations.register(Declarations.Model)
            class Test:

                id = Integer(primary_key=True)

                @classmethod
                def _postcommit_hook(cls):
                    nonlocal do_somthing
                    do_somthing += 1

                def add_precommit_hook(self):
                    self.postcommit_hook('_postcommit_hook')

                @classmethod
                def add_cl_precommit_hook(cls):
                    cls.postcommit_hook('_postcommit_hook')

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert()
        t.add_precommit_hook()
        self.assertEqual(do_somthing, 0)
        registry.commit()
        self.assertEqual(do_somthing, 1)
        registry.commit()
        self.assertEqual(do_somthing, 1)
        registry.Test.add_cl_precommit_hook()
        self.assertEqual(do_somthing, 1)
        registry.commit()
        self.assertEqual(do_somthing, 2)
        registry.commit()
        self.assertEqual(do_somthing, 2)
        t.add_precommit_hook()
        self.assertEqual(do_somthing, 2)
        registry.commit()
        self.assertEqual(do_somthing, 3)

    def test_postcommit_hook_in_thread(self):
        do_somthing = 0

        def add_in_registry():

            from anyblok import Declarations

            @Declarations.register(Declarations.Model)
            class Test:

                @classmethod
                def _postcommit_hook(cls):
                    nonlocal do_somthing
                    do_somthing += 1

        registry = self.init_registry(add_in_registry)
        registry.Test.postcommit_hook('_postcommit_hook')
        self.assertEqual(do_somthing, 0)

        def target():
            registry.commit()

        t = Thread(target=target)
        t.start()
        t.join()

        self.assertEqual(do_somthing, 0)
        registry.commit()
        self.assertEqual(do_somthing, 1)

    def test_postcommit_hook_in_thread_2(self):
        do_somthing = 0

        def add_in_registry():

            from anyblok import Declarations

            @Declarations.register(Declarations.Model)
            class Test:

                @classmethod
                def _postcommit_hook(cls):
                    nonlocal do_somthing
                    do_somthing += 1

        registry = self.init_registry(add_in_registry)
        self.assertEqual(do_somthing, 0)

        def target():
            registry.Test.postcommit_hook('_postcommit_hook')
            registry.commit()

        t = Thread(target=target)
        t.start()
        t.join()

        self.assertEqual(do_somthing, 1)

    def test_postcommit_hook_call_only_if_commited(self):
        do_somthing = 0

        def add_in_registry():

            from anyblok import Declarations

            @Declarations.register(Declarations.Model)
            class Test:

                @classmethod
                def _precommit_hook(cls):
                    raise Exception('Test')

                @classmethod
                def _postcommit_hook(cls):
                    nonlocal do_somthing
                    do_somthing += 1

        registry = self.init_registry(add_in_registry)
        registry.Test.postcommit_hook('_postcommit_hook')
        self.assertEqual(do_somthing, 0)
        registry.commit()
        self.assertEqual(do_somthing, 1)
        registry.Test.precommit_hook('_precommit_hook')
        registry.Test.postcommit_hook('_postcommit_hook')
        with self.assertRaises(Exception):
            registry.commit()

        self.assertEqual(do_somthing, 1)

    def test_postcommit_hook_call_only_if_raised(self):
        do_somthing = 0

        def add_in_registry():

            from anyblok import Declarations

            @Declarations.register(Declarations.Model)
            class Test:

                @classmethod
                def _precommit_hook(cls):
                    raise Exception('Test')

                @classmethod
                def _postcommit_hook(cls):
                    nonlocal do_somthing
                    do_somthing += 1

        registry = self.init_registry(add_in_registry)
        registry.Test.postcommit_hook(
            '_postcommit_hook', call_only_if='raised')
        self.assertEqual(do_somthing, 0)
        registry.commit()
        self.assertEqual(do_somthing, 0)
        registry.Test.precommit_hook('_precommit_hook')
        registry.Test.postcommit_hook(
            '_postcommit_hook', call_only_if='raised')
        with self.assertRaises(Exception):
            registry.commit()

        self.assertEqual(do_somthing, 1)

    def test_postcommit_hook_call_only_if_always(self):
        do_somthing = 0

        def add_in_registry():

            from anyblok import Declarations

            @Declarations.register(Declarations.Model)
            class Test:

                @classmethod
                def _precommit_hook(cls):
                    raise Exception('Test')

                @classmethod
                def _postcommit_hook(cls):
                    nonlocal do_somthing
                    do_somthing += 1

        registry = self.init_registry(add_in_registry)
        registry.Test.postcommit_hook(
            '_postcommit_hook', call_only_if='always')
        self.assertEqual(do_somthing, 0)
        registry.commit()
        self.assertEqual(do_somthing, 1)
        registry.Test.precommit_hook('_precommit_hook')
        registry.Test.postcommit_hook(
            '_postcommit_hook', call_only_if='always')
        with self.assertRaises(Exception):
            registry.commit()

        self.assertEqual(do_somthing, 2)

    def test_postcommit_hook_with_rollback(self):
        do_somthing = 0

        def add_in_registry():

            from anyblok import Declarations

            @Declarations.register(Declarations.Model)
            class Test:

                @classmethod
                def _postcommit_hook(cls):
                    nonlocal do_somthing
                    do_somthing += 1

        registry = self.init_registry(add_in_registry)
        registry.Test.postcommit_hook(
            '_postcommit_hook')
        self.assertEqual(do_somthing, 0)
        registry.rollback()
        registry.commit()
        self.assertEqual(do_somthing, 0)

    def test_postcommit_hook_with_exception(self):

        def add_in_registry():

            from anyblok import Declarations

            @Declarations.register(Declarations.Model)
            class Test:

                @classmethod
                def _postcommit_hook(cls):
                    raise Exception('Here one exception')

        registry = self.init_registry(add_in_registry)
        registry.Test.postcommit_hook(
            '_postcommit_hook')
        with LogCapture('anyblok.registry', level=ERROR) as logs:
            registry.commit()
            messages = logs.get_error_messages()
            message = messages[0]
            self.assertIn('Here one exception', message)
