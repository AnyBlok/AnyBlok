# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref


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
        self.format_backref(registry, namespace, properties)
        return relationship(self.get_tablename(registry), **self.kwargs)

    def must_be_declared_as_attr(self):
        """ Return True, because it is a relationship """
        return True
