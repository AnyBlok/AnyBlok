from anyblok.tests.testcase import DBTestCase
from unittest import skipIf
import sqlalchemy


class TestException(Exception):
    pass


class TestCoreQuery(DBTestCase):

    @skipIf(sqlalchemy.__version__ <= "0.9.7",
            "https://bitbucket.org/zzzeek/sqlalchemy/issue/3228")
    def test_update(self):
        def inherit_update():

            from anyblok import Declarations
            Model = Declarations.Model
            Integer = Declarations.Column.Integer

            @Declarations.target_registry(Model)
            class Test:

                id = Integer(primary_key=True)
                id2 = Integer()

                @classmethod
                def sqlalchemy_query_update(cls, query, *args, **kwargs):
                    raise TestException('test')

        registry = self.init_registry(inherit_update)
        try:
            registry.Test.query().update({'id2': 1})
            self.fail('Update must fail')
        except TestException:
            pass

        try:
            t = registry.System.Blok.query().first()
            t.update({'state': 'undefined'})
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
