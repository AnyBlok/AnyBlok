# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import BlokTestCase
from ..exceptions import ParameterException


class TestSystemParameter(BlokTestCase):

    def test_set(self):
        Parameter = self.registry.System.Parameter
        query = Parameter.query().filter(Parameter.key == 'test.parameter')
        if query.count():
            self.fail('key for test already existing')

        Parameter.set('test.parameter', True)
        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().value, {'value': True})
        self.assertEqual(query.first().multi, False)

    def test_set_with_multi(self):
        Parameter = self.registry.System.Parameter
        query = Parameter.query().filter(Parameter.key == 'test.parameter')
        if query.count():
            self.fail('key for test already existing')

        Parameter.set('test.parameter', {'test': True})
        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().value, {'test': True})
        self.assertEqual(query.first().multi, True)

    def test_get(self):
        Parameter = self.registry.System.Parameter
        Parameter.set('test.parameter', True)
        self.assertEqual(Parameter.get('test.parameter'), True)

    def test_get_with_multi(self):
        Parameter = self.registry.System.Parameter
        Parameter.set('test.parameter', {'test': True})
        self.assertEqual(Parameter.get('test.parameter'), {'test': True})

    def test_unexisting_get(self):
        Parameter = self.registry.System.Parameter
        with self.assertRaises(ParameterException):
            Parameter.get('test.parameter')

    def test_count(self):
        Parameter = self.registry.System.Parameter
        self.assertEqual(Parameter.is_exist('test.parameter'), False)
        Parameter.set('test.parameter', True)
        self.assertEqual(Parameter.is_exist('test.parameter'), True)

    def test_set_existing_key(self):
        Parameter = self.registry.System.Parameter
        query = Parameter.query().filter(Parameter.key == 'test.parameter')
        self.assertEqual(query.count(), 0)
        Parameter.set('test.parameter', True)
        self.assertEqual(query.count(), 1)
        self.assertEqual(Parameter.get('test.parameter'), True)
        Parameter.set('test.parameter', False)
        self.assertEqual(query.count(), 1)
        self.assertEqual(Parameter.get('test.parameter'), False)
