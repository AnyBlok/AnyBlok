import unittest
from sys import modules
from logging import getLogger

logger = getLogger(__name__)


class AnyBlokTestCase(unittest.TestCase):

    def check_module_version(self, module, operator, version):
        test = "%r %s %r" % (modules[module].__version__, operator, version)
        logger.warning('check the module version : %s' % test)
        return eval(test)
