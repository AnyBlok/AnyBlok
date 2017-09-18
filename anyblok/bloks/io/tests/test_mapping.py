# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import BlokTestCase
from ..exceptions import IOMappingSetException


class TestIOMapping(BlokTestCase):

    def setUp(self):
        super(TestIOMapping, self).setUp()
        self.Mapping = self.registry.IO.Mapping
        self.Model = self.registry.System.Model
        self.Column = self.registry.System.Column
        self.Field = self.registry.System.Field
        self.Blok = self.registry.System.Blok

    def test_set_primary_key(self):
        model = self.Model.query().first()
        res = self.Mapping.set_primary_keys(
            model.__registry_name__, 'test_set_pk', dict(name=model.name))
        query = self.Mapping.query()
        query = query.filter(self.Mapping.key == 'test_set_pk')
        self.assertEqual(query.count(), 1)
        mapping = query.first()
        self.assertEqual(mapping, res)
        self.assertEqual(mapping.model, model.__registry_name__)
        self.assertEqual(mapping.primary_key, dict(name=model.name))

    def test_set_primary_keys(self):
        column = self.Column.query().first()
        res = self.Mapping.set_primary_keys(
            column.__registry_name__, 'test_set_pks',
            dict(model=column.model, name=column.name))
        query = self.Mapping.query()
        query = query.filter(self.Mapping.key == 'test_set_pks')
        self.assertEqual(query.count(), 1)
        mapping = query.first()
        self.assertEqual(mapping, res)
        self.assertEqual(mapping.model, column.__registry_name__)
        self.assertEqual(mapping.primary_key,
                         dict(model=column.model, name=column.name))

    def test_set(self):
        column = self.Column.query().first()
        res = self.Mapping.set('test_set', column)
        query = self.Mapping.query()
        query = query.filter(self.Mapping.key == 'test_set')
        self.assertEqual(query.count(), 1)
        mapping = query.first()
        self.assertEqual(mapping, res)
        self.assertEqual(mapping.model, column.__registry_name__)
        self.assertEqual(mapping.primary_key,
                         dict(model=column.model, name=column.name))

    def test_get_primary_key(self):
        model = self.Model.query().first()
        self.Mapping.set_primary_keys(
            model.__registry_name__, 'test_get_pk', dict(name=model.name))
        mapping = self.Mapping.get_mapping_primary_keys(
            model.__registry_name__, 'test_get_pk')
        self.assertEqual(mapping, dict(name=model.name))

    def test_get_primary_keys(self):
        column = self.Column.query().first()
        self.Mapping.set_primary_keys(
            column.__registry_name__, 'test_get_pks',
            dict(model=column.model, name=column.name))
        mapping = self.Mapping.get_mapping_primary_keys(
            column.__registry_name__, 'test_get_pks')
        self.assertEqual(mapping, dict(model=column.model, name=column.name))

    def test_get(self):
        column = self.Column.query().first()
        self.Mapping.set('test_get', column)
        mapping = self.Mapping.get(column.__registry_name__, 'test_get')
        self.assertEqual(mapping, column)

    def test_delete(self):
        column = self.Column.query().first()
        self.Mapping.set('test_delete', column)
        mapping = self.Mapping.get(column.__registry_name__, 'test_delete')
        self.assertEqual(mapping, column)
        self.Mapping.delete(column.__registry_name__, 'test_delete')
        mapping = self.Mapping.get(column.__registry_name__, 'test_delete')
        self.assertEqual(mapping, None)

    def test_multi_delete(self):
        columns = {'test_%s' % m.code: m
                   for m in self.Column.query().limit(5).all()}
        model = self.Column.__registry_name__

        # create all
        for key, instance in columns.items():
            self.Mapping.set(key, instance)

        # check all
        for key, instance in columns.items():
            mapping = self.Mapping.get(model, key)
            self.assertEqual(mapping, instance)

        # delete all
        self.Mapping.multi_delete(model, *columns.keys())

        # check all
        for key, instance in columns.items():
            mapping = self.Mapping.get(model, key)
            self.assertNotEqual(mapping, instance)
            self.assertEqual(mapping, None)

    def test_multi_set_the_same_key_with_raise(self):
        column = self.Column.query().first()
        self.Mapping.set('test_set', column)
        with self.assertRaises(IOMappingSetException):
            self.Mapping.set('test_set', column)

    def test_multi_set_the_same_key_without_raise(self):
        column = self.Column.query().first()
        self.Mapping.set('test_set', column)
        self.Mapping.set('test_set', column, raiseifexist=False)

    def test_clean_all(self):
        blok = self.Blok.insert(name='Test', version='0.0.0')
        self.Mapping.set('test', blok)
        self.registry.execute("DELETE FROM system_blok WHERE name='Test'")
        self.assertTrue(self.Mapping.query().filter_by(
            key='test', model='Model.System.Blok').count())
        removed = self.Mapping.clean()
        self.assertEqual(removed, 1)
        self.assertFalse(self.Mapping.query().filter_by(
            key='test', model='Model.System.Blok').count())

    def test_clean_by_bloknames(self):
        self.Blok.insert(name='Test', version='0.0.0')
        blok = self.Blok.insert(name='Test2', version='0.0.0')
        self.Mapping.set('test', blok, blokname='Test')
        self.registry.execute("DELETE FROM system_blok WHERE name='Test2'")
        self.assertTrue(self.Mapping.query().filter_by(
            key='test', model='Model.System.Blok').count())
        removed = self.Mapping.clean(bloknames=['wrong'])
        self.assertEqual(removed, 0)
        self.assertTrue(self.Mapping.query().filter_by(
            key='test', model='Model.System.Blok').count())
        removed = self.Mapping.clean(bloknames=['Test'])
        self.assertEqual(removed, 1)
        self.assertFalse(self.Mapping.query().filter_by(
            key='test', model='Model.System.Blok').count())

    def test_clean_by_blokname(self):
        self.Blok.insert(name='Test', version='0.0.0')
        blok = self.Blok.insert(name='Test2', version='0.0.0')
        self.Mapping.set('test', blok, blokname='Test')
        self.registry.execute("DELETE FROM system_blok WHERE name='Test2'")
        self.assertTrue(self.Mapping.query().filter_by(
            key='test', model='Model.System.Blok').count())
        self.Mapping.clean(bloknames='Test')
        self.assertFalse(self.Mapping.query().filter_by(
            key='test', model='Model.System.Blok').count())

    def test_clean_by_models_1(self):
        blok = self.Blok.insert(name='Test', version='0.0.0')
        self.Mapping.set('test', blok)
        self.registry.execute("DELETE FROM system_blok WHERE name='Test'")
        self.assertTrue(self.Mapping.query().filter_by(
            key='test', model='Model.System.Blok').count())
        self.Mapping.clean(models=['Model.System.Column'])
        self.assertTrue(self.Mapping.query().filter_by(
            key='test', model='Model.System.Blok').count())
        self.Mapping.clean(models=['Model.System.Blok'])
        self.assertFalse(self.Mapping.query().filter_by(
            key='test', model='Model.System.Blok').count())

    def test_clean_by_models_2(self):
        blok = self.Blok.insert(name='Test', version='0.0.0')
        self.Mapping.set('test', blok)
        self.registry.execute("DELETE FROM system_blok WHERE name='Test'")
        self.assertTrue(self.Mapping.query().filter_by(
            key='test', model='Model.System.Blok').count())
        self.Mapping.clean(models=[self.Column])
        self.assertTrue(self.Mapping.query().filter_by(
            key='test', model='Model.System.Blok').count())
        self.Mapping.clean(models=[self.Blok])
        self.assertFalse(self.Mapping.query().filter_by(
            key='test', model='Model.System.Blok').count())

    def test_clean_by_model(self):
        blok = self.Blok.insert(name='Test', version='0.0.0')
        self.Mapping.set('test', blok)
        self.registry.execute("DELETE FROM system_blok WHERE name='Test'")
        self.assertTrue(self.Mapping.query().filter_by(
            key='test', model='Model.System.Blok').count())
        self.Mapping.clean(models=self.Blok)
        self.assertFalse(self.Mapping.query().filter_by(
            key='test', model='Model.System.Blok').count())

    def test_detect_key_from_model_and_primary_key(self):
        Mapping = self.registry.IO.Mapping
        Blok = self.registry.System.Blok

        values = []
        for i, blok in enumerate(Blok.query().all()):
            values.append(dict(key='key_%d' % i, model=Blok.__registry_name__,
                               primary_key=blok.to_primary_keys()))

        Mapping.multi_insert(*values)
        mapping = Mapping.get_from_model_and_primary_keys(
            Blok.__registry_name__, blok.to_primary_keys())
        entry = Mapping.get(blok.__registry_name__, mapping.key)
        self.assertEqual(entry, blok)

    def test_delete_for_blokname(self):
        self.Blok.insert(name='Test', version='0.0.0')
        self.assertFalse(
            self.Mapping.query().filter_by(blokname="Test").count()
        )
        for column in self.Column.query().limit(10).all():
            self.Mapping.set('test_' + column.code, column, blokname='Test')
        self.assertTrue(
            self.Mapping.query().filter_by(blokname="Test").count()
        )
        removed = self.Mapping.delete_for_blokname('Test')
        self.assertEqual(removed, 10)
        self.assertFalse(
            self.Mapping.query().filter_by(blokname="Test").count()
        )

    def test_delete_for_blokname_filter_by_model_1(self):
        self.Blok.insert(name='Test', version='0.0.0')
        nb_column = self.Column.query().count()
        self.assertFalse(
            self.Mapping.query().filter_by(blokname="Test").count()
        )
        for field in self.Field.query().all():
            self.Mapping.set('test_' + field.code, field, blokname='Test')

        self.assertEqual(
            self.Mapping.query().filter_by(blokname="Test").count(),
            self.Field.query().count()
        )
        removed = self.Mapping.delete_for_blokname(
            'Test', ['Model.System.Column'])
        self.assertEqual(removed, nb_column)

    def test_delete_for_blokname_filter_by_model_2(self):
        nb_column = self.Column.query().count()
        self.Blok.insert(name='Test', version='0.0.0')
        self.assertFalse(
            self.Mapping.query().filter_by(blokname="Test").count()
        )
        for field in self.Field.query().all():
            self.Mapping.set('test_' + field.code, field, blokname='Test')

        self.assertEqual(
            self.Mapping.query().filter_by(blokname="Test").count(),
            self.Field.query().count()
        )
        removed = self.Mapping.delete_for_blokname(
            'Test', [self.registry.System.Column])
        self.assertEqual(removed, nb_column)

    def test_delete_for_blokname_filter_by_model_3(self):
        nb_column = self.Column.query().count()
        self.Blok.insert(name='Test', version='0.0.0')
        self.assertFalse(
            self.Mapping.query().filter_by(blokname="Test").count()
        )
        for field in self.Field.query().all():
            self.Mapping.set('test_' + field.code, field, blokname='Test')

        self.assertEqual(
            self.Mapping.query().filter_by(blokname="Test").count(),
            self.Field.query().count()
        )
        removed = self.Mapping.delete_for_blokname(
            'Test', self.registry.System.Column)
        self.assertEqual(removed, nb_column)
