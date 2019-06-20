# This file is a part of the AnyBlok project
#
#    Copyright (C) 2016 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Pierre Verkest <pverkest@anybox.fr>
#    Copyright (C) 2019 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok.testing import sgdb_in
from anyblok.column import Integer as Int, String as Str
from anyblok.migration import MigrationException
from anyblok.relationship import Many2Many
from contextlib import contextmanager
from sqlalchemy import Column, Integer, TEXT, CheckConstraint
from anyblok import Declarations
from sqlalchemy.exc import InternalError, IntegrityError, OperationalError
from anyblok.config import Configuration
from .conftest import init_registry, drop_database, create_database


@pytest.fixture(scope="module")
def clean_db(request):
    def clean():
        url = Configuration.get('get_url')()
        drop_database(url)
        db_template_name = Configuration.get('db_template_name', None)
        create_database(url, template=db_template_name)

    request.addfinalizer(clean)


@contextmanager
def cnx(registry):
    cnx = registry.migration.conn
    try:
        yield cnx
    except Exception:
        cnx.execute("rollback")
        raise


def add_in_registry():
    register = Declarations.register
    Model = Declarations.Model

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

    if not sgdb_in(['MySQL', 'MariaDB']):
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


@pytest.fixture()
def registry(request, clean_db, bloks_loaded):
    registry = init_registry(add_in_registry)

    def rollback():
        for table in ('reltable', 'test', 'test2', 'othername', 'testfk',
                      'testunique', 'reltab', 'testm2m1',
                      'testm2m2', 'testfk2', 'testfktarget',  'testcheck',
                      'testchecklongconstraintname', 'testindex'):
            try:
                registry.migration.table(table).drop()
            except MigrationException:
                pass

        registry.close()

    request.addfinalizer(rollback)
    return registry


class TestMigration:

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Can't create empty table")
    def test_add_table(self, registry):
        registry.migration.table().add('test2')
        registry.migration.table('test2')

    def fill_test_table(self, registry):
        Test = registry.Test
        vals = [{'other': 'test %d' % x} for x in range(10)]
        Test.multi_insert(*vals)

    def test_add_column(self, registry):
        t = registry.migration.table('test')
        t.column().add(Column('new_column', Integer))
        t.column('new_column')

    def test_add_column_in_filled_table(self, registry):
        self.fill_test_table(registry)
        t = registry.migration.table('test')
        t.column().add(Column('new_column', Integer))
        t.column('new_column')

    def test_add_not_null_column(self, registry):
        t = registry.migration.table('test')
        t.column().add(Column('new_column', Integer, nullable=False))
        t.column('new_column')

    def test_add_not_null_column_in_filled_table(self, registry):
        self.fill_test_table(registry)
        t = registry.migration.table('test')
        t.column().add(Column('new_column', Integer, nullable=False))
        t.column('new_column')

    def test_add_column_with_default_value(self, registry):
        t = registry.migration.table('test')
        t.column().add(Column('new_column', Integer, default=100))
        t.column('new_column')

    def test_add_column_with_default_str_value(self, registry):
        t = registry.migration.table('test')
        t.column().add(Column('new_column', Integer, default='100'))
        t.column('new_column')

    def test_add_column_in_filled_table_with_default_value(self, registry):
        self.fill_test_table(registry)
        t = registry.migration.table('test')
        t.column().add(Column('new_column', Integer, default=100))
        t.column('new_column')
        res = [x for x in registry.execute(
            "select count(*) from test where new_column is null")][0][0]
        assert res == 0

    def test_add_not_null_column_in_filled_table_with_default_value(
        self, registry
    ):
        self.fill_test_table(registry)
        t = registry.migration.table('test')
        t.column().add(Column('new_column', Integer, nullable=False,
                       server_default="1"))
        t.column('new_column')

    def test_add_unique_constraint_on_good_table(self, registry):
        self.fill_test_table(registry)
        t = registry.migration.table('test')
        t.unique('unique_constraint').add(t.column('other'))
        registry.Test.insert(other='One entry')
        with pytest.raises(IntegrityError):
            registry.Test.insert(other='One entry')

    def test_add_unique_constraint_on_not_unique_column(self, registry):
        Test = registry.Test
        vals = [{'other': 'test'} for x in range(10)]
        Test.multi_insert(*vals)
        t = registry.migration.table('test')
        t.unique(None).add(t.column('other'))
        registry.Test.insert(other='One entry')
        registry.Test.insert(other='One entry')

    def test_drop_table(self, registry):
        registry.migration.table('test').drop()
        with pytest.raises(MigrationException):
            registry.migration.table('Test')

    def test_drop_column(self, registry):
        t = registry.migration.table('test')
        t.column('other').drop()
        with pytest.raises(MigrationException):
            t.column('other')

    def test_alter_table_name(self, registry):
        t = registry.migration.table('test')
        t.alter(name='othername')
        registry.migration.table('othername')
        with pytest.raises(MigrationException):
            registry.migration.table('test')

    def test_alter_column_name(self, registry):
        t = registry.migration.table('test')
        t.column('other').alter(name='othername')
        t.column('othername')
        with pytest.raises(MigrationException):
            t.column('other')

    def test_alter_column_nullable(self, registry):
        t = registry.migration.table('test')
        c = t.column('other').alter(nullable=False)
        assert not c.nullable

    def test_alter_column_nullable_in_filled_table(self, registry):
        t = registry.migration.table('test')
        t.column().add(Column('new_column', Integer))
        self.fill_test_table(registry)
        c = t.column('new_column').alter(nullable=False)
        # the column doesn't change of nullable to not lock the migration
        assert c.nullable

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for postgres")
    def test_alter_column_default(self, registry):
        t = registry.migration.table('test')
        c = t.column('other').alter(server_default='test')
        assert c.server_default == "'test'::character varying"

    def test_index(self, registry):
        t = registry.migration.table('test')
        t.index().add(t.column('integer'))
        t.index(t.column('integer')).drop()

    def test_alter_column_type(self, registry):
        t = registry.migration.table('test')
        c = t.column('other').alter(type_=TEXT)
        assert isinstance(c.type, TEXT)

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Can't drop primary key issue #92")
    def test_alter_column_primary_key(self, registry):
        t = registry.migration.table('test')
        t.primarykey().drop().add(t.column('other'))

    def test_alter_column_foreign_key(self, registry):
        t = registry.migration.table('test')
        t.foreign_key('my_fk').add(
            ['other'], [registry.System.Blok.name])
        t.foreign_key('my_fk').drop()

    def test_constraint_unique(self, registry):
        t = registry.migration.table('test')
        t.unique(name='test_unique_constraint').add(t.column('other'))
        t.unique(name='test_unique_constraint').drop()

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Can't drop check constraint issue #93")
    def test_constraint_check(self, registry):
        t = registry.migration.table('test')
        Test = registry.Test
        t.check('test').add(Test.other != 'test')
        # particuliar case of check constraint
        t.check('anyblok_ck_test__test').drop()

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_under_noautocommit_flag(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) NOT NULL
                );""")
        registry.migration.detect_changed()
        registry.migration.withoutautomigration = True
        with pytest.raises(MigrationException):
            registry.migration.detect_changed()

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_column_added(self, registry):
        # Remove a column on the table force the detection to found new column
        # which is existing in metadata but not in table
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(integer INT PRIMARY KEY NOT NULL);""")
        report = registry.migration.detect_changed()
        assert report.log_has("Add test.other")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not report.log_has("Add test.other")

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_table_removed(self, registry):
        with cnx(registry) as conn:
            conn.execute(
                """CREATE TABLE test2(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64),
                    other2 CHAR(64)
                );""")

        report = registry.migration.detect_changed()
        assert report.log_has("Drop Table test2")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert report.log_has("Drop Table test2")

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_table_removed_with_reinit_column(self, registry):
        with cnx(registry) as conn:
            conn.execute(
                """CREATE TABLE test2(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64),
                    other2 CHAR(64)
                );""")

        registry.migration.reinit_tables = True
        report = registry.migration.detect_changed()
        assert report.log_has("Drop Table test2")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has("Drop Table test2"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_table_removed_with_reinit_all(self, registry):
        with cnx(registry) as conn:
            conn.execute(
                """CREATE TABLE test2(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64),
                    other2 CHAR(64)
                );""")

        registry.migration.reinit_all = True
        report = registry.migration.detect_changed()
        assert report.log_has("Drop Table test2")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has("Drop Table test2"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_column_removed(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64),
                    other2 CHAR(64)
                );""")
        report = registry.migration.detect_changed()
        assert report.log_has("Drop Column test.other2")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert report.log_has("Drop Column test.other2")

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_column_removed_with_reinit_column(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64),
                    other2 CHAR(64)
                );""")
        registry.migration.reinit_columns = True
        report = registry.migration.detect_changed()
        assert report.log_has("Drop Column test.other2")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has("Drop Column test.other2"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_column_removed_with_reinit_all(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64),
                    other2 CHAR(64)
                );""")
        registry.migration.reinit_all = True
        report = registry.migration.detect_changed()
        assert report.log_has("Drop Column test.other2")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has("Drop Column test.other2"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_not_nullable_column_removed(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64),
                    other2 CHAR(64) NOT NULL
                );""")
        report = registry.migration.detect_changed()
        assert not(report.log_has("Drop Column test.other2"))
        assert report.log_has("Drop Column test.other2 (not null)")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert report.log_has("Drop Column test.other2")
        assert not(report.log_has("Drop Column test.other2 (not null)"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_nullable(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) NOT NULL
                );""")
        report = registry.migration.detect_changed()
        assert report.log_has("Alter test.other")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has("Alter test.other"))

    def test_detect_m2m_primary_key(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE reltable")
            conn.execute(
                """CREATE TABLE reltable (
                    idmodel1 INT,
                    idmodel2 INT,
                    FOREIGN KEY (idmodel1) REFERENCES testm2m1 (idmodel1),
                    FOREIGN KEY (idmodel2) REFERENCES testm2m2 (idmodel2)
                );""")

        with pytest.raises(MigrationException):
            registry.migration.detect_changed()

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_server_default(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) DEFAULT 9.99
                );""")
        report = registry.migration.detect_changed()
        assert report.log_has("Alter test.other")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has("Alter test.other"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_add_index_constrainte(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE testindex")
            conn.execute(
                """CREATE TABLE testindex(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64)
                );""")
        report = registry.migration.detect_changed()
        assert report.log_has("Add index constraint on testindex (other)")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has(
            "Add index constraint on testindex (other)"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_add_column_with_index_constrainte(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE testindex")
            conn.execute(
                """CREATE TABLE testindex(
                    integer INT PRIMARY KEY NOT NULL
                );""")
        report = registry.migration.detect_changed()
        assert report.log_has("Add testindex.other")
        assert report.log_has("Add index constraint on testindex (other)")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has("Add testindex.other"))
        assert not(report.log_has(
            "Add index constraint on testindex (other)"))

    def test_detect_drop_index(self, registry):
        with cnx(registry) as conn:
            conn.execute("""CREATE INDEX other_idx ON test (other);""")
        report = registry.migration.detect_changed()
        assert report.log_has("Drop index other_idx on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert report.log_has("Drop index other_idx on test")

    def test_detect_drop_anyblok_index(self, registry):
        with cnx(registry) as conn:
            conn.execute(
                """CREATE INDEX anyblok_ix_test__other ON test (other);""")
        report = registry.migration.detect_changed()
        assert report.log_has("Drop index anyblok_ix_test__other on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(
            report.log_has("Drop index anyblok_ix_test__other on test"))

    def test_detect_drop_index_with_reinit_indexes(self, registry):
        with cnx(registry) as conn:
            conn.execute("""CREATE INDEX other_idx ON test (other);""")
        registry.migration.reinit_indexes = True
        report = registry.migration.detect_changed()
        assert report.log_has("Drop index other_idx on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has("Drop index other_idx on test"))

    def test_detect_drop_index_with_reinit_all(self, registry):
        with cnx(registry) as conn:
            conn.execute("""CREATE INDEX other_idx ON test (other);""")
        registry.migration.reinit_all = True
        report = registry.migration.detect_changed()
        assert report.log_has("Drop index other_idx on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has("Drop index other_idx on test"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_type(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other INT
                );""")
        report = registry.migration.detect_changed()
        assert report.log_has("Alter test.other")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has("Alter test.other"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_primary_key(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT NOT NULL,
                    other CHAR(64) PRIMARY KEY NOT NULL
                );""")

        with pytest.raises(MigrationException):
            registry.migration.detect_changed()

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_add_foreign_key(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE testfk")
            conn.execute(
                """CREATE TABLE testfk(
                    integer INT PRIMARY KEY NOT NULL,
                    other INT
                );""")
        report = registry.migration.detect_changed()
        assert report.log_has(
            "Add Foreign keys on (testfk.other) => (testfktarget.integer)")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has(
            "Add Foreign keys on (testfk.other) => (testfktarget.integer)"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_foreign_key_options_changed(self, registry):
        with cnx(registry) as conn:
            conn.execute("drop table testfk2")
            conn.execute(
                """create table testfk2(
                    integer INT PRIMARY KEY NOT NULL,
                    other int
                        CONSTRAINT anyblok_fk_testfk2__other
                        references testfktarget(integer)
                );""")
        report = registry.migration.detect_changed()
        assert report.log_has(
            "Drop Foreign keys on testfk2.other => testfktarget.integer")
        assert report.log_has(
            "Add Foreign keys on (testfk2.other) => (testfktarget.integer)")

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_drop_foreign_key(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) references system_blok(name)
                );""")
        report = registry.migration.detect_changed()
        assert report.log_has(
            "Drop Foreign keys on test.other => system_blok.name")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert report.log_has(
            "Drop Foreign keys on test.other => system_blok.name")

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_drop_anyblok_foreign_key(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64)
                        CONSTRAINT anyblok_fk_test__other_on_system_blok__name
                        references system_blok(name)
                );""")
        report = registry.migration.detect_changed()
        assert report.log_has(
            "Drop Foreign keys on test.other => system_blok.name")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has(
            "Drop Foreign keys on test.other => system_blok.name"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_drop_foreign_key_with_reinit_constraint(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) references system_blok(name)
                );""")
        registry.migration.reinit_constraints = True
        report = registry.migration.detect_changed()
        assert report.log_has(
            "Drop Foreign keys on test.other => system_blok.name")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has(
            "Drop Foreign keys on test.other => system_blok.name"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_drop_foreign_key_with_reinit_all(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) references system_blok(name)
                );""")
        registry.migration.reinit_all = True
        report = registry.migration.detect_changed()
        assert report.log_has(
            "Drop Foreign keys on test.other => system_blok.name")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has(
            "Drop Foreign keys on test.other => system_blok.name"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_drop_column_with_foreign_key(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64),
                    other2 CHAR(64)
                    CONSTRAINT anyblok_fk_test__other2_on_system_blok__name
                    references system_blok(name)
                );""")
        report = registry.migration.detect_changed()
        assert report.log_has(
            "Drop Foreign keys on test.other2 => system_blok.name")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has(
            "Drop Foreign keys on test.other2 => system_blok.name"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_add_unique_constrainte(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE testunique")
            conn.execute(
                """CREATE TABLE testunique(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64)
                );""")
        report = registry.migration.detect_changed()
        assert report.log_has("Add unique constraint on testunique (other)")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has(
            "Add unique constraint on testunique (other)"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_add_column_with_unique_constrainte(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE testunique")
            conn.execute(
                """CREATE TABLE testunique(
                    integer INT PRIMARY KEY NOT NULL
                );""")
        report = registry.migration.detect_changed()
        assert report.log_has("Add unique constraint on testunique (other)")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has(
            "Add unique constraint on testunique (other)"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_drop_unique_constraint(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) CONSTRAINT unique_other UNIQUE
                );""")
        report = registry.migration.detect_changed()
        assert report.log_has("Drop constraint unique_other on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert report.log_has("Drop constraint unique_other on test")

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_drop_unique_anyblok_constraint(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) CONSTRAINT anyblok_uq_test__other UNIQUE
                );""")
        report = registry.migration.detect_changed()
        assert report.log_has("Drop constraint anyblok_uq_test__other on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(
            report.log_has("Drop constraint anyblok_uq_test__other on test"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_drop_unique_constraint_with_reinit_constraints(
        self, registry
    ):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) CONSTRAINT unique_other UNIQUE
                );""")

        registry.migration.reinit_constraints = True
        report = registry.migration.detect_changed()
        assert report.log_has("Drop constraint unique_other on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(
            report.log_has("Drop constraint unique_other on test"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_drop_unique_constraint_with_reinit_all(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) CONSTRAINT unique_other UNIQUE
                );""")

        registry.migration.reinit_all = True
        report = registry.migration.detect_changed()
        assert report.log_has("Drop constraint unique_other on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(
            report.log_has("Drop constraint unique_other on test"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="No CheckConstraint works #90")
    def test_no_detect_drop_and_add_check_constraint_with_long_name(
        self, registry
    ):
        report = registry.migration.detect_changed()
        assert not(
            report.log_has(
                "Drop check constraint anyblok_ck_testchecklongconstraintname"
                "__long_long_long_long_lon on testchecklongconstraintname"
            )
        )
        assert not(
            report.log_has(
                "Add check constraint anyblok_ck_testchecklongconstraintname__"
                "long_long_long_long_long_long_long_long_long_long_long_long_"
                "long_long_long_long_long_long_test on "
                "testchecklongconstraintname"
            )
        )

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_add_check_constraint(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE testcheck")
            conn.execute(
                """CREATE TABLE testcheck(
                    integer INT PRIMARY KEY NOT NULL
                );""")
        report = registry.migration.detect_changed()
        assert report.log_has(
            "Add check constraint anyblok_ck_testcheck__test on testcheck")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has(
            "Add check constraint anyblok_ck_testcheck__test on testcheck"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_drop_check_constraint(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) CONSTRAINT ck_other CHECK (other != 'test')
                );""")
        report = registry.migration.detect_changed()
        assert report.log_has("Drop check constraint ck_other on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert report.log_has("Drop check constraint ck_other on test")

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_drop_check_anyblok_constraint(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) CONSTRAINT anyblok_ck__test__check
                        CHECK (other != 'test')
                );""")
        report = registry.migration.detect_changed()
        assert report.log_has(
            "Drop check constraint anyblok_ck__test__check on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has(
            "Drop check constraint anyblok_ck__test__check on test"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_drop_check_constraint_with_reinit_constraint(
        self, registry
    ):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) CONSTRAINT ck_other CHECK (other != 'test')
                );""")
        registry.migration.reinit_constraints = True
        report = registry.migration.detect_changed()
        assert report.log_has("Drop check constraint ck_other on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(
            report.log_has("Drop check constraint ck_other on test"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="Test for Postgres only")
    def test_detect_drop_check_constraint_with_reinit_all(self, registry):
        with cnx(registry) as conn:
            conn.execute("DROP TABLE test")
            conn.execute(
                """CREATE TABLE test(
                    integer INT PRIMARY KEY NOT NULL,
                    other CHAR(64) CONSTRAINT ck_other CHECK (other != 'test')
                );""")
        registry.migration.reinit_all = True
        report = registry.migration.detect_changed()
        assert report.log_has("Drop check constraint ck_other on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(
            report.log_has("Drop check constraint ck_other on test"))

    def test_savepoint(self, registry):
        Test = registry.Test
        self.fill_test_table(registry)
        registry.migration.savepoint('test')
        self.fill_test_table(registry)
        assert Test.query().count() == 20
        registry.migration.rollback_savepoint('test')
        assert Test.query().count() == 10
        registry.migration.release_savepoint('test')

    def test_savepoint_without_rollback(self, registry):
        registry.migration.savepoint('test')
        registry.migration.release_savepoint('test')
        with pytest.raises((InternalError, OperationalError)):
            registry.migration.rollback_savepoint('test')
