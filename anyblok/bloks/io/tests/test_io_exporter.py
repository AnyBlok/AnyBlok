# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import BlokTestCase


class TestIOExportCSV(BlokTestCase):

    def test_get_counter_for_model(self):
        Exporter = self.registry.IO.Exporter
        val1 = Exporter.get_counter_by_model(Exporter.__registry_name__)
        val2 = Exporter.get_counter_by_model(Exporter.__registry_name__)
        self.assertEqual(int(val1) + 1, int(val2))

    def test_get_counter(self):
        Exporter = self.registry.IO.Exporter
        exporter = Exporter(model=Exporter.__registry_name__)
        val1 = exporter.get_counter()
        val2 = exporter.get_counter()
        self.assertEqual(int(val1) + 1, int(val2))
