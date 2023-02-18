# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Simon ANDRÉ <sandre@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok import Declarations
from anyblok.column import Integer, String, Date, DateTime
from anyblok.relationship import Many2One
from anyblok.field import Function
from datetime import date
from .conftest import init_registry
from sqlalchemy import func


register = Declarations.register
Model = Declarations.Model
Mixin = Declarations.Mixin
Core = Declarations.Core


def check_registry(Model, **kwargs):
    t = Model.insert(name="test", **kwargs)
    t2 = Model.query().filter(
        Model.type_entity == Model.__mapper__.polymorphic_identity).first()
    assert t2 is t
    return t


def multi_table_poly():
    @register(Model)
    class Employee:
        id = Integer(primary_key=True)
        name = String()
        type_entity = String()

        @classmethod
        def define_mapper_args(cls):
            mapper_args = super(Employee, cls).define_mapper_args()
            mapper_args.update({
                'polymorphic_identity': 'employee',
                'polymorphic_on': cls.type_entity,
            })
            return mapper_args

    @register(Model)
    class Engineer(Model.Employee):
        id = Integer(primary_key=True, foreign_key=Model.Employee.use('id'))
        engineer_name = String()

        @classmethod
        def define_mapper_args(cls):
            mapper_args = super(Engineer, cls).define_mapper_args()
            mapper_args.update({
                'polymorphic_identity': 'engineer',
            })
            return mapper_args

    @register(Model)
    class Manager(Model.Employee):
        id = Integer(primary_key=True, foreign_key=Model.Employee.use('id'))
        manager_name = String()

        @classmethod
        def define_mapper_args(cls):
            mapper_args = super(Manager, cls).define_mapper_args()
            mapper_args.update({
                'polymorphic_identity': 'manager',
            })
            return mapper_args


@pytest.fixture(scope="class")
def registry_multi_table_poly(request, bloks_loaded):
    registry = init_registry(multi_table_poly)
    request.addfinalizer(registry.close)
    return registry


class TestMultiTablePoly:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_multi_table_poly):
        transaction = registry_multi_table_poly.begin_nested()
        request.addfinalizer(transaction.rollback)

    def test_field_description(self, registry_multi_table_poly):
        registry = registry_multi_table_poly
        fd_employee = list(registry.Employee.fields_description().keys())
        fd_employee.sort()
        fd_engineer = list(registry.Engineer.fields_description().keys())
        fd_engineer.sort()
        fd_manager = list(registry.Manager.fields_description().keys())
        fd_manager.sort()
        assert fd_employee == ['id', 'name', 'type_entity']
        assert fd_engineer == ['engineer_name', 'id', 'name', 'type_entity']
        assert fd_manager == ['id', 'manager_name', 'name', 'type_entity']

    def test_multi_table_poly(self, registry_multi_table_poly):
        registry = registry_multi_table_poly
        check_registry(registry.Employee)
        check_registry(registry.Engineer, engineer_name='An engineer')
        check_registry(registry.Manager, manager_name='An manager')

    def test_query_with_polymorphic(self, registry_multi_table_poly):
        registry = registry_multi_table_poly
        registry.Employee.insert(name='employee')
        registry.Engineer.insert(name='engineer', engineer_name='john')
        registry.Manager.insert(name='manager', manager_name='doe')
        assert registry.Employee.query().count() == 3
        for mapper in (registry.Engineer,
                       [registry.Engineer, registry.Manager], '*'):
            query = registry.Employee.query().with_polymorphic(mapper)
            query = query.filter(
                registry.Engineer.engineer_name == 'john')
            employee = query.one()
            assert isinstance(employee, registry.Engineer)

    def test_getFieldType(self, registry_multi_table_poly):
        registry = registry_multi_table_poly
        assert registry.Employee.getFieldType('id') == 'Integer'
        assert registry.Employee.getFieldType('name') == 'String'
        assert registry.Employee.getFieldType('type_entity') == 'String'
        assert registry.Engineer.getFieldType('id') == 'Integer'
        assert registry.Engineer.getFieldType('name') == 'String'
        assert registry.Engineer.getFieldType('type_entity') == 'String'
        assert registry.Engineer.getFieldType('engineer_name') == 'String'
        assert registry.Manager.getFieldType('id') == 'Integer'
        assert registry.Manager.getFieldType('name') == 'String'
        assert registry.Manager.getFieldType('type_entity') == 'String'
        assert registry.Manager.getFieldType('manager_name') == 'String'


def single_table_poly():
    @register(Model)
    class Employee:
        id = Integer(primary_key=True)
        type_entity = String(label="Entity type")
        name = String()
        engineer_name = String()
        manager_name = String()

        @classmethod
        def define_mapper_args(cls):
            mapper_args = super(Employee, cls).define_mapper_args()
            mapper_args.update({
                'polymorphic_identity': 'employee',
                'polymorphic_on': cls.type_entity,
            })
            return mapper_args

    @register(Model, tablename=Model.Employee)
    class Engineer(Model.Employee):
        @classmethod
        def define_mapper_args(cls):
            mapper_args = super(Engineer, cls).define_mapper_args()
            mapper_args.update({
                'polymorphic_identity': 'engineer',
            })
            return mapper_args

    @register(Model, tablename=Model.Employee)
    class Manager(Model.Employee):
        @classmethod
        def define_mapper_args(cls):
            mapper_args = super(Manager, cls).define_mapper_args()
            mapper_args.update({
                'polymorphic_identity': 'manager',
            })
            return mapper_args

        @classmethod
        def default_filter_on_sql_statement(cls, statement):
            return statement.where(cls.type_entity == 'manager')


@pytest.fixture(scope="class")
def registry_single_table_poly(request, bloks_loaded):
    registry = init_registry(single_table_poly)
    request.addfinalizer(registry.close)
    return registry


class TestSingleTablePoly:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_single_table_poly):
        transaction = registry_single_table_poly.begin_nested()
        request.addfinalizer(transaction.rollback)

    def test_single_table_poly(self, registry_single_table_poly):
        registry = registry_single_table_poly
        check_registry(registry.Employee)
        check_registry(registry.Engineer, engineer_name='An engineer')
        check_registry(registry.Manager, manager_name='An manager')

    def test_get_primary_keys_on_single_table(self, registry_single_table_poly):
        registry = registry_single_table_poly
        employee_pks = registry.Employee.get_primary_keys()
        engineer_pks = registry.Engineer.get_primary_keys()
        assert employee_pks == engineer_pks

    def test_select_sql_statement(self, registry_single_table_poly):
        registry = registry_single_table_poly
        Employee = registry.Employee
        Engineer = registry.Engineer
        Manager = registry.Manager
        for index in range(3):
            Employee.insert(name='Employee %d' % index)
            Engineer.insert(name='Engineer %d' % index)
            Manager.insert(name='Manager %d' % index)

        for Model in (Employee, Engineer):
            assert Model.execute_sql_statement(
                Model.select_sql_statement(func.count(Model.id))
            ).scalars().one() == 9

        assert Manager.execute_sql_statement(
            Manager.select_sql_statement(func.count(Manager.id))
        ).scalars().one() == 3

    def test_update_sql_statement(self, registry_single_table_poly):
        registry = registry_single_table_poly
        Employee = registry.Employee
        Engineer = registry.Engineer
        Manager = registry.Manager
        for index in range(3):
            Employee.insert(name='Employee %d' % index)
            Engineer.insert(name='Engineer %d' % index)
            Manager.insert(name='Manager %d' % index)

        for Model in (Employee, Engineer):
            assert Model.execute_sql_statement(
                Model.update_sql_statement().values(name='other')
            ).rowcount == 9

        assert Manager.execute_sql_statement(
            Manager.update_sql_statement().values(name="another")
        ).rowcount == 3

    def test_delete_sql_statement_1(self, registry_single_table_poly):
        registry = registry_single_table_poly
        Employee = registry.Employee
        Engineer = registry.Engineer
        Manager = registry.Manager
        for index in range(3):
            Employee.insert(name='Employee %d' % index)
            Engineer.insert(name='Engineer %d' % index)
            Manager.insert(name='Manager %d' % index)

        assert Employee.execute_sql_statement(
            Employee.delete_sql_statement()
        ).rowcount == 9

    def test_delete_sql_statement_2(self, registry_single_table_poly):
        registry = registry_single_table_poly
        Employee = registry.Employee
        Engineer = registry.Engineer
        Manager = registry.Manager
        for index in range(3):
            Employee.insert(name='Employee %d' % index)
            Engineer.insert(name='Engineer %d' % index)
            Manager.insert(name='Manager %d' % index)

        assert Engineer.execute_sql_statement(
            Engineer.delete_sql_statement()
        ).rowcount == 9

    def test_delete_sql_statement_3(self, registry_single_table_poly):
        registry = registry_single_table_poly
        Employee = registry.Employee
        Engineer = registry.Engineer
        Manager = registry.Manager
        for index in range(3):
            Employee.insert(name='Employee %d' % index)
            Engineer.insert(name='Engineer %d' % index)
            Manager.insert(name='Manager %d' % index)

        assert Manager.execute_sql_statement(
            Manager.delete_sql_statement()
        ).rowcount == 3


def multi_table_poly_mixins():
    @register(Mixin)
    class MyMixins:
        birthday = Date()

    @register(Model)
    class Employee:
        id = Integer(primary_key=True)
        name = String()
        type_entity = String()

        @classmethod
        def define_mapper_args(cls):
            mapper_args = super(Employee, cls).define_mapper_args()
            mapper_args.update({
                'polymorphic_identity': 'employee',
                'polymorphic_on': cls.type_entity,
            })
            return mapper_args

    @register(Model)
    class Engineer(Model.Employee):
        id = Integer(primary_key=True, foreign_key=Model.Employee.use('id'))
        engineer_name = String()

        @classmethod
        def define_mapper_args(cls):
            mapper_args = super(Engineer, cls).define_mapper_args()
            mapper_args.update({
                'polymorphic_identity': 'engineer',
            })
            return mapper_args

    @register(Model)
    class Manager(Model.Employee, MyMixins):
        id = Integer(primary_key=True, foreign_key=Model.Employee.use('id'))
        manager_name = String()

        @classmethod
        def define_mapper_args(cls):
            mapper_args = super(Manager, cls).define_mapper_args()
            mapper_args.update({
                'polymorphic_identity': 'manager',
            })
            return mapper_args


@pytest.fixture(scope="class")
def registry_multi_table_poly_mixins(request, bloks_loaded):
    registry = init_registry(multi_table_poly_mixins)
    request.addfinalizer(registry.close)
    return registry


class TestMultiTablePolyMixins:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_multi_table_poly_mixins):
        transaction = registry_multi_table_poly_mixins.begin_nested()
        request.addfinalizer(transaction.rollback)

    def test_multi_table_poly_mixins(self, registry_multi_table_poly_mixins):
        registry = registry_multi_table_poly_mixins
        check_registry(registry.Employee)
        check_registry(registry.Engineer, engineer_name='An engineer')
        check_registry(registry.Manager, manager_name='An manager',
                       birthday=date.today())

    def test_getFieldType_with_mixin(self, registry_multi_table_poly_mixins):
        registry = registry_multi_table_poly_mixins
        assert registry.Employee.getFieldType('id') == 'Integer'
        assert registry.Employee.getFieldType('name') == 'String'
        assert registry.Employee.getFieldType('type_entity') == 'String'
        assert registry.Engineer.getFieldType('id') == 'Integer'
        assert registry.Engineer.getFieldType('name') == 'String'
        assert registry.Engineer.getFieldType('type_entity') == 'String'
        assert registry.Engineer.getFieldType('engineer_name') == 'String'
        assert registry.Manager.getFieldType('id') == 'Integer'
        assert registry.Manager.getFieldType('name') == 'String'
        assert registry.Manager.getFieldType('type_entity') == 'String'
        assert registry.Manager.getFieldType('manager_name') == 'String'
        assert registry.Manager.getFieldType('birthday') == 'Date'


def multi_table_foreign_key():
    @register(Model)
    class Room:
        id = Integer(primary_key=True)
        name = String()

    @register(Model)
    class Employee:
        id = Integer(primary_key=True)
        name = String()
        type_entity = String()
        room = Many2One(model=Model.Room, one2many='employees')

        @classmethod
        def define_mapper_args(cls):
            mapper_args = super(Employee, cls).define_mapper_args()
            mapper_args.update({
                'polymorphic_identity': 'employee',
                'polymorphic_on': cls.type_entity,
            })
            return mapper_args

    @register(Model)
    class Engineer(Model.Employee):
        id = Integer(primary_key=True, foreign_key=Model.Employee.use('id'))
        engineer_name = String()

        @classmethod
        def define_mapper_args(cls):
            mapper_args = super(Engineer, cls).define_mapper_args()
            mapper_args.update({
                'polymorphic_identity': 'engineer',
            })
            return mapper_args


@pytest.fixture(scope="class")
def registry_multi_table_poly_fk(request, bloks_loaded):
    registry = init_registry(multi_table_foreign_key)
    request.addfinalizer(registry.close)
    return registry


class TestMultiTablePolyFk:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_multi_table_poly_fk):
        transaction = registry_multi_table_poly_fk.begin_nested()
        request.addfinalizer(transaction.rollback)

    def test_multi_table_foreign_key(self, registry_multi_table_poly_fk):
        registry = registry_multi_table_poly_fk
        room = registry.Room.insert()
        check_registry(registry.Employee, room=room)
        check_registry(registry.Engineer,
                       engineer_name='An engineer', room=room)

    def test_getFieldType_with_relationship(self, registry_multi_table_poly_fk):
        registry = registry_multi_table_poly_fk
        assert registry.Employee.getFieldType('id') == 'Integer'
        assert registry.Employee.getFieldType('name') == 'String'
        assert registry.Employee.getFieldType('type_entity') == 'String'
        assert registry.Employee.getFieldType('room') == 'Many2One'
        assert registry.Engineer.getFieldType('id') == 'Integer'
        assert registry.Engineer.getFieldType('name') == 'String'
        assert registry.Engineer.getFieldType('type_entity') == 'String'
        assert registry.Engineer.getFieldType('engineer_name') == 'String'
        assert registry.Engineer.getFieldType('room') == 'Many2One'


def multi_table_foreign_key_with_one_define_mapper_args():
    @register(Model)
    class Room:
        id = Integer(primary_key=True)
        name = String()

    @register(Model)
    class Employee:
        id = Integer(primary_key=True)
        name = String()
        type_entity = String()
        room = Many2One(model=Model.Room, one2many='employees')

        @classmethod
        def define_mapper_args(cls):
            mapper_args = super(Employee, cls).define_mapper_args()
            if Model.Employee.__registry_name__ == cls.__registry_name__:
                mapper_args.update({
                    'polymorphic_on': cls.type_entity,
                })

            mapper_args.update({
                'polymorphic_identity': cls.__registry_name__,
            })
            return mapper_args

    @register(Model)
    class Engineer(Model.Employee):
        id = Integer(primary_key=True, foreign_key=Model.Employee.use('id'))
        engineer_name = String()


class TestPolymorphic:

    @pytest.fixture(autouse=True)
    def close_registry(self, request, bloks_loaded):

        def close():
            if hasattr(self, 'registry'):
                self.registry.close()

        request.addfinalizer(close)

    def init_registry(self, *args, **kwargs):
        self.registry = init_registry(*args, **kwargs)
        return self.registry

    def test_field_function_only_must_not_create_a_new_table(self):

        def single_table_poly_with_field_function():
            single_table_poly()

            @register(Model, tablename=Model.Employee)
            class Manager:

                full_name = Function(fget='get_full_name')

                def get_full_name(self):
                    return self.name + ' - ' + self.manager_name

        registry = self.init_registry(single_table_poly_with_field_function)
        check_registry(registry.Employee)
        check_registry(registry.Engineer, engineer_name='An engineer')
        t = check_registry(registry.Manager, manager_name='An manager')
        assert registry.Employee.__tablename__ == registry.Manager.__tablename__
        assert t.full_name == 'test - An manager'

    def test_field_function_must_be_available_in_subclass(self):

        def single_table_poly_with_field_function():
            single_table_poly()

            @register(Model)
            class Employee:

                full_name = Function(fget='get_full_name')

                def get_full_name(self):
                    sub_name = ''
                    if self.type_entity == 'manager':
                        sub_name = self.manager_name
                    elif self.type_entity == 'engineer':
                        sub_name = self.engineer_name

                    return self.name + ' - ' + sub_name

        registry = self.init_registry(single_table_poly_with_field_function)
        check_registry(registry.Employee)
        t1 = check_registry(registry.Engineer, engineer_name='An engineer')
        assert t1.full_name == 'test - An engineer'
        t2 = check_registry(registry.Manager, manager_name='An manager')
        assert t2.full_name == 'test - An manager'

    def test_multi_table_foreign_key2_with_one_define_mapper_args(self):
        registry = self.init_registry(
            multi_table_foreign_key_with_one_define_mapper_args)
        room = registry.Room.insert()
        check_registry(registry.Employee, room=room)
        check_registry(registry.Engineer, engineer_name='An engineer',
                       room=room)

    def test_query_with_polymorphic(self):
        registry = self.init_registry(multi_table_poly)
        registry.Employee.insert(name='employee')
        registry.Engineer.insert(name='engineer', engineer_name='john')
        registry.Manager.insert(name='manager', manager_name='doe')
        assert registry.Employee.query().count() == 3
        for mapper in (registry.Engineer,
                       [registry.Engineer, registry.Manager], '*'):
            query = registry.Employee.query().with_polymorphic(mapper)
            query = query.filter(
                registry.Engineer.engineer_name == 'john')
            employee = query.one()
            assert isinstance(employee, registry.Engineer)

    def test_getFieldType(self):
        registry = self.init_registry(multi_table_poly)
        assert registry.Employee.getFieldType('id') == 'Integer'
        assert registry.Employee.getFieldType('name') == 'String'
        assert registry.Employee.getFieldType('type_entity') == 'String'
        assert registry.Engineer.getFieldType('id') == 'Integer'
        assert registry.Engineer.getFieldType('name') == 'String'
        assert registry.Engineer.getFieldType('type_entity') == 'String'
        assert registry.Engineer.getFieldType('engineer_name') == 'String'
        assert registry.Manager.getFieldType('id') == 'Integer'
        assert registry.Manager.getFieldType('name') == 'String'
        assert registry.Manager.getFieldType('type_entity') == 'String'
        assert registry.Manager.getFieldType('manager_name') == 'String'

    def test_getFieldType_with_mixin(self):
        registry = self.init_registry(multi_table_poly_mixins)
        assert registry.Employee.getFieldType('id') == 'Integer'
        assert registry.Employee.getFieldType('name') == 'String'
        assert registry.Employee.getFieldType('type_entity') == 'String'
        assert registry.Engineer.getFieldType('id') == 'Integer'
        assert registry.Engineer.getFieldType('name') == 'String'
        assert registry.Engineer.getFieldType('type_entity') == 'String'
        assert registry.Engineer.getFieldType('engineer_name') == 'String'
        assert registry.Manager.getFieldType('id') == 'Integer'
        assert registry.Manager.getFieldType('name') == 'String'
        assert registry.Manager.getFieldType('type_entity') == 'String'
        assert registry.Manager.getFieldType('manager_name') == 'String'
        assert registry.Manager.getFieldType('birthday') == 'Date'

    def test_getFieldType_with_relationship(self):
        registry = self.init_registry(multi_table_foreign_key)
        assert registry.Employee.getFieldType('id') == 'Integer'
        assert registry.Employee.getFieldType('name') == 'String'
        assert registry.Employee.getFieldType('type_entity') == 'String'
        assert registry.Employee.getFieldType('room') == 'Many2One'
        assert registry.Engineer.getFieldType('id') == 'Integer'
        assert registry.Engineer.getFieldType('name') == 'String'
        assert registry.Engineer.getFieldType('type_entity') == 'String'
        assert registry.Engineer.getFieldType('engineer_name') == 'String'
        assert registry.Engineer.getFieldType('room') == 'Many2One'

    def test_field_description(self):
        registry = self.init_registry(multi_table_poly)
        fd_employee = list(registry.Employee.fields_description().keys())
        fd_employee.sort()
        fd_engineer = list(registry.Engineer.fields_description().keys())
        fd_engineer.sort()
        fd_manager = list(registry.Manager.fields_description().keys())
        fd_manager.sort()
        assert fd_employee == ['id', 'name', 'type_entity']
        assert fd_engineer == ['engineer_name', 'id', 'name', 'type_entity']
        assert fd_manager == ['id', 'manager_name', 'name', 'type_entity']

    def test_get_primary_keys_on_single_table(self):
        registry = self.init_registry(single_table_poly)
        employee_pks = registry.Employee.get_primary_keys()
        engineer_pks = registry.Engineer.get_primary_keys()
        assert employee_pks == engineer_pks

    def test_datetime_with_auto_update_on_single_table(self):

        def single_table_with_datetime_auto_update():
            single_table_poly()

            @register(Model)
            class Employee:
                update_at = DateTime(auto_update=True)

        registry = self.init_registry(single_table_with_datetime_auto_update)
        check_registry(registry.Employee)
        engineer = check_registry(
            registry.Engineer, engineer_name='An engineer')
        assert engineer.update_at is None
        manager = check_registry(
            registry.Manager, manager_name='An manager')
        assert manager.update_at is None
        engineer.engineer_name = 'Other'
        manager.manager_name = 'Other'
        registry.flush()
        assert engineer.update_at is not None
        assert manager.update_at is not None

    def test_datetime_with_auto_update_on_multi_table(self):

        def multi_table_with_datetime_auto_update():
            multi_table_poly()

            @register(Model)
            class Employee:
                update_at = DateTime(auto_update=True)

        registry = self.init_registry(multi_table_with_datetime_auto_update)
        check_registry(registry.Employee)
        engineer = check_registry(
            registry.Engineer, engineer_name='An engineer')
        assert engineer.update_at is None
        manager = check_registry(
            registry.Manager, manager_name='An manager')
        assert manager.update_at is None
        engineer.engineer_name = 'Other'
        manager.manager_name = 'Other'
        registry.flush()
        assert engineer.update_at is not None
        assert manager.update_at is not None
