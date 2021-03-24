# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Denis VIVIÈS <dvivies@geoblink.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest


@pytest.mark.usefixtures('rollback_registry')
class TestQueryScope:
    def test_dictone(self, rollback_registry):
        registry = rollback_registry
        query = registry.System.Model.query().filter_by(
            name='Model.System.Blok')
        model = query.one()
        assert query.dictone() == {
            'name': model.name,
            'table': model.table,
            'schema': model.schema,
            'is_sql_model': model.is_sql_model,
            'description': model.description,
        }

    def test_dictone_on_some_column(self, rollback_registry):
        registry = rollback_registry
        query = registry.System.Model.query('name', 'table').filter(
            registry.System.Model.name == 'Model.System.Blok')
        model = query.one()
        assert query.dictone() == {
            'name': model.name,
            'table': model.table,
        }

    def test_dictone_on_some_column_with_label(self, rollback_registry):
        registry = rollback_registry
        M = registry.System.Model
        query = M.query(M.name.label('n2'), M.table.label('t2')).filter(
            registry.System.Model.name == 'Model.System.Blok')
        model = query.one()
        assert query.dictone() == {
            'n2': model.n2,
            't2': model.t2,
        }

    def test_dictfirst(self, rollback_registry):
        registry = rollback_registry
        query = registry.System.Model.query()
        model = query.first()
        assert query.dictfirst() == {
            'name': model.name,
            'table': model.table,
            'schema': model.schema,
            'is_sql_model': model.is_sql_model,
            'description': model.description,
        }

    def test_dictfirst_on_some_column(self, rollback_registry):
        registry = rollback_registry
        query = registry.System.Model.query('name', 'table')
        model = query.first()
        assert query.dictfirst() == {
            'name': model.name,
            'table': model.table,
        }

    def test_dictfirst_on_some_column_with_label(self, rollback_registry):
        registry = rollback_registry
        M = registry.System.Model
        query = M.query(M.name.label('n2'), M.table.label('t2'))
        model = query.first()
        assert query.dictfirst() == {
            'n2': model.n2,
            't2': model.t2,
        }

    def test_dictall(self, rollback_registry):
        registry = rollback_registry
        query = registry.System.Model.query().limit(2)
        models = query.all()

        def to_dict(model):
            return {
                'name': model.name,
                'table': model.table,
                'schema': model.schema,
                'is_sql_model': model.is_sql_model,
                'description': model.description,
            }

        dictall = query.dictall()
        for i in range(2):
            assert to_dict(models[i]) in dictall

    def test_dictall_on_some_column(self, rollback_registry):
        registry = rollback_registry
        query = registry.System.Model.query('name', 'table').limit(2)
        models = query.all()

        def to_dict(model):
            return {
                'name': model.name,
                'table': model.table,
            }

        dictall = query.dictall()
        for i in range(2):
            assert to_dict(models[i]) in dictall

    def test_dictall_on_some_column_with_label(self, rollback_registry):
        registry = rollback_registry
        M = registry.System.Model
        query = M.query(M.name.label('n2'), M.table.label('t2')).limit(2)
        models = query.all()

        def to_dict(model):
            return {
                'n2': model.n2,
                't2': model.t2,
            }

        dictall = query.dictall()
        for i in range(2):
            assert to_dict(models[i]) in dictall

    def test_get_with_dict_use_prefix(self, rollback_registry):
        registry = rollback_registry
        M = registry.System.Field
        entry = M.query().get({'name': 'name', 'model': 'Model.System.Blok'})
        assert entry is not None

    def test_get_with_kwargs(self, rollback_registry):
        registry = rollback_registry
        M = registry.System.Field
        entry = M.query().get(name='name', model='Model.System.Blok')
        assert entry is not None
