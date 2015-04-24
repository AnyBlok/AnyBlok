# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import anyblok
from anyblok.tests.testcase import TestCase
from anyblok.blok import BlokManager
from sys import modules
from anyblok._imp import ImportManager
from os.path import join
from unittest import skipIf
from .mockblok import mockblok
ImportManagerException = anyblok.Declarations.Exception.ImportManagerException


tests_path = join('/'.join(__file__.split('/')[:-1]), 'mockblok')
fp = open(join(tests_path, 'mockfile.py'), 'r')
initial_file = fp.read()
fp.close()


def python_version():
    import sys
    return '%d.%d' % (sys.version_info.major, sys.version_info.minor)


class TestImportManager(TestCase):

    def setUp(self):
        super(TestImportManager, self).setUp()
        BlokManager.bloks['mockblok'] = mockblok
        BlokManager.ordered_bloks.append('mockblok')

    def tearDown(self):
        super(TestImportManager, self).tearDown()
        if '.mockblok.' in modules:
            mod_2_del = []
            for mod in modules.keys():
                if '.mockblok.' in mod:
                    mod_2_del.append(mod)

            for mod in mod_2_del:
                del modules[mod]

        del BlokManager.bloks['mockblok']
        BlokManager.ordered_bloks.remove('mockblok')

    def test_has_blok(self):
        ImportManager.add('mockblok')
        self.assertEqual(ImportManager.has('mockblok'), True)
        self.assertEqual(ImportManager.has('mockblok2'), False)

    def test_get_blok(self):
        ImportManager.add('mockblok')
        ImportManager.get('mockblok')

    def test_get_unexisting_blok(self):
        try:
            ImportManager.get('mockblok2')
            self.fail('No watchdog for inexisting blok module')
        except ImportManagerException:
            pass

    @skipIf(python_version() < '3.3', "Reload doesn't work in python 3.2")
    def test_reload(self):
        blok = ImportManager.add('mockblok')
        blok.imports()
        from .mockblok.mockpackage import mockfile1, mockfile2
        from .mockblok.mockpackage import submockpackage
        from .mockblok import mockfile

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
        try:
            self.assertEqual(mockfile1.foo, 'reload')
            self.assertEqual(mockfile2.foo, 'bar')
            self.assertEqual(submockpackage.mockfile1.foo, 'bar')
            self.assertEqual(submockpackage.mockfile2.foo, 'reload')
            self.assertEqual(mockfile.foo, 'reload')
        finally:
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

    def test_imports(self):
        blok = ImportManager.add('mockblok')
        blok.imports()
        from .mockblok.mockfile import foo
        self.assertEqual(foo, 'bar')
        from .mockblok.mockpackage import mockfile1, mockfile2
        from .mockblok.mockpackage import submockpackage
        self.assertEqual(mockfile1.foo, 'bar')
        self.assertEqual(mockfile2.foo, 'bar')
        self.assertEqual(submockpackage.mockfile1.foo, 'bar')
        self.assertEqual(submockpackage.mockfile2.foo, 'bar')
