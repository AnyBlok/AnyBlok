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
from anyblok.column import Integer, String


register = Declarations.register
Model = Declarations.Model
Mixin = Declarations.Mixin
Core = Declarations.Core


def simple_subclass_poly():
    @register(Model)
    class MainModel:
        id = Integer(primary_key=True)
        type_entity = String(label="Entity type")
        name = String()

        @classmethod
        def define_mapper_args(cls, mapper_args, properties):
            mapper_args.update({
                'polymorphic_identity': 'main',
                'polymorphic_on': properties['type_entity'],
            })
            return mapper_args

    @register(Model.MainModel, tablename=Model.MainModel)
    class Test(Model.MainModel):
        other = String()

        @classmethod
        def define_mapper_args(cls, mapper_args, properties):
            mapper_args.update({
                'polymorphic_identity': 'sub',
            })
            return mapper_args


def simple_subclass_poly2():
    @register(Model)
    class Employee:
        id = Integer(primary_key=True)
        name = String()
        type_entity = String()

        @classmethod
        def define_mapper_args(cls, mapper_args, properties):
            mapper_args.update({
                'polymorphic_identity': 'employee',
                'polymorphic_on': properties['type_entity'],
            })
            return mapper_args

    @register(Model)
    class Engineer(Model.Employee):
        id = Integer(primary_key=True, foreign_key=(Model.Employee, 'id'))
        engineer_name = String()

        @classmethod
        def define_mapper_args(cls, mapper_args, properties):
            mapper_args.update({
                'polymorphic_identity': 'engineer',
            })
            return mapper_args

    @register(Model)
    class Manager(Model.Employee):
        id = Integer(primary_key=True, foreign_key=(Model.Employee, 'id'))
        manager_name = String()

        @classmethod
        def define_mapper_args(cls, mapper_args, properties):
            mapper_args.update({
                'polymorphic_identity': 'manager',
            })
            return mapper_args


def two_subclass_poly():
    @register(Model)
    class MainModel:
        id = Integer(primary_key=True)
        type_entity = String(label="Entity type")
        name = String()

        @classmethod
        def define_mapper_args(cls, mapper_args, properties):
            mapper_args.update({
                'polymorphic_identity': 'main',
                'polymorphic_on': properties['type_entity'],
            })
            return mapper_args

    @register(Model.MainModel, tablename=Model.MainModel)
    class Test(Model.MainModel):
        other = String()

        @classmethod
        def define_mapper_args(cls, mapper_args, properties):
            mapper_args.update({
                'polymorphic_identity': 'sub',
            })
            return mapper_args

    @register(Model.MainModel, tablename=Model.MainModel)
    class Test2(Model.MainModel):
        other = String()

        @classmethod
        def define_mapper_args(cls, mapper_args, properties):
            mapper_args.update({
                'polymorphic_identity': 'sub2',
            })
            return mapper_args


def simple_subclass_poly_with_mixin():
    @register(Model)
    class MainModel:
        id = Integer(primary_key=True)
        type_entity = String(label="Entity type")
        name = String()

        @classmethod
        def define_mapper_args(cls, mapper_args, properties):
            mapper_args.update({
                'polymorphic_identity': 'main',
                'polymorphic_on': properties['type_entity'],
            })
            return mapper_args

    @register(Mixin)
    class MixinName:
        other = String()

    @register(Model.MainModel, tablename=Model.MainModel)
    class Test(Model.MainModel, Mixin.MixinName):
        @classmethod
        def define_mapper_args(cls, mapper_args, properties):
            mapper_args.update({
                'polymorphic_identity': 'sub',
            })
            return mapper_args


class TestPolymorphic(DBTestCase):

    def check_registry(self, Model, **kwargs):
        t = Model.insert(name="test", **kwargs)
        # Here we do not understand yet why polymorphic criteria is not
        # automatically use on query
        t2 = Model.query().filter(
            Model.type_entity == Model.__mapper__.polymorphic_identity).first()
        self.assertEqual(t2, t)

    def test_simple_subclass_poly(self):
        registry = self.init_registry(simple_subclass_poly)
        self.check_registry(registry.MainModel.Test, other='test')

    def test_simple_subclass_poly2(self):
        registry = self.init_registry(simple_subclass_poly2)
        self.check_registry(registry.Employee)
        self.check_registry(registry.Engineer, engineer_name='An engineer')
        self.check_registry(registry.Manager, manager_name='An manager')

    def test_two_subclass_poly(self):
        registry = self.init_registry(two_subclass_poly)
        self.check_registry(registry.MainModel.Test, other='test')
        self.check_registry(registry.MainModel.Test2, other='test')

    def test_simple_subclass_poly_with_mixin(self):
        registry = self.init_registry(simple_subclass_poly_with_mixin)
        self.check_registry(registry.MainModel.Test, other='test')

    def test_field_insert_simple_subclass_poly(self):
        registry = self.init_registry(simple_subclass_poly)
        t = registry.MainModel.Test.insert(name="test", other="other")
        self.assertEqual(t.name, "test")
        self.assertEqual(t.other, "other")

    def test_query_with_polymorphic(self):
        registry = self.init_registry(simple_subclass_poly2)
        registry.Employee.insert(name='employee')
        registry.Engineer.insert(name='engineer', engineer_name='john')
        registry.Manager.insert(name='manager', manager_name='doe')
        self.assertEqual(registry.Employee.query().count(), 3)
        for mapper in (registry.Engineer,
                       [registry.Engineer, registry.Manager], '*'):
            query = registry.Employee.query().with_polymorphic(mapper)
            query = query.filter(registry.Engineer.engineer_name == 'john')
            employee = query.one()
            self.assertTrue(isinstance(employee, registry.Engineer))
