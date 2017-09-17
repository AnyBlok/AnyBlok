# This file is a part of the AnyBlok project
#
#    Copyright (C) 2015 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import BlokTestCase


class TestIOCore(BlokTestCase):

    def checkExist(self):
        Mapping = self.registry.IO.Mapping
        self.assertTrue(
            Mapping.query().filter_by(
                key='test', model='Model.System.Blok').count())

    def checkUnExist(self):
        Mapping = self.registry.IO.Mapping
        self.assertFalse(
            Mapping.query().filter_by(
                key='test', model='Model.System.Blok').count())

    def test_session_delete_obj_with_mapping(self):
        Mapping = self.registry.IO.Mapping
        Blok = self.registry.System.Blok
        blok = Blok.insert(name='Test', version='0.0.0')
        self.checkUnExist()
        Mapping.set('test', blok)
        self.checkExist()
        blok.delete()
        self.checkUnExist()

    def test_query_delete_obj_with_mapping(self):
        Mapping = self.registry.IO.Mapping
        Blok = self.registry.System.Blok
        blok = Blok.insert(name='Test', version='0.0.0')
        self.checkUnExist()
        Mapping.set('test', blok)
        self.checkExist()
        Blok.query().filter_by(name='Test').delete()
        self.checkUnExist()
