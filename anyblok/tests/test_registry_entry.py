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
from anyblok.environment import EnvironmentManager


class TestRegistryEntry:

    @pytest.fixture(scope="class", autouse=True)
    def init_env(self, request):

        def revert():
            EnvironmentManager.set('current_blok', None)
            del RegistryManager.loaded_bloks['testEntry']
            RegistryManager.undeclare_entry('Other')

        request.addfinalizer(revert)
        RegistryManager.declare_entry('Other')
        RegistryManager.init_blok('testEntry')
        EnvironmentManager.set('current_blok', 'testEntry')

    @pytest.fixture(autouse=True)
    def init_registry(self, request):

        def revert():
            del RegistryManager.loaded_bloks['testEntry']['Other']['test']

        request.addfinalizer(revert)

    def assertInEntry(self, entry, *args):
        blokname = 'testEntry'
        blok = RegistryManager.loaded_bloks[blokname]
        assert len(blok['Other'][entry]['bases']) == len(args)
        for cls_ in args:
            hasCls = cls_ in blok['Other'][entry]['bases']
            assert hasCls

    def test_add_entry(self):
        class test:
            pass

        RegistryManager.add_entry_in_register('Other', 'test', test)
        self.assertInEntry('test', test)
        assert RegistryManager.has_entry_in_register(
            'testEntry', 'Other', 'test')

    def test_remove_entry(self):
        class test:
            pass

        def has_test_in_removed():
            core = RegistryManager.loaded_bloks['testEntry']['removed']
            if test in core:
                return True

            return False

        RegistryManager.add_entry_in_register('Other', 'test', test)
        self.assertInEntry('test', test)
        assert not (has_test_in_removed())
        RegistryManager.remove_in_register(test)
        assert has_test_in_removed()

    def test_get_entry_properties_in_register(self):
        class test:
            pass

        RegistryManager.add_entry_in_register('Other', 'test', test,
                                              property1='test')
        properties = RegistryManager.get_entry_properties_in_register(
            'Other', 'test')

        hasproperty1 = 'property1' in properties
        assert hasproperty1
        assert properties['property1'] == 'test'
