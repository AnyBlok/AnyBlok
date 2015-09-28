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
from anyblok.blok import BlokManager
from anyblok.model import Model
from anyblok.environment import EnvironmentManager


class TestRegistryManager(TestCase):

    @classmethod
    def tearDownClass(cls):
        super(TestRegistryManager, cls).tearDownClass()
        RegistryManager.undeclare_entry('Other')

    def test_declared_entries(self):
        hasModel = 'Model' in RegistryManager.declared_entries
        hasMixin = 'Mixin' in RegistryManager.declared_entries
        self.assertEqual(hasModel, True)
        self.assertEqual(hasMixin, True)

    def test_init_blok(self):
        RegistryManager.init_blok('newblok')
        is_exist = 'newblok' in RegistryManager.loaded_bloks
        self.assertEqual(is_exist, True)
        for core in ('Base', 'SqlBase', 'SqlViewBase', 'Session', 'Query',
                     'InstrumentedList'):
            self.assertIn(
                core, RegistryManager.loaded_bloks['newblok']['Core'].keys())
            self.assertEqual(
                RegistryManager.loaded_bloks['newblok']['Core'][core], [])

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
        for core in ('Base', 'SqlBase', 'SqlViewBase', 'Session', 'Query',
                     'InstrumentedList'):
            self.assertIn(
                core, RegistryManager.loaded_bloks['newblok']['Core'].keys())
            self.assertEqual(
                RegistryManager.loaded_bloks['newblok']['Core'][core], [])

        self.assertEqual(RegistryManager.loaded_bloks['newblok']['Model'],
                         {'registry_names': []})
        self.assertEqual(RegistryManager.loaded_bloks['newblok']['Mixin'],
                         {'registry_names': []})
        self.assertEqual(RegistryManager.loaded_bloks['newblok']['Other'],
                         {'registry_names': []})

    def test_anyblok_core_loaded(self):
        BlokManager.load()
        is_exist = 'anyblok-core' in RegistryManager.loaded_bloks
        self.assertEqual(is_exist, True)
        anyblokcore = RegistryManager.loaded_bloks['anyblok-core']
        self.assertEqual(len(anyblokcore['Core']['Base']), 1)
        self.assertEqual(len(anyblokcore['Core']['SqlBase']), 1)
        self.assertEqual(len(anyblokcore['Core']['SqlViewBase']), 1)
        self.assertEqual(len(anyblokcore['Core']['Session']), 1)
        self.assertEqual(len(anyblokcore['Core']['Query']), 1)
        self.assertEqual(len(anyblokcore['Core']['InstrumentedList']), 1)
        is_exist = 'Model.System' in anyblokcore['Model']
        self.assertEqual(is_exist, True)
        BlokManager.unload()

    def test_add_entry(self):
        RegistryManager.declare_entry('Other')
        RegistryManager.init_blok('newblok')
        is_exist = 'newblok' in RegistryManager.loaded_bloks
        self.assertEqual(is_exist, True)
        for entry in ('Base', 'SqlBase', 'SqlViewBase', 'Session', 'Query',
                      'InstrumentedList'):
            self.assertEqual(
                RegistryManager.loaded_bloks['newblok']['Core'][entry], [])

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
        BlokManager.load()
        try:
            RegistryManager.reload('anyblok-core')
        finally:
            BlokManager.unload()

    def test_global_property(self):
        RegistryManager.declare_entry('Other')
        blok = 'newblok'
        RegistryManager.init_blok(blok)
        try:
            oldblok = EnvironmentManager.get('current_blok')
            EnvironmentManager.set('current_blok', blok)
            self.assertEqual(RegistryManager.has_blok_property('myproperty'),
                             False)
            RegistryManager.add_or_replace_blok_property('myproperty', 2)
            self.assertEqual(
                RegistryManager.has_blok_property('myproperty'), True)
            self.assertEqual(
                RegistryManager.get_blok_property('myproperty'), 2)
            RegistryManager.add_or_replace_blok_property('myproperty', 3)
            self.assertEqual(
                RegistryManager.get_blok_property('myproperty'), 3)
            RegistryManager.remove_blok_property('myproperty')
            self.assertEqual(RegistryManager.has_blok_property('myproperty'),
                             False)
        finally:
            EnvironmentManager.set('current_blok', oldblok)
