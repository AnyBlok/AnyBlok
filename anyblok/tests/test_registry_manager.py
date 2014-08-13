# -*- coding: utf-8 -*-
from anyblok.tests.testcase import TestCase
from anyblok.registry import RegistryManager
from anyblok.blok import BlokManager
from anyblok.model import Model


class TestRegistryManager(TestCase):

    def test_declared_entries(self):
        hasModel = 'Model' in RegistryManager.declared_entries
        hasMixin = 'Mixin' in RegistryManager.declared_entries
        self.assertEqual(hasModel, True)
        self.assertEqual(hasMixin, True)

    def test_init_blok(self):
        RegistryManager.init_blok('newblok')
        is_exist = 'newblok' in RegistryManager.loaded_bloks
        self.assertEqual(is_exist, True)
        self.assertEqual(RegistryManager.loaded_bloks['newblok']['Core'],
                         {'Base': [], 'SqlBase': [], 'Session': []})
        self.assertEqual(RegistryManager.loaded_bloks['newblok']['Model'],
                         {'registry_names': []})
        self.assertEqual(RegistryManager.loaded_bloks['newblok']['Mixin'],
                         {'registry_names': []})

    def test_init_blok_with_other_entry(self):
        RegistryManager.declare_entry('Other')
        hasOther = 'Other' in RegistryManager.declared_entries
        self.assertEqual(hasOther, True)
        RegistryManager.init_blok('newblok')
        is_exist = 'newblok' in RegistryManager.loaded_bloks
        self.assertEqual(is_exist, True)
        self.assertEqual(RegistryManager.loaded_bloks['newblok']['Core'],
                         {'Base': [], 'SqlBase': [], 'Session': []})
        self.assertEqual(RegistryManager.loaded_bloks['newblok']['Model'],
                         {'registry_names': []})
        self.assertEqual(RegistryManager.loaded_bloks['newblok']['Mixin'],
                         {'registry_names': []})
        self.assertEqual(RegistryManager.loaded_bloks['newblok']['Other'],
                         {'registry_names': []})

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
        RegistryManager.init_blok('newblok')
        is_exist = 'newblok' in RegistryManager.loaded_bloks
        self.assertEqual(is_exist, True)
        self.assertEqual(RegistryManager.loaded_bloks['newblok']['Core'],
                         {'Base': [], 'SqlBase': [], 'Session': []})
        self.assertEqual(RegistryManager.loaded_bloks['newblok']['Model'],
                         {'registry_names': []})
        self.assertEqual(RegistryManager.loaded_bloks['newblok']['Mixin'],
                         {'registry_names': []})
        self.assertEqual(RegistryManager.loaded_bloks['newblok']['Other'],
                         {'registry_names': []})

    def test_add_callback(self):

        def callback():
            pass

        RegistryManager.declare_entry('Other', assemble_callback=callback,
                                      initialize_callback=callback)
        hasModel = 'Model' in RegistryManager.declared_entries
        hasMixin = 'Mixin' in RegistryManager.declared_entries
        hasOther = 'Other' in RegistryManager.declared_entries
        self.assertEqual(hasModel, True)
        self.assertEqual(hasMixin, True)
        self.assertEqual(hasOther, True)

        cb = Model.assemble_callback
        hasModelCb = cb == RegistryManager.callback_assemble_entries['Model']
        cb = callback
        hasOtherCb = cb == RegistryManager.callback_assemble_entries['Other']
        self.assertEqual(hasModelCb, True)
        self.assertEqual(hasOtherCb, True)

        cb = Model.initialize_callback
        hasModelCb = cb == RegistryManager.callback_initialize_entries['Model']
        cb = callback
        hasOtherCb = cb == RegistryManager.callback_initialize_entries['Other']
        self.assertEqual(hasModelCb, True)
        self.assertEqual(hasOtherCb, True)

        RegistryManager.init_blok('newblok')
        is_exist = 'newblok' in RegistryManager.loaded_bloks
        self.assertEqual(is_exist, True)
        hasCore = 'Core' in RegistryManager.loaded_bloks['newblok']
        hasModel = 'Model' in RegistryManager.loaded_bloks['newblok']
        hasMixin = 'Mixin' in RegistryManager.loaded_bloks['newblok']
        hasOther = 'Other' in RegistryManager.loaded_bloks['newblok']
        self.assertEqual(hasCore, True)
        self.assertEqual(hasModel, True)
        self.assertEqual(hasMixin, True)
        self.assertEqual(hasOther, True)

    def test_reload_blok(self):
        BlokManager.load('AnyBlok')
        try:
            RegistryManager.reload('anyblok-core')
        finally:
            BlokManager.unload()
