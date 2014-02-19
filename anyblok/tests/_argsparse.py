# -*- coding: utf-8 -*-
import unittest
from anyblok._argsparse import ArgsParseManagerException, ArgsParseManager


def fnct_argsparse(parser, default):
    default.update({'test': None})


def fnct_other_argsparse(parser, default):
    default.update({'test': None})


class TestArgsParseManager(unittest.TestCase):

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
            dbhost='localhost'))
        ArgsParseManager.get_url()

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
