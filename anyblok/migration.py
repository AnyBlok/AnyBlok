# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2016 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2019 Joachim Trouverie
#    Copyright (C) 2020 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#    Copyright (C) 2021 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from pkg_resources import iter_entry_points
from sqlalchemy.exc import IntegrityError, OperationalError
from alembic.migration import MigrationContext
from alembic.autogenerate import compare_metadata
from alembic.operations import Operations
from contextlib import contextmanager
from sqlalchemy import func, select, update, join, and_, text
from anyblok.config import Configuration
from sqlalchemy import inspect
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.ddl import CreateSchema, DropSchema
from .common import sgdb_in, return_list
from sqlalchemy.schema import (
    DDLElement, PrimaryKeyConstraint, CheckConstraint, UniqueConstraint)
from logging import getLogger

logger = getLogger(__name__)


MIGRATION_TYPE_PLUGINS_NAMESPACE = 'anyblok.migration_type.plugins'


class AlterSchema(DDLElement):
    def __init__(self, oldname, newname):
        self.oldname = oldname
        self.newname = newname


@compiles(CreateSchema, "mysql")
def compile_create_schema(element, compiler, **kw):
    schema = compiler.preparer.format_schema(element.element)
    return "CREATE SCHEMA %s CHARSET UTF8" % schema


@compiles(AlterSchema)
def compile_alter_schema(element, compiler, **kw):
    old_schema_name = compiler.preparer.format_schema(element.oldname)
    new_schema_name = compiler.preparer.format_schema(element.newname)
    return "ALTER SCHEMA %s RENAME TO %s" % (old_schema_name, new_schema_name)


@contextmanager
def cnx(migration):
    """ Context manager used by migration to get the connection """
    try:
        yield migration.conn
    except MigrationException:
        raise
    except Exception:  # pragma: no cover
        migration.conn.execute(text("rollback"))
        raise


class MigrationException(AttributeError):
    """ Simple Exception class for Migration """


class MigrationReport:
    """ Change report

    Get a new report::

        report = MigrationReport(migrationinstance, change_detected)

    """

    def ignore_migration_for(self, schema, table, default=None):
        if schema in self.ignore_migration_for_schema_from_configuration:
            return True

        if table in self.ignore_migration_for_table_from_configuration:
            return True

        return self.migration.ignore_migration_for.get(table, default)

    def raise_if_withoutautomigration(self):
        if self.migration.withoutautomigration:
            raise MigrationException("The metadata and the base structue are "
                                     "different, or this difference is "
                                     "forbidden in 'no auto migration' mode")

    def table_is_added(self, table):
        for action in self.actions:
            if action[0] == 'add_table' and action[1] is table:
                return True  # pragma: no cover

        return False

    def init_add_schema(self, diff):
        self.raise_if_withoutautomigration()
        _, schema = diff
        self.log_names.append('Add schema %s' % schema)

    def init_add_table(self, diff):
        self.raise_if_withoutautomigration()
        _, table = diff
        table_name = (
            '%s.%s' % (table.schema, table.name)
            if table.schema else table.name)
        self.log_names.append('Add table %s' % table_name)

    def init_add_column(self, diff):
        self.raise_if_withoutautomigration()
        _, schema, table, column = diff
        if self.ignore_migration_for(schema, table) is True:
            return True

        self.log_names.append('Add %s.%s' % (table, column.name))

    def can_remove_constraints(self, name):
        if name.startswith('anyblok_uq_'):
            return True

        if self.migration.reinit_constraints:
            return True

        if self.migration.reinit_all:
            return True

        return False

    def can_remove_fk_constraints(self, name):
        if name.startswith('anyblok_fk_'):
            return True

        if self.migration.reinit_constraints:
            return True

        if self.migration.reinit_all:
            return True

        return False

    def can_remove_check_constraints(self, name):
        if name.startswith('anyblok_ck_'):
            return True

        if self.migration.reinit_constraints:
            return True

        if self.migration.reinit_all:
            return True

        return False

    def init_remove_constraint(self, diff):
        _, constraint = diff
        if self.ignore_migration_for(constraint.table.schema,
                                     constraint.table.name) is True:
            return True

        self.log_names.append('Drop constraint %s on %s' % (
            constraint.name, constraint.table))

        if self.can_remove_constraints(constraint.name):
            self.raise_if_withoutautomigration()
        else:
            return True

    def can_remove_index(self, name):
        if name.startswith('anyblok_ix_'):
            return True

        if self.migration.reinit_indexes:
            return True

        if self.migration.reinit_all:
            return True

        return False

    def init_add_index(self, diff):
        self.raise_if_withoutautomigration()
        _, constraint = diff
        if self.ignore_migration_for(constraint.table.schema,
                                     constraint.table.name) is True:
            return True  # pragma: no cover

        columns = [x.name for x in constraint.columns]
        if self.table_is_added(constraint.table):
            return True  # pragma: no cover

        self.log_names.append('Add index constraint on %s (%s)' % (
            constraint.table.name, ', '.join(columns)))

    def init_remove_index(self, diff):
        _, index = diff
        if self.ignore_migration_for(index.table.schema,
                                     index.table.name) is True:
            return True

        self.log_names.append('Drop index %s on %s' % (index.name,
                                                       index.table))
        if self.can_remove_index(index.name):
            self.raise_if_withoutautomigration()
        else:
            return True

    def init_add_fk(self, diff):
        self.raise_if_withoutautomigration()
        _, fk = diff
        if self.ignore_migration_for(fk.table.schema, fk.table.name) is True:
            return True

        from_ = []
        to_ = []
        for column in fk.columns:
            if column.name in self.ignore_migration_for(
                fk.table.schema, fk.table.name, []
            ):
                return True

            for fk_ in column.foreign_keys:
                from_.append('%s.%s' % (fk.table.name, column.name))
                to_.append(fk_.target_fullname)

        self.log_names.append('Add Foreign keys on (%s) => (%s)' % (
            ', '.join(from_), ', '.join(to_)))

    def init_remove_fk(self, diff):
        _, fk = diff
        if self.ignore_migration_for(fk.table.schema, fk.table.name) is True:
            return True

        for column in fk.columns:
            if column.name in self.ignore_migration_for(
                fk.table.schema, fk.table.name, []
            ):
                return True

            for fk_ in column.foreign_keys:
                self.log_names.append('Drop Foreign keys on %s.%s => %s' % (
                    fk.table.name, column.name, fk_.target_fullname))

        if not self.can_remove_fk_constraints(fk.name):
            return True

        self.raise_if_withoutautomigration()

    def init_add_ck(self, diff):
        self.raise_if_withoutautomigration()
        _, table, ck = diff
        if self.ignore_migration_for(ck.table.schema, table) is True:
            return True

        if ck.table.schema:
            table = ck.table.schema + '.' + table

        self.log_names.append('Add check constraint %s on %s' % (
            ck.name, table))

    def init_remove_ck(self, diff):
        _, table, ck = diff
        if self.ignore_migration_for(ck['schema'], table) is True:
            return True

        if ck['schema']:
            table = ck['schema'] + '.' + table

        self.log_names.append('Drop check constraint %s on %s' % (
            ck['name'], table))

        if not self.can_remove_check_constraints(ck['name']):
            return True

        self.raise_if_withoutautomigration()

    def init_add_constraint(self, diff):
        self.raise_if_withoutautomigration()
        _, constraint = diff
        columns = []

        if self.ignore_migration_for(constraint.table.schema,
                                     constraint.table.name) is True:
            return True

        for column in constraint.columns:
            columns.append(column.name)
            if column.name in self.ignore_migration_for(constraint.table.schema,
                                                        constraint.table.name,
                                                        []):
                return True

        self.log_names.append('Add unique constraint on %s (%s)' % (
            constraint.table.name, ', '.join(columns)))

    def can_remove_column(self):
        if self.migration.reinit_columns:
            return True

        if self.migration.reinit_all:
            return True

        return False

    def init_remove_column(self, diff):
        column = diff[3]
        if self.ignore_migration_for(column.table.schema,
                                     column.table.name) is True:
            return True

        msg = "Drop Column %s.%s" % (column.table.name,
                                     column.name)

        if self.can_remove_column():
            self.log_names.append(msg)
            self.raise_if_withoutautomigration()
            return False

        fk_removed = []
        for fk in column.foreign_keys:
            if not self.can_remove_fk_constraints(fk.name):
                # only if fk is not removable. FK can come from
                # * DBA manager, it is the only raison to destroy it
                # * alembic, some constrainte change name during the remove
                if fk.name not in fk_removed:  # pragma: no cover
                    self.actions.append(('remove_fk', fk.constraint))
                    fk_removed.append(fk.name)

        if column.nullable is False:
            self.raise_if_withoutautomigration()
            msg += " (not null)"
            self.log_names.append(msg)
            self.actions.append(
                ('modify_nullable', column.table.schema, column.table.name,
                 column.name, {}, False, True))
            return True

        self.log_names.append(msg)
        return True

    def can_remove_table(self, schema):
        schemas = self.migration.metadata._schemas
        if schema and schema not in schemas:
            return False

        if self.migration.reinit_tables:
            return True

        if self.migration.reinit_all:
            return True

        return False

    def init_change_pk(self, diff):
        name, table, constraint = diff
        raise MigrationException(
            (
                "Change primary key constraint %s on %s: (%s). "
                "AnyBlok can't determine the good action to do "
                "for relation ship based on primary key who changed, "
                "You must make the migration by your self before."
            ) % (name, table, ', '.join([x.name for x in constraint.columns])))

    def init_remove_table(self, diff):
        table = diff[1]
        table_name = (
            '%s.%s' % (table.schema, table.name)
            if table.schema else table.name)
        self.log_names.append("Drop Table %s" % table_name)
        if self.can_remove_table(diff[1].schema):
            self.raise_if_withoutautomigration()
        else:
            return True

    def init_modify_type(self, diff):
        if self.ignore_migration_for(diff[1], diff[2]) is True:
            return True

        if diff[3] in self.ignore_migration_for(diff[1], diff[2], []):
            return True

        selected_plugin = self.get_plugin_for(diff[5], diff[6])
        if selected_plugin is not None:
            if not selected_plugin.need_to_modify_type():
                return True

        table = "%s.%s" % diff[1:3] if diff[1] else diff[2]
        self.log_names.append("Modify column type %s.%s : %s => %s" % (
            table, diff[3], diff[5], diff[6]))
        return False

    def init_modify_nullable(self, diff):
        if self.ignore_migration_for(diff[1], diff[2]) is True:
            return True

        if diff[3] in self.ignore_migration_for(diff[1], diff[2], []):
            return True

        table = "%s.%s" % diff[1:3] if diff[1] else diff[2]
        self.log_names.append("Modify column nullable %s.%s : %s => %s" % (
            table, diff[3], diff[5], diff[6]))
        return False

    def init_modify_server_default(self, diff):
        if self.ignore_migration_for(diff[1], diff[2]) is True:
            return True

        if diff[3] in self.ignore_migration_for(diff[1], diff[2], []):
            return True

        table = "%s.%s" % diff[1:3] if diff[1] else diff[2]
        self.log_names.append("Modify column default %s.%s : %s => %s" % (
            table, diff[3], diff[5], diff[6]))
        return False

    def init_plugins(self):
        """Get migration plugins from entry points"""

        def dialect_sort(plugin):
            """Sort plugins with dialect not None first"""
            return (plugin.dialect is None, plugin.dialect)

        plugins = sorted((
            entry_point.load()
            for entry_point
            in iter_entry_points(MIGRATION_TYPE_PLUGINS_NAMESPACE)
        ), key=dialect_sort)

        return plugins

    def get_plugin_for(self, oldvalue, newvalue):
        """search plugin by column types"""
        for plugin in self.plugins:
            if isinstance(plugin.dialect, (tuple, list)):
                dialects = plugin.dialect
            else:
                dialects = [plugin.dialect]

            if (
                issubclass(plugin, MigrationColumnTypePlugin) and
                isinstance(oldvalue, plugin.from_type) and
                isinstance(newvalue, plugin.to_type) and
                (
                    plugin.dialect is None or
                    sgdb_in(self.migration.conn.engine, dialects)
                )
            ):
                return plugin()

        return None

    def __init__(self, migration, diffs):
        """ Initializer

        :param migration: migration instance
        :param diffs: diff between the metadata and the database, come from
            change detection of alembic
        """
        self.migration = migration
        self.logs = []
        self.actions = []
        self.diffs = diffs
        self.log_names = []
        self.plugins = self.init_plugins()
        self.ignore_migration_for_table_from_configuration = [
            self.migration.loaded_namespaces[x].__tablename__
            for x in return_list(
                Configuration.get('ignore_migration_for_models')
            )
            if (
                x in self.migration.loaded_namespaces and
                self.migration.loaded_namespaces[x].is_sql
            )
        ]
        self.ignore_migration_for_schema_from_configuration = return_list(
            Configuration.get('ignore_migration_for_schemas'))

        mappers = {
            'add_schema': self.init_add_schema,
            'add_table': self.init_add_table,
            'add_column': self.init_add_column,
            'remove_constraint': self.init_remove_constraint,
            'add_index': self.init_add_index,
            'remove_index': self.init_remove_index,
            'add_fk': self.init_add_fk,
            'remove_fk': self.init_remove_fk,
            'add_ck': self.init_add_ck,
            'remove_ck': self.init_remove_ck,
            'add_constraint': self.init_add_constraint,
            'remove_column': self.init_remove_column,
            'remove_table': self.init_remove_table,
            'change_pk': self.init_change_pk,
            'modify_type': self.init_modify_type,
            'modify_nullable': self.init_modify_nullable,
            'modify_default': self.init_modify_server_default,
        }
        for diff in diffs:
            if isinstance(diff, list):
                self.raise_if_withoutautomigration()
                for change in diff:
                    _, _, table, column, _, _, _ = change
                    fnct = mappers.get(change[0])
                    if fnct:
                        if fnct(change):
                            continue
                    else:
                        logger.warning('Unknow diff: %r', change)

                    self.log_names.append('Alter %s.%s' % (table, column))
                    self.actions.append(change)
            else:
                fnct = mappers.get(diff[0])
                if fnct:
                    if fnct(diff):
                        continue
                else:
                    logger.warning('Unknow diff: %r', diff)

                self.actions.append(diff)

        for log_name in self.log_names:
            if log_name and not self.log_has(log_name):
                self.logs.append(log_name)

    def log_has(self, log):
        """ return True id the log is present

        .. warning:: this method is only used for the unittest

        :param log: log sentence expected
        """
        return log in self.logs

    def apply_change_add_schema(self, action):
        _, schema = action
        self.migration.schema().add(schema)

    def apply_change_add_table(self, action):
        _, table = action
        if table.schema:
            t = self.migration.schema(table.schema).table()
        else:
            t = self.migration.table()

        t.add(table.name, table=table)

    def get_migration_table(self, table):
        if table.schema:
            return self.migration.schema(table.schema).table(table.name)
        else:
            return self.migration.table(table.name)

    def apply_change_add_column(self, action):
        _, _, table, column = action
        t = self.get_migration_table(column.table)
        t.column().add(column)

    def apply_change_modify_nullable(self, action):
        _, schema, table, column, kwargs, oldvalue, newvalue = action
        if schema:
            t = self.migration.schema(schema).table(table)
        else:
            t = self.migration.table(table)

        t.column(column).alter(
            nullable=newvalue, existing_nullable=oldvalue, **kwargs)

    def apply_change_modify_type(self, action):
        _, schema, table, column, kwargs, oldvalue, newvalue = action
        if schema:
            t = self.migration.schema(schema).table(table)
        else:
            t = self.migration.table(table)

        selected_plugin = self.get_plugin_for(oldvalue, newvalue)
        if selected_plugin is not None:
            selected_plugin.apply(t.column(column), **kwargs)
        else:
            t.column(column).alter(
                type_=newvalue, existing_type=oldvalue, **kwargs)

    def apply_change_modify_default(self, action):
        _, schema, table, column, kwargs, oldvalue, newvalue = action
        if schema:
            t = self.migration.schema(schema).table(table)  # pragma: no cover
        else:
            t = self.migration.table(table)

        t.column(column).alter(
            server_default=newvalue, existing_server_default=oldvalue,
            **kwargs)

    def apply_change_remove_constraint(self, action):
        _, constraint = action
        if constraint.__class__ is UniqueConstraint:
            table = self.get_migration_table(constraint.table)
            table.unique(name=constraint.name).drop()

    def apply_change_remove_index(self, action):
        _, index = action
        if not index.unique:
            table = self.get_migration_table(index.table)
            table.index(name=index.name).drop()

    def apply_change_add_fk(self, action):
        _, fk = action
        t = self.get_migration_table(fk.table)
        from_ = []
        to_ = []
        for column in fk.columns:
            for fk_ in column.foreign_keys:
                from_.append(column.name)
                to_.append(fk_.column)

        t.foreign_key(fk.name).add(from_, to_)

    def apply_change_add_ck(self, action):
        _, table, ck = action
        t = self.get_migration_table(ck.table)
        t.check(ck.name).add(ck.sqltext)

    def apply_change_remove_fk(self, action):
        _, fk = action
        t = self.get_migration_table(fk.table)
        t.foreign_key(fk.name).drop()

    def apply_change_remove_ck(self, action):
        _, table, ck = action
        if ck['schema']:
            t = self.migration.schema(ck['schema']).table(table)
        else:
            t = self.migration.table(table)

        t.foreign_key(ck['name']).drop()

    def apply_change_add_constraint(self, action):
        _, constraint = action
        table = self.get_migration_table(constraint.table)
        table.unique(name=constraint.name).add(*constraint.columns)

    def apply_change_add_index(self, action):
        _, constraint = action
        table = self.get_migration_table(constraint.table)
        table.index().add(*constraint.columns, name=constraint.name)

    def apply_remove_table(self, action):
        table = self.get_migration_table(action[1])
        table.drop()

    def apply_remove_column(self, action):
        table = self.get_migration_table(action[3].table)
        table.column(action[3].name).drop()

    def apply_change(self):
        """ Apply the migration

        this method parses the detected change and calls the Migration
        system to apply the change with the api of Declarations
        """
        for log in self.logs:
            logger.debug(log)

        mappers = {
            'add_schema': self.apply_change_add_schema,
            'add_table': self.apply_change_add_table,
            'add_column': self.apply_change_add_column,
            'modify_nullable': self.apply_change_modify_nullable,
            'modify_type': self.apply_change_modify_type,
            'modify_default': self.apply_change_modify_default,
            'add_index': self.apply_change_add_index,
            'add_fk': self.apply_change_add_fk,
            'add_ck': self.apply_change_add_ck,
            'add_constraint': self.apply_change_add_constraint,
            'remove_constraint': self.apply_change_remove_constraint,
            'remove_index': self.apply_change_remove_index,
            'remove_fk': self.apply_change_remove_fk,
            'remove_ck': self.apply_change_remove_ck,
            'remove_table': self.apply_remove_table,
            'remove_column': self.apply_remove_column,
        }
        for action in self.actions:
            fnct = mappers.get(action[0])
            if fnct:
                fnct(action)


class MigrationConstraintForeignKey:
    """ Used to apply a migration on a foreign key

    You can add::

        table.column('my column').foreign_key().add(Blok.name)

    Or drop::

        table.column('my column').foreign_key().drop()

    """
    def __init__(self, table, name):
        self.table = table
        self.name = name

    def add(self, local_columns, remote_columns, **kwargs):
        """ Add a new foreign key

        :param remote_field: The column of the remote model
        :rtype: MigrationConstraintForeignKey instance
        """
        remote_columns = [
            x.property.columns[0] if hasattr(x, 'property') else x
            for x in remote_columns]

        remote_table = set(x.table.name for x in remote_columns)
        if len(remote_table) != 1:
            raise MigrationException(  # pragma: no cover
                "Remote column must have the same table "
                "(%s)" % ', '.join(remote_table))

        remote_table = remote_table.pop()
        remote_columns_names = [x.name for x in remote_columns]
        self.table.migration.operation.create_foreign_key(
            self.name, self.table.name, remote_table,
            local_columns, remote_columns_names,
            source_schema=self.table.schema,
            referent_schema=remote_columns[0].table.schema,
            **kwargs)

        return self

    def drop(self):
        """ Drop the foreign key """
        self.table.migration.operation.drop_constraint(
            self.name, self.table.name, type_='foreignkey',
            schema=self.table.schema)
        return self


class MigrationColumnTypePlugin:
    """Meta class for column migration type plugin

    Must be exposed as entry point in namespace 'anyblok.migration_type.plugins'

    :param to_type: Column type value (sqlalchemy.types) as used in Model
                    classes in source code
    :param from_type: Column type value (sqlalchemy.types) as required to
                      communicate with the DBMS
    :param dialect: DB dialect (list of strings or string)

    Example::

    class BooleanToTinyIntMySQL(MigrationColumnTypePlugin):

        to_type = sqlalchemy.types.Boolean
        from_type = sqlalchemy.types.TINYINT
        dialect = ['MySQL', 'MariaDB']

        def need_to_modify_type(self):
            return False

        def apply(self, column, **kwargs):
            '''Boolean are TINYINT in MySQL DataBases'''
            # do nothing
            pass
    """

    to_type = None
    from_type = None
    dialect = None

    def apply(self, column, **kwargs):
        """Apply column migration, this method MUST be overriden in plugins
        subclass
        """
        raise NotImplementedError()  # pragma: no cover

    def need_to_modify_type(self, column, **kwargs):
        """If False the type won't be modified"""
        return True  # pragma: no cover


class MigrationColumn:
    """ get or add a column

    Add a new column::

        table.column().add(Sqlachemy column)

    Get a column::

        c = table.column('My column name')

    Alter the column::

        c.alter(new_column_name='Another column name')

    Drop the column::

        c.drop()
    """
    def __init__(self, table, name):
        self.table = table
        self.name = name
        self.info = {}

        if name is not None:
            op = self.table.migration.operation
            with cnx(self.table.migration) as conn:
                columns = op.impl.dialect.get_columns(
                    conn, self.table.name, schema=table.schema)

            for c in columns:
                if c['name'] == name:
                    self.info.update(c)

            if not self.info:
                raise MigrationException(
                    "No column %r found on %r" % (name, self.table.name))

    def apply_default_value(self, column):
        if column.default:
            execute = self.table.migration.conn.execute
            val = column.default.arg
            table = self.table.migration.metadata.tables[self.table.name]
            table.append_column(column)
            cname = getattr(table.c, column.name)
            if column.default.is_callable:  # pragma: no cover
                Table = self.table.migration.metadata.tables['system_model']
                Column = self.table.migration.metadata.tables['system_column']
                j1 = join(Table, Column, Table.c.name == Column.c.model)
                query = select([Column.c.name]).select_from(j1)
                query = query.where(Column.c.primary_key.is_(True))
                query = query.where(Table.c.table == self.table.name)
                columns = [x[0] for x in execute(query).fetchall()]

                query = select([func.count()]).select_from(table)
                query = query.where(cname.is_(None))
                nb_row = self.table.migration.conn.execute(query).fetchone()[0]
                for offset in range(nb_row):
                    query = select(columns).select_from(table)
                    query = query.where(cname.is_(None)).limit(1)
                    res = execute(query).fetchone()
                    where = and_(
                        *[getattr(table.c, x) == res[x] for x in columns])
                    query = update(table).where(where).values(
                        {cname: val(None)})
                    execute(query)

            else:
                query = update(table).where(cname.is_(None)).values(
                    {cname: val})
                execute(query)

    def add(self, column):
        """ Add a new column

        The column is added in two phases, the last phase is only for the
        the nullable, if nullable can not be applied, a warning is logged

        :param column: sqlalchemy column
        :rtype: MigrationColumn instance
        """
        migration = self.table.migration
        nullable = column.nullable
        if not nullable:
            column.nullable = True

        # check the table exist
        table = (
            "%s.%s" % (self.table.schema, self.table.name)
            if self.table.schema
            else self.table.name)

        table_ = migration.metadata.tables[table]

        if sgdb_in(self.table.migration.conn.engine, ['MsSQL']):
            column.table = table_

        migration.operation.impl.add_column(self.table.name, column,
                                            schema=self.table.schema)
        self.apply_default_value(column)

        if not nullable:
            c = MigrationColumn(self.table, column.name)
            c.alter(nullable=False)

        return MigrationColumn(self.table, column.name)

    def alter(self, **kwargs):
        """ Alter an existing column

        Alter the column in two phases, because the nullable column has not
        locked the migration

        .. warning::
            See Alembic alter_column, the existing_* param are used for some
            dialect like mysql, is importante to filled them for these dialect

        :param new_column_name: New name for the column
        :param type_: New sqlalchemy type
        :param server_default: The default value in database server
        :param nullable: New nullable value
        :param comment: New comment value
        :rtype: MigrationColumn instance
        """
        vals = {}
        name = self.name
        if 'existing_server_default' in kwargs:
            esd = kwargs['existing_server_default']
            if esd:
                vals['existing_server_default'] = esd.arg
            else:
                vals['existing_server_default'] = esd
        else:
            vals['existing_server_default'] = (
                self.server_default
                if 'server_default' not in kwargs
                else None)
        vals.update({
            'existing_type': kwargs.get(
                'existing_type',
                self.type if 'type_' not in kwargs else None),
            'existing_autoincrement': (
                None
                if not sgdb_in(self.table.migration.conn.engine,
                               ['MySQL', 'MariaDB'])
                else kwargs.get(
                    'existing_autoincrement',
                    self.autoincrement
                    if 'autoincrement' not in kwargs else None)
            ),
            'existing_comment': kwargs.get(
                'existing_comment',
                self.comment if 'comment' not in kwargs else None)
        })
        vals.update({
            k: kwargs[k]
            for k in ('autoincrement', 'server_default', 'type_')
            if k in kwargs})

        if 'name' in kwargs:
            vals['new_column_name'] = kwargs['name']
            name = kwargs['name']

        if vals:
            self.table.migration.operation.alter_column(
                self.table.name, self.name,
                schema=self.table.schema, **vals)

        if 'nullable' in kwargs:
            nullable = kwargs['nullable']
            vals['existing_nullable'] = (
                self.nullable if 'nullable' in kwargs else None)
            savepoint = '%s_not_null' % name
            try:
                self.table.migration.savepoint(savepoint)
                self.table.migration.operation.alter_column(
                    self.table.name, self.name, nullable=nullable,
                    schema=self.table.schema, **vals)
                self.table.migration.release_savepoint(savepoint)
            except (IntegrityError, OperationalError) as e:
                self.table.migration.rollback_savepoint(savepoint)
                logger.warning(str(e))

        return MigrationColumn(self.table, name)

    def drop(self):
        """ Drop the column """
        self.table.migration.operation.drop_column(
                self.table.name, self.name, schema=self.table.schema)

    @property
    def nullable(self):
        """ Use for unittest return if the column is nullable """
        return self.info.get('nullable', None)

    @property
    def type(self):
        """ Use for unittest: return the column type """
        return self.info.get('type', None)

    @property
    def server_default(self):
        """ Use for unittest: return the default database value """
        sdefault = self.info.get('default', None)
        if sgdb_in(self.table.migration.conn.engine, ['MySQL', 'MariaDB']):
            if sdefault:
                if not isinstance(sdefault, str):
                    return sdefault.arg  # pragma: no cover
                elif sdefault is None:
                    return None  # pragma: no cover
                else:
                    return text(sdefault)

        return sdefault

    @property
    def comment(self):
        """ Use for unittest: return the default database value """
        return self.info.get('comment', None)

    @property
    def autoincrement(self):
        """ Use for unittest: return the default database value """
        table_name = (
            "%s.%s" % (self.table.schema, self.table.name)
            if self.table.schema else self.table.name)
        table = self.table.migration.metadata.tables[table_name]
        primary_keys = [x.name for x in table.primary_key.columns]
        if self.name in primary_keys:
            return False  # pragma: no cover

        return self.info.get('autoincrement', None)


class MigrationConstraintCheck:
    """ Used for the Check constraint

    Add a new constraint::

        table('My table name').check().add('check_my_column', 'mycolumn > 5')

    Get and drop the constraint::

        table('My table name').check('check_my_column').drop()

    """
    def __init__(self, table, name):
        self.table = table
        self.name = name
        # TODO dialect not have method to check if constraint exist

    def add(self, condition):
        """ Add the constraint

        :param condition: constraint to apply
        :rtype: MigrationConstraintCheck instance
        """
        self.table.migration.operation.create_check_constraint(
            self.name, self.table.name, condition,
            schema=self.table.schema)

        return self

    def drop(self):
        """ Drop the constraint """
        self.table.migration.operation.drop_constraint(
            self.name, self.table.name, type_='check',
            schema=self.table.schema)


class MigrationConstraintUnique:
    """ Used for the Unique constraint

    Add a new constraint::

        table('My table name').unique('constraint name').add('col1', 'col2')

    Get and drop the constraint::

        table('My table name').unique('constraint name').drop()

    Let AnyBlok to define the name of the constraint::

        table('My table name').unique(None).add('col1', 'col2')


    """
    def __init__(self, table, name):
        self.table = table
        self.name = name

    def add(self, *columns):
        """ Add the constraint

        :param *columns: list of SQLalchemy column
        :rtype: MigrationConstraintUnique instance
        :exception: MigrationException
        """
        if not columns:
            raise MigrationException(  # pragma: no cover
                """To add an unique constraint you """
                """must define one or more columns""")

        columns_name = [x.name for x in columns]
        savepoint = 'uq_%s' % (self.name or '')
        try:
            self.table.migration.savepoint(savepoint)
            self.table.migration.operation.create_unique_constraint(
                self.name, self.table.name, columns_name,
                schema=self.table.schema)
            self.table.migration.release_savepoint(savepoint)
        except (IntegrityError, OperationalError) as e:
            self.table.migration.rollback_savepoint(savepoint)

            logger.warning(
                "Error during the add of new unique constraint %r "
                "on table %r and columns %r : %r " % (self.name,
                                                      self.table.name,
                                                      columns_name, str(e)))

        return self

    def drop(self):
        """ Drop the constraint """
        self.table.migration.operation.drop_constraint(
            self.name, self.table.name, type_='unique',
            schema=self.table.schema)


class MigrationConstraintPrimaryKey:
    """ Used for the primary key constraint

    Add a new constraint::

        table('My table name').primarykey().add('col1', 'col2')

    Get and drop the constraint::

        table('My table name').primarykey('col1', 'col2').drop()
    """

    def __init__(self, table):
        self.table = table
        self.name = self.format_name()

    def format_name(self, *columns):
        return 'anyblok_pk_%s' % self.table.name

    def add(self, *columns):
        """ Add the constraint

        :param *columns: list of SQLalchemy column
        :rtype: MigrationConstraintPrimaryKey instance
        :exception: MigrationException
        """
        if not columns:
            raise MigrationException(  # pragma: no cover
                """To add a primary key constraint """
                """you must define one or more columns""")

        if sgdb_in(self.table.migration.conn.engine, ['MsSQL']):
            for column in columns:
                if column.nullable:
                    column.alter(nullable=False)

        columns_name = [x.name for x in columns]
        self.table.migration.operation.create_primary_key(
            self.name, self.table.name, columns_name)
        return self

    def drop(self):
        """ Drop the constraint """
        self.table.migration.operation.drop_constraint(
            self.name, self.table.name, type_='primary')
        return self


class MigrationIndex:
    """ Used for the index constraint

    Add a new constraint::

        table('My table name').index().add('col1', 'col2')

    Get and drop the constraint::

        table('My table name').index('col1', 'col2').drop()

    """

    def __init__(self, table, *columns, **kwargs):
        self.table = table
        if 'name' in kwargs:
            self.name = kwargs['name']
        else:
            self.name = self.format_name(*columns)
        self.exist = False

        if self.name is not None:
            op = self.table.migration.operation
            with cnx(self.table.migration) as conn:
                indexes = op.impl.dialect.get_indexes(
                    conn, self.table.name, schema=self.table.schema)

            for i in indexes:
                if i['name'] == self.name:
                    self.exist = True

            if not self.exist:
                raise MigrationException(  # pragma: no cover
                    "No index %r found on %r" % (self.name, self.table.name))

    def format_name(self, *columns):
        if columns:
            cols = [x.name for x in columns]
            cols.sort()
            cols = '_'.join(cols)
            return 'idx_%s_on_%s' % (cols, self.table.name)

        return None

    def add(self, *columns, **kwargs):
        """ Add the constraint

        :param *columns: list of SQLalchemy column
        :param **kwargs: other attribute fir l __init__
        :rtype: MigrationIndex instance
        :exception: MigrationException
        """
        if not columns:
            raise MigrationException(  # pragma: no cover
                "To add an index you must define one or more columns")

        index_name = kwargs.get('name', self.format_name(*columns))
        columns_name = [x.name for x in columns]
        self.table.migration.operation.create_index(
            index_name, self.table.name, columns_name,
            schema=self.table.schema)

        return MigrationIndex(self.table, *columns, **kwargs)

    def drop(self):
        """ Drop the constraint """
        self.table.migration.operation.drop_index(
            self.name, table_name=self.table.name,
            schema=self.table.schema)


class MigrationTable:
    """ Use to manipulate tables

    Add a table::

        table().add('New table')

    Get an existing table::

        t = table('My table name')

    Alter the table::

        t.alter(name='Another table name')

    Drop the table::

        t.drop()
    """

    def __init__(self, migration, name, schema=None):
        self.name = name
        self.migration = migration
        self.schema = schema

        if name is not None:
            with cnx(self.migration) as conn:
                has_table = migration.operation.impl.dialect.has_table
                if not has_table(conn, name, schema=schema):
                    raise MigrationException("No table %r found" % name)

    def add(self, name, table=None):
        """ Add a new table

        :param name: name of the table
        :param table: an existing instance of the table to create
        :rtype: MigrationTable instance
        """
        if table is not None:
            if table.schema != self.schema:
                raise MigrationException(  # pragma: no cover
                    "The schema of the table (%r.%r) and the MigrationTable %r"
                    "instance are not the same" % (
                        table.schema, table.name, self.schema))

            self.migration.metadata.create_all(
                bind=self.migration.conn,
                tables=[table])
        else:
            self.migration.operation.create_table(name, schema=self.schema)

        return MigrationTable(self.migration, name, self.schema)

    def column(self, name=None):
        """ Get Column

        :param name: Column name
        :rtype: MigrationColumn instance
        """
        return MigrationColumn(self, name)

    def drop(self):
        """ Drop the table """
        self.migration.operation.drop_table(self.name, schema=self.schema)

    def index(self, *columns, **kwargs):
        """ Get index

        :param *columns: List of the column's name
        :rtype: MigrationIndex instance
        """
        return MigrationIndex(self, *columns, **kwargs)

    def unique(self, name):
        """ Get unique

        :param name: str name of the unique constraint
        :rtype: MigrationConstraintUnique instance
        """
        return MigrationConstraintUnique(self, name)

    def check(self, name=None):
        """ Get check

        :param name: str name of the check constraint
        :rtype: MigrationConstraintCheck instance
        """
        return MigrationConstraintCheck(self, name)

    def primarykey(self):
        """ Get primary key

        :rtype: MigrationConstraintPrimaryKey instance
        """
        return MigrationConstraintPrimaryKey(self)

    def alter(self, **kwargs):
        """ Atler the current table

        :param name: New table name
        :rtype: MigrationTable instance
        :exception: MigrationException
        """
        if 'name' not in kwargs:
            raise MigrationException(  # pragma: no cover
                "Table can only alter name")

        name = kwargs['name']
        self.migration.operation.rename_table(
            self.name, name, schema=self.schema)
        return MigrationTable(self.migration, name, schema=self.schema)

    def foreign_key(self, name):
        """ Get a foreign key

        :rtype: MigrationConstraintForeignKey instance
        """
        return MigrationConstraintForeignKey(self, name)


class MigrationSchema:
    """ Use to manipulate tables

    Add a Schema::

        schema().add('New schema')

    Get an existing schema::

        s = schema('My table schema')

    Alter the schema::

        s.alter(name='Another schema name')

    Drop the schema::

        s.drop()
    """

    def __init__(self, migration, name):
        self.name = name
        self.migration = migration

        if name is not None:
            if not self.has_schema():
                raise MigrationException("No schema %r found" % self.name)

    def has_schema(self):
        with cnx(self.migration) as conn:
            if sgdb_in(conn.engine, ['MySQL', 'MariaDB', 'MsSQL']):
                query = """
                    SELECT count(*)
                    FROM INFORMATION_SCHEMA.SCHEMATA
                    WHERE SCHEMA_name='%s'
                """ % self.name
                return conn.execute(text(query)).fetchone()[0]
            else:
                return self.migration.operation.impl.dialect.has_schema(
                    conn, self.name)

    def add(self, name):
        """ Add a new schema

        :param name: name of the schema
        :rtype: MigrationSchema instance
        """
        with cnx(self.migration) as conn:
            conn.execute(CreateSchema(name))

        return MigrationSchema(self.migration, name)

    def table(self, name=None):
        """ Get a table

        :rtype: MigrationTable instance
        """
        return MigrationTable(self.migration, name, schema=self.name)

    def alter(self, name=None):
        """ Atler the current table

        :param name: New schema name
        :rtype: MigrationSchema instance
        :exception: MigrationException
        """
        with cnx(self.migration) as conn:
            conn.execute(AlterSchema(self.name, name))

        return MigrationSchema(self.migration, name)

    def drop(self, cascade=False):
        """ Drop the schema """
        with cnx(self.migration) as conn:
            conn.execute(DropSchema(self.name, cascade=cascade))


class Migration:
    """ Migration Main entry

    This class allows to manipulate all the migration class::

        migration = Migration(Session(), Base.Metadata)
        t = migration.table('My table name')
        c = t.column('My column name from t')
    """

    def __init__(self, registry):
        self.withoutautomigration = registry.withoutautomigration
        self.conn = registry.connection()
        self.loaded_namespaces = registry.loaded_namespaces
        self.loaded_views = registry.loaded_views
        self.metadata = registry.declarativebase.metadata
        self.ddl_compiler = self.conn.dialect.ddl_compiler(
            self.conn.dialect, None)
        self.ignore_migration_for = registry.ignore_migration_for

        opts = {
            'include_schemas': True,
            'compare_server_default': True,
            'render_item': self.render_item,
            'compare_type': self.compare_type,
        }
        self.context = MigrationContext.configure(self.conn, opts=opts)
        self.operation = Operations(self.context)
        self.reinit_all = Configuration.get('reinit_all', False)
        self.reinit_tables = Configuration.get('reinit_tables', False)
        self.reinit_columns = Configuration.get('reinit_columns', False)
        self.reinit_indexes = Configuration.get('reinit_indexes', False)
        self.reinit_constraints = Configuration.get(
            'reinit_constraints', False)

    def table(self, name=None, schema=None):
        """ Get a table

        :param name: default None, name of the table
        :param schema: default None, name of the schema

        :rtype: MigrationTable instance
        """
        return MigrationTable(self, name=name, schema=schema)

    def schema(self, name=None):
        """ Get a table

        :rtype: MigrationSchema instance
        """
        return MigrationSchema(self, name)

    def auto_upgrade_database(self, schema_only=False):
        """ Upgrade the database automaticly """
        report = self.detect_changed(schema_only=schema_only)
        report.apply_change()

    def detect_changed(self, schema_only=False):
        """ Detect the difference between the metadata and the database

        :rtype: MigrationReport instance
        """
        inspector = inspect(self.conn)
        if schema_only:
            diff = self.detect_added_new_schema(inspector)
        else:
            diff = compare_metadata(self.context, self.metadata)
            diff.extend(
                self.detect_undetected_constraint_from_alembic(inspector))

        return MigrationReport(self, diff)

    def detect_added_new_schema(self, inspector):
        diff = []
        schemas = self.metadata._schemas
        reflected_schemas = set(inspector.get_schema_names())
        added_schemas = schemas - reflected_schemas
        for schema in added_schemas:
            diff.append(('add_schema', schema))

        return diff

    def detect_undetected_constraint_from_alembic(self, inspector):
        diff = []
        diff.extend(self.detect_check_constraint_changed(inspector))
        diff.extend(self.detect_pk_constraint_changed(inspector))
        return diff

    def check_constraint_is_same(self, reflected_constraint, constraint):
        """the goal is to detect if contrainst changed when the name is long

        SQLAlchemy trunkated the name if function of database type (
        postgres 63 characters)

        this method check if the truncated name is the same that no truncated
        name and if the constraint text is the same: return True else False
        """
        truncated_name = self.ddl_compiler.preparer.format_constraint(
            constraint)
        if truncated_name == reflected_constraint['name']:
            return True

        return False  # pragma: no cover

    def detect_check_constraint_changed(self, inspector):
        if sgdb_in(self.conn.engine, ['MySQL', 'MariaDB', 'MsSQL']):
            # MySQL don t return the reflected constraint
            return []

        diff = []
        schemas = list(self.metadata._schemas)
        schemas.append(None)
        for schema in schemas:
            for table in inspector.get_table_names(schema=schema):
                table_ = "%s.%s" % (schema, table) if schema else table
                if table_ not in self.metadata.tables:
                    continue

                reflected_constraints = {
                    ck['name']: ck
                    for ck in inspector.get_check_constraints(
                        table, schema=schema)
                }
                constraints = {
                    ck.name: ck
                    for ck in self.metadata.tables[table_].constraints
                    if isinstance(ck, CheckConstraint)
                    if ck.name != '_unnamed_'
                }
                todrop = set(reflected_constraints.keys()) - set(
                    constraints.keys())
                toadd = set(constraints.keys()) - set(
                    reflected_constraints.keys())

                # check a constraint have not been truncated
                todrop_ = todrop.copy()
                for x in todrop_:
                    for y in toadd:
                        if self.check_constraint_is_same(
                            reflected_constraints[x], constraints[y]
                        ):
                            toadd.remove(y)
                            todrop.remove(x)
                            break

                for ck in todrop:
                    ck_ = reflected_constraints[ck]
                    ck_['schema'] = schema
                    diff.append(('remove_ck', table, ck_))

                for ck in toadd:
                    diff.append(('add_ck', table, constraints[ck]))

        return diff

    def detect_pk_constraint_changed(self, inspector):
        diff = []
        schemas = list(self.metadata._schemas)
        schemas.append(None)
        for schema in schemas:
            for table in inspector.get_table_names(schema=schema):
                table_ = "%s.%s" % (schema, table) if schema else table
                if table_ not in self.metadata.tables:
                    continue

                reflected_constraint = inspector.get_pk_constraint(
                    table, schema=schema)
                constraint = [
                    pk
                    for pk in self.metadata.tables[table_].constraints
                    if isinstance(pk, PrimaryKeyConstraint)
                ][0]
                reflected_columns = set(
                    reflected_constraint['constrained_columns'])
                columns = set(x.name for x in constraint.columns)
                if columns != reflected_columns:
                    diff.append(('change_pk', table, constraint))

        return diff

    def savepoint(self, name=None):
        """ Add a savepoint

        :param name: name of the save point
        :rtype: return the name of the save point
        """
        if sgdb_in(self.conn.engine, ['MySQL', 'MariaDB']):
            logger.warning(
                "Try to create a SAVEPOINT, but %r don't have this "
                "functionality" % self.conn.engine.dialect)
            return

        return self.conn._savepoint_impl(name=name)

    def rollback_savepoint(self, name):
        """ Rollback to the savepoint

        :param name: name of the savepoint
        """
        if sgdb_in(self.conn.engine, ['MySQL', 'MariaDB']):
            logger.warning(
                "Try to ROLLBACK TO SAVEPOINT, but %r don't have this "
                "functionality" % self.conn.engine.dialect)
            return

        self.conn._rollback_to_savepoint_impl(name)

    def release_savepoint(self, name):
        """ Release the save point

        :param name: name of the savepoint
        """
        if sgdb_in(self.conn.engine, ['MySQL', 'MariaDB']):
            logger.warning(
                "Try to RELEASE SAVEPOINT, but %r don't have this "
                "functionality" % self.conn.engine.dialect)
            return

        self.conn._release_savepoint_impl(name)

    def render_item(self, type_, obj, autogen_context):
        logger.debug("%r, %r, %r" % (type_, obj, autogen_context))
        return False

    def compare_type(self, context, inspected_column,
                     metadata_column, inspected_type, metadata_type):
        if hasattr(metadata_type, 'compare_type'):
            return metadata_type.compare_type(  # pragma: no cover
                inspected_type)

        return None
