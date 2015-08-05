# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.blok import BlokManager, Blok, BlokManagerException
from anyblok.tests.testcase import TestCase, DBTestCase
from anyblok.registry import RegistryException


class TestBlokManager(TestCase):

    def tearDown(self):
        super(TestBlokManager, self).tearDown()
        BlokManager.unload()

    def test_load_anyblok(self):
        BlokManager.load()
        if not BlokManager.list():
            self.fail('No blok load')
        if not BlokManager.has('anyblok-core'):
            self.fail("The blok 'anyblok-core' is missing")

        BlokManager.get('anyblok-core')

    def test_load_with_invalid_blok_group(self):
        try:
            BlokManager.load(entry_points=('Invalid blok group',))
            self.fail('Load with invalid blok group')
        except BlokManagerException:
            pass

    def test_load_without_blok_group(self):
        try:
            BlokManager.load(entry_points=())
            self.fail('No watchdog to load without blok groups')
        except BlokManagerException:
            pass

    def test_reload(self):
        BlokManager.load()
        BlokManager.set('invalid blok', None)
        BlokManager.get('invalid blok')
        BlokManager.reload()
        try:
            BlokManager.get('invalid blok')
            self.fail("Reload classmethod doesn't reload the bloks")
        except BlokManagerException:
            pass

    def test_reload_without_load(self):
        try:
            BlokManager.reload()
            self.fail('No exception when reload without previously load')
        except BlokManagerException:
            pass

    def test_get_invalid_blok(self):
        try:
            BlokManager.load()
            BlokManager.get('invalid blok')
            self.fail('No exception when get invalid blok')
        except BlokManagerException:
            pass

    def test_set(self):
        blok_name = 'ABlok'
        BlokManager.set(blok_name, Blok)
        self.assertEqual(BlokManager.has(blok_name), True)

    def test_set_two_time(self):
        blok_name = 'ABlok'
        BlokManager.set(blok_name, Blok)
        try:
            BlokManager.set(blok_name, Blok)
            self.fail("No watch dog for set two time the same blok")
        except BlokManagerException:
            pass


class DB2TestCase(DBTestCase):
    pass

   # @classmethod
   # def tearDownClass(cls):
   #     super(DB2TestCase, cls).tearDownClass()
   #     cls.regisrty.Session = None


class TestBlok(DB2TestCase):

    def test_blok_exist(self):
        Blok = self.registry.System.Blok
        query = Blok.query().filter(Blok.name == 'test-blok1')
        if not query.count():
            self.fail('No blok found')

        testblok1 = query.first()
        self.assertEqual(testblok1.state, 'uninstalled')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, None)
        self.assertEqual(testblok1.short_description, '')
        self.assertEqual(testblok1.long_description, '')

    def test_install(self):
        self.registry.upgrade(install=('test-blok1',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')

    def test_install_an_installed_blok(self):
        self.registry.upgrade(install=('test-blok1',))
        with self.assertRaises(RegistryException):
            self.registry.upgrade(install=('test-blok1',))

    def test_uninstall(self):
        self.registry.upgrade(install=('test-blok1',))
        self.registry.upgrade(uninstall=('test-blok1',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        self.assertEqual(testblok1.state, 'uninstalled')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, None)

    def test_uninstall_an_uninstalled_blok(self):
        with self.assertRaises(RegistryException):
            self.registry.upgrade(uninstall=('test-blok1',))

    def test_update(self):
        self.registry.upgrade(install=('test-blok1',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok1.version = '2.0.0'
        self.registry.upgrade(update=('test-blok1',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '2.0.0')

    def test_update_an_uninstalled_blok(self):
        with self.assertRaises(RegistryException):
            self.registry.upgrade(update=('test-blok1',))


class TestBlokRequired(DB2TestCase):

    def test_blok_exist(self):
        Blok = self.registry.System.Blok
        query = Blok.query().filter(Blok.name == 'test-blok2')
        if not query.count():
            self.fail('No blok found')

        testblok2 = query.first()
        self.assertEqual(testblok2.state, 'uninstalled')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, None)
        self.assertEqual(testblok2.short_description, 'Test blok2')

    def test_install_1by1(self):
        self.registry.upgrade(install=('test-blok1',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'uninstalled')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, None)
        self.registry.upgrade(install=('test-blok2',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, '1.0.0')

    def test_install(self):
        Blok = self.registry.System.Blok
        self.registry.upgrade(install=('test-blok2',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, '1.0.0')

    def test_uninstall(self):
        self.registry.upgrade(install=('test-blok2',))
        self.registry.upgrade(uninstall=('test-blok2',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'uninstalled')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, None)

    def test_uninstall_required(self):
        self.registry.upgrade(install=('test-blok2',))
        self.registry.upgrade(uninstall=('test-blok1',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        self.assertEqual(testblok1.state, 'uninstalled')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, None)
        self.assertEqual(testblok2.state, 'uninstalled')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, None)

    def test_update(self):
        self.registry.upgrade(install=('test-blok2',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok1.version = '2.0.0'
        testblok2.version = '2.0.0'
        self.registry.upgrade(update=('test-blok2',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.installed_version, '2.0.0')

    def test_update_required(self):
        self.registry.upgrade(install=('test-blok2',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok1.version = '2.0.0'
        testblok2.version = '2.0.0'
        self.registry.upgrade(update=('test-blok1',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '2.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.installed_version, '2.0.0')


class TestBlokRequired2(DB2TestCase):

    def test_blok_exist(self):
        Blok = self.registry.System.Blok
        query = Blok.query().filter(Blok.name == 'test-blok3')
        if not query.count():
            self.fail('No blok found')

        testblok2 = query.first()
        self.assertEqual(testblok2.state, 'uninstalled')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, None)
        long_description = ".. This file is a part of the AnyBlok project\n.."
        long_description += "\n..    Copyright (C) 2014 Jean-Sebastien SUZANNE"
        long_description += " <jssuzanne@anybox.fr>\n..\n.. This Source Code "
        long_description += "Form is subject to the terms of the Mozilla "
        long_description += "Public License,\n.. v. 2.0. If a copy of the MPL "
        long_description += "was not distributed with this file,You can\n.. "
        long_description += "obtain one at http://mozilla.org/MPL/2.0/.\n\n"
        long_description += "Test blok3\n"
        self.assertEqual(testblok2.long_description, long_description)

    def test_install_1by1(self):
        self.registry.upgrade(install=('test-blok1',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'uninstalled')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, None)
        self.assertEqual(testblok3.state, 'uninstalled')
        self.assertEqual(testblok3.version, '1.0.0')
        self.assertEqual(testblok3.installed_version, None)
        self.registry.upgrade(install=('test-blok2',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, '1.0.0')
        self.assertEqual(testblok3.state, 'uninstalled')
        self.assertEqual(testblok3.version, '1.0.0')
        self.assertEqual(testblok3.installed_version, None)
        self.registry.upgrade(install=('test-blok3',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, '1.0.0')
        self.assertEqual(testblok3.state, 'installed')
        self.assertEqual(testblok3.version, '1.0.0')
        self.assertEqual(testblok3.installed_version, '1.0.0')

    def test_install(self):
        Blok = self.registry.System.Blok
        self.registry.upgrade(install=('test-blok3',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, '1.0.0')
        self.assertEqual(testblok3.state, 'installed')
        self.assertEqual(testblok3.version, '1.0.0')
        self.assertEqual(testblok3.installed_version, '1.0.0')

    def test_uninstall(self):
        self.registry.upgrade(install=('test-blok3',))
        self.registry.upgrade(uninstall=('test-blok3',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, '1.0.0')
        self.assertEqual(testblok3.state, 'uninstalled')
        self.assertEqual(testblok3.version, '1.0.0')
        self.assertEqual(testblok3.installed_version, None)

    def test_uninstall_first_required(self):
        self.registry.upgrade(install=('test-blok3',))
        self.registry.upgrade(uninstall=('test-blok2',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'uninstalled')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, None)
        self.assertEqual(testblok3.state, 'uninstalled')
        self.assertEqual(testblok3.version, '1.0.0')
        self.assertEqual(testblok3.installed_version, None)

    def test_uninstall_all_required(self):
        self.registry.upgrade(install=('test-blok3',))
        self.registry.upgrade(uninstall=('test-blok1',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        self.assertEqual(testblok1.state, 'uninstalled')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, None)
        self.assertEqual(testblok2.state, 'uninstalled')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, None)
        self.assertEqual(testblok3.state, 'uninstalled')
        self.assertEqual(testblok3.version, '1.0.0')
        self.assertEqual(testblok3.installed_version, None)

    def test_update(self):
        self.registry.upgrade(install=('test-blok3',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        testblok1.version = '2.0.0'
        testblok2.version = '2.0.0'
        testblok3.version = '2.0.0'
        self.registry.upgrade(update=('test-blok3',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.installed_version, '1.0.0')
        self.assertEqual(testblok3.state, 'installed')
        self.assertEqual(testblok3.installed_version, '2.0.0')

    def test_update_first_required(self):
        self.registry.upgrade(install=('test-blok3',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        testblok1.version = '2.0.0'
        testblok2.version = '2.0.0'
        testblok3.version = '2.0.0'
        self.registry.upgrade(update=('test-blok2',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.installed_version, '2.0.0')
        self.assertEqual(testblok3.state, 'installed')
        self.assertEqual(testblok3.installed_version, '2.0.0')

    def test_update_all_required(self):
        self.registry.upgrade(install=('test-blok3',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        testblok1.version = '2.0.0'
        testblok2.version = '2.0.0'
        testblok3.version = '2.0.0'
        self.registry.upgrade(update=('test-blok1',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '2.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.installed_version, '2.0.0')
        self.assertEqual(testblok3.state, 'installed')
        self.assertEqual(testblok3.installed_version, '2.0.0')


class TestBlokConditionnal(DB2TestCase):

    def test_install_1by1(self):
        self.registry.upgrade(install=('test-blok1',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok4.state, 'uninstalled')
        self.assertEqual(testblok4.version, '1.0.0')
        self.assertEqual(testblok4.installed_version, None)
        self.assertEqual(testblok5.state, 'uninstalled')
        self.assertEqual(testblok5.version, '1.0.0')
        self.assertEqual(testblok5.installed_version, None)
        self.registry.upgrade(install=('test-blok4',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok4.state, 'installed')
        self.assertEqual(testblok4.version, '1.0.0')
        self.assertEqual(testblok4.installed_version, '1.0.0')
        self.assertEqual(testblok5.state, 'installed')
        self.assertEqual(testblok5.version, '1.0.0')
        self.assertEqual(testblok5.installed_version, '1.0.0')

    def test_install(self):
        self.registry.upgrade(install=('test-blok5',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok4.state, 'installed')
        self.assertEqual(testblok4.version, '1.0.0')
        self.assertEqual(testblok4.installed_version, '1.0.0')
        self.assertEqual(testblok5.state, 'installed')
        self.assertEqual(testblok5.version, '1.0.0')
        self.assertEqual(testblok5.installed_version, '1.0.0')

    def test_uninstall(self):
        self.registry.upgrade(install=('test-blok5',))
        with self.assertRaises(RegistryException):
            self.registry.upgrade(uninstall=('test-blok5',))

    def test_uninstall_conditionnal(self):
        self.registry.upgrade(install=('test-blok5',))
        self.registry.upgrade(uninstall=('test-blok1',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        self.assertEqual(testblok1.state, 'uninstalled')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, None)
        self.assertEqual(testblok4.state, 'installed')
        self.assertEqual(testblok4.version, '1.0.0')
        self.assertEqual(testblok4.installed_version, '1.0.0')
        self.assertEqual(testblok5.state, 'uninstalled')
        self.assertEqual(testblok5.version, '1.0.0')
        self.assertEqual(testblok5.installed_version, None)

    def test_update(self):
        self.registry.upgrade(install=('test-blok5',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        testblok1.version = '2.0.0'
        testblok4.version = '2.0.0'
        testblok5.version = '2.0.0'
        self.registry.upgrade(update=('test-blok5',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok4.state, 'installed')
        self.assertEqual(testblok4.installed_version, '1.0.0')
        self.assertEqual(testblok5.state, 'installed')
        self.assertEqual(testblok5.installed_version, '2.0.0')

    def test_update_conditionnal(self):
        self.registry.upgrade(install=('test-blok5',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        testblok1.version = '2.0.0'
        testblok4.version = '2.0.0'
        testblok5.version = '2.0.0'
        self.registry.upgrade(update=('test-blok1',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '2.0.0')
        self.assertEqual(testblok4.state, 'installed')
        self.assertEqual(testblok4.installed_version, '1.0.0')
        self.assertEqual(testblok5.state, 'installed')
        self.assertEqual(testblok5.installed_version, '2.0.0')


class TestBlokOptional(DB2TestCase):

    def test_install_1by1(self):
        self.registry.upgrade(install=('test-blok1',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok6.state, 'uninstalled')
        self.assertEqual(testblok6.version, '1.0.0')
        self.assertEqual(testblok6.installed_version, None)
        self.registry.upgrade(install=('test-blok6',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok6.state, 'installed')
        self.assertEqual(testblok6.version, '1.0.0')
        self.assertEqual(testblok6.installed_version, '1.0.0')

    def test_install(self):
        Blok = self.registry.System.Blok
        self.registry.upgrade(install=('test-blok6',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok6.state, 'installed')
        self.assertEqual(testblok6.version, '1.0.0')
        self.assertEqual(testblok6.installed_version, '1.0.0')

    def test_uninstall(self):
        self.registry.upgrade(install=('test-blok6',))
        self.registry.upgrade(uninstall=('test-blok6',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok6.state, 'uninstalled')
        self.assertEqual(testblok6.version, '1.0.0')
        self.assertEqual(testblok6.installed_version, None)

    def test_uninstall_optional(self):
        Blok = self.registry.System.Blok
        self.registry.upgrade(install=('test-blok6',))
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        testblok6.version = '2.0.0'
        self.registry.upgrade(uninstall=('test-blok1',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        self.assertEqual(testblok1.state, 'uninstalled')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, None)
        self.assertEqual(testblok6.state, 'installed')
        self.assertEqual(testblok6.version, '2.0.0')
        self.assertEqual(testblok6.installed_version, '2.0.0')

    def test_update(self):
        self.registry.upgrade(install=('test-blok6',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        testblok1.version = '2.0.0'
        testblok6.version = '2.0.0'
        self.registry.upgrade(update=('test-blok6',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok6.state, 'installed')
        self.assertEqual(testblok6.installed_version, '2.0.0')

    def test_update_optional(self):
        self.registry.upgrade(install=('test-blok6',))
        Blok = self.registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        testblok1.version = '2.0.0'
        testblok6.version = '2.0.0'
        self.registry.upgrade(update=('test-blok1',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '2.0.0')
        self.assertEqual(testblok6.state, 'installed')
        self.assertEqual(testblok6.installed_version, '2.0.0')


class TestBlokOrder(DB2TestCase):

    def check_order(self, mode, wanted):
        Test = self.registry.Test
        self.assertEqual(Test.query().filter(Test.mode == mode).all().blok,
                         wanted)

    def test_install(self):
        self.registry.upgrade(install=('test-blok3',))
        self.check_order('install', [
            'test-blok1', 'test-blok2', 'test-blok3'])

    def test_uninstall(self):
        from anyblok.blok import Blok, BlokManager
        old_uninstall = Blok.uninstall

        uninstalled = []

        def uninstall(self):
            cls = self.__class__
            uninstalled.extend(
                [x for x, y in BlokManager.bloks.items() if y is cls])

        try:
            Blok.uninstall = uninstall
            self.registry.upgrade(install=('test-blok3',))
            self.registry.upgrade(uninstall=('test-blok1',))
            self.assertEqual(uninstalled, [
                'test-blok3', 'test-blok2', 'test-blok1'])
        finally:
            Blok.uninstall = old_uninstall

    def test_update(self):
        self.registry.upgrade(install=('test-blok3',))
        self.registry.upgrade(update=('test-blok1',))
        self.check_order('update', [
            'test-blok1', 'test-blok2', 'test-blok3'])

    def test_load(self):
        self.registry.upgrade(install=('test-blok3',))
        self.check_order('load', [
            'anyblok-core', 'test-blok1', 'test-blok2', 'test-blok3'])


class TestBlokModel(DB2TestCase):

    def test_remove_foreign_key_after_uninstallation_1(self):
        self.registry.upgrade(install=('test-blok7', 'test-blok8'))
        t2 = self.registry.Test2.insert(label="test2")
        self.registry.Test.insert(label="Test1", test2=t2.id)
        self.registry.old_session_commit()
        from sqlalchemy.exc import IntegrityError
        with self.assertRaises(IntegrityError):
            self.registry.Test2.query().delete()

    def test_remove_foreign_key_after_uninstallation_2(self):
        self.registry.upgrade(install=('test-blok7', 'test-blok8'))
        t2 = self.registry.Test2.insert(label="test2")
        self.registry.Test.insert(label="Test1", test2=t2.id)
        self.registry.old_session_commit()
        self.registry.upgrade(uninstall=('test-blok8',))
        self.registry.Test2.query().delete()


class TestBlokSession(DB2TestCase):

    def test_session_with_no_change(self):
        Session = self.registry.Session
        self.registry.upgrade(install=('test-blok1',))
        self.assertIs(Session, self.registry.Session)

    def test_session_with_change_query(self):
        Session = self.registry.Session
        self.registry.upgrade(install=('test-blok11',))
        self.assertIsNot(Session, self.registry.Session)

    def test_session_with_change_session(self):
        Session = self.registry.Session
        self.registry.upgrade(install=('test-blok12',))
        self.assertIsNot(Session, self.registry.Session)
