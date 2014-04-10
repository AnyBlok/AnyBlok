from anyblok.tests.testcase import DBTestCase


def simple_column(ColumnType=None, **kwargs):

    from AnyBlok import target_registry, Model
    from AnyBlok.Column import Integer

    @target_registry(Model)
    class Test:

        id = Integer(label='id', primary_key=True)
        col = ColumnType(label="col", **kwargs)


def column_with_foreign_key():

    from AnyBlok import target_registry, Model
    from AnyBlok.Column import Integer, String

    @target_registry(Model)
    class Test:

        name = String(label='id', primary_key=True)

    @target_registry(Model)
    class Test2:

        id = Integer(label='id', primary_key=True)
        test = String(label='test_id', foreign_key=(Model.Test, 'name'))


class TestColumns(DBTestCase):

    def test_column_with_type_in_kwargs(self):
        from AnyBlok.Column import Integer

        self.init_registry(simple_column, ColumnType=Integer, type_=Integer)

    def test_column_with_foreign_key(self):
        registry = self.init_registry(column_with_foreign_key)
        registry.Test.insert(name='test')
        registry.Test2.insert(test='test')

    def test_integer(self):
        from AnyBlok.Column import Integer

        registry = self.init_registry(simple_column, ColumnType=Integer)
        test = registry.Test.insert(col=1)
        self.assertEqual(test.col, 1)

    def test_big_integer(self):
        from AnyBlok.Column import BigInteger

        registry = self.init_registry(simple_column, ColumnType=BigInteger)
        test = registry.Test.insert(col=1)
        self.assertEqual(test.col, 1)

    def test_small_integer(self):
        from AnyBlok.Column import SmallInteger

        registry = self.init_registry(simple_column, ColumnType=SmallInteger)
        test = registry.Test.insert(col=1)
        self.assertEqual(test.col, 1)

    def test_Float(self):
        from AnyBlok.Column import Float

        registry = self.init_registry(simple_column, ColumnType=Float)
        test = registry.Test.insert(col=1.0)
        self.assertEqual(test.col, 1.0)

    def test_decimal(self):
        from AnyBlok.Column import Decimal
        from decimal import Decimal as D

        registry = self.init_registry(simple_column, ColumnType=Decimal)
        test = registry.Test.insert(col=D('1.0'))
        self.assertEqual(test.col, D('1.0'))

    def test_boolean(self):
        from AnyBlok.Column import Boolean

        registry = self.init_registry(simple_column, ColumnType=Boolean)
        test = registry.Test.insert(col=True)
        self.assertEqual(test.col, True)

    def test_string(self):
        from AnyBlok.Column import String

        registry = self.init_registry(simple_column, ColumnType=String)
        test = registry.Test.insert(col='col')
        self.assertEqual(test.col, 'col')

    def test_string_with_size(self):
        from AnyBlok.Column import String

        registry = self.init_registry(simple_column, ColumnType=String,
                                      size=100)
        test = registry.Test.insert(col='col')
        self.assertEqual(test.col, 'col')

    def test_text(self):
        from AnyBlok.Column import Text

        registry = self.init_registry(simple_column, ColumnType=Text)
        test = registry.Test.insert(col='col')
        self.assertEqual(test.col, 'col')

    def test_ustring(self):
        from AnyBlok.Column import uString

        registry = self.init_registry(simple_column, ColumnType=uString)
        test = registry.Test.insert(col=u'col')
        self.assertEqual(test.col, u'col')

    def test_ustring_with_size(self):
        from AnyBlok.Column import uString

        registry = self.init_registry(simple_column, ColumnType=uString,
                                      size=100)
        test = registry.Test.insert(col=u'col')
        self.assertEqual(test.col, u'col')

    def test_utext(self):
        from AnyBlok.Column import uText

        registry = self.init_registry(simple_column, ColumnType=uText)
        test = registry.Test.insert(col=u'col')
        self.assertEqual(test.col, u'col')

    def test_date(self):
        from AnyBlok.Column import Date
        from datetime import date

        now = date.today()
        registry = self.init_registry(simple_column, ColumnType=Date)
        test = registry.Test.insert(col=now)
        self.assertEqual(test.col, now)

    def test_datetime(self):
        from AnyBlok.Column import DateTime
        import datetime

        now = datetime.datetime.now()
        registry = self.init_registry(simple_column, ColumnType=DateTime)
        test = registry.Test.insert(col=now)
        self.assertEqual(test.col, now)

    def test_interval(self):
        from AnyBlok.Column import Interval
        from datetime import timedelta

        dt = timedelta(days=5)
        registry = self.init_registry(simple_column, ColumnType=Interval)
        test = registry.Test.insert(col=dt)
        self.assertEqual(test.col, dt)

    def test_time(self):
        from AnyBlok.Column import Time
        from datetime import time

        now = time()
        registry = self.init_registry(simple_column, ColumnType=Time)
        test = registry.Test.insert(col=now)
        self.assertEqual(test.col, now)

    def test_large_binary(self):
        from AnyBlok.Column import LargeBinary
        from os import urandom

        blob = urandom(100000)

        registry = self.init_registry(simple_column, ColumnType=LargeBinary)

        test = registry.Test.insert(col=blob)
        self.assertEqual(test.col, blob)
