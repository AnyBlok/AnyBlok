# -*- coding: utf-8 -*-
import AnyBlok
from AnyBlok.Interface import ICoreInterface
from AnyBlok import target_registry, add_Adapter
from sys import modules
from zope.interface import implementer
from logging import getLogger
logger = getLogger(__name__)


class FieldException(Exception):
    """ Simple Exception for Field Adapter """


@implementer(ICoreInterface)
class AField:
    """ Adapter to Field Class

    The Field class are used to define type of AnyBlok field

    Add new field type::

        @target_registry(Field)
        class Function:
            pass

    the remove field are forbidden because the model can be used on the model
    """

    __interface__ = 'Field'

    def target_registry(self, registry, child, cls_, **kwargs):
        """ add new sub registry in the registry and add it in the
        sys.modules

        :param registry: Existing global registry
        :param child: Name of the new registry to add it
        :param cls_: Class Interface to add in registry
        """
        _registryname = registry.__registry_name__ + '.' + child
        if hasattr(registry, child):
            raise FieldException("The Field %r already exist" % _registryname)

        setattr(cls_, '__registry_name__', _registryname)
        setattr(cls_, '__interface__', self.__interface__)
        setattr(registry, child, cls_)
        modules[_registryname] = cls_
        logger.info("Add new type field : %r" % _registryname)

    def remove_registry(self, registry, child, cls_, **kwargs):
        """ Forbidden method """
        raise FieldException("Remove a field is forbiden")


add_Adapter(ICoreInterface, AField)


@target_registry(AnyBlok)
class Field:
    """ Field class

    This class can't be instancied
    """

    def __init__(self, label=None):
        """ Initialise the field

        :param label: label of this field
        :type label: str
        """
        self.MustNotBeInstanced(Field)
        if label is None:
            raise FieldException("Label argument are required")
        self.label = label

    def MustNotBeInstanced(self, cls):
        """ Raise an exception if the cls is an instance of this __class__

        :param cls: instance of the class
        """
        if self.__class__ is cls:
            raise FieldException(
                "%r class must not be instanced use a sub class" % cls)

    def get_sqlalchemy_mapping(self, registry, tablename, properties):
        """ Return the instance of the real field

        :param registry: current registry
        :param tablename: table name of the model
        :param properties: properties known of the model
        """
        return self
