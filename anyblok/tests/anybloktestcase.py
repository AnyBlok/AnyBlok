import unittest
from sys import modules
from logging import getLogger
from AnyBlok.Interface import ISqlAlchemyDataBase
from anyblok._argsparse import ArgsParseManager
from zope.component import getUtility
from anyblok.registry import RegistryManager
from anyblok.blok import BlokManager
import AnyBlok

logger = getLogger(__name__)


class AnyBlokTestCase(unittest.TestCase):
    """ Unittest class add helper for unit test in anyblok """
    @classmethod
    def init_argsparse_manager(cls, env=None):
        """ Initialise the argsparse manager with environ variable
        to launch the test

        .. warning::

            For the moment we not use the environ variable juste constante

        :param env: add another dict to merge with environ variable
        """
        if env is None:
            env = {}
        env.update({
            'dbname': 'test_anyblok',  # TODO use os.env
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
    def createdb(cls):
        """ Create a database in fonction of variable of environment

        ::

            cls.init_argsparse_manager()
            cls.createdb()

        """
        adapter = getUtility(ISqlAlchemyDataBase,
                             ArgsParseManager.get('dbdrivername'))
        dbname = ArgsParseManager.get('dbname')
        if dbname in adapter.listdb():
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


class AnyBlokDBTestCase(AnyBlokTestCase):
    """ Test case for all the Field, Column, RelationShip

    ::

        from anyblok.tests.anybloktestcase import AnyBlokDBTestCase


        def simple_column(ColumnType=None, **kwargs):

            from AnyBlok import target_registry, Model
            from AnyBlok.Column import Integer

            @target_registry(Model)
            class Test:

                id = Integer(label='id', primary_key=True)
                col = ColumnType(label="col", **kwargs)


        class TestColumns(AnyBlokDBTestCase):

            def test_integer(self):
                from AnyBlok.Column import Integer

                registry = self.init_registry(simple_column,
                                              ColumnType=Integer)
                test = registry.Test.insert(col=1)
                self.assertEqual(test.col, 1)

    .. warning::

        The database are create and drop for each unit test

    """

    part_to_load = ['AnyBlok']
    """ blok group to load """
    current_blok = 'anyblok-core'
    """ In the blok to add the new model """

    @classmethod
    def setUpClass(cls):
        """ Intialialise the argsparse manager """
        super(AnyBlokDBTestCase, cls).setUpClass()
        cls.init_argsparse_manager()

    def setUp(self):
        """ Create a database and load the blok manager """
        super(AnyBlokDBTestCase, self).setUp()
        self.createdb()
        BlokManager.load(*self.part_to_load)

    def tearDown(self):
        """ Clear the registry, unload the blok manager and  drop the database
        """
        RegistryManager.clear()
        BlokManager.unload()
        self.dropdb()
        super(AnyBlokDBTestCase, self).tearDown()

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
