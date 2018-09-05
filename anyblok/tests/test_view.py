# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import DBTestCase
from anyblok.model.factory import ViewFactory
from anyblok.model.common import VIEW
from anyblok.model.exceptions import ViewException
from anyblok import Declarations
from sqlalchemy.sql import select, expression, union
from sqlalchemy.exc import OperationalError
from anyblok.column import Integer, String
from anyblok.relationship import Many2One

register = Declarations.register
Model = Declarations.Model


def simple_view():

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, factory=ViewFactory)
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


def deprecated_view_before_0_19_2():

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, is_sql_view=True)
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


def deprecated_view_before_0_19_4():

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, type=VIEW)
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


def view_with_relationship():

    @register(Model)
    class Rs:
        id = Integer(primary_key=True)

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()
        rs_id = Integer(foreign_key=Model.Rs.use('id'))
        rs = Many2One(model=Model.Rs, column_names='rs_id')

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, factory=ViewFactory)
    class TestView:
        code = String(primary_key=True)
        val1 = Integer()
        val2 = Integer()
        rs = Many2One(model=Model.Rs)

        @classmethod
        def sqlalchemy_view_declaration(cls):
            T1 = cls.registry.T1
            T2 = cls.registry.T2
            query = select([T1.code.label('code'),
                            T1.val.label('val1'),
                            T1.rs_id.label('rs_id'),
                            T2.val.label('val2')])
            return query.where(T1.code == T2.code)


def view_with_relationship_on_self():

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()
        parent = Many2One(model='Model.T1')

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, factory=ViewFactory)
    class TestView:
        code = String(primary_key=True)
        val1 = Integer()
        val2 = Integer()
        parent = Many2One(model='Model.TestView')

        @classmethod
        def sqlalchemy_view_declaration(cls):
            T1 = cls.registry.T1
            TP = cls.registry.T1.aliased()
            T2 = cls.registry.T2
            subquery = union(
                select([
                    T1.code.label('code'),
                    TP.code.label('parent_code')]
                ).where(T1.parent_id == TP.id),
                select([
                    T1.code.label('code'),
                    expression.literal_column("null as parent_code")
                ]).where(T1.parent_id.is_(None))
            ).alias()
            query = select([T1.code.label('code'),
                            T1.val.label('val1'),
                            T2.val.label('val2'),
                            subquery.c.parent_code.label('parent_code')])
            query = query.where(subquery.c.code == T1.code)
            query = query.where(subquery.c.code == T2.code)
            return query


def view_with_relationship_on_self_2():

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()
        parent = Many2One(model='Model.T1')

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, factory=ViewFactory)
    class TestView:
        code = String(primary_key=True)
        val1 = Integer(primary_key=True)
        val2 = Integer()
        parent = Many2One(model='Model.TestView')

        @classmethod
        def sqlalchemy_view_declaration(cls):
            T1 = cls.registry.T1
            TP = cls.registry.T1.aliased()
            T2 = cls.registry.T2
            subquery = union(
                select([
                    T1.code.label('code'),
                    TP.id.label('parent_val1'),
                    TP.code.label('parent_code')
                ]).where(T1.parent_id == TP.id),
                select([
                    T1.code.label('code'),
                    expression.literal_column("null as parent_val1"),
                    expression.literal_column("null as parent_code")
                ]).where(T1.parent_id.is_(None))
            ).alias()
            query = select([T1.code.label('code'),
                            T1.val.label('val1'),
                            T2.val.label('val2'),
                            subquery.c.parent_val1.label('parent_val1'),
                            subquery.c.parent_code.label('parent_code')])
            query = query.where(subquery.c.code == T1.code)
            query = query.where(subquery.c.code == T2.code)
            return query


def simple_view_with_same_table_by_declaration_model():

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, factory=ViewFactory)
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

    @register(Model, factory=ViewFactory, tablename=Model.TestView)
    class TestView2:
        code = String(primary_key=True)
        val1 = Integer()
        val2 = Integer()


def simple_view_with_same_table_by_name():

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, factory=ViewFactory)
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

    @register(Model, factory=ViewFactory, tablename='testview')
    class TestView2:
        code = String(primary_key=True)
        val1 = Integer()
        val2 = Integer()


def simple_view_with_same_table_by_inherit():

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, factory=ViewFactory)
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

    @register(Model, factory=ViewFactory)
    class TestView2(Model.TestView):
        code = String(primary_key=True)
        val1 = Integer()
        val2 = Integer()


def simple_view_without_primary_key():

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, factory=ViewFactory)
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

    @register(Model)
    class T1:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model)
    class T2:
        id = Integer(primary_key=True)
        code = String()
        val = Integer()

    @register(Model, factory=ViewFactory)
    class TestView:
        code = String(primary_key=True)
        val1 = Integer()
        val2 = Integer()


class TestView(DBTestCase):

    def test_view_has_a_mapper(self):
        registry = self.init_registry(simple_view)
        self.assertIsNotNone(registry.TestView.__mapper__)

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

    def test_deprecated_view_1(self):
        registry = self.init_registry(deprecated_view_before_0_19_2)
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

    def test_deprecated_view_2(self):
        registry = self.init_registry(deprecated_view_before_0_19_4)
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

    def test_view_with_relationship(self):
        registry = self.init_registry(view_with_relationship)
        rs1 = registry.Rs.insert()
        rs2 = registry.Rs.insert()
        registry.T1.insert(code='test1', val=1, rs=rs1)
        registry.T2.insert(code='test1', val=2)
        registry.T1.insert(code='test2', val=3, rs=rs2)
        registry.T2.insert(code='test2', val=4)
        TestView = registry.TestView
        v1 = TestView.query().filter(TestView.code == 'test1').first()
        v2 = TestView.query().filter(TestView.code == 'test2').first()
        self.assertEqual(v1.val1, 1)
        self.assertEqual(v1.val2, 2)
        self.assertEqual(v1.rs.id, rs1.id)
        self.assertEqual(v2.val1, 3)
        self.assertEqual(v2.val2, 4)
        self.assertEqual(v2.rs.id, rs2.id)

    def test_fix_issue_53_with_one_column(self):
        registry = self.init_registry(view_with_relationship_on_self)
        parent = registry.T1.insert(code='test1', val=1)
        registry.T2.insert(code='test1', val=2)
        registry.T1.insert(code='test2', val=3, parent=parent)
        registry.T2.insert(code='test2', val=4)
        TestView = registry.TestView
        v1 = TestView.query().filter(TestView.code == 'test1').first()
        v2 = TestView.query().filter(TestView.code == 'test2').first()
        self.assertEqual(v1.val1, 1)
        self.assertEqual(v1.val2, 2)
        self.assertIsNone(v1.parent)
        self.assertEqual(v2.val1, 3)
        self.assertEqual(v2.val2, 4)
        self.assertEqual(v2.parent.code, v1.code)

    def test_fix_issue_53_with_two_column(self):
        registry = self.init_registry(view_with_relationship_on_self_2)
        parent = registry.T1.insert(code='test1', val=1)
        registry.T2.insert(code='test1', val=2)
        registry.T1.insert(code='test2', val=3, parent=parent)
        registry.T2.insert(code='test2', val=4)
        TestView = registry.TestView
        v1 = TestView.query().filter(TestView.code == 'test1').first()
        v2 = TestView.query().filter(TestView.code == 'test2').first()
        self.assertEqual(v1.val1, 1)
        self.assertEqual(v1.val2, 2)
        self.assertIsNone(v1.parent)
        self.assertEqual(v2.val1, 3)
        self.assertEqual(v2.val2, 4)
        self.assertEqual(v2.parent.code, v1.code)

    def check_same_view(self, registry):
        registry.T1.insert(code='test1', val=1)
        registry.T2.insert(code='test1', val=2)
        registry.T1.insert(code='test2', val=3)
        registry.T2.insert(code='test2', val=4)
        TestView = registry.TestView
        TestView2 = registry.TestView2
        self.assertEqual(registry.TestView.__view__,
                         registry.TestView2.__view__)
        v1 = TestView.query().filter(TestView.code == 'test1').first()
        v2 = TestView.query().filter(TestView2.code == 'test1').first()
        self.assertEqual(v1.val1, v2.val1)
        self.assertEqual(v1.val2, v2.val2)

    def test_same_view_by_declaration_model(self):
        registry = self.init_registry(
            simple_view_with_same_table_by_declaration_model)
        self.check_same_view(registry)

    def test_same_view_by_name(self):
        registry = self.init_registry(simple_view_with_same_table_by_name)
        self.check_same_view(registry)

    def test_same_view_by_inherit(self):
        registry = self.init_registry(simple_view_with_same_table_by_inherit)
        self.check_same_view(registry)

    def test_view_update_method(self):
        registry = self.init_registry(simple_view)
        registry.T1.insert(code='test1', val=1)
        registry.T2.insert(code='test1', val=2)
        registry.T1.insert(code='test2', val=3)
        registry.T2.insert(code='test2', val=4)
        with self.assertRaises(OperationalError):
            registry.TestView.query().update({'val2': 3})

    def test_view_delete_method(self):
        registry = self.init_registry(simple_view)
        registry.T1.insert(code='test1', val=1)
        registry.T2.insert(code='test1', val=2)
        registry.T1.insert(code='test2', val=3)
        registry.T2.insert(code='test2', val=4)
        with self.assertRaises(OperationalError):
            registry.TestView.query().delete()

    def test_simple_view_without_primary_key(self):
        with self.assertRaises(ViewException):
            self.init_registry(simple_view_without_primary_key)

    def test_simple_view_without_view_declaration(self):
        with self.assertRaises(ViewException):
            self.init_registry(simple_view_without_view_declaration)
