# -*- coding: utf-8 -*-
import anyblok
from os.path import join
from anyblok._argsparse import ArgsParseManagerException, ArgsParseManager
from anyblok._argsparse import add_configuration_file
from anyblok._argsparse import add_database
from anyblok._argsparse import add_install_bloks
from anyblok._argsparse import add_uninstall_bloks
from anyblok._argsparse import add_update_bloks
from anyblok._argsparse import add_interpreter
from anyblok._argsparse import add_logging
from anyblok.tests.testcase import TestCase
from argparse import ArgumentParser


def fnct_argsparse(parser, default):
    default.update({'test': None})


def fnct_other_argsparse(parser, default):
    default.update({'test': None})


class MockArgParseArguments:

    def __init__(self, configfile=None, args=None, kwargs=None):
        if configfile:
            cfile = join(anyblok.__path__[0], 'tests', configfile)
            self.configfile = cfile
        else:
            self.configfile = None
        self.args = args
        self.kwargs = kwargs

    def _get_args(self):
        return self.args

    def _get_kwargs(self):
        if self.kwargs is None:
            return tuple()
        return self.kwargs.items()


class TestArgsParseManager(TestCase):

    def setUp(self):
        super(TestArgsParseManager, self).setUp()
        ArgsParseManager.groups = {}
        ArgsParseManager.labels = {}
        ArgsParseManager.configuration = {}

    def assertAdded(self, group, part='AnyBlok', label=None, function_=None):
        self.assertEqual(ArgsParseManager.groups[part][group], [function_])

        if label:
            self.assertEqual(ArgsParseManager.labels[part][group], label)

    def test_add(self):
        ArgsParseManager.add('new-group', function_=fnct_argsparse)
        self.assertAdded('new-group', function_=fnct_argsparse)

    def test_add_with_label(self):
        ArgsParseManager.add(
            'new-group', label="One label", function_=fnct_argsparse)
        self.assertAdded(
            'new-group', label="One label", function_=fnct_argsparse)

    def test_add_other_part(self):
        ArgsParseManager.add(
            'new-group', part='other', function_=fnct_argsparse)
        self.assertAdded('new-group', part='other', function_=fnct_argsparse)

    def test_add_other_part_with_label(self):
        ArgsParseManager.add('new-group', part='other', label="One label",
                             function_=fnct_argsparse)
        self.assertAdded('new-group', part='other', label="One label",
                         function_=fnct_argsparse)

    def test_add_decorator(self):

        @ArgsParseManager.add('new-group')
        def fnct(parser, default):
            default.update({'other test': True})

        self.assertAdded('new-group', function_=fnct)

    def test_get(self):
        option = 'My option'
        ArgsParseManager.configuration['option'] = option
        res = ArgsParseManager.get('option')
        self.assertEqual(option, res)

    def test_get_use_default_value(self):
        option = 'My option by default'
        res = ArgsParseManager.get('option', option)
        self.assertEqual(option, res)

    def test_get_url(self):
        ArgsParseManager.configuration.update(dict(
            dbname='anyblok',
            dbdrivername='postgres',
            dbhost='localhost',
            dbusername=None,
            dbpassword=None,
            dbport=None,
        ))
        ArgsParseManager.get_url()

    def test_get_url_without_drivername(self):
        ArgsParseManager.configuration.update(dict(
            dbname=None,
            dbdrivername=None,
            dbhost=None,
            dbusername=None,
            dbpassword=None,
            dbport=None,
        ))
        try:
            ArgsParseManager.get_url()
            self.fail("No watchdog found for no drivername")
        except ArgsParseManagerException:
            pass

    def test_merge_for_one_part(self):
        ArgsParseManager.add('new-group', function_=fnct_argsparse)
        ArgsParseManager.add('new-group', function_=fnct_other_argsparse)
        ArgsParseManager.add('old-group', function_=fnct_argsparse)
        ArgsParseManager.add('old-group', part='other',
                             function_=fnct_argsparse)
        groups = ArgsParseManager.merge_groups('AnyBlok')
        self.assertEqual(groups, {
            'new-group': [fnct_argsparse, fnct_other_argsparse],
            'old-group': [fnct_argsparse]})

    def test_merge_for_more_parts(self):
        ArgsParseManager.add('new-group', function_=fnct_argsparse)
        ArgsParseManager.add('new-group', function_=fnct_other_argsparse)
        ArgsParseManager.add('old-group', function_=fnct_argsparse)
        ArgsParseManager.add('old-group', part='other',
                             function_=fnct_other_argsparse)
        groups = ArgsParseManager.merge_groups('AnyBlok', 'other')
        self.assertEqual(groups, {
            'new-group': [fnct_argsparse, fnct_other_argsparse],
            'old-group': [fnct_argsparse, fnct_other_argsparse]})

    def test_merge_no_parts(self):
        try:
            ArgsParseManager.merge_groups()
            self.fail('No watchdog to merge no part')
        except ArgsParseManagerException:
            pass

    def test_merge_inexisting_part(self):
        ArgsParseManager.merge_groups('other')

    def test_merge_label(self):
        ArgsParseManager.add('new-group', label="Label 1",
                             function_=fnct_other_argsparse)
        ArgsParseManager.add('old-group', label="Label 2", part='other',
                             function_=fnct_argsparse)
        labels = ArgsParseManager.merge_labels('AnyBlok')
        self.assertEqual(labels, {'new-group': "Label 1"})

    def test_merge_label_with_more_parts(self):
        ArgsParseManager.add('new-group', label="Label 1",
                             function_=fnct_other_argsparse)
        ArgsParseManager.add('old-group', label="Label 2", part='other',
                             function_=fnct_argsparse)
        labels = ArgsParseManager.merge_labels('AnyBlok', 'other')
        self.assertEqual(labels, {'new-group': "Label 1",
                                  'old-group': "Label 2"})

    def test_merge_labels_with_no_parts(self):
        try:
            ArgsParseManager.merge_labels()
            self.fail('No watchdog to merge no part')
        except ArgsParseManagerException:
            pass

    def test_merge_labels_inexisting_part(self):
        ArgsParseManager.merge_labels('other')

    def test_remove(self):
        ArgsParseManager.add('new-group', function_=fnct_argsparse)
        ArgsParseManager.remove('new-group', function_=fnct_argsparse)
        self.assertEqual(ArgsParseManager.groups['AnyBlok']['new-group'], [])

    def test_remove_other_part(self):
        ArgsParseManager.add('new-group', part='other',
                             function_=fnct_argsparse)
        ArgsParseManager.remove('new-group', part='other',
                                function_=fnct_argsparse)
        self.assertEqual(ArgsParseManager.groups['other']['new-group'], [])

    def test_remove_more_function(self):
        ArgsParseManager.add('new-group', function_=fnct_argsparse)
        ArgsParseManager.add('new-group', function_=fnct_other_argsparse)
        ArgsParseManager.remove('new-group', function_=fnct_argsparse)
        self.assertEqual(ArgsParseManager.groups['AnyBlok']['new-group'],
                         [fnct_other_argsparse])

    def test_remove_label(self):
        ArgsParseManager.add(
            'new-group', label="One label", function_=fnct_argsparse)
        ArgsParseManager.remove_label('new-group')
        try:
            ArgsParseManager.labels['AnyBlok']['new-group']
            self.fail("Label doesn't remove")
        except:
            pass

    def test_remove_label_other_part(self):
        ArgsParseManager.add('new-group', part='other', label="One label",
                             function_=fnct_argsparse)
        ArgsParseManager.remove_label('new-group', part='other')
        try:
            ArgsParseManager.labels['other']['new-group']
            self.fail("Label doesn't remove")
        except:
            pass

    def test_logging(self):
        ArgsParseManager.configuration.update(dict(
            logging_level='info',
            logging_mode='console',
            logging_filename=None,
            logging_socket=None,
            logging_facility=None,
        ))
        ArgsParseManager.init_logger()

    def test_logging_with_kwargs(self):
        ArgsParseManager.configuration.update(dict(
            logging_level='info',
            logging_mode='file',
            logging_filename=None,
            logging_socket=None,
            logging_facility=None,
        ))
        ArgsParseManager.init_logger(mode='console')

    def test_load(self):
        self.assertEqual(ArgsParseManager.load(), None)

    def test_empty_parse_option(self):
        args = MockArgParseArguments()
        ArgsParseManager.parse_options(args, ['AnyBlok'])
        self.assertEqual(ArgsParseManager.configuration, {})

    def test_parse_option(self):
        kwargs = {'test': 'value'}
        args = MockArgParseArguments(configfile="mock_configuration_file.cfg",
                                     kwargs=kwargs)
        ArgsParseManager.parse_options(args, ['AnyBlok'])
        kwargs.update({
            'dbname': 'anyblok',
            'dbdrivername': 'postgres',
            'dbusername': '',
            'dbpassword': '',
            'dbhost': 'localhost',
            'dbport': '',
            'wsgi_port': '8080',
        })
        self.assertEqual(ArgsParseManager.configuration, kwargs)

    def test_parse_option_configuration(self):
        args = MockArgParseArguments(configfile="mock_configuration_file.cfg")
        ArgsParseManager.parse_options(args, ['AnyBlok'])
        self.assertEqual(ArgsParseManager.configuration, {
            'dbname': 'anyblok',
            'dbdrivername': 'postgres',
            'dbusername': '',
            'dbpassword': '',
            'dbhost': 'localhost',
            'dbport': '',
            'wsgi_port': '8080',
        })

    def test_parse_option_kwargs(self):
        kwargs = {'test': 'value'}
        args = MockArgParseArguments(kwargs=kwargs)
        ArgsParseManager.parse_options(args, ['AnyBlok'])
        self.assertEqual(ArgsParseManager.configuration, kwargs)

    def test_parse_option_args(self):
        args = ('test',)
        args = MockArgParseArguments(args=args)
        try:
            ArgsParseManager.parse_options(args, ['AnyBlok'])
            self.fail("No watchdog for positionnal arguments")
        except ArgsParseManagerException:
            pass


class TestArgsParseOption(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestArgsParseOption, cls).setUpClass()
        cls.parser = ArgumentParser()
        cls.group = cls.parser.add_argument_group('label')
        cls.configuration = {}
        cls.function = {
            'add_configuration_file': add_configuration_file,
            'add_database': add_database,
            'add_install_bloks': add_install_bloks,
            'add_uninstall_bloks': add_uninstall_bloks,
            'add_update_bloks': add_update_bloks,
            'add_interpreter': add_interpreter,
            'add_logging': add_logging,
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

    def test_add_logging(self):
        self.function['add_logging'](self.group, self.configuration)
