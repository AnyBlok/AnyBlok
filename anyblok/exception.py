from anyblok import Declarations
from .declarations import DeclarationsException
from anyblok.environment import EnvironmentManager, EnvironmentException


@Declarations.add_declaration_type()
class Exception:
    """ Adapter to Exception Class

    The Exception class are used to define type of Declarations Exception

    Add new Exception type::

        @Declarations.target_registry(Declarations.Exception)
        class MyException:
            pass

    the remove exception are forbidden because this exception can be used
    """

    @classmethod
    def target_registry(self, parent, name, cls_, **kwargs):
        """ add new sub registry in the registry and add it in the
        sys.modules

        :param registry: Existing global registry
        :param child: Name of the new registry to add it
        :param cls_: Class Interface to add in registry
        """
        _registryname = parent.__registry_name__ + '.' + name
        if hasattr(parent, name) and not EnvironmentManager.get('reload',
                                                                False):
            raise DeclarationsException(
                "The Exception %r already exist" % _registryname)

        setattr(cls_, '__registry_name__', _registryname)
        setattr(cls_, '__declaration_type__', parent.__declaration_type__)
        setattr(parent, name, cls_)

    @classmethod
    def remove_registry(self, registry, child, cls_, **kwargs):
        """ Forbidden method """
        raise DeclarationsException("Remove an exception is forbiden")


Declarations.target_registry(Declarations.Exception,
                             cls_=DeclarationsException)
Declarations.target_registry(Declarations.Exception,
                             cls_=EnvironmentException)
