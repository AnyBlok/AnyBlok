# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase, DBTestCase
from anyblok import Declarations
from sqlalchemy import func
from unittest import skipIf
import sqlalchemy
Model = Declarations.Model
Field = Declarations.Field
Column = Declarations.Column
RelationShip = Declarations.RelationShip
register = Declarations.register
unregister = Declarations.unregister
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
        register(Field, cls_=OneField, name_='RealField')
        field = Field.RealField()
        field.get_sqlalchemy_mapping(None, None, 'a_field', None)
        self.assertEqual(field.label, 'A field')

    def test_add_interface(self):
        register(Field, cls_=OneField, name_='OneField')
        self.assertEqual('Field', Field.OneField.__declaration_type__)
        dir(Declarations.Field.OneField)

    def test_add_interface_with_decorator(self):

        @register(Field)
        class OneDecoratorField(OneField):
            pass

        self.assertEqual('Field', Field.OneDecoratorField.__declaration_type__)
        dir(Declarations.Field.OneDecoratorField)

    def test_add_same_interface(self):

        register(Field, cls_=OneField, name_="SameField")

        try:
            @register(Field)
            class SameField(OneField):
                pass

            self.fail('No watch dog to add 2 same field')
        except FieldException:
            pass

    def test_remove_interface(self):

        register(Field, cls_=OneField, name_="Field2Remove")
        try:
            unregister(Field.Field2Remove, OneField)
            self.fail('No watch dog to remove field')
        except FieldException:
            pass


@register(Field)
class OneFieldForTest(Field):
    pass


def field_without_name():

    OneFieldForTest = Field.OneFieldForTest

    @register(Model)
    class Test:

        id = Column.Integer(primary_key=True)
        field = OneFieldForTest()


class TestField2(DBTestCase):

    def test_field_without_name(self):
        self.init_registry(field_without_name)

    def define_field_function(self):

        @register(Model)
        class Test:

            id = Column.Integer(primary_key=True)
            first_name = Column.String()
            last_name = Column.String()
            name = Field.Function(
                fget='fget', fset='fset', fdel='fdel', fexpr='fexpr')

            def fget(self):
                return '{0} {1}'.format(self.first_name, self.last_name)

            def fset(self, value):
                self.first_name, self.last_name = value.split(' ', 1)

            def fdel(self):
                self.first_name = self.last_name = None

            def fexpr(cls):
                return func.concat(cls.first_name, ' ', cls.last_name)

    def test_field_function_fget(self):
        registry = self.init_registry(self.define_field_function)
        t = registry.Test.insert(first_name='Jean-Sebastien',
                                 last_name='SUZANNE')
        self.assertEqual(t.name, 'Jean-Sebastien SUZANNE')
        t = registry.Test.query().first()
        self.assertEqual(t.name, 'Jean-Sebastien SUZANNE')

    @skipIf(sqlalchemy.__version__ <= "0.9.8",
            "https://bitbucket.org/zzzeek/sqlalchemy/issue/3228")
    def test_field_function_fset(self):
        registry = self.init_registry(self.define_field_function)
        t = registry.Test.insert(name='Jean-Sebastien SUZANNE')
        self.assertEqual(t.first_name, 'Jean-Sebastien')
        self.assertEqual(t.last_name, 'SUZANNE')
        t = registry.Test.query().first()
        t.name = 'Mister ANYBLOK'
        self.assertEqual(t.first_name, 'Mister')
        self.assertEqual(t.last_name, 'ANYBLOK')
        t.update({'name': 'Jean-Sebastien SUZANNE'})
        self.assertEqual(t.first_name, 'Mister')
        self.assertEqual(t.last_name, 'ANYBLOK')

    def test_field_function_fdel(self):
        registry = self.init_registry(self.define_field_function)
        t = registry.Test.insert(first_name='jean-sebastien',
                                 last_name='suzanne')
        del t.name
        self.assertEqual(t.first_name, None)
        self.assertEqual(t.last_name, None)

    def test_field_function_fexpr(self):
        registry = self.init_registry(self.define_field_function)
        registry.Test.insert(first_name='Jean-Sebastien',
                             last_name='SUZANNE')
        t = registry.Test.query().filter(
            registry.Test.name == 'Jean-Sebastien SUZANNE').first()
        self.assertEqual(t.name, 'Jean-Sebastien SUZANNE')

    def test_field_function_without_fexpr(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Column.Integer(primary_key=True)
                val1 = Column.Integer()
                val2 = Field.Function(fget='fget', fset='fset')

                def fget(self):
                    return 2 * self.val1

                def fset(self, val):
                    self.val1 = val / 2

        registry = self.init_registry(add_in_registry)
        registry.Test.insert(val1=1)
        t = registry.Test.query().filter(registry.Test.val2 == 2).first()
        self.assertEqual(t.val1, 1)
        self.assertEqual(t.val2, 2)
