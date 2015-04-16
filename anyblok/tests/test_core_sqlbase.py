# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import DBTestCase


class TestCoreSQLBase(DBTestCase):

    def declare_model(self):
        from anyblok import Declarations
        Model = Declarations.Model
        Integer = Declarations.Column.Integer

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
                registry.Test.query().filter(registry.Test.id2 == x).count(),
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
            registry.Test.query().filter(registry.Test.id2 != id2).count(),
            nb_value - 1)

    def test_update(self):
        registry = self.init_registry(self.declare_model)
        nb_value = 3
        registry.Test.multi_insert(*[{'id2': x} for x in range(nb_value)])
        t = registry.Test.query().first()
        t.update({registry.Test.id2: 100})
        self.assertEqual(
            registry.Test.query().filter(registry.Test.id2 == 100).first(), t)

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
