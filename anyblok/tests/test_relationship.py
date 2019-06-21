# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok.field import FieldException
from anyblok.relationship import RelationShip, RelationShipList
from anyblok import Declarations
from anyblok.column import Integer
from anyblok.relationship import One2Many, Many2One
from .conftest import init_registry_with_bloks


register = Declarations.register
Model = Declarations.Model


class OneRelationShip(RelationShip):
    pass


class OneModel:
    __tablename__ = 'test'
    __registry_name__ = 'One.Model'


class MockRegistry:

    InstrumentedList = []


class TestRelationShip:

    def test_forbid_instance(self):
        with pytest.raises(FieldException):
            RelationShip(model=OneModel)

    def test_must_have_a_model(self):
        OneRelationShip(model=OneModel)
        with pytest.raises(FieldException):
            OneRelationShip()


class List(RelationShipList, list):
    def relationship_field_append_value(*a, **kw):
        return True

    def relationship_field_remove_value(*a, **kw):
        return True


class TestRelationShipList:

    def test_append(self):
        list_ = List()
        list_.append(1)
        assert list_ == [1]

    def test_extend(self):
        list_ = List()
        list_.extend([1, 2])
        assert list_ == [1, 2]

    def test_insert(self):
        list_ = List()
        list_.insert(0, 1)
        assert list_ == [1]
        list_.insert(0, 2)
        assert list_ == [2, 1]

    def test_pop(self):
        list_ = List()
        list_.extend([1, 2])
        assert list_ == [1, 2]
        list_.pop(0)
        assert list_ == [2]
        list_.pop(0)
        assert list_ == []

    def test_remove(self):
        list_ = List()
        list_.extend([3, 2, 1])
        assert list_ == [3, 2, 1]
        list_.remove(1)
        assert list_ == [3, 2]

    def test_clear(self):
        list_ = List()
        list_.extend([3, 2, 1])
        assert list_ == [3, 2, 1]
        list_.clear()
        assert list_ == []


def multi_parallel_foreign_key_with_definition():

    @register(Model)
    class Address:

        id = Integer(primary_key=True)

    @register(Model)
    class Person:

        id = Integer(primary_key=True)
        address_1_id = Integer(foreign_key=Model.Address.use('id'))
        address_2_id = Integer(foreign_key=Model.Address.use('id'))
        address_1 = Many2One(model=Model.Address,
                             column_names=['address_1_id'])
        address_2 = Many2One(model=Model.Address,
                             column_names=['address_2_id'])

    @register(Model)  # noqa
    class Address:

        persons = One2Many(model=Model.Person)


def multi_parallel_foreign_key_auto_detect():

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        persons = One2Many(model='Model.Person')

    @register(Model)
    class Person:

        id = Integer(primary_key=True)
        address_1 = Many2One(model=Model.Address)
        address_2 = Many2One(model=Model.Address)


@pytest.fixture(
    scope="class",
    params=[
        multi_parallel_foreign_key_with_definition,
        multi_parallel_foreign_key_auto_detect,
    ]
)
def registry_relationship_multiple_foreign_keys(request, bloks_loaded):
    registry = init_registry_with_bloks(
        [], request.param)
    request.addfinalizer(registry.close)
    return registry


class TestComplexeRelationShipCase:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_relationship_multiple_foreign_keys):
        transaction = registry_relationship_multiple_foreign_keys.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_with_multi_parallel_foreign_key_with_definition(
        self, registry_relationship_multiple_foreign_keys
    ):

        registry = registry_relationship_multiple_foreign_keys
        address_1 = registry.Address.insert()
        address_2 = registry.Address.insert()
        person = registry.Person.insert(
            address_1=address_1, address_2=address_2)
        assert address_1.persons == [person]
        assert address_2.persons == [person]
