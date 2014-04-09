# -*- coding: utf-8 -*-
from anyblok.tests.anyblokfieldtestcase import AnyBlokFieldTestCase
from anyblok.field import FieldException


def _complete_one2many(**kwargs):

    from AnyBlok import target_registry, Model
    from AnyBlok.Column import Integer, String
    from AnyBlok.RelationShip import One2Many

    primaryjoin = "address.id == person.address_id"

    @target_registry(Model)
    class Address:

        id = Integer(label='Id', primary_key=True)
        street = String(label='Street')
        zip = String(label='Zip')
        city = String(label='City')

    @target_registry(Model)
    class Person:

        name = String(label='Name', primary_key=True)
        address_id = Integer(label="Address", foreign_key=(
            Model.Address, 'id'))

    @target_registry(Model)  # noqa
    class Address:

        persons = One2Many(label="Persons", model=Model.Person,
                           remote_column="address_id",
                           primaryjoin=primaryjoin,
                           many2one="address")


def _minimum_one2many(**kwargs):

    from AnyBlok import target_registry, Model
    from AnyBlok.Column import Integer, String
    from AnyBlok.RelationShip import One2Many

    @target_registry(Model)
    class Address:

        id = Integer(label='Id', primary_key=True)
        street = String(label='Street')
        zip = String(label='Zip')
        city = String(label='City')

    @target_registry(Model)
    class Person:

        name = String(label='Name', primary_key=True)
        address_id = Integer(label="Address", foreign_key=(
            Model.Address, 'id'))

    @target_registry(Model)  # noqa
    class Address:

        persons = One2Many(label="Persons", model=Model.Person)


def _autodetect_two_foreign_key(**kwargs):

    from AnyBlok import target_registry, Model
    from AnyBlok.Column import Integer, String
    from AnyBlok.RelationShip import One2Many

    @target_registry(Model)
    class Address:

        id = Integer(label='Id', primary_key=True)
        street = String(label='Street')
        zip = String(label='Zip')
        city = String(label='City')

    @target_registry(Model)
    class Person:

        name = String(label='Name', primary_key=True)
        address_id = Integer(label="Address", foreign_key=(
            Model.Address, 'id'))
        address2_id = Integer(label="Address", foreign_key=(
            Model.Address, 'id'))

    @target_registry(Model)  # noqa
    class Address:

        persons = One2Many(label="Persons", model=Model.Person)


class TestOne2One(AnyBlokFieldTestCase):

    def test_complete_one2one(self):
        registry = self.init_registry(_complete_one2many)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name=u"Jean-sébastien SUZANNE")
        address.persons.append(person)

        self.assertEqual(person.address, address)

    def test_minimum_one2one(self):
        registry = self.init_registry(_minimum_one2many)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name=u"Jean-sébastien SUZANNE")
        address.persons.append(person)

    def test_autodetect_two_foreign_key(self):
        try:
            self.init_registry(_autodetect_two_foreign_key)
            self.fail('No watch dog to more than one foreign key')
        except FieldException:
            pass
