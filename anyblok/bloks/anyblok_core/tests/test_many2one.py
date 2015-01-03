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


def _complete_many2one(**kwargs):
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String
    Many2One = Declarations.RelationShip.Many2One

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2One(model=Model.Address,
                           remote_column="id", column_name="id_of_address",
                           one2many="persons", nullable=False)


def _minimum_many2one(**kwargs):
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String
    Many2One = Declarations.RelationShip.Many2One

    @register(Model)
    class Address:

        id = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2One(model=Model.Address)


def _many2one_with_str_model(**kwargs):
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String
    Many2One = Declarations.RelationShip.Many2One

    @register(Model)
    class Address:

        id = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2One(model='Model.Address')


def _minimum_many2one_without_model(**kwargs):
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String
    Many2One = Declarations.RelationShip.Many2One

    @register(Model)
    class Address:

        id = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2One()


def _auto_detect_type(ColumnType=None, **kwargs):
    String = Declarations.Column.String
    Many2One = Declarations.RelationShip.Many2One

    @register(Model)
    class Address:

        id = ColumnType(primary_key=True, **kwargs)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2One(model=Model.Address)


def _two_remote_primary_keys(**kwargs):
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String
    Many2One = Declarations.RelationShip.Many2One

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        id2 = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2One(model=Model.Address)


class TestMany2One(DBTestCase):

    def test_complete_many2one(self):
        registry = self.init_registry(_complete_many2one)

        address_exist = hasattr(registry.Person, 'address')
        self.assertEqual(address_exist, True)

        id_of_address_exist = hasattr(registry.Person, 'id_of_address')
        self.assertEqual(id_of_address_exist, True)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(
            name="Jean-sébastien SUZANNE", address=address)

        self.assertEqual(address.persons, [person])

    def test_minimum_many2one(self):
        registry = self.init_registry(_minimum_many2one)

        address_exist = hasattr(registry.Person, 'address')
        self.assertEqual(address_exist, True)

        address_id_exist = hasattr(registry.Person, 'address_id')
        self.assertEqual(address_id_exist, True)

        address = registry.Address.insert()

        person = registry.Person.insert(
            name="Jean-sébastien SUZANNE", address=address)

        self.assertEqual(person.address, address)

    def test_many2one_with_str_model(self):
        registry = self.init_registry(_many2one_with_str_model)

        address_exist = hasattr(registry.Person, 'address')
        self.assertEqual(address_exist, True)

        address_id_exist = hasattr(registry.Person, 'address_id')
        self.assertEqual(address_id_exist, True)

        address = registry.Address.insert()

        person = registry.Person.insert(
            name="Jean-sébastien SUZANNE", address=address)

        self.assertEqual(person.address, address)

    def test_minimum_many2one_without_model(self):
        try:
            self.init_registry(_minimum_many2one_without_model)
            self.fail("No watch dog when more no model")
        except FieldException:
            pass

    def test_two_remote_primary_keys(self):
        try:
            self.init_registry(_two_remote_primary_keys)
            self.fail("No watch dog when more than one primary keys")
        except FieldException:
            pass

    def check_autodetect_type(self, ColumnType):
        registry = self.init_registry(_auto_detect_type, ColumnType=ColumnType)
        self.assertEqual(
            str(registry.Address.id.property.columns[0].type),
            str(registry.Person.address_id.property.columns[0].type))

    def test_autodetect_type_integer(self):
        Integer = Declarations.Column.Integer
        self.check_autodetect_type(Integer)

    def test_autodetect_type_small_integer(self):
        SmallInteger = Declarations.Column.SmallInteger
        self.check_autodetect_type(SmallInteger)

    def test_autodetect_type_big_integer(self):
        BigInteger = Declarations.Column.BigInteger
        self.check_autodetect_type(BigInteger)

    def test_autodetect_type_float(self):
        Float = Declarations.Column.Float
        self.check_autodetect_type(Float)

    def test_autodetect_type_decimal(self):
        Decimal = Declarations.Column.Decimal
        self.check_autodetect_type(Decimal)

    def test_autodetect_type_string(self):
        String = Declarations.Column.String
        self.check_autodetect_type(String)

    def test_autodetect_type_ustring(self):
        uString = Declarations.Column.uString
        self.check_autodetect_type(uString)

    def test_autodetect_type_boolean(self):
        Boolean = Declarations.Column.Boolean
        self.check_autodetect_type(Boolean)

    def test_autodetect_type_datetime(self):
        DateTime = Declarations.Column.DateTime
        self.check_autodetect_type(DateTime)

    def test_autodetect_type_date(self):
        Date = Declarations.Column.Date
        self.check_autodetect_type(Date)

    def test_autodetect_type_time(self):
        Time = Declarations.Column.Time
        self.check_autodetect_type(Time)
