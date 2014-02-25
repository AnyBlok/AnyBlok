import unittest
from anyblok.blok import BlokManager


#TODO Make launcher of test on a base

class TestRelationShip(unittest.TestCase):

    def test_one2one(self):
        raise Exception("Unittest by AnyBlok must be implemented to test "
                        "Relation Ship fields")
        from AnyBlok.Column import Integer
        Integer(label="One Integer")

    def test_many2one(self):
        raise Exception("Unittest by AnyBlok must be implemented to test "
                        "Relation Ship fields")
        from AnyBlok.Column import BigInteger
        BigInteger(label="One Integer")

    def test_one2many(self):
        raise Exception("Unittest by AnyBlok must be implemented to test "
                        "Relation Ship fields")
        from AnyBlok.Column import SmallInteger
        SmallInteger(label="One Integer")

    def test_many2many(self):
        raise Exception("Unittest by AnyBlok must be implemented to test "
                        "Relation Ship fields")
        from AnyBlok.Column import Float
        Float(label="One Integer")
