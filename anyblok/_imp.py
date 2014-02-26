# -*- coding: utf-8 -*-
import imp
import anyblok
from sys import modules
from os.path import join, isdir, isfile
from os import listdir


class ImportManagerException(Exception):
    """ Simple inheritance of Exception class """
    pass


class ImportManager:
    """ Use to import blok or reload the blok import

        Add a blok and imports these modules::

            blok = ImportManager.add('new blok', 'path of the blok')
            blok.imports(*(modules to import in the blok))

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
        :param path: path of this blok
        :rtype: blok module
        """
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

        def mod_imports():
            """ Imports modules and / or packages listed in the blok path"""
            mods = [x for x in listdir(path) if '__' != x[:2] and x != 'tests']
            for mod in mods:
                if isdir(join(path, mod)):
                    if isfile(join(path, mod, '__init__.py')):
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
        """ Return the module imported for this blok

        :param blok: name of the blok to add
        :rtype: blok module
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


bloks = imp.new_module('bloks')
modules['anyblok.bloks'] = bloks
anyblok.bloks = bloks
