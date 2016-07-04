# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.registry import RegistryManager
from anyblok import Declarations
from anyblok.field import Field
from anyblok.relationship import RelationShip
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import DDLElement
from sqlalchemy.sql import table
from sqlalchemy.orm import Query, mapper, synonym
from sqlalchemy import inspection
from sqlalchemy.ext.hybrid import hybrid_method
from anyblok.common import TypeList, apply_cache
from copy import deepcopy
from sqlalchemy.ext.declarative import declared_attr
from .mapper import ModelAttribute
from sqlalchemy import ForeignKeyConstraint
from anyblok.common import anyblok_column_prefix
from texttable import Texttable


class ModelException(Exception):
    """Exception for Model declaration"""


class ViewException(ModelException):
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
    for base in bases:
        for p in base.__dict__.keys():
            if hasattr(getattr(base, p), '__class__'):
                if Field in getattr(base, p).__class__.__mro__:
                    return True

    return False


def has_sqlalchemy_fields(base):
    for p in base.__dict__.keys():
        attr = base.__dict__[p]
        if inspection.inspect(attr, raiseerr=False) is not None:
            return True

    return False


def get_fields(base, without_relationship=False, only_relationship=False):
    """ Return the fields for a model

    :param base: Model Class
    :param without_relationship: Do not return the relationship field
    :param only_relationship: return only the relationship field
    :rtype: dict with name of the field in key and instance of Field in value
    """
    fields = {}
    for p in base.__dict__.keys():
        if hasattr(getattr(base, p), '__class__'):
            if without_relationship:
                if RelationShip in getattr(base, p).__class__.__mro__:
                    continue

            if only_relationship:
                if RelationShip not in getattr(base, p).__class__.__mro__:
                    continue

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

        elif hasattr(parent, name):
            tablename = getattr(parent, name).__tablename__
        else:
            if parent is Declarations or parent is Declarations.Model:
                tablename = name.lower()
            elif hasattr(parent, '__tablename__'):
                tablename = parent.__tablename__
                tablename += '_' + name.lower()

        if not hasattr(parent, name):
            p = {
                '__tablename__': tablename,
                '__registry_name__': _registryname,
                'use': lambda x: ModelAttribute(_registryname, x),
            }
            ns = type(name, tuple(), p)
            setattr(parent, name, ns)

        if parent is Declarations:
            return

        kwargs['__registry_name__'] = _registryname
        kwargs['__tablename__'] = tablename

        RegistryManager.add_entry_in_register(
            'Model', _registryname, cls_, **kwargs)
        setattr(cls_, '__anyblok_kwargs__', kwargs)

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
        if name in properties['loaded_columns']:
            return

        if field.must_be_duplicate_before_added():
            field = deepcopy(field)

        attr_name = name
        if field.use_hybrid_property:
            attr_name = anyblok_column_prefix + name

        if field.must_be_declared_as_attr():
            # All the declaration are seen as mixin for sqlalchemy
            # some of them need de be defered for the initialisation
            # cause of the mixin as relation ship and column with foreign key
            def wrapper(cls):
                return field.get_sqlalchemy_mapping(
                    registry, namespace, name, properties)

            properties[attr_name] = declared_attr(wrapper)
            properties[attr_name].anyblok_field = field
        else:
            properties[attr_name] = field.get_sqlalchemy_mapping(
                registry, namespace, name, properties)

        if field.use_hybrid_property:
            properties[name] = field.get_property(
                registry, namespace, name, properties)
            properties['hybrid_property_columns'].append(name)

        properties['loaded_columns'].append(name)
        field.update_properties(registry, namespace, name, properties)

    @classmethod
    def apply_event_listner(cls, attr, method, registry, namespace, base,
                            properties):
        """ Find the event listener methods in the base to save the
        namespace and the method in the registry

        :param attr: name of the attibute
        :param method: method pointer
        :param registry: the current  registry
        :param namespace: the namespace of the model
        :param base: One of the base of the model
        :param properties: the properties of the model
        """
        if not hasattr(method, 'is_an_event_listener'):
            return
        elif method.is_an_event_listener is True:
            model = method.model
            event = method.event
            events = registry.events
            if model not in events:
                events[model] = {event: []}
            elif event not in events[model]:
                events[model][event] = []

            val = (namespace, attr)
            ev = events[model][event]
            if val not in ev:
                ev.append(val)

    @classmethod
    def apply_sqlalchemy_event_listner(cls, attr, method, registry, namespace,
                                       base, properties):
        """declare in the registry the sqlalchemy event

        :param attr: name of the attibute
        :param method: method pointer
        :param registry: the current  registry
        :param namespace: the namespace of the model
        :param base: One of the base of the model
        :param properties: the properties of the model
        """
        if not hasattr(method, 'is_an_sqlalchemy_event_listener'):
            return
        elif method.is_an_sqlalchemy_event_listener is True:
            registry._sqlalchemy_known_events.append(
                (method.sqlalchemy_listener,
                 namespace,
                 ModelAttribute(namespace, attr)))

    @classmethod
    def detect_hybrid_method(cls, attr, method, registry, namespace, base,
                             properties):
        """ Find the sqlalchemy hybrid methods in the base to save the
        namespace and the method in the registry

        :param attr: name of the attibute
        :param method: method pointer
        :param registry: the current registry
        :param namespace: the namespace of the model
        :param base: One of the base of the model
        :param properties: the properties of the model
        """
        if not hasattr(method, 'is_an_hybrid_method'):
            return
        elif method.is_an_hybrid_method is True:
            if attr not in properties['hybrid_method']:
                properties['hybrid_method'].append(attr)

    @classmethod
    def detect_table_and_mapper_args(cls, registry, namespace, base,
                                     properties):
        """Test if define_table/mapper_args are in the base, and call them
        save the value in the properties

        if  __table/mapper_args\_\_ are in the base then raise ModelException

        :param registry: the current registry
        :param namespace: the namespace of the model
        :param base: One of the base of the model
        :param properties: the properties of the model
        :exception: ModelException
        """
        if hasattr(base, '__table_args__'):
            raise ModelException(
                "'__table_args__' attribute is forbidden, on Model : %r (%r)."
                "Use the class method 'define_table_args' to define the value "
                "allow anyblok to fill his own '__table_args__' attribute" % (
                    namespace, base.__table_args__))

        if hasattr(base, '__mapper_args__'):
            raise ModelException(
                "'__mapper_args__' attribute is forbidden, on Model : %r (%r)."
                "Use the class method 'define_mapper_args' to define the "
                "value allow anyblok to fill his own '__mapper_args__' "
                "attribute" % (namespace, base.__mapper_args__))

        if hasattr(base, 'define_table_args'):
            properties['table_args'] = True

        if hasattr(base, 'define_mapper_args'):
            properties['mapper_args'] = True

    @classmethod
    def transform_base(cls, registry, namespace, base, properties):
        """ Detect specific declaration which must define by registry

        :param registry: the current registry
        :param namespace: the namespace of the model
        :param base: One of the base of the model
        :param properties: the properties of the model
        :rtype: new base
        """
        new_type_properties = {}
        for attr in dir(base):
            method = getattr(base, attr)
            new_type_properties.update(apply_cache(
                attr, method, registry, namespace, base, properties))
            cls.apply_event_listner(
                attr, method, registry, namespace, base, properties)
            cls.apply_sqlalchemy_event_listner(
                attr, method, registry, namespace, base, properties)
            cls.detect_hybrid_method(
                attr, method, registry, namespace, base, properties)

        cls.detect_table_and_mapper_args(
            registry, namespace, base, properties)

        if new_type_properties:
            return [type(namespace, (), new_type_properties), base]

        return [base]

    @classmethod
    def apply_hybrid_method(cls, base, registry, namespace, bases,
                            transformation_properties, properties):
        """ Create overload to define the write declaration of sqlalchemy
        hybrid method, add the overload in the declared bases of the
        namespace

        :param registry: the current registry
        :param namespace: the namespace of the model
        :param base: One of the base of the model
        :param transformation_properties: the properties of the model
        :param properties: assembled attributes of the namespace
        """
        type_properties = {}

        def apply_wrapper(attr):

            def wrapper(self, *args, **kwargs):
                self_ = self.registry.loaded_namespaces[self.__registry_name__]
                if self is self_:
                    return getattr(super(base, self), attr)(
                        self, *args, **kwargs)
                else:
                    return getattr(super(base, self), attr)(
                        *args, **kwargs)

            setattr(base, attr, hybrid_method(wrapper))

        if transformation_properties['hybrid_method']:
            for attr in transformation_properties['hybrid_method']:
                apply_wrapper(attr)

        return type_properties

    @classmethod
    def apply_table_and_mapper_args(cls, base, registry, namespace, bases,
                                    transformation_properties, properties):
        """ Create overwrite to define table and mapper args to define some
        options for SQLAlchemy

        :param registry: the current registry
        :param namespace: the namespace of the model
        :param base: One of the base of the model
        :param transformation_properties: the properties of the model
        :param properties: assembled attributes of the namespace
        """
        table_args = tuple(properties['add_in_table_args'])
        if table_args:
            def define_table_args(cls_):
                if cls_.__registry_name__ == namespace:
                    res = super(base, cls_).define_table_args()
                    fks = [x.name for x in res
                           if isinstance(x, ForeignKeyConstraint)]

                    t_args = [x for x in table_args
                              if (not isinstance(x, ForeignKeyConstraint) or
                                  x.name not in fks)]

                    return res + tuple(t_args)

                return ()

            base.define_table_args = classmethod(define_table_args)
            transformation_properties['table_args'] = True

        if transformation_properties['table_args']:

            def __table_args__(cls_):
                return cls_.define_table_args()

            base.__table_args__ = declared_attr(__table_args__)

        if transformation_properties['mapper_args']:

            def __mapper_args__(cls_):
                return cls_.define_mapper_args()

            base.__mapper_args__ = declared_attr(__mapper_args__)

    @classmethod
    def insert_in_bases(cls, registry, namespace, bases,
                        transformation_properties, properties):
        """ Add in the declared namespaces new base.

        :param registry: the current registry
        :param namespace: the namespace of the model
        :param base: One of the base of the model
        :param transformation_properties: the properties of the model
        :param properties: assembled attributes of the namespace
        """
        new_base = type(namespace, (), {})
        bases.insert(0, new_base)
        cls.apply_hybrid_method(new_base, registry, namespace, bases,
                                transformation_properties, properties)
        cls.apply_table_and_mapper_args(new_base, registry, namespace, bases,
                                        transformation_properties, properties)

    @classmethod
    def raise_if_has_sqlalchemy(cls, base):
        if has_sqlalchemy_fields(base):
            raise ModelException(
                "the base %r have an SQLAlchemy attribute" % base)

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
        properties = {'__depends__': set()}
        ns = registry.loaded_registries[namespace]

        for b in ns['bases']:
            bases.append(b)

            for b_ns in b.__anyblok_bases__:
                if b_ns.__registry_name__.startswith('Model.'):
                    properties['__depends__'].add(b_ns.__registry_name__)

                ps = cls.load_namespace_first_step(registry,
                                                   b_ns.__registry_name__)
                ps.update(properties)
                properties.update(ps)

        for b in bases:
            cls.raise_if_has_sqlalchemy(b)
            fields = get_fields(b)
            for p, f in fields.items():
                if p not in properties:
                    properties[p] = f

        if '__tablename__' in ns['properties']:
            properties['__tablename__'] = ns['properties']['__tablename__']

        registry.loaded_namespaces_first_step[namespace] = properties
        return properties

    @classmethod
    def apply_inheritance_base(cls, registry, namespace, ns, bases,
                               realregistryname, properties,
                               transformation_properties):

        # remove doublon
        for b in ns['bases']:
            if b in bases:
                continue

            kwargs = {
                'namespace': realregistryname} if realregistryname else {}
            bases.append(b, **kwargs)

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
                    raise ModelException(
                        "You have not to inherit the %r "
                        "Only the 'Mixin' and %r types are allowed" % (
                            brn, cls.__name__))

                bases += bs

    @classmethod
    def init_core_properties_and_bases(cls, registry, bases, properties):
        properties['loaded_columns'] = []
        properties['hybrid_property_columns'] = []
        properties['loaded_fields'] = {}
        if properties['is_sql_view']:
            bases.extend([x for x in registry.loaded_cores['SqlViewBase']])
        elif has_sql_fields(bases):
            bases.extend([x for x in registry.loaded_cores['SqlBase']])
            bases.append(registry.declarativebase)
        else:
            # remove tablename to inherit from a sqlmodel
            del properties['__tablename__']

        bases.extend([x for x in registry.loaded_cores['Base']])

    @classmethod
    def declare_all_fields(cls, registry, namespace, bases, properties):
        # do in the first time the fields and columns
        # because for the relationship on the same model
        # the primary keys must exist before the relationship
        # load all the base before do relationship because primary key
        # can be come from inherit
        for b in bases:
            for p, f in get_fields(b,
                                   without_relationship=True).items():
                cls.declare_field(
                    registry, p, f, namespace, properties)

        for b in bases:
            for p, f in get_fields(b, only_relationship=True).items():
                cls.declare_field(
                    registry, p, f, namespace, properties)

    @classmethod
    def apply_existing_table(cls, registry, namespace, tablename, properties):
        if '__tablename__' in properties:
            del properties['__tablename__']

        for t in registry.loaded_namespaces.keys():
            m = registry.loaded_namespaces[t]
            if m.is_sql:
                if getattr(m, '__tablename__'):
                    if m.__tablename__ == tablename:
                        properties['__table__'] = m.__table__
                        tablename = namespace.replace('.', '_').lower()

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
                'table_args': False,
                'mapper_args': False,
            }

        bases = TypeList(cls, registry, namespace, transformation_properties)
        ns = registry.loaded_registries[namespace]
        properties = ns['properties'].copy()
        properties['add_in_table_args'] = []

        if 'is_sql_view' not in properties:
            properties['is_sql_view'] = False

        cls.apply_inheritance_base(registry, namespace, ns, bases,
                                   realregistryname, properties,
                                   transformation_properties)

        if namespace in registry.loaded_registries['Model_names']:
            tablename = properties['__tablename__']
            cls.init_core_properties_and_bases(registry, bases, properties)

            if tablename in registry.declarativebase.metadata.tables:
                cls.apply_existing_table(
                    registry, namespace, tablename, properties)
            else:
                cls.declare_all_fields(registry, namespace, bases, properties)

            bases.append(registry.registry_base)
            cls.insert_in_bases(registry, namespace, bases,
                                transformation_properties, properties)
            if properties['is_sql_view']:
                cls.replace_properties_by_synonym(properties)
                bases = [type(tablename, tuple(bases), properties)]
                if properties['is_sql_view']:
                    cls.apply_view(namespace, tablename, bases[0], registry,
                                   properties)
            else:
                bases = [type(tablename, tuple(bases), properties)]

            properties = {}
            registry.add_in_registry(namespace, bases[0])
            registry.loaded_namespaces[namespace] = bases[0]

        return bases, properties

    @classmethod
    def replace_properties_by_synonym(cls, properties):
        for field in properties['loaded_columns']:
            properties[field] = synonym(anyblok_column_prefix + field)

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
                raise ViewException(
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

        pks = [col for col in properties['loaded_columns']
               if getattr(base, anyblok_column_prefix + col).primary_key]

        if not pks:
            raise ViewException(
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

        Blok = registry.System.Blok
        if not registry.withoutautomigration:
            Model = registry.System.Model
            Model.update_list()
            registry.update_blok_list()

        bloks = Blok.list_by_state('touninstall')
        Blok.uninstall_all(*bloks)
        return Blok.apply_state(*registry.ordered_loaded_bloks)

    @classmethod
    def autodoc_class(cls, model_cls):
        res = [":Declaration type: Model"]
        res.extend([':%s: %s' % (x.replace('_', ' ').strip(), str(y))
                    for x, y in model_cls.__anyblok_kwargs__.items()])
        res.extend([':Inherit model or mixin:', ''])
        res.extend([' * ' + str(x) for x in model_cls.__anyblok_bases__])
        res.extend(['', ''])
        if has_sql_fields([model_cls]):
            rows = [['field name', 'Description']]
            rows.extend([x, y.autodoc()]
                        for x, y in get_fields(model_cls).items())
            table = Texttable()
            table.set_cols_valign(["m", "t"])
            table.add_rows(rows)
            res.extend(['', table.draw(), '', ''])

        return '\n'.join(res)
