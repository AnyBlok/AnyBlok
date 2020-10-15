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
from contextlib import contextmanager
from sqlalchemy import (
    MetaData, Table, Column, Integer, String, CheckConstraint, ForeignKey)
from anyblok import Declarations
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

    if sgdb_in(['MySQL', 'MariaDB']):
        clean()

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
    class TestFKTarget:
        integer = Int(primary_key=True)

    @register(Model)
    class TestFK:
        integer = Int(primary_key=True)
        other = Int(
            foreign_key=Model.TestFKTarget.use('integer'))


@pytest.fixture()
def registry(request, clean_db, bloks_loaded):
    registry = init_registry(add_in_registry)

    def rollback():
        for table in ('reltable', 'test', 'test2', 'othername', 'testfk',
                      'testunique', 'reltab',
                      'testfktarget',  'testcheck', 'testindex'):
            try:
                registry.migration.table(table).drop()
            except MigrationException:
                pass

        registry.close()

    request.addfinalizer(rollback)
    return registry


class TestMigration:

    def test_detect_column_added_with_protected_table(self, registry):
        # Remove a column on the table force the detection to found new column
        # which is existing in metadata but not in table
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True)
            )
            registry.Test.__table__.create(bind=conn)

        registry.migration.ignore_migration_for = {'test': True}
        report = registry.migration.detect_changed()
        assert not report.log_has("Add test.other")

    def test_detect_column_added_with_protected_column(self, registry):
        # Remove a column on the table force the detection to found new column
        # which is existing in metadata but not in table
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True)
            )
            registry.Test.__table__.create(bind=conn)

        registry.migration.ignore_migration_for = {'test': ['other']}
        report = registry.migration.detect_changed()
        assert report.log_has("Add test.other")

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

        registry.migration.ignore_migration_for = {'test': True}
        report = registry.migration.detect_changed()
        assert not report.log_has("Drop Column test.other2")

    def test_detect_nullable_with_protected_table(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64), nullable=False),
            )
            registry.Test.__table__.create(bind=conn)

        registry.migration.ignore_migration_for = {'test': True}
        report = registry.migration.detect_changed()
        assert not report.log_has("Alter test.other")

    def test_detect_nullable_with_protected_column(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64), nullable=False),
            )
            registry.Test.__table__.create(bind=conn)

        registry.migration.ignore_migration_for = {'test': ['other']}
        report = registry.migration.detect_changed()
        assert not report.log_has("Alter test.other")

    def test_detect_server_default_with_protected_table(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64), server_default='9.99'),
            )
            registry.Test.__table__.create(bind=conn)

        registry.migration.ignore_migration_for = {'test': True}
        report = registry.migration.detect_changed()
        assert not report.log_has("Alter test.other")

    def test_detect_server_default_with_protected_column(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64), server_default='9.99'),
            )
            registry.Test.__table__.create(bind=conn)

        registry.migration.ignore_migration_for = {'test': ['other']}
        report = registry.migration.detect_changed()
        assert not report.log_has("Alter test.other")

    def test_detect_drop_anyblok_index(self, registry):
        with cnx(registry) as conn:
            conn.execute(
                """CREATE INDEX anyblok_ix_test__other ON test (other);""")

        registry.migration.ignore_migration_for = {'test': True}
        report = registry.migration.detect_changed()
        assert not report.log_has("Drop index anyblok_ix_test__other on test")

    def test_detect_type_with_protected_table(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', Integer),
            )
            registry.Test.__table__.create(bind=conn)

        registry.migration.ignore_migration_for = {'test': True}
        report = registry.migration.detect_changed()
        assert not report.log_has("Alter test.other")

    def test_detect_type_with_protected_column(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', Integer),
            )
            registry.Test.__table__.create(bind=conn)

        registry.migration.ignore_migration_for = {'test': ['other']}
        report = registry.migration.detect_changed()
        assert not report.log_has("Alter test.other")

    def test_detect_add_foreign_key_with_protected_table(self, registry):
        with cnx(registry) as conn:
            registry.TestFK.__table__.drop(bind=conn)
            registry.TestFK.__table__ = Table(
                'testfk', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', Integer),
            )
            registry.TestFK.__table__.create(bind=conn)

        registry.migration.ignore_migration_for = {'testfk': True}
        report = registry.migration.detect_changed()
        assert not report.log_has(
            "Add Foreign keys on (testfk.other) => (testfktarget.integer)")

    def test_detect_add_foreign_key_with_protected_column(self, registry):
        with cnx(registry) as conn:
            registry.TestFK.__table__.drop(bind=conn)
            registry.TestFK.__table__ = Table(
                'testfk', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', Integer),
            )
            registry.TestFK.__table__.create(bind=conn)

        registry.migration.ignore_migration_for = {'testfk': ['other']}
        report = registry.migration.detect_changed()
        assert not report.log_has(
            "Add Foreign keys on (testfk.other) => (testfktarget.integer)")

    def test_detect_drop_foreign_key_with_protected_table(self, registry):
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

        registry.migration.ignore_migration_for = {'test': True}
        report = registry.migration.detect_changed()
        assert not report.log_has(
            "Drop Foreign keys on test.other => system_blok.name")

    def test_detect_drop_foreign_key_with_protected_column(self, registry):
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

        registry.migration.ignore_migration_for = {'test': ['other']}
        report = registry.migration.detect_changed()
        assert not report.log_has(
            "Drop Foreign keys on test.other => system_blok.name")

    @pytest.mark.skipif(sgdb_in(['MsSQL']),
                        reason="MsSQL does not add unique #121")
    def test_detect_add_unique_constraint_with_protected_table(self, registry):
        with cnx(registry) as conn:
            registry.TestUnique.__table__.drop(bind=conn)
            registry.TestUnique.__table__ = Table(
                'testunique', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64)),
            )
            registry.TestUnique.__table__.create(bind=conn)

        registry.migration.ignore_migration_for = {'testunique': True}
        report = registry.migration.detect_changed()
        assert not report.log_has(
            "Add unique constraint on testunique (other)")

    @pytest.mark.skipif(sgdb_in(['MsSQL']),
                        reason="MsSQL does not add unique #121")
    def test_detect_add_unique_constraint_with_protected_column(self,
                                                                registry):
        with cnx(registry) as conn:
            registry.TestUnique.__table__.drop(bind=conn)
            registry.TestUnique.__table__ = Table(
                'testunique', MetaData(),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64)),
            )
            registry.TestUnique.__table__.create(bind=conn)

        registry.migration.ignore_migration_for = {'testunique': ['other']}
        report = registry.migration.detect_changed()
        assert not report.log_has(
            "Add unique constraint on testunique (other)")

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

        registry.migration.ignore_migration_for = {'test': True}
        report = registry.migration.detect_changed()
        assert not report.log_has(
            "Drop constraint anyblok_uq_test__other on test")

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

        registry.migration.ignore_migration_for = {'testcheck': True}
        report = registry.migration.detect_changed()
        assert not report.log_has(
            "Add check constraint anyblok_ck_testcheck__test on testcheck")

    @pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB', 'MsSQL']),
                        reason="No CheckConstraint works #90")
    def test_detect_drop_check_anyblok_constraint(self, registry):
        with cnx(registry) as conn:
            registry.Test.__table__.drop(bind=conn)
            registry.Test.__table__ = Table(
                'test', MetaData(naming_convention=naming_convention),
                Column('integer', Integer, primary_key=True),
                Column('other', String(64)),
                CheckConstraint(
                    "other != 'test'", name='check')
            )
            registry.Test.__table__.create(bind=conn)

        registry.migration.ignore_migration_for = {'test': True}
        report = registry.migration.detect_changed()
        assert not report.log_has(
            "Drop check constraint anyblok_ck__test__check on test")
