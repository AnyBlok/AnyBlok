from anyblok.registry import RegistryManager
from anyblok import Declarations


@Declarations.add_declaration_type()
class Core:
    """ The Core class are the base of all the AnyBlok model

    Add new core model::

        @Declarations.target_registry(Declarations.Core)
        class Base:
            pass

    Remove the core model::

        Declarations.remove_registry(Declarations.Core, 'Base', Base,
                                     blok='MyBlok')

    """

    @classmethod
    def target_registry(self, parent, name, cls_, **kwargs):
        """ add new sub registry in the registry and add it in the
        sys.modules

        :param registry: Existing global registry
        :param child: Name of the new registry to add it
        :param cls_: Class Interface to add in registry
        """
        if not hasattr(parent, name):
            core = type(name, tuple(), {})
            setattr(parent, name, core)

        if parent == Declarations:
            return

        RegistryManager.add_core_in_target_registry(name, cls_)

    @classmethod
    def remove_registry(self, registry, child, cls_, **kwargs):
        """ Remove the Interface in the registry

        :param registry: Existing global registry
        :param child: Name of the new registry to add it
        :param cls_: Class Interface to remove in registry
        """
        blok = kwargs.pop('blok')
        RegistryManager.remove_core_in_target_registry(blok, child, cls_)
