# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase, DBTestCase
from sqlalchemy import Integer as SA_Integer
from anyblok import Declarations
from anyblok.field import FieldException
from anyblok.column import (Column, Boolean, Json, String, BigInteger,
                            SmallInteger, uString, Text, uText, Selection,
                            Date, DateTime, Time, Interval, Decimal, Float,
                            LargeBinary, Integer, Sequence)


Model = Declarations.Model
register = Declarations.register


class OneColumn(Column):
    sqlalchemy_type = SA_Integer


class TestColumn(TestCase):

    def test_forbid_instance(self):
        try:
            Column()
            self.fail("Column mustn't be instanciated")
        except FieldException:
            pass

    def test_without_label(self):
        column = OneColumn()
        column.get_sqlalchemy_mapping(None, None, 'a_column', None)
        self.assertEqual(column.label, 'A column')


def simple_column(ColumnType=None, **kwargs):

    @register(Model)
    class Test:

        id = Integer(primary_key=True)
        col = ColumnType(**kwargs)


def column_with_foreign_key():

    @register(Model)
    class Test:

        name = String(primary_key=True)

    @register(Model)
    class Test2:

        id = Integer(primary_key=True)
        test = String(foreign_key=Model.Test.use('name'))


class TestColumns(DBTestCase):

    def test_column_with_type_in_kwargs(self):
        self.init_registry(simple_column, ColumnType=Integer, type_=Integer)

    def test_column_with_db_column_name_in_kwargs(self):
        registry = self.init_registry(simple_column, ColumnType=Integer,
                                      db_column_name='another_name')
        test = registry.Test.insert(col=1)
        self.assertEqual(test.col, 1)
        res = registry.execute('select id from test where another_name=1')
        self.assertEqual(res.fetchone()[0], test.id)

    def test_column_with_foreign_key(self):
        registry = self.init_registry(column_with_foreign_key)
        registry.Test.insert(name='test')
        registry.Test2.insert(test='test')

    def test_integer(self):
        registry = self.init_registry(simple_column, ColumnType=Integer)
        test = registry.Test.insert(col=1)
        self.assertEqual(test.col, 1)

    def test_integer_str_foreign_key(self):
        registry = self.init_registry(
            simple_column, ColumnType=Integer, foreign_key='Model.Test=>id')
        test = registry.Test.insert()
        test2 = registry.Test.insert(col=test.id)
        self.assertEqual(test2.col, test.id)

    def test_big_integer(self):
        registry = self.init_registry(simple_column, ColumnType=BigInteger)
        test = registry.Test.insert(col=1)
        self.assertEqual(test.col, 1)

    def test_small_integer(self):
        registry = self.init_registry(simple_column, ColumnType=SmallInteger)
        test = registry.Test.insert(col=1)
        self.assertEqual(test.col, 1)

    def test_Float(self):
        registry = self.init_registry(simple_column, ColumnType=Float)
        test = registry.Test.insert(col=1.0)
        self.assertEqual(test.col, 1.0)

    def test_decimal(self):
        from decimal import Decimal as D

        registry = self.init_registry(simple_column, ColumnType=Decimal)
        test = registry.Test.insert(col=D('1.0'))
        self.assertEqual(test.col, D('1.0'))

    def test_boolean(self):
        registry = self.init_registry(simple_column, ColumnType=Boolean)
        test = registry.Test.insert(col=True)
        self.assertEqual(test.col, True)

    def test_boolean_with_default(self):
        registry = self.init_registry(simple_column, ColumnType=Boolean,
                                      default=False)
        test = registry.Test.insert()
        self.assertEqual(test.col, False)

    def test_string(self):
        registry = self.init_registry(simple_column, ColumnType=String)
        test = registry.Test.insert(col='col')
        self.assertEqual(test.col, 'col')

    def test_string_with_size(self):
        registry = self.init_registry(simple_column, ColumnType=String,
                                      size=100)
        test = registry.Test.insert(col='col')
        self.assertEqual(test.col, 'col')

    def test_text(self):
        registry = self.init_registry(simple_column, ColumnType=Text)
        test = registry.Test.insert(col='col')
        self.assertEqual(test.col, 'col')

    def test_ustring(self):
        registry = self.init_registry(simple_column, ColumnType=uString)
        test = registry.Test.insert(col='col')
        self.assertEqual(test.col, 'col')

    def test_ustring_with_size(self):
        registry = self.init_registry(simple_column, ColumnType=uString,
                                      size=100)
        test = registry.Test.insert(col='col')
        self.assertEqual(test.col, 'col')

    def test_utext(self):
        registry = self.init_registry(simple_column, ColumnType=uText)
        test = registry.Test.insert(col='col')
        self.assertEqual(test.col, 'col')

    def test_date(self):
        from datetime import date

        now = date.today()
        registry = self.init_registry(simple_column, ColumnType=Date)
        test = registry.Test.insert(col=now)
        self.assertEqual(test.col, now)

    def test_datetime(self):
        import datetime

        now = datetime.datetime.now()
        registry = self.init_registry(simple_column, ColumnType=DateTime)
        test = registry.Test.insert(col=now)
        self.assertEqual(test.col, now)

    def test_interval(self):
        from datetime import timedelta

        dt = timedelta(days=5)
        registry = self.init_registry(simple_column, ColumnType=Interval)
        test = registry.Test.insert(col=dt)
        self.assertEqual(test.col, dt)

    def test_time(self):
        from datetime import time

        now = time()
        registry = self.init_registry(simple_column, ColumnType=Time)
        test = registry.Test.insert(col=now)
        self.assertEqual(test.col, now)

    def test_large_binary(self):
        from os import urandom

        blob = urandom(100000)
        registry = self.init_registry(simple_column, ColumnType=LargeBinary)

        test = registry.Test.insert(col=blob)
        self.assertEqual(test.col, blob)

    def test_selection(self):
        SELECTIONS = [
            ('admin', 'Admin'),
            ('regular-user', 'Regular user')
        ]

        registry = self.init_registry(
            simple_column, ColumnType=Selection, selections=SELECTIONS)
        test = registry.Test.insert(col=SELECTIONS[0][0])
        self.assertEqual(test.col, SELECTIONS[0][0])
        self.assertEqual(test.col.label, SELECTIONS[0][1])
        test = registry.Test.query().first()
        self.assertEqual(test.col, SELECTIONS[0][0])
        self.assertEqual(test.col.label, SELECTIONS[0][1])
        try:
            test.col = 'bad value'
            self.fail('No watchdog to check if the value is on the selection')
        except FieldException:
            pass

    def test_selection_key_other_than_str(self):
        SELECTIONS = [
            (0, 'Admin'),
            (1, 'Regular user')
        ]

        try:
            self.init_registry(
                simple_column, ColumnType=Selection, selections=SELECTIONS)
            self.fail('No watchdog to check if the key is not a str')
        except FieldException:
            pass

    def test_selection_comparator(self):
        SELECTIONS = [
            ('admin', 'Admin'),
            ('regular-user', 'Regular user')
        ]

        registry = self.init_registry(
            simple_column, ColumnType=Selection, selections=SELECTIONS)
        registry.Test.insert(col=SELECTIONS[0][0])
        registry.Test.query().filter(
            registry.Test.col.in_(['admin', 'regular-user'])).first()

    def test_selection_use_method(self):
        SELECTIONS = [
            ('admin', 'Admin'),
            ('regular-user', 'Regular user')
        ]

        def add_selection():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                col = Selection(selections='get_selection')

                @classmethod
                def get_selection(cls):
                    return SELECTIONS

        registry = self.init_registry(add_selection)
        registry.Test.insert(col=SELECTIONS[0][0])
        registry.Test.query().filter(
            registry.Test.col.in_(['admin', 'regular-user'])).first()

    def test_json(self):
        registry = self.init_registry(simple_column, ColumnType=Json)
        val = {'a': 'Test'}
        test = registry.Test.insert(col=val)
        self.assertEqual(test.col, val)

    def test_json_update(self):
        registry = self.init_registry(simple_column, ColumnType=Json)
        test = registry.Test.insert(col={'a': 'test'})
        test.col['b'] = 'test'
        self.assertEqual(test.col, {'a': 'test', 'b': 'test'})

    def test_json_simple_filter(self):
        registry = self.init_registry(simple_column, ColumnType=Json)
        Test = registry.Test
        Test.insert(col={'a': 'test'})
        Test.insert(col={'a': 'test'})
        Test.insert(col={'b': 'test'})
        self.assertEqual(
            Test.query().filter(Test.col == {'a': 'test'}).count(), 2)

    def test_json_null(self):
        registry = self.init_registry(simple_column, ColumnType=Json)
        Test = registry.Test
        Test.insert(col=None)
        Test.insert(col=None)
        Test.insert(col={'a': 'test'})
        self.assertEqual(Test.query().filter(Test.col == Json.Null).count(), 2)
        self.assertEqual(Test.query().filter(Test.col != Json.Null).count(), 1)

    def test_add_default_classmethod(self):
        val = 'test'

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                val = String(default="get_val")

                @classmethod
                def get_val(cls):
                    return val

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert()
        self.assertEqual(t.val, val)

    def test_add_default_without_classmethod(self):
        value = 'test'

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                val = String(default="get_val")

                def get_val(cls):
                    return value

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert()
        self.assertEqual(t.val, "get_val")

    def test_add_default_by_var(self):
        value = 'test'

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                val = String(default=value)

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert()
        self.assertEqual(t.val, value)

    def test_add_default(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                val = String(default='value')

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert()
        self.assertEqual(t.val, 'value')

    def test_add_field_as_default(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                val = String(default='val')

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert()
        self.assertEqual(t.val, 'val')

    def test_sequence(self):
        registry = self.init_registry(simple_column, ColumnType=Sequence)
        self.assertEqual(registry.Test.insert().col, "1")
        self.assertEqual(registry.Test.insert().col, "2")
        self.assertEqual(registry.Test.insert().col, "3")
        self.assertEqual(registry.Test.insert().col, "4")
        Seq = registry.System.Sequence
        self.assertEqual(
            Seq.query().filter(Seq.code == 'Model.Test=>col').count(), 1)

    def test_sequence_with_code_and_formater(self):
        registry = self.init_registry(simple_column, ColumnType=Sequence,
                                      code="SO", formater="{code}-{seq:06d}")
        self.assertEqual(registry.Test.insert().col, "SO-000001")
        self.assertEqual(registry.Test.insert().col, "SO-000002")
        self.assertEqual(registry.Test.insert().col, "SO-000003")
        self.assertEqual(registry.Test.insert().col, "SO-000004")
        Seq = registry.System.Sequence
        self.assertEqual(Seq.query().filter(Seq.code == 'SO').count(), 1)

    def test_sequence_with_foreign_key(self):
        with self.assertRaises(FieldException):
            self.init_registry(simple_column, ColumnType=Sequence,
                               foreign_key=Model.System.Model.use('name'))

    def test_sequence_with_default(self):
        with self.assertRaises(FieldException):
            self.init_registry(simple_column, ColumnType=Sequence,
                               default='default value')
