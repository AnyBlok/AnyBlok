# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Georges Racinet <gracinet@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.

"""This module's main purpose is to test the tests base classes.

Testing mod_authz itself is not the primary objective, we simply needed a
Blok and a very simple, non structural model, to exert the tests base
classes.
"""
import unittest
from anyblok.tests.testcase import SharedDataTestCase, sgdb_in
from anyblok.tests.testcase import BlokTestCase


class Helper:
    """A mixin to be added to testing test classes.

    The purpose of this mixin is to provide a high-level API to create
    and test registry and database conditions.
    """

    @classmethod
    def break_registry(cls):
        """Voluntarily break the database connection."""
        Blok = cls.registry.System.Blok
        # this is a Programming Error (type is wrong)
        # without proper rollbacking, any test running after that
        # would be in error, too.
        Blok.query().filter(Blok.name == 2).all()

    def assert_pristine_registry(self):
        """Assert that the registry works and has no leftover test data."""
        # always True, but needs the DB and registry to work
        self.assertEqual(
            self.registry.System.Blok.query().filter_by(
                name='no-such-blok').count(),
            0)
        # actual rollback of shared test data
        Grant = self.registry.Authorization.ModelPermissionGrant
        self.assertEqual(Grant.query().count(), 0)


@unittest.skipIf(sgdb_in(['MySQL', 'MariaDB', 'MsSQL']),
                 "ShareDataTestCase doesn't work, issue #96")
class TestSharedDataTestCaseException(unittest.TestCase):
    """Test class with an exception in setUpSharedData.

    We want to ensure that the test is indeed an error, but the
    database connection is not broken.

    In these tests, we use :class:`unittest.TestSuite` to perform the
    various stages of setup (and avoid relying too much on unittest
    internal API). Also :class:`unittest.TestSuite` promises to run the
    tests in the order they were added (we double check that anyway).
    """

    def test_without_error(self):
        """Test normal rollbacks of individual test cases and class."""

        run_order = []

        class SharedData(SharedDataTestCase, Helper):

            @classmethod
            def setUpSharedData(cls):
                cls.Grant = cls.registry.Authorization.ModelPermissionGrant
                cls.grant = cls.Grant.insert(model='abc',
                                             principal='me',
                                             permission='read')

            def test_normal(self):
                """Changes the data, and should be rollbacked in tearDown."""
                run_order.append('normal')
                self.assertEqual(self.grant.principal, 'me')
                self.grant.principal = 'changed'
                self.registry.flush()
                self.assertEqual(
                    self.Grant.query().filter_by(principal='changed').count(),
                    1)

            def test_rollbacked(self):
                """Previous test has been correctly rollbacked."""
                run_order.append('rollbacked')
                self.assertEqual(self.grant.principal, 'me')
                self.assertEqual(
                    self.Grant.query().filter_by(principal='me').count(),
                    1)

        class AfterSharedData(BlokTestCase, Helper):

            def test_class_rollbacked(self):
                run_order.append('class_rollbacked')
                self.assert_pristine_registry()

        result = unittest.TestResult()

        suite = unittest.TestSuite()
        suite.addTest(SharedData('test_normal'))
        suite.addTest(SharedData('test_rollbacked'))
        suite.addTest(AfterSharedData('test_class_rollbacked'))
        suite.run(result)

        self.assertEqual(run_order,
                         ['normal', 'rollbacked', 'class_rollbacked'])
        self.assertEqual(result.testsRun, 3)
        self.assertFalse(result.failures)
        self.assertFalse(result.errors)

    def test_setup_error(self):
        """Test rollback of test case and class with error in setUp"""

        run_order = []

        class SharedData(SharedDataTestCase, Helper):

            @classmethod
            def setUpSharedData(cls):
                cls.Grant = cls.registry.Authorization.ModelPermissionGrant
                cls.grant = cls.Grant.insert(model='abc',
                                             principal='me',
                                             permission='read')

            def setUp(self):
                run_order.append('error')
                super(SharedData, self).setUp()
                self.break_registry()

            def test_error(self):
                """Won't even be executed (error is in setUp)"""

        class AfterSharedData(BlokTestCase, Helper):

            def test_class_rollbacked(self):
                run_order.append('class_rollbacked')
                self.assert_pristine_registry()

        result = unittest.TestResult()

        suite = unittest.TestSuite()
        suite.addTest(SharedData('test_error'))
        suite.addTest(AfterSharedData('test_class_rollbacked'))
        suite.run(result)

        self.assertEqual(run_order, ['error', 'class_rollbacked'])
        self.assertEqual(result.testsRun, 2)

        self.assertEqual(len(result.errors), 1)
        self.assertFalse(result.failures)

    def test_setup_shared_data_error(self):
        """Test recovery of database errors in setUpSharedData"""

        run_order = []

        class BadTest(SharedDataTestCase):

            @classmethod
            def setUpSharedData(cls):
                run_order.append('test_error')
                cls.break_registry()

            def test_error(cls):
                """Won't even be executed (is after error in setUpClass)"""

        class GoodTest(BlokTestCase, Helper):

            def test_ok(self):
                """Test that registry and db connection work normally."""
                run_order.append('test_ok')
                self.assert_pristine_registry()

        result = unittest.TestResult()

        suite = unittest.TestSuite()
        suite.addTest(BadTest('test_error'))
        suite.addTest(GoodTest('test_ok'))
        suite.run(result)

        self.assertEqual(run_order, ['test_error', 'test_ok'])
        # only test_ok could actually be run
        self.assertEqual(result.testsRun, 1)
        # but it succeeded
        self.assertEqual(len(result.errors), 1)
        self.assertFalse(result.failures)
