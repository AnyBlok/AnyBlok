import anyblok
from zope.interface import Interface, Attribute, implementer
from zope.component import getGlobalSiteManager
gsm = getGlobalSiteManager()


Interface.__interface__ = 'Interface'
anyblok.AnyBlok.Interface = Interface


class ICoreInterface(Interface):

    __interface__ = Attribute("""Name of the interface""")

    def target_registry(registry, child, cls_, **kwargs):
        """ Add a child in registry """

    def remove_registry(registry, child, cls_):
        """ Remove child from registry """


@implementer(ICoreInterface)
class CoreInterface(object):

    __interface__ = 'Interface'
    __exception__ = "The interface to add in registry is already existing"

    def target_registry(self, registry, child, cls_, **kwargs):
        if hasattr(registry, child):
            raise Exception(self.__exception__)

        cls_.__interface__ = self.__interface__
        setattr(registry, child, cls_)

    def remove_registry(self, registry, child, cls_):
        if child in registry.__dict__:
            if registry.__dict__[child] == cls_:
                del registry.__dict__[child]


coreinterface = CoreInterface()
gsm.registerUtility(coreinterface, ICoreInterface, 'Interface')


anyblok.AnyBlok.Interface.ICoreInterface = ICoreInterface
