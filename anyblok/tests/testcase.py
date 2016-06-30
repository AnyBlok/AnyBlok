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
import os
from anyblok.config import Configuration
from anyblok.registry import RegistryManager
from anyblok.blok import BlokManager
from anyblok.environment import EnvironmentManager
import sqlalchemy
from sqlalchemy import event
from sqlalchemy_utils.functions import database_exists, create_database, orm
from copy import copy
from logging import getLogger

logger = getLogger(__name__)


def drop_database(url):
    url = copy(sqlalchemy.engine.url.make_url(url))
    database = url.database
    if url.drivername.startswith('postgresql'):
        url.database = 'postgres'
    elif not url.drivername.startswith('sqlite'):
        url.database = None

    engine = sqlalchemy.create_engine(url)
    if engine.dialect.name == 'sqlite' and url.database != ':memory:':
        os.remove(url.database)
    else:
        text = 'DROP DATABASE {0}'.format(orm.quote(engine, database))
        cnx = engine.connect()
        cnx.execute("ROLLBACK")
        cnx.execute(text)
        cnx.execute("commit")
        cnx.close()


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
        db_name = Configuration.get('db_name') or 'test_anyblok'
        db_driver_name = Configuration.get('db_driver_name') or 'postgresql'
        env.update({
            'db_name': db_name,
            'db_driver_name': db_driver_name,
        })
        Configuration.update(**env)

    @classmethod
    def createdb(cls, keep_existing=False):
        """Create the database specified in configuration.

        ::

            cls.init_configuration_manager()
            cls.createdb()

        :param keep_existing: If false drop the previous db before create it
        """
        url = Configuration.get('get_url')()
        db_template_name = Configuration.get('db_template_name', None)
        if database_exists(url):
            if keep_existing:
                return False

            drop_database(url)

        create_database(url, template=db_template_name)
        return True

    @classmethod
    def dropdb(cls):
        """Drop the database specified in configuration.

        ::

            cls.init_configuration_manager()
            cls.dropdb()

        """
        url = Configuration.get('get_url')()
        if database_exists(url):
            drop_database(url)

    @classmethod
    def additional_setting(cls):
        return dict(unittest=True)

    @classmethod
    def getRegistry(cls):
        """Return the registry for the test database.

        This assumes the database is created, and the registry has already
        been initialized::

            registry = self.getRegistry()

        :rtype: registry instance
        """
        additional_setting = cls.additional_setting()
        return RegistryManager.get(Configuration.get('db_name'),
                                   **additional_setting)

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

    @classmethod
    def setUpClass(cls):
        """ Intialialise the configuration manager """

        super(DBTestCase, cls).setUpClass()
        cls.init_configuration_manager()
        if cls.createdb(keep_existing=True):
            BlokManager.load(entry_points=('bloks', 'test_bloks'))
            registry = cls.getRegistry()
            registry.commit()
            registry.close()
            BlokManager.unload()

    def setUp(self):
        """ Create a database and load the blok manager """
        self.registry = None
        super(DBTestCase, self).setUp()
        BlokManager.load(entry_points=self.blok_entry_points)

    def tearDown(self):
        """ Clear the registry, unload the blok manager and  drop the database
        """
        if self.registry:
            self.registry.close()

        RegistryManager.clear()
        BlokManager.unload()
        super(DBTestCase, self).tearDown()

    def init_registry(self, function, **kwargs):
        """ call a function to filled the blok manager with new model

        :param function: function to call
        :param kwargs: kwargs for the function
        :rtype: registry instance
        """
        from copy import deepcopy
        loaded_bloks = deepcopy(RegistryManager.loaded_bloks)
        if function is not None:
            EnvironmentManager.set('current_blok', 'anyblok-core')
            try:
                function(**kwargs)
            finally:
                EnvironmentManager.set('current_blok', None)

        try:
            self.registry = registry = self.__class__.getRegistry()
        finally:
            RegistryManager.loaded_bloks = loaded_bloks

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
    def additional_setting(cls):
        return dict(unittest=True)

    @classmethod
    def setUpClass(cls):
        """ Initialize the registry.
        """
        super(BlokTestCase, cls).setUpClass()
        additional_setting = cls.additional_setting()
        if cls.registry is None:
            cls.registry = RegistryManager.get(Configuration.get('db_name'),
                                               **additional_setting)

        cls.registry.commit()

    def setUp(self):
        super(BlokTestCase, self).setUp()
        self.addCleanup(self.callCleanUp)
        self.registry.begin_nested()  # add SAVEPOINT

        @event.listens_for(self.registry.session, "after_transaction_end")
        def restart_savepoint(session, transaction):
            if transaction.nested and not transaction._parent.nested:
                session.expire_all()
                session.begin_nested()

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
            pass
        finally:
            self.registry.rollback()
            self.registry.session.close()

        self._transaction_case_teared_down = True
