# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import DBTestCase
from anyblok import Declarations
FieldException = Declarations.Exception.FieldException
register = Declarations.register
Model = Declarations.Model


def _complete_many2many(**kwargs):
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String
    Many2Many = Declarations.RelationShip.Many2Many

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2Many(model=Model.Address,
                            join_table="join_addresses_by_persons",
                            remote_column="id", local_column="name",
                            m2m_remote_column='a_id',
                            m2m_local_column='p_name',
                            many2many="persons")


def _minimum_many2many(**kwargs):
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String
    Many2Many = Declarations.RelationShip.Many2Many

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2Many(model=Model.Address)


def _many2many_with_str_model(**kwargs):
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String
    Many2Many = Declarations.RelationShip.Many2Many

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2Many(model='Model.Address')


def auto_detect_two_primary_keys(**kwargs):
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String
    Many2Many = Declarations.RelationShip.Many2Many

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        id2 = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2Many(model=Model.Address)


def unexisting_remote_column(**kwargs):
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String
    Many2Many = Declarations.RelationShip.Many2Many

    @register(Model)
    class Address:

        id = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2Many(model=Model.Address, remote_column="id2")


def reuse_many2many_table(**kwargs):
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String
    Many2Many = Declarations.RelationShip.Many2Many

    @register(Model)
    class Address:

        id = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2Many(model=Model.Address)

    @register(Model)  # noqa
    class Address:

        id = Integer(primary_key=True)
        persons = Many2Many(model=Model.Person,
                            join_table='join_person_and_address')


class TestMany2Many(DBTestCase):

    def test_complete_many2many(self):
        registry = self.init_registry(_complete_many2many)

        address_exist = hasattr(registry.Person, 'address')
        self.assertEqual(address_exist, True)

        m2m_tables_exist = hasattr(registry, 'many2many_tables')
        self.assertEqual(m2m_tables_exist, True)

        jt = registry.declarativebase.metadata.tables
        join_table_exist = 'join_addresses_by_persons' in jt
        self.assertEqual(join_table_exist, True)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")

        person.address.append(address)

        self.assertEqual(address.persons, [person])

    def test_minimum_many2many(self):
        registry = self.init_registry(_minimum_many2many)

        address_exist = hasattr(registry.Person, 'address')
        self.assertEqual(address_exist, True)

        m2m_tables_exist = hasattr(registry, 'many2many_tables')
        self.assertEqual(m2m_tables_exist, True)

        jt = registry.declarativebase.metadata.tables
        join_table_exist = 'join_person_and_address' in jt
        self.assertEqual(join_table_exist, True)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")

        person.address.append(address)

        self.assertEqual(person.address, [address])

    def test_many2many_with_str_model(self):
        registry = self.init_registry(_many2many_with_str_model)

        address_exist = hasattr(registry.Person, 'address')
        self.assertEqual(address_exist, True)

        m2m_tables_exist = hasattr(registry, 'many2many_tables')
        self.assertEqual(m2m_tables_exist, True)

        jt = registry.declarativebase.metadata.tables
        join_table_exist = 'join_person_and_address' in jt
        self.assertEqual(join_table_exist, True)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")

        person.address.append(address)

        self.assertEqual(person.address, [address])

    def test_auto_detect_two_primary_keys(self):
        try:
            self.init_registry(auto_detect_two_primary_keys)
            self.fail('No watch dog when two primary key')
        except FieldException:
            pass

    def test_unexisting_remote_column(self):
        try:
            self.init_registry(unexisting_remote_column)
            self.fail(
                "No watch dog when the remote or local column doesn't exist")
        except FieldException:
            pass

    def test_reuse_many2many_table(self):
        registry = self.init_registry(reuse_many2many_table)

        address = registry.Address.insert()
        person = registry.Person.insert(name="Jean-sébastien SUZANNE")

        person.address.append(address)

        self.assertEqual(address.persons, [person])
