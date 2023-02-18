# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2019 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#    Copyright (C) 2002 Pierre Verkest <pierreverkest84@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from anyblok.testing import sgdb_in
from anyblok.blok import BlokManager
from anyblok.registry import RegistryException, RegistryConflictingException


@pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                    reason='Not for MySQL and MariaDB')
class TestBlok:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_testblok):
        transaction = registry_testblok.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_blok_exist(self, registry_testblok):
        registry = registry_testblok
        Blok = registry.System.Blok
        query = Blok.query().filter(Blok.name == 'test-blok1')
        if not query.count():
            pytest.fail('No blok found')

        testblok1 = query.first()
        assert testblok1.state == 'uninstalled'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version is None
        assert testblok1.short_description == ''
        assert testblok1.long_description == ''

    def test_install(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        assert testblok1.state == 'installed'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version == '1.0.0'

    def test_install_an_installed_blok(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok1',))
        with pytest.raises(RegistryException):
            registry.upgrade(install=('test-blok1',))

    def test_uninstall(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok1',))
        registry.upgrade(uninstall=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        assert testblok1.state == 'uninstalled'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version is None

    def test_uninstall_an_uninstalled_blok(self, registry_testblok):
        registry = registry_testblok
        with pytest.raises(RegistryException):
            registry.upgrade(uninstall=('test-blok1',))

    def test_update(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok1.version = '2.0.0'
        registry.upgrade(update=('test-blok1',))
        assert testblok1.state == 'installed'
        assert testblok1.installed_version == '2.0.0'

    def test_update_an_uninstalled_blok(self, registry_testblok):
        registry = registry_testblok
        with pytest.raises(RegistryException):
            registry.upgrade(update=('test-blok1',))


@pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                    reason='Not for MySQL and MariaDB')
class TestBlokRequired:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_testblok):
        transaction = registry_testblok.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_blok_exist(self, registry_testblok):
        registry = registry_testblok
        Blok = registry.System.Blok
        query = Blok.query().filter(Blok.name == 'test-blok2')
        if not query.count():
            pytest.fail('No blok found')

        testblok2 = query.first()
        assert testblok2.state == 'uninstalled'
        assert testblok2.version == '1.0.0'
        assert testblok2.installed_version is None
        assert testblok2.short_description == 'Test blok2'

    def test_install_1by1(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        assert testblok1.state == 'installed'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version == '1.0.0'
        assert testblok2.state == 'uninstalled'
        assert testblok2.version == '1.0.0'
        assert testblok2.installed_version is None
        registry.upgrade(install=('test-blok2',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        assert testblok1.state == 'installed'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version == '1.0.0'
        assert testblok2.state == 'installed'
        assert testblok2.version == '1.0.0'
        assert testblok2.installed_version == '1.0.0'

    def test_install(self, registry_testblok):
        registry = registry_testblok
        Blok = registry.System.Blok
        registry.upgrade(install=('test-blok2',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        assert testblok1.state == 'installed'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version == '1.0.0'
        assert testblok2.state == 'installed'
        assert testblok2.version == '1.0.0'
        assert testblok2.installed_version == '1.0.0'

    def test_uninstall(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok2',))
        registry.upgrade(uninstall=('test-blok2',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        assert testblok1.state == 'installed'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version == '1.0.0'
        assert testblok2.state == 'uninstalled'
        assert testblok2.version == '1.0.0'
        assert testblok2.installed_version is None

    def test_uninstall_required(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok2',))
        registry.upgrade(uninstall=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        assert testblok1.state == 'uninstalled'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version is None
        assert testblok2.state == 'uninstalled'
        assert testblok2.version == '1.0.0'
        assert testblok2.installed_version is None

    def test_update(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok2',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok1.version = '2.0.0'
        testblok2.version = '2.0.0'
        registry.upgrade(update=('test-blok2',))
        assert testblok1.state == 'installed'
        assert testblok1.installed_version == '1.0.0'
        assert testblok2.state == 'installed'
        assert testblok2.installed_version == '2.0.0'

    def test_update_required(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok2',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok1.version = '2.0.0'
        testblok2.version = '2.0.0'
        registry.upgrade(update=('test-blok1',))
        assert testblok1.state == 'installed'
        assert testblok1.installed_version == '2.0.0'
        assert testblok2.state == 'installed'
        assert testblok2.installed_version == '2.0.0'


@pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                    reason='Not for MySQL and MariaDB')
class TestBlokRequired2:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_testblok):
        transaction = registry_testblok.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_blok_exist(self, registry_testblok):
        registry = registry_testblok
        Blok = registry.System.Blok
        query = Blok.query().filter(Blok.name == 'test-blok3')
        if not query.count():
            pytest.fail('No blok found')

        testblok2 = query.first()
        assert testblok2.state == 'uninstalled'
        assert testblok2.version == '1.0.0'
        assert testblok2.installed_version is None
        long_description = ".. This file is a part of the AnyBlok project\n.."
        long_description += "\n..    Copyright (C) 2014 Jean-Sebastien SUZANNE"
        long_description += " <jssuzanne@anybox.fr>\n..\n.. This Source Code "
        long_description += "Form is subject to the terms of the Mozilla "
        long_description += "Public License,\n.. v. 2.0. If a copy of the MPL "
        long_description += "was not distributed with this file,You can\n.. "
        long_description += "obtain one at http://mozilla.org/MPL/2.0/.\n\n"
        long_description += "Test blok3\n"
        assert testblok2.long_description == long_description

    def test_install_1by1(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        assert testblok1.state == 'installed'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version == '1.0.0'
        assert testblok2.state == 'uninstalled'
        assert testblok2.version == '1.0.0'
        assert testblok2.installed_version is None
        assert testblok3.state == 'uninstalled'
        assert testblok3.version == '1.0.0'
        assert testblok3.installed_version is None
        registry.upgrade(install=('test-blok2',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        assert testblok1.state == 'installed'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version == '1.0.0'
        assert testblok2.state == 'installed'
        assert testblok2.version == '1.0.0'
        assert testblok2.installed_version == '1.0.0'
        assert testblok3.state == 'uninstalled'
        assert testblok3.version == '1.0.0'
        assert testblok3.installed_version is None
        registry.upgrade(install=('test-blok3',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        assert testblok1.state == 'installed'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version == '1.0.0'
        assert testblok2.state == 'installed'
        assert testblok2.version == '1.0.0'
        assert testblok2.installed_version == '1.0.0'
        assert testblok3.state == 'installed'
        assert testblok3.version == '1.0.0'
        assert testblok3.installed_version == '1.0.0'

    def test_install(self, registry_testblok):
        registry = registry_testblok
        Blok = registry.System.Blok
        registry.upgrade(install=('test-blok3',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        assert testblok1.state == 'installed'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version == '1.0.0'
        assert testblok2.state == 'installed'
        assert testblok2.version == '1.0.0'
        assert testblok2.installed_version == '1.0.0'
        assert testblok3.state == 'installed'
        assert testblok3.version == '1.0.0'
        assert testblok3.installed_version == '1.0.0'

    def test_uninstall(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok3',))
        registry.upgrade(uninstall=('test-blok3',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        assert testblok1.state, 'installed'
        assert testblok1.version, '1.0.0'
        assert testblok1.installed_version, '1.0.0'
        assert testblok2.state, 'installed'
        assert testblok2.version, '1.0.0'
        assert testblok2.installed_version, '1.0.0'
        assert testblok3.state, 'uninstalled'
        assert testblok3.version, '1.0.0'
        assert testblok3.installed_version is None

    def test_uninstall_first_required(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok3',))
        registry.upgrade(uninstall=('test-blok2',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        assert testblok1.state == 'installed'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version == '1.0.0'
        assert testblok2.state == 'uninstalled'
        assert testblok2.version == '1.0.0'
        assert testblok2.installed_version is None
        assert testblok3.state == 'uninstalled'
        assert testblok3.version == '1.0.0'
        assert testblok3.installed_version is None

    def test_uninstall_all_required(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok3',))
        registry.upgrade(uninstall=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        assert testblok1.state == 'uninstalled'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version is None
        assert testblok2.state == 'uninstalled'
        assert testblok2.version == '1.0.0'
        assert testblok2.installed_version is None
        assert testblok3.state == 'uninstalled'
        assert testblok3.version == '1.0.0'
        assert testblok3.installed_version is None

    def test_update(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok3',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        testblok1.version = '2.0.0'
        testblok2.version = '2.0.0'
        testblok3.version = '2.0.0'
        registry.upgrade(update=('test-blok3',))
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        assert testblok1.state == 'installed'
        assert testblok1.installed_version == '1.0.0'
        assert testblok2.state == 'installed'
        assert testblok2.installed_version == '1.0.0'
        assert testblok3.state == 'installed'
        assert testblok3.installed_version == '2.0.0'

    def test_update_first_required(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok3',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        testblok1.version = '2.0.0'
        testblok2.version = '2.0.0'
        testblok3.version = '2.0.0'
        registry.upgrade(update=('test-blok2',))
        assert testblok1.state == 'installed'
        assert testblok1.installed_version == '1.0.0'
        assert testblok2.state == 'installed'
        assert testblok2.installed_version == '2.0.0'
        assert testblok3.state == 'installed'
        assert testblok3.installed_version == '2.0.0'

    def test_update_all_required(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok3',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok2 = Blok.query().filter(Blok.name == 'test-blok2').first()
        testblok3 = Blok.query().filter(Blok.name == 'test-blok3').first()
        testblok1.version = '2.0.0'
        testblok2.version = '2.0.0'
        testblok3.version = '2.0.0'
        registry.upgrade(update=('test-blok1',))
        assert testblok1.state == 'installed'
        assert testblok1.installed_version == '2.0.0'
        assert testblok2.state == 'installed'
        assert testblok2.installed_version == '2.0.0'
        assert testblok3.state == 'installed'
        assert testblok3.installed_version == '2.0.0'


@pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                    reason='Not for MySQL and MariaDB')
class TestBlokConditionnal:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_testblok):
        transaction = registry_testblok.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_install_1by1(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        assert testblok1.state == 'installed'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version == '1.0.0'
        assert testblok4.state == 'uninstalled'
        assert testblok4.version == '1.0.0'
        assert testblok4.installed_version is None
        assert testblok5.state == 'uninstalled'
        assert testblok5.version == '1.0.0'
        assert testblok5.installed_version is None
        registry.upgrade(install=('test-blok4',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        assert testblok1.state == 'installed'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version == '1.0.0'
        assert testblok4.state == 'installed'
        assert testblok4.version == '1.0.0'
        assert testblok4.installed_version == '1.0.0'
        assert testblok5.state == 'installed'
        assert testblok5.version == '1.0.0'
        assert testblok5.installed_version == '1.0.0'

    def test_install(self, registry_testblok):
        registry = registry_testblok
        Blok = registry.System.Blok
        registry.upgrade(install=('test-blok5',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        assert testblok1.state == 'installed'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version == '1.0.0'
        assert testblok4.state == 'installed'
        assert testblok4.version == '1.0.0'
        assert testblok4.installed_version, '1.0.0'
        assert testblok5.state == 'installed'
        assert testblok5.version == '1.0.0'
        assert testblok5.installed_version == '1.0.0'

    def test_uninstall(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok5',))
        with pytest.raises(RegistryException):
            registry.upgrade(uninstall=('test-blok5',))

    def test_uninstall_conditionnal(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok5',))
        registry.upgrade(uninstall=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        assert testblok1.state, 'uninstalled'
        assert testblok1.version, '1.0.0'
        assert testblok1.installed_version is None
        assert testblok4.state, 'installed'
        assert testblok4.version, '1.0.0'
        assert testblok4.installed_version, '1.0.0'
        assert testblok5.state, 'uninstalled'
        assert testblok5.version, '1.0.0'
        assert testblok5.installed_version is None

    def test_update(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok5',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        testblok1.version = '2.0.0'
        testblok4.version = '2.0.0'
        testblok5.version = '2.0.0'
        registry.upgrade(update=('test-blok5',))
        assert testblok1.state == 'installed'
        assert testblok1.installed_version == '1.0.0'
        assert testblok4.state == 'installed'
        assert testblok4.installed_version == '1.0.0'
        assert testblok5.state == 'installed'
        assert testblok5.installed_version == '2.0.0'

    def test_update_conditionnal(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok5',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok4 = Blok.query().filter(Blok.name == 'test-blok4').first()
        testblok5 = Blok.query().filter(Blok.name == 'test-blok5').first()
        testblok1.version = '2.0.0'
        testblok4.version = '2.0.0'
        testblok5.version = '2.0.0'
        registry.upgrade(update=('test-blok1',))
        assert testblok1.state == 'installed'
        assert testblok1.installed_version == '2.0.0'
        assert testblok4.state == 'installed'
        assert testblok4.installed_version == '1.0.0'
        assert testblok5.state == 'installed'
        assert testblok5.installed_version == '2.0.0'


@pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                    reason='Not for MySQL and MariaDB')
class TestBlokOptional:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_testblok):
        transaction = registry_testblok.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_install_1by1(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok1',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        assert testblok1.state == 'installed'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version == '1.0.0'
        assert testblok6.state == 'uninstalled'
        assert testblok6.version == '1.0.0'
        assert testblok6.installed_version is None
        registry.upgrade(install=('test-blok6',))
        assert testblok1.state == 'installed'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version == '1.0.0'
        assert testblok6.state == 'installed'
        assert testblok6.version == '1.0.0'
        assert testblok6.installed_version == '1.0.0'

    def test_install(self, registry_testblok):
        registry = registry_testblok
        Blok = registry.System.Blok
        registry.upgrade(install=('test-blok6',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        assert testblok1.state == 'installed'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version == '1.0.0'
        assert testblok6.state == 'installed'
        assert testblok6.version == '1.0.0'
        assert testblok6.installed_version == '1.0.0'

    def test_uninstall(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok6',))
        registry.upgrade(uninstall=('test-blok6',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        assert testblok1.state == 'installed'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version == '1.0.0'
        assert testblok6.state == 'uninstalled'
        assert testblok6.version == '1.0.0'
        assert testblok6.installed_version is None

    def test_uninstall_optional(self, registry_testblok):
        registry = registry_testblok
        Blok = registry.System.Blok
        registry.upgrade(install=('test-blok6',))
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        testblok6.version = '2.0.0'
        registry.upgrade(uninstall=('test-blok1',))
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        assert testblok1.state == 'uninstalled'
        assert testblok1.version == '1.0.0'
        assert testblok1.installed_version is None
        assert testblok6.state == 'installed'
        assert testblok6.version == '2.0.0'
        assert testblok6.installed_version == '2.0.0'

    def test_update(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok6',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        testblok1.version = '2.0.0'
        testblok6.version = '2.0.0'
        registry.upgrade(update=('test-blok6',))
        assert testblok1.state == 'installed'
        assert testblok1.installed_version == '1.0.0'
        assert testblok6.state == 'installed'
        assert testblok6.installed_version == '2.0.0'

    def test_update_optional(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok6',))
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok6 = Blok.query().filter(Blok.name == 'test-blok6').first()
        testblok1.version = '2.0.0'
        testblok6.version = '2.0.0'
        registry.upgrade(update=('test-blok1',))
        assert testblok1.state == 'installed'
        assert testblok1.installed_version == '2.0.0'
        assert testblok6.state == 'installed'
        assert testblok6.installed_version == '2.0.0'


@pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                    reason='Not for MySQL and MariaDB')
class TestBlokConflicting:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_testblok):
        transaction = registry_testblok.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_marked_as_conflicting(self, registry_testblok):
        blok1 = BlokManager.get('test-blok1')
        blok13 = BlokManager.get('test-blok13')
        assert blok13.conflicting == ['test-blok1']
        assert blok1.conflicting_by == ['test-blok13']

    def test_install_1by1(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok1',))
        with pytest.raises(RegistryConflictingException):
            registry.upgrade(install=('test-blok13',))

    def test_install_both(self, registry_testblok):
        registry = registry_testblok
        with pytest.raises(RegistryConflictingException):
            registry.upgrade(install=('test-blok1', 'test-blok13'))

    def test_uninstall_first_and_intall_another_in_two_step(
        self, registry_testblok
    ):
        registry = registry_testblok
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok13 = Blok.query().filter(Blok.name == 'test-blok13').first()
        registry.upgrade(install=('test-blok1',))
        assert testblok1.state == 'installed'
        assert testblok13.state == 'uninstalled'
        registry.upgrade(uninstall=('test-blok1',))
        assert testblok1.state == 'uninstalled'
        assert testblok13.state == 'uninstalled'
        registry.upgrade(install=('test-blok13',))
        assert testblok1.state == 'uninstalled'
        assert testblok13.state == 'installed'

    def test_replace_blok_by_another_in_one_step(self, registry_testblok):
        registry = registry_testblok
        Blok = registry.System.Blok
        testblok1 = Blok.query().filter(Blok.name == 'test-blok1').first()
        testblok13 = Blok.query().filter(Blok.name == 'test-blok13').first()
        registry.upgrade(install=('test-blok1',))
        assert testblok1.state == 'installed'
        assert testblok13.state == 'uninstalled'
        registry.upgrade(uninstall=('test-blok1',), install=('test-blok13',))
        assert testblok1.state == 'uninstalled'
        assert testblok13.state == 'installed'


@pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                    reason='Not for MySQL and MariaDB')
class TestBlokUndefined:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_testblok):
        transaction = registry_testblok.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_blok_15_exist(self, registry_testblok):
        registry = registry_testblok
        Blok = registry.System.Blok
        query = Blok.query().filter(Blok.name == 'test-blok15')
        if not query.count():
            pytest.fail('No blok found')

        testblok15 = query.first()
        assert testblok15.state == 'uninstalled'
        assert testblok15.version == '1.0.0'
        assert testblok15.installed_version is None
        assert testblok15.short_description == 'Test blok15'

    def test_blok_undefined_exist(self, registry_testblok):
        registry = registry_testblok
        Blok = registry.System.Blok
        query = Blok.query().filter(Blok.name == 'test-undefined')
        if not query.count():
            pytest.fail('No blok found')

        testblokundefined = query.first()
        assert testblokundefined.state == 'undefined'
        assert testblokundefined.version == '0.0.0'
        assert testblokundefined.installed_version is None
        assert testblokundefined.short_description == 'Blok undefined'

    def test_install_both(self, registry_testblok):
        registry = registry_testblok
        with pytest.raises(RegistryException):
            registry.upgrade(install=('test-blok15',))

    def test_install_undefined(self, registry_testblok):
        registry = registry_testblok
        with pytest.raises(RegistryException):
            registry.upgrade(install=('test-undefined',))


@pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                    reason='Not for MySQL and MariaDB')
class TestBlokOrder:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_testblok):
        transaction = registry_testblok.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def check_order(self, registry, mode, wanted):
        Test = registry.Test
        bloks = Test.query().filter(Test.mode == mode).all().blok
        for _wanted in wanted:
            assert _wanted in bloks

    def test_install(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok3',))
        self.check_order(registry, 'install', [
            'test-blok1', 'test-blok2', 'test-blok3'])

    def test_uninstall(self, registry_testblok):
        from anyblok.blok import Blok, BlokManager
        old_uninstall = Blok.uninstall

        uninstalled = []

        def uninstall(self):
            cls = self.__class__
            uninstalled.extend(
                [x for x, y in BlokManager.bloks.items() if y is cls])

        try:
            Blok.uninstall = uninstall
            registry = registry_testblok
            registry.upgrade(install=('test-blok3',))
            registry.upgrade(uninstall=('test-blok1',))
            assert uninstalled == [
                'test-blok3', 'test-blok2', 'test-blok1']
        finally:
            Blok.uninstall = old_uninstall

    def test_update(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok3',))
        registry.upgrade(update=('test-blok1',))
        self.check_order(registry, 'update', [
            'test-blok1', 'test-blok2', 'test-blok3'])

    def test_load(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok3',))
        self.check_order(registry, 'load', [
            'anyblok-core', 'test-blok1', 'test-blok2', 'test-blok3'])


@pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                    reason='Not for MySQL and MariaDB')
class TestBlokModel:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_testblok):
        transaction = registry_testblok.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_remove_foreign_key_after_uninstallation(self, registry_testblok):
        registry = registry_testblok
        registry.upgrade(install=('test-blok7', 'test-blok8'))
        t2 = registry.Test2.insert(label="test2")
        registry.Test.insert(label="Test1", test2=t2.id)
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            with registry.begin_nested():
                registry.Test2.execute_sql_statement(
                    registry.Test2.delete_sql_statement())

        registry.upgrade(uninstall=('test-blok8',))
        registry.Test2.execute_sql_statement(
            registry.Test2.delete_sql_statement())

    def test_auto_migration_is_between_pre_and_post_migration_1(
        self, registry_testblok
    ):
        registry = registry_testblok
        registry.upgrade(install=('test-blok14',))
        blok = BlokManager.get('test-blok14')
        assert blok.table_exist_before_automigration is False
        assert blok.table_exist_after_automigration is True
        registry.Test.insert()
        assert registry.Test.query().count() == 1

    def test_auto_migration_is_between_pre_and_post_migration_2(
        self, registry_testblok
    ):
        registry = registry_testblok
        registry.upgrade(install=('test-blok14',))
        blok = BlokManager.get('test-blok14')
        registry.Test.insert()
        assert registry.Test.query().count() == 1
        registry.upgrade(update=('test-blok14',))
        assert blok.table_exist_before_automigration is True
        assert blok.table_exist_after_automigration is True
        assert registry.Test.query().count() == 1


@pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                    reason='Not for MySQL and MariaDB')
class TestBlokSession:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_testblok_func):
        request.addfinalizer(
            registry_testblok_func.unittest_transaction.rollback)

    def test_session_with_no_change(self, registry_testblok_func):
        registry = registry_testblok_func
        Session = registry.Session
        registry.upgrade(install=('test-blok1',))
        assert Session is registry.Session

    def test_session_with_change_query(self, registry_testblok_func):
        registry = registry_testblok_func
        Session = registry.Session
        registry.upgrade(install=('test-blok11',))
        assert Session is not registry.Session

    def test_session_with_change_session(self, registry_testblok_func):
        registry = registry_testblok_func
        Session = registry.Session
        registry.upgrade(install=('test-blok12',))
        assert Session is not registry.Session


@pytest.mark.skipif(sgdb_in(['MySQL', 'MariaDB']),
                    reason='Not for MySQL and MariaDB')
class TestBlokInstallLifeCycle:

    @pytest.fixture(autouse=True)
    def transact(self, request, registry_testblok_func):
        def clear_called_methods():
            BlokManager.get('test-blok16').called_methods = []
        request.addfinalizer(clear_called_methods)
        request.addfinalizer(
            registry_testblok_func.unittest_transaction.rollback)

    @pytest.fixture()
    def registry_blok16_installed(self, registry_testblok_func):
        registry_testblok_func.upgrade(install=('test-blok16',))
        blok = BlokManager.get('test-blok16')
        blok.called_methods = []
        return registry_testblok_func

    def test_install_without_demo(self, registry_testblok_func):
        registry = registry_testblok_func
        registry.System.Parameter.set("with-demo", False)
        registry.upgrade(install=('test-blok16',))
        blok = BlokManager.get('test-blok16')
        assert blok.called_methods == [
            "pre_migration", "post_migration", "update",
        ]

    def test_install_with_demo(self, registry_testblok_func):
        registry = registry_testblok_func
        registry.System.Parameter.set("with-demo", True)
        registry.upgrade(install=('test-blok16',))
        blok = BlokManager.get('test-blok16')
        assert blok.called_methods == [
            "pre_migration", "post_migration", "update", "update_demo",
        ]

    def test_update_without_demo(self, registry_blok16_installed):
        registry = registry_blok16_installed
        registry.System.Parameter.set("with-demo", False)
        registry.upgrade(update=('test-blok16',))
        blok = BlokManager.get('test-blok16')
        assert blok.called_methods == [
            "pre_migration", "post_migration", "update",
        ]

    def test_update_with_demo(self, registry_blok16_installed):
        registry = registry_blok16_installed
        registry.System.Parameter.set("with-demo", True)
        registry.upgrade(update=('test-blok16',))
        blok = BlokManager.get('test-blok16')
        assert blok.called_methods == [
            "pre_migration", "post_migration", "update", "update_demo",
        ]

    def test_unistall_without_demo(self, registry_blok16_installed):
        registry = registry_blok16_installed
        registry.System.Parameter.set("with-demo", False)
        registry.upgrade(uninstall=('test-blok16',))
        blok = BlokManager.get('test-blok16')
        assert blok.called_methods == [
            "uninstall",
        ]

    def test_unistall_with_demo(self, registry_blok16_installed):
        registry = registry_blok16_installed
        registry.System.Parameter.set("with-demo", True)
        registry.upgrade(uninstall=('test-blok16',))
        blok = BlokManager.get('test-blok16')
        assert blok.called_methods == [
            "uninstall_demo", "uninstall",
        ]

    def test_update_loadwithoutmigration(self, registry_blok16_installed):
        registry = registry_blok16_installed
        registry.loadwithoutmigration = True
        registry.System.Parameter.set("with-demo", True)
        registry.upgrade(update=('test-blok16',))
        blok = BlokManager.get('test-blok16')
        assert blok.called_methods == []

    def test_update_withoutautomigration(self, registry_blok16_installed):
        registry = registry_blok16_installed
        registry.withoutautomigration = True
        registry.System.Parameter.set("with-demo", True)
        registry.upgrade(update=('test-blok16',))
        blok = BlokManager.get('test-blok16')
        assert blok.called_methods == [
            "pre_migration", "post_migration", "update", "update_demo",
        ]
