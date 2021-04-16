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
from anyblok.migration import (
    MigrationException, MigrationColumnTypePlugin, MigrationReport)
from anyblok.relationship import Many2Many
from contextlib import contextmanager
from sqlalchemy import (
    MetaData, Table, Column, Integer, String, Boolean, TEXT,
    CheckConstraint, ForeignKey, text
)
from sqlalchemy.dialects.mysql.types import TINYINT, DATETIME
from sqlalchemy.dialects.mssql.base import BIT
from anyblok import Declarations
from sqlalchemy.exc import IntegrityError
from anyblok.config import Configuration
from .conftest import init_registry, drop_database, create_database
from anyblok.common import naming_convention
from mock import patch


@pytest.fixture(scope="module")
def clean_db(request, configuration_loaded):

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
        cnx.execute(text("rollback"))
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

    if not sgdb_in(['MySQL', 'MariaDB', 'MsSQL']):
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


class MockMigrationColumnTypePluginInteger2String(MigrationColumnTypePlugin):

    to_type = String
    from_type = Integer
    dialect = None


class MockMigrationColumnTypePluginInteger2StringMySQL(
    MigrationColumnTypePlugin
):

    to_type = String
    from_type = Integer
    dialect = ['MySQL']


class TestMigration:

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB', 'MsSQL']),
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

    @pytest.mark.skipif(sgdb_in(['MsSQL']),
                        reason="Not rollback to savepoint")
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

    @pytest.mark.skipif(sgdb_in(['MsSQL']),
                        reason="Can't change server default")
    def test_add_not_null_column_in_filled_table_with_default_value(
        self, registry
    ):
        self.fill_test_table(registry)
        t = registry.migration.table('test')
        t.column().add(Column('new_column', Integer, nullable=False,
                       server_default="1"))
        t.column('new_column')

    @pytest.mark.skipif(sgdb_in(['MsSQL']),
                        reason="Not rollback to savepoint")
    def test_add_unique_constraint_on_good_table(self, registry):
        self.fill_test_table(registry)
        t = registry.migration.table('test')
        t.unique('unique_constraint').add(t.column('other'))
        registry.Test.insert(other='One entry')
        with pytest.raises(IntegrityError):
            registry.Test.insert(other='One entry')

    @pytest.mark.skipif(sgdb_in(['MsSQL']), reason="#121")
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

    @pytest.mark.skipif(sgdb_in(['MsSQL']),
                        reason="Not rollback to savepoint")
    def test_alter_column_nullable_in_filled_table(self, registry):
        t = registry.migration.table('test')
        t.column().add(Column('new_column', Integer))
        self.fill_test_table(registry)
        c = t.column('new_column').alter(nullable=False)
        # the column doesn't change of nullable to not lock the migration
        assert c.nullable

    @pytest.mark.skipif(sgdb_in(['MsSQL']),
                        reason="Can't change server default")
    def test_alter_column_default(self, registry):
        t = registry.migration.table('test')
        c = t.column('other').alter(server_default='test')
        if sgdb_in(['PostgreSQL']):
            assert c.server_default == "'test'::character varying"
        else:
            assert str(c.server_default) == "'test'"

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

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB', 'MsSQL']),
                        reason="Can't drop check constraint issue #93")
    def test_constraint_check(self, registry):
        t = registry.migration.table('test')
        Test = registry.Test
        t.check('test').add(Test.other != 'test')
        # particuliar case of check constraint
        t.check('anyblok_ck_test__test').drop()

    def test_detect_under_noautocommit_flag(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64), nullable=False),
            )
            registry.Test.__table__.create(bind=conn)

        registry.migration.detect_changed()
        registry.migration.withoutautomigration = True
        with pytest.raises(MigrationException):
            registry.migration.detect_changed()

    def test_detect_column_added(self, registry):
        # Remove a column on the table force the detection to found new column
        # which is existing in metadata but not in table
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True)
            )
            registry.Test.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has("Add test.other")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not report.log_has("Add test.other")

    def test_detect_table_removed(self, registry):
        with cnx(registry) as conn:
            Table(
                'test2', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64)),
                Column('other2', String(64)),
            ).create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has("Drop Table test2")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert report.log_has("Drop Table test2")

    def test_detect_table_removed_with_reinit_column(self, registry):
        with cnx(registry) as conn:
            Table(
                'test2', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64)),
                Column('other2', String(64)),
            ).create(bind=conn)

        registry.migration.reinit_tables = True
        report = registry.migration.detect_changed()
        assert report.log_has("Drop Table test2")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has("Drop Table test2"))

    def test_detect_table_removed_with_reinit_all(self, registry):
        with cnx(registry) as conn:
            Table(
                'test2', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64)),
                Column('other2', String(64)),
            ).create(bind=conn)

        registry.migration.reinit_all = True
        report = registry.migration.detect_changed()
        assert report.log_has("Drop Table test2")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has("Drop Table test2"))

    def test_detect_column_removed(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64)),
                Column('other2', String(64)),
            )
            registry.Test.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has("Drop Column test.other2")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert report.log_has("Drop Column test.other2")

    def test_detect_column_removed_with_reinit_column(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64)),
                Column('other2', String(64)),
            )
            registry.Test.__table__.create(bind=conn)

        registry.migration.reinit_columns = True
        report = registry.migration.detect_changed()
        assert report.log_has("Drop Column test.other2")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has("Drop Column test.other2"))

    def test_detect_column_removed_with_reinit_all(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64)),
                Column('other2', String(64)),
            )
            registry.Test.__table__.create(bind=conn)

        registry.migration.reinit_all = True
        report = registry.migration.detect_changed()
        assert report.log_has("Drop Column test.other2")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has("Drop Column test.other2"))

    def test_detect_not_nullable_column_removed(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64)),
                Column('other2', String(64), nullable=False),
            )
            registry.Test.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert not(report.log_has("Drop Column test.other2"))
        assert report.log_has("Drop Column test.other2 (not null)")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert report.log_has("Drop Column test.other2")
        assert not(report.log_has("Drop Column test.other2 (not null)"))

    def test_detect_nullable(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64), nullable=False),
            )
            registry.Test.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has("Alter test.other")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has("Alter test.other"))

    def test_detect_m2m_primary_key(self, registry):
        with cnx(registry) as conn:
            Table('reltable', registry.declarativebase.metadata,
                  autoload_with=conn).drop(bind=conn)

            meta = MetaData()
            meta._add_table('testm2m1', None, registry.TestM2M1.__table__)
            meta._add_table('testm2m2', None, registry.TestM2M2.__table__)

            Table(
                'reltable', meta,
                Column('idmodel1', Integer, ForeignKey('testm2m1.idmodel1')),
                Column('idmodel2', Integer, ForeignKey('testm2m2.idmodel2')),
            ).create(bind=conn)

        with pytest.raises(MigrationException):
            registry.migration.detect_changed()

    def test_detect_server_default(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64), server_default='9.99'),
            )
            registry.Test.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has("Alter test.other")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has("Alter test.other"))

    def test_detect_add_index_constraint(self, registry):
        with cnx(registry) as conn:
            registry.TestIndex.__table__.drop(bind=conn)
            registry.TestIndex.__table__ = Table(
                'testindex', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64)),
            )
            registry.TestIndex.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has("Add index constraint on testindex (other)")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has(
            "Add index constraint on testindex (other)"))

    def test_detect_add_column_with_index_constraint(self, registry):
        with cnx(registry) as conn:
            registry.TestIndex.__table__.drop(bind=conn)
            registry.TestIndex.__table__ = Table(
                'testindex', MetaData(),
                Column('integer', Integer, primary_key=True),
            )
            registry.TestIndex.__table__.create(bind=conn)

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
            conn.execute(text("CREATE INDEX other_idx ON test (other);"))
        report = registry.migration.detect_changed()
        assert report.log_has("Drop index other_idx on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert report.log_has("Drop index other_idx on test")

    def test_detect_drop_anyblok_index(self, registry):
        with cnx(registry) as conn:
            conn.execute(
                text("CREATE INDEX anyblok_ix_test__other ON test (other);"))
        report = registry.migration.detect_changed()
        assert report.log_has("Drop index anyblok_ix_test__other on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(
            report.log_has("Drop index anyblok_ix_test__other on test"))

    def test_detect_drop_index_with_reinit_indexes(self, registry):
        with cnx(registry) as conn:
            conn.execute(text("CREATE INDEX other_idx ON test (other);"))
        registry.migration.reinit_indexes = True
        report = registry.migration.detect_changed()
        assert report.log_has("Drop index other_idx on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has("Drop index other_idx on test"))

    def test_detect_drop_index_with_reinit_all(self, registry):
        with cnx(registry) as conn:
            conn.execute(text("CREATE INDEX other_idx ON test (other);"))
        registry.migration.reinit_all = True
        report = registry.migration.detect_changed()
        assert report.log_has("Drop index other_idx on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has("Drop index other_idx on test"))

    def test_detect_type(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', Integer),
            )
            registry.Test.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has("Alter test.other")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has("Alter test.other"))

    def test_detect_primary_key(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, nullable=False),
                Column('other', String(64), primary_key=True),
            )
            registry.Test.__table__.create(bind=conn)

        with pytest.raises(MigrationException):
            registry.migration.detect_changed()

    def test_detect_add_foreign_key(self, registry):
        with cnx(registry) as conn:
            registry.TestFK.__table__.drop(bind=conn)
            registry.TestFK.__table__ = Table(
                'testfk', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', Integer),
            )
            registry.TestFK.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has(
            "Add Foreign keys on (testfk.other) => (testfktarget.integer)")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has(
            "Add Foreign keys on (testfk.other) => (testfktarget.integer)"))

    @pytest.mark.skipif(sgdb_in(['MsSQL']),
                        reason="MsSQL does not change fk")
    def test_detect_foreign_key_options_changed(self, registry):
        with cnx(registry) as conn:
            registry.TestFK2.__table__.drop(bind=conn)
            meta = MetaData()
            meta._add_table(
                'testfktarget', None, registry.TestFKTarget.__table__)
            registry.TestFK2.__table__ = Table(
                'testfk2', meta,
                Column('integer', Integer, primary_key=True),
                Column('other', Integer, ForeignKey('testfktarget.integer')),
            )
            registry.TestFK2.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has(
            "Drop Foreign keys on testfk2.other => testfktarget.integer")
        assert report.log_has(
            "Add Foreign keys on (testfk2.other) => (testfktarget.integer)")

    def test_detect_drop_foreign_key(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            meta = MetaData()
            meta._add_table(
                'system_blok', None, registry.System.Blok.__table__)
            registry.Test.__table__ = Table(
                'test', meta,
                Column('integer', Integer, primary_key=True),
                Column('other', String(64), ForeignKey('system_blok.name')),
            )
            registry.Test.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has(
            "Drop Foreign keys on test.other => system_blok.name")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert report.log_has(
            "Drop Foreign keys on test.other => system_blok.name")

    def test_detect_drop_anyblok_foreign_key(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            meta = MetaData(naming_convention=naming_convention)
            meta._add_table(
                'system_blok', None, registry.System.Blok.__table__)
            registry.Test.__table__ = Table(
                'test', meta,
                Column('integer', Integer, primary_key=True),
                Column('other', String(64), ForeignKey('system_blok.name')),
            )
            registry.Test.__table__.create(bind=conn)
            # anyblok_fk_test__other_on_system_blok__name

        report = registry.migration.detect_changed()
        assert report.log_has(
            "Drop Foreign keys on test.other => system_blok.name")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has(
            "Drop Foreign keys on test.other => system_blok.name"))

    def test_detect_drop_foreign_key_with_reinit_constraint(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            meta = MetaData()
            meta._add_table(
                'system_blok', None, registry.System.Blok.__table__)
            registry.Test.__table__ = Table(
                'test', meta,
                Column('integer', Integer, primary_key=True),
                Column('other', String(64), ForeignKey('system_blok.name')),
            )
            registry.Test.__table__.create(bind=conn)

        registry.migration.reinit_constraints = True
        report = registry.migration.detect_changed()
        assert report.log_has(
            "Drop Foreign keys on test.other => system_blok.name")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has(
            "Drop Foreign keys on test.other => system_blok.name"))

    def test_detect_drop_foreign_key_with_reinit_all(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            meta = MetaData()
            meta._add_table(
                'system_blok', None, registry.System.Blok.__table__)
            registry.Test.__table__ = Table(
                'test', meta,
                Column('integer', Integer, primary_key=True),
                Column('other', String(64), ForeignKey('system_blok.name')),
            )
            registry.Test.__table__.create(bind=conn)

        registry.migration.reinit_all = True
        report = registry.migration.detect_changed()
        assert report.log_has(
            "Drop Foreign keys on test.other => system_blok.name")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has(
            "Drop Foreign keys on test.other => system_blok.name"))

    def test_detect_drop_column_with_foreign_key(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            meta = MetaData(naming_convention=naming_convention)
            meta._add_table(
                'system_blok', None, registry.System.Blok.__table__)
            registry.Test.__table__ = Table(
                'test', meta,
                Column('integer', Integer, primary_key=True),
                Column('other', String(64)),
                Column('other2', String(64), ForeignKey('system_blok.name')),
            )
            registry.Test.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has(
            "Drop Foreign keys on test.other2 => system_blok.name")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has(
            "Drop Foreign keys on test.other2 => system_blok.name"))

    @pytest.mark.skipif(sgdb_in(['MsSQL']),
                        reason="MsSQL does not add unique #121")
    def test_detect_add_unique_constraint(self, registry):
        with cnx(registry) as conn:
            registry.TestUnique.__table__.drop(bind=conn)
            registry.TestUnique.__table__ = Table(
                'testunique', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64)),
            )
            registry.TestUnique.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has("Add unique constraint on testunique (other)")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has(
            "Add unique constraint on testunique (other)"))

    @pytest.mark.skipif(sgdb_in(['MsSQL']),
                        reason="MsSQL does not add unique #121")
    def test_detect_add_column_with_unique_constraint(self, registry):
        with cnx(registry) as conn:
            registry.TestUnique.__table__.drop(bind=conn)
            registry.TestUnique.__table__ = Table(
                'testunique', MetaData(),
                Column('integer', Integer, primary_key=True),
            )
            registry.TestUnique.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has("Add unique constraint on testunique (other)")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has(
            "Add unique constraint on testunique (other)"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="MySQL transform unique constraint on index")
    @pytest.mark.skipif(sgdb_in(['MsSQL']),
                        reason="MsSQL does not drop unique #121")
    def test_detect_drop_unique_constraint(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64), unique=True),
            )
            registry.Test.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has("Drop constraint test_other_key on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert report.log_has("Drop constraint test_other_key on test")

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="MySQL transform unique constraint on index")
    @pytest.mark.skipif(sgdb_in(['MsSQL']),
                        reason="MsSQL does not drop unique #121")
    def test_detect_drop_unique_anyblok_constraint(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(naming_convention=naming_convention),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64), unique=True),
            )
            registry.Test.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has("Drop constraint anyblok_uq_test__other on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(
            report.log_has("Drop constraint anyblok_uq_test__other on test"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="MySQL transform unique constraint on index")
    @pytest.mark.skipif(sgdb_in(['MsSQL']),
                        reason="MsSQL does not drop unique #121")
    def test_detect_drop_unique_constraint_with_reinit_constraints(
        self, registry
    ):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64), unique=True),
            )
            registry.Test.__table__.create(bind=conn)

        registry.migration.reinit_constraints = True
        report = registry.migration.detect_changed()
        assert report.log_has("Drop constraint test_other_key on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(
            report.log_has("Drop constraint test_other_key on test"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="MySQL transform unique constraint on index")
    @pytest.mark.skipif(sgdb_in(['MsSQL']),
                        reason="MsSQL does not drop unique #121")
    def test_detect_drop_unique_constraint_with_reinit_all(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64), unique=True),
            )
            registry.Test.__table__.create(bind=conn)

        registry.migration.reinit_all = True
        report = registry.migration.detect_changed()
        assert report.log_has("Drop constraint test_other_key on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(
            report.log_has("Drop constraint test_other_key on test"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB', 'MsSQL']),
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

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB', 'MsSQL']),
                        reason="No CheckConstraint works #90")
    def test_detect_add_check_constraint(self, registry):
        with cnx(registry) as conn:
            registry.TestCheck.__table__.drop(bind=conn)
            registry.TestCheck.__table__ = Table(
                'testcheck', MetaData(naming_convention=naming_convention),
                Column('integer', Integer, primary_key=True),
            )
            registry.TestCheck.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has(
            "Add check constraint anyblok_ck_testcheck__test on testcheck")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has(
            "Add check constraint anyblok_ck_testcheck__test on testcheck"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB', 'MsSQL']),
                        reason="No CheckConstraint works #90")
    def test_detect_drop_check_constraint(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64)),
                CheckConstraint("other != 'test'", name='ck_other')
            )
            registry.Test.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has("Drop check constraint ck_other on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert report.log_has("Drop check constraint ck_other on test")

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB', 'MsSQL']),
                        reason="No CheckConstraint works #90")
    def test_detect_drop_check_anyblok_constraint(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(naming_convention=naming_convention),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64)),
                CheckConstraint("other != 'test'", name='check')
            )
            registry.Test.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has(
            "Drop check constraint anyblok_ck_test__check on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has(
            "Drop check constraint anyblok_ck_test__check on test"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB', 'MsSQL']),
                        reason="No CheckConstraint works #90")
    def test_detect_drop_check_constraint_with_reinit_constraint(
        self, registry
    ):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64)),
                CheckConstraint("other != 'test'", name='ck_other')
            )
            registry.Test.__table__.create(bind=conn)

        registry.migration.reinit_constraints = True
        report = registry.migration.detect_changed()
        assert report.log_has("Drop check constraint ck_other on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(
            report.log_has("Drop check constraint ck_other on test"))

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB', 'MsSQL']),
                        reason="No CheckConstraint works #90")
    def test_detect_drop_check_constraint_with_reinit_all(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64)),
                CheckConstraint("other != 'test'", name='ck_other')
            )
            registry.Test.__table__.create(bind=conn)

        registry.migration.reinit_all = True
        report = registry.migration.detect_changed()
        assert report.log_has("Drop check constraint ck_other on test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(
            report.log_has("Drop check constraint ck_other on test"))

    @pytest.mark.skipif(
        sgdb_in(['MySQL', 'MariaDB']),
        reason=(
            "Modification of schema create an implicite commit "
            "with MySQL and MariaDB, save point is by passed for them"
        )
    )
    def test_savepoint(self, registry):
        Test = registry.Test
        self.fill_test_table(registry)
        registry.migration.savepoint('test')
        self.fill_test_table(registry)
        assert Test.query().count() == 20
        registry.migration.rollback_savepoint('test')
        assert Test.query().count() == 10
        registry.migration.release_savepoint('test')


@pytest.fixture()
def registry_plugin(request, clean_db, bloks_loaded):
    registry = init_registry(add_in_registry)
    request.addfinalizer(registry.close)
    return registry


class TestMigrationPlugin:

    @pytest.mark.skipif(
        not sgdb_in(['MySQL', 'MariaDB']),
        reason='Plugin for MySQL only')
    def test_boolean_with_mysql(self, registry_plugin):
        report = MigrationReport(registry_plugin.migration, [])
        res = report.init_modify_type(
            [None, None, 'test', 'other', {}, TINYINT(), Boolean()])
        assert res is True

    @pytest.mark.skipif(
        not sgdb_in(['MySQL', 'MariaDB']),
        reason='Plugin for MySQL only')
    def test_datetime_with_mysql(self, registry_plugin):
        report = MigrationReport(registry_plugin.migration, [])
        res = report.init_modify_type(
            [None, None, 'test', 'other', {}, DATETIME(), DATETIME()])
        assert res is True

    @pytest.mark.skipif(
        not sgdb_in(['MsSQL']),
        reason='Plugin for MsSQL only')
    def test_boolean_with_mssql(self, registry_plugin):
        report = MigrationReport(registry_plugin.migration, [])
        res = report.init_modify_type(
            [None, None, 'test', 'other', {}, BIT(), Boolean()])
        assert res is True

    @pytest.mark.skipif(
        not sgdb_in(['PostgreSQL']),
        reason='Plugin for MsSQL only')
    def test_boolean_with_postgres(self, registry_plugin):
        report = MigrationReport(registry_plugin.migration, [])
        res = report.init_modify_type(
            [None, None, 'test', 'other', {}, Integer(), Boolean()])
        assert res is False

    def test_alter_column_type_with_plugin_1(self, registry_plugin):
        report = MigrationReport(registry_plugin.migration, [])
        report.plugins = [
            MockMigrationColumnTypePluginInteger2String,
        ]
        with patch(
            'anyblok.tests.test_migration.'
            'MockMigrationColumnTypePluginInteger2String.apply'
        ) as mockapply:
            report.apply_change_modify_type(
                [None, None, 'test', 'other', {}, Integer(), String()])
            mockapply.assert_called()

    def test_alter_column_type_with_plugin_2(self, registry_plugin):
        report = MigrationReport(registry_plugin.migration, [])
        report.plugins = [
            MockMigrationColumnTypePluginInteger2String,
        ]
        with patch(
            'anyblok.migration.MigrationColumn.alter'
        ) as mockapply:
            report.apply_change_modify_type(
                [None, None, 'test', 'other', {}, String(), Integer()])
            mockapply.assert_called()

    @pytest.mark.skipif(
        not sgdb_in(['MySQL', 'MariaDB']),
        reason='Plugin for MySQL only')
    def test_alter_column_type_with_plugin_3(self, registry_plugin):
        report = MigrationReport(registry_plugin.migration, [])
        report.plugins = [
            MockMigrationColumnTypePluginInteger2StringMySQL,
        ]
        with patch(
            'anyblok.tests.test_migration.'
            'MockMigrationColumnTypePluginInteger2StringMySQL.apply'
        ) as mockapply:
            report.apply_change_modify_type(
                [None, None, 'test', 'other', {}, Integer(), String()])
            mockapply.assert_called()

    @pytest.mark.skipif(
        sgdb_in(['MySQL', 'MariaDB']),
        reason='Plugin for MySQL only')
    def test_alter_column_type_with_plugin_4(self, registry_plugin):
        report = MigrationReport(registry_plugin.migration, [])
        report.plugins = [
            MockMigrationColumnTypePluginInteger2StringMySQL,
        ]
        with patch(
            'anyblok.migration.MigrationColumn.alter'
        ) as mockapply:
            report.apply_change_modify_type(
                [None, None, 'test', 'other', {}, Integer(), String()])
            mockapply.assert_called()
