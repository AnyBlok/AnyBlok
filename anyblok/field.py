# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok import Declarations
from anyblok.environment import EnvironmentManager
from logging import getLogger
logger = getLogger(__name__)


@Declarations.register(Declarations.Exception)
class FieldException(Exception):
    """ Simple Exception for Field """


@Declarations.add_declaration_type()
class Field:
    """ Field class

    This class can't be instanciated
    """

    @classmethod
    def register(self, parent, name, cls_, **kwargs):
        """ add new sub registry in the registry

        :param parent: Parent to attach the declaration to
        :param name: Name of the new field
        :param cls_: Class to add in the declaration
        :exception: FieldException
        """
        _registryname = parent.__registry_name__ + '.' + name
        if hasattr(parent, name) and not EnvironmentManager.get('reload',
                                                                False):
            raise FieldException("The Field %r already exist" % _registryname)

        setattr(parent, name, cls_)
        logger.info("Add new type field : %r" % _registryname)

    @classmethod
    def unregister(self, child, cls_):
        """ Forbidden method

        :exception: FieldException
        """
        raise FieldException("Removing a field is forbidden")

    def __init__(self, *args, **kwargs):
        """ Initialize the field

        :param label: label of this field
        :type label: str
        """
        self.forbid_instance(Field)
        self.label = None

        if 'label' in kwargs:
            self.label = kwargs.pop('label')

        self.args = args
        self.kwargs = kwargs

    def forbid_instance(self, cls):
        """ Raise an exception if the cls is an instance of this __class__

        :param cls: instance of the class
        :exception: FieldException
        """
        if self.__class__ is cls:
            raise FieldException(
                "%r class must not be instanciated use a sub class" % cls)

    def update_properties(self, registry, namespace, fieldname, properties):
        """ Update the propertie use to add new column

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        :param properties: properties known to the model
        """

    def get_sqlalchemy_mapping(self, registry, namespace, fieldname,
                               properties):
        """ Return the instance of the real field

        :param registry: current registry
        :param namespace: name of the model
        :param fieldname: name of the field
        :param properties: properties known of the model
        :rtype: instance of Field
        """
        self.format_label(fieldname)
        return self

    def format_label(self, fieldname):
        """ Return the label for this field

        :param fieldname: if no label filled, the fieldname will be capitalized
            and returned
        :rtype: the label for this field
        """
        if not self.label:
            label = fieldname.replace('_', ' ')
            self.label = label.capitalize()

    def native_type(self):
        """ Return the native SqlAlchemy type

        :exception: FieldException
        """
        raise FieldException("No native type for this field")
