import unittest
from sys import modules
from logging import getLogger

logger = getLogger(__name__)


class AnyBlokTestCase(unittest.TestCase):
    """ Unittest class add helper for unit test in anyblok """

    def check_package_version(self, package, operator, version):
        """ Check the version of one package

        :param package: Name of the package
        :param operator: Operator for the validation
        :param version: the referential version
        :rtype: boolean
        """
        test = "%r %s %r" % (modules[package].__version__, operator, version)
        logger.warning('check the module version : %s' % test)
        return eval(test)
