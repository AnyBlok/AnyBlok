# -*- coding: utf-8 -*-
import imp
import anyblok
from sys import modules
from os.path import join, isdir


class ImportManagerException(Exception):
    pass


class ImportManager:
    """ Use to import blok or reload the blok import"""

    modules = {}

    @classmethod
    def add(cls, blok, path):
        """ Add new module in sys.modules """
        if cls.has(blok):
            return cls.get(blok)

        bloks = modules['anyblok.bloks']
        module_name = 'anyblok.bloks.' + blok
        module = imp.new_module(module_name)

        # add import registry
        modules[module_name] = module  # for import anyblok.bloks.blok
        setattr(bloks, blok, module)  # for from anyblok.bloks import blok
        cls.modules[blok] = module  # just for ImportManager.get/has

        # add function of module
        def mod_import_module(filename):
            """ Import the python module """
            mod_name = '.'.join(filename.split('.')[:-1])
            mod = imp.load_source(
                module_name + '.' + mod_name, join(path, filename))
            setattr(module, mod_name, mod)

        def mod_import_package(packagename):
            """ Import the python package """
            mod = imp.load_package(
                module_name + '.' + packagename, join(path, packagename))
            setattr(module, packagename, mod)

        def mod_imports(*args):
            """ Imports modules and / or packages list """
            for mod in args:
                if isdir(join(path, mod)):
                    mod_import_package(mod)
                else:
                    mod_import_module(mod)

        def mod_reload():
            """ Reload all the import for this module """
            for mod_name, mod in modules.items():
                if module_name + '.' in mod_name:
                    imp.reload(mod)

        setattr(module, 'import_module', mod_import_module)
        setattr(module, 'import_package', mod_import_package)
        setattr(module, 'imports', mod_imports)
        setattr(module, 'reload', mod_reload)

        return module

    @classmethod
    def get(cls, blok):
        """ Return the module imported for this blok """
        if not cls.has(blok):
            raise ImportManagerException('Unexisting blok %r' % blok)
        return cls.modules[blok]

    @classmethod
    def has(cls, blok):
        """ Return True if the blok was imported """
        return blok in cls.modules


bloks = imp.new_module('bloks')
modules['anyblok.bloks'] = bloks
anyblok.bloks = bloks
