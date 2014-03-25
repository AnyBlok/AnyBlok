# -*- coding: utf-8 -*-
from alembic.migration import MigrationContext
from alembic.autogenerate import compare_metadata
from alembic.operations import Operations
from sqlalchemy import schema
from contextlib import contextmanager


@contextmanager
def cnx(migration):
    try:
        yield migration.conn
    except MigrationException:
        raise
    except Exception:
        migration.conn.execute("rollback")
        raise


class MigrationException(Exception):
    pass


class MigrationReport:

    def __init__(self, migration, diffs):
        self.migration = migration
        self.logs = []
        self.actions = []
        self.diffs = diffs
        log_names = []
        for diff in diffs:
            if isinstance(diff, list):
                for change in diff:
                    _, _, table, column, _, _, _ = change
                    log_names.append('Alter %s.%s' % (table, column))
                    self.actions.append(change)
            else:
                name = diff[0]
                if name == 'add_column':
                    _, _, table, column = diff
                    log_names.append('Add %s.%s' % (table, column.name))
                elif name == 'remove_constraint':
                    _, constraint = diff
                    log_names.append('Drop constraint %s on %s' % (
                        constraint.name, constraint.table))
                elif name == 'remove_index':
                    _, index = diff
                    log_names.append('Drop index %s on %s' % (
                        index.name, index.table))

                self.actions.append(diff)

        for log_name in log_names:
            if log_name and not self.log_has(log_name):
                self.logs.append(log_name)

    def log_has(self, log):
        return log in self.logs

    def apply_change(self):
        for action in self.actions:
            if action[0] == 'add_column':
                _, _, table, column = action
                self.migration.table(table).column().add(column)
            elif action[0] == 'modify_nullable':
                _, _, table, column, kwargs, oldvalue, newvalue = action
                self.migration.table(table).column(column).alter(
                    nullable=newvalue, existing_nullable=oldvalue, **kwargs)
            elif action[0] == 'modify_type':
                _, _, table, column, kwargs, oldvalue, newvalue = action
                self.migration.table(table).column(column).alter(
                    type_=newvalue, existing_type=oldvalue, **kwargs)
            elif action[0] == 'modify_default':
                _, _, table, column, kwargs, oldvalue, newvalue = action
                self.migration.table(table).column(column).alter(
                    server_default=newvalue, existing_server_default=oldvalue,
                    **kwargs)
            elif action[0] == 'remove_constraint':
                _, constraint = action
                if constraint.__class__ is schema.UniqueConstraint:
                    table = self.migration.table(constraint.table)
                    table.unique(name=constraint.name).drop()
            elif action[0] == 'remove_index':
                _, index = action
                if not index.unique:
                    table = self.migration.table(index.table.name)
                    table.index(name=index.name).drop()


class MigrationConstraintForeignKey:

    def __init__(self, column):
        self.column = column
        self.name = self.format_name()

    def format_name(self, *columns):
        return '%s_%s_fkey' % (self.column.table.name, self.column.name)

    def add(self, remote_field, **kwargs):
        remote_table = remote_field.property.columns[0].table.name
        remote_column = remote_field.property.columns[0].name
        self.column.table.migration.operation.create_foreign_key(
            self.name, self.column.table.name, remote_table,
            [self.column.name], [remote_column], **kwargs)
        return self

    def drop(self):
        self.column.table.migration.operation.drop_constraint(
            self.name, self.column.table.name, type_='foreignkey')
        return self


class MigrationColumn:

    def __init__(self, table, name):
        self.table = table
        self.name = name
        self.info = {}

        if name is not None:
            op = self.table.migration.operation
            with cnx(self.table.migration) as conn:
                columns = op.impl.dialect.get_columns(
                    conn, self.table.name)

            for c in columns:
                if c['name'] == name:
                    self.info.update(c)

            if not self.info:
                raise MigrationException(
                    "No column %r found on %r" % (name, self.table.name))

    def add(self, column):
        self.table.migration.operation.impl.add_column(self.table.name, column)
        t = self.table.migration.metadata.tables[self.table.name]
        for constraint in t.constraints:
            if not isinstance(constraint, schema.PrimaryKeyConstraint):
                self.table.migration.operation.impl.add_constraint(constraint)

        return MigrationColumn(self.table, column.name)

    def alter(self, **kwargs):
        vals = {}
        name = self.name

        for k in ('existing_type', 'existing_server_default',
                  'existing_nullable', 'existing_autoincrement',
                  'nullable', 'server_default', 'type_'):
            if k in kwargs:
                vals[k] = kwargs[k]

        if 'name' in kwargs:
            vals['new_column_name'] = kwargs['name']
            name = kwargs['name']

        if vals:
            self.table.migration.operation.alter_column(
                self.table.name, self.name, **vals)

        return MigrationColumn(self.table, name)

    def drop(self):
        self.table.migration.operation.drop_column(self.table.name, self.name)

    def nullable(self):
        return self.info['nullable']

    def type(self):
        return self.info['type']

    def server_default(self):
        return self.info['default']

    def foreign_key(self):
        return MigrationConstraintForeignKey(self)


class MigrationConstraintCheck:

    def __init__(self, table, name):
        self.table = table
        self.name = name
        #TODO dialect not have method to check if constraint exist

    def add(self, name, condition):
        self.table.migration.operation.create_check_constraint(
            name, self.table.name, condition)

        return MigrationConstraintCheck(self.table, self.name)

    def drop(self):
        self.table.migration.operation.drop_constraint(
            self.name, self.table.name, type_='check')


class MigrationConstraintUnique:

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
                uniques = op.impl.dialect.get_unique_constraints(
                    conn, self.table.name)

            for u in uniques:
                if u['name'] == self.name:
                    self.exist = True

            if not self.exist:
                raise MigrationException(
                    "No unique constraint %r found on %r" % (
                        self.name, self.table.name))

    def format_name(self, *columns):
        if columns:
            cols = [x.name for x in columns]
            cols.sort()
            cols = '_'.join(cols)
            return 'unique_%s_on_%s' % (cols, self.table.name)

        return None

    def add(self, *columns):
        if not columns:
            raise MigrationException("""To add an unique constraint you """
                                     """must define one or more columns""")

        unique_name = self.format_name(*columns)
        columns_name = [x.name for x in columns]
        self.table.migration.operation.create_unique_constraint(
            unique_name, self.table.name, columns_name)

        return MigrationConstraintUnique(self.table, *columns)

    def drop(self):
        self.table.migration.operation.drop_constraint(
            self.name, self.table.name, type_='unique')


class MigrationConstraintPrimaryKey:

    def __init__(self, table):
        self.table = table
        self.name = self.format_name()

    def format_name(self, *columns):
        return '%s_pkey' % self.table.name

    def add(self, *columns):
        if not columns:
            raise MigrationException("""To add an primary key  constraint """
                                     """you must define one or more columns""")

        columns_name = [x.name for x in columns]
        self.table.migration.operation.create_primary_key(
            self.name, self.table.name, columns_name)
        return self

    def drop(self):
        self.table.migration.operation.drop_constraint(
            self.name, self.table.name, type_='primary')
        return self


class MigrationIndex:

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
                    conn, self.table.name, None)

            for i in indexes:
                if i['name'] == self.name:
                    self.exist = True

            if not self.exist:
                raise MigrationException(
                    "No index %r found on %r" % (self.name, self.table.name))

    def format_name(self, *columns):
        if columns:
            cols = [x.name for x in columns]
            cols.sort()
            cols = '_'.join(cols)
            return 'idx_%s_on_%s' % (cols, self.table.name)

        return None

    def add(self, *columns):
        if not columns:
            raise MigrationException(
                "To add an index you must define one or more columns")

        index_name = self.format_name(*columns)
        columns_name = [x.name for x in columns]
        self.table.migration.operation.create_index(
            index_name, self.table.name, columns_name)

        return MigrationIndex(self.table, *columns)

    def drop(self):
        self.table.migration.operation.drop_index(
            self.name, table_name=self.table.name)


class MigrationTable:

    def __init__(self, migration, name):
        self.name = name
        self.migration = migration

        if name is not None:
            with cnx(self.migration) as conn:
                if not self.migration.operation.impl.dialect.has_table(conn,
                                                                       name):
                    raise MigrationException("No table %r found" % name)

    def add(self, name):
        self.migration.operation.create_table(name)
        return MigrationTable(self.migration, name)

    def column(self, name=None):
        return MigrationColumn(self, name)

    def drop(self):
        self.migration.operation.drop_table(self.name)

    def index(self, *columns, **kwargs):
        return MigrationIndex(self, *columns, **kwargs)

    def unique(self, *columns, **kwargs):
        return MigrationConstraintUnique(self, *columns, **kwargs)

    def check(self, name=None):
        return MigrationConstraintCheck(self, name)

    def primarykey(self):
        return MigrationConstraintPrimaryKey(self)

    def alter(self, **kwargs):
        if 'name' not in kwargs:
            raise MigrationException("Table can only alter name")

        name = kwargs['name']
        self.migration.operation.rename_table(self.name, name)
        return MigrationTable(self.migration, name)


class Migration:

    def __init__(self, session, metadata):
        self.conn = session.connection()
        self.metadata = metadata

        opts = {
            'compare_type': True,
            'compare_server_default': True,
        }
        self.context = MigrationContext.configure(self.conn, opts=opts)
        self.operation = Operations(self.context)

    def table(self, name=None):
        return MigrationTable(self, name)

    def auto_upgrade_database(self):
        #TODO
        pass

    def detect_changed(self):
        diff = compare_metadata(self.context, self.metadata)
        return MigrationReport(self, diff)
