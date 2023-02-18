# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Georges RACINET <gracinet@anybox.fr>
#    Copyright (C) 2019 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
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
from sqlalchemy.orm import clear_mappers
from sqlalchemy import event
from sqlalchemy_utils.functions import database_exists, create_database, orm
from copy import copy
from testfixtures import LogCapture as LC
from contextlib import contextmanager
from logging import getLogger, DEBUG, INFO, WARNING, ERROR, CRITICAL
from .common import sgdb_in as sgdb_in_, DATABASES_CACHED
from anyblok import (
    load_init_function_from_entry_points,
    configuration_post_load,
)

logger = getLogger(__name__)


class MockParser:

    def _get_kwargs(self):
        return []

    def _get_args(self):
        return False


def load_configuration():
    load_init_function_from_entry_points(unittest=True)
    Configuration.load_config_for_test()
    Configuration.parse_options(MockParser())
    configuration_post_load(unittest=True)


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


@contextmanager
def tmp_configuration(**values):
    """Add Configuration value only in the contextmanager
    ::

        with TestCase.Configuration(db_name='a db name'):
            assert Configuration.get('db_name') == 'a db name'

    :param **values: values to update
    """
    old_values = {
        x: Configuration.get(x)
        for x in values.keys()
    }
    Configuration.update(**values)
    try:
        yield
    finally:
        Configuration.update(**old_values)


class TestCase(unittest.TestCase):
    """Common helpers, not meant to be used directly."""

    _transaction_case_teared_down = False

    @classmethod
    def init_configuration_manager(cls, **env):
        """ Initialise the configuration manager with environ variable
        to launch the test

        .. warning::

            For the moment we not use the environ variable juste constante

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
    def createdb(cls, keep_existing=False, with_demo=False):
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

        registry = RegistryManager.get(Configuration.get('db_name', None))
        if registry is None:
            return

        registry.System.Parameter.set(
            "with-demo", Configuration.get('with_demo', with_demo))

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

    Configuration = tmp_configuration


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
        clear_mappers()
        super(DBTestCase, self).tearDown()

    def init_registry(self, function, **kwargs):
        """ call a function to filled the blok manager with new model

        :param function: function to call
        :param kwargs: kwargs for the function
        :rtype: registry instance
        """
        return self.init_registry_with_bloks(None, function, **kwargs)

    def init_registry_with_bloks(self, bloks, function, **kwargs):
        """ call a function to filled the blok manager with new model and
        bloks to install

        :param bloks: list of blok's names
        :param function: function to call
        :param kwargs: kwargs for the function
        :rtype: registry instance
        """
        if bloks is None:
            bloks = []

        if isinstance(bloks, tuple):
            bloks = list(bloks)

        if 'anyblok-test' not in bloks:
            bloks.append('anyblok-test')

        from copy import deepcopy
        loaded_bloks = deepcopy(RegistryManager.loaded_bloks)
        if function is not None:
            EnvironmentManager.set('current_blok', 'anyblok-test')
            try:
                function(**kwargs)
            finally:
                EnvironmentManager.set('current_blok', None)

        try:
            self.registry = registry = self.__class__.getRegistry()
            if bloks:
                registry.upgrade(install=bloks)
        finally:
            RegistryManager.loaded_bloks = loaded_bloks

        return registry

    def reload_registry(self, registry, function, **kwargs):
        """ call a function to filled the blok manager with new model and
        before reload the registry

        :param bloks: list of blok's names
        :param function: function to call
        :param kwargs: kwargs for the function
        :rtype: registry instance
        """
        from copy import deepcopy
        loaded_bloks = deepcopy(RegistryManager.loaded_bloks)
        if function is not None:
            EnvironmentManager.set('current_blok', 'anyblok-test')
            try:
                function(**kwargs)
            finally:
                EnvironmentManager.set('current_blok', None)

        try:
            registry.reload()
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
            if len(BlokManager.list()) == 0:
                BlokManager.load()

            cls.registry = RegistryManager.get(Configuration.get('db_name'),
                                               **additional_setting)

        cls.registry.commit()

    def setUp(self):
        super(BlokTestCase, self).setUp()
        self.addCleanup(self.callCleanUp)
        self.registry.begin_nested()  # add SAVEPOINT

        @event.listens_for(self.registry.session, "after_transaction_end")
        def restart_savepoint(session, transaction):
            # TODO gracinet: while working on SharedDataTestCase
            # I noticed that this could keep listening long after everything
            # has been teared down. See SharedDataTestCase for unregistration
            # example.
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


class SharedDataTestCase(BlokTestCase):

    @classmethod
    def setUpClass(cls):
        super(SharedDataTestCase, cls).setUpClass()
        cls.pre_data_savepoint = cls.registry.begin_nested()
        try:
            cls.setUpSharedData()
        except Exception:
            cls.tearDownClass()
            raise

    @classmethod
    def setUpSharedData(cls):
        """To be implemented by concrete test classes."""

    @classmethod
    def make_case_savepoint(cls, session=None):
        if session is None:
            session = cls.registry
        cls.case_savepoint = session.begin_nested()

    def setUp(self):
        # we don't want to execute BlokTestCase.setUp(), only its parent's:
        super(BlokTestCase, self).setUp()
        # tearDown is not called in case of errors in setUp, but these are:
        self.addCleanup(self.callCleanUp)
        self.make_case_savepoint()

        @event.listens_for(self.registry.session, "after_transaction_end")
        def restart_savepoint(session, transaction):
            if transaction is self.case_savepoint:
                session.expire_all()
                self.make_case_savepoint()

        self.savepoint_restarter = restart_savepoint

    @classmethod
    def tearDownClass(cls):
        cls.pre_data_savepoint.rollback()
        super(SharedDataTestCase, cls).tearDownClass()

    def tearDown(self):
        """Roll back the session """
        super(BlokTestCase, self).tearDown()
        self.case_savepoint.rollback()
        self.registry.System.Cache.invalidate_all()
        event.remove(self.registry.session, "after_transaction_end",
                     self.savepoint_restarter)
        self._transaction_case_teared_down = True


class LogCapture(LC):
    """Overwrite ``testfixtures.LogCapture`` to add some helper methods"""

    def get_messages(self, *levels):
        """Return the captured messages
        ::

            with LogCapture() as logs:
                messages = logs.get_messages(INFO, WARNING)

        :param *levels: list of logging.level
        :rtype: list of formated message
        """
        return [
            self.format(r)
            for r in self.records
            if (not levels or r.levelno in levels)
        ]

    def get_debug_messages(self):
        """Return only the logging.DEBUG messages"""
        return self.get_messages(DEBUG)

    def get_info_messages(self):
        """Return only the logging.INFO messages"""
        return self.get_messages(INFO)

    def get_warning_messages(self):
        """Return only the logging.WARNING messages"""
        return self.get_messages(WARNING)

    def get_error_messages(self):
        """Return only the logging.ERROR messages"""
        return self.get_messages(ERROR)

    def get_critical_messages(self):
        """Return only the logging.CRITICAL messages"""
        return self.get_messages(CRITICAL)


def skip_unless_bloks_installed(*bloks):
    """A decorator to skip a test if some Bloks aren't installed.

    In cases of soft dependency between Bloks (i.e., the dependent Blok
    has some of its features behaving differently if another Blok is installed
    without actually requiring it), it's useful to write tests that will
    be executed only if some Bloks are installed.

    Here's an example taken from Anyblok / Wms Base,
    where the ``wms-inventory`` Blok wants to take Reservation
    into account if it's installed yet doesn't
    want to introduce a hard requirement onto ``wms-reservation``

        @skip_unless_bloks_installed('wms-reservation')
        def test_choose_affected_with_reserved(self):
            # this test can now safely assume that wms-reservation is installed

    """
    def bloks_decorator(testmethod):
        def wrapped(self):
            Blok = self.registry.System.Blok
            for blok_name in bloks:
                blok = Blok.query().get(blok_name)
                if blok.state != 'installed':
                    raise unittest.SkipTest(
                        "Blok %r is not installed" % blok_name)
            return testmethod(self)
        # necessary not to be ignored by test runner
        wrapped.__name__ = testmethod.__name__
        return wrapped
    return bloks_decorator


def sgdb_in(databases):
    if not DATABASES_CACHED:
        load_configuration()

    url = Configuration.get('get_url')(db_name='')
    engine = sqlalchemy.create_engine(url)
    return sgdb_in_(engine, databases)
