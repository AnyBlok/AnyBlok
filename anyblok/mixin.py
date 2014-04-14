from anyblok.registry import RegistryManager
from anyblok import Declarations


@Declarations.add_declaration_type(isAnEntry=True)
class Mixin:
    """ The Mixin class are used to define a behaviour one one or more model:

    Add new mixin class::

        @Declarations.target_registry(Declarations.Mixin)
        class MyMixinclass:
            pass

    Remove a mixin class::

        Declarations.remove_registry(Declarations.Mixin, 'MyMixinclass',
                                     MyMixinclass, blok='MyBlok')
    """

    @classmethod
    def target_registry(self, parent, name, cls_, **kwargs):
        """ add new sub registry in the registry and add it in the
        sys.modules

        :param parent: Existing global registry
        :param name: Name of the new registry to add it
        :param cls_: Class Interface to add in registry
        """
        _registryname = parent.__registry_name__ + '.' + name

        if not hasattr(parent, name):
            ns = type(name, tuple(), {})
            setattr(parent, name, ns)
            kwargs['__registry_name__'] = _registryname

        if parent is Declarations:
            return

        RegistryManager.add_entry_in_target_registry(
            'Mixin', _registryname, cls_, **kwargs)

    @classmethod
    def remove_registry(self, parent, name, cls_, **kwargs):
        """ Remove the Interface in the registry

        :param parent: Existing global registry
        :param name: Name of the new registry to add it
        :param cls_: Class Interface to remove in registry
        """
        blok = kwargs.pop('blok')
        _registryname = parent.__registry_name__ + '.' + name
        RegistryManager.remove_entry_in_target_registry(blok, 'Mixin',
                                                        _registryname, cls_,
                                                        **kwargs)
