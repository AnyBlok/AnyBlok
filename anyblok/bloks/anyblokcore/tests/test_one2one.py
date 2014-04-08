# -*- coding: utf-8 -*-
from anyblok.tests.anyblokfieldtestcase import AnyBlokFieldTestCase
from anyblok.field import FieldException


def _complete_one2one(**kwargs):

    from AnyBlok import target_registry, Model
    from AnyBlok.Column import Integer, String
    from AnyBlok.RelationShip import One2One

    @target_registry(Model)
    class Address:

        id = Integer(label='Id', primary_key=True)
        street = String(label='Street')
        zip = String(label='Zip')
        city = String(label='City')

    @target_registry(Model)
    class Person:

        name = String(label='Name', primary_key=True)
        address = One2One(label="Address", model=Model.Address,
                          remote_column="id", column_name="id_of_address",
                          backref="person", nullable=False)


def _minimum_one2one(**kwargs):

    from AnyBlok import target_registry, Model
    from AnyBlok.Column import Integer, String
    from AnyBlok.RelationShip import One2One

    @target_registry(Model)
    class Address:

        id = Integer(label='Id', primary_key=True)

    @target_registry(Model)
    class Person:

        name = String(label='Name', primary_key=True)
        address = One2One(label="Address", model=Model.Address,
                          backref="person")


def _minimum_one2one_without_backref(**kwargs):

    from AnyBlok import target_registry, Model
    from AnyBlok.Column import Integer, String
    from AnyBlok.RelationShip import One2One

    @target_registry(Model)
    class Address:

        id = Integer(label='Id', primary_key=True)

    @target_registry(Model)
    class Person:

        name = String(label='Name', primary_key=True)
        address = One2One(label="Address", model=Model.Address)


class TestMany2One(AnyBlokFieldTestCase):

    def test_complete_one2one(self):
        registry = self.init_registry(_complete_one2one)

        address_exist = hasattr(registry.Person, 'address')
        self.assertEqual(address_exist, True)

        id_of_address_exist = hasattr(registry.Person, 'id_of_address')
        self.assertEqual(id_of_address_exist, True)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(
            name=u"Jean-sébastien SUZANNE", address=address)

        self.assertEqual(address.person, person)

    def test_minimum_one2one(self):
        registry = self.init_registry(_minimum_one2one)

        address_exist = hasattr(registry.Person, 'address')
        self.assertEqual(address_exist, True)

        address_id_exist = hasattr(registry.Person, 'address_id')
        self.assertEqual(address_id_exist, True)

        address = registry.Address.insert()

        person = registry.Person.insert(
            name=u"Jean-sébastien SUZANNE", address=address)

        self.assertEqual(address.person, person)

    def test_minimum_one2one_without_backref(self):
        try:
            self.init_registry(_minimum_one2one_without_backref)
            self.fail("No watch dog when no backref")
        except FieldException:
            pass
