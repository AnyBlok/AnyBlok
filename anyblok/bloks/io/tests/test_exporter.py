# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import BlokTestCase
from ..exceptions import ExporterException


class TestExporter(BlokTestCase):

    def test_get_external_id(self):
        Exporter = self.registry.IO.Exporter
        val1 = Exporter.get_external_id(Exporter.__registry_name__)
        val2 = Exporter.get_external_id(Exporter.__registry_name__)
        val1 = val1.split('_')
        val1 = '_'.join([val1[0], str(int(val1[1]) + 1)])
        self.assertEqual(val1, val2)

    def test_get_key_for_mapping(self):
        Exporter = self.registry.IO.Exporter
        Blok = self.registry.System.Blok
        entry = Blok.from_primary_keys(name='anyblok-core')
        val1 = Exporter.get_external_id(Blok.__registry_name__)
        val1 = val1.split('_')
        val1 = '_'.join([val1[0], str(int(val1[1]) + 1)])
        self.assertEqual(Exporter.get_key_mapping(entry), val1)

    def test_get_key_for_mapping_2nd_time(self):
        Exporter = self.registry.IO.Exporter
        Blok = self.registry.System.Blok
        entry = Blok.from_primary_keys(name='anyblok-core')
        val1 = Exporter.get_external_id(Blok.__registry_name__)
        val1 = val1.split('_')
        val1 = '_'.join([val1[0], str(int(val1[1]) + 1)])
        self.assertEqual(Exporter.get_key_mapping(entry), val1)
        self.assertEqual(Exporter.get_key_mapping(entry), val1)

    def test_export_with_entries_doesnt_come_from_model(self):
        Exporter = self.registry.IO.Exporter
        Blok = self.registry.System.Blok
        exporter = Exporter(model=Blok.__registry_name__)
        with self.assertRaises(ExporterException):
            exporter.run([exporter])
