# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase
from anyblok import Declarations
Field = Declarations.Field
Column = Declarations.Column
RelationShip = Declarations.RelationShip
target_registry = Declarations.target_registry
remove_registry = Declarations.remove_registry
FieldException = Declarations.Exception.FieldException


class OneField(Field):
    pass


class TestField(TestCase):

    def test_forbid_instance(self):
        try:
            Field()
            self.fail("Field mustn't be instanciated")
        except FieldException:
            pass

    def test_without_label(self):
        target_registry(Field, cls_=OneField, name_='RealField')
        field = Field.RealField()
        field.get_sqlalchemy_mapping(None, None, 'a_field', None)
        self.assertEqual(field.label, 'A field')

    def test_add_interface(self):
        target_registry(Field, cls_=OneField, name_='OneField')
        self.assertEqual('Field', Field.OneField.__declaration_type__)
        dir(Declarations.Field.OneField)

    def test_add_interface_with_decorator(self):

        @target_registry(Field)
        class OneDecoratorField(OneField):
            pass

        self.assertEqual('Field', Field.OneDecoratorField.__declaration_type__)
        dir(Declarations.Field.OneDecoratorField)

    def test_add_same_interface(self):

        target_registry(Field, cls_=OneField, name_="SameField")

        try:
            @target_registry(Field)
            class SameField(OneField):
                pass

            self.fail('No watch dog to add 2 same field')
        except FieldException:
            pass

    def test_remove_interface(self):

        target_registry(Field, cls_=OneField, name_="Field2Remove")
        try:
            remove_registry(Field.Field2Remove, OneField)
            self.fail('No watch dog to remove field')
        except FieldException:
            pass
