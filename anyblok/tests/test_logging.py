from .anybloktestcase import AnyBlokTestCase
from anyblok._logging import DataBaseLogging, DataBaseLoggingException
from anyblok._logging import setter, getter


class TestDataBaseLogging(AnyBlokTestCase):

    def tearDown(self):
        super(TestDataBaseLogging, self).tearDown()
        DataBaseLogging.define_setter(setter)
        DataBaseLogging.define_getter(getter)
        DataBaseLogging.set(None)

    def test_set_and_get(self):
        dbname = 'test db name'
        DataBaseLogging.set(dbname)
        self.assertEqual(DataBaseLogging.get(), dbname)

    def test_without_setter(self):
        DataBaseLogging.define_setter(None)
        try:
            DataBaseLogging.set('test')
            self.fail('No setter must be raise an exception')
        except DataBaseLoggingException:
            pass

    def test_bad_setter(self):
        DataBaseLogging.define_setter('Is not a function')
        try:
            DataBaseLogging.set('test')
            self.fail('Bad setter must be raise an exception')
        except DataBaseLoggingException:
            pass

    def test_without_getter(self):
        DataBaseLogging.define_getter(None)
        try:
            DataBaseLogging.get()
            self.fail('No getter must be raise an exception')
        except DataBaseLoggingException:
            pass

    def test_bad_getter(self):
        DataBaseLogging.define_getter('Is not a function')
        try:
            DataBaseLogging.get()
            self.fail('Bad getter must be raise an exception')
        except DataBaseLoggingException:
            pass
