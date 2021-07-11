# This file is a part of the AnyBlok project
#
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from nose.plugins import Plugin
from os.path import join
from os.path import relpath
from os.path import normpath
from os import pardir
from os import walk
import warnings


def isindir(path, dirpath):
    # normpath simplifies stuff like a/../c but doesn't follow symlinks
    # that's what we need. Nose will feed us absolute paths, btw
    return not relpath(normpath(path), normpath(dirpath)).startswith(pardir)


class Arg2OptOptions:

    def __init__(self, options):
        self.options = options

    def _get_args(self):
        return False

    def _get_kwargs(self):
        keys = ['configfile', 'db_name', 'db_driver_name', 'db_user_name',
                'db_password', 'db_host', 'db_port']

        return [(x, getattr(self.options, x))
                for x in keys] + [('withoutautomigration', True)]

    def __getattr__(self, name, default=None):
        return getattr(self.options, name, default)


class AnyBlokPlugin(Plugin):
    name = 'anyblok-bloks'
    score = 100

    def __init__(self):
        super(AnyBlokPlugin, self).__init__()
        self.registryLoaded = False
        self.AnyBlokOptions = None

    def options(self, parser, env):
        super(AnyBlokPlugin, self).options(parser, env)
        parser.add_option("--anyblok-configfile", dest="configfile")
        parser.add_option('--anyblok-db-name', dest='db_name',
                          default=env.get('ANYBLOK_DATABASE_NAME'),
                          help="Name of the database")
        parser.add_option('--anyblok-db-driver-name', dest='db_driver_name',
                          default=env.get('ANYBLOK_DATABASE_DRIVER'),
                          help="the name of the database backend. This name "
                               "will correspond to a module in "
                               "sqlalchemy/databases or a third party plug-in")
        parser.add_option('--anyblok-db-user-name', dest='db_user_name',
                          default=env.get('ANYBLOK_DATABASE_USER'),
                          help="The user name")
        parser.add_option('--anyblok-db-password', dest='db_password',
                          default=env.get('ANYBLOK_DATABASE_PASSWORD'),
                          help="database password")
        parser.add_option('--anyblok-db-host', dest='db_host',
                          default=env.get('ANYBLOK_DATABASE_HOST'),
                          help="The name of the host")
        parser.add_option('--anyblok-db-port', dest='db_port',
                          default=env.get('ANYBLOK_DATABASE_PORT'),
                          help="The port number")
        parser.add_option('--anyblok-db-url', dest='db_url',
                          default=env.get('ANYBLOK_DATABASE_URL'),
                          help="Complete URL for connection with the database")

    def configure(self, options, conf):
        super(AnyBlokPlugin, self).configure(options, conf)
        if self.enabled:
            warnings.simplefilter('default')
            self.AnyBlokOptions = Arg2OptOptions(options)

    def load_registry(self):
        if not self.enabled or self.registryLoaded:
            return

        from anyblok.config import Configuration, get_db_name
        from anyblok import (
            load_init_function_from_entry_points,
            configuration_post_load,
        )
        from anyblok.blok import BlokManager
        from anyblok.registry import RegistryManager
        from anyblok.common import return_list

        # Load the registry here not in configuration,
        # because the configurations are not loaded in order of score
        self.registryLoaded = True
        load_init_function_from_entry_points(unittest=True)
        Configuration.load_config_for_test()
        Configuration.parse_options(self.AnyBlokOptions)
        configuration_post_load()
        BlokManager.load()
        db_name = get_db_name()

        registry = RegistryManager.get(db_name)
        if not registry:
            return

        installed_bloks = registry.System.Blok.list_by_state("installed")
        selected_bloks = return_list(
            Configuration.get('selected_bloks')) or installed_bloks

        unwanted_bloks = return_list(Configuration.get('unwanted_bloks')) or []

        self.authorized_blok_paths = set(
            BlokManager.getPath(b) for b in BlokManager.list()
            if b in selected_bloks and b not in unwanted_bloks)

        test_dirs = self.authorized_blok_test_dirs = set()
        for startpath in self.authorized_blok_paths:
            for root, dirs, _ in walk(startpath):
                if 'tests' in dirs:
                    test_dirs.add(join(root, 'tests'))

        registry.close()  # free the registry to force create it again

    def file_from_authorized_blok_tests(self, file_path):
        return any(isindir(file_path, tp)
                   for tp in self.authorized_blok_test_dirs)

    def wantModule(self, module):
        self.load_registry()
        return True

    def wantFile(self, file_path, package=None):
        self.load_registry()
        return (self.enabled and
                file_path.endswith(".py") and
                self.file_from_authorized_blok_tests(file_path))

    def wantDirectory(self, path):
        self.load_registry()
        return (self.enabled and
                any(isindir(path, bp) for bp in self.authorized_blok_paths))
