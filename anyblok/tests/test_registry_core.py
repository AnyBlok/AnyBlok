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


class TestRegistryCore:

    @pytest.fixture(scope="class", autouse=True)
    def init_env(self, request):

        def revert():
            EnvironmentManager.set('current_blok', None)
            del RegistryManager.loaded_bloks['testCore']
            RegistryManager.undeclare_core('test')

        request.addfinalizer(revert)
        RegistryManager.declare_core('test')
        RegistryManager.init_blok('testCore')
        EnvironmentManager.set('current_blok', 'testCore')

    @pytest.fixture(autouse=True)
    def init_registry(self, request):

        def revert():
            RegistryManager.loaded_bloks['testCore']['Core']['test'] = []

        request.addfinalizer(revert)

    def assertInCore(self, *args):
        blokname = 'testCore'
        blok = RegistryManager.loaded_bloks[blokname]
        assert len(blok['Core']['test']) == len(args)
        for cls_ in args:
            hasCls = cls_ in blok['Core']['test']
            assert hasCls

    def test_add_core(self):
        class test:
            pass

        RegistryManager.add_core_in_register('test', test)
        self.assertInCore(test)
        assert RegistryManager.has_core_in_register('testCore', 'test')

    def test_remove_core(self):
        class test:
            pass

        def has_test_in_removed():
            core = RegistryManager.loaded_bloks['testCore']['removed']
            if test in core:
                return True

            return False

        RegistryManager.add_core_in_register('test', test)
        self.assertInCore(test)
        assert not has_test_in_removed()
        RegistryManager.remove_in_register(test)
        assert has_test_in_removed()
