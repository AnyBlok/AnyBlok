# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import anyblok
from sys import modules
from os.path import splitext, split
from os import listdir
from importlib import import_module
from .common import python_version


@anyblok.Declarations.register(anyblok.Declarations.Exception)
class ImportManagerException(Exception):
    """ Exception for Import Manager """


class ImportManager:
    """ Use to import the blok or reload the blok imports

        Add a blok and imports its modules::

            blok = ImportManager.add('my blok')
            blok.imports()

        Reload the modules of a blok::

            if ImportManager.has('my blok'):
                blok = ImportManager.get('my blok')
                blok.reload()
                # import the unimported module
    """
    modules = {}

    @classmethod
    def add(cls, blok):
        """ Store the blok so that we know which bloks to reload if needed

        :param blok: name of the blok to add
        :rtype: loader instance
        :exception: ImportManagerException
        """
        from anyblok.blok import BlokManager
        if cls.has(blok):
            return cls.get(blok)

        if not BlokManager.has(blok):
            raise ImportManagerException("Unexisting blok")

        loader = Loader(blok)
        cls.modules[blok] = loader
        return loader

    @classmethod
    def get(cls, blok):
        """ Return the module imported for this blok

        :param blok: name of the blok to add
        :rtype: loader instance
        :exception: ImportManagerException
        """
        if not cls.has(blok):
            raise ImportManagerException('Unexisting blok %r' % blok)
        return cls.modules[blok]

    @classmethod
    def has(cls, blok):
        """ Return True if the blok was imported

        :param blok: name of the blok to add
        :rtype: boolean
        """
        return blok in cls.modules


class Loader:

    def __init__(self, blok):
        self.blok = blok
        self.import_known = []

    def imports(self):
        """ Imports modules and / or packages listed in the blok path"""
        from anyblok.blok import BlokManager
        from anyblok.registry import RegistryManager

        RegistryManager.init_blok(self.blok)
        b = BlokManager.get(self.blok)
        main_path = modules[b.__module__].__file__
        path, init = split(main_path)

        mods = [x for x in listdir(path) if x != init and x[0] != '.']
        for module in mods:
            module_name = b.__module__ + '.' + splitext(module)[0]
            try:
                import_module(module_name)
            except ImportError:
                pass

        self.import_known = [x for x in modules.keys()
                             if b.__module__ + '.' in x]

    def reload(self):
        """ Reload all the imports for this module

        :exception: ImportManagerException
        """
        isimp = False
        try:
            from importlib import reload as reload_module
        except ImportError:
            isimp = True
            from imp import reload as reload_module

        from anyblok.blok import BlokManager
        from anyblok.registry import RegistryManager
        from anyblok.environment import EnvironmentManager

        b = BlokManager.get(self.blok)
        b.clean_before_reload()
        RegistryManager.init_blok(self.blok)
        main_path = modules[b.__module__].__file__
        path, init = split(main_path)
        mods = [x for x in listdir(path) if x != init and x[0] != '.']

        try:
            EnvironmentManager.set('reload', True)

            for module in mods:
                module_name = b.__module__ + '.' + splitext(module)[0]
                if module_name in self.import_known:
                    continue

                try:
                    import_module(module_name)
                except ImportError:
                    pass

            self.import_known.sort()
            for module in self.import_known:
                try:
                    if isimp:
                        module2load = modules[module]
                    elif python_version() == (3, 3):
                        module2load = module
                    elif python_version() >= (3, 4):
                        module2load = modules[module]
                    else:
                        raise ImportManagerException(
                            "Unknow action to do to reload module %r" % module)

                    reload_module(module2load)
                except ImportError:
                    pass
        finally:
            EnvironmentManager.set('reload', False)

        self.import_known = [x for x in modules.keys()
                             if b.__module__ + '.' in x]
