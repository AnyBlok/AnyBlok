# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.registry import RegistryManager
from anyblok import Declarations
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import DDLElement
from sqlalchemy.sql import table
from sqlalchemy.orm import Query, mapper
from sqlalchemy.ext.hybrid import hybrid_method
from anyblok.common import TypeList, apply_cache


@Declarations.register(Declarations.Exception)
class ModelException(Exception):
    """Exception for Model declaration"""


@Declarations.register(Declarations.Exception)
class ViewException(Declarations.Exception.ModelException):
    """Exception for View declaration"""


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
    """ Tells whether the model as field or not

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
    """ Return the fields for a model

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
    """ The Model class is used to define or inherit an SQL table.

    Add new model class::

        @Declarations.register(Declarations.Model)
        class MyModelclass:
            pass

    Remove a model class::

        Declarations.unregister(Declarations.Model.MyModelclass,
                                MyModelclass)

    There are three Model families:

    * No SQL Model: These models have got any field, so any table
    * SQL Model:
    * SQL View Model: it is a model mapped with a SQL View, the insert, update
      delete method are forbidden by the database

    Each model has a:

    * registry name: compose by the parent + . + class model name
    * table name: compose by the parent + '_' + class model name

    The table name can be overloaded by the attribute tablename. the wanted
    value are a string (name of the table) of a model in the declaration.

    ..warning::

        Two models can have the same table name, both models are mapped on
        the table. But they must have the same column.
    """

    @classmethod
    def register(self, parent, name, cls_, **kwargs):
        """ add new sub registry in the registry

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

        RegistryManager.add_entry_in_register(
            'Model', _registryname, cls_, **kwargs)

    @classmethod
    def unregister(self, entry, cls_):
        """ Remove the Interface from the registry

        :param entry: entry declaration of the model where the ``cls_``
            must be removed
        :param cls_: Class Interface to remove in registry
        """
        RegistryManager.remove_in_register(cls_)

    @classmethod
    def declare_field(self, registry, name, field, namespace, properties):
        """ Declare the field/column/relationship to put in the properties
        of the model

        :param registry: the current  registry
        :param name: name of the field / column or relationship
        :param field: the declaration field / column or relationship
        :param namespace: the namespace of the model
        :param properties: the properties of the model
        """
        if name in properties:
            return

        from sqlalchemy.ext.declarative import declared_attr

        def wrapper(cls):
            return field.get_sqlalchemy_mapping(
                registry, namespace, name, properties)

        properties[name] = declared_attr(wrapper)
        properties['loaded_columns'].append(name)
        field.update_properties(registry, namespace, name, properties)

    @classmethod
    def apply_event_listner(cls, registry, namespace, base, properties):
        """ Find the event listener methods in the base to save the
        namespace and the method in the registry

        :param registry: the current  registry
        :param namespace: the namespace of the model
        :param base: One of the base of the model
        :param properties: the properties of the model
        """
        for attr in dir(base):
            method = getattr(base, attr)
            if not hasattr(method, 'is_an_event_listener'):
                continue
            elif method.is_an_event_listener is True:
                model = method.model
                event = method.event
                if model not in registry.events:
                    registry.events[model] = {event: []}
                elif event not in registry.events[model]:
                    registry.events[model][event] = []

                val = (namespace, attr)
                if val not in registry.events[model][event]:
                    registry.events[model][event].append(val)

    @classmethod
    def detect_hybrid_method(cls, registry, namespace, base, properties):
        """ Find the sqlalchemy hybrid methods in the base to save the
        namespace and the method in the registry

        :param registry: the current registry
        :param namespace: the namespace of the model
        :param base: One of the base of the model
        :param properties: the properties of the model
        """
        for attr in dir(base):
            method = getattr(base, attr)
            if not hasattr(method, 'is_an_hybrid_method'):
                continue
            elif method.is_an_hybrid_method is True:
                if attr not in properties['hybrid_method']:
                    properties['hybrid_method'].append(attr)

    @classmethod
    def transform_base(cls, registry, namespace, base, properties):
        """ Detect specific declaration which must define by registry

        :param registry: the current registry
        :param namespace: the namespace of the model
        :param base: One of the base of the model
        :param properties: the properties of the model
        :rtype: new base
        """
        new_base = apply_cache(registry, namespace, base, properties)
        cls.apply_event_listner(registry, namespace, new_base, properties)
        cls.detect_hybrid_method(registry, namespace, new_base, properties)
        return new_base

    @classmethod
    def apply_hybrid_method(cls, registry, namespace, bases, properties):
        """ Create overload to define the write declaration of sqlalchemy
        hybrid method, add the overload in the declared bases of the
        namespace

        :param registry: the current registry
        :param namespace: the namespace of the model
        :param base: One of the base of the model
        :param properties: the properties of the model
        """
        if not properties['hybrid_method']:
            return

        new_base = type(namespace, tuple(), {})

        def apply_wrapper(attr):

            def wrapper(self, *args, **kwargs):
                self_ = self.registry.loaded_namespaces[self.__registry_name__]
                if self is self_:
                    return getattr(super(new_base, self), attr)(
                        self, *args, **kwargs)
                else:
                    return getattr(super(new_base, self), attr)(
                        *args, **kwargs)

            setattr(new_base, attr, hybrid_method(wrapper))

        for attr in properties['hybrid_method']:
            apply_wrapper(attr)

        bases.insert(0, new_base)

    @classmethod
    def insert_in_bases(cls, registry, namespace, bases, properties):
        """ Add in the declared namespaces new base.

        :param registry: the current registry
        :param namespace: the namespace of the model
        :param base: One of the base of the model
        :param properties: the properties of the model
        """
        cls.apply_hybrid_method(registry, namespace, bases, properties)

    @classmethod
    def load_namespace_first_step(cls, registry, namespace):
        """ Return the properties of the declared bases for a namespace.
        This is the first step because some actions need to known all the
        properties

        :param registry: the current registry
        :param namespace: the namespace of the model
        :rtype: dict of the known properties
        """
        if namespace in registry.loaded_namespaces_first_step:
            return registry.loaded_namespaces_first_step[namespace]

        bases = []
        properties = {}
        ns = registry.loaded_registries[namespace]
        if '__tablename__' in ns['properties']:
            properties['__tablename__'] = ns['properties']['__tablename__']

        for b in ns['bases']:
            bases.append(b)

            for b_ns in b.__anyblok_bases__:
                ps = cls.load_namespace_first_step(registry,
                                                   b_ns.__registry_name__)
                ps.update(properties)
                properties.update(ps)

        for b in bases:
            fields = get_fields(b)
            for p, f in fields.items():
                if p not in properties:
                    properties[p] = f

        registry.loaded_namespaces_first_step[namespace] = properties
        return properties

    @classmethod
    def load_namespace_second_step(cls, registry, namespace,
                                   realregistryname=None,
                                   transformation_properties=None):
        """ Return the bases and the properties of the namespace

        :param registry: the current registry
        :param namespace: the namespace of the model
        :param realregistryname: the name of the model if the namespace is a
            mixin
        :rtype: the list od the bases and the properties
        :exception: ModelException
        """
        if namespace in registry.loaded_namespaces:
            return [registry.loaded_namespaces[namespace]], {}

        if transformation_properties is None:
            transformation_properties = {
                'hybrid_method': [],
            }

        bases = TypeList(cls, registry, namespace, transformation_properties)
        ns = registry.loaded_registries[namespace]
        properties = ns['properties'].copy()

        if 'is_sql_view' not in properties:
            properties['is_sql_view'] = False

        for b in ns['bases']:
            if b in bases:
                continue

            if realregistryname:
                bases.append(b, namespace=realregistryname)
            else:
                bases.append(b)

            if b.__doc__ and '__doc__' not in properties:
                properties['__doc__'] = b.__doc__

            for b_ns in b.__anyblok_bases__:
                brn = b_ns.__registry_name__
                if brn in registry.loaded_registries['Mixin_names']:
                    tp = transformation_properties
                    if realregistryname:
                        bs, ps = cls.load_namespace_second_step(
                            registry, brn, realregistryname=realregistryname,
                            transformation_properties=tp)
                    else:
                        bs, ps = cls.load_namespace_second_step(
                            registry, brn, realregistryname=namespace,
                            transformation_properties=tp)
                elif brn in registry.loaded_registries['Model_names']:
                    bs, ps = cls.load_namespace_second_step(registry, brn)
                else:
                    raise Declarations.Exception.ModelException(
                        "You have not to inherit the %r "
                        "Only the 'Mixin' and %r types are allowed" % (
                            brn, cls.__name__))

                bases += bs

        if namespace in registry.loaded_registries['Model_names']:
            properties['loaded_columns'] = []
            properties['loaded_fields'] = {}
            tablename = properties['__tablename__']
            if properties['is_sql_view']:
                bases.extend([x for x in registry.loaded_cores['SqlViewBase']])
            elif has_sql_fields(bases):
                bases.extend([x for x in registry.loaded_cores['SqlBase']])
                bases.append(registry.declarativebase)
            else:
                # remove tablename to inherit from a sqlmodel
                del properties['__tablename__']

            bases.extend([x for x in registry.loaded_cores['Base']])

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

            bases.append(registry.registry_base)
            cls.insert_in_bases(registry, namespace, bases,
                                transformation_properties)
            bases = [type(tablename, tuple(bases), properties)]

            if properties['is_sql_view']:
                cls.apply_view(namespace, tablename, bases[0], registry,
                               properties)

            properties = {}
            registry.add_in_registry(namespace, bases[0])
            registry.loaded_namespaces[namespace] = bases[0]

        return bases, properties

    @classmethod
    def apply_view(cls, namespace, tablename, base, registry, properties):
        """ Transform the sqlmodel to view model

        :param namespace: Namespace of the model
        :param tablename: Name od the table of the model
        :param base: Model cls
        :param registry: current registry
        :param properties: properties of the model
        :exception: MigrationException
        :exception: ViewException
        """
        if hasattr(base, '__view__'):
            view = base.__view__
        elif tablename in registry.loaded_views:
            view = registry.loaded_views[tablename]
        else:
            if not hasattr(base, 'sqlalchemy_view_declaration'):
                raise Declarations.Exception.ViewException(
                    "%r.'sqlalchemy_view_declaration' is required to "
                    "define the query to apply of the view" % namespace)

            view = table(tablename)
            registry.loaded_views[tablename] = view
            selectable = getattr(base, 'sqlalchemy_view_declaration')()

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

        pks = []
        for col in properties['loaded_columns']:
            if getattr(base, col).primary_key:
                pks.append(col)

        if not pks:
            raise Declarations.Exception.ViewException(
                "%r have any primary key defined" % namespace)

        pks = [getattr(view.c, x) for x in pks]
        mapper(base, view, primary_key=pks)
        setattr(base, '__view__', view)

    @classmethod
    def assemble_callback(cls, registry):
        """ Assemble callback is called to assemble all the Model
        from the installed bloks

        :param registry: registry to update
        """
        registry.loaded_namespaces_first_step = {}
        registry.loaded_views = {}
        registry.caches = {}
        registry.events = {}

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

        This callback updates the database information about

        * Model
        * Column
        * RelationShip

        :param registry: registry to update
        """
        for Model in registry.loaded_namespaces.values():
            Model.initialize_model()

        Model = registry.System.Model
        Model.update_list()

        Blok = registry.System.Blok
        Blok.update_list()
        bloks = Blok.list_by_state('touninstall')
        Blok.uninstall_all(*bloks)
        return Blok.apply_state(*registry.ordered_loaded_bloks)
