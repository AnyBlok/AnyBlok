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
from sqlalchemy.exc import IntegrityError

from anyblok import Declarations
from anyblok.column import Integer, String
from anyblok.schema import (
    ForeignKeyConstraint,
    Index,
    PrimaryKeyConstraint,
    UniqueConstraint,
)

from .conftest import init_registry, reset_db

register = Declarations.register
unregister = Declarations.unregister
Model = Declarations.Model


def registry_foreign_keys():
    @register(Model)
    class Test1:
        id = Integer(primary_key=True)
        code = String(primary_key=True, default="test")

    @register(Model)
    class Test2:
        id = Integer(primary_key=True)
        test_id = Integer()
        test_code = String()

        @classmethod
        def define_table_args(cls):
            table_args = super().define_table_args()
            Test1 = cls.anyblok.Test1
            return table_args + (
                ForeignKeyConstraint(
                    [cls.test_id, cls.test_code],
                    [Test1.id, Test1.code],
                ),
            )


def registry_unique():
    @register(Model)
    class Test:
        id = Integer(primary_key=True)
        code = String()

        @classmethod
        def define_table_args(cls):
            table_args = super().define_table_args()
            return table_args + (UniqueConstraint(cls.code),)


def registry_pk():
    @register(Model)
    class Test:
        id = Integer()
        code = String()

        @classmethod
        def define_table_args(cls):
            table_args = super().define_table_args()
            return table_args + (PrimaryKeyConstraint(cls.id, cls.code),)


def registry_index():
    @register(Model)
    class Test:
        id = Integer(primary_key=True)
        code = String()

        @classmethod
        def define_table_args(cls):
            table_args = super().define_table_args()
            return table_args + (Index("idx_code", cls.code),)


class TestSchema:
    @pytest.fixture(autouse=True)
    def close_registry(self, request, bloks_loaded):
        def close():
            if hasattr(self, "registry"):
                self.registry.close()

        request.addfinalizer(close)

    def init_registry(self, *args, **kwargs):
        reset_db()
        self.registry = init_registry(*args, **kwargs)
        return self.registry

    def test_fk(self):
        registry = self.init_registry(registry_foreign_keys)
        t1 = registry.Test1.insert()
        registry.Test2.insert(test_id=t1.id, test_code=t1.code)

    def test_unique(self):
        registry = self.init_registry(registry_unique)
        registry.Test.insert(code="unique")
        with pytest.raises(IntegrityError):
            registry.Test.insert(code="unique")

    def test_pk(self):
        registry = self.init_registry(registry_pk)
        registry.Test.insert(id=1, code="pk")

    def test_index(self):
        registry = self.init_registry(registry_index)
        registry.Test.insert(code="index")
