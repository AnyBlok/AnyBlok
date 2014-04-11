import AnyBlok
from AnyBlok.Interface import ICoreInterface
from AnyBlok import target_registry, add_Adapter
from sys import modules
from zope.interface import implementer


@implementer(ICoreInterface)
class AException:
    """ Adapter to Exception Class

    The Exception class are used to define type of AnyBlok Exception

    Add new Exception type::

        @target_registry(AnyBlok.Exception)
        class MyException:
            pass

    the remove exception are forbidden because this exception can be used
    """

    __interface__ = 'Exception'

    def target_registry(self, registry, child, cls_, **kwargs):
        """ add new sub registry in the registry and add it in the
        sys.modules

        :param registry: Existing global registry
        :param child: Name of the new registry to add it
        :param cls_: Class Interface to add in registry
        """
        _registryname = registry.__registry_name__ + '.' + child
        if hasattr(registry, child):
            raise AnyBlokException(
                "The Exception %r already exist" % _registryname)

        setattr(cls_, '__registry_name__', _registryname)
        setattr(cls_, '__interface__', self.__interface__)
        setattr(registry, child, cls_)
        modules[_registryname] = cls_

    def remove_registry(self, registry, child, cls_, **kwargs):
        """ Forbidden method """
        raise AnyBlokException("Remove an exception is forbiden")


add_Adapter(ICoreInterface, AException)


@target_registry(AnyBlok)
class Exception(Exception):
    __interface__ = 'Exception'


@target_registry(AnyBlok.Exception)
class AnyBlokException(Exception):
    """ Simple Exception """


from .interface import CoreInterfaceException
target_registry(AnyBlok.Exception, cls_=CoreInterfaceException)
