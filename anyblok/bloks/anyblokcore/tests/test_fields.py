from anyblok.tests.testcase import DBTestCase
from AnyBlok.Exception import FieldException
from AnyBlok import target_registry, Model
from AnyBlok import Field
from AnyBlok.Column import Integer


@target_registry(Field)
class OneFieldForTest(Field):
    pass


def field_with_name():

    from AnyBlok.Field import OneFieldForTest

    @target_registry(Model)
    class Test:

        id = Integer(label='id', primary_key=True)
        field = OneFieldForTest(label='id')


def field_without_name():

    from AnyBlok.Field import OneFieldForTest

    @target_registry(Model)
    class Test:

        id = Integer(label='id', primary_key=True)
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
