# -*- coding: utf-8 -*-
import anyblok
from sys import modules
from os.path import join, splitext, basename, isdir
from os import listdir
from importlib.machinery import SourceFileLoader


@anyblok.Declarations.target_registry(anyblok.Declarations.Exception)
class ImportManagerException(Exception):
    """ Simple inheritance of Exception class """
    pass


class ImportManager:
    """ Use to import blok or reload the blok import


        Add a blok and imports these modules::

            blok = ImportManager.add('my blok')
            blok.imports()

        Reload the modules of one blok::

            if ImportManager.has('my blok'):
                blok = ImportManager.get('my blok')
                blok.reload()

    """

    modules = {}

    @classmethod
    def add(cls, blok, path):
        """ Add new module in sys.modules

        :param blok: name of the blok to add
        :rtype: loader instance
        """
        from anyblok.blok import BlokManager
        if cls.has(blok):
            return cls.get(blok)

        if not BlokManager.has(blok):
            raise ImportManagerException("Unexisting blok")

        loader = Loader(blok, path)
        cls.modules[blok] = loader
        return loader

    @classmethod
    def get(cls, blok):
        """ Return the module imported for this blok

        :param blok: name of the blok to add
        :rtype: loader instance
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

    def __init__(self, blok, path):
        self.blok = blok
        self.path = '/' + join(*path.split('/')[:-1])
        self.module = basename(path)

    def imports(self):
        """ Imports modules and / or packages listed in the blok path"""
        from anyblok.registry import RegistryManager
        from anyblok.blok import BlokManager

        if RegistryManager.has_blok(self.blok):
            BlokManager.get(self.blok).clean_before_reload()

        RegistryManager.init_blok(self.blok)
        module_name = 'anyblok.bloks.' + self.blok
        module_path = join(self.path, self.module)
        loader = SourceFileLoader(module_name, module_path)
        mainmodule = loader.load_module(module_name)

        mods = [x for x in listdir(self.path)
                if x != self.module and x[0] != '.']
        for module in mods:
            module_name = 'anyblok.bloks.' + self.blok + '.'
            module_name += splitext(module)[0]
            module_path = join(self.path, module)
            if isdir(module_path):
                module_path = join(module_path, '__init__.py')

            loader = SourceFileLoader(module_name, module_path)
            try:
                mod = loader.load_module(module_name)
                setattr(mainmodule, splitext(module)[0], mod)
            except FileNotFoundError:
                pass

    def reload(self):
        """ Reload all the import for this module """
        isimportlib = isimp = False
        try:
            from importlib import reload as _reload
            isimportlib = True
        except ImportError:
            from imp import reload as _reload
            isimp = True

        from anyblok.blok import BlokManager
        from anyblok.registry import RegistryManager
        from anyblok.environment import EnvironmentManager
        BlokManager.get(self.blok).clean_before_reload()
        RegistryManager.init_blok(self.blok)
        module_name = 'anyblok.bloks.' + self.blok
        try:
            EnvironmentManager.set('reload', True)
            for mod_name, mod in modules.items():
                if module_name + '.' in mod_name:
                    if isimportlib:
                        _reload(mod_name)
                    elif isimp:
                        _reload(mod)
        finally:
            EnvironmentManager.set('reload', False)
