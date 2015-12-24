# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import DBTestCase
from anyblok.column import Integer, String, Selection
from anyblok.relationship import Many2One, One2One, Many2Many, One2Many
from anyblok.declarations import Declarations
from anyblok.bloks.anyblok_core.exceptions import SqlBaseException


Model = Declarations.Model
register = Declarations.register


class TestCoreSQLBase(DBTestCase):

    def declare_model(self):
        from anyblok import Declarations
        Model = Declarations.Model

        @Declarations.register(Model)
        class Test:
            id = Integer(primary_key=True)
            id2 = Integer()

    def test_insert_and_query(self):
        registry = self.init_registry(self.declare_model)
        t1 = registry.Test.insert(id2=1)
        self.assertEqual(registry.Test.query().first(), t1)

    def test_multi_insert(self):
        registry = self.init_registry(self.declare_model)
        nb_value = 3
        registry.Test.multi_insert(*[{'id2': x} for x in range(nb_value)])
        self.assertEqual(registry.Test.query().count(), nb_value)
        for x in range(nb_value):
            self.assertEqual(
                registry.Test.query().filter(
                    registry.Test.id2 == x).count(),
                1)

    def test_delete(self):
        registry = self.init_registry(self.declare_model)
        nb_value = 3
        registry.Test.multi_insert(*[{'id2': x} for x in range(nb_value)])
        self.assertEqual(registry.Test.query().count(), nb_value)
        t = registry.Test.query().first()
        id2 = t.id2
        t.delete()
        self.assertEqual(registry.Test.query().count(), nb_value - 1)
        self.assertEqual(
            registry.Test.query().filter(
                registry.Test.id2 != id2).count(),
            nb_value - 1)

    def test_expire(self):
        registry = self.init_registry(self.declare_model)
        t = registry.Test.insert(id2=2)
        self.assertEqual(t.__dict__.get('id2'), 2)
        t.expire()
        self.assertIsNone(t.__dict__.get('id2'))

    def test_refresh(self):
        registry = self.init_registry(self.declare_model)
        t = registry.Test.insert(id2=2)
        self.assertEqual(t.__dict__.get('id2'), 2)
        t.id2 = 3
        self.assertEqual(t.__dict__.get('id2'), 3)
        t.refresh()
        self.assertEqual(t.__dict__.get('id2'), 2)

    def test_delete_entry_added_in_relationship(self):
        registry = self.init_registry(self.add_in_registry_m2o)
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        self.assertEqual(len(t1.test2), 1)
        t2.delete()
        self.assertEqual(len(t1.test2), 0)

    def test_update(self):
        registry = self.init_registry(self.declare_model)
        nb_value = 3
        registry.Test.multi_insert(*[{'id2': x} for x in range(nb_value)])
        t = registry.Test.query().first()
        t.update({registry.Test.id2: 100})
        self.assertEqual(
            registry.Test.query().filter(
                registry.Test.id2 == 100).first(),
            t)

    def test_get_primary_keys(self):
        registry = self.init_registry(self.declare_model)
        self.assertEqual(registry.Test.get_primary_keys(), ['id'])

    def test_to_and_from_primary_keys(self):
        registry = self.init_registry(self.declare_model)
        nb_value = 3
        registry.Test.multi_insert(*[{'id2': x} for x in range(nb_value)])
        t = registry.Test.query().first()
        self.assertEqual(t.to_primary_keys(), {'id': t.id})
        self.assertEqual(registry.Test.from_primary_keys(id=t.id), t)

    def add_in_registry_m2o(self):

        @register(Model)
        class Test:
            id = Integer(primary_key=True)
            name = String()

        @register(Model)
        class Test2:
            id = Integer(primary_key=True)
            name = String()
            test = Many2One(model=Model.Test, one2many="test2")

    def add_in_registry_o2m(self):

        @register(Model)
        class Test:
            id = Integer(primary_key=True)
            name = String()

        @register(Model)
        class Test2:
            id = Integer(primary_key=True)
            name = String()
            test_id = Integer(foreign_key=Model.Test.use('id'))

        @register(Model)  # noqa
        class Test:
            test2 = One2Many(model=Model.Test2, many2one="test")

    def add_in_registry_o2o(self):

        @register(Model)
        class Test:
            id = Integer(primary_key=True)
            name = String()

        @register(Model)
        class Test2:
            id = Integer(primary_key=True)
            name = String()
            test = One2One(model=Model.Test, backref='test2')

    def add_in_registry_m2m(self):

        @register(Model)
        class Test:
            id = Integer(primary_key=True)
            name = String()

        @register(Model)
        class Test2:
            id = Integer(primary_key=True)
            name = String()
            test = Many2Many(model=Model.Test, many2many='test2')

    def test_to_dict_m2o_with_pks(self):
        registry = self.init_registry(self.add_in_registry_m2o)
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        self.assertEqual(t1.to_dict('name'), {'name': 't1'})
        self.assertEqual(t2.to_dict('name'), {'name': 't2'})
        self.assertEqual(t2.to_dict('name', 'test'),
                         {'name': 't2', 'test': {'id': t1.id}})

    def test_to_dict_o2o_with_pks(self):
        registry = self.init_registry(self.add_in_registry_o2o)
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        self.assertEqual(t1.to_dict('name'), {'name': 't1'})
        self.assertEqual(t2.to_dict('name'), {'name': 't2'})
        self.assertEqual(t2.to_dict('name', 'test'),
                         {'name': 't2', 'test': {'id': t1.id}})
        self.assertEqual(t1.to_dict('name', 'test2'),
                         {'name': 't1', 'test2': {'id': t2.id}})

    def test_to_dict_m2m_with_pks(self):
        registry = self.init_registry(self.add_in_registry_m2m)
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2')
        t2.test.append(t1)
        self.assertEqual(t1.to_dict('name'), {'name': 't1'})
        self.assertEqual(t2.to_dict('name'), {'name': 't2'})
        self.assertEqual(t2.to_dict('name', 'test'),
                         {'name': 't2', 'test': [{'id': t1.id}]})
        self.assertEqual(t1.to_dict('name', 'test2'),
                         {'name': 't1', 'test2': [{'id': t2.id}]})

    def test_to_dict_o2m_with_pks(self):
        registry = self.init_registry(self.add_in_registry_m2o)
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        self.assertEqual(t1.to_dict('name', 'test2'),
                         {'name': 't1', 'test2': [{'id': t2.id}]})

    def test_to_dict_m2o_with_column(self):
        registry = self.init_registry(self.add_in_registry_m2o)
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        self.assertEqual(t2.to_dict('name', ('test', ('name',))),
                         {'name': 't2', 'test': {'name': 't1'}})

    def test_to_dict_o2o_with_column(self):
        registry = self.init_registry(self.add_in_registry_o2o)
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        self.assertEqual(t2.to_dict('name', ('test', ('name',))),
                         {'name': 't2', 'test': {'name': 't1'}})
        self.assertEqual(t1.to_dict('name', ('test2', ('name',))),
                         {'name': 't1', 'test2': {'name': 't2'}})

    def test_to_dict_m2m_with_column(self):
        registry = self.init_registry(self.add_in_registry_m2m)
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2')
        t2.test.append(t1)
        self.assertEqual(t2.to_dict('name', ('test', ('name',))),
                         {'name': 't2', 'test': [{'name': 't1'}]})
        self.assertEqual(t1.to_dict('name', ('test2', ('name',))),
                         {'name': 't1', 'test2': [{'name': 't2'}]})

    def test_to_dict_o2m_with_column(self):
        registry = self.init_registry(self.add_in_registry_m2o)
        t1 = registry.Test.insert(name='t1')
        registry.Test2.insert(name='t2', test=t1)
        self.assertEqual(t1.to_dict('name', ('test2', ('name',))),
                         {'name': 't1', 'test2': [{'name': 't2'}]})

    def test_to_dict_m2o_with_all_columns(self):
        registry = self.init_registry(self.add_in_registry_m2o)
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        self.assertEqual(t2.to_dict('name', ('test',)),
                         {'name': 't2', 'test': {'name': 't1',
                                                 'id': t1.id,
                                                 'test2': [{'id': t2.id}]}})
        self.assertEqual(t2.to_dict('name', ('test', None)),
                         {'name': 't2', 'test': {'name': 't1',
                                                 'id': t1.id,
                                                 'test2': [{'id': t2.id}]}})
        self.assertEqual(t2.to_dict('name', ('test', ())),
                         {'name': 't2', 'test': {'name': 't1',
                                                 'id': t1.id,
                                                 'test2': [{'id': t2.id}]}})

    def test_to_dict_o2o_with_all_columns(self):
        registry = self.init_registry(self.add_in_registry_o2o)
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        self.assertEqual(t2.to_dict('name', ('test',)),
                         {'name': 't2', 'test': {'name': 't1',
                                                 'id': t1.id,
                                                 'test2': {'id': t2.id}}})
        self.assertEqual(t2.to_dict('name', ('test', None)),
                         {'name': 't2', 'test': {'name': 't1',
                                                 'id': t1.id,
                                                 'test2': {'id': t2.id}}})
        self.assertEqual(t2.to_dict('name', ('test', ())),
                         {'name': 't2', 'test': {'name': 't1',
                                                 'id': t1.id,
                                                 'test2': {'id': t2.id}}})

    def test_to_dict_m2m_with_all_columns(self):
        registry = self.init_registry(self.add_in_registry_m2m)
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2')
        t2.test.append(t1)
        self.assertEqual(t2.to_dict('name', ('test',)),
                         {'name': 't2', 'test': [{'name': 't1',
                                                  'id': t1.id,
                                                  'test2': [{'id': t2.id}]}]})
        self.assertEqual(t2.to_dict('name', ('test', None)),
                         {'name': 't2', 'test': [{'name': 't1',
                                                  'id': t1.id,
                                                  'test2': [{'id': t2.id}]}]})
        self.assertEqual(t2.to_dict('name', ('test', ())),
                         {'name': 't2', 'test': [{'name': 't1',
                                                  'id': t1.id,
                                                  'test2': [{'id': t2.id}]}]})
        self.assertEqual(t1.to_dict('name', ('test2',)),
                         {'name': 't1', 'test2': [{'name': 't2',
                                                   'id': t2.id,
                                                   'test': [{'id': t1.id}]}]})
        self.assertEqual(t1.to_dict('name', ('test2', None)),
                         {'name': 't1', 'test2': [{'name': 't2',
                                                   'id': t2.id,
                                                   'test': [{'id': t1.id}]}]})
        self.assertEqual(t1.to_dict('name', ('test2', ())),
                         {'name': 't1', 'test2': [{'name': 't2',
                                                   'id': t2.id,
                                                   'test': [{'id': t1.id}]}]})

    def test_to_dict_o2m_with_all_columns(self):
        registry = self.init_registry(self.add_in_registry_m2o)
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        self.assertEqual(t1.to_dict('name', ('test2',)),
                         {'name': 't1', 'test2': [{'name': 't2',
                                                   'id': t2.id,
                                                   'test': {'id': t1.id}}]})
        self.assertEqual(t1.to_dict('name', ('test2', None)),
                         {'name': 't1', 'test2': [{'name': 't2',
                                                   'id': t2.id,
                                                   'test': {'id': t1.id}}]})
        self.assertEqual(t1.to_dict('name', ('test2', ())),
                         {'name': 't1', 'test2': [{'name': 't2',
                                                   'id': t2.id,
                                                   'test': {'id': t1.id}}]})

    def test_bad_definition_of_relation(self):
        registry = self.init_registry(self.add_in_registry_m2o)
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        with self.assertRaises(SqlBaseException):
            t2.to_dict('name', ('test', 'name'))

    def test_bad_definition_of_relation2(self):
        registry = self.init_registry(self.add_in_registry_m2o)
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        with self.assertRaises(SqlBaseException):
            t2.to_dict('name', ('test', ('name',), ()))

    def test_bad_definition_of_relation3(self):
        registry = self.init_registry(self.add_in_registry_m2o)
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        with self.assertRaises(SqlBaseException):
            t2.to_dict('name', ())

    def test_refresh_update(self):
        registry = self.init_registry(self.add_in_registry_m2o)
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        t3 = registry.Test.insert(name='t3')
        t2.update(dict(test_id=t3.id))
        self.assertIs(t2.test, t3)

    def test_find_relationship_by_relationship(self):
        registry = self.init_registry(self.add_in_registry_m2o)
        fields = registry.Test2.find_relationship('test')
        self.assertIn('test', fields)
        self.assertIn('test_id', fields)

    def test_find_relationship_by_column(self):
        registry = self.init_registry(self.add_in_registry_m2o)
        fields = registry.Test2.find_relationship('test_id')
        self.assertIn('test', fields)
        self.assertIn('test_id', fields)

    def declare_model_with_column_selection(self):
        from anyblok import Declarations
        Model = Declarations.Model

        @Declarations.register(Model)
        class Test:
            id = Integer(primary_key=True)
            select = Selection(
                selections=[('key', 'value'), ('key2', 'value2')],
                default='key')

    def test_expire_with_column_selection(self):
        registry = self.init_registry(self.declare_model_with_column_selection)
        t = registry.Test.insert()
        t.select = 'key2'
        t.expire('select')
        self.assertEqual(t.select, 'key')

    def test_find_remote_attribute_to_expire_by_relationship_m2o(self):
        registry = self.init_registry(self.add_in_registry_m2o)
        self.assertEqual(
            registry.Test2.find_remote_attribute_to_expire('test'),
            {'test': ['test2']})

    def test_find_remote_attribute_to_expire_by_column_m2o(self):
        registry = self.init_registry(self.add_in_registry_m2o)
        self.assertEqual(
            registry.Test2.find_remote_attribute_to_expire('test_id'),
            {'test': ['test2']})

    def test_find_remote_attribute_to_expire_by_relationship_o2m(self):
        registry = self.init_registry(self.add_in_registry_o2m)
        self.assertEqual(
            registry.Test2.find_remote_attribute_to_expire('test'),
            {'test': ['test2']})

    def test_find_remote_attribute_to_expire_by_column_o2m(self):
        registry = self.init_registry(self.add_in_registry_o2m)
        self.assertEqual(
            registry.Test2.find_remote_attribute_to_expire('test_id'),
            {'test': ['test2']})

    def test_find_remote_attribute_to_expire_by_relationship_o2o(self):
        registry = self.init_registry(self.add_in_registry_o2o)
        self.assertEqual(
            registry.Test2.find_remote_attribute_to_expire('test'),
            {'test': ['test2']})

    def test_find_remote_attribute_to_expire_by_column_o2o(self):
        registry = self.init_registry(self.add_in_registry_o2o)
        self.assertEqual(
            registry.Test2.find_remote_attribute_to_expire('test_id'),
            {'test': ['test2']})

    def test_find_remote_attribute_to_expire_by_relationship_m2m(self):
        registry = self.init_registry(self.add_in_registry_m2m)
        self.assertEqual(
            registry.Test2.find_remote_attribute_to_expire('test'),
            {'test': ['test2']})

    def test_find_remote_attribute_to_expire_by_relationship_m2m_2(self):
        registry = self.init_registry(self.add_in_registry_m2m)
        self.assertEqual(
            registry.Test.find_remote_attribute_to_expire('test2'),
            {'test2': ['test']})

    def test_expire_relationship_mapped_m2o(self):
        registry = self.init_registry(self.add_in_registry_m2o)
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        t1.test2  # load test2 mmaper, need for the test
        self.assertEqual(t1.__dict__.get('test2'), [t2])
        t2.expire_relationship_mapped({'test': ['test2']})
        self.assertIsNone(t1.__dict__.get('test2'))

    def test_expire_relationship_mapped_o2m(self):
        registry = self.init_registry(self.add_in_registry_o2m)
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        t1.test2  # load test2 mmaper, need for the test
        self.assertEqual(t1.__dict__.get('test2'), [t2])
        t2.expire_relationship_mapped({'test': ['test2']})
        self.assertIsNone(t1.__dict__.get('test2'))

    def test_expire_relationship_mapped_o2o(self):
        registry = self.init_registry(self.add_in_registry_o2o)
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2', test=t1)
        t1.test2  # load test2 mmaper, need for the test
        self.assertIs(t1.__dict__.get('test2'), t2)
        t2.expire_relationship_mapped({'test': ['test2']})
        self.assertIsNone(t1.__dict__.get('test2'))

    def test_expire_relationship_mapped_m2m(self):
        registry = self.init_registry(self.add_in_registry_m2m)
        t1 = registry.Test.insert(name='t1')
        t2 = registry.Test2.insert(name='t2')
        t2.test.append(t1)
        t1.test2  # load test2 mmaper, need for the test
        self.assertEqual(t1.__dict__.get('test2'), [t2])
        t2.expire_relationship_mapped({'test': ['test2']})
        self.assertIsNone(t1.__dict__.get('test2'))
