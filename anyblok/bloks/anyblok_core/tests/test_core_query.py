from anyblok.tests.testcase import DBTestCase


class TestException(Exception):
    pass


class TestCoreQuery(DBTestCase):

    def test_update(self):

        def inherit_update():

            from anyblok import Declarations
            Model = Declarations.Model
            Integer = Declarations.Column.Integer

            @Declarations.target_registry(Model)
            class Test:

                id = Integer(label="ID", primary_key=True)

                @classmethod
                def update(cls, query, **kwargs):
                    raise TestException('test')

        registry = self.init_registry(inherit_update)
        try:
            registry.Test.query().update()
            self.fail('Update must fail')
        except TestException:
            pass

    def test_inherit(self):

        def inherit():

            from anyblok import Declarations
            Core = Declarations.Core

            @Declarations.target_registry(Core)
            class Query:

                def foo(self):
                    return True

        registry = self.init_registry(inherit)
        self.assertEqual(registry.System.Blok.query().foo(), True)
