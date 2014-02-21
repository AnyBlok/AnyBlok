import AnyBlok
from AnyBlok.Interface import ICoreInterface
from AnyBlok import target_registry
from anyblok.registry import RegistryManager
from sys import modules
from zope.interface import implementer
from zope.component import getGlobalSiteManager
gsm = getGlobalSiteManager()


@implementer(ICoreInterface)
class ACore(object):

    __interface__ = 'Core'

    def target_registry(self, registry, child, cls_, **kwargs):
        _registryname = registry.__registry_name__ + '.' + child
        if not hasattr(registry, child):
            p = {
                '__registry_name__': _registryname,
                '__interface__': self.__interface__,
            }
            core = type(child, tuple(), p)
            setattr(registry, child, core)
            modules[_registryname] = core

        if registry == AnyBlok:
            return

        RegistryManager.add_core_in_target_registry(child, cls_)

    def remove_registry(self, registry, child, cls_, **kwargs):
        blok = kwargs.pop('blok')
        RegistryManager.remove_core_in_target_registry(blok, child, cls_)


core = ACore()
gsm.registerUtility(core, ICoreInterface, 'Core')


@target_registry(AnyBlok)
class Core:
    pass
