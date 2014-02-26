import unittest
import anyblok
from sys import modules
from anyblok._imp import ImportManager, ImportManagerException
from os.path import join


tests_path = join(anyblok.__path__[0], 'tests', 'mockblok')
fp = open(join(tests_path, 'mockfile.py'), 'r')
initial_file = fp.read()
fp.close()


class TestImportManager(unittest.TestCase):

    def tearDown(self):
        super(TestImportManager, self).tearDown()
        if 'anyblok.bloks.blokTest' in modules:
            mod_2_del = []
            for mod in modules.keys():
                if 'anyblok.bloks.blokTest' in mod:
                    mod_2_del.append(mod)

            for mod in mod_2_del:
                del modules[mod]

            del ImportManager.modules['blokTest']

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

    def test_bloks_exist(self):
        from anyblok import bloks
        dir(bloks)

    def test_add_blok(self):
        blok = ImportManager.add('blokTest', tests_path)
        self.assertEqual(modules['anyblok.bloks.blokTest'], blok)

    def test_add_existing_blok(self):
        blok1 = ImportManager.add('blokTest', tests_path)
        blok2 = ImportManager.add('blokTest', tests_path)
        self.assertEqual(modules['anyblok.bloks.blokTest'], blok1)
        self.assertEqual(modules['anyblok.bloks.blokTest'], blok2)

    def test_has_blok(self):
        ImportManager.add('blokTest', tests_path)
        self.assertEqual(ImportManager.has('blokTest'), True)
        self.assertEqual(ImportManager.has('blokTest2'), False)

    def test_get_blok(self):
        ImportManager.add('blokTest', tests_path)
        blok = ImportManager.get('blokTest')
        self.assertEqual(modules['anyblok.bloks.blokTest'], blok)

    def test_get_unexisting_blok(self):
        try:
            ImportManager.get('blokTest')
            self.fail('No watchdog for inexisting blok module')
        except ImportManagerException:
            pass

    def test_import_module(self):
        blok = ImportManager.add('blokTest', tests_path)
        blok.import_module('mockfile.py')
        from anyblok.bloks.blokTest.mockfile import foo
        self.assertEqual(foo, 'bar')

    def test_reload_module(self):
        blok = ImportManager.add('blokTest', tests_path)
        blok.import_module('mockfile.py')
        from anyblok.bloks.blokTest import mockfile
        fp = open(join(tests_path, 'mockfile.py'), 'w')
        fp.write("""foo = 'reload'""")
        fp.close()
        blok.reload()
        self.assertEqual(mockfile.foo, 'reload')

    def test_import_package(self):
        blok = ImportManager.add('blokTest', tests_path)
        blok.import_package('mockpackage')
        from anyblok.bloks.blokTest.mockpackage import mockfile1, mockfile2
        from anyblok.bloks.blokTest.mockpackage import submockpackage
        self.assertEqual(mockfile1.foo, 'bar')
        self.assertEqual(mockfile2.foo, 'bar')
        self.assertEqual(submockpackage.mockfile1.foo, 'bar')
        self.assertEqual(submockpackage.mockfile2.foo, 'bar')

    def test_reload_package(self):
        blok = ImportManager.add('blokTest', tests_path)
        blok.import_package('mockpackage')
        from anyblok.bloks.blokTest.mockpackage import mockfile1, mockfile2
        from anyblok.bloks.blokTest.mockpackage import submockpackage

        fp = open(join(tests_path, 'mockpackage', 'mockfile1.py'), 'w')
        fp.write("""foo = 'reload'""")
        fp.close()

        fp = open(join(tests_path, 'mockpackage', 'submockpackage',
                       'mockfile2.py'), 'w')
        fp.write("""foo = 'reload'""")
        fp.close()

        blok.reload()
        self.assertEqual(mockfile1.foo, 'reload')
        self.assertEqual(mockfile2.foo, 'bar')
        self.assertEqual(submockpackage.mockfile1.foo, 'bar')
        self.assertEqual(submockpackage.mockfile2.foo, 'reload')

    def test_imports(self):
        blok = ImportManager.add('blokTest', tests_path)
        blok.imports()
        from anyblok.bloks.blokTest.mockfile import foo
        self.assertEqual(foo, 'bar')
        from anyblok.bloks.blokTest.mockpackage import mockfile1, mockfile2
        from anyblok.bloks.blokTest.mockpackage import submockpackage
        self.assertEqual(mockfile1.foo, 'bar')
        self.assertEqual(mockfile2.foo, 'bar')
        self.assertEqual(submockpackage.mockfile1.foo, 'bar')
        self.assertEqual(submockpackage.mockfile2.foo, 'bar')
