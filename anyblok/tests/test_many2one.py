# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2019 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#    Copyright (C) 2020 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok.testing import sgdb_in
from anyblok import Declarations
from anyblok.config import Configuration
from sqlalchemy.exc import IntegrityError
from anyblok.field import FieldException
from anyblok.column import (
    Integer, String, BigInteger, Float, Decimal, Boolean, DateTime, Date, Time,
    Sequence, Email, UUID, URL, Country, Color, PhoneNumber, Selection,
    TimeStamp)
from anyblok.relationship import Many2One, ordering_list
from sqlalchemy import ForeignKeyConstraint, inspect
from .conftest import init_registry_with_bloks, init_registry, reset_db


COLUMNS = [
    Integer,
    BigInteger,
    Float,
    Decimal,
    String,
    Boolean,
    Date,
    Time,
    Email,
    UUID,
    Selection,
]


if not sgdb_in(['MySQL', 'MariaDB', 'MsSQL']):
    COLUMNS.extend([DateTime, TimeStamp])


try:
    import colour  # noqa
    COLUMNS.append(Color)
except Exception:
    pass

try:
    import furl  # noqa
    if not sgdb_in(['MySQL', 'MariaDB', 'MsSQL']):
        COLUMNS.append(URL)
except Exception:
    pass


try:
    import phonenumbers  # noqa
    COLUMNS.append(PhoneNumber)
except Exception:
    pass

try:
    import pycountry  # noqa
    COLUMNS.append(Country)
except Exception:
    pass


register = Declarations.register
Model = Declarations.Model
Mixin = Declarations.Mixin


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


def _complete_many2one_with_ordered_one2many(**kwargs):

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
                           one2many=(
                               "persons",
                               dict(
                                   order_by="ModelPerson.name",
                                   collection_class=ordering_list('name'),
                               ),
                           ),
                           nullable=False)


def _complete_many2one_with_schema(**kwargs):

    @register(Model)
    class Address:
        __db_schema__ = 'test_db_m2o_schema'

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:
        __db_schema__ = 'test_db_m2o_schema'

        name = String(primary_key=True)
        address = Many2One(model=Model.Address,
                           remote_columns="id", column_names="id_of_address",
                           one2many="persons", nullable=False)


def _complete_many2one_with_different_schema1(**kwargs):

    @register(Model)
    class Address:
        __db_schema__ = 'test_db_m2o_schema'

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:
        __db_schema__ = 'test_db_other_m2o_schema'

        name = String(primary_key=True)
        address = Many2One(model=Model.Address,
                           remote_columns="id", column_names="id_of_address",
                           one2many="persons", nullable=False)


def _complete_many2one_with_different_schema2(**kwargs):

    @register(Model)
    class Address:
        __db_schema__ = 'test_db_m2o_schema'

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


def _many2one_to_polymorphic_models_1(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()
        type_entity = String(default='shipping')

        @classmethod
        def define_mapper_args(cls):
            mapper_args = super(Address, cls).define_mapper_args()
            mapper_args.update({
                'polymorphic_on': cls.type_entity,
            })
            return mapper_args

    @register(Model.Address, tablename=Model.Address)
    class Shipping(Model.Address):

        @classmethod
        def define_mapper_args(cls):
            mapper_args = super(Shipping, cls).define_mapper_args()
            mapper_args.update({
                'polymorphic_identity': 'shipping',
            })
            return mapper_args

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2One(model=Model.Address, one2many="persons")


def _many2one_to_polymorphic_models_2(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()
        type_entity = String(default='shipping')

        @classmethod
        def define_mapper_args(cls):
            mapper_args = super(Address, cls).define_mapper_args()
            mapper_args.update({
                'polymorphic_on': cls.type_entity,
            })
            return mapper_args

    @register(Model.Address)
    class Shipping(Model.Address):
        id = Integer(primary_key=True, foreign_key=Model.Address.use('id'))

        @classmethod
        def define_mapper_args(cls):
            mapper_args = super(Shipping, cls).define_mapper_args()
            mapper_args.update({
                'polymorphic_identity': 'shipping',
            })
            return mapper_args

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address = Many2One(model=Model.Address, one2many="persons")


def _minimum_many2one_with_schema(**kwargs):

    @register(Model)
    class Address:
        __db_schema__ = 'test_db_m2o_schema'

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:
        __db_schema__ = 'test_db_m2o_schema'

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


def many2one_on_mapping_model_and_column_1(**kwargs):

    @register(Model, tablename="x")
    class Address:

        id = Integer(primary_key=True, db_column_name="x1")
        street = String(db_column_name="x2")
        zip = String(db_column_name="x3")
        city = String(db_column_name="x4")

    @register(Model, tablename="y")
    class Person:

        name = String(primary_key=True, db_column_name="y1")
        address = Many2One(model=Model.Address)


def many2one_on_mapping_model_and_column_2(**kwargs):

    @register(Model, tablename="x")
    class Address:

        id = Integer(primary_key=True, db_column_name="x1")
        street = String(db_column_name="x2")
        zip = String(db_column_name="x3")
        city = String(db_column_name="x4")

    @register(Model, tablename="y")
    class Person:

        name = String(primary_key=True, db_column_name="y1")
        address_id = Integer(db_column_name="y2",
                             foreign_key=Model.Address.use('id'))
        address = Many2One(model=Model.Address)


@pytest.fixture(
    scope="class",
    params=[
        (_complete_many2one, 'id_of_address', True),
        (_complete_many2one_with_ordered_one2many, 'id_of_address', True),
        (_complete_many2one_with_schema, 'id_of_address', True),
        (_complete_many2one_with_different_schema1, 'id_of_address', True),
        (_complete_many2one_with_different_schema2, 'id_of_address', True),
        (_minimum_many2one, 'address_id', False),
        (_many2one_to_polymorphic_models_1, 'address_id', True),
        (_many2one_to_polymorphic_models_2, 'address_id', True),
        (_minimum_many2one_with_schema, 'address_id', False),
        (_many2one_with_str_model, 'address_id', False),
        (many2one_on_mapping_model_and_column_1, 'address_id', False),
        (many2one_on_mapping_model_and_column_2, 'address_id', False),
    ]
)
def registry_many2one(request, bloks_loaded, db_schema):
    reset_db()
    registry = init_registry_with_bloks(
        [], request.param[0])
    request.addfinalizer(registry.close)
    return registry, request.param[1], request.param[2]


@pytest.mark.relationship
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
            person.delete()  # issue 68
            address.expire('persons')

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


@pytest.fixture(scope="class", params=COLUMNS)
def registry_many2one_auto_detect(request, bloks_loaded):
    reset_db()
    registry = init_registry_with_bloks(
        [], _auto_detect_type, ColumnType=request.param)
    request.addfinalizer(registry.close)
    return registry


@pytest.mark.relationship
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


@pytest.mark.relationship
class TestMany2OneOld:

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

    def test_2_many2one(self):
        with pytest.raises(FieldException):
            self.init_registry(_many2one_with_same_name_for_column_names)

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB', 'MsSQL']),
                        reason='ISSUE #89')
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
        assert test is test2.test

    def test_minimum_many2one_without_model(self):
        with pytest.raises(FieldException):
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
        assert t2.parent is t1
        assert t1.children[0] is t2

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
        assert t2.parent is t1
        assert t1.children[0] is t2

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
        assert t2.parent is t1
        assert t1.children[0] is t2

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

        with pytest.raises(IntegrityError):
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
        inspector = inspect(registry.session.connection())
        indexes = inspector.get_indexes(registry.Person.__tablename__)
        assert len(indexes) == 1

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
        inspector = inspect(registry.session.connection())
        constraint = inspector.get_pk_constraint(registry.Person.__tablename__)
        pks = constraint['constrained_columns']
        assert 'address_id' in pks

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
        assert test.id == test2.test_id
        assert test.id2 is test2.test_id2

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
        assert test.id == test2.test_id
        assert test.id2 is test2.test_id2

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
        assert test.id == test2.test_id
        assert test.id2 is test2.test_id2

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
        assert test.id == test2.other_test_id
        assert test.id2 is test2.other_test_id2

    def test_with_multi_foreign_key_on_unexisting_column(self):
        registry = self.init_registry(_two_remote_primary_keys)
        test = registry.Test.insert(id2="10")
        test2 = registry.Test2.insert(test=test)
        assert test.id == test2.test_id
        assert test.id2 is test2.test_id2

    def test_many2one_with_multi_fk_expire_field(self):
        registry = self.init_registry(_two_remote_primary_keys)
        assert('test',) in registry.expire_attributes['Model.Test2']['test_id']
        assert ('test',) in registry.expire_attributes[
            'Model.Test2']['test_id2']

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
        assert test.id == test2.test_id
        assert test.id2 is test2.test_id2

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

        with pytest.raises(FieldException):
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
        assert test1.test_id == test2.test_id

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
        assert testM2O.test is test
        with pytest.raises(IntegrityError):
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
        assert testM2O.test is test
        test.delete()
        assert not (registry.TestM2O.query().count())

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
        assert person.address_1 is address_1
        assert person.address_2 is address_2
        assert person.address_1 is not person.address_2

    def test_many2one_with_order_list_on_one2many(self):

        def add_in_registry():

            @register(Model)
            class Address:

                id = Integer(primary_key=True)

            @register(Model)
            class Person:

                id = Integer(primary_key=True)
                name = String()
                address = Many2One(
                    model=Model.Address,
                    one2many=(
                        'persons',
                        dict(
                            order_by="ModelPerson.name",
                            collection_class=ordering_list('name'),
                        )
                    )
                )

        registry = self.init_registry(add_in_registry)
        address = registry.Address.insert()
        p3 = registry.Person.insert(name='test 3', address=address)
        p1 = registry.Person.insert(name='test 1', address=address)
        p4 = registry.Person.insert(name='test 4', address=address)
        p2 = registry.Person.insert(name='test 2', address=address)
        assert address.persons == [p1, p2, p3, p4]
        assert address.persons.ordering_attr == 'name'
