from anyblok import AnyBlok
from anyblok.registry import RegistryManager
from zope.interface import implementer
from zope.component import getGlobalSiteManager
gsm = getGlobalSiteManager()


@implementer(AnyBlok.Interface.ICoreInterface)
class ACore(object):

    __interface__ = 'Core'

    def target_registry(self, registry, child, cls_, **kwargs):
        _registryname = registry.__registry_name__ + '.' + child
        if not hasattr(registry, child):
            p = {
                '__registry_name__': _registryname,
                '__interface__': self.__interface__,
            }
            setattr(registry, child, type(child, tuple(), p))

        if registry == AnyBlok:
            return

        RegistryManager.add_core_in_target_registry(child, cls_)

    def remove_registry(self, registry, child, cls_, **kwargs):
        blok = kwargs.pop('blok')
        RegistryManager.remove_core_in_target_registry(blok, child, cls_)


core = ACore()
gsm.registerUtility(core, AnyBlok.Interface.ICoreInterface, 'Core')


@AnyBlok.target_registry(AnyBlok)
class Core:
    pass
