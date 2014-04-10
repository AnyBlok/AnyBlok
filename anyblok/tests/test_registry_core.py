# -*- coding: utf-8 -*-
from anyblok.tests.testcase import TestCase
from anyblok.registry import RegistryManager
from anyblok import AnyBlok


old_loaded_bloks = RegistryManager.loaded_bloks
old_declared_entries = []
old_declared_entries += RegistryManager.declared_entries
old_mustbeload_declared_entries = []
old_mustbeload_declared_entries += RegistryManager.mustbeload_declared_entries
old_callback_declared_entries = RegistryManager.callback_declared_entries


class TestRegistryCore(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestRegistryCore, cls).setUpClass()
        RegistryManager.init_blok('testCore')
        AnyBlok.current_blok = 'testCore'

    @classmethod
    def tearDownClass(cls):
        super(TestRegistryCore, cls).tearDownClass()
        AnyBlok.current_blok = None
        del RegistryManager.loaded_bloks['testCore']

    def setUp(self):
        super(TestRegistryCore, self).setUp()
        blokname = 'testCore'
        RegistryManager.loaded_bloks[blokname]['Core']['test'] = []

    def assertInCore(self, *args):
        blokname = 'testCore'
        blok = RegistryManager.loaded_bloks[blokname]
        self.assertEqual(len(blok['Core']['test']), len(args))
        for cls_ in args:
            hasCls = cls_ in blok['Core']['test']
            self.assertEqual(hasCls, True)

    def test_add_core(self):
        class test:
            pass

        RegistryManager.add_core_in_target_registry('test', test)
        self.assertInCore(test)
        self.assertEqual(
            RegistryManager.has_core_in_target_registry('testCore', 'test'),
            True)

    def test_remove_core(self):
        class test:
            pass

        RegistryManager.add_core_in_target_registry('test', test)
        self.assertInCore(test)
        self.assertEqual(
            RegistryManager.has_core_in_target_registry('testCore', 'test'),
            True)
        RegistryManager.remove_core_in_target_registry(
            'testCore', 'test', test)
        self.assertEqual(
            RegistryManager.has_core_in_target_registry('testCore', 'test'),
            False)
