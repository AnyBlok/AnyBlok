from anyblok.tests.testcase import DBTestCase
from anyblok import Declarations
target_registry = Declarations.target_registry
Model = Declarations.Model


def simple_column(ColumnType=None, **kwargs):

    Integer = Declarations.Column.Integer

    @target_registry(Model)
    class Test:

        id = Integer(primary_key=True)
        col = ColumnType(**kwargs)


def column_with_foreign_key():

    Integer = Declarations.Column.Integer
    String = Declarations.Column.String

    @target_registry(Model)
    class Test:

        name = String(primary_key=True)

    @target_registry(Model)
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
        test = registry.Test.insert(col=u'col')
        self.assertEqual(test.col, u'col')

    def test_ustring_with_size(self):
        uString = Declarations.Column.uString
        registry = self.init_registry(simple_column, ColumnType=uString,
                                      size=100)
        test = registry.Test.insert(col=u'col')
        self.assertEqual(test.col, u'col')

    def test_utext(self):
        uText = Declarations.Column.uText
        registry = self.init_registry(simple_column, ColumnType=uText)
        test = registry.Test.insert(col=u'col')
        self.assertEqual(test.col, u'col')

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
            (u'admin', u'Admin'),
            (u'regular-user', u'Regular user')
        ]

        Selection = Declarations.Column.Selection
        registry = self.init_registry(
            simple_column, ColumnType=Selection, selections=SELECTIONS)
        registry.Test.insert(col=SELECTIONS[0][0])
        test = registry.Test.query().first()
        self.assertEqual(test.col, SELECTIONS[0][0])
        self.assertEqual(str(test.col), SELECTIONS[0][1])
        self.assertEqual(repr(test.col), 'Selection : %s(%r)' % (
            SELECTIONS[0][1], SELECTIONS[0][0]))
