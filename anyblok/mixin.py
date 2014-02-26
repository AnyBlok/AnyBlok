# -*- coding: utf-8 -*-
from anyblok.registry import RegistryManager
import AnyBlok
from AnyBlok.Interface import ICoreInterface
from AnyBlok import add_Adapter, target_registry
from zope.interface import implementer
from sys import modules


@implementer(ICoreInterface)
class AMixin:
    """ Adapter to Mixin Class

    The Mixin class are used to define a behaviour one one or more model:

    Add new mixin class::

        @target_registry(Mixin)
        class MyMixinclass:
            pass

    Remove a mixin class::

        remove_registry(Mixin, 'MyMixinclass', MyMixinclass, blok='MyBlok')
    """

    __interface__ = 'Mixin'

    def target_registry(self, registry, child, cls_, **kwargs):
        """ add new sub registry in the registry and add it in the
        sys.modules

        :param registry: Existing global registry
        :param child: Name of the new registry to add it
        :param cls_: Class Interface to add in registry
        """
        _registryname = registry.__registry_name__ + '.' + child

        if not hasattr(registry, child):
            p = {
                '__registry_name__': _registryname,
                '__interface__': self.__interface__,
            }
            ns = type(child, tuple(), p)
            setattr(registry, child, ns)
            modules[_registryname] = ns
            kwargs['__registry_name__'] = _registryname

        if registry is AnyBlok:
            return

        RegistryManager.add_entry_in_target_registry(
            'Mixin', _registryname, cls_, **kwargs)

    def remove_registry(self, registry, child, cls_, **kwargs):
        """ Remove the Interface in the registry

        :param registry: Existing global registry
        :param child: Name of the new registry to add it
        :param cls_: Class Interface to remove in registry
        """
        blok = kwargs.pop('blok')
        _registryname = registry.__registry_name__ + '.' + child
        RegistryManager.remove_entry_in_target_registry(blok, 'Mixin',
                                                        _registryname, cls_,
                                                        **kwargs)

add_Adapter(ICoreInterface, AMixin)
RegistryManager.declare_entry('Mixin')


@target_registry(AnyBlok)
class Mixin:
    pass
