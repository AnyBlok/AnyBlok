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
from anyblok.column import (Column,
                            Boolean,
                            Json,
                            String,
                            BigInteger,
                            SmallInteger,
                            uString,
                            Text,
                            uText,
                            Selection,
                            Date,
                            DateTime,
                            Time,
                            Interval,
                            Decimal,
                            Float,
                            LargeBinary,
                            Integer)


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
        test = String(foreign_key=(Model.Test, 'name'))


class TestColumns(DBTestCase):

    def test_column_with_type_in_kwargs(self):
        self.reload_registry_with(
            simple_column, ColumnType=Integer, type_=Integer)

    def test_column_with_db_column_name_in_kwargs(self):
        self.reload_registry_with(simple_column, ColumnType=Integer,
                                  db_column_name='another_name')
        test = self.registry.Test.insert(col=1)
        self.assertEqual(test.col, 1)
        res = self.registry.execute('select id from test where another_name=1')
        self.assertEqual(res.fetchone()[0], test.id)

    def test_column_with_foreign_key(self):
        self.reload_registry_with(column_with_foreign_key)
        self.registry.Test.insert(name='test')
        self.registry.Test2.insert(test='test')

    def test_integer(self):
        self.reload_registry_with(simple_column, ColumnType=Integer)
        test = self.registry.Test.insert(col=1)
        self.assertEqual(test.col, 1)

    def test_integer_str_foreign_key(self):
        self.reload_registry_with(
            simple_column, ColumnType=Integer,
            foreign_key=('Model.Test', 'id'))
        test = self.registry.Test.insert()
        test2 = self.registry.Test.insert(col=test.id)
        self.assertEqual(test2.col, test.id)

    def test_big_integer(self):
        self.reload_registry_with(simple_column, ColumnType=BigInteger)
        test = self.registry.Test.insert(col=1)
        self.assertEqual(test.col, 1)

    def test_small_integer(self):
        self.reload_registry_with(simple_column, ColumnType=SmallInteger)
        test = self.registry.Test.insert(col=1)
        self.assertEqual(test.col, 1)

    def test_Float(self):
        self.reload_registry_with(simple_column, ColumnType=Float)
        test = self.registry.Test.insert(col=1.0)
        self.assertEqual(test.col, 1.0)

    def test_decimal(self):
        from decimal import Decimal as D

        self.reload_registry_with(simple_column, ColumnType=Decimal)
        test = self.registry.Test.insert(col=D('1.0'))
        self.assertEqual(test.col, D('1.0'))

    def test_boolean(self):
        self.reload_registry_with(simple_column, ColumnType=Boolean)
        test = self.registry.Test.insert(col=True)
        self.assertEqual(test.col, True)

    def test_boolean_with_default(self):
        self.reload_registry_with(simple_column, ColumnType=Boolean,
                                  default=False)
        test = self.registry.Test.insert()
        self.assertEqual(test.col, False)

    def test_string(self):
        self.reload_registry_with(simple_column, ColumnType=String)
        test = self.registry.Test.insert(col='col')
        self.assertEqual(test.col, 'col')

    def test_string_with_size(self):
        self.reload_registry_with(simple_column, ColumnType=String, size=100)
        test = self.registry.Test.insert(col='col')
        self.assertEqual(test.col, 'col')

    def test_text(self):
        self.reload_registry_with(simple_column, ColumnType=Text)
        test = self.registry.Test.insert(col='col')
        self.assertEqual(test.col, 'col')

    def test_ustring(self):
        self.reload_registry_with(simple_column, ColumnType=uString)
        test = self.registry.Test.insert(col='col')
        self.assertEqual(test.col, 'col')

    def test_ustring_with_size(self):
        self.reload_registry_with(simple_column, ColumnType=uString, size=100)
        test = self.registry.Test.insert(col='col')
        self.assertEqual(test.col, 'col')

    def test_utext(self):
        self.reload_registry_with(simple_column, ColumnType=uText)
        test = self.registry.Test.insert(col='col')
        self.assertEqual(test.col, 'col')

    def test_date(self):
        from datetime import date

        now = date.today()
        self.reload_registry_with(simple_column, ColumnType=Date)
        test = self.registry.Test.insert(col=now)
        self.assertEqual(test.col, now)

    def test_datetime(self):
        import datetime

        now = datetime.datetime.now()
        self.reload_registry_with(simple_column, ColumnType=DateTime)
        test = self.registry.Test.insert(col=now)
        self.assertEqual(test.col, now)

    def test_interval(self):
        from datetime import timedelta

        dt = timedelta(days=5)
        self.reload_registry_with(simple_column, ColumnType=Interval)
        test = self.registry.Test.insert(col=dt)
        self.assertEqual(test.col, dt)

    def test_time(self):
        from datetime import time

        now = time()
        self.reload_registry_with(simple_column, ColumnType=Time)
        test = self.registry.Test.insert(col=now)
        self.assertEqual(test.col, now)

    def test_large_binary(self):
        from os import urandom

        blob = urandom(100000)
        self.reload_registry_with(simple_column, ColumnType=LargeBinary)

        test = self.registry.Test.insert(col=blob)
        self.assertEqual(test.col, blob)

    def test_selection(self):
        SELECTIONS = [
            ('admin', 'Admin'),
            ('regular-user', 'Regular user')
        ]

        self.reload_registry_with(
            simple_column, ColumnType=Selection, selections=SELECTIONS)
        test = self.registry.Test.insert(col=SELECTIONS[0][0])
        self.assertEqual(test.col, SELECTIONS[0][0])
        self.assertEqual(test.col.label, SELECTIONS[0][1])
        test = self.registry.Test.query().first()
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
            self.reload_registry_with(
                simple_column, ColumnType=Selection, selections=SELECTIONS)
            self.fail('No watchdog to check if the key is not a str')
        except FieldException:
            pass

    def test_selection_comparator(self):
        SELECTIONS = [
            ('admin', 'Admin'),
            ('regular-user', 'Regular user')
        ]

        self.reload_registry_with(
            simple_column, ColumnType=Selection, selections=SELECTIONS)
        self.registry.Test.insert(col=SELECTIONS[0][0])
        self.registry.Test.query().filter(
            self.registry.Test.col.in_(['admin', 'regular-user'])).first()

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

        self.reload_registry_with(add_selection)
        self.registry.Test.insert(col=SELECTIONS[0][0])
        self.registry.Test.query().filter(
            self.registry.Test.col.in_(['admin', 'regular-user'])).first()

    def test_json(self):
        self.reload_registry_with(simple_column, ColumnType=Json)
        val = {'a': 'Test'}
        test = self.registry.Test.insert(col=val)
        self.assertEqual(test.col, val)

    def test_json_update(self):
        self.reload_registry_with(simple_column, ColumnType=Json)
        test = self.registry.Test.insert(col={'a': 'test'})
        test.col['b'] = 'test'
        self.assertEqual(test.col, {'a': 'test', 'b': 'test'})

    def test_json_simple_filter(self):
        self.reload_registry_with(simple_column, ColumnType=Json)
        Test = self.registry.Test
        Test.insert(col={'a': 'test'})
        Test.insert(col={'a': 'test'})
        Test.insert(col={'b': 'test'})
        self.assertEqual(
            Test.query().filter(Test.col == {'a': 'test'}).count(), 2)

    # WORKS with json postgres column but not with the generic AnyBlok column
    # def test_json_filter(self):
    #     Json = Declarations.Column.Json
    #     self.reload_registry_with(simple_column, ColumnType=Json)
    #     Test = self.registry.Test
    #     t1 = Test.insert(col={'a': 'Test1'})
    #     Test.insert(col={'a': 'Test2'})
    #     self.assertEqual(Test.query().filter(
    #         Test.col['a'] == 'Test1').first(), t1)

    # def test_json_filter_numeric(self):
    #     Json = Declarations.Column.Json
    #     self.reload_registry_with(simple_column, ColumnType=Json)
    #     Test = self.registry.Test
    #     t1 = Test.insert(col={'a': 1})
    #     Test.insert(col={'a': 2})
    #     self.assertEqual(Test.query().filter(
    #         Test.col['a'] == 1).first(), t1)

    # def test_json_filter_astext(self):
    #     Json = Declarations.Column.Json
    #     self.reload_registry_with(simple_column, ColumnType=Json)
    #     Test = self.registry.Test
    #     t1 = Test.insert(col={'a': 'Test1'})
    #     Test.insert(col={'a': 'Test2'})
    #     self.assertEqual(Test.query().filter(
    #         Test.col['a'].astext == 'Test1').first(), t1)

    # def test_json_filter_cast(self):
    #     Json = Declarations.Column.Json
    #     Integer = Declarations.Column.Integer
    #     self.reload_registry_with(simple_column, ColumnType=Json)
    #     Test = self.registry.Test
    #     t1 = Test.insert(col={'a': '1'})
    #     Test.insert(col={'a': '2'})
    #     self.assertEqual(Test.query().filter(
    #         Test.col['a'].cast(Integer) == 1).first(), t1)

    def test_json_null(self):
        self.reload_registry_with(simple_column, ColumnType=Json)
        Test = self.registry.Test
        Test.insert(col=None)
        Test.insert(col=None)
        Test.insert(col={'a': 'test'})
        self.assertEqual(Test.query().filter(Test.col == Json.Null).count(), 2)
        self.assertEqual(Test.query().filter(Test.col != Json.Null).count(), 1)
