# This file is a part of the AnyBlok project
#
#    Copyright (C) 2023 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest

from anyblok import Declarations
from anyblok.column import Integer, String
from anyblok.relationship import Many2Many, Many2One, One2One

from .conftest import init_registry, reset_db

Model = Declarations.Model
register = Declarations.register


def column_with_foreign_key():
    @register(Model)
    class Test:
        id = Integer(primary_key=True)
        test = String(foreign_key=Model.System.Model.use("name"), size=256)


def _minimum_many2one():
    @register(Model)
    class Test:
        id = Integer(primary_key=True)
        model = Many2One(model=Model.System.Model)


def _minimum_one2one():
    @register(Model)
    class Test:
        id = Integer(primary_key=True)
        model = One2One(model=Model.System.Model, backref="test")


def _minimum_many2many(**kwargs):
    @register(Model)
    class Test:
        id = Integer(primary_key=True)
        addresses = Many2Many(model=Model.System.Model)


@pytest.mark.column
class TestDeprecatedModels:
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
        self.init_registry(column_with_foreign_key)

    def test_relationship_m2o(self):
        self.init_registry(_minimum_many2one)

    def test_relationship_o2o(self):
        self.init_registry(_minimum_one2one)

    def test_relationship_m2m(self):
        self.init_registry(_minimum_many2many)
