# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok.tests.testcase import LogCapture
from logging import DEBUG
from anyblok.registry import RegistryManager
from anyblok.environment import EnvironmentManager
from anyblok.model import (has_sql_fields, get_fields, ModelException,
                           has_sqlalchemy_fields)
from anyblok import Declarations
from anyblok.column import Integer, String
from .conftest import init_registry, reset_db

register = Declarations.register
unregister = Declarations.unregister
Model = Declarations.Model


class OneModel:
    __tablename__ = 'test'


class TestModel:

    @pytest.fixture(scope="class", autouse=True)
    def init_env(self, request):

        def revert():
            EnvironmentManager.set('current_blok', None)
            del RegistryManager.loaded_bloks['testModel']

        request.addfinalizer(revert)
        RegistryManager.init_blok('testModel')
        EnvironmentManager.set('current_blok', 'testModel')

    @pytest.fixture(autouse=True)
    def init_blok(self):
        blokname = 'testModel'
        RegistryManager.loaded_bloks[blokname]['Model'] = {
            'registry_names': []}

    def assertInModel(self, *args):
        blokname = 'testModel'
        blok = RegistryManager.loaded_bloks[blokname]
        assert len(blok['Model']['Model.MyModel']['bases']) == len(args)
        for cls_ in args:
            has = cls_ in blok['Model']['Model.MyModel']['bases']
            assert has is True

    def assertInRemoved(self, cls):
        core = RegistryManager.loaded_bloks['testModel']['removed']
        if cls in core:
            return True

        self.fail('Not in removed')

    def test_add_interface(self):
        register(Model, cls_=OneModel, name_='MyModel')
        assert 'Model' == Model.MyModel.__declaration_type__
        self.assertInModel(OneModel)
        dir(Declarations.Model.MyModel)

    def test_add_interface_with_decorator(self):

        @register(Model)
        class MyModel:
            pass

        assert 'Model' == Model.MyModel.__declaration_type__
        self.assertInModel(MyModel)

    def test_add_two_interface(self):

        register(Model, cls_=OneModel, name_="MyModel")

        @register(Model)
        class MyModel:
            pass

        self.assertInModel(OneModel, MyModel)

    def test_remove_interface_with_1_cls_in_registry(self):

        register(Model, cls_=OneModel, name_="MyModel")
        self.assertInModel(OneModel)
        unregister(Model.MyModel, OneModel)
        self.assertInModel(OneModel)
        self.assertInRemoved(OneModel)

    def test_remove_interface_with_2_cls_in_registry(self):

        register(Model, cls_=OneModel, name_="MyModel")

        @register(Model)
        class MyModel:
            pass

        self.assertInModel(OneModel, MyModel)
        unregister(Model.MyModel, OneModel)
        self.assertInModel(MyModel, OneModel)
        self.assertInRemoved(OneModel)


def simple_model():

    @register(Model)
    class Test:
        id = Integer(primary_key=True)
        name = String()


def simple_model_with_schema():

    @register(Model)
    class Test:
        __db_schema__ = 'test_db_schema'

        id = Integer(primary_key=True)
        name = String()


def simple_model_with_tablename():

    @register(Model, tablename='othername')
    class Test:
        id = Integer(primary_key=True)
        name = String()


def simple_models_with_same_table():

    @register(Model)
    class Test:
        id = Integer(primary_key=True)
        name = String()

    @register(Model, tablename='test')
    class Test2:
        id = Integer(primary_key=True)
        name = String()


def simple_models_with_same_table_by_declaration_model():

    @register(Model)
    class Test:
        id = Integer(primary_key=True)
        name = String()

    @register(Model, tablename=Model.Test)
    class Test2:
        id = Integer(primary_key=True)
        name = String()


def simple_models_with_same_table_by_inherit():

    @register(Model)
    class Test:
        id = Integer(primary_key=True)
        name = String()

    @register(Model)
    class Test2:
        id = Integer(primary_key=True)
        name = String()

    @register(Model, tablename='test')  # noqa
    class Test2:
        pass


def simple_models_with_inherit_sqlmodel():

    @register(Model)
    class Test:
        id = Integer(primary_key=True)
        name = String()

    @register(Model)
    class Test2(Model.Test):
        pass

    @register(Model)
    class Test3(Model.Test):
        pass


def model_with_foreign_key():

    @register(Model)
    class TestFk:

        name = String(primary_key=True)

    @register(Model)
    class Test:

        id = Integer(primary_key=True)
        name = String(foreign_key=Model.TestFk.use('name'))


class TestModel2:

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

    def test_anyblok_attribute(self):
        registry = self.init_registry(simple_model)
        self.check_registry(registry.Test)
        assert registry.System.anyblok is registry
        assert registry.System.Model.anyblok is registry
        t2 = registry.Test.query().first()
        registry.System.Model.anyblok.refresh(t2)

    def test_str(self):
        registry = self.init_registry(simple_model)
        test = registry.System.Model.query().get('Model.Test')
        assert str(test) == 'Model.Test'

    def test_deprecated_registry_attribute_getter(self):
        with pytest.warns(DeprecationWarning):
            registry = self.init_registry(simple_model)
            self.check_registry(registry.Test)
            # NoSQL Base must also have registry
            assert registry.System.registry
            assert registry.System.Model.registry
            assert registry.System.Model.registry is not registry
            t2 = registry.Test.query().first()
            registry.System.Model.registry.refresh(t2)

    def test_deprecated_registry_attribute_setter_1(self):
        with pytest.warns(DeprecationWarning):
            registry = self.init_registry(simple_model)
            self.check_registry(registry.Test)
            assert registry.System.registry.foo is None
            assert registry.System.anyblok.foo is None
            registry.System.registry.foo = 'bar'
            assert registry.System.registry.foo == 'bar'
            assert registry.System.anyblok.foo == 'bar'

    def test_deprecated_registry_attribute_setter_2(self):
        with pytest.warns(DeprecationWarning):
            registry = self.init_registry(simple_model)
            self.check_registry(registry.Test)
            assert registry.System.Model.registry.foo is None
            assert registry.System.Model.anyblok.foo is None
            registry.System.registry.foo = 'bar'
            assert registry.System.Model.registry.foo == 'bar'
            assert registry.System.Model.anyblok.foo == 'bar'

    def test_model_is_assembled(self):
        with LogCapture('anyblok.registry', level=DEBUG) as logs:
            self.init_registry(None)
            messages = logs.get_debug_messages()
            assert "Assemble 'Model' entry" in messages

    def test_model_is_initialized(self):
        with LogCapture('anyblok.registry', DEBUG) as logs:
            self.init_registry(None)
            messages = logs.get_debug_messages()
            assert "Initialize 'Model' entry" in messages

    def check_registry(self, Model):
        t = Model.insert(name="test")
        t2 = Model.query().first()
        assert t2 is t

    def check_registry_same_table(self, Model1, Model2):
        t = Model1.insert(name="test")
        t2 = Model2.query().first()
        assert t2.name == t.name

    def test_simple_model(self):
        registry = self.init_registry(simple_model)
        self.check_registry(registry.Test)
        model = registry.System.Model.query().get('Model.Test')
        assert model.table == 'test'
        assert model.schema is None

    def test_simple_model_with_schema(self):
        registry = self.init_registry(simple_model_with_schema)
        self.check_registry(registry.Test)
        model = registry.System.Model.query().get('Model.Test')
        assert model.table == 'test'
        assert model.schema == 'test_db_schema'

    def test_simple_model_with_tablename(self):
        registry = self.init_registry(simple_model_with_tablename)
        self.check_registry(registry.Test)
        assert registry.Test.__table__.name == 'othername'
        assert registry.Test.__tablename__ == 'othername'

    def test_simple_models_with_same_table(self):
        registry = self.init_registry(simple_models_with_same_table)
        self.check_registry_same_table(registry.Test, registry.Test2)

    def test_simple_models_with_same_table_by_declaration_model(self):
        registry = self.init_registry(
            simple_models_with_same_table_by_declaration_model)
        self.check_registry_same_table(registry.Test, registry.Test2)

    def test_simple_models_with_same_table_by_inherit(self):
        registry = self.init_registry(simple_models_with_same_table_by_inherit)
        self.check_registry_same_table(registry.Test, registry.Test2)

    def test_simple_models_with_inherit_sqlmodel(self):
        registry = self.init_registry(simple_models_with_inherit_sqlmodel)
        self.check_registry_same_table(registry.Test, registry.Test2)

    def test_simple_model_with_wrong_column(self):
        registry = self.init_registry(simple_model)

        try:
            registry.Test.insert(name="test", other="other")
            self.fail('No error when an inexisting colomn has filled')
        except TypeError:
            pass

    def test_model_with_foreign_key(self):
        registry = self.init_registry(model_with_foreign_key)
        registry.TestFk.insert(name='test')
        self.check_registry(registry.Test)

    def test_model_with_foreign_key_with_db_column_name(self):

        def model_with_foreign_key():

            @register(Model)
            class TestFk:

                name = String(primary_key=True, db_column_name='other')

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                name = String(foreign_key=Model.TestFk.use('name'))

        registry = self.init_registry(model_with_foreign_key)
        registry.TestFk.insert(name='test')
        self.check_registry(registry.Test)

    def test_table_args(self):
        val = 'one arg'

        def add_in_registry():

            @register(Model)
            class Test:

                @classmethod
                def define_table_args(cls):
                    return (val,)

        registry = self.init_registry(add_in_registry)
        assert len(registry.Test.__table_args__) == 1
        assert registry.Test.__table_args__[0] == val

    def test_table_args_with_inherit(self):
        val = 'first arg'
        val2 = 'second arg'

        def add_in_registry():

            @register(Model)
            class Test:

                @classmethod
                def define_table_args(cls):
                    return (val,)

            @register(Model)  # noqa
            class Test:

                @classmethod
                def define_table_args(cls):
                    return super(Test, cls).define_table_args() + (val2,)

        registry = self.init_registry(add_in_registry)
        assert len(registry.Test.__table_args__) == 2
        assert val in registry.Test.__table_args__
        assert val2 in registry.Test.__table_args__

    def test_table_args_in_cls_attribute(self):

        def add_in_registry():

            @register(Model)
            class Test:
                __table_args__ = ()

        with pytest.raises(ModelException):
            self.init_registry(add_in_registry)

    def test_mapper_args(self):
        val = 'one arg'

        def add_in_registry():

            @register(Model)
            class Test:

                @classmethod
                def define_mapper_args(cls):
                    return {val: val}

        registry = self.init_registry(add_in_registry)
        assert len(registry.Test.__mapper_args__) == 1
        assert registry.Test.__mapper_args__[val] == val

    def test_mapper_args_with_inherit(self):
        val = 'first arg'
        val2 = 'second arg'

        def add_in_registry():

            @register(Model)
            class Test:

                @classmethod
                def define_mapper_args(cls):
                    return {val: val}

            @register(Model)  # noqa
            class Test:

                @classmethod
                def define_mapper_args(cls):
                    mapper_args = super(Test, cls).define_mapper_args()
                    mapper_args.update({val2: val2})
                    return mapper_args

        registry = self.init_registry(add_in_registry)
        assert len(registry.Test.__mapper_args__) == 2
        assert registry.Test.__mapper_args__[val] == val
        assert registry.Test.__mapper_args__[val2] == val2

    def test_mapper_args_in_cls_attribute(self):

        def add_in_registry():

            @register(Model)
            class Test:
                __mapper_args__ = {}

        with pytest.raises(ModelException):
            self.init_registry(add_in_registry)

    def test_with_sqlalchemy_fields(self):
        from sqlalchemy import Column as SaC, String as SaS

        def add_in_registry():

            @register(Model)
            class Test:
                one_field = SaC(SaS(64))

        with pytest.raises(ModelException):
            self.init_registry(add_in_registry)

    def test_update_0(self):
        registry = self.init_registry(None)
        t = registry.System.Blok.query().first()
        t.update(**{'state': 'undefined'})
        assert t.state == 'undefined'

    def test_update_1(self):
        registry = self.init_registry(None)
        t = registry.System.Blok.query().first()
        t.update(state='undefined')
        assert t.state == 'undefined'

    def test_fix_issue_52(self):

        def add_in_registry():

            @register(Model)
            class Test:
                id = Integer(primary_key=True)
                type = String()

        registry = self.init_registry(add_in_registry)
        assert registry.Test is not None


class TestModelAssembling:

    def test_has_sql_fields_ok(self):

        class MyModel:
            one_field = String()

        assert has_sql_fields([MyModel]) is True

    def test_has_sql_fields_ko(self):

        class MyModel:
            one_field = None

        assert has_sql_fields([MyModel]) is False

    def test_get_fields(self):

        class MyModel:
            one_field = String()

        assert get_fields(MyModel) == {'one_field': MyModel.one_field}

    def test_has_sqlalchemy_fields(self):
        from sqlalchemy import Column as SaC, String as SaS

        class MyModel:
            one_field = SaC(SaS(64))

        assert has_sqlalchemy_fields(MyModel)

    def test_has_sqlalchemy_fields2(self):

        class MyModel:
            one_field = String()

        assert not (has_sqlalchemy_fields(MyModel))
