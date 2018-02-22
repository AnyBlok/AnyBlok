# This file is a part of the AnyBlok project
#
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from nose.plugins import Plugin
from anyblok.config import Configuration, get_db_name
from anyblok import (
    load_init_function_from_entry_points,
    configuration_post_load,
)
from anyblok.blok import BlokManager
from anyblok.registry import RegistryManager, return_list
from os.path import join
from os import walk


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
        self.authoried_bloks_test_files = []
        self.bloks_path = []
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
            self.AnyBlokOptions = Arg2OptOptions(options)

    def load_registry(self):
        if self.enabled and self.registryLoaded is False:
            # Load the registry here not in configuration,
            # because the configuration are not load in order of score
            self.registryLoaded = True
            load_init_function_from_entry_points(unittest=True)
            Configuration.load_config_for_test()
            Configuration.parse_options(self.AnyBlokOptions)
            configuration_post_load()
            BlokManager.load()
            db_name = get_db_name()

            registry = RegistryManager.get(db_name)
            if registry:
                installed_bloks = registry.System.Blok.list_by_state(
                    "installed")
                selected_bloks = return_list(
                    Configuration.get('selected_bloks')) or installed_bloks

                unwanted_bloks = return_list(
                    Configuration.get('unwanted_bloks')) or []

                self.bloks_path = [BlokManager.getPath(x)
                                   for x in BlokManager.ordered_bloks]

                self.authoried_bloks_test_files = []
                for blok in installed_bloks:
                    if blok not in selected_bloks or blok in unwanted_bloks:
                        continue

                    startpath = BlokManager.getPath(blok)
                    for root, dirs, _ in walk(startpath):
                        if 'tests' in dirs:
                            self.authoried_bloks_test_files.append(
                                join(root, 'tests'))

                registry.close()  # free the registry to force create it again

    def file_from_blok(self, file):
        for blok_path in self.bloks_path:
            if file.startswith(blok_path):
                return True

        return False

    def file_from_authorized_bloks(self, file):
        for testFile in self.authoried_bloks_test_files:
            if file.startswith(testFile):
                return True

        return False

    def wantModule(self, module):
        self.load_registry()
        return True

    def wantFile(self, file, package=None):
        self.load_registry()
        if self.enabled:
            if file.endswith(".py"):
                if self.file_from_blok(file):
                    return self.file_from_authorized_bloks(file)

        return None
