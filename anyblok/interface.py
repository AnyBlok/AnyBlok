import AnyBlok
from sys import modules
from zope.interface import Interface, Attribute, implementer


Interface.__interface__ = 'Interface'
AnyBlok.Interface = Interface
modules['AnyBlok.Interface'] = Interface


class CoreInterfaceException(Exception):
    """ Simple Exception for CoreInterface """


class ICoreInterface(Interface):
    """ Interface to target_registry """

    __interface__ = Attribute("""Name of the interface""")

    def target_registry(registry, child, cls_, **kwargs):
        """ Add a child in registry """

    def remove_registry(registry, child, cls_, **kwargs):
        """ Remove child from registry """


@implementer(ICoreInterface)
class ACoreInterface(object):
    """ Adapter to add a new interface on the registry

        Add new interface::

            @AnyBlok.target_registry(AnyBlok.Interface)
            class NewInterface:
                pass

        Remove the existing interface::

            AnyBlok.remove_registry(AnyBlok.Interface, 'NewInterface',
                                    cls_=NewInterface)

    """

    __interface__ = 'Interface'

    def target_registry(self, registry, child, cls_, **kwargs):
        """ add new sub registry in the registry and add it in the
        sys.modules

        :param registry: Existing global registry
        :param child: Name of the new registry to add it
        :param cls_: Class Interface to add in registry
        """

        if registry is not AnyBlok.Interface:
            raise CoreInterfaceException(
                "The Interface must be add only under Interface")

        if hasattr(registry, child):
            raise CoreInterfaceException(
                "The interface to add in registry is already existing")

        cls_.__interface__ = self.__interface__
        setattr(registry, child, cls_)
        modules['AnyBlok.Interface.' + child] = cls_

    def remove_registry(self, registry, child, cls_, **kwargs):
        """ Remove the Interface in the registry

        :param registry: Existing global registry
        :param child: Name of the new registry to add it
        :param cls_: Class Interface to remove in registry
        """

        if hasattr(registry, child):
            if getattr(registry, child) == cls_:
                delattr(registry, child)


AnyBlok.add_Adapter(ICoreInterface, ACoreInterface)


AnyBlok.Interface.ICoreInterface = ICoreInterface
modules['AnyBlok.Interface.ICoreInterface'] = ICoreInterface
