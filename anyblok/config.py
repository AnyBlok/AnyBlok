# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from .logging import log
from argparse import ArgumentParser
from configparser import ConfigParser
import sys
import os
import json
import yaml
from appdirs import AppDirs
from os.path import join, isfile
from logging import (getLogger, config, NOTSET, DEBUG, INFO, WARNING, ERROR,
                     CRITICAL, basicConfig, Logger)
logger = getLogger(__name__)


def getParser(description):
    """ Return a parser

    :param description: label of the configuration help
    :rtype: ``ArgumentParser`` instance
    """
    return ArgumentParser(description=description)


class ConfigurationException(LookupError):
    """ Simple Exception for Configuration"""


class Configuration:
    """ ``Configuration`` is used to define the options of the real argparse
    and its default values. Each application or blok can declare needed
    options here.

    This class stores three attributes:

    * groups: lists of options indexed by part, a part is a ``ConfigParser``
      group, or a process name
    * labels: if a group has got a label then all the options in group are
      gathered in a parser group
    * configuration: result of the ``Configuration`` after loading

    """

    groups = {}
    labels = {}
    configuration = {}

    @classmethod
    def init_groups_for(cls, group, part, label):
        if part not in cls.groups:
            cls.groups[part] = {group: []}
        elif group not in cls.groups[part]:
            cls.groups[part][group] = []

        if label:
            if part not in cls.labels:
                cls.labels[part] = {group: label}
            else:
                cls.labels[part][group] = label

    @classmethod
    def add(cls, group, part='bloks', label=None, function_=None,
            must_be_loaded_by_unittest=False):
        """ Add a function in a part and a group.

        The function must have two arguments:

        * ``parser``: the parser instance of argparse
        * ``default``: A dict with the default value

        This function is called to know what the options of this must do.
        You can declare this group:

        * either by calling the ``add`` method as a function::

            def foo(parser, default):
                pass

            Configuration.add('create-db', function_=foo)

        * or by calling the ``add`` method as a decorator::

            @Configuration.add('create-db')
            def bar(parser, default):
                pass

        By default the group is unnamed, if you want a named group, you must
        set the ``label`` attribute::

            @Configuration.add('create-db', label="Name of the group")
            def bar(parser, default):
                pass

        :param part: ConfigParser group or process name
        :param group: group is a set of parser option
        :param label: If the group has a label then all the functions in the
            group are put in group parser
        :param function_: function to add
        :param must_be_loaded_by_unittest: unittest call this function to init
            configuration of AnyBlok for run unittest"
        """
        cls.init_groups_for(group, part, label)
        if function_:
            if function_ not in cls.groups[part][group]:
                function_.must_be_loaded_by_unittest = \
                    must_be_loaded_by_unittest
                cls.groups[part][group].append(function_)
        else:

            def wrapper(function):
                if function not in cls.groups[part][group]:
                    function.must_be_loaded_by_unittest = \
                        must_be_loaded_by_unittest
                    cls.groups[part][group].append(function)
                return function

            return wrapper

    @classmethod
    def get(self, opt, default=None):
        """ Get a value from the configuration dict after loading

        After the loading of the application, all the options are saved in the
        Configuration. And all the applications have free access to
        these options::

            from anyblok._configuration import Configuration

            database = Configuration.get('db_name')

        ..warning::

            Some options are used as a default value not real value, such
            as the db_name

        :param opt: name of the option
        :param default: default value if the option doesn't exist
        """
        res = self.configuration.get(opt)
        if res:
            return res
        elif default:
            return default

        return res

    @classmethod
    def remove_label(cls, group, part='bloks'):
        """ Remove an existing label

        The goal of this function is to remove an existing label of a specific
        group::

            @Configuration.add('create-db', label="Name of the group")
            def bar(parser, defaul):
                pass

            Configuration.remove_label('create-db')

        :param part: ConfigParser group or process name
        :param group: group is a set of parser option
        """
        if part in cls.labels:
            if group in cls.labels[part]:
                del cls.labels[part][group]

    @classmethod
    def remove(cls, group, function_, part='bloks'):
        """ Remove an existing function

        If your application inherits some unwanted options from a specific
        function, you can unlink this function::

            def foo(opt, default):
                pass

            Configuration.add('create-db', function_=foo)
            Configuration.remove('create-db', function_=foo)

        :param part: ConfigParser group or process name
        :param group: group is a set of parser option
        :param function_: function to add
        """
        if part in cls.groups:
            if group in cls.groups[part]:
                if function_ in cls.groups[part][group]:
                    cls.groups[part][group].remove(function_)

    @classmethod
    def _merge_groups(cls, *parts):
        """ Internal method to merge groups in function of parts

        :param parts: parts to merge
        :exception: ConfigurationException
        """
        if not parts:
            raise ConfigurationException("No parts to merge")

        groups = {}

        for part in parts:
            if part not in cls.groups:
                continue

            for k, v in cls.groups[part].items():
                if k in groups:
                    groups[k].extend(v)
                else:
                    groups[k] = [] + v

        return groups

    @classmethod
    def _merge_labels(cls, *parts):
        """ Internal method to merge labels in function of parts

        :param parts: parts to merge
        :exception: ConfigurationException
        """
        if not parts:
            raise ConfigurationException("No parts to merge")

        labels = {}

        for part in parts:
            if part not in cls.labels:
                continue

            for k, v in cls.labels[part].items():
                labels[k] = v

        return labels

    @classmethod
    def get_url(cls, db_name=None):
        """ Return an sqlalchemy URL for database

        Get the options of the database, the only option which can be
        overloaded is the name of the database::

            url = Configuration.get_url(db_name='Mydb')

        :param db_name: Name of the database
        :rtype: SqlAlchemy URL
        :exception: ConfigurationException
        """
        drivername = cls.configuration.get('db_driver_name', None)
        username = cls.configuration.get('db_user_name', None)
        password = cls.configuration.get('db_password', None)
        host = cls.configuration.get('db_host', None)
        port = cls.configuration.get('db_port', None)
        port = int(port) if port else None
        database = cls.configuration.get('db_name', None)

        if drivername is None:
            raise ConfigurationException('No Drivername defined')

        if db_name is not None:
            database = db_name

        from sqlalchemy.engine.url import URL
        return URL(drivername, username=username, password=password, host=host,
                   port=port, database=database)

    @classmethod
    @log(logger)
    def load_config_for_test(cls):
        if not cls.configuration:
            parser = getParser("Initialise unit test")
            for part in cls.groups.values():
                for fncts in part.values():
                    for fnct in fncts:
                        if fnct.must_be_loaded_by_unittest:
                            fnct(parser, cls.configuration)

    @classmethod
    @log(logger)
    def load(cls, description='AnyBlok :', configuration_groups=None,
             parts_to_load=('bloks',), useseparator=False):
        """ Load the argparse definition and parse them

        :param description: description of configuration
        :param configuration_groups: list configuration groupe to load
        :param parts_to_load: group of blok to load
        :param useseparator: boolean(default False)
        """

        sep = len(sys.argv)
        our_argv = sys.argv[1:]
        if useseparator:
            description += "[options] -- other arguments"
            parser = getParser(description)

            try:
                sep = sys.argv.index('--')
                our_argv = sys.argv[1:sep]
            except ValueError:
                pass
        else:
            parser = getParser(description)

        cls._load(parser, configuration_groups, parts_to_load)
        args = parser.parse_args(our_argv)
        if sep is not None:
            del sys.argv[1:sep+1]

        cls.parse_options(args, parts_to_load)

    @classmethod
    def _load(cls, parser, configuration_groups, parts_to_load):
        """ Load the argparse definition and parse them

        :param description: description of configuration
        :param configuration_groups: list configuration groupe to load
        :param parts_to_load: group of blok to load
        :param useseparator: boolean(default False)
        """
        if configuration_groups is None:
            return

        groups = cls._merge_groups(*parts_to_load)
        labels = cls._merge_labels(*parts_to_load)

        for group in groups:
            if group not in configuration_groups:
                continue

            label = labels.get(group)
            if label:
                g = parser.add_argument_group(label)
            else:
                g = parser

            for function in groups[group]:
                function(g, cls.configuration)

    @classmethod
    def initialize_logging(cls):
        level = {
            'NOTSET': NOTSET,
            'DEBUG': DEBUG,
            'INFO': INFO,
            'WARNING': WARNING,
            'ERROR': ERROR,
            'CRITICAL': CRITICAL
        }.get(cls.configuration.get('logging_level'))
        logging_configfile = cls.configuration.get('logging_configfile')
        json_logging_configfile = cls.configuration.get(
            'json_logging_configfile')
        yaml_logging_configfile = cls.configuration.get(
            'yaml_logging_configfile')
        logging_level_qualnames = cls.configuration.get(
            'logging_level_qualnames')

        if logging_configfile:
            config.fileConfig(logging_configfile)
        elif json_logging_configfile:
            with open(json_logging_configfile, 'rt') as f:
                configfile = json.load(f.read())
                config.dictConfig(configfile)
        elif yaml_logging_configfile:
            with open(yaml_logging_configfile, 'rt') as f:
                configfile = yaml.load(f.read())
                config.dictConfig(configfile)

        if level:
            basicConfig(level=level)
            if logging_level_qualnames:
                qualnames = set(x.split('.')[0]
                                for x in Logger.manager.loggerDict.keys()
                                if x in logging_level_qualnames)
            else:
                qualnames = set(x.split('.')[0]
                                for x in Logger.manager.loggerDict.keys())

            for qualname in qualnames:
                getLogger(qualname).setLevel(level)

    @classmethod
    def parse_configfile(cls, configfile, parts_to_load):
        cur_cwd = os.getcwd()
        configfile = os.path.abspath(configfile)
        print('Load config file %r' % configfile)
        if not isfile(configfile):
            return

        cwd_file, file_name = os.path.split(configfile)
        configuration = {}
        try:
            os.chdir(cwd_file)
            cparser = ConfigParser()
            cparser.read(configfile)
            sections = [y for x in parts_to_load + ('AnyBlok',)
                        if cparser.has_section(x)
                        for y in cparser.items(x)]

            for opt, value in sections:
                if opt in ('logging_configfile', 'json_logging_configfile',
                           'yaml_logging_configfile'):
                    if value:
                        value = os.path.abspath(value)

                configuration[opt] = value

            if 'extend' in configuration:
                extend = configuration.pop('extend')
                if extend:
                    cls.parse_configfile(extend, parts_to_load)

        finally:
            os.chdir(cur_cwd)

        cls.configuration.update(configuration)

    @classmethod
    def parse_options(cls, arguments, parts_to_load):
        if arguments._get_args():
            raise ConfigurationException(
                'Positional arguments are forbidden')

        ad = AppDirs('AnyBlok')
        # load the global configuration file
        cls.parse_configfile(
            join(ad.site_config_dir, 'conf.cfg'), parts_to_load)
        # load the user configuration file
        cls.parse_configfile(
            join(ad.user_config_dir, 'conf.cfg'), parts_to_load)
        if 'configfile' in dict(arguments._get_kwargs()).keys():
            if arguments.configfile:
                cls.parse_configfile(arguments.configfile, parts_to_load)

        for opt, value in arguments._get_kwargs():
            if opt not in cls.configuration or value:
                cls.configuration[opt] = value

        if 'logging_level' in cls.configuration:
            cls.initialize_logging()


@Configuration.add('config')
def add_configuration_file(parser, configuration):
    parser.add_argument('-c', dest='configfile', default='',
                        help="Relative path of the config file")
    parser.add_argument('--without-auto-migration', dest='withoutautomigration',
                        action='store_true')
    configuration.update({
        'configfile': None,
        'withoutautomigration': False,
    })


@Configuration.add('database', label="Database",
                   must_be_loaded_by_unittest=True)
def add_database(group, configuration):
    group.add_argument('--db-name', default='',
                       help="Name of the database")
    group.add_argument('--db-driver-name', default='',
                       help="the name of the database backend. This name "
                            "will correspond to a module in "
                            "sqlalchemy/databases or a third party plug-in")
    group.add_argument('--db-user-name', default='',
                       help="The user name")
    group.add_argument('--db-password', default='',
                       help="database password")
    group.add_argument('--db-host', default='',
                       help="The name of the host")
    group.add_argument('--db-port', default='',
                       help="The port number")
    group.add_argument('--db-echo', action="store_true")

    configuration.update({
        'db_name': os.environ.get('ANYBLOK_DATABASE_NAME'),
        'db_driver_name': os.environ.get('ANYBLOK_DATABASE_DRIVER'),
        'db_user_name': os.environ.get('ANYBLOK_DATABASE_USER'),
        'db_password': os.environ.get('ANYBLOK_DATABASE_PASSWORD'),
        'db_host': os.environ.get('ANYBLOK_DATABASE_HOST'),
        'db_port': os.environ.get('ANYBLOK_DATABASE_PORT'),
        'db_echo': os.environ.get('ANYBLOK_DATABASE_ECHO') or False,
    })


@Configuration.add('install-bloks')
def add_install_bloks(parser, configuration):
    parser.add_argument('--install-bloks', default='',
                        help="blok to install")
    parser.add_argument('--install-all-bloks',
                        action='store_true')
    parser.add_argument('--test-blok-at-install',
                        action='store_true')
    parser.set_defaults(test_blok=False)


@Configuration.add('uninstall-bloks')
def add_uninstall_bloks(parser, configuration):
    parser.add_argument('--uninstall-bloks',
                        default='', help="bloks to uninstall")


@Configuration.add('update-bloks')
def add_update_bloks(parser, configuration):
    parser.add_argument('--update-bloks', default='',
                        help="bloks to update")
    parser.add_argument('--update-all-bloks',
                        action='store_true')


@Configuration.add('interpreter')
def add_interpreter(parser, configuration):
    parser.add_argument('--script', dest='python_script',
                        help="Python script to execute")


@Configuration.add('schema', label="Schema options")
def add_schema(group, configuration):
    from graphviz.files import FORMATS
    group.add_argument('--schema-format',
                       default='png', choices=tuple(FORMATS))


@Configuration.add('doc', label="Doc options")
def add_doc(group, configuration):
    group.add_argument('--doc-format',
                       default='RST', choices=('RST', 'UML', 'SQL'))
    group.add_argument('--doc-output',
                       default='anyblok-documentation')
    group.add_argument('--doc-wanted-models',
                       help='Detail only these models separated by ","')
    group.add_argument('--doc-unwanted-models',
                       help='No detail these models separated by ","')


@Configuration.add('unittest', label="Unittest")
def add_unittest(group, configuration):
    group.add_argument('--selected-bloks', default='',
                       help="Name of the bloks to test")
    group.add_argument('--unwanted-bloks', default='',
                       help="Name of the bloks to no test")


@Configuration.add('logging', label="Logging")
def add_logging(group, configuration):
    group.add_argument('--logging-level', dest='logging_level',
                       choices=['NOTSET', 'DEBUG', 'INFO', 'WARNING',
                                'ERROR', 'CRITICAL'], default='')
    group.add_argument('--logging-level-qualnames', nargs='+',
                       dest='logging_level_qualnames',
                       help="Limit the log level on a qualnames list")
    group.add_argument('--logging-config-file', dest='logging_configfile',
                       default='',
                       help="Relative path of the logging config file")
    group.add_argument('--logging-json-config-file',
                       dest='json_logging_configfile', default='',
                       help="Relative path of the logging config file (json). "
                            "Only if the logging config file doesn't filled")
    group.add_argument('--logging-yaml-config-file',
                       dest='yaml_logging_configfile', default='',
                       help="Relative path of the logging config file (yaml). "
                            "Only if the logging and json config file doesn't "
                            "filled")
