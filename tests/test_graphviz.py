# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase
from anyblok._graphviz import ModelSchema, SQLSchema


class TestSQLSchema(TestCase):

    def test_one_table(self):
        dot = SQLSchema('My table model')
        dot.add_table('My table')
        dot.render()

    def test_one_label(self):
        dot = SQLSchema('My table model')
        dot.add_table('My table')
        dot.render()

    def test_one_table_with_column(self):
        dot = SQLSchema('My table model')
        table = dot.add_table('My table')
        table.add_column('My column', 'Integer', primary_key=True)
        dot.render()

    def test_one_table_with_foreign_key(self):
        dot = SQLSchema('My table model')
        table = dot.add_table('My table')
        table.add_column('My column', 'Integer', primary_key=True)
        table2 = dot.add_table('A 2nd table')
        table2.add_foreign_key('My fk', table, nullable=False)
        dot.render()

    def test_one_table_with_foreign_key_on_label(self):
        dot = SQLSchema('My table model')
        table = dot.add_label('My table')
        table.add_column('My column', 'Integer', primary_key=True)
        table2 = dot.add_table('A 2nd table')
        table2.add_foreign_key('My fk', table, nullable=False)
        dot.render()

    def test_get_table(self):
        dot = SQLSchema('My UML model')
        table = dot.add_table('My table')
        self.assertEqual(dot.get_table('My table'), table)

    def test_get_table_with_label(self):
        dot = SQLSchema('My UML model')
        table = dot.add_label('My table')
        self.assertEqual(dot.get_table('My table'), table)


class TestModelSchema(TestCase):

    def test_one_model_with_label(self):
        dot = ModelSchema('My UML model')
        dot.add_label('My label')
        dot.render()

    def test_one_model_with_class(self):
        dot = ModelSchema('My UML model')
        dot.add_class('My class')
        dot.render()

    def test_one_model_with_class_which_extend_label(self):
        dot = ModelSchema('My UML model')
        label = dot.add_label('My label')
        cls = dot.add_class('My class')
        cls.add_method('One method')
        cls.extend(label)
        dot.render()

    def test_one_model_with_class_which_associate_label(self):
        dot = ModelSchema('My UML model')
        label = dot.add_label('My label')
        cls = dot.add_class('My class')
        cls.associate(label)
        cls.associate(cls, label_from='test')
        dot.render()

    def test_one_model_with_class_which_agregate_label(self):
        dot = ModelSchema('My UML model')
        label = dot.add_label('My label')
        cls = dot.add_class('My class')
        cls.agregate(label, label_to='test', multiplicity_to='test')
        dot.render()

    def test_one_model_with_class_which_strong_agregate_label(self):
        dot = ModelSchema('My UML model')
        label = dot.add_label('My label')
        cls = dot.add_class('My class')
        cls.strong_agregate(label, multiplicity_from='test')
        dot.render()

    def test_get_class(self):
        dot = ModelSchema('My UML model')
        cls = dot.add_class('My class')
        self.assertEqual(dot.get_class('My class'), cls)

    def test_get_class_with_label(self):
        dot = ModelSchema('My UML model')
        cls = dot.add_label('My class')
        self.assertEqual(dot.get_class('My class'), cls)
