from anyblok.tests.testcase import DBTestCase


def simple_model():

    from AnyBlok import target_registry, Model
    from AnyBlok.Column import Integer, String

    @target_registry(Model)
    class Test:
        id = Integer(label="id", primary_key=True)
        name = String(label="Name")


def model_with_foreign_key():

    from AnyBlok import target_registry, Model
    from AnyBlok.Column import Integer, String

    @target_registry(Model)
    class TestFk:

        name = String(label="Name", primary_key=True)

    @target_registry(Model)
    class Test:

        id = Integer(label="id", primary_key=True)
        name = String(label="Name", foreign_key=(Model.TestFk, 'name'))


class TestInherit(DBTestCase):

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
