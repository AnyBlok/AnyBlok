# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase
from anyblok.registry import RegistryManager
from anyblok.blok import BlokManager, Blok


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
        cls.init_argsparse_manager()
        cls.createdb()
        BlokManager.load('AnyBlok')

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
