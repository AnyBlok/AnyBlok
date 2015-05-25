# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase
from anyblok.field import FieldException
from anyblok.relationship import RelationShip


class OneRelationShip(RelationShip):
    pass


class OneModel:
    __tablename__ = 'test'
    __registry_name__ = 'One.Model'


class MockRegistry:

    InstrumentedList = []


class TestRelationShip(TestCase):

    def test_forbid_instance(self):
        try:
            RelationShip(model=OneModel)
            self.fail("RelationShip mustn't be instanciated")
        except FieldException:
            pass

    def test_must_have_a_model(self):
        OneRelationShip(model=OneModel)
        try:
            OneRelationShip()
            self.fail("No watchdog, the model must be required")
        except FieldException:
            pass
