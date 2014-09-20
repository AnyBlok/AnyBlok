from anyblok.registry import RegistryManager
from anyblok import Declarations
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import DDLElement
from sqlalchemy.sql import table
from sqlalchemy.orm import Query, mapper


class CreateView(DDLElement):
    def __init__(self, name, selectable):
        self.name = name
        self.selectable = selectable


class DropView(DDLElement):
    def __init__(self, name):
        self.name = name


@compiles(CreateView)
def compile_create_view(element, compiler, **kw):
    return "CREATE VIEW %s AS %s" % (
        element.name, compiler.sql_compiler.process(element.selectable))


@compiles(DropView)
def compile_drop_view(element, compiler, **kw):
    return "DROP VIEW IF EXISTS %s" % (element.name)


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
            if not isinstance(tablename, str):
                tablename = tablename.__tablename__

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
        ns = registry.loaded_registries[namespace]
        properties = ns['properties'].copy()

        if 'is_sql_view' not in properties:
            properties['is_sql_view'] = False

        for b in ns['bases']:
            if b in bases:
                continue

            bases.append(b)
            if b.__doc__ and '__doc__' not in properties:
                properties['__doc__'] = b.__doc__

            for b_ns in b.__anyblok_bases__:
                bs, ps = cls.load_namespace_second_step(
                    registry,
                    b_ns.__registry_name__)
                bases += bs

        if namespace in registry.loaded_registries['Model_names']:
            properties['loaded_columns'] = []
            tablename = properties['__tablename__']
            if properties['is_sql_view']:
                bases += registry.loaded_cores['SqlViewBase']
            elif has_sql_fields(bases):
                bases += registry.loaded_cores['SqlBase']
                bases += [registry.declarativebase]
            else:
                # remove tablename to inherit from a sqlmodel
                del properties['__tablename__']

            bases += registry.loaded_cores['Base']

            if tablename in registry.declarativebase.metadata.tables:
                if '__tablename__' in properties:
                    del properties['__tablename__']

                for t in registry.loaded_namespaces.keys():
                    m = registry.loaded_namespaces[t]
                    if m.is_sql:
                        if getattr(m, '__tablename__'):
                            if m.__tablename__ == tablename:
                                properties['__table__'] = m.__table__
                                tablename = namespace.replace('.', '_').lower()
            else:
                for b in bases:
                    for p, f in get_fields(b).items():
                        cls.declare_field(
                            registry, p, f, namespace, properties)

            bases = [type(tablename, tuple(bases), properties)]

            if properties['is_sql_view']:
                if not hasattr(bases[0], 'sqlalchemy_view_declaration'):
                    raise Declarations.Exception.ViewException(
                        "%r.'sqlalchemy_view_declaration' is required to "
                        "define the query to apply of the view" % namespace)
                pks = []
                for col in properties['loaded_columns']:
                    if getattr(bases[0], col).primary_key:
                        pks.append(col)

                if not pks:
                    raise Declarations.Exception.ViewException(
                        "%r have any primary key defined" % namespace)

                view = table(tablename)
                selectable = getattr(bases[0], 'sqlalchemy_view_declaration')()

                if isinstance(selectable, Query):
                    selectable = selectable.subquery()

                for c in selectable.c:
                    c._make_proxy(view)

                DropView(tablename).execute_at(
                    'before-create', registry.declarativebase.metadata)
                CreateView(tablename, selectable).execute_at(
                    'after-create', registry.declarativebase.metadata)
                DropView(tablename).execute_at(
                    'before-drop', registry.declarativebase.metadata)

                pks = [getattr(view.c, x) for x in pks]
                mapper(bases[0], view, primary_key=pks)

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
        return Blok.apply_state(*registry.ordered_loaded_bloks)
