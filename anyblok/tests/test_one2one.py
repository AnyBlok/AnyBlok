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


def _complete_one2one(**kwargs):
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String
    One2One = Declarations.RelationShip.One2One

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = One2One(model=Model.Address,
                          remote_column="id", column_name="id_of_address",
                          backref="person", nullable=False)


def _minimum_one2one(**kwargs):
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String
    One2One = Declarations.RelationShip.One2One

    @register(Model)
    class Address:

        id = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = One2One(model=Model.Address, backref="person")


def _one2one_with_str_method(**kwargs):
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String
    One2One = Declarations.RelationShip.One2One

    @register(Model)
    class Address:

        id = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = One2One(model="Model.Address", backref="person")


def _minimum_one2one_without_backref(**kwargs):
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String
    One2One = Declarations.RelationShip.One2One

    @register(Model)
    class Address:

        id = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = One2One(model=Model.Address)


def _minimum_one2one_with_one2many(**kwargs):
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String
    One2One = Declarations.RelationShip.One2One

    @register(Model)
    class Address:

        id = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = One2One(model=Model.Address,
                          backref="person", one2many="persons")


class TestOne2One(DBTestCase):

    def test_complete_one2one(self):
        registry = self.init_registry(_complete_one2one)

        address_exist = hasattr(registry.Person, 'address')
        self.assertEqual(address_exist, True)

        id_of_address_exist = hasattr(registry.Person, 'id_of_address')
        self.assertEqual(id_of_address_exist, True)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(
            name="Jean-sébastien SUZANNE", address=address)

        self.assertEqual(address.person, person)

    def test_minimum_one2one(self):
        registry = self.init_registry(_minimum_one2one)

        address_exist = hasattr(registry.Person, 'address')
        self.assertEqual(address_exist, True)

        address_id_exist = hasattr(registry.Person, 'address_id')
        self.assertEqual(address_id_exist, True)

        address = registry.Address.insert()

        person = registry.Person.insert(
            name="Jean-sébastien SUZANNE", address=address)

        self.assertEqual(address.person, person)

    def test_one2one_with_str_model(self):
        registry = self.init_registry(_one2one_with_str_method)

        address_exist = hasattr(registry.Person, 'address')
        self.assertEqual(address_exist, True)

        address_id_exist = hasattr(registry.Person, 'address_id')
        self.assertEqual(address_id_exist, True)

        address = registry.Address.insert()

        person = registry.Person.insert(
            name="Jean-sébastien SUZANNE", address=address)

        self.assertEqual(address.person, person)

    def test_minimum_one2one_without_backref(self):
        try:
            self.init_registry(_minimum_one2one_without_backref)
            self.fail("No watch dog when no backref")
        except FieldException:
            pass

    def test_minimum_one2one_with_one2many(self):
        try:
            self.init_registry(_minimum_one2one_with_one2many)
            self.fail("No watch dog when one2many")
        except FieldException:
            pass
