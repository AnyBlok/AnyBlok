# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase, DBTestCase
from anyblok.field import FieldException
from anyblok.relationship import RelationShip, RelationShipList
from anyblok import Declarations
from anyblok.column import Integer
from anyblok.relationship import One2Many, Many2One


register = Declarations.register
Model = Declarations.Model


class OneRelationShip(RelationShip):
    pass


class OneModel:
    __tablename__ = 'test'
    __registry_name__ = 'One.Model'


class MockRegistry:

    InstrumentedList = []


class TestRelationShip(TestCase):

    def test_forbid_instance(self):
        try:
            RelationShip(model=OneModel)
            self.fail("RelationShip mustn't be instanciated")
        except FieldException:
            pass

    def test_must_have_a_model(self):
        OneRelationShip(model=OneModel)
        try:
            OneRelationShip()
            self.fail("No watchdog, the model must be required")
        except FieldException:
            pass


class TestRelationShipList(TestCase):

    @classmethod
    def setupClass(cls):
        cls.List = type(
            'List', (RelationShipList, list),
            {
                'relationship_field_append_value': lambda *a, **kw: True,
                'relationship_field_remove_value': lambda *a, **kw: True,
            })

    def setUp(self):
        self.list = self.List()

    def test_append(self):
        self.assertEqual(self.list, [])
        self.list.append(1)
        self.assertEqual(self.list, [1])

    def test_extend(self):
        self.assertEqual(self.list, [])
        self.list.extend([1, 2])
        self.assertEqual(self.list, [1, 2])

    def test_insert(self):
        self.assertEqual(self.list, [])
        self.list.insert(0, 1)
        self.assertEqual(self.list, [1])
        self.list.insert(0, 2)
        self.assertEqual(self.list, [2, 1])

    def test_pop(self):
        self.list.extend([1, 2])
        self.assertEqual(self.list, [1, 2])
        self.list.pop(0)
        self.assertEqual(self.list, [2])
        self.list.pop(0)
        self.assertEqual(self.list, [])

    def test_remove(self):
        self.list.extend([3, 2, 1])
        self.assertEqual(self.list, [3, 2, 1])
        self.list.remove(1)
        self.assertEqual(self.list, [3, 2])

    def test_clear(self):
        self.list.extend([3, 2, 1])
        self.assertEqual(self.list, [3, 2, 1])
        self.list.clear()
        self.assertEqual(self.list, [])


class TestComplexeRelationShipCase(DBTestCase):

    def test_with_multi_parallel_foreign_key_with_definition(self):

        def add_in_registry():

            @register(Model)
            class Address:

                id = Integer(primary_key=True)

            @register(Model)
            class Person:

                id = Integer(primary_key=True)
                address_1_id = Integer(foreign_key=Model.Address.use('id'))
                address_2_id = Integer(foreign_key=Model.Address.use('id'))
                address_1 = Many2One(model=Model.Address,
                                     column_names=['address_1_id'])
                address_2 = Many2One(model=Model.Address,
                                     column_names=['address_2_id'])

            @register(Model)  # noqa
            class Address:

                persons = One2Many(model=Model.Person)

        registry = self.init_registry(add_in_registry)
        address_1 = registry.Address.insert()
        address_2 = registry.Address.insert()
        person = registry.Person.insert(
            address_1=address_1, address_2=address_2)
        self.assertEqual(address_1.persons, [person])
        self.assertEqual(address_2.persons, [person])

    def test_with_multi_parallel_foreign_key_auto_detect(self):

        def add_in_registry():

            @register(Model)
            class Address:

                id = Integer(primary_key=True)
                persons = One2Many(model='Model.Person')

            @register(Model)
            class Person:

                id = Integer(primary_key=True)
                address_1 = Many2One(model=Model.Address)
                address_2 = Many2One(model=Model.Address)

        registry = self.init_registry(add_in_registry)
        address_1 = registry.Address.insert()
        address_2 = registry.Address.insert()
        person = registry.Person.insert(
            address_1=address_1, address_2=address_2)
        self.assertEqual(address_1.persons, [person])
        self.assertEqual(address_2.persons, [person])
