import unittest
from sys import modules
from logging import getLogger
from AnyBlok.Interface import ISqlAlchemyDataBase
from anyblok._argsparse import ArgsParseManager
from zope.component import getUtility
from anyblok.registry import RegistryManager
from anyblok.blok import BlokManager
import AnyBlok
from anyblok import start

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

    def check_package_version(self, package, operator, version):
        """ Check the version of one package

        ::

            self.check_package_version('alembic', '>', '0.6.4')

        :param package: Name of the package
        :param operator: Operator for the validation
        :param version: the referential version
        :rtype: boolean
        """
        test = "%r %s %r" % (modules[package].__version__, operator, version)
        logger.warning('check the module version : %s' % test)
        return eval(test)

    @classmethod
    def createdb(cls, keep_existing=False):
        """ Create a database in fonction of variable of environment

        ::

            cls.init_argsparse_manager()
            cls.createdb()

        :param keep_existing: If false drop the previous db before create it
        """
        adapter = getUtility(ISqlAlchemyDataBase,
                             ArgsParseManager.get('dbdrivername'))
        dbname = ArgsParseManager.get('dbname')
        if dbname in adapter.listdb():
            if keep_existing:
                return

            adapter.dropdb(dbname)

        adapter.createdb(dbname)

    @classmethod
    def dropdb(cls):
        """ Drop a database in fonction of variable of environment

        ::

            cls.init_argsparse_manager()
            cls.dropdb()

        """
        adapter = getUtility(ISqlAlchemyDataBase,
                             ArgsParseManager.get('dbdrivername'))
        adapter.dropdb(ArgsParseManager.get('dbname'))

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

            from AnyBlok import target_registry, Model
            from AnyBlok.Column import Integer

            @target_registry(Model)
            class Test:

                id = Integer(label='id', primary_key=True)
                col = ColumnType(label="col", **kwargs)


        class TestColumns(DBTestCase):

            def test_integer(self):
                from AnyBlok.Column import Integer

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

    def init_registry(self, function, **kwargs):
        """ call a function to filled the blok manager with new model

        :param function: function to call
        :param kwargs: kwargs for the function
        :rtype: registry instance
        """
        AnyBlok.current_blok = self.current_blok
        try:
            function(**kwargs)
        finally:
            AnyBlok.current_blok = None
        return self.getRegistry()


class BlokTestCase(TestCase):
    """ Use to test bloks without have to create new database for each test

    ::

        from anyblok.tests.testcase import BlokTestCase


        class MyBlokTest(BlokTestCase):

            parts_to_load = ['AnyBlok']
            need_blok = ['blok 1', 'blok 2', ..., 'blok n']

            def test_1(self):
                ...

    """

    parts_to_load = None
    """ Group of blok to load """

    need_blok = ['anyblok-core']
    """ List of the blok need for this test """

    @classmethod
    def setUpClass(cls):
        """ Intialialise the argsparse manager """
        super(BlokTestCase, cls).setUpClass()
        cls.init_argsparse_manager()
        cls.createdb(keep_existing=True)
        registry = start('BlokTestCase', parts_to_load=cls.parts_to_load)
        cls.registry = registry

        query = registry.System.Blok.query('name')
        query = query.filter(registry.System.Blok.name.in_(cls.need_blok),
                             registry.System.Blok.state == 'uninstalled')

        bloks = [x[0] for x in query.all()]

        if bloks:
            registry.upgrade(install=bloks)

    def tearDown(self):
        """ Roll back the session """
        self.registry.rollback()

    @classmethod
    def tearDownClass(self):
        """ Clear the registry, unload the blok manager
        """
        RegistryManager.clear()
        BlokManager.unload()
        super(BlokTestCase, self).tearDownClass()
