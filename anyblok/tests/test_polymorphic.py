# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Simon ANDRÉ <sandre@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import DBTestCase
from anyblok import Declarations
from anyblok.column import Integer, String, Date
from anyblok.relationship import Many2One
from datetime import date


register = Declarations.register
Model = Declarations.Model
Mixin = Declarations.Mixin
Core = Declarations.Core


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


class TestPolymorphic(DBTestCase):

    def check_registry(self, Model, **kwargs):
        t = Model.insert(name="test", **kwargs)
        t2 = Model.query().filter(
            Model.type_entity == Model.__mapper__.polymorphic_identity).first()
        self.assertEqual(t2, t)

    def test_single_table_poly(self):
        registry = self.init_registry(single_table_poly)
        self.check_registry(registry.Employee)
        self.check_registry(registry.Engineer,
                            engineer_name='An engineer')
        self.check_registry(registry.Manager, manager_name='An manager')

    def test_multi_table_poly(self):
        registry = self.init_registry(multi_table_poly)
        self.check_registry(registry.Employee)
        self.check_registry(registry.Engineer,
                            engineer_name='An engineer')
        self.check_registry(registry.Manager, manager_name='An manager')

    def test_multi_table_poly_mixins(self):
        registry = self.init_registry(multi_table_poly_mixins)
        self.check_registry(registry.Employee)
        self.check_registry(registry.Engineer,
                            engineer_name='An engineer')
        self.check_registry(registry.Manager, manager_name='An manager',
                            birthday=date.today())

    def test_multi_table_foreign_key(self):
        registry = self.init_registry(multi_table_foreign_key)
        room = registry.Room.insert()
        self.check_registry(registry.Employee, room=room)
        self.check_registry(registry.Engineer,
                            engineer_name='An engineer', room=room)

    def test_multi_table_foreign_key2_with_one_define_mapper_args(self):
        registry = self.init_registry(
            multi_table_foreign_key_with_one_define_mapper_args)
        room = registry.Room.insert()
        self.check_registry(registry.Employee, room=room)
        self.check_registry(registry.Engineer,
                            engineer_name='An engineer', room=room)

    def test_query_with_polymorphic(self):
        registry = self.init_registry(multi_table_poly)
        registry.Employee.insert(name='employee')
        registry.Engineer.insert(name='engineer', engineer_name='john')
        registry.Manager.insert(name='manager', manager_name='doe')
        self.assertEqual(registry.Employee.query().count(), 3)
        for mapper in (registry.Engineer,
                       [registry.Engineer, registry.Manager], '*'):
            query = registry.Employee.query().with_polymorphic(mapper)
            query = query.filter(
                registry.Engineer.engineer_name == 'john')
            employee = query.one()
            self.assertTrue(isinstance(employee, registry.Engineer))
