# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import DBTestCase
from anyblok import Declarations
from anyblok.column import Integer, String
from anyblok.relationship import One2Many


register = Declarations.register
Model = Declarations.Model
Mixin = Declarations.Mixin


def _complete_one2many(**kwargs):
    primaryjoin = "address.id == person.address_id"

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address_id = Integer(foreign_key=Model.Address.use('id'))

    @register(Model)  # noqa
    class Address:

        persons = One2Many(model=Model.Person,
                           remote_columns="address_id",
                           primaryjoin=primaryjoin,
                           many2one="address")


def _minimum_one2many(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address_id = Integer(foreign_key=Model.Address.use('id'))

    @register(Model)  # noqa
    class Address:

        persons = One2Many(model=Model.Person)


def _minimum_one2many_remote_field_in_mixin(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Mixin)
    class MPerson:
        address_id = Integer(foreign_key=Model.Address.use('id'))

    @register(Model)
    class Person(Mixin.MPerson):

        name = String(primary_key=True)

    @register(Model)  # noqa
    class Address:

        persons = One2Many(model=Model.Person)


def _one2many_with_str_model(**kwargs):

    @register(Model)
    class Address:

        id = Integer(primary_key=True)
        street = String()
        zip = String()
        city = String()

    @register(Model)
    class Person:

        name = String(primary_key=True)
        address_id = Integer(foreign_key=Model.Address.use('id'))

    @register(Model)  # noqa
    class Address:

        persons = One2Many(model='Model.Person')


def _multi_fk_one2many():

    @register(Model)
    class Test:

        id = Integer(primary_key=True, unique=True)
        id2 = String(primary_key=True, unique=True)

    @register(Model)
    class Test2:

        id = Integer(primary_key=True)
        test_id = Integer(foreign_key=Model.Test.use('id'))
        test_id2 = String(foreign_key=Model.Test.use('id2'))

    @register(Model)  # noqa
    class Test:

        test2 = One2Many(model=Model.Test2, many2one="test")


class TestOne2Many(DBTestCase):

    def test_complete_one2many(self):
        registry = self.init_registry(_complete_one2many)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")
        address.persons.append(person)

        self.assertEqual(person.address, address)

    def test_complete_one2many_expire_field(self):
        registry = self.init_registry(_complete_one2many)
        self.assertIn(
            ('address',),
            registry.expire_attributes['Model.Person']['address_id'])
        self.assertIn(
            ('address', 'persons'),
            registry.expire_attributes['Model.Person']['address_id'])

    def test_minimum_one2many(self):
        registry = self.init_registry(_minimum_one2many)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")
        address.persons.append(person)

    def test_minimum_one2many_remote_field_in_mixin(self):
        registry = self.init_registry(_minimum_one2many)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")
        address.persons.append(person)

    def test_one2many_with_str_model(self):
        registry = self.init_registry(_one2many_with_str_model)

        address = registry.Address.insert(
            street='14-16 rue soleillet', zip='75020', city='Paris')

        person = registry.Person.insert(name="Jean-sébastien SUZANNE")
        address.persons.append(person)

    def test_same_model_backref(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                parent_id = Integer(foreign_key='Model.Test=>id')
                children = One2Many(model='Model.Test', many2one='parent')

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert()
        t2 = registry.Test.insert(parent=t1)
        self.assertIs(t1.children[0], t2)
        self.assertIs(t2.parent, t1)

    def test_complet_with_multi_foreign_key(self):

        def add_in_registry():
            primaryjoin = "test.id == test2.test_id and "
            primaryjoin += "test.id2 == test2.test_id2"

            @register(Model)
            class Test:

                id = Integer(primary_key=True, unique=True)
                id2 = String(primary_key=True, unique=True)

            @register(Model)
            class Test2:

                id = Integer(primary_key=True)
                test_id = Integer(foreign_key=Model.Test.use('id'))
                test_id2 = String(foreign_key=Model.Test.use('id2'))

            @register(Model)  # noqa
            class Test:

                test2 = One2Many(model=Model.Test2,
                                 remote_columns=['test_id', 'test_id2'],
                                 primaryjoin=primaryjoin,
                                 many2one="test")

        registry = self.init_registry(add_in_registry)
        t1 = registry.Test.insert(id2="test")
        t2 = registry.Test2.insert(test=t1)
        self.assertEqual(len(t1.test2), 1)
        self.assertIs(t1.test2[0], t2)

    def test_with_multi_foreign_key(self):
        registry = self.init_registry(_multi_fk_one2many)
        t1 = registry.Test.insert(id2="test")
        t2 = registry.Test2.insert(test=t1)
        self.assertEqual(len(t1.test2), 1)
        self.assertIs(t1.test2[0], t2)

    def test_with_multi_foreign_key_expire_field(self):
        registry = self.init_registry(_multi_fk_one2many)
        self.assertIn(
            ('test',),
            registry.expire_attributes['Model.Test2']['test_id'])
        self.assertIn(
            ('test', 'test2'),
            registry.expire_attributes['Model.Test2']['test_id'])
        self.assertIn(
            ('test',),
            registry.expire_attributes['Model.Test2']['test_id2'])
        self.assertIn(
            ('test', 'test2'),
            registry.expire_attributes['Model.Test2']['test_id2'])
