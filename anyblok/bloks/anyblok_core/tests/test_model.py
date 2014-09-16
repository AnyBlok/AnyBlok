from anyblok.tests.testcase import TestCase, DBTestCase
from anyblok.model import has_sql_fields, get_fields
from anyblok import Declarations
target_registry = Declarations.target_registry
Model = Declarations.Model


def simple_model():
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String

    @target_registry(Model)
    class Test:
        id = Integer(primary_key=True)
        name = String()


def model_with_foreign_key():
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String

    @target_registry(Model)
    class TestFk:

        name = String(primary_key=True)

    @target_registry(Model)
    class Test:

        id = Integer(primary_key=True)
        name = String(foreign_key=(Model.TestFk, 'name'))


class TestModel(DBTestCase):

    def check_registry(self, Model):
        t = Model.insert(name="test")
        t2 = Model.query().first()
        self.assertEqual(t2, t)

    def test_simple_model(self):
        registry = self.init_registry(simple_model)
        self.check_registry(registry.Test)

    def test_simple_model_with_wrong_column(self):
        registry = self.init_registry(simple_model)

        try:
            registry.Test.insert(name="test", other="other")
            self.fail('No error when an inexisting colomn has filled')
        except TypeError:
            pass

    def test_simple_model_with_wrong_value(self):
        registry = self.init_registry(simple_model)

        t = registry.Test.insert(name=1)
        registry.commit()
        self.assertNotEqual(t.name, 1)

    def test_model_with_foreign_key(self):
        registry = self.init_registry(model_with_foreign_key)
        registry.TestFk.insert(name='test')
        self.check_registry(registry.Test)


class TestModelAssembling(TestCase):

    def test_has_sql_fields_ok(self):

        class MyModel:
            one_field = Declarations.Column.String()

        self.assertEqual(has_sql_fields([MyModel]), True)

    def test_has_sql_fields_ko(self):

        class MyModel:
            one_field = None

        self.assertEqual(has_sql_fields([MyModel]), False)

    def test_get_fields(self):

        class MyModel:
            one_field = Declarations.Column.String()

        self.assertEqual(get_fields(MyModel), {'one_field': MyModel.one_field})
