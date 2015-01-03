# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from sqlalchemy.orm import relationship


FieldException = Declarations.Exception.FieldException


@Declarations.add_declaration_type()
class RelationShip(Declarations.Field):
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

    def get_registry_name(self):
        """ Return the registry name of the remote model

        :rtype: str of the registry name
        """
        if isinstance(self.model, str):
            return self.model
        else:
            return self.model.__registry_name__

    def get_tablename(self, registry):
        """ Return the table name of the remote model

        :rtype: str of the table name
        """
        if isinstance(self.model, str):
            model = registry.loaded_namespaces_first_step[self.model]
            return model['__tablename__']
        else:
            return self.model.__tablename__

    def apply_instrumentedlist(self, registry):
        self.kwargs['collection_class'] = registry.InstrumentedList
        backref = self.kwargs.get('backref')
        if not backref:
            return

        if not isinstance(backref, (list, tuple)):
            backref = (backref, {})

        backref[1]['collection_class'] = registry.InstrumentedList
        self.kwargs['backref'] = backref

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

        if len(pks) != 1:
            raise FieldException(
                "We must have one and only one primary key")

        return pks[0]

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
        return relationship(self.get_tablename(registry), **self.kwargs)
