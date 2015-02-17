# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import unittest
from logging import getLogger
from anyblok._argsparse import ArgsParseManager
from anyblok.registry import RegistryManager
from anyblok.blok import BlokManager
from anyblok.environment import EnvironmentManager
import anyblok

logger = getLogger(__name__)


class TestCase(unittest.TestCase):
    """ Unittest class add helper for unit test in anyblok """
    @classmethod
    def init_argsparse_manager(cls, prefix=None, **env):
        """ Initialise the argsparse manager with environ variable
        to launch the test

        .. warning::

            For the moment we not use the environ variable juste constante

        :param prefix: prefix the database name
        :param env: add another dict to merge with environ variable
        """

        dbname = 'test_anyblok'

        if prefix:
            dbname = prefix + '_' + dbname

        if env is None:
            env = {}
        env.update({
            'dbname': dbname,  # TODO use os.env
            'dbdrivername': 'postgres',
            'dbusername': '',
            'dbpassword': '',
            'dbhost': '',
            'dbport': '',
        })
        ArgsParseManager.configuration = env

    @classmethod
    def createdb(cls, keep_existing=False):
        """ Create a database in fonction of variable of environment

        ::

            cls.init_argsparse_manager()
            cls.createdb()

        :param keep_existing: If false drop the previous db before create it
        """
        bdd = anyblok.BDD[ArgsParseManager.get('dbdrivername')]
        dbname = ArgsParseManager.get('dbname')
        if dbname in bdd.listdb():
            if keep_existing:
                return True

            bdd.dropdb(dbname)

        bdd.createdb(dbname)

    @classmethod
    def dropdb(cls):
        """ Drop a database in fonction of variable of environment

        ::

            cls.init_argsparse_manager()
            cls.dropdb()

        """
        bdd = anyblok.BDD[ArgsParseManager.get('dbdrivername')]
        bdd.dropdb(ArgsParseManager.get('dbname'))

    def getRegistry(self):
        """ Return the registry for the database in argsparse i

        ::

            registry = self.getRegistry()

        :rtype: registry instance
        """
        return RegistryManager.get(ArgsParseManager.get('dbname'))


class DBTestCase(TestCase):
    """ Test case for all the Field, Column, RelationShip

    ::

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

    .. warning::

        The database are create and drop for each unit test

    """

    parts_to_load = ['AnyBlok']
    """ blok group to load """
    current_blok = 'anyblok-core'
    """ In the blok to add the new model """

    @classmethod
    def setUpClass(cls):
        """ Intialialise the argsparse manager """
        super(DBTestCase, cls).setUpClass()
        cls.init_argsparse_manager(prefix='db_testcase')

    def setUp(self):
        """ Create a database and load the blok manager """
        super(DBTestCase, self).setUp()
        self.createdb()
        BlokManager.load(*self.parts_to_load)

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
    """ Use to test bloks without have to create new database for each test

    ::

        from anyblok.tests.testcase import BlokTestCase


        class MyBlokTest(BlokTestCase):

            def test_1(self):
                # access of the registry by ``self.registry``
                ...

    """

    @classmethod
    def setUpClass(cls):
        """ Intialialise the argsparse manager

        Deactivate the commit method of the registry
        """
        super(BlokTestCase, cls).setUpClass()
        if not hasattr(cls, 'registry'):
            cls.registry = RegistryManager.get(ArgsParseManager.get('dbname'))

        def session_commit(*args, **kwargs):
            pass

        cls.old_session_commit = cls.registry.session_commit
        cls.registry.session_commit = session_commit

    @classmethod
    def tearDownClass(cls):
        super(BlokTestCase, cls).tearDownClass()
        cls.registry.session_commit = cls.old_session_commit

    def tearDown(self):
        """ Roll back the session """
        self.registry.rollback()
