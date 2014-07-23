from anyblok.registry import RegistryManager
from anyblok import Declarations


def has_sql_fields(bases):
    """ Indicate if the model as field or not

    :param bases: list of Model's Class
    :rtype: boolean
    """
    Field = Declarations.Field
    for base in bases:
        for p in dir(base):
            if hasattr(getattr(base, p), '__class__'):
                if Field in getattr(base, p).__class__.__mro__:
                    return True

    return False


def get_fields(base):
    """ Return the fields for one model

    :param base: Model Class
    :rtype: dict with name of the field in key and instance of Field in value
    """
    Field = Declarations.Field
    fields = {}
    for p in dir(base):
        if hasattr(getattr(base, p), '__class__'):
            if Field in getattr(base, p).__class__.__mro__:
                fields[p] = getattr(base, p)
    return fields


@Declarations.add_declaration_type(isAnEntry=True,
                                   assemble='assemble_callback',
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
                '__registry_name__': _registryname,
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
    def declare_field(self, registry, name, field, namespace, properties):
        if name in properties:
            return

        from sqlalchemy.ext.declarative import declared_attr

        def wrapper(cls):
            return field.get_sqlalchemy_mapping(
                registry, namespace, name, properties)

        field.update_properties(registry, namespace, name, properties)
        properties[name] = declared_attr(wrapper)
        properties['loaded_columns'].append(name)

    @classmethod
    def load_namespace_first_step(cls, registry, namespace):
        if namespace in registry.loaded_namespaces_first_step:
            return registry.loaded_namespaces_first_step[namespace]

        bases = []
        properties = {}
        ns = registry.loaded_registries[namespace]

        for b in ns['bases']:
            bases.append(b)

            for b_ns in b.__anyblok_bases__:
                ps = cls.load_namespace_first_step(registry,
                                                   b_ns.__registry_name__)
                ps.update(properties)
                properties.update(ps)

        if namespace in registry.loaded_registries['Model_names']:
            for b in bases:
                fields = get_fields(b)
                for p, f in fields.items():
                    properties[p] = f

            registry.loaded_namespaces_first_step[namespace] = properties
            properties = {}

        return properties

    @classmethod
    def load_namespace_second_step(cls, registry, namespace):
        if namespace in registry.loaded_namespaces:
            return [registry.loaded_namespaces[namespace]], {}

        bases = []
        properties = {}
        ns = registry.loaded_registries[namespace]

        for b in ns['bases']:
            if b in bases:
                continue

            bases.append(b)
            p = ns['properties'].copy()
            if b.__doc__:
                p['__doc__'] = b.__doc__

            p.update(properties)
            properties.update(p)

            for b_ns in b.__anyblok_bases__:
                bs, ps = cls.load_namespace_second_step(
                    registry,
                    b_ns.__registry_name__)
                bases += bs
                ps.update(properties)
                properties.update(ps)

        if namespace in registry.loaded_registries['Model_names']:
            properties['loaded_columns'] = []
            tablename = properties['__tablename__']
            if has_sql_fields(bases):
                bases += registry.loaded_cores['SqlBase']
                bases += [registry.declarativebase]

            bases += registry.loaded_cores['Base']
            for b in bases:
                for p, f in get_fields(b).items():
                    cls.declare_field(
                        registry, p, f, namespace, properties)

            bases = [type(tablename, tuple(bases), properties)]
            properties = {}
            registry.add_in_registry(namespace, bases[0])
            registry.loaded_namespaces[namespace] = bases[0]

        return bases, properties

    @classmethod
    def assemble_callback(cls, registry):
        """ Assemble callback is called to assemble all the Model
        from the installed bloks

        :param registry: registry to update
        """
        registry.loaded_namespaces_first_step = {}

        # get all the information to create a namespace
        for namespace in registry.loaded_registries['Model_names']:
            cls.load_namespace_first_step(registry, namespace)

        # create the namespace with all the information come from first
        # step
        for namespace in registry.loaded_registries['Model_names']:
            cls.load_namespace_second_step(registry, namespace)

    @classmethod
    def initialize_callback(cls, registry):
        """ initialize callback is called after assembling all entries

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
