# -*- coding: utf-8 -*-
import unittest
from anyblok.registry import Registry
from anyblok.blok import BlokManager
from anyblok._argsparse import ArgsParseManager
from anyblok.migration import MigrationException
from contextlib import contextmanager
from sqlalchemy import Column, Integer, TEXT
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
        for table in ('test', 'test2', 'othername'):
            try:
                self.registry.migration.table(table).drop()
            except:
                pass

        self.registry.migration.conn.close()
        self.registry.close()

    @contextmanager
    def cnx(self):
        cnx = self.registry.session.connection()
        try:
            yield cnx
        except Exception:
            cnx.execute("rollback")
            raise
        finally:
            cnx.close()

    def test_add_table(self):
        self.registry.migration.table().add('test2')
        self.registry.migration.table('test2')

    def test_add_column(self):
        t = self.registry.migration.table('test')
        t.column().add(Column('new_column', Integer))
        t.column('new_column')

    def test_drop_table(self):
        self.registry.migration.table('test').drop()
        try:
            self.registry.migration.table('Test')
            self.fail("Table not drop")
        except MigrationException:
            pass

    def test_drop_column(self):
        t = self.registry.migration.table('test')
        t.column('other').drop()
        try:
            t.column('other')
            self.fail("Column not drop")
        except MigrationException:
            pass

    def test_alter_table_name(self):
        t = self.registry.migration.table('test')
        t.alter(name='othername')
        self.registry.migration.table('othername')
        try:
            self.registry.migration.table('test')
            self.fail("table not rename")
        except MigrationException:
            pass

    def test_alter_column_name(self):
        t = self.registry.migration.table('test')
        t.column('other').alter(name='othername')
        t.column('othername')
        try:
            t.column('other')
            self.fail("Column not rename")
        except MigrationException:
            pass

    def test_alter_column_nullable(self):
        t = self.registry.migration.table('test')
        c = t.column('other').alter(nullable=False)
        self.assertEqual(c.nullable(), False)

    def test_alter_column_default(self):
        t = self.registry.migration.table('test')
        c = t.column('other').alter(server_default='test')
        self.assertEqual(c.server_default(), "'test'::character varying")

    def test_index(self):
        t = self.registry.migration.table('test')
        t.index().add(t.column('integer'))
        t.index(t.column('integer')).drop()

    def test_alter_column_type(self):
        t = self.registry.migration.table('test')
        c = t.column('other').alter(type_=TEXT)
        self.assertEqual(c.type().__class__, TEXT)

    def test_alter_column_primary_key(self):
        t = self.registry.migration.table('test')
        t.primarykey().drop().add(t.column('other'))

    def test_alter_column_foreign_key(self):
        c = self.registry.migration.table('test').column('other')
        c.foreign_key().add(self.registry.System.Blok.name)
        c.foreign_key().drop()

    def test_constraint_unique(self):
        t = self.registry.migration.table('test')
        t.unique().add(t.column('other'))
        t.unique(t.column('other')).drop()

    def test_constraint_check(self):
        t = self.registry.migration.table('test')
        Test = self.registry.Test
        name = 'chk_name_on_test'
        t.check().add(name, Test.other != 'test')
        t.check(name).drop()

    def test_detect_column_added(self):
        # Remove a column on the table force the detection to found new column
        # which is existing in metadata but not in table
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(integer INT PRIMARY KEY NOT NULL);""")
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has("Add test.other"), True)

    def test_detect_nullable(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) NOT NULL
                );""")
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has("Alter test.other"), True)

    def test_detect_server_default(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) DEFAULT 9.99
                );""")
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has("Alter test.other"), True)

    def test_detect_index(self):
        with self.cnx() as conn:
            conn.execute("""CREATE INDEX other_idx ON test (other);""")
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has("add index 'other_idx' on test"), True)

    def test_detect_type(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other INT
                );""")
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has("Alter test.other"), True)

    def test_detect_primary_key(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT NOT NULL,
                    other CHAR(64) PRIMARY KEY NOT NULL
                );""")
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has("Alter test.integer"), True)
        self.assertEqual(report.log_has("Alter test.other"), True)

    def test_detect_foreign_key(self):
        #with self.cnx() as conn:
        #    conn.execute("DROP TABLE test")
        #    conn.execute(
        #        """CREATE TABLE test(
        #            integer INT PRIMARY KEY NOT NULL,
        #            other CHAR(64) references system_blok(name)
        #        );""")
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has("Alter test.other"), True)

    def test_detect_constrainte(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) CONSTRAINT unique_other UNIQUE
                );""")
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has("Alter test.other"), True)
