# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok.declarations import Declarations, hybrid_method
from anyblok.column import Integer
from .conftest import init_registry

register = Declarations.register
Model = Declarations.Model
Mixin = Declarations.Mixin
Core = Declarations.Core


class TestHybridMethod:

    @pytest.fixture(autouse=True)
    def close_registry(self, request, bloks_loaded):

        def close():
            if hasattr(self, 'registry'):
                self.registry.close()

        request.addfinalizer(close)

    def init_registry(self, *args, **kwargs):
        self.registry = init_registry(*args, **kwargs)
        return self.registry

    def check_hybrid_method(self, Test):
        t1 = Test.insert(val=1)
        t2 = Test.insert(val=2)
        assert t1.val_is(1) is True
        assert t1.val_is(2) is False
        assert t2.val_is(1) is False
        assert t2.val_is(2) is True
        query = Test.query().filter(Test.val_is(1))
        assert query.count() == 1
        assert query.first() is t1
        query = Test.query().filter(Test.val_is(2))
        assert query.count() == 1
        assert query.first() is t2

    def test_hybrid_method_model(self):

        def add_in_registry():

            @register(Model)
            class Test:
                id = Integer(primary_key=True)
                val = Integer(nullable=False)

                @hybrid_method
                def val_is(self, val):
                    return self.val == val

        registry = self.init_registry(add_in_registry)
        self.check_hybrid_method(registry.Test)

    def test_hybrid_method_model2(self):

        def add_in_registry():

            @register(Model)
            class Test:
                id = Integer(primary_key=True)
                val = Integer(nullable=False)

                # check decorator with ()
                @hybrid_method()
                def val_is(self, val):
                    return self.val == val

        registry = self.init_registry(add_in_registry)
        self.check_hybrid_method(registry.Test)

    def test_hybrid_method_core(self):

        def add_in_registry():

            @register(Core)
            class SqlBase:

                @hybrid_method
                def val_is(self, val):
                    return self.val == val

            @register(Model)
            class Test:
                id = Integer(primary_key=True)
                val = Integer(nullable=False)

        registry = self.init_registry(add_in_registry)
        self.check_hybrid_method(registry.Test)

    def test_hybrid_method_mixin(self):

        def add_in_registry():

            @register(Mixin)
            class MTest:
                id = Integer(primary_key=True)
                val = Integer(nullable=False)

                @hybrid_method
                def val_is(self, val):
                    return self.val == val

            @register(Model)
            class Test(Mixin.MTest):
                pass

        registry = self.init_registry(add_in_registry)
        self.check_hybrid_method(registry.Test)

    def test_hybrid_with_alias(self):

        def add_in_registry():

            @register(Model)
            class Test:
                id = Integer(primary_key=True)
                val = Integer(nullable=False)

                @hybrid_method
                def val_is(self, val):
                    return self.val == val

        registry = self.init_registry(add_in_registry)
        self.check_hybrid_method(registry.Test)
        Test = registry.Test.aliased()
        query = Test.query().filter(Test.val_is(1))
        assert query.count() == 1
        query = Test.query().filter(Test.val_is(2))
        assert query.count() == 1

    def add_inherited_hybrid_method(self, withcore=False, withmixin=False,
                                    withmodel=False):

        @register(Core)
        class SqlBase:

            if withcore:
                @hybrid_method
                def val_is(self, val):
                    pass

        @register(Mixin)
        class MTest:
            id = Integer(primary_key=True)
            val = Integer(nullable=False)

            if withmixin:
                @hybrid_method
                def val_is(self, val):
                    pass

        @register(Model)
        class Test(Mixin.MTest):

            if withmodel:
                @hybrid_method
                def val_is(self, val):
                    pass

        @register(Model)  # noqa
        class Test:

            def val_is(self, val):
                return self.val == val

    def test_inherit_core(self):
        registry = self.init_registry(self.add_inherited_hybrid_method,
                                      withcore=True)
        self.check_hybrid_method(registry.Test)

    def test_inherit_mixin(self):
        registry = self.init_registry(self.add_inherited_hybrid_method,
                                      withmixin=True)
        self.check_hybrid_method(registry.Test)

    def test_inherit_model(self):
        registry = self.init_registry(self.add_inherited_hybrid_method,
                                      withmodel=True)
        self.check_hybrid_method(registry.Test)

    def test_inherit_core_and_mixin(self):
        registry = self.init_registry(self.add_inherited_hybrid_method,
                                      withcore=True, withmixin=True)
        self.check_hybrid_method(registry.Test)

    def test_inherit_core_and_model(self):
        registry = self.init_registry(self.add_inherited_hybrid_method,
                                      withcore=True, withmodel=True)
        self.check_hybrid_method(registry.Test)

    def test_inherit_mixin_and_model(self):
        registry = self.init_registry(self.add_inherited_hybrid_method,
                                      withmixin=True, withmodel=True)
        self.check_hybrid_method(registry.Test)

    def test_inherit_core_and_mixin_and_model(self):
        registry = self.init_registry(self.add_inherited_hybrid_method,
                                      withcore=True, withmixin=True,
                                      withmodel=True)
        self.check_hybrid_method(registry.Test)
