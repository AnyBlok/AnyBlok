# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import BlokTestCase


class TestCoreSqlBase(BlokTestCase):

    def test_insert(self):
        Blok = self.registry.System.Blok
        Blok.insert(name='OneBlok', state='undefined', version='0.0.0')
        blok = Blok.query().filter(Blok.name == 'OneBlok').first()
        self.assertEqual(blok.state, 'undefined')

    def test_multi_insert(self):
        Blok = self.registry.System.Blok
        Blok.multi_insert(
            dict(name='OneBlok', state='undefined', version='0.0.0'),
            dict(name='TwoBlok', state='undefined', version='0.0.0'),
            dict(name='ThreeBlok', state='undefined', version='0.0.0'))
        states = Blok.query('state').filter(Blok.name.in_(['OneBlok',
                                                           'TwoBlok',
                                                           'ThreeBlok'])).all()
        states = [x[0] for x in states]
        self.assertEqual(states, ['undefined', 'undefined', 'undefined'])

    def test_from_primary_key(self):
        Model = self.registry.System.Model
        model = Model.query().first()
        model2 = Model.from_primary_keys(name=model.name)
        self.assertEqual(model, model2)

    def test_from_primary_keys(self):
        Column = self.registry.System.Column
        column = Column.query().first()
        column2 = Column.from_primary_keys(model=column.model,
                                           name=column.name)
        self.assertEqual(column, column2)

    def test_get_primary_key(self):
        self.assertEqual(self.registry.System.Model.get_primary_keys(),
                         ['name'])

    def test_get_primary_keys(self):
        pks = self.registry.System.Column.get_primary_keys()
        model_in_pks = 'model' in pks
        name_in_pks = 'name' in pks
        self.assertEqual(model_in_pks, True)
        self.assertEqual(name_in_pks, True)

    def test_to_primary_key(self):
        model = self.registry.System.Model.query().first()
        self.assertEqual(model.to_primary_keys(), dict(name=model.name))

    def test_to_primary_keys(self):
        column = self.registry.System.Column.query().first()
        self.assertEqual(column.to_primary_keys(),
                         {'model': column.model, 'name': column.name})
