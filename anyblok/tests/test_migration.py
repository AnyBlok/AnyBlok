# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Pierre Verkest <pverkest@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase
from anyblok.registry import Registry, RegistryManager
from anyblok.blok import BlokManager
from anyblok.config import Configuration
from anyblok.environment import EnvironmentManager
from anyblok.column import Integer as Int, String as Str
from anyblok.migration import MigrationException
from anyblok.relationship import Many2Many
from contextlib import contextmanager
from sqlalchemy import Column, Integer, TEXT
from anyblok import Declarations
from sqlalchemy.exc import InternalError
from unittest import skipIf
import alembic
from copy import deepcopy


class TestMigration(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestMigration, cls).setUpClass()
        cls.init_configuration_manager()
        cls.createdb()
        BlokManager.load()

        register = Declarations.register
        Model = Declarations.Model

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
            other = Int(foreign_key=Model.TestFKTarget.use('integer'))

        @register(Model)
        class TestM2M1:
            idmodel1 = Int(primary_key=True)

        @register(Model)
        class TestM2M2:
            idmodel2 = Int(primary_key=True)
            rel_m2m = Many2Many(label="Rel", model=Model.TestM2M1,
                                join_table='reltable',
                                remote_columns='idmodel1',
                                m2m_remote_columns='idmodel1',
                                local_columns='idmodel2',
                                m2m_local_columns='idmodel2',
                                many2many='rel_m2m_inv')

        EnvironmentManager.set('current_blok', None)

    def setUp(self):
        super(TestMigration, self).setUp()
        self.registry = Registry(Configuration.get('db_name'))

    @classmethod
    def tearDownClass(cls):
        super(TestMigration, cls).tearDownClass()
        BlokManager.unload()
        RegistryManager.loaded_bloks = cls.loaded_bloks
        cls.dropdb()

    def tearDown(self):
        super(TestMigration, self).tearDown()
        for table in ('test', 'test2', 'othername', 'testfk', 'testfktarget',
                      'testunique', 'reltab', 'testm2m1', 'testm2m2'):
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

    def test_add_column_with_default_value(self):
        t = self.registry.migration.table('test')
        t.column().add(Column('new_column', Integer, default=100))
        t.column('new_column')

    def test_add_column_with_default_str_value(self):
        t = self.registry.migration.table('test')
        t.column().add(Column('new_column', Integer, default='100'))
        t.column('new_column')

    def test_add_column_with_default_callable_value(self):

        def get_val():
            return 100

        self.fill_test_table()
        t = self.registry.migration.table('test')
        t.column().add(Column('new_column', Integer, default=get_val))
        t.column('new_column')
        res = [x for x in self.registry.execute(
            "select count(*) from test where new_column is null")][0][0]
        self.assertEqual(res, 0)

    def test_add_column_in_filled_table_with_default_value(self):
        self.fill_test_table()
        t = self.registry.migration.table('test')
        t.column().add(Column('new_column', Integer, default=100))
        t.column('new_column')
        res = [x for x in self.registry.execute(
            "select count(*) from test where new_column is null")][0][0]
        self.assertEqual(res, 0)

    def test_add_not_null_column_in_filled_table_with_default_value(self):
        self.fill_test_table()
        t = self.registry.migration.table('test')
        t.column().add(Column('new_column', Integer, nullable=False,
                       server_default="1"))
        t.column('new_column')

    def test_drop_table(self):
        self.registry.migration.table('test').drop()
        with self.assertRaises(MigrationException):
            self.registry.migration.table('Test')

    def test_drop_column(self):
        t = self.registry.migration.table('test')
        t.column('other').drop()
        with self.assertRaises(MigrationException):
            t.column('other')

    def test_alter_table_name(self):
        t = self.registry.migration.table('test')
        t.alter(name='othername')
        self.registry.migration.table('othername')
        with self.assertRaises(MigrationException):
            self.registry.migration.table('test')

    def test_alter_column_name(self):
        t = self.registry.migration.table('test')
        t.column('other').alter(name='othername')
        t.column('othername')
        with self.assertRaises(MigrationException):
            t.column('other')

    def test_alter_column_nullable(self):
        t = self.registry.migration.table('test')
        c = t.column('other').alter(nullable=False)
        self.assertFalse(c.nullable())

    def test_alter_column_nullable_in_filled_table(self):
        t = self.registry.migration.table('test')
        t.column().add(Column('new_column', Integer))
        self.fill_test_table()
        c = t.column('new_column').alter(nullable=False)
        # the column doesn't change of nullable to not lock the migration
        self.assertTrue(c.nullable())

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
        t = self.registry.migration.table('test')
        t.foreign_key('my_fk').add(
            ['other'], [self.registry.System.Blok.name])
        t.foreign_key('my_fk').drop()

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

    def test_detect_under_noautocommit_flag(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) NOT NULL
                );""")
        self.registry.migration.detect_changed()
        self.registry.migration.withoutautomigration = True
        with self.assertRaises(MigrationException):
            self.registry.migration.detect_changed()

    def test_detect_column_added(self):
        # Remove a column on the table force the detection to found new column
        # which is existing in metadata but not in table
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(integer INT PRIMARY KEY NOT NULL);""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Add test.other"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has("Add test.other"))

    def test_detect_column_removed(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64),
                    other2 CHAR(64)
                );""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Drop Column test.other2"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Drop Column test.other2"))

    def test_detect_not_nullable_column_removed(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64),
                    other2 CHAR(64) NOT NULL
                );""")
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has("Drop Column test.other2"))
        self.assertTrue(report.log_has("Drop Column test.other2 (not null)"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Drop Column test.other2"))
        self.assertFalse(report.log_has("Drop Column test.other2 (not null)"))

    def test_detect_nullable(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) NOT NULL
                );""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Alter test.other"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has("Alter test.other"))

    @skipIf(alembic.__version__ < "0.8.3", "Alembic doesn't implement yet")
    def test_detect_m2m_primary_key(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE reltable")
            conn.execute(
                """CREATE TABLE reltable (
                    idmodel1 INT,
                    idmodel2 INT,
                    FOREIGN KEY (idmodel1) REFERENCES testm2m1 (idmodel1),
                    FOREIGN KEY (idmodel2) REFERENCES testm2m2 (idmodel2)
                );""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Alter reltable.idmodel1"))
        self.assertTrue(report.log_has("Alter reltable.idmodel2"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has("Alter reltable.idmodel1"))
        self.assertFalse(report.log_has("Alter reltable.idmodel2"))

    def test_detect_server_default(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) DEFAULT 9.99
                );""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Alter test.other"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has("Alter test.other"))

    def test_detect_drop_index(self):
        with self.cnx() as conn:
            conn.execute("""CREATE INDEX other_idx ON test (other);""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Drop index other_idx on test"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has("Drop index other_idx on test"))

    def test_detect_type(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other INT
                );""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Alter test.other"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has("Alter test.other"))

    @skipIf(alembic.__version__ < "0.8.3", "Alembic doesn't implement yet")
    def test_detect_primary_key(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT NOT NULL,
                    other CHAR(64) PRIMARY KEY NOT NULL
                );""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Alter test.integer"))
        self.assertTrue(report.log_has("Alter test.other"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has("Alter test.integer"))
        self.assertFalse(report.log_has("Alter test.other"))

    def test_detect_add_foreign_key(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE testfk")
            conn.execute(
                """CREATE TABLE testfk(
                    integer INT PRIMARY KEY NOT NULL,
                    other INT
                );""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has(
            "Add Foreign keys on (testfk.other) => (testfktarget.integer)"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has(
            "Add Foreign keys on (testfk.other) => (testfktarget.integer)"))

    def test_detect_drop_foreign_key(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) references system_blok(name)
                );""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has(
            "Drop Foreign keys on test.other => system_blok.name"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has(
            "Drop Foreign keys on test.other => system_blok.name"))

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
        self.assertTrue(report.log_has(
            "Drop Foreign keys on test.other2 => system_blok.name"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has(
            "Drop Foreign keys on test.other2 => system_blok.name"))

    def test_detect_add_unique_constrainte(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE testunique")
            conn.execute(
                """CREATE TABLE testunique(
                    integer INT  PRIMARY KEY NOT NULL,
                    other CHAR(64)
                );""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has(
            "Add unique constraint on testunique (other)"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has(
            "Add unique constraint on testunique (other)"))

    def test_detect_drop_constraint(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) CONSTRAINT unique_other UNIQUE
                );""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Drop constraint unique_other on test"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(
            report.log_has("Drop constraint unique_other on test"))

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
        with self.assertRaises(InternalError):
            self.registry.migration.rollback_savepoint('test')
