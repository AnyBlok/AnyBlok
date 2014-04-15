# -*- coding: utf-8 -*-
from pkg_resources import iter_entry_points
import anyblok
from anyblok._imp import ImportManager
from anyblok._logging import log
from anyblok.environment import EnvironmentManager
from time import sleep
from sys import modules
from os.path import dirname, join


@anyblok.Declarations.target_registry(anyblok.Declarations.Exception)
class BlokManagerException(Exception):
    """ Simple exception to BlokManager """

    def __init__(self, *args, **kwargs):
        EnvironmentManager.set('current_blok', None)
        super(BlokManagerException, self).__init__(*args, **kwargs)


class BlokManager:
    """ Manage the bloks for one process

    One blok is a setuptools entrypoint, this entry point is define
    by property bloks_groups in the first load

    the property bloks, is a dict with all the entry point load

    Use this class to import all the blok in the entrypoint::

        BlokManager.load('AnyBlok')

    """

    bloks = {}
    bloks_groups = None
    ordered_bloks = []
    auto_install = []

    @classmethod
    def list(cls):
        """ Return the ordered bloks

        :rtype: list of blok name ordered by loading
        """
        return cls.ordered_bloks

    @classmethod
    def has(cls, blok):
        """ Return True if the blok has loaded

        :param blok: blok name
        :rtype: bool
        """
        return blok and blok in cls.ordered_bloks or False

    @classmethod
    def get(cls, blok):
        """ Return the loaded blok

        :param blok: blok name
        :rtype: blok instance
        """
        if not cls.has(blok):
            raise BlokManagerException('%r not found' % blok)

        return cls.bloks[blok]

    @classmethod
    def set(cls, blokname, blok):
        """ Add new blok

        :param blokname: blok name
        :param blok: blok instance
        """
        if cls.has(blokname):
            raise BlokManagerException('%r already add' % blokname)

        cls.bloks[blokname] = blok
        cls.ordered_bloks.append(blokname)

    @classmethod
    @log()
    def reload(cls):
        """ Reload the entry points

        Empty the dict bloks and use the bloks_groups property to load bloks
        """
        if cls.bloks_groups is None:
            raise BlokManagerException(
                "You must use the load classmethod before use reload")

        bloks_groups = []
        bloks_groups += cls.bloks_groups
        cls.unload()
        cls.load(*bloks_groups)

    @classmethod
    @log()
    def unload(cls):
        """ Unload all the blok but not the registry """
        from anyblok.registry import RegistryManager

        RegistryManager.unload()
        cls.bloks = {}
        cls.ordered_bloks = []
        cls.bloks_groups = None
        cls.auto_install = []

    @classmethod
    @log()
    def load(cls, *bloks_groups):
        """ Load all the blok and import it

        :param bloks_groups: Use by iter_entry_points to get the blok
        """
        if not bloks_groups:
            raise BlokManagerException("The bloks_groups mustn't be empty")

        cls.bloks_groups = bloks_groups

        if EnvironmentManager.get('current_blok'):
            while EnvironmentManager.get('current_blok'):
                sleep(0.1)

        EnvironmentManager.set('current_blok', 'start')

        bloks = []
        for bloks_group in bloks_groups:
            count = 0
            for i in iter_entry_points(bloks_group):
                count += 1
                try:
                    blok = i.load()
                    cls.set(i.name, blok)
                    bloks.append((blok.priority, i.name))
                except Exception as e:
                    raise BlokManagerException(str(e))

            if not count:
                raise BlokManagerException(
                    "Invalid bloks group %r" % bloks_group)

        # Empty the orderred blok to reload it in function of priority
        cls.ordered_bloks = []
        bloks.sort()

        def get_need_blok(blok):
            if cls.has(blok):
                return True

            if blok not in cls.bloks:
                return False

            for required in cls.bloks[blok].required:
                if not get_need_blok(required):
                    raise BlokManagerException(
                        "Not %s required bloks found" % required)

            for optional in cls.bloks[blok].optional:
                get_need_blok(optional)

            cls.ordered_bloks.append(blok)
            EnvironmentManager.set('current_blok', blok)

            if not ImportManager.has(blok):
                # Import only if not exist don't reload here
                module = modules[cls.bloks[blok].__module__]
                mod = ImportManager.add(blok, module.__file__)
                mod.imports()
            else:
                mod = ImportManager.get(blok)
                mod.reload()

            if cls.bloks[blok].autoinstall:
                cls.auto_install.append(blok)

            return True

        try:
            while bloks:
                blok = bloks.pop(0)[1]
                get_need_blok(blok)

        finally:
            EnvironmentManager.set('current_blok', None)

    @classmethod
    def get_files_from(cls, blok, attribute):
        """ Return a files list with absolute path

        :param blok: blok name in ordered_bloks
        :param attribute: must be a list of property of this blok

        :rtype: list of file with absolute path
                if attribute doesn't exist then return []
        """
        blok = cls.get(blok)
        if not hasattr(blok, attribute):
            return []

        b_path = dirname(modules[blok.__module__].__file__)
        return [join(b_path, x) for x in getattr(blok, attribute)]


class Blok:
    """ Super class for all the blok

    define the default value for:

    * priority: order to load blok
    * required: list of the blok need to install this blok
    * optional: list of bloks to install if present in the blok list
    * conditionnal: if all the list is installated the install this blok
    * imports: list of the python file to import
    """

    autoinstall = False
    priority = 100
    required = []
    optional = []
    conditional = []

    html = []
    js = []
    css = []

    def __init__(self, registry):
        self.registry = registry

    @classmethod
    def clean_before_reload(cls):
        pass

    def install(self):
        pass

    def update(self):
        pass

    def uninstall(self):
        pass
