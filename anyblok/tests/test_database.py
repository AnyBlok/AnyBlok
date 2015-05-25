# -*- coding: utf-8 -*-
# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.tests.testcase import TestCase
from anyblok.config import Configuration
from datetime import datetime
import anyblok


class TestDataBase(TestCase):

    drivername = None
    ready_to_test = False

    def setUp(self):
        super(TestDataBase, self).setUp()
        self.load_env_for_drivername()

    def load_env_for_drivername(self):

        if self.drivername is None:
            return

        if Configuration.get('db_drivername') == 'postgres':
            self.ready_to_test = True


class TestPostgres(TestDataBase):

    drivername = 'postgres'

    def test_database(self):
        if not self.ready_to_test:
            return

        db_name = Configuration.get('db_name') + datetime.strftime(
            datetime.today(), '%Y-%m-%d_%H:%M:%S')
        bdd = anyblok.BDD[self.drivername]
        bdd.createdb(db_name)
        has_dblist = db_name in bdd.listdb()
        self.assertEqual(has_dblist, True)

        bdd.dropdb(db_name)
        has_dblist = db_name in bdd.listdb()
        self.assertEqual(has_dblist, False)
