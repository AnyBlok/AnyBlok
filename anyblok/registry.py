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
    mustbeload_declared_entries = []
    callback_declared_entries = {}
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
    def declare_entry(cls, entry, mustbeload=False, callback=None):
        """ Add new entry in the declared entry

        :param entry: entry name
        :param mustbeload: If true the The registry must be load the entry
        :type mustbeload: bool
        :param callback: function callback to call to load it
        """
        if entry not in cls.declared_entries:
            cls.declared_entries.append(entry)

            if mustbeload:
                if entry not in cls.mustbeload_declared_entries:
                    cls.mustbeload_declared_entries.append(entry)

            if callback:
                cls.callback_declared_entries[entry] = callback

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
                'Session': [],
            }
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
        current_blok = EnvironmentManager.get('current_blok')
        cls.loaded_bloks[current_blok]['Core'][core].append(cls_)

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
    def add_entry_in_target_registry(cls, entry, key, cls_, **kwargs):
        """ Load entry in blok

        warning the global var current_blok must be filled on the good blok
        :param entry: is the existing entry name
        :param key: is the existing key in the entry
        :param ``cls_``: Class of the entry / key to remove in loaded blok
        """
        bases = []

        for base in cls_.__bases__:
            if base is not object:
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
    def remove_entry_in_target_registry(cls, blok, entry, key, cls_, **kwargs):
        """ Remove Class in blok and in entry

        :param blok: name of the blok
        :param entry: is the existing entry name
        :param key: is the existing key in the entry
        :param ``cls_``: Class of the entry / key to remove in loaded blok
        """
        cls.loaded_bloks[blok][entry][key]['bases'].remove(cls_)
        cls.loaded_bloks[blok][entry][key]['properties'].update(kwargs)


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
        self.loaded_namespaces_first_step = {}
        self.loaded_namespaces = {}
        self.declarativebase = None
        self.loaded_bloks = {}
        self.loaded_registries = {
            x + '_names': []
            for x in RegistryManager.mustbeload_declared_entries}
        self.loaded_cores = {
            'Base': [self.registry_base],
            'SqlBase': [],
            'Session': [],
        }
        self.ordered_loaded_bloks = []
        self.loaded_namespaces = {}
        self.children_namespaces = {}

    def get(self, namespace):
        """ Return the namespace Class

        :param namespace: namespace to get from the registry str
        :rtype: namespace cls
        """
        if namespace not in self.loaded_namespaces:
            raise RegistryManagerException(
                "No namespace %r loaded" % namespace)

        return self.loaded_namespaces[namespace]

    def get_bloks_to_load(self):
        """ Return the bloks to load by the registry, this bloks are installed,
        or will be installed

        :rtype: list of blok's name
        """
        conn = None
        try:
            conn = self.engine.connect()
            res = conn.execute("""
                select system_blok.name
                from system_blok
                where system_blok.state in ('installed',
                                            'toinstall',
                                            'toupdate')
                order by system_blok.order""").fetchall()
            toload = [x[0] for x in res]
        except (ProgrammingError, OperationalError):
            toload = []
        finally:
            if conn:
                conn.close()

        for blok in BlokManager.auto_install:
            if blok not in toload:
                toload.append(blok)

        return toload

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

            if entry in RegistryManager.mustbeload_declared_entries:
                self.loaded_registries[entry + '_names'].append(key)

    def load_core(self, blok, core):
        """ load one core type for one blok

        :param blok: name of the blok
        :param core: the core name to load
        """
        bases = RegistryManager.loaded_bloks[blok]['Core'][core]
        bases.reverse()
        for base in bases:
            self.loaded_cores[core].insert(0, base)

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

        for core in ('Base', 'SqlBase', 'Session'):
            self.load_core(blok, core)

        for entry in RegistryManager.declared_entries:
            self.load_entry(blok, entry)

        self.loaded_bloks[blok] = b
        self.ordered_loaded_bloks.append(blok)
        logger.info("Blok %r loaded" % blok)
        return True

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
        try:
            self.declarativebase = declarative_base(class_registry=dict(
                registry=self))
            toload = self.get_bloks_to_load()

            def has_sql_fields(bases):
                Field = Declarations.Field
                for base in bases:
                    for p in dir(base):
                        if hasattr(getattr(base, p), '__class__'):
                            if Field in getattr(base, p).__class__.__mro__:
                                return True

                return False

            def get_fields(base):
                Field = Declarations.Field
                fields = {}
                for p in dir(base):
                    if hasattr(getattr(base, p), '__class__'):
                        if Field in getattr(base, p).__class__.__mro__:
                            fields[p] = getattr(base, p)
                return fields

            def declare_field(name, field, namespace, properties):
                if name in properties:
                    return

                from sqlalchemy.ext.declarative import declared_attr

                def wrapper(cls):
                    return field.get_sqlalchemy_mapping(
                        self, namespace, name, properties)

                field.update_properties(self, namespace, name, properties)
                properties[name] = declared_attr(wrapper)
                properties['loaded_columns'].append(name)

            def load_namespace_first_step(namespace):
                if namespace in self.loaded_namespaces_first_step:
                    return self.loaded_namespaces_first_step[namespace]

                bases = []
                properties = {}
                ns = self.loaded_registries[namespace]

                for b in ns['bases']:
                    bases.append(b)

                    for b_ns in b.__anyblok_bases__:
                        ps = load_namespace_first_step(b_ns.__registry_name__)
                        ps.update(properties)
                        properties.update(ps)

                if namespace in self.loaded_registries['Model_names']:
                    for b in bases:
                        fields = get_fields(b)
                        for p, f in fields.items():
                            properties[p] = f

                    self.loaded_namespaces_first_step[namespace] = properties
                    properties = {}

                return properties

            def load_namespace_second_step(namespace):
                if namespace in self.loaded_namespaces:
                    return [self.loaded_namespaces[namespace]], {}

                bases = []
                properties = {}
                ns = self.loaded_registries[namespace]

                for b in ns['bases']:
                    bases.append(b)
                    p = ns['properties']
                    p.update(properties)
                    properties.update(p)

                    for b_ns in b.__anyblok_bases__:
                        bs, ps = load_namespace_second_step(
                            b_ns.__registry_name__)
                        bases += bs
                        ps.update(properties)
                        properties.update(ps)

                if namespace in self.loaded_registries['Model_names']:
                    properties['loaded_columns'] = []
                    tablename = properties['__tablename__']
                    if has_sql_fields(bases):
                        bases += self.loaded_cores['SqlBase']
                        bases += [self.declarativebase]

                    bases += self.loaded_cores['Base']
                    for b in bases:
                        for p, f in get_fields(b).items():
                            declare_field(p, f, namespace, properties)

                    bases = [type(tablename, tuple(bases), properties)]
                    properties = {}
                    self.add_in_registry(namespace, bases[0])
                    self.loaded_namespaces[namespace] = bases[0]

                return bases, properties

            for blok in toload:
                self.load_blok(blok)

            # get all the information to create a namespace
            for namespace in self.loaded_registries['Model_names']:
                load_namespace_first_step(namespace)

            # create the namespace with all the information come from first
            # step
            for namespace in self.loaded_registries['Model_names']:
                load_namespace_second_step(namespace)

            self.declarativebase.metadata.create_all(self.engine)

            Session = type('Session', tuple(self.loaded_cores['Session']), {})
            self.Session = scoped_session(
                sessionmaker(bind=self.engine, class_=Session),
                EnvironmentManager.scoped_function_for_session)

            self.migration = Migration(self.session,
                                       self.declarativebase.metadata)
            self.migration.auto_upgrade_database()

            Model = self.System.Model
            Model.update_list()

            Blok = self.System.Blok
            Blok.update_list()
            Blok.apply_state(*self.ordered_loaded_bloks)
        except:
            self.close()
            raise

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

    def clean_model(self):
        for model in self.loaded_namespaces.keys():
            name = model.split('.')[1]
            if hasattr(self, name) and getattr(self, name):
                setattr(self, name, None)

    @log()
    def reload(self):
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
