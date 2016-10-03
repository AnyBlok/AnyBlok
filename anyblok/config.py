# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from .logging import log
from argparse import ArgumentParser, _ArgumentGroup, REMAINDER
from configparser import ConfigParser
import sys
import os
import json
import yaml
from appdirs import AppDirs
from os.path import join, isfile
from sqlalchemy.engine.url import URL, make_url
from logging import (getLogger, config, NOTSET, DEBUG, INFO, WARNING, ERROR,
                     CRITICAL, basicConfig, Logger)
logger = getLogger(__name__)


def get_url(db_name=None):
    """ Return an sqlalchemy URL for database

    Get the options of the database, the only option which can be
    overloaded is the name of the database::

        url = get_url(db_name='Mydb')

    ..note::

        Since 0.5.3, an URL can be define by the configuration file.
        The *username*, *password* and *database* if overwrite by the
        options if they are filled::

            # db_url = 'postgresql:///db'
            get_url()
            ==> 'postgresql:///db'
            # db_user_name = 'jssuzanne'
            # db_password = 'secret'
            get_url()
            ==> 'postgresql://jssuzanne:secret@/db'
            # db_name = 'db1'
            get_url()
            ==> 'postgresql://jssuzanne:secret@/db1'
            get_url(db_name='Mydb')
            ==> 'postgresql://jssuzanne:secret@/Mydb'

    :param db_name: Name of the database
    :rtype: SqlAlchemy URL
    :exception: ConfigurationException
    """
    url = Configuration.get('db_url', None)
    drivername = Configuration.get('db_driver_name', None)
    username = Configuration.get('db_user_name', None)
    password = Configuration.get('db_password', None)
    host = Configuration.get('db_host', None)
    port = Configuration.get('db_port', None)
    database = Configuration.get('db_name', None)

    if db_name is not None:
        database = db_name

    if url:
        url = make_url(url)
        if username:
            url.username = username
        if password:
            url.password = password
        if database:
            url.database = database

        return url

    if drivername is None:
        raise ConfigurationException('No Drivername defined')

    return URL(drivername, username=username, password=password, host=host,
               port=port, database=database)


class ConfigurationException(LookupError):
    """ Simple Exception for Configuration"""


def is_none(type, value):
    """Check if the value is a *NoneValue* in function of the type

    :param type: type of value
    :param value: value to check
    :rtype: *bool*, True if it is a *NoneValue*
    """
    if value is None:
        return True
    if isinstance(value, str) and value.upper() == 'NONE':
        return True
    if value == '' and type is not str:
        return True

    return False


def cast_value(cast, value):
    """Cast the value

    :param cast: final type of data wanted
    :param value: initial value to cast
    :rtype: casted value or *NoneValue*
    """
    if is_none(cast, value):
        return None
    elif not cast:
        return value
    elif cast is bool and isinstance(value, str):
        if value.upper() == 'TRUE':
            return True
        else:
            return False
    else:
        return cast(value)


def nargs_type(key, nargs, cast):

    def wrap(val):
        if isinstance(val, str):
            sep = ' '
            if '\n' in val:
                sep = '\n'
            elif ',' in val:
                sep = ','
            val = [x.strip() for x in val.split(sep)]

        if not isinstance(val, list):
            raise ConfigurationException("Waiting list not %r for %r "
                                         "get : %r" % (type(val), key, val))

        limit = len(val)
        if nargs not in ('?', '+', '*', REMAINDER):
            limit = int(nargs)

        return [cast_value(cast, x) for x in val[:limit]]

    return wrap


class AnyBlokActionsContainer:

    def add_argument(self, *args, **kwargs):
        """Overload the method to add the entry in the configuration dict"""
        default = kwargs.pop('default', None)
        nargs = kwargs.get('nargs', None)
        type = kwargs.get('type')
        arg = super(AnyBlokActionsContainer, self).add_argument(
            *args, **kwargs)
        if type is None:
            if kwargs.get('action') == 'store_true':
                type = bool
                if default is None:
                    default = False
            else:
                type = str

        dest = arg.dest
        if nargs:
            type = nargs_type(dest, nargs, type)

        Configuration.add_argument(dest, default, type=type)
        return arg

    def set_defaults(self, **kwargs):
        """Overload the method to update the entry in the configuration dict"""
        super(AnyBlokActionsContainer, self).set_defaults(**kwargs)
        for dest, default in kwargs.items():
            if not Configuration.has(dest):
                raise KeyError('Unexisting option %s' % dest)

            Configuration.set(dest, default)

    def add_argument_group(self, *args, **kwargs):
        group = AnyBlokArgumentGroup(self, *args, **kwargs)
        self._action_groups.append(group)
        return group


class AnyBlokArgumentParser(AnyBlokActionsContainer, ArgumentParser):
    """Over load the argparse in the goal to define type directly by
    Configuration class for argparse and config files
    """


class AnyBlokArgumentGroup(AnyBlokActionsContainer, _ArgumentGroup):
    """Over load the argparse group in the goal to define type directly by
    Configuration class for argparse and config files
    """


def AnyBlokPlugin(import_definition):
    """Callable to cast import string definition to object

    ::

        path = AnyBlokPlugin('sys:path')
        //
        Registry = AnyBlokPlugin('anyblok.registry:Registry')

    :param import_definition: string of the object to import
    :rtype: imported object
    """
    if not isinstance(import_definition, str):
        return import_definition

    import_path, import_name = import_definition.split(':')
    module = __import__(import_path, fromlist=[import_name])
    if hasattr(module, import_name):
        return getattr(module, import_name)

    raise ImportError("%s does not exist in %s" % (import_name, import_path))


class ConfigOption:

    def __init__(self, value, type):
        self.type = type
        self.set(value)

    def get(self):
        return self.value

    def set(self, value):
        self.value = cast_value(self.type, value)


def getParser(**kwargs):
    """ Return a parser

    :param description: label of the configuration help
    :rtype: ``ArgumentParser`` instance
    """
    return AnyBlokArgumentParser(**kwargs)


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
    applications = {
        'default': {
            'description': "[options] -- other arguments",
            'configuration_groups': ['config', 'database'],
        },
    }

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
    def has(cls, option):
        """ Check if the option exist in the configuration dict

        Return True if the option is in the configuration dict and the
        value is not None. A None value is diferent that a ConfigOption with
        None value

        :param opt: option key to check
        :rtype: boolean True is exist
        """
        if option in cls.configuration and cls.configuration[option]:
            return True

        return False

    @classmethod
    def get(cls, opt, default=None):
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
        if cls.has(opt):
            return cls.configuration[opt].get()

        return default

    @classmethod
    def set(cls, opt, value):
        """ Set a value to the configuration dict

        :param opt: name of the option
        :param value: value to set
        """

        try:
            if opt in cls.configuration:
                cls.configuration[opt].set(value)
            else:
                cls.add_argument(opt, value, type(value))
        except:
            logger.exception("Error durring set the value %r on the option "
                             "%r" % (value, opt))
            raise

    @classmethod
    def update(cls, *args, **kwargs):
        if args:
            if len(args) > 1:
                raise ConfigurationException("Wainting only one dict")

            if not isinstance(args[0], dict):
                raise ConfigurationException("Wainting a dict")

            for k, v in args[0].items():
                cls.set(k, v)

        for k, v in kwargs.items():
            cls.set(k, v)

    @classmethod
    def add_argument(cls, key, value, type=str):
        cls.configuration[key] = ConfigOption(value, type)

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
    @log(logger)
    def load_config_for_test(cls):
        """Load the argparse configuration need for the unittest"""
        if not cls.configuration:
            parser = getParser()
            for parts in cls.groups.values():
                for part, fncts in parts.items():
                    for fnct in fncts:
                        if (
                            fnct.must_be_loaded_by_unittest or
                            part in ('plugins',)
                        ):
                            fnct(parser)

    @classmethod
    @log(logger)
    def load(cls, application, configuration_groups=None,
             parts_to_load=('bloks',), useseparator=False, **kwargs):
        """ Load the argparse definition and parse them

        :param application: name of the application
        :param configuration_groups: iterable configuration group to load
        :param parts_to_load: group of blok to load
        :param useseparator: boolean(default False)
        :param \**kwargs: ArgumentParser named arguments
        """

        sep = len(sys.argv)
        our_argv = sys.argv[1:]
        description = {}
        if application in cls.applications:
            description.update(cls.applications[application])
        else:
            description.update(cls.applications['default'])

        description.update(kwargs)
        _configuration_groups = description.pop('configuration_groups',
                                                ['config', 'database'])
        configuration_groups = set(configuration_groups or []).union(
            _configuration_groups)
        configuration_groups.add('plugins')
        if useseparator:
            parser = getParser(**description)

            try:
                sep = sys.argv.index('--')
                our_argv = sys.argv[1:sep]
            except ValueError:
                pass
        else:
            parser = getParser(**description)

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
                function(g)

    @classmethod
    def initialize_logging(cls):
        level = {
            'NOTSET': NOTSET,
            'DEBUG': DEBUG,
            'INFO': INFO,
            'WARNING': WARNING,
            'ERROR': ERROR,
            'CRITICAL': CRITICAL
        }.get(cls.get('logging_level'))
        logging_configfile = cls.get('logging_configfile')
        json_logging_configfile = cls.get('json_logging_configfile')
        yaml_logging_configfile = cls.get('yaml_logging_configfile')
        logging_level_qualnames = cls.get('logging_level_qualnames')

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

        cls.update(**configuration)

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
                cls.set(opt, value)

        if 'logging_level' in cls.configuration:
            cls.initialize_logging()


@Configuration.add('plugins', label='Plugins',
                   must_be_loaded_by_unittest=True)
def add_plugins(group):
    group.add_argument('--registry-cls', dest='Registry', type=AnyBlokPlugin,
                       default='anyblok.registry:Registry',
                       help="Registry class to use")
    group.add_argument('--migration-cls', dest='Migration',
                       type=AnyBlokPlugin,
                       default='anyblok.migration:Migration',
                       help="Migration class to use")
    group.add_argument('--get-url-fnct', dest='get_url',
                       type=AnyBlokPlugin,
                       default='anyblok.config:get_url',
                       help="get_url function to use")


@Configuration.add('config')
def add_configuration_file(parser):
    parser.add_argument('-c', dest='configfile',
                        help="Relative path of the config file")
    parser.add_argument('--without-auto-migration', dest='withoutautomigration',
                        action='store_true')


@Configuration.add('database', label="Database",
                   must_be_loaded_by_unittest=True)
def add_database(group):
    group.add_argument('--db-name',
                       default=os.environ.get('ANYBLOK_DATABASE_NAME'),
                       help="Name of the database")
    group.add_argument('--db-url',
                       default=os.environ.get('ANYBLOK_DATABASE_URL'),
                       help="Complete URL for connection with the database")
    group.add_argument('--db-driver-name',
                       default=os.environ.get('ANYBLOK_DATABASE_DRIVER'),
                       help="the name of the database backend. This name "
                            "will correspond to a module in "
                            "sqlalchemy/databases or a third party plug-in")
    group.add_argument('--db-user-name',
                       default=os.environ.get('ANYBLOK_DATABASE_USER'),
                       help="The user name")
    group.add_argument('--db-password',
                       default=os.environ.get('ANYBLOK_DATABASE_PASSWORD'),
                       help="database password")
    group.add_argument('--db-host',
                       default=os.environ.get('ANYBLOK_DATABASE_HOST'),
                       help="The name of the host")
    group.add_argument('--db-port', type=int,
                       default=os.environ.get('ANYBLOK_DATABASE_PORT'),
                       help="The port number")
    group.add_argument('--db-echo', action="store_true",
                       default=(os.environ.get(
                           'ANYBLOK_DATABASE_ECHO') or False))
    group.add_argument('--db-echo-pool', action="store_true", default=False)
    group.add_argument('--db-max-overflow', type=int, default=10)
    group.add_argument('--db-pool-size', type=int, default=5)
    group.add_argument('--default-encrypt-key',
                       default=os.environ.get('ANYBLOK_ENCRYPT_KEY'),
                       help=("Default ey definition to encrypt column with "
                             "encryp_key=True"))


@Configuration.add('create_db', must_be_loaded_by_unittest=True)
def add_create_database(group):
    group.add_argument(
        '--db-template-name',
        default=os.environ.get('ANYBLOK_DATABASE_TEMPLATE_NAME'),
        help="Name of the template")


@Configuration.add('install-bloks')
def add_install_bloks(parser):
    parser.add_argument('--install-bloks', nargs="+", help="blok to install")
    parser.add_argument('--install-all-bloks', action='store_true')
    parser.add_argument('--test-blok-at-install', action='store_true')


@Configuration.add('uninstall-bloks')
def add_uninstall_bloks(parser):
    parser.add_argument('--uninstall-bloks', nargs="+",
                        help="bloks to uninstall")


@Configuration.add('install-or-update-bloks')
def add_install_or_update_bloks(parser):
    parser.add_argument('--install-or-update-bloks', nargs="+",
                        help="bloks to install or update")


@Configuration.add('update-bloks', label='Update database')
def add_update_bloks(parser):
    parser.add_argument('--update-bloks', nargs="+", help="bloks to update")
    parser.add_argument('--update-all-bloks', action='store_true')
    parser.add_argument('--reinit-all', action='store_true')
    parser.add_argument('--reinit-tables', action='store_true')
    parser.add_argument('--reinit-columns', action='store_true')
    parser.add_argument('--reinit-indexes', action='store_true')
    parser.add_argument('--reinit-constraints', action='store_true')


@Configuration.add('interpreter')
def add_interpreter(parser):
    parser.add_argument('--script', dest='python_script',
                        help="Python script to execute")


@Configuration.add('schema', label="Schema options")
def add_schema(group):
    try:
        from graphviz.files import FORMATS
    except ImportError:
        from graphviz.backend import FORMATS

    group.add_argument('--schema-format',
                       default='png', choices=tuple(FORMATS))


@Configuration.add('doc', label="Doc options")
def add_doc(group):
    group.add_argument('--doc-format',
                       default='RST', choices=('RST', 'UML', 'SQL'))
    group.add_argument('--doc-output',
                       default='anyblok-documentation')
    group.add_argument('--doc-wanted-models', nargs='+',
                       help='Detail only these models')
    group.add_argument('--doc-unwanted-models', nargs='+',
                       help='No detail these models')


@Configuration.add('unittest', label="Unittest")
def add_unittest(group):
    group.add_argument('--selected-bloks', nargs='+',
                       help="Name of the bloks to test")
    group.add_argument('--unwanted-bloks', nargs='+',
                       help="Name of the bloks to no test")


@Configuration.add('logging', label="Logging")
def add_logging(group):
    group.add_argument('--logging-level', dest='logging_level',
                       choices=['NOTSET', 'DEBUG', 'INFO', 'WARNING',
                                'ERROR', 'CRITICAL'])
    group.add_argument('--logging-level-qualnames', nargs='+',
                       help="Limit the log level on a qualnames list")
    group.add_argument('--logging-config-file', dest='logging_configfile',
                       help="Relative path of the logging config file")
    group.add_argument('--logging-json-config-file',
                       dest='json_logging_configfile',
                       help="Relative path of the logging config file (json). "
                            "Only if the logging config file doesn't filled")
    group.add_argument('--logging-yaml-config-file',
                       dest='yaml_logging_configfile',
                       help="Relative path of the logging config file (yaml). "
                            "Only if the logging and json config file doesn't "
                            "filled")
