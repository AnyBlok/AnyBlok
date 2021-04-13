# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Denis VIVIÈS <dvivies@geoblink.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest


@pytest.mark.usefixtures('rollback_registry')
class TestCoreSqlBase:

    def test_insert(self, rollback_registry):
        registry = rollback_registry
        Blok = registry.System.Blok
        Blok.insert(name='OneBlok', state='undefined', version='0.0.0')
        blok = Blok.query().filter(Blok.name == 'OneBlok').first()
        assert blok.state == 'undefined'

    def test_multi_insert(self, rollback_registry):
        registry = rollback_registry
        Blok = registry.System.Blok
        Blok.multi_insert(
            dict(name='OneBlok', state='undefined', version='0.0.0'),
            dict(name='TwoBlok', state='undefined', version='0.0.0'),
            dict(name='ThreeBlok', state='undefined', version='0.0.0'))
        states = Blok.query('state').filter(Blok.name.in_(['OneBlok',
                                                           'TwoBlok',
                                                           'ThreeBlok'])).all()
        states = [x[0] for x in states]
        assert states == ['undefined', 'undefined', 'undefined']

    def test_from_primary_key(self, rollback_registry):
        registry = rollback_registry
        Model = registry.System.Model
        model = Model.query().first()
        model2 = Model.from_primary_keys(name=model.name)
        assert model == model2

    def test_from_primary_keys(self, rollback_registry):
        registry = rollback_registry
        Column = registry.System.Column
        column = Column.query().first()
        column2 = Column.from_primary_keys(model=column.model,
                                           name=column.name)
        assert column == column2

    def test_get_primary_key(self, rollback_registry):
        registry = rollback_registry
        assert registry.System.Model.get_primary_keys() == ['name']

    def test_get_primary_keys(self, rollback_registry):
        registry = rollback_registry
        pks = registry.System.Column.get_primary_keys()
        model_in_pks = 'model' in pks
        name_in_pks = 'name' in pks
        assert model_in_pks is True
        assert name_in_pks is True

    def test_to_primary_key(self, rollback_registry):
        registry = rollback_registry
        model = registry.System.Model.query().first()
        assert model.to_primary_keys() == dict(name=model.name)

    def test_to_primary_keys(self, rollback_registry):
        registry = rollback_registry
        column = registry.System.Column.query().first()
        assert column.to_primary_keys() == {
            'model': column.model, 'name': column.name}

    def test_fields_description(self, rollback_registry):
        registry = rollback_registry
        Model = registry.System.Model
        res = {'description': {'id': 'description',
                               'label': 'Description',
                               'model': None,
                               'nullable': True,
                               'primary_key': False,
                               'type': 'Function'},
               'is_sql_model': {'id': 'is_sql_model',
                                'label': 'Is a SQL model',
                                'model': None,
                                'nullable': True,
                                'primary_key': False,
                                'type': 'Boolean'},
               'name': {'id': 'name',
                        'label': 'Name',
                        'model': None,
                        'nullable': False,
                        'primary_key': True,
                        'type': 'String'},
               'table': {'id': 'table',
                         'label': 'Table',
                         'model': None,
                         'nullable': True,
                         'primary_key': False,
                         'type': 'String'},
               'schema': {'id': 'schema',
                          'label': 'Schema',
                          'model': None,
                          'nullable': True,
                          'primary_key': False,
                          'type': 'String'}}
        assert Model.fields_description() == res

    def test_fields_description_limited_field(self, rollback_registry):
        registry = rollback_registry
        Model = registry.System.Model
        res = {'table': {'id': 'table',
                         'label': 'Table',
                         'model': None,
                         'nullable': True,
                         'primary_key': False,
                         'type': 'String'}}
        assert Model.fields_description(fields=['table']) == res

    def test_fields_description_cache(self, rollback_registry):
        registry = rollback_registry
        Model = registry.System.Model
        Column = registry.System.Column
        res = {'table': {'id': 'table',
                         'label': 'Table',
                         'model': None,
                         'nullable': True,
                         'primary_key': False,
                         'type': 'String'}}
        assert Model.fields_description(fields=['table']) == res
        column = Column.from_primary_keys(model='Model.System.Model',
                                          name='table')
        column.label = 'Test'
        assert Model.fields_description(fields=['table']) == res
        Model.fire('Update Model', 'Model.System.Model')
        assert Model.fields_description(fields=['table']) != res

    def test_to_dict(self, rollback_registry):
        registry = rollback_registry
        M = registry.System.Model
        model = M.query().first()
        assert model.to_dict() == {
            'name': model.name,
            'table': model.table,
            'schema': model.schema,
            'is_sql_model': model.is_sql_model,
            'description': model.description,
        }

    def test_to_dict_on_some_columns(self, rollback_registry):
        registry = rollback_registry
        M = registry.System.Model
        model = M.query().first()
        assert model.to_dict('name', 'table') == {
            'name': model.name,
            'table': model.table,
        }

    def test_select_sql_statement_with_column(self, rollback_registry):
        registry = rollback_registry
        Blok = registry.System.Blok
        assert Blok.execute_sql_statement(
            Blok.select_sql_statement('name').where(
                Blok.name == 'anyblok-core').limit(1)
        ).one() == ('anyblok-core',)

    def test_from_multi_primary_keys(self, rollback_registry):
        registry = rollback_registry
        Blok = registry.System.Blok
        blok_names = Blok.from_multi_primary_keys(
            dict(name='anyblok-core'),
            dict(name='anyblok-test'),
        ).name
        assert 'anyblok-core' in blok_names
        assert 'anyblok-test' in blok_names

    def test_from_multi_primary_keys_empty(self, rollback_registry):
        registry = rollback_registry
        Blok = registry.System.Blok
        assert Blok.from_multi_primary_keys() == []

    def test_get_hybrid_property_columns(self, rollback_registry):
        registry = rollback_registry
        Column = registry.System.Column
        columns = Column.get_hybrid_property_columns()
        for x in ['name', 'model', 'autoincrement', 'foreign_key',
                  'primary_key', 'unique', 'nullable', 'remote_model']:
            assert x in columns
