from anyblok.registry import RegistryManager
from anyblok import Declarations


@Declarations.add_declaration_type(isAnEntry=True,
                                   initialize='initialize_callback')
class Model:
    """ The Model class are used to define or inherit a SQL table.

    Add new model class::

        @Declarations.target_registry(Declarations.Model)
        class MyModelclass:
            pass

    Remove a model class::

        Declarations.remove_registry(Declarations.Model, 'MyModelclass',
                                     MyModelclass, blok='MyBlok')
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
        if 'tablename' in kwargs:
            tablename = kwargs.pop('tablename')
        else:
            if parent is Declarations:
                tablename = name.lower()
            elif parent is Declarations.Model:
                tablename = name.lower()
            elif hasattr(parent, '__tablename__'):
                tablename = parent.__tablename__
                tablename += '_' + name.lower()

        if not hasattr(parent, name):

            p = {
                '__tablename__': tablename,
            }
            ns = type(name, tuple(), p)
            setattr(parent, name, ns)

        if parent is Declarations:
            return

        kwargs['__registry_name__'] = _registryname
        kwargs['__tablename__'] = tablename

        RegistryManager.add_entry_in_target_registry(
            'Model', _registryname, cls_, **kwargs)

    @classmethod
    def remove_registry(self, parent, name, cls_, **kwargs):
        """ Remove the Interface in the registry

        :param registry: Existing global registry
        :param name: Name of the new registry to add it
        :param cls_: Class Interface to remove in registry
        """
        blok = kwargs.pop('blok')
        _registryname = parent.__registry_name__ + '.' + name
        RegistryManager.remove_entry_in_target_registry(blok, 'Model',
                                                        _registryname, cls_,
                                                        **kwargs)

    @classmethod
    def initialize_callback(cls, registry):
        """ initialize callback call after assembling all entries

        This callback update the database information about

        * Model
        * Column
        * RelationShip

        :param registry: registry to update
        """
        Model = registry.System.Model
        Model.update_list()

        Blok = registry.System.Blok
        Blok.update_list()
        Blok.apply_state(*registry.ordered_loaded_bloks)
