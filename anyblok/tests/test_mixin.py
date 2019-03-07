# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok.registry import RegistryManager
from anyblok import Declarations
from anyblok.environment import EnvironmentManager
register = Declarations.register
unregister = Declarations.unregister
Mixin = Declarations.Mixin


class OneInterface:
    pass


class TestCoreInterfaceMixin:

    @pytest.fixture(scope="class", autouse=True)
    def init_env(self, request):

        def revert():
            EnvironmentManager.set('current_blok', None)
            del RegistryManager.loaded_bloks['testMixin']

        request.addfinalizer(revert)
        RegistryManager.init_blok('testMixin')
        EnvironmentManager.set('current_blok', 'testMixin')

    @pytest.fixture(autouse=True)
    def init_blok(self):
        blokname = 'testMixin'
        RegistryManager.loaded_bloks[blokname]['Mixin'] = {
            'registry_names': []}

    def assertInMixin(self, *args):
        blokname = 'testMixin'
        blok = RegistryManager.loaded_bloks[blokname]
        assert len(blok['Mixin']['Mixin.MyMixin']['bases']) == len(args)
        for cls_ in args:
            has = cls_ in blok['Mixin']['Mixin.MyMixin']['bases']
            assert has is True

    def assertInRemoved(self, cls):
        core = RegistryManager.loaded_bloks['testMixin']['removed']
        if cls in core:
            return True

        self.fail('Not in removed')

    def test_add_interface(self):
        register(Mixin, cls_=OneInterface, name_='MyMixin')
        assert 'Mixin' == Mixin.MyMixin.__declaration_type__
        self.assertInMixin(OneInterface)
        dir(Declarations.Mixin.MyMixin)

    def test_add_interface_with_decorator(self):

        @register(Mixin)
        class MyMixin:
            pass

        assert 'Mixin' == Mixin.MyMixin.__declaration_type__
        self.assertInMixin(MyMixin)

    def test_add_two_interface(self):

        register(Mixin, cls_=OneInterface, name_="MyMixin")

        @register(Mixin)
        class MyMixin:
            pass

        self.assertInMixin(OneInterface, MyMixin)

    def test_remove_interface_with_1_cls_in_registry(self):

        register(Mixin, cls_=OneInterface, name_="MyMixin")
        self.assertInMixin(OneInterface)
        unregister(Mixin.MyMixin, OneInterface)

        blokname = 'testMixin'
        assert hasattr(Mixin, blokname) is False
        self.assertInMixin(OneInterface)
        self.assertInRemoved(OneInterface)

    def test_remove_interface_with_2_cls_in_registry(self):

        register(Mixin, cls_=OneInterface, name_="MyMixin")

        @register(Mixin)
        class MyMixin:
            pass

        self.assertInMixin(OneInterface, MyMixin)
        unregister(Mixin.MyMixin, OneInterface)
        self.assertInMixin(MyMixin, OneInterface)
        self.assertInRemoved(OneInterface)
