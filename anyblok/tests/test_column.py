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
Model = Declarations.Model
Field = Declarations.Field
Column = Declarations.Column
RelationShip = Declarations.RelationShip
register = Declarations.register
unregister = Declarations.unregister
FieldException = Declarations.Exception.FieldException


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
        register(Column, cls_=OneColumn, name_='RealColumn')
        column = Column.RealColumn()
        column.get_sqlalchemy_mapping(None, None, 'a_column', None)
        self.assertEqual(column.label, 'A column')

    def test_add_interface(self):
        register(Column, cls_=OneColumn, name_='OneColumn')
        self.assertEqual('Column', Column.OneColumn.__declaration_type__)
        dir(Declarations.Column.OneColumn)

    def test_add_interface_with_decorator(self):

        @register(Column)
        class OneDecoratorColumn(Column):
            sqlalchemy_type = SA_Integer

        self.assertEqual('Column',
                         Column.OneDecoratorColumn.__declaration_type__)
        dir(Declarations.Column.OneDecoratorColumn)

    def test_add_same_interface(self):

        register(Field, cls_=OneColumn, name_="SameColumn")

        try:
            @register(Column)
            class SameColumn(Column):
                sqlalchemy_type = SA_Integer

            self.fail('No watch dog to add 2 same Column')
        except FieldException:
            pass

    def test_remove_interface(self):

        register(Column, cls_=OneColumn, name_="Column2Remove")
        try:
            unregister(Column.Column2Remove, OneColumn)
            self.fail('No watch dog to remove Column')
        except FieldException:
            pass


def simple_column(ColumnType=None, **kwargs):

    Integer = Declarations.Column.Integer

    @register(Model)
    class Test:

        id = Integer(primary_key=True)
        col = ColumnType(**kwargs)


def column_with_foreign_key():

    Integer = Declarations.Column.Integer
    String = Declarations.Column.String

    @register(Model)
    class Test:

        name = String(primary_key=True)

    @register(Model)
    class Test2:

        id = Integer(primary_key=True)
        test = String(foreign_key=(Model.Test, 'name'))


class TestColumns(DBTestCase):

    def test_column_with_type_in_kwargs(self):
        Integer = Declarations.Column.Integer
        self.init_registry(simple_column, ColumnType=Integer, type_=Integer)

    def test_column_with_foreign_key(self):
        registry = self.init_registry(column_with_foreign_key)
        registry.Test.insert(name='test')
        registry.Test2.insert(test='test')

    def test_integer(self):
        Integer = Declarations.Column.Integer
        registry = self.init_registry(simple_column, ColumnType=Integer)
        test = registry.Test.insert(col=1)
        self.assertEqual(test.col, 1)

    def test_integer_str_foreign_key(self):
        Integer = Declarations.Column.Integer
        registry = self.init_registry(
            simple_column, ColumnType=Integer, foreign_key=('test', 'id'))
        test = registry.Test.insert()
        test2 = registry.Test.insert(col=test.id)
        self.assertEqual(test2.col, test.id)

    def test_big_integer(self):
        BigInteger = Declarations.Column.BigInteger
        registry = self.init_registry(simple_column, ColumnType=BigInteger)
        test = registry.Test.insert(col=1)
        self.assertEqual(test.col, 1)

    def test_small_integer(self):
        SmallInteger = Declarations.Column.SmallInteger
        registry = self.init_registry(simple_column, ColumnType=SmallInteger)
        test = registry.Test.insert(col=1)
        self.assertEqual(test.col, 1)

    def test_Float(self):
        Float = Declarations.Column.Float
        registry = self.init_registry(simple_column, ColumnType=Float)
        test = registry.Test.insert(col=1.0)
        self.assertEqual(test.col, 1.0)

    def test_decimal(self):
        from decimal import Decimal as D

        Decimal = Declarations.Column.Decimal
        registry = self.init_registry(simple_column, ColumnType=Decimal)
        test = registry.Test.insert(col=D('1.0'))
        self.assertEqual(test.col, D('1.0'))

    def test_boolean(self):
        Boolean = Declarations.Column.Boolean
        registry = self.init_registry(simple_column, ColumnType=Boolean)
        test = registry.Test.insert(col=True)
        self.assertEqual(test.col, True)

    def test_string(self):
        String = Declarations.Column.String
        registry = self.init_registry(simple_column, ColumnType=String)
        test = registry.Test.insert(col='col')
        self.assertEqual(test.col, 'col')

    def test_string_with_size(self):
        String = Declarations.Column.String
        registry = self.init_registry(simple_column, ColumnType=String,
                                      size=100)
        test = registry.Test.insert(col='col')
        self.assertEqual(test.col, 'col')

    def test_text(self):
        Text = Declarations.Column.Text
        registry = self.init_registry(simple_column, ColumnType=Text)
        test = registry.Test.insert(col='col')
        self.assertEqual(test.col, 'col')

    def test_ustring(self):
        uString = Declarations.Column.uString
        registry = self.init_registry(simple_column, ColumnType=uString)
        test = registry.Test.insert(col='col')
        self.assertEqual(test.col, 'col')

    def test_ustring_with_size(self):
        uString = Declarations.Column.uString
        registry = self.init_registry(simple_column, ColumnType=uString,
                                      size=100)
        test = registry.Test.insert(col='col')
        self.assertEqual(test.col, 'col')

    def test_utext(self):
        uText = Declarations.Column.uText
        registry = self.init_registry(simple_column, ColumnType=uText)
        test = registry.Test.insert(col='col')
        self.assertEqual(test.col, 'col')

    def test_date(self):
        from datetime import date

        Date = Declarations.Column.Date
        now = date.today()
        registry = self.init_registry(simple_column, ColumnType=Date)
        test = registry.Test.insert(col=now)
        self.assertEqual(test.col, now)

    def test_datetime(self):
        import datetime

        DateTime = Declarations.Column.DateTime
        now = datetime.datetime.now()
        registry = self.init_registry(simple_column, ColumnType=DateTime)
        test = registry.Test.insert(col=now)
        self.assertEqual(test.col, now)

    def test_interval(self):
        from datetime import timedelta

        Interval = Declarations.Column.Interval
        dt = timedelta(days=5)
        registry = self.init_registry(simple_column, ColumnType=Interval)
        test = registry.Test.insert(col=dt)
        self.assertEqual(test.col, dt)

    def test_time(self):
        from datetime import time

        Time = Declarations.Column.Time
        now = time()
        registry = self.init_registry(simple_column, ColumnType=Time)
        test = registry.Test.insert(col=now)
        self.assertEqual(test.col, now)

    def test_large_binary(self):
        from os import urandom

        blob = urandom(100000)
        LargeBinary = Declarations.Column.LargeBinary
        registry = self.init_registry(simple_column, ColumnType=LargeBinary)

        test = registry.Test.insert(col=blob)
        self.assertEqual(test.col, blob)

    def test_selection(self):
        SELECTIONS = [
            ('admin', 'Admin'),
            ('regular-user', 'Regular user')
        ]

        Selection = Declarations.Column.Selection
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

        Selection = Declarations.Column.Selection
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

        Selection = Declarations.Column.Selection
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
            Integer = Declarations.Column.Integer
            Selection = Declarations.Column.Selection

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
        Json = Declarations.Column.Json
        registry = self.init_registry(simple_column, ColumnType=Json)
        val = {'a': 'Test'}
        test = registry.Test.insert(col=val)
        self.assertEqual(test.col, val)

    def test_json_update(self):
        Json = Declarations.Column.Json
        registry = self.init_registry(simple_column, ColumnType=Json)
        test = registry.Test.insert(col={'a': 'test'})
        test.col['b'] = 'test'
        self.assertEqual(test.col, {'a': 'test', 'b': 'test'})

    def test_json_simple_filter(self):
        Json = Declarations.Column.Json
        registry = self.init_registry(simple_column, ColumnType=Json)
        Test = registry.Test
        Test.insert(col={'a': 'test'})
        Test.insert(col={'a': 'test'})
        Test.insert(col={'b': 'test'})
        self.assertEqual(
            Test.query().filter(Test.col == {'a': 'test'}).count(), 2)

    # WORKS with json postgres column but not with the generic AnyBlok column
    # def test_json_filter(self):
    #     Json = Declarations.Column.Json
    #     registry = self.init_registry(simple_column, ColumnType=Json)
    #     Test = registry.Test
    #     t1 = Test.insert(col={'a': 'Test1'})
    #     Test.insert(col={'a': 'Test2'})
    #     self.assertEqual(Test.query().filter(
    #         Test.col['a'] == 'Test1').first(), t1)

    # def test_json_filter_numeric(self):
    #     Json = Declarations.Column.Json
    #     registry = self.init_registry(simple_column, ColumnType=Json)
    #     Test = registry.Test
    #     t1 = Test.insert(col={'a': 1})
    #     Test.insert(col={'a': 2})
    #     self.assertEqual(Test.query().filter(
    #         Test.col['a'] == 1).first(), t1)

    # def test_json_filter_astext(self):
    #     Json = Declarations.Column.Json
    #     registry = self.init_registry(simple_column, ColumnType=Json)
    #     Test = registry.Test
    #     t1 = Test.insert(col={'a': 'Test1'})
    #     Test.insert(col={'a': 'Test2'})
    #     self.assertEqual(Test.query().filter(
    #         Test.col['a'].astext == 'Test1').first(), t1)

    # def test_json_filter_cast(self):
    #     Json = Declarations.Column.Json
    #     Integer = Declarations.Column.Integer
    #     registry = self.init_registry(simple_column, ColumnType=Json)
    #     Test = registry.Test
    #     t1 = Test.insert(col={'a': '1'})
    #     Test.insert(col={'a': '2'})
    #     self.assertEqual(Test.query().filter(
    #         Test.col['a'].cast(Integer) == 1).first(), t1)

    def test_json_null(self):
        Json = Declarations.Column.Json
        registry = self.init_registry(simple_column, ColumnType=Json)
        Test = registry.Test
        Test.insert(col=None)
        Test.insert(col=None)
        Test.insert(col={'a': 'test'})
        self.assertEqual(Test.query().filter(Test.col == Json.Null).count(), 2)
        self.assertEqual(Test.query().filter(Test.col != Json.Null).count(), 1)
