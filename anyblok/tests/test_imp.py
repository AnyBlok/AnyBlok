import anyblok
from anyblok.tests.testcase import TestCase
from anyblok.blok import BlokManager, Blok
from sys import modules
from anyblok._imp import ImportManager
from os.path import join
ImportManagerException = anyblok.Declarations.Exception.ImportManagerException


tests_path = join(anyblok.__path__[0], 'tests', 'mockblok')
fp = open(join(tests_path, 'mockfile.py'), 'r')
initial_file = fp.read()
fp.close()


class OneBlok(Blok):
    pass


class TestImportManager(TestCase):

    def setUp(self):
        super(TestImportManager, self).setUp()
        BlokManager.bloks['blokTest'] = OneBlok
        BlokManager.ordered_bloks.append('blokTest')

    def tearDown(self):
        super(TestImportManager, self).tearDown()
        if 'AnyBlok.bloks.blokTest' in modules:
            mod_2_del = []
            for mod in modules.keys():
                if 'AnyBlok.bloks.blokTest' in mod:
                    mod_2_del.append(mod)

        fp = open(join(tests_path, 'mockfile.py'), 'w')
        fp.write(initial_file)
        fp.close()

        fp = open(join(tests_path, 'mockpackage', 'mockfile1.py'), 'w')
        fp.write(initial_file)
        fp.close()

        fp = open(join(tests_path, 'mockpackage', 'submockpackage',
                       'mockfile2.py'), 'w')
        fp.write(initial_file)
        fp.close()

        del BlokManager.bloks['blokTest']
        BlokManager.ordered_bloks.remove('blokTest')

    def test_has_blok(self):
        ImportManager.add('blokTest', join(tests_path, '__init__.py'))
        self.assertEqual(ImportManager.has('blokTest'), True)
        self.assertEqual(ImportManager.has('blokTest2'), False)

    def test_get_blok(self):
        ImportManager.add('blokTest', join(tests_path, '__init__.py'))
        blok = ImportManager.get('blokTest')
        self.assertEqual(blok.path, tests_path)

    def test_get_unexisting_blok(self):
        try:
            ImportManager.get('blokTest2')
            self.fail('No watchdog for inexisting blok module')
        except ImportManagerException:
            pass

    def test_reload(self):
        blok = ImportManager.add('blokTest', join(tests_path, '__init__.py'))
        blok.imports()
        from anyblok.bloks.blokTest.mockpackage import mockfile1, mockfile2
        from anyblok.bloks.blokTest.mockpackage import submockpackage
        from anyblok.bloks.blokTest import mockfile

        fp = open(join(tests_path, 'mockpackage', 'mockfile1.py'), 'w')
        fp.write("""foo = 'reload'""")
        fp.close()

        fp = open(join(tests_path, 'mockpackage', 'submockpackage',
                       'mockfile2.py'), 'w')
        fp.write("""foo = 'reload'""")
        fp.close()

        fp = open(join(tests_path, 'mockfile.py'), 'w')
        fp.write("""foo = 'reload'""")
        fp.close()

        blok.reload()
        self.assertEqual(mockfile1.foo, 'reload')
        self.assertEqual(mockfile2.foo, 'bar')
        self.assertEqual(submockpackage.mockfile1.foo, 'bar')
        self.assertEqual(submockpackage.mockfile2.foo, 'reload')
        self.assertEqual(mockfile.foo, 'reload')

    def test_imports(self):
        blok = ImportManager.add('blokTest', join(tests_path, '__init__.py'))
        blok.imports()
        from anyblok.bloks.blokTest.mockfile import foo
        self.assertEqual(foo, 'bar')
        from anyblok.bloks.blokTest.mockpackage import mockfile1, mockfile2
        from anyblok.bloks.blokTest.mockpackage import submockpackage
        self.assertEqual(mockfile1.foo, 'bar')
        self.assertEqual(mockfile2.foo, 'bar')
        self.assertEqual(submockpackage.mockfile1.foo, 'bar')
        self.assertEqual(submockpackage.mockfile2.foo, 'bar')
