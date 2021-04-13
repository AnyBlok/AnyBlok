# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2019 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#    Copyright (C) 2021 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.registry import RegistryManager
from anyblok import Declarations
from anyblok.field import Field, FieldException
from anyblok.relationship import RelationShip
from anyblok.column import Column
from sqlalchemy import inspection
from anyblok.common import TypeList
from copy import deepcopy
from sqlalchemy.ext.declarative import declared_attr
from anyblok.mapper import ModelAttribute, format_schema
from anyblok.common import anyblok_column_prefix
from texttable import Texttable
from .plugins import get_model_plugins
from .exceptions import ModelException
from .factory import has_sql_fields, ModelFactory


def has_sqlalchemy_fields(base):
    for p in base.__dict__.keys():
        attr = base.__dict__[p]
        if inspection.inspect(attr, raiseerr=False) is not None:
            return True

    return False


def is_in_mro(cls, base, attr):
    return cls in getattr(base, attr).__class__.__mro__


def get_fields(base, without_relationship=False, only_relationship=False,
               without_column=False):
    """ Return the fields for a model

    :param base: Model Class
    :param without_relationship: Do not return the relationship field
    :param only_relationship: return only the relationship field
    :param without_column: Do not return the column field
    :rtype: dict with name of the field in key and instance of Field in value
    """
    fields = {}
    for p in base.__dict__.keys():
        try:
            if hasattr(getattr(base, p), '__class__'):
                if without_relationship and is_in_mro(RelationShip, base, p):
                    continue

                if without_column and is_in_mro(Column, base, p):
                    continue

                if only_relationship and not is_in_mro(RelationShip, base, p):
                    continue

                if is_in_mro(Field, base, p):
                    fields[p] = getattr(base, p)

        except FieldException:  # pragma: no cover
            pass

    return fields


def autodoc_fields(declaration_cls, model_cls):  # pragma: no cover
    """Produces autodocumentation table for the fields.

    Exposed as a function in order to be reusable by a simple export,
    e.g., from anyblok.mixin.
    """
    if not has_sql_fields([model_cls]):
        return ''

    rows = [['Fields', '']]
    rows.extend([x, y.autodoc()]
                for x, y in get_fields(model_cls).items())
    table = Texttable(max_width=0)
    table.set_cols_valign(["m", "t"])
    table.add_rows(rows)
    return table.draw() + '\n\n'


def update_factory(kwargs):
    if 'factory' in kwargs:
        kwargs['__model_factory__'] = kwargs.pop('factory')


@Declarations.add_declaration_type(isAnEntry=True,
                                   pre_assemble='pre_assemble_callback',
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

    autodoc_anyblok_kwargs = True

    autodoc_anyblok_bases = True

    autodoc_anyblok_fields = True

    @classmethod
    def pre_assemble_callback(cls, registry):
        plugins = get_model_plugins(registry)

        def call_plugins(method, *args, **kwargs):
            """call the method on each plugin"""
            for plugin in plugins:
                if hasattr(plugin, method):
                    getattr(plugin, method)(*args, **kwargs)

        registry.call_plugins = call_plugins

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
            return  # pragma: no cover

        kwargs['__registry_name__'] = _registryname
        kwargs['__tablename__'] = tablename
        update_factory(kwargs)

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
    def declare_field(cls, registry, name, field, namespace, properties,
                      transformation_properties):
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

        if field.must_be_copied_before_declaration():
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

        registry.call_plugins('declare_field', name, field, namespace,
                              properties, transformation_properties)

        properties['loaded_columns'].append(name)
        field.update_properties(registry, namespace, name, properties)

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
            if attr in ('registry', 'anyblok', '_sa_registry'):
                continue

            method = getattr(base, attr)
            registry.call_plugins(
                'transform_base_attribute',
                attr, method, namespace, base, properties, new_type_properties)

        registry.call_plugins(
            'transform_base', namespace, base, properties, new_type_properties)

        if new_type_properties:
            return [type(namespace, (), new_type_properties), base]

        return [base]

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
        registry.call_plugins('insert_in_bases', new_base, namespace,
                              properties, transformation_properties)

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
        properties = {
            '__depends__': set(),
            '__db_schema__': format_schema(None, namespace)
        }
        ns = registry.loaded_registries[namespace]

        for b in ns['bases']:
            bases.append(b)

            for b_ns in b.__anyblok_bases__:
                if b_ns.__registry_name__.startswith('Model.'):
                    properties['__depends__'].add(b_ns.__registry_name__)

                ps = cls.load_namespace_first_step(registry,
                                                   b_ns.__registry_name__)
                ps = ps.copy()
                ps.update(properties)
                properties.update(ps)

        for b in bases:
            cls.raise_if_has_sqlalchemy(b)
            fields = get_fields(b)
            for p, f in fields.items():
                if p not in properties:
                    properties[p] = f

            if hasattr(b, '__db_schema__'):
                properties['__db_schema__'] = format_schema(b.__db_schema__,
                                                            namespace)

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
                    raise ModelException(  # pragma: no cover
                        "You have not to inherit the %r "
                        "Only the 'Mixin' and %r types are allowed" % (
                            brn, cls.__name__))

                bases += bs

    @classmethod
    def init_core_properties_and_bases(cls, registry, bases, properties):
        properties['loaded_columns'] = []
        properties['hybrid_property_columns'] = []
        properties['loaded_fields'] = {}
        properties['__model_factory__'].insert_core_bases(bases, properties)

    @classmethod
    def declare_all_fields(cls, registry, namespace, bases, properties,
                           transformation_properties):
        # do in the first time the fields and columns
        # because for the relationship on the same model
        # the primary keys must exist before the relationship
        # load all the base before do relationship because primary key
        # can be come from inherit
        for b in bases:
            for p, f in get_fields(b,
                                   without_relationship=True).items():
                cls.declare_field(
                    registry, p, f, namespace, properties,
                    transformation_properties)

        for b in bases:
            for p, f in get_fields(b, only_relationship=True).items():
                cls.declare_field(
                    registry, p, f, namespace, properties,
                    transformation_properties)

    @classmethod
    def apply_existing_table(cls, registry, namespace, tablename, properties,
                             bases, transformation_properties):
        if '__tablename__' in properties:
            del properties['__tablename__']

        for t in registry.loaded_namespaces.keys():
            m = registry.loaded_namespaces[t]
            if m.is_sql:
                if getattr(m, '__tablename__'):
                    if m.__tablename__ == tablename:
                        properties['__table__'] = m.__table__
                        tablename = namespace.replace('.', '_').lower()

        for b in bases:
            for p, f in get_fields(b,
                                   without_relationship=True,
                                   without_column=True).items():
                cls.declare_field(
                    registry, p, f, namespace, properties,
                    transformation_properties)

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
            transformation_properties = {}

        bases = TypeList(cls, registry, namespace, transformation_properties)
        ns = registry.loaded_registries[namespace]
        properties = ns['properties'].copy()
        first_step = registry.loaded_namespaces_first_step[namespace]
        properties['__depends__'] = first_step['__depends__']
        properties['__db_schema__'] = first_step.get('__db_schema__', None)

        registry.call_plugins('initialisation_tranformation_properties',
                              properties, transformation_properties)

        properties['__model_factory__'] = properties.get(
            '__model_factory__', ModelFactory)(registry)

        cls.apply_inheritance_base(registry, namespace, ns, bases,
                                   realregistryname, properties,
                                   transformation_properties)

        if namespace in registry.loaded_registries['Model_names']:
            tablename = properties['__tablename__']
            modelname = namespace.replace('.', '')
            cls.init_core_properties_and_bases(registry, bases, properties)

            if tablename in registry.declarativebase.metadata.tables:
                cls.apply_existing_table(
                    registry, namespace, tablename, properties,
                    bases, transformation_properties)
            else:
                cls.declare_all_fields(registry, namespace, bases, properties,
                                       transformation_properties)

            bases.append(registry.registry_base)
            cls.insert_in_bases(registry, namespace, bases,
                                transformation_properties, properties)
            bases = [
                properties['__model_factory__'].build_model(
                    modelname, bases, properties)]

            properties = {}
            registry.add_in_registry(namespace, bases[0])
            registry.loaded_namespaces[namespace] = bases[0]
            registry.call_plugins('after_model_construction', bases[0],
                                  namespace, transformation_properties)

        return bases, properties

    @classmethod
    def assemble_callback(cls, registry):
        """ Assemble callback is called to assemble all the Model
        from the installed bloks

        :param registry: registry to update
        """
        registry.loaded_namespaces_first_step = {}
        registry.loaded_views = {}

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
