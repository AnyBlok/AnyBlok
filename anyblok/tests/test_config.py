# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from os.path import join
from anyblok import config
from anyblok.config import (
    Configuration,
    add_configuration_file,
    add_plugins,
    add_database,
    add_install_bloks,
    add_uninstall_bloks,
    add_update_bloks,
    add_interpreter,
    add_schema,
    add_doc,
    add_logging,
    add_install_or_update_bloks,
    ConfigurationException,
    AnyBlokActionsContainer,
    ConfigOption,
    AnyBlokPlugin,
    define_preload_option,
    get_url,
    get_db_name,
    is_none,
    cast_value,
    nargs_type,
)
from anyblok.testing import tmp_configuration
from sqlalchemy.engine.url import make_url


old_getParser = config.getParser


def fnct_configuration(parser, default):
    default.update({'test': None})


def fnct_other_configuration(parser, default):
    default.update({'test': None})


def MockPluginFnct():
    pass


class MockPluginClass:
    pass


class MockArgParseArguments:

    def __init__(self, configfile=None, args=None, kwargs=None):
        if configfile:
            cfile = join('/'.join(__file__.split('/')[:-1]), configfile)
            self.configfile = cfile
            if kwargs is None:
                kwargs = {}

            kwargs['configfile'] = configfile
        else:
            self.configfile = None
        self.args = args
        self.kwargs = kwargs
        self.logging_level = None
        self.logging_configfile = None
        self.json_logging_configfile = None
        self.yaml_logging_configfile = None

    def _get_args(self):
        return self.args

    def _get_kwargs(self):
        if self.kwargs is None:
            return tuple()
        return self.kwargs.items()


class MockArguments:

    configfile = None
    logging_level = None
    logging_configfile = None
    json_logging_configfile = None
    yaml_logging_configfile = None
    vals = {'var1': 'val1',
            'var2': 'val2',
            'var3': 'val3'}

    def _get_kwargs(self):
        return self.vals.items()

    def _get_args(self):
        return False


class MockArgumentValue:

    def __init__(self, **kwargs):
        self.default = None
        self.type = str
        self.__dict__.update(kwargs)


class MockArgumentParser:

    def __init__(self, *args, **kwargs):
        self.args = MockArguments()

    def add_argument_group(self, *args, **kwargs):
        return MockArgumentParser()

    def parse_args(self, *args, **kwargs):
        return self.args

    def add_argument(self, *args, **kwargs):
        return MockArgumentValue(**kwargs)

    def set_defaults(self, *args, **kwargs):
        pass


@pytest.fixture(scope="class")
def protect_configuration(request):
    def getParser(*args, **kwargs):
        return MockArgumentParser()

    config.getParser = getParser
    old_configuration = Configuration.configuration.copy()
    old_groups = Configuration.groups.copy()
    old_labels = Configuration.labels.copy()

    def reset():
        config.getParser = old_getParser
        Configuration.configuration = old_configuration
        Configuration.groups = old_groups
        Configuration.labels = old_labels

    request.addfinalizer(reset)


class TestConfiguration:

    @pytest.fixture(autouse=True)
    def reset_conf(self, protect_configuration):
        Configuration.groups = {}
        Configuration.labels = {}
        Configuration.configuration = {}

    def assertAdded(self, group, label=None, function_=None):
        assert Configuration.groups[group] == [function_]

        if label:
            assert Configuration.labels[group] == label

    def test_add(self):
        Configuration.add('new-group', function_=fnct_configuration)
        self.assertAdded('new-group', function_=fnct_configuration)

    def test_add_with_label(self):
        Configuration.add(
            'new-group', label="One label", function_=fnct_configuration)
        self.assertAdded(
            'new-group', label="One label", function_=fnct_configuration)

    def test_add_decorator(self):

        @Configuration.add('new-group')
        def fnct(parser, default):
            default.update({'other test': True})

        self.assertAdded('new-group', function_=fnct)

    def test_has(self):
        assert Configuration.has('option') is False
        Configuration.configuration['option'] = ConfigOption('option', str)
        assert Configuration.has('option') is True

    def test_get(self):
        option = 'My option'
        Configuration.configuration['option'] = ConfigOption(option, str)
        res = Configuration.get('option')
        assert option == res

    def test_fnct_plugins_config(self):
        option = 'anyblok.tests.test_config:MockPluginFnct'
        Configuration.configuration['option'] = ConfigOption(
            option, AnyBlokPlugin)
        res = Configuration.get('option')
        assert MockPluginFnct is res

    def test_class_plugins_config(self):
        option = 'anyblok.tests.test_config:MockPluginClass'
        Configuration.configuration['option'] = ConfigOption(
            option, AnyBlokPlugin)
        res = Configuration.get('option')
        assert MockPluginClass is res

    def test_wrong_plugins_config(self):
        option = 'anyblok.tests.test_config:MockPluginWrong'
        with pytest.raises(ImportError):
            Configuration.configuration['option'] = ConfigOption(
                option, AnyBlokPlugin)

    def test_update(self):
        Configuration.update(one_option=1)
        assert Configuration.get('one_option') == 1

    def test_update2(self):
        Configuration.update(dict(one_option=1))
        assert Configuration.get('one_option') == 1

    def test_set_str(self):
        Configuration.set('value', '1')
        assert Configuration.configuration['value'].type == str
        assert Configuration.get('value') == '1'

    def test_set_int(self):
        Configuration.set('value', 1)
        assert Configuration.configuration['value'].type == int
        assert Configuration.get('value') == 1

    def test_set_float(self):
        Configuration.set('value', 1.)
        assert Configuration.configuration['value'].type == float
        assert Configuration.get('value') == 1.

    def test_set_list(self):
        Configuration.set('value', [1])
        assert Configuration.configuration['value'].type == list
        assert Configuration.get('value') == [1]

    def test_set_tuple(self):
        Configuration.set('value', (1,))
        assert Configuration.configuration['value'].type == tuple
        assert Configuration.get('value') == (1,)

    def test_set_dict(self):
        Configuration.set('value', {'a': 1})
        assert Configuration.configuration['value'].type == dict
        assert Configuration.get('value') == {'a': 1}

    def test_get_use_default_value(self):
        option = 'My option by default'
        res = Configuration.get('option', option)
        assert option == res

    def check_url(self, url, wanted_url):
        wanted_url = make_url(wanted_url)
        for x in ('drivername', 'host', 'port', 'username', 'password',
                  'database'):
            assert getattr(url, x) == getattr(wanted_url, x)

    def test_is_none_1(self):
        assert is_none(str, None) is True

    def test_is_none_2(self):
        assert is_none(str, 'None') is True

    def test_is_none_3(self):
        assert is_none(float, '') is True

    def test_is_none_4(self):
        assert is_none(str, '') is False

    def test_cast_value_1(self):
        assert cast_value(str, None) is None

    def test_cast_value_2(self):
        assert cast_value(None, 1) == 1

    def test_cast_value_3(self):
        assert cast_value(bool, 'true') is True

    def test_cast_value_4(self):
        assert cast_value(bool, 'false') is False

    def test_cast_value_5(self):
        assert cast_value(bool, 1) is True

    def test_nargs_type_1(self):
        assert nargs_type('test', 1, str)('test') == ['test']

    def test_nargs_type_2(self):
        assert nargs_type('test', 2, str)('foo\nbar') == ['foo', 'bar']

    def test_nargs_type_3(self):
        assert nargs_type('test', 2, str)('foo,bar') == ['foo', 'bar']

    def test_nargs_type_4(self):
        with pytest.raises(ConfigurationException):
            nargs_type('test', 2, str)(1)

    def test_nargs_type_5(self):
        assert nargs_type('test', 1, str)('foo\nbar') == ['foo']

    def test_nargs_type_6(self):
        assert nargs_type('test', '*', str)('foo\nbar') == ['foo', 'bar']

    def test_set_defaults(self):
        parser = self.get_parser()
        with pytest.raises(KeyError):
            parser.set_defaults(foo='bar')

    def test_AnyBlokPlugin_1(self):
        def foo():
            pass

        assert AnyBlokPlugin(foo) is foo

    def test_update_1(self):
        with pytest.raises(ConfigurationException) as e:
            Configuration.update({}, {})

        assert e.match('Too many args. Only one expected')

    def test_update_2(self):
        with pytest.raises(ConfigurationException) as e:
            Configuration.update(1)

        assert e.match('Wrong args type. Dict expected')

    def test_get_db_name_by_config_name(self):
        with tmp_configuration(db_name='anyblok',
                               db_driver_name='postgres',
                               db_host='localhost',
                               db_user_name=None,
                               db_password=None,
                               db_port=None):
            assert get_db_name() == 'anyblok'

    def test_get_db_name_by_config_url(self):
        with tmp_configuration(db_name=None,
                               db_driver_name=None,
                               db_host=None,
                               db_url='postgres://localhost/anyblok',
                               db_user_name=None,
                               db_password=None,
                               db_port=None):
            assert get_db_name() == 'anyblok'

    def test_get_db_name_ko(self):
        with tmp_configuration(db_name=None,
                               db_driver_name=None,
                               db_host=None,
                               db_user_name=None,
                               db_password=None,
                               db_port=None):
            with pytest.raises(ConfigurationException):
                get_db_name()

    def test_get_url(self):
        with tmp_configuration(db_name='anyblok',
                               db_driver_name='postgres',
                               db_host='localhost',
                               db_user_name=None,
                               db_password=None,
                               db_port=None):
            url = get_url()
            self.check_url(url, 'postgres://localhost/anyblok')

    def test_get_url2(self):
        with tmp_configuration(db_name='anyblok',
                               db_driver_name='postgres',
                               db_host='localhost',
                               db_user_name=None,
                               db_password=None,
                               db_port=None):
            url = get_url(db_name='anyblok2')
            self.check_url(url, 'postgres://localhost/anyblok2')

    def test_get_url3(self):
        with tmp_configuration(db_url='postgres:///anyblok',
                               db_name=None,
                               db_driver_name=None,
                               db_host=None,
                               db_user_name=None,
                               db_password=None,
                               db_port=None):
            url = get_url()
            self.check_url(url, 'postgres:///anyblok')

    def test_get_url4(self):
        with tmp_configuration(db_url='postgres:///anyblok',
                               db_name='anyblok2',
                               db_driver_name=None,
                               db_host=None,
                               db_user_name='jssuzanne',
                               db_password='secret',
                               db_port=None):
            url = get_url()
            self.check_url(url, 'postgres://jssuzanne:secret@/anyblok2')

    def test_get_url5(self):
        with tmp_configuration(db_url='postgres:///anyblok',
                               db_name='anyblok2',
                               db_driver_name=None,
                               db_host=None,
                               db_user_name='jssuzanne',
                               db_password='secret',
                               db_port=None):
            url = get_url(db_name='anyblok3')
            self.check_url(url, 'postgres://jssuzanne:secret@/anyblok3')

    def test_get_url_without_drivername(self):
        with tmp_configuration(db_name=None,
                               db_driver_name=None,
                               db_host=None,
                               db_user_name=None,
                               db_password=None,
                               db_port=None):
            with pytest.raises(ConfigurationException):
                get_url()

    def test_remove(self):
        Configuration.add('new-group', function_=fnct_configuration)
        Configuration.remove('new-group', function_=fnct_configuration)
        assert Configuration.groups['new-group'] == []

    def test_remove_more_function(self):
        Configuration.add('new-group', function_=fnct_configuration)
        Configuration.add('new-group', function_=fnct_other_configuration)
        Configuration.remove('new-group', function_=fnct_configuration)
        assert Configuration.groups['new-group'] == [fnct_other_configuration]

    def test_remove_label(self):
        Configuration.add(
            'new-group', label="One label", function_=fnct_configuration)
        Configuration.remove_label('new-group')
        with pytest.raises(KeyError):
            Configuration.labels['AnyBlok']['new-group']

    def test_load_without_configuration_groupes(self):
        assert Configuration.load('default') is None

    def test_empty_parse_option(self):
        args = MockArgParseArguments()
        Configuration.parse_options(args)
        assert Configuration.configuration == {}

    def assertConfig(self, kwargs):
        config = {x: y.get() for x, y in Configuration.configuration.items()}
        assert config == kwargs

    def test_parse_option(self):
        kwargs = {'test': 'value'}
        args = MockArgParseArguments(configfile="mock_configuration_file.cfg",
                                     kwargs=kwargs)
        Configuration.parse_options(args)
        kwargs.update({
            'db_name': 'anyblok',
            'db_driver_name': 'postgres',
            'db_user_name': '',
            'db_password': '',
            'db_host': 'localhost',
            'db_port': '',
        })
        self.assertConfig(kwargs)

    def test_parse_option_configuration(self):
        args = MockArgParseArguments(configfile="mock_configuration_file.cfg")
        Configuration.parse_options(args)
        self.assertConfig({
            'db_name': 'anyblok',
            'db_driver_name': 'postgres',
            'db_user_name': '',
            'db_password': '',
            'db_host': 'localhost',
            'db_port': '',
            'configfile': 'mock_configuration_file.cfg',
        })

    def test_parse_option_configuration_with_extend(self):
        args = MockArgParseArguments(
            configfile="mockblok/mock_configuration_file.cfg")
        Configuration.parse_options(args)
        self.assertConfig({
            'db_name': 'anyblok',
            'db_driver_name': 'postgres',
            'db_user_name': '',
            'db_password': '',
            'db_host': 'localhost',
            'db_port': '',
            'configfile': 'mockblok/mock_configuration_file.cfg',
        })

    def test_parse_option_kwargs(self):
        kwargs = {'test': 'value'}
        args = MockArgParseArguments(kwargs=kwargs)
        Configuration.parse_options(args)
        self.assertConfig(kwargs)

    def test_parse_option_args(self):
        args = ('test',)
        args = MockArgParseArguments(args=args)
        with pytest.raises(ConfigurationException):
            Configuration.parse_options(args)

    def test_load_with_configuration_groupes(self):
        Configuration.load('default', configuration_groups=['install-bloks'])
        self.assertConfig(MockArguments.vals)

    def test_load_with_bad_configuration_groupes(self):
        Configuration.load('default', configuration_groups=['bad-groups'])
        self.assertConfig(MockArguments.vals)

    def get_parser(self):

        class Parser(AnyBlokActionsContainer, MockArgumentParser):
            pass

        return Parser()

    def test_add_deprecated_argument(self):
        parser = self.get_parser()
        with pytest.warns(DeprecationWarning) as record:
            parser.add_argument(
                '--value', dest='value', deprecated="test deprecated")
            assert str(record.list[0].message) == 'test deprecated'

        with pytest.warns(DeprecationWarning) as record:
            Configuration.get('value')
            assert str(record.list[0].message) == 'test deprecated'

    def test_add_removed_argument_1(self):
        parser = self.get_parser()
        parser.add_argument('--value', dest='value', removed=True)
        with pytest.raises(ConfigurationException):
            Configuration.set('value', 1)

    def test_add_removed_argument_2(self):
        parser = self.get_parser()
        parser.add_argument('--value', dest='value', removed=True)
        with pytest.raises(ConfigurationException):
            Configuration.get('value')

    def test_add_removed_argument_3(self):
        parser = self.get_parser()
        parser.add_argument('--value', dest='value',
                            default=1, removed=True)

    def test_add_argument_str(self):
        parser = self.get_parser()
        parser.add_argument('--value', dest='value', default='1')
        assert Configuration.configuration['value'].type == str
        assert Configuration.get('value') == '1'

    def test_add_argument_int(self):
        parser = self.get_parser()
        parser.add_argument('--value', dest='value', type=int, default=1)
        assert Configuration.configuration['value'].type == int
        assert Configuration.get('value') == 1

    def test_add_argument_float(self):
        parser = self.get_parser()
        parser.add_argument('--value', dest='value', type=float, default=1)
        assert Configuration.configuration['value'].type == float
        assert Configuration.get('value') == 1.

    def test_add_argument_list(self):
        parser = self.get_parser()
        parser.add_argument('--value', dest='value', nargs="+", default='1, 2')
        assert Configuration.get('value') == ['1', '2']

    def test_default_str(self):
        parser = self.get_parser()
        parser.add_argument('--value', dest='value', default='1')
        parser.set_defaults(value='2')
        assert Configuration.get('value') == '2'

    def test_add_application_properties(self):
        assert Configuration.applications.get(
            'test_add_application_properties') is None
        Configuration.add_application_properties(
            'test_add_application_properties', ['logging'],
            description='Just a test')
        assert Configuration.applications.get(
            'test_add_application_properties') is not None
        assert (
            Configuration.applications['test_add_application_properties'] ==
            {
                'configuration_groups': [
                    'config', 'database', 'plugins', 'logging'],
                'description': 'Just a test'
            })

    def test_add_application_properties_and_load_it(self):
        Configuration.add_application_properties(
            'test_add_application_properties', ['logging'])
        parser = MockArgumentParser()

        # add twice to check doublon
        Configuration.add('logging', function_=add_logging, label='Logging')
        Configuration.add('logging', function_=add_logging, label='Logging')

        Configuration.add('database', function_=add_database, label='Database')
        Configuration.add('config', function_=add_configuration_file)
        Configuration.add('install-bloks', function_=add_install_bloks)
        Configuration._load(parser, ['config', 'database', 'logging'])

    def test_initialize_logging(self):
        Configuration.add('logging', function_=add_logging, label='Logging')
        Configuration.set('logging_level', 'DEBUG')
        Configuration.set('logging_level_qualnames', ['test'])
        Configuration.initialize_logging()


@pytest.fixture(scope="function")
def parser():
    return MockArgumentParser()


@pytest.fixture(scope="function")
def group(parser):
    return parser.add_argument_group('label')


class TestConfigurationOption:
    function = {
        'add_configuration_file': add_configuration_file,
        'add_plugins': add_plugins,
        'add_database': add_database,
        'add_install_bloks': add_install_bloks,
        'add_uninstall_bloks': add_uninstall_bloks,
        'add_update_bloks': add_update_bloks,
        'add_interpreter': add_interpreter,
        'add_schema': add_schema,
        'add_doc': add_doc,
        'define_preload_option': define_preload_option,
        'add_logging': add_logging,
        'add_install_or_update_bloks': add_install_or_update_bloks,
    }

    def test_add_configuration_file(self, parser):
        self.function['add_configuration_file'](parser)

    def test_add_plugins(self, group):
        self.function['add_plugins'](group)

    def test_add_database(self, group):
        self.function['add_database'](group)

    def test_add_install_bloks(self, parser):
        self.function['add_install_bloks'](parser)

    def test_add_uninstall_bloks(self, parser):
        self.function['add_uninstall_bloks'](parser)

    def test_add_update_bloks(self, parser):
        self.function['add_update_bloks'](parser)

    def test_add_interpreter(self, parser):
        self.function['add_interpreter'](parser)

    def test_add_schema(self, group):
        self.function['add_schema'](group)

    def test_add_doc(self, group):
        self.function['add_doc'](group)

    def test_define_preload_option(self, parser):
        self.function['define_preload_option'](parser)

    def test_add_logging(self, parser):
        self.function['add_logging'](parser)

    def test_add_install_or_update_bloks(self, parser):
        self.function['add_install_or_update_bloks'](parser)
