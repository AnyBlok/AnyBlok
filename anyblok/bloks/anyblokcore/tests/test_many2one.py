# -*- coding: utf-8 -*-
from anyblok.tests.testcase import DBTestCase
from anyblok.field import FieldException


def _complete_many2one(**kwargs):

    from AnyBlok import target_registry, Model
    from AnyBlok.Column import Integer, String
    from AnyBlok.RelationShip import Many2One

    @target_registry(Model)
    class Address:

        id = Integer(label='Id', primary_key=True)
        street = String(label='Street')
        zip = String(label='Zip')
        city = String(label='City')

    @target_registry(Model)
    class Person:

        name = String(label='Name', primary_key=True)
        address = Many2One(label="Address", model=Model.Address,
                           remote_column="id", column_name="id_of_address",
                           one2many="persons", nullable=False)


def _minimum_many2one(**kwargs):

    from AnyBlok import target_registry, Model
    from AnyBlok.Column import Integer, String
    from AnyBlok.RelationShip import Many2One

    @target_registry(Model)
    class Address:

        id = Integer(label='Id', primary_key=True)

    @target_registry(Model)
    class Person:

        name = String(label='Name', primary_key=True)
        address = Many2One(label="Address", model=Model.Address)


def _minimum_many2one_without_model(**kwargs):

    from AnyBlok import target_registry, Model
    from AnyBlok.Column import Integer, String
    from AnyBlok.RelationShip import Many2One

    @target_registry(Model)
    class Address:

        id = Integer(label='Id', primary_key=True)

    @target_registry(Model)
    class Person:

        name = String(label='Name', primary_key=True)
        address = Many2One(label="Address")


def _auto_detect_type(ColumnType=None, **kwargs):
    if ColumnType is None:
        raise Exception("Test invalid")

    from AnyBlok import target_registry, Model
    from AnyBlok.Column import String
    from AnyBlok.RelationShip import Many2One

    @target_registry(Model)
    class Address:

        id = ColumnType(label='Id', primary_key=True, **kwargs)

    @target_registry(Model)
    class Person:

        name = String(label='Name', primary_key=True)
        address = Many2One(label="Address", model=Model.Address)


def _two_remote_primary_keys(**kwargs):

    from AnyBlok import target_registry, Model
    from AnyBlok.Column import Integer, String
    from AnyBlok.RelationShip import Many2One

    @target_registry(Model)
    class Address:

        id = Integer(label='Id', primary_key=True)
        id2 = Integer(label='Id2', primary_key=True)

    @target_registry(Model)
    class Person:

        name = String(label='Name', primary_key=True)
        address = Many2One(label="Address", model=Model.Address)


class TestMany2One(DBTestCase):

    def test_complete_many2one(self):
        registry = self.init_registry(_complete_many2one)

        address_exist = hasattr(registry.Person, 'address')
        self.assertEqual(address_exist, True)

        id_of_address_exist = hasattr(registry.Person, 'id_of_address')
        self.assertEqual(id_of_address_exist, True)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(
            name=u"Jean-sébastien SUZANNE", address=address)

        self.assertEqual(address.persons, [person])

    def test_minimum_many2one(self):
        registry = self.init_registry(_minimum_many2one)

        address_exist = hasattr(registry.Person, 'address')
        self.assertEqual(address_exist, True)

        address_id_exist = hasattr(registry.Person, 'address_id')
        self.assertEqual(address_id_exist, True)

        address = registry.Address.insert()

        person = registry.Person.insert(
            name=u"Jean-sébastien SUZANNE", address=address)

        self.assertEqual(person.address, address)

    def test_minimum_many2one_without_model(self):
        try:
            self.init_registry(_minimum_many2one_without_model)
            self.fail("No watch dog when more no model")
        except FieldException:
            pass

    def test_two_remote_primary_keys(self):
        try:
            self.init_registry(_two_remote_primary_keys)
            self.fail("No watch dog when more than one primary keys")
        except FieldException:
            pass

    def check_autodetect_type(self, ColumnType):
        registry = self.init_registry(_auto_detect_type, ColumnType=ColumnType)
        self.assertEqual(
            str(registry.Address.id.property.columns[0].type),
            str(registry.Person.address_id.property.columns[0].type))

    def test_autodetect_type_integer(self):
        from AnyBlok.Column import Integer

        self.check_autodetect_type(Integer)

    def test_autodetect_type_small_integer(self):
        from AnyBlok.Column import SmallInteger

        self.check_autodetect_type(SmallInteger)

    def test_autodetect_type_big_integer(self):
        from AnyBlok.Column import BigInteger

        self.check_autodetect_type(BigInteger)

    def test_autodetect_type_float(self):
        from AnyBlok.Column import Float

        self.check_autodetect_type(Float)

    def test_autodetect_type_decimal(self):
        from AnyBlok.Column import Decimal

        self.check_autodetect_type(Decimal)

    def test_autodetect_type_string(self):
        from AnyBlok.Column import String

        self.check_autodetect_type(String)

    def test_autodetect_type_ustring(self):
        from AnyBlok.Column import uString

        self.check_autodetect_type(uString)

    def test_autodetect_type_boolean(self):
        from AnyBlok.Column import Boolean

        self.check_autodetect_type(Boolean)

    def test_autodetect_type_datetime(self):
        from AnyBlok.Column import DateTime

        self.check_autodetect_type(DateTime)

    def test_autodetect_type_date(self):
        from AnyBlok.Column import Date

        self.check_autodetect_type(Date)

    def test_autodetect_type_time(self):
        from AnyBlok.Column import Time

        self.check_autodetect_type(Time)
