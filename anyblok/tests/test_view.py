# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import DBTestCase
from anyblok.model import ViewException
from anyblok import Declarations
from sqlalchemy.sql import select
from sqlalchemy.exc import OperationalError
from anyblok.column import Integer, String

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

    @register(Model, is_sql_view=True, tablename=Model.TestView)
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

    @register(Model, is_sql_view=True, tablename='testview')
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

    @register(Model, is_sql_view=True)
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

    @register(Model, is_sql_view=True)
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

    @register(Model, is_sql_view=True)
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
