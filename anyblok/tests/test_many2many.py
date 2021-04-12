# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Pierre Verkest <pverkest@anybox.fr>
#    Copyright (C) 2019 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.testing import sgdb_in
import pytest
from anyblok import Declarations
from anyblok.config import Configuration
from anyblok.mapper import ModelAttributeException
from anyblok.column import Integer, String, DateTime
from anyblok.relationship import Many2Many, Many2One, ordering_list
from anyblok.field import FieldException
from datetime import datetime
from .conftest import init_registry, reset_db

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


def _complete_many2many_with_ordered_backref(**kwargs):

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
                              many2many=(
                                  "persons",
                                  dict(
                                      order_by="ModelPerson.name",
                                      collection_class=ordering_list('name'),
                                  ),
                              ))


def _complete_many2many_with_schema(**kwargs):

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
        addresses = Many2Many(model=Model.Address,
                              join_table="join_addresses_by_persons",
                              schema="test_db_m2m_schema",
                              remote_columns="id", local_columns="name",
                              m2m_remote_columns='a_id',
                              m2m_local_columns='p_name',
                              many2many="persons")


def _complete_many2many_with_diferent_schema1(**kwargs):

    @register(Model)
    class Address:
        __db_schema__ = 'test_db_m2m_schema'

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:
        __db_schema__ = 'test_db_m2m_other_schema'

        name = String(primary_key=True)
        addresses = Many2Many(model=Model.Address,
                              join_table="join_addresses_by_persons",
                              remote_columns="id", local_columns="name",
                              m2m_remote_columns='a_id',
                              m2m_local_columns='p_name',
                              many2many="persons")


def _complete_many2many_with_diferent_schema2(**kwargs):

    @register(Model)
    class Address:
        __db_schema__ = 'test_db_m2m_schema'

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


@pytest.fixture(
    scope="class",
    params=[
        _complete_many2many,
        _complete_many2many_with_ordered_backref,
        _complete_many2many_with_schema,
        _complete_many2many_with_diferent_schema1,
        _complete_many2many_with_diferent_schema2,
    ]
)
def registry_many2many(request, bloks_loaded, db_schema):
    reset_db()
    registry = init_registry(request.param)
    request.addfinalizer(registry.close)
    return registry


@pytest.mark.relationship
class TestMany2ManyComplete:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_many2many):
        transaction = registry_many2many.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_complete_many2many(self, registry_many2many):
        registry = registry_many2many

        address_exist = hasattr(registry.Person, 'addresses')
        assert address_exist

        m2m_tables_exist = hasattr(registry, 'many2many_tables')
        assert m2m_tables_exist

        jt = registry.declarativebase.metadata.tables
        join_table = 'join_addresses_by_persons'
        if registry.Person.__db_schema__:
            join_table = '%s.%s' % (registry.Person.__db_schema__, join_table)
        assert join_table in jt

        assert len(jt[join_table].primary_key.columns) == 2
        assert 'a_id' in jt[join_table].primary_key.columns
        assert 'p_name' in jt[join_table].primary_key.columns

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")

        person.addresses.append(address)

        assert address.persons == [person]

    def test_many2many_autodoc(self, registry_many2many):
        registry = registry_many2many
        registry.loaded_namespaces_first_step['Model.Person'][
            'addresses'].autodoc_get_properties()

    def test_complete_many2many_expire_field(self, registry_many2many):
        registry = registry_many2many
        assert ('x2m', 'addresses', 'persons') in registry.expire_attributes[
            'Model.Person']['addresses']
        assert ('x2m', 'persons', 'addresses') in registry.expire_attributes[
            'Model.Address']['persons']


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


def many2many_on_mapper(**kwargs):

    @register(Model, tablename="x")
    class Address:

        id = Integer(primary_key=True, db_column_name="x1")
        street = String(db_column_name="x2")
        zip = String(db_column_name="x3")
        city = String(db_column_name="x4")

    @register(Model, tablename="y")
    class Person:

        name = String(primary_key=True, db_column_name="y1")
        addresses = Many2Many(model=Model.Address)


def _minimum_many2many_with_schema(**kwargs):

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
        id2 = Integer(primary_key=True, autoincrement=False)

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
        persons = Many2Many(
            model=Model.Person,
            join_table='join_person_and_address_for_addresses')


@pytest.mark.relationship
class TestMany2Many:

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

    def test_minimum_many2many(self):
        registry = self.init_registry(_minimum_many2many)

        address_exist = hasattr(registry.Person, 'addresses')
        assert address_exist

        m2m_tables_exist = hasattr(registry, 'many2many_tables')
        assert m2m_tables_exist

        jt = registry.declarativebase.metadata.tables
        join_table_exist = 'join_person_and_address_for_addresses' in jt
        assert join_table_exist

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")

        person.addresses.append(address)

        assert person.addresses == [address]

    def test_many2many_on_mapper(self):
        registry = self.init_registry(many2many_on_mapper)

        address_exist = hasattr(registry.Person, 'addresses')
        assert address_exist

        m2m_tables_exist = hasattr(registry, 'many2many_tables')
        assert m2m_tables_exist

        jt = registry.declarativebase.metadata.tables
        join_table_exist = 'join_y_and_x_for_addresses' in jt
        assert join_table_exist

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")

        person.addresses.append(address)

        assert person.addresses == [address]

    def test_minimum_many2many_with_schema(self, db_schema):
        registry = self.init_registry(_minimum_many2many_with_schema)

        address_exist = hasattr(registry.Person, 'addresses')
        assert address_exist

        m2m_tables_exist = hasattr(registry, 'many2many_tables')
        assert m2m_tables_exist

        jt = registry.declarativebase.metadata.tables
        join_table_exist = (
            '%s.join_person_and_address_for_addresses' % (
                registry.Person.__db_schema__
            ) in jt)
        assert join_table_exist

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")

        person.addresses.append(address)

        assert person.addresses == [address]

    def test_many2many_with_str_model(self):
        registry = self.init_registry(_many2many_with_str_model)

        address_exist = hasattr(registry.Person, 'addresses')
        assert address_exist

        m2m_tables_exist = hasattr(registry, 'many2many_tables')
        assert m2m_tables_exist

        jt = registry.declarativebase.metadata.tables
        join_table_exist = 'join_person_and_address_for_addresses' in jt
        assert join_table_exist

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")

        person.addresses.append(address)

        assert person.addresses == [address]

    def test_many2many_with_two_primary_key(self):
        registry = self.init_registry(auto_detect_two_primary_keys)

        address = registry.Address.insert(id2=1)
        person = registry.Person.insert(name="Jean-sébastien SUZANNE")
        person.addresses.append(address)

        assert person.addresses == [address]

    def test_unexisting_remote_columns(self):
        with pytest.raises(ModelAttributeException):
            self.init_registry(unexisting_remote_columns)

    def test_reuse_many2many_table(self):
        registry = self.init_registry(reuse_many2many_table)

        address = registry.Address.insert()
        person = registry.Person.insert(name="Jean-sébastien SUZANNE")

        person.addresses.append(address)

        assert address.persons == [person]

    def test_declared_in_mixin(self):
        registry = self.init_registry(_minimum_many2many_by_mixin)

        address_exist = hasattr(registry.Person, 'addresses')
        assert address_exist

        m2m_tables_exist = hasattr(registry, 'many2many_tables')
        assert m2m_tables_exist

        jt = registry.declarativebase.metadata.tables
        join_table_exist = 'join_person_and_address_for_addresses' in jt
        assert join_table_exist

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")

        person.addresses.append(address)

        assert person.addresses == [address]

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB', 'MsSQL']),
                        reason='ISSUE #90')
    def test_declared_in_mixin_inherit_by_two_models(self):
        def add_in_registry():
            _minimum_many2many_by_mixin()

            @register(Model)
            class Person2(Mixin.MixinM2M):

                name = String(primary_key=True)

        registry = self.init_registry(add_in_registry)

        address_exist = hasattr(registry.Person, 'addresses')
        assert address_exist
        address_exist = hasattr(registry.Person2, 'addresses')
        assert address_exist

        m2m_tables_exist = hasattr(registry, 'many2many_tables')
        assert m2m_tables_exist

        jt = registry.declarativebase.metadata.tables
        join_table_exist = 'join_person_and_address_for_addresses' in jt
        assert join_table_exist
        join_table_exist = 'join_person2_and_address_for_addresses' in jt
        assert join_table_exist

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
        assert t1.test2[0] is t2

        jt = registry.declarativebase.metadata.tables
        assert len(jt['join_test_and_test2'].primary_key.columns) == 4
        assert 't1_id' in jt[
            'join_test_and_test2'].primary_key.columns
        assert 't1_id2' in jt[
            'join_test_and_test2'].primary_key.columns
        assert 't2_id' in jt[
            'join_test_and_test2'].primary_key.columns
        assert 't2_id2' in jt[
            'join_test_and_test2'].primary_key.columns

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
        assert t1.test2[0] is t2

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
        assert t1.test2[0] is t2

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
        assert t1.test2[0] is t2

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
        assert t1.test2[0] is t2

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
        assert t1.test2[0] is t2

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
        assert t1 in t2.parents

    def test_many2many_on_self_with_schema(self, db_schema):

        def add_in_registry():

            @register(Model)
            class Test:
                __db_schema__ = 'test_db_m2m_schema'

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
        assert t1 in t2.parents

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
        assert t1 in t2.parents

    def test_many2many_on_self_auto_column_with_schema(self, db_schema):

        def add_in_registry():

            @register(Model)
            class Test2:
                __db_schema__ = 'test_db_m2m_schema'

                id = Integer(primary_key=True)
                childs = Many2Many(
                    model='Model.Test2',
                    many2many='parents'
                )

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test2.insert()
        t2 = registry.Test2.insert()
        t1.childs.append(t2)
        assert t1 in t2.parents

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

        with pytest.raises(FieldException):
            self.init_registry(add_in_registry)

    def assert_rich_many2many_complete_config(self, registry):
        person = registry.Person.insert(name='jssuzanne')
        address = registry.Address.insert(
            street='somewhere', zip="75001", city="Paris")
        person.addresses.append(address)
        personaddress = registry.PersonAddress.query().one()
        assert personaddress.a_id == address.id
        assert personaddress.p_name == person.name
        assert personaddress.id
        assert personaddress.create_at
        assert personaddress.foo == 'bar'

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
        self.assert_rich_many2many_complete_config(registry)

    def test_rich_many2many_complete_config_on_mapper(self):
        def add_in_registry():

            @register(Model, tablename="x")
            class Address:

                id = Integer(primary_key=True, db_column_name="x1")
                street = String(db_column_name="x2")
                zip = String(db_column_name="x3")
                city = String(db_column_name="x4")

            @register(Model, tablename="y")
            class PersonAddress:
                id = Integer(primary_key=True, db_column_name="y1")
                a_id = Integer(
                    foreign_key=Model.Address.use('id'), nullable=False,
                    db_column_name="y2")
                p_name = String(
                    foreign_key='Model.Person=>name', nullable=False,
                    db_column_name="y3")
                create_at = DateTime(default=datetime.now, db_column_name="y4")
                foo = String(default='bar', db_column_name="y5")

            @register(Model, tablename="z")
            class Person:

                name = String(primary_key=True, db_column_name="z1")
                addresses = Many2Many(model=Model.Address,
                                      join_model=Model.PersonAddress,
                                      many2many="persons")

        registry = self.init_registry(add_in_registry)
        self.assert_rich_many2many_complete_config(registry)

    def test_rich_many2many_complete_config_with_schema(self, db_schema):
        def add_in_registry():

            @register(Model)
            class Address:
                __db_schema__ = 'test_db_m2m_schema'

                id = Integer(primary_key=True)
                street = String()
                zip = String()
                city = String()

            @register(Model)
            class PersonAddress:
                __db_schema__ = 'test_db_m2m_schema'

                id = Integer(primary_key=True)
                a_id = Integer(
                    foreign_key=Model.Address.use('id'), nullable=False)
                p_name = String(
                    foreign_key='Model.Person=>name', nullable=False)
                create_at = DateTime(default=datetime.now)
                foo = String(default='bar')

            @register(Model)
            class Person:
                __db_schema__ = 'test_db_m2m_schema'

                name = String(primary_key=True)
                addresses = Many2Many(
                    model=Model.Address,
                    join_table="test_db_m2m_schema.personaddress",
                    remote_columns="id", local_columns="name",
                    m2m_remote_columns='a_id',
                    m2m_local_columns='p_name',
                    many2many="persons")

        registry = self.init_registry(add_in_registry)
        self.assert_rich_many2many_complete_config(registry)

    def test_rich_many2many_complete_config_with_different_schema(self,
                                                                  db_schema):
        def add_in_registry():

            @register(Model)
            class Address:
                __db_schema__ = 'test_db_m2m_schema1'

                id = Integer(primary_key=True)
                street = String()
                zip = String()
                city = String()

            @register(Model)
            class PersonAddress:
                __db_schema__ = 'test_db_m2m_schema2'

                id = Integer(primary_key=True)
                a_id = Integer(
                    foreign_key=Model.Address.use('id'), nullable=False)
                p_name = String(
                    foreign_key='Model.Person=>name', nullable=False)
                create_at = DateTime(default=datetime.now)
                foo = String(default='bar')

            @register(Model)
            class Person:
                __db_schema__ = 'test_db_m2m_schema3'

                name = String(primary_key=True)
                addresses = Many2Many(
                    model=Model.Address,
                    join_table="test_db_m2m_schema2.personaddress",
                    remote_columns="id", local_columns="name",
                    m2m_remote_columns='a_id',
                    m2m_local_columns='p_name',
                    many2many="persons")

        registry = self.init_registry(add_in_registry)
        self.assert_rich_many2many_complete_config(registry)

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
        assert personaddress.a_id == address.id
        assert personaddress.p_name == person.name
        assert personaddress.id
        assert personaddress.create_at
        assert personaddress.foo == 'bar'

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
        assert personaddress.a_id == address.id
        assert personaddress.p_name == person.name
        assert personaddress.id
        assert personaddress.create_at
        assert personaddress.foo == 'bar'

    def test_rich_many2many_minimum_config_on_join_model_with_schema(self,
                                                                     db_schema):

        def add_in_registry():

            @register(Model)
            class Address:
                __db_schema__ = 'test_db_m2m_schema'

                id = Integer(primary_key=True)
                street = String()
                zip = String()
                city = String()

            @register(Model)
            class PersonAddress:
                __db_schema__ = 'test_db_m2m_schema'

                id = Integer(primary_key=True)
                a_id = Integer(
                    foreign_key=Model.Address.use('id'), nullable=False)
                p_name = String(
                    foreign_key='Model.Person=>name', nullable=False)
                create_at = DateTime(default=datetime.now)
                foo = String(default='bar')

            @register(Model)
            class Person:
                __db_schema__ = 'test_db_m2m_schema'

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
        assert personaddress.a_id == address.id
        assert personaddress.p_name == person.name
        assert personaddress.id
        assert personaddress.create_at
        assert personaddress.foo == 'bar'

    def test_rich_many2many_minimum_config_on_join_model_with_dif_schema(
        self, db_schema
    ):

        def add_in_registry():

            @register(Model)
            class Address:
                __db_schema__ = 'test_db_m2m_schema1'

                id = Integer(primary_key=True)
                street = String()
                zip = String()
                city = String()

            @register(Model)
            class PersonAddress:
                __db_schema__ = 'test_db_m2m_schema2'

                id = Integer(primary_key=True)
                a_id = Integer(
                    foreign_key=Model.Address.use('id'), nullable=False)
                p_name = String(
                    foreign_key='Model.Person=>name', nullable=False)
                create_at = DateTime(default=datetime.now)
                foo = String(default='bar')

            @register(Model)
            class Person:
                __db_schema__ = 'test_db_m2m_schema3'

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
        assert personaddress.a_id == address.id
        assert personaddress.p_name == person.name
        assert personaddress.id
        assert personaddress.create_at
        assert personaddress.foo == 'bar'

    def test_rich_many2many_minimum_config_on_join_model_with_di_schema2(
        self, db_schema
    ):

        def add_in_registry():

            @register(Model)
            class Address:
                __db_schema__ = 'test_db_m2m_schema1'

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
                __db_schema__ = 'test_db_m2m_schema3'

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
        assert personaddress.a_id == address.id
        assert personaddress.p_name == person.name
        assert personaddress.id
        assert personaddress.create_at
        assert personaddress.foo == 'bar'

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
        assert personaddress.address_id == address.id
        assert personaddress.person_name == person.name
        assert personaddress.id
        assert personaddress.create_at
        assert personaddress.foo == 'bar'

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
        assert personaddress.address_id == address.id
        assert personaddress.person_name == person.name
        assert personaddress.create_at
        assert personaddress.foo == 'bar'

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
        assert personaddress.a_id == address.id
        assert personaddress.p_name == person.name
        assert personaddress.id
        assert personaddress.create_at
        assert personaddress.foo == 'bar'

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

        with pytest.raises(FieldException):
            self.init_registry(add_in_registry)

    def test_rich_many2many_complete_config_on_self_with_schema(self,
                                                                db_schema):

        def add_in_registry():

            @register(Model)
            class TestLink:
                __db_schema__ = 'test_db_m2m_schema'

                id = Integer(primary_key=True)
                t_left = Integer(foreign_key='Model.Test=>id', nullable=False)
                t_right = Integer(foreign_key='Model.Test=>id', nullable=False)
                create_at = DateTime(default=datetime.now)
                foo = String(default='bar')

            @register(Model)
            class Test:
                __db_schema__ = 'test_db_m2m_schema'

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
        assert link.t_left == t2.id
        assert link.t_right == t1.id
        assert link.id
        assert link.create_at
        assert link.foo == 'bar'

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
        assert link.t_left == t2.id
        assert link.t_right == t1.id
        assert link.id
        assert link.create_at
        assert link.foo == 'bar'

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
        assert link.t_left == t2.id
        assert link.t_right == t1.id
        assert link.id
        assert link.create_at
        assert link.foo == 'bar'

    def test_rich_many2many_minimum_config_on_self_with_schema(self, db_schema):

        def add_in_registry():

            @register(Model)
            class TestLink:
                __db_schema__ = 'test_db_m2m_schema'

                id = Integer(primary_key=True)
                t_left = Integer(foreign_key='Model.Test=>id', nullable=False)
                t_right = Integer(foreign_key='Model.Test=>id', nullable=False)
                create_at = DateTime(default=datetime.now)
                foo = String(default='bar')

            @register(Model)
            class Test:
                __db_schema__ = 'test_db_m2m_schema'

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
        assert link.t_left == t2.id
        assert link.t_right == t1.id
        assert link.id
        assert link.create_at
        assert link.foo == 'bar'

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

        with pytest.raises(FieldException):
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

        with pytest.raises(FieldException):
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
        assert link.t_left == t2.id
        assert link.t_right == t1.id
        assert link.id
        assert link.create_at
        assert link.foo == 'bar'

    def test_rich_many2many_minimum_config_on_self_with_many2one(self):

        def add_in_registry():

            @register(Model)
            class TestLink:
                id = Integer(primary_key=True)
                left = Many2One(model='Model.Test', nullable=False)
                right = Many2One(model='Model.Test', nullable=False)
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
        assert link.left_id == t2.id
        assert link.right_id == t1.id
        assert link.id
        assert link.create_at
        assert link.foo == 'bar'

    def test_rich_many2many_minimum_config_on_self_with_pk_many2one_2(self):

        def add_in_registry():

            @register(Model)
            class TestLink:
                left = Many2One(
                    model='Model.Test', nullable=False, primary_key=True)
                right = Many2One(
                    model='Model.Test', nullable=False, primary_key=True)
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
        assert link.left_id == t2.id
        assert link.right_id == t1.id
        assert link.create_at
        assert link.foo == 'bar'

    def test_with_twice_the_same_many2many(self):
        def add_in_registry(**kwargs):

            @register(Model)
            class Address:

                id = Integer(primary_key=True)
                street = String()
                zip = String()
                city = String()

            @register(Model)
            class Person:

                name = String(primary_key=True)
                invoiced_addresses = Many2Many(model=Model.Address)
                delivery_addresses = Many2Many(model=Model.Address)

        registry = self.init_registry(add_in_registry)
        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')
        person = registry.Person.insert(name="Jean-sébastien SUZANNE")

        person.invoiced_addresses.append(address)

        assert person.invoiced_addresses == [address]
        assert person.delivery_addresses == []

    def test_many2many_and_order_list(self):

        def add_in_registry(**kwargs):

            @register(Model)
            class Address:

                id = Integer(primary_key=True)
                street = String()
                zip = String()
                city = String()

            @register(Model)
            class Person:

                name = String(primary_key=True)
                addresses = Many2Many(
                    model=Model.Address,
                    many2many=(
                        "persons",
                        dict(
                            order_by="ModelPerson.name",
                            collection_class=ordering_list('name'),
                        )
                    ),
                    order_by="ModelAddress.city",
                    collection_class=ordering_list('city'),
                )

        registry = self.init_registry(add_in_registry)

        address3 = registry.Address.insert(city='Paris 3')
        address1 = registry.Address.insert(city='Paris 1')
        address4 = registry.Address.insert(city='Paris 4')
        address2 = registry.Address.insert(city='Paris 2')

        person3 = registry.Person.insert(name="test 3")
        person1 = registry.Person.insert(name="test 1")
        person4 = registry.Person.insert(name="test 4")
        person2 = registry.Person.insert(name="test 2")

        person3.addresses.append(address3)
        person1.addresses.append(address1)
        person4.addresses.append(address4)
        person2.addresses.append(address2)

        person1.addresses.append(address4)
        person1.addresses.append(address2)

        address1.persons.append(person4)

        registry.flush()

        assert address1.persons.ordering_attr == 'name'
        assert person1.addresses.ordering_attr == 'city'

        assert address1.persons == [person1, person4]
        assert address2.persons == [person1, person2]
        assert address3.persons == [person3]
        assert address4.persons == [person1, person4]

        person1.refresh()
        assert person1.addresses == [address1, address2, address4]
        assert person2.addresses == [address2]
        assert person3.addresses == [address3]
        person4.refresh()
        assert person4.addresses == [address1, address4]
