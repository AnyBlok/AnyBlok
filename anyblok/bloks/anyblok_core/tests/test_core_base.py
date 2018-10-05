# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest

from anyblok.tests.testcase import BlokTestCase
from ..exceptions import CoreBaseException


class TestCoreBase(BlokTestCase):

    def test_to_primary_keys(self):
        with self.assertRaises(CoreBaseException):
            test = self.registry.System()
            test.to_primary_keys()

    def test_from_primary_keys(self):
        with self.assertRaises(CoreBaseException):
            self.registry.System.from_primary_keys()

    def test_get_primary_keys(self):
        with self.assertRaises(CoreBaseException):
            self.registry.System.get_primary_keys()

    def test_get_model(self):
        M = self.registry.System.Model
        M2 = self.registry.System.get_model('Model.System.Model')
        self.assertEqual(M, M2)


@pytest.mark.usefixtures('rollback_registry')
class TestCoreBaseScope:
    def test_to_primary_keys(self, rollback_registry):
        registry = rollback_registry
        with pytest.raises(CoreBaseException) as ex:
            test = registry.System()
            test.to_primary_keys()

    def test_from_primary_keys(self, rollback_registry):
        registry = rollback_registry
        with pytest.raises(CoreBaseException) as ex:
            registry.System.from_primary_keys()

    def test_get_primary_keys(self, rollback_registry):
        registry = rollback_registry
        with pytest.raises(CoreBaseException) as ex:
            registry.System.get_primary_keys()

    def test_get_model(self, rollback_registry):
        registry = rollback_registry
        m = registry.System.Model
        m2 = registry.System.get_model('Model.System.Model')
        assert m == m2

