# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok.registry import RegistryManager
from anyblok.common import return_list
from anyblok.blok import BlokManager
from anyblok.model import Model
from anyblok.environment import EnvironmentManager
from .conftest import init_registry


class TestRegistryManager:

    @pytest.fixture(autouse=True)
    def revert_registry_manager(self, request):
        def revert():
            RegistryManager.undeclare_entry('Other')

        request.addfinalizer(revert)

    def test_declared_entries(self):
        hasModel = 'Model' in RegistryManager.declared_entries
        hasMixin = 'Mixin' in RegistryManager.declared_entries
        assert hasModel
        assert hasMixin

    def test_init_blok(self):
        RegistryManager.init_blok('newblok')
        is_exist = 'newblok' in RegistryManager.loaded_bloks
        assert is_exist
        for core in ('Base', 'SqlBase', 'SqlViewBase', 'Session', 'Query',
                     'InstrumentedList'):
            assert core in RegistryManager.loaded_bloks[
                'newblok']['Core'].keys()
            assert RegistryManager.loaded_bloks['newblok']['Core'][core] == []

        assert RegistryManager.loaded_bloks['newblok']['Model'] == {
            'registry_names': []}
        assert RegistryManager.loaded_bloks['newblok']['Mixin'] == {
            'registry_names': []}

    def test_init_blok_with_other_entry(self):
        RegistryManager.declare_entry('Other')
        hasOther = 'Other' in RegistryManager.declared_entries
        assert hasOther
        RegistryManager.init_blok('newblok')
        is_exist = 'newblok' in RegistryManager.loaded_bloks
        assert is_exist
        for core in ('Base', 'SqlBase', 'SqlViewBase', 'Session', 'Query',
                     'InstrumentedList'):
            assert core in RegistryManager.loaded_bloks[
                'newblok']['Core'].keys()
            assert RegistryManager.loaded_bloks['newblok']['Core'][core] == []

        assert RegistryManager.loaded_bloks['newblok']['Model'] == {
            'registry_names': []}
        assert RegistryManager.loaded_bloks['newblok']['Mixin'] == {
            'registry_names': []}
        assert RegistryManager.loaded_bloks['newblok']['Other'] == {
            'registry_names': []}

    def test_anyblok_core_loaded(self):
        BlokManager.load()
        is_exist = 'anyblok-core' in RegistryManager.loaded_bloks
        assert is_exist
        anyblokcore = RegistryManager.loaded_bloks['anyblok-core']
        assert len(anyblokcore['Core']['Base']) == 1
        assert len(anyblokcore['Core']['SqlBase']) == 1
        assert len(anyblokcore['Core']['SqlViewBase']) == 1
        assert len(anyblokcore['Core']['Session']) == 1
        assert len(anyblokcore['Core']['Query']) == 1
        assert len(anyblokcore['Core']['InstrumentedList']) == 1
        is_exist = 'Model.System' in anyblokcore['Model']
        assert is_exist
        BlokManager.unload()

    def test_add_entry(self):
        RegistryManager.declare_entry('Other')
        RegistryManager.init_blok('newblok')
        is_exist = 'newblok' in RegistryManager.loaded_bloks
        assert is_exist
        for entry in ('Base', 'SqlBase', 'SqlViewBase', 'Session', 'Query',
                      'InstrumentedList'):
            assert RegistryManager.loaded_bloks['newblok']['Core'][entry] == []

        assert RegistryManager.loaded_bloks['newblok']['Model'] == {
            'registry_names': []}
        assert RegistryManager.loaded_bloks['newblok']['Mixin'] == {
            'registry_names': []}
        assert RegistryManager.loaded_bloks['newblok']['Other'] == {
            'registry_names': []}

    def test_add_callback(self):

        def callback():
            pass

        RegistryManager.declare_entry('Other', assemble_callback=callback,
                                      initialize_callback=callback)
        hasModel = 'Model' in RegistryManager.declared_entries
        hasMixin = 'Mixin' in RegistryManager.declared_entries
        hasOther = 'Other' in RegistryManager.declared_entries
        assert hasModel
        assert hasMixin
        assert hasOther

        cb = Model.assemble_callback
        hasModelCb = cb == RegistryManager.callback_assemble_entries['Model']
        cb = callback
        hasOtherCb = cb == RegistryManager.callback_assemble_entries['Other']
        assert hasModelCb
        assert hasOtherCb

        cb = Model.initialize_callback
        hasModelCb = cb == RegistryManager.callback_initialize_entries['Model']
        cb = callback
        hasOtherCb = cb == RegistryManager.callback_initialize_entries['Other']
        assert hasModelCb
        assert hasOtherCb

        RegistryManager.init_blok('newblok')
        is_exist = 'newblok' in RegistryManager.loaded_bloks
        assert is_exist
        hasCore = 'Core' in RegistryManager.loaded_bloks['newblok']
        hasModel = 'Model' in RegistryManager.loaded_bloks['newblok']
        hasMixin = 'Mixin' in RegistryManager.loaded_bloks['newblok']
        hasOther = 'Other' in RegistryManager.loaded_bloks['newblok']
        assert hasCore
        assert hasModel
        assert hasMixin
        assert hasOther

    def test_reload_blok(self):
        BlokManager.load()
        try:
            RegistryManager.reload()
        finally:
            BlokManager.unload()

    def test_global_property(self):
        RegistryManager.declare_entry('Other')
        blok = 'newblok'
        RegistryManager.init_blok(blok)
        try:
            oldblok = EnvironmentManager.get('current_blok')
            EnvironmentManager.set('current_blok', blok)
            assert not RegistryManager.has_blok_property('myproperty')
            RegistryManager.add_or_replace_blok_property('myproperty', 2)
            assert RegistryManager.has_blok_property('myproperty')
            assert RegistryManager.get_blok_property('myproperty') == 2
            RegistryManager.add_or_replace_blok_property('myproperty', 3)
            assert RegistryManager.get_blok_property('myproperty') == 3
            RegistryManager.remove_blok_property('myproperty')
            assert not RegistryManager.has_blok_property('myproperty')
        finally:
            EnvironmentManager.set('current_blok', oldblok)

    def test_has_entry_in_register(self):
        assert RegistryManager.has_entry_in_register(
            'anyblok-core', 'Model', 'Model.System') is True

    def test_has_entry_in_register_unexisting_entry(self):
        assert RegistryManager.has_entry_in_register(
            'anyblok-core', 'Unexisting', 'Model.System') is False

    def test_has_entry_in_register_unexisting_key(self):
        assert RegistryManager.has_entry_in_register(
            'anyblok-core', 'Model', 'Model.Unexisting') is False

    def test_reload(self, bloks_loaded):
        init_registry(None)
        RegistryManager.reload()

    def test_complete_reload(self, bloks_loaded):
        registry = init_registry(None)
        registry.complete_reload()

    def test_clear(self, bloks_loaded):
        init_registry(None)
        RegistryManager.clear()

    def test_has_blok_ok(self):
        assert RegistryManager.has_blok('anyblok-core') is True

    def test_has_blok_ko(self):
        assert RegistryManager.has_blok('unexisting-blok') is False

    def test_return_list_1(self):
        assert return_list('plop') == ['plop']

    def test_return_list_2(self):
        assert return_list(['plop']) == ['plop']
