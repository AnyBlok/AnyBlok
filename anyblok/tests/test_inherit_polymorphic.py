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


class TestInheritPolymorphic(DBTestCase):

    def check_registry(self, Model):
        t = Model.insert(name="test", other="other")
        # Here we do not understand yet why polymorphic criteria is not
        # automatically use on query
        t2 = Model.query().filter(
            Model.type_entity == Model.__mapper__.polymorphic_identity).first()
        self.assertEqual(t2, t)

    def test_simple_subclass_poly(self):
        registry = self.init_registry(simple_subclass_poly)
        self.check_registry(registry.MainModel.Test)

    def test_two_subclass_poly(self):
        registry = self.init_registry(two_subclass_poly)
        self.check_registry(registry.MainModel.Test)
        self.check_registry(registry.MainModel.Test2)

    def test_simple_subclass_poly_with_mixin(self):
        registry = self.init_registry(simple_subclass_poly_with_mixin)
        self.check_registry(registry.MainModel.Test)

    def test_field_insert_simple_subclass_poly(self):
        registry = self.init_registry(simple_subclass_poly)
        t = registry.MainModel.Test.insert(name="test", other="other")
        self.assertEqual(t.name, "test")
        self.assertEqual(t.other, "other")
