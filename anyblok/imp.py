# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from .common import python_version

issix = False
try:
    from importlib import reload as reload_module
except ImportError:
    issix = True
    from six.moves import reload_module


def reload_wraper(module):
    if issix:
        module2reload = module

    elif python_version() == (3, 3):
        module2reload = module.__name__
    elif python_version() >= (3, 4):
        module2reload = module
    else:
        raise ImportManagerException(
            "Unknow action to do to reload module %r" %
            module.__name__)

    reload_module(module2reload)


def reload_module_if_blok_is_reloading(module):
    from anyblok.environment import EnvironmentManager

    if EnvironmentManager.get('reload', default=False):
        reload_wraper(module)


class ImportManagerException(AttributeError):
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

    def imports(self):
        """ Imports modules and / or packages listed in the blok path"""
        from anyblok.blok import BlokManager
        from anyblok.registry import RegistryManager

        RegistryManager.init_blok(self.blok)
        b = BlokManager.get(self.blok)
        b.import_declaration_module()

    def reload(self):
        """ Reload all the imports for this module

        :exception: ImportManagerException
        """
        from anyblok.blok import BlokManager
        from anyblok.registry import RegistryManager
        from anyblok.environment import EnvironmentManager

        b = BlokManager.get(self.blok)
        if not hasattr(b, 'reload_declaration_module'):
            return

        try:
            EnvironmentManager.set('reload', True)
            RegistryManager.init_blok(self.blok)
            b.reload_declaration_module(reload_wraper)
        finally:
            EnvironmentManager.set('reload', False)
