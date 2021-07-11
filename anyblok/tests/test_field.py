# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok.field import Field, FieldException, Function, JsonRelated
from anyblok.column import Integer, String, Json
from anyblok import Declarations
from sqlalchemy import func, types
from .conftest import init_registry
from anyblok.testing import sgdb_in


Model = Declarations.Model
register = Declarations.register


class OneField(Field):
    pass


class TestField:

    def test_forbid_instance(self):
        with pytest.raises(FieldException):
            Field()

    def test_without_label(self):
        field = OneField()
        field.get_sqlalchemy_mapping(None, None, 'a_field', None)
        assert field.label == 'A field'


def define_field_function():

    @register(Model)
    class Test:

        id = Integer(primary_key=True)
        first_name = String()
        last_name = String()
        name = Function(fget='fget', fset='fset', fdel='fdel',
                        fexpr='fexpr')

        def fget(self):
            return '{0} {1}'.format(self.first_name, self.last_name)

        def fset(self, value):
            self.first_name, self.last_name = value.split(' ', 1)

        def fdel(self):
            self.first_name = self.last_name = None

        @classmethod
        def fexpr(cls):
            return func.concat(cls.first_name, ' ', cls.last_name)


@pytest.fixture(scope="class")
def registry_field_function(request, bloks_loaded):
    registry = init_registry(define_field_function)
    request.addfinalizer(registry.close)
    return registry


@pytest.mark.field
class TestFieldFunction:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_field_function):
        transaction = registry_field_function.begin_nested()
        request.addfinalizer(transaction.rollback)

    def test_field_function_fget(self, registry_field_function):
        registry = registry_field_function
        t = registry.Test.insert(first_name='Jean-Sebastien',
                                 last_name='SUZANNE')
        assert t.name == 'Jean-Sebastien SUZANNE'
        t = registry.Test.query().first()
        assert t.name == 'Jean-Sebastien SUZANNE'

    def test_field_function_fdel(self, registry_field_function):
        registry = registry_field_function
        t = registry.Test.insert(first_name='jean-sebastien',
                                 last_name='suzanne')
        del t.name
        assert t.first_name is None
        assert t.last_name is None

    def test_field_function_fexpr(self, registry_field_function):
        registry = registry_field_function
        registry.Test.insert(first_name='Jean-Sebastien',
                             last_name='SUZANNE')
        t = registry.Test.query().filter(
            registry.Test.name == 'Jean-Sebastien SUZANNE').first()
        assert t.name == 'Jean-Sebastien SUZANNE'

    def test_with_subquery(self, registry_field_function):
        registry = registry_field_function
        Test = registry.Test
        subquery = Test.query(Test.name).subquery()
        assert subquery.c.keys() == ['name']


def define_field_json_related():

    @register(Model)
    class Test:

        id = Integer(primary_key=True)
        properties = Json()
        name = JsonRelated(json_column='properties', keys=['name'])


@pytest.fixture(scope="class")
def registry_json_related(request, bloks_loaded):
    registry = init_registry(define_field_json_related)
    request.addfinalizer(registry.close)
    return registry


@pytest.mark.skipif(sgdb_in(['MariaDB']),
                    reason='JSON is not existing in this SGDB')
@pytest.mark.field
class TestJsonRelated:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_json_related):
        transaction = registry_json_related.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    @pytest.mark.skipif(sgdb_in(['MariaDB', 'MsSQL']),
                        reason='JSON is not existing in this SGDB')
    def test_field_json_related_hasattr(self, registry_json_related):
        registry = registry_json_related
        registry.Test.name

    def test_field_json_related_autodoc(self, registry_json_related):
        registry = registry_json_related
        registry.loaded_namespaces_first_step['Model.Test'][
            'name'].autodoc_get_properties()

    def test_field_json_related_get_1(self, registry_json_related):
        registry = registry_json_related
        t = registry.Test.insert()
        assert t.name is None

    def test_field_json_related_get_2(self, registry_json_related):
        registry = registry_json_related
        t = registry.Test.insert(properties={})
        assert t.name is None

    def test_field_json_related_get_3(self, registry_json_related):
        registry = registry_json_related
        t = registry.Test.insert(properties={'name': 'jssuzanne'})
        assert t.name == 'jssuzanne'

    def test_field_json_related_del_1(self, registry_json_related):
        registry = registry_json_related
        t = registry.Test.insert(properties={'name': 'jssuzanne'})
        del t.name
        assert t.name is None
        assert t.properties == {'name': None}

    def test_field_json_related_set_1(self, registry_json_related):
        registry = registry_json_related
        t = registry.Test.insert()
        t.name = 'jssuzanne'
        assert t.properties == {'name': 'jssuzanne'}

    def test_field_json_related_set_2(self, registry_json_related):
        registry = registry_json_related
        t = registry.Test.insert(properties={})
        t.name = 'jssuzanne'
        assert t.properties == {'name': 'jssuzanne'}

    def test_field_json_related_set_3(self, registry_json_related):
        registry = registry_json_related
        t = registry.Test.insert(properties={'name': 'other'})
        t.name = 'jssuzanne'
        assert t.properties == {'name': 'jssuzanne'}

    @pytest.mark.skipif(sgdb_in(['MariaDB', 'MsSQL']),
                        reason='JSON is not existing in this SGDB')
    def test_field_json_related_exp_1(self, registry_json_related):
        registry = registry_json_related
        Test = registry.Test
        Test.insert()
        query = registry.Test.query().filter(
            Test.name.cast(types.String) == '"jssuzanne"')
        assert not (query.count())

    @pytest.mark.skipif(sgdb_in(['MariaDB', 'MsSQL']),
                        reason='JSON is not existing in this SGDB')
    def test_field_json_related_exp_2(self, registry_json_related):
        registry = registry_json_related
        Test = registry.Test
        Test.insert(properties={})
        query = registry.Test.query().filter(
            Test.name.cast(types.String) == '"jssuzanne"')
        assert not (query.count())

    @pytest.mark.skipif(sgdb_in(['MariaDB', 'MsSQL']),
                        reason='JSON is not existing in this SGDB')
    def test_field_json_related_exp_3(self, registry_json_related):
        registry = registry_json_related
        Test = registry.Test
        Test.insert(properties={'name': 'jssuzanne'})
        query = registry.Test.query().filter(
            Test.name.cast(types.String) == '"jssuzanne"')
        assert query.count()

    def test_with_subquery(self, registry_json_related):
        registry = registry_json_related
        Test = registry.Test
        subquery = Test.query(Test.name).subquery()
        assert subquery.c.keys() == ['name']


def define_field_json_related2():

    @register(Model)
    class Test:

        id = Integer(primary_key=True)
        properties = Json()
        name = JsonRelated(json_column='properties', keys=['sub', 'name'])


@pytest.fixture(scope="class")
def registry_json_related2(request, bloks_loaded):
    registry = init_registry(define_field_json_related2)
    request.addfinalizer(registry.close)
    return registry


@pytest.mark.skipif(sgdb_in(['MariaDB']),
                    reason='JSON is not existing in this SGDB')
@pytest.mark.field
class TestJsonRelated2:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_json_related2):
        transaction = registry_json_related2.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_field_json_related_get_4(self, registry_json_related2):
        registry = registry_json_related2
        t = registry.Test.insert(
            properties={'sub': {'name': 'jssuzanne'}})
        assert t.name == 'jssuzanne'

    def test_field_json_related_del_2(self, registry_json_related2):
        registry = registry_json_related2
        t = registry.Test.insert()
        del t.name
        assert t.name is None
        assert t.properties == {'sub': {'name': None}}

    def test_field_json_related_set_4(self, registry_json_related2):
        registry = registry_json_related2
        t = registry.Test.insert(properties={'sub': {'name': 'other'}})
        t.name = 'jssuzanne'
        assert t.properties == {'sub': {'name': 'jssuzanne'}}

    @pytest.mark.skipif(sgdb_in(['MariaDB', 'MsSQL']),
                        reason='JSON is not existing in this SGDB')
    def test_field_json_related_exp_4(self, registry_json_related2):
        registry = registry_json_related2
        Test = registry.Test
        Test.insert(properties={'sub': {'name': 'jssuzanne'}})
        query = registry.Test.query().filter(
            Test.name.cast(types.String) == '"jssuzanne"')
        assert query.count()


def field_without_name():

    @register(Model)
    class Test:

        id = Integer(primary_key=True)
        field = OneField()


@pytest.mark.field
class TestField2:

    @pytest.fixture(autouse=True)
    def close_registry(self, request, bloks_loaded):

        def close():
            if hasattr(self, 'registry'):
                self.registry.close()

        request.addfinalizer(close)

    def init_registry(self, *args, **kwargs):
        self.registry = init_registry(*args, **kwargs)
        return self.registry

    def test_field_without_name(self):
        self.init_registry(field_without_name)

    def test_field_function_fset(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                _name = String()
                name = Function(fget='fget', fset='fset', fdel='fdel',
                                fexpr='fexpr')

                def fget(self):
                    return self._name

                def fset(self, value):
                    self._name = value

                def fdel(self):
                    self._name = None

                @classmethod
                def fexpr(cls):
                    return cls._name

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert(name='Jean-Sebastien SUZANNE')
        assert t._name == 'Jean-Sebastien SUZANNE'
        t = registry.Test.query().first()
        t.name = 'Mister ANYBLOK'
        assert t._name == 'Mister ANYBLOK'
        t.update(name='Jean-Sebastien SUZANNE')
        assert t._name == 'Jean-Sebastien SUZANNE'

    def test_class_hasattr(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                val1 = Integer()
                val2 = Function(fget='fget', fset='fset')

                def fget(self):
                    return 2 * self.val1

        registry = self.init_registry(add_in_registry)
        registry.Test.val2

    @pytest.mark.skipif(sgdb_in(['MariaDB']),
                        reason='JSON is not existing in this SGDB')
    def test_field_json_related_with_missing_json_column(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                properties = Json()
                name = JsonRelated(keys=['name'])

        with pytest.raises(FieldException):
            self.init_registry(add_in_registry)

    @pytest.mark.skipif(sgdb_in(['MariaDB']),
                        reason='JSON is not existing in this SGDB')
    def test_field_json_related_with_missing_keys(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                properties = Json()
                name = JsonRelated(json_column='properties')

        with pytest.raises(FieldException):
            self.init_registry(add_in_registry)

    @pytest.mark.skipif(sgdb_in(['MariaDB']),
                        reason='JSON is not existing in this SGDB')
    def test_field_json_related_with_adapter(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                properties = Json()
                name = JsonRelated(json_column='properties', keys=['name'],
                                   set_adapter=str, get_adapter=int)

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert()
        assert t.name is None
        t.name = 1
        assert t.properties == {'name': '1'}
        t.properties['name'] = '2'
        assert t.name == 2

    @pytest.mark.skipif(sgdb_in(['MariaDB']),
                        reason='JSON is not existing in this SGDB')
    def test_field_json_related_with_adapter_with_method(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                properties = Json()
                name = JsonRelated(json_column='properties', keys=['name'],
                                   set_adapter='fromint', get_adapter='toint')

                def fromint(self, value):
                    if value:
                        return str(value)

                    return value

                def toint(self, value):
                    if value:
                        return int(value)

                    return value

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert()
        assert t.name is None
        t.name = 1
        assert t.properties == {'name': '1'}
        t.properties['name'] = '2'
        assert t.name == 2
