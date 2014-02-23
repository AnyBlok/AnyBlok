# -*- coding: utf-8 -*-
import AnyBlok
from anyblok.interface import ICoreInterface
from AnyBlok import target_registry
from sys import modules
from zope.interface import implementer


class FieldException(Exception):
    pass


@implementer(ICoreInterface)
class AField:

    __interface__ = 'Field'

    def target_registry(self, registry, child, cls_, **kwargs):
        _registryname = registry.__registry_name__ + '.' + child
        if hasattr(registry, child):
            raise FieldException("The Field %r already exist")

        setattr(cls_, '__registry_name__', _registryname)
        setattr(cls_, '__interface__', self.__interface__)
        setattr(registry, child, cls_)
        modules[_registryname] = cls_

    def remove_registry(self, registry, child, cls_, **kwargs):
        raise FieldException("Remove a field is forbiden")


AnyBlok.add_Adapter(ICoreInterface, AField)


@target_registry(AnyBlok)
class Field:

    def __init__(self, label=None):
        self.MustNotBeInstanced(Field)
        if label is None:
            raise FieldException("Label argument are required")
        self.label = label

    def MustNotBeInstanced(self, cls):
        if self.__class__ is cls:
            raise FieldException(
                "%r class must not be instanced use a sub class" % cls)

    @classmethod
    def is_sql_field(cls):
        return False

    def get_sqlalchemy_mapping(self, registry, tablename, properties):
        return self
