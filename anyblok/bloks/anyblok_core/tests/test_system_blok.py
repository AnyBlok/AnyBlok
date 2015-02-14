# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import BlokTestCase


class TestSystemBlok(BlokTestCase):

    def test_list_by_state_installed(self):
        installed = self.registry.System.Blok.list_by_state('installed')
        core_is_installed = 'anyblok-core' in installed
        self.assertEqual(core_is_installed, True)

    def test_list_by_state_without_state(self):
        self.assertEqual(self.registry.System.Blok.list_by_state(), None)
