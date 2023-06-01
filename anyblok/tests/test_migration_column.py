# This file is a part of the AnyBlok project
#
#    Copyright (C) 2022 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok import Declarations
from anyblok.column import Integer

from .conftest import init_registry, reset_db
from .test_column import COLUMNS, simple_column


Model = Declarations.Model
register = Declarations.register


@pytest.fixture(params=COLUMNS)
def column_definition(request, bloks_loaded):
    return request.param


def simple_column(ColumnType=None, **kwargs):
    @register(Model)
    class Test:
        id = Integer(primary_key=True)
        col = ColumnType(**kwargs)

        @classmethod
        def meth_secretkey(cls):
            return "secretkey"


@pytest.mark.column
class TestColumns:
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

    def test_migration_columns(self, column_definition):
        column, value, kwargs = column_definition
        registry = self.init_registry(
            simple_column, ColumnType=column, **kwargs
        )
        report = registry.migration.detect_changed()
        logs = [
            x
            for x in report.logs
            if not x.startswith('Drop Table')
        ]
        assert logs == []
