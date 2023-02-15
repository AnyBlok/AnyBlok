# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2016 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2021 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from logging import getLogger
import warnings
from sqlalchemy import create_engine, event, MetaData, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import (ProgrammingError, OperationalError,
                            InvalidRequestError)
from sqlalchemy_utils.functions import database_exists
from .config import Configuration, get_url
from .migration import Migration
from .blok import BlokManager
from .environment import EnvironmentManager
from .authorization.query import QUERY_WITH_NO_RESULTS, PostFilteredQuery
from anyblok.common import anyblok_column_prefix, naming_convention
from pkg_resources import iter_entry_points
from .version import parse_version
from .logging import log
from sqlalchemy.orm.session import close_all_sessions
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm.decl_base import _declarative_constructor
from sqlalchemy.orm.decl_api import DeclarativeMeta, registry as SQLARegistry

try:
    import pyodbc
    pyodbc.pooling = False
    PyODBCProgrammingError = pyodbc.ProgrammingError
except ImportError:

    class PyODBCProgrammingError(Exception):
        pass

logger = getLogger(__name__)


class RegistryManagerException(Exception):
    """ Simple Exception for Registry """


class RegistryException(Exception):
    """ Simple Exception for Registry """


class RegistryConflictingException(Exception):
    """ Simple Exception for Registry """


class RegistryManager:
    """ Manage the global registry

    Add new entry::

        RegistryManager.declare_entry('newEntry')
        RegistryManager.init_blok('newBlok')
        EnvironmentManager.set('current_blok', 'newBlok')
        RegistryManager.add_entry_in_register(
            'newEntry', 'oneKey', cls_)
        EnvironmentManager.set('current_blok', None)

    Remove an existing entry::

        if RegistryManager.has_entry_in_register('newBlok', 'newEntry',
                                                        'oneKey'):
            RegistryManager.remove_entry_in_register(
                'newBlok', 'newEntry', 'oneKey', cls_)

    get a new registry for a database::

        registry = RegistryManager.get('my database')

    """

    loaded_bloks = {}
    declared_entries = []
    declared_cores = []
    callback_pre_assemble_entries = {}
    callback_assemble_entries = {}
    callback_initialize_entries = {}
    callback_unload_entries = {}
    registries = {}

    @classmethod
    def has_blok(cls, blok):
        """ Return True if the blok is already loaded

        :param blok: name of the blok
        :rtype: boolean
        """

        return blok in cls.loaded_bloks

    @classmethod
    def clear(cls):
        """ Clear the registry dict to force the creation of new registry """
        registries = [r for r in cls.registries.values()]
        for registry in registries:
            registry.close()

    @classmethod
    def unload(cls):
        """Call all the unload callbacks"""
        for entry, unload_callback in cls.callback_unload_entries.items():
            logger.info('Unload: %r' % entry)
            unload_callback()  # pragma: no cover

    @classmethod
    def get(cls, db_name, loadwithoutmigration=False, log_repeat=True,
            **kwargs):
        """ Return an existing Registry

        If the Registry doesn't exist then the Registry are created and added
        to registries dict

        :param db_name: the name of the database linked to this registry
        :param loadwithoutmigration: if True, registry is created without
                                     any migration of the database
        :param log_repeat: if False, when the registry is load whitout
                           migration, the warning is not logged
        :rtype: ``Registry``
        """
        EnvironmentManager.set('db_name', db_name)
        if db_name in cls.registries:
            if loadwithoutmigration and log_repeat:
                logger.warning(
                    "Ignoring loadwithoutmigration=True for database %r "
                    "because its registry is already loaded", db_name)
            return cls.registries[db_name]

        _Registry = Configuration.get('Registry', Registry)
        logger.info("Loading registry for database %r with class %r",
                    db_name, _Registry)
        registry = _Registry(
            db_name, loadwithoutmigration=loadwithoutmigration, **kwargs)
        cls.registries[db_name] = registry
        return registry

    @classmethod
    def reload(cls):
        """ Reload the blok

        The purpose is to reload the python module to get changes in python
        file

        """
        for registry in cls.registries.values():
            registry.close_session()
            registry.Session = None
            registry.blok_list_is_loaded = False
            if registry.unittest:
                registry.init_bind()

            registry.reload()

    @classmethod
    def declare_core(cls, core):
        """ Add new core in the declared cores

        ::

            RegistryManager.declare_core('Core name')

            -----------------------------------------

            @Declarations.register(Declarations.Core)
            class ``Core name``:
                ...

        .. warning::

            The core must be declared in the application, not in the bloks
            The declaration must be done before the loading of the bloks

        :param core: core name
        """

        if core not in cls.declared_cores:
            cls.declared_cores.append(core)

    @classmethod
    def undeclare_core(cls, core):
        if core in cls.declared_cores:
            cls.declared_cores.remove(core)

    @classmethod
    def declare_entry(cls, entry,
                      pre_assemble_callback=None,
                      assemble_callback=None,
                      initialize_callback=None):
        """ Add new entry in the declared entries

        ::

            def assemble_callback(registry):
                ...

            def initialize_callback(registry):
                ...

            RegistryManager.declare_entry(
                'Entry name', assemble_callback=assemble_callback,
                initialize_callback=initialize_callback)

            @Declarations.register(Declarations.``Entry name``)
            class MyClass:
                ...

        .. warning::

            The entry must be declared in the application, not in the bloks
            The declaration must be done before the loading of the bloks

        :param entry: entry name
        :param assemble_callback: function callback to call to assemble
        :param initialize_callback: function callback to call to init after
            assembling
        """

        if entry not in cls.declared_entries:
            cls.declared_entries.append(entry)

            if pre_assemble_callback:
                cls.callback_pre_assemble_entries[entry] = pre_assemble_callback

            if assemble_callback:
                cls.callback_assemble_entries[entry] = assemble_callback

            if initialize_callback:
                cls.callback_initialize_entries[entry] = initialize_callback

    @classmethod
    def declare_unload_callback(cls, entry, unload_callback):
        """Save a unload callback in registry Manager

        :param entry: declaration type name
        :param unload_callback: classmethod pointer
        """
        cls.callback_unload_entries[  # pragma: no cover
            entry] = unload_callback

    @classmethod
    def undeclare_entry(cls, entry):
        if entry in cls.declared_entries:
            cls.declared_entries.remove(entry)

            if entry in cls.callback_pre_assemble_entries:
                del cls.callback_pre_assemble_entries[  # pragma: no cover
                    entry]

            if entry in cls.callback_assemble_entries:
                del cls.callback_assemble_entries[entry]

            if entry in cls.callback_initialize_entries:
                del cls.callback_initialize_entries[entry]

    @classmethod
    def init_blok(cls, blokname):
        """ init one blok to be known by the RegistryManager

        All bloks loaded must be initialized because the registry will be
        created with this information

        :param blokname: name of the blok
        """
        blok = {
            'Core': {core: [] for core in cls.declared_cores},
            'properties': {},
            'removed': [],
        }
        for de in cls.declared_entries:
            blok[de] = {'registry_names': []}

        cls.loaded_bloks[blokname] = blok

    @classmethod
    def has_core_in_register(cls, blok, core):
        """ Return True if One Class exist in this blok for this core

        :param blok: name of the blok
        :param core: is the existing core name
        """
        return len(cls.loaded_bloks[blok]['Core'][core]) > 0

    @classmethod
    def add_core_in_register(cls, core, cls_):
        """ Load core in blok

        warning the global var current_blok must be filled on the good blok

        :param core: is the existing core name
        :param ``cls_``: Class of the Core to save in loaded blok target
            registry
        """

        current_blok = EnvironmentManager.get('current_blok')
        cls.loaded_bloks[current_blok]['Core'][core].append(cls_)

    @classmethod
    def remove_in_register(cls, cls_):
        """ Remove Class in blok and in entry

        :param ``cls_``: Class of the entry / key to remove in loaded blok
        """
        current_blok = EnvironmentManager.get('current_blok')
        removed = cls.loaded_bloks[current_blok]['removed']
        if cls_ not in removed:
            removed.append(cls_)

    @classmethod
    def has_entry_in_register(cls, blok, entry, key):
        """ Return True if One Class exist in this blok for this entry

        :param blok: name of the blok
        :param entry: is the existing entry name
        :param key: is the existing key in the entry
        """
        if entry not in cls.loaded_bloks[blok]:
            return False

        if key not in cls.loaded_bloks[blok][entry]:
            return False

        return len(cls.loaded_bloks[blok][entry][key]['bases']) > 0

    @classmethod
    def add_entry_in_register(cls, entry, key, cls_, **kwargs):
        """ Load entry in blok

        warning the global var current_blok must be filled on the good blok
        :param entry: is the existing entry name
        :param key: is the existing key in the entry
        :param ``cls_``: Class of the entry / key to remove in loaded blok
        """

        bases = []

        for base in cls_.__bases__:
            if hasattr(base, '__registry_name__'):
                bases.append(base)

        setattr(cls_, '__anyblok_bases__', bases)

        cb = EnvironmentManager.get('current_blok')

        if key not in cls.loaded_bloks[cb][entry]:
            cls.loaded_bloks[cb][entry][key] = {
                'bases': [],
                'properties': {},
            }

        cls.loaded_bloks[cb][entry][key]['properties'].update(kwargs)
        # Add before in registry because it is the same order than the
        # inheritance __bases__ and __mro__
        cls.loaded_bloks[cb][entry][key]['bases'].insert(0, cls_)

        if key not in cls.loaded_bloks[cb][entry]['registry_names']:
            cls.loaded_bloks[cb][entry]['registry_names'].append(key)

    @classmethod
    def get_entry_properties_in_register(cls, entry, key):
        cb = EnvironmentManager.get('current_blok')
        if key not in cls.loaded_bloks[cb][entry]:
            return {}  # pragma: no cover

        return cls.loaded_bloks[cb][entry][key]['properties'].copy()

    @classmethod
    def has_blok_property(cls, property_):
        """ Return True if the property exists in blok

        :param property_: name of the property
        """
        blok = EnvironmentManager.get('current_blok')

        if property_ in cls.loaded_bloks[blok]['properties']:
            return True

        return False

    @classmethod
    def add_or_replace_blok_property(cls, property_, value):
        """ Save the value in the properties

        :param property_: name of the property
        :param value: the value to save, the type is not important
        """
        blok = EnvironmentManager.get('current_blok')
        cls.loaded_bloks[blok]['properties'][property_] = value

    @classmethod
    def get_blok_property(cls, property_, default=None):
        """ Return the value in the properties

        :param property_: name of the property
        :param default: return default If not entry in the property
        """
        blok = EnvironmentManager.get('current_blok')
        return cls.loaded_bloks[blok]['properties'].get(property_, default)

    @classmethod
    def remove_blok_property(cls, property_):
        """ Remove the property if exist

        :param property_: name of the property
        """
        blok = EnvironmentManager.get('current_blok')
        if cls.has_blok_property(property_):
            del cls.loaded_bloks[blok]['properties'][property_]


class NewSQLARegistry(SQLARegistry):

    def __getattr__(self, key):
        sself = super(NewSQLARegistry, self)
        if hasattr(sself, key):
            return getattr(sself, key)  # pragma: no cover

        warnings.warn(
            "'registry' attribute is deprecated because SQLAlchemy 1.4 add is "
            "own 'registry' attribute. Replace it by 'anyblok' attribute",
            DeprecationWarning, stacklevel=2)
        return getattr(self._class_registry['registry'], key)


class DeprecatedClassProperty:
    def __init__(self, registry):
        self.registry = registry

    def __getattr__(self, key, **kw):  # pragma: no cover
        warnings.warn(
            "'registry' attribute is deprecated because SQLAlchemy 1.4 add is "
            "own 'registry' attribute. Replace it by 'anyblok' attribute",
            DeprecationWarning, stacklevel=2)
        return getattr(self.registry, key, **kw)

    def __setattr__(self, key, value):  # pragma: no cover
        if key == 'registry':
            return super().__setattr__(key, value)

        warnings.warn(
            "'registry' attribute is deprecated because SQLAlchemy 1.4 add is "
            "own 'registry' attribute. Replace it by 'anyblok' attribute",
            DeprecationWarning, stacklevel=2)
        return setattr(self.registry, key, value)


def declarative_base(
    bind=None,
    metadata=None,
    mapper=None,
    cls=object,
    name="Base",
    constructor=_declarative_constructor,
    class_registry=None,
    metaclass=DeclarativeMeta,
):
    return NewSQLARegistry(
        _bind=bind,
        metadata=metadata,
        class_registry=class_registry,
        constructor=constructor,
    ).generate_base(
        mapper=mapper,
        cls=cls,
        name=name,
        metaclass=metaclass,
    )


class Registry:
    """ Define one registry

    A registry is linked to a database, and stores the definition of the
    installed Bloks, Models, Mixins for this database::

        registry = Registry('My database')
    """

    def __init__(self, db_name, loadwithoutmigration=False, unittest=False,
                 **kwargs):
        self.db_name = db_name
        self.loadwithoutmigration = loadwithoutmigration
        self.unittest = unittest
        self.additional_setting = kwargs
        self.init_engine(db_name=db_name)
        self.init_bind()
        self.registry_base = type("RegistryBase", tuple(), {
            'anyblok': self,
            'registry': DeprecatedClassProperty(self),  # For Model No SQL
            'Env': EnvironmentManager})
        self.withoutautomigration = Configuration.get('withoutautomigration')
        self.ini_var()
        self.Session = None
        self.nb_query_bases = self.nb_session_bases = 0
        self.blok_list_is_loaded = False
        self.pre_assemble_entries()
        self.load()

    def init_bind(self):
        """Initialize the bind"""
        if self.unittest:
            self.bind = self.engine.connect()
            self.unittest_transaction = self.bind.begin()
        else:
            self.bind = self.engine
            self.unittest_transaction = None

    def init_engine_options(self, url):
        """Define the options to initialize the engine"""
        return dict(
            echo=Configuration.get('db_echo') or False,
            max_overflow=Configuration.get('db_max_overflow') or 10,
            echo_pool=Configuration.get('db_echo_pool') or False,
            pool_size=Configuration.get('db_pool_size') or 5,
            isolation_level=self.additional_setting.get(
                'isolation_level',
                Configuration.get('isolation_level', 'READ_UNCOMMITTED')
            ),
        )

    def init_engine(self, db_name=None):
        """Define the engine

        :param db_name: name of the database to link
        """
        url = Configuration.get('get_url', get_url)(db_name=db_name)
        kwargs = self.init_engine_options(url)
        kwargs['future'] = True
        self.rw_engine = create_engine(url, **kwargs)
        self.apply_engine_events(self.rw_engine)

    def apply_engine_events(self, engine):
        """Add engine events

        the engine event come from:

        * entrypoints: ``anyblok.engine.event``
        * entrypoints: ``anyblok.engine.event.**dialect's name**``
        * registry additional_setting: ``anyblok.engine.event``
        """
        def _apply_engine_events(key):
            for i in iter_entry_points(key):
                logger.info('Update engine event for %s from entrypoint %r' % (
                    key, i))
                i.load()(engine)

        _apply_engine_events('anyblok.engine.event')
        _apply_engine_events('anyblok.engine.event.' + engine.dialect.name)

        for funct in self.additional_setting.get('anyblok.engine.event', []):
            logger.info('Update engine event %r' % funct)
            funct(engine)

    @property
    def engine(self):
        """property to get the engine"""
        return self.rw_engine

    def ini_var(self):
        """ Initialize the var to load the registry """
        self.loaded_namespaces = {}
        self.declarativebase = None
        self.loaded_bloks = {}
        self.loaded_registries = {x + '_names': []
                                  for x in RegistryManager.declared_entries}
        self.loaded_cores = {core: []
                             for core in RegistryManager.declared_cores}
        self.ordered_loaded_bloks = []
        self.loaded_namespaces = {}
        self.children_namespaces = {}
        self.properties = {}
        self.removed = []
        EnvironmentManager.set('_precommit_hook', [])
        EnvironmentManager.set('_postcommit_hook', [])
        self._sqlalchemy_known_events = []
        self.expire_attributes = {}

        # key = tablename
        # value = True if all table else list of columns names
        self.ignore_migration_for = {}

    @classmethod
    def db_exists(cls, db_name=None):
        if not db_name:
            raise RegistryException('db_name is required')

        url = Configuration.get('get_url', get_url)(db_name=db_name)
        return database_exists(url)

    def listen_sqlalchemy_known_event(self):
        for e, namespace, method in self._sqlalchemy_known_events:
            if hasattr(method, 'get_attribute'):
                method = method.get_attribute(self)

            event.listen(e.mapper(self, namespace, usehybrid=False), e.event,
                         method, *e.args, **e.kwargs)

    def remove_sqlalchemy_known_event(self):
        for e, namespace, method in self._sqlalchemy_known_events:
            try:
                if hasattr(method, 'get_attribute'):
                    method = method.get_attribute(self)

                event.remove(e.mapper(self, namespace), e.event,
                             method)
            except InvalidRequestError:
                pass

    def get(self, namespace):
        """ Return the namespace Class

        :param namespace: namespace to get from the registry str
        :rtype: namespace cls
        :exception: RegistryManagerException
        """
        if namespace not in self.loaded_namespaces:
            raise RegistryManagerException(
                "No namespace %r loaded" % namespace)

        return self.loaded_namespaces[namespace]

    def has(self, namespace):
        return True if namespace in self.loaded_namespaces else False

    def get_bloks_by_states(self, *states):
        """ Return the bloks in these states

        :param states: list of the states
        :rtype: list of blok's name
        """
        if not states:
            return []

        res = []
        query = """SELECT "order", name"""
        query += " FROM system_blok"
        query += " WHERE state in ('%s')" % "', '".join(states)
        try:
            res = self.execute(text(query), fetchall=True)
        except (ProgrammingError, OperationalError, PyODBCProgrammingError):
            # During the first connection the database is empty
            pass

        if res:
            res.sort()
            return [x[1] for x in res]

        return []

    def get_bloks_to_load(self):
        """ Return the bloks to load by the registry

        :rtype: list of blok's name
        """
        return self.get_bloks_by_states('installed', 'toupdate')

    def get_bloks_to_install(self, loaded):
        """ Return the bloks to install in the registry

        :rtype: list of blok's name
        """
        toinstall = self.get_bloks_by_states('toinstall')
        for blok in BlokManager.auto_install:
            if blok not in (toinstall + loaded):
                toinstall.append(blok)

        if toinstall and self.withoutautomigration:
            raise RegistryManagerException(  # pragma: no cover
                "Install modules %r is forbidden with no auto migration "
                "mode" % toinstall)

        return toinstall

    def check_permission(self, target, principals, permission):
        """Check that one of the principals has permisson on target.

        :param target: model instance (record) or class. Checking a permission
                       on a model class with a policy that needs to work on
                       records is considered a configuration error: the policy
                       has the right to fail.
        :param principals: list, set or tuple of strings
        :rtype: bool
        """
        return self.lookup_policy(target, permission).check(
            target, principals, permission)

    def wrap_query_permission(self, query, principals, permission, models=()):
        """Wrap query to return only authorized results

        :param principals: list, set or tuple of strings
        :param models: models on which to apply security filtering. If
                       not supplied, it will be infered from the query. The
                       length and ordering much match that of expected results.
        :returns: a query-like object, implementing the results fetching API,
                  but that can't be further filtered.

        This method calls all the relevant policies to apply pre- and
        post-filtering. Although postfiltering is discouraged in authorization
        policies for performance and expressiveness (limit, offset),
        there are cases for which it is unavoidable, or in which the tradeoff
        goes the other way.

        In normal operation, the relevant models are infered directly from
        the query.
        For join situations, and more complex queries, the caller has control
        on the models on which to exert permission checking.

        For instance, it might make sense to use a join between Model1 and
        Model2 to actually constrain Model1 (on which permission filtering
        should occur) by information contained in Model2, even if the passed
        principals should not grant access to the relevant Model2 records.
        """
        if not models:
            models = []
            for column in query.column_descriptions:
                if column['aliased']:
                    # actually, think aliases could work almost direcly
                    # it's just a matter of documenting that what the policy
                    # gets may be an alias instead of a model.
                    raise NotImplementedError(  # pragma: no cover
                        "Sorry, table/model aliases aren't supported yet. "
                        "Here's the unsupported column: %r" % column)
                if not issubclass(column['type'], self.registry_base):
                    raise NotImplementedError(  # pragma: no cover
                        "Sorry, only model columns are supported for now. "
                        "Here is the unsupported one: %r" % column)
                models.append(column['type'])

        postfilters = {}
        for model in models:
            policy = self.lookup_policy(model, permission)
            query = policy.filter(model, query, principals, permission)
            if query is False:  # TODO use a dedicated singleton ?
                return QUERY_WITH_NO_RESULTS
            if policy.postfilter is not None:  # pragma: no cover
                postfilters[model] = lambda rec: policy.postfilter(
                    rec, principals, permission)
        return PostFilteredQuery(query, postfilters)

    def lookup_policy(self, target, permission):
        """Return the policy instance that applies to target or its model.

        :param target: model class or instance

        If a policy is declared for the precise permission, it is returned.
        Otherwise, the default policy for that model is returned.
        By ultimate default the special
        :class:`anyblok.authorization.rule.DenyAll` is returned.
        """
        model_name = target.__registry_name__
        policy = self._authz_policies.get((model_name, permission))
        if policy is not None:
            return policy

        policy = self._authz_policies.get(model_name)
        if policy is not None:
            return policy

        return self._authz_policies.get(None)

    def load_entry(self, blok, entry):
        """ load one entry type for one blok

        :param blok: name of the blok
        :param entry: declaration type to load
        """
        _entry = RegistryManager.loaded_bloks[blok][entry]
        for key in _entry['registry_names']:
            v = _entry[key]
            if key not in self.loaded_registries:
                self.loaded_registries[key] = {'properties': {}, 'bases': []}

            self.loaded_registries[key]['properties'].update(v['properties'])
            old_bases = [] + self.loaded_registries[key]['bases']
            self.loaded_registries[key]['bases'] = v['bases']
            self.loaded_registries[key]['bases'] += old_bases
            self.loaded_registries[entry + '_names'].append(key)

    def load_core(self, blok, core):
        """ load one core type for one blok

        :param blok: name of the blok
        :param core: the core name to load
        """
        if core in RegistryManager.loaded_bloks[blok]['Core']:
            bases = RegistryManager.loaded_bloks[blok]['Core'][core]
            for base in bases:
                self.loaded_cores[core].insert(0, base)
        else:
            logger.warning('No Core %r found' % core)

    def load_properties(self, blok):
        properties = RegistryManager.loaded_bloks[blok]['properties']
        for k, v in properties.items():  # pragma: no cover
            if k not in self.properties:
                self.properties[k] = v
            elif isinstance(self.properties[k], dict) and isinstance(v, dict):
                self.properties.update(v)
            elif isinstance(self.properties[k], list) and isinstance(v, list):
                self.properties.extend(v)
            else:
                self.properties[k] = v

    def load_removed(self, blok):
        for removed in RegistryManager.loaded_bloks[blok]['removed']:
            if removed not in self.removed:
                self.removed.append(removed)

    def load_bloks(self, bloks, toinstall, toload, required=True):
        for blok in bloks:
            if required:
                if not self.load_blok(blok, toinstall, toload):
                    raise RegistryManagerException(  # pragma: no cover
                        "Required blok %r not found" % blok)
            elif toinstall or blok in toload:
                self.load_blok(blok, toinstall, toload)

    def load_blok(self, blok, toinstall, toload):
        """ load on blok, load all the core and all the entry for one blok

        :param blok: name of the blok
        :exception: RegistryManagerException
        """
        if blok in self.ordered_loaded_bloks:
            return True

        if blok not in BlokManager.bloks:
            return False  # pragma: no cover

        b = BlokManager.bloks[blok](self)
        self.load_bloks(b.required + b.conditional, toinstall, toload)
        self.load_bloks(b.optional, toinstall, toload, required=False)

        for core in RegistryManager.declared_cores:
            self.load_core(blok, core)

        for entry in RegistryManager.declared_entries:
            self.load_entry(blok, entry)

        self.load_properties(blok)
        self.load_removed(blok)
        self.loaded_bloks[blok] = b
        self.ordered_loaded_bloks.append(blok)
        logger.debug("Blok %r loaded" % blok)
        return True

    def check_dependencies(self, blok, dependencies_to_install, toinstall):
        if blok in dependencies_to_install:
            return True

        if blok not in BlokManager.bloks:
            return False  # pragma: no cover

        b = BlokManager.bloks[blok](self)
        for required in b.required:
            if not self.check_dependencies(required, dependencies_to_install,
                                           toinstall):
                raise RegistryManagerException(  # pragma: no cover
                    "%r: Required blok not found %r" % (blok, required))

        for optional in b.optional:
            self.check_dependencies(
                optional, dependencies_to_install, toinstall)

        if blok not in toinstall:
            dependencies_to_install.append(blok)

        return True

    def update_to_install_blok_dependencies_state(self, toinstall):
        dependencies_to_install = []

        for blok in toinstall:
            self.check_dependencies(blok, dependencies_to_install, toinstall)

        if dependencies_to_install:
            query = """
                update system_blok
                set state='toinstall'
                where name in ('%s')
                and state = 'uninstalled'""" % "', '".join(
                dependencies_to_install)
            try:
                self.execute(query)
            except (ProgrammingError, OperationalError):  # pragma: no cover
                pass

            return True

        return False

    def execute(self, *args, **kwargs):
        fetchall = kwargs.pop('fetchall', False)
        if self.Session:
            res = self.session.execute(*args, **kwargs)
            if fetchall:
                return res.fetchall()

            return res
        else:
            conn = None
            with self.engine.connect() as conn:
                res = conn.execute(*args, **kwargs)
                if fetchall:
                    return res.fetchall()

                return res  # pragma: no cover

    def get_namespace(self, parent, child):
        if hasattr(parent, child) and getattr(parent, child):
            return getattr(parent, child)

        tmpns = type(child, tuple(), {'children_namespaces': {}})
        if hasattr(parent, 'children_namespaces'):
            parent.children_namespaces[child] = tmpns

        setattr(parent, child, tmpns)
        return tmpns

    def final_namespace(self, parent, child, base):
        if hasattr(parent, child) and getattr(parent, child):
            other_base = self.get_namespace(parent, child)
            other_base = other_base.children_namespaces.copy()
            for ns, cns in other_base.items():
                setattr(base, ns, cns)

            if hasattr(parent, 'children_namespaces'):
                if child in parent.children_namespaces:
                    parent.children_namespaces[child] = base

        elif hasattr(parent, 'children_namespaces'):
            parent.children_namespaces[child] = base

        setattr(parent, child, base)

    def add_in_registry(self, namespace, base):
        """ Add a class as an attribute of the registry

        :param namespace: tree path of the attribute
        :param base: class to add
        """
        namespace = namespace.split('.')[1:]

        def update_namespaces(parent, namespaces):
            if len(namespaces) == 1:
                self.final_namespace(parent, namespaces[0], base)
            else:
                new_parent = self.get_namespace(parent, namespaces[0])
                update_namespaces(new_parent, namespaces[1:])

        update_namespaces(self, namespace)

    def create_session_factory(self):
        """Create the SQLA Session factory

        in function of the Core Session class ans the Core Qery class
        """
        if self.Session is None or self.must_recreate_session_factory():
            bind = self.bind
            if self.Session:
                if not self.withoutautomigration:
                    # this is the only case to use commit in the construction
                    # of the registry
                    self.commit()

                # remove all existing instance to create a new instance
                # because the instance are cached
                self.Session.remove()

            query_bases = [] + self.loaded_cores['Query']
            query_bases += [self.registry_base]
            Query = type('Query', tuple(query_bases), {})
            session_bases = [self.registry_base] + self.loaded_cores['Session']
            Session = type('Session', tuple(session_bases), {
                'registry_query': Query})

            self.Session = scoped_session(
                sessionmaker(bind=bind, class_=Session, future=True),
                EnvironmentManager.scoped_function_for_session())

            self.nb_query_bases = len(self.loaded_cores['Query'])
            self.nb_session_bases = len(self.loaded_cores['Session'])
            self.apply_session_events()
        else:
            self.flush()

    def must_recreate_session_factory(self):
        """Check if the SQLA Session Factory must be destroy and recreate

        :rtype: Boolean, True if nb Core Session/Query inheritance change
        """
        nb_query_bases = len(self.loaded_cores['Query'])
        if nb_query_bases != self.nb_query_bases:
            return True

        nb_session_bases = len(self.loaded_cores['Session'])
        if nb_session_bases != self.nb_session_bases:
            return True

        return False

    @log(logger, level='debug')
    def load(self):
        """ Load all the namespaces of the registry

        Create all the table, make the shema migration
        Update Blok, Model, Column rows
        """
        mustreload = False
        blok2install = None
        try:
            self.declarativebase = declarative_base(
                metadata=MetaData(naming_convention=naming_convention),
                class_registry=dict(registry=self))
            toload = self.get_bloks_to_load()
            toinstall = self.get_bloks_to_install(toload)
            if self.update_to_install_blok_dependencies_state(toinstall):
                toinstall = self.get_bloks_to_install(toload)
            if self.loadwithoutmigration and not toload and toinstall:
                logger.warning("Impossible to use loadwithoumigration")
                self.loadwithoutmigration = False  # pragma: no cover

            self.load_bloks(toload, False, toload)
            if toinstall and not self.loadwithoutmigration:
                blok2install = toinstall[0]
                self.load_blok(blok2install, True, toload)

            instrumentedlist_base = [] + self.loaded_cores['InstrumentedList']
            instrumentedlist_base += [list]
            self.InstrumentedList = type(
                'InstrumentedList', tuple(instrumentedlist_base), {})
            self.assemble_entries()
            self.create_session_factory()

            self.apply_model_schema_on_table(blok2install)
            self.listen_sqlalchemy_known_event()
            mustreload = self.is_reload_needed() or mustreload

        except Exception as e:
            self.close()
            raise e

        if len(toinstall) > 1 or mustreload:
            self.reload()
        else:
            self.System.Blok.load_all()

        self.loadwithoutmigration = False

    def apply_session_events(self):
        """Add session events

        the session event come from:

        * entrypoints: ``anyblok.session.event``
        * entrypoints: ``anyblok.session.event.**sgdb**``
        * registry additional_setting: ``anyblok.session.event``
        """
        def _apply_session_events(key):
            for i in iter_entry_points(key):
                logger.info(
                    'Update session event for %s from entrypoint %r' % (
                        key, i))
                i.load()(self.session)  # pragma: no cover

        _apply_session_events('anyblok.session.event')
        _apply_session_events(
            'anyblok.session.event.' + self.engine.dialect.name)

        for funct in self.additional_setting.get('anyblok.session.event', []):
            logger.info('Update session event %r' % funct)
            funct(self.session)

    def assemble_entries(self):
        for entry in RegistryManager.declared_entries:
            if entry in RegistryManager.callback_assemble_entries:
                logger.debug('Assemble %r entry' % entry)
                RegistryManager.callback_assemble_entries[entry](self)

    def pre_assemble_entries(self):
        for entry in RegistryManager.declared_entries:
            if entry in RegistryManager.callback_pre_assemble_entries:
                logger.debug('Pre assemble %r entry' % entry)
                RegistryManager.callback_pre_assemble_entries[entry](self)

    def apply_model_schema_on_table(self, blok2install):
        # replace the engine by the session.connection for bind attribute
        # because session.connection is already the connection use
        # by blok, migration and all write on the data base
        # or use engine for bind, force create_all method to create new
        # new connection, this new connection have not acknowedge of the
        # data in the session.connection, and risk of bad lock on the
        # tables
        if self.loadwithoutmigration:
            return

        if not self.withoutautomigration and blok2install == 'anyblok-core':
            self.declarativebase.metadata.tables['system_blok'].create(
                bind=self.connection(), checkfirst=True)

        self.migration = Configuration.get('Migration', Migration)(self)
        query = """
            SELECT name, installed_version
            FROM system_blok
            WHERE
                (state = 'toinstall' AND name = '%s')
                OR state = 'toupdate'""" % blok2install
        res = self.execute(query, fetchall=True)
        if res:
            for blok, installed_version in res:
                b = BlokManager.get(blok)(self)
                parsed_version = (
                    parse_version(installed_version)
                    if installed_version is not None
                    else None)
                b.pre_migration(parsed_version)

            self.migration.auto_upgrade_database(schema_only=True)
            if not self.withoutautomigration:
                self.declarativebase.metadata.create_all(self.connection())

            self.migration.auto_upgrade_database()

            for blok, installed_version in res:
                b = BlokManager.get(blok)(self)
                parsed_version = (
                    parse_version(installed_version)
                    if installed_version is not None
                    else None)
                b.post_migration(parsed_version)

        else:
            self.migration.auto_upgrade_database()

    def is_reload_needed(self):

        """Determines whether a reload is needed or not."""

        if self.loadwithoutmigration:
            return

        mustreload = False
        for entry in RegistryManager.declared_entries:
            if entry in RegistryManager.callback_initialize_entries:
                logger.debug('Initialize %r entry' % entry)
                r = RegistryManager.callback_initialize_entries[entry](
                    self)
                mustreload = mustreload or r

        return mustreload

    def expire(self, obj, attribute_names=None):
        """Expire object in session, you can define some attribute which are
        expired::

            registry.expire(instance, ['attr1', 'attr2', ...])

        :param obj: instance of ``Model``
        :param attribute_names: list of string, names of the attr to expire
        """
        if attribute_names:
            hybrid_property_columns = (
                obj.__class__.get_hybrid_property_columns()
            )
            attribute_names = [
                (anyblok_column_prefix + x
                 if x in hybrid_property_columns else x)
                for x in attribute_names
            ]

        self.session.expire(obj, attribute_names=attribute_names)

    def flag_modified(self, obj, attribute_names=None):
        """ Flag the attributes as modified
        ::

            registry.flag_modified(instance, ['attr1', 'attr2', ...])

        :param obj: instance of ``Model``
        :param attribute_names: list of string, names of the attr to expire
        """
        if attribute_names:
            hybrid_property_columns = (
                obj.__class__.get_hybrid_property_columns()
            )
            for attribute_name in attribute_names:
                if attribute_name in hybrid_property_columns:
                    attribute_name = anyblok_column_prefix + attribute_name

                flag_modified(obj, attribute_name)

    def expire_all(self):
        """Expire all the objects in session

        ::
            registry.expire_all()

        """
        self.session.expire_all()

    def expunge(self, obj):
        """Expunge instance of the session, remove all links of this instance
        in the session::

            registry.expunge(instance_of_model)

        """
        self.session.expunge(obj)

    def refresh(self, obj, attribute_names=None, with_for_update=None):
        """Expire  and reload object in session, you can define some attribute
        which are refreshed::

            registry.refresh(instance, ['attr1', 'attr2', ...])

        :param obj: instance of ``Model``
        :param attribute_names: list of string, names of the attr to refresh
        :param with_for_update: Boolean, acquire lock on the row until
        commit/rollback transaction
        """
        if attribute_names:
            attribute_names = [
                (anyblok_column_prefix + x
                 if x in obj.hybrid_property_columns else x)
                for x in attribute_names]

        self.session.refresh(
            obj,
            attribute_names=attribute_names,
            with_for_update=with_for_update,
        )

    def rollback(self, *args, **kwargs):
        logger.debug('[ROLLBACK] with args=%r and kwargs = %r', args, kwargs)
        self.session.rollback(*args, **kwargs)
        EnvironmentManager.set('_precommit_hook', [])
        EnvironmentManager.set('_postcommit_hook', [])

    def close_session(self):
        """ Close only the session, not the registry
        After the call of this method the registry won't be usable
        you should use close method which call this method
        """

        if self.unittest_transaction and self.unittest_transaction.is_active:
            self.unittest_transaction.rollback()

        if self.Session:
            session = self.Session()
            if not self.unittest_transaction:
                session.rollback()

            session.expunge_all()
            close_all_sessions()

        if self.unittest_transaction:
            self.unittest_transaction.close()
            self.bind.close()

    def close(self):
        """Release the session, connection and engine"""
        self.close_session()
        self.engine.dispose()
        if self.db_name in RegistryManager.registries:
            del RegistryManager.registries[self.db_name]

    def __getattr__(self, attribute):
        # TODO safe the call of session for reload
        if self.Session:
            session = self.Session()
            if attribute == 'session':
                return session
            if hasattr(session, attribute):
                return getattr(session, attribute)

        else:
            return super(Registry, self).__getattr__(attribute)

    def precommit_hook(self, registryname, method, *args, **kwargs):
        """ Add a method in the precommit_hook list

        a precommit hook is a method called just before the commit, it is used
        to call this method once, because a hook is saved only once

        :param registryname: namespace of the model
        :param method: method to call on the registryname
        :param put_at_the_end_if_exist: if true and hook allready exist then the
            hook are moved at the end
        """
        put_at_the_end_if_exist = kwargs.pop('put_at_the_end_if_exist', False)

        entry = (registryname, method, args, kwargs)
        _precommit_hook = EnvironmentManager.get('_precommit_hook', [])
        if entry in _precommit_hook:
            if put_at_the_end_if_exist:
                _precommit_hook.remove(entry)
                _precommit_hook.append(entry)

        else:
            _precommit_hook.append(entry)

        EnvironmentManager.set('_precommit_hook', _precommit_hook)

    def postcommit_hook(self, registryname, method, *args, **kwargs):
        """ Add a method in the postcommit_hook list

        a precommit hook is a method called just after the commit, it is used
        to call this method once, because a hook is saved only once

        you can choice if the hook is called in function of ``call_only_if``:

        * ``commited``: Call if the commit is done without exception
        * ``raised``: Call if one exception was raised
        * ``always``: Always call

        :param registryname: namespace of the model
        :param method: method to call on the registryname
        :param put_at_the_end_if_exist: if true and hook allready exist then the
            hook are moved at the end
        :param call_only_if: ['commited' (default), 'raised', 'always']
        """
        put_at_the_end_if_exist = kwargs.pop('put_at_the_end_if_exist', False)
        call_only_if = kwargs.pop('call_only_if', 'commited')

        entry = (registryname, method, call_only_if, args, kwargs)
        _postcommit_hook = EnvironmentManager.get('_postcommit_hook', [])
        if entry in _postcommit_hook:
            if put_at_the_end_if_exist:
                _postcommit_hook.remove(entry)
                _postcommit_hook.append(entry)

        else:
            _postcommit_hook.append(entry)

        EnvironmentManager.set('_postcommit_hook', _postcommit_hook)

    def apply_precommit_hook(self):
        hooks = []
        _precommit_hook = EnvironmentManager.get('_precommit_hook')
        if _precommit_hook:
            hooks.extend(_precommit_hook)

        for hook in hooks:
            Model = self.loaded_namespaces[hook[0]]
            method = hook[1]
            a = hook[2]
            kw = hook[3]
            getattr(Model, method)(*a, **kw)
            _precommit_hook.remove(hook)

    def apply_postcommit_hook(self, withexception=False):
        hooks = []
        _postcommit_hook = EnvironmentManager.get('_postcommit_hook')
        if _postcommit_hook:
            hooks.extend(_postcommit_hook)

        for hook in hooks:
            registryname, method, call_only_if, a, kw = hook
            if withexception is False and call_only_if == 'raised':
                _postcommit_hook.remove(hook)
                continue

            if withexception is True and call_only_if == 'commited':
                _postcommit_hook.remove(hook)
                continue

            Model = self.loaded_namespaces[registryname]
            try:
                getattr(Model, method)(*a, **kw)
            except Exception as e:
                logger.exception(str(e))
            finally:
                _postcommit_hook.remove(hook)

    @log(logger, level='debug')
    def commit(self, *args, **kwargs):
        """ Overload the commit method of the SqlAlchemy session """
        logger.debug('[COMMIT] with args=%r and kwargs = %r', args, kwargs)
        try:
            self.apply_precommit_hook()
            self.session_commit(*args, **kwargs)
            try:
                self.apply_postcommit_hook(withexception=False)
            except Exception as e:  # pragma: no cover
                logger.exception(str(e))
        except Exception as e:
            try:
                self.apply_postcommit_hook(withexception=True)
            except Exception as e:  # pragma: no cover
                logger.exception(str(e))

            raise e

    def flush(self):
        if not self.session._flushing:
            self.session.flush()

    def session_commit(self, *args, **kwargs):
        if self.Session:
            session = self.Session()
            session.commit(*args, **kwargs)

    def clean_model(self):
        """ Clean the registry of all the namespaces """
        for model in self.loaded_namespaces.keys():
            name = model.split('.')[1]
            if hasattr(self, name) and getattr(self, name):
                setattr(self, name, None)

    @log(logger, level='debug')
    def complete_reload(self):
        """ Reload the code and registry"""
        BlokManager.reload()
        RegistryManager.reload()

    @log(logger, level='debug')
    def reload(self):
        """ Reload the registry, close session, clean registry, reinit var """
        # self.close_session()
        self.remove_sqlalchemy_known_event()
        self.clean_model()
        self.ini_var()
        self.load()

    def get_bloks(self, blok, filter_states, filter_modes):
        Blok = self.System.Blok
        definition_blok = BlokManager.bloks[blok]
        bloks_name = []
        for filter_mode in filter_modes:
            bloks_name.extend(getattr(definition_blok, filter_mode))

        if not bloks_name:
            return []

        query = Blok.query()
        query = query.filter(Blok.name.in_(bloks_name))
        query = query.filter(Blok.state.in_(filter_states))
        return query.all().name

    def check_conflict_with(self, blok):
        Blok = self.System.Blok
        definition_blok = BlokManager.bloks[blok]
        conflicting_bloks = []
        conflicting_bloks.extend(definition_blok.conflicting)
        conflicting_bloks.extend(definition_blok.conflicting_by)

        query = Blok.query()
        query = query.filter(Blok.name.in_(conflicting_bloks))
        query = query.filter(
            Blok.state.in_(['installed', 'toinstall', 'toupdate']))
        if query.count():
            raise RegistryConflictingException(
                "Installation of the blok %r is forbidden, because the blok "
                "%r conflict with the blok(s) : %r" % (
                    blok, blok, [str(x) for x in query.all()]))

    def apply_state(self, blok_name, state, in_states):
        """Apply the state of the blok name

        :param blok_name: the name of the blok
        :param state: the state to apply
        :param in_states: the blok must be in this state
        :exception: RegistryException
        """
        Blok = self.System.Blok
        query = Blok.query().filter(Blok.name == blok_name)
        blok = query.first()
        if blok is None:
            raise RegistryException(
                "Blok %r not found in entry point declarations" %
                blok_name)

        if blok.state == state:
            logger.debug("Does not change state for blok %s because is the "
                         "same %s" % (blok_name, state))
            return

        if blok.state not in in_states:
            raise RegistryException(
                "Apply state %r is forbidden because the state %r of "
                "blok %r is not one of %r" % (
                    state, blok.state, blok_name, in_states))

        logger.info("Change state %s => %s for blok %s" % (
            blok.state, state, blok_name))
        Q = "UPDATE system_blok SET state='%s' where name='%s';" % (
            state, blok_name)
        self.execute(Q)
        # blok.update(state=state)

    @log(logger, level='debug', withargs=True)
    def upgrade(self, install=None, update=None, uninstall=None):
        """ Upgrade the current registry

        :param install: list of the blok to install
        :param update: list of the blok to update
        :param uninstall: list of the blok to uninstall
        :exception: RegistryException
        """
        Blok = self.System.Blok

        def upgrade_state_bloks(state):
            def wrap(bloks):
                for blok in bloks:
                    if state == 'toinstall':
                        self.check_conflict_with(blok)
                        self.apply_state(blok, state, ['uninstalled'])
                        upgrade_state_bloks(state)(
                            self.get_bloks(
                                blok,  ['undefined', 'uninstalled'],
                                ['required', 'optional', 'conditional']))
                    elif state == 'toupdate':
                        self.apply_state(blok, state, ['installed'])
                        upgrade_state_bloks(state)(
                            self.get_bloks(blok, ['installed'], [
                                'required_by', 'optional_by',
                                'conditional_by']))
                    elif state == 'touninstall':
                        if Blok.check_if_the_conditional_are_installed(blok):
                            raise RegistryException(
                                "the blok %r can not be unistalled because "
                                "this blok is a conditional blok and all the "
                                "bloks in his conditional list are installed "
                                "You must uninstall one of them" % blok)
                        self.apply_state(blok, state, ['installed'])
                        upgrade_state_bloks(state)(self.get_bloks(blok, [
                            'installed', 'toinstall', 'touninstall'], [
                            'required_by', 'conditional_by']))
                        upgrade_state_bloks('toupdate')(self.get_bloks(blok, [
                            'installed', 'toinstall', 'touninstall'], [
                            'optional_by']))

            return wrap

        upgrade_state_bloks('touninstall')(uninstall or [])
        upgrade_state_bloks('toinstall')(install or [])
        upgrade_state_bloks('toupdate')(update or [])
        self.reload()
        self.expire_all()

    @log(logger, level='debug')
    def update_blok_list(self):
        if not self.blok_list_is_loaded:
            self.System.Blok.update_list()
            self.blok_list_is_loaded = True
