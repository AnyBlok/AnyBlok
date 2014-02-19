# -*- coding: utf-8 -*-
import unittest
from anyblok.registry import RegistryManager
from anyblok.blok import BlokManager


old_loaded_bloks = RegistryManager.loaded_bloks
old_declared_entries = RegistryManager.declared_entries
old_mustbeload_declared_entries = RegistryManager.mustbeload_declared_entries


class TestRegistryManager(unittest.TestCase):

    def setUp(self):
        super(TestRegistryManager, self).setUp()
        RegistryManager.loaded_bloks = old_loaded_bloks.copy()
        RegistryManager.declared_entries = [] + old_declared_entries
        mde = [] + old_mustbeload_declared_entries
        RegistryManager.mustbeload_declared_entries = mde

    def test_declared_entries(self):
        self.assertEqual(RegistryManager.declared_entries, ['Model', 'Mixin'])
        self.assertEqual(RegistryManager.mustbeload_declared_entries,
                         ['Model'])

    def test_init_blok(self):
        RegistryManager.init_blok('newblok')
        is_exist = 'newblok' in RegistryManager.loaded_bloks
        self.assertEqual(is_exist, True)
        self.assertEqual(RegistryManager.loaded_bloks['newblok'],
                         {
                             'Core': {
                                 'Base': [],
                                 'SqlBase': [],
                                 'Session': [],
                             },
                             'Model': {},
                             'Mixin': {},
                         })

    def test_init_blok_with_other_entry(self):
        RegistryManager.declare_entry('Other')
        self.assertEqual(RegistryManager.declared_entries,
                         ['Model', 'Mixin', 'Other'])
        RegistryManager.init_blok('newblok')
        is_exist = 'newblok' in RegistryManager.loaded_bloks
        self.assertEqual(is_exist, True)
        self.assertEqual(RegistryManager.loaded_bloks['newblok'],
                         {
                             'Core': {
                                 'Base': [],
                                 'SqlBase': [],
                                 'Session': [],
                             },
                             'Model': {},
                             'Mixin': {},
                             'Other': {},
                         })

    def test_anyblok_core_loaded(self):
        BlokManager.load('AnyBlok')
        is_exist = 'anyblok-core' in RegistryManager.loaded_bloks
        self.assertEqual(is_exist, True)
        anyblokcore = RegistryManager.loaded_bloks['anyblok-core']
        self.assertEqual(len(anyblokcore['Core']['Base']), 1)
        self.assertEqual(len(anyblokcore['Core']['SqlBase']), 1)
        self.assertEqual(len(anyblokcore['Core']['Session']), 1)
        is_exist = 'AnyBlok.System' in anyblokcore['Model']
        self.assertEqual(is_exist, True)


class TestRegistry(unittest.TestCase):
    pass
