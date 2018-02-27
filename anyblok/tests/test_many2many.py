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
from anyblok.column import Integer, String, DateTime
from anyblok.relationship import Many2Many, Many2One
from anyblok.field import FieldException
from datetime import datetime

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

    def test_many2many_on_self(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                childs = Many2Many(
                    model='Model.Test',
                    m2m_remote_columns='id2',
                    many2many='parents'
                )

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert()
        t2 = registry.Test.insert()
        t1.childs.append(t2)
        self.assertIn(t1, t2.parents)

    def test_many2many_on_self_auto_column(self):

        def add_in_registry():

            @register(Model)
            class Test2:

                id = Integer(primary_key=True)
                childs = Many2Many(
                    model='Model.Test2',
                    many2many='parents'
                )

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test2.insert()
        t2 = registry.Test2.insert()
        t1.childs.append(t2)
        self.assertIn(t1, t2.parents)

    def test_many2many_on_multi_fk_miss_on_m2m_column(self):

        def add_in_registry():

            @register(Model)
            class Address:

                id = Integer(primary_key=True)
                street = String(primary_key=True)

            @register(Model)
            class Person:

                name = String(primary_key=True)
                addresses = Many2Many(
                    m2m_remote_columns=['test_id'],
                    model=Model.Address)

        with self.assertRaises(FieldException):
            self.init_registry(add_in_registry)

    def test_rich_many2many_complete_config(self):

        def add_in_registry():

            @register(Model)
            class Address:

                id = Integer(primary_key=True)
                street = String()
                zip = String()
                city = String()

            @register(Model)
            class PersonAddress:
                id = Integer(primary_key=True)
                a_id = Integer(
                    foreign_key=Model.Address.use('id'), nullable=False)
                p_name = String(
                    foreign_key='Model.Person=>name', nullable=False)
                create_at = DateTime(default=datetime.now)
                foo = String(default='bar')

            @register(Model)
            class Person:

                name = String(primary_key=True)
                addresses = Many2Many(model=Model.Address,
                                      join_table="personaddress",
                                      remote_columns="id", local_columns="name",
                                      m2m_remote_columns='a_id',
                                      m2m_local_columns='p_name',
                                      many2many="persons")

        registry = self.init_registry(add_in_registry)
        person = registry.Person.insert(name='jssuzanne')
        address = registry.Address.insert(
            street='somewhere', zip="75001", city="Paris")
        person.addresses.append(address)
        personaddress = registry.PersonAddress.query().one()
        self.assertEqual(personaddress.a_id, address.id)
        self.assertEqual(personaddress.p_name, person.name)
        self.assertTrue(personaddress.id)
        self.assertTrue(personaddress.create_at)
        self.assertEqual(personaddress.foo, 'bar')

    def test_rich_many2many_minimum_config(self):

        def add_in_registry():

            @register(Model)
            class Address:

                id = Integer(primary_key=True)
                street = String()
                zip = String()
                city = String()

            @register(Model)
            class PersonAddress:
                id = Integer(primary_key=True)
                a_id = Integer(
                    foreign_key=Model.Address.use('id'), nullable=False)
                p_name = String(
                    foreign_key='Model.Person=>name', nullable=False)
                create_at = DateTime(default=datetime.now)
                foo = String(default='bar')

            @register(Model)
            class Person:

                name = String(primary_key=True)
                addresses = Many2Many(model=Model.Address,
                                      join_table="personaddress",
                                      many2many="persons")

        registry = self.init_registry(add_in_registry)
        person = registry.Person.insert(name='jssuzanne')
        address = registry.Address.insert(
            street='somewhere', zip="75001", city="Paris")
        person.addresses.append(address)
        personaddress = registry.PersonAddress.query().one()
        self.assertEqual(personaddress.a_id, address.id)
        self.assertEqual(personaddress.p_name, person.name)
        self.assertTrue(personaddress.id)
        self.assertTrue(personaddress.create_at)
        self.assertEqual(personaddress.foo, 'bar')

    def test_rich_many2many_minimum_config_on_join_model(self):

        def add_in_registry():

            @register(Model)
            class Address:

                id = Integer(primary_key=True)
                street = String()
                zip = String()
                city = String()

            @register(Model)
            class PersonAddress:
                id = Integer(primary_key=True)
                a_id = Integer(
                    foreign_key=Model.Address.use('id'), nullable=False)
                p_name = String(
                    foreign_key='Model.Person=>name', nullable=False)
                create_at = DateTime(default=datetime.now)
                foo = String(default='bar')

            @register(Model)
            class Person:

                name = String(primary_key=True)
                addresses = Many2Many(model=Model.Address,
                                      join_model=Model.PersonAddress,
                                      many2many="persons")

        registry = self.init_registry(add_in_registry)
        person = registry.Person.insert(name='jssuzanne')
        address = registry.Address.insert(
            street='somewhere', zip="75001", city="Paris")
        person.addresses.append(address)
        personaddress = registry.PersonAddress.query().one()
        self.assertEqual(personaddress.a_id, address.id)
        self.assertEqual(personaddress.p_name, person.name)
        self.assertTrue(personaddress.id)
        self.assertTrue(personaddress.create_at)
        self.assertEqual(personaddress.foo, 'bar')

    def test_rich_many2many_minimum_config_with_many2one(self):

        def add_in_registry():

            @register(Model)
            class Address:

                id = Integer(primary_key=True)
                street = String()
                zip = String()
                city = String()

            @register(Model)
            class PersonAddress:
                id = Integer(primary_key=True)
                person = Many2One(
                    model='Model.Person', nullable=False,
                    foreign_key_options={'ondelete': 'cascade'})
                address = Many2One(
                    model=Model.Address, nullable=False,
                    foreign_key_options={'ondelete': 'cascade'})
                create_at = DateTime(default=datetime.now)
                foo = String(default='bar')

            @register(Model)
            class Person:

                name = String(primary_key=True)
                addresses = Many2Many(model=Model.Address,
                                      join_model=Model.PersonAddress,
                                      many2many="persons")

        registry = self.init_registry(add_in_registry)
        person = registry.Person.insert(name='jssuzanne')
        address = registry.Address.insert(
            street='somewhere', zip="75001", city="Paris")
        person.addresses.append(address)
        personaddress = registry.PersonAddress.query().one()
        self.assertEqual(personaddress.address_id, address.id)
        self.assertEqual(personaddress.person_name, person.name)
        self.assertTrue(personaddress.id)
        self.assertTrue(personaddress.create_at)
        self.assertEqual(personaddress.foo, 'bar')

    def test_rich_many2many_minimum_config_with_pk_many2one(self):

        def add_in_registry():

            @register(Model)
            class Address:

                id = Integer(primary_key=True)
                street = String()
                zip = String()
                city = String()

            @register(Model)
            class PersonAddress:
                person = Many2One(
                    model='Model.Person', nullable=False,
                    primary_key=True,
                    foreign_key_options={'ondelete': 'cascade'})
                address = Many2One(
                    model=Model.Address, nullable=False,
                    primary_key=True,
                    foreign_key_options={'ondelete': 'cascade'})
                create_at = DateTime(default=datetime.now)
                foo = String(default='bar')

            @register(Model)
            class Person:

                name = String(primary_key=True)
                addresses = Many2Many(model=Model.Address,
                                      join_model=Model.PersonAddress,
                                      many2many="persons")

        registry = self.init_registry(add_in_registry)
        person = registry.Person.insert(name='jssuzanne')
        address = registry.Address.insert(
            street='somewhere', zip="75001", city="Paris")
        person.addresses.append(address)
        personaddress = registry.PersonAddress.query().one()
        self.assertEqual(personaddress.address_id, address.id)
        self.assertEqual(personaddress.person_name, person.name)
        self.assertTrue(personaddress.create_at)
        self.assertEqual(personaddress.foo, 'bar')

    def test_rich_many2many_minimum_config_on_join_model_and_join_table_1(self):

        def add_in_registry():

            @register(Model)
            class Address:

                id = Integer(primary_key=True)
                street = String()
                zip = String()
                city = String()

            @register(Model)
            class PersonAddress:
                id = Integer(primary_key=True)
                a_id = Integer(
                    foreign_key=Model.Address.use('id'), nullable=False)
                p_name = String(
                    foreign_key='Model.Person=>name', nullable=False)
                create_at = DateTime(default=datetime.now)
                foo = String(default='bar')

            @register(Model)
            class Person:

                name = String(primary_key=True)
                addresses = Many2Many(model=Model.Address,
                                      join_model=Model.PersonAddress,
                                      many2many="persons")

        registry = self.init_registry(add_in_registry)
        person = registry.Person.insert(name='jssuzanne')
        address = registry.Address.insert(
            street='somewhere', zip="75001", city="Paris")
        person.addresses.append(address)
        personaddress = registry.PersonAddress.query().one()
        self.assertEqual(personaddress.a_id, address.id)
        self.assertEqual(personaddress.p_name, person.name)
        self.assertTrue(personaddress.id)
        self.assertTrue(personaddress.create_at)
        self.assertEqual(personaddress.foo, 'bar')

    def test_rich_many2many_minimum_config_on_join_model_and_join_table_2(self):

        def add_in_registry():

            @register(Model)
            class Address:

                id = Integer(primary_key=True)
                street = String()
                zip = String()
                city = String()

            @register(Model)
            class PersonAddress:
                id = Integer(primary_key=True)
                a_id = Integer(
                    foreign_key=Model.Address.use('id'), nullable=False)
                p_name = String(
                    foreign_key='Model.Person=>name', nullable=False)
                create_at = DateTime(default=datetime.now)
                foo = String(default='bar')

            @register(Model)
            class Person:

                name = String(primary_key=True)
                addresses = Many2Many(model=Model.Address,
                                      join_table="other_join_table",
                                      join_model=Model.PersonAddress,
                                      many2many="persons")

        with self.assertRaises(FieldException):
            self.init_registry(add_in_registry)

    def test_rich_many2many_complete_config_on_self(self):

        def add_in_registry():

            @register(Model)
            class TestLink:
                id = Integer(primary_key=True)
                t_left = Integer(foreign_key='Model.Test=>id', nullable=False)
                t_right = Integer(foreign_key='Model.Test=>id', nullable=False)
                create_at = DateTime(default=datetime.now)
                foo = String(default='bar')

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                childs = Many2Many(
                    model='Model.Test',
                    many2many='parents',
                    join_table="testlink",
                    remote_columns="id", local_columns="id",
                    m2m_local_columns='t_left',
                    m2m_remote_columns='t_right',
                )

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert()
        t2 = registry.Test.insert()
        t1.parents.append(t2)
        link = registry.TestLink.query().one()
        self.assertEqual(link.t_left, t2.id)
        self.assertEqual(link.t_right, t1.id)
        self.assertTrue(link.id)
        self.assertTrue(link.create_at)
        self.assertEqual(link.foo, 'bar')

    def test_rich_many2many_minimum_config_on_self(self):

        def add_in_registry():

            @register(Model)
            class TestLink:
                id = Integer(primary_key=True)
                t_left = Integer(foreign_key='Model.Test=>id', nullable=False)
                t_right = Integer(foreign_key='Model.Test=>id', nullable=False)
                create_at = DateTime(default=datetime.now)
                foo = String(default='bar')

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                childs = Many2Many(
                    model='Model.Test',
                    many2many='parents',
                    join_table="testlink",
                    m2m_local_columns='t_left',
                    m2m_remote_columns='t_right',
                )

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert()
        t2 = registry.Test.insert()
        t1.parents.append(t2)
        link = registry.TestLink.query().one()
        self.assertEqual(link.t_left, t2.id)
        self.assertEqual(link.t_right, t1.id)
        self.assertTrue(link.id)
        self.assertTrue(link.create_at)
        self.assertEqual(link.foo, 'bar')

    def test_rich_many2many_minimum_config_on_self_without_columns_1(self):

        def add_in_registry():

            @register(Model)
            class TestLink:
                id = Integer(primary_key=True)
                t_left = Integer(foreign_key='Model.Test=>id', nullable=False)
                t_right = Integer(foreign_key='Model.Test=>id', nullable=False)
                create_at = DateTime(default=datetime.now)
                foo = String(default='bar')

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                childs = Many2Many(
                    model='Model.Test',
                    many2many='parents',
                    join_table="testlink",
                    m2m_local_columns='t_left',
                )

        with self.assertRaises(FieldException):
            self.init_registry(add_in_registry)

    def test_rich_many2many_minimum_config_on_self_without_columns_2(self):

        def add_in_registry():

            @register(Model)
            class TestLink:
                id = Integer(primary_key=True)
                t_left = Integer(foreign_key='Model.Test=>id', nullable=False)
                t_right = Integer(foreign_key='Model.Test=>id', nullable=False)
                create_at = DateTime(default=datetime.now)
                foo = String(default='bar')

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                childs = Many2Many(
                    model='Model.Test',
                    many2many='parents',
                    join_table="testlink",
                    m2m_remote_columns='t_right',
                )

        with self.assertRaises(FieldException):
            self.init_registry(add_in_registry)

    def test_rich_many2many_minimum_config_on_self_with_join_model(self):

        def add_in_registry():

            @register(Model)
            class TestLink:
                id = Integer(primary_key=True)
                t_left = Integer(foreign_key='Model.Test=>id', nullable=False)
                t_right = Integer(foreign_key='Model.Test=>id', nullable=False)
                create_at = DateTime(default=datetime.now)
                foo = String(default='bar')

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                childs = Many2Many(
                    model='Model.Test',
                    many2many='parents',
                    join_model=Model.TestLink,
                    m2m_local_columns='t_left',
                    m2m_remote_columns='t_right',
                )

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert()
        t2 = registry.Test.insert()
        t1.parents.append(t2)
        link = registry.TestLink.query().one()
        self.assertEqual(link.t_left, t2.id)
        self.assertEqual(link.t_right, t1.id)
        self.assertTrue(link.id)
        self.assertTrue(link.create_at)
        self.assertEqual(link.foo, 'bar')

    def test_rich_many2many_minimum_config_on_self_with_many2one(self):

        def add_in_registry():

            @register(Model)
            class TestLink:
                id = Integer(primary_key=True)
                left = Many2One(
                    model='Model.Test', nullable=False,
                    foreign_key_options={'ondelete': 'cascade'})
                right = Many2One(
                    model='Model.Test', nullable=False,
                    foreign_key_options={'ondelete': 'cascade'})
                create_at = DateTime(default=datetime.now)
                foo = String(default='bar')

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                childs = Many2Many(
                    model='Model.Test',
                    many2many='parents',
                    join_model=Model.TestLink,
                    m2m_local_columns='left_id',
                    m2m_remote_columns='right_id',
                )

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert()
        t2 = registry.Test.insert()
        t1.parents.append(t2)
        link = registry.TestLink.query().one()
        self.assertEqual(link.left_id, t2.id)
        self.assertEqual(link.right_id, t1.id)
        self.assertTrue(link.id)
        self.assertTrue(link.create_at)
        self.assertEqual(link.foo, 'bar')

    def test_rich_many2many_minimum_config_on_self_with_pk_many2one_2(self):

        def add_in_registry():

            @register(Model)
            class TestLink:
                left = Many2One(
                    model='Model.Test', nullable=False,
                    primary_key=True,
                    foreign_key_options={'ondelete': 'cascade'})
                right = Many2One(
                    model='Model.Test', nullable=False,
                    primary_key=True,
                    foreign_key_options={'ondelete': 'cascade'})
                create_at = DateTime(default=datetime.now)
                foo = String(default='bar')

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                childs = Many2Many(
                    model='Model.Test',
                    many2many='parents',
                    join_model=Model.TestLink,
                    m2m_local_columns='left',
                    m2m_remote_columns='right',
                )

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert()
        t2 = registry.Test.insert()
        t1.parents.append(t2)
        link = registry.TestLink.query().one()
        self.assertEqual(link.left_id, t2.id)
        self.assertEqual(link.right_id, t1.id)
        self.assertTrue(link.create_at)
        self.assertEqual(link.foo, 'bar')
