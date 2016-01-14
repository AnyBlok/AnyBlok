# -*- coding: utf-8 -*-
from sqlalchemy.exc import IntegrityError
from alembic.migration import MigrationContext
from alembic.autogenerate import compare_metadata
from alembic.operations import Operations
from sqlalchemy import schema
from contextlib import contextmanager
from sqlalchemy import func, select, update, join, alias, and_
from anyblok.config import Configuration
import re
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


class MigrationException(AttributeError):
    """ Simple Exception class for Migration """


class MigrationReport:
    """ Change report

    Get a new report::

        report = MigrationReport(migrationinstance, change_detected)

    """
    def raise_if_withoutautomigration(self):
        if self.migration.withoutautomigration:
            raise MigrationException("The metadata and the base structue are "
                                     "different, or this difference is "
                                     "forbidden in 'no auto migration' mode")

    def init_add_column(self, diff):
        self.raise_if_withoutautomigration()
        _, _, table, column = diff
        self.log_names.append('Add %s.%s' % (table, column.name))

    def check_if_table_and_columns_exist(self, table, *columns):
        try:  # check if the table and the column exist
            table = self.migration.table(table)
            for column in columns:
                table.column(column)
            return True
        except:
            return False

    def can_remove_constraints(self, name):
        unique = "anyblok_uq_(?P<table>\w+)__(?P<columns>\w+)"
        check = "anyblok_ck_(?P<table>\w+)_(?P<constraint>\w+)"

        m = re.search(unique, name)
        if m and self.check_if_table_and_columns_exist(m.group('table'),
                                                       m.group('columns')):
            return True

        m = re.search(check, name)
        if m and self.check_if_table_and_columns_exist(m.group('table')):
            return True

        if self.migration.reinit_constraints:
            return True

        if self.migration.reinit_all:
            return True

        return False

    def can_remove_fk_constraints(self, name):
        fk = ("anyblok_fk_(?P<table>\w+)__(?P<columns>\w+)_on_"
              "(?P<referred_table>\w+)__(?P<referred_columns>\w+)")
        m = re.search(fk, name)
        if m is not None:
            local = self.check_if_table_and_columns_exist(
                m.group('table'), m.group('columns'))
            referred = self.check_if_table_and_columns_exist(
                m.group('referred_table'), m.group('referred_columns'))
            if local and referred:
                return True

        if self.migration.reinit_constraints:
            return True

        if self.migration.reinit_all:
            return True

        return False

    def init_remove_constraint(self, diff):
        _, constraint = diff
        self.log_names.append('Drop constraint %s on %s' % (
            constraint.name, constraint.table))

        if self.can_remove_constraints(constraint.name):
            self.raise_if_withoutautomigration()
        else:
            return True

    def can_remove_index(self, name):
        key = "anyblok_ix_(?P<table>\w+)__(?P<columns>\w+)"
        m = re.search(key, name)
        if m and self.check_if_table_and_columns_exist(m.group('table'),
                                                       m.group('columns')):
            return True

        if self.migration.reinit_indexes:
            return True

        if self.migration.reinit_all:
            return True

        return False

    def init_remove_index(self, diff):
        _, index = diff
        self.log_names.append('Drop index %s on %s' % (index.name,
                                                       index.table))
        if self.can_remove_index(index.name):
            self.raise_if_withoutautomigration()
        else:
            return True

    def init_add_fk(self, diff):
        self.raise_if_withoutautomigration()
        _, fk = diff
        from_ = []
        to_ = []
        for column in fk.columns:
            for fk_ in column.foreign_keys:
                from_.append('%s.%s' % (fk.table.name, column.name))
                to_.append(fk_.target_fullname)

        self.log_names.append('Add Foreign keys on (%s) => (%s)' % (
            ', '.join(from_), ', '.join(to_)))

    def init_remove_fk(self, diff):
        _, fk = diff
        for column in fk.columns:
            for fk_ in column.foreign_keys:
                self.log_names.append('Drop Foreign keys on %s.%s => %s' % (
                    fk.table.name, column.name, fk_.target_fullname))

        if not self.can_remove_fk_constraints(fk.name):
            return True

        self.raise_if_withoutautomigration()

    def init_add_constraint(self, diff):
        self.raise_if_withoutautomigration()
        _, constraint = diff
        columns = [x.name for x in constraint.columns]
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
                if fk.name not in fk_removed:
                    self.actions.append(('remove_fk', fk.constraint))
                    fk_removed.append(fk.name)

        if column.nullable is False:
            self.raise_if_withoutautomigration()
            msg += " (not null)"
            self.log_names.append(msg)
            self.actions.append(
                ('modify_nullable', None, column.table.name,
                 column.name, {}, False, True))
            return True

        self.log_names.append(msg)
        return True

    def can_remove_table(self):
        if self.migration.reinit_tables:
            return True

        if self.migration.reinit_all:
            return True

        return False

    def init_remove_table(self, diff):
        self.log_names.append("Drop Table %s" % diff[1].name)
        if self.can_remove_table():
            self.raise_if_withoutautomigration()
        else:
            return True

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
        mappers = {
            'add_column': self.init_add_column,
            'remove_constraint': self.init_remove_constraint,
            'remove_index': self.init_remove_index,
            'add_fk': self.init_add_fk,
            'remove_fk': self.init_remove_fk,
            'add_constraint': self.init_add_constraint,
            'remove_column': self.init_remove_column,
            'remove_table': self.init_remove_table,
        }
        for diff in diffs:
            if isinstance(diff, list):
                self.raise_if_withoutautomigration()
                for change in diff:
                    _, _, table, column, _, _, _ = change
                    self.log_names.append('Alter %s.%s' % (table, column))
                    self.actions.append(change)
            else:
                fnct = mappers.get(diff[0])
                if fnct:
                    if fnct(diff):
                        continue
                else:
                    print(diff)

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

    def apply_change_add_column(self, action):
        _, _, table, column = action
        self.migration.table(table).column().add(column)

    def apply_change_modify_nullable(self, action):
        _, _, table, column, kwargs, oldvalue, newvalue = action
        self.migration.table(table).column(column).alter(
            nullable=newvalue, existing_nullable=oldvalue, **kwargs)

    def apply_change_modify_type(self, action):
        _, _, table, column, kwargs, oldvalue, newvalue = action
        self.migration.table(table).column(column).alter(
            type_=newvalue, existing_type=oldvalue, **kwargs)

    def apply_change_modify_default(self, action):
        _, _, table, column, kwargs, oldvalue, newvalue = action
        self.migration.table(table).column(column).alter(
            server_default=newvalue, existing_server_default=oldvalue,
            **kwargs)

    def apply_change_remove_constraint(self, action):
        # FIXME, test for check, foreignkey
        _, constraint = action
        if constraint.__class__ is schema.UniqueConstraint:
            table = self.migration.table(constraint.table)
            table.unique(name=constraint.name).drop()

    def apply_change_remove_index(self, action):
        _, index = action
        if not index.unique:
            table = self.migration.table(index.table.name)
            table.index(name=index.name).drop()

    def apply_change_add_fk(self, action):
        _, fk = action
        t = self.migration.table(fk.table.name)
        from_ = []
        to_ = []
        for column in fk.columns:
            for fk_ in column.foreign_keys:
                from_.append(column.name)
                to_.append(fk_.column)

        name = 'fk_%s' % '_'.join(from_)
        t.foreign_key(name).add(from_, to_)

    def apply_change_remove_fk(self, action):
        _, fk = action
        t = self.migration.table(fk.table.name)
        t.foreign_key(fk.name).drop()

    def apply_change_add_constraint(self, action):
        _, constraint = action
        table = self.migration.table(constraint.table.name)
        # FIXME, test for check, foreignkey
        table.unique(name=constraint.name).add(*constraint.columns)

    def apply_remove_table(self, action):
        self.migration.table(action[1].name).drop()

    def apply_remove_column(self, action):
        self.migration.table(action[2]).column(action[3].name).drop()

    def apply_change(self):
        """ Apply the migration

        this method parses the detected change and calls the Migration
        system to apply the change with the api of Declarations
        """
        for log in self.logs:
            logger.info(log)

        mappers = {
            'add_column': self.apply_change_add_column,
            'modify_nullable': self.apply_change_modify_nullable,
            'modify_type': self.apply_change_modify_type,
            'modify_default': self.apply_change_modify_default,
            'add_fk': self.apply_change_add_fk,
            'add_constraint': self.apply_change_add_constraint,
            'remove_constraint': self.apply_change_remove_constraint,
            'remove_index': self.apply_change_remove_index,
            'remove_fk': self.apply_change_remove_fk,
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
            raise MigrationException("Remote column must have the same table "
                                     "(%s)" % ', '.join(remote_table))

        remote_table = remote_table.pop()
        remote_columns = [x.name for x in remote_columns]
        self.table.migration.operation.create_foreign_key(
            self.name, self.table.name, remote_table,
            local_columns, remote_columns, **kwargs)
        return self

    def drop(self):
        """ Drop the foreign key """
        self.table.migration.operation.drop_constraint(
            self.name, self.table.name, type_='foreignkey')
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

    def apply_default_value(self, column):
        if column.default:
            execute = self.table.migration.conn.execute
            val = column.default.arg
            table = self.table.migration.metadata.tables[self.table.name]
            table.append_column(column)
            cname = getattr(table.c, column.name)
            if column.default.is_callable:
                table2 = alias(select([table]).limit(1).where(cname.is_(None)))
                Table = self.table.migration.metadata.tables['system_model']
                Column = self.table.migration.metadata.tables['system_column']
                j1 = join(Table, Column, Table.c.name == Column.c.model)
                query = select([func.count()]).select_from(table)
                nb_row = self.table.migration.conn.execute(query).fetchone()[0]
                query = select([Column.c.name]).select_from(j1)
                query = query.where(Column.c.primary_key.is_(True))
                query = query.where(Table.c.table == self.table.name)
                columns = [x[0] for x in execute(query).fetchall()]
                where = and_(*[getattr(table.c, x) == getattr(table2.c, x)
                               for x in columns])
                for offset in range(nb_row):
                    # call for each row because the default value
                    # could be a sequence or depend of other field
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
        nullable = column.nullable
        if not nullable:
            column.nullable = True

        self.table.migration.operation.impl.add_column(self.table.name, column)
        self.apply_default_value(column)

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

        # TODO get the default value of the column and apply it on null value

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
            self.name, self.table.name, condition)

        return self

    def drop(self):
        """ Drop the constraint """
        self.table.migration.operation.drop_constraint(
            self.name, self.table.name, type_='check')


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

        :param \*column: list of column name
        :rtype: MigrationConstraintUnique instance
        :exception: MigrationException
        """
        if not columns:
            raise MigrationException("""To add an unique constraint you """
                                     """must define one or more columns""")

        columns_name = [x.name for x in columns]
        savepoint = 'add_unique_constraint_%s' % (self.name or '')
        try:
            self.table.migration.savepoint(savepoint)
            self.table.migration.operation.create_unique_constraint(
                self.name, self.table.name, columns_name)
        except IntegrityError as e:
            self.table.migration.rollback_savepoint(savepoint)
            logger.warn("Error during the add of new unique constraint %r on "
                        "table %r and columns %r : %r " % (self.name,
                                                           self.table.name,
                                                           columns_name,
                                                           str(e)))

        return self

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
        return 'anyblok_pk_%s' % self.table.name

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

    def unique(self, name):
        """ Get unique

        :param \*columns: List of the column's name
        :rtype: MigrationConstraintUnique instance
        """
        return MigrationConstraintUnique(self, name)

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

    def foreign_key(self, name):
        """ Get a foreign key

        :rtype: MigrationConstraintForeignKey instance
        """
        return MigrationConstraintForeignKey(self, name)


class Migration:
    """ Migration Main entry

    This class allows to manipulate all the migration class::

        migration = Migration(Session(), Base.Metadata)
        t = migration.table('My table name')
        c = t.column('My column name from t')
    """

    def __init__(self, registry):
        self.withoutautomigration = registry.withoutautomigration
        self.conn = registry.session.connection()
        self.metadata = registry.declarativebase.metadata

        opts = {
            'compare_type': True,
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
