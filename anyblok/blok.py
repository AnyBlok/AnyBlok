# -*- coding: utf-8 -*-
from pkg_resources import iter_entry_points
import anyblok
from anyblok.registry import RegistryManager
from anyblok._imp import ImportManager
from time import sleep
from imp import reload, load_source
from sys import modules
from os.path import dirname, join, isdir


class BlokManagerException(Exception):
    """ Simple exception to BlokManager """

    def __init__(self, *args, **kwargs):
        anyblok.AnyBlok.current_blok = None
        super(BlokManagerException, self).__init__(*args, **kwargs)


class BlokManager:
    """ Manage the bloks for one process

    One blok is a setuptools entrypoint, this entry point is define
    by property bloks_groups in the first load

    the property bloks, is a dict with all the entry point load
    """

    bloks = {}
    bloks_groups = None
    ordered_bloks = []

    @classmethod
    def list(cls):
        """ Return the ordered bloks """
        return cls.ordered_bloks

    @classmethod
    def has(cls, blok):
        """ Return True if the blok has loaded """
        return blok and blok in cls.ordered_bloks or False

    @classmethod
    def get(cls, blok):
        """ Return the loaded blok """
        if not cls.has(blok):
            raise BlokManagerException('%r not found' % blok)

        return cls.bloks[blok]

    @classmethod
    def set(cls, blokname, blok):
        """ Add new blok """
        if cls.has(blokname):
            raise BlokManagerException('%r already add' % blokname)

        cls.bloks[blokname] = blok
        cls.ordered_bloks.append(blokname)

    @classmethod
    @anyblok.log()
    def reload(cls):
        """ Reload the entry points

        Empty the dict bloks and use the bloks_groups property to load bloks
        """
        if cls.bloks_groups is None:
            raise BlokManagerException(
                "You must use the load classmethod before use reload")

        cls.bloks = {}
        cls.ordered_bloks = []
        cls.load(*cls.bloks_groups)

    @classmethod
    @anyblok.log()
    def load(cls, *bloks_groups):
        """ Load all the blok and import it

        bloks_groups is use by iter_entry_points to get the blok
        """
        if not isinstance(bloks_groups, (list, tuple)):
            raise BlokManagerException(
                'The bloks_groups must be a list or a tuple')

        cls.bloks_groups = bloks_groups

        if anyblok.AnyBlok.current_blok:
            while anyblok.AnyBlok.current_blok:
                sleep(0.1)

        anyblok.AnyBlok.current_blok = 'start'

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

        #Empty the orderred blok to reload it in function of priority
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
            anyblok.AnyBlok.current_blok = blok
            RegistryManager.init_blok(blok)

            if not ImportManager.has(blok):
                # Import only if not exist don't reload here
                mod_path = dirname(modules[cls.bloks[blok].__module__].__file__)
                mod = ImportManager.add(blok, mod_path)
                mod.imports(*cls.bloks[blok].imports)

            return True

        try:
            while bloks:
                blok = bloks.pop(0)[1]
                get_need_blok(blok)

        except Exception as e:
            raise BlokManagerException(str(e))

        anyblok.AnyBlok.current_blok = None

    @classmethod
    def get_files_from(cls, blok, attribute):
        """ Return a files list with absolute path

        blok is the blok name in ordered_bloks
        attribute must be a list property of this blok

        if attribute doesn't exist then return []
        """
        blok = cls.get(blok)
        if not hasattr(blok, attribute):
            return []

        b_path = dirname(modules[blok.__module__].__file__)
        return [join(b_path, x) for x in getattr(blok, attribute)]


class Blok:
    """ Super class for all the blok

    define the default value for
    * priority: order to load blok
    * required: list of the blok need to install this blok
    * optional: list of bloks to install if present in the blok list
    * conditionnal: if all the list is installated the install this blok
    * imports: list of the python file to import
    """

    priority = 100
    required = []
    optional = []
    conditional = []
    imports = []
