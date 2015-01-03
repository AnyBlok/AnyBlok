# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from sqlalchemy import Table, Column, ForeignKey
from anyblok import Declarations


FieldException = Declarations.Exception.FieldException


@Declarations.register(Declarations.RelationShip)
class Many2Many(Declarations.RelationShip):
    """ Define a relationship attribute on the model

    ::

        @register(Model)
        class TheModel:

            relationship = Many2Many(label="The relationship",
                                     model=Model.RemoteModel,
                                     join_table="many2many table",
                                     remote_column="The remote column",
                                     m2m_remote_column="Name in many2many"
                                     local_column="local primary key"
                                     m2m_local_column="Name in many2many"
                                     many2many="themodels")

    if the join_table is not defined, then the table join is
        "join_'local table'_and_'remote table'"

    If the remote_column are not define then, the system take the primary key
    of the remote model

    if the local_column are not define the take the primary key of the local
        model

    :param model: the remote model
    :param join_table: the many2many table to join local and remote models
    :param remote_column: the column name on the remote model
    :param m2m_remote_column: the column name to remote model in m2m table
    :param local_column: the column on the model
    :param m2m_local_column: the column name to local model in m2m table
    :param many2many: create the opposite many2many on the remote model
    """

    def __init__(self, **kwargs):
        super(Many2Many, self).__init__(**kwargs)

        self.join_table = None
        if 'join_table' in kwargs:
            self.join_table = self.kwargs.pop('join_table')

        self.remote_column = None
        if 'remote_column' in kwargs:
            self.remote_column = self.kwargs.pop('remote_column')
            self.kwargs['info']['remote_column'] = self.remote_column

        self.m2m_remote_column = None
        if 'm2m_remote_column' in kwargs:
            self.m2m_remote_column = self.kwargs.pop('m2m_remote_column')

        self.local_column = None
        if 'local_column' in kwargs:
            self.local_column = self.kwargs.pop('local_column')
            self.kwargs['info']['local_column'] = self.local_column

        self.m2m_local_column = None
        if 'm2m_local_column' in kwargs:
            self.m2m_local_column = self.kwargs.pop('m2m_local_column')

        if 'many2many' in kwargs:
            self.kwargs['backref'] = self.kwargs.pop('many2many')
            self.kwargs['info']['remote_name'] = self.kwargs['backref']

    def get_m2m_column_info(self, tablename, properties, column, m2m_column):
        if column is None:
            column = self.find_primary_key(properties)
        elif column not in properties:
            raise FieldException("%r does not exist in %r" % (column,
                                                              tablename))

        if m2m_column is None:
            m2m_column = '%s_%s' % (tablename, column)

        foreignkey = '%s.%s' % (tablename, column)

        return m2m_column, properties[column].native_type(), foreignkey

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
        if self.join_table is None:
            self.join_table = 'join_%s_and_%s' % (local_tablename,
                                                  remote_tablename)

        if self.join_table not in registry.declarativebase.metadata.tables:
            rname, rtype, rfk = self.get_m2m_column_info(
                remote_tablename, remote_properties, self.remote_column,
                self.m2m_remote_column)

            lname, ltype, lfk = self.get_m2m_column_info(
                local_tablename, local_properties, self.local_column,
                self.m2m_local_column)

            Table(self.join_table, registry.declarativebase.metadata,
                  Column(lname, ltype, ForeignKey(lfk)),
                  Column(rname, rtype, ForeignKey(rfk)))

        self.kwargs['secondary'] = self.join_table

        return super(Many2Many, self).get_sqlalchemy_mapping(
            registry, namespace, fieldname, properties)
