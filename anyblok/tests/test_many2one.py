# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import DBTestCase
from anyblok import Declarations
from sqlalchemy.exc import IntegrityError
from anyblok.field import FieldException
from anyblok.column import (Integer,
                            String,
                            SmallInteger,
                            BigInteger,
                            Float,
                            Decimal,
                            uString,
                            Boolean,
                            DateTime,
                            Date,
                            Time)
from anyblok.relationship import Many2One
from sqlalchemy import ForeignKeyConstraint


register = Declarations.register
Model = Declarations.Model
Mixin = Declarations.Mixin


def _complete_many2one(**kwargs):

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
                           remote_columns="id", column_names="id_of_address",
                           one2many="persons", nullable=False)


def _many2one_with_same_name_for_column_names(**kwargs):

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
                           column_names="address")


def _minimum_many2one(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2One(model=Model.Address)


def _many2one_with_str_model(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2One(model='Model.Address')


def _minimum_many2one_without_model(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2One()


def _auto_detect_type(ColumnType=None, **kwargs):

    @register(Model)
    class Address:

        id = ColumnType(primary_key=True, **kwargs)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2One(model=Model.Address)


def _two_remote_primary_keys(**kwargs):

    @register(Model)
    class Test:

        id = Integer(primary_key=True, unique=True)
        id2 = String(primary_key=True, unique=True)

    @register(Model)
    class Test2:

        id = Integer(primary_key=True)
        test = Many2One(model=Model.Test)


class TestMany2One(DBTestCase):

    def test_complete_many2one(self):
        registry = self.init_registry(_complete_many2one)
        address_exist = hasattr(registry.Person, 'address')
        self.assertTrue(address_exist)
        id_of_address_exist = hasattr(registry.Person, 'id_of_address')
        self.assertTrue(id_of_address_exist)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(
            name="Jean-sébastien SUZANNE", address=address)

        self.assertEqual(address.persons, [person])

    def test_complete_many2one_expire_field(self):
        registry = self.init_registry(_complete_many2one)
        self.assertIn(
            ('address',),
            registry.expire_attributes['Model.Person']['id_of_address'])

    def test_2_many2one(self):
        with self.assertRaises(FieldException):
            self.init_registry(_many2one_with_same_name_for_column_names)

    def test_minimum_many2one(self):
        registry = self.init_registry(_minimum_many2one)
        address_exist = hasattr(registry.Person, 'address')
        self.assertTrue(address_exist)
        address_id_exist = hasattr(registry.Person, 'address_id')
        self.assertTrue(address_id_exist)
        address = registry.Address.insert()
        person = registry.Person.insert(
            name="Jean-sébastien SUZANNE", address=address)
        self.assertEqual(person.address, address)

    def test_minimum_many2one_expire_field(self):
        registry = self.init_registry(_minimum_many2one)
        self.assertEqual(
            registry.expire_attributes['Model.Person']['address_id'],
            {('address',)})

    def test_many2one_with_str_model(self):
        registry = self.init_registry(_many2one_with_str_model)
        address_exist = hasattr(registry.Person, 'address')
        self.assertTrue(address_exist)
        address_id_exist = hasattr(registry.Person, 'address_id')
        self.assertTrue(address_id_exist)
        address = registry.Address.insert()
        person = registry.Person.insert(
            name="Jean-sébastien SUZANNE", address=address)
        self.assertIs(person.address, address)

    def test_minimum_many2one_without_model(self):
        with self.assertRaises(FieldException):
            self.init_registry(_minimum_many2one_without_model)

    def check_autodetect_type(self, ColumnType):
        registry = self.init_registry(_auto_detect_type, ColumnType=ColumnType)
        self.assertEqual(
            str(registry.Address.id.property.columns[0].type),
            str(registry.Person.address_id.property.columns[0].type))

    def test_autodetect_type_integer(self):
        self.check_autodetect_type(Integer)

    def test_autodetect_type_small_integer(self):
        self.check_autodetect_type(SmallInteger)

    def test_autodetect_type_big_integer(self):
        self.check_autodetect_type(BigInteger)

    def test_autodetect_type_float(self):
        self.check_autodetect_type(Float)

    def test_autodetect_type_decimal(self):
        self.check_autodetect_type(Decimal)

    def test_autodetect_type_string(self):
        self.check_autodetect_type(String)

    def test_autodetect_type_ustring(self):
        self.check_autodetect_type(uString)

    def test_autodetect_type_boolean(self):
        self.check_autodetect_type(Boolean)

    def test_autodetect_type_datetime(self):
        self.check_autodetect_type(DateTime)

    def test_autodetect_type_date(self):
        self.check_autodetect_type(Date)

    def test_autodetect_type_time(self):
        self.check_autodetect_type(Time)

    def test_same_model(self):
        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                parent = Many2One(model='Model.Test', one2many='children')

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert()
        t2 = registry.Test.insert(parent=t1)
        self.assertEqual(t2.parent, t1)
        self.assertEqual(t1.children[0], t2)

    def test_same_model_pk_by_inherit(self):
        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)

            @register(Model)  # noqa
            class Test:

                parent = Many2One(model='Model.Test', one2many='children')

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert()
        t2 = registry.Test.insert(parent=t1)
        self.assertEqual(t2.parent, t1)
        self.assertEqual(t1.children[0], t2)

    def test_same_model_pk_by_mixin(self):
        def add_in_registry():

            @register(Mixin)
            class MTest:

                id = Integer(primary_key=True)

            @register(Model)  # noqa
            class Test(Mixin.MTest):

                parent = Many2One(model='Model.Test', one2many='children')

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert()
        t2 = registry.Test.insert(parent=t1)
        self.assertEqual(t2.parent, t1)
        self.assertEqual(t1.children[0], t2)

    def test_add_unique_constraint(self):
        def add_in_registry():

            @register(Model)
            class Address:

                id = Integer(primary_key=True)

            @register(Model)
            class Person:

                name = String(primary_key=True)
                address = Many2One(model=Model.Address, unique=True)

        registry = self.init_registry(add_in_registry)
        address = registry.Address.insert()
        registry.Person.insert(
            name="Jean-sébastien SUZANNE", address=address)

        with self.assertRaises(IntegrityError):
            registry.Person.insert(name="Other", address=address)

    def test_complet_with_multi_foreign_key(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True, unique=True)
                id2 = String(primary_key=True, unique=True)

            @register(Model)
            class Test2:

                @classmethod
                def define_table_args(cls):
                    table_args = super(Test2, cls).define_table_args()
                    return table_args + (ForeignKeyConstraint(
                        [cls.test_id, cls.test_id2], ['test.id', 'test.id2']),)

                id = Integer(primary_key=True)
                test_id = Integer(
                    foreign_key=Model.Test.use('id'), nullable=False)
                test_id2 = String(
                    foreign_key=Model.Test.use('id2'), nullable=False)
                test = Many2One(model=Model.Test,
                                remote_columns=('id', 'id2'),
                                column_names=('test_id', 'test_id2'))

        registry = self.init_registry(add_in_registry)
        test = registry.Test.insert(id2="10")
        test2 = registry.Test2.insert(test=test)
        self.assertEqual(test.id, test2.test_id)
        self.assertEqual(test.id2, test2.test_id2)

    def test_complet_with_multi_foreign_key_without_constraint(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True, unique=True)
                id2 = String(primary_key=True, unique=True)

            @register(Model)
            class Test2:

                id = Integer(primary_key=True)
                test_id = Integer(
                    foreign_key=Model.Test.use('id'), nullable=False)
                test_id2 = String(
                    foreign_key=Model.Test.use('id2'), nullable=False)
                test = Many2One(model=Model.Test,
                                remote_columns=('id', 'id2'),
                                column_names=('test_id', 'test_id2'))

        registry = self.init_registry(add_in_registry)
        test = registry.Test.insert(id2="10")
        test2 = registry.Test2.insert(test=test)
        self.assertEqual(test.id, test2.test_id)
        self.assertEqual(test.id2, test2.test_id2)

    def test_with_multi_foreign_key_on_existing_column(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True, unique=True)
                id2 = String(primary_key=True, unique=True)

            @register(Model)
            class Test2:

                id = Integer(primary_key=True)
                test_id = Integer(
                    foreign_key=Model.Test.use('id'), nullable=False)
                test_id2 = String(
                    foreign_key=Model.Test.use('id2'), nullable=False)
                test = Many2One(model=Model.Test)

        registry = self.init_registry(add_in_registry)
        test = registry.Test.insert(id2="10")
        test2 = registry.Test2.insert(test=test)
        self.assertEqual(test.id, test2.test_id)
        self.assertEqual(test.id2, test2.test_id2)

    def test_with_multi_foreign_key_on_existing_column2(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True, unique=True)
                id2 = String(primary_key=True, unique=True)

            @register(Model)
            class Test2:

                id = Integer(primary_key=True)
                other_test_id = Integer(
                    foreign_key=Model.Test.use('id'), nullable=False)
                other_test_id2 = String(
                    foreign_key=Model.Test.use('id2'), nullable=False)
                test = Many2One(model=Model.Test)

        registry = self.init_registry(add_in_registry)
        test = registry.Test.insert(id2="10")
        test2 = registry.Test2.insert(test=test)
        self.assertEqual(test.id, test2.other_test_id)
        self.assertEqual(test.id2, test2.other_test_id2)

    def test_with_multi_foreign_key_on_unexisting_column(self):
        registry = self.init_registry(_two_remote_primary_keys)
        test = registry.Test.insert(id2="10")
        test2 = registry.Test2.insert(test=test)
        self.assertEqual(test.id, test2.test_id)
        self.assertEqual(test.id2, test2.test_id2)

    def test_many2one_with_multi_fk_expire_field(self):
        registry = self.init_registry(_two_remote_primary_keys)
        self.assertIn(
            ('test',),
            registry.expire_attributes['Model.Test2']['test_id'])
        self.assertIn(
            ('test',),
            registry.expire_attributes['Model.Test2']['test_id2'])

    def test_with_multi_foreign_key_on_unexisting_named_column(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True, unique=True)
                id2 = String(primary_key=True, unique=True)

            @register(Model)
            class Test2:

                id = Integer(primary_key=True)
                test = Many2One(model=Model.Test,
                                column_names=('test_id', 'test_id2'))

        registry = self.init_registry(add_in_registry)
        test = registry.Test.insert(id2="10")
        test2 = registry.Test2.insert(test=test)
        self.assertEqual(test.id, test2.test_id)
        self.assertEqual(test.id2, test2.test_id2)

    def test_with_multi_foreign_key_on_unexisting_named_column2(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True, unique=True)
                id2 = Integer(primary_key=True, unique=True)

            @register(Model)
            class Test2:

                id = Integer(primary_key=True)
                test = Many2One(model=Model.Test, column_names=(
                    'other_test_id', 'other_test_id2'))

        with self.assertRaises(FieldException):
            self.init_registry(add_in_registry)

    def test_m2o_in_mixin(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)

            @register(Mixin)
            class MTest:

                test = Many2One(model=Model.Test)

            @register(Model)
            class Test1(Mixin.MTest):

                id = Integer(primary_key=True)

            @register(Model)
            class Test2(Mixin.MTest):

                id = Integer(primary_key=True)

        registry = self.init_registry(add_in_registry)
        test = registry.Test.insert()
        test1 = registry.Test1.insert(test=test)
        test2 = registry.Test2.insert(test=test)
        self.assertEqual(test1.test_id, test2.test_id)
