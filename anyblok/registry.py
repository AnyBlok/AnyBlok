# -*- coding: utf-8 -*-
import AnyBlok
from anyblok._argsparse import ArgsParseManager
from anyblok._imp import ImportManager
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base


class RegistryManager:
    """ Manage the global registry

    Add new entry::

        RegistryManager.declare_entry('newEntry')
        RegistryManager.init_blok('newBlok')
        AnyBlok.current_blok = 'newBlok'
        RegistryManager.add_entry_in_target_registry(
            'newEntry', 'oneKey', cls_)
        AnyBlok.current_blok = None

    Remove an existing entry::

        if RegistryManager.has_entry_in_target_registry('newBlok', 'newEntry',
                                                        'oneKey'):
            RegistryManager.remove_entry_in_target_registry(
                'newBlok', 'newEntry', 'oneKey', cls_)

    """

    loaded_bloks = {}
    declared_entries = []
    mustbeload_declared_entries = []
    callback_declared_entries = {}
    registries = {}
    scoped_fnct = None

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
        cls.registries = {}

    @classmethod
    def get(cls, dbname):
        """ Return an existing Registry

        If the Registry does'nt exist then the Registry are created and add to
        registries dict

        :param dbname: the name of the database link with this registry
        :rtype: ``Registry``
        """
        if dbname in cls.registries:
            return cls.registries[dbname]

        registry = Registry(dbname, cls.scoped_fnct)
        cls.registries[dbname] = registry
        return registry

    @classmethod
    def reload(cls, blok):
        """ Reload the blok

        The purpose is to reload python module to get change in python file

        :param blok: the name of the blok to reload
        """
        mod = ImportManager.get(blok)
        AnyBlok.current_blok = blok
        try:
            mod.reload()
        finally:
            AnyBlok.current_blok = None

        registry2remove = []
        for dbname, registry in cls.registries.items():
            installed = registry.installed_bloks()

            if not installed:
                continue

            if blok in installed:
                registry2remove.append(dbname)

        for dbname in registry2remove:
            del cls.registries[dbname]

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

        warning the global var AnyBlok.current_blok must be field on the
        good blok

        :param core: is the existing core name
        :param ``cls_``: Class of the Core to save in loaded blok target registry
        """
        cls.loaded_bloks[AnyBlok.current_blok]['Core'][core].append(cls_)

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

        warning the global var AnyBlok.current_blok must be field on the
        good blok
        :param entry: is the existing entry name
        :param key: is the existing key in the entry
        :param ``cls_``: Class of the entry / key to remove in loaded blok
        """
        cb = AnyBlok.current_blok

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

        registry = Registry.get('My database')
    """

    def __init__(self, dbname, scoped_fnct=None):
        self.dbname = dbname
        self.scoped_fnct = scoped_fnct
        url = ArgsParseManager.get_url(dbname=dbname)
        self.engine = create_engine(url)
        self.declarative_base = declarative_base(class_registry=dict(
            registry=self))

    def installed_bloks(self):
        """ Return the list of the installed blok

        :rtype: Return the list or None if anyblok-core not installed
        """
        if not hasattr(self, 'System'):
            return None

        if not hasattr(self.System, 'Blok'):
            return None

        return self.System.Blok.list_by_state('installed')
