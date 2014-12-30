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
target_registry = Declarations.target_registry
Model = Declarations.Model


def _complete_one2many(**kwargs):
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String
    One2Many = Declarations.RelationShip.One2Many

    primaryjoin = "address.id == person.address_id"

    @target_registry(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @target_registry(Model)
    class Person:

        name = String(primary_key=True)
        address_id = Integer(foreign_key=(Model.Address, 'id'))

    @target_registry(Model)  # noqa
    class Address:

        persons = One2Many(model=Model.Person,
                           remote_column="address_id",
                           primaryjoin=primaryjoin,
                           many2one="address")


def _minimum_one2many(**kwargs):
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String
    One2Many = Declarations.RelationShip.One2Many

    @target_registry(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @target_registry(Model)
    class Person:

        name = String(primary_key=True)
        address_id = Integer(foreign_key=(Model.Address, 'id'))

    @target_registry(Model)  # noqa
    class Address:

        persons = One2Many(model=Model.Person)


def _one2many_with_str_model(**kwargs):
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String
    One2Many = Declarations.RelationShip.One2Many

    @target_registry(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @target_registry(Model)
    class Person:

        name = String(primary_key=True)
        address_id = Integer(foreign_key=(Model.Address, 'id'))

    @target_registry(Model)  # noqa
    class Address:

        persons = One2Many(model='Model.Person')


def _autodetect_two_foreign_key(**kwargs):
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String
    One2Many = Declarations.RelationShip.One2Many

    @target_registry(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @target_registry(Model)
    class Person:

        name = String(primary_key=True)
        address_id = Integer(foreign_key=(Model.Address, 'id'))
        address2_id = Integer(foreign_key=(Model.Address, 'id'))

    @target_registry(Model)  # noqa
    class Address:

        persons = One2Many(model=Model.Person)


class TestOne2One(DBTestCase):

    def test_complete_one2one(self):
        registry = self.init_registry(_complete_one2many)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")
        address.persons.append(person)

        self.assertEqual(person.address, address)

    def test_minimum_one2one(self):
        registry = self.init_registry(_minimum_one2many)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")
        address.persons.append(person)

    def test_one2many_with_str_model(self):
        registry = self.init_registry(_one2many_with_str_model)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")
        address.persons.append(person)

    def test_autodetect_two_foreign_key(self):
        try:
            self.init_registry(_autodetect_two_foreign_key)
            self.fail('No watch dog to more than one foreign key')
        except FieldException:
            pass
