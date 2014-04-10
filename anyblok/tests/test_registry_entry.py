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


class TestRegistryEntry(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestRegistryEntry, cls).setUpClass()
        RegistryManager.declare_entry('Other')
        RegistryManager.init_blok('testEntry')
        AnyBlok.current_blok = 'testEntry'

    @classmethod
    def tearDownClass(cls):
        super(TestRegistryEntry, cls).tearDownClass()
        AnyBlok.current_blok = None
        del RegistryManager.loaded_bloks['testEntry']

    def tearDown(self):
        super(TestRegistryEntry, self).tearDown()
        del RegistryManager.loaded_bloks['testEntry']['Other']['test']

    def assertInEntry(self, entry, *args):
        blokname = 'testEntry'
        blok = RegistryManager.loaded_bloks[blokname]
        self.assertEqual(len(blok['Other'][entry]['bases']), len(args))
        for cls_ in args:
            hasCls = cls_ in blok['Other'][entry]['bases']
            self.assertEqual(hasCls, True)

    def test_add_core(self):
        class test:
            pass

        RegistryManager.add_entry_in_target_registry('Other', 'test', test)
        self.assertInEntry('test', test)
        self.assertEqual(
            RegistryManager.has_entry_in_target_registry('testEntry', 'Other',
                                                         'test'),
            True)

    def test_remove_core(self):
        class test:
            pass

        RegistryManager.add_entry_in_target_registry('Other', 'test', test)
        self.assertInEntry('test', test)
        self.assertEqual(
            RegistryManager.has_entry_in_target_registry('testEntry', 'Other',
                                                         'test'),
            True)
        RegistryManager.remove_entry_in_target_registry(
            'testEntry', 'Other', 'test', test)
        self.assertEqual(
            RegistryManager.has_entry_in_target_registry('testEntry', 'Other',
                                                         'test'),
            False)
