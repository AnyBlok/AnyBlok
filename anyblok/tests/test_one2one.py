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
from anyblok import Declarations
from anyblok.config import Configuration
from anyblok.field import FieldException
from anyblok.column import Integer, String
from anyblok.relationship import One2One
from sqlalchemy import ForeignKeyConstraint
from .conftest import init_registry, reset_db

register = Declarations.register
Model = Declarations.Model


@pytest.fixture(
    scope="class",
    params=[
        ('prefix', 'suffix'),
        ('', ''),
    ]
)
def db_schema(request, bloks_loaded):
    Configuration.set('prefix_db_schema', request.param[0])
    Configuration.set('suffix_db_schema', request.param[1])

    def rollback():
        Configuration.set('prefix_db_schema', '')
        Configuration.set('suffix_db_schema', '')

    request.addfinalizer(rollback)


def _minimum_one2one(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = One2One(model=Model.Address, backref="person")


def _minimum_one2one_with_schema(**kwargs):

    @register(Model)
    class Address:
        __db_schema__ = 'test_db_m2m_schema'

        id = Integer(primary_key=True)

    @register(Model)
    class Person:
        __db_schema__ = 'test_db_m2m_schema'

        name = String(primary_key=True)
        address = One2One(model=Model.Address, backref="person")


def _minimum_one2one_with_diferent_schema1(**kwargs):

    @register(Model)
    class Address:
        __db_schema__ = 'test_db_m2m_schema'

        id = Integer(primary_key=True)

    @register(Model)
    class Person:
        __db_schema__ = 'test_other_db_schema'

        name = String(primary_key=True)
        address = One2One(model=Model.Address, backref="person")


def _minimum_one2one_with_diferent_schema2(**kwargs):

    @register(Model)
    class Address:
        __db_schema__ = 'test_db_m2m_schema'

        id = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = One2One(model=Model.Address, backref="person")


def _one2one_with_str_method(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = One2One(model="Model.Address", backref="person")


def _minimum_one2one_on_mapper_1(**kwargs):

    @register(Model, tablename="x")
    class Address:

        id = Integer(primary_key=True, db_column_name="x1")

    @register(Model, tablename="y")
    class Person:

        name = String(primary_key=True, db_column_name="y1")
        address = One2One(model=Model.Address, backref="person")


def _minimum_one2one_on_mapper_2(**kwargs):

    @register(Model, tablename="x")
    class Address:

        id = Integer(primary_key=True, db_column_name="x1")

    @register(Model, tablename="y")
    class Person:

        name = String(primary_key=True, db_column_name="y1")
        address_id = Integer(db_column_name="y2",
                             foreign_key=Model.Address.use('id'))
        address = One2One(model=Model.Address, backref="person")


@pytest.fixture(scope="class", params=[
    _minimum_one2one,
    _minimum_one2one_with_schema,
    _minimum_one2one_with_diferent_schema1,
    _minimum_one2one_with_diferent_schema2,
    _one2one_with_str_method,
    _minimum_one2one_on_mapper_1,
    _minimum_one2one_on_mapper_2,
])
def registry_minimum_one2one(request, bloks_loaded, db_schema):
    reset_db()
    registry = init_registry(request.param)
    request.addfinalizer(registry.close)
    return registry


@pytest.mark.relationship
class TestMinimumOne2One:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_minimum_one2one):
        transaction = registry_minimum_one2one.begin_nested()
        request.addfinalizer(transaction.rollback)

    def test_minimum_one2one(self, registry_minimum_one2one):
        registry = registry_minimum_one2one
        assert hasattr(registry.Person, 'address')
        assert hasattr(registry.Person, 'address_id')
        address = registry.Address.insert()
        person = registry.Person.insert(
            name="Jean-sébastien SUZANNE", address=address)

        assert address.person is person

    def test_one2one_multi_entry_for_same(self, registry_minimum_one2one):
        registry = registry_minimum_one2one
        address = registry.Address.insert()
        p1 = registry.Person.insert(
            name="Jean-sébastien SUZANNE", address=address)
        assert p1.address is address
        p2 = registry.Person.insert(name="Franck BRET", address=address)
        assert p2.address is address
        assert p1.address_id is None

    def test_minimum_one2one_expire_field(self, registry_minimum_one2one):
        registry = registry_minimum_one2one
        assert ('address',) in registry.expire_attributes[
            'Model.Person']['address_id']
        assert ('address', 'person') in registry.expire_attributes[
            'Model.Person']['address_id']


def _multi_fk_one2one():

    @register(Model)
    class Test:

        id = Integer(primary_key=True, unique=True)
        id2 = String(primary_key=True, unique=True)

    @register(Model)
    class Test2:

        id = Integer(primary_key=True)
        test = One2One(model=Model.Test,
                       column_names=('test_id', 'test_id2'),
                       backref="test2")


@pytest.fixture(scope="class")
def registry_multi_fk_one2one(request, bloks_loaded):
    reset_db()
    registry = init_registry(_multi_fk_one2one)
    request.addfinalizer(registry.close)
    return registry


@pytest.mark.relationship
class TestMultiFKOne2One:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_multi_fk_one2one):
        transaction = registry_multi_fk_one2one.begin_nested()
        request.addfinalizer(transaction.rollback)

    def test_with_multi_foreign_key_on_unexisting_named_column(
        self, registry_multi_fk_one2one
    ):
        registry = registry_multi_fk_one2one
        test = registry.Test.insert(id2="10")
        test2 = registry.Test2.insert(test=test)
        assert test.id == test2.test_id
        assert test.id2 == test2.test_id2

    def test_multi_o2o_one2one_expire_field(
        self, registry_multi_fk_one2one
    ):
        registry = registry_multi_fk_one2one
        assert ('test',) in registry.expire_attributes[
            'Model.Test2']['test_id']
        assert ('test', 'test2') in registry.expire_attributes[
            'Model.Test2']['test_id']
        assert ('test',) in registry.expire_attributes[
            'Model.Test2']['test_id2']
        assert ('test', 'test2') in registry.expire_attributes[
            'Model.Test2']['test_id2']


def _complete_one2one(**kwargs):

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
                          remote_columns="id", column_names="id_of_address",
                          backref="person", nullable=False)


def _complete_one2one_with_schema(**kwargs):

    @register(Model)
    class Address:
        __db_schema__ = 'test_db_m2m_schema'

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:
        __db_schema__ = 'test_db_m2m_schema'

        name = String(primary_key=True)
        address = One2One(model=Model.Address,
                          remote_columns="id", column_names="id_of_address",
                          backref="person", nullable=False)


def _minimum_one2one_without_backref(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = One2One(model=Model.Address)


def _minimum_one2one_with_one2many(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = One2One(model=Model.Address,
                          backref="person", one2many="persons")


@pytest.mark.relationship
class TestOne2One:

    @pytest.fixture(autouse=True)
    def close_registry(self, request, bloks_loaded):

        def close():
            if hasattr(self, 'registry'):
                self.registry.close()

        request.addfinalizer(close)

    def init_registry(self, *args, **kwargs):
        reset_db()
        self.registry = init_registry(*args, **kwargs)
        return self.registry

    def test_complete_one2one(self):
        registry = self.init_registry(_complete_one2one)
        assert hasattr(registry.Person, 'address')
        assert hasattr(registry.Person, 'id_of_address')
        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')
        person = registry.Person.insert(
            name="Jean-sébastien SUZANNE", address=address)

        assert address.person is person

    def test_complete_one2one_with_schema(self, db_schema):
        registry = self.init_registry(_complete_one2one_with_schema)
        assert hasattr(registry.Person, 'address')
        assert hasattr(registry.Person, 'id_of_address')
        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')
        person = registry.Person.insert(
            name="Jean-sébastien SUZANNE", address=address)

        assert address.person is person

    def test_minimum_one2one_without_backref(self):
        with pytest.raises(FieldException):
            self.init_registry(_minimum_one2one_without_backref)

    def test_minimum_one2one_with_one2many(self):
        with pytest.raises(FieldException):
            self.init_registry(_minimum_one2one_with_one2many)

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
                test = One2One(model=Model.Test,
                               remote_columns=('id', 'id2'),
                               column_names=('test_id', 'test_id2'),
                               backref="test2")

        registry = self.init_registry(add_in_registry)
        test = registry.Test.insert(id2="10")
        test2 = registry.Test2.insert(test=test)
        assert test.id == test2.test_id
        assert test.id2 == test2.test_id2

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
                test = One2One(model=Model.Test,
                               remote_columns=('id', 'id2'),
                               column_names=('test_id', 'test_id2'),
                               backref="test2")

        registry = self.init_registry(add_in_registry)
        test = registry.Test.insert(id2="10")
        test2 = registry.Test2.insert(test=test)
        assert test.id == test2.test_id
        assert test.id2 == test2.test_id2

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
                test = One2One(model=Model.Test, backref="test2")

        registry = self.init_registry(add_in_registry)
        test = registry.Test.insert(id2="10")
        test2 = registry.Test2.insert(test=test)
        assert test.id == test2.test_id
        assert test.id2 == test2.test_id2

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
                test = One2One(model=Model.Test, backref="test2")

        registry = self.init_registry(add_in_registry)
        test = registry.Test.insert(id2="10")
        test2 = registry.Test2.insert(test=test)
        assert test.id == test2.other_test_id
        assert test.id2 == test2.other_test_id2

    def test_with_multi_foreign_key_on_unexisting_column(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True, unique=True)
                id2 = String(primary_key=True, unique=True)

            @register(Model)
            class Test2:

                id = Integer(primary_key=True)
                test = One2One(model=Model.Test, backref="test2")

        registry = self.init_registry(add_in_registry)
        test = registry.Test.insert(id2="10")
        test2 = registry.Test2.insert(test=test)
        assert test.id == test2.test_id
        assert test.id2 == test2.test_id2

    def test_with_multi_foreign_key_on_unexisting_named_column2(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True, unique=True)
                id2 = Integer(primary_key=True, unique=True)

            @register(Model)
            class Test2:

                id = Integer(primary_key=True)
                test = One2One(model=Model.Test, column_names=(
                    'other_test_id', 'other_test_id2'), backref="test2")

        with pytest.raises(FieldException):
            self.init_registry(add_in_registry)
