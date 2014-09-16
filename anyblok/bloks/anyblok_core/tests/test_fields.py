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


def field_without_name():

    OneFieldForTest = Field.OneFieldForTest

    @target_registry(Model)
    class Test:

        id = Column.Integer(primary_key=True)
        field = OneFieldForTest()


class TestField(DBTestCase):

    def test_field_without_name(self):
        self.init_registry(field_without_name)
