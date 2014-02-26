import unittest
from anyblok.blok import BlokManager

#TODO Make launcher of test on a base


class TestRelationShip(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestRelationShip, cls).setUpClass()
        BlokManager.load('AnyBlok')

        from AnyBlok.Column import Integer

        class TestModel:
            __tablename__ = "test_model"
            id = Integer(label="ID", primary_key=True)

        cls.TestModel = TestModel

    @classmethod
    def tearDownClass(cls):
        super(TestRelationShip, cls).tearDownClass()
        BlokManager.unload()

    def test_one2one(self):
        from AnyBlok.RelationShip import One2One
        One2One(label="One One2One", model=self.TestModel, backref="test")

    def test_many2one(self):
        from AnyBlok.RelationShip import Many2One
        Many2One(label="One Many2One", model=self.TestModel)

    def test_one2many(self):
        from AnyBlok.RelationShip import One2Many
        One2Many(label="One One2Many", model=self.TestModel)

    def test_many2many(self):
        from AnyBlok.RelationShip import Many2Many
        Many2Many(label="One Many2Many", model=self.TestModel)
