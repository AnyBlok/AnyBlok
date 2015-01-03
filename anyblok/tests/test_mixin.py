# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase
from anyblok.registry import RegistryManager
from anyblok import Declarations
from anyblok.environment import EnvironmentManager
register = Declarations.register
unregister = Declarations.unregister
Mixin = Declarations.Mixin


class OneInterface:
    pass


class TestCoreInterfaceMixin(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestCoreInterfaceMixin, cls).setUpClass()
        RegistryManager.init_blok('testMixin')
        EnvironmentManager.set('current_blok', 'testMixin')

    @classmethod
    def tearDownClass(cls):
        super(TestCoreInterfaceMixin, cls).tearDownClass()
        EnvironmentManager.set('current_blok', None)
        del RegistryManager.loaded_bloks['testMixin']

    def setUp(self):
        super(TestCoreInterfaceMixin, self).setUp()
        blokname = 'testMixin'
        RegistryManager.loaded_bloks[blokname]['Mixin'] = {
            'registry_names': []}

    def assertInMixin(self, *args):
        blokname = 'testMixin'
        blok = RegistryManager.loaded_bloks[blokname]
        self.assertEqual(len(blok['Mixin']['Mixin.MyMixin']['bases']),
                         len(args))
        for cls_ in args:
            has = cls_ in blok['Mixin']['Mixin.MyMixin']['bases']
            self.assertEqual(has, True)

    def assertInRemoved(self, cls):
        core = RegistryManager.loaded_bloks['testMixin']['removed']
        if cls in core:
            return True

        self.fail('Not in removed')

    def test_add_interface(self):
        register(Mixin, cls_=OneInterface, name_='MyMixin')
        self.assertEqual('Mixin', Mixin.MyMixin.__declaration_type__)
        self.assertInMixin(OneInterface)
        dir(Declarations.Mixin.MyMixin)

    def test_add_interface_with_decorator(self):

        @register(Mixin)
        class MyMixin:
            pass

        self.assertEqual('Mixin', Mixin.MyMixin.__declaration_type__)
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
        self.assertEqual(hasattr(Mixin, blokname), False)
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
