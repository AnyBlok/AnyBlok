# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok.tests.testcase import DBTestCase
from anyblok import Declarations
from sqlalchemy.exc import IntegrityError
from anyblok.field import FieldException
from anyblok.column import (
    Integer, String, BigInteger, Float, Decimal, Boolean, DateTime, Date, Time,
    Sequence)
from anyblok.relationship import Many2One
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.engine.reflection import Inspector
from .conftest import init_registry_with_bloks


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


def _minimum_many2one(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2One(model=Model.Address)


def _many2one_with_str_model(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2One(model='Model.Address')


@pytest.fixture(
    scope="class",
    params=[
        (_complete_many2one, 'id_of_address', True),
        (_minimum_many2one, 'address_id', False),
        (_many2one_with_str_model, 'address_id', False),
    ]
)
def registry_many2one(request, bloks_loaded):
    registry = init_registry_with_bloks(
        [], request.param[0])
    request.addfinalizer(registry.close)
    return registry, request.param[1], request.param[2]


class TestMany2One:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_many2one):
        transaction = registry_many2one[0].begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_ok(self, request, registry_many2one):
        registry, column_name, has_one2many = registry_many2one
        address_exist = hasattr(registry.Person, 'address')
        assert address_exist
        column_name_exist = hasattr(registry.Person, column_name)
        assert column_name_exist

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(
            name="Jean-sébastien SUZANNE", address=address)

        if has_one2many:
            assert address.persons == [person]

    def test_autodoc(self, registry_many2one):
        registry, _, _ = registry_many2one
        registry.loaded_namespaces_first_step['Model.Person'][
            'address'].autodoc_get_properties()

    def test_expire_field(self, registry_many2one):
        registry, column_name, _ = registry_many2one
        id_of_address = registry.expire_attributes['Model.Person'][
            column_name]
        assert ('address',) in id_of_address


def _auto_detect_type(ColumnType=None, **kwargs):

    @register(Model)
    class Address:

        id = ColumnType(primary_key=True, **kwargs)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2One(model=Model.Address)


@pytest.fixture(
    scope="class",
    params=[
        (Integer, {}),
        (BigInteger, {}),
        (Float, {}),
        (Decimal, {}),
        (String, {}),
        (Boolean, {}),
        (DateTime, {}),
        (Date, {}),
        (Time, {}),
    ]
)
def registry_many2one_auto_detect(request, bloks_loaded):
    registry = init_registry_with_bloks(
        [], _auto_detect_type, ColumnType=request.param[0], **request.param[1])
    request.addfinalizer(registry.close)
    return registry


class TestMany2OneAutoDetectColumn:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_many2one_auto_detect):
        transaction = registry_many2one_auto_detect.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_check_autodetect_type(self, registry_many2one_auto_detect):
        registry = registry_many2one_auto_detect
        assert(
            str(registry.Address.id.property.columns[0].type) ==
            str(registry.Person.address_id.property.columns[0].type)
        )


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


def _minimum_many2one_without_model(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2One()


def _two_remote_primary_keys(**kwargs):

    @register(Model)
    class Test:

        id = Integer(primary_key=True, unique=True)
        id2 = String(primary_key=True, unique=True)

    @register(Model)
    class Test2:

        id = Integer(primary_key=True)
        test = Many2One(model=Model.Test)


class TestMany2OneOld(DBTestCase):

    def test_2_many2one(self):
        with self.assertRaises(FieldException):
            self.init_registry(_many2one_with_same_name_for_column_names)

    def test_minimum_many2one_on_sequence(self):

        def add_in_registry():

            @register(Model)
            class Test:
                id = Integer(primary_key=True)
                seq = Sequence(primary_key=True, formater="V-{seq}")

            @register(Model)
            class Test2:

                seq = Sequence(primary_key=True)
                test = Many2One(model=Model.Test)

        registry = self.init_registry(add_in_registry)
        test = registry.Test.insert()
        test2 = registry.Test2.insert(test=test)
        self.assertIs(test, test2.test)

    def test_minimum_many2one_without_model(self):
        with self.assertRaises(FieldException):
            self.init_registry(_minimum_many2one_without_model)

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

    def test_add_index_constraint(self):
        def add_in_registry():

            @register(Model)
            class Address:

                id = Integer(primary_key=True)

            @register(Model)
            class Person:

                name = String(primary_key=True)
                address = Many2One(model=Model.Address, index=True)

        registry = self.init_registry(add_in_registry)
        inspector = Inspector(registry.session.connection())
        indexes = inspector.get_indexes(registry.Person.__tablename__)
        self.assertEqual(len(indexes), 1)

    def test_add_primary_keys_constraint(self):
        def add_in_registry():

            @register(Model)
            class Address:

                id = Integer(primary_key=True)

            @register(Model)
            class Person:

                name = String(primary_key=True)
                address = Many2One(model=Model.Address, primary_key=True)

        registry = self.init_registry(add_in_registry)
        inspector = Inspector(registry.session.connection())
        pks = inspector.get_primary_keys(registry.Person.__tablename__)
        self.assertIn('address_id', pks)

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

    def test_delete_m2o_without_fk_options_on_delete_cascade(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)

            @register(Model)
            class TestM2O:

                id = Integer(primary_key=True)
                test = Many2One(model=Model.Test, nullable=True)

        registry = self.init_registry(add_in_registry)
        test = registry.Test.insert()
        testM2O = registry.TestM2O.insert(test=test)
        self.assertIs(testM2O.test, test)
        with self.assertRaises(IntegrityError):
            test.delete()

    def test_delete_m2o_with_fk_options_on_delete_cascade(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)

            @register(Model)
            class TestM2O:

                id = Integer(primary_key=True)
                test = Many2One(model=Model.Test, nullable=True,
                                foreign_key_options={'ondelete': 'cascade'})

        registry = self.init_registry(add_in_registry)
        test = registry.Test.insert()
        testM2O = registry.TestM2O.insert(test=test)
        self.assertIs(testM2O.test, test)
        test.delete()
        self.assertFalse(registry.TestM2O.query().count())

    def test_2_simple_many2one_on_the_same_model(self):

        def add_in_registry():

            @register(Model)
            class Address:

                id = Integer(primary_key=True)

            @register(Model)
            class Person:

                name = String(primary_key=True)
                address_1 = Many2One(model=Model.Address)
                address_2 = Many2One(model=Model.Address)

        registry = self.init_registry(add_in_registry)
        address_1 = registry.Address.insert()
        address_2 = registry.Address.insert()
        person = registry.Person.insert(
            name='test', address_1=address_1, address_2=address_2)
        self.assertIs(person.address_1, address_1)
        self.assertIs(person.address_2, address_2)
        self.assertIsNot(person.address_1, person.address_2)
