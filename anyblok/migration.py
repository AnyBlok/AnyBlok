# -*- coding: utf-8 -*-
from sqlalchemy.exc import IntegrityError
from alembic.migration import MigrationContext
from alembic.autogenerate import compare_metadata
from alembic.operations import Operations
from sqlalchemy import schema
from contextlib import contextmanager
from anyblok import Declarations
from logging import getLogger

logger = getLogger(__name__)


@contextmanager
def cnx(migration):
    """ Context manager used by migration to get the connection """
    try:
        yield migration.conn
    except MigrationException:
        raise
    except Exception:
        migration.conn.execute("rollback")
        raise


@Declarations.register(Declarations.Exception)
class MigrationException(Exception):
    """ Simple Exception class for Migration """


class MigrationReport:
    """ Change report

    Get a new report::

        report = MigrationReport(migrationinstance, change_detected)

    """

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
                elif name == 'add_fk':
                    _, fk = diff
                    for column in fk.columns:
                        for fk_ in column.foreign_keys:
                            log_names.append(
                                'Add Foreign keys on %s.%s => %s' % (
                                    fk.table.name, column.name,
                                    fk_.target_fullname))
                elif name == 'remove_fk':
                    _, fk = diff
                    for column in fk.columns:
                        for fk_ in column.foreign_keys:
                            log_names.append(
                                'Drop Foreign keys on %s.%s => %s' % (
                                    fk.table.name, column.name,
                                    fk_.target_fullname))
                elif name == 'add_constraint':
                    _, constraint = diff
                    columns = [x.name for x in constraint.columns]
                    log_names.append('Add unique constraint on %s (%s)' % (
                        constraint.table.name, ', '.join(columns)))
                elif name in ('remove_table', 'remove_column'):
                    # No save remove table or column
                    # Remove table or column is
                    continue
                else:
                    print(diff)

                self.actions.append(diff)

        for log_name in log_names:
            if log_name and not self.log_has(log_name):
                self.logs.append(log_name)

    def log_has(self, log):
        """ return True id the log is present

        .. warning:: this method is only used for the unittest

        :param log: log sentence expected
        """
        return log in self.logs

    def apply_change(self):
        """ Apply the migration

        this method parses the detected change and calls the Migration
        system to apply the change with the api of Declarations
        """
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
            elif action[0] == 'add_fk':
                _, fk = action
                t = self.migration.table(fk.table.name)
                for column in fk.columns:
                    for fk_ in column.foreign_keys:
                        t.column(name=column.name).foreign_key().add(
                            fk_.column)
            elif action[0] == 'remove_fk':
                _, fk = action
                t = self.migration.table(fk.table.name)
                for column in fk.columns:
                    t.column(name=column.name).foreign_key().drop()
            elif action[0] == 'add_constraint':
                _, constraint = action
                table = self.migration.table(constraint.table.name)
                table.unique(name=constraint.name).add(*constraint.columns)


class MigrationConstraintForeignKey:
    """ Used to apply a migration on a foreign key

    You can add::

        table.column('my column').foreign_key().add(Blok.name)

    Or drop::

        table.column('my column').foreign_key().drop()

    """
    def __init__(self, column):
        self.column = column
        self.name = self.format_name()

    def format_name(self, *columns):
        return '%s_%s_fkey' % (self.column.table.name, self.column.name)

    def add(self, remote_field, **kwargs):
        """ Add a new foreign key

        :param remote_field: The column of the remote model
        :rtype: MigrationConstraintForeignKey instance
        """
        if hasattr(remote_field, 'propery'):
            remote_field = remote_field.property.columns[0]

        remote_table = remote_field.table.name
        remote_column = remote_field.name
        self.column.table.migration.operation.create_foreign_key(
            self.name, self.column.table.name, remote_table,
            [self.column.name], [remote_column], **kwargs)
        return self

    def drop(self):
        """ Drop the foreign key """
        self.column.table.migration.operation.drop_constraint(
            self.name, self.column.table.name, type_='foreignkey')
        return self


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
                    conn, self.table.name)

            for c in columns:
                if c['name'] == name:
                    self.info.update(c)

            if not self.info:
                raise MigrationException(
                    "No column %r found on %r" % (name, self.table.name))

    def add(self, column):
        """ Add a new column

        The column is added in two phases, the last phase is only for the
        the nullable, if nullable can not be applied, a warning is logged

        :param column: sqlalchemy column
        :rtype: MigrationColumn instance
        """
        nullable = column.nullable
        if not nullable:
            column.nullable = True

        self.table.migration.operation.impl.add_column(self.table.name, column)
        if not nullable:
            c = MigrationColumn(self.table, column.name)
            c.alter(existing_type=column.type,
                    existing_server_default=column.server_default,
                    existing_autoincrement=column.autoincrement,
                    existing_nullable=True, nullable=False)

        t = self.table.migration.metadata.tables[self.table.name]
        for constraint in t.constraints:
            if not isinstance(constraint, schema.PrimaryKeyConstraint):
                if not isinstance(constraint, schema.ForeignKeyConstraint):
                    self.table.migration.operation.impl.add_constraint(
                        constraint)

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
        :param existing_type: Old sqlalchemy type
        :param server_default: The default value in database server
        :param existing_server_default: Old default value
        :param nullable: New nullable value
        :param existing_nullable: Old nullable value
        :param autoincrement: New auto increment use for Integer whith primary
            key only
        :param existing_autoincrement: Old auto increment
        :rtype: MigrationColumn instance
        """
        vals = {}
        name = self.name

        for k in ('existing_type', 'existing_server_default',
                  'existing_nullable', 'existing_autoincrement',
                  'autoincrement', 'server_default', 'type_'):
            if k in kwargs:
                vals[k] = kwargs[k]

        if 'name' in kwargs:
            vals['new_column_name'] = kwargs['name']
            name = kwargs['name']

        if vals:
            self.table.migration.operation.alter_column(
                self.table.name, self.name, **vals)

        if 'nullable' in kwargs:
            nullable = kwargs['nullable']
            savepoint = '%s_not_null' % name
            try:
                self.table.migration.savepoint(savepoint)
                self.table.migration.operation.alter_column(
                    self.table.name, self.name, nullable=nullable, **vals)
            except IntegrityError as e:
                self.table.migration.rollback_savepoint(savepoint)
                logger.warn(str(e))

        return MigrationColumn(self.table, name)

    def drop(self):
        """ Drop the column """
        self.table.migration.operation.drop_column(self.table.name, self.name)

    def nullable(self):
        """ Use for unittest return if the column is nullable """
        return self.info['nullable']

    def type(self):
        """ Use for unittest: return the column type """
        return self.info['type']

    def server_default(self):
        """ Use for unittest: return the default database value """
        return self.info['default']

    def foreign_key(self):
        """ Get a foreign key

        :rtype: MigrationConstraintForeignKey instance
        """
        return MigrationConstraintForeignKey(self)


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

    def add(self, name, condition):
        """ Add the constraint

        :param name: name of the constraint
        :param condition: constraint to apply
        :rtype: MigrationConstraintCheck instance
        """
        self.table.migration.operation.create_check_constraint(
            name, self.table.name, condition)

        return MigrationConstraintCheck(self.table, self.name)

    def drop(self):
        """ Drop the constraint """
        self.table.migration.operation.drop_constraint(
            self.name, self.table.name, type_='check')


class MigrationConstraintUnique:
    """ Used for the Unique constraint

    Add a new constraint::

        table('My table name').unique().add('col1', 'col2')

    Get and drop the constraint::

        table('My table name').unique('col1', 'col2').drop()

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
                uniques = op.impl.dialect.get_unique_constraints(
                    conn, self.table.name)

            for u in uniques:
                if u['name'] == self.name:
                    self.exist = True

            if not self.exist:
                raise MigrationException(
                    "No unique constraints %r found on %r" % (
                        self.name, self.table.name))

    def format_name(self, *columns):
        if columns:
            cols = [x.name for x in columns]
            cols.sort()
            cols = '_'.join(cols)
            return 'unique_%s_on_%s' % (cols, self.table.name)

        return None

    def add(self, *columns):
        """ Add the constraint

        :param \*column: list of column name
        :rtype: MigrationConstraintUnique instance
        :exception: MigrationException
        """
        if not columns:
            raise MigrationException("""To add an unique constraint you """
                                     """must define one or more columns""")

        unique_name = self.format_name(*columns)
        columns_name = [x.name for x in columns]
        self.table.migration.operation.create_unique_constraint(
            unique_name, self.table.name, columns_name)

        return MigrationConstraintUnique(self.table, *columns)

    def drop(self):
        """ Drop the constraint """
        self.table.migration.operation.drop_constraint(
            self.name, self.table.name, type_='unique')


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
        return '%s_pkey' % self.table.name

    def add(self, *columns):
        """ Add the constraint

        :param \*column: list of column name
        :rtype: MigrationConstraintPrimaryKey instance
        :exception: MigrationException
        """
        if not columns:
            raise MigrationException("""To add a primary key constraint """
                                     """you must define one or more columns""")

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
        """ Add the constraint

        :param \*column: list of column name
        :rtype: MigrationIndex instance
        :exception: MigrationException
        """
        if not columns:
            raise MigrationException(
                "To add an index you must define one or more columns")

        index_name = self.format_name(*columns)
        columns_name = [x.name for x in columns]
        self.table.migration.operation.create_index(
            index_name, self.table.name, columns_name)

        return MigrationIndex(self.table, *columns)

    def drop(self):
        """ Drop the constraint """
        self.table.migration.operation.drop_index(
            self.name, table_name=self.table.name)


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

    def __init__(self, migration, name):
        self.name = name
        self.migration = migration

        if name is not None:
            with cnx(self.migration) as conn:
                if not self.migration.operation.impl.dialect.has_table(conn,
                                                                       name):
                    raise MigrationException("No table %r found" % name)

    def add(self, name):
        """ Add a new table

        :param name: name of the table
        :rtype: MigrationTable instance
        """
        self.migration.operation.create_table(name)
        return MigrationTable(self.migration, name)

    def column(self, name=None):
        """ Get Column

        :param name: Column name
        :rtype: MigrationColumn instance
        """
        return MigrationColumn(self, name)

    def drop(self):
        """ Drop the table """
        self.migration.operation.drop_table(self.name)

    def index(self, *columns, **kwargs):
        """ Get index

        :param \*columns: List of the column's name
        :rtype: MigrationIndex instance
        """
        return MigrationIndex(self, *columns, **kwargs)

    def unique(self, *columns, **kwargs):
        """ Get unique

        :param \*columns: List of the column's name
        :rtype: MigrationConstraintUnique instance
        """
        return MigrationConstraintUnique(self, *columns, **kwargs)

    def check(self, name=None):
        """ Get check

        :param \*columns: List of the column's name
        :rtype: MigrationConstraintCheck instance
        """
        return MigrationConstraintCheck(self, name)

    def primarykey(self):
        """ Get primary key

        :param \*columns: List of the column's name
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
            raise MigrationException("Table can only alter name")

        name = kwargs['name']
        self.migration.operation.rename_table(self.name, name)
        return MigrationTable(self.migration, name)


class Migration:
    """ Migration Main entry

    This class allows to manipulate all the migration class::

        migration = Migration(Session(), Base.Metadata)
        t = migration.table('My table name')
        c = t.column('My column name from t')
    """

    def __init__(self, session, metadata):
        self.conn = session.connection()
        self.metadata = metadata

        opts = {
            'compare_type': True,
            'compare_server_default': True,
            'render_item': self.render_item,
            'compare_type': self.compare_type,
        }
        self.context = MigrationContext.configure(self.conn, opts=opts)
        self.operation = Operations(self.context)

    def table(self, name=None):
        """ Get a table

        :rtype: MigrationTable instance
        """
        return MigrationTable(self, name)

    def auto_upgrade_database(self):
        """ Upgrade the database automaticly """
        report = self.detect_changed()
        report.apply_change()

    def detect_changed(self):
        """ Detect the difference between the metadata and the database

        :rtype: MigrationReport instance
        """
        diff = compare_metadata(self.context, self.metadata)
        return MigrationReport(self, diff)

    def savepoint(self, name=None):
        """ Add a savepoint

        :param name: name of the save point
        :rtype: return the name of the save point
        """
        return self.conn._savepoint_impl(name=name)

    def rollback_savepoint(self, name):
        """ Rollback to the savepoint

        :param name: name of the savepoint
        """
        self.conn._rollback_to_savepoint_impl(name, None)

    def release_savepoint(self, name):
        """ Release the save point

        :param name: name of the savepoint
        """
        self.conn._release_savepoint_impl(name, None)

    def render_item(self, type_, obj, autogen_context):
        logger.debug("%r, %r, %r" % (type_, obj, autogen_context))
        return False

    def compare_type(self, context, inspected_column,
                     metadata_column, inspected_type, metadata_type):
        if hasattr(metadata_type, 'compare_type'):
            return metadata_type.compare_type(inspected_type)

        return None
