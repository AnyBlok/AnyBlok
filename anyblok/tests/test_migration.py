# -*- coding: utf-8 -*-
import unittest
from anyblok.registry import Registry
from anyblok.blok import BlokManager
from anyblok._argsparse import ArgsParseManager
from contextlib import contextmanager
from sqlalchemy import Column, Integer
from zope.component import getUtility


class TestMigration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestMigration, cls).setUpClass()
        env = {
            'dbname': 'test_anyblok',  # TODO use os.env
            'dbdrivername': 'postgres',
            'dbusername': '',
            'dbpassword': '',
            'dbhost': '',
            'dbport': '',
        }
        ArgsParseManager.configuration = env
        BlokManager.load('AnyBlok')

        import AnyBlok
        from AnyBlok import target_registry, Model
        from AnyBlok.Column import Integer as Int, String as Str

        AnyBlok.current_blok = 'anyblok-core'

        @target_registry(Model)
        class Test:
            integer = Int(label="Integer", primary_key=True)
            other = Str(label="Other")

        AnyBlok.current_blok = None
        from AnyBlok.Interface import ISqlAlchemyDataBase

        adapter = getUtility(ISqlAlchemyDataBase, 'postgres')
        adapter.createdb(ArgsParseManager.get('dbname'))

    def setUp(self):
        super(TestMigration, self).setUp()
        self.registry = Registry(ArgsParseManager.get('dbname'))

    @classmethod
    def tearDownClass(cls):
        super(TestMigration, cls).tearDownClass()
        BlokManager.unload()
        from AnyBlok.Interface import ISqlAlchemyDataBase

        adapter = getUtility(ISqlAlchemyDataBase, 'postgres')
        adapter.dropdb(ArgsParseManager.get('dbname'))

    def tearDown(self):
        super(TestMigration, self).tearDown()
        self.registry.close()

    @contextmanager
    def cnx(self):
        cnx = None
        try:
            cnx = self.registry.engine.connect()
            yield cnx
        except Exception:
            if cnx:
                cnx.execute("rollback")
            raise
        finally:
            if cnx:
                cnx.close()

    def test_add_column(self):
        self.registry.migration.add_column(
            'test', Column('new_column', Integer))
        with self.cnx() as conn:
            conn.execute("select new_column from test")

    def test_remove_column(self):
        self.registry.migration.add_column(
            'test', Column('new_column', Integer))
        self.registry.migration.remove_column('test', 'new_column')
        try:
            with self.cnx() as conn:
                conn.execute("select new_column from test")
            self.fail("Column not remove")
        except:
            pass

    def test_alter_column_name(self):
        self.fail('Not Implemented yet')

    def test_alter_column_nullable(self):
        self.fail('Not Implemented yet')

    def test_alter_column_autoincrement(self):
        self.fail('Not Implemented yet')

    def test_alter_column_default(self):
        self.fail('Not Implemented yet')

    def test_alter_column_index(self):
        self.fail('Not Implemented yet')

    def test_alter_column_type(self):
        self.fail('Not Implemented yet')

    def test_alter_column_primary_key(self):
        self.fail('Not Implemented yet')

    def test_alter_column_foreign_key(self):
        self.fail('Not Implemented yet')

    def test_alter_column_constrainte(self):
        self.fail('Not Implemented yet')

    def test_detect_column_added(self):
        # Remove a column on the table force the detection to found new column
        # which is existing in metadata but not in table
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(integer INT PRIMARY KEY NOT NULL);""")
        report = self.registry.migration.detect_changed()
        self.assertEqual(
            report.log_has("Add system_column.autoincrement"), True)

    def test_detect_nullable(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) NOT NULL
                );""")
        report = self.registry.migration.detect_changed()
        self.assertEqual(
            report.log_has("Alter system_column.autoincrement"), True)
        self.fail('Not Implemented yet')

    def test_detect_autoincrement(self):
        self.fail('Not Implemented yet')

    def test_detect_default(self):
        self.fail('Not Implemented yet')

    def test_detect_index(self):
        self.fail('Not Implemented yet')

    def test_detect_type(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other INT
                );""")
        report = self.registry.migration.detect_changed()
        self.assertEqual(
            report.log_has("Alter system_column.autoincrement"), True)
        self.fail('Not Implemented yet')

    def test_detect_primary_key(self):
        self.fail('Not Implemented yet')

    def test_detect_foreign_key(self):
        self.fail('Not Implemented yet')

    def test_detect_constrainte(self):
        self.fail('Not Implemented yet')
