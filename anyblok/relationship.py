# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2015 Pierre Verkest <pverkest@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy import Table, Column, ForeignKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref
from sqlalchemy.schema import Column as SA_Column
from sqlalchemy.ext.declarative import declared_attr
from .field import Field, FieldException


class RelationShip(Field):
    """ RelationShip class

    The RelationShip class is used to define the type of SQL field Declarations

    Add a new relation ship type::

        @Declarations.register(Declarations.RelationShip)
        class Many2one:
            pass

    the relationship column are forbidden because the model can be used on
    the model
    """

    def __init__(self, *args, **kwargs):
        self.forbid_instance(RelationShip)
        if 'model' in kwargs:
            self.model = kwargs.pop('model')
        else:
            raise FieldException("model is required attribut")

        super(RelationShip, self).__init__(*args, **kwargs)

        if 'info' not in self.kwargs:
            self.kwargs['info'] = {}

        self.kwargs['info']['remote_model'] = self.get_registry_name()
        self.backref_properties = {}

    def get_registry_name(self):
        """ Return the registry name of the remote model

        :rtype: str of the registry name
        """
        if isinstance(self.model, str):
            return self.model
        else:
            return self.model.__registry_name__

    def get_tablename(self, registry, model=None):
        """ Return the table name of the remote model

        :rtype: str of the table name
        """
        if model is None:
            model = self.model

        if isinstance(model, str):
            model = registry.loaded_namespaces_first_step[model]
            return model['__tablename__']
        else:
            return model.__tablename__

    def apply_instrumentedlist(self, registry):
        """ Add the InstrumentedList class to replace List class as result
        of the query

        :param registry: current registry
        """
        self.kwargs['collection_class'] = registry.InstrumentedList
        self.backref_properties['collection_class'] = registry.InstrumentedList

    def define_backref_properties(self, registry, namespace, properties):
        """ Add in the backref_properties, new property for the backref

        :param registry: current registry
        :param namespace: name of the model
        :param properties: properties known of the model
        """
        pass

    def format_backref(self, registry, namespace, properties):
        """ Create the real backref, with the backref string and the
        backref properties

        :param registry: current registry
        :param namespace: name of the model
        :param properties: properties known of the model
        """
        _backref = self.kwargs.get('backref')
        if not _backref:
            return

        if isinstance(_backref, (list, tuple)):
            _backref, backref_properties = _backref
            self.backref_properties.update(backref_properties)

        self.define_backref_properties(registry, namespace, properties)

        if self.backref_properties:
            self.kwargs['backref'] = backref(_backref,
                                             **self.backref_properties)

    def find_primary_key(self, properties):
        """ Return the primary key come from the first step property

        :param properties: first step properties for the model
        :rtype: column name of the primary key
        :exception: FieldException
        """
        pks = []
        for f, p in properties.items():
            if f == '__tablename__':
                continue
            if 'primary_key' in p.kwargs:
                pks.append(f)

        return pks

    def check_existing_remote_model(self, registry):
        """ Check if the remote model exists

        The information of the existance come from the first step of
        assembling

        :exception: FieldException if the model doesn't exist
        """
        remote_model = self.get_registry_name()
        if remote_model not in registry.loaded_namespaces_first_step:
            raise FieldException(
                "Remote model %r doesn't exist" % remote_model)

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """ Return the instance of the real field

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        :param properties: properties known of the model
        :rtype: sqlalchemy relation ship instance
        """
        self.check_existing_remote_model(registry)
        self.format_label(fieldname)
        self.kwargs['info']['label'] = self.label
        self.kwargs['info']['rtype'] = self.__class__.__name__
        self.apply_instrumentedlist(registry)
        self.format_backref(registry, namespace, properties)
        return relationship(self.get_tablename(registry), **self.kwargs)

    def must_be_declared_as_attr(self):
        """ Return True, because it is a relationship """
        return True


class Many2One(RelationShip):
    """ Define a relationship attribute on the model

    ::

        @register(Model)
        class TheModel:

            relationship = Many2One(label="The relationship",
                                    model=Model.RemoteModel,
                                    remote_columns="The remote column",
                                    column_names="The column which have the "
                                                "foreigh key",
                                    nullable=True,
                                    unique=False,
                                    one2many="themodels")

    If the ``remote_columns`` are not define then, the system takes the primary
    key of the remote model

    If the column doesn't exist, the column will be created. Use the
    nullable option.
    If the name is not filled, the name is "'remote table'_'remote colum'"

    :param model: the remote model
    :param remote_columns: the column name on the remote model
    :param column_names: the column on the model which have the foreign key
    :param nullable: If the column_names is nullable
    :param unique: If True, add the unique constraint on the column
    :param one2many: create the one2many link with this many2one
    """

    def __init__(self, **kwargs):
        super(Many2One, self).__init__(**kwargs)

        self.remote_columns = None
        if 'remote_columns' in kwargs:
            self.remote_columns = self.kwargs.pop('remote_columns')
            if not isinstance(self.remote_columns, (list, tuple)):
                self.remote_columns = [self.remote_columns]

        self.nullable = True
        if 'nullable' in kwargs:
            self.nullable = self.kwargs.pop('nullable')
            self.kwargs['info']['nullable'] = self.nullable

        self.unique = False
        if 'unique' in kwargs:
            self.unique = self.kwargs.pop('unique')
            self.kwargs['info']['unique'] = self.unique

        if 'one2many' in kwargs:
            self.kwargs['backref'] = self.kwargs.pop('one2many')
            self.kwargs['info']['remote_name'] = self.kwargs['backref']

        self.column_names = None
        if 'column_names' in kwargs:
            self.column_names = self.kwargs.pop('column_names')
            if not isinstance(self.column_names, (list, tuple)):
                self.column_names = [self.column_names]

    def find_foreign_key(self, registry, namespace, fieldname, properties):
        """Find and return the field name with a foreign key to the remote
        model, if no exist, the generate the fieldname with remote primary keys

        :param registry: the registry which load the relationship
        :param namespace: the name space of the model
        :param fieldname: fieldname of the relationship
        :param propertie: the properties known
        """
        remote_model = self.get_registry_name()
        remote_table = self.get_tablename(registry)
        cnames = []
        for cname in properties['loaded_columns']:
            col = properties[cname]
            if hasattr(col, 'anyblok_field'):
                if hasattr(col.anyblok_field, 'foreign_key'):
                    rn = col.anyblok_field.foreign_key[0]
                    if not isinstance(rn, str):
                        rn = rn.__registry_name__

                    if rn != remote_model:
                        continue

                    cnames.append(cname)

        if not cnames:
            cnames = ["%s_%s" % (remote_table, x) for x in self.remote_columns]

        self.column_names = cnames

    def update_properties(self, registry, namespace, fieldname, properties):
        """ Create the column which has the foreign key if the column doesn't
        exist

        :param registry: the registry which load the relationship
        :param namespace: the name space of the model
        :param fieldname: fieldname of the relationship
        :param propertie: the properties known
        """
        add_fksc = False
        self.check_existing_remote_model(registry)
        remote_table = self.get_tablename(registry)
        remote_properties = registry.loaded_namespaces_first_step.get(
            self.get_registry_name())

        if self.remote_columns is None:
            self.remote_columns = self.find_primary_key(remote_properties)

        self.kwargs['info']['remote_columns'] = self.remote_columns

        if self.column_names is None:
            self.find_foreign_key(registry, namespace, fieldname, properties)

        if fieldname in self.column_names:
            raise FieldException("The column_names and the fieldname %r are "
                                 "the same, please choose another "
                                 "column_names" % fieldname)

        self.kwargs['info']['local_columns'] = ', '.join(self.column_names)
        remote_types = {x: remote_properties[x].native_type()
                        for x in self.remote_columns}

        self_properties = registry.loaded_namespaces_first_step.get(namespace)
        for cname in self.column_names:
            if cname in self_properties:
                del remote_types[self_properties[cname].foreign_key[1]]

        col_names = []
        ref_cols = []
        for cname in self.column_names:
            if cname not in self_properties:
                if len(remote_types) == 1:
                    rc, remote_type = list(remote_types.items())[0]
                    foreign_key = '%s.%s' % (remote_table, rc)
                else:
                    rc = cname[len(remote_table) + 1:]
                    if rc in remote_types:
                        remote_type = remote_types[rc]
                        foreign_key = '%s.%s' % (remote_table, rc)
                    else:
                        raise FieldException("Can not create the local "
                                             "column %r" % cname)

                add_fksc = True
                self.create_column(cname, remote_type, foreign_key, properties)
                col_names.append(cname)
                ref_cols.append(foreign_key)
            else:
                col_names.append(cname)
                foreign_key = properties[cname].anyblok_field.foreign_key
                foreign_key = '%s.%s' % (foreign_key[0].__tablename__,
                                         foreign_key[1])
                ref_cols.append(foreign_key)

        if namespace == self.get_registry_name():
            self.kwargs['remote_side'] = [properties[x]
                                          for x in self.remote_columns]

        if (len(self.column_names) > 1 or add_fksc) and col_names and ref_cols:
            properties['add_in_table_args'].append(
                ForeignKeyConstraint(col_names, ref_cols))

    def create_column(self, cname, remote_type, foreign_key, properties):

        def wrapper(cls):
            return SA_Column(
                remote_type,
                nullable=self.nullable,
                unique=self.unique,
                info=dict(label=self.label, foreign_key=foreign_key))

        properties[cname] = declared_attr(wrapper)

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """ Create the relationship

        :param registry: the registry which load the relationship
        :param namespace: the name space of the model
        :param fieldname: fieldname of the relationship
        :param propertie: the properties known
        :rtype: Many2One relationship
        """
        fks = ["%s.%s" % (properties['__tablename__'], x)
               for x in self.column_names]
        fks = '[%s]' % ', '.join(fks)
        self.kwargs['foreign_keys'] = fks

        return super(Many2One, self).get_sqlalchemy_mapping(
            registry, namespace, fieldname, properties)


class One2One(Many2One):
    """ Define a relationship attribute on the model

    ::

        @register(Model)
        class TheModel:

            relationship = One2One(label="The relationship",
                                   model=Model.RemoteModel,
                                   remote_columns="The remote column",
                                   column_names="The column which have the "
                                               "foreigh key",
                                   nullable=False,
                                   backref="themodels")

    If the remote_columns are not define then, the system take the primary key
    of the remote model

    If the column doesn't exist, then the column will be create. Use the
    nullable option.
    If the name is not filled then the name is "'remote table'_'remote colum'"

    :param model: the remote model
    :param remote_columns: the column name on the remote model
    :param column_names: the column on the model which have the foreign key
    :param nullable: If the column_names is nullable
    :param backref: create the one2one link with this one2one
    """

    def __init__(self, **kwargs):
        super(One2One, self).__init__(**kwargs)

        if 'backref' not in kwargs:
            raise FieldException("backref is a required argument")

        if 'one2many' in kwargs:
            raise FieldException("Unknow argmument 'one2many'")

        self.kwargs['info']['remote_name'] = self.kwargs['backref']

    def define_backref_properties(self, registry, namespace, properties):
        """ Add option uselist = False

        :param registry: the registry which load the relationship
        :param namespace: the name space of the model
        :param propertie: the properties known
        """
        self.backref_properties.update({'uselist': False})


class Many2Many(RelationShip):
    """ Define a relationship attribute on the model

    ::

        @register(Model)
        class TheModel:

            relationship = Many2Many(label="The relationship",
                                     model=Model.RemoteModel,
                                     join_table="many2many table",
                                     remote_columns="The remote column",
                                     m2m_remote_columns="Name in many2many"
                                     local_columns="local primary key"
                                     m2m_local_columns="Name in many2many"
                                     many2many="themodels")

    if the join_table is not defined, then the table join is
        "join\_'local table'_and\_'remote table'"

    .. warning::

        The join_table must be filled when the declaration of the
        Many2Many is done in a Mixin

    If the remote_columns are not define then, the system take the primary key
    of the remote model

    if the local_columns are not define the take the primary key of the local
        model

    :param model: the remote model
    :param join_table: the many2many table to join local and remote models
    :param remote_columns: the column name on the remote model
    :param m2m_remote_columns: the column name to remote model in m2m table
    :param local_columns: the column on the model
    :param m2m_local_columns: the column name to local model in m2m table
    :param many2many: create the opposite many2many on the remote model
    """

    def __init__(self, **kwargs):
        super(Many2Many, self).__init__(**kwargs)

        self.join_table = None
        if 'join_table' in kwargs:
            self.join_table = self.kwargs.pop('join_table')

        self.remote_columns = None
        if 'remote_columns' in kwargs:
            self.remote_columns = self.kwargs.pop('remote_columns')
            if not isinstance(self.remote_columns, (list, tuple)):
                self.remote_columns = [self.remote_columns]

            self.kwargs['info']['remote_columns'] = self.remote_columns

        self.m2m_remote_columns = None
        if 'm2m_remote_columns' in kwargs:
            self.m2m_remote_columns = self.kwargs.pop('m2m_remote_columns')
            if not isinstance(self.m2m_remote_columns, (list, tuple)):
                self.m2m_remote_columns = [self.m2m_remote_columns]

        self.local_columns = None
        if 'local_columns' in kwargs:
            self.local_columns = self.kwargs.pop('local_columns')
            if not isinstance(self.local_columns, (list, tuple)):
                self.local_columns = [self.local_columns]

            self.kwargs['info']['local_columns'] = self.local_columns

        self.m2m_local_columns = None
        if 'm2m_local_columns' in kwargs:
            self.m2m_local_columns = self.kwargs.pop('m2m_local_columns')
            if not isinstance(self.m2m_local_columns, (list, tuple)):
                self.m2m_local_columns = [self.m2m_local_columns]

        if 'many2many' in kwargs:
            self.kwargs['backref'] = self.kwargs.pop('many2many')
            self.kwargs['info']['remote_name'] = self.kwargs['backref']

    def get_m2m_columns(self, tablename, properties, columns, m2m_columns):
        if not columns:
            columns = self.find_primary_key(properties)
        else:
            for column in columns:
                if column not in properties:
                    raise FieldException(
                        "%r does not exist in %r" % (column, tablename))

        if m2m_columns is None:
            m2m_columns = ['%s_%s' % (tablename, column) for column in columns]

        cols = []
        col_names = []
        ref_cols = []
        for i, column in enumerate(m2m_columns):
            sqltype = properties[columns[i]].native_type()
            foreignkey = "%s.%s" % (tablename, columns[i])
            cols.append(Column(column, sqltype, primary_key=True))
            col_names.append(column)
            ref_cols.append(foreignkey)

        return cols, ForeignKeyConstraint(col_names, ref_cols)

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """ Create the relationship

        :param registry: the registry which load the relationship
        :param namespace: the name space of the model
        :param fieldname: fieldname of the relationship
        :param properties: the properties known
        :rtype: Many2One relationship
        """
        self.check_existing_remote_model(registry)
        remote_properties = registry.loaded_namespaces_first_step.get(
            self.get_registry_name())
        local_properties = registry.loaded_namespaces_first_step.get(namespace)

        local_tablename = properties['__tablename__']
        remote_tablename = self.get_tablename(registry)
        join_table = self.join_table
        if self.join_table is None:
            join_table = 'join_%s_and_%s' % (local_tablename, remote_tablename)

        if join_table not in registry.declarativebase.metadata.tables:
            remote_columns, remote_fk = self.get_m2m_columns(
                remote_tablename, remote_properties, self.remote_columns,
                self.m2m_remote_columns)
            local_columns, local_fk = self.get_m2m_columns(
                local_tablename, local_properties, self.local_columns,
                self.m2m_local_columns)

            Table(join_table, registry.declarativebase.metadata, *(
                local_columns + remote_columns + [local_fk, remote_fk]))

        self.kwargs['secondary'] = join_table

        return super(Many2Many, self).get_sqlalchemy_mapping(
            registry, namespace, fieldname, properties)


class One2Many(RelationShip):
    """ Define a relationship attribute on the model

    ::

        @register(Model)
        class TheModel:

            relationship = One2Many(label="The relationship",
                                    model=Model.RemoteModel,
                                    remote_columns="The remote column",
                                    primaryjoin="Join condition"
                                    many2one="themodel")

    If the primaryjoin is not filled then the join condition is
        "'local table'.'local promary key' == 'remote table'.'remote colum'"

    :param model: the remote model
    :param remote_columns: the column name on the remote model
    :param primaryjoin: the join condition between the remote column
    :param many2one: create the many2one link with this one2many
    """
    def __init__(self, **kwargs):
        super(One2Many, self).__init__(**kwargs)

        self.remote_columns = None
        if 'remote_columns' in kwargs:
            self.remote_columns = self.kwargs.pop('remote_columns')
            if not isinstance(self.remote_columns, (list, tuple)):
                self.remote_columns = [self.remote_columns]

        if 'many2one' in kwargs:
            self.kwargs['backref'] = self.kwargs.pop('many2one')
            self.kwargs['info']['remote_names'] = self.kwargs['backref']

    def find_foreign_key(self, registry, properties, tablename):
        """ Return the primary key come from the first step property

        :param registry: the registry which load the relationship
        :param properties: first step properties for the model
        :param tablename: the name of the table for the foreign key
        :rtype: column name of the primary key
        """
        fks = []
        for f, p in properties.items():
            if f == '__tablename__':
                continue

            if not hasattr(p, 'foreign_key'):
                continue

            if p.foreign_key:
                model, _ = p.foreign_key
                if self.get_tablename(registry, model=model) == tablename:
                    fks.append(f)

        return fks

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """ Create the relationship

        :param registry: the registry which load the relationship
        :param namespace: the name space of the model
        :param fieldname: fieldname of the relationship
        :param propertie: the properties known
        :rtype: Many2One relationship
        """
        self.check_existing_remote_model(registry)
        remote_properties = registry.loaded_namespaces_first_step.get(
            self.get_registry_name())

        tablename = properties['__tablename__']
        if self.remote_columns is None:
            self.remote_columns = self.find_foreign_key(registry,
                                                        remote_properties,
                                                        tablename)

        self.kwargs['info']['remote_columns'] = self.remote_columns

        if 'primaryjoin' not in self.kwargs:
            remote_table = self.get_tablename(registry)
            pjs = []
            for cname in self.remote_columns:
                col = remote_properties[cname]
                pjs.append("%s.%s == %s.%s" % (
                    tablename, col.foreign_key[1], remote_table, cname))

            # This must be a python and not a SQL AND cause of eval do
            # on the primaryjoin
            self.kwargs['primaryjoin'] = ' and '.join(pjs)

        return super(One2Many, self).get_sqlalchemy_mapping(
            registry, namespace, fieldname, properties)

    def define_backref_properties(self, registry, namespace, properties):
        """ Add option in the backref if both model and remote model are the
        same, it is for the One2Many on the same model

        :param registry: the registry which load the relationship
        :param namespace: the name space of the model
        :param propertie: the properties known
        """
        if namespace == self.get_registry_name():
            self_properties = registry.loaded_namespaces_first_step.get(
                namespace)
            pks = self.find_primary_key(self_properties)
            self.backref_properties.update({'remote_side': [
                properties[pk] for pk in pks]})
