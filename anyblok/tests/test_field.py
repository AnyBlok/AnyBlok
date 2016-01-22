# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase, DBTestCase
from anyblok.field import Field, FieldException, Function
from anyblok.column import Integer, String
from anyblok import Declarations
from sqlalchemy import func


Model = Declarations.Model
register = Declarations.register


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
        field = OneField()
        field.get_sqlalchemy_mapping(None, None, 'a_field', None)
        self.assertEqual(field.label, 'A field')


def field_without_name():

    @register(Model)
    class Test:

        id = Integer(primary_key=True)
        field = OneField()


class TestField2(DBTestCase):

    def test_field_without_name(self):
        self.init_registry(field_without_name)

    def define_field_function(self):

        @register(Model)
        class Test:

            id = Integer(primary_key=True)
            first_name = String()
            last_name = String()
            name = Function(fget='fget', fset='fset', fdel='fdel',
                            fexpr='fexpr')

            def fget(self):
                return '{0} {1}'.format(self.first_name, self.last_name)

            def fset(self, value):
                self.first_name, self.last_name = value.split(' ', 1)

            def fdel(self):
                self.first_name = self.last_name = None

            @classmethod
            def fexpr(cls):
                return func.concat(cls.first_name, ' ', cls.last_name)

    def test_field_function_fget(self):
        registry = self.init_registry(self.define_field_function)
        t = registry.Test.insert(first_name='Jean-Sebastien',
                                 last_name='SUZANNE')
        self.assertEqual(t.name, 'Jean-Sebastien SUZANNE')
        t = registry.Test.query().first()
        self.assertEqual(t.name, 'Jean-Sebastien SUZANNE')

    def test_field_function_fset(self):

        def add_in_registry():

            @register(Model)
            class Test:

                id = Integer(primary_key=True)
                _name = String()
                name = Function(fget='fget', fset='fset', fdel='fdel',
                                fexpr='fexpr')

                def fget(self):
                    return self._name

                def fset(self, value):
                    self._name = value

                def fdel(self):
                    self._name = None

                @classmethod
                def fexpr(cls):
                    return cls._name

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert(name='Jean-Sebastien SUZANNE')
        self.assertEqual(t._name, 'Jean-Sebastien SUZANNE')
        t = registry.Test.query().first()
        t.name = 'Mister ANYBLOK'
        self.assertEqual(t._name, 'Mister ANYBLOK')
        t.update(name='Jean-Sebastien SUZANNE')
        self.assertEqual(t._name, 'Jean-Sebastien SUZANNE')

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

                id = Integer(primary_key=True)
                val1 = Integer()
                val2 = Function(fget='fget', fset='fset')

                def fget(self):
                    return 2 * self.val1

                def fset(self, val):
                    self.val1 = val / 2

        registry = self.init_registry(add_in_registry)
        registry.Test.insert(val1=1)
        with self.assertRaises(FieldException):
            registry.Test.query().filter(
                registry.Test.val2 == 2).first()
