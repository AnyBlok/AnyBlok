# This file is a part of the AnyBlok project
#
#    Copyright (C) 2016 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
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
from sqlalchemy import Column, Integer, TEXT, CheckConstraint
from anyblok import Declarations
from sqlalchemy.exc import InternalError, IntegrityError
from copy import deepcopy
from sqlalchemy.orm import clear_mappers


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
        class TestIndex:
            integer = Int(primary_key=True)
            other = Str(index=True)

        @register(Model)
        class TestCheck:
            integer = Int(primary_key=True)

            @classmethod
            def define_table_args(cls):
                table_args = super(TestCheck, cls).define_table_args()
                return table_args + (
                    CheckConstraint('integer > 0', name='test'),)

        @register(Model)
        class TestCheckLongConstraintName:
            integer = Int(primary_key=True)

            @classmethod
            def define_table_args(cls):
                table_args = super(TestCheckLongConstraintName,
                                   cls).define_table_args()
                return table_args + (
                    CheckConstraint('integer > 0', name=(
                        'long_long_long_long_long_long_long_long_long_long_'
                        'long_long_long_long_long_long_long_long_test')),)

        @register(Model)
        class TestFKTarget:
            integer = Int(primary_key=True)

        @register(Model)
        class TestFK:
            integer = Int(primary_key=True)
            other = Int(
                foreign_key=Model.TestFKTarget.use('integer'))

        @register(Model)
        class TestFK2:
            integer = Int(primary_key=True)
            other = Int(
                foreign_key=Model.TestFKTarget.use('integer').options(
                    ondelete='cascade'))

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
        self.registry = Registry(Configuration.get('db_name'), unittest=True)

    @classmethod
    def tearDownClass(cls):
        super(TestMigration, cls).tearDownClass()
        BlokManager.unload()
        RegistryManager.loaded_bloks = cls.loaded_bloks
        cls.dropdb()

    def tearDown(self):
        super(TestMigration, self).tearDown()
        for table in ('test', 'test2', 'othername', 'testfk', 'testfktarget',
                      'testunique', 'reltab', 'testm2m1', 'testm2m2',
                      'testfk2', 'testcheck', 'testchecklongconstraintname',
                      'testindex'):
            try:
                self.registry.migration.table(table).drop()
            except Exception:
                pass

        self.registry.migration.conn.close()
        clear_mappers()
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

    def test_add_unique_constraint_on_good_table(self):
        self.fill_test_table()
        t = self.registry.migration.table('test')
        t.unique('unique_constraint').add(t.column('other'))
        self.registry.Test.insert(other='One entry')
        with self.assertRaises(IntegrityError):
            self.registry.Test.insert(other='One entry')

    def test_add_unique_constraint_on_not_unique_column(self):
        Test = self.registry.Test
        vals = [{'other': 'test'} for x in range(10)]
        Test.multi_insert(*vals)
        t = self.registry.migration.table('test')
        t.unique(None).add(t.column('other'))
        self.registry.Test.insert(other='One entry')
        self.registry.Test.insert(other='One entry')

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
        t.unique(name='test_unique_constraint').add(t.column('other'))
        t.unique(name='test_unique_constraint').drop()

    def test_constraint_check(self):
        t = self.registry.migration.table('test')
        Test = self.registry.Test
        t.check('test').add(Test.other != 'test')
        # particuliar case of check constraint
        t.check('anyblok_ck_test__test').drop()

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

    def test_detect_table_removed(self):
        with self.cnx() as conn:
            conn.execute(
                """CREATE TABLE test2(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64),
                    other2 CHAR(64)
                );""")

        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Drop Table test2"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Drop Table test2"))

    def test_detect_table_removed_with_reinit_column(self):
        with self.cnx() as conn:
            conn.execute(
                """CREATE TABLE test2(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64),
                    other2 CHAR(64)
                );""")

        self.registry.migration.reinit_tables = True
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Drop Table test2"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has("Drop Table test2"))

    def test_detect_table_removed_with_reinit_all(self):
        with self.cnx() as conn:
            conn.execute(
                """CREATE TABLE test2(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64),
                    other2 CHAR(64)
                );""")

        self.registry.migration.reinit_all = True
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Drop Table test2"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has("Drop Table test2"))

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

    def test_detect_column_removed_with_reinit_column(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64),
                    other2 CHAR(64)
                );""")
        self.registry.migration.reinit_columns = True
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Drop Column test.other2"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has("Drop Column test.other2"))

    def test_detect_column_removed_with_reinit_all(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64),
                    other2 CHAR(64)
                );""")
        self.registry.migration.reinit_all = True
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Drop Column test.other2"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has("Drop Column test.other2"))

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

        with self.assertRaises(MigrationException):
            self.registry.migration.detect_changed()

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

    def test_detect_add_index_constrainte(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE testindex")
            conn.execute(
                """CREATE TABLE testindex(
                    integer INT  PRIMARY KEY NOT NULL,
                    other CHAR(64)
                );""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has(
            "Add index constraint on testindex (other)"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has(
            "Add index constraint on testindex (other)"))

    def test_detect_add_column_with_index_constrainte(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE testindex")
            conn.execute(
                """CREATE TABLE testindex(
                    integer INT  PRIMARY KEY NOT NULL
                );""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Add testindex.other"))
        self.assertTrue(report.log_has(
            "Add index constraint on testindex (other)"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has("Add testindex.other"))
        self.assertFalse(report.log_has(
            "Add index constraint on testindex (other)"))

    def test_detect_drop_index(self):
        with self.cnx() as conn:
            conn.execute("""CREATE INDEX other_idx ON test (other);""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Drop index other_idx on test"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Drop index other_idx on test"))

    def test_detect_drop_anyblok_index(self):
        with self.cnx() as conn:
            conn.execute(
                """CREATE INDEX anyblok_ix_test__other ON test (other);""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(
            report.log_has("Drop index anyblok_ix_test__other on test"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(
            report.log_has("Drop index anyblok_ix_test__other on test"))

    def test_detect_drop_index_with_reinit_indexes(self):
        with self.cnx() as conn:
            conn.execute("""CREATE INDEX other_idx ON test (other);""")
        self.registry.migration.reinit_indexes = True
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Drop index other_idx on test"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has("Drop index other_idx on test"))

    def test_detect_drop_index_with_reinit_all(self):
        with self.cnx() as conn:
            conn.execute("""CREATE INDEX other_idx ON test (other);""")
        self.registry.migration.reinit_all = True
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

    def test_detect_primary_key(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT NOT NULL,
                    other CHAR(64) PRIMARY KEY NOT NULL
                );""")

        with self.assertRaises(MigrationException):
            self.registry.migration.detect_changed()

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

    def test_detect_foreign_key_options_changed(self):
        with self.cnx() as conn:
            conn.execute("drop table testfk2")
            conn.execute(
                """create table testfk2(
                    integer int primary key not null,
                    other int
                        CONSTRAINT anyblok_fk_testfk2__other
                        references testfktarget(integer)
                );""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has(
            "Drop Foreign keys on testfk2.other => testfktarget.integer"))
        self.assertTrue(report.log_has(
            "Add Foreign keys on (testfk2.other) => (testfktarget.integer)"))

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
        self.assertTrue(report.log_has(
            "Drop Foreign keys on test.other => system_blok.name"))

    def test_detect_drop_anyblok_foreign_key(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64)
                        CONSTRAINT anyblok_fk_test__other_on_system_blok__name
                        references system_blok(name)
                );""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has(
            "Drop Foreign keys on test.other => system_blok.name"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has(
            "Drop Foreign keys on test.other => system_blok.name"))

    def test_detect_drop_foreign_key_with_reinit_constraint(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) references system_blok(name)
                );""")
        self.registry.migration.reinit_constraints = True
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has(
            "Drop Foreign keys on test.other => system_blok.name"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has(
            "Drop Foreign keys on test.other => system_blok.name"))

    def test_detect_drop_foreign_key_with_reinit_all(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) references system_blok(name)
                );""")
        self.registry.migration.reinit_all = True
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
                    other2 CHAR(64)
                    CONSTRAINT anyblok_fk_test__other2_on_system_blok__name
                    references system_blok(name)
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

    def test_detect_add_column_with_unique_constrainte(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE testunique")
            conn.execute(
                """CREATE TABLE testunique(
                    integer INT  PRIMARY KEY NOT NULL
                );""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has(
            "Add unique constraint on testunique (other)"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has(
            "Add unique constraint on testunique (other)"))

    def test_detect_drop_unique_constraint(self):
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
        self.assertTrue(report.log_has("Drop constraint unique_other on test"))

    def test_detect_drop_unique_anyblok_constraint(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) CONSTRAINT anyblok_uq_test__other UNIQUE
                );""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(
            report.log_has("Drop constraint anyblok_uq_test__other on test"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(
            report.log_has("Drop constraint anyblok_uq_test__other on test"))

    def test_detect_drop_unique_constraint_with_reinit_constraints(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) CONSTRAINT unique_other UNIQUE
                );""")

        self.registry.migration.reinit_constraints = True
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Drop constraint unique_other on test"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(
            report.log_has("Drop constraint unique_other on test"))

    def test_detect_drop_unique_constraint_with_reinit_all(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) CONSTRAINT unique_other UNIQUE
                );""")

        self.registry.migration.reinit_all = True
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has("Drop constraint unique_other on test"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(
            report.log_has("Drop constraint unique_other on test"))

    def test_no_detect_drop_and_add_check_constraint_with_long_name(self):
        report = self.registry.migration.detect_changed()
        self.assertFalse(
            report.log_has(
                "Drop check constraint anyblok_ck_testchecklongconstraintname"
                "__long_long_long_long_lon on testchecklongconstraintname"
            )
        )
        self.assertFalse(
            report.log_has(
                "Add check constraint anyblok_ck_testchecklongconstraintname__"
                "long_long_long_long_long_long_long_long_long_long_long_long_"
                "long_long_long_long_long_long_test on "
                "testchecklongconstraintname"
            )
        )

    def test_detect_add_check_constraint(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE testcheck")
            conn.execute(
                """CREATE TABLE testcheck(
                    integer INT PRIMARY KEY NOT NULL
                );""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has(
            "Add check constraint anyblok_ck_testcheck__test on testcheck"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has(
            "Add check constraint anyblok_ck_testcheck__test on testcheck"))

    def test_detect_drop_check_constraint(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) CONSTRAINT ck_other CHECK (other != 'test')
                );""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(
            report.log_has("Drop check constraint ck_other on test"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertTrue(
            report.log_has("Drop check constraint ck_other on test"))

    def test_detect_drop_check_anyblok_constraint(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) CONSTRAINT anyblok_ck__test__check
                        CHECK (other != 'test')
                );""")
        report = self.registry.migration.detect_changed()
        self.assertTrue(report.log_has(
            "Drop check constraint anyblok_ck__test__check on test"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(report.log_has(
            "Drop check constraint anyblok_ck__test__check on test"))

    def test_detect_drop_check_constraint_with_reinit_constraint(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) CONSTRAINT ck_other CHECK (other != 'test')
                );""")
        self.registry.migration.reinit_constraints = True
        report = self.registry.migration.detect_changed()
        self.assertTrue(
            report.log_has("Drop check constraint ck_other on test"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(
            report.log_has("Drop check constraint ck_other on test"))

    def test_detect_drop_check_constraint_with_reinit_all(self):
        with self.cnx() as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) CONSTRAINT ck_other CHECK (other != 'test')
                );""")
        self.registry.migration.reinit_all = True
        report = self.registry.migration.detect_changed()
        self.assertTrue(
            report.log_has("Drop check constraint ck_other on test"))
        report.apply_change()
        report = self.registry.migration.detect_changed()
        self.assertFalse(
            report.log_has("Drop check constraint ck_other on test"))

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
