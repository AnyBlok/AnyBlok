# -*- coding: utf-8 -*-
import imp
import anyblok
from sys import modules
from os.path import join, isdir, isfile
from os import listdir


@anyblok.Declarations.target_registry(anyblok.Declarations.Exception)
class ImportManagerException(Exception):
    """ Simple inheritance of Exception class """
    pass


class ImportManager:
    """ Use to import blok or reload the blok import


        ..warning

            use the namespace to declare your each of your blok

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
        from anyblok.registry import RegistryManager
        from anyblok.blok import BlokManager
        if cls.has(blok):
            return cls.get(blok)

        module_name = 'anyblok.bloks.' + blok

        # add import registry
        module = modules[module_name]
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
            if RegistryManager.has_blok(blok):
                BlokManager.get(blok).clean_before_reload()

            RegistryManager.init_blok(blok)
            mods = [x for x in listdir(path) if '_' != x[0]]
            for mod in mods:
                if mod == 'tests':
                    continue

                if isdir(join(path, mod)):
                    if isfile(join(path, mod, '__init__.py')):
                        mod_import_package(mod)
                else:
                    if mod[-3:] != '.py':
                        continue

                    mod_import_module(mod)

        def mod_reload():
            """ Reload all the import for this module """
            BlokManager.get(blok).clean_before_reload()
            RegistryManager.init_blok(blok)
            for mod_name, mod in modules.items():
                if module_name + '.' in mod_name:
                    if mod_name[len(module_name) + 1] != '_':
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
