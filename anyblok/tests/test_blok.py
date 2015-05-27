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


class TestBlok(DBTestCase):

    blok_entry_points = ('bloks', 'test_bloks')

    def test_blok_exist(self):
        registry = self.init_registry(None)
        Blok = registry.System.Blok
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
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')

    def test_install_an_installed_blok(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok1',))
        try:
            self.upgrade(registry, install=('test-blok1',))
            self.fail('No watchdog to install an installed blok')
        except RegistryException:
            pass

    def test_uninstall(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok1',))
        self.upgrade(registry, uninstall=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        self.assertEqual(testblok1.state, 'uninstalled')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, None)

    def test_uninstall_an_uninstalled_blok(self):
        registry = self.init_registry(None)
        try:
            self.upgrade(registry, uninstall=('test-blok1',))
            self.fail('No watchdog to uninstall an uninstalled blok')
        except RegistryException:
            pass

    def test_update(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok1.version = '2.0.0'
        self.upgrade(registry, update=('test-blok1',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '2.0.0')

    def test_update_an_uninstalled_blok(self):
        registry = self.init_registry(None)
        try:
            self.upgrade(registry, update=('test-blok1',))
            self.fail('No watchdog to update an uninstalled blok')
        except RegistryException:
            pass


class TestBlokRequired(DBTestCase):

    blok_entry_points = ('bloks', 'test_bloks')

    def test_blok_exist(self):
        registry = self.init_registry(None)
        Blok = registry.System.Blok
        query = Blok.query().filter(Blok.name == 'test-blok2')
        if not query.count():
            self.fail('No blok found')

        testblok2 = query.first()
        self.assertEqual(testblok2.state, 'uninstalled')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, None)
        self.assertEqual(testblok2.short_description, 'Test blok2')

    def test_install_1by1(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'uninstalled')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, None)
        self.upgrade(registry, install=('test-blok2',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, '1.0.0')

    def test_install(self):
        registry = self.init_registry(None)
        Blok = registry.System.Blok
        self.upgrade(registry, install=('test-blok2',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, '1.0.0')

    def test_uninstall(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok2',))
        self.upgrade(registry, uninstall=('test-blok2',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'uninstalled')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, None)

    def test_uninstall_required(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok2',))
        self.upgrade(registry, uninstall=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        self.assertEqual(testblok1.state, 'uninstalled')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, None)
        self.assertEqual(testblok2.state, 'uninstalled')
        self.assertEqual(testblok2.version, '1.0.0')
        self.assertEqual(testblok2.installed_version, None)

    def test_update(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok2',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok1.version = '2.0.0'
        testblok2.version = '2.0.0'
        self.upgrade(registry, update=('test-blok2',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.installed_version, '2.0.0')

    def test_update_required(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok2',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok1.version = '2.0.0'
        testblok2.version = '2.0.0'
        self.upgrade(registry, update=('test-blok1',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '2.0.0')
        self.assertEqual(testblok2.state, 'installed')
        self.assertEqual(testblok2.installed_version, '2.0.0')


class TestBlokRequired2(DBTestCase):

    blok_entry_points = ('bloks', 'test_bloks')

    def test_blok_exist(self):
        registry = self.init_registry(None)
        Blok = registry.System.Blok
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
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok1',))
        Blok = registry.System.Blok
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
        self.upgrade(registry, install=('test-blok2',))
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
        self.upgrade(registry, install=('test-blok3',))
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
        registry = self.init_registry(None)
        Blok = registry.System.Blok
        self.upgrade(registry, install=('test-blok3',))
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
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok3',))
        self.upgrade(registry, uninstall=('test-blok3',))
        Blok = registry.System.Blok
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
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok3',))
        self.upgrade(registry, uninstall=('test-blok2',))
        Blok = registry.System.Blok
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
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok3',))
        self.upgrade(registry, uninstall=('test-blok1',))
        Blok = registry.System.Blok
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
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok3',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        testblok1.version = '2.0.0'
        testblok2.version = '2.0.0'
        testblok3.version = '2.0.0'
        self.upgrade(registry, update=('test-blok3',))
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
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok3',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        testblok1.version = '2.0.0'
        testblok2.version = '2.0.0'
        testblok3.version = '2.0.0'
        self.upgrade(registry, update=('test-blok2',))
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
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok3',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        testblok1.version = '2.0.0'
        testblok2.version = '2.0.0'
        testblok3.version = '2.0.0'
        self.upgrade(registry, update=('test-blok1',))
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


class TestBlokConditionnal(DBTestCase):

    blok_entry_points = ('bloks', 'test_bloks')

    def test_install_1by1(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok1',))
        Blok = registry.System.Blok
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
        self.upgrade(registry, install=('test-blok4',))
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
        registry = self.init_registry(None)
        Blok = registry.System.Blok
        self.upgrade(registry, install=('test-blok5',))
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
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok5',))
        try:
            self.upgrade(registry, uninstall=('test-blok5',))
            self.fail('No watchdog to uninstall conditionnal blok')
        except RegistryException:
            pass

    def test_uninstall_conditionnal(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok5',))
        self.upgrade(registry, uninstall=('test-blok1',))
        Blok = registry.System.Blok
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
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok5',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        testblok1.version = '2.0.0'
        testblok4.version = '2.0.0'
        testblok5.version = '2.0.0'
        self.upgrade(registry, update=('test-blok5',))
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
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok5',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        testblok1.version = '2.0.0'
        testblok4.version = '2.0.0'
        testblok5.version = '2.0.0'
        self.upgrade(registry, update=('test-blok1',))
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


class TestBlokOptional(DBTestCase):

    blok_entry_points = ('bloks', 'test_bloks')

    def test_install_1by1(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok6.state, 'uninstalled')
        self.assertEqual(testblok6.version, '1.0.0')
        self.assertEqual(testblok6.installed_version, None)
        self.upgrade(registry, install=('test-blok6',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok6.state, 'installed')
        self.assertEqual(testblok6.version, '1.0.0')
        self.assertEqual(testblok6.installed_version, '1.0.0')

    def test_install(self):
        registry = self.init_registry(None)
        Blok = registry.System.Blok
        self.upgrade(registry, install=('test-blok6',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok6.state, 'installed')
        self.assertEqual(testblok6.version, '1.0.0')
        self.assertEqual(testblok6.installed_version, '1.0.0')

    def test_uninstall(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok6',))
        self.upgrade(registry, uninstall=('test-blok6',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok6.state, 'uninstalled')
        self.assertEqual(testblok6.version, '1.0.0')
        self.assertEqual(testblok6.installed_version, None)

    def test_uninstall_optional(self):
        registry = self.init_registry(None)
        Blok = registry.System.Blok
        self.upgrade(registry, install=('test-blok6',))
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        testblok6.version = '2.0.0'
        self.upgrade(registry, uninstall=('test-blok1',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        self.assertEqual(testblok1.state, 'uninstalled')
        self.assertEqual(testblok1.version, '1.0.0')
        self.assertEqual(testblok1.installed_version, None)
        self.assertEqual(testblok6.state, 'installed')
        self.assertEqual(testblok6.version, '2.0.0')
        self.assertEqual(testblok6.installed_version, '2.0.0')

    def test_update(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok6',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        testblok1.version = '2.0.0'
        testblok6.version = '2.0.0'
        self.upgrade(registry, update=('test-blok6',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '1.0.0')
        self.assertEqual(testblok6.state, 'installed')
        self.assertEqual(testblok6.installed_version, '2.0.0')

    def test_update_optional(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok6',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        testblok1.version = '2.0.0'
        testblok6.version = '2.0.0'
        self.upgrade(registry, update=('test-blok1',))
        # here the registry are restart the all the instance must be refresh
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        self.assertEqual(testblok1.state, 'installed')
        self.assertEqual(testblok1.installed_version, '2.0.0')
        self.assertEqual(testblok6.state, 'installed')
        self.assertEqual(testblok6.installed_version, '2.0.0')


class TestBlokOrder(DBTestCase):

    blok_entry_points = ('bloks', 'test_bloks')

    def check_order(self, registry, mode, wanted):
        Test = registry.Test
        self.assertEqual(Test.query().filter(Test.mode == mode).all().blok,
                         wanted)

    def test_install(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok3',))
        self.check_order(registry, 'install', [
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
            registry = self.init_registry(None)
            self.upgrade(registry, install=('test-blok3',))
            self.upgrade(registry, uninstall=('test-blok1',))
            self.assertEqual(uninstalled, [
                'test-blok3', 'test-blok2', 'test-blok1'])
        finally:
            Blok.uninstall = old_uninstall

    def test_update(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok3',))
        self.upgrade(registry, update=('test-blok1',))
        self.check_order(registry, 'update', [
            'test-blok1', 'test-blok2', 'test-blok3'])

    def test_load(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok3',))
        self.check_order(registry, 'load', [
            'anyblok-core', 'test-blok1', 'test-blok2', 'test-blok3'])


class TestBlokModel(DBTestCase):

    blok_entry_points = ('bloks', 'test_bloks')

    def test_remove_foreign_key_after_uninstallation(self):
        registry = self.init_registry(None)
        self.upgrade(registry, install=('test-blok7', 'test-blok8'))
        t2 = registry.Test2.insert(label="test2")
        registry.Test.insert(label="Test1", test2=t2.id)
        registry.old_session_commit()
        from sqlalchemy.exc import IntegrityError
        try:
            registry.Test2.query().delete()
            self.fail('No watch dog')
        except IntegrityError:
            pass
        registry.rollback()
        self.upgrade(registry, uninstall=('test-blok8',))
        registry.Test2.query().delete()


class TestBlokSession(DBTestCase):

    blok_entry_points = ('bloks', 'test_bloks')

    def test_session_with_no_change(self):
        registry = self.init_registry(None)
        Session = registry.Session
        self.upgrade(registry, install=('test-blok1',))
        self.assertIs(Session, registry.Session)

    def test_session_with_change_query(self):
        registry = self.init_registry(None)
        Session = registry.Session
        self.upgrade(registry, install=('test-blok11',))
        self.assertIsNot(Session, registry.Session)

    def test_session_with_change_session(self):
        registry = self.init_registry(None)
        Session = registry.Session
        self.upgrade(registry, install=('test-blok12',))
        self.assertIsNot(Session, registry.Session)
