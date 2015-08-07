# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
"""Base classes for unit/integration tests with anyblok.

This module provides :class:`BlokTestCase`, which is the main one meant for
blok tests, and :class:`DBTestCase`, whose primary purpose is to test anyblok
itself, in so-called "framework tests".
"""

import unittest
from logging import getLogger
from anyblok.config import Configuration
from anyblok.registry import RegistryManager
from anyblok.blok import BlokManager
from anyblok.environment import EnvironmentManager
import anyblok
import sqlalchemy

logger = getLogger(__name__)


class TestCase(unittest.TestCase):
    """Common helpers, not meant to be used directly."""

    _transaction_case_teared_down = False

    @classmethod
    def init_configuration_manager(cls, **env):
        """ Initialise the configuration manager with environ variable
        to launch the test

        .. warning::

            For the moment we not use the environ variable juste constante

        :param prefix: prefix the database name
        :param env: add another dict to merge with environ variable
        """
        db_name = Configuration.get('db_name', 'test_anyblok')
        db_driver_name = Configuration.get('db_driver_name', 'postgres')
        env.update({
            'db_name': db_name,
            'db_driver_name': db_driver_name,
        })
        Configuration.configuration.update(env)

    @classmethod
    def createdb(cls, keep_existing=False):
        """Create the database specified in configuration.

        ::

            cls.init_configuration_manager()
            cls.createdb()

        :param keep_existing: If false drop the previous db before create it
        """
        bdd = anyblok.BDD[Configuration.get('db_driver_name')]
        db_name = Configuration.get('db_name')
        if db_name in bdd.listdb():
            if keep_existing:
                return True

            bdd.dropdb(db_name)

        bdd.createdb(db_name)

    @classmethod
    def dropdb(cls):
        """Drop the database specified in configuration.

        ::

            cls.init_configuration_manager()
            cls.dropdb()

        """
        bdd = anyblok.BDD[Configuration.get('db_driver_name')]
        bdd.dropdb(Configuration.get('db_name'))

    def getRegistry(self):
        """Return the registry for the test database.

        This assumes the database is created, and the registry has already
        been initialized::

            registry = self.getRegistry()

        :rtype: registry instance
        """
        return RegistryManager.get(Configuration.get('db_name'))

    def setUp(self):
        super(TestCase, self).setUp()
        self.addCleanup(self.callCleanUp)

    def callCleanUp(self):
        if not self._transaction_case_teared_down:
            self.cleanUp()

    def cleanUp(self):
        self.tearDown()

    def tearDown(self):
        """ Roll back the session """
        super(TestCase, self).tearDown()
        self._transaction_case_teared_down = True


class DBTestCase(TestCase):
    """Base class for tests that need to work on an empty database.

    .. warning::

        The database is created and dropped with each unit test

    For instance, this is the one used for Field, Column, RelationShip, and
    more generally core framework tests.

    The drawback of using this base class is that tests will be slow. The
    advantage is ultimate test isolation.

    Sample usage::

        from anyblok.tests.testcase import DBTestCase


        def simple_column(ColumnType=None, **kwargs):

            @Declarations.register(Declarations.Model)
            class Test:

                id = Declarations.Column.Integer(primary_key=True)
                col = ColumnType(**kwargs)


        class TestColumns(DBTestCase):

            def test_integer(self):
                Integer = Declarations.Column.Integer

                registry = self.init_registry(simple_column,
                                              ColumnType=Integer)
                test = registry.Test.insert(col=1)
                self.assertEqual(test.col, 1)

    """

    blok_entry_points = ('bloks',)
    """setuptools entry points to load blok """

    current_blok = 'anyblok-core'
    """In the blok to add the new model """

    @classmethod
    def setUpClass(cls):
        """ Intialialise the configuration manager """
        super(DBTestCase, cls).setUpClass()
        cls.init_configuration_manager()

    def setUp(self):
        """ Create a database and load the blok manager """
        super(DBTestCase, self).setUp()
        self.createdb()
        BlokManager.load(entry_points=self.blok_entry_points)

    def tearDown(self):
        """ Clear the registry, unload the blok manager and  drop the database
        """
        RegistryManager.clear()
        BlokManager.unload()
        self.dropdb()
        super(DBTestCase, self).tearDown()

    def upgrade(self, registry, **kwargs):
        """ Upgrade the registry::

            class MyTest(DBTestCase):

                def test_mytest(self):
                    registry = self.init_registry(...)
                    self.upgrade(registry, install=('MyBlok',))

        :param registry: registry to upgrade
        :param install: list the blok to install
        :param update: list the blok to update
        :param uninstall: list the blok to uninstall
        """
        session_commit = registry.session_commit
        registry.session_commit = registry.old_session_commit
        registry.upgrade(**kwargs)
        registry.session_commit = session_commit

    def init_registry(self, function, **kwargs):
        """ call a function to filled the blok manager with new model

        :param function: function to call
        :param kwargs: kwargs for the function
        :rtype: registry instance
        """
        from copy import deepcopy
        loaded_bloks = deepcopy(RegistryManager.loaded_bloks)
        if function is not None:
            EnvironmentManager.set('current_blok', self.current_blok)
            try:
                function(**kwargs)
            finally:
                EnvironmentManager.set('current_blok', None)

        try:
            registry = self.getRegistry()
        finally:
            RegistryManager.loaded_bloks = loaded_bloks

        def session_commit(*args, **kwargs):
            pass

        registry.old_session_commit = registry.session_commit
        registry.session_commit = session_commit

        return registry


class BlokTestCase(unittest.TestCase):
    """Base class for tests meant to run on a preinstalled database.

    The tests written with this class don't need to start afresh on a new
    database, and therefore run much faster than those inheriting
    :class:`DBTestCase`. Instead, they expect the tested bloks to be already
    installed and up to date.

    The session gets rollbacked after each test.

    Such tests are appropriate for a typical blok developper workflow:

    * create and install the bloks once
    * run the tests of the blok under development repeatedly
    * upgrade the bloks in database when needed (schema change, update of
      dependencies)

    They are also appropriate for on the fly testing while installing the
    bloks: the tests of each blok get run on the database state they expect,
    before dependent (downstream) bloks, that could. e.g., alter the database
    schema, get themselves installed.
    This is useful to test a whole stack at once using only one
    database (typically in CI bots).

    Sample usage::

        from anyblok.tests.testcase import BlokTestCase


        class MyBlokTest(BlokTestCase):

            def test_1(self):
                # access to the registry by ``self.registry``
                ...

    """

    _transaction_case_teared_down = False
    registry = None
    """The instance of :class:`anyblok.registry.Registry`` to use in tests.

    The ``session_commit()`` method is disabled to avoid side effects from one
    test to the other.
    """

    @classmethod
    def setUpClass(cls):
        """ Initialize the registry.
        """
        super(BlokTestCase, cls).setUpClass()
        if cls.registry is None:
            cls.registry = RegistryManager.get(Configuration.get('db_name'))

        def session_commit(*args, **kwargs):
            pass

        cls.old_session_commit = cls.registry.session_commit
        cls.registry.session_commit = session_commit

    @classmethod
    def tearDownClass(cls):
        super(BlokTestCase, cls).tearDownClass()
        cls.registry.session_commit = cls.old_session_commit

    def setUp(self):
        super(BlokTestCase, self).setUp()
        self.addCleanup(self.callCleanUp)
        self.registry.begin_nested()  # add SAVEPOINT

    def callCleanUp(self):
        if not self._transaction_case_teared_down:
            self.cleanUp()

    def cleanUp(self):
        self.tearDown()

    def tearDown(self):
        """ Roll back the session """
        super(BlokTestCase, self).tearDown()
        try:
            self.registry.System.Cache.invalidate_all()
        except sqlalchemy.exc.InvalidRequestError:
            self.registry.Session.rollback()
        finally:
            self.registry.rollback()

        self._transaction_case_teared_down = True
