# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Denis VIVIÈS <dvivies@geoblink.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest


@pytest.mark.usefixtures('rollback_registry')
class TestSystemBlok:
    def test_list_by_state_installed(self, rollback_registry):
        registry = rollback_registry
        installed = registry.System.Blok.list_by_state('installed')
        core_is_installed = 'anyblok-core' in installed
        assert core_is_installed is True

    def test_list_by_state_without_state(self, rollback_registry):
        registry = rollback_registry
        assert registry.System.Blok.list_by_state() is None

    def test_is_installed(self, rollback_registry):
        registry = rollback_registry
        assert registry.System.Blok.is_installed('anyblok-core') is True
