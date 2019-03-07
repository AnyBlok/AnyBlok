# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok.registry import RegistryManager
from anyblok import Declarations
from anyblok.environment import EnvironmentManager
from anyblok.blok import BlokManager

register = Declarations.register
unregister = Declarations.unregister
Core = Declarations.Core


class OneInterface:
    pass


@pytest.fixture(scope="module")
def bloks_loaded(request):
    request.addfinalizer(BlokManager.unload)
    BlokManager.load()


class TestCoreInterfaceCoreBase:

    _corename = 'Base'

    @pytest.fixture(autouse=True, scope="class")
    def add_testCore(self, request, bloks_loaded):
        def reset():
            EnvironmentManager.set('current_blok', None)
            del RegistryManager.loaded_bloks['testCore' + self._corename]

        request.addfinalizer(reset)
        RegistryManager.init_blok('testCore' + self._corename)
        EnvironmentManager.set('current_blok', 'testCore' + self._corename)

    @pytest.fixture(autouse=True)
    def initialize_testCore(self, bloks_loaded):
        blokname = 'testCore' + self._corename
        RegistryManager.loaded_bloks[blokname]['Core'][self._corename] = []

    def assertInCore(self, *args):
        blokname = 'testCore' + self._corename
        blok = RegistryManager.loaded_bloks[blokname]
        assert len(blok['Core'][self._corename]) == len(args)
        for cls_ in args:
            hasCls = cls_ in blok['Core'][self._corename]
            assert hasCls is True

    def assertInRemoved(self, cls):
        core = RegistryManager.loaded_bloks['testCoreBase']['removed']
        if cls in core:
            return True

        self.fail('Not in removed')

    def test_add_interface(self):
        register(Core, cls_=OneInterface, name_='Base')
        assert 'Core' == Core.Base.__declaration_type__
        self.assertInCore(OneInterface)
        dir(Declarations.Core.Base)

    def test_add_interface_with_decorator(self):

        @register(Core)
        class Base:
            pass

        assert 'Core' == Core.Base.__declaration_type__
        self.assertInCore(Base)

    def test_add_two_interface(self):

        register(Core, cls_=OneInterface, name_="Base")

        @register(Core)
        class Base:
            pass

        self.assertInCore(OneInterface, Base)

    def test_remove_interface_with_1_cls_in_registry(self):

        register(Core, cls_=OneInterface, name_="Base")
        self.assertInCore(OneInterface)
        unregister(Core.Base, OneInterface)
        self.assertInCore(OneInterface)
        self.assertInRemoved(OneInterface)

    def test_remove_interface_with_2_cls_in_registry(self):

        register(Core, cls_=OneInterface, name_="Base")

        @register(Core)
        class Base:
            pass

        self.assertInCore(OneInterface, Base)
        unregister(Core.Base, OneInterface)
        self.assertInCore(Base, OneInterface)
        self.assertInRemoved(OneInterface)
