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
                            add_database,
                            add_install_bloks,
                            add_uninstall_bloks,
                            add_update_bloks,
                            add_interpreter,
                            add_schema,
                            add_doc,
                            add_unittest,
                            ConfigurationException)
from anyblok.tests.testcase import TestCase


old_getParser = config.getParser


def fnct_configuration(parser, default):
    default.update({'test': None})


def fnct_other_configuration(parser, default):
    default.update({'test': None})


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


class MockArgumentParser:

    def __init__(self, *args, **kwargs):
        self.args = MockArguments()

    def add_argument_group(self, *args, **kwargs):
        return MockArgumentParser()

    def parse_args(self, *args, **kwargs):
        return self.args

    def add_argument(self, *args, **kwargs):
        pass

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

    def test_get(self):
        option = 'My option'
        Configuration.configuration['option'] = option
        res = Configuration.get('option')
        self.assertEqual(option, res)

    def test_get_use_default_value(self):
        option = 'My option by default'
        res = Configuration.get('option', option)
        self.assertEqual(option, res)

    def test_get_url(self):
        Configuration.configuration.update(dict(
            db_name='anyblok',
            db_driver_name='postgres',
            db_host='localhost',
            db_user_name=None,
            db_password=None,
            db_port=None,
        ))
        Configuration.get_url()

    def test_get_url_without_drivername(self):
        Configuration.configuration.update(dict(
            db_name=None,
            db_driver_name=None,
            db_host=None,
            db_user_name=None,
            db_password=None,
            db_port=None,
        ))
        try:
            Configuration.get_url()
            self.fail("No watchdog found for no drivername")
        except ConfigurationException:
            pass

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
        try:
            Configuration._merge_groups()
            self.fail('No watchdog to merge no part')
        except ConfigurationException:
            pass

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
        try:
            Configuration._merge_labels()
            self.fail('No watchdog to merge no part')
        except ConfigurationException:
            pass

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
        try:
            Configuration.labels['AnyBlok']['new-group']
            self.fail("Label doesn't remove")
        except:
            pass

    def test_remove_label_other_part(self):
        Configuration.add('new-group', part='other', label="One label",
                          function_=fnct_configuration)
        Configuration.remove_label('new-group', part='other')
        try:
            Configuration.labels['other']['new-group']
            self.fail("Label doesn't remove")
        except:
            pass

    def test_load_without_configuration_groupes(self):
        self.assertEqual(Configuration.load(), None)

    def test_empty_parse_option(self):
        args = MockArgParseArguments()
        Configuration.parse_options(args, ['AnyBlok'])
        self.assertEqual(Configuration.configuration, {})

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
        self.assertEqual(Configuration.configuration, kwargs)

    def test_parse_option_configuration(self):
        args = MockArgParseArguments(configfile="mock_configuration_file.cfg")
        Configuration.parse_options(args, ())
        self.assertEqual(Configuration.configuration, {
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
        self.assertEqual(Configuration.configuration, {
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
        self.assertEqual(Configuration.configuration, kwargs)

    def test_parse_option_args(self):
        args = ('test',)
        args = MockArgParseArguments(args=args)
        try:
            Configuration.parse_options(args, ['AnyBlok'])
            self.fail("No watchdog for positionnal arguments")
        except ConfigurationException:
            pass

    def test_load_with_configuration_groupes(self):
        Configuration.load(configuration_groups=['install-bloks'])
        self.assertEqual(Configuration.configuration, MockArguments.vals)

    def test_load_with_bad_configuration_groupes(self):
        Configuration.load(configuration_groups=['bad-groups'])
        self.assertEqual(Configuration.configuration, MockArguments.vals)


class TestConfigurationOption(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestConfigurationOption, cls).setUpClass()
        cls.parser = MockArgumentParser()
        cls.group = cls.parser.add_argument_group('label')
        cls.configuration = {}
        cls.function = {
            'add_configuration_file': add_configuration_file,
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
        self.function['add_configuration_file'](self.parser,
                                                self.configuration)

    def test_add_database(self):
        self.function['add_database'](self.group, self.configuration)

    def test_add_install_bloks(self):
        self.function['add_install_bloks'](self.parser, self.configuration)

    def test_add_uninstall_bloks(self):
        self.function['add_uninstall_bloks'](self.parser, self.configuration)

    def test_add_update_bloks(self):
        self.function['add_update_bloks'](self.parser, self.configuration)

    def test_add_interpreter(self):
        self.function['add_interpreter'](self.parser, self.configuration)

    def test_add_schema(self):
        self.function['add_schema'](self.group, self.configuration)

    def test_add_doc(self):
        self.function['add_doc'](self.group, self.configuration)

    def test_add_unittest(self):
        self.function['add_unittest'](self.group, self.configuration)
