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
import inspect
from copy import deepcopy

from sqlalchemy import inspection
from sqlalchemy.orm import declared_attr
from texttable import Texttable

from anyblok import Declarations
from anyblok.common import (
    BaseModelFirstStepList,
    BaseModelSecondStepList,
    anyblok_column_prefix,
)
from anyblok.mapper import ModelAttribute, format_schema
from anyblok.registry import RegistryManager

from .exceptions import ModelException
from .factory import ModelFactory, has_sql_fields
from .plugins import get_model_plugins


def has_sqlalchemy_fields(base):
    for p in base.__dict__.keys():
        attr = base.__dict__[p]
        if inspection.inspect(attr, raiseerr=False) is not None:
            return True

    return False


def autodoc_fields(declaration_cls, model_cls):  # pragma: no cover
    """Produces autodocumentation table for the fields.

    Exposed as a function in order to be reusable by a simple export,
    e.g., from anyblok.mixin.
    """
    if not has_sql_fields([model_cls]):
        return ""

    rows = [["Fields", ""]]
    fields = {}
    fields.update(model_cls.__dict__.get("__declared_fields__", {}))
    fields.update(model_cls.__dict__.get("__declared_columns__", {}))
    fields.update(model_cls.__dict__.get("__declared_relationships__", {}))
    rows.extend([x, y.autodoc()] for x, y in fields.items())
    table = Texttable(max_width=0)
    table.set_cols_valign(["m", "t"])
    table.add_rows(rows)
    return table.draw() + "\n\n"


def update_factory(kwargs):
    if "factory" in kwargs:
        kwargs["__model_factory__"] = kwargs.pop("factory")


def check_model_base(cls, registryname):
    if has_sqlalchemy_fields(cls):
        raise ModelException("the base %r have an SQLAlchemy attribute" % cls)

    if hasattr(cls, "__table_args__"):
        raise ModelException(
            "'__table_args__' attribute is forbidden, on Model : %r (%r)."
            "Use the class method 'define_table_args' to define the value "
            "allow anyblok to fill his own '__table_args__' attribute"
            % (registryname, cls.__table_args__)
        )

    if hasattr(cls, "__mapper_args__"):
        raise ModelException(
            "'__mapper_args__' attribute is forbidden, on Model : %r (%r)."
            "Use the class method 'define_mapper_args' to define the "
            "value allow anyblok to fill his own '__mapper_args__' "
            "attribute" % (registryname, cls.__mapper_args__)
        )


@Declarations.add_declaration_type(
    isAnEntry=True,
    pre_assemble="pre_assemble_callback",
    assemble="assemble_callback",
    initialize="initialize_callback",
)
class Model:
    """The Model class is used to define or inherit an SQL table.

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
        plugins_by = {}
        for plugin in get_model_plugins(registry):
            for attr, func in inspect.getmembers(
                plugin, predicate=inspect.ismethod
            ):
                by = plugins_by.setdefault(attr, [])
                by.append(func)

        def call_plugins(method, *args, **kwargs):
            """call the method on each plugin"""
            for func in plugins_by.get(method, []):
                func(*args, **kwargs)

        registry.call_plugins = call_plugins

    @classmethod
    def register(self, parent, name, cls_, **kwargs):
        """add new sub registry in the registry

        :param parent: Existing global registry
        :param name: Name of the new registry to add it
        :param cls_: Class Interface to add in registry
        """
        _registryname = parent.__registry_name__ + "." + name
        check_model_base(cls_, _registryname)

        if "tablename" in kwargs:
            tablename = kwargs.pop("tablename")
            if not isinstance(tablename, str):
                tablename = tablename.__tablename__

        elif hasattr(parent, name):
            tablename = getattr(parent, name).__tablename__
        else:
            if parent is Declarations or parent is Declarations.Model:
                tablename = name.lower()
            elif hasattr(parent, "__tablename__"):
                tablename = parent.__tablename__
                tablename += "_" + name.lower()

        if not hasattr(parent, name):
            p = {
                "__tablename__": tablename,
                "__registry_name__": _registryname,
                "use": lambda x: ModelAttribute(_registryname, x),
            }
            ns = type(name, tuple(), p)
            setattr(parent, name, ns)

        if parent is Declarations:
            return  # pragma: no cover

        kwargs["__registry_name__"] = _registryname
        kwargs["__tablename__"] = tablename
        update_factory(kwargs)

        RegistryManager.add_entry_in_register(
            "Model", _registryname, cls_, **kwargs
        )
        setattr(cls_, "__anyblok_kwargs__", kwargs)

    @classmethod
    def unregister(self, entry, cls_):
        """Remove the Interface from the registry

        :param entry: entry declaration of the model where the ``cls_``
            must be removed
        :param cls_: Class Interface to remove in registry
        """
        RegistryManager.remove_in_register(cls_)

    @classmethod
    def declare_field(
        cls,
        registry,
        name,
        field,
        namespace,
        properties,
        transformation_properties,
    ):
        """Declare the field/column/relationship to put in the properties
        of the model

        :param registry: the current  registry
        :param name: name of the field / column or relationship
        :param field: the declaration field / column or relationship
        :param namespace: the namespace of the model
        :param properties: the properties of the model
        """
        if name in properties["loaded_columns"]:
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
                    registry, namespace, name, properties
                )

            properties[attr_name] = declared_attr(wrapper)
            properties[attr_name].anyblok_field = field
        else:
            properties[attr_name] = field.get_sqlalchemy_mapping(
                registry, namespace, name, properties
            )

        if field.use_hybrid_property:
            properties[name] = field.get_property(
                registry, namespace, name, properties
            )
            properties[name].sqla_column = properties[attr_name]

            properties["hybrid_property_columns"].append(name)

        def field_description():
            return registry.get(namespace).fields_description(name)[name]

        def from_model():
            return registry.get(namespace)

        properties[name].anyblok_field_name = name
        properties[name].anyblok_registry_name = namespace
        properties[name].field_description = field_description
        properties[name].from_model = from_model
        properties["loaded_columns"].append(name)
        field.update_properties(registry, namespace, name, properties)

    @classmethod
    def transform_base(
        cls, registry, namespace, base, transformation_properties
    ):
        """Detect specific declaration which must define by registry

        :param registry: the current registry
        :param namespace: the namespace of the model
        :param base: One of the base of the model
        :param transformation_properties: the properties of the model
        :rtype: new base
        """
        registry.call_plugins(
            "transform_base", namespace, base, transformation_properties
        )

    @classmethod
    def load_namespace_first_step(cls, registry, namespace):
        """Return the properties of the declared bases for a namespace.
        This is the first step because some actions need to known all the
        properties

        :param registry: the current registry
        :param namespace: the namespace of the model
        :rtype: dict of the known properties
        """
        if namespace in registry.loaded_namespaces_first_step:
            return registry.loaded_namespaces_first_step[namespace]

        ns = registry.loaded_registries[namespace]
        properties = {}
        bases = BaseModelFirstStepList(cls, registry, properties)
        db_schema = format_schema(None, namespace)

        for b in ns["bases"][::-1]:
            for b_ns in b.__anyblok_bases__:
                bases.insert(0, b_ns.__registry_name__)

            bases.insert(0, b)
            if hasattr(b, "__db_schema__"):
                db_schema = format_schema(b.__db_schema__, namespace)

        properties.update(
            {
                "__db_schema__": db_schema,
                "__bases__": bases,
            }
        )
        if "__tablename__" in ns["properties"]:
            properties["__tablename__"] = ns["properties"]["__tablename__"]

        registry.loaded_namespaces_first_step[namespace] = properties
        return properties

    @classmethod
    def apply_inheritance_base(
        cls,
        registry,
        namespace,
        first_step,
        bases,
        realregistryname,
        properties,
        transformation_properties,
    ):
        kwargs = {"namespace": realregistryname} if realregistryname else {}
        for base in first_step["__bases__"][::-1]:
            if isinstance(base, str):
                tp = transformation_properties
                if base in registry.loaded_registries["Mixin_names"]:
                    bs, _ = cls.load_namespace_second_step(
                        registry,
                        base,
                        realregistryname=realregistryname or namespace,
                        transformation_properties=tp,
                    )
                elif base in registry.loaded_registries["Model_names"]:
                    bs, _ = cls.load_namespace_second_step(registry, base)
                else:
                    raise ModelException(  # pragma: no cover
                        "You have not to inherit the %r "
                        "Only the 'Mixin' and %r types are allowed"
                        % (base, cls.__name__)
                    )

                for bs_ in bs[::-1]:
                    bases.insert(0, bs_)
            else:
                bases.insert(0, base, **kwargs)
                if base.__doc__:
                    properties["__doc__"] = base.__doc__

    @classmethod
    def init_core_properties_and_bases(cls, registry, bases, properties):
        properties["loaded_columns"] = []
        properties["hybrid_property_columns"] = []
        properties["loaded_fields"] = {}
        properties["__model_factory__"].insert_core_bases(bases, properties)

    @classmethod
    def declare_all_fields(
        cls, registry, namespace, properties, transformation_properties
    ):
        # do in the first time the fields and columns
        # because for the relationship on the same model
        # the primary keys must exist before the relationship
        # load all the base before do relationship because primary key
        # can be come from inherit
        for key in (
            "__declared_fields__",
            "__declared_columns__",
            "__declared_relationships__",
        ):
            for p, f in transformation_properties[key].items():
                cls.declare_field(
                    registry,
                    p,
                    f,
                    namespace,
                    properties,
                    transformation_properties,
                )

    @classmethod
    def apply_existing_table(
        cls,
        registry,
        namespace,
        tablename,
        properties,
        bases,
        transformation_properties,
    ):
        if "__tablename__" in properties:
            del properties["__tablename__"]

        for t in registry.loaded_namespaces.keys():
            m = registry.loaded_namespaces[t]
            if m.is_sql:
                if getattr(m, "__tablename__"):
                    if m.__tablename__ == tablename:
                        properties["__table__"] = m.__table__
                        tablename = namespace.replace(".", "_").lower()

        for p, f in transformation_properties["__declared_fields__"].items():
            cls.declare_field(
                registry,
                p,
                f,
                namespace,
                properties,
                transformation_properties,
            )

    @classmethod
    def load_namespace_second_step(
        cls,
        registry,
        namespace,
        realregistryname=None,
        transformation_properties=None,
    ):
        """Return the bases and the properties of the namespace

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

        ns = registry.loaded_registries[namespace]
        bases = BaseModelSecondStepList(
            Model, registry, namespace, transformation_properties
        )
        properties = ns["properties"].copy()
        first_step = registry.loaded_namespaces_first_step[namespace]
        properties["__db_schema__"] = first_step.get("__db_schema__", None)

        registry.call_plugins(
            "initialisation_tranformation_properties",
            properties,
            transformation_properties,
        )

        properties["__model_factory__"] = properties.get(
            "__model_factory__", ModelFactory
        )(registry)

        cls.apply_inheritance_base(
            registry,
            namespace,
            first_step,
            bases,
            realregistryname,
            properties,
            transformation_properties,
        )
        if namespace in registry.loaded_registries["Model_names"]:
            tablename = properties["__tablename__"]
            modelname = namespace.replace(".", "")
            cls.init_core_properties_and_bases(registry, bases, properties)

            if tablename in registry.declarativebase.metadata.tables:
                cls.apply_existing_table(
                    registry,
                    namespace,
                    tablename,
                    properties,
                    bases,
                    transformation_properties,
                )
            else:
                cls.declare_all_fields(
                    registry,
                    namespace,
                    properties,
                    transformation_properties,
                )

            bases.append(registry.registry_base)

            registry.call_plugins(
                "before_model_construction",
                namespace,
                first_step,
                properties,
                transformation_properties,
            )
            bases = [
                properties["__model_factory__"].build_model(
                    modelname, bases, properties
                )
            ]

            properties = {}
            registry.add_in_registry(namespace, bases[0])
            registry.loaded_namespaces[namespace] = bases[0]
            registry.call_plugins(
                "after_model_construction",
                bases[0],
                namespace,
                transformation_properties,
            )

        return bases, properties

    @classmethod
    def assemble_callback(cls, registry):
        """Assemble callback is called to assemble all the Model
        from the installed bloks

        :param registry: registry to update
        """
        registry.loaded_namespaces_first_step = {}
        registry.loaded_views = {}

        # get all the information to create a namespace
        for namespace in registry.loaded_registries["Model_names"]:
            cls.load_namespace_first_step(registry, namespace)

        # create the namespace with all the information come from first
        # step
        for namespace in registry.loaded_registries["Model_names"]:
            cls.load_namespace_second_step(registry, namespace)

    @classmethod
    def initialize_callback(cls, registry):
        """initialize callback is called after assembling all entries

        This callback updates the database information about

        * Model
        * Column
        * RelationShip

        :param registry: registry to update
        """
        for Model in registry.loaded_namespaces.values():
            Model.initialize_model()
            if not registry.loadwithoutmigration:
                Model.clear_all_model_caches()

        if registry.loadwithoutmigration:
            return False

        Blok = registry.System.Blok
        if not registry.withoutautomigration:
            registry.update_blok_list()

        bloks = Blok.list_by_state("touninstall")
        Blok.uninstall_all(*bloks)
        return Blok.apply_state(*registry.ordered_loaded_bloks)
