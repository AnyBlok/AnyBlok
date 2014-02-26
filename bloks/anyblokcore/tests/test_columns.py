import unittest
from anyblok.blok import BlokManager

#TODO Make launcher of test on a base


class TestColumns(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestColumns, cls).setUpClass()
        BlokManager.load('AnyBlok')

    @classmethod
    def tearDownClass(cls):
        super(TestColumns, cls).tearDownClass()
        BlokManager.unload()

    def test_integer(self):
        from AnyBlok.Column import Integer
        Integer(label="One Integer")

    def test_big_integer(self):
        from AnyBlok.Column import BigInteger
        BigInteger(label="One Integer")

    def test_small_integer(self):
        from AnyBlok.Column import SmallInteger
        SmallInteger(label="One Integer")

    def test_Float(self):
        from AnyBlok.Column import Float
        Float(label="One Integer")

    def test_decimal(self):
        from AnyBlok.Column import Decimal
        Decimal(label="One Integer")

    def test_boolean(self):
        from AnyBlok.Column import Boolean
        Boolean(label="One Integer")

    def test_string(self):
        from AnyBlok.Column import String
        String(label="One Integer")

    def test_text(self):
        from AnyBlok.Column import Text
        Text(label="One Integer")

    def test_ustring(self):
        from AnyBlok.Column import uString
        uString(label="One Integer")

    def test_utext(self):
        from AnyBlok.Column import uText
        uText(label="One Integer")

    def test_enum(self):
        from AnyBlok.Column import Enum
        Enum(label="One Integer")

    def test_date(self):
        from AnyBlok.Column import Date
        Date(label="One Integer")

    def test_datetime(self):
        from AnyBlok.Column import DateTime
        DateTime(label="One Integer")

    def test_interval(self):
        from AnyBlok.Column import Interval
        Interval(label="One Integer")

    def test_time(self):
        from AnyBlok.Column import Time
        Time(label="One Integer")

    def test_binary(self):
        from AnyBlok.Column import Binary
        Binary(label="One Integer")

    def test_large_binary(self):
        from AnyBlok.Column import LargeBinary
        LargeBinary(label="One Integer")
