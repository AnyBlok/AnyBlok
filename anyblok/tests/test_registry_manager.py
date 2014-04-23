# -*- coding: utf-8 -*-
from anyblok.tests.testcase import TestCase
from anyblok.registry import RegistryManager
from anyblok.blok import BlokManager
from anyblok.model import Model


old_loaded_bloks = RegistryManager.loaded_bloks
old_declared_entries = []
old_declared_entries += RegistryManager.declared_entries
old_callback_assemble_entries = RegistryManager.callback_assemble_entries
old_callback_initialize_entries = RegistryManager.callback_initialize_entries


class TestRegistryManager(TestCase):

    def setUp(self):
        super(TestRegistryManager, self).setUp()
        RegistryManager.loaded_bloks = old_loaded_bloks.copy()
        RegistryManager.declared_entries = [] + old_declared_entries
        cae = old_callback_assemble_entries.copy()
        RegistryManager.callback_assemble_entries = cae
        cie = old_callback_initialize_entries.copy()
        RegistryManager.callback_initialize_entries = cie

    def test_declared_entries(self):
        self.assertEqual(RegistryManager.declared_entries, ['Model', 'Mixin'])

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
        is_exist = 'Model.System' in anyblokcore['Model']
        self.assertEqual(is_exist, True)
        BlokManager.unload()

    def test_add_entry(self):
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

    def test_add_callback(self):

        def callback():
            pass

        RegistryManager.declare_entry('Other', assemble_callback=callback,
                                      initialize_callback=callback)
        self.assertEqual(RegistryManager.declared_entries,
                         ['Model', 'Mixin', 'Other'])
        self.assertEqual(RegistryManager.callback_assemble_entries,
                         {'Other': callback})
        self.assertEqual(RegistryManager.callback_initialize_entries,
                         {'Model': Model.initialize_callback,
                          'Other': callback})
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
