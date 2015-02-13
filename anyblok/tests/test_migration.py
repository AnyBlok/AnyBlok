# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase
from anyblok.registry import Registry, RegistryManager
from anyblok.blok import BlokManager
from anyblok._argsparse import ArgsParseManager
from anyblok.environment import EnvironmentManager
from contextlib import contextmanager
from sqlalchemy import Column, Integer, TEXT
from anyblok import Declarations
from sqlalchemy.exc import InternalError
from unittest import skipIf
import alembic
from copy import deepcopy
MigrationException = Declarations.Exception.MigrationException


class TestMigration(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestMigration, cls).setUpClass()
        cls.init_argsparse_manager()
        cls.createdb()
        BlokManager.load('AnyBlok')

        register = Declarations.register
        Model = Declarations.Model
        Int = Declarations.Column.Integer
        Str = Declarations.Column.String

        cls.loaded_bloks = deepcopy(RegistryManager.loaded_bloks)
        EnvironmentManager.set('current_blok', 'anyblok-core')

        @register(Model)
        class Test:
            integer = Int(primary_key=True)
            other = Str()

        @register(Model)
        class TestUnique:
            integer = Int(primary_key=True)
            other = Str(unique=True)

        @register(Model)
        class TestFKTarget:
            integer = Int(primary_key=True)

        @register(Model)
        class TestFK:
            integer = Int(primary_key=True)
            other = Int(foreign_key=(Model.TestFKTarget, 'integer'))

        EnvironmentManager.set('current_blok', None)

    def setUp(self):
        super(TestMigration, self).setUp()
        self.registry = Registry(ArgsParseManager.get('dbname'))
        self.registry.init_migration()

    @classmethod
    def tearDownClass(cls):
        super(TestMigration, cls).tearDownClass()
        BlokManager.unload()
        RegistryManager.loaded_bloks = cls.loaded_bloks
        cls.dropdb()

    def tearDown(self):
        super(TestMigration, self).tearDown()
        for table in ('test', 'test2', 'othername', 'testfk', 'testfktarget',
                      'testunique'):
            try:
                self.registry.migration.table(table).drop()
            except:
                pass

        self.registry.migration.conn.close()
        self.registry.close()

    @contextmanager
    def cnx(self):
        cnx = self.registry.migration.conn
        try:
            yield cnx
        except Exception:
            cnx.execute("rollback")
            raise

    def test_add_table(self):
        self.registry.migration.table().add('test2')
        self.registry.migration.table('test2')

    def fill_test_table(self):
        Test = self.registry.Test
        vals = [{'other': 'test %d' % x} for x in range(10)]
        Test.multi_insert(*vals)

    def test_add_column(self):
        t = self.registry.migration.table('test')
        t.column().add(Column('new_column', Integer))
        t.column('new_column')

    def test_add_column_in_filled_table(self):
        self.fill_test_table()
        t = self.registry.migration.table('test')
        t.column().add(Column('new_column', Integer))
        t.column('new_column')

    def test_add_not_null_column(self):
        t = self.registry.migration.table('test')
        t.column().add(Column('new_column', Integer, nullable=False))
        t.column('new_column')

    def test_add_not_null_column_in_filled_table(self):
        self.fill_test_table()
        t = self.registry.migration.table('test')
        t.column().add(Column('new_column', Integer, nullable=False))
        t.column('new_column')

    def test_add_not_null_column_in_filled_table_with_default_value(self):
        self.fill_test_table()
        t = self.registry.migration.table('test')
        t.column().add(Column('new_column', Integer, nullable=False,
                       server_default="1"))
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

    def test_alter_column_nullable_in_filled_table(self):
        t = self.registry.migration.table('test')
        t.column().add(Column('new_column', Integer))
        self.fill_test_table()
        c = t.column('new_column').alter(nullable=False)
        # the column doesn't change of nullable to not lock the migration
        self.assertEqual(c.nullable(), True)

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
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has("Add test.other"), False)

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
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has("Alter test.other"), False)

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
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has("Alter test.other"), False)

    def test_detect_drop_index(self):
        with self.cnx() as conn:
            conn.execute("""CREATE INDEX other_idx ON test (other);""")
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has("Drop index other_idx on test"), True)
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has(
            "Drop index other_idx on test"), False)

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
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has("Alter test.other"), False)

    @skipIf(alembic.__version__ <= "0.7.4", "Alembic doesn't implement yet")
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
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has("Alter test.integer"), False)
        self.assertEqual(report.log_has("Alter test.other"), False)

    def test_detect_add_foreign_key(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE testfk")
            conn.execute(
                """CREATE TABLE testfk(
                    integer INT PRIMARY KEY NOT NULL,
                    other INT
                );""")
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has(
            "Add Foreign keys on testfk.other => testfktarget.integer"), True)
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has(
            "Add Foreign keys on testfk.other => testfktarget.integer"), False)

    def test_detect_drop_foreign_key(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) references system_blok(name)
                );""")
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has(
            "Drop Foreign keys on test.other => system_blok.name"), True)
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has(
            "Drop Foreign keys on test.other => system_blok.name"), False)

    def test_detect_drop_column_with_foreign_key(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64),
                    other2 CHAR(64) references system_blok(name)
                );""")
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has(
            "Drop Foreign keys on test.other2 => system_blok.name"), True)
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has(
            "Drop Foreign keys on test.other2 => system_blok.name"), False)

    def test_detect_add_unique_constrainte(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE testunique")
            conn.execute(
                """CREATE TABLE testunique(
                    integer INT  PRIMARY KEY NOT NULL,
                    other CHAR(64)
                );""")
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has(
            "Add unique constraint on testunique (other)"), True)
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertEqual(report.log_has(
            "Add unique constraint on testunique (other)"), False)

    def test_detect_drop_constraint(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) CONSTRAINT unique_other UNIQUE
                );""")
        report = self.registry.migration.detect_changed()
        self.assertEqual(
            report.log_has("Drop constraint unique_other on test"), True)
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertEqual(
            report.log_has("Drop constraint unique_other on test"), False)

    def test_savepoint(self):
        Test = self.registry.Test
        self.fill_test_table()
        self.registry.migration.savepoint('test')
        self.fill_test_table()
        self.assertEqual(Test.query().count(), 20)
        self.registry.migration.rollback_savepoint('test')
        self.assertEqual(Test.query().count(), 10)
        self.registry.migration.release_savepoint('test')

    def test_savepoint_without_rollback(self):
        self.registry.migration.savepoint('test')
        self.registry.migration.release_savepoint('test')
        try:
            self.registry.migration.rollback_savepoint('test')
            self.fail("save point must be release")
        except InternalError:
            pass
