# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from os.path import join
from anyblok import config
from anyblok.config import (Configuration,
                            add_configuration_file,
                            add_plugins,
                            add_database,
                            add_install_bloks,
                            add_uninstall_bloks,
                            add_update_bloks,
                            add_interpreter,
                            add_schema,
                            add_doc,
                            add_unittest,
                            ConfigurationException,
                            AnyBlokActionsContainer,
                            ConfigOption,
                            AnyBlokPlugin)
from anyblok.tests.testcase import TestCase
from sqlalchemy.engine.url import make_url
from anyblok.config import get_url


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


class TestConfiguration(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestConfiguration, cls).setUpClass()

        def getParser(*args, **kwargs):
            return MockArgumentParser()

        config.getParser = getParser
        cls.old_configuration = Configuration.configuration.copy()
        cls.old_groups = Configuration.groups.copy()
        cls.old_labels = Configuration.labels.copy()

    @classmethod
    def tearDownClass(cls):
        super(TestConfiguration, cls).tearDownClass()
        config.getParser = old_getParser
        Configuration.configuration = cls.old_configuration
        Configuration.groups = cls.old_groups
        Configuration.labels = cls.old_labels

    def setUp(self):
        super(TestConfiguration, self).setUp()
        Configuration.groups = {}
        Configuration.labels = {}
        Configuration.configuration = {}

    def assertAdded(self, group, part='bloks', label=None, function_=None):
        self.assertEqual(Configuration.groups[part][group], [function_])

        if label:
            self.assertEqual(Configuration.labels[part][group], label)

    def test_add(self):
        Configuration.add('new-group', function_=fnct_configuration)
        self.assertAdded('new-group', function_=fnct_configuration)

    def test_add_with_label(self):
        Configuration.add(
            'new-group', label="One label", function_=fnct_configuration)
        self.assertAdded(
            'new-group', label="One label", function_=fnct_configuration)

    def test_add_other_part(self):
        Configuration.add(
            'new-group', part='other', function_=fnct_configuration)
        self.assertAdded('new-group', part='other',
                         function_=fnct_configuration)

    def test_add_other_part_with_label(self):
        Configuration.add('new-group', part='other', label="One label",
                          function_=fnct_configuration)
        self.assertAdded('new-group', part='other', label="One label",
                         function_=fnct_configuration)

    def test_add_decorator(self):

        @Configuration.add('new-group')
        def fnct(parser, default):
            default.update({'other test': True})

        self.assertAdded('new-group', function_=fnct)

    def test_has(self):
        self.assertFalse(Configuration.has('option'))
        Configuration.configuration['option'] = ConfigOption('option', str)
        self.assertTrue(Configuration.has('option'))

    def test_get(self):
        option = 'My option'
        Configuration.configuration['option'] = ConfigOption(option, str)
        res = Configuration.get('option')
        self.assertEqual(option, res)

    def test_fnct_plugins_config(self):
        option = 'anyblok.tests.test_config:MockPluginFnct'
        Configuration.configuration['option'] = ConfigOption(
            option, AnyBlokPlugin)
        res = Configuration.get('option')
        self.assertIs(MockPluginFnct, res)

    def test_class_plugins_config(self):
        option = 'anyblok.tests.test_config:MockPluginClass'
        Configuration.configuration['option'] = ConfigOption(
            option, AnyBlokPlugin)
        res = Configuration.get('option')
        self.assertIs(MockPluginClass, res)

    def test_wrong_plugins_config(self):
        option = 'anyblok.tests.test_config:MockPluginWrong'
        with self.assertRaises(ImportError):
            Configuration.configuration['option'] = ConfigOption(
                option, AnyBlokPlugin)

    def test_update(self):
        Configuration.update(one_option=1)
        self.assertEqual(Configuration.get('one_option'), 1)

    def test_update2(self):
        Configuration.update(dict(one_option=1))
        self.assertEqual(Configuration.get('one_option'), 1)

    def test_set_str(self):
        Configuration.set('value', '1')
        self.assertEqual(Configuration.configuration['value'].type, str)
        self.assertEqual(Configuration.get('value'), '1')

    def test_set_int(self):
        Configuration.set('value', 1)
        self.assertEqual(Configuration.configuration['value'].type, int)
        self.assertEqual(Configuration.get('value'), 1)

    def test_set_float(self):
        Configuration.set('value', 1.)
        self.assertEqual(Configuration.configuration['value'].type, float)
        self.assertEqual(Configuration.get('value'), 1.)

    def test_set_list(self):
        Configuration.set('value', [1])
        self.assertEqual(Configuration.configuration['value'].type, list)
        self.assertEqual(Configuration.get('value'), [1])

    def test_set_tuple(self):
        Configuration.set('value', (1,))
        self.assertEqual(Configuration.configuration['value'].type, tuple)
        self.assertEqual(Configuration.get('value'), (1,))

    def test_set_dict(self):
        Configuration.set('value', {'a': 1})
        self.assertEqual(Configuration.configuration['value'].type, dict)
        self.assertEqual(Configuration.get('value'), {'a': 1})

    def test_get_use_default_value(self):
        option = 'My option by default'
        res = Configuration.get('option', option)
        self.assertEqual(option, res)

    def check_url(self, url, wanted_url):
        wanted_url = make_url(wanted_url)
        for x in ('drivername', 'host', 'port', 'username', 'password',
                  'database'):
            self.assertEqual(
                getattr(url, x), getattr(wanted_url, x),
                "check url(%s) == url(%s) on attribute %r" % (url, wanted_url,
                                                              x))

    def test_get_url(self):
        with TestCase.Configuration(db_name='anyblok',
                                    db_driver_name='postgres',
                                    db_host='localhost',
                                    db_user_name=None,
                                    db_password=None,
                                    db_port=None):
            url = get_url()
            self.check_url(url, 'postgres://localhost/anyblok')

    def test_get_url2(self):
        with TestCase.Configuration(db_name='anyblok',
                                    db_driver_name='postgres',
                                    db_host='localhost',
                                    db_user_name=None,
                                    db_password=None,
                                    db_port=None):
            url = get_url(db_name='anyblok2')
            self.check_url(url, 'postgres://localhost/anyblok2')

    def test_get_url3(self):
        with TestCase.Configuration(db_url='postgres:///anyblok',
                                    db_name=None,
                                    db_driver_name=None,
                                    db_host=None,
                                    db_user_name=None,
                                    db_password=None,
                                    db_port=None):
            url = get_url()
            self.check_url(url, 'postgres:///anyblok')

    def test_get_url4(self):
        with TestCase.Configuration(db_url='postgres:///anyblok',
                                    db_name='anyblok2',
                                    db_driver_name=None,
                                    db_host=None,
                                    db_user_name='jssuzanne',
                                    db_password='secret',
                                    db_port=None):
            url = get_url()
            self.check_url(url, 'postgres://jssuzanne:secret@/anyblok2')

    def test_get_url5(self):
        with TestCase.Configuration(db_url='postgres:///anyblok',
                                    db_name='anyblok2',
                                    db_driver_name=None,
                                    db_host=None,
                                    db_user_name='jssuzanne',
                                    db_password='secret',
                                    db_port=None):
            url = get_url(db_name='anyblok3')
            self.check_url(url, 'postgres://jssuzanne:secret@/anyblok3')

    def test_get_url_without_drivername(self):
        with TestCase.Configuration(db_name=None,
                                    db_driver_name=None,
                                    db_host=None,
                                    db_user_name=None,
                                    db_password=None,
                                    db_port=None):
            with self.assertRaises(ConfigurationException):
                get_url()

    def test_merge_for_one_part(self):
        Configuration.add('new-group', function_=fnct_configuration)
        Configuration.add('new-group', function_=fnct_other_configuration)
        Configuration.add('old-group', function_=fnct_configuration)
        Configuration.add('old-group', part='other',
                          function_=fnct_configuration)
        groups = Configuration._merge_groups('bloks')
        self.assertEqual(groups, {
            'new-group': [fnct_configuration, fnct_other_configuration],
            'old-group': [fnct_configuration]})

    def test_merge_for_more_parts(self):
        Configuration.add('new-group', function_=fnct_configuration)
        Configuration.add('new-group', function_=fnct_other_configuration)
        Configuration.add('old-group', function_=fnct_configuration)
        Configuration.add('old-group', part='other',
                          function_=fnct_other_configuration)
        groups = Configuration._merge_groups('bloks', 'other')
        self.assertEqual(groups, {
            'new-group': [fnct_configuration, fnct_other_configuration],
            'old-group': [fnct_configuration, fnct_other_configuration]})

    def test_merge_no_parts(self):
        with self.assertRaises(ConfigurationException):
            Configuration._merge_groups()

    def test_merge_inexisting_part(self):
        Configuration._merge_groups('other')

    def test_merge_label(self):
        Configuration.add('new-group', label="Label 1",
                          function_=fnct_other_configuration)
        Configuration.add('old-group', label="Label 2", part='other',
                          function_=fnct_configuration)
        labels = Configuration._merge_labels('bloks')
        self.assertEqual(labels, {'new-group': "Label 1"})

    def test_merge_label_with_more_parts(self):
        Configuration.add('new-group', label="Label 1",
                          function_=fnct_other_configuration)
        Configuration.add('old-group', label="Label 2", part='other',
                          function_=fnct_configuration)
        labels = Configuration._merge_labels('bloks', 'other')
        self.assertEqual(labels, {'new-group': "Label 1",
                                  'old-group': "Label 2"})

    def test_merge_labels_with_no_parts(self):
        with self.assertRaises(ConfigurationException):
            Configuration._merge_labels()

    def test_merge_labels_inexisting_part(self):
        Configuration._merge_labels('other')

    def test_remove(self):
        Configuration.add('new-group', function_=fnct_configuration)
        Configuration.remove('new-group', function_=fnct_configuration)
        self.assertEqual(Configuration.groups['bloks']['new-group'], [])

    def test_remove_other_part(self):
        Configuration.add('new-group', part='other',
                          function_=fnct_configuration)
        Configuration.remove('new-group', part='other',
                             function_=fnct_configuration)
        self.assertEqual(Configuration.groups['other']['new-group'], [])

    def test_remove_more_function(self):
        Configuration.add('new-group', function_=fnct_configuration)
        Configuration.add('new-group', function_=fnct_other_configuration)
        Configuration.remove('new-group', function_=fnct_configuration)
        self.assertEqual(Configuration.groups['bloks']['new-group'],
                         [fnct_other_configuration])

    def test_remove_label(self):
        Configuration.add(
            'new-group', label="One label", function_=fnct_configuration)
        Configuration.remove_label('new-group')
        with self.assertRaises(KeyError):
            Configuration.labels['AnyBlok']['new-group']

    def test_remove_label_other_part(self):
        Configuration.add('new-group', part='other', label="One label",
                          function_=fnct_configuration)
        Configuration.remove_label('new-group', part='other')
        with self.assertRaises(KeyError):
            Configuration.labels['other']['new-group']

    def test_load_without_configuration_groupes(self):
        self.assertEqual(Configuration.load('default'), None)

    def test_empty_parse_option(self):
        args = MockArgParseArguments()
        Configuration.parse_options(args, ['AnyBlok'])
        self.assertEqual(Configuration.configuration, {})

    def assertConfig(self, kwargs):
        config = {x: y.get() for x, y in Configuration.configuration.items()}
        self.assertEqual(config, kwargs)

    def test_parse_option(self):
        kwargs = {'test': 'value'}
        args = MockArgParseArguments(configfile="mock_configuration_file.cfg",
                                     kwargs=kwargs)
        Configuration.parse_options(args, ())
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
        Configuration.parse_options(args, ())
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
        Configuration.parse_options(args, ())
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
        Configuration.parse_options(args, ['AnyBlok'])
        self.assertConfig(kwargs)

    def test_parse_option_args(self):
        args = ('test',)
        args = MockArgParseArguments(args=args)
        with self.assertRaises(ConfigurationException):
            Configuration.parse_options(args, ['AnyBlok'])

    def test_load_with_configuration_groupes(self):
        Configuration.load('default', configuration_groups=['install-bloks'])
        self.assertConfig(MockArguments.vals)

    def test_load_with_bad_configuration_groupes(self):
        Configuration.load('default', configuration_groups=['bad-groups'])
        self.assertConfig(MockArguments.vals)

    def get_parer(self):

        class Parser(AnyBlokActionsContainer, MockArgumentParser):
            pass

        return Parser()

    def test_add_argument_str(self):
        parser = self.get_parer()
        parser.add_argument('--value', dest='value', default='1')
        self.assertEqual(Configuration.configuration['value'].type, str)
        self.assertEqual(Configuration.get('value'), '1')

    def test_add_argument_int(self):
        parser = self.get_parer()
        parser.add_argument('--value', dest='value', type=int, default=1)
        self.assertEqual(Configuration.configuration['value'].type, int)
        self.assertEqual(Configuration.get('value'), 1)

    def test_add_argument_float(self):
        parser = self.get_parer()
        parser.add_argument('--value', dest='value', type=float, default=1)
        self.assertEqual(Configuration.configuration['value'].type, float)
        self.assertEqual(Configuration.get('value'), 1.)

    def test_add_argument_list(self):
        parser = self.get_parer()
        parser.add_argument('--value', dest='value', nargs="+", default='1, 2')
        self.assertEqual(Configuration.get('value'), ['1', '2'])

    def test_default_str(self):
        parser = self.get_parer()
        parser.add_argument('--value', dest='value', default='1')
        parser.set_defaults(value='2')
        self.assertEqual(Configuration.get('value'), '2')


class TestConfigurationOption(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestConfigurationOption, cls).setUpClass()
        cls.parser = MockArgumentParser()
        cls.group = cls.parser.add_argument_group('label')
        cls.function = {
            'add_configuration_file': add_configuration_file,
            'add_plugins': add_plugins,
            'add_database': add_database,
            'add_install_bloks': add_install_bloks,
            'add_uninstall_bloks': add_uninstall_bloks,
            'add_update_bloks': add_update_bloks,
            'add_interpreter': add_interpreter,
            'add_schema': add_schema,
            'add_doc': add_doc,
            'add_unittest': add_unittest,
        }

    def test_add_configuration_file(self):
        self.function['add_configuration_file'](self.parser)

    def test_add_plugins(self):
        self.function['add_plugins'](self.group)

    def test_add_database(self):
        self.function['add_database'](self.group)

    def test_add_install_bloks(self):
        self.function['add_install_bloks'](self.parser)

    def test_add_uninstall_bloks(self):
        self.function['add_uninstall_bloks'](self.parser)

    def test_add_update_bloks(self):
        self.function['add_update_bloks'](self.parser)

    def test_add_interpreter(self):
        self.function['add_interpreter'](self.parser)

    def test_add_schema(self):
        self.function['add_schema'](self.group)

    def test_add_doc(self):
        self.function['add_doc'](self.group)

    def test_add_unittest(self):
        self.function['add_unittest'](self.group)
