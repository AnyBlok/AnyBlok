# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations


FieldException = Declarations.Exception.FieldException


@Declarations.register(Declarations.RelationShip)
class One2Many(Declarations.RelationShip):
    """ Define a relationship attribute on the model

    ::

        @register(Model)
        class TheModel:

            relationship = One2Many(label="The relationship",
                                    model=Model.RemoteModel,
                                    remote_column="The remote column",
                                    primaryjoin="Join condition"
                                    many2one="themodel")

    If the primaryjoin is not filled then the join condition is
        "'local table'.'local promary key' == 'remote table'.'remote colum'"

    :param model: the remote model
    :param remote_column: the column name on the remote model
    :param primaryjoin: the join condition between the remote column
    :param many2one: create the many2one link with this one2many
    """
    def __init__(self, **kwargs):
        super(One2Many, self).__init__(**kwargs)

        self.remote_column = None
        if 'remote_column' in kwargs:
            self.remote_column = self.kwargs.pop('remote_column')

        if 'many2one' in kwargs:
            self.kwargs['backref'] = self.kwargs.pop('many2one')
            self.kwargs['info']['remote_name'] = self.kwargs['backref']

    def find_foreign_key(self, properties, tablename):
        """ Return the primary key come from the first step property

        :param properties: first step properties for the model
        :param tablename: the name of the table for the foreign key
        :rtype: column name of the primary key
        """
        fks = []
        for f, p in properties.items():
            if f == '__tablename__':
                continue
            if p.foreign_key and p.foreign_key.split('.')[0] == tablename:
                fks.append(f)

        if len(fks) != 1:
            raise FieldException(
                "We must have one and only one foreign key")

        return fks[0]

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
        self_properties = registry.loaded_namespaces_first_step.get(namespace)

        tablename = properties['__tablename__']
        if self.remote_column is None:
            self.remote_column = self.find_foreign_key(remote_properties,
                                                       tablename)

        self.kwargs['info']['remote_column'] = self.remote_column

        if 'primaryjoin' not in self.kwargs:
            local_column = self.find_primary_key(self_properties)

            primaryjoin = tablename + '.' + local_column + " == "
            primaryjoin += self.get_tablename(registry)
            primaryjoin += '.' + self.remote_column
            self.kwargs['primaryjoin'] = primaryjoin

        return super(One2Many, self).get_sqlalchemy_mapping(
            registry, namespace, fieldname, properties)
