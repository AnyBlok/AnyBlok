# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import BlokTestCase


class TestQuery(BlokTestCase):

    def test_dictone(self):
        query = self.registry.System.Model.query().filter_by(
            name='Model.System.Blok')
        model = query.one()
        self.assertEqual(query.dictone(), {
            'name': model.name,
            'table': model.table,
            'is_sql_model': model.is_sql_model,
            'description': model.description,
        })

    def test_dictone_on_some_column(self):
        query = self.registry.System.Model.query('name', 'table').filter_by(
            name='Model.System.Blok')
        model = query.one()
        self.assertEqual(query.dictone(), {
            'name': model.name,
            'table': model.table,
        })

    def test_dictone_on_some_column_with_label(self):
        M = self.registry.System.Model
        query = M.query(M.name.label('n2'), M.table.label('t2')).filter_by(
            name='Model.System.Blok')
        model = query.one()
        self.assertEqual(query.dictone(), {
            'n2': model.n2,
            't2': model.t2,
        })

    def test_dictfirst(self):
        query = self.registry.System.Model.query()
        model = query.first()
        self.assertEqual(query.dictfirst(), {
            'name': model.name,
            'table': model.table,
            'is_sql_model': model.is_sql_model,
            'description': model.description,
        })

    def test_dictfirst_on_some_column(self):
        query = self.registry.System.Model.query('name', 'table')
        model = query.first()
        self.assertEqual(query.dictfirst(), {
            'name': model.name,
            'table': model.table,
        })

    def test_dictfirst_on_some_column_with_label(self):
        M = self.registry.System.Model
        query = M.query(M.name.label('n2'), M.table.label('t2'))
        model = query.first()
        self.assertEqual(query.dictfirst(), {
            'n2': model.n2,
            't2': model.t2,
        })

    def test_dictall(self):
        query = self.registry.System.Model.query().limit(2)
        models = query.all()

        def to_dict(model):
            return {
                'name': model.name,
                'table': model.table,
                'is_sql_model': model.is_sql_model,
                'description': model.description,
            }

        dictall = query.dictall()
        for i in range(2):
            self.assertIn(to_dict(models[i]), dictall)

    def test_dictall_on_some_column(self):
        query = self.registry.System.Model.query('name', 'table').limit(2)
        models = query.all()

        def to_dict(model):
            return {
                'name': model.name,
                'table': model.table,
            }

        dictall = query.dictall()
        for i in range(2):
            self.assertIn(to_dict(models[i]), dictall)

    def test_dictall_on_some_column_with_label(self):
        M = self.registry.System.Model
        query = M.query(M.name.label('n2'), M.table.label('t2')).limit(2)
        models = query.all()

        def to_dict(model):
            return {
                'n2': model.n2,
                't2': model.t2,
            }

        dictall = query.dictall()
        for i in range(2):
            self.assertIn(to_dict(models[i]), dictall)
