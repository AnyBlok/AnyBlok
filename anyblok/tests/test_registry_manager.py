# -*- coding: utf-8 -*-
from anyblok.tests.testcase import TestCase
from anyblok.registry import RegistryManager
from anyblok.blok import BlokManager


old_loaded_bloks = RegistryManager.loaded_bloks
old_declared_entries = []
old_declared_entries += RegistryManager.declared_entries
old_mustbeload_declared_entries = []
old_mustbeload_declared_entries += RegistryManager.mustbeload_declared_entries
old_callback_declared_entries = RegistryManager.callback_declared_entries


class TestRegistryManager(TestCase):

    def setUp(self):
        super(TestRegistryManager, self).setUp()
        RegistryManager.loaded_bloks = old_loaded_bloks.copy()
        RegistryManager.declared_entries = [] + old_declared_entries
        mde = [] + old_mustbeload_declared_entries
        RegistryManager.mustbeload_declared_entries = mde
        cde = old_callback_declared_entries.copy()
        RegistryManager.callback_declared_entries = cde

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
                             'Model': {'registry_names': []},
                             'Mixin': {'registry_names': []}})

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
                             'Model': {'registry_names': []},
                             'Mixin': {'registry_names': []},
                             'Other': {'registry_names': []}})

    def test_anyblok_core_loaded(self):
        BlokManager.load('AnyBlok')
        is_exist = 'anyblok-core' in RegistryManager.loaded_bloks
        self.assertEqual(is_exist, True)
        anyblokcore = RegistryManager.loaded_bloks['anyblok-core']
        self.assertEqual(len(anyblokcore['Core']['Base']), 1)
        self.assertEqual(len(anyblokcore['Core']['SqlBase']), 1)
        self.assertEqual(len(anyblokcore['Core']['Session']), 1)
        is_exist = 'AnyBlok.Model.System' in anyblokcore['Model']
        self.assertEqual(is_exist, True)
        BlokManager.unload()

    def test_add_mustbeload(self):
        RegistryManager.declare_entry('Other', mustbeload=True)
        self.assertEqual(RegistryManager.declared_entries,
                         ['Model', 'Mixin', 'Other'])
        self.assertEqual(RegistryManager.mustbeload_declared_entries,
                         ['Model', 'Other'])
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
                             'Model': {'registry_names': []},
                             'Mixin': {'registry_names': []},
                             'Other': {'registry_names': []}})

    def test_add_callback(self):

        def callback():
            pass

        RegistryManager.declare_entry('Other', callback=callback)
        self.assertEqual(RegistryManager.declared_entries,
                         ['Model', 'Mixin', 'Other'])
        self.assertEqual(RegistryManager.mustbeload_declared_entries,
                         ['Model'])
        self.assertEqual(RegistryManager.callback_declared_entries,
                         {'Other': callback})
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
                             'Model': {'registry_names': []},
                             'Mixin': {'registry_names': []},
                             'Other': {'registry_names': []}})

    def test_reload_blok(self):
        BlokManager.load('AnyBlok')
        try:
            RegistryManager.reload('anyblok-core')
        finally:
            BlokManager.unload()
