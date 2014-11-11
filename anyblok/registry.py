# -*- coding: utf-8 -*-
from anyblok import Declarations
from anyblok._argsparse import ArgsParseManager
from anyblok._imp import ImportManager
from anyblok.blok import BlokManager
from anyblok._logging import log
from anyblok.environment import EnvironmentManager
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from anyblok.migration import Migration
from sqlalchemy.exc import ProgrammingError, OperationalError
from functools import lru_cache
from logging import getLogger

logger = getLogger(__name__)


@Declarations.target_registry(Declarations.Exception)
class RegistryManagerException(Exception):
    """ Simple Exception for Registry """


class RegistryManager:
    """ Manage the global registry

    Add new entry::

        RegistryManager.declare_entry('newEntry')
        RegistryManager.init_blok('newBlok')
        EnvironmentManager.set('current_blok', 'newBlok')
        RegistryManager.add_entry_in_target_registry(
            'newEntry', 'oneKey', cls_)
        EnvironmentManager.set('current_blok', None)

    Remove an existing entry::

        if RegistryManager.has_entry_in_target_registry('newBlok', 'newEntry',
                                                        'oneKey'):
            RegistryManager.remove_entry_in_target_registry(
                'newBlok', 'newEntry', 'oneKey', cls_)

    get a new registry for a database::

        registry = RegistryManager.get('my database')

    """

    loaded_bloks = {}
    declared_entries = []
    callback_assemble_entries = {}
    callback_initialize_entries = {}
    registries = {}
    needed_bloks = []

    @classmethod
    def has_blok(cls, blok):
        """ Return True if the blok is already loaded

        :param blok: name of the blok
        :rtype: boolean
        """

        return blok in cls.loaded_bloks

    @classmethod
    def clear(cls):
        """ Clear the registry dict to forced the creation of new registry """
        registries = [r for r in cls.registries.values()]
        for registry in registries:
            registry.close()

    @classmethod
    def get(cls, dbname):
        """ Return an existing Registry

        If the Registry does'nt exist then the Registry are created and add to
        registries dict

        :param dbname: the name of the database link with this registry
        :rtype: ``Registry``
        """
        EnvironmentManager.set('dbname', dbname)
        if dbname in cls.registries:
            return cls.registries[dbname]

        registry = Registry(dbname)
        cls.registries[dbname] = registry
        return registry

    @classmethod
    def unload(cls):
        """ Unload the registry bloks """

        for blok in cls.loaded_bloks.keys():
            cls.init_blok(blok)

    @classmethod
    def reload(cls, blok):
        """ Reload the blok

        The purpose is to reload python module to get change in python file

        :param blok: the name of the blok to reload
        """
        cls.unload()
        mod = ImportManager.get(blok)
        EnvironmentManager.set('current_blok', blok)
        try:
            EnvironmentManager.set('reload', True)
            mod.imports()
            mod.reload()
        finally:
            EnvironmentManager.set('reload', False)
            EnvironmentManager.set('current_blok', None)

        for registry in cls.registries.values():
            registry.reload()

    @classmethod
    def declare_entry(cls, entry, assemble_callback=None,
                      initialize_callback=None):
        """ Add new entry in the declared entry

        ::

            def assemble_callback(registry):
                ...

            def initialize_callback(registry):
                ...

            RegistryManager.declare_entry(
                'Entry name', assemble_callback=assemble_callback,
                initialize_callback=initialize_callback)

        :param entry: entry name
        :param assemble_callback: function callback to call to assemble
        :param initialize_callback: function callback to call to init after
            assembling
        """

        if entry not in cls.declared_entries:
            cls.declared_entries.append(entry)

            if assemble_callback:
                cls.callback_assemble_entries[entry] = assemble_callback

            if initialize_callback:
                cls.callback_initialize_entries[entry] = initialize_callback

    @classmethod
    def undeclare_entry(cls, entry):
        if entry in cls.declared_entries:
            cls.declared_entries.remove(entry)

            if entry in cls.callback_assemble_entries:
                del cls.callback_assemble_entries[entry]

            if entry in cls.callback_initialize_entries:
                del cls.callback_initialize_entries[entry]

    @classmethod
    def init_blok(cls, blokname):
        """ init one blok to be know by RegistryManager

        All bloks loaded must be initialize because the registry will be create
        with this information

        :param blokname: name of the blok
        """
        blok = {
            'Core': {
                'Base': [],
                'SqlBase': [],
                'SqlViewBase': [],
                'Session': [],
                'Query': [],
                'InstrumentedList': [],
            },
            'properties': {},
        }
        for de in cls.declared_entries:
            blok[de] = {'registry_names': []}

        cls.loaded_bloks[blokname] = blok

    @classmethod
    def has_core_in_target_registry(cls, blok, core):
        """ Return True if One Class exist in this blok for this core

        :param blok: name of the blok
        :param core: is the existing core name
        """
        return len(cls.loaded_bloks[blok]['Core'][core]) > 0

    @classmethod
    def add_core_in_target_registry(cls, core, cls_):
        """ Load core in blok

        warning the global var current_blok must be filled on the good blok

        :param core: is the existing core name
        :param ``cls_``: Class of the Core to save in loaded blok target
            registry
        """

        new_cls = cls.apply_cache('Core.' + core, cls_)
        current_blok = EnvironmentManager.get('current_blok')
        cls.loaded_bloks[current_blok]['Core'][core].append(new_cls)

    @classmethod
    def remove_core_in_target_registry(cls, blok, core, cls_):
        """ Remove Class in blok and in core

        :param blok: name of the blok
        :param core: is the existing core name
        :param ``cls_``: Class of the Core to remove in loaded blok target
                        registry
        """
        cls.loaded_bloks[blok]['Core'][core].remove(cls_)

    @classmethod
    def has_entry_in_target_registry(cls, blok, entry, key):
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
    def apply_cache(cls, key, cls_):
        caches = cls.get_blok_property('caches', {})
        methods_cached = {}

        def apply_wrapper(attr, method):
            @lru_cache(maxsize=method.size)
            def wrapper(*args, **kwargs):
                return method(*args, **kwargs)

            wrapper.indentify = (key, attr)
            caches[key][attr].append(wrapper)
            if method.is_cache_classmethod:
                methods_cached[attr] = classmethod(wrapper)
            else:
                methods_cached[attr] = wrapper

        for attr in dir(cls_):
            method = getattr(cls_, attr)
            if not hasattr(method, 'is_cache_method'):
                continue
            elif method.is_cache_method is True:
                if key not in caches:
                    caches[key] = {attr: []}
                elif attr not in caches[key]:
                    caches[key][attr] = []

                apply_wrapper(attr, method)

        cls.add_or_replace_blok_property('caches', caches)
        if methods_cached:
            return type(key, (cls_,), methods_cached)

        return cls_

    @classmethod
    def add_entry_in_target_registry(cls, entry, key, cls_, **kwargs):
        """ Load entry in blok

        warning the global var current_blok must be filled on the good blok
        :param entry: is the existing entry name
        :param key: is the existing key in the entry
        :param ``cls_``: Class of the entry / key to remove in loaded blok
        """

        new_cls = cls.apply_cache(key, cls_)
        bases = []

        for base in new_cls.__bases__:
            if hasattr(base, '__registry_name__'):
                bases.append(base)

        setattr(new_cls, '__anyblok_bases__', bases)

        cb = EnvironmentManager.get('current_blok')

        if key not in cls.loaded_bloks[cb][entry]:
            cls.loaded_bloks[cb][entry][key] = {
                'bases': [],
                'properties': {},
            }

        cls.loaded_bloks[cb][entry][key]['properties'].update(kwargs)
        # Add before in registry because it is the same order than the
        # inheritance __bases__ and __mro__
        cls.loaded_bloks[cb][entry][key]['bases'].insert(0, new_cls)

        if key not in cls.loaded_bloks[cb][entry]['registry_names']:
            cls.loaded_bloks[cb][entry]['registry_names'].append(key)

    @classmethod
    def get_entry_properties_in_target_registry(cls, entry, key):
        cb = EnvironmentManager.get('current_blok')
        if key not in cls.loaded_bloks[cb][entry]:
            return {}

        return cls.loaded_bloks[cb][entry][key]['properties'].copy()

    @classmethod
    def remove_entry_in_target_registry(cls, blok, entry, key, cls_, **kwargs):
        """ Remove Class in blok and in entry

        :param blok: name of the blok
        :param entry: is the existing entry name
        :param key: is the existing key in the entry
        :param ``cls_``: Class of the entry / key to remove in loaded blok
        """
        cls.loaded_bloks[blok][entry][key]['bases'].remove(cls_)
        cls.loaded_bloks[blok][entry][key]['properties'].update(kwargs)

    @classmethod
    def has_blok_property(cls, property_):
        """ Return True if the property exit in blok

        :param property\_: name of the property
        """
        blok = EnvironmentManager.get('current_blok')

        if property_ in cls.loaded_bloks[blok]['properties']:
            return True

        return False

    @classmethod
    def add_or_replace_blok_property(cls, property_, value):
        """ Save the value in the properties

        :param property\_: name of the property
        :param value: the value to save, the type is not important
        """
        blok = EnvironmentManager.get('current_blok')
        cls.loaded_bloks[blok]['properties'][property_] = value

    @classmethod
    def get_blok_property(cls, property_, default=None):
        """ Return the value in the properties

        :param property\_: name of the property
        :param default: return default If not entry in the property
        """
        blok = EnvironmentManager.get('current_blok')
        return cls.loaded_bloks[blok]['properties'].get(property_, default)

    @classmethod
    def remove_blok_property(cls, property_):
        """ Remove the property if exist

        :param property\_: name of the property
        """
        blok = EnvironmentManager.get('current_blok')
        if cls.has_blok_property(property_):
            del cls.loaded_bloks[blok]['properties'][property_]

    @classmethod
    def add_needed_bloks(cls, *bloks):
        for blok in bloks:
            if blok not in cls.needed_bloks:
                cls.needed_bloks.append(blok)

    @classmethod
    def get_needed_bloks(cls):
        return cls.needed_bloks


class Registry:
    """ Define one registry

    A registry is link with a database, a have the definition of the installed
    Blok, Model, Mixin for this database::

        registry = Registry('My database')
    """

    def __init__(self, dbname):
        self.dbname = dbname
        url = ArgsParseManager.get_url(dbname=dbname)
        self.engine = create_engine(url)
        self.registry_base = type("RegistryBase", tuple(), {'registry': self})
        self.ini_var()
        self.Session = None
        self.load()

    def ini_var(self):
        """ Initialize the var to load the  registry """
        self.loaded_namespaces = {}
        self.declarativebase = None
        self.loaded_bloks = {}
        self.loaded_registries = {x + '_names': []
                                  for x in RegistryManager.declared_entries}
        self.loaded_cores = {
            'Base': [self.registry_base],
            'SqlBase': [],
            'SqlViewBase': [],
            'Session': [],
            'Query': [],
            'InstrumentedList': [],
        }
        self.ordered_loaded_bloks = []
        self.loaded_namespaces = {}
        self.children_namespaces = {}
        self.properties = {}
        self._precommit_hook = []

    def get(self, namespace):
        """ Return the namespace Class

        :param namespace: namespace to get from the registry str
        :rtype: namespace cls
        """
        if namespace not in self.loaded_namespaces:
            raise RegistryManagerException(
                "No namespace %r loaded" % namespace)

        return self.loaded_namespaces[namespace]

    def get_bloks_by_states(self, *states):
        """ Return the bloks in fonction of this state

        :param states: list of the states
        :rtype: list of blok's name
        """
        if not states:
            return []
        conn = None
        try:
            conn = self.engine.connect()
            res = conn.execute("""
                select system_blok.name
                from system_blok
                where system_blok.state in ('%s')
                order by system_blok.order""" % "', '".join(states)).fetchall()
            toload = [x[0] for x in res]
        except (ProgrammingError, OperationalError):
            toload = []
        finally:
            if conn:
                conn.close()

        return toload

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

        for blok in RegistryManager.get_needed_bloks():
            if blok not in (toinstall + loaded):
                toinstall.append(blok)

        return toinstall

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
        bases = RegistryManager.loaded_bloks[blok]['Core'][core]
        for base in bases:
            self.loaded_cores[core].insert(0, base)

    def load_properties(self, blok):
        properties = RegistryManager.loaded_bloks[blok]['properties']
        for k, v in properties.items():
            if k not in self.properties:
                self.properties[k] = v
            elif isinstance(self.properties[k], dict) and isinstance(v, dict):
                self.properties.update(v)
            elif isinstance(self.properties[k], list) and isinstance(v, list):
                self.properties.extend(v)
            else:
                self.properties[k] = v

    def load_blok(self, blok):
        """ load on blok, load all the core and all the entry for one blok

        :param blok: name of the blok
        """
        if blok in self.ordered_loaded_bloks:
            return True

        if blok not in BlokManager.bloks:
            return False

        b = BlokManager.bloks[blok](self)
        for required in b.required:
            if not self.load_blok(required):
                raise RegistryManagerException(
                    "Required blok not found")

        for optional in b.optional:
            self.load_blok(optional)

        for core in ('Base', 'SqlBase', 'SqlViewBase', 'Session', 'Query',
                     'InstrumentedList'):
            self.load_core(blok, core)

        for entry in RegistryManager.declared_entries:
            self.load_entry(blok, entry)

        self.load_properties(blok)
        self.loaded_bloks[blok] = b
        self.ordered_loaded_bloks.append(blok)
        logger.info("Blok %r loaded" % blok)
        return True

    def update_to_install_blok_dependencies_state(self, toinstall):
        dependencies_to_install = []

        def check_dependencies(blok):
            if blok in dependencies_to_install:
                return True

            if blok not in BlokManager.bloks:
                return False

            b = BlokManager.bloks[blok](self)
            for required in b.required:
                if not check_dependencies(required):
                    raise RegistryManagerException(
                        "%r: Required blok not found %r" % (blok, required))

            for optional in b.optional:
                check_dependencies(optional)

            if blok not in toinstall:
                dependencies_to_install.append(blok)

            return True

        for blok in toinstall:
            check_dependencies(blok)

        if dependencies_to_install:
            conn = None
            try:
                conn = self.engine.connect()
                conn.execute("""
                    update system_blok
                    set state='toinstall'
                    where name in ('%s')
                    and state = 'uninstalled'""" % "', '".join(
                    dependencies_to_install))
            except (ProgrammingError, OperationalError):
                pass
            finally:
                if conn:
                    conn.close()

            return True

        return False

    def add_in_registry(self, namespace, base):
        """ Add a class as an attribute of the registry

        :param namespace: tree path of the attribute
        :param base: class to add
        """
        namespace = namespace.split('.')[1:]

        def final_namespace(parent, child):
            if hasattr(parent, child) and getattr(parent, child):
                other_base = get_namespace(parent, child)
                other_base = other_base.children_namespaces.copy()
                for ns, cns in other_base.items():
                    setattr(base, ns, cns)

                if hasattr(parent, 'children_namespaces'):
                    if child in parent.children_namespaces:
                        parent.children_namespaces[child] = base

            elif hasattr(parent, 'children_namespaces'):
                parent.children_namespaces[child] = base

            setattr(parent, child, base)

        def get_namespace(parent, child):
            if hasattr(parent, child) and getattr(parent, child):
                return getattr(parent, child)

            tmpns = type(child, tuple(), {'children_namespaces': {}})
            if hasattr(parent, 'children_namespaces'):
                parent.children_namespaces[child] = tmpns

            setattr(parent, child, tmpns)
            return tmpns

        def update_namespaces(parent, namespaces):
            if len(namespaces) == 1:
                final_namespace(parent, namespaces[0])
            else:
                new_parent = get_namespace(parent, namespaces[0])
                update_namespaces(new_parent, namespaces[1:])

        update_namespaces(self, namespace)

    @log()
    def load(self):
        """ Load all the namespace of the registry

        Create all the table, make the shema migration
        Update Blok, Model, Column rows
        """
        mustreload = False
        try:
            self.declarativebase = declarative_base(class_registry=dict(
                registry=self))
            toload = self.get_bloks_to_load()
            toinstall = self.get_bloks_to_install(toload)
            if self.update_to_install_blok_dependencies_state(toinstall):
                toinstall = self.get_bloks_to_install(toload)

            for blok in toload:
                self.load_blok(blok)

            if toinstall:
                self.load_blok(toinstall[0])

            instrumentedlist_base = [] + self.loaded_cores['InstrumentedList']
            instrumentedlist_base += [list]
            self.InstrumentedList = type(
                'InstrumentedList', tuple(instrumentedlist_base), {})

            for entry in RegistryManager.declared_entries:
                if entry in RegistryManager.callback_assemble_entries:
                    logger.info('Assemble %r entry' % entry)
                    RegistryManager.callback_assemble_entries[entry](self)

            self.declarativebase.metadata.create_all(self.engine)

            query_bases = [] + self.loaded_cores['Query']
            query_bases += [self.registry_base]
            Query = type('Query', tuple(query_bases), {})
            Session = type('Session', tuple(self.loaded_cores['Session']), {
                'registry_query': Query})
            self.Session = scoped_session(
                sessionmaker(bind=self.engine, class_=Session),
                EnvironmentManager.scoped_function_for_session)

            self.init_migration()
            self.migration.auto_upgrade_database()

            for entry in RegistryManager.declared_entries:
                if entry in RegistryManager.callback_initialize_entries:
                    logger.info('Initialize %r entry' % entry)
                    r = RegistryManager.callback_initialize_entries[entry](
                        self)
                    mustreload = mustreload or r

            self.commit()
        except:
            self.close()
            raise

        if len(toinstall) > 1 or mustreload:
            self.reload()

    def init_migration(self):
        self.migration = Migration(self.session,
                                   self.declarativebase.metadata)

    def close_session(self):
        """ Close only the session, not the registry
        After the call of this method the registry won't be usable
        you should use close method which call this method
        """
        if self.Session:
            session = self.Session()
            session.rollback()
            session.close_all()

    def close(self):
        """Release the session, connection and engin"""
        self.close_session()
        self.engine.dispose()
        if self.dbname in RegistryManager.registries:
            del RegistryManager.registries[self.dbname]

    def __getattr__(self, attribute):
        # TODO safe the call of session for reload
        if self.Session:
            session = self.Session()
            if attribute == 'session':
                return session
            if hasattr(session, attribute):
                return getattr(session, attribute)

        else:
            super(Registry, self).__getattr__(attribute)

    def precommit_hook(self, registryname, method, put_at_the_if_exist):
        entry = (registryname, method)
        if entry in self._precommit_hook:
            if put_at_the_if_exist:
                self._precommit_hook.remove(entry)
                self._precommit_hook.append(entry)

        else:
            self._precommit_hook.append(entry)

    def commit(self, *args, **kwargs):
        hooks = []
        if self._precommit_hook:
            hooks.extend(self._precommit_hook)

        for hook in hooks:
            Model = self.loaded_namespaces[hook[0]]
            method = hook[1]
            getattr(Model, method)()
            self._precommit_hook.remove(hook)

        self.session_commit(*args, **kwargs)

    def session_commit(self, *args, **kwargs):
        if self.Session:
            session = self.Session()
            session.commit(*args, **kwargs)

    def clean_model(self):
        """ Clean the registry of all the namespace """
        for model in self.loaded_namespaces.keys():
            name = model.split('.')[1]
            if hasattr(self, name) and getattr(self, name):
                setattr(self, name, None)

    @log()
    def reload(self):
        """ Reload the registry, close session, clean registry, reinit var """
        self.close_session()
        self.clean_model()
        self.ini_var()
        self.load()

    @log(withargs=True)
    def upgrade(self, install=None, update=None, uninstall=None):
        """ Upgrade the current registry

        :param install: list of the blok to install
        :param update: list of the blok to update
        :param uninstall: list of the blok to uninstall
        """
        Blok = self.System.Blok

        def upgrade_state_bloks(bloks, state):
            if not bloks:
                return

            for blok in bloks:
                Blok.query().filter(Blok.name == blok).update({'state': state})

        upgrade_state_bloks(install, 'toinstall')
        upgrade_state_bloks(update, 'toupdate')
        upgrade_state_bloks(uninstall, 'touninstall')

        self.commit()
        self.reload()
