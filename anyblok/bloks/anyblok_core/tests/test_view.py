from anyblok.tests.testcase import DBTestCase
from anyblok import Declarations
from sqlalchemy.sql import select
target_registry = Declarations.target_registry
Model = Declarations.Model


def simple_view():
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String

    @target_registry(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @target_registry(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @target_registry(Model, is_sql_view=True)
    class TestView:
        code = String(primary_key=True)
        val1 = Integer()
        val2 = Integer()

        @classmethod
        def sqlalchemy_view_declaration(cls):
            T1 = cls.registry.T1
            T2 = cls.registry.T2
            query = select([T1.code.label('code'),
                            T1.val.label('val1'),
                            T2.val.label('val2')])
            return query.where(T1.code == T2.code)


def simple_view_without_primary_key():
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String

    @target_registry(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @target_registry(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @target_registry(Model, is_sql_view=True)
    class TestView:
        code = String()
        val1 = Integer()
        val2 = Integer()

        @classmethod
        def sqlalchemy_view_declaration(cls):
            T1 = cls.registry.T1
            T2 = cls.registry.T2
            query = select([T1.code.label('code'),
                            T1.val.label('val1'),
                            T1.val.label('val2')])
            return query.where(T1.code == T2.code)


def simple_view_without_view_declaration():
    Integer = Declarations.Column.Integer
    String = Declarations.Column.String

    @target_registry(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @target_registry(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @target_registry(Model, is_sql_view=True)
    class TestView:
        code = String(primary_key=True)
        val1 = Integer()
        val2 = Integer()


class TestView(DBTestCase):

    def test_simple_view(self):
        registry = self.init_registry(simple_view)

        registry.T1.insert(code='test1', val=1)
        registry.T2.insert(code='test1', val=2)
        registry.T1.insert(code='test2', val=3)
        registry.T2.insert(code='test2', val=4)

        TestView = registry.TestView
        v1 = TestView.query().filter(TestView.code == 'test1').first()
        v2 = TestView.query().filter(TestView.code == 'test2').first()
        self.assertEqual(v1.val1, 1)
        self.assertEqual(v1.val2, 2)
        self.assertEqual(v2.val1, 3)
        self.assertEqual(v2.val2, 4)

    def test_view_update_method(self):
        registry = self.init_registry(simple_view)

        registry.T1.insert(code='test1', val=1)
        registry.T2.insert(code='test1', val=2)
        registry.T1.insert(code='test2', val=3)
        registry.T2.insert(code='test2', val=4)

        try:
            registry.TestView.query().update({'val2': 3})
            self.fail('No watchdog for update')
        except Declarations.Exception.ViewException:
            pass

    def test_view_delete_method(self):
        registry = self.init_registry(simple_view)

        registry.T1.insert(code='test1', val=1)
        registry.T2.insert(code='test1', val=2)
        registry.T1.insert(code='test2', val=3)
        registry.T2.insert(code='test2', val=4)

        try:
            registry.TestView.query().delete()
            self.fail('No watchdog for delete')
        except Declarations.Exception.ViewException:
            pass

    def test_simple_view_without_primary_key(self):
        try:
            self.init_registry(simple_view_without_primary_key)
            self.fail('No error when any primary key column are declared')
        except Declarations.Exception.ViewException:
            pass

    def test_simple_view_without_view_declaration(self):
        try:
            self.init_registry(simple_view_without_view_declaration)
            self.fail('No error when any view declaration method are declared')
        except Declarations.Exception.ViewException:
            pass
