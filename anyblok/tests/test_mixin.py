# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase, DBTestCase
from anyblok.registry import RegistryManager
from anyblok import Declarations
from anyblok.environment import EnvironmentManager
from anyblok.column import Integer, String, Boolean
from anyblok.bloks.anyblok_core.exceptions import (
    ForbidDeleteException, ForbidUpdateException
)
register = Declarations.register
unregister = Declarations.unregister
Mixin = Declarations.Mixin
Model = Declarations.Model


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


class TestGivenMixin(DBTestCase):

    def test_forbidden_delete(self):

        def add_in_registry():

            @register(Model)
            class Test(Mixin.ForbidDelete):

                id = Integer(primary_key=True)

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert()
        with self.assertRaises(ForbidDeleteException):
            t.delete()

    def test_forbidden_update(self):

        def add_in_registry():

            @register(Model)
            class Test(Mixin.ForbidUpdate):

                id = Integer(primary_key=True)
                name = String()

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert()
        t.name = 'test'
        with self.assertRaises(ForbidUpdateException):
            registry.flush()

    def test_readonly_delete(self):

        def add_in_registry():

            @register(Model)
            class Test(Mixin.ReadOnly):

                id = Integer(primary_key=True)

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert()
        with self.assertRaises(ForbidDeleteException):
            t.delete()

    def test_readonly_update(self):

        def add_in_registry():

            @register(Model)
            class Test(Mixin.ReadOnly):

                id = Integer(primary_key=True)
                name = String()

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert()
        t.name = 'test'
        with self.assertRaises(ForbidUpdateException):
            registry.flush()

    def test_conditional_forbidden_delete(self):

        def add_in_registry():

            @register(Model)
            class Test(Mixin.ConditionalForbidDelete):

                id = Integer(primary_key=True)
                forbid_delete = Boolean(default=False)

                def check_if_forbid_delete_condition_is_true(self):
                    return self.forbid_delete

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert()
        t2 = registry.Test.insert(forbid_delete=True)
        t1.delete()

        with self.assertRaises(ForbidDeleteException):
            t2.delete()

    def test_conditional_forbidden_delete_mission_method(self):

        def add_in_registry():

            @register(Model)
            class Test(Mixin.ConditionalForbidDelete):

                id = Integer(primary_key=True)

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert()
        with self.assertRaises(ForbidDeleteException):
            t.delete()

    def test_conditional_forbidden_update_missing_method(self):

        def add_in_registry():

            @register(Model)
            class Test(Mixin.ConditionalForbidUpdate):

                id = Integer(primary_key=True)
                name = String()

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert()
        t.name = 'test'
        with self.assertRaises(ForbidUpdateException):
            registry.flush()

    def test_conditional_forbidden_update(self):

        def add_in_registry():

            @register(Model)
            class Test(Mixin.ConditionalForbidUpdate):

                id = Integer(primary_key=True)
                forbid_update = Boolean(default=False)
                name = String()

                def check_if_forbid_update_condition_is_true(self, **changed):
                    return self.forbid_update

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert()
        t1.name = 'test'
        registry.flush()
        t2 = registry.Test.insert(forbid_update=True)
        t2.name = 'test'
        with self.assertRaises(ForbidUpdateException):
            registry.flush()

    def add_in_registry_conditional_readonly(self):

        @register(Model)
        class Test(Mixin.ConditionalReadOnly):

            id = Integer(primary_key=True)
            readonly = Boolean(default=False)
            name = String()

            def check_if_forbid_update_condition_is_true(self,
                                                         **previous_values):
                return previous_values.get('readonly', self.readonly)

            def check_if_forbid_delete_condition_is_true(self):
                return self.readonly

    def test_conditional_readonly_delete(self):
        registry = self.init_registry(self.add_in_registry_conditional_readonly)
        t1 = registry.Test.insert()
        t1.delete()
        t2 = registry.Test.insert(readonly=True)
        with self.assertRaises(ForbidDeleteException):
            t2.delete()

    def test_conditional_readonly_update(self):
        registry = self.init_registry(self.add_in_registry_conditional_readonly)
        t1 = registry.Test.insert()
        t1.name = 'test'
        registry.flush()
        t2 = registry.Test.insert(readonly=True)
        t2.name = 'test'
        with self.assertRaises(ForbidUpdateException):
            registry.flush()

    def test_boolean_forbidden_delete(self):

        def add_in_registry():

            @register(Model)
            class Test(Mixin.BooleanForbidDelete):

                id = Integer(primary_key=True)

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert()
        t2 = registry.Test.insert(forbid_delete=True)
        t1.delete()

        with self.assertRaises(ForbidDeleteException):
            t2.delete()

    def test_boolean_forbidden_update(self):

        def add_in_registry():

            @register(Model)
            class Test(Mixin.BooleanForbidUpdate):

                id = Integer(primary_key=True)
                name = String()

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert()
        t1.name = 'test'
        registry.flush()
        t2 = registry.Test.insert(forbid_update=True)
        t2.name = 'test'
        with self.assertRaises(ForbidUpdateException):
            registry.flush()

    def add_in_registry_boolean_readonly(self):

        @register(Model)
        class Test(Mixin.BooleanReadOnly):

            id = Integer(primary_key=True)
            name = String()

    def test_boolean_readonly_delete(self):
        registry = self.init_registry(self.add_in_registry_boolean_readonly)
        t1 = registry.Test.insert()
        t1.delete()
        t2 = registry.Test.insert(readonly=True)
        with self.assertRaises(ForbidDeleteException):
            t2.delete()

    def test_boolean_readonly_update(self):
        registry = self.init_registry(self.add_in_registry_boolean_readonly)
        t1 = registry.Test.insert()
        t1.name = 'test'
        registry.flush()
        t2 = registry.Test.insert(readonly=True)
        t2.name = 'test'
        with self.assertRaises(ForbidUpdateException):
            registry.flush()

    def add_in_registry_state_readonly(self):

        @register(Model)
        class Test(Mixin.StateReadOnly):
            DEFAULT_STATE = 'draft'

            @classmethod
            def get_states(cls):
                return {
                    'draft': 'Draft',
                    'started': 'Started',
                    'done': 'Done',
                }

            def check_if_forbid_update_condition_is_true(self, **changed):
                if 'state' in changed:
                    return False

                return self.state == 'done'

            def check_if_forbid_delete_condition_is_true(self):
                return self.state != 'draft'

            id = Integer(primary_key=True)
            name = String()

    def test_state_readonly_delete_1(self):
        registry = self.init_registry(self.add_in_registry_state_readonly)
        t = registry.Test.insert()
        t.delete()

    def test_state_readonly_delete_2(self):
        registry = self.init_registry(self.add_in_registry_state_readonly)
        t = registry.Test.insert(state='started')
        with self.assertRaises(ForbidDeleteException):
            t.delete()

    def test_state_readonly_delete_3(self):
        registry = self.init_registry(self.add_in_registry_state_readonly)
        t = registry.Test.insert(state='done')
        with self.assertRaises(ForbidDeleteException):
            t.delete()

    def test_state_readonly_update_1(self):
        registry = self.init_registry(self.add_in_registry_state_readonly)
        t1 = registry.Test.insert()
        t1.name = 'test'
        registry.flush()

    def test_state_readonly_update_2(self):
        registry = self.init_registry(self.add_in_registry_state_readonly)
        t = registry.Test.insert(state='done')
        t.name = 'test'
        with self.assertRaises(ForbidUpdateException):
            registry.flush()

    def test_state_readonly_update_3(self):
        registry = self.init_registry(self.add_in_registry_state_readonly)
        t = registry.Test.insert()
        t.name = 'test1'
        t.state = 'started'
        registry.flush()
        t.name = 'test2'
        t.state = 'done'
        registry.flush()
        t.name = 'test3'
        with self.assertRaises(ForbidUpdateException):
            registry.flush()
