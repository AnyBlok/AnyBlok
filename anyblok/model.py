# -*- coding: utf-8 -*-
from anyblok.registry import RegistryManager
import AnyBlok
from AnyBlok import add_Adapter, target_registry
from AnyBlok.Interface import ICoreInterface
from zope.interface import implementer
from sys import modules


@implementer(ICoreInterface)
class AModel:
    """ Adapter to Model Class

    The Model class are used to define or inherit a SQL table.

    Add new model class::

        @target_registry(Model)
        class MyModelclass:
            pass

    Remove a model class::

        remove_registry(Model, 'MyModelclass', MyModelclass, blok='MyBlok')
    """

    __interface__ = 'Model'

    def target_registry(self, registry, child, cls_, **kwargs):
        """ add new sub registry in the registry and add it in the
        sys.modules

        :param registry: Existing global registry
        :param child: Name of the new registry to add it
        :param cls_: Class Interface to add in registry
        """
        _registryname = registry.__registry_name__ + '.' + child
        if 'tablename' in kwargs:
            tablename = kwargs.pop('tablename')
        else:
            if registry is AnyBlok:
                tablename = child.lower()
            elif registry is AnyBlok.Model:
                tablename = child.lower()
            elif hasattr(registry, '__tablename__'):
                tablename = registry.__tablename__
                tablename += '_' + child.lower()

        if not hasattr(registry, child):

            p = {
                '__registry_name__': _registryname,
                '__interface__': self.__interface__,
                '__tablename__': tablename,
            }
            ns = type(child, tuple(), p)
            setattr(registry, child, ns)
            modules[_registryname] = ns

        if registry is AnyBlok:
            return

        kwargs['__registry_name__'] = _registryname
        kwargs['__tablename__'] = tablename

        RegistryManager.add_entry_in_target_registry(
            'Model', _registryname, cls_, **kwargs)

    def remove_registry(self, registry, child, cls_, **kwargs):
        """ Remove the Interface in the registry

        :param registry: Existing global registry
        :param child: Name of the new registry to add it
        :param cls_: Class Interface to remove in registry
        """
        blok = kwargs.pop('blok')
        _registryname = registry.__registry_name__ + '.' + child
        RegistryManager.remove_entry_in_target_registry(blok, 'Model',
                                                        _registryname, cls_,
                                                        **kwargs)

add_Adapter(ICoreInterface, AModel)
RegistryManager.declare_entry('Model', mustbeload=True)


@target_registry(AnyBlok)
class Model:
    pass
