# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase
from anyblok.blok import BlokManager
from sys import modules
from anyblok.imp import ImportManager, ImportManagerException
from os.path import join
from .mockblok import mockblok


tests_path = join('/'.join(__file__.split('/')[:-1]), 'mockblok')
with open(join(tests_path, 'mockfile.py'), 'r') as fp:
    initial_file = fp.read()


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

    def test_reload(self):
        blok = ImportManager.add('mockblok')
        blok.imports()
        from .mockblok.mockpackage import mockfile1, mockfile2
        from .mockblok.mockpackage import submockpackage
        from .mockblok import mockfile

        with open(join(tests_path, 'mockpackage', 'mockfile1.py'), 'w') as fp:
            fp.write("""foo = 'reload'""")

        with open(join(tests_path, 'mockpackage', 'submockpackage',
                       'mockfile2.py'), 'w') as fp:
            fp.write("""foo = 'reload'""")

        with open(join(tests_path, 'mockfile.py'), 'w') as fp:
            fp.write("""foo = 'reload'""")

        try:
            self.assertEqual(mockfile1.foo, 'bar')
            self.assertEqual(mockfile2.foo, 'bar')
            self.assertEqual(submockpackage.mockfile1.foo, 'bar')
            self.assertEqual(submockpackage.mockfile2.foo, 'bar')
            self.assertEqual(mockfile.foo, 'bar')
            blok.reload()
            self.assertEqual(mockfile1.foo, 'reload')
            self.assertEqual(mockfile2.foo, 'bar')
            self.assertEqual(submockpackage.mockfile1.foo, 'bar')
            self.assertEqual(submockpackage.mockfile2.foo, 'reload')
            self.assertEqual(mockfile.foo, 'reload')
        finally:
            with open(join(tests_path, 'mockfile.py'), 'w') as fp:
                fp.write(initial_file)

            with open(join(tests_path, 'mockpackage',
                           'mockfile1.py'), 'w') as fp:
                fp.write(initial_file)

            with open(join(tests_path, 'mockpackage', 'submockpackage',
                           'mockfile2.py'), 'w') as fp:
                fp.write(initial_file)

    def test_imports(self):
        blok = ImportManager.add('mockblok')
        blok.imports()
        from .mockblok.mockpackage import mockfile1, mockfile2
        from .mockblok.mockpackage import submockpackage
        from .mockblok import mockfile
        self.assertEqual(mockfile1.foo, 'bar')
        self.assertEqual(mockfile2.foo, 'bar')
        self.assertEqual(submockpackage.mockfile1.foo, 'bar')
        self.assertEqual(submockpackage.mockfile2.foo, 'bar')
        self.assertEqual(mockfile.foo, 'bar')
