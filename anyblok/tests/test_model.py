# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase
from anyblok.registry import RegistryManager
from anyblok.environment import EnvironmentManager
from anyblok import Declarations
register = Declarations.register
unregister = Declarations.unregister
Model = Declarations.Model


class OneModel:
    __tablename__ = 'test'


class TestModel(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestModel, cls).setUpClass()
        RegistryManager.init_blok('testModel')
        EnvironmentManager.set('current_blok', 'testModel')

    @classmethod
    def tearDownClass(cls):
        super(TestModel, cls).tearDownClass()
        EnvironmentManager.set('current_blok', None)
        del RegistryManager.loaded_bloks['testModel']

    def setUp(self):
        super(TestModel, self).setUp()
        blokname = 'testModel'
        RegistryManager.loaded_bloks[blokname]['Model'] = {
            'registry_names': []}

    def assertInModel(self, *args):
        blokname = 'testModel'
        blok = RegistryManager.loaded_bloks[blokname]
        self.assertEqual(len(blok['Model']['Model.MyModel']['bases']),
                         len(args))
        for cls_ in args:
            has = cls_ in blok['Model']['Model.MyModel']['bases']
            self.assertEqual(has, True)

    def assertInRemoved(self, cls):
        core = RegistryManager.loaded_bloks['testModel']['removed']
        if cls in core:
            return True

        self.fail('Not in removed')

    def test_add_interface(self):
        register(Model, cls_=OneModel, name_='MyModel')
        self.assertEqual('Model', Model.MyModel.__declaration_type__)
        self.assertInModel(OneModel)
        dir(Declarations.Model.MyModel)

    def test_add_interface_with_decorator(self):

        @register(Model)
        class MyModel:
            pass

        self.assertEqual('Model', Model.MyModel.__declaration_type__)
        self.assertInModel(MyModel)

    def test_add_two_interface(self):

        register(Model, cls_=OneModel, name_="MyModel")

        @register(Model)
        class MyModel:
            pass

        self.assertInModel(OneModel, MyModel)

    def test_remove_interface_with_1_cls_in_registry(self):

        register(Model, cls_=OneModel, name_="MyModel")
        self.assertInModel(OneModel)
        unregister(Model.MyModel, OneModel)
        self.assertInModel(OneModel)
        self.assertInRemoved(OneModel)

    def test_remove_interface_with_2_cls_in_registry(self):

        register(Model, cls_=OneModel, name_="MyModel")

        @register(Model)
        class MyModel:
            pass

        self.assertInModel(OneModel, MyModel)
        unregister(Model.MyModel, OneModel)
        self.assertInModel(MyModel, OneModel)
        self.assertInRemoved(OneModel)
