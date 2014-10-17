from anyblok.tests.testcase import DBTestCase
from anyblok import Declarations
from sqlalchemy import func
from unittest import skipIf
import sqlalchemy
target_registry = Declarations.target_registry
Field = Declarations.Field
Model = Declarations.Model
Column = Declarations.Column
FieldException = Declarations.Exception.FieldException


@target_registry(Field)
class OneFieldForTest(Field):
    pass


def field_without_name():

    OneFieldForTest = Field.OneFieldForTest

    @target_registry(Model)
    class Test:

        id = Column.Integer(primary_key=True)
        field = OneFieldForTest()


class TestField(DBTestCase):

    def test_field_without_name(self):
        self.init_registry(field_without_name)

    def define_field_function(self):

        @target_registry(Model)
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
