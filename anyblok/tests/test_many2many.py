# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Pierre Verkest <pverkest@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import DBTestCase
from anyblok import Declarations
from anyblok.mapper import ModelAttributeException
from anyblok.column import Integer, String
from anyblok.relationship import Many2Many

register = Declarations.register
Model = Declarations.Model
Mixin = Declarations.Mixin


def _complete_many2many(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:

        name = String(primary_key=True)
        addresses = Many2Many(model=Model.Address,
                              join_table="join_addresses_by_persons",
                              remote_columns="id", local_columns="name",
                              m2m_remote_columns='a_id',
                              m2m_local_columns='p_name',
                              many2many="persons")


def _minimum_many2many(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:

        name = String(primary_key=True)
        addresses = Many2Many(model=Model.Address)


def _minimum_many2many_by_mixin(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Mixin)
    class MixinM2M:
        addresses = Many2Many(model=Model.Address)

    @register(Model)
    class Person(Mixin.MixinM2M):

        name = String(primary_key=True)


def _many2many_with_str_model(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:

        name = String(primary_key=True)
        addresses = Many2Many(model='Model.Address')


def auto_detect_two_primary_keys(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        id2 = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        addresses = Many2Many(model=Model.Address)


def unexisting_remote_columns(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        addresses = Many2Many(model=Model.Address, remote_columns="id2")


def reuse_many2many_table(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        addresses = Many2Many(model=Model.Address)

    @register(Model)  # noqa
    class Address:

        id = Integer(primary_key=True)
        persons = Many2Many(model=Model.Person,
                            join_table='join_person_and_address')


class TestMany2Many(DBTestCase):

    def test_complete_many2many(self):
        registry = self.init_registry(_complete_many2many)

        address_exist = hasattr(registry.Person, 'addresses')
        self.assertTrue(address_exist)

        m2m_tables_exist = hasattr(registry, 'many2many_tables')
        self.assertTrue(m2m_tables_exist)

        jt = registry.declarativebase.metadata.tables
        join_table_exist = 'join_addresses_by_persons' in jt
        self.assertEqual(join_table_exist, True)

        self.assertEqual(
            len(jt['join_addresses_by_persons'].primary_key.columns),
            2)
        self.assertTrue('a_id' in jt[
            'join_addresses_by_persons'].primary_key.columns)
        self.assertTrue('p_name' in jt[
            'join_addresses_by_persons'].primary_key.columns)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")

        person.addresses.append(address)

        self.assertEqual(address.persons, [person])

    def test_complete_many2many_expire_field(self):
        registry = self.init_registry(_complete_many2many)
        self.assertIn(
            ('x2m', 'addresses', 'persons'),
            registry.expire_attributes['Model.Person']['addresses'])
        self.assertIn(
            ('x2m', 'persons', 'addresses'),
            registry.expire_attributes['Model.Address']['persons'])

    def test_minimum_many2many(self):
        registry = self.init_registry(_minimum_many2many)

        address_exist = hasattr(registry.Person, 'addresses')
        self.assertTrue(address_exist)

        m2m_tables_exist = hasattr(registry, 'many2many_tables')
        self.assertTrue(m2m_tables_exist)

        jt = registry.declarativebase.metadata.tables
        join_table_exist = 'join_person_and_address' in jt
        self.assertEqual(join_table_exist, True)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")

        person.addresses.append(address)

        self.assertEqual(person.addresses, [address])

    def test_many2many_with_str_model(self):
        registry = self.init_registry(_many2many_with_str_model)

        address_exist = hasattr(registry.Person, 'addresses')
        self.assertTrue(address_exist)

        m2m_tables_exist = hasattr(registry, 'many2many_tables')
        self.assertTrue(m2m_tables_exist)

        jt = registry.declarativebase.metadata.tables
        join_table_exist = 'join_person_and_address' in jt
        self.assertEqual(join_table_exist, True)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")

        person.addresses.append(address)

        self.assertEqual(person.addresses, [address])

    def test_unexisting_remote_columns(self):
        with self.assertRaises(ModelAttributeException):
            self.init_registry(unexisting_remote_columns)

    def test_reuse_many2many_table(self):
        registry = self.init_registry(reuse_many2many_table)

        address = registry.Address.insert()
        person = registry.Person.insert(name="Jean-sébastien SUZANNE")

        person.addresses.append(address)

        self.assertEqual(address.persons, [person])

    def test_declared_in_mixin(self):
        registry = self.init_registry(_minimum_many2many_by_mixin)

        address_exist = hasattr(registry.Person, 'addresses')
        self.assertTrue(address_exist)

        m2m_tables_exist = hasattr(registry, 'many2many_tables')
        self.assertTrue(m2m_tables_exist)

        jt = registry.declarativebase.metadata.tables
        join_table_exist = 'join_person_and_address' in jt
        self.assertEqual(join_table_exist, True)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")

        person.addresses.append(address)

        self.assertEqual(person.addresses, [address])

    def test_declared_in_mixin_inherit_by_two_models(self):
        def add_in_registry():
            _minimum_many2many_by_mixin()

            @register(Model)
            class Person2(Mixin.MixinM2M):

                name = String(primary_key=True)

        registry = self.init_registry(add_in_registry)

        address_exist = hasattr(registry.Person, 'addresses')
        self.assertTrue(address_exist)
        address_exist = hasattr(registry.Person2, 'addresses')
        self.assertTrue(address_exist)

        m2m_tables_exist = hasattr(registry, 'many2many_tables')
        self.assertTrue(m2m_tables_exist)

        jt = registry.declarativebase.metadata.tables
        join_table_exist = 'join_person_and_address' in jt
        self.assertEqual(join_table_exist, True)
        join_table_exist = 'join_person2_and_address' in jt
        self.assertEqual(join_table_exist, True)

    def test_comlet_with_multi_primary_keys_remote_and_local(self):

        def add_in_registry():

            @register(Model)
            class Test:
                id = Integer(primary_key=True)
                id2 = String(primary_key=True)

            @register(Model)
            class Test2:
                id = Integer(primary_key=True)
                id2 = String(primary_key=True)
                test = Many2Many(model=Model.Test,
                                 join_table="join_test_and_test2",
                                 remote_columns=['id', 'id2'],
                                 m2m_remote_columns=['t2_id', 't2_id2'],
                                 local_columns=['id', 'id2'],
                                 m2m_local_columns=['t1_id', 't1_id2'],
                                 many2many="test2")

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert(id2="test1")
        t2 = registry.Test2.insert(id2="test2")
        t2.test.append(t1)
        self.assertIs(t1.test2[0], t2)

        jt = registry.declarativebase.metadata.tables
        self.assertEqual(
            len(jt['join_test_and_test2'].primary_key.columns),
            4)
        self.assertTrue('t1_id' in jt[
            'join_test_and_test2'].primary_key.columns)
        self.assertTrue('t1_id2' in jt[
            'join_test_and_test2'].primary_key.columns)
        self.assertTrue('t2_id' in jt[
            'join_test_and_test2'].primary_key.columns)
        self.assertTrue('t2_id2' in jt[
            'join_test_and_test2'].primary_key.columns)

    def test_comlet_with_multi_primary_keys_remote(self):

        def add_in_registry():

            @register(Model)
            class Test:
                id = Integer(primary_key=True)
                id2 = String(primary_key=True)

            @register(Model)
            class Test2:
                id = Integer(primary_key=True)
                test = Many2Many(model=Model.Test,
                                 join_table="join_test_and_test2",
                                 remote_columns=['id', 'id2'],
                                 m2m_remote_columns=['t2_id', 't2_id2'],
                                 local_columns='id',
                                 m2m_local_columns='t1_id',
                                 many2many="test2")

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert(id2="test1")
        t2 = registry.Test2.insert()
        t2.test.append(t1)
        self.assertIs(t1.test2[0], t2)

    def test_comlet_with_multi_primary_keys_local(self):

        def add_in_registry():

            @register(Model)
            class Test:
                id = Integer(primary_key=True)

            @register(Model)
            class Test2:
                id = Integer(primary_key=True)
                id2 = String(primary_key=True)
                test = Many2Many(model=Model.Test,
                                 join_table="join_test_and_test2",
                                 remote_columns='id',
                                 m2m_remote_columns='t2_id',
                                 local_columns=['id', 'id2'],
                                 m2m_local_columns=['t1_id', 't1_id2'],
                                 many2many="test2")

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert()
        t2 = registry.Test2.insert(id2='test2')
        t2.test.append(t1)
        self.assertIs(t1.test2[0], t2)

    def test_minimum_with_multi_primary_keys_remote_and_local(self):

        def add_in_registry():

            @register(Model)
            class Test:
                id = Integer(primary_key=True)
                id2 = String(primary_key=True)

            @register(Model)
            class Test2:
                id = Integer(primary_key=True)
                id2 = String(primary_key=True)
                test = Many2Many(model=Model.Test, many2many="test2")

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert(id2="test1")
        t2 = registry.Test2.insert(id2="test2")
        t2.test.append(t1)
        self.assertIs(t1.test2[0], t2)

    def test_minimum_with_multi_primary_keys_remote(self):

        def add_in_registry():

            @register(Model)
            class Test:
                id = Integer(primary_key=True)
                id2 = String(primary_key=True)

            @register(Model)
            class Test2:
                id = Integer(primary_key=True)
                test = Many2Many(model=Model.Test, many2many="test2")

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert(id2="test1")
        t2 = registry.Test2.insert()
        t2.test.append(t1)
        self.assertIs(t1.test2[0], t2)

    def test_minimum_with_multi_primary_keys_local(self):

        def add_in_registry():

            @register(Model)
            class Test:
                id = Integer(primary_key=True)

            @register(Model)
            class Test2:
                id = Integer(primary_key=True)
                id2 = String(primary_key=True)
                test = Many2Many(model=Model.Test, many2many="test2")

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert()
        t2 = registry.Test2.insert(id2="test2")
        t2.test.append(t1)
        self.assertIs(t1.test2[0], t2)
