# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok.column import Integer, String, Selection
from anyblok.relationship import Many2One, One2One, Many2Many, One2Many
from anyblok.declarations import Declarations
from anyblok.bloks.anyblok_core.exceptions import SqlBaseException
from sqlalchemy.orm.exc import NoResultFound
from .conftest import init_registry


Model = Declarations.Model
register = Declarations.register


def declare_model():
    from anyblok import Declarations
    Model = Declarations.Model

    @Declarations.register(Model)
    class Test:
        id = Integer(primary_key=True)
        id2 = Integer()
        select = Selection(
            selections=[('key', 'value'), ('key2', 'value2')],
            default='key')


@pytest.fixture(scope="class")
def registry_declare_model(request, bloks_loaded):
    registry = init_registry(declare_model)
    request.addfinalizer(registry.close)
    return registry


class TestCoreSQLBase:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_declare_model):
        transaction = registry_declare_model.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_insert_and_query(self, registry_declare_model):
        registry = registry_declare_model
        t1 = registry.Test.insert(id2=1)
        assert registry.Test.query().first() == t1

    def test_insert_and_select(self, registry_declare_model):
        Test = registry_declare_model.Test
        t1 = Test.insert(id2=1)
        assert Test.execute_sql_statement(
            Test.select_sql_statement()).scalars().first() == t1

    def test_query_one_is_more_explicite(self, registry_declare_model):
        registry = registry_declare_model
        with pytest.raises(NoResultFound) as exc:
            registry.Test.query().one()

        assert (
            str(exc._excinfo[1]) ==
            "On Model 'Model.Test': No row was found when one was required")

    def test_query_dictone_is_more_explicite(self, registry_declare_model):
        registry = registry_declare_model
        with pytest.raises(NoResultFound) as exc:
            registry.Test.query().dictone()

        assert (
            str(exc._excinfo[1]) ==
            "On Model 'Model.Test': No row was found when one was required")

    def test_multi_insert(self, registry_declare_model):
        registry = registry_declare_model
        nb_value = 3
        registry.Test.multi_insert(*[{'id2': x} for x in range(nb_value)])
        assert registry.Test.query().count() == nb_value
        for x in range(nb_value):
            assert registry.Test.query().filter(
                registry.Test.id2 == x).count() == 1

    def test_classmethod_delete(self, registry_declare_model):
        registry = registry_declare_model
        nb_value = 3
        Test = registry.Test
        Test.multi_insert(*[{'id2': x} for x in range(nb_value)])
        assert Test.query().count() == nb_value
        id2 = 1
        Test.execute_sql_statement(
            Test.delete_sql_statement().where(Test.id2 == id2))
        assert registry.Test.query().count() == nb_value - 1
        assert registry.Test.query().filter(
            registry.Test.id2 != id2).count() == nb_value - 1

    def test_delete_by_query(self, registry_declare_model):
        registry = registry_declare_model
        nb_value = 3
        registry.Test.multi_insert(*[{'id2': x} for x in range(nb_value)])
        assert registry.Test.query().count() == nb_value
        t = registry.Test.query().first()
        id2 = t.id2
        t.delete(byquery=True)
        assert registry.Test.query().count() == nb_value - 1
        assert registry.Test.query().filter(
            registry.Test.id2 != id2).count() == nb_value - 1

    def test_delete(self, registry_declare_model):
        registry = registry_declare_model
        nb_value = 3
        registry.Test.multi_insert(*[{'id2': x} for x in range(nb_value)])
        assert registry.Test.query().count() == nb_value
        t = registry.Test.query().first()
        id2 = t.id2
        t.delete()
        assert registry.Test.query().count() == nb_value - 1
        assert registry.Test.query().filter(
            registry.Test.id2 != id2).count() == nb_value - 1

    def test_delete_with_get(self, registry_declare_model):
        registry = registry_declare_model
        nb_value = 3
        registry.Test.multi_insert(*[{'id2': x} for x in range(nb_value)])
        assert registry.Test.query().count() == nb_value
        t = registry.Test.query().first()
        assert registry.Test.query().get(t.id) is t
        t.delete()
        assert registry.Test.query().get(t.id) is None

    def test_expire(self, registry_declare_model):
        registry = registry_declare_model
        t = registry.Test.insert(id2=2)
        assert t.id2 == 2
        t.id2 = 3
        assert t.id2 == 3
        t.expire()
        assert t.id2 == 2

    def test_refresh(self, registry_declare_model):
        registry = registry_declare_model
        t = registry.Test.insert(id2=2)
        assert t.id2 == 2
        t.id2 = 3
        assert t.id2 == 3
        t.refresh()
        assert t.id2 == 2

    def test_modified(self, registry_declare_model):
        registry = registry_declare_model
        t = registry.Test.insert(id2=2)
        assert 'id2' not in t.get_modified_fields()
        t.flag_modified('id2')
        assert 'id2' in t.get_modified_fields()

    def test_classmethod_update(self, registry_declare_model):
        registry = registry_declare_model
        nb_value = 3
        Test = registry.Test
        Test.multi_insert(*[{'id2': x} for x in range(nb_value)])
        t = Test.query().filter_by(id2=1).one()
        assert Test.execute_sql_statement(
            Test.update_sql_statement().where(Test.id2 == 1).values(id2=100)
        ).rowcount == 1
        assert registry.Test.query().filter(
            registry.Test.id2 == 100).first() == t

    def test_update(self, registry_declare_model):
        registry = registry_declare_model
        nb_value = 3
        registry.Test.multi_insert(*[{'id2': x} for x in range(nb_value)])
        t = registry.Test.query().first()
        assert t.update(id2=100) == 1
        assert registry.Test.query().filter(
            registry.Test.id2 == 100).first() == t

    def test_update_byquery(self, registry_declare_model):
        registry = registry_declare_model
        nb_value = 3
        registry.Test.multi_insert(*[{'id2': x} for x in range(nb_value)])
        t = registry.Test.query().first()
        assert t.update(byquery=True, id2=100) == 1
        assert registry.Test.query().filter(
            registry.Test.id2 == 100).first() == t

    def test_get_primary_keys(self, registry_declare_model):
        registry = registry_declare_model
        assert registry.Test.get_primary_keys() == ['id']

    def test_to_and_from_primary_keys(self, registry_declare_model):
        registry = registry_declare_model
        nb_value = 3
        registry.Test.multi_insert(*[{'id2': x} for x in range(nb_value)])
        t = registry.Test.query().first()
        assert t.to_primary_keys() == {'id': t.id}
        assert registry.Test.from_primary_keys(id=t.id) == t

    def test_expire_with_column_selection(self, registry_declare_model):
        registry = registry_declare_model
        t = registry.Test.insert()
        t.select = 'key2'
        t.expire('select')
        assert t.select == 'key'

    def test_with_subquery(self, registry_declare_model):
        registry = registry_declare_model
        Test = registry.Test
        subquery = Test.query(Test.id2).subquery()
        assert subquery.c.keys() == ['id2']


def declare_model_with_m2o():

    @register(Model)
    class Test:
        id = Integer(primary_key=True)
        name = String()

    @register(Model)
    class Test2:
        id = Integer(primary_key=True)
        name = String()
        test = Many2One(model=Model.Test, one2many="test2")


@pytest.fixture(scope="class")
def registry_declare_model_with_m2o(request, bloks_loaded):
    registry = init_registry(declare_model_with_m2o)
    request.addfinalizer(registry.close)
    return registry


class TestCoreSQLBaseM2O:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_declare_model_with_m2o):
        transaction = registry_declare_model_with_m2o.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_delete_entry_added_in_relationship(
        self, registry_declare_model_with_m2o
    ):
        registry = registry_declare_model_with_m2o
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        assert len(t1.test2) == 1
        t2.delete()
        assert len(t1.test2) == 0

    def test_with_subquery_1(self, registry_declare_model_with_m2o):
        registry = registry_declare_model_with_m2o
        Test2 = registry.Test2
        subquery = Test2.query(Test2.test).subquery()
        assert subquery.c.keys() == ['test']

    def test_with_subquery_2(self, registry_declare_model_with_m2o):
        registry = registry_declare_model_with_m2o
        Test2 = registry.Test2
        subquery = Test2.query(Test2.test_id).subquery()
        assert subquery.c.keys() == ['test_id']

    def test_to_dict_m2o_with_pks(self, registry_declare_model_with_m2o):
        registry = registry_declare_model_with_m2o
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        assert t1.to_dict('name') == {'name': 't1'}
        assert t2.to_dict('name') == {'name': 't2'}
        assert t2.to_dict('name', 'test') == {
            'name': 't2', 'test': {'id': t1.id}}

    def test_to_dict_o2m_with_pks(self, registry_declare_model_with_m2o):
        registry = registry_declare_model_with_m2o
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        assert t1.to_dict('name', 'test2') == {
            'name': 't1', 'test2': [{'id': t2.id}]}

    def test_to_dict_m2o_with_column(self, registry_declare_model_with_m2o):
        registry = registry_declare_model_with_m2o
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        assert t2.to_dict('name', ('test', ('name',))) == {
            'name': 't2', 'test': {'name': 't1'}}

    def test_to_dict_o2m_with_column(self, registry_declare_model_with_m2o):
        registry = registry_declare_model_with_m2o
        t1 = registry.Test.insert(name='t1')
        registry.Test2.insert(name='t2', test=t1)
        assert t1.to_dict('name', ('test2', ('name',))) == {
            'name': 't1', 'test2': [{'name': 't2'}]}

    def test_to_dict_m2o_with_all_columns(
        self, registry_declare_model_with_m2o
    ):
        registry = registry_declare_model_with_m2o
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        assert t2.to_dict('name', ('test',)) == {
            'name': 't2', 'test': {'name': 't1',
                                   'id': t1.id,
                                   'test2': [{'id': t2.id}]}}
        assert t2.to_dict('name', ('test', None)) == {
            'name': 't2', 'test': {'name': 't1',
                                   'id': t1.id,
                                   'test2': [{'id': t2.id}]}}
        assert t2.to_dict('name', ('test', ())) == {
            'name': 't2', 'test': {'name': 't1',
                                   'id': t1.id,
                                   'test2': [{'id': t2.id}]}}

    def test_to_dict_o2m_with_all_columns(
        self, registry_declare_model_with_m2o
    ):
        registry = registry_declare_model_with_m2o
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        assert t1.to_dict('name', ('test2',)) == {
            'name': 't1', 'test2': [{'name': 't2',
                                     'id': t2.id,
                                     'test_id': t1.id,
                                     'test': {'id': t1.id}}]}
        assert t1.to_dict('name', ('test2', None)) == {
            'name': 't1', 'test2': [{'name': 't2',
                                     'id': t2.id,
                                     'test_id': t1.id,
                                     'test': {'id': t1.id}}]}
        assert t1.to_dict('name', ('test2', ())) == {
            'name': 't1', 'test2': [{'name': 't2',
                                     'id': t2.id,
                                     'test_id': t1.id,
                                     'test': {'id': t1.id}}]}

    def test_bad_definition_of_relation(self, registry_declare_model_with_m2o):
        registry = registry_declare_model_with_m2o
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        with pytest.raises(SqlBaseException):
            t2.to_dict('name', ('test', 'name'))

    def test_bad_definition_of_relation2(self, registry_declare_model_with_m2o):
        registry = registry_declare_model_with_m2o
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        with pytest.raises(SqlBaseException):
            t2.to_dict('name', ('test', ('name',), ()))

    def test_bad_definition_of_relation3(self, registry_declare_model_with_m2o):
        registry = registry_declare_model_with_m2o
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        with pytest.raises(SqlBaseException):
            t2.to_dict('name', ())

    def test_refresh_update_m2o(self, registry_declare_model_with_m2o):
        registry = registry_declare_model_with_m2o
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        t3 = registry.Test.insert(name='t3')
        assert t1.test2 == [t2]
        assert t2.test is t1
        assert t2.test_id == t1.id
        assert t3.test2 == []
        t2.test = t3
        assert t1.test2 == []
        assert t2.test is t3
        assert t2.test_id is t3.id
        assert t3.test2 == [t2]
        t2.test = None
        assert t1.test2 == []
        assert t2.test is None
        assert t2.test_id is None
        assert t3.test2 == []

    def test_refresh_update_m2o_2(self, registry_declare_model_with_m2o):
        registry = registry_declare_model_with_m2o
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        t3 = registry.Test.insert(name='t3')
        assert t1.test2 == [t2]
        assert t2.test is t1
        assert t2.test_id == t1.id
        assert t3.test2 == []
        t2.test_id = t3.id
        assert t1.test2 == []
        assert t2.test is t3
        assert t2.test_id == t3.id
        assert t3.test2 == [t2]

    def test_refresh_update_m2o_3(self, registry_declare_model_with_m2o):
        registry = registry_declare_model_with_m2o
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        t3 = registry.Test.insert(name='t3')
        assert t1.test2 == [t2]
        assert t2.test is t1
        assert t2.test_id == t1.id
        assert t3.test2 == []
        t3.test2.append(t2)
        assert t1.test2 == []
        assert t2.test is t3
        assert t2.test_id == t3.id
        assert t3.test2 == [t2]
        t3.test2.remove(t2)
        assert t1.test2 == []
        assert t2.test is None
        assert t2.test_id is None
        assert t3.test2 == []

    def test_find_relationship_by_relationship(
        self, registry_declare_model_with_m2o
    ):
        registry = registry_declare_model_with_m2o
        fields = registry.Test2.find_relationship('test')
        assert 'test' in fields
        assert 'test_id' in fields

    def test_find_relationship_by_column(self, registry_declare_model_with_m2o):
        registry = registry_declare_model_with_m2o
        fields = registry.Test2.find_relationship('test_id')
        assert 'test' in fields
        assert 'test_id' in fields

    def test_getFieldType(self, registry_declare_model_with_m2o):
        registry = registry_declare_model_with_m2o
        assert registry.Test.getFieldType('id') == 'Integer'
        assert registry.Test.getFieldType('name') == 'String'
        assert registry.Test2.getFieldType('id') == 'Integer'
        assert registry.Test2.getFieldType('name') == 'String'
        assert registry.Test2.getFieldType('test') == 'Many2One'
        assert registry.Test.getFieldType('test2') == 'One2Many'

    def test_repr_m2o(self, registry_declare_model_with_m2o):
        registry = registry_declare_model_with_m2o
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        wanted = (
            "<Model.Test2(id=%s, name='t2', test=<Model.Test(id=%s)>"
            ", test_id=%s)>" % (t2.id, t1.id, t1.id))
        assert repr(t2) == wanted


def declare_model_with_o2o():
    @register(Model)
    class Test:
        id = Integer(primary_key=True)
        name = String()

    @register(Model)
    class Test2:
        id = Integer(primary_key=True)
        name = String()
        test = One2One(model=Model.Test, backref='test2')


@pytest.fixture(scope="class")
def registry_declare_model_with_o2o(request, bloks_loaded):
    registry = init_registry(declare_model_with_o2o)
    request.addfinalizer(registry.close)
    return registry


class TestCoreSQLBaseo2O:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_declare_model_with_o2o):
        transaction = registry_declare_model_with_o2o.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_to_dict_o2o_with_pks(self, registry_declare_model_with_o2o):
        registry = registry_declare_model_with_o2o
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        assert t1.to_dict('name') == {'name': 't1'}
        assert t2.to_dict('name') == {'name': 't2'}
        assert t2.to_dict('name', 'test') == {
            'name': 't2', 'test': {'id': t1.id}}
        assert t1.to_dict('name', 'test2') == {
            'name': 't1', 'test2': {'id': t2.id}}

    def test_to_dict_o2o_with_column(self, registry_declare_model_with_o2o):
        registry = registry_declare_model_with_o2o
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        assert t2.to_dict('name', ('test', ('name',))) == {
            'name': 't2', 'test': {'name': 't1'}}
        assert t1.to_dict('name', ('test2', ('name',))) == {
            'name': 't1', 'test2': {'name': 't2'}}

    def test_to_dict_o2o_with_all_columns(
        self, registry_declare_model_with_o2o
    ):
        registry = registry_declare_model_with_o2o
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        assert t2.to_dict('name', ('test',)) == {
            'name': 't2', 'test': {'name': 't1',
                                   'id': t1.id,
                                   'test2': {'id': t2.id}}}
        assert t2.to_dict('name', ('test', None)) == {
            'name': 't2', 'test': {'name': 't1',
                                   'id': t1.id,
                                   'test2': {'id': t2.id}}}
        assert t2.to_dict('name', ('test', ())) == {
            'name': 't2', 'test': {'name': 't1',
                                   'id': t1.id,
                                   'test2': {'id': t2.id}}}

    def test_refresh_update_o2o(self, registry_declare_model_with_o2o):
        registry = registry_declare_model_with_o2o
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        t3 = registry.Test.insert(name='t3')
        assert t1.test2 is t2
        assert t2.test is t1
        assert t2.test_id is t1.id
        assert t3.test2 is None
        t2.test = t3
        assert t1.test2 is None
        assert t2.test is t3
        assert t2.test_id == t3.id
        assert t3.test2 is t2

    def test_refresh_update_o2o_2(self, registry_declare_model_with_o2o):
        registry = registry_declare_model_with_o2o
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        t3 = registry.Test.insert(name='t3')
        assert t1.test2 is t2
        assert t2.test is t1
        assert t3.test2 is None
        t3.test2 = t2
        assert t1.test2 is None
        assert t2.test is t3
        assert t2.test_id is t3.id
        assert t3.test2 is t2

    def test_refresh_update_o2o_3(self, registry_declare_model_with_o2o):
        registry = registry_declare_model_with_o2o
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        t3 = registry.Test.insert(name='t3')
        assert t1.test2 is t2
        assert t2.test is t1
        assert t2.test_id == t1.id
        assert t3.test2 is None
        t2.test_id = t3.id
        assert t1.test2 is None
        assert t2.test is t3
        assert t2.test_id == t3.id
        assert t3.test2 is t2

    def test_repr_o2o(self, registry_declare_model_with_o2o):
        registry = registry_declare_model_with_o2o
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        wanted = (
            "<Model.Test2(id=%s, name='t2', test=<Model.Test(id=%s)>"
            ", test_id=%s)>" % (t2.id, t1.id, t1.id))
        assert repr(t2) == wanted


def declare_model_with_o2m():

    @register(Model)
    class Test:
        id = Integer(primary_key=True)
        name = String()

    @register(Model)
    class Test2:
        id = Integer(primary_key=True)
        name = String()
        test_id = Integer(foreign_key=Model.Test.use('id'))

    @register(Model)  # noqa
    class Test:
        test2 = One2Many(model=Model.Test2, many2one="test")


@pytest.fixture(scope="class")
def registry_declare_model_with_o2m(request, bloks_loaded):
    registry = init_registry(declare_model_with_o2m)
    request.addfinalizer(registry.close)
    return registry


class TestCoreSQLBaseo2m:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_declare_model_with_o2m):
        transaction = registry_declare_model_with_o2m.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_refresh_update_o2m(self, registry_declare_model_with_o2m):
        registry = registry_declare_model_with_o2m
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        t3 = registry.Test2.insert(name='t3')
        assert t1.test2 == [t2]
        assert t2.test is t1
        assert t3.test is None
        t1.test2.append(t3)
        assert t2 in t1.test2
        assert t3 in t1.test2
        assert t2.test is t1
        assert t3.test is t1
        t1.test2.remove(t2)
        assert t1.test2 == [t3]
        assert t2.test is None
        assert t3.test is t1

    def test_refresh_update_o2m_2(self, registry_declare_model_with_o2m):
        registry = registry_declare_model_with_o2m
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        t3 = registry.Test2.insert(name='t3')
        assert t1.test2 == [t2]
        assert t2.test is t1
        assert t3.test is None
        t3.test = t1
        assert t2 in t1.test2
        assert t3 in t1.test2
        assert t2.test is t1
        assert t3.test is t1
        assert t3.test_id is t1.id

    def test_refresh_update_o2m_3(self, registry_declare_model_with_o2m):
        registry = registry_declare_model_with_o2m
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        t3 = registry.Test2.insert(name='t3')
        assert t1.test2 == [t2]
        assert t2.test is t1
        assert t3.test is None
        t3.test_id = t1.id
        assert t2 in t1.test2
        assert t3 in t1.test2
        assert t2.test is t1
        assert t3.test is t1

    def test_repr_o2m(self, registry_declare_model_with_o2m):
        registry = registry_declare_model_with_o2m
        t1 = registry.Test.insert(name='t1')
        registry.Test2.insert(name='t2', test=t1)
        wanted = "<Model.Test(id=%s, name='t1', test2=<not loaded>)>" % t1.id
        assert repr(t1) == wanted


def declare_model_with_m2m():
    @register(Model)
    class Test:
        id = Integer(primary_key=True)
        name = String()

    @register(Model)
    class Test2:
        id = Integer(primary_key=True)
        name = String()
        test = Many2Many(model=Model.Test, many2many='test2')


@pytest.fixture(scope="class")
def registry_declare_model_with_m2m(request, bloks_loaded):
    registry = init_registry(declare_model_with_m2m)
    request.addfinalizer(registry.close)
    return registry


class TestCoreSQLBasem2m:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_declare_model_with_m2m):
        transaction = registry_declare_model_with_m2m.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_to_dict_m2m_with_pks(self, registry_declare_model_with_m2m):
        registry = registry_declare_model_with_m2m
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2')
        t2.test.append(t1)
        assert t1.to_dict('name') == {'name': 't1'}
        assert t2.to_dict('name') == {'name': 't2'}
        assert t2.to_dict('name', 'test') == {
            'name': 't2', 'test': [{'id': t1.id}]}
        assert t1.to_dict('name', 'test2') == {
            'name': 't1', 'test2': [{'id': t2.id}]}

    def test_to_dict_m2m_with_column(self, registry_declare_model_with_m2m):
        registry = registry_declare_model_with_m2m
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2')
        t2.test.append(t1)
        assert t2.to_dict('name', ('test', ('name',))) == {
            'name': 't2', 'test': [{'name': 't1'}]}
        assert t1.to_dict('name', ('test2', ('name',))) == {
            'name': 't1', 'test2': [{'name': 't2'}]}

    def test_to_dict_m2m_with_all_columns(
        self, registry_declare_model_with_m2m
    ):
        registry = registry_declare_model_with_m2m
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2')
        t2.test.append(t1)
        assert t2.to_dict('name', ('test',)) == {
            'name': 't2', 'test': [{'name': 't1',
                                    'id': t1.id,
                                    'test2': [{'id': t2.id}]}]}
        assert t2.to_dict('name', ('test', None)) == {
            'name': 't2', 'test': [{'name': 't1',
                                    'id': t1.id,
                                    'test2': [{'id': t2.id}]}]}
        assert t2.to_dict('name', ('test', ())) == {
            'name': 't2', 'test': [{'name': 't1',
                                    'id': t1.id,
                                    'test2': [{'id': t2.id}]}]}
        assert t1.to_dict('name', ('test2',)) == {
            'name': 't1', 'test2': [{'name': 't2',
                                     'id': t2.id,
                                     'test': [{'id': t1.id}]}]}
        assert t1.to_dict('name', ('test2', None)) == {
            'name': 't1', 'test2': [{'name': 't2',
                                     'id': t2.id,
                                     'test': [{'id': t1.id}]}]}
        assert t1.to_dict('name', ('test2', ())) == {
            'name': 't1', 'test2': [{'name': 't2',
                                     'id': t2.id,
                                     'test': [{'id': t1.id}]}]}

    def test_refresh_update_m2m(self, registry_declare_model_with_m2m):
        registry = registry_declare_model_with_m2m
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2')
        t3 = registry.Test2.insert(name='t3')
        assert t1.test2 == []
        assert t2.test == []
        assert t3.test == []
        t1.test2.append(t2)
        assert t1.test2 == [t2]
        assert t2.test == [t1]
        assert t3.test == []
        t1.test2.append(t3)
        assert t2 in t1.test2
        assert t3 in t1.test2
        assert t2.test == [t1]
        assert t3.test == [t1]
        t1.test2.remove(t2)
        assert t1.test2 == [t3]
        assert t2.test == []
        assert t3.test == [t1]

    def test_refresh_update_m2m_2(self, registry_declare_model_with_m2m):
        registry = registry_declare_model_with_m2m
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2')
        t3 = registry.Test2.insert(name='t3')
        assert t1.test2 == []
        assert t2.test == []
        assert t3.test == []
        t2.test.append(t1)
        assert t1.test2 == [t2]
        assert t2.test == [t1]
        assert t3.test == []
        t3.test.append(t1)
        assert t2 in t1.test2
        assert t3 in t1.test2
        assert t2.test == [t1]
        assert t3.test == [t1]
        t2.test.remove(t1)
        assert t1.test2 == [t3]
        assert t2.test == []
        assert t3.test == [t1]

    def test_repr_m2m(self, registry_declare_model_with_m2m):
        registry = registry_declare_model_with_m2m
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2')
        t2.test.append(t1)
        wanted = (
            "<Model.Test2(id=%s, name='t2', test=<Model.Test len(1)>)>" % t2.id
        )
        assert repr(t2) == wanted
