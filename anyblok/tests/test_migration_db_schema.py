# This file is a part of the AnyBlok project
#
#    Copyright (C) 2019 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok.testing import sgdb_in
from anyblok.column import Integer as Int, String as Str
from anyblok.migration import MigrationException, DropSchema
from contextlib import contextmanager
from sqlalchemy import (
    MetaData, Table, Column, Integer, String, CheckConstraint, ForeignKey,
    text)
from anyblok import Declarations
from sqlalchemy.exc import IntegrityError
from anyblok.config import Configuration
from .conftest import init_registry, drop_database, create_database
from anyblok.common import naming_convention


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
        __db_schema__ = 'test_db_schema'

        integer = Int(primary_key=True)
        other = Str()

    @register(Model)
    class TestUnique:
        __db_schema__ = 'test_db_schema'

        integer = Int(primary_key=True)
        other = Str(unique=True)

    @register(Model)
    class TestIndex:
        __db_schema__ = 'test_db_schema'

        integer = Int(primary_key=True)
        other = Str(index=True)

    if not sgdb_in(['MySQL', 'MariaDB']):
        @register(Model)
        class TestCheck:
            __db_schema__ = 'test_db_schema'

            integer = Int(primary_key=True)

            @classmethod
            def define_table_args(cls):
                table_args = super(TestCheck, cls).define_table_args()
                return table_args + (
                    CheckConstraint('integer > 0', name='test'),)

    @register(Model)
    class TestFKTarget:
        __db_schema__ = 'test_db_schema'

        integer = Int(primary_key=True)

    @register(Model)
    class TestFK:
        __db_schema__ = 'test_db_schema'

        integer = Int(primary_key=True)
        other = Int(
            foreign_key=Model.TestFKTarget.use('integer'))

    @register(Model)
    class TestFK2:
        __db_schema__ = 'test_db_schema'

        integer = Int(primary_key=True)
        other = Int(
            foreign_key=Model.TestFKTarget.use('integer').options(
                ondelete='cascade'))


@pytest.fixture()
def registry(request, clean_db, bloks_loaded):
    registry = init_registry(add_in_registry)

    def rollback():
        for table in ('test', 'testfk', 'testunique', 'testfk2',
                      'testfktarget', 'testindex', 'testcheck'):
            try:
                registry.migration.table(table, schema='test_db_schema').drop()
            except MigrationException:
                pass

        registry.close()

    request.addfinalizer(rollback)
    return registry


class TestMigrationDbSchema:

    def test_add_schema(self, registry):
        registry.migration.schema().add('other_schema')
        registry.migration.schema('other_schema')
        registry.migration.schema('other_schema').drop()

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB', 'MsSQL']),
                        reason="Can't create empty table")
    def test_add_table_from_schema(self, registry):
        schema = registry.migration.schema('test_db_schema')
        schema.table().add('test2')
        table = schema.table('test2')
        assert table.schema == 'test_db_schema'

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB', 'MsSQL']),
                        reason="Can't create empty table")
    def test_add_table(self, registry):
        registry.migration.table(schema='test_db_schema').add('test2')
        table = registry.migration.table('test2', schema='test_db_schema')
        assert table.schema == 'test_db_schema'

    def test_add_column(self, registry):
        t = registry.migration.table('test', schema='test_db_schema')
        t.column().add(Column('new_column', Integer))
        t.column('new_column')

    def test_add_unique_constraint(self, registry):
        t = registry.migration.table('test', schema='test_db_schema')
        t.unique('unique_constraint').add(t.column('other'))
        registry.Test.insert(other='One entry')
        with pytest.raises(IntegrityError):
            registry.Test.insert(other='One entry')

    def test_drop_schema(self, registry):
        schema = registry.migration.schema('test_db_schema')
        schema.table('test').drop()
        schema.table('testfk').drop()
        schema.table('testunique').drop()
        schema.table('testfk2').drop()
        schema.table('testfktarget').drop()
        schema.table('testindex').drop()
        if not sgdb_in(['MySQL', 'MariaDB']):
            schema.table('testcheck').drop()

        schema.drop()
        with pytest.raises(MigrationException):
            registry.migration.schema('test_db_schema')

        # MySQL waiting that this schema exist for the next test
        registry.migration.schema().add('test_db_schema')

    def test_drop_table(self, registry):
        registry.migration.table('test', schema='test_db_schema').drop()
        with pytest.raises(MigrationException):
            registry.migration.table('Test', schema='test_db_schema')

    def test_drop_column(self, registry):
        t = registry.migration.table('test', schema='test_db_schema')
        t.column('other').drop()
        with pytest.raises(MigrationException):
            t.column('other')

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB', 'MsSQL']),
                        reason="Can't rename schema #122")
    def test_alter_schema_name(self, registry):
        registry.migration.schema('test_db_schema').alter(name='test_db_other')
        with pytest.raises(MigrationException):
            registry.migration.schema('test_db_schema')

        registry.migration.schema('test_db_other')
        registry.migration.schema('test_db_other').table('test')

    def test_alter_table_name(self, registry):
        t = registry.migration.table('test', schema='test_db_schema')
        t.alter(name='othername')
        registry.migration.table('othername', schema='test_db_schema')
        with pytest.raises(MigrationException):
            registry.migration.table('test')

    def test_alter_column_name(self, registry):
        t = registry.migration.table('test', schema='test_db_schema')
        t.column('other').alter(name='othername')
        t.column('othername')
        with pytest.raises(MigrationException):
            t.column('other')

    def test_index(self, registry):
        t = registry.migration.table('test', schema='test_db_schema')
        t.index().add(t.column('integer'))
        t.index(t.column('integer')).drop()

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="FIXME: can't create foreign key")
    def test_alter_column_foreign_key(self, registry):
        t = registry.migration.table('test', schema='test_db_schema')
        t.foreign_key('my_fk').add(
            ['other'], [registry.System.Blok.name])
        t.foreign_key('my_fk').drop()

    def test_constraint_unique(self, registry):
        t = registry.migration.table('test', schema='test_db_schema')
        t.unique(name='test_unique_constraint').add(t.column('other'))
        t.unique(name='test_unique_constraint').drop()

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB', 'MsSQL']),
                        reason="Can't drop check constraint issue #93")
    def test_constraint_check(self, registry):
        t = registry.migration.table('test', schema='test_db_schema')
        Test = registry.Test
        t.check('test').add(Test.other != 'test')
        # particuliar case of check constraint
        t.check('anyblok_ck_test__test').drop()

    def test_detect_schema_added(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.TestFK.__table__.drop(bind=conn)
            registry.TestUnique.__table__.drop(bind=conn)
            registry.TestFK2.__table__.drop(bind=conn)
            registry.TestFKTarget.__table__.drop(bind=conn)
            registry.TestIndex.__table__.drop(bind=conn)
            if not sgdb_in(['MySQL', 'MariaDB']):
                registry.TestCheck.__table__.drop(bind=conn)

            conn.execute(DropSchema('test_db_schema'))

        report = registry.migration.detect_changed(schema_only=True)
        assert report.log_has("Add schema test_db_schema")
        report.apply_change()
        report = registry.migration.detect_changed(schema_only=True)
        assert not report.log_has("Add schema test_db_schema")

    def test_detect_table_added(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has("Add table test_db_schema.test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not report.log_has("Add table test_db_schema.test")

    def test_detect_column_added(self, registry):
        # Remove a column on the table force the detection to found new column
        # which is existing in metadata but not in table
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                schema='test_db_schema'
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
                schema='test_db_schema'
            ).create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has("Drop Table test_db_schema.test2")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert report.log_has("Drop Table test_db_schema.test2")

    def test_detect_column_removed(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64)),
                Column('other2', String(64)),
                schema='test_db_schema'
            )
            registry.Test.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has("Drop Column test.other2")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert report.log_has("Drop Column test.other2")

    def test_detect_nullable(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64), nullable=False),
                schema='test_db_schema'
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
                schema='test_db_schema'
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
                schema='test_db_schema'
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

    def test_detect_drop_anyblok_index(self, registry):
        with cnx(registry) as conn:
            conn.execute(text(
                """CREATE INDEX anyblok_ix_test__other
                   ON test_db_schema.test (other);"""))
        report = registry.migration.detect_changed()
        assert report.log_has(
            "Drop index anyblok_ix_test__other on test_db_schema.test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(
            report.log_has(
                "Drop index anyblok_ix_test__other on test_db_schema.test"))

    def test_detect_type(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', Integer),
                schema='test_db_schema'
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
                schema='test_db_schema'
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
                schema='test_db_schema'
            )
            registry.TestFK.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has(
            "Add Foreign keys on (testfk.other) => "
            "(test_db_schema.testfktarget.integer)")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not report.log_has(
            "Add Foreign keys on (testfk.other) => "
            "(test_db_schema.testfktarget.integer)")

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
                schema='test_db_schema'
            )
            registry.TestFK2.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has(
            "Drop Foreign keys on testfk2.other => "
            "test_db_schema.testfktarget.integer")
        assert report.log_has(
            "Add Foreign keys on (testfk2.other) => "
            "(test_db_schema.testfktarget.integer)")

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="FIXME: can't create foreign key")
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
                schema='test_db_schema'
            )
            registry.Test.__table__.create(bind=conn)
            # anyblok_fk_test__other_on_system_blok__name

        report = registry.migration.detect_changed()

        message = (
            "Drop Foreign keys on test.other => %ssystem_blok.name"
        ) % ('dbo.' if sgdb_in(['MsSQL']) else '')
        assert report.log_has(message)
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not report.log_has(message)

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                        reason="FIXME: can't create foreign key")
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
                schema='test_db_schema'
            )
            registry.Test.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        message = (
            "Drop Foreign keys on test.other2 => %ssystem_blok.name"
        ) % ('dbo.' if sgdb_in(['MsSQL']) else '')
        assert report.log_has(message)
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not report.log_has(message)

    @pytest.mark.skipif(sgdb_in(['MsSQL']),
                        reason="MsSQL does not add unique #121")
    def test_detect_add_unique_constraint(self, registry):
        with cnx(registry) as conn:
            registry.TestUnique.__table__.drop(bind=conn)
            registry.TestUnique.__table__ = Table(
                'testunique', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64)),
                schema='test_db_schema'
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
                schema='test_db_schema'
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
    def test_detect_drop_unique_anyblok_constraint(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(naming_convention=naming_convention),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64), unique=True),
                schema='test_db_schema'
            )
            registry.Test.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has(
            "Drop constraint anyblok_uq_test__other on test_db_schema.test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not report.log_has(
            "Drop constraint anyblok_uq_test__other on test_db_schema.test")

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB', 'MsSQL']),
                        reason="No CheckConstraint works #90")
    def test_detect_add_check_constraint(self, registry):
        with cnx(registry) as conn:
            registry.TestCheck.__table__.drop(bind=conn)
            registry.TestCheck.__table__ = Table(
                'testcheck', MetaData(naming_convention=naming_convention),
                Column('integer', Integer, primary_key=True),
                schema='test_db_schema'
            )
            registry.TestCheck.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has(
            "Add check constraint anyblok_ck_testcheck__test "
            "on test_db_schema.testcheck")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not report.log_has(
            "Add check constraint anyblok_ck_testcheck__test "
            "on test_db_schema.testcheck")

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB', 'MsSQL']),
                        reason="No CheckConstraint works #90")
    def test_detect_drop_check_anyblok_constraint(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(naming_convention=naming_convention),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64),
                       CheckConstraint("other != 'test'", name='check')),
                schema='test_db_schema'
            )
            registry.Test.__table__.create(bind=conn)

        report = registry.migration.detect_changed()
        assert report.log_has(
            "Drop check constraint anyblok_ck_test__check "
            "on test_db_schema.test")
        report.apply_change()
        report = registry.migration.detect_changed()
        assert not(report.log_has(
            "Drop check constraint anyblok_ck_test__check "
            "on test_db_schema.test"))
