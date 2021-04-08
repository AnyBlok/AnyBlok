# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from sqlalchemy.schema import ForeignKey
from anyblok.mapper import (ModelAttribute, ModelAttributeException,
                            ModelAttributeAdapter, ModelAdapter, ModelRepr,
                            ModelReprException, ModelAttributeAdapterException,
                            ModelMapper, ModelAttributeMapper, MapperAdapter,
                            MapperException)
from anyblok import Declarations
from anyblok.column import String, Integer
from .conftest import init_registry, reset_db

register = Declarations.register
unregister = Declarations.unregister
Model = Declarations.Model


class TestModelAttribute:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_blok):
        transaction = registry_blok.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_get_attribute(self, registry_blok):
        registry = registry_blok
        ma = ModelAttribute('Model.System.Model', 'name')
        assert ma.get_attribute(registry) == registry.get(
            'Model.System.Model').name

    def test_without_attribute(self, registry_blok):
        with pytest.raises(ModelAttributeException):
            ModelAttribute('Model.System.Model', None)

    def test_without_model(self, registry_blok):
        with pytest.raises(ModelAttributeException):
            ModelAttribute(None, 'name')

    def test_without_model_and_attribute(self, registry_blok):
        with pytest.raises(ModelAttributeException):
            ModelAttribute(None, None)

    def test_get_attribute_unexisting_model(self, registry_blok):
        registry = registry_blok
        ma = ModelAttribute('Model.Unexisting.Model', 'name')
        with pytest.raises(ModelAttributeException):
            ma.get_attribute(registry)

    def test_get_attribute_unexisting_attribute(self, registry_blok):
        registry = registry_blok
        ma = ModelAttribute('Model.System.Model', 'id')
        with pytest.raises(ModelAttributeException):
            ma.get_attribute(registry)

    def test_get_fk_name_with_wrong_model(self, registry_blok):
        registry = registry_blok
        ma = ModelAttribute('Model.System', 'name')
        with pytest.raises(ModelAttributeException):
            ma.get_fk_name(registry)

    def test_get_fk_name_with_unexisting_model(self, registry_blok):
        registry = registry_blok
        ma = ModelAttribute('Model.Unexisting.Model', 'name')
        with pytest.raises(ModelAttributeException):
            ma.get_fk_name(registry)

    def test_get_fk_name_unexisting_attribute(self, registry_blok):
        registry = registry_blok
        ma = ModelAttribute('Model.System.Model', 'id')
        with pytest.raises(ModelAttributeException):
            ma.get_fk_name(registry)

    def test_get_fk_name(self, registry_blok):
        registry = registry_blok
        ma = ModelAttribute('Model.System.Model', 'name')
        assert ma.get_fk_name(registry) == 'system_model.name'

    def test_get_fk(self, registry_blok):
        registry = registry_blok
        ma = ModelAttribute('Model.System.Model', 'name')
        assert isinstance(ma.get_fk(registry), ForeignKey)

    def test_get_fk_with_options(self, registry_blok):
        registry = registry_blok
        ma = ModelAttribute('Model.System.Model', 'name').options(
            ondelete='cascade')
        mafk = ma.get_fk(registry)
        assert isinstance(mafk, ForeignKey)

    def test_use(self, registry_blok):
        ma = Declarations.Model.System.Model.use('name')
        assert isinstance(ma, ModelAttribute)
        assert ma.model_name == 'Model.System.Model'
        assert ma.attribute_name == 'name'

    def test_str(self, registry_blok):
        ma = ModelAttribute('Model.System.Model', 'name')
        assert str(ma) == 'Model.System.Model => name'

    def test_get_fk_remote(self, registry_blok):
        registry = registry_blok
        ma = ModelAttribute('Model.System.Column', 'name')
        assert ma.get_fk_remote(registry) is None

    def test_get_complete_remote(self, registry_blok):
        registry = registry_blok
        ma = ModelAttribute('Model.System.Field', 'name')
        assert ma.get_complete_remote(registry) is None

    def test_existing_FakeColumn(self, registry_blok):
        registry = registry_blok
        ma = ModelAttribute('Model.System.Field', 'name')
        assert ma.add_fake_column(registry) is None

    def test_existing_FakeRelationShip(self, registry_blok):
        registry = registry_blok
        ma = ModelAttribute('Model.System.Field', 'name')
        assert ma.add_fake_relationship(
            registry, 'Model.System', 'test') is None

    def test_get_column_name(self, registry_blok):
        registry = registry_blok
        ma = ModelAttribute('Model.System.Field', 'name')
        assert ma.get_column_name(registry) == 'name'

    def test_check_model_in_first_step_no_sql_model(self, registry_blok):
        registry = registry_blok
        ma = ModelAttribute('Model.System', 'name')
        with pytest.raises(ModelAttributeException):
            ma.check_model_in_first_step(registry)


class TestModelAttributeAdapter:

    def test_from_declaration(self):
        ma = ModelAttribute('Model.System.Model', 'name')
        maa = ModelAttributeAdapter(ma)
        assert maa is ma

    def test_from_registry_name(self):
        maa = ModelAttributeAdapter("Model.System.Model=>name")
        assert isinstance(maa, ModelAttribute)
        assert maa.model_name == 'Model.System.Model'
        assert maa.attribute_name == 'name'

    def test_from_registry_name_without_attribute(self):
        with pytest.raises(ModelAttributeAdapterException):
            ModelAttributeAdapter("Model.System.Model")


class TestModelRepr:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_blok):
        transaction = registry_blok.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_unexisting_model(self, registry_blok):
        registry = registry_blok
        mr = ModelRepr('Model.Unexisting.Model')
        with pytest.raises(ModelReprException):
            mr.check_model(registry)

    def test_get_tablename(self, registry_blok):
        registry = registry_blok
        mr = ModelRepr('Model.System.Model')
        assert mr.tablename(registry) == 'system_model'

    def test_get_registry_name(self, registry_blok):
        mr = ModelRepr('Model.System.Model')
        assert mr.model_name == 'Model.System.Model'

    def test_str(self, registry_blok):
        mr = ModelRepr('Model.System.Model')
        assert str(mr) == 'Model.System.Model'

    def test_get_primary_keys(self, registry_blok):
        registry = registry_blok
        mr = ModelRepr('Model.System.Model')
        mas = mr.primary_keys(registry)
        assert len(mas) == 1
        assert [x.attribute_name for x in mas] == ['name']

    def test_without_model(self, registry_blok):
        with pytest.raises(ModelReprException):
            ModelRepr(None)

    def test_mapper_self(self, registry_blok):
        mm = ModelMapper('SELF', None)
        assert mm.mapper(
            registry_blok, 'Model.System.Blok'
        ) is registry_blok.System.Blok


class TestModelAdapter:

    def test_from_declaration(self):
        mr = ModelRepr('Model.System.Model')
        mra = ModelAdapter(mr)
        assert mr is mra

    def test_from_registry_name(self):
        mra = ModelAdapter("Model.System.Model")
        assert isinstance(mra, ModelRepr)
        assert mra.model_name == 'Model.System.Model'


class TestModelMapper:

    def test_not_capable(self):
        assert not (ModelMapper.capable(None))

    def test_capable_by_declaration(self):
        assert ModelMapper.capable(Model.System.Model)

    def test_capable_by_registry_name(self):
        assert ModelMapper.capable('Model.System.Model')

    def test_capable_by_model_repr(self):
        assert ModelMapper.capable(ModelRepr('Model.System.Model'))

    def test_model_repr(self):
        assert ModelMapper(ModelRepr('Model.System.Model'), None)

    def test_by_declaration(self):
        mm = ModelMapper(Model.System.Model, 'even')
        assert isinstance(mm.model, ModelRepr)
        assert mm.model.model_name, 'Model.System.Model'

    def test_by_registry_name(self):
        mm = ModelMapper('Model.System.Model', 'event')
        assert isinstance(mm.model, ModelRepr)
        assert mm.model.model_name, 'Model.System.Model'

    def test_listen_sqlalchemy(self):

        def method():
            pass

        mm = ModelMapper(Model.System.Model, 'before_insert')
        mm.listen(method)
        assert method.is_an_sqlalchemy_event_listener
        assert method.sqlalchemy_listener is mm

    def test_listen_anyblok(self):
        def method():
            pass

        mm = ModelMapper(Model.System.Model, 'event')
        mm.listen(method)
        assert method.is_an_event_listener
        assert method.model == 'Model.System.Model'
        assert method.event == 'event'


class TestModelAttributeMapper:

    def test_not_str_capable(self):
        assert not (ModelAttributeMapper.capable('Model.System.Model'))

    def test_not_capable(self):
        assert not (ModelAttributeMapper.capable(None))

    def test_capable_by_declaration(self):
        assert ModelAttributeMapper.capable(
            Model.System.Model.use('name'))

    def test_capable_by_registry_name(self):
        assert ModelAttributeMapper.capable(
            'Model.System.Model=>name')

    def test_by_declaration(self):
        mam = ModelAttributeMapper(Model.System.Model.use('name'), 'event')
        assert isinstance(mam.attribute, ModelAttribute)
        assert mam.attribute.model_name == 'Model.System.Model'

    def test_by_registry_name(self):
        mam = ModelAttributeMapper('Model.System.Model=>name', 'event')
        assert isinstance(mam.attribute, ModelAttribute)
        assert mam.attribute.model_name == 'Model.System.Model'

    def test_listen(self):

        def method():
            pass

        mam = ModelAttributeMapper(Model.System.Model.use('name'), 'set')
        mam.listen(method)
        assert method.is_an_sqlalchemy_event_listener
        assert method.sqlalchemy_listener is mam


class TestMapperAdapter:

    def test_model_mapper(self):
        mam = MapperAdapter('Model.System.Model', 'event')
        assert isinstance(mam, ModelMapper)

    def test_model_attribute_mapper(self):
        mam = MapperAdapter('Model.System.Model=>name', 'event')
        assert isinstance(mam, ModelAttributeMapper)

    def test_no_mapper(self):
        with pytest.raises(MapperException):
            MapperAdapter(None)


class TestMapperOther:

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

    def test_get_fk_name_with_name_different_of_column_name(self):

        def add_in_registry():

            @register(Model)
            class Test:

                name = String(primary_key=True, db_column_name='other')

        registry = self.init_registry(add_in_registry)
        ma = ModelAttribute('Model.Test', 'name')
        assert ma.get_fk_name(registry) == 'test.other'

    def test_get_foreign_key_for(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)

            @register(Model)
            class Test2:

                id = Integer(primary_key=True)
                test_id = Integer(foreign_key=Model.Test.use('id'))

        registry = self.init_registry(add_in_registry)
        mr = ModelRepr('Model.Test2')
        mas = mr.foreign_keys_for(registry, 'Model.Test')
        assert len(mas) == 1
        assert [x.attribute_name for x in mas] == ['test_id']

    def test_get_mapper(self):
        registry = self.init_registry(None)
        mm = ModelMapper(Model.System.Model, 'even')
        assert mm.mapper(registry, None) is registry.System.Model

    def test_get_attribute_mapper(self):
        registry = self.init_registry(None)
        mam = ModelAttributeMapper(Model.System.Model.use('name'), 'set')
        # We can't compare that the column are the same, because is the case
        # of the call are in the class attribute (no instance) SQLAlchemy
        # Wrap the result for each call, then each call return a différent
        # object, but it is not an error
        getted = str(mam.mapper(registry, None) == 'test')
        wanted = str(registry.System.Model.name == 'test')
        assert getted == wanted
