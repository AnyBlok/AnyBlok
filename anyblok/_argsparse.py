# -*- coding: utf-8 -*-
from anyblok._logging import init_logger, log
from argparse import ArgumentParser
from configparser import ConfigParser
from anyblok import Declarations


def getParser(description):
    """ Return a parser

    :param description: label of the configuration help
    :rtype: instance of ArgsParseManagerException
    """
    return ArgumentParser(description=description)


@Declarations.target_registry(Declarations.Exception)
class ArgsParseManagerException(Exception):
    """ Simple Exception for ArgsParse """
    pass


class ArgsParseManager:
    """ ArgsParse is use to define the option of argparse and default value

    * groups: list of option by part, a part is a ConfigParser group, or
              a process name

    * labels: if a group has got a label then all the option in group are put
              in parser group

    * configuration: result of the ArgsParser after load

    """

    groups = {}
    labels = {}
    configuration = {}

    @classmethod
    def add(cls, group, part='AnyBlok', label=None, function_=None):
        """ Add a function, each function are added in part and group.

        exemple ::

            def foo(parser, default):
                pass

            ArgsParseManager.add('create-db', function_=foo)

            @ArgsParseManager.add('create-db')
            def bar(parser, defaul):
                pass

        :param part: ConfigParser group or process name
        :param group: group is a set of parser option
        :param label: If the group have a label then all function in group are
            put in group parser
        :param function_: function to add
        """
        if part not in cls.groups:
            cls.groups[part] = {group: []}
        elif group not in cls.groups[part]:
            cls.groups[part][group] = []

        if label:
            if part not in cls.labels:
                cls.labels[part] = {group: label}
            else:
                cls.labels[part][group] = label

        if function_:
            if function_ not in cls.groups[part][group]:
                cls.groups[part][group].append(function_)
        else:

            def wraper(function):
                if function not in cls.groups[part][group]:
                    cls.groups[part][group].append(function)
                return function

            return wraper

    @classmethod
    def get(self, opt, default=None):
        """ get a value in configuration dict after load """
        res = self.configuration.get(opt)
        if res:
            return res
        elif default:
            return default

        return res

    @classmethod
    def remove_label(cls, group, part='AnyBlok'):
        """ remove existing label """
        if part in cls.labels:
            if group in cls.labels[part]:
                del cls.labels[part][group]

    @classmethod
    def remove(cls, group, function_, part='AnyBlok'):
        """ remove existing function """
        if part in cls.groups:
            if group in cls.groups[part]:
                if function_ in cls.groups[part][group]:
                    cls.groups[part][group].remove(function_)

    @classmethod
    def merge_groups(cls, *parts):
        """ Merge groups in function of parts """
        if not parts:
            raise ArgsParseManagerException("No parts to merge")

        groups = {}

        for part in parts:
            if part not in cls.groups:
                continue

            for k, v in cls.groups[part].items():
                if k in groups:
                    groups[k].extend(v)
                else:
                    groups[k] = v

        return groups

    @classmethod
    def merge_labels(cls, *parts):
        """ Merge labels in function of parts """
        if not parts:
            raise ArgsParseManagerException("No parts to merge")

        labels = {}

        for part in parts:
            if part not in cls.labels:
                continue

            for k, v in cls.labels[part].items():
                labels[k] = v

        return labels

    @classmethod
    def get_url(cls, dbname=None):
        """ Return an URL sqlalchemy for database """
        config = cls.configuration
        drivername = username = password = host = port = database = None
        if config.get('dbdrivername'):
            drivername = config['dbdrivername']
        if config.get('dbusername'):
            username = config['dbusername']
        if config.get('dbpassword'):
            password = config['dbpassword']
        if config.get('dbhost'):
            host = config['dbhost']
        if config.get('dbport'):
            port = config['dbport']
        if config.get('dbname'):
            database = config['dbname']

        if drivername is None:
            raise ArgsParseManagerException('No Drivername defined')

        if dbname is not None:
            database = dbname

        from sqlalchemy.engine.url import URL
        return URL(drivername, username=username, password=password, host=host,
                   port=port, database=database)

    @classmethod
    @log()
    def load(cls, description='AnyBlok :', argsparse_groups=None,
             parts_to_load=None):
        parser = getParser(description)

        if argsparse_groups is None:
            return

        if parts_to_load is None:
            parts_to_load = ['AnyBlok']

        groups = cls.merge_groups(*parts_to_load)
        labels = cls.merge_labels(*parts_to_load)

        for group in groups:
            if group not in argsparse_groups:
                continue

            label = labels.get(group)
            if label:
                g = parser.add_argument_group(label)
            else:
                g = parser

            for function in groups[group]:
                function(g, cls.configuration)

        args = parser.parse_args()
        cls.parse_options(args, parts_to_load)

    @classmethod
    def parse_options(cls, arguments, parts_to_load):

        if arguments._get_args():
            raise ArgsParseManagerException(
                'Positionnal arguments is forbiden')

        if arguments.configfile:
            cparser = ConfigParser()
            cparser.read(arguments.configfile)
            for section in parts_to_load:
                if cparser.has_section(section):
                    for opt, value in cparser.items(section):
                        cls.configuration[opt] = value

        for opt, value in arguments._get_kwargs():
            if opt not in cls.configuration or value:
                cls.configuration[opt] = value

    @classmethod
    def init_logger(cls, **kwargs):
        config_var = ['level', 'mode', 'filename', 'socket', 'facility']
        for cv in config_var:
            if cv not in kwargs:
                val = cls.get('logging_' + cv)
                if val is not None:
                    kwargs[cv] = cls.get('logging_' + cv)

        init_logger(**kwargs)


@ArgsParseManager.add('config')
def add_configuration_file(parser, configuration):
    parser.add_argument('-c', dest='configfile', default='',
                        help="Relative path of the config file")
    configuration['configfile'] = None


@ArgsParseManager.add('database', label="Database")
def add_database(group, configuration):
    group.add_argument('--db_name', dest='dbname', default='',
                       help="Name of the data base")
    group.add_argument('--db_drivername', dest='dbdrivername', default='',
                       help="the name of the database backend. This name "
                            "will correspond to a module in "
                            "sqlalchemy/databases or a third party plug-in")
    group.add_argument('--db_username', dest='dbusername', default='',
                       help="The user name")
    group.add_argument('--db_password', dest='dbpassword', default='',
                       help="database password")
    group.add_argument('--db_host', dest='dbhost', default='',
                       help="The name of the host")
    group.add_argument('--db_port', dest='dbport', default='',
                       help="The port number")


@ArgsParseManager.add('install-bloks')
def add_install_bloks(parser, configuration):
    parser.add_argument('--install-bloks', dest='install_bloks', default='',
                        help="blok to install")


@ArgsParseManager.add('uninstall-bloks')
def add_uninstall_bloks(parser, configuration):
    parser.add_argument('--uninstall-bloks', dest='uninstall_bloks',
                        default='', help="blok to uninstall")


@ArgsParseManager.add('update-bloks')
def add_update_bloks(parser, configuration):
    parser.add_argument('--update-bloks', dest='update_bloks', default='',
                        help="blok to update")


@ArgsParseManager.add('interpreter')
def add_interpreter(parser, configuration):
    parser.add_argument('--script', dest='python_script',
                        help="Python script to exec")


@ArgsParseManager.add('logging', label="Logging options")
def add_logging(group, configuration):
    group.add_argument('--logging-level', dest='logging_level',
                       default='info',
                       help='debug, info, warning, error, critical')
    group.add_argument('--logging-mode', dest='logging_mode',
                       default='console',
                       help='console, file, socket, syslog')
    group.add_argument('--logging-filename', dest='logging_filename',
                       help='filename of the log file')
    configuration['logging_filename'] = None
    group.add_argument('--logging-socket', dest='logging_socket',
                       help='(host, port) or UNIX socket interface')
    configuration['logging_socket'] = None
    group.add_argument('--logging-facility', dest='logging_facility',
                       help='Facility for unix socket')
    configuration['logging_facility'] = None
