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
        """ add new sub registry in the registry

        :param parent: Existing declaration
        :param name: Name of the new declaration to add it
        :param cls_: Class Interface to add in the declaration
        """
        if not hasattr(parent, name):
            core = type(name, tuple(), {})
            setattr(parent, name, core)

        if parent == Declarations:
            return

        RegistryManager.add_core_in_target_registry(name, cls_)

    @classmethod
    def remove_registry(self, entry, cls_):
        """ Remove the Interface in the registry

        :param entry: entry declaration of the model where the ``cls_``
            must be removed
        :param cls_: Class Interface to remove in the declaration
        """
        RegistryManager.remove_in_target_registry(cls_)
