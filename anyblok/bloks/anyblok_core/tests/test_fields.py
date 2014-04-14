from anyblok.tests.testcase import DBTestCase
from anyblok import Declarations
target_registry = Declarations.target_registry
Field = Declarations.Field
Model = Declarations.Model
Column = Declarations.Column
FieldException = Declarations.Exception.FieldException


@target_registry(Field)
class OneFieldForTest(Field):
    pass


def field_with_name():

    OneFieldForTest = Field.OneFieldForTest

    @target_registry(Model)
    class Test:

        id = Column.Integer(label='id', primary_key=True)
        field = OneFieldForTest(label='id')


def field_without_name():

    OneFieldForTest = Field.OneFieldForTest

    @target_registry(Model)
    class Test:

        id = Column.Integer(label='id', primary_key=True)
        field = OneFieldForTest()


class TestField(DBTestCase):

    def test_field_with_name(self):
        self.init_registry(field_with_name)

    def test_field_without_name(self):
        try:
            self.init_registry(field_without_name)
            self.fail('No watch dog if no label attribute')
        except FieldException:
            pass
