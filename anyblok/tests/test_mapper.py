# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase, DBTestCase
from sqlalchemy.schema import ForeignKey
from anyblok.mapper import (ModelAttribute, ModelAttributeException,
                            ModelAttributeAdapter, ModelAdapter, ModelRepr,
                            ModelReprException, ModelAttributeAdapterException,
                            ModelMapper, ModelAttributeMapper, MapperAdapter,
                            MapperException)
from anyblok import Declarations
from anyblok.column import String

register = Declarations.register
unregister = Declarations.unregister
Model = Declarations.Model


class TestModelAttribute(DBTestCase):

    def test_get_attribute(self):
        registry = self.init_registry(None)
        ma = ModelAttribute('Model.System.Model', 'name')
        self.assertEqual(ma.get_attribute(registry),
                         registry.get('Model.System.Model').name)

    def test_get_attribute_unexisting_model(self):
        registry = self.init_registry(None)
        ma = ModelAttribute('Model.Unexisting.Model', 'name')
        with self.assertRaises(ModelAttributeException):
            ma.get_attribute(registry)

    def test_get_attribute_unexisting_attribute(self):
        registry = self.init_registry(None)
        ma = ModelAttribute('Model.System.Model', 'id')
        with self.assertRaises(ModelAttributeException):
            ma.get_attribute(registry)

    def test_get_fk_name_with_wrong_model(self):
        registry = self.init_registry(None)
        ma = ModelAttribute('Model.System', 'name')
        with self.assertRaises(ModelAttributeException):
            ma.get_fk_name(registry)

    def test_get_fk_name_with_unexisting_model(self):
        registry = self.init_registry(None)
        ma = ModelAttribute('Model.Unexisting.Model', 'name')
        with self.assertRaises(ModelAttributeException):
            ma.get_fk_name(registry)

    def test_get_fk_name_unexisting_attribute(self):
        registry = self.init_registry(None)
        ma = ModelAttribute('Model.System.Model', 'id')
        with self.assertRaises(ModelAttributeException):
            ma.get_fk_name(registry)

    def test_get_fk_name(self):
        registry = self.init_registry(None)
        ma = ModelAttribute('Model.System.Model', 'name')
        self.assertEqual(ma.get_fk_name(registry), 'system_model.name')

    def test_get_fk_name_with_name_different_of_column_name(self):

        def add_in_registry():

            @register(Model)
            class Test:

                name = String(primary_key=True, db_column_name='other')

        registry = self.init_registry(add_in_registry)
        ma = ModelAttribute('Model.Test', 'name')
        self.assertEqual(ma.get_fk_name(registry), 'test.other')

    def test_get_fk(self):
        registry = self.init_registry(None)
        ma = ModelAttribute('Model.System.Model', 'name')
        self.assertTrue(isinstance(ma.get_fk(registry), ForeignKey))

    def test_get_fk_with_options(self):
        registry = self.init_registry(None)
        ma = ModelAttribute('Model.System.Model', 'name').options(
            ondelete='cascade')
        mafk = ma.get_fk(registry)
        self.assertTrue(isinstance(mafk, ForeignKey))

    def test_use(self):
        ma = Declarations.Model.System.Model.use('name')
        self.assertTrue(isinstance(ma, ModelAttribute))
        self.assertEqual(ma.model_name, 'Model.System.Model')
        self.assertEqual(ma.attribute_name, 'name')


class TestModelAttributeAdapter(TestCase):

    def test_from_declaration(self):
        ma = ModelAttribute('Model.System.Model', 'name')
        maa = ModelAttributeAdapter(ma)
        self.assertIs(maa, ma)

    def test_from_registry_name(self):
        maa = ModelAttributeAdapter("Model.System.Model=>name")
        self.assertTrue(isinstance(maa, ModelAttribute))
        self.assertEqual(maa.model_name, 'Model.System.Model')
        self.assertEqual(maa.attribute_name, 'name')

    def test_from_registry_name_without_attribute(self):
        with self.assertRaises(ModelAttributeAdapterException):
            ModelAttributeAdapter("Model.System.Model")


class TestModelRepr(DBTestCase):

    def test_unexisting_model(self):
        registry = self.init_registry(None)
        mr = ModelRepr('Model.Unexisting.Model')
        with self.assertRaises(ModelReprException):
            mr.check_model(registry)

    def test_get_tablename(self):
        registry = self.init_registry(None)
        mr = ModelRepr('Model.System.Model')
        self.assertEqual(mr.tablename(registry), 'system_model')

    def test_get_registry_name(self):
        mr = ModelRepr('Model.System.Model')
        self.assertEqual(mr.model_name, 'Model.System.Model')

    def test_get_primary_keys(self):
        registry = self.init_registry(None)
        mr = ModelRepr('Model.System.Model')
        mas = mr.primary_keys(registry)
        self.assertEqual(len(mas), 1)
        self.assertEqual([x.attribute_name for x in mas], ['name'])

    def test_get_foreign_key_for(self):
        registry = self.init_registry(None)
        mr = ModelRepr('Model.System.Cron.Job')
        mas = mr.foreign_keys_for(registry, 'Model.System.Model')
        self.assertEqual(len(mas), 1)
        self.assertEqual([x.attribute_name for x in mas], ['model'])


class TestModelAdapter(TestCase):

    def test_from_declaration(self):
        mr = ModelRepr('Model.System.Model')
        mra = ModelAdapter(mr)
        self.assertIs(mr, mra)

    def test_from_registry_name(self):
        mra = ModelAdapter("Model.System.Model")
        self.assertTrue(isinstance(mra, ModelRepr))
        self.assertEqual(mra.model_name, 'Model.System.Model')


class TestModelMapper(DBTestCase):

    def test_not_capable(self):
        self.assertFalse(ModelMapper.capable(None))

    def test_capable_by_declaration(self):
        self.assertTrue(ModelMapper.capable(Model.System.Model))

    def test_capable_by_registry_name(self):
        self.assertTrue(ModelMapper.capable('Model.System.Model'))

    def test_by_declaration(self):
        mm = ModelMapper(Model.System.Model, 'even')
        self.assertTrue(isinstance(mm.model, ModelRepr))
        self.assertTrue(mm.model.model_name, 'Model.System.Model')

    def test_by_registry_name(self):
        mm = ModelMapper('Model.System.Model', 'event')
        self.assertTrue(isinstance(mm.model, ModelRepr))
        self.assertTrue(mm.model.model_name, 'Model.System.Model')

    def test_listen_sqlalchemy(self):

        def method():
            pass

        mm = ModelMapper(Model.System.Model, 'before_insert')
        mm.listen(method)
        self.assertTrue(method.is_an_sqlalchemy_event_listener)
        self.assertEqual(method.sqlalchemy_listener, mm)

    def test_listen_anyblok(self):
        def method():
            pass

        mm = ModelMapper(Model.System.Model, 'event')
        mm.listen(method)
        self.assertTrue(method.is_an_event_listener)
        self.assertEqual(method.model, 'Model.System.Model')
        self.assertEqual(method.event, 'event')

    def test_get_mapper(self):
        registry = self.init_registry(None)
        mm = ModelMapper(Model.System.Model, 'even')
        self.assertIs(mm.mapper(registry, None), registry.System.Model)


class TestModelAttributeMapper(DBTestCase):

    def test_not_str_capable(self):
        self.assertFalse(ModelAttributeMapper.capable('Model.System.Model'))

    def test_not_capable(self):
        self.assertFalse(ModelAttributeMapper.capable(None))

    def test_capable_by_declaration(self):
        self.assertTrue(ModelAttributeMapper.capable(
            Model.System.Model.use('name')))

    def test_capable_by_registry_name(self):
        self.assertTrue(ModelAttributeMapper.capable(
            'Model.System.Model=>name'))

    def test_by_declaration(self):
        mam = ModelAttributeMapper(Model.System.Model.use('name'), 'event')
        self.assertTrue(isinstance(mam.attribute, ModelAttribute))
        self.assertTrue(mam.attribute.model_name, 'Model.System.Model')

    def test_by_registry_name(self):
        mam = ModelAttributeMapper('Model.System.Model=>name', 'event')
        self.assertTrue(isinstance(mam.attribute, ModelAttribute))
        self.assertTrue(mam.attribute.model_name, 'Model.System.Model')

    def test_listen(self):

        def method():
            pass

        mam = ModelAttributeMapper(Model.System.Model.use('name'), 'set')
        mam.listen(method)
        self.assertTrue(method.is_an_sqlalchemy_event_listener)
        self.assertEqual(method.sqlalchemy_listener, mam)

    def test_get_mapper(self):
        registry = self.init_registry(None)
        mam = ModelAttributeMapper(Model.System.Model.use('name'), 'set')
        self.assertIs(mam.mapper(registry, None), registry.System.Model.name)


class TestMapperAdapter(TestCase):

    def test_model_mapper(self):
        mam = MapperAdapter('Model.System.Model', 'event')
        self.assertTrue(isinstance(mam, ModelMapper))

    def test_model_attribute_mapper(self):
        mam = MapperAdapter('Model.System.Model=>name', 'event')
        self.assertTrue(isinstance(mam, ModelAttributeMapper))

    def test_no_mapper(self):
        with self.assertRaises(MapperException):
            MapperAdapter(None)
