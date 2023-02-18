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
from anyblok.column import Integer, String
from anyblok.relationship import One2Many, ordering_list
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


def _complete_one2many(**kwargs):
    primaryjoin = "ModelAddress.id == ModelPerson.address_id"

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address_id = Integer(foreign_key=Model.Address.use('id'))

    @register(Model)  # noqa
    class Address:

        persons = One2Many(model=Model.Person,
                           remote_columns="address_id",
                           primaryjoin=primaryjoin,
                           many2one="address")


def _complete_one2many_with_orderlist(**kwargs):
    primaryjoin = "ModelAddress.id == ModelPerson.address_id"

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address_id = Integer(foreign_key=Model.Address.use('id'))

    @register(Model)  # noqa
    class Address:

        persons = One2Many(model=Model.Person,
                           remote_columns="address_id",
                           primaryjoin=primaryjoin,
                           order_by="ModelPerson.name",
                           collection_class=ordering_list('name'),
                           many2one="address")


def _complete_one2many_with_schema(**kwargs):
    primaryjoin = "ModelAddress.id == ModelPerson.address_id"

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
        address_id = Integer(foreign_key=Model.Address.use('id'))

    @register(Model)  # noqa
    class Address:
        __db_schema__ = 'test_db_m2m_schema'

        persons = One2Many(model=Model.Person,
                           remote_columns="address_id",
                           primaryjoin=primaryjoin,
                           many2one="address")


def _complete_one2many_with_diferent_schema1(**kwargs):
    primaryjoin = "ModelAddress.id == ModelPerson.address_id"

    @register(Model)
    class Address:
        __db_schema__ = 'test_other_db_schema'

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:
        __db_schema__ = 'test_db_m2m_schema'

        name = String(primary_key=True)
        address_id = Integer(foreign_key=Model.Address.use('id'))

    @register(Model)  # noqa
    class Address:
        __db_schema__ = 'test_other_db_schema'

        persons = One2Many(model=Model.Person,
                           remote_columns="address_id",
                           primaryjoin=primaryjoin,
                           many2one="address")


def _complete_one2many_with_diferent_schema2(**kwargs):
    primaryjoin = "ModelAddress.id == ModelPerson.address_id"

    @register(Model)
    class Address:
        __db_schema__ = 'test_other_db_schema'

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address_id = Integer(foreign_key=Model.Address.use('id'))

    @register(Model)  # noqa
    class Address:
        __db_schema__ = 'test_other_db_schema'

        persons = One2Many(model=Model.Person,
                           remote_columns="address_id",
                           primaryjoin=primaryjoin,
                           many2one="address")


@pytest.fixture(
    scope="class",
    params=[
        _complete_one2many,
        _complete_one2many_with_orderlist,
        _complete_one2many_with_schema,
        _complete_one2many_with_diferent_schema1,
        _complete_one2many_with_diferent_schema2,
    ]
)
def registry_complete_one2many(request, bloks_loaded, db_schema):
    reset_db()
    registry = init_registry(request.param)
    request.addfinalizer(registry.close)
    return registry


@pytest.mark.relationship
class TestCompleteOne2Many:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_complete_one2many):
        transaction = registry_complete_one2many.begin_nested()
        request.addfinalizer(transaction.rollback)

    def test_complete_one2many(self, registry_complete_one2many):
        registry = registry_complete_one2many

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")
        address.persons.append(person)

        assert person.address is address

    def test_one2many_autodoc(self, registry_complete_one2many):
        registry = registry_complete_one2many
        registry.loaded_namespaces_first_step['Model.Address'][
            'persons'].autodoc_get_properties()

    def test_complete_one2many_expire_field(self, registry_complete_one2many):
        registry = registry_complete_one2many
        assert ('address',) in registry.expire_attributes[
            'Model.Person']['address_id']
        assert ('address', 'persons') in registry.expire_attributes[
            'Model.Person']['address_id']

    def test_get_field_description(self, registry_complete_one2many):
        registry = registry_complete_one2many
        assert registry.Address.fields_description('persons') == {
            'persons': {
                'id': 'persons',
                'label': 'Persons',
                'local_columns': ['id'],
                'model': 'Model.Person',
                'nullable': True,
                'primary_key': False,
                'remote_columns': ['address_id'],
                'remote_name': 'address',
                'type': 'One2Many'
            },
        }


def _multi_fk_one2many():

    @register(Model)
    class Test:

        id = Integer(primary_key=True, unique=True)
        id2 = String(primary_key=True, unique=True)

    @register(Model)
    class Test2:

        id = Integer(primary_key=True)
        test_id = Integer(foreign_key=Model.Test.use('id'))
        test_id2 = String(foreign_key=Model.Test.use('id2'))

    @register(Model)  # noqa
    class Test:

        test2 = One2Many(model=Model.Test2, many2one="test")


@pytest.fixture(scope="class")
def registry_multi_fk_one2many(request, bloks_loaded):
    reset_db()
    registry = init_registry(_multi_fk_one2many)
    request.addfinalizer(registry.close)
    return registry


@pytest.mark.relationship
class TestMultiFkOne2Many:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_multi_fk_one2many):
        transaction = registry_multi_fk_one2many.begin_nested()
        request.addfinalizer(transaction.rollback)

    def test_with_multi_foreign_key(self, registry_multi_fk_one2many):
        registry = registry_multi_fk_one2many
        t1 = registry.Test.insert(id2="test")
        t2 = registry.Test2.insert(test=t1)
        assert len(t1.test2) == 1
        assert t1.test2[0] is t2

    def test_with_multi_foreign_key_expire_field(
        self, registry_multi_fk_one2many
    ):
        registry = registry_multi_fk_one2many
        assert ('test',) in registry.expire_attributes[
            'Model.Test2']['test_id']
        assert ('test', 'test2') in registry.expire_attributes[
            'Model.Test2']['test_id']
        assert ('test',) in registry.expire_attributes[
            'Model.Test2']['test_id2']
        assert ('test', 'test2') in registry.expire_attributes[
            'Model.Test2']['test_id2']


def _minimum_one2many(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()
        persons = One2Many(model='Model.Person')

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address_id = Integer(foreign_key=Model.Address.use('id'))


def one2many_on_mapper(**kwargs):

    @register(Model, tablename="x")
    class Address:

        id = Integer(primary_key=True, db_column_name="x1")
        street = String(db_column_name="x2")
        zip = String(db_column_name="x3")
        city = String(db_column_name="x4")
        persons = One2Many(model='Model.Person')

    @register(Model, tablename="y")
    class Person:

        name = String(primary_key=True, db_column_name="y1")
        address_id = Integer(foreign_key=Model.Address.use('id'),
                             db_column_name="y2")


def _minimum_one2many_with_schema(**kwargs):

    @register(Model)
    class Address:
        __db_schema__ = 'test_db_m2m_schema'

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()
        persons = One2Many(model='Model.Person')

    @register(Model)
    class Person:
        __db_schema__ = 'test_db_m2m_schema'

        name = String(primary_key=True)
        address_id = Integer(foreign_key=Model.Address.use('id'))


def _minimum_one2many_remote_field_in_mixin(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Mixin)
    class MPerson:
        address_id = Integer(foreign_key=Model.Address.use('id'))

    @register(Model)
    class Person(Mixin.MPerson):

        name = String(primary_key=True)

    @register(Model)  # noqa
    class Address:

        persons = One2Many(model=Model.Person)


def _one2many_with_str_model(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address_id = Integer(foreign_key=Model.Address.use('id'))

    @register(Model)  # noqa
    class Address:

        persons = One2Many(model='Model.Person')


@pytest.mark.relationship
class TestOne2Many:

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

    def test_minimum_one2many(self):
        registry = self.init_registry(_minimum_one2many)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")
        address.persons.append(person)

    def test_minimum_one2many_on_mapper(self):
        registry = self.init_registry(one2many_on_mapper)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")
        address.persons.append(person)

    def test_minimum_one2many_with_schema(self, db_schema):
        registry = self.init_registry(_minimum_one2many_with_schema)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")
        address.persons.append(person)

    def test_minimum_one2many_remote_field_in_mixin(self):
        registry = self.init_registry(_minimum_one2many_remote_field_in_mixin)

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

    def test_same_model_backref(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                parent_id = Integer(foreign_key='Model.Test=>id')
                children = One2Many(model='Model.Test', many2one='parent')

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert()
        t2 = registry.Test.insert(parent=t1)
        assert t1.children[0] is t2
        assert t2.parent is t1

    def test_complet_with_multi_foreign_key(self):

        def add_in_registry():
            primaryjoin = "ModelTest.id == ModelTest2.test_id and "
            primaryjoin += "ModelTest.id2 == ModelTest2.test_id2"

            @register(Model)
            class Test:

                id = Integer(primary_key=True, unique=True)
                id2 = String(primary_key=True, unique=True)

            @register(Model)
            class Test2:

                id = Integer(primary_key=True)
                test_id = Integer(foreign_key=Model.Test.use('id'))
                test_id2 = String(foreign_key=Model.Test.use('id2'))

            @register(Model)  # noqa
            class Test:

                test2 = One2Many(model=Model.Test2,
                                 remote_columns=['test_id', 'test_id2'],
                                 primaryjoin=primaryjoin,
                                 many2one="test")

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert(id2="test")
        t2 = registry.Test2.insert(test=t1)
        assert len(t1.test2) == 1
        assert t1.test2[0] is t2

    def test_with_multi_parallel_foreign_key_auto_detect(self):

        def add_in_registry():

            @register(Model)
            class Address:

                id = Integer(primary_key=True)
                street = String()
                zip = String()
                city = String()

            @register(Model)
            class Person:

                name = String(primary_key=True)
                address_1_id = Integer(foreign_key=Model.Address.use('id'))
                address_2_id = Integer(foreign_key=Model.Address.use('id'))

            @register(Model)  # noqa
            class Address:

                persons = One2Many(model=Model.Person)

        registry = self.init_registry(add_in_registry)
        address_1 = registry.Address.insert()
        address_2 = registry.Address.insert()
        person = registry.Person.insert(
            name='test', address_1_id=address_1.id, address_2_id=address_2.id)
        assert address_1.persons == [person]
        assert address_2.persons == [person]

    def test_with_multi_parallel_foreign_key_with_specific_primaryjoin(self):

        def add_in_registry():
            primaryjoin = (
                "or_("
                "ModelAddress.id == ModelPerson.address_1_id,"
                "ModelAddress.id == ModelPerson.address_2_id"
                ")"
            )

            @register(Model)
            class Address:

                id = Integer(primary_key=True)
                street = String()
                zip = String()
                city = String()

            @register(Model)
            class Person:

                name = String(primary_key=True)
                address_1_id = Integer(foreign_key=Model.Address.use('id'))
                address_2_id = Integer(foreign_key=Model.Address.use('id'))

            @register(Model)  # noqa
            class Address:

                persons = One2Many(model=Model.Person,
                                   primaryjoin=primaryjoin)

        registry = self.init_registry(add_in_registry)
        address_1 = registry.Address.insert()
        address_2 = registry.Address.insert()
        person = registry.Person.insert(
            name='test', address_1_id=address_1.id, address_2_id=address_2.id)
        assert address_1.persons == [person]
        assert address_2.persons == [person]

    def test_order_list(self):

        def add_in_registry():
            primaryjoin = "ModelAddress.id == ModelPerson.address_id"

            @register(Model)
            class Address:

                id = Integer(primary_key=True)
                street = String()
                zip = String()
                city = String()

            @register(Model)
            class Person:

                id = Integer(primary_key=True)
                name = String()
                address_id = Integer(foreign_key=Model.Address.use('id'))

            @register(Model)  # noqa
            class Address:

                persons = One2Many(model=Model.Person,
                                   remote_columns="address_id",
                                   primaryjoin=primaryjoin,
                                   order_by="ModelPerson.name",
                                   collection_class=ordering_list('name'),
                                   many2one="address")

        registry = self.init_registry(add_in_registry)

        address = registry.Address.insert()
        assert address.persons.ordering_attr == 'name'

        p3 = registry.Person.insert(name='test 3', address_id=address.id)
        p1 = registry.Person.insert(name='test 1', address_id=address.id)
        p4 = registry.Person.insert(name='test 4', address_id=address.id)
        p2 = registry.Person.insert(name='test 2', address_id=address.id)
        address.refresh()
        assert address.persons == [p1, p2, p3, p4]
