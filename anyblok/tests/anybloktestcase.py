import unittest
from sys import modules
from logging import getLogger
from AnyBlok.Interface import ISqlAlchemyDataBase
from anyblok._argsparse import ArgsParseManager
from zope.component import getUtility
from anyblok.registry import RegistryManager

logger = getLogger(__name__)


class AnyBlokTestCase(unittest.TestCase):
    """ Unittest class add helper for unit test in anyblok """
    @classmethod
    def init_argsparse_manager(cls, env=None):
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
        return RegistryManager.get(ArgsParseManager.get('dbname'))
